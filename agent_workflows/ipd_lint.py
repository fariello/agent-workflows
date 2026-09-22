"""Deterministic, read-only IPD linter (Set ipd-structure, Order 02).

Enforces the canonical schema (``agent_workflows.ipd_schema``) against an IPD document. This module
makes NO model calls, uses NO network, and performs NO writes. It is stdlib-only and Python 3.9
compatible.

Hard boundary (spec Section 10.1): a passing lint means only that the document conforms to the
modeled STRUCTURAL and STATE contract for the requested checkpoint. It does NOT establish semantic
coverage, correctness, meaningful atomicity, evidence sufficiency/authenticity, truthful
blocking-classification, or successful execution. Those remain the semantic reviewer's job.

Dispositions (spec Sections 13.2, 13.3): ``conforming`` (the only pass), ``quarantined`` and
``legacy/not evaluated`` (non-passing informational), and ``error`` (conformance errors). Process
exit is separate from disposition: exit 0 = evaluation succeeded with no conformance error (which
INCLUDES an evaluation that yields ``quarantined``/``legacy/not evaluated``); exit 1 = conformance
error(s); exit 2 = invocation/parse/internal failure. Authoritative gates require disposition
``conforming``, not merely exit 0.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, FrozenSet, List, NamedTuple, Optional, Tuple

from agent_workflows import ipd_schema as S
from agent_workflows import lifecycle_style as _LS
from agent_workflows import term as _T
from agent_workflows.term import Term

# --------------------------------------------------------------------------------------
# Diagnostics
# --------------------------------------------------------------------------------------


class Diagnostic(NamedTuple):
    line: int  # 1-based; 0 when not tied to a line
    col: int  # 1-based; 0 when not tied to a column
    code: str  # stable rule code, e.g. IPD-E201
    message: str

    def render(self, path: str) -> str:
        return f"{path}:{self.line}:{self.col} {self.code} {self.message}"


# Stable rule codes (grouped by area).
C_PARSE = "IPD-P001"
C_META_MISSING = "IPD-M101"
C_META_DUP = "IPD-M102"
C_META_UNKNOWN = "IPD-M103"
C_META_FIELD = "IPD-M104"
C_META_PATH = "IPD-M105"
C_HEADING_ORDER = "IPD-H201"
C_HEADING_MISSING = "IPD-H202"
C_HEADING_DUP = "IPD-H203"
C_EXEC_PLACEMENT = "IPD-H204"
C_VALID_PLACEMENT = "IPD-H205"
C_ID_GRAMMAR = "IPD-I301"
C_ID_FAMILY = "IPD-I302"
C_BIJECTION = "IPD-I303"
C_WATERMARK = "IPD-I304"
C_DEPENDS = "IPD-I305"
C_EXEC_STATE = "IPD-S401"
C_VALID_STATE = "IPD-S402"
C_CROSS_STATE = "IPD-S403"
C_CHECKPOINT = "IPD-S404"
C_EXEC_HISTORY = "IPD-S405"
C_EXEC_ATTRIBUTION = (
    "IPD-S406"  # terminal history actor/summary attribution (Order wezhxg)
)
C_READINESS_UNATTESTED = (
    "IPD-M107"  # `- Readiness:` present with no review verdict behind it (rdattest)
)
C_GATE_HAND_ROLLED_MOVE = (
    "IPD-M108"  # gate prescribes hand-rolled terminal lifecycle move (dcri4s)
)
C_OQ = "IPD-Q501"
C_SIZE = "IPD-Z601"
C_SIZE_DENSITY = "IPD-Z602"
C_SCOPE_PATHS = "IPD-M106"  # Scope-Paths declared-scope allowlist (Order oorry1)
C_NAME = "IPD-N001"  # filename does not match the plan grammar (awcheck Order 03)
# orchtyped `dpdyed` (spec `r07vma` R1a/R3/R7): an Order-0 orchestrator's checklist row is not a
# well-formed TYPED CHILD-TRACKING ROW. Sited in the `IPD-S4xx` state/SHAPE family because that is
# what it judges; `IPD-S407` was the next free number in that family, confirmed by comparing the
# IMPORTED values of every `C_*` constant rather than by grepping the source (three constants are
# multi-line assignments a single-line grep misses: `IPD-S406`, `IPD-M107`, `IPD-M108`).
C_ORCH_ROW = "IPD-S407"
# IPD-C8xx is the CITATION-ANCHOR area, opened fresh by citeanchor `mzc019` rather than extending
# IPD-I3xx (the id-family group, which concerns E-*/V-* identifiers and has nothing to do with
# citations). Codes are stable and are NEVER recycled; IPD-D701 is RETIRED and must not be revived.
C_CITATION_ANCHOR = (
    "IPD-C801"  # a code citation carrying no durable anchor (spec Section 10.2)
)


def _name_conformant(path: Path, legacy: bool) -> bool:
    """True if the plan's FILENAME conforms to the clustered `.ipd.md` grammar. Loads the shipped
    normalizer the portable way (engine.resolve_source_root, like check_engine). When it cannot be
    located, returns True (do not flag on an unavailable normalizer). With legacy=True, a name that
    fails is_conformant but is a recognized legacy shape (parse_name non-None) is accepted."""
    try:
        # Reuse the portable normalizer loader in check_engine (the `agent_workflows` package is
        # whitelisted for this stdlib-only module; check_engine owns the layout-agnostic path logic).
        from agent_workflows import check_engine as _ce

        npn = _ce._load_normalizer()
        if npn is None:
            return True
        if npn.is_conformant(path.name, expected_type="ipd"):
            return True
        if legacy and npn.parse_name(path.name) is not None:
            return True
        return False
    except Exception:
        return True  # never let a name-check failure produce a false structural error


def _with_name_check(res, path: Path, legacy: bool):
    """Return (diagnostics, disposition) augmented with an IPD-N001 filename-conformity diagnostic.

    Additive: keeps all structural diagnostics. Respects the terminal-dir short-circuit - a file that
    lints as `legacy/not evaluated` (a grandfathered terminal-dir file, not being evaluated) is left
    alone. A nonconformant name on an EVALUATED plan forces the ERROR disposition (unless --legacy
    accepts the name)."""
    diags = list(res.diagnostics)
    disp = res.disposition
    if disp == S.DISPOSITION_LEGACY:
        return diags, disp  # not evaluated; do not add a name finding
    # Only name-check ACTUAL plan files (under a plans/ tree). A fixture or arbitrary path passed to
    # `aw ipd lint` is not subject to the plan filename grammar.
    parts = {p for p in path.parts}
    if "plans" not in parts:
        return diags, disp
    if not _name_conformant(path, legacy):
        diags.append(
            Diagnostic(
                0,
                0,
                C_NAME,
                "filename does not match the plan grammar (YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md)",
            )
        )
        disp = S.DISPOSITION_ERROR
    return diags, disp


# IPD-D701 (em/en dash in authored prose) was RETIRED: the no-dash convention is a
# user-facing prose rule only (see GUIDING_PRINCIPLES P13, AGENTS.md execution contract).
# IPDs are internal/AI-facing artifacts, so the linter no longer flags dashes in them.


# --------------------------------------------------------------------------------------
# Fence-aware structural reader (spec Section 4.1)
# --------------------------------------------------------------------------------------


class H2(NamedTuple):
    title: str  # heading text without the leading "## "
    line: int  # 1-based line number


class Leaf(NamedTuple):
    kind: str  # "E" or "V" or "other"
    ident: str  # e.g. "E-01" (empty for "other")
    checked: bool
    text: str  # remainder after the id
    line: int
    section: str  # the enclosing H2 title
    fields: Dict[str, str]  # indented "- Key: value" sub-fields
    target: str  # for V rows: the "validates E-NN" target (empty otherwise)


class ParsedDoc(NamedTuple):
    title: str
    meta_fields: Dict[str, str]
    meta_errors: List[S.MetaError]
    h2: List[H2]
    exec_leaves: List[Leaf]
    valid_leaves: List[Leaf]
    exec_task_groups: int
    open_questions: List[Dict[str, str]]
    size_assessment: Optional[str]
    history_lines: List[Tuple[int, str]]
    gate_lines: List[Tuple[int, str]] = []


_FENCE_RE = re.compile(r"^(\s*)(```|~~~)")
_H1_RE = re.compile(r"^# (.+)$")
_H2_RE = re.compile(r"^## (.+?)\s*$")
_H3_RE = re.compile(r"^### (.+?)\s*$")
_LEAF_RE = re.compile(r"^- \[([ x])\]\s+(.*)$")
_SUBFIELD_RE = re.compile(r"^\s+- ([A-Za-z][A-Za-z /-]*?):\s?(.*)$")
# orchtyped `dpdyed` (spec `r07vma` R1a): the TYPED CHILD-TRACKING ROW grammar, and the ONLY
# definition of it in the tree (R3). A conforming orchestrator checklist row is exactly:
#
#     - [ ] E-NN CONFIRM <child-id6> REACHED <status>
#
# FULLY ANCHORED AT BOTH ENDS ON PURPOSE. `^` refuses an over-indented row or one that merely
# CONTAINS the phrase mid-line, and `$` refuses trailing prose after the status, which is the shape a
# deliverable would take if the grammar let a row carry a second clause ("... REACHED executed and
# then re-run the suite"). Widening either anchor re-opens the place R1a exists to close.
# THE TICKED BOX IS TOLERATED (`[ x]`) because a mid-execution or hand-run orchestrator legitimately
# carries ticked rows, and shape conformance is not a statement about progress.
# CONTINUATION LINES ARE DELIBERATELY NOT MATCHED HERE. R1a leaves them unparsed as human-readable
# context and spec Section 3a limit 1 records that as an honest limit: the prose residue remains the
# semantic probe's business (`77tr3o` R-12), and an implementer who extends this pattern into the
# continuation lines has changed the contract and broken that division of labour.
_ORCH_ROW_RE = re.compile(
    r"^- \[[ x]\] (E-[0-9]{2,}) CONFIRM ([0-9a-z]{6}) REACHED ([A-Za-z][A-Za-z-]*)$"
)
_HISTORY_LINE_RE = re.compile(r"^-\s+(?:\d{4}-\d{2}-\d{2})\s+(\S+)")
# ipdgates Order wezhxg: parse the full terminal history line `- <date> <status> (<actor>): <msg>`
# so the post-transition attribution lint can reject a generic/empty actor + empty summary.
#
# THE ACTOR CAPTURE IS LAZY (`.*?`), NOT `[^)]*` AND NOT GREEDY (plan fn2l1u E-03), and the choice is
# settled by measurement. `[^)]*` stopped at the FIRST `)`, so an actor CONTAINING parentheses (e.g.
# `opencode (its_direct/some-model)`, the shape 274 of 638 tracked plans carry in `- Author:` and that
# agents copy into `--actor`) never matched at all; `_newest_executed_history` then fell through to its
# bare-line branch and reported an EMPTY actor for a line where one is plainly present. Because
# IPD-S406 runs POST-transition, that fired AFTER the lifecycle commit and left finalize
# `committed-incomplete` with a resume instruction that could not succeed.
#
# GREEDY WOULD HAVE BEEN A REGRESSION, which is why lazy is not a style preference. Against
# `- 2026-09-08 executed (opencode/model): fixed foo(bar): baz` - a line that parses CORRECTLY today -
# greedy anchors on the LAST `):` and captures actor `opencode/model): fixed foo(bar`, silently
# corrupting it. Lazy yields actor `opencode/model` and the full message, identical to the old
# pattern's output. Measured over all 3073 tracked history records: lazy changes the captures of ZERO
# previously-parsing lines. Do NOT loosen the date or status portions.
_HISTORY_ATTRIB_RE = re.compile(
    r"^-\s+(?:\d{4}-\d{2}-\d{2})\s+(?P<status>\S+)\s+\((?P<actor>.*?)\)\s*:\s*(?P<msg>.*)$"
)
# The generic machine-default actor(s) the attribution lint rejects (pinned narrowly per OQ; do NOT
# expand to bare tool/human names like `Antigravity`/`maintainer`). Targets ONLY the `aw set` default.
_GENERIC_ACTORS: FrozenSet[str] = frozenset(("aw set", "aw set, --by-human"))


def _structural_lines(text: str) -> List[Tuple[int, str]]:
    """Yield (1-based line number, line) for lines OUTSIDE fenced code, indented code, actual YAML
    front matter, and block quotes. This is what structural checks see (spec Section 4.1)."""
    out: List[Tuple[int, str]] = []
    lines = text.splitlines()
    in_fence = False
    fence_marker = ""
    # YAML front matter: only if the very first line is exactly '---'.
    idx = 0
    n = len(lines)
    if n and lines[0].strip() == "---":
        # skip to the closing '---'
        idx = 1
        while idx < n and lines[idx].strip() != "---":
            idx += 1
        idx += 1  # skip the closing fence
    for i in range(idx, n):
        raw = lines[i]
        lineno = i + 1
        m = _FENCE_RE.match(raw)
        if m:
            marker = m.group(2)
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            continue
        if in_fence:
            continue
        if raw.startswith("    ") or raw.startswith("\t"):
            # indented code block (4 spaces / tab) - excluded from structure, but indented
            # sub-fields of a leaf use 2 spaces so they are NOT excluded here.
            continue
        if raw.lstrip().startswith(">"):
            continue  # block quote
        out.append((lineno, raw))
    return out


def parse(text: str) -> ParsedDoc:
    """Parse an IPD into its structural pieces, fence-aware. Never raises on ordinary content."""
    struct = _structural_lines(text)
    title = ""
    h2: List[H2] = []
    # Metadata block: contiguous "- Field:" bullet lines after the H1, before the first H2.
    meta_slice: List[str] = []
    seen_h1 = False
    first_h2_seen = False
    for lineno, raw in struct:
        if not seen_h1:
            m1 = _H1_RE.match(raw)
            if m1:
                title = m1.group(1).strip()
                seen_h1 = True
            continue
        if not first_h2_seen and _H2_RE.match(raw):
            first_h2_seen = True
        if not first_h2_seen:
            meta_slice.append(raw)
    meta_fields, meta_errors = S.parse_metadata_block(meta_slice)

    for lineno, raw in struct:
        mh = _H2_RE.match(raw)
        if mh:
            h2.append(H2(mh.group(1).strip(), lineno))

    # Walk leaves within the execution + validation sections (identified by H2 title).
    exec_title = S.H_EXECUTION
    valid_titles = {S.H_VALIDATION_CHILD, S.H_VALIDATION_ORCH}
    exec_leaves: List[Leaf] = []
    valid_leaves: List[Leaf] = []
    exec_task_groups = 0
    open_questions: List[Dict[str, str]] = []
    size_assessment: Optional[str] = None
    history_lines: List[Tuple[int, str]] = []
    gate_lines: List[Tuple[int, str]] = []

    current_h2 = ""
    current_leaf: Optional[Leaf] = None
    cur_fields: Dict[str, str] = {}
    pending_oq: Optional[Dict[str, str]] = None

    def _flush_leaf():
        nonlocal current_leaf, cur_fields
        if current_leaf is not None:
            lf = current_leaf._replace(fields=dict(cur_fields))
            # Route by ENCLOSING SECTION, not by parsed kind, so a malformed leaf in a checklist
            # section is retained (kind "other") and flagged by the id-family check (spec 5.5).
            if lf.section == exec_title:
                exec_leaves.append(lf)
            elif lf.section in valid_titles:
                valid_leaves.append(lf)
        current_leaf = None
        cur_fields = {}

    def _flush_oq():
        nonlocal pending_oq
        if pending_oq is not None:
            open_questions.append(pending_oq)
        pending_oq = None

    for lineno, raw in struct:
        mh = _H2_RE.match(raw)
        if mh:
            _flush_leaf()
            _flush_oq()
            current_h2 = mh.group(1).strip()
            continue
        # Workflow history line
        if current_h2 == S.H_WORKFLOW_HISTORY:
            if raw.lstrip().startswith("- "):
                history_lines.append((lineno, raw))
            continue
        # Task-group H3 inside the execution section.
        mh3 = _H3_RE.match(raw)
        if mh3:
            _flush_leaf()
            if current_h2 == exec_title and mh3.group(1).strip().lower().startswith(
                "task group"
            ):
                exec_task_groups += 1
            # Open-question H3 (OQ-NN:)
            if current_h2 == S.H_OPEN_QUESTIONS:
                _flush_oq()
                moq = S.OQ_HEADING_RE.match(raw)
                if moq:
                    pending_oq = {"id": moq.group(1), "line": str(lineno)}
            continue
        # Leaf line.
        ml = _LEAF_RE.match(raw)
        if ml and current_h2 in ({exec_title} | valid_titles):
            _flush_leaf()
            checked = ml.group(1) == "x"
            body = ml.group(2)
            me = S.E_ROW_RE.match(raw)
            mv = S.V_ROW_RE.match(raw)
            if current_h2 == exec_title:
                if me:
                    ident = me.group(1)
                    current_leaf = Leaf(
                        "E", ident, checked, body, lineno, current_h2, {}, ""
                    )
                else:
                    current_leaf = Leaf(
                        "other", "", checked, body, lineno, current_h2, {}, ""
                    )
            else:  # validation section
                if mv:
                    current_leaf = Leaf(
                        "V",
                        mv.group(1),
                        checked,
                        body,
                        lineno,
                        current_h2,
                        {},
                        mv.group(2),
                    )
                else:
                    current_leaf = Leaf(
                        "other", "", checked, body, lineno, current_h2, {}, ""
                    )
            cur_fields = {}
            continue
        # Indented sub-field of the current leaf.
        msf = _SUBFIELD_RE.match(raw)
        if msf and current_leaf is not None:
            cur_fields[msf.group(1).strip()] = msf.group(2).strip()
            continue
        # OQ sub-fields + size assessment (plain "- Field: value" bullets under their H2).
        mmeta = S._META_LINE_RE.match(raw)
        if mmeta:
            fld = mmeta.group("field").strip()
            val = mmeta.group("value").strip()
            if current_h2 == S.H_OPEN_QUESTIONS and pending_oq is not None:
                pending_oq[fld] = val
            elif current_h2 == S.H_APPROVAL_GATE and fld == "Size assessment":
                size_assessment = val

    _flush_leaf()
    _flush_oq()

    lines = text.splitlines()
    gate_h2_idx = next(
        (i for i, h in enumerate(h2) if h.title == S.H_APPROVAL_GATE), None
    )
    if gate_h2_idx is not None:
        start_line = h2[gate_h2_idx].line
        end_line = (
            h2[gate_h2_idx + 1].line - 1 if gate_h2_idx + 1 < len(h2) else len(lines)
        )
        gate_lines = [(lno, lines[lno - 1]) for lno in range(start_line, end_line + 1)]

    return ParsedDoc(
        title=title,
        meta_fields=meta_fields,
        meta_errors=meta_errors,
        h2=h2,
        exec_leaves=exec_leaves,
        valid_leaves=valid_leaves,
        exec_task_groups=exec_task_groups,
        open_questions=open_questions,
        size_assessment=size_assessment,
        history_lines=history_lines,
        gate_lines=gate_lines,
    )


# --------------------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------------------


def _dir_of(path: Optional[Path]) -> Optional[str]:
    if path is None:
        return None
    parts = path.resolve().parts
    for anchor in ("pending", "executed", "superseded", "not-executed", "reusable"):
        if anchor in parts:
            return anchor
    return None


def check_metadata(doc: ParsedDoc, directory: Optional[str]) -> List[Diagnostic]:
    diags: List[Diagnostic] = []
    for me in doc.meta_errors:
        code = (
            C_META_DUP
            if me.message == "duplicate field"
            else (C_META_UNKNOWN if me.message == "unknown field" else C_META_FIELD)
        )
        diags.append(Diagnostic(0, 0, code, f"{me.field}: {me.message}"))
    for me in S.validate_metadata(doc.meta_fields, directory=directory):
        code = (
            C_META_MISSING
            if "missing" in me.message
            else (
                C_META_PATH
                if me.field == "Status" and "directory" in me.message
                else C_META_FIELD
            )
        )
        diags.append(Diagnostic(0, 0, code, f"{me.field}: {me.message}"))
    # watermark vs present ids
    present: List[int] = []
    for leaf in doc.exec_leaves:
        suf = S.suffix_of(leaf.ident)
        if suf is not None:
            present.append(suf)
    wm_raw = doc.meta_fields.get(S.META_WATERMARK)
    wm = None
    if wm_raw is not None:
        try:
            wm = int(wm_raw)
        except ValueError:
            diags.append(
                Diagnostic(0, 0, C_WATERMARK, "Highest E allocated must be an integer")
            )
    werr = S.watermark_error(wm, present)
    if werr:
        diags.append(Diagnostic(0, 0, C_WATERMARK, werr))
    return diags


def _kind(doc: ParsedDoc) -> str:
    return doc.meta_fields.get("Kind", S.KIND_CHILD)


def check_headings(doc: ParsedDoc) -> List[Diagnostic]:
    diags: List[Diagnostic] = []
    kind = _kind(doc)
    expected = S.H2_ORDER_BY_KIND.get(kind)
    if expected is None:
        return diags  # unknown kind already flagged in metadata
    titles = [h.title for h in doc.h2]
    # presence + uniqueness
    for want in expected:
        cnt = titles.count(want)
        if cnt == 0:
            diags.append(
                Diagnostic(0, 0, C_HEADING_MISSING, f"required H2 missing: {want}")
            )
        elif cnt > 1:
            line = next((h.line for h in doc.h2 if h.title == want), 0)
            diags.append(Diagnostic(line, 1, C_HEADING_DUP, f"duplicate H2: {want}"))
    # order: the subsequence of expected headings must appear in the expected order
    present_expected = [t for t in titles if t in expected]
    if present_expected != [t for t in expected if t in titles]:
        diags.append(
            Diagnostic(
                0,
                0,
                C_HEADING_ORDER,
                f"H2 headings are out of canonical order for kind {kind}",
            )
        )
    # execution immediately after Goal; validation immediately before gate
    if S.H_GOAL in titles and S.H_EXECUTION in titles:
        gi = titles.index(S.H_GOAL)
        if not (gi + 1 < len(titles) and titles[gi + 1] == S.H_EXECUTION):
            line = next((h.line for h in doc.h2 if h.title == S.H_EXECUTION), 0)
            diags.append(
                Diagnostic(
                    line,
                    1,
                    C_EXEC_PLACEMENT,
                    "execution checklist must be the H2 immediately after Goal",
                )
            )
    vtitle = S.VALIDATION_HEADING_BY_KIND.get(kind)
    if vtitle in titles and S.H_APPROVAL_GATE in titles:
        ai = titles.index(S.H_APPROVAL_GATE)
        if not (ai - 1 >= 0 and titles[ai - 1] == vtitle):
            line = next((h.line for h in doc.h2 if h.title == vtitle), 0)
            diags.append(
                Diagnostic(
                    line,
                    1,
                    C_VALID_PLACEMENT,
                    "validation checklist must be the H2 immediately before the approval gate",
                )
            )
    return diags


def check_ids_and_bijection(doc: ParsedDoc) -> List[Diagnostic]:
    diags: List[Diagnostic] = []
    # id family per section + grammar + uniqueness
    e_ids: List[str] = []
    seen_e = set()
    for lf in doc.exec_leaves:
        if lf.kind == "other" or not S.E_ID_STRICT.match(lf.ident):
            diags.append(
                Diagnostic(
                    lf.line,
                    1,
                    C_ID_FAMILY,
                    "execution-section leaf must be a valid E-* item",
                )
            )
            continue
        if lf.ident in seen_e:
            diags.append(
                Diagnostic(
                    lf.line,
                    1,
                    C_ID_GRAMMAR,
                    f"duplicate execution id {lf.ident}",
                )
            )
        seen_e.add(lf.ident)
        e_ids.append(lf.ident)
    v_targets: Dict[str, str] = {}
    seen_v = set()
    for lf in doc.valid_leaves:
        if lf.kind == "other" or not S.V_ID_STRICT.match(lf.ident):
            diags.append(
                Diagnostic(
                    lf.line,
                    1,
                    C_ID_FAMILY,
                    "validation-section leaf must be a valid V-* item",
                )
            )
            continue
        if lf.ident in seen_v:
            diags.append(
                Diagnostic(
                    lf.line,
                    1,
                    C_ID_GRAMMAR,
                    f"duplicate validation id {lf.ident}",
                )
            )
        seen_v.add(lf.ident)
        v_targets[lf.ident] = lf.target
    for err in S.bijection_errors(e_ids, v_targets):
        diags.append(Diagnostic(0, 0, C_BIJECTION, err))
    # dependencies
    edges: Dict[str, List[str]] = {}
    for lf in doc.exec_leaves:
        if lf.kind != "E":
            continue
        dep_raw = lf.fields.get("Depends on", "none")
        deps, derr = S.parse_depends_on(dep_raw)
        if derr:
            diags.append(Diagnostic(lf.line, 1, C_DEPENDS, f"{lf.ident}: {derr}"))
        edges[lf.ident] = deps
    for err in S.dependency_errors(edges):
        diags.append(Diagnostic(0, 0, C_DEPENDS, err))
    return diags


def check_states(doc: ParsedDoc) -> List[Diagnostic]:
    diags: List[Diagnostic] = []
    exec_by_suffix: Dict[Optional[int], str] = {}
    for lf in doc.exec_leaves:
        if lf.kind != "E":
            continue
        state = lf.fields.get("Execution state", "")
        has_note = bool(lf.fields.get("Execution note", "").strip())
        err = S.execution_row_error(state, lf.checked, has_note)
        if err:
            diags.append(Diagnostic(lf.line, 1, C_EXEC_STATE, f"{lf.ident}: {err}"))
        exec_by_suffix[S.suffix_of(lf.ident)] = state
    for lf in doc.valid_leaves:
        if lf.kind != "V":
            continue
        result = lf.fields.get("Result", "")
        observed_nonempty = bool(lf.fields.get("Observed evidence", "").strip())
        err = S.validation_row_error(result, lf.checked, observed_nonempty)
        if err:
            diags.append(Diagnostic(lf.line, 1, C_VALID_STATE, f"{lf.ident}: {err}"))
        # cross-state with the matching E
        ex_state = exec_by_suffix.get(S.suffix_of(lf.ident))
        if ex_state is not None:
            cerr = S.cross_state_error(ex_state, result)
            if cerr:
                diags.append(
                    Diagnostic(lf.line, 1, C_CROSS_STATE, f"{lf.ident}: {cerr}")
                )
    return diags


def check_gate_contract(doc: ParsedDoc) -> List[Diagnostic]:
    """Refuse a plan whose gate prescribes a hand-rolled terminal move (Order dcri4s E-05)."""
    if not doc.gate_lines:
        return []
    gate_text = "\n".join(raw for _, raw in doc.gate_lines)
    if "aw ipd finalize" in gate_text:
        return []
    pattern = r"\bgit\s+mv\b.*?(?:executed/|terminal\s+directory|status:\s*executed)"
    m = re.search(pattern, gate_text, re.IGNORECASE | re.DOTALL)
    if m:
        start_pos = m.start()
        prefix = gate_text[max(0, start_pos - 40) : start_pos].strip()
        if re.search(
            r"\b(?:never(?:\s+with(?:\s+a(?:\s+raw)?)?)?|not|in no case may you)\s*`?$",
            prefix,
            re.IGNORECASE,
        ):
            return []
        line_num = doc.gate_lines[0][0]
        for lno, raw in doc.gate_lines:
            if re.search(r"\bgit\s+mv\b", raw):
                line_num = lno
                break
        return [
            Diagnostic(
                line_num,
                1,
                C_GATE_HAND_ROLLED_MOVE,
                "approval gate must not prescribe a hand-rolled terminal move "
                "(`git mv` to `executed/`); run the transition via `aw ipd finalize` "
                "(or report results and let the runner finalize in a managed lane)",
            )
        ]
    return []


def check_open_questions(doc: ParsedDoc) -> List[Diagnostic]:
    diags: List[Diagnostic] = []
    for oq in doc.open_questions:
        blocking = oq.get("Blocking", "")
        status = oq.get("Status", "")
        has_rationale = bool(oq.get("Resolution or deferral rationale", "").strip())
        has_owner = (
            bool(oq.get("Owner", "").strip())
            and oq.get("Owner", "").strip().lower() != "none"
        )
        err = S.open_question_error(blocking, status, has_rationale, has_owner)
        if err:
            diags.append(
                Diagnostic(
                    int(oq.get("line", "0")),
                    1,
                    C_OQ,
                    "{0}: {1}".format(oq.get("id", "OQ"), err),
                )
            )
        # askme: an UNRESOLVED BLOCKING question is refused at EVERY checkpoint, not only at
        # `pre-execution`. The narrow version was measured insufficient on 2026-09-08: plan `xipfy1`
        # carried `Blocking: yes` / `Status: open` and a default `aw ipd lint` reported CONFORMING, so
        # an agent could author, hand over, and report a plan whose load-bearing question was never
        # put to the human. The question is the author's to ASK (`/askme`), not to carry silently.
        #
        # SCOPED TO `Blocking: yes` DELIBERATELY, on the maintainer's ruling of 2026-09-08 after the
        # alternative was measured: 66 of 103 pending plans carry a NON-blocking open question, which
        # is the normal, healthy state of a plan in progress (a noted minor choice with a stated
        # lean). Firing on those would have declared the repository broken and would have forced an
        # agent to edit other agents' in-flight plans to get its own commit through. Only 14 plans
        # carry a blocking one, and those are exactly the cases where a real decision is being
        # skipped. Widening this to every open question needs a maintainer decision, not a tweak.
        #
        # The pre-execution checkpoint rule below is intentionally NOT removed: it is reached through
        # a different call path (`aw ipd begin`), and GUIDING_PRINCIPLES 6 prefers a redundant gate
        # over a gap when the two fire at different moments.
        elif blocking == "yes" and status == "open":
            diags.append(
                Diagnostic(
                    int(oq.get("line", "0")),
                    1,
                    C_OQ,
                    "{0}: BLOCKING question is still 'open'. Ask the human and record the answer "
                    "(run `/askme`, then set 'Status: resolved' with a rationale). If it does not "
                    "actually block, set 'Blocking: no'.".format(oq.get("id", "OQ")),
                )
            )
    return diags


def check_size(doc: ParsedDoc) -> List[Diagnostic]:
    diags: List[Diagnostic] = []
    e_count = sum(1 for lf in doc.exec_leaves if lf.kind == "E")
    warn = S.size_warning(doc.exec_task_groups, e_count)
    sa = doc.size_assessment
    if sa is not None and sa not in S.SIZE_ASSESSMENTS:
        diags.append(
            Diagnostic(
                0, 0, C_SIZE, "Size assessment must be 'standard' or 'exception'"
            )
        )
    if warn and sa == "standard":
        diags.append(
            Diagnostic(
                0,
                0,
                C_SIZE,
                "size thresholds exceeded but Size assessment is 'standard' (needs 'exception' + rationale)",
            )
        )
    return diags


def check_density(doc: ParsedDoc) -> List[Diagnostic]:
    """Advisory density check (spec Section 8.1, Order 07).

    Flags E-items whose action text appears to bundle multiple independent deliverables
    or test-surfaces. Does NOT affect the conformance disposition.
    """
    advisories: List[Diagnostic] = []
    for lf in doc.exec_leaves:
        if lf.kind != "E":
            continue
        reason = S.e_item_density_advisory(lf.text)
        if reason:
            advisories.append(
                Diagnostic(
                    lf.line,
                    1,
                    C_SIZE_DENSITY,
                    f"{lf.ident}: action text may bundle multiple concerns ({reason})",
                )
            )
    return advisories


# --------------------------------------------------------------------------------------
# Citation anchors (citeanchor `mzc019`; spec Section 10.2) - ADVISORY, date-gated
# --------------------------------------------------------------------------------------
#
# WHAT THIS RULE IS FOR. A citation of the form `somefile.py:897-905` is true only at the instant it
# is written, and the plan pipeline is deliberately longer than that instant: a plan is authored,
# reviewed (often twice), approved, and executed days later while other agents commit to the same
# files. By execution time the offset names different code.
#
# THE FAILURE IS SILENT MISDIRECTION, NOT A DANGLING POINTER, and that is why this rule keys on the
# anchor's FORM and never on whether the target resolves. A drifted offset almost never points at
# nothing; it points at OTHER, VALID, PLAUSIBLE-LOOKING code, so the executor reads the wrong
# construct and believes the plan described it. Measured on plan `216rgg` before it executed: its
# cross-type citation landed on a `seen_ids` dictionary initialization instead of the branch it
# described, and its `doctor.py` citation landed on a BLANK LINE. Scanning the same corpus for
# PROVABLY dead citations found almost none, which is the symptom restated rather than reassurance.
#
# REVIEW CANNOT FIX THIS, which is why the check exists at all: `216rgg` was reviewed twice and its
# own history records that every line number in it was measured at HEAD. That was TRUE when written.
#
# THE NAIVE FORM OF THIS TEST IS PROVABLY USELESS, and avoiding it is the substance of the
# implementation below. "Is there a backticked token on the same line?" was MEASURED over the whole
# pending corpus at HEAD 55324de2: only 3 of 2304 structural citations (0%) would flag, because a
# citation is nearly always written in backticks itself and a file path is itself a dotted token. That
# form cannot even flag the `216rgg` cell this rule was written from. So the candidate-anchor set
# EXCLUDES (a) the matched citation text, (b) a backticked bare file path, and (c) a backticked bare
# line range (the filename-less continuation form, e.g. `:906-915`). What remains and counts as
# durable is a QUALIFIED IDENTIFIER (`module.function`, `Class.method`) or a QUOTED CONTENT STRING.
# Measured with that correction on the same corpus: 1078 of 2304 (47%) flag, the `216rgg` Findings-row
# cell and its prose sentence BOTH flag, and its E-01 bullet correctly does NOT (it names
# `check_engine.check_collisions` beside the offset, the compliant (a)+(c) form).
#
# A MARKDOWN TABLE ROW IS JUDGED PER CELL, not per line, so one column's symbol cannot vouch for a
# bare offset several columns away. That is the same "symbol nearby" fallacy measured at 0% above,
# just at row scale; the `216rgg` Findings row is the concrete case (its Evidence cell carries
# `check_collisions` while its Location cell carries only the bare offset).
#
# ADVISORY ONLY, NEVER GATING, for a reason this repository has already paid for: `check.setid-collision`
# shipped at `error` for behavior later ruled CORRECT, and backlog `gjadwm` records that a gate which
# false-positives trains agents to bypass it. A citation-form heuristic over prose WILL have false
# positives. Note `ipd_lint` does not call `artifact_core.drift_exit_code`; it reaches the same outcome
# by carrying a finding in `LintResult.advisories`, which never flips the disposition. Emit there.
_CITATION_SRC_EXT = (
    r"(?:py|md|json|jsonl|toml|sh|yml|yaml|txt|cfg|ini|lock|html|css|js|ts|tsx|rs|go"
    r"|c|h|cpp|java|sql)"
)
#: A `path/to/file.ext:123` or `path/to/file.ext:123-456` citation.
_CITATION_RE = re.compile(r"\b[\w./-]*[\w-]\." + _CITATION_SRC_EXT + r":\d+(?:-\d+)?\b")
_BACKTICK_TOKEN_RE = re.compile(r"`([^`]+)`")
#: A backticked BARE line range (`:906-915`) - the filename-less continuation form. NOT an anchor.
_BARE_LINE_RANGE_RE = re.compile(r"^:\d+(?:-\d+)?$")
#: A backticked BARE file path (`check_engine.py`) with no offset and no symbol. NOT an anchor: it
#: names the file the citation already named.
_BARE_PATH_RE = re.compile(r"^[\w./-]*[\w-]\." + _CITATION_SRC_EXT + r"$")
#: A QUALIFIED identifier (`module.function`, `Class.method`, `pkg.mod.CONST`). IS an anchor.
_QUALIFIED_IDENT_RE = re.compile(r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+$")

#: citeanchor `mzc019` E-04. The authoring-date cutover: a plan dated BEFORE this is SUPPRESSED.
#:
#: The DATE MECHANISM is borrowed from `check_engine`'s durable-carrier rule (a module-level compact
#: `YYYYMMDD` constant plus a per-plan helper). Its SEVERITY LADDER is deliberately NOT borrowed.
#: `carrier_severity_for_plan` DOWNGRADES a pre-cutover plan to `info` and still EMITS the finding;
#: this rule is `info` in BOTH tiers, so a downgrade would be a no-op and the gate must SUPPRESS
#: instead - a pre-cutover plan yields NOTHING AT ALL. Do not "restore parity" with the carrier rule:
#: that would reintroduce roughly a thousand advisories on plans nobody is editing, and a diagnostic
#: that fires mostly on untouchable history is one every reader learns to skip, destroying the value
#: of the one finding that matters.
#:
#: SET STRICTLY AFTER THE NEWEST PLAN DATE PRESENT AT EXECUTION TIME, re-measured rather than
#: inherited. Measured over the 89 pending plans at HEAD 55324de2: the newest `- Date:` is
#: 2026-09-20, so `20260919` (the carrier constant's value, which this plan's review suggested) would
#: have fired on plans authored after that review. A later re-measurement must move this forward the
#: same way rather than assuming this value still holds.
#:
#: RE-MEASURED 2026-09-22 AND MOVED FORWARD, exactly as the paragraph above instructs. Five plans were
#: authored on 2026-09-21 (the orchestrator-coverage children `k311gw`, `04vf1h`, `p9j6c0`, `40it5e`
#: plus that day's other work), so the newest pending `- Date:` became `20260921` - EQUAL to this
#: constant, and the rule applies at `>=`, so the advisory was one day from firing on plans authored
#: before it existed. `tests/test_ipd_lint.py` asserts the constant is STRICTLY GREATER than the
#: newest plan date for that reason and caught it. Moved to `20260923` rather than `20260922` so a
#: plan authored later today does not immediately re-trip the same guard.
CITATION_ANCHOR_CUTOVER_DATE = "20260923"  # compact YYYYMMDD

_CITATION_PLAN_DATE_RE = re.compile(r"(?m)^- Date:[ \t]*(\d{4})-(\d{2})-(\d{2})[ \t]*$")


def _citation_anchor_applies(doc: ParsedDoc) -> bool:
    """True when this plan is POST-cutover and therefore subject to the citation-anchor advisory.

    A plan with NO parseable `- Date:` is treated as PRE-cutover (suppressed). That direction is
    copied from the carrier precedent and for its stated reason: `IPD-M101` already owns the
    missing-`Date` complaint, so this rule must not invent a second consequence for the same defect.
    """
    raw = doc.meta_fields.get("Date")
    if not raw:
        return False
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", str(raw).strip())
    if m is None:
        return False
    return "{0}{1}{2}".format(*m.groups()) >= CITATION_ANCHOR_CUTOVER_DATE


def _citation_units(line: str) -> List[str]:
    """The text spans a citation is judged against: a table row's CELLS, else the whole line."""
    stripped = line.strip()
    if stripped.startswith("|"):
        return stripped.strip("|").split("|")
    return [line]


def _has_durable_anchor(unit: str) -> bool:
    """True when ``unit`` carries a durable anchor BESIDE its citation (spec Section 10.2 (a)/(b))."""
    for token in _BACKTICK_TOKEN_RE.findall(unit):
        tok = token.strip()
        if not tok:
            continue
        if _CITATION_RE.search(tok):
            continue  # the citation itself is not evidence that the citation is anchored
        if _BARE_LINE_RANGE_RE.match(tok):
            continue  # `:906-915` - a second offset, not an anchor
        if _BARE_PATH_RE.match(tok):
            continue  # `check_engine.py` - names the file the citation already named
        if re.search(r"\s", tok):
            return True  # a quoted content string (Section 10.2 (b))
        if _QUALIFIED_IDENT_RE.match(tok):
            return True  # `module.function` / `Class.method` (Section 10.2 (a))
    return False


def check_citation_anchors(doc: ParsedDoc, text: str) -> List[Diagnostic]:
    """Advisory: a code citation with no durable anchor beside it (spec Section 10.2, `IPD-C801`).

    Returns ADVISORY diagnostics only; the caller must place them in ``LintResult.advisories`` so the
    conformance disposition and process exit status are untouched.

    REUSES ``_structural_lines`` rather than re-implementing fence detection, which is what makes a
    citation inside a fenced block, an indented pasted traceback, YAML front matter, or a block quote
    exempt for free. Re-implementing it is how a rule starts flagging pasted diagnostics, whose
    offsets are the FACT being reported (the Section 10.2 line-as-subject exception).

    KNOWN AND ACCEPTED LIMIT, recorded so it is not later filed as a bug: the helper's unit is a LINE,
    so a multi-line E-item whose symbol sits on the first line and whose offset sits on an indented
    continuation line is judged per line, and the continuation flags. That is a false positive. It is
    precisely why this rule is `info` and must not be promoted to a gating severity without the
    measurement the plan's deferred row demands.
    """
    if not _citation_anchor_applies(doc):
        return []
    out: List[Diagnostic] = []
    for lineno, line in _structural_lines(text):
        for unit in _citation_units(line):
            if not _CITATION_RE.search(unit):
                continue
            if _has_durable_anchor(unit):
                continue
            for m in _CITATION_RE.finditer(unit):
                out.append(
                    Diagnostic(
                        lineno,
                        1,
                        C_CITATION_ANCHOR,
                        "citation '{0}' has no durable anchor: name the SYMBOL "
                        "(`module.function`) or quote a unique content string, and keep the line "
                        "number only as a trailing convenience. A bare offset expires before this "
                        "plan executes and then misdirects the executor to unrelated valid code "
                        "(spec ipd-structure-and-linting Section 10.2).".format(
                            m.group(0)
                        ),
                    )
                )
    return out


# rdattest: `- Readiness:` is a REVIEW OUTPUT, not an authoring field, and this rule is the only thing
# that says so mechanically.
#
# THE FAILURE THIS EXISTS TO STOP, observed 2026-09-06 and committed before the maintainer caught it:
# an agent authoring a fresh plan Set wrote `- Readiness: go-pending-approval` into all four plans at
# AUTHORING TIME, having never run a review. `plan_readiness.is_plan_review_approved` consults the
# FIELD FIRST and only falls back to parsing the workflow history when the field is ABSENT, so those
# four plans asserted "review has cleared this plan" and the predicate returned True for every one of
# them. Under `aw <host> run ... --full-auto` that predicate is what flips a reviewed plan to approved
# and its queue action to `execute` in the same run (the host drivers' auto-approve sites, which call
# the shared predicate), so a hand-typed field could have carried unreviewed plans into execution.
# NOTE this module deliberately does NOT name or import any driver module: an anti-divergence guard
# (`tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests`) requires the shared rule
# modules to stay ignorant of the runner, and it correctly caught an earlier draft of this comment.
#
# WHY THE EXISTING CHECKS DID NOT CATCH IT: `ipd_schema.validate_metadata` validates the VOCABULARY
# (an out-of-enum value is IPD-M104) and `aw ipd scaffold` correctly omits the field entirely, so a
# fabricated but well-spelled value passed every gate. The vocabulary was policed; the PROVENANCE was
# not. `plan-review.md` calls the field "REQUIRED output of the review", but that instruction only
# reaches an agent that is running a review, never one that is authoring.
#
# THE RULE: if `- Readiness:` is present, the plan's own `## Workflow history` must contain evidence
# that a review produced it. Absence of the field is SILENT and remains the correct authoring state
# (the field is optional, and absence makes the predicate fall back to prose and fail closed).
#
# DELIBERATELY EVIDENCE-BASED, NOT AUTHORSHIP-BASED: it would be tempting to key this on `Status`
# (e.g. "only a reviewed plan may carry Readiness"), but a review legitimately writes the field in the
# SAME pass that sets `reviewed`, and `plan-review-long` can leave a plan at `to-review` with a
# recorded NO-GO readiness. Keying on the history evidence admits both while still refusing a value
# with nothing behind it.
_REVIEW_EVIDENCE_RE = re.compile(
    r"(?i)\b(?:/?plan-review(?:-long)?\b|APPROVE\b|NO-GO\b|REJECT\b)"
)


def check_readiness_attestation(doc: ParsedDoc) -> List[Diagnostic]:
    """Refuse a `- Readiness:` value that no review in the plan's history accounts for (rdattest)."""
    raw = doc.meta_fields.get(S.META_READINESS)
    if raw is None or not str(raw).strip():
        # Absent is the correct authoring state and is silent, by design.
        return []
    history = "\n".join(line for _lineno, line in doc.history_lines)
    if _REVIEW_EVIDENCE_RE.search(history):
        return []
    return [
        Diagnostic(
            0,
            0,
            C_READINESS_UNATTESTED,
            f"{S.META_READINESS}: '{str(raw).strip()}' is a REVIEW OUTPUT but no review verdict "
            "appears in '## Workflow history'. Do not write this field when authoring: the "
            "auto-approve gate reads it BEFORE the history, so a hand-written value asserts that a "
            "review cleared the plan when none has. Remove the line and let /plan-review write it.",
        )
    ]


def check_checkpoint(
    doc: ParsedDoc, checkpoint: str, directory: Optional[str]
) -> List[Diagnostic]:
    """Checkpoint-specific state requirements (spec Section 9.2)."""
    diags: List[Diagnostic] = []
    status = doc.meta_fields.get("Status", "")
    if not S.checkpoint_allows_status(checkpoint, status, directory):
        diags.append(
            Diagnostic(
                0,
                0,
                C_CHECKPOINT,
                f"status '{status}' is incompatible with checkpoint '{checkpoint}'",
            )
        )
    if checkpoint == "pre-execution":
        for oq in doc.open_questions:
            if oq.get("Blocking") == "yes" and oq.get("Status") == "open":
                diags.append(
                    Diagnostic(
                        int(oq.get("line", "0")),
                        1,
                        C_CHECKPOINT,
                        "{0}: unresolved blocking question at pre-execution".format(
                            oq.get("id", "OQ")
                        ),
                    )
                )
    if checkpoint == "pre-transition":
        for lf in doc.exec_leaves:
            if lf.kind == "E" and lf.fields.get("Execution state") != "performed":
                diags.append(
                    Diagnostic(
                        lf.line,
                        1,
                        C_CHECKPOINT,
                        f"{lf.ident}: not 'performed' at pre-transition",
                    )
                )
        for lf in doc.valid_leaves:
            if lf.kind == "V":
                if lf.fields.get("Result") != "pass":
                    diags.append(
                        Diagnostic(
                            lf.line,
                            1,
                            C_CHECKPOINT,
                            f"{lf.ident}: not 'pass' at pre-transition",
                        )
                    )
                if not lf.fields.get("Observed evidence", "").strip():
                    diags.append(
                        Diagnostic(
                            lf.line,
                            1,
                            C_CHECKPOINT,
                            f"{lf.ident}: empty Observed evidence at pre-transition",
                        )
                    )
    if checkpoint == "post-transition":
        if status == "executed":
            has_executed = False
            for lineno, line_text in doc.history_lines:
                m = _HISTORY_LINE_RE.match(line_text.strip())
                if m and m.group(1).rstrip(":").lower() == "executed":
                    has_executed = True
                    break
            if not has_executed:
                diags.append(
                    Diagnostic(
                        0,
                        0,
                        C_EXEC_HISTORY,
                        "plan with 'Status: executed' must carry an 'executed' ## Workflow history entry at post-transition",
                    )
                )
            # ipdgates Order wezhxg: the NEWEST terminal `executed` entry (the one this transition
            # wrote) MUST carry a non-generic actor AND a nonempty summary. Applied FORWARD-ONLY:
            # grandfather the existing executed tree by keying on Order 02's cutoff marker - a plan
            # WITHOUT a real `Scope-Paths` allowlist (absent, or `Scope-Paths: grandfathered`) is
            # pre-cutoff and is NOT subject to the strict attribution rule (OQ-01).
            diags.extend(_check_terminal_attribution(doc))
    return diags


def _is_grandfathered_for_attribution(doc: ParsedDoc) -> bool:
    """True when the plan is PRE-CUTOFF for the Order-wezhxg attribution lint (grandfathered).

    Consumes Order oorry1's cutoff marker: a plan with NO real `Scope-Paths` allowlist (the field is
    absent, or its value is the reserved `grandfathered` sentinel) predates the machinery and is not
    subject to the strict actor/summary rule. A plan declaring a REAL allowlist is post-cutoff.
    """
    sp = doc.meta_fields.get(S.META_SCOPE_PATHS)
    if not sp:
        return True
    _paths, is_grandfathered, _errs = S.parse_scope_paths(sp)
    return is_grandfathered


def _newest_executed_history(doc: ParsedDoc):
    """Return the parsed (status, actor, msg) of the NEWEST `executed` history entry, or None.

    History entries are appended newest-first (a new line is inserted right after the H2), so the
    FIRST `executed` line encountered scanning top-down is the newest one - the entry this transition
    wrote.
    """
    for _lineno, line_text in doc.history_lines:
        m = _HISTORY_ATTRIB_RE.match(line_text.strip())
        if m and m.group("status").rstrip(":").lower() == "executed":
            return m.group("actor").strip(), m.group("msg").strip()
        # A bare `executed` line without the (actor): msg shape also counts as the newest executed
        # entry but with an empty actor/msg (so the attribution rule flags it).
        bare = _HISTORY_LINE_RE.match(line_text.strip())
        if bare and bare.group(1).rstrip(":").lower() == "executed":
            return "", ""
    return None


def _check_terminal_attribution(doc: ParsedDoc) -> List[Diagnostic]:
    """Reject a generic/empty actor or empty summary on the newest `executed` entry (Order wezhxg)."""
    if _is_grandfathered_for_attribution(doc):
        return []  # pre-cutoff: do not retroactively fail the grandfathered executed tree
    newest = _newest_executed_history(doc)
    if newest is None:
        return []  # the missing-executed-entry case is already covered by C_EXEC_HISTORY
    actor, msg = newest
    out: List[Diagnostic] = []
    if not actor or actor in _GENERIC_ACTORS:
        out.append(
            Diagnostic(
                0,
                0,
                C_EXEC_ATTRIBUTION,
                "the newest 'executed' history entry must name a non-generic actor/model "
                "(the machine-default 'aw set' / an empty actor is rejected); run the transition "
                "via `aw ipd finalize --actor <agent/model>`",
            )
        )
    if not msg:
        out.append(
            Diagnostic(
                0,
                0,
                C_EXEC_ATTRIBUTION,
                "the newest 'executed' history entry must carry a nonempty summary",
            )
        )
    return out


def _scope_paths_gate_applies(checkpoint: str, status: str) -> bool:
    """True when the conditional Scope-Paths requirement is in force (Order oorry1).

    It fires at the `pre-execution` checkpoint AND for any plan whose persisted `Status` is at the
    ready-to-execute tier (`approved`/`auto-approved`), so an approved plan cannot slip past the
    gate regardless of the requested checkpoint. It does NOT fire at `author`/`review-finalize`
    (drafting/review) so a fresh draft and every un-stamped pending plan still lint clean until
    they reach the gate.
    """
    return checkpoint == "pre-execution" or status in S.READY_TO_EXECUTE


def check_scope_paths(
    doc: ParsedDoc, checkpoint: str, directory: Optional[str]
) -> Tuple[List[Diagnostic], List[Diagnostic]]:
    """Conditional Scope-Paths enforcement (Order oorry1). Returns (blocking, advisory).

    At the ready-to-execute gate (Section 9.2): a plan with NO `Scope-Paths` field is a BLOCKING
    error; a plan carrying `Scope-Paths: grandfathered` yields only an ADVISORY diagnostic
    (non-blocking); a plan declaring a REAL allowlist is validated against the Section 4.5 grammar
    (malformed = BLOCKING). Terminal-dir records never reach this function (they short-circuit to
    the `legacy` disposition in `lint_text`), so grandfathered terminal plans are unaffected.
    """
    blocking: List[Diagnostic] = []
    advisory: List[Diagnostic] = []
    status = doc.meta_fields.get("Status", "")
    if not _scope_paths_gate_applies(checkpoint, status):
        return blocking, advisory
    if S.META_SCOPE_PATHS not in doc.meta_fields:
        blocking.append(
            Diagnostic(
                0,
                0,
                C_SCOPE_PATHS,
                "Scope-Paths is required at the ready-to-execute gate: declare a comma-separated "
                "allowlist of repo-relative paths/pathspecs, or the sentinel 'grandfathered'",
            )
        )
        return blocking, advisory
    value = doc.meta_fields.get(S.META_SCOPE_PATHS, "")
    _paths, is_grandfathered, errors = S.parse_scope_paths(value)
    if is_grandfathered:
        advisory.append(
            Diagnostic(
                0,
                0,
                C_SCOPE_PATHS,
                "Scope-Paths: grandfathered is advisory-satisfied (pre-cutoff plan); a re-reviewed "
                "or new plan should declare a real path allowlist",
            )
        )
        return blocking, advisory
    for err in errors:
        blocking.append(Diagnostic(0, 0, C_SCOPE_PATHS, "Scope-Paths: {0}".format(err)))
    return blocking, advisory


# ipddeps Order ovbnyq (spec 25kzda 2.9-2.11): phased cross-IPD Item-Dependencies enforcement.
# lint_text is PURE, so it only performs the SYNTAX-level checks (missing / unresolved / malformed)
# here; the RESOLUTION-level checks (dangling / ambiguous / cycle) need the repo and are added in
# lint_file via the ONE shared check_engine evaluator. The rule IDs are the shared
# `check.ipd-dependency-*` family so every surface reports the same rule.
_DEP_BLOCKING_CHECKPOINTS = frozenset(
    ("review-finalize", "pre-execution", "pre-transition")
)


def check_item_dependencies(
    doc: ParsedDoc, checkpoint: str, directory: Optional[str]
) -> Tuple[List[Diagnostic], List[Diagnostic]]:
    """Pure SYNTAX-level Item-Dependencies enforcement. Returns (blocking, advisory).

    At `author`: a valid statement passes; a missing statement or the `unresolved` sentinel is
    ADVISORY (an honest not-ready draft); a malformed statement is always BLOCKING. At
    review-finalize/pre-execution/pre-transition: missing / `unresolved` / malformed are BLOCKING.
    Resolution (dangling/ambiguous/cycle) is added by lint_file (needs the repo).
    """
    blocking: List[Diagnostic] = []
    advisory: List[Diagnostic] = []
    is_blocking_phase = checkpoint in _DEP_BLOCKING_CHECKPOINTS
    raw = doc.meta_fields.get(S.META_ITEM_DEPENDENCIES)
    if raw is None:
        # MISSING-statement mandatoriness is CUTOVER-conditional (spec 2.11) and lint_text is PURE
        # (no repo -> cannot know the cutover). Emitting a finding here would either mass-fail /
        # pollute the advisory channel for the entire pre-cutover corpus. So the pure lint emits
        # NOTHING for a missing statement; the repo-aware, cutover-gated MISSING enforcement (which
        # blocks only a POST-CUTOVER plan at a blocking phase) is applied in lint_file via the shared
        # evaluator. Pre-cutover / no-cutover plans are thus grandfathered and never mass-failed.
        return blocking, advisory
    value = raw.strip()
    if value == S.ITEM_DEPENDENCIES_UNRESOLVED:
        diag = Diagnostic(
            0,
            0,
            S.RULE_IPD_DEP_UNRESOLVED,
            "Item-Dependencies is still the `unresolved` scaffold sentinel; resolve it before "
            "review-readiness/execution",
        )
        (blocking if is_blocking_phase else advisory).append(diag)
        return blocking, advisory
    _edges, _ready, err = S.parse_item_dependencies(value)
    if err:
        # malformed is always blocking (an invalid statement is never acceptable)
        blocking.append(
            Diagnostic(0, 0, S.RULE_IPD_DEP_MALFORMED, f"Item-Dependencies: {err}")
        )
    return blocking, advisory


# --------------------------------------------------------------------------------------
# The typed child-tracking row (spec `r07vma` R1a/R3/R7/R8), orchtyped `dpdyed`
# --------------------------------------------------------------------------------------
#
# THIS IS THE ONE IMPLEMENTATION OF THE RULE (R3). `/plan-review` (child `r3xk1f`) and both runners
# (child `0xmk4e`) call :func:`orchestrator_row_conformance`; neither may carry a second regex or a
# "cheap version", which is the drift R3 exists to prevent.
#
# WHY IT LIVES HERE rather than in a new shared module (this plan's OQ-01, resolved from repository
# evidence). `runner_shared` keeps EXACTLY `{render_stream, runner_profiles}` as its module-level
# first-party imports and `tests/test_orchestrator_probe_cache.py::
# test_no_new_module_level_first_party_import_in_runner_shared` asserts that by SET EQUALITY, so the
# import a new module would need there breaks a shipped test. `runner_shared` already reaches
# `ipd_lint` through function-local imports in four places, which is how a runner reaches this.
#
# EVERY FIRST-PARTY IMPORT THIS SECTION NEEDS IS FUNCTION-LOCAL, AND THAT IS REQUIRED RATHER THAN
# STYLISTIC: `ipd_set_plan` imports `ipd_lint` AT MODULE LEVEL, so a module-level import of it here
# would close an import cycle. The established precedent in this file is `_name_conformant`, which
# imports `check_engine` in its body for the same reason.

#: The machine reasons a row can be refused for. A consumer routes on these; humans read `message`.
ORCH_ROW_NOT_TYPED = "not-a-typed-child-tracking-row"
ORCH_ROW_CHILD_UNKNOWN = "child-id6-is-not-a-row-of-this-orchestrators-child-table"
ORCH_ROW_STATUS_UNKNOWN = "status-is-outside-the-plan-status-vocabulary"
ORCH_ROW_NO_DEPENDS = "missing-the-depends-on-edge"
ORCH_ROW_TABLE_UNUSABLE = "child-table-cannot-resolve-a-child-id6"

#: The THREE CONTENT REQUIREMENTS of R7, held as data so the message cannot drift from the rule and
#: so a test can assert the CONTENTS rather than an exact string (which would make every wording
#: improvement a test failure). Spec `r07vma` R7: the refusal states what is wrong and why, forbids
#: satisfying it by deletion, and names BOTH remedies WITHOUT PRESCRIBING either.
ORCH_ROW_INVARIANT = (
    "an Order-0 orchestrator is retired PROGRAMMATICALLY, with the pre-transition E-*/V-* checkpoint "
    "deliberately skipped, so a step parked on a parent is performed by NOBODY and is marked complete "
    "having never run"
)
ORCH_ROW_NO_DELETION = (
    "DELETING the item is NOT an acceptable fix: the checklist is what makes a Set execute completely "
    "and in order when it is run BY HAND, so deleting it causes the lost work this rule prevents"
)
ORCH_ROW_REMEDIES = (
    "two remedies are legitimate and this rule does not prescribe either: MOVE the step into a child "
    "plan whose `- Item-Dependencies:` put it in the right order, OR REMOVE it because a child "
    "already covers it (which is removal for redundancy, not deletion to silence this rule)"
)
#: The canonical form, rendered from the same grammar the check enforces, so the instruction an author
#: reads and the rule that refuses them have ONE source (spec OQ-01's proposed direction, partially).
ORCH_ROW_CANONICAL = "- [ ] E-NN CONFIRM <child-id6> REACHED <status>"


class OrchestratorRow(NamedTuple):
    """One orchestrator checklist row, with its three typed fields or its refusal.

    PER-ROW DETAIL RATHER THAN A BARE BOOL is required by R8 (a consumer reports EVERY finding, not
    the first) and by R3: children `r3xk1f` and `0xmk4e` render their own output from these fields, so
    a bool would force each to re-derive the rule.
    """

    line: int  # 1-based line of the row
    ident: str  # "E-NN" when the row parses as an E item, else ""
    row: str  # the row as written (reconstructed canonical single line)
    child_id6: str  # typed field 1, "" when the row did not parse
    status: str  # typed field 2, "" when the row did not parse
    depends_on: str  # typed field 3 (the `Depends on:` edge), "" when absent
    conforming: bool
    reason: str  # one of the ORCH_ROW_* reasons, "" when conforming
    message: str  # the rendered R7 refusal, "" when conforming


class OrchestratorRowResult(NamedTuple):
    """The verdict for a whole orchestrator: every row, plus any table-level cause."""

    applies: bool  # False for a `Kind: child` plan (the rule is orchestrator-only)
    conforming: bool
    rows: Tuple[OrchestratorRow, ...]
    table_reason: str  # why the child table could not resolve an id6 ("" when it could)
    declared_orders: Tuple[str, ...]  # the Order tokens `parse_child_table` resolved

    @property
    def findings(self) -> Tuple[OrchestratorRow, ...]:
        return tuple(r for r in self.rows if not r.conforming)


def render_orchestrator_row_refusal(
    *, row: str, ident: str, reason: str, detail: str
) -> str:
    """Render the R7 refusal for one row. The ONLY place this message is composed."""
    where = "{0} ".format(ident) if ident else ""
    return (
        "{where}is not a typed child-tracking row ({reason}): {detail}. "
        "Write it as `{canonical}`. WHY: {invariant}. {no_deletion}. FIX: {remedies}. "
        "Row as written: {row!r}"
    ).format(
        where=where,
        reason=reason,
        detail=detail,
        canonical=ORCH_ROW_CANONICAL,
        invariant=ORCH_ROW_INVARIANT,
        no_deletion=ORCH_ROW_NO_DELETION,
        remedies=ORCH_ROW_REMEDIES,
        row=row,
    )


def _child_id6_index(text: str) -> Tuple[FrozenSet[str], str]:
    """The id6s an orchestrator's own child table declares, and why it could not be read.

    THE ID CELLS COME FROM ``runner_shared.child_table_rows``, which is ALREADY the shared row-walk
    behind the probe cache and ``parse_declared_child_orders``; consuming it is what R3 requires
    rather than a second table scanner. ``ipd_set_plan.parse_child_table`` deliberately supplies NO
    id6 (its result fields are exactly ``('rows','reason')`` and ``order_to_id`` is an INPUT), so it
    is consumed by the caller for the ORDER GRAPH and its refusal ``reason`` only.

    SIX OF TWELVE LIVE ORCHESTRATORS DECLARE NO ``Id`` COLUMN AT ALL (measured 2026-09-22:
    ``5e4sb6``, ``ao1rb7``, ``a5wdne``, ``tb63qv``, ``2xz59a``, ``s0gnha`` use
    ``| Order | File | ... |``). Such a table cannot resolve a child id6, which is an explicit
    REFUSAL naming the missing column, never a silent pass and never a crash.

    ONLY TWO CELL SHAPES RESOLVE, AND THE NARROWNESS IS A MEASURED CORRECTION rather than caution.
    A cell resolves when a BACKTICKED token is a valid id6, or when the WHOLE cell is one; both shapes
    are live (measured 2026-09-22: ``yeh7gc`` writes bare ``r2i1b1`` while every other table writes
    ``` `dpdyed` ``` , sometimes followed by prose as in
    ``` `1bdxcp` (authored as Order 02 before the placement row existed; runs THIRD) ```).
    SCANNING THE CELL FOR ANY ``\\b[0-9a-z]{6}\\b`` WAS TRIED FIRST AND IS WRONG: an id6 is
    indistinguishable from an ordinary six-letter English word, and the live prose cell
    ``UNAUTHORED, must be written before this Set runs`` resolves to ``before`` under that rule. That
    is not a cosmetic miss, it is a FORGED reference: the cell exists precisely to say the child is
    unauthored, so accepting it would let a typed row claim to track a child nobody has written.
    Validation of this function caught it, which is why the narrow rule is stated here with the reason.
    """
    from agent_workflows import artifact_core as _core
    from agent_workflows import runner_shared as _rs

    rows = _rs.child_table_rows(text)
    if not rows:
        return frozenset(), "no readable `## {0}` table".format(S.H_CHILD_IPDS)
    header_idx = None
    id_idx = None
    for i, cells in enumerate(rows):
        lowered = [c.strip().strip("`").strip().lower() for c in cells]
        if "order" in lowered:
            header_idx = i
            if "id" in lowered:
                id_idx = lowered.index("id")
            break
    if header_idx is None:
        return frozenset(), "child table has no recognizable `Order` header row"
    if id_idx is None:
        return frozenset(), (
            "child table declares no `Id` column (header: {0!r}), so no row can name a child id6; "
            "add the column before a typed row can resolve".format(
                " | ".join(c.strip() for c in rows[header_idx])
            )
        )
    found = set()
    for cells in rows[header_idx + 1 :]:
        if id_idx >= len(cells):
            continue
        cell = cells[id_idx]
        candidates = [t.strip() for t in _BACKTICK_TOKEN_RE.findall(cell)]
        candidates.append(cell.strip())
        for cand in candidates:
            if _core.is_valid_id6(cand):
                found.add(cand)
                break
    if not found:
        return frozenset(), (
            "child table has an `Id` column but no cell in it resolves to an id6"
        )
    return frozenset(found), ""


def orchestrator_row_conformance(
    text: str, *, doc: Optional[ParsedDoc] = None
) -> OrchestratorRowResult:
    """THE conformance rule for an orchestrator's typed child-tracking rows (R1a, R3).

    Returns a per-ROW verdict plus an overall one. A `Kind: child` plan yields ``applies=False`` and
    is reported conforming, because the rule is about an Order-0 parent's checklist and nothing else.

    KIND IS READ FROM ``doc.meta_fields``, which ``parse`` bounds to the metadata region, so a plan
    QUOTING `- Kind: orchestrator` in its prose is not misclassified.

    ROWS COME FROM ``doc.exec_leaves``, which ``parse`` builds from ``_structural_lines``, so a
    conforming-shaped row quoted inside a fenced code block is not seen at all. That is deliberate:
    this plan's own body quotes the grammar template, and a raw-line scan would flag a plan for
    describing the rule.

    AN UNUSABLE CHILD TABLE MEANS CONFORMANCE IS UNKNOWN, NOT SATISFIED, so every row is refused with
    the cause surfaced rather than passing by default.
    """
    if doc is None:
        doc = parse(text)
    if doc.meta_fields.get("Kind") != S.KIND_ORCHESTRATOR:
        return OrchestratorRowResult(False, True, (), "", ())

    from agent_workflows import ipd_set_plan as _isp

    table = _isp.parse_child_table(text)
    declared_orders = tuple(sorted((table.rows or {}).keys(), key=lambda s: int(s)))
    id6s, id_reason = _child_id6_index(text)
    # PRECEDENCE, stated because two live orchestrators hit both causes at once (`5e4sb6`): BOTH are
    # reported when both apply, because each names a different edit an author must make.
    causes = [c for c in (id_reason, table.reason or "") if c]
    table_reason = "; ".join(causes)

    out: List[OrchestratorRow] = []
    for leaf in doc.exec_leaves:
        raw = "- [{0}] {1}".format("x" if leaf.checked else " ", leaf.text).rstrip()
        m = _ORCH_ROW_RE.match(raw)
        ident = leaf.ident or (m.group(1) if m else "")
        depends_on = (leaf.fields.get("Depends on") or "").strip()
        if m is None:
            out.append(
                OrchestratorRow(
                    leaf.line,
                    ident,
                    raw,
                    "",
                    "",
                    depends_on,
                    False,
                    ORCH_ROW_NOT_TYPED,
                    render_orchestrator_row_refusal(
                        row=raw,
                        ident=ident,
                        reason=ORCH_ROW_NOT_TYPED,
                        detail=(
                            "the row does not match the typed grammar exactly (it must carry no "
                            "prose before or after the three fields; free prose belongs on the "
                            "continuation lines)"
                        ),
                    ),
                )
            )
            continue
        child_id6, status = m.group(2), m.group(3)
        reason = ""
        detail = ""
        if table_reason:
            reason = ORCH_ROW_TABLE_UNUSABLE
            detail = (
                "the row names child {0!r} but this orchestrator's own child table cannot resolve a "
                "child id6, so conformance is UNKNOWN rather than satisfied: {1}".format(
                    child_id6, table_reason
                )
            )
        elif child_id6 not in id6s:
            reason = ORCH_ROW_CHILD_UNKNOWN
            detail = "{0!r} is not a row of this orchestrator's own child table (it declares {1})".format(
                child_id6, ", ".join(sorted(id6s)) or "no id6 at all"
            )
        elif status not in S.RECOGNIZED_STATUS:
            reason = ORCH_ROW_STATUS_UNKNOWN
            detail = "{0!r} is not a plan status; the vocabulary is {1}".format(
                status, ", ".join(sorted(S.RECOGNIZED_STATUS))
            )
        elif not depends_on:
            reason = ORCH_ROW_NO_DEPENDS
            detail = (
                "the row supplies no `- Depends on:` edge, which is the third typed field "
                "(write `- Depends on: none` when it has no predecessor)"
            )
        out.append(
            OrchestratorRow(
                leaf.line,
                ident,
                raw,
                child_id6,
                status,
                depends_on,
                not reason,
                reason,
                ""
                if not reason
                else render_orchestrator_row_refusal(
                    row=raw, ident=ident, reason=reason, detail=detail
                ),
            )
        )
    rows = tuple(out)
    return OrchestratorRowResult(
        True,
        all(r.conforming for r in rows),
        rows,
        table_reason,
        declared_orders,
    )


# THE PHASES AT WHICH THE ROW RULE BLOCKS A LINT. Every inclusion and every exclusion below is a
# MEASUREMENT taken 2026-09-22, not a preference, because this constant is where the rule's blast
# radius is decided and a wrong value here either mass-refuses other agents' approved plans or ships a
# rule that never fires.
#
# `review-finalize` IS THE PRIMARY GATE, because it is where R5's bounded repair loop lives. A
# violation found at review costs a revision; found anywhere later it costs a dead end.
#
# `pre-transition` IS INCLUDED because that is the gate `aw ipd finalize` runs, so a HAND-RUN
# orchestrator cannot reach `executed` carrying an untyped row. Note the runner-owned ROLLUP does not
# pass through it (`ipd_lifecycle.ROLLUP_OMITTED_GATES["pre-transition-ev-checkpoint"]`), so this does
# not block a legitimate retirement.
#
# `author` IS EXCLUDED ON A CORPUS MEASUREMENT. The grammar is NEW, so nothing authored before it
# conforms by accident: 11 of the 12 live pending orchestrators do not conform (the twelfth, `d1u4sy`,
# is written in the grammar on purpose) and 6 of the 12 additionally declare no `Id` column at all.
# `aw check plans` sweeps at `author` (`check_engine._IPD_LINT_SWEEP_CHECKPOINT`), so firing here
# would turn `aw ipd lint --all` and `aw check` red on eleven other agents' APPROVED plans before the
# migration that fixes them (child `68uhp0`) has run. Spec `25kzda` 2.5b records where that leads: mass
# false-refusal "would teach agents to DELETE the child checklist", the exact failure R2/R7 prevent.
#
# `post-transition` IS EXCLUDED MECHANICALLY: it runs on the ALREADY-COMMITTED plan, so a finding there
# cannot refuse anything and would only leave a completed transition `committed-incomplete`.
#
# `pre-execution` IS EXCLUDED, AND THIS ONE WAS LEARNED BY BREAKING A TEST RATHER THAN BY REASONING.
# It was included first, on the reasoning that it is the ready-to-execute gate. That made
# `tests/test_orchestrator_retirement.py::TheHumanFacingGateIsUNCHANGED::
# test_the_ordinary_finalize_still_refuses_an_orchestrator` fail, and the failure was CORRECT: that
# test mints a real begin receipt via `ipd_lifecycle.begin`, which gates on the `pre-execution` lint,
# and its fixture is built from the REAL `aw ipd scaffold` skeleton. Measured directly:
# `ipd_authoring.build_skeleton(kind="orchestrator", ...)` emits the row `- [ ] E-01 TODO one
# observable action.` and the prose placeholder `TODO: child IPD table (Order | File | What it does |
# Depends on).` in place of a table, so THE SHIPPED SCAFFOLD IS NOT CONFORMING and `aw ipd begin`
# would refuse every freshly scaffolded orchestrator before its author could fill it in. Blocking at
# `begin` is therefore blocking the wrong end of the lifecycle: an orchestrator is authored, reviewed
# and repaired BEFORE it is begun, and `review-finalize` already covers that. Teaching the scaffold to
# emit a conforming skeleton is the right fix and is spec OQ-01's own proposed direction, but
# `ipd_authoring.py` is NOT in this plan's `- Scope-Paths:`, so it is reported as a finding (backlog
# filed) rather than done here. If a later plan makes the scaffold conforming, adding `pre-execution`
# back becomes a one-line change with this test as its proof.
#
# THE ROUTE FOR THE PRE-EXISTING CORPUS IS CHILD `68uhp0`'s TO CHOOSE (spec criterion 12), and this
# constant does not pre-empt it: a migrate-all route leaves it untouched.
_ORCH_ROW_BLOCKING_CHECKPOINTS = frozenset(("review-finalize", "pre-transition"))


def check_orchestrator_rows(
    doc: ParsedDoc, text: str, checkpoint: str
) -> List[Diagnostic]:
    """`IPD-S407`: every orchestrator checklist row must be a typed child-tracking row.

    Gated on `Kind: orchestrator` (a child plan is untouched) and on the checkpoint (see
    `_ORCH_ROW_BLOCKING_CHECKPOINTS`). Delegates ENTIRELY to
    :func:`orchestrator_row_conformance`; no rule logic lives here, so the linter and both of the
    Set's other consumers cannot disagree.
    """
    if checkpoint not in _ORCH_ROW_BLOCKING_CHECKPOINTS:
        return []
    if doc.meta_fields.get("Kind") != S.KIND_ORCHESTRATOR:
        return []
    result = orchestrator_row_conformance(text, doc=doc)
    # EVERY finding, not the first (R8).
    return [Diagnostic(row.line, 1, C_ORCH_ROW, row.message) for row in result.findings]


# --------------------------------------------------------------------------------------
# Top-level lint
# --------------------------------------------------------------------------------------


class LintResult(NamedTuple):
    disposition: str  # conforming | quarantined | legacy/not evaluated | error
    diagnostics: List[Diagnostic]
    advisories: List[Diagnostic] = []

    @property
    def passing(self) -> bool:
        return self.disposition in S.PASSING_DISPOSITIONS


def _is_terminal_dir(directory: Optional[str]) -> bool:
    return directory in ("executed", "superseded", "not-executed")


def lint_text(
    text: str,
    *,
    checkpoint: str = "author",
    directory: Optional[str] = None,
    legacy: bool = False,
    doc: Optional[ParsedDoc] = None,
) -> LintResult:
    """Lint IPD source text. Pure: no I/O. Returns a LintResult (disposition + diagnostics).

    ``doc`` lets a caller that has ALREADY parsed ``text`` hand the parse in, so the document is
    parsed exactly ONCE per lint. ``lint_file`` uses it to share one parse between the pure checks
    here and its own repo-aware checks (plqjt7 E-02 requires consuming the already-parsed
    ``doc.open_questions`` rather than re-parsing the plan). Purity is unaffected: parsing is pure,
    and omitting the argument keeps the original behavior exactly.
    """
    if doc is None:
        doc = parse(text)
    # Legacy/grandfathered: a terminal-dir file evaluated without migration.
    # At post-transition, the just-transitioned plan is evaluated for S405 history agreement.
    if _is_terminal_dir(directory) and not legacy and checkpoint != "post-transition":
        return LintResult(S.DISPOSITION_LEGACY, [])
    # Quarantined: metadata declares quarantine (nonterminal only; the trio is validated in metadata).
    if S.is_quarantined(doc.meta_fields) and not _is_terminal_dir(directory):
        return LintResult(S.DISPOSITION_QUARANTINED, [])

    diags: List[Diagnostic] = []
    diags += check_metadata(doc, directory)
    diags += check_readiness_attestation(doc)
    diags += check_headings(doc)
    diags += check_ids_and_bijection(doc)
    diags += check_states(doc)
    diags += check_gate_contract(doc)
    diags += check_open_questions(doc)
    diags += check_size(doc)
    diags += check_checkpoint(doc, checkpoint, directory)
    diags += check_orchestrator_rows(doc, text, checkpoint)
    scope_blocking, scope_advisory = check_scope_paths(doc, checkpoint, directory)
    diags += scope_blocking
    dep_blocking, dep_advisory = check_item_dependencies(doc, checkpoint, directory)
    diags += dep_blocking
    disposition = S.DISPOSITION_CONFORMING if not diags else S.DISPOSITION_ERROR
    advisories = check_density(doc) + scope_advisory + dep_advisory
    advisories += _draft_ready_advisory(doc, text, checkpoint)
    # citeanchor `mzc019` E-03/E-04: ADVISORY-ONLY by construction. It is appended to `advisories`
    # and NEVER to `diags`, so `disposition` (computed above) cannot see it and the exit status cannot
    # move. Date-gated inside the check itself, so a pre-cutover plan contributes nothing.
    advisories += check_citation_anchors(doc, text)
    return LintResult(disposition, diags, advisories)


# agentadhere Phase 1 (IPD uisjns E-03; catalog invariant I-12): the same draft-ready nudge the
# check engine emits, surfaced as a PASSING advisory from `aw ipd lint --phase author` on a
# placeholder-free draft. Detect-and-nudge only (never flips status).
C_DRAFT_READY = "check.ipd-draft-ready-to-review"


def _draft_ready_advisory(doc, text: str, checkpoint: str) -> List[Diagnostic]:
    if checkpoint != "author":
        return []
    status = (doc.meta_fields.get("Status") or "").strip().lower()
    if status != "draft":
        return []
    try:
        from agent_workflows import ipd_authoring as _authoring

        if not _authoring.authoring_placeholders_resolved(text):
            return []
    except Exception:
        return []
    id6 = (doc.meta_fields.get("Id") or "").strip() or "<id6>"
    return [
        Diagnostic(
            0,
            0,
            C_DRAFT_READY,
            "draft has no remaining authoring placeholders; advance it with "
            f"`aw ipd set to-review {id6}`",
        )
    ]


def lint_file(
    path: Path, *, checkpoint: str = "author", legacy: bool = False
) -> LintResult:
    text = path.read_text(encoding="utf-8")
    # Parse ONCE and share the parse with the pure linter below, so the repo-aware checks that follow
    # consume the already-parsed document instead of re-parsing the same text.
    doc = parse(text)
    result = lint_text(
        text, checkpoint=checkpoint, directory=_dir_of(path), legacy=legacy, doc=doc
    )
    # ipddeps ovbnyq (spec 2.9-2.11): RESOLUTION-level Item-Dependencies checks (dangling / ambiguous
    # / cycle) need the repo, so they run HERE (lint_file has the path -> repo_root) via the ONE
    # shared check_engine evaluator, only at the blocking phases (author stays pure/advisory). They
    # are merged into the LintResult so a dangling/cyclic statement blocks at review-readiness+.
    if checkpoint in _DEP_BLOCKING_CHECKPOINTS and result.disposition in (
        S.DISPOSITION_CONFORMING,
        S.DISPOSITION_ERROR,
    ):
        try:
            from agent_workflows import check_engine as _ce

            # Derive the repo root by walking up to the dir that contains `.aw` (or `.agents`), so a
            # plan under `<root>/.aw/records/plans/pending/...` resolves to `<root>`, not its parent.
            repo_root = path.resolve().parent
            for anc in path.resolve().parents:
                if (anc / ".aw").is_dir() or (anc / ".agents").is_dir():
                    repo_root = anc
                    break
            resolution_rules = {
                S.RULE_IPD_DEP_DANGLING,
                S.RULE_IPD_DEP_AMBIGUOUS,
                S.RULE_IPD_DEP_CYCLE,
                # MISSING is cutover-gated in the evaluator (post-cutover plans only), so it is applied
                # here (repo-aware) rather than in the pure lint_text; pre-cutover/no-cutover plans
                # are grandfathered and never blocked.
                S.RULE_IPD_DEP_MISSING,
            }
            extra = [
                Diagnostic(0, 0, d.rule, d.detail)
                for d in _ce.evaluate_ipd_dependencies(
                    repo_root, phase=checkpoint, plans=[(path, text)]
                )
                if d.rule in resolution_rules
            ]
            if extra:
                merged = list(result.diagnostics) + extra
                result = LintResult(
                    S.DISPOSITION_ERROR, merged, list(result.advisories)
                )
        except Exception:
            # Resolution is best-effort; a repo-scan failure never masks the pure lint result.
            pass
    result = _merge_review_escalation(path, result, text, checkpoint, doc)
    result = _merge_durable_carrier(path, result, text, checkpoint, doc)
    return result


# revgate Order 02 (plqjt7 E-02): the review-escalation rule at the two checkpoints where it matters.
#
# `review-finalize` is where the reviewer is finishing (the moment to demand the escalation) and
# `pre-execution` is the last gate before work starts. `pre-transition` is deliberately EXCLUDED: by
# the time a plan is finalizing, execution already happened, so a gating finding needed to stop it
# earlier - blocking there would only strand a completed plan.
_REVIEW_ESCALATION_CHECKPOINTS = frozenset(("review-finalize", "pre-execution"))


def _merge_review_escalation(
    path: Path, result: LintResult, text: str, checkpoint: str, doc: ParsedDoc
) -> LintResult:
    """Merge `check.review-finding-unescalated` diagnostics into a LintResult (plqjt7 E-02).

    THIS LIVES IN ``lint_file``, NOT ``lint_text``, and that placement is load-bearing. ``lint_text``
    is PURE by documented contract ("Pure: no I/O", :func:`lint_text`), and a plan's findings live in
    a SEPARATE FILE under ``.aw/records/reviews/``, so this check cannot be performed there without
    breaking that contract. The established precedent is exact: the Item-Dependencies RESOLUTION
    checks were moved to ``lint_file`` for the same reason (see the comment above, "lint_text is
    PURE, so it only performs the SYNTAX-level checks here").

    The consequence is intended and is asserted by the tests: a text-only ``lint_text`` call CANNOT
    report this rule, because it cannot see the separate artifact.

    Delegates to the ONE shared evaluator (``check_engine.evaluate_review_finding_escalation``) so
    the checkpoint gate and ``aw check`` cannot disagree. Reuses the ALREADY-PARSED
    ``doc.open_questions`` list rather than re-parsing the plan.
    """
    if checkpoint not in _REVIEW_ESCALATION_CHECKPOINTS:
        return result
    if result.disposition not in (S.DISPOSITION_CONFORMING, S.DISPOSITION_ERROR):
        return result  # legacy / quarantined: leave the grandfathered disposition alone
    try:
        from agent_workflows import check_engine as _ce

        repo_root = path.resolve().parent
        for anc in path.resolve().parents:
            if (anc / ".aw").is_dir() or (anc / ".agents").is_dir():
                repo_root = anc
                break
        extra = [
            Diagnostic(0, 1, d.rule, d.detail)
            for d in _ce.evaluate_review_finding_escalation(
                repo_root,
                plan_path=path,
                plan_text=text,
                open_questions=doc.open_questions,
            )
        ]
        if extra:
            return LintResult(
                S.DISPOSITION_ERROR,
                list(result.diagnostics) + extra,
                list(result.advisories),
            )
    except Exception:
        # Consistent with the sibling resolution block: a repo-scan failure never masks the pure lint
        # result. NOTE this is NOT the fail-open path for a malformed artifact - that case is an
        # explicit reported branch inside the evaluator (E-07(b)), so a bad review file produces a
        # finding here rather than being swallowed.
        pass
    return result


# durablecapture Order 01 (`rnkqrc`) E-03: the durable-carrier rule at the ONE checkpoint that matters.
#
# `pre-transition` ONLY, and the asymmetry with `_REVIEW_ESCALATION_CHECKPOINTS` directly above is
# DELIBERATE rather than an inconsistency to be "fixed" later. That set EXCLUDES `pre-transition`
# because "blocking there would only strand a completed plan": a gating review finding needed to stop
# work BEFORE it started. This rule does the exact opposite for the opposite reason: the transition to
# `executed` is the precise moment an uncarried obligation VANISHES (`attention_contract._PLANS_MAP`
# maps `executed` -> `done`), so the claim of doneness is the only place the question can be asked. One
# set excludes the phase the other requires, and both are right about their own concern.
#
# DO NOT WIDEN THIS TO THE EARLIER PHASES. Firing at `author`/`review-finalize`/`pre-execution` would
# demand a carrier for a row a plan is still drafting, which is the mass-failure E-05 exists to avoid;
# 664 such rows exist across all 106 pending plans today (measured 2026-09-18).
#
# THE EXISTING `pre-execution` BLOCKING-OQ CHECK IS UNTOUCHED. Its exclusion from `pre-transition` is
# deliberate and documented (`check_checkpoint`), and this item ADDS a different question at a different
# phase rather than relocating an existing one. Two gates, two questions.
_CARRIER_CHECKPOINTS = frozenset(("pre-transition",))


def _merge_durable_carrier(
    path: Path, result: LintResult, text: str, checkpoint: str, doc: ParsedDoc
) -> LintResult:
    """Merge `check.ipd-uncarried-obligation` diagnostics into a LintResult (durablecapture `rnkqrc`).

    THIS LIVES IN ``lint_file``, NOT ``check_checkpoint``/``lint_text``, and that placement is a
    CORRECTNESS CONSTRAINT rather than a preference. ``lint_text`` is PURE by documented contract
    ("Pure: no I/O", :func:`lint_text`), and this rule RESOLVES a carrier id6 against the backlog and
    plans trees, which is I/O. The repository has already made this exact move twice with the reason
    recorded: the Item-Dependencies RESOLUTION checks and :func:`_merge_review_escalation` both sit
    here. This function follows the latter's shape exactly: gate on a checkpoint frozenset, skip
    legacy/quarantined dispositions, reuse the ALREADY-PARSED ``doc`` rather than re-parsing, and
    delegate to the ONE shared evaluator.

    THE CONSEQUENCE IS INTENDED AND IS ASSERTED BY THE TESTS: a text-only ``lint_text`` call CANNOT
    report this rule, exactly as it cannot report the review-escalation rule today. A test that got
    this rule out of ``lint_text`` would prove the predicate had been wired into the pure path.

    Only a FAILING (non-advisory) verdict blocks. A grandfathered pre-cutover plan yields an
    `info`-severity Drift from the evaluator, which is surfaced as an ADVISORY here and never flips the
    disposition, so the 106 pending plans that predate this rule still lint conforming.
    """
    if checkpoint not in _CARRIER_CHECKPOINTS:
        return result
    if result.disposition not in (S.DISPOSITION_CONFORMING, S.DISPOSITION_ERROR):
        return result  # legacy / quarantined: leave the grandfathered disposition alone
    try:
        from agent_workflows import check_engine as _ce

        repo_root = path.resolve().parent
        for anc in path.resolve().parents:
            if (anc / ".aw").is_dir() or (anc / ".agents").is_dir():
                repo_root = anc
                break
        blocking: List[Diagnostic] = []
        advisory: List[Diagnostic] = []
        for d in _ce.evaluate_durable_carrier(
            repo_root,
            plan_path=path,
            plan_text=text,
            open_questions=doc.open_questions,
        ):
            diag = Diagnostic(0, 1, d.rule, d.detail)
            (advisory if d.severity == "info" else blocking).append(diag)
        if blocking:
            return LintResult(
                S.DISPOSITION_ERROR,
                list(result.diagnostics) + blocking,
                list(result.advisories) + advisory,
            )
        if advisory:
            return LintResult(
                result.disposition,
                list(result.diagnostics),
                list(result.advisories) + advisory,
            )
    except Exception:
        # Consistent with both sibling merge blocks: a repo-scan failure never masks the pure lint
        # result. NOTE this is NOT a fail-open path for a malformed CARRIER reference - that case is an
        # explicit reported branch inside `evaluate_carrier_obligation`, so a bad id6 produces a finding
        # here rather than being swallowed.
        pass
    return result


# --------------------------------------------------------------------------------------
# CLI (wired from cli.py `aw ipd lint`)
# --------------------------------------------------------------------------------------

BOUNDARY_TEXT = (
    "aw ipd lint is DETERMINISTIC and READ-ONLY: it checks IPD structure and state only "
    "(no model, no network, no writes). A passing lint does NOT establish semantic coverage, "
    "correctness, meaningful atomicity, evidence sufficiency, truthful blocking classification, "
    "or successful execution; those remain the semantic reviewer's job."
)


# Generated index / scaffolding files under .agents/plans that are NOT IPDs and must not be linted.
_NON_IPD_BASENAMES = frozenset(("README.md", "STATUS.md", "INDEX.md"))


# citeanchor `mzc019` E-05: the advisory codes whose text is printed in DEFAULT human output.
#
# WHY THIS EXISTS. Without it, E-03 would ship a nudge that nudges nobody. The per-advisory render
# lines below are gated `if has_adv and detail`, where `detail` comes from `--detail`/`--long`; with no
# flag the entire finding collapses into the single word `advisory` in the status line, carrying NO
# code and NO message. Measured on the one pending plan then carrying advisories (`5e4sb6`, two
# `IPD-Z602` findings): the default invocation printed one line ending `advisory` and zero finding
# lines. An author who does not know to pass a flag they have no reason to suspect learns nothing, and
# the whole premise of the scaffold line is that the author MEETS the rule.
#
# DELIBERATELY NARROW, AND THE NARROWNESS IS THE POINT. Only the codes listed here become verbose by
# default. `IPD-Z602`'s existing default-quiet behavior is unchanged, because making EVERY advisory
# verbose by default would change unrelated output for every plan in the tree - a separate decision
# with its own blast radius. Adding a code here is a deliberate act; do not widen it to a blanket.
#
# THIS CHANGES ONLY WHAT IS PRINTED. Exit status and disposition do not move (an advisory never
# reaches `diagnostics`), and the `--agent`/`--json` paths already emit every advisory unconditionally
# with `severity: "info"`, so they need no change and must not gain one.
_ALWAYS_VISIBLE_ADVISORY_CODES = frozenset((C_CITATION_ANCHOR,))


def _visible_advisories(advisories: List[Diagnostic], detail: bool) -> List[Diagnostic]:
    """The advisories to print in human mode: all of them with ``--detail``, else only the
    always-visible codes (citeanchor `mzc019` E-05)."""
    if detail:
        return list(advisories)
    return [a for a in advisories if a.code in _ALWAYS_VISIBLE_ADVISORY_CODES]


def _iter_plan_files(root: Path) -> List[Path]:
    # Layout-aware (IPD awretrofit Order 01): resolve .aw/records/plans with a legacy
    # .agents/plans read-fallback, so `aw ipd lint --all` scans the migrated tree instead of
    # false-passing with conforming=0.
    from agent_workflows.record_producers import resolve_record_path

    try:
        base = resolve_record_path("plans", target_repo=str(root))
    except Exception:
        base = root / ".aw" / "records" / "plans"
    if not base.is_dir() and (root / ".agents" / "plans").is_dir():
        base = root / ".agents" / "plans"
    if not base.is_dir():
        return []
    return sorted(p for p in base.rglob("*.md") if p.name not in _NON_IPD_BASENAMES)


def _default_pending_files() -> List[Path]:
    """awlintmulti Order 01: every pending plan across both pending dirs (.aw/records/plans/pending
    and legacy .agents/plans/pending), excluding README/INDEX/STATUS sentinels."""
    from pathlib import Path as _P

    roots = [
        _P(".aw") / "records" / "plans" / "pending",
        _P(".agents") / "plans" / "pending",
    ]
    out: List[Path] = []
    for r in roots:
        if r.is_dir():
            for p in sorted(r.rglob("*.md")):
                if p.name not in ("README.md", "INDEX.md", "STATUS.md"):
                    out.append(p)
    return out


def run_lint(args: argparse.Namespace) -> int:
    """Entry point for `aw ipd lint`. Returns the process exit code (0/1/2)."""
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Evidence,
        select_output,
    )
    from agent_workflows.result_types import (
        Diagnostic as OutDiag,
    )

    checkpoint = getattr(args, "phase", None) or "author"
    ctx = select_output(args)
    if checkpoint not in S.CHECKPOINTS:
        err_msg = f"unknown --phase '{checkpoint}'"
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="ipd lint",
                status="cannot-run",
                exit_code=2,
                summary=err_msg,
            )
            return get_renderer(ctx).emit(res, ctx)
        print(f"error: {err_msg}")
        return 2

    legacy = getattr(args, "legacy", False)
    detail = getattr(args, "detail", False) or getattr(args, "long", False)
    term = Term(color=False if getattr(args, "no_color", False) else None)

    def _format_lint_line(path: Path, disp: str, has_advisories: bool = False) -> str:
        from agent_workflows import attention as _att

        raw_text = ""
        try:
            raw_text = path.read_text(encoding="utf-8")
        except OSError:
            pass

        # THE `- Status:` COLUMN IS LIFECYCLE and routes through the SHARED resolver (plan `9zvl2w`
        # E-03, spec `uonrjg` R10.3). This is the only lifecycle `status_256` call in this module; the
        # DISPOSITION column below is a different vocabulary and is handled separately.
        m_stat = re.search(r"(?m)^-\s*Status:\s*(\S+)", raw_text)
        status_word = m_stat.group(1).lower() if m_stat else "draft"
        status_resolved = _T.resolve_lifecycle(_LS.FAMILY_PLANS, status_word)
        # PADDED BY VISIBLE COLUMNS (Section 9.4), never by `len()` on styled text. The glyph is
        # carried inside this column ahead of the word, as `attention.py` does, so the column ORDER
        # and COUNT are unchanged and only this column widens 12 -> 15.
        status_marker = term.format_lifecycle_marker(status_resolved, width=2)
        status_padded = (
            status_marker
            + " "
            + (
                term.style_lifecycle_text(status_word, status_resolved)
                + (" " * max(0, 12 - _T.visible_width(status_word)))
            )
        )

        m_prio = re.search(r"(?m)^-\s*Priority:\s*(\S+)", raw_text)
        priority = m_prio.group(1).lower() if m_prio else None

        m_br = re.search(r"(?m)^-\s*Blocks-Release:\s*(\S+)", raw_text)
        blocks_release = m_br.group(1) if m_br else None

        prio_txt = ""
        if priority:
            pcode = {"high": 196, "medium": 214, "low": 244}.get(priority, 244)
            prio_txt = "  " + (
                term.color256(f"[{priority}]", pcode, bold=True)
                if getattr(term, "color", False)
                else f"[{priority}]"
            )

        blocking_txt = ""
        if blocks_release:
            blocking_txt = "  " + (
                term.color256("[blocking]", 196, bold=True)
                if getattr(term, "color", False)
                else "[blocking]"
            )

        lead = ">  " if blocks_release else "   "
        # PLAIN TYPE WORD (criterion A10, Section 9.1) - same removal as `status_set.py` and
        # `attention.py`; see the note there for why Section 11 item 5's path-segment exemption does
        # not cover a bare type word.
        type_word = "plan"
        type_prefix = type_word + (" " * max(0, 10 - len(type_word))) + "  "
        stem = _att._identity_stem(str(path))
        disp_word = (
            "advisory"
            if (disp == S.DISPOSITION_CONFORMING and has_advisories)
            else disp
        )
        # THE DISPOSITION COLUMN IS A MIXED VOCABULARY AND IS CONVERTED BY VALUE, NOT WHOLESALE
        # (plan `9zvl2w` E-03, recorded decision; spec `uonrjg` Section 7.2 and D15).
        #
        # THE DECISION: route ONLY `quarantined` through the shared resolver and leave `conforming`,
        # `advisory`, `legacy/not evaluated` and `error` on the generic `status_256` palette they use
        # today. The column holds FIVE words (`ipd_schema.DISPOSITIONS` plus the derived `advisory`),
        # of which exactly ONE is a value spec Section 7.2 claims. Converting the column WHOLESALE
        # would route four generic command outcomes through the lifecycle resolver, which R10.3
        # forbids in terms ("Generic `Term` outcomes such as command-level OK, WARN, and FAIL remain
        # valid and are outside this spec"), and would render each as `?` via criterion A20's unknown
        # path. Leaving the column ENTIRELY generic would leave a spec-claimed value unconverted and
        # make criterion A17 unsatisfiable for this view. So the split is by VALUE.
        #
        # THE COST IS REAL AND THE GLYPH IS WHAT PAYS IT. `quarantined` renders 214 (orange) today,
        # and the spec's `parked` stage is gray 244 - which is ALSO where `legacy/not evaluated`
        # already lands (it has no `ROLE_COLOR_256` entry and falls back to 244). So adopting the
        # spec color alone would make a quarantined plan nearly indistinguishable from an unevaluated
        # one, cutting against Section 7.2's own stated reason for listing it ("the lint view must
        # show it without calling it a pass"). The `◇` glyph is therefore LOAD-BEARING here, not
        # decorative: it is the cue that survives the shared color, and it is emitted unconditionally
        # for this value. Criterion A11 keeps it present with color off, and Section 11 item 2's
        # redundancy rule is what makes that sufficient.
        #
        # READ AS A CONDITION, NOT AS A STATUS (D15). `quarantined` is carried by the `- Quarantine:`
        # FIELD (`ipd_schema.is_quarantined`, consulted at `_with_name_check`), never by a `- Status:`
        # value, so it is passed as `condition=` and reaches Section 8's condition rung. Do NOT start
        # reading it from `- Status:`: no plan's status can hold it.
        if disp_word == S.DISPOSITION_QUARANTINED:
            disp_resolved = _T.resolve_lifecycle(
                _LS.FAMILY_PLANS, None, condition=S.DISPOSITION_QUARANTINED
            )
            disp_styled = (
                term.format_lifecycle_marker(disp_resolved)
                + " "
                + term.style_lifecycle_text(disp_word, disp_resolved)
            )
        else:
            disp_styled = (
                term.status_256(disp_word)
                if getattr(term, "color", False)
                else disp_word
            )

        return f"- {lead}{status_padded} {type_prefix}{stem}{prio_txt}{blocking_txt}  {disp_styled}"

    try:
        if getattr(args, "all", False):
            root = Path(getattr(args, "path", None) or ".")
            files = _iter_plan_files(root)
            counts = {
                S.DISPOSITION_CONFORMING: 0,
                S.DISPOSITION_QUARANTINED: 0,
                S.DISPOSITION_LEGACY: 0,
                S.DISPOSITION_ERROR: 0,
            }
            all_diags: list[OutDiag] = []
            for f in files:
                res = lint_file(f, checkpoint=checkpoint, legacy=legacy)
                diags, disp = _with_name_check(res, f, legacy)
                counts[disp] = counts.get(disp, 0) + 1
                for d in diags:
                    all_diags.append(
                        OutDiag(
                            location=str(f),
                            rule=d.code,
                            detail=d.message,
                            severity="error"
                            if disp == S.DISPOSITION_ERROR
                            else "warning",
                        )
                    )
                for a in getattr(res, "advisories", []):
                    all_diags.append(
                        OutDiag(
                            location=str(f),
                            rule=a.code,
                            detail=a.message,
                            severity="info",
                        )
                    )
                if not (ctx.is_agent or ctx.is_json):
                    has_adv = bool(getattr(res, "advisories", []))
                    term.line(_format_lint_line(f, disp, has_advisories=has_adv))
                    if diags:
                        for d in diags:
                            loc_str = f"line {d.line}" if d.line else ""
                            rule_str = f"{d.code} ({loc_str})" if loc_str else d.code
                            diag_txt = (
                                term.color256(f"     ! {rule_str}: {d.message}", 196)
                                if getattr(term, "color", False)
                                else f"     ! {rule_str}: {d.message}"
                            )
                            term.line(diag_txt)
                    if has_adv:
                        for a in _visible_advisories(res.advisories, detail):
                            loc_str = f"line {a.line}" if a.line else ""
                            rule_str = f"{a.code} ({loc_str})" if loc_str else a.code
                            adv_txt = (
                                term.color256(
                                    f"     ? advisory: {rule_str}: {a.message}", 214
                                )
                                if getattr(term, "color", False)
                                else f"     ? advisory: {rule_str}: {a.message}"
                            )
                            term.line(adv_txt)

            any_error = bool(counts.get(S.DISPOSITION_ERROR, 0))
            exit_code = 1 if any_error else 0
            if ctx.is_agent or ctx.is_json:
                status = "clean" if not any_error else "findings"
                res = CommandResult(
                    command="ipd lint",
                    status=status,
                    exit_code=exit_code,
                    summary=f"linted {len(files)} plan(s)",
                    diagnostics=all_diags,
                    evidence=[
                        Evidence(key="plans-inventory", value=counts, status=status)
                    ],
                    data={"counts": counts, "files": [str(f) for f in files]},
                )
                return get_renderer(ctx).emit(res, ctx)

            term.line("counts: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
            return exit_code

        # awlintmulti Order 01: `path` is now a LIST (nargs="*"). Lint the explicit files when given,
        # else default to every pending plan across both pending dirs.
        target = getattr(args, "path", None)
        paths: List[Path]
        if isinstance(target, str):
            paths = [Path(target)]  # back-compat: a single string
        elif target:
            paths = [Path(p) for p in target]
        else:
            paths = _default_pending_files()
        if not paths:
            err_msg = "no IPD files to lint (none given and no pending plans found)."
            if ctx.is_agent or ctx.is_json:
                res = CommandResult(
                    command="ipd lint",
                    status="cannot-run",
                    exit_code=2,
                    summary=err_msg,
                )
                return get_renderer(ctx).emit(res, ctx)
            print(f"error: {err_msg}")
            return 2

        any_error = False
        all_diags = []
        for path in paths:
            if not path.is_file():
                err_msg = f"not a file: {path}"
                if ctx.is_agent or ctx.is_json:
                    res = CommandResult(
                        command="ipd lint",
                        status="cannot-run",
                        exit_code=2,
                        summary=err_msg,
                    )
                    return get_renderer(ctx).emit(res, ctx)
                print(f"error: {err_msg}")
                return 2
            res = lint_file(path, checkpoint=checkpoint, legacy=legacy)
            diags, disp = _with_name_check(res, path, legacy)
            if disp == S.DISPOSITION_ERROR:
                any_error = True
            for d in diags:
                all_diags.append(
                    OutDiag(
                        location=str(path),
                        rule=d.code,
                        detail=d.message,
                        severity="error" if disp == S.DISPOSITION_ERROR else "warning",
                    )
                )
            for a in getattr(res, "advisories", []):
                all_diags.append(
                    OutDiag(
                        location=str(path),
                        rule=a.code,
                        detail=a.message,
                        severity="info",
                    )
                )
            if not (ctx.is_agent or ctx.is_json):
                has_adv = bool(getattr(res, "advisories", []))
                term.line(_format_lint_line(path, disp, has_advisories=has_adv))
                if diags:
                    for d in diags:
                        loc_str = f"line {d.line}" if d.line else ""
                        rule_str = f"{d.code} ({loc_str})" if loc_str else d.code
                        diag_txt = (
                            term.color256(f"     ! {rule_str}: {d.message}", 196)
                            if getattr(term, "color", False)
                            else f"     ! {rule_str}: {d.message}"
                        )
                        term.line(diag_txt)
                if has_adv:
                    for a in _visible_advisories(res.advisories, detail):
                        loc_str = f"line {a.line}" if a.line else ""
                        rule_str = f"{a.code} ({loc_str})" if loc_str else a.code
                        adv_txt = (
                            term.color256(
                                f"     ? advisory: {rule_str}: {a.message}", 214
                            )
                            if getattr(term, "color", False)
                            else f"     ? advisory: {rule_str}: {a.message}"
                        )
                        term.line(adv_txt)

        exit_code = 1 if any_error else 0
        if ctx.is_agent or ctx.is_json:
            status = "clean" if not any_error else "findings"
            summary = (
                f"linted {len(paths)} plan(s)"
                if not any_error
                else f"lint detected violation(s) in {len(paths)} plan(s)"
            )
            res = CommandResult(
                command="ipd lint",
                status=status,
                exit_code=exit_code,
                summary=summary,
                diagnostics=all_diags,
                evidence=[
                    Evidence(
                        key="plans-lint",
                        value={"files": len(paths), "errors": any_error},
                        status=status,
                    )
                ],
                data={"files": [str(p) for p in paths]},
            )
            return get_renderer(ctx).emit(res, ctx)

        return exit_code
    except (
        Exception
    ) as exc:  # invocation/internal failure -> exit 2, never a false pass
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="ipd lint",
                status="cannot-run",
                exit_code=2,
                summary=f"lint failed to run: {exc}",
            )
            return get_renderer(ctx).emit(res, ctx)
        print(f"error: lint failed to run: {exc}")
        return 2

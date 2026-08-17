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
from typing import Dict, List, NamedTuple, Optional, Tuple

from agent_workflows import ipd_schema as S

# --------------------------------------------------------------------------------------
# Diagnostics
# --------------------------------------------------------------------------------------


class Diagnostic(NamedTuple):
    line: int  # 1-based; 0 when not tied to a line
    col: int  # 1-based; 0 when not tied to a column
    code: str  # stable rule code, e.g. IPD-E201
    message: str

    def render(self, path: str) -> str:
        return "{0}:{1}:{2} {3} {4}".format(
            path, self.line, self.col, self.code, self.message
        )


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
C_OQ = "IPD-Q501"
C_SIZE = "IPD-Z601"
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


_FENCE_RE = re.compile(r"^(\s*)(```|~~~)")
_H1_RE = re.compile(r"^# (.+)$")
_H2_RE = re.compile(r"^## (.+?)\s*$")
_H3_RE = re.compile(r"^### (.+?)\s*$")
_LEAF_RE = re.compile(r"^- \[([ x])\]\s+(.*)$")
_SUBFIELD_RE = re.compile(r"^\s+- ([A-Za-z][A-Za-z /-]*?):\s?(.*)$")
_HISTORY_LINE_RE = re.compile(r"^-\s+(?:\d{4}-\d{2}-\d{2})\s+(\S+)")


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
        diags.append(Diagnostic(0, 0, code, "{0}: {1}".format(me.field, me.message)))
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
        diags.append(Diagnostic(0, 0, code, "{0}: {1}".format(me.field, me.message)))
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
                Diagnostic(
                    0, 0, C_HEADING_MISSING, "required H2 missing: {0}".format(want)
                )
            )
        elif cnt > 1:
            line = next((h.line for h in doc.h2 if h.title == want), 0)
            diags.append(
                Diagnostic(line, 1, C_HEADING_DUP, "duplicate H2: {0}".format(want))
            )
    # order: the subsequence of expected headings must appear in the expected order
    present_expected = [t for t in titles if t in expected]
    if present_expected != [t for t in expected if t in titles]:
        diags.append(
            Diagnostic(
                0,
                0,
                C_HEADING_ORDER,
                "H2 headings are out of canonical order for kind {0}".format(kind),
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
                    "duplicate execution id {0}".format(lf.ident),
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
                    "duplicate validation id {0}".format(lf.ident),
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
            diags.append(
                Diagnostic(lf.line, 1, C_DEPENDS, "{0}: {1}".format(lf.ident, derr))
            )
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
            diags.append(
                Diagnostic(lf.line, 1, C_EXEC_STATE, "{0}: {1}".format(lf.ident, err))
            )
        exec_by_suffix[S.suffix_of(lf.ident)] = state
    for lf in doc.valid_leaves:
        if lf.kind != "V":
            continue
        result = lf.fields.get("Result", "")
        observed_nonempty = bool(lf.fields.get("Observed evidence", "").strip())
        err = S.validation_row_error(result, lf.checked, observed_nonempty)
        if err:
            diags.append(
                Diagnostic(lf.line, 1, C_VALID_STATE, "{0}: {1}".format(lf.ident, err))
            )
        # cross-state with the matching E
        ex_state = exec_by_suffix.get(S.suffix_of(lf.ident))
        if ex_state is not None:
            cerr = S.cross_state_error(ex_state, result)
            if cerr:
                diags.append(
                    Diagnostic(
                        lf.line, 1, C_CROSS_STATE, "{0}: {1}".format(lf.ident, cerr)
                    )
                )
    return diags


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
                "status '{0}' is incompatible with checkpoint '{1}'".format(
                    status, checkpoint
                ),
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
                        "{0}: not 'performed' at pre-transition".format(lf.ident),
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
                            "{0}: not 'pass' at pre-transition".format(lf.ident),
                        )
                    )
                if not lf.fields.get("Observed evidence", "").strip():
                    diags.append(
                        Diagnostic(
                            lf.line,
                            1,
                            C_CHECKPOINT,
                            "{0}: empty Observed evidence at pre-transition".format(
                                lf.ident
                            ),
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
    return diags


# --------------------------------------------------------------------------------------
# Top-level lint
# --------------------------------------------------------------------------------------


class LintResult(NamedTuple):
    disposition: str  # conforming | quarantined | legacy/not evaluated | error
    diagnostics: List[Diagnostic]

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
) -> LintResult:
    """Lint IPD source text. Pure: no I/O. Returns a LintResult (disposition + diagnostics)."""
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
    diags += check_headings(doc)
    diags += check_ids_and_bijection(doc)
    diags += check_states(doc)
    diags += check_open_questions(doc)
    diags += check_size(doc)
    diags += check_checkpoint(doc, checkpoint, directory)
    disposition = S.DISPOSITION_CONFORMING if not diags else S.DISPOSITION_ERROR
    return LintResult(disposition, diags)


def lint_file(
    path: Path, *, checkpoint: str = "author", legacy: bool = False
) -> LintResult:
    text = path.read_text(encoding="utf-8")
    return lint_text(
        text, checkpoint=checkpoint, directory=_dir_of(path), legacy=legacy
    )


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


def run_lint(args: argparse.Namespace) -> int:
    """Entry point for `aw ipd lint`. Returns the process exit code (0/1/2)."""
    checkpoint = getattr(args, "phase", None) or "author"
    if checkpoint not in S.CHECKPOINTS:
        print("error: unknown --phase '{0}'".format(checkpoint))
        return 2
    agent = getattr(args, "agent", False)
    legacy = getattr(args, "legacy", False)

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
            for f in files:
                res = lint_file(f, checkpoint=checkpoint, legacy=legacy)
                counts[res.disposition] = counts.get(res.disposition, 0) + 1
                if agent:
                    for d in res.diagnostics:
                        print(
                            "{0}\t{1}\t{2}".format(
                                f, d.code, d.message.replace("\t", " ")
                            )
                        )
                    if not res.diagnostics:
                        print("{0}\t{1}\t{2}".format(f, "DISPOSITION", res.disposition))
                else:
                    print("{0}: {1}".format(res.disposition, f))
            if not agent:
                print(
                    "counts: "
                    + ", ".join("{0}={1}".format(k, v) for k, v in counts.items())
                )
            return 1 if counts.get(S.DISPOSITION_ERROR, 0) else 0

        target = getattr(args, "path", None)
        if not target:
            print("error: a FILE is required (or use --all)")
            return 2
        path = Path(target)
        if not path.is_file():
            print("error: not a file: {0}".format(target))
            return 2
        res = lint_file(path, checkpoint=checkpoint, legacy=legacy)
        if agent:
            for d in res.diagnostics:
                print(
                    "{0}\t{1}\t{2}".format(path, d.code, d.message.replace("\t", " "))
                )
            if not res.diagnostics:
                print("{0}\t{1}\t{2}".format(path, "DISPOSITION", res.disposition))
        else:
            if res.diagnostics:
                for d in res.diagnostics:
                    print(d.render(str(path)))
            print("disposition: {0}".format(res.disposition))
        return 1 if res.disposition == S.DISPOSITION_ERROR else 0
    except (
        Exception
    ) as exc:  # invocation/internal failure -> exit 2, never a false pass
        print("error: lint failed to run: {0}".format(exc))
        return 2

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
C_OQ = "IPD-Q501"
C_SIZE = "IPD-Z601"
C_SIZE_DENSITY = "IPD-Z602"
C_SCOPE_PATHS = "IPD-M106"  # Scope-Paths declared-scope allowlist (Order oorry1)
C_NAME = "IPD-N001"  # filename does not match the plan grammar (awcheck Order 03)


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


_FENCE_RE = re.compile(r"^(\s*)(```|~~~)")
_H1_RE = re.compile(r"^# (.+)$")
_H2_RE = re.compile(r"^## (.+?)\s*$")
_H3_RE = re.compile(r"^### (.+?)\s*$")
_LEAF_RE = re.compile(r"^- \[([ x])\]\s+(.*)$")
_SUBFIELD_RE = re.compile(r"^\s+- ([A-Za-z][A-Za-z /-]*?):\s?(.*)$")
_HISTORY_LINE_RE = re.compile(r"^-\s+(?:\d{4}-\d{2}-\d{2})\s+(\S+)")
# ipdgates Order wezhxg: parse the full terminal history line `- <date> <status> (<actor>): <msg>`
# so the post-transition attribution lint can reject a generic/empty actor + empty summary.
_HISTORY_ATTRIB_RE = re.compile(
    r"^-\s+(?:\d{4}-\d{2}-\d{2})\s+(?P<status>\S+)\s+\((?P<actor>[^)]*)\)\s*:\s*(?P<msg>.*)$"
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
    diags += check_headings(doc)
    diags += check_ids_and_bijection(doc)
    diags += check_states(doc)
    diags += check_open_questions(doc)
    diags += check_size(doc)
    diags += check_checkpoint(doc, checkpoint, directory)
    scope_blocking, scope_advisory = check_scope_paths(doc, checkpoint, directory)
    diags += scope_blocking
    dep_blocking, dep_advisory = check_item_dependencies(doc, checkpoint, directory)
    diags += dep_blocking
    disposition = S.DISPOSITION_CONFORMING if not diags else S.DISPOSITION_ERROR
    advisories = check_density(doc) + scope_advisory + dep_advisory
    advisories += _draft_ready_advisory(doc, text, checkpoint)
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

        m_stat = re.search(r"(?m)^-\s*Status:\s*(\S+)", raw_text)
        status_word = m_stat.group(1).lower() if m_stat else "draft"
        status_padded = (
            term.status_256(status_word, width=12)
            if getattr(term, "color", False)
            else status_word.ljust(12)
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
        type_word = "plan"
        type_txt = (
            term.color256(type_word, _att._TREE_COLOR_256, bold=True)
            if getattr(term, "color", False)
            else type_word
        )
        type_prefix = type_txt + (" " * max(0, 10 - len(type_word))) + "  "
        stem = _att._identity_stem(str(path))
        disp_word = (
            "advisory"
            if (disp == S.DISPOSITION_CONFORMING and has_advisories)
            else disp
        )
        disp_styled = (
            term.status_256(disp_word) if getattr(term, "color", False) else disp_word
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
                    if has_adv and detail:
                        for a in res.advisories:
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
                if has_adv and detail:
                    for a in res.advisories:
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

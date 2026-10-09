"""Deterministic verifiers for production actions (artdispatch aeq7f8).

Pure-ish module implementing the verification codes from spec 25kzda 4.8 / z7nbn1 4.4 / 89xjll:
  - SPEC-PLAN-COUNT
  - SPEC-PLAN-CONFORMANCE
  - SPEC-PLAN-GATE-CARRY
  - SPEC-PLAN-TRACE

Each verifier returns a list of findings `[(code, plan_or_source_id6, message)]` rendered from the
25kzda 4.8 message templates.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Container, Mapping, NamedTuple, Sequence

from agent_workflows import check_engine as _ce
from agent_workflows import ipd_lint as _lint
from agent_workflows import plans_refs as _pr
from agent_workflows import specs as _specs

_PLAN_ID_RE = re.compile(r"(?m)^-[ \t]*Id:[ \t]*([0-9a-z]{6})[ \t]*$")
_ITEM_DEPS_RE = re.compile(r"(?m)^-[ \t]*Item-Dependencies:[ \t]*(.*?)[ \t]*$")
_SCOPE_PATHS_RE = re.compile(r"(?m)^-[ \t]*Scope-Paths:[ \t]*(.*?)[ \t]*$")
_ITEM_FROM_BACKLOG_RE = re.compile(r"(?m)^-[ \t]*From-Backlog:[ \t]*([^\n]*?)[ \t]*$")
_SET_RE = re.compile(r"(?m)^-[ \t]*Set:[ \t]*(\S+)")
_TERMINAL_DISPOSITIONS = frozenset(("executed", "superseded", "not-executed"))

# Spec requirement IDs cutover (spec 89xjll Section 5.1 / IPD rtvdak E-06): specs adopt
# requirement and acceptance IDs GOING FORWARD, so a spec whose FILENAME date is at or after
# the cutover is bound by SPEC-PLAN-TRACE, while a pre-cutover spec is grandfathered.
# THIS CONSTANT IS THE FALLBACK, NOT THE BOUNDARY: `spec_requires_requirement_ids` resolves
# `config.resolve_cutover_date(repo, "spec_requirement_ids")` FIRST, so a repository moves its
# own boundary in `.aw/config/project.json` and never by editing Python. The fallback is non-None
# DELIBERATELY, avoiding BOTH documented failure modes: a config-only resolver fails open to
# None in a fresh clone or CI checkout lacking install history and grandfathers every spec
# forever (the decoration mode), while a constant-only rule ships an immovable date in a
# repo that already moved that capability into config.
SPEC_REQUIREMENT_IDS_CUTOVER_DATE = (
    "20261001"  # compact YYYYMMDD; bound iff filename date >= this
)

_SPEC_DATE_RE = re.compile(r"\A(\d{8})-")


def spec_requires_requirement_ids(filename: str, repo_root: Path | None = None) -> bool:
    """True iff a spec filename's leading YYYYMMDD date is at/after the spec_requirement_ids cutover.

    When repo_root is provided, resolves dynamically via resolve_cutover_date(repo_root, 'spec_requirement_ids').
    Falls back to SPEC_REQUIREMENT_IDS_CUTOVER_DATE when unconfigured or repo_root is omitted.
    A filename with no parseable leading date is treated as pre-cutover (returns False) so a legacy
    or unusually-named spec is grandfathered. Front-matter `- Date:` is not consulted.
    """
    m = _SPEC_DATE_RE.match(Path(filename).name)
    if m is None:
        return False
    cutover: str | None = None
    if repo_root is not None:
        from agent_workflows import config as _config

        cutover = _config.resolve_cutover_date(
            repo_root, "spec_requirement_ids", compact=True
        )
    if cutover is None:
        cutover = SPEC_REQUIREMENT_IDS_CUTOVER_DATE
    return m.group(1) >= cutover


class HandoffPlan(NamedTuple):
    """An active plan linking a backlog item or spec in a production handoff."""

    path: Path
    id6: str
    status: str
    kind: str
    set: str | None

    @property
    def set_id(self) -> str | None:
        return self.set


def existing_handoff_plans(
    repo: Path,
    source_type: str,
    source_id6: str,
    *,
    exclude_ids: Container[str] | None = None,
) -> list[HandoffPlan]:
    """Return active (non-terminal-disposition) plans linking the source in path order."""
    repo = Path(repo)
    source_id6 = str(source_id6).strip().lower()
    results: list[HandoffPlan] = []
    for p, text in _ce._iter_plan_ipds(repo):
        disp = _ce._plan_disposition(repo, p)
        if disp in _TERMINAL_DISPOSITIONS:
            continue
        p_id = _extract_plan_id(p, text)
        if exclude_ids is not None and p_id in exclude_ids:
            continue

        if source_type in ("backlog", "From-Backlog"):
            from_bkl = _read_from_backlog(text)
            if not from_bkl or from_bkl.lower() != source_id6:
                continue
        elif source_type in ("spec", "From-Spec"):
            m_from = _ce._ITEM_FROM_SPEC_RE.search(text)
            from_spec = m_from.group(1).strip() if m_from else None
            if not from_spec or from_spec.lower() != source_id6:
                continue
        else:
            continue

        m_status = _ce._PLAN_STATUS_RE.search(text)
        status = m_status.group(1).strip() if m_status else ""
        doc = _lint.parse(text)
        kind = (doc.meta_fields.get("Kind") or "").strip()
        m_set = _SET_RE.search(text)
        set_val = m_set.group(1).strip() if m_set else None

        results.append(
            HandoffPlan(
                path=p,
                id6=p_id,
                status=status,
                kind=kind,
                set=set_val,
            )
        )
    return sorted(results, key=lambda x: str(x.path))


def _read_from_backlog(text: str) -> str | None:
    """The plan's `- From-Backlog:` id6, or None when absent, sentinel, or malformed (plan okp2o4)."""
    m = _ITEM_FROM_BACKLOG_RE.search(text)
    if not m:
        return None
    cls = _lint.S.classify_source_link(m.group(1))
    if cls.verdict == _lint.S.SOURCE_LINK_USABLE:
        return cls.id6
    return None


def _extract_plan_id(path: Path, text: str) -> str:
    """Extract 6-char plan id from frontmatter or filename."""
    m = _PLAN_ID_RE.search(text)
    if m:
        return m.group(1).strip()
    m_ref = _pr._read_id(text)
    if m_ref:
        return m_ref.strip()
    parts = path.stem.split("-")
    if len(parts) >= 4 and len(parts[3]) == 6:
        return parts[3]
    return path.stem


def _find_spec_text_and_path(
    repo: Path, spec_id6: str
) -> tuple[Path | None, str | None]:
    """Find the spec file path and content for a given spec id6."""
    target_id6 = str(spec_id6).strip().lower()
    for p, text in _ce._iter_spec_records(repo):
        m = _specs._SPEC_ID_BULLET_RE.search(text)
        if m and m.group(1).strip().lower() == target_id6:
            return p, text
        if target_id6 in p.name.lower():
            return p, text
    return None, None


def spec_plan_count(
    repo: Path,
    spec_id6: str,
    baseline_plan_ids: Sequence[str] | Mapping[str, Any] | set[str] | None = None,
    *,
    host: str = "<host>",
) -> list[tuple[str, str, str]]:
    """Verify SPEC-PLAN-COUNT: accepts existing active plans carrying From-Spec as continued output,
    refusing only when (a) no active linked plan remains, (b) an unlinked new plan was created,
    or (c) this action introduced a second Set.
    """
    repo = Path(repo)
    baseline_ids: set[str] = set()
    if baseline_plan_ids is not None:
        if isinstance(baseline_plan_ids, Mapping):
            baseline_ids = set(baseline_plan_ids.keys())
        else:
            baseline_ids = set(baseline_plan_ids)

    all_linked = existing_handoff_plans(repo, "spec", spec_id6)
    pre_existing_linked = [p for p in all_linked if p.id6 in baseline_ids]
    new_linked = [p for p in all_linked if p.id6 not in baseline_ids]

    # Find new plans linking a different spec (or none)
    unlinked_new_plans: list[str] = []
    for p, text in _ce._iter_plan_ipds(repo):
        p_id = _extract_plan_id(p, text)
        if p_id not in baseline_ids:
            m_from = _ce._ITEM_FROM_SPEC_RE.search(text)
            from_spec = m_from.group(1).strip() if m_from else None
            if from_spec != spec_id6:
                unlinked_new_plans.append(p_id)

    # Condition (a): after the turn there is no active plan linking the spec at all
    if not all_linked:
        msg = (
            f"[SPEC-PLAN-COUNT] Spec {spec_id6} produced 0 new linked IPDs; "
            "expected at least one, each carrying From-Spec. Quarantine the authoring action, "
            f"reconcile duplicates, run aw check all, then: aw {host} run {spec_id6}"
        )
        return [("SPEC-PLAN-COUNT", spec_id6, msg)]

    # Condition (b): a new plan links a different spec (or none)
    if unlinked_new_plans:
        unlinked_str = ", ".join(sorted(unlinked_new_plans))
        msg = (
            f"[SPEC-PLAN-COUNT] Spec {spec_id6} produced new plan(s) ({unlinked_str}) "
            f"linking a different spec or none; expected each carrying From-Spec. Quarantine the authoring action, "
            f"reconcile duplicates, run aw check all, then: aw {host} run {spec_id6}"
        )
        return [("SPEC-PLAN-COUNT", spec_id6, msg)]

    # Condition (c): THIS ACTION INTRODUCED A SECOND SET
    pre_existing_sets = {
        p.set if p.set is not None else p.id6 for p in pre_existing_linked
    }
    if pre_existing_linked:
        conflicting_new = [
            np
            for np in new_linked
            if (np.set if np.set is not None else np.id6) not in pre_existing_sets
        ]
        if conflicting_new:
            pre_ids_str = ", ".join(sorted(p.id6 for p in pre_existing_linked))
            pre_sets_str = ", ".join(sorted(pre_existing_sets))
            new_ids_str = ", ".join(sorted(np.id6 for np in conflicting_new))
            new_sets_str = ", ".join(
                sorted(
                    {np.set if np.set is not None else np.id6 for np in conflicting_new}
                )
            )
            msg = (
                f"[SPEC-PLAN-COUNT] Spec {spec_id6} introduced a second Set: "
                f"pre-existing active plan(s) ({pre_ids_str}) carry Set(s) {pre_sets_str}, "
                f"but new plan(s) ({new_ids_str}) carry Set(s) {new_sets_str}. "
                f"Quarantine the authoring action, reconcile duplicates, run aw check all, then: aw {host} run {spec_id6}"
            )
            return [("SPEC-PLAN-COUNT", spec_id6, msg)]
    else:
        new_sets = {np.set if np.set is not None else np.id6 for np in new_linked}
        if len(new_sets) > 1:
            all_new_ids = ", ".join(sorted(np.id6 for np in new_linked))
            new_sets_str = ", ".join(sorted(new_sets))
            msg = (
                f"[SPEC-PLAN-COUNT] Spec {spec_id6} introduced multiple Sets: "
                f"new plan(s) ({all_new_ids}) span Sets {new_sets_str}. "
                f"Quarantine the authoring action, reconcile duplicates, run aw check all, then: aw {host} run {spec_id6}"
            )
            return [("SPEC-PLAN-COUNT", spec_id6, msg)]

    return []


def _check_ipd_conformance(
    repo: Path,
    p_raw: Path | str,
    expected_origin_field: str,
    expected_origin_id6: str,
    *,
    continued_ids: Container[str] | None = None,
) -> tuple[str, list[tuple[str, str]]]:
    """Validate common IPD conformance requirements (used by spec and backlog production).

    Returns (plan_id, [(diagnostic_code, diagnostic_message)]).
    """
    repo = Path(repo)
    p = Path(p_raw)
    if not p.is_absolute():
        p = repo / p
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        return "<unknown>", [("check.readable", f"cannot read {p}: {exc}")]

    plan_id = _extract_plan_id(p, text)
    diags: list[tuple[str, str]] = []

    # 1. Bucket: sits under pending/
    disp = _ce._plan_disposition(repo, p)
    if disp != "pending":
        diags.append(("check.plan-bucket", f"plan is in {disp!r}, expected 'pending'"))

    # 2. Status: to-review (or legitimate status for continued plans)
    m_status = _ce._PLAN_STATUS_RE.search(text)
    status_val = m_status.group(1).strip() if m_status else ""
    is_continued = continued_ids is not None and plan_id in continued_ids
    if is_continued:
        if status_val not in ("to-review", "reviewed", "approved", "auto-approved"):
            diags.append(
                (
                    "check.plan-status",
                    f"plan status is {status_val!r}, expected 'to-review', 'reviewed', 'approved', or 'auto-approved'",
                )
            )
    else:
        if status_val != "to-review":
            diags.append(
                (
                    "check.plan-status",
                    f"plan status is {status_val!r}, expected 'to-review'",
                )
            )

    # 3. Origin link: carries expected_origin_id6
    if expected_origin_field == "From-Spec":
        m_from = _ce._ITEM_FROM_SPEC_RE.search(text)
        from_val = m_from.group(1).strip() if m_from else ""
        if from_val != expected_origin_id6:
            diags.append(("check.from-spec", "missing or invalid From-Spec field"))
    elif expected_origin_field == "From-Backlog":
        from_val = _read_from_backlog(text) or ""
        if from_val != expected_origin_id6:
            diags.append(
                ("check.from-backlog", "missing or invalid From-Backlog field")
            )

    # 4. Scope-Paths: concrete (not empty, not TODO, not grandfathered)
    m_scope = _SCOPE_PATHS_RE.search(text)
    scope_val = m_scope.group(1).strip() if m_scope else ""
    if not scope_val or "TODO" in scope_val or scope_val == "grandfathered":
        diags.append(
            (
                "check.scope-paths",
                "Scope-Paths must be concrete (not empty, not TODO, not grandfathered)",
            )
        )
    else:
        paths, is_gf, errs = _lint.S.parse_scope_paths(scope_val)
        if is_gf or errs or not paths:
            detail = "; ".join(errs) if errs else "invalid scope paths"
            diags.append(("check.scope-paths", detail))

    # 5. Item-Dependencies: resolved (not unresolved)
    m_deps = _ITEM_DEPS_RE.search(text)
    deps_val = m_deps.group(1).strip() if m_deps else ""
    if "unresolved" in deps_val.lower():
        diags.append(
            ("check.item-dependencies", "Item-Dependencies contains 'unresolved'")
        )

    # 6. Lints conforming at review-finalize (IPD-S408 de-duplicated: owned by Set verifier)
    lint_res = _lint.lint_file(p, checkpoint="review-finalize", suppress_s408=True)
    if lint_res.disposition != _lint.S.DISPOSITION_CONFORMING:
        for diag in lint_res.diagnostics:
            if diag.code == _lint.C_ORCH_NOT_READY:
                continue
            diags.append((diag.code, diag.message))

    return plan_id, diags


def _format_orchestrator_findings(
    findings: Sequence[Any],
    plan_id: str,
) -> str:
    parts: list[str] = []
    for f in findings:
        remedy = (
            str(f.remedy)
            .replace("<id6>", plan_id)
            .replace("<child-id6>", str(f.subject))
        )
        if remedy in str(f.detail):
            parts.append(f"{f.subject}: {f.detail}")
        else:
            parts.append(f"{f.subject}: {f.detail}; {remedy}")
    return "; ".join(parts)


def spec_plan_set(
    repo: Path,
    spec_id6: str,
    produced_paths: Sequence[Path | str],
    *,
    host: str,
    run_id: str,
    state: Mapping[str, Any],
    asker: Any = None,
    runner: Any = None,
) -> list[tuple[str, str, str]]:
    """Verify SPEC-PLAN-SET: every produced orchestrator plan is ready for review.

    Pass criterion (25kzda 4.8):
      Every produced orchestrator plan, evaluated by Section 2.5d (the probe may be asked).
      Every produced orchestrator is ready for review; a passing verdict is recorded for its current text.
    """
    repo = Path(repo)
    findings: list[tuple[str, str, str]] = []

    from agent_workflows import orchestrator_readiness as _orch_readiness
    from agent_workflows import runner_shared as _rs

    retry_budget = _rs.frozen_retry_budget(state)

    for p_raw in produced_paths:
        p = Path(p_raw)
        if not p.is_absolute():
            p = repo / p
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        doc = _lint.parse(text)
        if (doc.meta_fields.get("Kind") or "").strip() != "orchestrator":
            continue

        plan_id = _extract_plan_id(p, text)
        readiness = _orch_readiness.review_readiness(
            repo,
            p,
            ask=True,
            host=host,
            state=state,
            asker=asker,
            runner=runner,
            retry_budget=retry_budget,
        )
        if not readiness.ready:
            findings_str = _format_orchestrator_findings(readiness.findings, plan_id)
            msg = (
                f"[SPEC-PLAN-SET] Orchestrator {plan_id} produced from spec {spec_id6} "
                f"is not ready for review: {findings_str}. "
                f"Fix it with the IPD authoring tools, then: aw {host} run resume {run_id}"
            )
            findings.append(("SPEC-PLAN-SET", plan_id, msg))

    return findings


def spec_plan_conformance(
    repo: Path,
    spec_id6: str,
    produced_paths: Sequence[Path | str],
    *,
    host: str = "<host>",
    run_id: str = "<run-id>",
    continued_ids: Container[str] | None = None,
) -> list[tuple[str, str, str]]:
    """Verify SPEC-PLAN-CONFORMANCE: each produced plan is canonical, to-review, in pending/,
    carries From-Spec, concrete Scope-Paths, resolved Item-Dependencies, and conformant E/V checklists.

    Pass criterion (25kzda 4.8):
      New IPD is canonical, `to-review`, in `pending/`, has `From-Spec: <id6>`, concrete Scope-Paths,
      a resolved `Item-Dependencies` statement, and conformant E/V checklists.
    """
    repo = Path(repo)
    findings: list[tuple[str, str, str]] = []

    for p_raw in produced_paths:
        plan_id, diags = _check_ipd_conformance(
            repo, p_raw, "From-Spec", spec_id6, continued_ids=continued_ids
        )
        for code, detail in diags:
            msg = (
                f"[SPEC-PLAN-CONFORMANCE] Generated IPD {plan_id} for spec {spec_id6} "
                f"fails {code}: {detail}. "
                f"Fix it with the IPD authoring tools, then: aw {host} run resume {run_id}"
            )
            findings.append(("SPEC-PLAN-CONFORMANCE", plan_id, msg))

    return findings


def spec_plan_gate_carry(
    repo: Path,
    spec_id6: str,
    produced_paths: Sequence[Path | str],
    *,
    host: str = "<host>",
) -> list[tuple[str, str, str]]:
    """Verify SPEC-PLAN-GATE-CARRY: a spec release gate is copied exactly to the IPD;
    an absent spec gate is not invented.

    Pass criterion (25kzda 4.8):
      A spec release gate is copied exactly to the IPD; an absent spec gate is not invented.
    """
    repo = Path(repo)
    findings: list[tuple[str, str, str]] = []

    _spec_path, spec_text = _find_spec_text_and_path(repo, spec_id6)
    spec_gate: str | None = None
    if spec_text:
        m_sg = _ce._META_BLOCKS_RELEASE_RE.search(spec_text)
        spec_gate = m_sg.group(1).strip() if m_sg else None

    for p_raw in produced_paths:
        p = Path(p_raw)
        if not p.is_absolute():
            p = repo / p
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue

        plan_id = _extract_plan_id(p, text)
        m_pg = _ce._META_BLOCKS_RELEASE_RE.search(text)
        plan_gate = m_pg.group(1).strip() if m_pg else None

        if not _ce._same_release(repo, spec_gate, plan_gate):
            msg = (
                f"[SPEC-PLAN-GATE-CARRY] Spec {spec_id6} and IPD {plan_id} disagree on Blocks-Release. "
                "Quarantine the handoff, correct it, run aw check all, then: "
                f"aw {host} run {spec_id6}"
            )
            findings.append(("SPEC-PLAN-GATE-CARRY", plan_id, msg))

    return findings


_REQ_ID_RE = re.compile(r"^([RFGICPTBH](?:[-_]?\d+(?:\.\d+)*(?:[a-zA-Z](?:-\d+)?)?))")
_AC_ID_RE = re.compile(r"^(A[C]?[-_]?\d+(?:\.\d+)*(?:[a-zA-Z](?:-\d+)?)?)")
_DELIM_RE = re.compile(r"^([:.\s|]|$)")
_MARKER_RE = re.compile(r"^(?:[:.\-\s|]|\*\*|`)*`?\[(Should|Optional|Deferred)\]`?")


def parse_spec_requirement_ids(spec_text: str) -> tuple[set[str], set[str]]:
    """Parse declared requirement and acceptance IDs from spec text (IPD rtvdak E-03 / spec 89xjll).

    Honors the declaration-site rule (spec 89xjll Section 4.1):
      1. Appears at the beginning of a line outside of fenced code blocks, preceded by at most
         one structural marker (markdown bullet `- `, `* `, `+ `; table pipe `|`; heading `## `;
         or bare text at start of paragraph preceded by blank line).
      2. Initial token matches admitted requirement ID or acceptance criterion ID grammar,
         optionally wrapped in bold (**...**) or backticks (`...`).
      3. Followed by delimiter (colon, period, hyphen, whitespace, closing formatting markers,
         or table delimiter).
    Mentions mid-sentence, parenthetical notes, other-spec citations, or in paragraph prose
    are NOT extracted.
    FORM B dotted paragraphs, FORM C numbered headings, and the N family are excluded from TRACE.

    Returns:
      (declared_requirement_ids, declared_acceptance_ids) as two disjoint sets.
    """
    req_ids, ac_ids, _ = _parse_spec_ids_and_markers(spec_text)
    return req_ids, ac_ids


def parse_spec_id_markers(spec_text: str) -> dict[str, str]:
    """Parse marker tokens (`[Should]`, `[Optional]`, `[Deferred]`) attached to declared IDs.

    Returns mapping of id -> marker name ('Should', 'Optional', 'Deferred').
    For acceptance IDs, only 'Deferred' is recognized ('Should'/'Optional' has no effect).
    """
    _, _, markers = _parse_spec_ids_and_markers(spec_text)
    return markers


def _parse_spec_ids_and_markers(
    spec_text: str,
) -> tuple[set[str], set[str], dict[str, str]]:
    req_ids: set[str] = set()
    ac_ids: set[str] = set()
    markers: dict[str, str] = {}

    in_code_block = False
    can_start_para = True

    for line in spec_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            can_start_para = False
            continue
        if in_code_block:
            continue

        if not stripped:
            can_start_para = True
            continue

        # Check structural marker
        m_bullet = re.match(r"^[ \t]*[-*+][ \t]+(.*)$", line)
        m_pipe = re.match(r"^[ \t]*\|[ \t]*(.*)$", line)
        m_heading = re.match(r"^[ \t]*#{1,6}[ \t]+(.*)$", line)

        rest: str | None = None
        if m_bullet:
            rest = m_bullet.group(1).strip()
            can_start_para = False
        elif m_pipe:
            rest = m_pipe.group(1).strip()
            can_start_para = False
        elif m_heading:
            rest = m_heading.group(1).strip()
            can_start_para = True  # Start of section (spec 89xjll Section 4.1)
        elif can_start_para:
            rest = stripped
            can_start_para = False

        if rest is None:
            can_start_para = False
            continue

        token: str | None = None
        after: str = ""
        m_bold = re.match(r"^\*\*([^*]+)\*\*(.*)$", rest)
        m_tick = re.match(r"^`([^`]+)`(.*)$", rest)
        if m_bold:
            token = m_bold.group(1).strip()
            after = m_bold.group(2).strip()
        elif m_tick:
            token = m_tick.group(1).strip()
            after = m_tick.group(2).strip()
        else:
            m_r = _REQ_ID_RE.match(rest)
            m_a = _AC_ID_RE.match(rest)
            if m_r:
                tok = m_r.group(1)
                rem = rest[len(tok) :]
                if _DELIM_RE.match(rem):
                    token = tok
                    after = rem.strip()
            elif m_a:
                tok = m_a.group(1)
                rem = rest[len(tok) :]
                if _DELIM_RE.match(rem):
                    token = tok
                    after = rem.strip()

        if not token:
            continue

        if m_bold or m_tick:
            m_r = _REQ_ID_RE.match(token)
            m_a = _AC_ID_RE.match(token)
            if m_r and m_r.group(1) == token:
                is_req = True
            elif m_a and m_a.group(1) == token:
                is_req = False
            else:
                continue
        else:
            is_req = bool(_REQ_ID_RE.match(token))

        # A declaration line allows the next line to be another declaration
        can_start_para = True

        m_marker = _MARKER_RE.search(after)
        marker_val = m_marker.group(1) if m_marker else None

        if is_req:
            req_ids.add(token)
            if marker_val:
                markers[token] = marker_val
        else:
            ac_ids.add(token)
            if marker_val == "Deferred":
                markers[token] = marker_val

    return req_ids, ac_ids, markers


def _find_executed_linked_plans(repo: Path, spec_id6: str) -> list[Path]:
    """Find plans in executed/ linking spec_id6 by From-Spec (spec 89xjll Section 6.1)."""
    repo = Path(repo)
    target_id6 = str(spec_id6).strip().lower()
    executed_dir = repo / ".aw" / "records" / "plans" / "executed"
    if not executed_dir.is_dir():
        return []
    plans: list[Path] = []
    for p in sorted(executed_dir.glob("*.ipd.md")):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        m_from = _ce._ITEM_FROM_SPEC_RE.search(text)
        from_spec = m_from.group(1).strip() if m_from else None
        if from_spec and from_spec.lower() == target_id6:
            plans.append(p)
    return plans


def spec_plan_trace(
    repo: Path,
    spec_id6: str,
    produced_paths: Sequence[Path | str],
    *,
    host: str = "<host>",
    run_id: str = "<run-id>",
    continued_ids: Container[str] | None = None,
) -> list[tuple[str, str, str]]:
    """Verify SPEC-PLAN-TRACE: every mandatory spec requirement maps to at least one E item
    and every acceptance criterion maps to at least one V item; there are no unknown references.

    Pass criterion (25kzda 4.8):
      Every mandatory spec requirement maps to at least one E item and every acceptance criterion
      maps to at least one V item; there are no unknown references

    Citation-not-implementation limit (spec 89xjll Section 6.4):
      A trace check proves only that a plan step CITES a requirement or acceptance identifier;
      it does NOT prove that the plan correctly, completely, or safely implements the requirement.
      SPEC-PLAN-TRACE is a structural citation gate, never a semantic proof of implementation.
      A produced plan verified by this check may be described as trace-verified against declared
      identifiers, but MUST NOT be described as having verified the semantic correctness of the
      implementation. A PASS produced by the grandfathered or zero-id path of Section 6.3 is
      VACUOUS and MUST NOT be described as trace-verified at all.
    """
    repo = Path(repo)
    spec_path, spec_text = _find_spec_text_and_path(repo, spec_id6)
    if not spec_path or not spec_text:
        return []

    # Check grandfathering per spec filename date
    if not spec_requires_requirement_ids(spec_path.name, repo_root=repo):
        return []

    req_ids, ac_ids = parse_spec_requirement_ids(spec_text)
    markers = parse_spec_id_markers(spec_text)

    # A spec declaring no traceable IDs passes vacuously
    if not req_ids and not ac_ids:
        return []

    mandatory_reqs = {
        r for r in req_ids if markers.get(r) not in ("Should", "Optional", "Deferred")
    }
    mandatory_acs = {a for a in ac_ids if markers.get(a) != "Deferred"}
    declared_all = req_ids | ac_ids

    # Assemble pooled plan set: passed produced_paths plus executed linked plans
    pooled_paths: list[Path] = []
    seen_paths: set[Path] = set()
    for p_raw in produced_paths:
        p = Path(p_raw)
        if not p.is_absolute():
            p = repo / p
        if p not in seen_paths:
            seen_paths.add(p)
            pooled_paths.append(p)

    for p in _find_executed_linked_plans(repo, spec_id6):
        if p not in seen_paths:
            seen_paths.add(p)
            pooled_paths.append(p)

    # Qualified citation regex for producing spec
    cite_pattern = re.compile(
        rf"(?i)`?{re.escape(spec_id6)}`?[ \t]+`?([a-zA-Z0-9]+(?:[-_.][a-zA-Z0-9]+)*)`?"
    )

    cited_reqs: set[str] = set()
    cited_acs: set[str] = set()
    unknown_refs: set[str] = set()

    for p in pooled_paths:
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        doc = _lint.parse(text)
        is_orch = (doc.meta_fields.get("Kind") or "").strip() == "orchestrator"

        # Search E leaves
        for leaf in doc.exec_leaves:
            if is_orch and _lint._ORCH_ROW_RE.match(leaf.text):
                continue
            leaf_content = f"{leaf.text}\n" + "\n".join(
                str(v) for v in leaf.fields.values()
            )
            for cited_id in cite_pattern.findall(leaf_content):
                if cited_id in declared_all:
                    if cited_id in req_ids:
                        cited_reqs.add(cited_id)
                else:
                    unknown_refs.add(cited_id)

        # Search V leaves
        for leaf in doc.valid_leaves:
            leaf_content = f"{leaf.text}\n" + "\n".join(
                str(v) for v in leaf.fields.values()
            )
            for cited_id in cite_pattern.findall(leaf_content):
                if cited_id in declared_all:
                    if cited_id in ac_ids:
                        cited_acs.add(cited_id)
                else:
                    unknown_refs.add(cited_id)

    uncovered_reqs = mandatory_reqs - cited_reqs
    uncovered_acs = mandatory_acs - cited_acs

    missing_or_unknown = sorted(uncovered_reqs | uncovered_acs | unknown_refs)
    if not missing_or_unknown:
        return []

    # Identify plan_id for finding message (a newly produced plan preferred)
    target_plan_id = spec_id6
    if produced_paths:
        new_plans: list[str] = []
        for p_raw in produced_paths:
            p = Path(p_raw)
            if not p.is_absolute():
                p = repo / p
            try:
                p_text = p.read_text(encoding="utf-8")
                pid = _extract_plan_id(p, p_text)
            except OSError:
                pid = p.stem
            if continued_ids is None or pid not in continued_ids:
                new_plans.append(pid)
        target_plan_id = (
            new_plans[0]
            if new_plans
            else (_extract_plan_id(Path(produced_paths[0]), "") or spec_id6)
        )

    ids_str = ", ".join(missing_or_unknown)
    msg = (
        f"[SPEC-PLAN-TRACE] Generated IPD {target_plan_id} does not cover spec items: {ids_str}. "
        f"Correct and sync the IPD, then: aw {host} run resume {run_id}"
    )
    return [("SPEC-PLAN-TRACE", target_plan_id, msg)]


def spec_plan_trace_vacuity(repo: Path, spec_id6: str) -> str | None:
    """Return the vacuity reason ('grandfathered' or 'no-ids') if TRACE passes vacuously, else None."""
    repo = Path(repo)
    spec_path, spec_text = _find_spec_text_and_path(repo, spec_id6)
    if not spec_path or not spec_text:
        return "grandfathered"
    if not spec_requires_requirement_ids(spec_path.name, repo_root=repo):
        return "grandfathered"
    req_ids, ac_ids = parse_spec_requirement_ids(spec_text)
    if not req_ids and not ac_ids:
        return "no-ids"
    return None


def spec_plan_trace_deferred(repo: Path, spec_id6: str) -> list[str]:
    """Return the list of declared requirement and acceptance IDs carrying the [Deferred] marker."""
    repo = Path(repo)
    _, spec_text = _find_spec_text_and_path(repo, spec_id6)
    if not spec_text:
        return []
    markers = parse_spec_id_markers(spec_text)
    return sorted(id_name for id_name, m in markers.items() if m == "Deferred")


def _find_backlog_text_and_path(
    repo: Path, item_id6: str
) -> tuple[Path | None, str | None]:
    """Find the backlog item file path and content for a given backlog id6."""
    from agent_workflows import backlog as _backlog

    target_id6 = str(item_id6).strip().lower()
    for p in _backlog._iter_items(Path(repo)):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        item = _backlog.parse_item(text)
        if item.id and item.id.lower() == target_id6:
            return p, text
    return None, None


def backlog_graduate_count(
    repo: Path,
    item_id6: str,
    baseline_plan_ids: Sequence[str] | Mapping[str, Any] | set[str] | None = None,
    *,
    host: str = "<host>",
) -> list[tuple[str, str, str]]:
    """Verify BACKLOG-GRADUATE-COUNT: accepts existing active plans carrying From-Backlog as continued output,
    refusing only when (a) no active linked plan remains, (b) an unlinked new plan was created,
    or (c) this action introduced a second Set.
    """
    repo = Path(repo)
    baseline_ids: set[str] = set()
    if baseline_plan_ids is not None:
        if isinstance(baseline_plan_ids, Mapping):
            baseline_ids = set(baseline_plan_ids.keys())
        else:
            baseline_ids = set(baseline_plan_ids)

    all_linked = existing_handoff_plans(repo, "backlog", item_id6)
    pre_existing_linked = [p for p in all_linked if p.id6 in baseline_ids]
    new_linked = [p for p in all_linked if p.id6 not in baseline_ids]

    # Find new plans linking a different item (or none)
    unlinked_new_plans: list[str] = []
    for p, text in _ce._iter_plan_ipds(repo):
        p_id = _extract_plan_id(p, text)
        if p_id not in baseline_ids:
            if _read_from_backlog(text) != item_id6:
                unlinked_new_plans.append(p_id)

    # Condition (a): after the turn there is no active plan linking the item at all
    if not all_linked:
        msg = (
            f"[BACKLOG-GRADUATE-COUNT] Backlog {item_id6} produced 0 linked IPDs; "
            "expected at least one, each carrying From-Backlog. Quarantine the action, "
            f"reconcile them, run aw check all, then: aw {host} run {item_id6}"
        )
        return [("BACKLOG-GRADUATE-COUNT", item_id6, msg)]

    # Condition (b): a new plan links a different item (or none)
    if unlinked_new_plans:
        unlinked_str = ", ".join(sorted(unlinked_new_plans))
        msg = (
            f"[BACKLOG-GRADUATE-COUNT] Backlog {item_id6} produced new plan(s) ({unlinked_str}) "
            f"linking a different item or none; expected each carrying From-Backlog. Quarantine the action, "
            f"reconcile them, run aw check all, then: aw {host} run {item_id6}"
        )
        return [("BACKLOG-GRADUATE-COUNT", item_id6, msg)]

    # Condition (c): THIS ACTION INTRODUCED A SECOND SET
    pre_existing_sets = {
        p.set if p.set is not None else p.id6 for p in pre_existing_linked
    }
    if pre_existing_linked:
        conflicting_new = [
            np
            for np in new_linked
            if (np.set if np.set is not None else np.id6) not in pre_existing_sets
        ]
        if conflicting_new:
            pre_ids_str = ", ".join(sorted(p.id6 for p in pre_existing_linked))
            pre_sets_str = ", ".join(sorted(pre_existing_sets))
            new_ids_str = ", ".join(sorted(np.id6 for np in conflicting_new))
            new_sets_str = ", ".join(
                sorted(
                    {np.set if np.set is not None else np.id6 for np in conflicting_new}
                )
            )
            msg = (
                f"[BACKLOG-GRADUATE-COUNT] Backlog {item_id6} introduced a second Set: "
                f"pre-existing active plan(s) ({pre_ids_str}) carry Set(s) {pre_sets_str}, "
                f"but new plan(s) ({new_ids_str}) carry Set(s) {new_sets_str}. "
                f"Quarantine the action, reconcile them, run aw check all, then: aw {host} run {item_id6}"
            )
            return [("BACKLOG-GRADUATE-COUNT", item_id6, msg)]
    else:
        new_sets = {np.set if np.set is not None else np.id6 for np in new_linked}
        if len(new_sets) > 1:
            all_new_ids = ", ".join(sorted(np.id6 for np in new_linked))
            new_sets_str = ", ".join(sorted(new_sets))
            msg = (
                f"[BACKLOG-GRADUATE-COUNT] Backlog {item_id6} introduced multiple Sets: "
                f"new plan(s) ({all_new_ids}) span Sets {new_sets_str}. "
                f"Quarantine the action, reconcile them, run aw check all, then: aw {host} run {item_id6}"
            )
            return [("BACKLOG-GRADUATE-COUNT", item_id6, msg)]

    return []


def backlog_graduate_set(
    repo: Path,
    item_id6: str,
    produced_paths: Sequence[Path | str],
    *,
    host: str,
    run_id: str,
    state: Mapping[str, Any],
    asker: Any = None,
    runner: Any = None,
) -> list[tuple[str, str, str]]:
    """Verify BACKLOG-GRADUATE-SET: every produced orchestrator plan is ready for review.

    Pass criterion (25kzda 4.9):
      Every produced orchestrator plan, evaluated by Section 2.5d (the probe may be asked).
      Every produced orchestrator is ready for review; a passing verdict is recorded for its current text;
      only then may the item be set graduated.
    """
    repo = Path(repo)
    findings: list[tuple[str, str, str]] = []

    from agent_workflows import orchestrator_readiness as _orch_readiness
    from agent_workflows import runner_shared as _rs

    retry_budget = _rs.frozen_retry_budget(state)

    for p_raw in produced_paths:
        p = Path(p_raw)
        if not p.is_absolute():
            p = repo / p
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        doc = _lint.parse(text)
        if (doc.meta_fields.get("Kind") or "").strip() != "orchestrator":
            continue

        plan_id = _extract_plan_id(p, text)
        readiness = _orch_readiness.review_readiness(
            repo,
            p,
            ask=True,
            host=host,
            state=state,
            asker=asker,
            runner=runner,
            retry_budget=retry_budget,
        )
        if not readiness.ready:
            findings_str = _format_orchestrator_findings(readiness.findings, plan_id)
            msg = (
                f"[BACKLOG-GRADUATE-SET] Orchestrator {plan_id} produced from backlog {item_id6} "
                f"is not ready for review: {findings_str}. "
                f"Fix it with the IPD authoring tools, then: aw {host} run resume {run_id}"
            )
            findings.append(("BACKLOG-GRADUATE-SET", plan_id, msg))

    return findings


def backlog_graduate_ipd(
    repo: Path,
    item_id6: str,
    produced_paths: Sequence[Path | str],
    *,
    host: str = "<host>",
    run_id: str = "<run-id>",
    continued_ids: Container[str] | None = None,
) -> list[tuple[str, str, str]]:
    """Verify BACKLOG-GRADUATE-IPD: each produced plan is canonical, to-review, in pending/,
    carries From-Backlog, concrete Scope-Paths, resolved Item-Dependencies, and conformant E/V checklists.

    Pass criterion (25kzda 4.9):
      EVERY generated IPD is canonical, `to-review`, in `pending/`, has resolved `Item-Dependencies`,
      and is conformant.
    """
    repo = Path(repo)
    findings: list[tuple[str, str, str]] = []

    for p_raw in produced_paths:
        plan_id, diags = _check_ipd_conformance(
            repo, p_raw, "From-Backlog", item_id6, continued_ids=continued_ids
        )
        for code, detail in diags:
            msg = (
                f"[BACKLOG-GRADUATE-IPD] IPD {plan_id} generated from backlog {item_id6} "
                f"fails {code}: {detail}. Fix it, then: aw {host} run resume {run_id}"
            )
            findings.append(("BACKLOG-GRADUATE-IPD", plan_id, msg))

    return findings


def backlog_gate_handoff(
    repo: Path,
    item_id6: str,
    produced_paths: Sequence[Path | str],
    *,
    host: str = "<host>",
) -> list[tuple[str, str, str]]:
    """Verify BACKLOG-GATE-HANDOFF: if backlog blocks release R, every generated IPD
    also blocks R before the item is set graduated; all references resolve.

    Pass criterion (25kzda 4.9):
      If backlog blocks release R, every generated IPD (or the generated spec) also blocks R
      before the item is set graduated; all references resolve.
    """
    repo = Path(repo)
    findings: list[tuple[str, str, str]] = []

    _bkl_path, bkl_text = _find_backlog_text_and_path(repo, item_id6)
    bkl_gate: str | None = None
    if bkl_text:
        m_bg = _ce._META_BLOCKS_RELEASE_RE.search(bkl_text)
        bkl_gate = m_bg.group(1).strip() if m_bg else None

    # If backlog does not block a release, no gate handoff requirement on IPD
    if not bkl_gate:
        return []

    for p_raw in produced_paths:
        p = Path(p_raw)
        if not p.is_absolute():
            p = repo / p
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue

        plan_id = _extract_plan_id(p, text)
        m_pg = _ce._META_BLOCKS_RELEASE_RE.search(text)
        plan_gate = m_pg.group(1).strip() if m_pg else None

        if not _ce._same_release(repo, bkl_gate, plan_gate):
            release_val = bkl_gate
            msg = (
                f"[BACKLOG-GATE-HANDOFF] Backlog {item_id6} did not preserve release gate {release_val} on IPD {plan_id}. "
                "Quarantine the handoff, correct the fields, run aw check all, then: "
                f"aw {host} run {item_id6}"
            )
            findings.append(("BACKLOG-GATE-HANDOFF", plan_id, msg))

    return findings


def backlog_cross_tree(
    repo: Path,
    item_id6: str,
    produced_paths: Sequence[Path | str],
    *,
    host: str = "<host>",
) -> list[tuple[str, str, str]]:
    """Verify BACKLOG-CROSS-TREE: no dangling gate, mismatched gate, orphaned live blocker,
    or dangling source link exists across the repository for this handoff.

    Pass criterion (25kzda 4.9):
      No dangling gate, mismatched gate, orphaned live blocker, or dangling source link exists.
    """
    repo = Path(repo)
    findings: list[tuple[str, str, str]] = []

    # Consult all three cross-tree entry points (F-5)
    all_drifts = []
    try:
        all_drifts.extend(_ce.check_release_gates(repo))
    except Exception:
        pass
    try:
        all_drifts.extend(_ce.release_gate_warnings(repo))
    except Exception:
        pass
    try:
        all_drifts.extend(_ce.check_from_spec_dangling(repo))
    except Exception:
        pass

    target_paths: set[str] = set()
    bkl_p, _ = _find_backlog_text_and_path(repo, item_id6)
    if bkl_p:
        try:
            target_paths.add(str(bkl_p.resolve()))
        except Exception:
            pass
        try:
            target_paths.add(str(bkl_p.relative_to(repo)).replace("\\", "/"))
        except ValueError:
            target_paths.add(str(bkl_p).replace("\\", "/"))

    produced_ids: set[str] = set()
    for p_raw in produced_paths:
        p = Path(p_raw)
        if not p.is_absolute():
            p = repo / p
        try:
            target_paths.add(str(p.resolve()))
        except Exception:
            pass
        try:
            target_paths.add(str(p.relative_to(repo)).replace("\\", "/"))
        except ValueError:
            target_paths.add(str(p).replace("\\", "/"))
        try:
            p_text = p.read_text(encoding="utf-8")
            produced_ids.add(_extract_plan_id(p, p_text))
        except OSError:
            pass

    # Filter findings to those located at the item or a produced path
    for drift in all_drifts:
        loc = str(drift.location).replace("\\", "/")
        loc_resolved = ""
        try:
            loc_resolved = str(Path(drift.location).resolve())
        except Exception:
            pass

        matches = (
            item_id6 in loc
            or any(pid in loc for pid in produced_ids)
            or loc in target_paths
            or (loc_resolved and loc_resolved in target_paths)
            or any(loc.endswith(tp) for tp in target_paths if tp)
        )
        if matches:
            if drift.rule == "check.orphaned-live-blocker":
                # Warn-class disposition (E-02): emit as advisory warning on stderr, does not fail the item
                print(
                    f"[BACKLOG-CROSS-TREE] Warning: {drift.rule}: {drift.detail}",
                    file=sys.stderr,
                )
                continue
            msg = (
                f"[BACKLOG-CROSS-TREE] Backlog handoff violates {drift.rule}: {drift.detail}. "
                "Quarantine the item, repair it, run aw check all, then: "
                f"aw {host} run {item_id6}"
            )
            findings.append(("BACKLOG-CROSS-TREE", item_id6, msg))

    return findings


def backlog_graduate_legitimacy(
    repo: Path,
    item_id6: str,
    handoff_commit: str | None = None,
    *,
    status_before: str | None = None,
    host: str = "<host>",
) -> list[tuple[str, str, str]]:
    """Verify BACKLOG-GRADUATE-LEGITIMACY: backlog changed open -> graduated through the setter
    only after the handoff commit; history cites the generated artifacts; the item was NOT set done.

    Pass criterion (25kzda 4.9):
      Backlog changed `open -> graduated` through the setter only after the handoff commit;
      history cites the generated artifacts; the item was NOT set `done`.
    """
    repo = Path(repo)
    msg = (
        f"[BACKLOG-GRADUATE-LEGITIMACY] Backlog {item_id6} was transitioned without a valid handoff, "
        "or was closed `done` instead of `graduated`. Contain the item, restore it with "
        f'aw backlog set open {item_id6} --message "handoff incomplete", then: '
        f"aw {host} run {item_id6}"
    )

    # Clause 1: was NOT set done, and prior status must be 'open' (F-6)
    if status_before != "open":
        return [("BACKLOG-GRADUATE-LEGITIMACY", item_id6, msg)]

    from agent_workflows import backlog as _backlog

    bkl_path, bkl_text = _find_backlog_text_and_path(repo, item_id6)
    if not bkl_path or not bkl_text:
        return [("BACKLOG-GRADUATE-LEGITIMACY", item_id6, msg)]

    item = _backlog.parse_item(bkl_text)
    if item.status != "graduated" or "/graduated/" not in str(bkl_path).replace(
        "\\", "/"
    ):
        return [("BACKLOG-GRADUATE-LEGITIMACY", item_id6, msg)]

    # Clause 2: through setter (Workflow history carries setter record)
    history_records = _backlog._prior_history_records(bkl_text)
    if not history_records:
        return [("BACKLOG-GRADUATE-LEGITIMACY", item_id6, msg)]

    # Clause 4: history cites the generated artifacts
    newest = history_records[0]
    if "graduated" not in newest:
        return [("BACKLOG-GRADUATE-LEGITIMACY", item_id6, msg)]
    if not re.search(r"[a-z0-9]{6}|run-[0-9a-zA-Z]+", newest):
        return [("BACKLOG-GRADUATE-LEGITIMACY", item_id6, msg)]

    # Clause 3: only after the handoff commit (commit ancestry check)
    if handoff_commit:
        import subprocess

        try:
            rel_p = str(bkl_path.relative_to(repo)).replace("\\", "/")
        except ValueError:
            rel_p = str(bkl_path).replace("\\", "/")
        res = subprocess.run(
            ["git", "log", "-n", "1", "--format=%H", "--", rel_p],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        item_commit = res.stdout.strip()
        if not item_commit:
            return [("BACKLOG-GRADUATE-LEGITIMACY", item_id6, msg)]
        if item_commit != handoff_commit:
            res_ancestor = subprocess.run(
                ["git", "merge-base", "--is-ancestor", handoff_commit, item_commit],
                cwd=repo,
                capture_output=True,
                text=True,
            )
            if res_ancestor.returncode != 0:
                return [("BACKLOG-GRADUATE-LEGITIMACY", item_id6, msg)]

    return []

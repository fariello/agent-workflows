"""Orchestrator review readiness and coverage verification.

Spec 25kzda Section 2.5d and ipd-structure-and-linting Section 10 rule 19.

Evaluates whether an orchestrator plan (- Kind: orchestrator) is ready for review:
1. Every row of ## Child IPDs names a child that exists on disk.
2. Every child is to-review, reviewed, approved, auto-approved, or executed;
   a child not in a terminal directory also passes author-checkpoint lint.
3. Checklist rows conform to spec r07vma R1a (IPD-S407).
4. Coverage record is pass and matches the current text fingerprint;
   when ask=True, probes the model if absent or stale.

All first-party imports are function-local.
"""

from __future__ import annotations

import argparse
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, NamedTuple

# Finding codes (stable strings)
CODE_TABLE_UNUSABLE = "child-table-unusable"
CODE_CHILD_UNAUTHORED = "child-unauthored"
CODE_CHILD_OPEN_ENDED = "child-open-ended"
CODE_CHILD_STATUS = "child-status-not-ready"
CODE_CHILD_LINT = "child-lint-failing"
CODE_ROW_NONCONFORMING = "orchestrator-row-nonconforming"
CODE_COVERAGE_ABSENT = "coverage-record-absent"
CODE_COVERAGE_STALE = "coverage-record-stale"
CODE_COVERAGE_FAIL = "coverage-fail"
CODE_COVERAGE_COULD_NOT_ASK = "coverage-could-not-ask"
CODE_COVERAGE_UNKNOWN = "coverage-unknown"

# Condition 4 code set exported for runner consumers (spec 25kzda 2.5d / Order 04 5etev3)
CONDITION_4_CODES: frozenset[str] = frozenset(
    {
        CODE_COVERAGE_ABSENT,
        CODE_COVERAGE_STALE,
        CODE_COVERAGE_FAIL,
        CODE_COVERAGE_COULD_NOT_ASK,
        CODE_COVERAGE_UNKNOWN,
    }
)

# Remedy text constants satisfying spec r07vma R7:
# states invariant, forbids deleting checklist, names legitimate remedies.
REMEDY_CHILD_UNAUTHORED = (
    "author the missing child and its row; do not delete the checklist"
)
REMEDY_CHILD_OPEN_ENDED = (
    "author the missing child and its row; do not delete the checklist"
)
REMEDY_TABLE_UNUSABLE = (
    "author the missing child and its row; do not delete the checklist"
)
REMEDY_CHILD_STATUS = (
    "bring the child to `to-review` with `aw ipd set to-review <child-id6>`"
)
REMEDY_CHILD_LINT = "fix the child's named lint finding"
REMEDY_ROW_NONCONFORMING = (
    "move the step to a child with dependencies that put it in the right order, "
    "or remove it because it is redundant; do not delete the checklist"
)
REMEDY_COVERAGE_RECORD = "run `aw ipd coverage <id6>`"
REMEDY_COVERAGE_FAIL = (
    "assign the quoted obligation by id6 to a child in the table or add a child for it; "
    "do not delete the checklist"
)
REMEDY_COVERAGE_COULD_NOT_ASK = "retry with `aw ipd coverage <id6>`"

REMEDIES: dict[str, str] = {
    CODE_TABLE_UNUSABLE: REMEDY_TABLE_UNUSABLE,
    CODE_CHILD_UNAUTHORED: REMEDY_CHILD_UNAUTHORED,
    CODE_CHILD_OPEN_ENDED: REMEDY_CHILD_OPEN_ENDED,
    CODE_CHILD_STATUS: REMEDY_CHILD_STATUS,
    CODE_CHILD_LINT: REMEDY_CHILD_LINT,
    CODE_ROW_NONCONFORMING: REMEDY_ROW_NONCONFORMING,
    CODE_COVERAGE_ABSENT: REMEDY_COVERAGE_RECORD,
    CODE_COVERAGE_STALE: REMEDY_COVERAGE_RECORD,
    CODE_COVERAGE_FAIL: REMEDY_COVERAGE_FAIL,
    CODE_COVERAGE_COULD_NOT_ASK: REMEDY_COVERAGE_COULD_NOT_ASK,
    CODE_COVERAGE_UNKNOWN: REMEDY_COVERAGE_RECORD,
}

_ORDER_TOKEN_RE = re.compile(r"^(?:order\s*)?(?P<order>\d+)$", re.IGNORECASE)
_READY_CHILD_STATUSES = frozenset(
    {"to-review", "reviewed", "approved", "auto-approved", "executed"}
)


class Finding(NamedTuple):
    """One reason an orchestrator plan is not ready for review."""

    code: str
    subject: str
    detail: str
    remedy: str


class ReviewReadiness(NamedTuple):
    """The aggregate review-readiness evaluation for an IPD."""

    applies: bool
    ready: bool
    findings: tuple[Finding, ...] = ()
    id6: str = ""
    setid: str = ""
    cached: bool = False
    calls: int = 0
    written: bool = False
    committed: bool = False


_BATCH_META_RE = re.compile(r"^- (Id|Set|Order|Kind|Status):\s*([^\n]+)", re.MULTILINE)


def resolve_all_set_memberships(repo: Path | str) -> dict[str, Any]:
    """Scan the plans tree once and return {setid: SetMembership} for fast batch lookups."""
    from agent_workflows import runner_shared as _rs

    root = Path(repo)
    candidates: list[Path] = []
    for base in (root / ".aw" / "records" / "plans", root / ".agents" / "plans"):
        if base.is_dir():
            for p in sorted(base.rglob("*.ipd.md")):
                if p.name not in ("README.md", "INDEX.md", "STATUS.md"):
                    candidates.append(p)

    from agent_workflows import selectors as _sel

    grouped: dict[str, list[_rs.SetMember]] = {}
    for path in sorted(candidates):
        hdr = _sel._read_header(path)
        if hdr is None:
            continue
        region = _sel.metadata_region(hdr)
        meta = dict(_BATCH_META_RE.findall(region))
        id6 = (meta.get("Id") or "").strip()
        if not id6:
            continue
        raw_set = (meta.get("Set") or "").strip()
        setid = raw_set.split("(")[0].strip().split()[0].strip() if raw_set else ""
        if not setid:
            continue
        raw_order = (meta.get("Order") or "").strip()
        try:
            order: int | None = int(raw_order)
        except ValueError:
            order = None
        member = _rs.SetMember(
            id6=id6,
            order=order,
            kind=(meta.get("Kind") or "").strip(),
            status=(meta.get("Status") or "").strip(),
            path=path,
        )
        grouped.setdefault(setid, []).append(member)

    res: dict[str, _rs.SetMembership] = {}
    for setid, members in grouped.items():
        orch: _rs.SetMember | None = None
        children: list[_rs.SetMember] = []
        for m in members:
            if m.is_orchestrator:
                if orch is None:
                    orch = m
                else:
                    children.append(m)
            else:
                children.append(m)
        children.sort(key=lambda m: (m.order is None, m.order or 0, m.id6))
        res[setid] = _rs.SetMembership(
            setid=setid, orchestrator=orch, children=tuple(children)
        )
    return res


def review_readiness(
    repo: Path | str,
    plan_path: Path | str,
    *,
    ask: bool = False,
    model: str | None = None,
    host: str | None = None,
    state: Mapping[str, Any] | None = None,
    asker: Any = None,
    runner: Any = None,
    membership: Any = None,
    retry_budget: int | None = None,
    status_overrides: Mapping[str, str] | None = None,
    suppress_commit: bool = False,
) -> ReviewReadiness:
    """Evaluate whether the orchestrator at `plan_path` is ready for review (spec 25kzda 2.5d).

    Returns a :class:`ReviewReadiness` tuple.
    Non-orchestrator plans return applies=False, ready=True.
    """
    from agent_workflows import coverage_record as _cr
    from agent_workflows import ipd_lint as _ipd_lint
    from agent_workflows import run_selection_policy as _rsp
    from agent_workflows import runner_shared as _rs

    repo_path = Path(repo)
    path = Path(plan_path)
    if not path.is_absolute():
        path = (repo_path / path).resolve()

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return ReviewReadiness(
            applies=False,
            ready=False,
            findings=(
                Finding(
                    code=CODE_TABLE_UNUSABLE,
                    subject=str(plan_path),
                    detail=f"cannot read plan file: {exc}",
                    remedy=REMEDY_TABLE_UNUSABLE,
                ),
            ),
        )

    doc = _ipd_lint.parse(text)
    kind = (doc.meta_fields.get("Kind") or "").strip()
    id6 = (doc.meta_fields.get("Id") or "").strip()
    raw_set = (doc.meta_fields.get("Set") or "").strip()
    setid = raw_set.split("(")[0].strip().split()[0].strip() if raw_set else ""

    if kind != "orchestrator":
        return ReviewReadiness(
            applies=False, ready=True, findings=(), id6=id6, setid=setid
        )

    findings: list[Finding] = []

    # Condition 1: child table rows
    active_membership = membership
    if active_membership is None:
        active_membership = _rs.read_set_membership(repo_path, setid)

    unauthored_tokens, parsed = _rs.find_unauthored_child_rows(text, active_membership)
    if not parsed:
        findings.append(
            Finding(
                code=CODE_TABLE_UNUSABLE,
                subject=id6,
                detail="child table is absent or could not be parsed",
                remedy=REMEDY_TABLE_UNUSABLE,
            )
        )
    else:
        for token in unauthored_tokens:
            if _ORDER_TOKEN_RE.match(token) is None:
                findings.append(
                    Finding(
                        code=CODE_CHILD_OPEN_ENDED,
                        subject=token,
                        detail=f"row {token!r} in '## Child IPDs' is open-ended or unresolvable",
                        remedy=REMEDY_CHILD_OPEN_ENDED,
                    )
                )
            else:
                findings.append(
                    Finding(
                        code=CODE_CHILD_UNAUTHORED,
                        subject=token,
                        detail=f"row {token!r} in '## Child IPDs' resolves to no plan on disk",
                        remedy=REMEDY_CHILD_UNAUTHORED,
                    )
                )

    # Condition 2: children status and lint
    if parsed:
        declared, _ = _rs.parse_declared_child_orders(text)
        children_by_order: dict[int, list[_rs.SetMember]] = {}
        for c in active_membership.children:
            if c.order is not None:
                children_by_order.setdefault(c.order, []).append(c)
        children_by_id6 = {c.id6: c for c in active_membership.children}

        checked_child_ids: set[str] = set()
        for token in declared:
            matched_children: list[_rs.SetMember] = []
            m_ord = _ORDER_TOKEN_RE.match(token)
            if m_ord is not None:
                ord_val = int(m_ord.group("order"))
                matched_children.extend(children_by_order.get(ord_val, []))
            elif token.lower() in children_by_id6:
                matched_children.append(children_by_id6[token.lower()])

            for child in matched_children:
                if child.id6 in checked_child_ids:
                    continue
                checked_child_ids.add(child.id6)

                child_status = (
                    status_overrides.get(child.id6)
                    if (status_overrides and child.id6 in status_overrides)
                    else child.status
                )
                in_terminal = _rsp.is_in_terminal_directory(child.path)
                if child_status == "executed" and in_terminal:
                    # A child under executed/ with Status: executed is ready without being linted
                    continue
                if child_status not in _READY_CHILD_STATUSES:
                    findings.append(
                        Finding(
                            code=CODE_CHILD_STATUS,
                            subject=child.id6,
                            detail=f"child {child.id6} has status {child_status!r} (must be to-review, reviewed, approved, auto-approved, or executed)",
                            remedy=REMEDY_CHILD_STATUS,
                        )
                    )
                else:
                    # Child status is in ready set; lint it if not in terminal directory
                    if not in_terminal:
                        child_lint = _ipd_lint.lint_file(
                            child.path, checkpoint="author", suppress_s408=True
                        )
                        if not child_lint.passing:
                            diag_summary = "; ".join(
                                f"{d.code} {d.message}" for d in child_lint.diagnostics
                            )
                            findings.append(
                                Finding(
                                    code=CODE_CHILD_LINT,
                                    subject=child.id6,
                                    detail=f"child {child.id6} fails author lint: {diag_summary}",
                                    remedy=REMEDY_CHILD_LINT,
                                )
                            )

    # Condition 3: checklist row conformance
    row_result = _ipd_lint.orchestrator_row_conformance(text, doc=doc)
    if not row_result.conforming:
        for r in row_result.findings:
            findings.append(
                Finding(
                    code=CODE_ROW_NONCONFORMING,
                    subject=r.ident or f"line {r.line}",
                    detail=r.message,
                    remedy=REMEDY_ROW_NONCONFORMING,
                )
            )

    # Condition 4: coverage record
    rec = _cr.read(text)
    is_curr = _cr.is_current(text)
    cached = False
    calls = 0
    written = False
    committed = False

    if is_curr:
        cached = True
        calls = 0
        if rec.verdict == _cr.COVERAGE_FAIL:
            if rec.quotes:
                for q in rec.quotes:
                    findings.append(
                        Finding(
                            code=CODE_COVERAGE_FAIL,
                            subject=id6,
                            detail=f"uncovered obligation: {q}",
                            remedy=REMEDY_COVERAGE_FAIL,
                        )
                    )
            else:
                findings.append(
                    Finding(
                        code=CODE_COVERAGE_FAIL,
                        subject=id6,
                        detail="coverage verdict is fail",
                        remedy=REMEDY_COVERAGE_FAIL,
                    )
                )
    else:
        # Not current (absent or stale)
        if not ask:
            cached = False
            calls = 0
            if rec.verdict == _cr.COVERAGE_ABSENT or not rec.fingerprint:
                findings.append(
                    Finding(
                        code=CODE_COVERAGE_ABSENT,
                        subject=id6,
                        detail=f"plan has no coverage record (never checked); run `aw ipd coverage {id6}`",
                        remedy=REMEDY_COVERAGE_RECORD,
                    )
                )
            else:
                findings.append(
                    Finding(
                        code=CODE_COVERAGE_STALE,
                        subject=id6,
                        detail=f"plan changed since the check on {rec.date} (fingerprint mismatch); run `aw ipd coverage {id6}`",
                        remedy=REMEDY_COVERAGE_RECORD,
                    )
                )
        else:
            # ask=True: probe the model
            resolved_host = host or "oc"
            resolved_budget = (
                retry_budget
                if retry_budget is not None
                else _rs.resolve_retry_budget(None, repo=repo_path)
            )
            probe_state: dict[str, Any] = dict(state) if state is not None else {}
            opts = dict(probe_state.get("options") or {})
            if model:
                opts["model"] = model
            if suppress_commit:
                opts["commit"] = False
            probe_state["options"] = opts

            target = _rs.ProbeTarget(
                id6=id6,
                position=0,
                setid=setid,
                path=path,
                text=text,
            )
            outcome = _rs.probe_orchestrator(
                probe_state,
                target,
                repo=repo_path,
                host=resolved_host,
                retry_budget=resolved_budget,
                asker=asker,
                runner=runner,
                commit=(not suppress_commit),
            )
            cached = outcome.cached
            calls = outcome.calls
            written = getattr(outcome, "written", False)
            committed = getattr(outcome, "committed", False)

            if outcome.answer == _rs.PROBE_ANSWER_EXECUTIONS:
                if outcome.quotes:
                    for q in outcome.quotes:
                        findings.append(
                            Finding(
                                code=CODE_COVERAGE_FAIL,
                                subject=id6,
                                detail=f"uncovered obligation: {q}",
                                remedy=REMEDY_COVERAGE_FAIL,
                            )
                        )
                else:
                    findings.append(
                        Finding(
                            code=CODE_COVERAGE_FAIL,
                            subject=id6,
                            detail="coverage verdict is fail",
                            remedy=REMEDY_COVERAGE_FAIL,
                        )
                    )
            elif outcome.answer == _rs.PROBE_ANSWER_COULD_NOT_ASK:
                findings.append(
                    Finding(
                        code=CODE_COVERAGE_COULD_NOT_ASK,
                        subject=id6,
                        detail=f"could not reach coverage probe: {outcome.detail}; retry with `aw ipd coverage {id6}`",
                        remedy=REMEDY_COVERAGE_COULD_NOT_ASK,
                    )
                )
            elif outcome.answer != _rs.PROBE_ANSWER_NO_EXECUTIONS:
                findings.append(
                    Finding(
                        code=CODE_COVERAGE_UNKNOWN,
                        subject=id6,
                        detail=f"unknown probe answer: {outcome.answer} ({outcome.detail})",
                        remedy=REMEDY_COVERAGE_RECORD,
                    )
                )

    ready = len(findings) == 0
    return ReviewReadiness(
        applies=True,
        ready=ready,
        findings=tuple(findings),
        id6=id6,
        setid=setid,
        cached=cached,
        calls=calls,
        written=written,
        committed=committed,
    )


def render_human(result: ReviewReadiness) -> str:
    """Render a human-readable summary of review readiness."""
    if not result.applies:
        return (
            f"Plan {result.id6 or '<unknown>'} is not an orchestrator (not applicable)."
        )
    if result.ready:
        return f"Orchestrator {result.id6} is ready for review."
    lines = [f"Orchestrator {result.id6} is not ready for review:"]
    for f in result.findings:
        lines.append(f"  - [{f.code}] {f.subject}: {f.detail}")
        lines.append(f"    Remedy: {f.remedy}")
    return "\n".join(lines)


def render_agent(
    result: ReviewReadiness, *, cmd: str = "ipd coverage"
) -> dict[str, Any]:
    """Produce a schema-valid aw.agent/v1 result record."""
    outcome = "clean" if result.ready else "findings"
    exit_code = 0 if result.ready else 1
    summary = (
        f"orchestrator {result.id6} is ready for review"
        if result.ready
        else f"orchestrator {result.id6} is not ready for review ({len(result.findings)} finding(s))"
    )
    return {
        "schema": "aw.agent/v1",
        "kind": "result",
        "cmd": cmd,
        "exit": exit_code,
        "outcome": outcome,
        "verified": True,
        "complete": True,
        "summary": summary,
        "data": {
            "id6": result.id6,
            "setid": result.setid,
            "ready": result.ready,
            "cached": result.cached,
            "calls": result.calls,
            "written": result.written,
            "committed": result.committed,
            "finding_codes": [f.code for f in result.findings],
            "findings": [
                {
                    "code": f.code,
                    "subject": f.subject,
                    "detail": f.detail,
                    "remedy": f.remedy,
                }
                for f in result.findings
            ],
        },
    }


def run_coverage(
    args: argparse.Namespace, term: Any = None, context: Any = None
) -> int:
    """CLI implementation of `aw ipd coverage <id6|setid|path>...`."""
    from agent_workflows import agent_schema as _as
    from agent_workflows import ipd_lint as _ipd_lint
    from agent_workflows import runner_profiles as _rp
    from agent_workflows import selectors as _sel
    from agent_workflows.result_types import select_output

    ctx = context or select_output(args)
    cwd = Path.cwd()
    repo_root: Path | None = None
    for anc in [cwd] + list(cwd.parents):
        if (anc / ".aw").is_dir() or (anc / ".agents").is_dir():
            repo_root = anc
            break

    raw_targets = getattr(args, "targets", None) or []
    if not repo_root:
        err_msg = "no agent-workflows project root located"
        if ctx.is_agent or ctx.is_json:
            rec = {
                "schema": _as.SCHEMA_VERSION,
                "kind": "result",
                "cmd": "ipd coverage",
                "exit": 2,
                "outcome": "cannot-run",
                "verified": False,
                "complete": False,
                "summary": err_msg,
                "detail": err_msg,
            }
            print(_as.render_jsonl_record(rec), end="")
            return 2
        print(f"error: {err_msg}")
        return 2

    if not raw_targets:
        err_msg = "no orchestrator selected; specify one or more id6, setid, or path arguments"
        if ctx.is_agent or ctx.is_json:
            rec = {
                "schema": _as.SCHEMA_VERSION,
                "kind": "result",
                "cmd": "ipd coverage",
                "exit": 2,
                "outcome": "cannot-run",
                "verified": False,
                "complete": False,
                "summary": err_msg,
                "detail": err_msg,
            }
            print(_as.render_jsonl_record(rec), end="")
            return 2
        print(f"error: {err_msg}")
        return 2

    # Resolve launch profile for host/model defaults
    host_arg = getattr(args, "host", None)
    model_arg = getattr(args, "model", None)
    no_commit = bool(getattr(args, "no_commit", False))

    resolved_host = host_arg or "oc"
    resolved_model = model_arg
    try:
        cfg = _rp.load()
        resolved = _rp.resolve(
            cfg, runner=resolved_host, model=resolved_model, generic=True
        )
        if not host_arg and resolved.runner:
            resolved_host = resolved.runner
        if not model_arg and resolved.model:
            resolved_model = resolved.model
    except (KeyError, ValueError, AttributeError, OSError):
        resolved_host = host_arg or "oc"

    state: dict[str, Any] = {
        "options": {
            "model": resolved_model or "",
            "runner": resolved_host,
            "commit": not no_commit,
        }
    }

    # Resolve targets to plans
    plan_paths: list[Path] = []
    for token in raw_targets:
        p = Path(token)
        if not p.is_absolute():
            p = (repo_root / p).resolve()
        if p.is_file():
            if p not in plan_paths:
                plan_paths.append(p)
            continue
        resolution = _sel.resolve(repo_root, "plans", token)
        for rp in sorted(resolution.paths):
            if rp not in plan_paths:
                plan_paths.append(rp)

    if not plan_paths:
        err_msg = f"no matching plans found for targets: {raw_targets}"
        if ctx.is_agent or ctx.is_json:
            rec = {
                "schema": _as.SCHEMA_VERSION,
                "kind": "result",
                "cmd": "ipd coverage",
                "exit": 2,
                "outcome": "cannot-run",
                "verified": False,
                "complete": False,
                "summary": err_msg,
                "detail": err_msg,
            }
            print(_as.render_jsonl_record(rec), end="")
            return 2
        print(f"error: {err_msg}")
        return 2

    # Filter to orchestrator plans
    orchestrator_plans: list[Path] = []
    non_orchestrator_plans: list[Path] = []
    for p in plan_paths:
        try:
            doc = _ipd_lint.parse(p.read_text(encoding="utf-8", errors="replace"))
            if doc.meta_fields.get("Kind") == "orchestrator":
                orchestrator_plans.append(p)
            else:
                non_orchestrator_plans.append(p)
        except OSError:
            pass

    if not orchestrator_plans:
        err_msg = "no orchestrator plans selected among targets"
        if ctx.is_agent or ctx.is_json:
            rec = {
                "schema": _as.SCHEMA_VERSION,
                "kind": "result",
                "cmd": "ipd coverage",
                "exit": 2,
                "outcome": "cannot-run",
                "verified": False,
                "complete": False,
                "summary": err_msg,
                "detail": err_msg,
            }
            print(_as.render_jsonl_record(rec), end="")
            return 2
        print(f"error: {err_msg}")
        return 2

    # Run review_readiness(..., ask=True)
    memberships = resolve_all_set_memberships(repo_root)
    results: list[ReviewReadiness] = []
    for orch_path in orchestrator_plans:
        res = review_readiness(
            repo_root,
            orch_path,
            ask=True,
            model=resolved_model,
            host=resolved_host,
            state=state,
            membership=memberships.get(
                _ipd_lint.parse(orch_path.read_text(encoding="utf-8", errors="replace"))
                .meta_fields.get("Set", "")
                .split("(")[0]
                .strip()
                .split()[0]
                .strip()
            ),
            suppress_commit=no_commit,
        )
        results.append(res)

    all_ready = all(r.ready for r in results)
    exit_code = 0 if all_ready else 1

    if ctx.is_agent or ctx.is_json:
        outcome = "clean" if all_ready else "findings"
        summary = (
            f"all {len(results)} selected orchestrator(s) ready for review"
            if all_ready
            else f"{sum(1 for r in results if not r.ready)} of {len(results)} orchestrator(s) not ready for review"
        )
        orch_data = [
            {
                "id6": r.id6,
                "setid": r.setid,
                "ready": r.ready,
                "cached": r.cached,
                "calls": r.calls,
                "written": r.written,
                "committed": r.committed,
                "finding_codes": [f.code for f in r.findings],
                "findings": [
                    {
                        "code": f.code,
                        "subject": f.subject,
                        "detail": f.detail,
                        "remedy": f.remedy,
                    }
                    for f in r.findings
                ],
            }
            for r in results
        ]
        first = orch_data[0] if orch_data else {}
        data_block: dict[str, Any] = {
            "orchestrators": orch_data,
            "id6": first.get("id6", ""),
            "ready": first.get("ready", False),
            "cached": first.get("cached", False),
            "calls": first.get("calls", 0),
            "written": first.get("written", False),
            "committed": first.get("committed", False),
            "finding_codes": first.get("finding_codes", []),
        }
        if non_orchestrator_plans:
            data_block["not_applicable"] = [str(p) for p in non_orchestrator_plans]

        rec = {
            "schema": _as.SCHEMA_VERSION,
            "kind": "result",
            "cmd": "ipd coverage",
            "exit": exit_code,
            "outcome": outcome,
            "verified": True,
            "complete": True,
            "summary": summary,
            "data": data_block,
        }
        print(_as.render_jsonl_record(rec), end="")
        return exit_code

    # Human rendering
    for r in results:
        print(render_human(r))
        if no_commit:
            print(
                f"  (record {'written' if r.written else 'not written'}, commit suppressed by --no-commit)"
            )
        elif r.written:
            print(f"  (record written, committed={r.committed})")
    for non_p in non_orchestrator_plans:
        print(f"Plan {non_p.name} is not an orchestrator (not applicable).")
    return exit_code

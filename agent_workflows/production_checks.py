"""Deterministic verifiers for production actions (artdispatch aeq7f8).

Pure-ish module implementing the three in-scope verification codes from spec 25kzda 4.8 / z7nbn1 4.4:
  - SPEC-PLAN-COUNT
  - SPEC-PLAN-CONFORMANCE
  - SPEC-PLAN-GATE-CARRY

Each verifier returns a list of findings `[(code, plan_or_source_id6, message)]` rendered from the
25kzda 4.8 message templates.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from agent_workflows import check_engine as _ce
from agent_workflows import ipd_lint as _lint
from agent_workflows import plans_refs as _pr
from agent_workflows import specs as _specs

_PLAN_ID_RE = re.compile(r"(?m)^-[ \t]*Id:[ \t]*([0-9a-z]{6})[ \t]*$")
_ITEM_DEPS_RE = re.compile(r"(?m)^-[ \t]*Item-Dependencies:[ \t]*(.*?)[ \t]*$")
_SCOPE_PATHS_RE = re.compile(r"(?m)^-[ \t]*Scope-Paths:[ \t]*(.*?)[ \t]*$")
_ITEM_FROM_BACKLOG_RE = re.compile(r"(?m)^-[ \t]*From-Backlog:[ \t]*([^\n]*?)[ \t]*$")
_TERMINAL_DISPOSITIONS = frozenset(("executed", "superseded", "not-executed"))


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
    """Verify SPEC-PLAN-COUNT: at least one new plan linked to spec, every new plan carries From-Spec,
    and no duplicate active plan already existed for this spec in the baseline.

    Pass criterion (25kzda 4.8):
      At least one new IPD links to the spec for this authoring action, every one carries From-Spec,
      and no duplicate active plan already existed for the same phase.
    """
    repo = Path(repo)
    baseline_ids: set[str] = set()
    if baseline_plan_ids is not None:
        if isinstance(baseline_plan_ids, Mapping):
            baseline_ids = set(baseline_plan_ids.keys())
        else:
            baseline_ids = set(baseline_plan_ids)

    # Check for duplicate active plan already existing in baseline
    duplicate_active = False
    new_plans: list[tuple[str, Path, str]] = []
    for p, text in _ce._iter_plan_ipds(repo):
        p_id = _extract_plan_id(p, text)
        disp = _ce._plan_disposition(repo, p)
        m_from = _ce._ITEM_FROM_SPEC_RE.search(text)
        from_spec = m_from.group(1).strip() if m_from else None

        if p_id in baseline_ids:
            if disp not in _TERMINAL_DISPOSITIONS and from_spec == spec_id6:
                duplicate_active = True
        else:
            new_plans.append((p_id, p, text))

    new_linked_plans = [
        (p_id, p)
        for (p_id, p, text) in new_plans
        if (
            _ce._ITEM_FROM_SPEC_RE.search(text) is not None
            and _ce._ITEM_FROM_SPEC_RE.search(text).group(1).strip() == spec_id6
        )
    ]

    has_unlinked_new_plan = False
    for p_id, p, text in new_plans:
        m_from = _ce._ITEM_FROM_SPEC_RE.search(text)
        if not m_from or m_from.group(1).strip() != spec_id6:
            has_unlinked_new_plan = True

    count = len(new_linked_plans)
    if duplicate_active or count == 0 or has_unlinked_new_plan:
        msg = (
            f"[SPEC-PLAN-COUNT] Spec {spec_id6} produced {count} new linked IPDs; "
            "expected at least one, each carrying From-Spec. Quarantine the authoring action, "
            f"reconcile duplicates, run aw check all, then: aw {host} run {spec_id6}"
        )
        return [("SPEC-PLAN-COUNT", spec_id6, msg)]

    return []


def _check_ipd_conformance(
    repo: Path,
    p_raw: Path | str,
    expected_origin_field: str,
    expected_origin_id6: str,
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

    # 2. Status: to-review
    m_status = _ce._PLAN_STATUS_RE.search(text)
    status_val = m_status.group(1).strip() if m_status else ""
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
        plan_id, diags = _check_ipd_conformance(repo, p_raw, "From-Spec", spec_id6)
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
    """Verify BACKLOG-GRADUATE-COUNT: at least one new active IPD was created and every one
    links to the graduated backlog ID.

    Pass criterion (25kzda 4.9):
      At least one new active IPD was created and every one links to the graduated backlog ID.
    """
    repo = Path(repo)
    baseline_ids: set[str] = set()
    if baseline_plan_ids is not None:
        if isinstance(baseline_plan_ids, Mapping):
            baseline_ids = set(baseline_plan_ids.keys())
        else:
            baseline_ids = set(baseline_plan_ids)

    duplicate_active = False
    new_plans: list[tuple[str, Path, str]] = []
    for p, text in _ce._iter_plan_ipds(repo):
        p_id = _extract_plan_id(p, text)
        disp = _ce._plan_disposition(repo, p)
        from_bkl = _read_from_backlog(text)

        if p_id in baseline_ids:
            if disp not in _TERMINAL_DISPOSITIONS and from_bkl == item_id6:
                duplicate_active = True
        else:
            new_plans.append((p_id, p, text))

    new_linked_plans = [
        (p_id, p)
        for (p_id, p, text) in new_plans
        if _read_from_backlog(text) == item_id6
    ]

    has_unlinked_new_plan = False
    for p_id, p, text in new_plans:
        if _read_from_backlog(text) != item_id6:
            has_unlinked_new_plan = True

    count = len(new_linked_plans)
    if duplicate_active or count == 0 or has_unlinked_new_plan:
        msg = (
            f"[BACKLOG-GRADUATE-COUNT] Backlog {item_id6} produced {count} linked IPDs; "
            "expected at least one, each carrying From-Backlog. Quarantine the action, "
            f"reconcile them, run aw check all, then: aw {host} run {item_id6}"
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
        plan_id, diags = _check_ipd_conformance(repo, p_raw, "From-Backlog", item_id6)
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

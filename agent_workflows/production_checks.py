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
from pathlib import Path
from typing import Any, Mapping, Sequence

from agent_workflows import check_engine as _ce
from agent_workflows import ipd_lint as _lint
from agent_workflows import plans_refs as _pr
from agent_workflows import specs as _specs

_PLAN_ID_RE = re.compile(r"(?m)^-[ \t]*Id:[ \t]*([0-9a-z]{6})[ \t]*$")
_ITEM_DEPS_RE = re.compile(r"(?m)^-[ \t]*Item-Dependencies:[ \t]*(.*?)[ \t]*$")
_SCOPE_PATHS_RE = re.compile(r"(?m)^-[ \t]*Scope-Paths:[ \t]*(.*?)[ \t]*$")
_TERMINAL_DISPOSITIONS = frozenset(("executed", "superseded", "not-executed"))


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
        p = Path(p_raw)
        if not p.is_absolute():
            p = repo / p
        try:
            text = p.read_text(encoding="utf-8")
        except OSError as exc:
            msg = (
                f"[SPEC-PLAN-CONFORMANCE] Generated IPD <unknown> for spec {spec_id6} "
                f"fails check.readable: cannot read {p}: {exc}. Fix it with the IPD authoring tools, "
                f"then: aw {host} run resume {run_id}"
            )
            findings.append(("SPEC-PLAN-CONFORMANCE", "<unknown>", msg))
            continue

        plan_id = _extract_plan_id(p, text)

        # 1. Bucket: sits under pending/
        disp = _ce._plan_disposition(repo, p)
        if disp != "pending":
            msg = (
                f"[SPEC-PLAN-CONFORMANCE] Generated IPD {plan_id} for spec {spec_id6} "
                f"fails check.plan-bucket: plan is in {disp!r}, expected 'pending'. "
                f"Fix it with the IPD authoring tools, then: aw {host} run resume {run_id}"
            )
            findings.append(("SPEC-PLAN-CONFORMANCE", plan_id, msg))

        # 2. Status: to-review
        m_status = _ce._PLAN_STATUS_RE.search(text)
        status_val = m_status.group(1).strip() if m_status else ""
        if status_val != "to-review":
            msg = (
                f"[SPEC-PLAN-CONFORMANCE] Generated IPD {plan_id} for spec {spec_id6} "
                f"fails check.plan-status: plan status is {status_val!r}, expected 'to-review'. "
                f"Fix it with the IPD authoring tools, then: aw {host} run resume {run_id}"
            )
            findings.append(("SPEC-PLAN-CONFORMANCE", plan_id, msg))

        # 3. From-Spec: carries spec_id6
        m_from = _ce._ITEM_FROM_SPEC_RE.search(text)
        from_spec = m_from.group(1).strip() if m_from else ""
        if from_spec != spec_id6:
            msg = (
                f"[SPEC-PLAN-CONFORMANCE] Generated IPD {plan_id} for spec {spec_id6} "
                "fails check.from-spec: missing or invalid From-Spec field. "
                f"Fix it with the IPD authoring tools, then: aw {host} run resume {run_id}"
            )
            findings.append(("SPEC-PLAN-CONFORMANCE", plan_id, msg))

        # 4. Scope-Paths: concrete (not empty, not TODO, not grandfathered)
        m_scope = _SCOPE_PATHS_RE.search(text)
        scope_val = m_scope.group(1).strip() if m_scope else ""
        if not scope_val or "TODO" in scope_val or scope_val == "grandfathered":
            msg = (
                f"[SPEC-PLAN-CONFORMANCE] Generated IPD {plan_id} for spec {spec_id6} "
                "fails check.scope-paths: Scope-Paths must be concrete (not empty, not TODO, not grandfathered). "
                f"Fix it with the IPD authoring tools, then: aw {host} run resume {run_id}"
            )
            findings.append(("SPEC-PLAN-CONFORMANCE", plan_id, msg))
        else:
            paths, is_gf, errs = _lint.S.parse_scope_paths(scope_val)
            if is_gf or errs or not paths:
                detail = "; ".join(errs) if errs else "invalid scope paths"
                msg = (
                    f"[SPEC-PLAN-CONFORMANCE] Generated IPD {plan_id} for spec {spec_id6} "
                    f"fails check.scope-paths: {detail}. "
                    f"Fix it with the IPD authoring tools, then: aw {host} run resume {run_id}"
                )
                findings.append(("SPEC-PLAN-CONFORMANCE", plan_id, msg))

        # 5. Item-Dependencies: resolved (not unresolved)
        m_deps = _ITEM_DEPS_RE.search(text)
        deps_val = m_deps.group(1).strip() if m_deps else ""
        if "unresolved" in deps_val.lower():
            msg = (
                f"[SPEC-PLAN-CONFORMANCE] Generated IPD {plan_id} for spec {spec_id6} "
                f"fails check.item-dependencies: Item-Dependencies contains 'unresolved'. "
                f"Fix it with the IPD authoring tools, then: aw {host} run resume {run_id}"
            )
            findings.append(("SPEC-PLAN-CONFORMANCE", plan_id, msg))

        # 6. Lints conforming at review-finalize
        lint_res = _lint.lint_file(p, checkpoint="review-finalize")
        if lint_res.disposition != _lint.S.DISPOSITION_CONFORMING:
            for diag in lint_res.diagnostics:
                msg = (
                    f"[SPEC-PLAN-CONFORMANCE] Generated IPD {plan_id} for spec {spec_id6} "
                    f"fails {diag.code}: {diag.message}. "
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

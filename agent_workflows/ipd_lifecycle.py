"""Single-IPD execution lifecycle: the fail-closed `aw ipd begin` execution-start receipt.

IPD ipdgates Order 03 (`xjbvu2`). Before an approved IPD's execution begins, there must be a durable,
independently-inspectable proof that the plan passed the `pre-execution` gate at a known base HEAD,
with its requirements and `Scope-Paths` FROZEN. `aw ipd begin <plan> --actor <agent/model>` produces
that proof: a LOCAL, gitignored receipt under ``.aw/state/ipd-lifecycle/<id6>.receipt.json``.

Fail-closed contract (the whole point): ANY failure mode - a non-conforming `pre-execution` lint
(exit 1) or an unrunnable lint (exit 2), a dirty/ambiguous baseline, a missing/empty ``--actor``, an
unresolvable/duplicate plan selector, or an interrupted write - MUST leave NO valid receipt and
therefore NO execution authority. The receipt is written ATOMICALLY (temp file + ``os.replace``) so an
interrupted write can never leave a partial/valid receipt, and it is RESUMABLE (re-reading returns the
same receipt deterministically).

Receipt binding (OQ-01 resolved): {plan Id, plan content digest, frozen requirement/scope digest,
base HEAD, actor/model, timestamp, frozen ``Scope-Paths``}. LIFETIME (OQ-01, human-resolved): the
receipt PERSISTS across unrelated intervening commits (HEAD movement does NOT invalidate it, so a
concurrent multi-agent workflow on disjoint file sets never needs a needless re-``begin``); it is
invalidated only by (a) a change to the plan's own content digest, or (b) an intervening commit that
touched a path INSIDE this plan's ``Scope-Paths``. This module records the base HEAD + frozen
``Scope-Paths`` that make (b)'s path-overlap collision check possible; ENFORCING that check is Order 04
(`aw ipd finalize`), not here.

Scope fence (Order 03): this module produces ONLY the begin receipt. It does NOT finalize, transition,
or remove any bypass; it does not mutate the plan or any tracked file.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

# Receipt schema version (bump on an incompatible receipt-shape change).
RECEIPT_SCHEMA_VERSION = 1

# Exit-code convention shared with `aw ipd lint` (0 ok / 1 findings / 2 cannot-run).
EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_CANNOT_RUN = 2

_RECEIPT_SUBDIR = ("state", "ipd-lifecycle")


class BeginResult(NamedTuple):
    """The outcome of an `aw ipd begin` attempt.

    ``exit_code`` follows the shared convention. ``receipt`` is the written receipt dict on success
    (EXIT_OK), else None. ``receipt_path`` is where a receipt was (or would be) written. ``message``
    is a human-readable summary/diagnostic. ``findings`` carries structured lint findings when the
    gate failed.
    """

    exit_code: int
    receipt: Optional[Dict[str, Any]]
    receipt_path: Optional[Path]
    message: str
    findings: Tuple[str, ...] = ()


# --------------------------------------------------------------------------------------
# Pure helpers
# --------------------------------------------------------------------------------------


def _repo_root(start: Path) -> Path:
    """Resolve the git worktree top-level for ``start`` (falls back to ``start`` when not a repo)."""
    from agent_workflows.run_evidence import get_worktree_path

    return Path(get_worktree_path(str(start)))


def receipt_dir(repo_root: Path) -> Path:
    """The gitignored directory that holds begin receipts: ``<repo>/.aw/state/ipd-lifecycle/``."""
    return repo_root.joinpath(".aw", *_RECEIPT_SUBDIR)


def receipt_path_for(repo_root: Path, plan_id: str) -> Path:
    """The receipt path for a plan id6: ``.aw/state/ipd-lifecycle/<id6>.receipt.json``."""
    return receipt_dir(repo_root) / f"{plan_id}.receipt.json"


def plan_content_digest(text: str) -> str:
    """A stable sha256 over the plan's exact bytes (identity of the plan content at begin time)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _requirements_from_plan(text: str) -> Dict[str, List[str]]:
    """Extract the freezable requirement categories from an IPD's parsed structure.

    Maps the IPD's own structure onto the four `run_freeze` categories:
      * ``scope``      = the declared ``Scope-Paths`` entries (or the free-form ``Scope:`` prose when
                          the plan is grandfathered / declares no real allowlist), so the frozen scope
                          fence is bound into the receipt digest;
      * ``must``       = each execution leaf's action text (the E-* items);
      * ``validation`` = each validation leaf's row text (the V-* items).
    An ``output`` category is intentionally omitted (IPDs do not declare it structurally).
    """
    from agent_workflows import ipd_lint as _lint
    from agent_workflows import ipd_schema as _schema

    doc = _lint.parse(text)

    scope: List[str] = []
    sp_value = doc.meta_fields.get(_schema.META_SCOPE_PATHS)
    if sp_value:
        paths, is_grandfathered, _errs = _schema.parse_scope_paths(sp_value)
        if is_grandfathered:
            # Freeze the sentinel plus the free-form Scope: prose so the scope fence is still bound.
            scope.append("grandfathered")
            free_scope = doc.meta_fields.get("Scope")
            if free_scope:
                scope.append(free_scope)
        else:
            scope.extend(paths)
    else:
        free_scope = doc.meta_fields.get("Scope")
        if free_scope:
            scope.append(free_scope)

    must = [lf.text for lf in doc.exec_leaves if lf.kind == "E" and lf.text.strip()]
    validation = [
        lf.text for lf in doc.valid_leaves if lf.kind == "V" and lf.text.strip()
    ]

    requirements: Dict[str, List[str]] = {}
    if scope:
        requirements["scope"] = scope
    if must:
        requirements["must"] = must
    if validation:
        requirements["validation"] = validation
    return requirements


def _frozen_scope_paths(text: str) -> List[str]:
    """The plan's declared ``Scope-Paths`` entries (empty list for a grandfathered/absent value).

    This is the concrete path allowlist Order 04's finalize compares against; for a grandfathered
    plan there is no machine allowlist, so an empty list is recorded (finalize treats that as
    'no declared path fence to reconcile' and relies on the free-form scope in the frozen digest).
    """
    from agent_workflows import ipd_schema as _schema
    from agent_workflows import ipd_lint as _lint

    doc = _lint.parse(text)
    sp_value = doc.meta_fields.get(_schema.META_SCOPE_PATHS)
    if not sp_value:
        return []
    paths, is_grandfathered, _errs = _schema.parse_scope_paths(sp_value)
    if is_grandfathered:
        return []
    return list(paths)


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Write ``payload`` as pretty JSON atomically (temp file in the same dir + ``os.replace``).

    An interrupted write leaves the temp file (cleaned up) and NEVER a partial destination file, so
    a crash mid-write cannot produce a partial/valid receipt.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".receipt-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(data)
        os.replace(tmp, str(path))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def read_receipt(repo_root: Path, plan_id: str) -> Optional[Dict[str, Any]]:
    """Return the stored receipt for ``plan_id`` (or None if absent/unreadable/corrupt)."""
    p = receipt_path_for(repo_root, plan_id)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def receipt_is_current(receipt: Dict[str, Any], plan_text: str) -> bool:
    """True when ``receipt`` still matches the plan's CURRENT content digest (digest-invalidation).

    A plan-digest change invalidates a prior receipt (OQ-01 rule (a)). The path-overlap collision
    rule (b) is enforced by Order 04's finalize, not here.
    """
    return receipt.get("plan_content_digest") == plan_content_digest(plan_text)


# --------------------------------------------------------------------------------------
# The begin transaction
# --------------------------------------------------------------------------------------


def begin(
    repo_root: Path,
    plan_path: Path,
    actor: str,
    *,
    timestamp: str,
) -> BeginResult:
    """Run the fail-closed pre-execution gate and, on success, write the atomic begin receipt.

    Ordered fail-closed checks (each leaves NO valid receipt on failure):
      1. ``--actor`` is present and non-empty;
      2. the plan file exists and parses to a valid ``- Id:`` id6;
      3. the ``pre-execution`` lint disposition is ``conforming`` (else exit 1; an unrunnable lint or
         internal error is exit 2);
      4. the worktree baseline is clean and unambiguous (a dirty tree or an unversioned/absent HEAD
         is refused with an actionable diagnostic);
      5. the plan requirements + ``Scope-Paths`` freeze successfully.
    Only when all pass is the receipt built and written atomically.
    """
    from agent_workflows import ipd_lint as _lint
    from agent_workflows import ipd_schema as _schema
    from agent_workflows import run_freeze
    from agent_workflows.run_evidence import get_git_dirty_digest, get_git_head

    # 1. actor required (non-empty).
    if not actor or not actor.strip():
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            None,
            "aw ipd begin requires a non-empty --actor <agent/model> (no execution authority "
            "without an attributed actor).",
        )
    actor = actor.strip()

    # 2. plan file must exist and carry a valid id6.
    if not plan_path.is_file():
        return BeginResult(
            EXIT_CANNOT_RUN, None, None, f"plan file not found: {plan_path}"
        )
    try:
        plan_text = plan_path.read_text(encoding="utf-8")
    except OSError as exc:
        return BeginResult(
            EXIT_CANNOT_RUN, None, None, f"cannot read plan file {plan_path}: {exc}"
        )
    doc = _lint.parse(plan_text)
    plan_id = (doc.meta_fields.get("Id") or "").strip()
    if not plan_id or not _schema._core.is_valid_id6(plan_id):
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            None,
            f"plan {plan_path} has no valid 6-char '- Id:' handle; cannot bind a receipt.",
        )

    rcpt_path = receipt_path_for(repo_root, plan_id)

    # 3. pre-execution gate (invoke the linter; never reimplement it).
    try:
        lint_res = _lint.lint_file(plan_path, checkpoint="pre-execution")
    except Exception as exc:  # unrunnable/internal linter failure = cannot-run.
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            rcpt_path,
            f"pre-execution lint could not run (treated as fail-closed): {exc}",
        )
    if not lint_res.passing:
        finding_lines = tuple(f"{d.code} {d.message}" for d in lint_res.diagnostics)
        return BeginResult(
            EXIT_FINDINGS,
            None,
            rcpt_path,
            f"pre-execution gate did NOT conform ({lint_res.disposition}); no receipt written. "
            "Repair the plan and re-run.",
            findings=finding_lines,
        )

    # 4. clean, unambiguous baseline.
    head = get_git_head(str(repo_root))
    if head == "unversioned":
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            rcpt_path,
            "cannot capture a base HEAD (not a git repo, or git unavailable); baseline is "
            "ambiguous, refusing to issue a receipt.",
        )
    dirty = get_git_dirty_digest(str(repo_root))
    if dirty != "clean":
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            rcpt_path,
            "refusing to begin on a DIRTY worktree: uncommitted changes make the frozen base "
            "ambiguous (a later scope comparison could not attribute changes to this execution). "
            "Commit or stash unrelated work first, then re-run `aw ipd begin`.",
        )

    # 5. freeze requirements + Scope-Paths.
    try:
        frozen = run_freeze.freeze_requirements(_requirements_from_plan(plan_text))
    except ValueError as exc:
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            rcpt_path,
            f"cannot freeze the plan's requirements/scope: {exc}",
        )

    receipt: Dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "kind": "ipd_begin_receipt",
        "plan_id": plan_id,
        "plan_path": _repo_relative(repo_root, plan_path),
        "plan_content_digest": plan_content_digest(plan_text),
        "requirement_digest": frozen.requirement_digest,
        "scope_paths": _frozen_scope_paths(plan_text),
        "base_head": head,
        "actor": actor,
        "timestamp": timestamp,
        "pre_execution": {
            "disposition": lint_res.disposition,
            "advisories": [f"{a.code} {a.message}" for a in lint_res.advisories],
        },
    }

    # Atomic write - an interrupted write leaves no valid receipt.
    _atomic_write_json(rcpt_path, receipt)

    return BeginResult(
        EXIT_OK,
        receipt,
        rcpt_path,
        f"begin receipt written for {plan_id} at base {head[:12]} (actor {actor}).",
    )


def _repo_relative(repo_root: Path, path: Path) -> str:
    """Return ``path`` relative to ``repo_root`` (POSIX), or the resolved absolute path if outside."""
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


# --------------------------------------------------------------------------------------
# CLI entry (`aw ipd begin`)
# --------------------------------------------------------------------------------------


def run_begin(args) -> int:
    """Entry point for `aw ipd begin <plan> --actor <agent/model>`. Returns 0/1/2."""
    from agent_workflows import selectors
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic as OutDiag,
        select_output,
    )

    ctx = select_output(args)

    selector = getattr(args, "plan", None)
    actor = getattr(args, "actor", None)
    repo_root = _repo_root(Path(getattr(args, "dir", None) or "."))
    now = getattr(args, "_now", None) or _utc_now()

    def _emit(exit_code: int, status: str, summary: str, diags=None, data=None) -> int:
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="ipd begin",
                status=status,
                exit_code=exit_code,
                summary=summary,
                diagnostics=list(diags or []),
                data=data or {},
            )
            return get_renderer(ctx).emit(res, ctx)
        prefix = {EXIT_OK: "", EXIT_FINDINGS: "findings: ", EXIT_CANNOT_RUN: "error: "}[
            exit_code
        ]
        print(f"{prefix}{summary}")
        for d in diags or []:
            print(f"  {d.rule} {d.detail}")
        return exit_code

    # Resolve the plan selector (must resolve to exactly one plan).
    if not selector:
        return _emit(
            EXIT_CANNOT_RUN, "cannot-run", "aw ipd begin requires a <plan> selector."
        )
    resolution = selectors.resolve(repo_root, "plans", selector)
    if not resolution.paths:
        return _emit(
            EXIT_CANNOT_RUN,
            "cannot-run",
            f"no plan matched selector {selector!r}.",
        )
    if len(resolution.paths) > 1:
        cand = ", ".join(p.name for p in resolution.paths)
        return _emit(
            EXIT_CANNOT_RUN,
            "cannot-run",
            f"selector {selector!r} is ambiguous ({resolution.kind}); matched: {cand}.",
        )
    plan_path = resolution.paths[0]

    result = begin(repo_root, plan_path, actor or "", timestamp=now)

    if result.exit_code == EXIT_OK and result.receipt is not None:
        receipt = result.receipt
        rcpt_path = result.receipt_path or receipt_path_for(
            repo_root, receipt["plan_id"]
        )
        return _emit(
            EXIT_OK,
            "clean",
            result.message,
            data={
                "receipt_path": _repo_relative(repo_root, rcpt_path),
                "plan_id": receipt["plan_id"],
                "base_head": receipt["base_head"],
                "requirement_digest": receipt["requirement_digest"],
            },
        )
    if result.exit_code == EXIT_FINDINGS:
        diags = [
            OutDiag(
                location=str(plan_path), rule="IPD-BEGIN", detail=f, severity="error"
            )
            for f in result.findings
        ]
        return _emit(EXIT_FINDINGS, "findings", result.message, diags=diags)
    return _emit(EXIT_CANNOT_RUN, "cannot-run", result.message)


def _utc_now() -> str:
    """An ISO-8601 UTC timestamp (deterministic format; value depends on the clock)."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

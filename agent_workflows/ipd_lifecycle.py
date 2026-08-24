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
# The finalize transaction (Order v7e88a): atomic terminal transition + scope comparison
# --------------------------------------------------------------------------------------


class FinalizeResult(NamedTuple):
    """The outcome of an `aw ipd finalize` attempt.

    ``exit_code`` follows the shared 0/1/2 convention. ``commit`` is the lifecycle commit hash on
    success. ``evidence`` carries the captured pre-execution/pre-transition/post-transition gate
    outputs and the scope comparison. ``findings`` lists refusal reasons.
    """

    exit_code: int
    commit: Optional[str]
    message: str
    evidence: Dict[str, Any] = {}
    findings: Tuple[str, ...] = ()


def _git(repo_root: Path, args: List[str]) -> Tuple[int, str, str]:
    """Run a git command in ``repo_root``; return (returncode, stdout, stderr)."""
    import subprocess

    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _paths_changed_by_this_execution(repo_root: Path, base_head: str) -> List[str]:
    """Repo-relative paths this execution changed: committed since base + current working tree.

    Union of `git diff --name-only <base>..HEAD` (commits made since the frozen base) and
    `git status --porcelain` (staged + unstaged + untracked working-tree changes). This is the set
    of paths the CURRENT worktree presents relative to the frozen base - i.e. what THIS execution
    produced (unrelated concurrent commits on disjoint paths are handled by the intervening-commit
    collision check, not here).
    """
    changed: set = set()
    rc, out, _err = _git(repo_root, ["diff", "--name-only", f"{base_head}..HEAD"])
    if rc == 0:
        changed.update(ln.strip() for ln in out.splitlines() if ln.strip())
    rc, out, _err = _git(repo_root, ["status", "--porcelain"])
    if rc == 0:
        for ln in out.splitlines():
            # porcelain: 'XY <path>' or 'XY <old> -> <new>' for renames.
            body = ln[3:] if len(ln) > 3 else ln.strip()
            if " -> " in body:
                body = body.split(" -> ", 1)[1]
            p = body.strip().strip('"')
            if p:
                changed.add(p)
    return sorted(changed)


def _intervening_commits_touching(
    repo_root: Path, base_head: str, scope_paths: List[str]
) -> List[str]:
    """Paths inside ``scope_paths`` that an intervening commit (base..HEAD) modified.

    Per OQ-01 rule (b): a commit made SINCE the frozen base that touched a path INSIDE the plan's
    Scope-Paths is a same-file collision (another actor edited this plan's declared territory), which
    finalize must refuse. Returns the offending in-scope paths (empty when none / no allowlist).
    """
    if not scope_paths:
        return []
    rc, out, _err = _git(repo_root, ["diff", "--name-only", f"{base_head}..HEAD"])
    if rc != 0:
        return []
    committed = [ln.strip() for ln in out.splitlines() if ln.strip()]
    hits = [p for p in committed if any(_scope_match(p, pat) for pat in scope_paths)]
    return sorted(set(hits))


def _scope_match(path: str, pattern: str) -> bool:
    """fnmatch a repo-relative path against a Scope-Paths entry (literal, dir-bounded, or glob).

    A trailing-slash directory entry (`tests/`) or a bare directory (`agent_workflows`) matches any
    path beneath it; an entry containing a glob is matched via fnmatch; a literal file matches
    exactly. This mirrors the Scope-Paths grammar (Order oorry1).
    """
    import fnmatch

    p = path.strip().replace("\\", "/")
    pat = pattern.strip().replace("\\", "/")
    if not pat:
        return False
    # Directory-bounded: `dir/` or `dir/**` matches anything under dir/.
    if pat.endswith("/"):
        return p == pat[:-1] or p.startswith(pat)
    if pat.endswith("/**"):
        base = pat[:-3]
        return p == base or p.startswith(base + "/")
    if "*" in pat or "?" in pat or "[" in pat:
        # A dir/* style also should match nested files, so try both fnmatch and prefix.
        if fnmatch.fnmatch(p, pat):
            return True
        # `dir/*.py` should not match nested, but `dir/**/*.py` should; fnmatch handles `**` loosely,
        # so also accept a leading-directory prefix match for `dir/**...`.
        if "**" in pat:
            prefix = pat.split("**", 1)[0].rstrip("/")
            return bool(prefix) and (p == prefix or p.startswith(prefix + "/"))
        return False
    # Literal path: exact match, or a directory prefix (a bare `agent_workflows` covers the tree).
    return p == pat or p.startswith(pat + "/")


def _is_implicitly_allowed(path: str, plan_rel: str) -> bool:
    """True when ``path`` is an implicit lifecycle-artifact allowance (Order oorry1) or the plan file.

    The plan's own file (moving through the lifecycle) and the plans/records index refresh are always
    in scope and need not be declared.
    """
    from agent_workflows import ipd_schema as _schema

    p = path.strip().replace("\\", "/")
    if p == plan_rel:
        return True
    # The plan file's destination (executed/…) and its pending origin both count as the plan itself.
    if p.startswith(".aw/records/plans/") and p.endswith(Path(plan_rel).name):
        return True
    for spec in _schema.scope_paths_implicit_allowances():
        if _scope_match(p, spec):
            return True
    return False


def finalize_precheck(
    repo_root: Path, plan_path: Path
) -> Tuple[int, str, Dict[str, Any], Tuple[str, ...]]:
    """E-01: validate the begin receipt + pre-transition lint + scope comparison. No mutation.

    Returns ``(exit_code, message, evidence, findings)``. exit_code 0 means the precheck PASSED and
    the forward transition may proceed; 1 means a refusal (findings explain it); 2 means cannot-run.
    Leaves the plan unmoved in every case.
    """
    from agent_workflows import ipd_lint as _lint

    evidence: Dict[str, Any] = {}

    plan_text = plan_path.read_text(encoding="utf-8")
    doc = _lint.parse(plan_text)
    plan_id = (doc.meta_fields.get("Id") or "").strip()
    if not plan_id:
        return EXIT_CANNOT_RUN, f"plan {plan_path} has no '- Id:' handle.", evidence, ()

    # 1. matching begin receipt must exist and still match the plan digest.
    receipt = read_receipt(repo_root, plan_id)
    if receipt is None:
        return (
            EXIT_FINDINGS,
            f"no begin receipt for {plan_id}: run `aw ipd begin` first (fail-closed: no receipt = "
            "no execution authority).",
            evidence,
            (f"missing begin receipt at {receipt_path_for(repo_root, plan_id)}",),
        )
    if not receipt_is_current(receipt, plan_text):
        return (
            EXIT_FINDINGS,
            f"the begin receipt for {plan_id} is STALE: the plan content changed since begin; "
            "re-run `aw ipd begin`.",
            evidence,
            ("plan content digest no longer matches the receipt",),
        )
    evidence["pre_execution"] = receipt.get("pre_execution", {})
    base_head = str(receipt.get("base_head") or "").strip()
    if not base_head or base_head == "unversioned":
        return (
            EXIT_CANNOT_RUN,
            f"the begin receipt for {plan_id} has no usable base HEAD; cannot compute a scope delta.",
            evidence,
            (),
        )
    evidence["base_head"] = base_head
    scope_paths: List[str] = list(receipt.get("scope_paths") or [])
    evidence["scope_paths"] = scope_paths

    # 2. pre-transition lint (fail closed).
    try:
        lint_res = _lint.lint_file(plan_path, checkpoint="pre-transition")
    except Exception as exc:
        return (
            EXIT_CANNOT_RUN,
            f"pre-transition lint could not run (fail-closed): {exc}",
            evidence,
            (),
        )
    evidence["pre_transition"] = {
        "disposition": lint_res.disposition,
        "diagnostics": [f"{d.code} {d.message}" for d in lint_res.diagnostics],
    }
    if not lint_res.passing:
        return (
            EXIT_FINDINGS,
            f"pre-transition gate did NOT conform ({lint_res.disposition}); plan left unmoved.",
            evidence,
            tuple(f"{d.code} {d.message}" for d in lint_res.diagnostics),
        )

    # 3. scope comparison against the frozen base + literal Scope-Paths (OQ-01 path-overlap rule).
    plan_rel = _repo_relative(repo_root, plan_path)
    changed = _paths_changed_by_this_execution(repo_root, base_head)
    evidence["changed_paths"] = changed

    findings: List[str] = []
    # (a) unexplained-path refusal: a path THIS execution changed that is outside Scope-Paths.
    #     A grandfathered plan (empty literal allowlist) has NO machine path fence, so this
    #     per-path refusal is inapplicable (Order oorry1: grandfathered = advisory, no allowlist);
    #     only the implicit lifecycle allowances + free-form scope apply. See DECISION register.
    if scope_paths:
        for p in changed:
            if _is_implicitly_allowed(p, plan_rel):
                continue
            if not any(_scope_match(p, pat) for pat in scope_paths):
                findings.append(
                    f"unexplained path outside Scope-Paths: {p} (declared: {scope_paths})"
                )
    # (b) intervening-commit COMPUTATION: which in-Scope-Paths paths were touched by a commit since
    #     base. This is the substrate Order 06's adversarial concurrency/rollback matrix builds on to
    #     distinguish a genuine FOREIGN same-file collision from THIS execution's own sanctioned
    #     in-scope commits (begin -> do work -> commit -> finalize is the normal single-actor flow, in
    #     which the in-scope commits ARE this execution's work and must NOT be refused). Finalize
    #     (this Order) therefore COMPUTES + surfaces the candidate set in evidence but does not make it
    #     a blanket blocking refusal here; authorship-aware enforcement is Order 06 (DECISION register).
    collisions = _intervening_commits_touching(repo_root, base_head, scope_paths)
    collisions = [c for c in collisions if not _is_implicitly_allowed(c, plan_rel)]

    evidence["scope_audit"] = {
        "grandfathered": not scope_paths,
        "in_scope": bool(scope_paths) and not findings,
        "unexplained_paths": list(findings),
        "intervening_in_scope_commits": collisions,
        "findings": list(findings),
    }
    if findings:
        return (
            EXIT_FINDINGS,
            "finalize REFUSED: changed paths did not stay within the reviewed Scope-Paths "
            "(plan left unmoved).",
            evidence,
            tuple(findings),
        )
    return (
        EXIT_OK,
        "precheck passed (receipt valid, pre-transition conforming, in scope).",
        evidence,
        (),
    )


def _refresh_plans_index_fail_loud(repo_root: Path) -> None:
    """Refresh the owned plans index FAIL-LOUD (never the status_set swallow).

    Regenerates the index, then verifies freshness via `--check`. Raises RuntimeError on any
    failure so finalize treats a stale/failed index as a TRANSACTION failure, not a silent success.
    """
    import argparse

    from agent_workflows import plans_index as _pidx

    # Regenerate (no swallow: any exception propagates).
    _pidx.run_index(
        argparse.Namespace(
            dir=str(repo_root),
            check=False,
            as_agent=False,
            agent=False,
            json=False,
            no_color=True,
            limit=None,
            quiet=True,
        )
    )
    # Verify it is now fresh.
    rc = _pidx.run_index(
        argparse.Namespace(
            dir=str(repo_root),
            check=True,
            agent=False,
            json=False,
            no_color=True,
            limit=None,
            quiet=True,
        )
    )
    if rc != 0:
        raise RuntimeError(
            "owned plans index refresh did not converge (aw index plans --check nonzero); "
            "finalize fails closed rather than committing a stale index."
        )


def finalize(
    repo_root: Path,
    plan_path: Path,
    actor: str,
    message: str,
    *,
    apply: bool = False,
) -> FinalizeResult:
    """The atomic terminal transaction for one IPD (E-01 precheck + E-02 forward transition).

    On the happy path (``apply=True``): validate receipt + pre-transition lint + scope comparison
    (E-01); then append the attributed history entry, set terminal status, move the plan, refresh the
    owned index fail-loud, create the path-scoped lifecycle commit, run post-transition lint, and
    report the commit + captured three-phase gate evidence. Any precheck refusal leaves the plan
    unmoved. (Two-way reconciliation is Order 05; rollback/failure semantics are Order 06.)
    """
    import argparse

    from agent_workflows import ipd_lint as _lint
    from agent_workflows import status_set as _ss

    if not actor or not actor.strip():
        return FinalizeResult(
            EXIT_CANNOT_RUN, None, "finalize requires a non-empty --actor."
        )
    if not message or not message.strip():
        return FinalizeResult(
            EXIT_CANNOT_RUN, None, "finalize requires a non-empty --message."
        )
    if not plan_path.is_file():
        return FinalizeResult(
            EXIT_CANNOT_RUN, None, f"plan file not found: {plan_path}"
        )

    exit_code, msg, evidence, findings = finalize_precheck(repo_root, plan_path)
    if exit_code != EXIT_OK:
        return FinalizeResult(exit_code, None, msg, evidence, findings)

    if not apply:
        return FinalizeResult(
            EXIT_OK,
            None,
            "precheck passed; re-run with --apply to perform the terminal transaction.",
            evidence,
            (),
        )

    # --- E-02 forward transition (precheck passed) ---
    rec = _ss.read_artifact_record(plan_path, repo_root)
    if rec is None:
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"could not read plan record for {plan_path}.",
            evidence,
        )
    ns = argparse.Namespace(actor=actor, message=message, by_human=False)
    try:
        dest_path, norm_status = _ss.apply_status_change(rec, "executed", repo_root, ns)
    except Exception as exc:
        return FinalizeResult(
            EXIT_CANNOT_RUN, None, f"terminal status/move failed: {exc}", evidence
        )

    # Owned-index refresh MUST fail loud (never the status_set swallow).
    try:
        _refresh_plans_index_fail_loud(repo_root)
    except Exception as exc:
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"owned plans-index refresh FAILED ({exc}); transaction aborted (plan moved on disk but "
            "NOT committed). Re-run after repair; rollback semantics are Order 06.",
            evidence,
        )

    # Path-scoped lifecycle commit: only this plan's own files (old path, new path, index).
    plans_dir = dest_path.parent.parent
    commit_paths = [
        _repo_relative(repo_root, plan_path),
        _repo_relative(repo_root, dest_path),
        _repo_relative(repo_root, plans_dir / "INDEX.json"),
        _repo_relative(repo_root, plans_dir / "INDEX.md"),
    ]
    # Stage only the existing ones.
    stage = [
        p
        for p in commit_paths
        if (repo_root / p).exists() or p == _repo_relative(repo_root, plan_path)
    ]
    rc, _out, err = _git(repo_root, ["add", "--", *stage])
    if rc != 0:
        return FinalizeResult(
            EXIT_CANNOT_RUN, None, f"git add failed: {err.strip()}", evidence
        )
    commit_msg = f"lifecycle({rec.id6 or 'plan'}): finalize {rec.id6 or plan_path.name} -> executed\n\n{message}\n\nExecuted by {actor} via aw ipd finalize."
    rc, _out, err = _git(repo_root, ["commit", "-m", commit_msg, "--", *stage])
    if rc != 0:
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"lifecycle commit failed: {err.strip()} (plan moved but not committed; rollback is "
            "Order 06).",
            evidence,
        )
    rc, out, _err = _git(repo_root, ["rev-parse", "HEAD"])
    commit_hash = out.strip() if rc == 0 else None

    # Post-transition lint on the MOVED file.
    try:
        post = _lint.lint_file(dest_path, checkpoint="post-transition")
        evidence["post_transition"] = {
            "disposition": post.disposition,
            "diagnostics": [f"{d.code} {d.message}" for d in post.diagnostics],
        }
    except Exception as exc:
        evidence["post_transition"] = {"error": str(exc)}

    return FinalizeResult(
        EXIT_OK,
        commit_hash,
        f"finalized {rec.id6 or plan_path.name} -> executed at {commit_hash[:12] if commit_hash else '?'} "
        f"(actor {actor}).",
        evidence,
        (),
    )


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


# --------------------------------------------------------------------------------------
# CLI entry (`aw ipd finalize`)
# --------------------------------------------------------------------------------------


def run_finalize(args) -> int:
    """Entry point for `aw ipd finalize <plan> --actor --message [--apply]`. Returns 0/1/2."""
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
    message = getattr(args, "message", None)
    apply = bool(getattr(args, "apply", False))
    repo_root = _repo_root(Path(getattr(args, "dir", None) or "."))

    def _emit(exit_code: int, status: str, summary: str, diags=None, data=None) -> int:
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="ipd finalize",
                status=status,
                exit_code=exit_code,
                summary=summary,
                diagnostics=list(diags or []),
                data=data or {},
            )
            return get_renderer(ctx).emit(res, ctx)
        prefix = {EXIT_OK: "", EXIT_FINDINGS: "refused: ", EXIT_CANNOT_RUN: "error: "}[
            exit_code
        ]
        print(f"{prefix}{summary}")
        for d in diags or []:
            print(f"  {d.rule} {d.detail}")
        return exit_code

    if not selector:
        return _emit(
            EXIT_CANNOT_RUN, "cannot-run", "aw ipd finalize requires a <plan> selector."
        )
    resolution = selectors.resolve(repo_root, "plans", selector)
    if not resolution.paths:
        return _emit(
            EXIT_CANNOT_RUN, "cannot-run", f"no plan matched selector {selector!r}."
        )
    if len(resolution.paths) > 1:
        cand = ", ".join(p.name for p in resolution.paths)
        return _emit(
            EXIT_CANNOT_RUN,
            "cannot-run",
            f"selector {selector!r} is ambiguous ({resolution.kind}); matched: {cand}.",
        )
    plan_path = resolution.paths[0]

    result = finalize(repo_root, plan_path, actor or "", message or "", apply=apply)

    if result.exit_code == EXIT_OK:
        return _emit(
            EXIT_OK,
            "clean",
            result.message,
            data={"commit": result.commit, "evidence": result.evidence},
        )
    if result.exit_code == EXIT_FINDINGS:
        diags = [
            OutDiag(
                location=str(plan_path), rule="IPD-FINALIZE", detail=f, severity="error"
            )
            for f in result.findings
        ]
        return _emit(EXIT_FINDINGS, "findings", result.message, diags=diags)
    return _emit(EXIT_CANNOT_RUN, "cannot-run", result.message)

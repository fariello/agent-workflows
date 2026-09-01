"""Atomic workflow primitives: `aw work begin` / `aw test` / `aw commit` / `aw finish`
(agentadhere Phase 2, IPD 8dto0g).

Findings bu9yij (sections 4.3, 7.4) concluded that reliable process adherence comes from replacing
a chain of remembered duties with a small number of ATOMIC actions that (a) validate BEFORE they
mutate, (b) make the compliant path the EASY path, and (c) produce evidence AT the action boundary.
This module supplies the four primitives, each calling the phase-1 shared policy engine
(``check_engine``) and REUSING the existing machinery rather than forking a second path:

  * ``aw work begin <ipd>``  - validate the plan via the phase-1 engine (fail closed on findings) and
    allocate/associate an ISOLATED git worktree via ``worktree_lease.allocate_worktree`` + a recorded
    lease. No second worktree path.
  * ``aw test <ipd> -- <cmd>`` - run ``<cmd>``, capture stdout/stderr/exit + env metadata (command
    line, cwd, timestamp, git HEAD/tree), and bind that evidence to the current tree/commit under the
    plan's LOCAL run-record area. HONEST label: the evidence is locally produced and forgeable by a
    privileged local agent (findings 6.6); non-forgeable / CI-reproduced evidence is deferred to
    phases 5/7.
  * ``aw commit <ipd> -- <paths>`` - compute the plan's allowed scope from its ``Scope-Paths``, refuse
    when the staged index holds ANY out-of-scope change, run the phase-1 engine, and commit ONLY the
    declared in-scope paths by REUSING ``git_commit_helper.offer_commit`` (path-scoped ``git add --
    <paths>``, never ``add -A``/``-a``, never ``--no-verify``, never push). No second commit path.
    Optionally carries run-ownership trailers (``AW-Run``/``AW-Item``) so a checker can identify which
    run and work item produced a commit; absent them the message is composed exactly as before.
  * ``aw finish <ipd>`` - verify the plan's required evidence (from ``aw test``) is present and bound
    to the current tree, then perform ONLY a VALID NON-AUTHORITATIVE status transition through the
    tooled ``aw set`` path. It MUST NOT perform the authoritative terminal ``executed`` transition
    (that stays with ``aw ipd finalize``), MUST NOT push, and MUST NOT tag.

The isolation, commit, and lifecycle machinery is REUSED (``worktree_lease``, ``git_commit_helper``,
``status_set``); this module only orchestrates validate-then-act + evidence capture. The local
evidence + lease state live under the gitignored ``.aw/state/`` tree so they never pollute the
tracked worktree. Stdlib-only, Python 3.9 compatible.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows import check_engine as _ce
from agent_workflows import git_commit_helper as _gch
from agent_workflows import selectors as _selectors
from agent_workflows import worktree_lease as _wl

# The gitignored local state root for work-primitive artifacts (evidence + lease records). Under
# `.aw/state/` (already gitignored) so it is never committed and is honestly local/forgeable.
_WORK_STATE_SUBDIR = ".aw/state/work"

# Terminal/authoritative statuses `aw finish` must NEVER set (that authority stays with
# `aw ipd finalize`). Everything else in the plan status sequence is a valid non-authoritative step.
_AUTHORITATIVE_STATUSES = frozenset({"executed", "done"})


# --------------------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------------------


def _git(repo_root: Path, args: List[str]) -> Tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args], cwd=str(repo_root), capture_output=True, text=True, check=False
    )
    return proc.returncode, proc.stdout, proc.stderr


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _split_remainder(raw: List[str]) -> Tuple[Optional[str], List[str]]:
    """Split an ``argparse.REMAINDER`` capture into (--dir value, tokens-after--).

    ``argparse.REMAINDER`` greedily captures EVERYTHING after the last positional, including any
    options (e.g. ``--dir .``) the user placed after the plan selector and before the ``--`` command
    marker. This helper recovers a ``--dir <value>`` that landed inside the remainder and returns the
    command tokens that follow the ``--`` marker (or the whole remainder if there is no marker).
    """
    if not raw:
        return None, []
    dir_val: Optional[str] = None
    # Everything after the FIRST `--` marker is the verbatim command/paths.
    if "--" in raw:
        idx = raw.index("--")
        pre, post = raw[:idx], raw[idx + 1 :]
    else:
        pre, post = [], list(raw)
    # Recover a `--dir <val>` (or `--dir=<val>`) that argparse swallowed into the remainder's pre part.
    i = 0
    while i < len(pre):
        tok = pre[i]
        if tok == "--dir" and i + 1 < len(pre):
            dir_val = pre[i + 1]
            i += 2
            continue
        if tok.startswith("--dir="):
            dir_val = tok[len("--dir=") :]
            i += 1
            continue
        i += 1
    # If there was no `--` marker, `pre` is empty and `post` is the whole remainder; strip a swallowed
    # leading `--dir <val>` from post in that case too.
    if not raw or "--" not in raw:
        cleaned: List[str] = []
        j = 0
        while j < len(post):
            if post[j] == "--dir" and j + 1 < len(post):
                dir_val = post[j + 1]
                j += 2
                continue
            if post[j].startswith("--dir="):
                dir_val = post[j][len("--dir=") :]
                j += 1
                continue
            cleaned.append(post[j])
            j += 1
        post = cleaned
    return dir_val, post


def _resolve_repo_root(args: argparse.Namespace) -> Path:
    from agent_workflows.project_context import resolve_verb_repo_root

    return resolve_verb_repo_root(getattr(args, "dir", None))


def _resolve_plan(
    repo_root: Path, selector: Optional[str]
) -> Tuple[Optional[Path], Optional[str]]:
    """Resolve a plan selector to exactly one plan path, or (None, message)."""
    if not selector:
        return None, "a <plan> selector is required"
    res = _selectors.resolve(repo_root, "plans", selector)
    if not res.paths:
        return None, f"no plan matched selector {selector!r}"
    if len(res.paths) > 1:
        cand = ", ".join(p.name for p in res.paths)
        return None, f"selector {selector!r} is ambiguous ({res.kind}); matched: {cand}"
    return res.paths[0], None


def _plan_id6(text: str) -> Optional[str]:
    import re

    m = re.search(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$", text)
    return m.group(1) if m else None


def _plan_status(text: str) -> Optional[str]:
    import re

    m = re.search(r"(?m)^- Status:\s*(\S+)\s*$", text)
    return m.group(1) if m else None


def _plan_scope_paths(text: str) -> Tuple[List[str], bool]:
    """The plan's declared Scope-Paths (entries, is_grandfathered). Empty list when absent."""
    from agent_workflows import ipd_lint as _lint
    from agent_workflows import ipd_schema as _schema

    doc = _lint.parse(text)
    sp_value = doc.meta_fields.get(_schema.META_SCOPE_PATHS)
    if not sp_value:
        return [], False
    paths, is_grandfathered, _errs = _schema.parse_scope_paths(sp_value)
    return paths, is_grandfathered


def _work_dir(repo_root: Path, plan_id: str) -> Path:
    return repo_root / _WORK_STATE_SUBDIR / plan_id


def _evidence_path(repo_root: Path, plan_id: str) -> Path:
    return _work_dir(repo_root, plan_id) / "test-evidence.json"


def _lease_path(repo_root: Path, plan_id: str) -> Path:
    return _work_dir(repo_root, plan_id) / "work-lease.json"


def _atomic_write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".aw-work-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _validate_plan_via_engine(repo_root: Path, plan_path: Path) -> List[_core.Drift]:
    """Run the phase-1 shared policy engine over plans and return ONLY the findings for this plan
    (fail-closed inputs to `aw work begin`). Advisory (info-severity) findings are excluded so a
    mere draft-readiness nudge does not block starting work."""
    drift = _ce.check_type(repo_root, "plans")
    target = str(plan_path.resolve())
    out: List[_core.Drift] = []
    for d in drift:
        try:
            same = str(Path(d.location).resolve()) == target
        except OSError:
            same = d.location == str(plan_path)
        if not same:
            continue
        enriched = _ce.enrich_drift(d)
        if enriched.severity == "info":
            continue  # advisory nudge, not a blocking finding
        out.append(enriched)
    return out


# --------------------------------------------------------------------------------------
# aw work begin
# --------------------------------------------------------------------------------------


def run_work_begin(args: argparse.Namespace) -> int:
    """`aw work begin <ipd>`: validate the plan (fail closed) then allocate an isolated worktree."""
    repo_root = _resolve_repo_root(args)
    selector = getattr(args, "plan", None) or getattr(args, "selector", None)
    plan_path, err = _resolve_plan(repo_root, selector)
    if err:
        print(f"error: {err}")
        return 2
    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read plan: {exc}")
        return 2
    plan_id = _plan_id6(text) or plan_path.stem

    # Validate BEFORE mutating (findings 7.4): fail closed on any blocking finding.
    findings = _validate_plan_via_engine(repo_root, plan_path)
    if findings:
        print(
            f"aw work begin: refusing to start - {len(findings)} finding(s) on {plan_path.name}:"
        )
        for d in findings:
            print(f"  {d.rule}: {d.detail}")
        return 1

    # Allocate an isolated worktree via the SHARED lease machinery (no second worktree path).
    try:
        handle = _wl.allocate_worktree(repo_root, plan_id)
    except _wl.WorktreeError as exc:
        print(f"aw work begin: worktree allocation failed: {exc}")
        return 2

    lease = {
        "plan_id": plan_id,
        "plan_path": str(plan_path.relative_to(repo_root)),
        "lane_id": handle.lane_id,
        "worktree_path": str(handle.path),
        "branch": handle.branch,
        "base_commit": handle.base_commit,
        "allocated_at": _now_iso(),
    }
    _atomic_write_json(_lease_path(repo_root, plan_id), lease)
    print(
        f"aw work begin: validated {plan_path.name}; allocated worktree {handle.path} "
        f"(branch {handle.branch}, base {handle.base_commit[:12]})"
    )
    return 0


# --------------------------------------------------------------------------------------
# aw test
# --------------------------------------------------------------------------------------


def run_test(args: argparse.Namespace) -> int:
    """`aw test <ipd> -- <cmd>`: run the command, capture evidence bound to the current tree/commit."""
    selector = getattr(args, "plan", None)
    dir_val, cmd = _split_remainder(list(getattr(args, "cmd_argv", None) or []))
    if dir_val and not getattr(args, "dir", None):
        args.dir = dir_val
    repo_root = _resolve_repo_root(args)
    plan_path, err = _resolve_plan(repo_root, selector)
    if err:
        print(f"error: {err}")
        return 2
    if not cmd:
        print(
            "error: aw test requires a command after `--` (e.g. `aw test <ipd> -- pytest`)"
        )
        return 2
    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read plan: {exc}")
        return 2
    plan_id = _plan_id6(text) or plan_path.stem

    # Capture the git HEAD + tree the evidence is bound to (BEFORE running, the state under test).
    _rc, head_out, _e = _git(repo_root, ["rev-parse", "HEAD"])
    git_head = head_out.strip() or None
    _rc, tree_out, _e = _git(repo_root, ["rev-parse", "HEAD^{tree}"])
    git_tree = tree_out.strip() or None

    started = _now_iso()
    proc = subprocess.run(
        cmd, cwd=str(repo_root), capture_output=True, text=True, check=False
    )
    ended = _now_iso()

    evidence = {
        "schema_version": "aw.work-evidence/v1",
        "plan_id": plan_id,
        # HONEST label (findings 6.6): local evidence is forgeable by a privileged local agent;
        # non-forgeable / CI-reproduced evidence is a later phase (5/7).
        "assurance": "local-forgeable",
        "command": cmd,
        "cwd": str(repo_root),
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "git_head": git_head,
        "git_tree": git_tree,
        "started_at": started,
        "ended_at": ended,
    }
    _atomic_write_json(_evidence_path(repo_root, plan_id), evidence)
    passed = proc.returncode == 0
    print(
        f"aw test: recorded evidence for {plan_id} (exit {proc.returncode}, "
        f"{'PASS' if passed else 'FAIL'}) bound to tree {(git_tree or '?')[:12]}; "
        f"local-forgeable, not a CI-reproduced authority boundary"
    )
    # `aw test` reports the command's own exit faithfully (evidence is never silently 'passed').
    return 0 if passed else 1


# --------------------------------------------------------------------------------------
# aw commit
# --------------------------------------------------------------------------------------


def _staged_paths(repo_root: Path) -> List[str]:
    rc, out, _e = _git(repo_root, ["diff", "--name-only", "--cached"])
    if rc != 0:
        return []
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def _in_scope(path: str, scope_paths: List[str], plan_rel: str) -> bool:
    from agent_workflows import ipd_lifecycle as _life

    if _life._is_implicitly_allowed(path, plan_rel):
        return True
    return any(_life._scope_match(path, pat) for pat in scope_paths)


def _trailers_from_args(args: argparse.Namespace) -> List[str]:
    """Resolve optional run-ownership trailers from ``args``, defaulting to NONE.

    Threading only (IPD m73aet E-03): NO new CLI flag is added, because the values come from a live
    run and the runner wiring is deliberately deferred - a public flag whose only consumer does not
    exist yet is a contract taken on for nothing. A programmatic caller (the eventual runner)
    supplies them on the namespace instead:

      * ``trailers`` - preformatted ``"Key: value"`` strings, used as-is; or
      * ``run_id`` / ``item_id6`` - the raw ids, formatted into the canonical ``AW-Run``/``AW-Item``
        keys by ``git_commit_helper.run_item_trailers`` so the key spelling is single-sourced.

    Absent both, this returns ``[]`` and ``aw commit`` composes its message exactly as before. In
    particular the plan's own id6 is NOT auto-derived into an ``AW-Item`` trailer: that would change
    the default behavior of an existing caller, which this plan's scope excludes.
    """

    explicit = list(getattr(args, "trailers", None) or [])
    if explicit:
        return explicit
    return _gch.run_item_trailers(
        getattr(args, "run_id", None), getattr(args, "item_id6", None)
    )


def run_commit(args: argparse.Namespace) -> int:
    """`aw commit <ipd> -- <paths>`: scope-refuse out-of-scope staged, run the engine, commit in-scope
    paths via the SHARED git_commit_helper (no forked commit path, no add -A, no push).

    Optionally carries run-ownership trailers (``AW-Run``/``AW-Item``); see :func:`_trailers_from_args`.
    """
    selector = getattr(args, "plan", None)
    raw = list(getattr(args, "path_argv", None) or [])
    dir_val, paths = _split_remainder(raw)
    if dir_val and not getattr(args, "dir", None):
        args.dir = dir_val
    # Recover -m/--message and --no-commit that argparse.REMAINDER swallowed from the pre-`--` part.
    pre = raw[: raw.index("--")] if "--" in raw else []
    i = 0
    while i < len(pre):
        if pre[i] in ("-m", "--message") and i + 1 < len(pre):
            if not getattr(args, "message", None):
                args.message = pre[i + 1]
            i += 2
            continue
        if pre[i].startswith("--message="):
            if not getattr(args, "message", None):
                args.message = pre[i][len("--message=") :]
            i += 1
            continue
        if pre[i] == "--no-commit":
            args.no_commit = True
        i += 1
    repo_root = _resolve_repo_root(args)
    plan_path, err = _resolve_plan(repo_root, selector)
    if err:
        print(f"error: {err}")
        return 2
    if not paths:
        print(
            "error: aw commit requires paths after `--` (e.g. `aw commit <ipd> -- file.py`)"
        )
        return 2
    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read plan: {exc}")
        return 2
    scope_paths, is_grandfathered = _plan_scope_paths(text)
    try:
        plan_rel = str(plan_path.relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        plan_rel = plan_path.name

    # Compute the plan's allowed scope and refuse if ANY currently-staged path is out of scope.
    # (A grandfathered/absent Scope-Paths carries no allowlist, so scope enforcement is skipped with
    # a clear notice - the deterministic refusal only applies to a plan that DECLARED its territory.)
    if scope_paths and not is_grandfathered:
        staged = _staged_paths(repo_root)
        out_of_scope = [p for p in staged if not _in_scope(p, scope_paths, plan_rel)]
        # also refuse if a requested path is itself out of scope
        req_out = [
            p
            for p in paths
            if not _in_scope(str(Path(p)).replace("\\", "/"), scope_paths, plan_rel)
        ]
        if out_of_scope or req_out:
            print("aw commit: refusing - out-of-scope change(s) present:")
            for p in sorted(set(out_of_scope + req_out)):
                print(f"  {p}")
            print("  declared Scope-Paths: " + ", ".join(scope_paths))
            return 1
    elif not scope_paths:
        print(
            "aw commit: note - plan declares no Scope-Paths allowlist; committing the requested "
            "paths without scope enforcement"
        )

    # Run the phase-1 engine before mutating (validate-then-act). Blocking findings refuse the commit.
    findings = _validate_plan_via_engine(repo_root, plan_path)
    if findings:
        print(f"aw commit: refusing - {len(findings)} finding(s) on {plan_path.name}:")
        for d in findings:
            print(f"  {d.rule}: {d.detail}")
        return 1

    # Commit ONLY the declared in-scope paths by REUSING the shared path-scoped helper.
    message = getattr(args, "message", None) or f"work: {plan_rel}"
    outcome = _gch.offer_commit(
        repo_root,
        paths,
        message=message,
        assume_yes=bool(
            getattr(args, "commit", True)
        ),  # aw commit is an explicit commit intent
        no_commit=bool(getattr(args, "no_commit", False)),
        on_unrelated_staged="scope",
        trailers=_trailers_from_args(args),
    )
    if outcome.status == _gch.STATUS_COMMITTED:
        print(f"aw commit: committed {len(outcome.staged)} path(s): {outcome.commit}")
        return 0
    if outcome.status == _gch.STATUS_NOTHING_TO_COMMIT:
        print(f"aw commit: nothing to commit ({outcome.message})")
        return 1
    print(f"aw commit: {outcome.status}: {outcome.message}")
    return 1


# --------------------------------------------------------------------------------------
# aw finish
# --------------------------------------------------------------------------------------


def run_finish(args: argparse.Namespace) -> int:
    """`aw finish <ipd>`: require bound evidence, then perform ONLY a valid NON-AUTHORITATIVE status
    transition via the tooled `aw set` path. Never sets `executed`/`done`, never pushes, never tags."""
    repo_root = _resolve_repo_root(args)
    selector = getattr(args, "plan", None)
    plan_path, err = _resolve_plan(repo_root, selector)
    if err:
        print(f"error: {err}")
        return 2
    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read plan: {exc}")
        return 2
    plan_id = _plan_id6(text) or plan_path.stem
    target = getattr(args, "to", None)

    # Authority honesty (hard MUST): aw finish must NEVER perform the authoritative terminal
    # transition; that stays with `aw ipd finalize`.
    if target and target.strip().lower() in _AUTHORITATIVE_STATUSES:
        print(
            f"aw finish: refusing to set '{target}' - the authoritative terminal transition is "
            f"performed only by `aw ipd finalize`, never by `aw finish`."
        )
        return 2

    # Require the bound evidence from `aw test` (E-02), and that it is bound to the CURRENT tree.
    ev_path = _evidence_path(repo_root, plan_id)
    if not ev_path.is_file():
        print(
            f"aw finish: refusing - no test evidence bound for {plan_id}. Run "
            f"`aw test {plan_id} -- <command>` first."
        )
        return 1
    try:
        evidence = json.loads(ev_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"aw finish: refusing - cannot read evidence record: {exc}")
        return 1
    _rc, tree_out, _e = _git(repo_root, ["rev-parse", "HEAD^{tree}"])
    cur_tree = tree_out.strip() or None
    if evidence.get("git_tree") and cur_tree and evidence["git_tree"] != cur_tree:
        print(
            "aw finish: refusing - the recorded test evidence is bound to a STALE tree "
            f"({str(evidence['git_tree'])[:12]}), not the current tree ({cur_tree[:12]}). "
            f"Re-run `aw test {plan_id} -- <command>` on the current tree."
        )
        return 1
    if evidence.get("exit_code") not in (0, None):
        print(
            f"aw finish: refusing - the bound test evidence records a FAILING run "
            f"(exit {evidence.get('exit_code')}). Fix and re-run `aw test`."
        )
        return 1

    if not target:
        print(
            f"aw finish: evidence for {plan_id} is present and bound to the current tree. "
            f"Specify the next non-authoritative status with `--to <status>` "
            f"(e.g. reviewed/approved); `aw finish` never sets executed (use `aw ipd finalize`)."
        )
        return 0

    # Delegate the transition to the TOOLED `aw set` path so it writes an attributed history line
    # (never a hand-edit). This reuses status_set; it does not push or tag.
    from agent_workflows import status_set as _status_set
    from agent_workflows.term import Term

    ns = argparse.Namespace(
        dir=str(repo_root), message="aw finish: evidence-bound transition"
    )
    rc = _status_set.run_set_command(
        [target, plan_id],
        scoped_type="plans",
        repo_root=repo_root,
        args=ns,
        term=Term(),
    )
    if rc == 0:
        print(
            f"aw finish: transitioned {plan_id} -> {target} (evidence-bound, non-authoritative)"
        )
    return rc

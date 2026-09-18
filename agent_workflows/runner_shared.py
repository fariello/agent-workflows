"""The ONE shared library for the two host runners (rununify Order 02, `818uru`).

`oc_runipd` (the OpenCode driver) and `agy_runipd` (the Antigravity driver) are near-duplicate
programs. Measured at HEAD `1ecc5891`: 86 top-level symbols are defined in BOTH, and only 33 of them
are AST-identical while 50 have DRIFTED. This module is the home for the identical ones, so each has
exactly one definition and a fix to it reaches both drivers.

WHY THE IDENTICAL SET IS THE DANGEROUS SET, since "identical" sounds like "harmless". Two identical
copies have no behavioral disagreement TODAY, which is exactly why nothing signals when one is edited
and the other is not; that is how the 50 currently-diverged symbols got that way. The cost is
already visible in this package's history: `DriverError` was defined TWICE as two DISTINCT classes,
so `agy_runipd` needed a hand-written wrapper to translate one into the other before its `main` could
catch a preflight refusal raised from the OpenCode code path.

# ---- THE ADMISSION RULE -------------------------------------------------------------------------

A symbol belongs here only if BOTH runners' definitions were PROVEN identical by AST comparison
(`ast.dump(ast.parse(ast.unparse(node)), include_attributes=False)`), never merely judged similar by
reading. `tests/test_runner_shared.py` holds the pre-move fingerprint of every symbol below and
FAILS if a body drifted from what was moved.

State the rule precisely, because the obvious wording is FALSE one screen further down: it is
"identical bodies MODULO AN EXPLICITLY INJECTED DEPENDENCY", not "identical bodies verbatim". Some
symbols here call a symbol that STAYS in the runners, either because it is host-specific or because
it is DIVERGED and deciding which side wins belongs to a later plan. Those take the dependency as an
explicit PARAMETER, and each runner keeps a one-line wrapper at the original name and signature that
binds its own. The complete list is enumerated below; an unenumerated injection is a defect rather
than a judgment call, and `tests/test_runner_shared.py` pins the list so it cannot grow silently.

WHAT MAY NEVER HAPPEN HERE, and why each prohibition exists rather than just that it does:

  * This module MUST NOT import either runner, at module level or lazily inside a function. The
    import cycle is the lesser reason. The real one is that importing a DIVERGED symbol from one
    runner into shared code would silently give BOTH drivers that runner's behavior, which is a
    behavior change wearing a de-duplication's clothes. `tests/test_runner_shared.py` asserts the
    absence by AST, so the rule is enforced and not merely documented.
  * NO module-level mutable state. A registration seam ("each runner registers its own
    `write_report` at import time") was considered for the injected dependencies and DECLINED by the
    maintainer: process-global state makes behavior depend on import ORDER and leaks between tests.
    A parameter is passed at the call, so there is nothing to register and nothing to leak.
  * A symbol whose bodies DIFFER belongs to a later child of the `rununify` Set, not here. Moving a
    diverged symbol requires first deciding which side is authoritative, with evidence, and that
    decision is the intellectual work this module is deliberately NOT doing.

Per the orchestrator's OQ-02, this is the shared runner library and `plan_readiness.py` is a
DESIGNATED peer it may import, NOT something it absorbs: `status_set.py` and `ipd_schema.py` import
`plan_readiness` too, and they are not runners.

# ---- INJECTED DEPENDENCIES (the complete list) --------------------------------------------------

TEN symbols call something they cannot reach from here. Each takes it as a keyword-only parameter;
each runner wraps it at the original name and signature, so NO call site in either runner was
rewritten. The parenthetical says why the dependency could not simply move too:

  * `run_checked(..., env_builder=)`         <- `pinned_child_env`   (opencode-only, host-specific)
  * `save_state(..., write_report=)`         <- `write_report`       (DIVERGED)
  * `discover_plans(..., parse_plan_file=)`  <- `parse_plan_file`    (SUPERSEDED, and the parameter is
                                                 now VESTIGIAL: rununify 06 (`sy7uwh`) unified BOTH
                                                 the record type and this parser into this module, so
                                                 each runner's wrapper injects the SHARED
                                                 `parse_plan_file` and the two hosts get the same
                                                 `PlanRecord`. The parameter is retained ON PURPOSE:
                                                 it is fingerprint-pinned in
                                                 `runner_shared_premove_fingerprints.json` and
                                                 removing it would rewrite call sites the maintainer's
                                                 wrapper ruling exists to leave alone. Collapsing it
                                                 belongs to a later plan; the ORIGINAL reason it
                                                 existed - "the two runners' `PlanRecord` are
                                                 different NamedTuples, oc's carrying a `kind` field
                                                 agy's lacks" - is GONE, and that sentence is
                                                 preserved here only so a reader is not misled by the
                                                 surviving mechanism)
  * `validate_manifest(..., parse_dependency_token=)`               (opencode-only)
  * `print_status(..., driver_label=)`       <- the host's own name  (the sole host-naming-only symbol
                                                 of the 34: the two bodies differed ONLY by the
                                                 literal 'opencode' vs 'antigravity')
  * `git_head(..., run_checked=)`            <- `run_checked`        (see below)
  * `git_status(..., run_checked=)`          <- `run_checked`        (see below)
  * `git_common_dir(..., run_checked=)`      <- `run_checked`        (see below)
  * `build_lane_outcome(..., run_checked=)`  <- `run_checked`        (integpath-02 `6sb3yu`; the SAME
                                                 intra-seam dependency as the three above, see below)
  * `integrate_lane_branch(..., run_checked=, host_label=)`          (integpath-02 `6sb3yu`;
                                                 `run_checked` is threaded through to
                                                 `build_lane_outcome`'s one call. `host_label` is a
                                                 SECOND parameter and is NOT an injected dependency -
                                                 it is the one value the two runners' bodies actually
                                                 differed by, the merge subject's `aw oc run` /
                                                 `aw agy run` label - so this symbol is the only one
                                                 here carrying both kinds of parameter. Its runner
                                                 wrapper binds both.)

THE LAST THREE ARE AN INTRA-SEAM DEPENDENCY the authoring analysis did not predict, and they are
worth explaining because the obvious "fix" is a trap. Those three helpers' bodies CALL `run_checked`,
which is itself moved here and which gained the `env_builder` parameter, so a naive lift raises
`TypeError: run_checked() missing 1 required keyword-only argument`. The tempting repair is to
rewrite them to use the shared `_run_git` sitting right above them - and that would be a BEHAVIOR
CHANGE, not a cleanup: `git_head` would stop raising `DriverError` on failure and start returning an
empty string, and `git_status` would stop passing `--short`. Both results flow straight into every
run's outcome record (`starting_head`/`starting_status`/`ending_head`/`ending_status`), and no suite
would have caught it. So the seam's OWN mechanism is applied uniformly instead: the dependency is
injected, and each runner binds its own `run_checked` wrapper.

TWO SYMBOLS THAT COULD NOT MOVE AT ALL, recorded here because a reader comparing this module against
the plan's 34-symbol manifest will otherwise think they were forgotten:

  * `disable_lane_prompt` MUTATES a module-level `_LANE_PROMPT_DISABLED` flag through `global`. A
    shared `global` would write THIS module's flag while each runner's `_lane_reclaim_prompt`
    (DIVERGED, so it stays behind) kept reading its OWN, and prompt suppression on a repeated
    interrupt would silently stop working - a regression whose only symptom is an unattended run
    stopping to ask a question nobody is there to answer. It stays defined in both runners, and
    `tests/test_runner_shared.py::UnmovableSymbolTests` pins that reason so it is not "finished"
    later by someone who reads the count and not the constraint.
  * `_read_set`/`_read_order`/`describe_unresolved_plan_selector`/`validate_manifest` close over the
    module constants `_SET_RE`, `_ORDER_RE`, `ID6_RE` and `SCHEMA_VERSION`. Those four constants are
    themselves byte-identical in both runners, so they MOVE here rather than being injected, and each
    runner re-exports them so its other call sites are untouched.

Conventions follow `host_runner.py`: a docstring stating what the module owns and its design posture,
banner comments per section, and no import of a caller.

# ---- SPEC 2.1's RUN FLAG SURFACE (runflags-01, `uyeko5`) ----------------------------------------

A SECOND thing now lives here, and it is not one of the 34 moved symbols: the spec `25kzda` 2.1 POLICY
FLAG SURFACE (`RUN_POLICY_FLAGS` and the `register_*`/`freeze_*`/`resolve_*` helpers below). It
belongs in this module and not in either runner for exactly the reason the module exists: registering
eight flags twice is how two parsers diverge, and the shipped `--full-auto` had ALREADY diverged
(default `False` on opencode, `True` on antigravity) before anything shared existed to stop it.

It is admitted under a DIFFERENT rule from the 34, stated so the admission rule above is not read as
having been bent: the 34 are PROVEN-IDENTICAL EXISTING bodies moved without edit, fingerprint-pinned
by `tests/test_runner_shared.py`. This block is NEW code that never existed in either runner, so it
has no pre-move fingerprint to match and is deliberately absent from that fixture. What replaces the
fingerprint as its guard is `tests/test_run_flag_surface.py`, which drives every assertion from
`RUN_POLICY_FLAGS` as DATA and therefore fails when the spec grows a flag the code lacks.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import functools
import hashlib
import json
import os
import re
import secrets
import shlex
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Container, Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import (
    Any,
    Callable,
    NamedTuple,
    Optional,
    TextIO,
)

from agent_workflows import runner_profiles
from agent_workflows.render_stream import (
    Palette,
    StreamTracker,
    _STATUS_COLOR,
    execution_index,
    record_integration_refusal as render_record_integration_refusal,
    render_run_summary_table,
)

# ---- module constants the moved bodies close over ------------------------------------------------
# Byte-identical in both runners (verified by comparing the assignment VALUES at the AST level), so
# they move rather than being injected. Both runners re-export them, leaving their other call sites
# unchanged.

SCHEMA_VERSION = 1

ID6_RE = re.compile(r"^[a-z0-9]{6}$")

_SET_RE = re.compile(r"(?m)^-\s*Set:\s*(.+?)\s*$")
_ORDER_RE = re.compile(r"(?m)^-\s*Order:\s*(\d+)\s*$")

# rununify 06 (`sy7uwh`) E-03: the two constants `parse_plan_file` closes over, moved here with it.
#
# `_KIND_RE` came from `oc_runipd` (agy had none and imported the READER instead), and
# `_PLAN_FILENAME_RE` was BYTE-IDENTICAL in both runners, so both move rather than being injected -
# the same rule `_SET_RE`/`_ORDER_RE` above already follow. Leaving a duplicate constant behind
# reproduces the defect one layer down: a fix to the pattern would still not reach the runner
# carrying its own copy. Both runners re-export them, so their other call sites are unchanged.
#
# NOTE (lanetruth-03 / 8guhs0 E-01) there is deliberately NO dependency regex here, and the note is
# carried from `oc_runipd` because that is where the trap lives: the deleted `_DEPS_RE` matched a
# LEGACY `Dependencies:`/`Depends-on:` field no plan uses, so the canonical `- Item-Dependencies:`
# statement was invisible and every queue item froze with `dependencies: []`. The field NAME comes
# from `ipd_schema.META_ITEM_DEPENDENCIES` and its GRAMMAR from `ipd_schema.parse_item_dependencies`
# (see `_read_item_dependencies`). Re-adding a dependency regex here is a regression guarded by
# `tests/test_runner_item_dependencies.py`.
_KIND_RE = re.compile(r"(?m)^-\s*Kind:\s*(\S+)\s*$")

_PLAN_FILENAME_RE = re.compile(
    r"^\d{8}-([a-z0-9_-]+)-(\d{1,3})-([a-z0-9]{6})-(.+)\.(ipd|draft|plan)\.md$"
)


# ---- errors --------------------------------------------------------------------------------------
# ONE `DriverError` for the package. It was previously defined in BOTH runners as two DISTINCT
# classes, which is why `agy_runipd` carried a wrapper whose only job was to catch oc's class and
# re-raise its own as a translation. Its two SUBCLASSES now live here too (rununify 03, `i3d6ml`);
# the sentence that used to say they "stay put" is superseded below, at the classes themselves.


class DriverError(RuntimeError):
    pass


# THE TWO SUBCLASSES, moved here by rununify 03 (`i3d6ml`) E-02, and the reason the earlier note above
# said they would NOT move is recorded rather than deleted, because the note was RIGHT about the risk
# and only wrong about the conclusion. It read: "their docstrings differ, so those classes are DIVERGED
# and stay put". Docstring divergence is not behavioral divergence: `_normalize_dump` strips docstrings
# before comparing, and with them stripped both classes' bodies are `pass` in both runners. So what the
# note actually recorded was that nobody had yet checked whether the CATCH still works.
#
# IT DOES, AND THAT IS THE LOAD-BEARING FACT. Each runner's `main` catches its OWN name today, and
# `tests/test_runner_shared.py`'s `SharedErrorTests` asserts each is a `DriverError` subclass in BOTH
# runners. Before the move, a `StallTimeout` raised through oc's code path was a DIFFERENT class from
# the one agy's `except StallTimeout` names, so a cross-host raise was caught only by the broader
# `except DriverError` - exactly the translation problem `DriverError` itself was moved to end. After
# the move there is ONE class, so `except StallTimeout` in either runner catches a raise originating in
# either, and every `except DriverError` still catches both because the parent is unchanged. V-02 proves
# this by raising each through one runner's name and catching it through the other's.


class StallTimeout(DriverError):
    """Raised when the child agent produces no JSONL events for stall_timeout seconds."""


class EmptyStatusSelection(DriverError):
    """A STATUS selector (`reviews`/`review`/`to-review`) matched nothing, which is a SUCCESS.

    revsweep 76gsmv E-04, implementing spec `25kzda` 2.4a property 3: "an empty `reviews` result
    is a success, not an error ... it reports that plainly and exits 0 ... the one deliberate
    exception to the Section 2.3 rule that zero matches exit 2. A misspelled id6 still exits 2;
    only the status selectors are exempt."

    WHY A SUBCLASS RATHER THAN A RETURN VALUE. `expand_selectors` is called from deep inside
    `initialize_run`, BEFORE the run directory is created. Returning an empty list would let
    `initialize_run` proceed to mkdir a run directory and freeze an empty queue, so the "start no
    run" half of the requirement would be lost. Raising through the existing `DriverError` channel
    reaches `main` with nothing created, and subclassing keeps every OTHER `except DriverError` in
    the package catching it exactly as before; only `main`'s own handler, which is ordered ahead of
    the generic one, treats it as exit 0.

    SHARED SINCE rununify 03 (`i3d6ml`). Both runners' definitions carried the docstring above in
    different words and an identical (empty) body, so this is one class now and each `main` catches
    the same object. The ORDERING requirement inside each `main` is unchanged and is what makes the
    exit-0 treatment work: the handler for this class must precede the generic `except DriverError`,
    or the generic one absorbs it and the run exits 2.
    """


# ---- run / misc ----------------------------------------------------------------------------------


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def should_color(stream: TextIO | None = None) -> bool:
    """Decide whether to emit ANSI color for ``stream`` (default stdout)."""
    target: TextIO = stream if stream is not None else sys.stdout
    if os.environ.get("FORCE_COLOR"):
        return True
    if os.environ.get("NO_COLOR"):
        return False
    try:
        return bool(target.isatty())
    except (AttributeError, ValueError):
        return False


def new_run_id() -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run-{stamp}-{os.getpid()}"


def state_root(repo: Path | str | None = None) -> Path:
    """Resolve the canonical runs root through the project-context authority.

    Pure, side-effect-free runs-root resolver. Derived from the resolved records root,
    so records_backend settings (repository, companion, home) each yield the correct
    location, while repository-backed projects continue to resolve to <repo>/.aw/records/runs.
    """
    from agent_workflows.project_context import resolve_project_context

    target = (
        Path(repo).expanduser().resolve() if repo is not None else Path.cwd().resolve()
    )
    ctx = resolve_project_context(target_repo=str(target))
    records_dir = Path(ctx.logical_roots["records"]).resolve()
    if not records_dir.exists() and (target / ".aw" / "records").is_dir():
        records_dir = (target / ".aw" / "records").resolve()
    return records_dir / "runs"


# ---- analytics namespace reservation -------------------------------------------------------------

ANALYTICS_DIRNAME: str = "analytics"
ANALYTICS_CACHE_SUBDIR: str = "cache"
ANALYTICS_SNAPSHOTS_SUBDIR: str = "snapshots"
ANALYTICS_EXPORTS_SUBDIR: str = "exports"


def analytics_root(repo: Path | str | None = None) -> Path:
    """The reserved analytics directory under the resolved runs root."""
    return state_root(repo) / ANALYTICS_DIRNAME


def analytics_cache_dir(repo: Path | str | None = None) -> Path:
    """The disposable analytics cache directory."""
    return analytics_root(repo) / ANALYTICS_CACHE_SUBDIR


def analytics_snapshots_dir(repo: Path | str | None = None) -> Path:
    """The disposable analytics snapshots directory."""
    return analytics_root(repo) / ANALYTICS_SNAPSHOTS_SUBDIR


def analytics_exports_dir(repo: Path | str | None = None) -> Path:
    """The disposable analytics exports directory."""
    return analytics_root(repo) / ANALYTICS_EXPORTS_SUBDIR


def path_is_within_analytics(path: str | Path, repo: Path | str | None = None) -> bool:
    """Pure containment predicate: True if `path` resolves inside a reserved analytics tree.

    Resolves symlinks and relative segments (e.g. `..`).
    Checks canonical resolved runs root as well as legacy roots (.aw/runs, .agents/runs).
    Returns False for sibling paths whose names merely start with 'analytics' (e.g. 'analytics_backup').
    Pure and side-effect free: does NOT create any files or directories.
    """
    if not path:
        return False

    target_p = Path(path).expanduser().resolve()

    repo_candidates: list[Path] = []
    if repo is not None:
        repo_candidates.append(Path(repo).expanduser().resolve())
    else:
        try:
            from agent_workflows.project_context import find_project_root

            discovered = find_project_root(target_p)
            if discovered:
                repo_candidates.append(discovered.resolve())
        except Exception:
            pass
        cwd = Path.cwd().resolve()
        if cwd not in repo_candidates:
            repo_candidates.append(cwd)

    analytics_roots: list[Path] = []
    for r in repo_candidates:
        try:
            analytics_roots.append(analytics_root(r).resolve())
        except Exception:
            pass
        analytics_roots.append((r / ".aw" / "runs" / ANALYTICS_DIRNAME).resolve())
        analytics_roots.append((r / ".agents" / "runs" / ANALYTICS_DIRNAME).resolve())

    for a_root in analytics_roots:
        try:
            target_p.relative_to(a_root)
            return True
        except ValueError:
            continue

    # Also structurally check if target_p has an 'analytics' directory whose parent is named 'runs'
    for parent in [target_p, *target_p.parents]:
        if parent.name == ANALYTICS_DIRNAME:
            if parent.parent.name == "runs":
                return True

    return False


def resolve_run_dir(repo_arg: str, run_id: str) -> Path:
    looks_like_path = (
        os.sep in run_id
        or (os.altsep and os.altsep in run_id)
        or run_id.startswith("~")
    )
    if looks_like_path:
        candidate = Path(run_id).expanduser()
        for run_dir in (candidate, Path.cwd() / candidate):
            if run_dir.is_dir() and (run_dir / "state.json").is_file():
                return run_dir.resolve()
        raise DriverError(f"Run not found: {run_id}")
    repo = Path(repo_arg).expanduser().resolve()
    run_dir = state_root(repo) / run_id
    if run_dir.is_dir():
        return run_dir
    raise DriverError(f"Run not found: {run_id}")


# ---- git -----------------------------------------------------------------------------------------
# NOTE a NAME COLLISION that is NOT a re-fork: `layout_inventory.py` and `layout_migration.py` also
# define `_run_git`, but with different bodies AND a different return type (they return a
# `CompletedProcess` and invoke `git -C <repo>`; this one returns a `(rc, out, err)` tuple and runs
# with `cwd=repo`). Three genuinely different functions sharing a name. Do NOT "unify" them.


def _run_git(
    repo: Path, args: list[str], *, timeout: float | None = None
) -> tuple[int, str, str]:
    """Run a git command in ``repo``; return (returncode, stdout, stderr).

    ``timeout`` DEFAULTS TO None, which is exactly today's behavior (wait indefinitely), so every
    existing caller is unaffected. It exists for an INTERACTIVE read-only caller that must not hang
    forever on a wedged git: `artifact_audit.build_finalize_evidence_index` passes one and treats a
    `subprocess.TimeoutExpired` as an unprovable `unknown` rather than a pass. Raising is deliberate:
    swallowing a timeout here would make a hang indistinguishable from an empty history.
    """
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


def declared_spec_paths(text: str) -> list[str]:
    """The SPEC files a plan's `- Scope-Paths:` says it will change, in declared order.

    A spec is identified by the `.spec.md` type facet of the uniform artifact-naming grammar, not by
    directory, so a spec is still recognized if the records tree is relocated. `grandfathered` and an
    empty value yield `[]`.
    """
    m = re.search(r"^- Scope-Paths:[ \t]*(.+)$", text, re.M)
    if not m:
        return []
    raw = m.group(1).strip()
    if not raw or raw.lower() in ("grandfathered", "none"):
        return []
    out: list[str] = []
    for part in raw.split(","):
        p = part.strip()
        if p.endswith(".spec.md"):
            out.append(p)
    return out


def spec_impacts_for_queue(
    repo: Path, queue: "Sequence[Mapping[str, Any]]"
) -> list[dict]:
    """Per queued item, the spec files it DECLARES it will change (for the pre-run announcement).

    Reads each item's plan file from disk rather than trusting anything cached in run state, so the
    announcement reflects the plan as it stands at dispatch. An unreadable plan is skipped rather than
    failing the run: this is an advisory surface, and refusing to start a run because an announcement
    could not be built would be a worse failure than a missing line of output.
    """
    impacts: list[dict] = []
    for item in queue:
        raw = item.get("path") or item.get("plan_path") or ""
        if not raw:
            continue
        p = Path(raw)
        if not p.is_absolute():
            p = repo / p
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        specs = declared_spec_paths(text)
        if specs:
            impacts.append(
                {
                    "id6": item.get("id6"),
                    "setid": item.get("setid"),
                    "specs": specs,
                }
            )
    return impacts


def conflicted_paths(repo: Path) -> list[str]:
    """The paths git left in the UNMERGED (``U``) state by a failed merge, sorted.

    Read via `git diff --name-only --diff-filter=U`, which reports exactly the conflicted entries and
    nothing else. MUST be called BEFORE `git merge --abort`, because the abort clears the index state
    this reads. Returns `[]` when git reports nothing (a merge that failed for a reason OTHER than a
    content conflict, e.g. a refusal to start), so a caller can distinguish "conflicted in these files"
    from "did not conflict".
    """
    _rc, out, _err = _run_git(repo, ["diff", "--name-only", "--diff-filter=U"])
    return sorted(p.strip() for p in out.splitlines() if p.strip())


def merge_in_progress(repo: Path) -> bool:
    """Did the last `git merge` ACTUALLY START, i.e. does `MERGE_HEAD` exist?

    dirtygates-02 (`metc8b`) E-02: this is the STRUCTURAL DISCRIMINATOR between the two ways a
    `git merge` can fail, and it deliberately does NOT look at git's message text.

    MEASURED (git 2.43.0, four scratch repositories):

    * a CONTENT CONFLICT starts the merge, so `MERGE_HEAD` EXISTS, `git diff --diff-filter=U` names
      the conflicted paths, and `git merge --abort` succeeds (rc=0) leaving a clean tree; while
    * a LOCAL-CHANGES REFUSAL ("error: Your local changes to the following files would be overwritten
      by merge") never starts the merge at all, so `MERGE_HEAD` is ABSENT, `--diff-filter=U` is EMPTY,
      the working-tree content survives untouched, HEAD is unmoved, and `git merge --abort` FAILS
      rc=128 with "fatal: There is no merge to abort (MERGE_HEAD missing)".

    WHY NOT MATCH THE MESSAGE. Git's English is localizable (`LANG`/`LC_ALL` change it) and its
    wording moves between versions, so a text test passes in the author's locale and MISCLASSIFIES
    silently everywhere else. Misclassification is expensive here, not cosmetic: `merge-conflict` is
    terminal on its first attempt by `classify_integration_refusal`, so a text test that fails in a
    different locale converts a self-clearing condition into permanent in-run loss. The `MERGE_HEAD`
    file is git's own plumbing state and carries no language.

    Read via `git rev-parse --verify --quiet MERGE_HEAD` rather than probing `.git/MERGE_HEAD` on the
    filesystem, because in a LINKED WORKTREE `.git` is a FILE pointing at
    `<common>/worktrees/<name>/`, so a path probe would look in the wrong directory and always report
    False. Every integration in this module runs in main, but the helper is shared and must not be a
    trap for a worktree caller.
    """
    rc, _out, _err = _run_git(repo, ["rev-parse", "--verify", "--quiet", "MERGE_HEAD"])
    return rc == 0


def format_local_changes_refusal_reason(*, merge_stdout: str, merge_stderr: str) -> str:
    """The operator-facing reason for a merge git REFUSED TO START because main holds local changes.

    dirtygates-02 (`metc8b`) E-02. DELIBERATELY NOT :func:`format_merge_conflict_reason`, which is a
    separate function for a reason that is easy to undo by "simplifying" the two together:

    * that helper HARD-CODES the words "merge-back conflict" into every string it builds, and this
      condition is NOT a conflict. Reusing it reproduced exactly the misleading
      "merge-back conflict; error: Your local changes ..." text that the two stranded lanes of
      2026-09-13 recorded (`bzz5e6`, `f6idxs`), which is the defect E-02 exists to fix; and
    * its whole contract is CONFLICTED PATHS read from the index, and a refusal to start leaves NONE
      (`conflicted_paths` returns `[]` here, as its own docstring notes).

    Git's own text already NAMES the offending files, so it is carried VERBATIM rather than
    re-worded: a summary would be a second place that can drift from what git actually said.

    STDERR FIRST here, which is the OPPOSITE of the conflict helper's stdout-first order, and both are
    correct because git writes the two classes to different streams (measured): a content conflict
    goes to STDOUT ("CONFLICT (content): ...", empty stderr), while this refusal goes to STDERR
    ("error: Your local changes ...", empty stdout). Each helper reads the stream its own class
    actually uses, and falls back to the other so an unexpected routing still reports something.
    """
    detail = (merge_stderr or "").strip() or (merge_stdout or "").strip()
    head = (
        "integration refused by git: main has uncommitted local changes to file(s) this merge "
        "would overwrite, so the merge never started (no conflict, nothing to resolve); it is "
        "re-attempted once the base is clean"
    )
    return f"{head}; {detail}" if detail else head


def generated_manifest_paths(paths: Sequence[str]) -> list[str]:
    """The subset of ``paths`` that are GENERATED index manifests (`INDEX.json` / `INDEX.md`).

    These are byte-deterministically regenerated from the artifact files, so a conflict in one is not
    a substantive disagreement and is NOT resolved by editing it: the fix is to regenerate. Kept as a
    name test rather than a hardcoded path list so it holds for any record tree.
    """
    out: list[str] = []
    for p in paths:
        name = p.rsplit("/", 1)[-1]
        if name in ("INDEX.json", "INDEX.md"):
            out.append(p)
    return out


def format_merge_conflict_reason(
    repo: Path,
    *,
    merge_stdout: str,
    merge_stderr: str,
    paths: Sequence[str] | None = None,
) -> str:
    """Build the operator-facing reason for a lane merge-back that failed on a real git conflict.

    WHY THIS EXISTS (mergemsg; measured 2026-09-06 in run `run-20260906T162533Z-1552446`). Both hosts
    used to report `f"merge-back conflict: {(err2 or err).strip()}"`, keeping only STDERR from each of
    the two merge attempts. But GIT WRITES MERGE CONFLICTS TO STDOUT: a conflicting
    `git merge --no-ff` exits 1 with `CONFLICT (content): Merge conflict in <path>` on **stdout** and
    an **empty stderr**, while the preceding EXPECTED `--ff-only` failure writes
    `fatal: Not possible to fast-forward` plus the diverging-branches advice to **stderr**. So
    `(err2 or err)` fell through to the ff-only text on EVERY genuine conflict, and the report always
    described a merge whose failure was not an error, never the conflict itself. The conflicted paths,
    the one thing the operator needs, sat in the discarded stdout.

    So: name the PATHS (authoritative, read from the index), and use the conflicting merge's STDOUT.
    NEVER fall back to the `--ff-only` output, which describes an expected non-erroneous outcome.

    ``paths`` should be the result of :func:`conflicted_paths` captured BEFORE `git merge --abort`; when
    omitted it is read now (only correct if the merge state still stands).
    """
    resolved = list(paths) if paths is not None else conflicted_paths(repo)
    detail = (merge_stdout or "").strip() or (merge_stderr or "").strip()

    parts: list[str] = []
    if resolved:
        parts.append(
            f"merge-back conflict in {len(resolved)} file(s): {', '.join(resolved)}"
        )
        generated = generated_manifest_paths(resolved)
        if generated and len(generated) == len(resolved):
            # The whole conflict is regenerable, so the fix is NOT a manual merge. Say so, because a
            # human reading "conflict" reasonably reaches for a merge tool.
            parts.append(
                "every conflicted path is a GENERATED index manifest, so no substantive change "
                "disagrees: re-run the owning `aw index <type>` to regenerate rather than merging "
                "by hand"
            )
        elif generated:
            parts.append(
                "generated index manifest(s) among them (regenerate with `aw index <type>`, do not "
                f"hand-merge): {', '.join(generated)}"
            )
    else:
        parts.append("merge-back conflict")
    if detail:
        parts.append(detail)
    return "; ".join(parts)


def git_head(repo: Path, *, run_checked: Callable[..., str]) -> str:
    return run_checked(["git", "rev-parse", "HEAD"], cwd=repo)


def git_branch(repo: Path) -> str:
    result = subprocess.run(
        ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return result.stdout.strip() if result.returncode == 0 else "(detached)"


def git_status(repo: Path, *, run_checked: Callable[..., str]) -> str:
    return run_checked(["git", "status", "--short"], cwd=repo)


def git_common_dir(repo: Path, *, run_checked: Callable[..., str]) -> Path:
    raw = run_checked(["git", "rev-parse", "--git-common-dir"], cwd=repo)
    path = Path(raw)
    return path if path.is_absolute() else (repo / path).resolve()


def run_checked(
    argv: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    *,
    env_builder: Callable[[dict[str, str] | None], dict[str, str]],
) -> str:
    # lanetruth Order 01 (af7i6p) E-05: this function USED to build the PYTHONPATH prepend
    # itself. That read as a pin but was MEASURABLY INERT, because the cwd entry precedes
    # PYTHONPATH in sys.path, so a child launched from a lane still imported the lane's copy.
    # It now delegates to the single shared definition (`pinned_child_env`), and callers pass
    # module argv built by `pinned_module_argv`, which supplies the SUPPRESSING half that makes
    # the selecting half actually bite. One definition of the pin, not two.
    merged_env = env_builder(env)
    result = subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        env=merged_env,
        text=True,
        # ttywedge Order 01 (g40w37): deny an inherited terminal (see driver_finalize).
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        details = (result.stderr.strip() + "\n" + result.stdout.strip()).strip()
        raise DriverError(
            f"Command failed ({result.returncode}): {shlex.join(argv)}\n{details}"
        )
    return result.stdout.strip()


# ---- json / state --------------------------------------------------------------------------------


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DriverError(f"Required file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DriverError(f"Invalid JSON in {path}: {exc}") from exc


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        if hasattr(os, "O_DIRECTORY"):
            with contextlib.suppress(OSError):
                dir_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp_name)


def append_jsonl(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_state(run_dir: Path) -> dict[str, Any]:
    return load_json(run_dir / "state.json")


def save_state(
    run_dir: Path,
    state: dict[str, Any],
    *,
    write_report: Callable[[Path, dict[str, Any]], None],
) -> None:
    state["updated_at"] = utc_now()
    atomic_write_json(run_dir / "state.json", state)
    write_report(run_dir, state)


def print_status(run_dir: Path, *, driver_label: str) -> None:
    state = load_state(run_dir)
    pal = Palette(should_color(sys.stdout))
    print(render_run_summary_table(state, run_dir, pal=pal, driver_label=driver_label))


# ---- lanes ---------------------------------------------------------------------------------------
# `disable_lane_prompt` is deliberately ABSENT and stays in both runners: it mutates a module-level
# `_LANE_PROMPT_DISABLED` via `global`, and a shared `global` would write THIS module's flag while
# each runner's DIVERGED `_lane_reclaim_prompt` kept reading its own. See the module docstring.


def _lane_records_from_state(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Every lane THIS run allocated, read back from durable per-item state (E-04).

    Reuses the existing `worktree`/`worktree_branch` (and `preserved_*`) fields rather than adding a
    second store. Note `preserved_worktree`/`preserved_branch` were previously WRITTEN and never READ
    anywhere in the package; this is the consumer that makes them meaningful."""
    lanes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in state.get("queue", []):
        candidates: list[dict[str, Any]] = []
        for attempt in item.get("attempts", []) or []:
            if attempt.get("worktree"):
                candidates.append(
                    {
                        "worktree": attempt.get("worktree"),
                        "branch": attempt.get("worktree_branch"),
                        "lane_id": attempt.get("worktree_lane_id") or item.get("id6"),
                        "base_commit": attempt.get("worktree_base"),
                        "disposition": attempt.get("worktree_disposition"),
                    }
                )
        if item.get("preserved_worktree"):
            candidates.append(
                {
                    "worktree": item.get("preserved_worktree"),
                    "branch": item.get("preserved_branch"),
                    "lane_id": item.get("preserved_lane_id") or item.get("id6"),
                    "base_commit": item.get("preserved_base"),
                    "disposition": item.get("preserved_disposition"),
                }
            )
        for rec in candidates:
            key = "{0}|{1}".format(rec.get("branch"), rec.get("worktree"))
            if key in seen:
                continue
            seen.add(key)
            rec["id6"] = item.get("id6")
            rec["status"] = item.get("status")
            lanes.append(rec)
    return lanes


def describe_lane(repo: Path, lane: dict[str, Any]) -> dict[str, Any]:
    """The E-01 classifier's reading of one recorded lane, shaped for reporting (E-06).

    The classifier is the SINGLE source of the reported facts; this adds no second git probe and no
    new CLI verb (`aw doctor --lanes` and `aw recover` are owned by plan `2c122z`)."""
    from agent_workflows import worktree_lease

    lane_id = lane.get("lane_id") or lane.get("id6") or ""
    base = lane.get("base_commit") or "HEAD"
    st = worktree_lease.inspect_lane(repo, lane_id, base_commit=base)
    return {
        "id6": lane.get("id6"),
        "lane_id": lane_id,
        "branch": st.branch,
        "worktree": str(st.worktree_path) if st.worktree_path else lane.get("worktree"),
        "state": st.state,
        "commits_ahead": st.commits_ahead,
        "dirty": st.dirty,
        "head": st.head,
        "base_sha": st.base_sha,
        "reclaimable": st.reclaimable,
        "holds_work": st.holds_work,
        "owner_live": st.owner_live,
        # Whether ANOTHER live process owns it, which is the question reclamation must ask (a driver
        # reclaiming its own lanes is itself the live owner of every one of them).
        "owned_by_other_live_process": worktree_lease.lane_owned_by_other_live_process(
            repo, lane_id
        ),
    }


def format_lane_report(lanes: list[dict[str, Any]]) -> str:
    """One actionable line per lane, so an operator can tell at a glance which lane matters (E-06).

    The lane that holds work is the one to look at; an empty lane is noise. Reporting both without
    distinguishing them is what forced a hand inspection of five lanes to find the one holding work."""
    from agent_workflows import worktree_lease

    if not lanes:
        return "No lanes were allocated by this run."
    lines: list[str] = []
    for lane in lanes:
        if lane["holds_work"]:
            detail_bits = []
            if lane["commits_ahead"]:
                detail_bits.append(
                    "{0} commit(s) beyond base".format(lane["commits_ahead"])
                )
            if lane["dirty"]:
                detail_bits.append("uncommitted changes")
            what = "HOLDS WORK ({0})".format(
                ", ".join(detail_bits) if detail_bits else "work present"
            )
        elif lane["state"] == worktree_lease.LANE_ABSENT:
            what = "already gone"
        else:
            what = "empty ({0}, nothing to recover)".format(lane["state"].lower())
        lines.append(
            "  {0} {1}: {2}\n      branch {3}\n      worktree {4}".format(
                lane["id6"] or "-",
                lane["lane_id"],
                what,
                lane["branch"],
                lane["worktree"] or "(not registered)",
            )
        )
    return "\n".join(lines)


def print_lane_interrupt_report(lanes: list[dict[str, Any]]) -> None:
    """Print the E-06 report for the lanes a reclamation pass just handled."""
    if not lanes:
        return
    pal = Palette(should_color(sys.stderr))
    preserved = [lane for lane in lanes if lane.get("action") == "preserved"]
    reclaimed = [lane for lane in lanes if lane.get("action") == "reclaimed"]
    print(pal("\n--- Lane reclamation ---", "bold"), file=sys.stderr)
    if preserved:
        print(
            pal(
                "PRESERVED (holds work; inspect these, nothing was deleted):", "yellow"
            ),
            file=sys.stderr,
        )
        print(format_lane_report(preserved), file=sys.stderr)
        for lane in preserved:
            if lane.get("snapshot_commit"):
                print(
                    pal(
                        "      uncommitted edits committed as an interrupted snapshot "
                        "{0}".format(lane["snapshot_commit"][:12]),
                        "cyan",
                    ),
                    file=sys.stderr,
                )
    if reclaimed:
        print(
            pal("Reclaimed (provably empty, nothing to recover):", "dim"),
            file=sys.stderr,
        )
        for lane in reclaimed:
            print(
                "  {0} {1}".format(lane["id6"] or "-", lane["branch"]), file=sys.stderr
            )
    if not preserved and not reclaimed:
        print("No lane needed reclamation.", file=sys.stderr)


def build_recovery_lane_notice(
    item: dict[str, Any], state: dict[str, Any], recovery: bool
) -> str:
    """Tell a RESUMING agent, in the prompt, that it is continuing an interrupted attempt (E-11).

    Enriches the EXISTING `recovery` branch of the prompt (the `Mode: RECOVERY/CONTINUATION` line)
    with the lane facts E-04 now records, rather than adding a mechanism. A first attempt gets
    nothing, so a normal prompt is unchanged. There is deliberately NO acknowledgement gate and NO
    refusal path: a refusal would be one more way for an unattended run to stall. The point is that
    the agent must establish current state itself instead of assuming a clean start.
    """
    if not recovery:
        return ""
    lane_branch = item.get("preserved_branch")
    lane_path = item.get("preserved_worktree")
    lane_base = item.get("preserved_base")
    if not lane_branch:
        for attempt in reversed(item.get("attempts", []) or []):
            if attempt.get("worktree_branch"):
                lane_branch = attempt.get("worktree_branch")
                lane_path = attempt.get("worktree")
                lane_base = attempt.get("worktree_base")
                break
    lines = [
        "",
        "",
        "## You are continuing an INTERRUPTED attempt",
        "",
        "A previous attempt at this IPD was interrupted or killed before it finished. It is NOT a",
        "clean start. Whatever that attempt did is already on disk or already committed, and it may",
        "be half-applied. Establish the CURRENT state yourself before you edit anything: read the",
        "plan's execution/validation state, inspect the git log and the working tree, and check",
        "which E-items were actually performed. Do not assume the previous attempt did nothing, and",
        "do not assume it finished what it started.",
    ]
    if lane_branch:
        facts: list[str] = []
        try:
            from agent_workflows import worktree_lease

            repo = Path(state.get("repo", "."))
            lane_id = str(
                item.get("preserved_lane_id")
                or (item.get("attempts") or [{}])[-1].get("worktree_lane_id")
                or item.get("id6")
                or ""
            )
            st = worktree_lease.inspect_lane(
                repo, lane_id, base_commit=lane_base or "HEAD"
            )
            if st.commits_ahead:
                facts.append(f"it HOLDS {st.commits_ahead} commit(s) beyond its base")
            if st.dirty:
                facts.append("its tree has uncommitted changes")
            if not facts and st.exists:
                facts.append("it holds no commits and its tree is clean")
            if not st.exists:
                facts.append("it no longer exists")
        except Exception:
            facts.append("its current contents could not be read; inspect it yourself")
        lines.extend(
            [
                "",
                f"That attempt's lane branch is `{lane_branch}`"
                + (f" at `{lane_path}`" if lane_path else "")
                + ".",
                "State of that lane: " + "; ".join(facts) + ".",
                "A commit there whose message says INTERRUPTED SNAPSHOT is preserved uncommitted work",
                "from the interrupted attempt, not reviewed or validated work.",
            ]
        )
    return "\n".join(lines)


def allocate_isolation_worktree(repo: Path, id6: str) -> Any:
    """Allocate a per-lane git worktree for an execute-action child (reuses worktree_lease).

    Returns a `worktree_lease.WorktreeHandle` whose branch is normally `aw/lane/<id6>` in
    `.aw/worktrees/<id6>`, based at main HEAD, or raises `worktree_lease.WorktreeError` on a genuinely
    failed `git worktree add` (still fail-closed).

    laneorphan-01 (`zwnjp3`): allocation is now IDEMPOTENT for the same lane identity, so a run is
    never wedged by its own interrupt debris. It may ADOPT an existing empty lane at the same base, or
    return an ATTEMPT-SCOPED lane (`aw/lane/<id6>_attemptN` in `.aw/worktrees/<id6>_attemptN`) when the
    existing lane holds work, is cut from a stale base, is foreign, or is owned by a LIVE process.
    Read `handle.branch`, `handle.path`, and `handle.disposition` rather than assuming the name."""
    from agent_workflows import worktree_lease

    return worktree_lease.allocate_worktree(repo, id6, base_commit="HEAD")


def teardown_isolation_worktree(repo: Path, handle: Any) -> None:
    """Remove a lane's worktree + branch (reuses worktree_lease.teardown_worktree).

    DESTRUCTIVE: this deletes the lane BRANCH and force-removes the worktree, so it must only ever be
    called on a lane that holds NO work. Callers on a non-success path must go through
    `reclaim_lanes_on_interrupt`, which classifies first and preserves anything holding work."""
    from agent_workflows import worktree_lease

    worktree_lease.teardown_worktree(repo, handle, force=True)


# ---- STRANDED LANES: the reporting predicate (lanestrand-01 `pr5b0t` E-01/E-02) ------------------
#
# THE PREDICATE IS TWO SEPARATE QUESTIONS, and conflating them is the defect this section exists to
# prevent. `describe_lane` answers the FIRST ("does this lane hold work?") and CANNOT answer the
# SECOND ("has that work reached the integration target?"), because `inspect_lane` computes
# `commits_ahead` as `rev-list --count <base_sha>..<head>` where `base_sha` is the commit the lane was
# CUT FROM (read from the branch creation reflog by `worktree_lease._lane_base_sha`). That compares a
# lane against ITS OWN BASE, never against main.
#
# MEASURED, not reasoned (lanestrand-01 E-01, on a throwaway repo built the way the runner builds a
# lane, `git worktree add -b aw/lane/demo01 <path> <base>`):
#
#   BEFORE MERGE: state=HOLDS-WORK commits_ahead=1 holds_work=True   is-ancestor(lane,main) rc=1
#   AFTER  MERGE: state=HOLDS-WORK commits_ahead=1 holds_work=True   is-ancestor(lane,main) rc=0
#
# So `holds_work` stays True FOREVER after a successful `--no-ff` merge, and a predicate resting on it
# alone would report EVERY recovered lane as stranded permanently. Only
# `git merge-base --is-ancestor <lane-branch> <target>` distinguished the two states.

#: A lane that holds work which has NOT reached the integration target: unintegrated work, at risk of
#: being lost silently. The word is `ys1dor`'s (its OQ-02 resolved the screaming-red outcome word as
#: `STRANDED`), reused here rather than re-chosen, so the run summary and the cross-tree attention view
#: name the same condition identically.
LANE_STRANDED = "STRANDED"

#: A lane whose work HAS reached the integration target. Not an attention item: reporting it is the
#: same false positive in the other direction, and per the measurement above it is what a
#: `holds_work`-only predicate would do to every recovered lane.
LANE_LANDED = "LANDED"

#: A lane holding no work at all (clean, no commits beyond its base, or already gone). Nothing to lose.
LANE_EMPTY_OF_WORK = "EMPTY"

#: A lane currently owned by a LIVE process. Deliberately NOT reported: a driver run in progress
#: legitimately owns its lane, and a gate that reds during every normal run is a gate that gets
#: bypassed (the failure mode backlog `gjadwm` records).
LANE_LIVE = "LIVE"

#: A lane whose landing question could NOT be answered (the branch is gone, or git refused). It stays
#: VISIBLE as a stated unknown rather than resolving to a silent OK, which is the same ruling that
#: shaped `1f9m2j`/`zexed1`: do not print a green verdict the data does not support.
LANE_UNKNOWN = "UNKNOWN"

LANE_REPORT_STATES: tuple[str, ...] = (
    LANE_STRANDED,
    LANE_LANDED,
    LANE_EMPTY_OF_WORK,
    LANE_LIVE,
    LANE_UNKNOWN,
)

#: The states that need a human act, and are therefore worth reporting. `LANDED`, `EMPTY` and `LIVE`
#: are correct behavior and are deliberately silent.
LANE_ATTENTION_STATES: frozenset[str] = frozenset((LANE_STRANDED, LANE_UNKNOWN))

#: The integration target the landing question asks about, when the run record names no other. Both
#: drivers merge a verified lane into whatever the shared checkout has checked out, which is `main` in
#: this repository (`integrate_lane_branch` runs a bare `git merge` in the main checkout), so `HEAD` is
#: the honest fallback: it is the branch the merge would actually land on.
LANE_INTEGRATION_TARGET_FALLBACK = "HEAD"


def lane_work_has_landed(
    repo: Path, branch: str, *, target: str = LANE_INTEGRATION_TARGET_FALLBACK
) -> Optional[bool]:
    """Has ``branch``'s work reached ``target``? True / False / None when unanswerable.

    THE ONE GIT REACHABILITY QUESTION, and the only question in the stranded predicate that nothing
    existing already answers (see this section's header for the measurement). `git merge-base
    --is-ancestor <branch> <target>` is exact for both integration shapes the drivers produce: a
    fast-forward makes the lane tip an ancestor of the target trivially, and the controlled `--no-ff`
    merge makes it an ancestor through the merge commit.

    RETURNS THREE VALUES ON PURPOSE. `None` means the question could not be answered (the branch no
    longer exists, the target does not resolve, or git failed), and the caller must keep that visible
    as an UNKNOWN instead of reading it as either answer. git's own exit convention is 0 = ancestor,
    1 = not an ancestor, and anything else = error, which is why the error case is not folded into
    `False`.
    """
    if not branch:
        return None
    rc, _out, _err = _run_git(repo, ["rev-parse", "--verify", "--quiet", branch])
    if rc != 0:
        return None
    rc, _out, _err = _run_git(repo, ["rev-parse", "--verify", "--quiet", target])
    if rc != 0:
        return None
    rc, _out, _err = _run_git(repo, ["merge-base", "--is-ancestor", branch, target])
    if rc == 0:
        return True
    if rc == 1:
        return False
    return None


def classify_lane_integration(
    repo: Path,
    lane: dict[str, Any],
    *,
    target: str = LANE_INTEGRATION_TARGET_FALLBACK,
) -> dict[str, Any]:
    """Classify ONE recorded lane as `STRANDED` / `LANDED` / `EMPTY` / `LIVE` / `UNKNOWN`.

    THE TWO QUESTIONS, and which fact answers each:

      1. "Does this lane hold work?"  -> :func:`describe_lane`, which supplies `holds_work`,
         `commits_ahead`, `dirty`, `owner_live` and `owned_by_other_live_process`. This half is NOT
         reimplemented here; reimplementing it is the duplication `nuanaw`'s one-reader constraint
         forbids.
      2. "Has that work reached the integration target?" -> :func:`lane_work_has_landed`, the ONE added
         git reachability question. IT WENT IN A NEW HELPER RATHER THAN INTO `describe_lane` because
         `describe_lane`'s body is pinned byte-for-byte against a pre-move fingerprint fixture
         (`tests/fixtures/runner_shared_premove_fingerprints.json`, captured at HEAD `1ecc5891`) that
         proves it was a PURE MOVE out of the two runners; editing it would break that proof for a
         reason unrelated to what the proof is about, exactly as `lane_records_including_sweep`
         records for `_lane_records_from_state`.

    `holds_work` ALONE IS INSUFFICIENT AND MUST NOT BE TREATED AS SUFFICIENT BY A LATER READER. It is
    computed against the lane's OWN creation base, so it stays True forever after a successful merge
    (measured; see this section's header). A `holds_work`-only predicate reports every recovered lane
    as stranded permanently.

    ORDER OF DECISION, each exclusion deliberate:

      * LIVE first. A live owner means a run is in progress and the lane is correctly held. `owner_live`
        is `Optional[bool]` (`inspect_lane` sets it to `None` when no owner record exists), so `None` is
        an UNKNOWN owner and never a "not live"; only an explicit `True`, or
        `owned_by_other_live_process`, suppresses the report.
      * EMPTY next. No commits beyond base and a clean tree means there is nothing to lose.
      * Then the landing question. `True` -> LANDED (silent), `False` -> STRANDED, `None` -> UNKNOWN.

    PURE ENOUGH TO TEST: it prints nothing, exits nothing, and takes no argparse namespace. Rendering
    belongs to the consumer, and there is more than one consumer.

    CONVERGENCE NOTE (`nuanaw` ask 5 / plan `pr5b0t` E-02). Plan `rl67b0` (`integpath-04`) builds a
    lane RESOLVER for `aw <host> integrate <id6>` that reconstructs lane identity from the same
    `preserved_lane_id`/`preserved_base`/`preserved_branch` fields and refuses on `owner_live`. It was
    still `pending` when this landed, so this reader stands alone; when it lands, ITS resolver is the
    intended merge point and the lane-identity half here should be replaced by DELETION rather than by a
    rewrite. Do not fork a second lane resolver.
    """
    described = describe_lane(repo, lane)
    branch = described.get("branch") or lane.get("branch") or ""

    owner_live = described.get("owner_live")
    live = bool(described.get("owned_by_other_live_process")) or owner_live is True

    if live:
        landed = lane_work_has_landed(repo, str(branch), target=target)
        state = LANE_LIVE
        why = "a live process currently owns this lane"
    elif not described.get("holds_work"):
        landed = None
        state = LANE_EMPTY_OF_WORK
        why = "the lane holds no commits beyond its base and its tree is clean"
    else:
        landed = lane_work_has_landed(repo, str(branch), target=target)
        if landed is True:
            state = LANE_LANDED
            why = "the lane's work is reachable from {0}".format(target)
        elif landed is False:
            state = LANE_STRANDED
            why = "the lane holds work that is NOT reachable from {0}".format(target)
        else:
            state = LANE_UNKNOWN
            why = (
                "the lane holds work but whether it reached {0} could not be determined "
                "(branch or target unresolvable)".format(target)
            )

    record = dict(described)
    record["lane_state"] = state
    record["landed"] = landed
    record["integration_target"] = target
    record["why"] = why
    record["needs_attention"] = state in LANE_ATTENTION_STATES
    return record


def stranded_lane_records(
    repo: Path,
    states: Any,
    *,
    target: str = LANE_INTEGRATION_TARGET_FALLBACK,
    attention_only: bool = True,
) -> list[dict[str, Any]]:
    """Every lane needing attention across ``states`` (an iterable of run-record ``state.json`` dicts).

    THE ONE READER. Both the end-of-run summary and the cross-tree attention view consume this rather
    than each deriving its own verdict, because two derivations of "is this work lost" would drift and
    only one of them would be wrong at a time.

    THE FACTS COME FROM THE RUN RECORD, NEVER FROM A FILESYSTEM WALK. The lane identity, branch, base
    and integration signal are read back through :func:`lane_records_including_sweep` (which composes
    `_lane_records_from_state` and adds the coordinator's review sweep lane); the only live probe is the
    lane classification itself. This is why the historical record of a run keeps reporting what it did
    at the time: a verdict derived from today's filesystem would report a recovered run clean and
    rewrite history, which is what `xtklpd`'s review measured.

    Each record carries `lane_state`, `landed`, `integration_target`, `why`, `needs_attention` plus
    every `describe_lane` field, and additionally `run_id`, `id6`, `item_status`, `integration_signal`,
    `preserved_reason` and `worktree` so a caller can render without a second pass. `integration_detail`
    IS ON THE ATTEMPT AND NOT THE ITEM (`ys1dor` F-10 measured the item's 21 keys and it is absent), so
    it is read from `item["attempts"][-1]` and tolerated as absent.

    ABSOLUTE PATHS ARE NOT SANITIZED HERE, deliberately: `worktree` is returned as recorded because a
    caller that must ACT on the lane needs the real path. RENDERING is where the repository-relative
    rule binds (`preserved_worktree` is an absolute home path in most recorded items), and
    `lane_worktree_display` below is the shared way to satisfy it.

    De-duplicated by `(run_id, branch, worktree)`, so one lane named by both an attempt and the
    item-level `preserved_*` fields yields one record.
    """
    from agent_workflows import worktree_lease

    if worktree_lease._WORKTREE_CACHE is None:
        with worktree_lease.memoize_worktrees(repo):
            return stranded_lane_records(
                repo, states, target=target, attention_only=attention_only
            )

    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for state in states:
        if not isinstance(state, dict):
            continue
        run_id = str(state.get("run_id") or "")
        queue = state.get("queue") or []
        by_id: dict[str, dict[str, Any]] = {}
        for item in queue:
            if isinstance(item, dict) and item.get("id6"):
                by_id[str(item["id6"])] = item
        try:
            lanes = lane_records_including_sweep(state)
        except Exception:
            continue

        # E-02: Fast pruning for cleanly terminal runs with no preserved worktrees
        if attention_only and queue:
            has_pres = any(
                bool(it.get("preserved_worktree"))
                for it in queue
                if isinstance(it, dict)
            )
            if not has_pres:
                all_term = all(
                    it.get("status") in ("executed", "done", "graduated")
                    for it in queue
                    if isinstance(it, dict)
                )
                if all_term:
                    sweep = review_sweep_lane_record(state)
                    if sweep is None or sweep.get("retired"):
                        wt_cache = worktree_lease._WORKTREE_CACHE or {}
                        br_cache = worktree_lease._BRANCH_CACHE or {}
                        any_live = False
                        for lane_rec in lanes:
                            b = lane_rec.get("branch") or ""
                            ref = "refs/heads/" + b if b else ""
                            if ref in wt_cache or ref in br_cache:
                                any_live = True
                                break
                        if not any_live:
                            continue

        for lane in lanes:
            key = (
                run_id,
                str(lane.get("branch") or ""),
                str(lane.get("worktree") or ""),
            )
            if key in seen:
                continue
            seen.add(key)
            try:
                record = classify_lane_integration(repo, lane, target=target)
            except Exception:
                # A lane we cannot classify is an UNKNOWN, never a silent pass.
                record = {
                    "lane_id": lane.get("lane_id"),
                    "branch": lane.get("branch"),
                    "worktree": lane.get("worktree"),
                    "lane_state": LANE_UNKNOWN,
                    "landed": None,
                    "integration_target": target,
                    "why": "the lane could not be classified",
                    "needs_attention": True,
                }
            if attention_only and not record.get("needs_attention"):
                continue
            item = by_id.get(str(lane.get("id6") or ""), {})
            attempts = item.get("attempts") or []
            last_attempt = (
                attempts[-1] if attempts and isinstance(attempts[-1], dict) else {}
            )
            record["run_id"] = run_id
            record["id6"] = lane.get("id6")
            record["item_status"] = lane.get("status") or item.get("status")
            record["integration_signal"] = item.get(
                "integration_signal"
            ) or last_attempt.get("integration_signal")
            record["integration_detail"] = last_attempt.get("integration_detail")
            record["preserved_reason"] = item.get("preserved_reason")
            record.setdefault("worktree", lane.get("worktree"))
            out.append(record)
    out.sort(key=lambda r: (str(r.get("branch") or ""), str(r.get("run_id") or "")))
    return out


def lane_worktree_display(repo: Path, worktree: Any) -> Optional[str]:
    """A lane worktree rendered SAFE for a human board or an agent-consumed payload, or None.

    THE PROHIBITION THIS EXISTS TO ENFORCE, measured rather than supposed: `preserved_worktree` is an
    ABSOLUTE path under the maintainer's home directory in most recorded run items, and `ys1dor`'s
    review independently measured the same field and FORBADE printing it. `aw attention --json` is a
    payload agents paste and CI reads, and `attention.Item.path` is contractually "repo-relative
    POSIX", so an absolute worktree would violate both the leak rule and the payload's own field
    contract.

    Returns a repository-relative POSIX path when the worktree lies inside ``repo`` (the normal case:
    lanes live under `.aw/worktrees/<lane>`), and otherwise returns None so the caller OMITS it rather
    than leaking it. Never returns an absolute path.
    """
    if not worktree:
        return None
    try:
        candidate = Path(str(worktree))
        root = Path(repo).resolve()
        rel = candidate.resolve().relative_to(root)
    except (ValueError, OSError, RuntimeError):
        # Outside the repository (or unresolvable): omit rather than leak.
        name = Path(str(worktree)).name
        parent = Path(str(worktree)).parent.name
        if parent == "worktrees" and name:
            # The canonical lane shape, reconstructed WITHOUT the absolute prefix.
            return ".aw/worktrees/{0}".format(name)
        return None
    text = rel.as_posix()
    return text if text not in ("", ".") else None


# ---- the REVIEW SWEEP LANE ------------------------------------------------------------------------
# dirtygates Order 05 (`ajxr5d`) E-02/E-04/E-11, OQ-02 + OQ-04 (both resolved by the maintainer).
#
# WHY A REVIEW NEEDS A LANE AT ALL, measured rather than argued. A review turn is NOT read-only with
# respect to the tree: it edits the plan under review and adds a review record, and it committed both
# to MAIN (commit `a9510164`). Worse, measured live 2026-09-13, reviewing the orchestrator `8lfoum`
# produced commit `59cdc718` holding FIVE files, three of them SIBLING CHILD PLANS (`d7qoxv`,
# `metc8b`, `u23gbn`) that were still `queued` in the same run, so one item's turn rewrote three other
# items' pending input before their turns ran. Those files sat uncommitted for ~36 minutes and a
# concurrent execute run had its items refused against them.
#
# WHY ONE LANE FOR THE WHOLE SWEEP AND NOT ONE PER REVIEW (OQ-02, maintainer). A review writes only two
# files, both scoped to the plan under review, so reviews in a shared lane touch DISJOINT paths and
# there is nothing to collide over. And one lane is what makes SESSION SHARING safe by construction:
# incident `lanesess xd9sll` was N TREES to ONE session (sessions keyed per SET, worktrees allocated
# per ITEM, so an opencode session's own directory binding overrode `--dir`), and ONE tree to ONE
# session cannot reproduce that cardinality mismatch. The accepted cost, stated plainly: the sweep
# shares one lane, so a conflict strands that review rather than only that item's merge.
#
# WHY THE LANE MUST BE REFRESHED (OQ-04, maintainer chose option (a)). The lane is cut ONCE at
# `base_commit="HEAD"`, and every review then merges to main, so main advances while the lane keeps its
# original base. Measured in a scratch repo: after two reviews merged, the lane still read `peer v1`
# while main read `peer v2`, and a plan a peer corrected ON MAIN mid-sweep read its PRE-correction text
# inside the lane. In a nine-item sweep, review 9 would read a tree eight merges behind - which is the
# exact opposite of the cross-plan awareness one shared lane was chosen to preserve.

#: The sweep lane's identity. NOT an item id6, deliberately: it is a COORDINATOR-owned resource whose
#: lifetime spans many items, so keying it on any one item's id6 would make that item's completion look
#: like the lane's owner. Prefixed `review-sweep-` so `_lane_records_from_state`'s reader and an
#: operator reading `git worktree list` can both tell what it is at a glance.
REVIEW_SWEEP_LANE_PREFIX = "review-sweep-"


def review_sweep_lane_id(run_id: str) -> str:
    """The sweep lane's id for `run_id`, e.g. `review-sweep-run-2026...`.

    RUN-SCOPED, so two concurrent runs each get their own sweep lane instead of fighting over one, and
    so an interrupted run's sweep lane is attributable to the run that left it.
    """
    return "{0}{1}".format(REVIEW_SWEEP_LANE_PREFIX, run_id)


def is_review_sweep_lane_id(lane_id: str) -> bool:
    """Whether `lane_id` designates a review sweep lane rather than a per-item execute lane."""
    return bool(lane_id) and str(lane_id).startswith(REVIEW_SWEEP_LANE_PREFIX)


def allocate_review_sweep_worktree(repo: Path, run_id: str) -> Any:
    """Allocate the ONE lane every review turn of `run_id` runs in (E-02).

    Reuses `worktree_lease.allocate_worktree`, the SAME machinery an execute lane uses, so there is no
    second isolation path: the only difference is the lane IDENTITY (run-scoped, not item-scoped) and
    the fact that the coordinator allocates it once instead of the per-item path allocating it per turn.

    IDEMPOTENT for the same run, which is what makes it safe to call before every review turn rather
    than requiring the caller to remember whether it already holds one: `allocate_worktree` ADOPTS an
    existing EMPTY lane at the same base and ATTEMPT-SCOPES alongside one holding work. Note the
    adoption path is the common one only for a lane that is still at its base; once the sweep's first
    review has committed, callers must reuse the handle they already have rather than re-allocating,
    because a lane holding work would be attempt-scoped into a SECOND tree. See `refresh_sweep_lane`
    for how a reused handle is kept current.
    """
    from agent_workflows import worktree_lease

    return worktree_lease.allocate_worktree(
        repo, review_sweep_lane_id(run_id), base_commit="HEAD"
    )


class SweepLaneRefresh(NamedTuple):
    """The outcome of one attempt to bring the sweep lane up to main (E-02, OQ-04 option (a)).

    Carries WHY it did or did not happen, not merely whether: a refusal is a normal outcome (the lane
    legitimately holds an in-flight edit, or it has diverged) and the next review must be told which,
    because a stale tree changes what that review READS while a diverged one changes what it can MERGE.
    """

    refreshed: bool
    reason: str
    #: The lane's HEAD after this call, so a caller can record what the next turn actually reads.
    head: str | None = None
    #: True when the lane was ALREADY current, which is the no-op case and not a failure.
    already_current: bool = False


def refresh_sweep_lane(
    repo: Path, handle: Any, *, main_ref: str = "HEAD"
) -> SweepLaneRefresh:
    """Fast-forward the sweep lane to main between reviews (OQ-04 option (a), the maintainer's choice).

    THE DEFECT THIS CLOSES, measured at review round 2 (finding F-14): the sweep lane is cut once at
    sweep start and NOTHING refreshed it, so cross-plan awareness - one of the two reasons OQ-02 chose a
    single lane - degraded monotonically with every merge. Verified before writing this: no rebase,
    refresh, or re-base-onto helper existed anywhere in `worktree_lease.py` or either runner.

    IT IS `--ff-only`, AND THAT IS THE WHOLE SAFETY ARGUMENT. A fast-forward can only ever move the lane
    FORWARD to a commit that already contains its history, so it cannot rewrite, drop, or reorder a
    commit the lane holds. If the lane has DIVERGED (it holds a commit main does not), git REFUSES and
    this reports that refusal instead of forcing anything. Never `rebase`, never `merge --no-ff`, never
    `reset --hard`: each of those can move or discard lane work, and the lane may hold a review that has
    not merged yet.

    IT REFUSES ON A DIRTY LANE, BEFORE TOUCHING GIT. A review's own in-flight edits live in the lane's
    working tree, and `git merge --ff-only` updates tracked files, so refreshing over uncommitted work
    risks a checkout conflict at best and a silent overwrite of an edit at worst. A dirty lane is
    therefore left EXACTLY as it is and the staleness is reported, which is the conservative half of the
    trade OQ-04 accepted.
    """
    lane_path = Path(getattr(handle, "path", "") or "")
    if not lane_path.is_dir():
        return SweepLaneRefresh(
            refreshed=False, reason="the sweep lane's worktree is not present on disk"
        )

    rc, dirty_out, _err = _run_git(lane_path, ["status", "--porcelain"])
    if rc != 0:
        return SweepLaneRefresh(
            refreshed=False,
            reason="could not read the sweep lane's status; left untouched",
        )
    if dirty_out.strip():
        return SweepLaneRefresh(
            refreshed=False,
            reason=(
                "the sweep lane holds UNCOMMITTED work, so it was left exactly as it is rather than "
                "risk a refresh overwriting an in-flight review edit"
            ),
        )

    rc, target, _err = _run_git(repo, ["rev-parse", main_ref])
    if rc != 0:
        return SweepLaneRefresh(
            refreshed=False, reason=f"could not resolve {main_ref} in the main checkout"
        )
    target_sha = target.strip()

    rc, before, _err = _run_git(lane_path, ["rev-parse", "HEAD"])
    lane_head = before.strip() if rc == 0 else None
    if lane_head and lane_head == target_sha:
        return SweepLaneRefresh(
            refreshed=False,
            reason="the sweep lane is already at main; nothing to refresh",
            head=lane_head,
            already_current=True,
        )

    rc, _out, err = _run_git(lane_path, ["merge", "--ff-only", target_sha])
    if rc != 0:
        # A DIVERGED lane, which is the expected refusal when a review's merge has not landed yet. Not
        # an error and not a data-loss risk: the lane keeps its own commits, main keeps its own, and the
        # next review simply reads a tree that is behind. Reported so the run record can say so.
        return SweepLaneRefresh(
            refreshed=False,
            reason=(
                "the sweep lane could not fast-forward to main (it holds commits main does not); "
                "left untouched: " + (err or "").strip()
            ),
            head=lane_head,
        )
    rc, after, _err = _run_git(lane_path, ["rev-parse", "HEAD"])
    return SweepLaneRefresh(
        refreshed=True,
        reason="the sweep lane was fast-forwarded to main",
        head=after.strip() if rc == 0 else target_sha,
    )


#: Where the sweep lane's identity lives in durable run state. RUN-LEVEL, not per item, because the
#: lane is a COORDINATOR resource whose lifetime spans many items: recording it under one item would
#: make that item's completion look like the lane's owner and would leave the lane unfindable after it.
REVIEW_SWEEP_LANE_KEY = "review_sweep_lane"


def review_sweep_lane_record(state: dict[str, Any]) -> dict[str, Any] | None:
    """The sweep lane this run allocated, read back from durable state, or None."""
    record = state.get(REVIEW_SWEEP_LANE_KEY)
    return record if isinstance(record, dict) and record.get("branch") else None


def lane_records_including_sweep(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Every lane this run allocated, INCLUDING the review sweep lane (`ajxr5d` E-11).

    COMPOSES `_lane_records_from_state` rather than editing it, and that is deliberate rather than
    stylistic: that function's body is pinned BYTE-FOR-BYTE against a pre-move fingerprint fixture
    (`runner_shared_premove_fingerprints.json`, captured at HEAD `1ecc5891`) which proves it was a PURE
    MOVE out of the two runners. Editing it would break that proof for a reason unrelated to what the
    proof is about. So the per-item reader stays exactly as it was and the sweep lane is added here.

    WHY THE SWEEP LANE NEEDS ITS OWN SOURCE AT ALL, since a review turn does record its lane on its own
    attempt (so the per-item reader usually finds it): a run interrupted BETWEEN reviews, or one whose
    sweep lane was allocated and then refused before any attempt recorded it, leaves a lane no attempt
    names. Without the RUN-LEVEL record the interrupt reclaimer would not see it, and the lane would be
    leaked with no owner - which is exactly the orphan class `laneorphan-01` exists to prevent.

    De-duplicated by `(branch, worktree)` exactly as the per-item reader does, so the common case yields
    ONE record and not two.
    """
    lanes = _lane_records_from_state(state)
    sweep = review_sweep_lane_record(state)
    if sweep is None or sweep.get("retired"):
        return lanes
    key = "{0}|{1}".format(sweep.get("branch"), sweep.get("worktree"))
    if any(
        "{0}|{1}".format(rec.get("branch"), rec.get("worktree")) == key for rec in lanes
    ):
        return lanes
    lanes.append(
        {
            "worktree": sweep.get("worktree"),
            "branch": sweep.get("branch"),
            "lane_id": sweep.get("lane_id"),
            "base_commit": sweep.get("base_commit"),
            "disposition": sweep.get("disposition"),
            # NOT an item's id6, because the lane belongs to no ITEM. The lane id is carried in that slot
            # so a report names something an operator can act on rather than an empty column.
            "id6": sweep.get("lane_id"),
            "status": "review-sweep",
        }
    )
    return lanes


def review_sweep_lane_handle(state: dict[str, Any]) -> Any | None:
    """Rebuild the sweep lane's `WorktreeHandle` from durable state, or None if none was allocated.

    REBUILT FROM STATE rather than held in memory, for the reason `retry_deferred_integrations` rebuilds
    its own handles: the coordinator's retirement happens in a LATER stack frame than the turn that
    allocated the lane, and an interrupted run must be able to find the lane in a whole new process.
    """
    from agent_workflows import worktree_lease

    record = review_sweep_lane_record(state)
    if record is None:
        return None
    return worktree_lease.WorktreeHandle(
        lane_id=str(record.get("lane_id") or ""),
        path=Path(str(record.get("worktree") or "")),
        branch=str(record.get("branch") or ""),
        base_commit=str(record.get("base_commit") or ""),
    )


#: Where the sweep's SHARED SESSION id lives. RUN-LEVEL and keyed to the sweep, NOT to a set, because
#: the review sweep is a run-wide sweep: `aw oc run reviews` selects every plan awaiting review across
#: every Set, and the CLI's promise is that "all reviews in a run share the same session for continuity".
#: Keying it per set would silently split that continuity the first time a sweep spanned two Sets.
REVIEW_SWEEP_SESSION_KEY = "review_sweep_session"


def turn_runs_in_review_sweep_lane(state: dict[str, Any], work_dir: str | None) -> bool:
    """Whether `work_dir` IS this run's sweep lane (`ajxr5d` E-04).

    THE DISTINCTION THIS DRAWS IS THE WHOLE OF `xd9sll`'s RULE, correctly stated. That incident is
    usually summarized as "an isolated turn must never reuse a session", but the recorded CAUSE is a
    MISMATCH OF CARDINALITY: sessions were keyed per SET while worktrees were allocated per ITEM, so
    lanes 2..N inherited lane 1's session and an opencode session's own directory binding overrode
    `--dir`. The invariant that actually holds is therefore NARROWER and stronger: never carry one
    session into a DIFFERENT TREE.

    A per-item execute lane is a different tree on every turn, so it must keep getting a fresh session -
    unchanged. The review sweep lane is ONE tree for every review in the run, so one session in it
    cannot reproduce the incident by construction, which is why OQ-02's one-lane ruling dissolved the
    apparent conflict with the sweep's promised continuity rather than trading against it.

    COMPARED BY RESOLVED PATH, not by string: a symlinked or relative spelling of the same tree is the
    same tree, and answering False for it would silently drop the continuity this exists to preserve.
    """
    if not work_dir:
        return False
    record = review_sweep_lane_record(state)
    if record is None:
        return False
    recorded = str(record.get("worktree") or "")
    if not recorded:
        return False
    try:
        return os.path.realpath(str(work_dir)) == os.path.realpath(recorded)
    except OSError:  # pragma: no cover - defensive
        return str(work_dir) == recorded


def acquire_review_sweep_lane(
    repo: Path,
    run_dir: Path,
    state: dict[str, Any],
    *,
    save_state: Callable[[Path, dict[str, Any]], None],
) -> tuple[Any, SweepLaneRefresh | None]:
    """Return the ONE lane every review turn of this run shares, allocating it on first use (E-02).

    Returns `(handle, refresh)` where `refresh` is None on the allocating call (a brand-new lane is cut
    from HEAD and is current by construction) and the `SweepLaneRefresh` outcome on every reuse.

    ALLOCATED LAZILY ON THE FIRST REVIEW rather than eagerly at run start, and this is a deliberate
    narrowing of the plan's wording ("allocated by the COORDINATOR once, before the first review
    dispatches"). The property that matters is ONE LANE FOR THE WHOLE SWEEP, and lazy allocation delivers
    exactly that while additionally not cutting a worktree for a run that contains no review items at
    all. It is still coordinator-owned in the sense that decides the semantics: the lane is keyed on the
    RUN, its record lives in run-level state, and its retirement is the coordinator's (see
    `retire_review_sweep_lane`), so no item's turn can destroy the lane the next review needs.

    THE REFRESH IS HERE, ON REUSE, WHICH IS THE ONLY PLACE IT IS BOTH CORRECT AND SUFFICIENT (OQ-04
    option (a)). It runs before the next review is dispatched and after the previous one's merge has had
    its chance to land, which is precisely the window the maintainer's ruling names. A refusal (dirty or
    diverged lane) is returned rather than raised: a stale tree is a reportable condition, not a reason
    to abandon a review.
    """
    existing = review_sweep_lane_handle(state)
    if existing is not None and Path(existing.path).is_dir():
        refresh = refresh_sweep_lane(repo, existing)
        record = dict(review_sweep_lane_record(state) or {})
        record["turns"] = int(record.get("turns", 0)) + 1
        record["last_refresh"] = refresh.reason
        record["last_refresh_refreshed"] = refresh.refreshed
        if refresh.head:
            record["head"] = refresh.head
        state[REVIEW_SWEEP_LANE_KEY] = record
        save_state(run_dir, state)
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "review-sweep-lane-refreshed",
                "lane_id": existing.lane_id,
                "branch": existing.branch,
                "refreshed": refresh.refreshed,
                "detail": refresh.reason,
                "head": refresh.head,
            },
        )
        return existing, refresh

    handle = allocate_review_sweep_worktree(repo, str(state.get("run_id") or ""))
    state[REVIEW_SWEEP_LANE_KEY] = {
        "lane_id": handle.lane_id,
        "branch": handle.branch,
        "worktree": str(handle.path),
        "base_commit": handle.base_commit,
        "disposition": getattr(handle, "disposition", "created"),
        "displaced_from": getattr(handle, "displaced_from", None),
        "turns": 1,
    }
    save_state(run_dir, state)
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "at": utc_now(),
            "event": "review-sweep-lane-allocated",
            "lane_id": handle.lane_id,
            "branch": handle.branch,
            "worktree": str(handle.path),
            "base_commit": handle.base_commit,
            "disposition": getattr(handle, "disposition", "created"),
        },
    )
    return handle, None


def retire_review_sweep_lane(
    repo: Path,
    run_dir: Path,
    state: dict[str, Any],
    *,
    save_state: Callable[[Path, dict[str, Any]], None],
    reason: str = "sweep complete",
) -> dict[str, Any] | None:
    """Retire the sweep lane at the END of the run, preserving it if it still holds work (E-11).

    Returns a record of what happened, or None when this run allocated no sweep lane. Idempotent: once
    the lane is gone the record is marked and a second call is a no-op, so wiring it into more than one
    coordinator exit path (normal drain, refused item, interrupt) is safe.

    CLASSIFIES BEFORE DESTROYING, through `lane_containment.teardown_review_sweep_lane`, which is the
    EXISTING spec-R5.5 gate. So a sweep ending with an unmerged review keeps its lane, its branch and
    its commit, and the run record says which condition held. That is not a nicety: a stranded review is
    the measured failure mode of a shared lane whose merge conflicts, and force-removing the lane would
    convert a recoverable stranding into destroyed work.
    """
    from agent_workflows import lane_containment

    record = review_sweep_lane_record(state)
    if record is None or record.get("retired"):
        return record
    handle = review_sweep_lane_handle(state)
    if handle is None:
        return record
    # EVERY REVIEW ITEM THAT USED THE LANE is handed to the gate, because the submission-retention
    # question is per ITEM while the lane is shared: with no items the gate correctly refuses (absence of
    # a receipt means NOT collected, spec R2.5), which would make a clean shared lane unretirable.
    decision = lane_containment.teardown_review_sweep_lane(
        repo=repo,
        handle=handle,
        run_dir=run_dir,
        items=[
            entry
            for entry in state.get("queue", [])
            if entry.get("action") == "review"
            or entry.get("review_integrated") is not None
        ],
    )
    record = dict(record)
    record["retired"] = bool(decision.torn_down)
    record["retire_reason"] = decision.reason if not decision.torn_down else reason
    record["retire_reason_codes"] = list(decision.reason_codes)
    if not decision.torn_down:
        # PRESERVED, and named where a reader looks. The lane holds something the gate could not
        # account for, which for a sweep lane is most often a review whose merge did not land.
        record["preserved_worktree"] = str(handle.path)
        record["preserved_branch"] = handle.branch
    state[REVIEW_SWEEP_LANE_KEY] = record
    save_state(run_dir, state)
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "at": utc_now(),
            "event": (
                "review-sweep-lane-retired"
                if decision.torn_down
                else "review-sweep-lane-preserved"
            ),
            "lane_id": handle.lane_id,
            "branch": handle.branch,
            "worktree": str(handle.path),
            "detail": record["retire_reason"],
            "reason_codes": list(decision.reason_codes),
        },
    )
    return record


def commit_review_lane_output(
    repo: Path, handle: Any, id6: str, *, host_label: str
) -> tuple[str | None, tuple[str, ...]]:
    """Commit a review turn's UNCOMMITTED lane output to the lane branch, so the merge can carry it.

    Returns `(commit_sha_or_None, committed_paths)`. `None` means the lane tree was already clean, which
    is the normal case for a review that committed its own work; NO empty commit is ever made.

    WHY THIS IS REQUIRED AND IS NOT THE DRIVER OVERSTEPPING (`ajxr5d`, found while executing E-03). Before
    isolation, a review that edited the plan and wrote its record but did NOT commit left those files in
    MAIN's working tree, where the operator saw them and could commit them - the dirty window this plan
    exists to close, but also, incidentally, a place the work survived. In a lane, uncommitted files are
    INVISIBLE to `integrate_lane_branch`, which merges the BRANCH (`git diff base..branch`), and the lane
    is later torn down. So isolating a review WITHOUT this step would silently DESTROY the output of any
    review that did not commit for itself, which is a strictly worse outcome than the dirty tree. Landing
    the work is therefore the conservative choice, not the liberal one.

    IT IS PATH-SCOPED, ALWAYS, and never `git add -A`/`git add .`/`git commit -a` (the execution contract
    forbids all three). The staged set is exactly what `git status --porcelain` reports INSIDE THE LANE,
    which by construction is only this turn's own work: the lane is cut fresh from HEAD for the sweep and
    nothing else writes to it. It also cannot sweep a co-worker's edit into a commit, because a co-worker
    works in the shared checkout and not in the driver's lane.

    NO HOOK-SUPPRESSING FLAG IS USED, and no `--no-verify`: this is an ordinary `git commit`, so whatever
    a repository's hooks would say about a review's output they still say. A hook REJECTION is returned as
    "nothing committed" (`None`), which leaves the work in the lane and makes the integration a no-op that
    the caller reports rather than a silent loss.
    """
    wt = Path(getattr(handle, "path", "") or "")
    if not wt.is_dir():
        return None, ()
    rc, out, _err = _run_git(wt, ["status", "--porcelain"])
    if rc != 0 or not out.strip():
        return None, ()
    paths: list[str] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        entry = line[3:] if len(line) > 3 else ""
        if (
            " -> " in entry
        ):  # a rename: stage BOTH endpoints or the commit is half a move
            old, new = entry.split(" -> ", 1)
            paths.extend([old.strip().strip('"'), new.strip().strip('"')])
        elif entry.strip():
            paths.append(entry.strip().strip('"'))
    paths = sorted({p for p in paths if p})
    if not paths:
        return None, ()
    rc, _out, _err = _run_git(wt, ["add", "--", *paths])
    if rc != 0:
        return None, ()
    subject = f"review({host_label}): record the review of {id6}"
    rc, _out, _err = _run_git(
        wt,
        [
            "commit",
            "-m",
            subject,
            "-m",
            (
                "Committed by the driver because the review turn left its output uncommitted in its "
                "lane. Path-scoped to the paths the turn itself wrote; hooks ran normally."
            ),
            "--",
            *paths,
        ],
    )
    if rc != 0:
        # A hook refused, or there was nothing to commit after all. Leave the work in the lane: the
        # caller reports a non-integration and the lane is PRESERVED rather than torn down.
        return None, tuple(paths)
    rc, sha, _err = _run_git(wt, ["rev-parse", "HEAD"])
    return (sha.strip() if rc == 0 else None), tuple(paths)


class ReviewWriteScope(NamedTuple):
    """WHAT one review turn wrote, split into what a review is FOR and what it reached beyond (E-10).

    ``allowed`` is the plan under review plus its own review record. ``out_of_scope`` is everything
    else, and ``queued_siblings`` is the subset of that which belongs to an item STILL QUEUED in the
    same run - the measured harm (F-9), and the one case the run record must never be silent about.
    """

    changed: tuple[str, ...]
    allowed: tuple[str, ...]
    out_of_scope: tuple[str, ...]
    queued_siblings: tuple[str, ...]

    @property
    def clean(self) -> bool:
        return not self.out_of_scope


def review_record_path_fragment(id6: str) -> str:
    """The distinguishing fragment of a review record's filename for plan `id6`.

    Reviews are named by the uniform artifact grammar (`...-<id6>-<slug>.review.md`), so an id6 plus the
    `.review.md` type facet identifies THIS plan's record without this module having to know the whole
    naming grammar (which `artifact_core` owns and which must not be re-forked here).
    """
    return str(id6)


def lane_branch_tip(repo: Path, handle: Any) -> str | None:
    """The lane branch's current commit sha, or None when it cannot be read.

    Captured by a caller BEFORE a turn runs, so the turn's own writes can later be measured from it
    (see :func:`review_turn_changed_files`). Returns None rather than raising: this feeds a REPORTING
    path, and a run must never die because a scope report could not resolve a rev.
    """
    branch = str(getattr(handle, "branch", "") or "")
    if not branch:
        return None
    rc, out, _err = _run_git(repo, ["rev-parse", "--verify", "--quiet", branch])
    tip = out.strip()
    return tip or None if rc == 0 else None


def review_turn_changed_files(
    repo: Path, handle: Any, *, since_commit: str | None
) -> tuple[str, ...]:
    """The paths THIS review turn wrote, measured from the turn's OWN commits.

    DELIBERATELY NOT `build_lane_outcome(...).changed_files`, which is what this replaced and which was
    WRONG FOR A REVIEW for a structural reason rather than a subtle one. That helper measures
    ``git diff <base>..<branch>`` where ``base`` is the worktree base FROZEN AT ALLOCATE. For an EXECUTE
    turn that is exactly right: the lane is cut per item and torn down after it, so its base is the
    turn's own starting point. But the REVIEW SWEEP LANE is allocated ONCE PER RUN
    (`review_sweep_lane`, base ``HEAD``) and is deliberately NOT torn down between reviews, because
    every review of the run shares the one tree. So one frozen base serves the whole run while `main`
    keeps moving, and `base..branch` then reports every file MAIN changed as though this review had
    written it.

    MEASURED 2026-09-17, which is why this function exists: a review of plan `5w8g8j` whose own commit
    touched exactly TWO files (its plan and its review record) was reported as having "also wrote 34
    path(s) outside its own plan and review record", and the named paths included `oc_runipd.py`,
    `runner_shared.py`, `cli.py`, thirteen test files, `CHANGELOG.md` and a spec. A plan review cannot
    write product code, and it had not: those were `main`'s own commits, landed by other turns and by
    concurrent sessions while the sweep lane's base stayed put. On a live sweep lane the drift was 42
    commits.

    WHY THAT MATTERED RATHER THAN BEING COSMETIC NOISE. The scope report exists for a REAL measured
    harm (`ajxr5d` F-9): an orchestrator review silently rewrote three sibling child plans that had not
    had their turns. The chosen shape is PERMIT-AND-RECONCILE, so the report IS the whole guard: there
    is no refusal behind it. A guard that names 34 innocent paths every run is one an operator learns
    to skim, and then the one real sibling rewrite is skimmed with it.

    ``since_commit`` is the lane branch tip as it stood BEFORE this turn ran, captured by the caller at
    lane acquisition. When it is None (no tip recorded, a first-use lane with no commits yet, or an
    unreadable rev) this falls back to the frozen-base measurement rather than reporting nothing:
    OVER-reporting is the safe direction here, because the failure mode of under-reporting is the
    silent sibling rewrite this guard was built to catch.
    """
    branch = str(getattr(handle, "branch", "") or "")
    if not branch:
        return ()
    since = str(since_commit or "").strip()
    if not since:
        # Fall back to the frozen base: noisier, never blind.
        since = str(getattr(handle, "base_commit", "") or "").strip()
    if not since:
        return ()
    rc, out, _err = _run_git(repo, ["diff", "--name-only", f"{since}..{branch}"])
    if rc != 0:
        return ()
    return tuple(line.strip() for line in out.splitlines() if line.strip())


def classify_review_writes(
    changed_files: Sequence[str],
    *,
    id6: str,
    queued_id6s: Sequence[str] = (),
) -> ReviewWriteScope:
    """Split a review lane's changed paths into the two files a review is FOR and anything beyond (E-10).

    A REVIEW'S LEGITIMATE OUTPUT IS EXACTLY TWO FILES, measured on commit `a9510164`: the plan under
    review (revisions applied) and its review record. A path is `allowed` when it carries this plan's
    OWN id6; everything else is out of scope.

    THE SHAPE CHOSEN IS PERMIT-AND-RECONCILE, NOT REFUSE (E-10's explicit choice, recorded in the plan's
    decisions register). WHY: an ORCHESTRATOR review SHOULD read its children - that is exactly how this
    Set's collision with three approved plans was caught - and it may have a genuine reason to correct a
    child's text. Refusing would break that legitimate case, and the objection measured in F-9 was never
    that the write happened but that it happened SILENTLY, to an item that had not had its turn. So the
    write is permitted and NAMED, mirroring the execute path's own two-way scope reconciliation
    (`_compute_scope_reconciliation`), which is reachable only from finalize and therefore never runs for
    a review.

    `queued_id6s` lets the caller flag the specific harm rather than only the general case: a path
    carrying ANOTHER item's id6 while that item is still `queued` in this run is a queued item's input
    being rewritten by a different item's turn.
    """
    changed = tuple(p for p in changed_files if str(p).strip())
    allowed: list[str] = []
    out_of_scope: list[str] = []
    others = tuple(
        str(other) for other in queued_id6s if str(other) and str(other) != str(id6)
    )
    queued_siblings: list[str] = []
    for path in changed:
        if str(id6) in path:
            allowed.append(path)
            continue
        out_of_scope.append(path)
        if any(other in path for other in others):
            queued_siblings.append(path)
    return ReviewWriteScope(
        changed=changed,
        allowed=tuple(allowed),
        out_of_scope=tuple(out_of_scope),
        queued_siblings=tuple(queued_siblings),
    )


def describe_review_write_scope(scope: ReviewWriteScope, *, id6: str) -> str:
    """One operator-facing sentence for a review whose writes went beyond its own two files (E-10)."""
    if scope.clean:
        return (
            f"review {id6} wrote only its own plan and review record "
            f"({len(scope.allowed)} path(s))"
        )
    detail = (
        f"review {id6} also wrote {len(scope.out_of_scope)} path(s) outside its own plan and "
        f"review record: {', '.join(scope.out_of_scope)}"
    )
    if scope.queued_siblings:
        detail += (
            "; of those, these belong to items still QUEUED in this run: "
            + ", ".join(scope.queued_siblings)
        )
    return detail


# ---- lane -> main integration --------------------------------------------------------------------
# integpath-02 (`6sb3yu`): the integration REFUSAL and the DIRTY-OVERLAP CHECK were defined in BOTH
# runners and had already drifted, so the three behavior changes the `integpath` Set makes would each
# have had to be written twice. They now have ONE definition each, here.
#
# WHY THE COLLAPSE WAS SAFE, measured rather than judged. `dirty_tree_overlap`'s and
# `build_lane_outcome`'s executable ASTs were BYTE-IDENTICAL across the two runners (the whole diff
# was comment and docstring), and `integrate_lane_branch`'s 13 top-level statements matched
# statement-for-statement except ONE: the `--no-ff` merge subject's host label, `aw oc run` versus
# `aw agy run`. That single value is now the `host_label` PARAMETER below, and it has NO DEFAULT on
# purpose (see its docstring).
#
# THREE OF THE FOUR COLLABORATORS NEEDED NOTHING. The complete external-name set of the moved bodies
# is `_run_git`, `conflicted_paths`, `format_merge_conflict_reason` and `build_lane_outcome`. The
# first three were ALREADY in this module and already `is`-identical in both runners, so the shared
# bodies just call their own module-level names; injecting them would be cargo-culting the
# `run_checked` precedent, which exists only because THAT dependency is host-specific.
# `build_lane_outcome` was the fourth and MOVED here too (identical executable AST), because the
# alternative was an injection parameter whose only purpose would be to route around a duplicate.
#
# BUT `build_lane_outcome` CALLS `run_checked`, so it lands in exactly the intra-seam situation the
# module docstring describes for `git_head`/`git_status`/`git_common_dir`: `run_checked` is itself
# shared and gained a host-specific `env_builder`, so a naive lift raises `TypeError`. The same
# established remedy applies - `run_checked` is INJECTED as a keyword-only parameter and each runner
# binds its own wrapper - and `integrate_lane_branch` therefore threads it through to its one call.


def merge_write_set(repo: Path, branch: str) -> list[str] | None:
    """mergedirty-01 (`fujm0y`) E-02: the paths a merge of ``branch`` into HEAD would actually WRITE.

    Computed as the MERGE RESULT TREE diffed against HEAD: ``git merge-tree --write-tree HEAD
    <branch>`` writes the merged tree object, and ``git diff --name-only HEAD <tree>`` names exactly
    the paths that tree changes relative to HEAD. That is the set the working tree would be updated
    at, which is precisely the set a pre-merge dirty guard must ask about.

    RETURNS ``None`` WHEN THE ANSWER IS UNKNOWN, and that is a distinct third value rather than an
    empty list. ``git merge-tree`` exits non-zero for a CONFLICTING merge (rc 1), an unmergeable ref
    (rc 1), and a usage error such as an older git that lacks ``--write-tree`` (rc 129, measured).
    In every one of those cases the write set is UNKNOWN, and reporting `[]` would fabricate "no
    paths", which the guard would read as "clear" - the exact fail-open shape this plan exists to
    remove. `None` means "do not decide from me": the caller falls back to the lane's own
    `changed_files` and lets the merge itself, or the existing conflict classification, be the
    authority. A conflicting merge is a `merge-conflict` (terminal) and must NOT be reclassified as
    deferrable dirt (OQ-01).

    WHY NOT THE MERGE-BASE-TO-BOTH-TIPS UNION, which is what this plan originally prescribed and
    review DISPROVED (finding F-7). The union includes every path main advanced on since the lane
    base whether or not the merge writes it. MEASURED (git 2.43.0): base holds `a.txt`+`b.txt`, the
    lane changes only `a.txt`, main advances `b.txt` AND is left dirty on `b.txt`. The union is
    `['a.txt', 'b.txt']`, so a guard fed the union REFUSES on `b.txt` - yet the real `git merge
    --no-ff` exits 0 ("Merge made by the 'ort' strategy"), touches only `a.txt`, and the co-worker's
    dirty `b.txt` survives intact. So the union refuses an integration that succeeds safely. The
    merge-result diff returns `[]` on that same fixture and `['renamed.txt']` on the rename fixture
    the defect was reproduced with, which is exactly the discrimination required. Do NOT "simplify"
    this back to a union: it reads as more thorough and is measurably wrong.

    ``--no-renames`` IS DELIBERATE ON THE DIFF. With rename detection on, a lane that renames ``a``
    -> ``b`` reports only ``b``, yet the merge must still DELETE ``a`` in main, so dirt on ``a``
    would pass the guard and git would then refuse to start the merge (measured: write set
    `['b.txt']` with renames, `['a.txt', 'b.txt']` without, and the real merge fails on ``a.txt``).
    The guard needs every path the working tree is written at, so rename detection - which exists to
    make diffs READABLE - must be off here.

    ``-z`` IS ALSO DELIBERATE. Git QUOTES unusual path names in the default `--name-only` output
    (measured: `"w\\303\\251ird name.txt"`), which would not string-compare against the porcelain
    paths this set is intersected with. NUL-delimited output is emitted raw, so the two sides agree.
    """
    rc, out, _err = _run_git(repo, ["merge-tree", "--write-tree", "HEAD", branch])
    if rc != 0:
        # UNKNOWN, not empty. See the docstring: conflict, unmergeable ref and unsupported flag all
        # land here, and none of them licenses claiming the merge writes nothing.
        return None
    lines = out.strip().splitlines()
    if not lines or not lines[0].strip():
        return None
    tree = lines[0].strip()
    rc2, names, _err2 = _run_git(
        repo, ["diff", "--name-only", "--no-renames", "-z", "HEAD", tree]
    )
    if rc2 != 0:
        return None
    return sorted({p for p in names.split("\0") if p.strip()})


def dirty_tree_overlap(repo: Path, changed_files: Sequence[str]) -> list[str]:
    """driverfin-03 (7kbtkw) E-01: report the MAIN tree's un-owned dirty paths that overlap an
    INCOMING CHANGE.

    Inspect ``git status --short`` in the MAIN repo (working tree + index) and return the sorted set
    of paths that are BOTH dirty in main AND part of the incoming change. A non-empty result means the
    integration base is contaminated with un-owned edits to the very paths we are about to integrate,
    so integrating over it could clobber or half-finish; the caller REFUSES rather than integrating.

    ``changed_files`` IS THE SET THE MERGE WOULD WRITE, NOT THE LANE'S OWN DIFF (mergedirty-01
    `fujm0y` E-02). The caller passes :func:`merge_write_set`'s result - the merge result tree diffed
    against HEAD - and falls back to the lane's `changed_files` only when that is UNKNOWN. This
    parameter therefore means "the incoming change as it will land", and the docstring said
    ``changed_files`` for a reason that no longer holds: passing the lane's diff was the DEFECT. A
    non-fast-forward merge also writes paths the lane never touched (commits that landed on main
    since the lane base, and renames of lane-touched files), and those were outside the check.
    REPRODUCED (git 2.43.0): the lane changed only `a.txt`, main renamed `a.txt` to `renamed.txt` and
    was dirty there, `dirty_tree_overlap(repo, ["a.txt"])` returned `[]` (guard says clear), and
    `git merge --no-ff` then failed on `renamed.txt`.

    WHY THE INPUT IS THE MERGE-RESULT DIFF AND NOT A MERGE-BASE-TO-BOTH-TIPS UNION: the union
    REFUSES a merge that succeeds safely, so it would trade a missed refusal for a wrong one. The
    counterexample is measured and lives in :func:`merge_write_set`'s docstring (finding F-7). Read it
    before changing the input set, because the union reads as the more thorough choice and is not.

    The porcelain short format is `XY<space>path` (renames use `orig -> dest`); we take the last
    path token so both the origin and destination of a rename are considered dirty.
    """
    incoming = {p for p in changed_files if p.strip()}
    if not incoming:
        return []
    _rc, out, _err = _run_git(repo, ["status", "--short", "--untracked-files=all"])
    dirty: set[str] = set()
    for line in out.splitlines():
        if not line.strip():
            continue
        # Strip the two status columns and the following space: entries are `XY path` (min 3 chars).
        entry = line[3:] if len(line) > 3 else line.strip()
        # A rename/copy renders as `orig -> dest`; treat both endpoints as dirty.
        if " -> " in entry:
            orig, dest = entry.split(" -> ", 1)
            dirty.add(orig.strip())
            dirty.add(dest.strip())
        else:
            dirty.add(entry.strip())
    return sorted(incoming & dirty)


def build_lane_outcome(
    repo: Path, handle: Any, id6: str, *, run_checked: Callable[..., str]
) -> Any:
    """Build a single `orchestrate_isolation.LaneOutcome` for a finalized lane branch.

    base_commit = the worktree base (frozen at allocate); head_commit = the lane branch HEAD after the
    agent + finalize commits; changed_files + diff come from `git diff base..head` on the lane branch.
    per_lane_validation_passed=True (the driver only builds this after its own verification+finalize
    passed).

    ``run_checked`` is INJECTED for the reason the module docstring gives for
    `git_head`/`git_status`/`git_common_dir`: the shared `run_checked` takes a host-specific
    `env_builder`, so this body cannot resolve a module-level `run_checked` here. Each runner binds
    its own wrapper. Do NOT "simplify" these three calls onto `_run_git`: that would stop them raising
    `DriverError` on a failed `git rev-parse`/`git diff` and silently build a LaneOutcome from empty
    strings, which the integration gate would then revalidate as an empty change.
    """
    from agent_workflows import orchestrate_isolation

    base = handle.base_commit
    head = run_checked(["git", "rev-parse", handle.branch], cwd=repo)
    name_out = run_checked(
        ["git", "diff", "--name-only", f"{base}..{handle.branch}"], cwd=repo
    )
    changed = tuple(p for p in name_out.splitlines() if p.strip())
    diff = run_checked(["git", "diff", f"{base}..{handle.branch}"], cwd=repo)
    return orchestrate_isolation.LaneOutcome(
        lane_id=id6,
        actor_role="driver",
        base_commit=base,
        head_commit=head,
        worktree_path=str(handle.path),
        changed_files=changed,
        diff=diff,
        per_lane_validation_passed=True,
        status=orchestrate_isolation.STATUS_COMPLETED,
    )


#: dirtygates Order 05 (`ajxr5d`) E-03, OQ-01 (resolved by the maintainer: WIDEN the shared function
#: rather than fork a second merge path). THE ACTION KIND vocabulary `integrate_lane_branch` accepts.
#:
#: WHY IT IS A DECLARED VOCABULARY AND NOT A BOOLEAN. A `skip_revalidation=True` flag would state the
#: MECHANISM and hide the REASON, and the reason is the whole justification: a review turn produces no
#: code and therefore has nothing to revalidate, whereas an execute turn does and must be revalidated.
#: Naming the action makes the gate's own docstring able to say WHY it skipped, and makes a future
#: third action have to declare itself rather than inherit whichever branch it happens to fall into.
INTEGRATION_ACTION_EXECUTE = "execute"
INTEGRATION_ACTION_REVIEW = "review"
INTEGRATION_ACTION_KINDS: tuple[str, ...] = (
    INTEGRATION_ACTION_EXECUTE,
    INTEGRATION_ACTION_REVIEW,
)


def integrate_lane_branch(
    repo: Path,
    handle: Any,
    id6: str,
    validation_runner: Any,
    *,
    host_label: str,
    run_checked: Callable[..., str],
    action_kind: str,
) -> tuple[bool, str, str]:
    """Integrate a verified lane branch back to main behind the REUSED integration gate, failing
    closed on a contaminated base or a non-passing gate result.

    ``action_kind`` SELECTS WHETHER STEP 1's REVALIDATION GATE RUNS, and it is stated by the caller.
    ``"execute"`` runs the merge-and-revalidate gate exactly as before. ``"review"`` SKIPS IT, and the
    skip is TRUE rather than convenient: a review turn's whole output is the plan under review plus its
    review record (measured on commit ``a9510164``), so there is no code to revalidate and no test
    result the gate could compute. THE SKIP IS EXPLICIT AND NEVER SYNTHESIZED (plan `ajxr5d` OQ-01's
    load-bearing line): this function does NOT construct a passing `IntegrationGateResult`, does not
    hand a "validation passed" value to the gate, and does not call `validation_runner` for a review.
    Passing a fake attestation into a gate is the same family of defect as hand-writing a
    `- Readiness:` field, and it is forbidden here for the same reason. Skipping a gate for an action
    that produces nothing for it to check is simply a true statement; forging its verdict is not.

    ``action_kind`` HAS NO DEFAULT DELIBERATELY, for the reason ``host_label`` has none, only stronger:
    a default would let a new caller silently skip revalidation (if the default were ``"review"``) or
    silently revalidate an action with nothing to revalidate (if it were ``"execute"``), and either
    mis-binding is invisible until it matters. It is REFUSED rather than coerced when unrecognized, so
    a typo cannot fall through to whichever branch happens to be first. The per-host WRAPPERS bind it
    as a literal exactly as they bind ``host_label``, so their signatures do not change and
    `tests/test_runner_shared.py::LaneIntegrationExtractionTests
    ::test_each_wrapper_keeps_the_ORIGINAL_signature` stays green untouched; the REVIEW path calls the
    review-bound wrapper rather than reaching around it.

    0. driverfin-03 (7kbtkw) E-01 DIRTY-TREE GUARD: BEFORE invoking the gate, assert the MAIN tree has
       no un-owned dirty paths overlapping the incoming lane's `changed_files`. If it does, REFUSE:
       do not run the gate, do not touch main, return kind ``"integration-blocked"`` so the caller
       preserves the verified branch/worktree.
    1. Build a LaneOutcome and call `orchestrate_isolation.execute_merge_and_revalidate_gate`
       (DETECTS conflict/stale-base/lane-failure + REVALIDATES the combined diff). Conflict DETECTION
       is the gate's job; conflict RESOLUTION is a human/serial ordering.
    2. On `IntegrationGateResult.passed`, the driver performs the actual git integration onto main:
       `git merge --ff-only` (the clean serial case), falling back to a controlled `--no-ff` merge if
       main advanced; a real git conflict aborts the merge (leaving main clean, no markers/partial
       merge) and is treated as a non-passing integration.
    3. driverfin-03 (7kbtkw) E-02: on a NON-passing gate result (or a real git conflict) leave main
       UNTOUCHED, return kind ``"merge-conflict"`` with the failing paths/reason, and do NOT fake
       executed; a human/serial ordering owns resolution via the preserved lane branch.
    4. dirtygates-02 (`metc8b`) E-02: a merge git REFUSED TO START because main holds uncommitted local
       changes to a file the merge would overwrite is NOT a content conflict, and is returned as
       ``"integration-blocked"`` (the TRANSIENT arm the deferral ladder may re-attempt) carrying git's
       own message. The two failure classes are told apart by :func:`merge_in_progress` - a structural
       `MERGE_HEAD` test - and NOT by matching git's localizable English. No `git merge --abort` is
       issued for this class, because no merge was ever started.

       NOTE THIS IS REACHABLE DESPITE STEP 0's GUARD, which is why the arm is needed and not dead
       code. `dirty_tree_overlap` intersects main's dirt with the lane's `changed_files`, and that set
       comes from `git diff --name-only`, which applies RENAME DETECTION: a lane that renamed
       ``a`` -> ``b`` reports only ``b``, yet the merge must still DELETE ``a`` in main, so locally
       modified ``a`` passes step 0 and git then refuses. Measured, and it is the shape of every plan
       moving `pending/` -> `executed/`. (`fujm0y` is approved to widen step 0's input; this arm is
       correct either way, because git remains the authority on its own preconditions.)

    Returns ``(integrated, reason, kind)`` where ``kind`` is one of ``"integrated"``,
    ``"integration-blocked"``, or ``"merge-conflict"``. ``integrated=True`` (kind ``"integrated"``)
    means the lane's commits are on main.

    ``host_label`` is the driver's own operator-facing name (``"aw oc run"`` / ``"aw agy run"``) and
    is the ONE value that differed between the two runners' copies. It has NO DEFAULT DELIBERATELY:
    the label lands in a merge commit subject on MAIN, so a default would let a new caller silently
    attribute its integrations to the wrong driver in git history, and that misattribution is
    invisible until someone audits the log. The subject TEMPLATE stays here, shared, so the subject's
    shape cannot drift per host again. ``run_checked`` is injected for `build_lane_outcome`; see its
    docstring.
    """
    from agent_workflows import orchestrate_isolation

    if action_kind not in INTEGRATION_ACTION_KINDS:
        # FAIL CLOSED on an unrecognized kind rather than defaulting to either branch. Defaulting to
        # `execute` would revalidate a review (a gate call with nothing to check), and defaulting to
        # `review` would skip revalidation for an execute turn, which is the one thing this parameter
        # exists to keep impossible. A typo must be a refusal, not a silent choice.
        raise DriverError(
            "integrate_lane_branch: unrecognized action_kind {0!r}; expected one of {1}".format(
                action_kind, ", ".join(repr(k) for k in INTEGRATION_ACTION_KINDS)
            )
        )

    lane = build_lane_outcome(repo, handle, id6, run_checked=run_checked)

    # E-01: fail closed on a contaminated integration base BEFORE running the gate.
    #
    # mergedirty-01 (`fujm0y`) E-02: the guard is asked about THE PATHS THE MERGE WOULD WRITE, not the
    # paths the LANE changed. Those two sets differ whenever main advanced or a rename is involved,
    # and the difference was the defect: with the lane's own diff, dirt on a path the merge writes but
    # the lane never touched passed the guard and git then refused the merge, so a deferrable
    # condition was reported as a terminal `merge-conflict`. `merge_write_set` returns None when it
    # cannot know (a conflicting merge, or a git without `--write-tree`), and then the lane's
    # `changed_files` remains the input: that keeps the previous behavior on the unknown path instead
    # of silently checking NOTHING, and a real conflict stays the merge's own to classify.
    predicted = merge_write_set(repo, handle.branch)
    incoming = lane.changed_files if predicted is None else predicted
    overlap = dirty_tree_overlap(repo, incoming)
    if overlap:
        return (
            False,
            (
                "integration refused: main tree has un-owned dirty paths overlapping the incoming "
                f"change: {', '.join(overlap)}"
            ),
            "integration-blocked",
        )

    # dirtygates Order 05 (`ajxr5d`) E-03: THE ONE STEP A REVIEW SKIPS, and it is skipped by NOT
    # RUNNING, never by fabricating a verdict. `result` stays None for a review and the `not
    # result.passed` refusal below is therefore not consulted; no `IntegrationGateResult` is
    # constructed, `validation_runner` is never called, and nothing is recorded as having validated.
    # Steps 0 (the dirty-overlap guard above) and 2-4 (the real merge below) are FULLY SHARED, which is
    # the reason OQ-01 chose to widen this function rather than fork a review-only merge path: those
    # steps carry the ff-only-then-no-ff sequence, the capture-conflicted-paths-BEFORE-abort ordering,
    # and the `host_label` merge subject, all of which a second implementation would have to duplicate.
    if action_kind == INTEGRATION_ACTION_EXECUTE:
        result = orchestrate_isolation.execute_merge_and_revalidate_gate(
            integration_base_commit=handle.base_commit,
            lane_outcomes=[lane],
            merge_order=[id6],
            full_validation_runner=validation_runner,
        )
        if not result.passed:
            # E-02: a non-passing gate result is diff-based (no partial merge to abort). Record the
            # gate's failing findings + paths so a human/serial ordering can resolve the preserved lane
            # branch.
            failing = "; ".join(
                f"{f.check_name}[{f.lane_id}]: {f.message}" for f in result.findings
            )
            detail = failing or result.message
            return (
                False,
                f"integration gate did not pass ({result.status}): {detail}",
                "merge-conflict",
            )

    # Gate passed (conflict-free, revalidated), or - for a review - was correctly not run. Perform the
    # real integration onto main.
    # NOTE the ff-only attempt's output is DELIBERATELY discarded: its failure is the EXPECTED
    # "main advanced" case, not an error, so it must never reach the operator-facing reason (mergemsg).
    rc, _out, _err = _run_git(repo, ["merge", "--ff-only", handle.branch])
    if rc == 0:
        return True, "fast-forward integrated to main", "integrated"
    # main advanced past the lane base: attempt a controlled non-ff merge of ONLY this branch.
    rc, out2, err2 = _run_git(
        repo,
        [
            "merge",
            "--no-ff",
            "--no-edit",
            "-m",
            f"integrate({host_label}): merge verified lane {id6} to main",
            handle.branch,
        ],
    )
    if rc == 0:
        return True, "controlled non-ff merge integrated to main", "integrated"
    # The merge FAILED. Which of the two ways it can fail decides the outcome kind, and that is
    # decided STRUCTURALLY (dirtygates-02 `metc8b` E-02).
    #
    # WHY THIS SPLIT EXISTS, measured rather than reasoned. Lanes `bzz5e6` and `f6idxs` (2026-09-13)
    # each finished their work, passed their gate, finalized on their lane branch, and were then
    # recorded `merge-conflict` carrying git's own "Your local changes to the following files would be
    # overwritten by merge" text. That is NOT a content conflict: git never started the merge, left no
    # conflicted path, and the condition clears itself the moment the un-owned edit is committed. It
    # belongs on `integration-blocked`, the TRANSIENT arm.
    #
    # AND THE ARM IS LOAD-BEARING, so do NOT "simplify" the two kinds back together.
    # `classify_integration_refusal` defers ONLY `integration-blocked`; `merge-conflict` is terminal on
    # its FIRST attempt, deliberately, because repetition cannot resolve a real conflict. So a
    # local-changes refusal recorded as `merge-conflict` is excluded from the deferral ladder and its
    # verified work is lost for the rest of the run - which is exactly what happened to those two
    # lanes. Conversely, routing a REAL conflict onto `integration-blocked` would spin the ladder
    # against a failure repetition cannot fix.
    #
    # THE DISCRIMINATOR IS `MERGE_HEAD`, NOT GIT'S ENGLISH (see `merge_in_progress`): a content
    # conflict STARTS the merge (`MERGE_HEAD` present, `U` entries listed), while a local-changes
    # refusal never starts it (`MERGE_HEAD` absent, no `U` entries). Message text is localizable and
    # version-dependent, so a text test would misclassify silently outside the author's locale.
    #
    # DO NOT NEST THIS UNDER A "MAIN ADVANCED" ASSUMPTION. Measured: the refusal is reached by TWO
    # routes. With main advanced, the `--ff-only` attempt fails as diverged and the `--no-ff` attempt
    # refuses (rc=2). With main NOT advanced, `--ff-only` ITSELF refuses with the same text (rc=1) and
    # execution falls through to the `--no-ff` attempt, which refuses identically. Keying only on the
    # structural test classifies both correctly; keying on "main advanced" would miss the second.
    if merge_in_progress(repo):
        # A real merge conflict: abort so main stays clean (no markers/partial merge); a human/serial
        # ordering resolves it via the preserved lane branch (E-02).
        # Capture the conflicted paths BEFORE aborting - the abort clears the index state they live in.
        conflicted = conflicted_paths(repo)
        _run_git(repo, ["merge", "--abort"])
        return (
            False,
            format_merge_conflict_reason(
                repo, merge_stdout=out2, merge_stderr=err2, paths=conflicted
            ),
            "merge-conflict",
        )

    # Git REFUSED TO START the merge, so there is nothing to abort and NO abort is issued: with no
    # `MERGE_HEAD`, `git merge --abort` exits 128 ("fatal: There is no merge to abort"). Main is
    # already exactly as it was found - HEAD unmoved and the uncommitted edit intact - because git
    # checks this precondition BEFORE touching the working tree, which is what makes attempting the
    # merge safe. The lane branch and worktree are preserved by the caller, unchanged by this arm.
    return (
        False,
        format_local_changes_refusal_reason(merge_stdout=out2, merge_stderr=err2),
        "integration-blocked",
    )


# ==================================================================================================
# integpath-03 (`51vw4y`): THE INTEGRATION DEFERRAL LADDER
# ==================================================================================================
#
# THE DEFECT, MEASURED RATHER THAN REASONED. `integrate_lane_branch` above REFUSES on a contaminated
# base and that refusal is CORRECT and unchanged by this section. What was wrong is what happened
# NEXT: the caller wrote `integration-blocked`, which sits in both runners' `TERMINAL_STATES`, so the
# item was never re-attempted for the rest of the run. One transient condition, permanent loss.
#
# Run `run-20260905T050043Z-639569` (34 items, 7h40m, $183.95, of which $88.23 went on the four
# refused lanes): four items finished their work, passed their gates, finalized on their lane
# branches, and then failed to integrate on dirty-path overlap (`76gsmv` 08:06:32, `eyh1fu` 08:51:26,
# `txc9l1` 10:48:33, `uyeko5` 11:47:04). Three more (`6ypimw`, `wpomxa`, `5slbpi`) cascaded to
# `dependency-blocked` because their prerequisites never reached `executed`. Seven of 34 items lost.
# All four merged clean against main afterwards: the work was never in conflict, it was refused
# because of WHEN it was attempted. A lane refused at 08:06 would have integrated at 08:40 when the
# next item finished. NOTHING WAITED, which is the whole defect.
#
# WHY REPETITION IS A LEGITIMATE STRATEGY HERE, WHICH IS NOT GENERALLY TRUE. The refusal cause is
# another writer's UNCOMMITTED file in a shared checkout, so it clears on its own. That is why this
# ladder gets its own budget and must never borrow `run_recovery.DEFAULT_RETRY_LIMIT`, whose own
# rationale is that "a retry cannot turn failure into success by mere repetition" - true of a paid
# correction turn, false of an integration re-attempt costing one `git status` and one `git
# merge-tree`.
#
# ONLY THE DIRTY-OVERLAP ARM DEFERS, AND THAT SCOPING IS LOAD-BEARING. `integrate_lane_branch`
# returns THREE kinds. `"merge-conflict"` means the reused gate returned a non-passing result (real
# conflict, stale base, combined-red, scope), which repetition does NOT fix; deferring it would spin
# the ladder against a genuine failure and burn the budget for nothing, and every positive-arm test
# would still pass. :func:`classify_integration_refusal` is the single place that decision is made.
#
# RE-VERIFICATION IS MANDATORY ON EVERY ATTEMPT and is not this section's job to skip: a lane
# verified against yesterday's main is not verified against today's, so each re-attempt calls
# `integrate_lane_branch` again, which routes through
# `orchestrate_isolation.execute_merge_and_revalidate_gate`. There is deliberately no fast path that
# takes a clean `merge-tree` as sufficient.

#: The NON-TERMINAL status a deferred integration carries. Deliberately NOT in either runner's
#: `TERMINAL_STATES`: that absence is the single fact that makes a re-attempt possible, keeps
#: `cascade_dependency_blocked` from killing dependents, and keeps the orchestrator waiting.
INTEGRATION_DEFERRED_STATUS = "integration-deferred"

#: The terminal status a deferred integration ends at when the ladder is exhausted. Today's outcome,
#: reached LAST instead of FIRST.
INTEGRATION_BLOCKED_STATUS = "integration-blocked"

#: The refusal kind that is TRANSIENT and therefore deferrable (un-owned dirty overlap in main).
INTEGRATION_REFUSAL_TRANSIENT = "integration-blocked"

#: The refusal kind that is NOT transient and must stay terminal on its first attempt.
INTEGRATION_REFUSAL_CONFLICT = "merge-conflict"

#: `--integration-retry-limit`'s default. TEN, not `DEFAULT_RETRY_LIMIT`'s two, because the two count
#: different things (see the section header). Ten cheap re-attempts is the maintainer-approved value.
DEFAULT_INTEGRATION_RETRY_LIMIT = 10

#: `--on-integration-blocked`'s vocabulary. `block` reproduces the pre-ladder behavior EXACTLY, which
#: is what makes this change safe to adopt: an operator who distrusts the ladder can pin it off.
ON_INTEGRATION_BLOCKED_DEFER = "defer"
ON_INTEGRATION_BLOCKED_POLL = "poll"
ON_INTEGRATION_BLOCKED_ASK = "ask"
ON_INTEGRATION_BLOCKED_BLOCK = "block"
ON_INTEGRATION_BLOCKED_CHOICES = (
    ON_INTEGRATION_BLOCKED_DEFER,
    ON_INTEGRATION_BLOCKED_POLL,
    ON_INTEGRATION_BLOCKED_ASK,
    ON_INTEGRATION_BLOCKED_BLOCK,
)

#: Rung 2's poll-count bound: how many times the runner re-checks main when NOTHING else is
#: dispatchable. Paired with the staleness bound below; NEITHER is sufficient alone.
DEFAULT_INTEGRATION_POLL_LIMIT = 10

#: Rung 2's per-poll sleep, seconds.
DEFAULT_INTEGRATION_POLL_INTERVAL = 30.0

#: Rung 2's STALENESS bound, seconds (about one hour). Ten polls at 30s is five minutes whether main
#: is alive or has been idle since yesterday, so a poll count alone is the WRONG SOLE BOUND: it makes
#: the wait arbitrary. Measuring main's last activity is what makes it EVIDENCE-BASED - if nothing has
#: moved in main for an hour, nobody is about to commit and polling is superstition.
DEFAULT_INTEGRATION_STALENESS_LIMIT = 3600.0

#: Which bound ended a rung-2 poll, reported so "polled 10x over 5m; main last active 3m ago" and
#: "gave up immediately, main idle 4h" are distinguishable facts. The second tells the operator the
#: dirt is ABANDONED and needs a human, which is a different action from the first.
POLL_BOUND_COUNT = "poll-count-exhausted"
POLL_BOUND_STALE = "main-inactive"
POLL_BOUND_CLEARED = "dirt-cleared"


def classify_integration_refusal(integ_kind: str) -> bool:
    """Is this refusal the TRANSIENT one the deferral ladder may re-attempt?

    ONE definition, so the two hosts cannot disagree about which arm defers. `True` only for the
    dirty-overlap refusal; `False` for `merge-conflict` and for anything unrecognized, which is the
    fail-closed direction (an unknown kind keeps today's terminal path rather than acquiring a retry
    loop nobody reasoned about).
    """

    return integ_kind == INTEGRATION_REFUSAL_TRANSIENT


def resolve_integration_retry_limit(cli_value: Any) -> int:
    """`--integration-retry-limit`'s effective value: CLI over the default of 10.

    DELIBERATELY NOT CLAMPED TO SPEC 2.1's 0..10 RANGE, which bounds the CORRECTION budget
    specifically (`resolve_retry_budget` reaches that bound through
    `run_recovery.validate_retry_budget`). Conflating the two is the category error spec 2.1's new
    Rules bullet and backlog `5wdoze` both name explicitly. A NEGATIVE value is refused, because a
    negative count of re-attempts is not a policy, it is a typo.
    """

    if cli_value is None:
        return DEFAULT_INTEGRATION_RETRY_LIMIT
    try:
        value = int(cli_value)
    except (TypeError, ValueError) as exc:
        raise RunFlagRefusal(
            f"--integration-retry-limit: {cli_value!r} is not an integer"
        ) from exc
    if value < 0:
        raise RunFlagRefusal(
            f"--integration-retry-limit: {value} is negative; it counts integration "
            "re-attempts, so the minimum is 0 (never re-attempt)"
        )
    return value


def resolve_on_integration_blocked(cli_value: Any) -> str:
    """`--on-integration-blocked`'s effective value, validated against the closed vocabulary."""

    if cli_value is None:
        return ON_INTEGRATION_BLOCKED_DEFER
    value = str(cli_value).strip().lower()
    if value not in ON_INTEGRATION_BLOCKED_CHOICES:
        raise RunFlagRefusal(
            f"--on-integration-blocked: {cli_value!r} is not one of "
            f"{list(ON_INTEGRATION_BLOCKED_CHOICES)}"
        )
    return value


class IntegrationDeferralDecision(NamedTuple):
    """What to do with an integration that was just REFUSED, and why.

    `status` is the status to write: :data:`INTEGRATION_DEFERRED_STATUS` (non-terminal, re-attempt
    later) or :data:`INTEGRATION_BLOCKED_STATUS` / `merge-conflict` (terminal, today's behavior).
    `deferred` is the same fact as a bool for a caller that only branches. `attempts_used` is the
    running count AFTER this refusal, and `limit` the budget it is measured against, so a report can
    say "3 of 10" rather than merely "deferred".
    """

    status: str
    deferred: bool
    reason: str
    attempts_used: int
    limit: int


def decide_integration_deferral(
    *,
    integ_kind: str,
    attempts_used: int,
    limit: int,
    policy: str = ON_INTEGRATION_BLOCKED_DEFER,
) -> IntegrationDeferralDecision:
    """RUNG 1's decision: does this refusal DEFER, or is it terminal?

    THE FOUR REASONS A REFUSAL STAYS TERMINAL, each deliberate:

    * the kind is NOT the transient dirty-overlap one (`merge-conflict` and anything unrecognized);
    * `--on-integration-blocked=block`, the operator pinning today's behavior;
    * the budget is exhausted, so a permanently dirty path cannot spin the loop forever; or
    * the budget is zero, which is `block` spelled as a count.

    `attempts_used` is the count INCLUDING the attempt that just failed, so the first refusal arrives
    as 1. PURE: it writes no state, touches no file, and consults no clock, which is what lets every
    rung transition be pinned by a unit test with no live run.
    """

    if not classify_integration_refusal(integ_kind):
        return IntegrationDeferralDecision(
            status=INTEGRATION_REFUSAL_CONFLICT,
            deferred=False,
            reason=(
                f"integration refusal kind {integ_kind!r} is not the transient dirty-overlap "
                "condition; repetition cannot fix a conflict, stale base, combined-red "
                "revalidation, or scope violation, so it is terminal on its first attempt"
            ),
            attempts_used=attempts_used,
            limit=limit,
        )
    if policy == ON_INTEGRATION_BLOCKED_BLOCK:
        return IntegrationDeferralDecision(
            status=INTEGRATION_BLOCKED_STATUS,
            deferred=False,
            reason=(
                "--on-integration-blocked=block: the operator pinned the pre-ladder behavior, so "
                "the first refusal is terminal and the lane is preserved"
            ),
            attempts_used=attempts_used,
            limit=limit,
        )
    if attempts_used > limit:
        return IntegrationDeferralDecision(
            status=INTEGRATION_BLOCKED_STATUS,
            deferred=False,
            reason=(
                f"integration re-attempt budget exhausted ({attempts_used - 1} re-attempt(s) after "
                f"the first, limit {limit}); the overlapping dirty path never cleared, so the lane "
                "is preserved and a human owns it"
            ),
            attempts_used=attempts_used,
            limit=limit,
        )
    return IntegrationDeferralDecision(
        status=INTEGRATION_DEFERRED_STATUS,
        deferred=True,
        reason=(
            f"integration DEFERRED (attempt {attempts_used} of {limit + 1}): main holds un-owned "
            "dirty paths overlapping this change, which is transient by nature, so the lane is "
            "preserved and integration is re-attempted through the full revalidate gate once other "
            "work advances"
        ),
        attempts_used=attempts_used,
        limit=limit,
    )


def deferred_integration_items(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Every queue item currently sitting in the non-terminal deferred state, in queue order."""

    return [
        item
        for item in (state.get("queue") or [])
        if isinstance(item, dict) and item.get("status") == INTEGRATION_DEFERRED_STATUS
    ]


def main_last_activity_age(repo: Path, *, now: float | None = None) -> float | None:
    """How long ago ANYTHING last moved in main, in seconds, or `None` when unmeasurable.

    THE NEWER of two signals, because either alone answers the wrong question:

    * main's HEAD COMMIT TIME - somebody landed work; and
    * the most recent MTIME among main's dirty (or untracked) files - somebody is editing right now
      and has not committed yet, which is precisely the state that caused the refusal.

    A run that consulted only HEAD would call an actively-edited tree idle and give up on a lane that
    was about to be integrable; one that consulted only mtimes would call a freshly-committed tree
    idle. So rung 2's staleness bound needs the NEWER, and this returns exactly that.

    WALL-CLOCK, NOT LOOP ITERATIONS (OQ-01). The bound distinguishes "someone is actively working in
    main and will commit shortly" from "this dirt was abandoned yesterday", which is a statement about
    elapsed real time. An iteration count would also couple the wait to QUEUE SIZE, so a run with one
    deferred item and nothing else to do would give up faster than an identical run with more items,
    which is backwards.

    Returns `None` rather than 0.0 or infinity when neither signal can be read, so a caller can tell
    "no evidence" from "very recent" and fail toward NOT polling on a repository it cannot observe.
    """

    current = time.time() if now is None else now
    newest: float | None = None

    rc, out, _err = _run_git(repo, ["log", "-1", "--format=%ct"])
    if rc == 0 and out.strip():
        try:
            newest = float(out.strip().splitlines()[0])
        except (TypeError, ValueError):
            newest = None

    rc, out, _err = _run_git(repo, ["status", "--short", "--untracked-files=all"])
    if rc == 0:
        for line in out.splitlines():
            if not line.strip():
                continue
            entry = line[3:] if len(line) > 3 else line.strip()
            if " -> " in entry:
                entry = entry.split(" -> ", 1)[1]
            candidate = repo / entry.strip()
            try:
                mtime = candidate.stat().st_mtime
            except OSError:
                continue
            if newest is None or mtime > newest:
                newest = mtime

    if newest is None:
        return None
    return max(0.0, current - newest)


class PollOutcome(NamedTuple):
    """The result of one rung-2 poll episode, shaped so a report can be HONEST about it.

    `bound` is which of the three conditions ended it (:data:`POLL_BOUND_CLEARED`,
    :data:`POLL_BOUND_COUNT`, :data:`POLL_BOUND_STALE`), `polls` how many checks were made, and
    `last_activity_age` main's measured idle time at the end (`None` when unmeasurable). `detail` is
    one operator-facing sentence naming both the bound and the age, because "polled 10x over 5m; main
    last active 3m ago" and "gave up immediately, main idle 4h" demand different human responses.
    """

    cleared: bool
    bound: str
    polls: int
    last_activity_age: float | None
    detail: str


def poll_for_integration_window(
    repo: Path,
    changed_files: Sequence[str],
    *,
    poll_limit: int = DEFAULT_INTEGRATION_POLL_LIMIT,
    interval: float = DEFAULT_INTEGRATION_POLL_INTERVAL,
    staleness_limit: float = DEFAULT_INTEGRATION_STALENESS_LIMIT,
    sleep: Callable[[float], None] | None = None,
    overlap: Callable[[Path, Sequence[str]], list[str]] | None = None,
    activity_age: Callable[[Path], float | None] | None = None,
) -> PollOutcome:
    """RUNG 2: wait for the overlapping dirt to clear, bounded TWICE, when nothing else can run.

    TWO INDEPENDENT BOUNDS, BOTH REQUIRED, and the second is the one carrying the design's argument:

    (i) ``poll_limit`` - a maximum number of checks; and
    (ii) ``staleness_limit`` - stop when main's last activity (see :func:`main_last_activity_age`) is
         older than this. Ten polls at 30s is five minutes whether main is alive or has been idle
         since yesterday, so bound (i) alone makes the wait ARBITRARY. Bound (ii) is what makes it
         evidence-based, and it is checked BEFORE the first sleep so an abandoned tree costs no wait
         at all.

    The staleness bound also fires when the age is UNMEASURABLE (`None`), which is the fail-closed
    direction: a repository whose activity cannot be observed is not one to sit and wait on.

    `sleep`/`overlap`/`activity_age` are injectable so a test controls time and dirt instead of
    sleeping for real. The defaults are the shared implementations, so there is no second overlap
    check and no second clock.
    """

    _sleep = time.sleep if sleep is None else sleep
    _overlap = dirty_tree_overlap if overlap is None else overlap
    _age = main_last_activity_age if activity_age is None else activity_age

    polls = 0
    age = _age(repo)
    while True:
        if not _overlap(repo, changed_files):
            return PollOutcome(
                cleared=True,
                bound=POLL_BOUND_CLEARED,
                polls=polls,
                last_activity_age=age,
                detail=(
                    f"the overlapping dirty path cleared after {polls} poll(s); integration is "
                    "re-attempted through the full revalidate gate"
                ),
            )
        age = _age(repo)
        if age is None or age > staleness_limit:
            described = "unmeasurable" if age is None else f"{int(age)}s ago"
            return PollOutcome(
                cleared=False,
                bound=POLL_BOUND_STALE,
                polls=polls,
                last_activity_age=age,
                detail=(
                    f"stopped polling after {polls} poll(s): main was last active {described} "
                    f"(staleness bound {int(staleness_limit)}s), so nobody is about to commit and "
                    "the overlapping dirt looks ABANDONED; it needs a human, not more waiting"
                ),
            )
        if polls >= poll_limit:
            return PollOutcome(
                cleared=False,
                bound=POLL_BOUND_COUNT,
                polls=polls,
                last_activity_age=age,
                detail=(
                    f"stopped polling after {polls} poll(s) (poll bound {poll_limit}); main was "
                    f"last active {int(age)}s ago, so it IS still active and the dirt may yet "
                    "clear, but this run has waited its budget"
                ),
            )
        polls += 1
        _sleep(interval)


def record_integration_refusal(
    *,
    run_dir: Path,
    state: MutableMapping[str, Any],
    item: MutableMapping[str, Any],
    attempt: MutableMapping[str, Any],
    integ_kind: str,
    integ_reason: str,
    branch: str | None,
    save_state: Callable[..., Any],
    append_jsonl: Callable[..., Any],
) -> IntegrationDeferralDecision:
    """Record ONE refused integration and return the ladder's decision. Shared by both hosts.

    THIS IS RUNG 1's WRITE SITE, and it is shared for the reason integpath-02 collapsed its three
    neighbours: the two hosts' copies of this block had ALREADY drifted once, so a ladder written into
    each would be written twice and fixed once. Each host keeps only its own printing.

    WHAT IT DOES, in order: count this attempt (durably, so a resume cannot lose the count and restart
    the budget), ask :func:`decide_integration_deferral` for the verdict, write the resulting status,
    and emit an event that names the RUNG rather than merely the failure. What it deliberately does NOT
    do is tear the lane down or touch main: the lane is preserved on every branch of the decision, and
    the refusal condition itself is `integrate_lane_branch`'s and is not revisited here.

    THE BUDGET LIVES ON THE ITEM, not on the attempt record. A deferred item is re-attempted from the
    dispatch loop WITHOUT a new agent turn, so there is no new attempt record to count in; counting per
    attempt would reset the budget on every retry and make it unbounded, which is the exact spin the
    limit exists to prevent.
    """

    options = state.get("options") or {}
    limit = int(options.get("integration_retry_limit", DEFAULT_INTEGRATION_RETRY_LIMIT))
    policy = str(options.get("on_integration_blocked", ON_INTEGRATION_BLOCKED_DEFER))
    attempts_used = int(item.get("integration_attempts", 0)) + 1
    item["integration_attempts"] = attempts_used

    decision = decide_integration_deferral(
        integ_kind=integ_kind,
        attempts_used=attempts_used,
        limit=limit,
        policy=policy,
    )

    # The diagnostic reason string these two keys carried BEFORE this plan is preserved verbatim: it is
    # read by existing reports, and F-3 records that its presence once made a reader think the ladder
    # already existed. It says WHY the integration was refused; the ladder's own verdict is the
    # separate `integration_ladder` record below, so the two facts are not conflated.
    attempt["integration_deferred"] = integ_reason
    item["integration_deferral"] = integ_reason
    attempt["disposition"] = decision.status
    attempt["finalized"] = True
    item["status"] = decision.status
    ladder = {
        "kind": integ_kind,
        "deferrable": classify_integration_refusal(integ_kind),
        "status": decision.status,
        "deferred": decision.deferred,
        "attempts_used": decision.attempts_used,
        "limit": decision.limit,
        "policy": policy,
        "verdict": decision.reason,
    }
    item["integration_ladder"] = ladder
    attempt["integration_ladder"] = ladder
    save_state(run_dir, state)
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "at": utc_now(),
            "event": (
                "ipd-integration-deferred"
                if decision.deferred
                else (
                    "ipd-integration-blocked"
                    if decision.status == INTEGRATION_BLOCKED_STATUS
                    else "ipd-merge-conflict"
                )
            ),
            "id6": item.get("id6"),
            "setid": item.get("setid"),
            "detail": integ_reason,
            "verdict": decision.reason,
            "attempts_used": decision.attempts_used,
            "limit": decision.limit,
            "policy": policy,
            "branch": branch,
        },
    )
    return decision


def reattempt_deferred_integrations(
    *,
    repo: Path,
    run_dir: Path,
    state: MutableMapping[str, Any],
    integrate: Callable[..., tuple[bool, str, str]],
    finish_integrated: Callable[..., None],
    save_state: Callable[..., Any],
    append_jsonl: Callable[..., Any],
    handle_for: Callable[[Mapping[str, Any]], Any],
    validation_runner_for: Callable[[Mapping[str, Any]], Any],
    poll: bool = False,
    interactive: bool = False,
    ask: bool = False,
) -> list[dict[str, Any]]:
    """RUNG 1 (and, with ``poll``/``ask``, rungs 2 and 3): retry every deferred item's integration.

    CALLED FROM THE TOP OF THE DISPATCH LOOP, which is why rung 1 costs nothing: that loop already
    reloads state and already runs `cascade_dependency_blocked` each iteration, so the next item's
    completion IS the natural retry trigger. Zero waiting, zero tokens, nothing blocked.

    EVERY RE-ATTEMPT GOES THROUGH ``integrate``, i.e. through `integrate_lane_branch` and therefore
    through `orchestrate_isolation.execute_merge_and_revalidate_gate`. There is deliberately no
    shortcut that treats a clean `dirty_tree_overlap` as sufficient: that would prove only the absence
    of un-owned dirt, and say nothing about whether the suite still passes against today's main.

    ``poll``/``ask`` are passed by the caller when NOTHING ELSE IS DISPATCHABLE (the loop's own
    `runnable is None`), which is rung 2's trigger. That condition covers both the last-item case and
    the case where five items remain and ALL are deferred - a last-item test would miss the second.

    Returns the per-item records for the report.
    """

    records: list[dict[str, Any]] = []
    for item in deferred_integration_items(state):
        handle = handle_for(item)
        if handle is None:
            # The lane is gone (torn down out of band, or a resume in a checkout that never had it).
            # Fail toward the terminal state rather than looping on something unreachable.
            item["status"] = INTEGRATION_BLOCKED_STATUS
            item["integration_ladder"] = {
                "status": INTEGRATION_BLOCKED_STATUS,
                "deferred": False,
                "verdict": (
                    "the deferred lane could not be resolved in this checkout, so the deferral "
                    "cannot be retried here; the item is terminal and whatever branch exists is "
                    "left untouched"
                ),
            }
            save_state(run_dir, state)
            records.append({"id6": item.get("id6"), "outcome": "lane-unresolvable"})
            continue

        if poll:
            outcome = poll_for_integration_window(
                repo,
                tuple(item.get("integration_changed_files") or ()),
                poll_limit=int(
                    (state.get("options") or {}).get(
                        "integration_poll_limit", DEFAULT_INTEGRATION_POLL_LIMIT
                    )
                ),
            )
            item["integration_poll"] = {
                "bound": outcome.bound,
                "polls": outcome.polls,
                "last_activity_age": outcome.last_activity_age,
                "detail": outcome.detail,
                "cleared": outcome.cleared,
            }
            save_state(run_dir, state)
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "ipd-integration-poll",
                    "id6": item.get("id6"),
                    "bound": outcome.bound,
                    "polls": outcome.polls,
                    "last_activity_age": outcome.last_activity_age,
                    "detail": outcome.detail,
                },
            )

        integrated, reason, kind = integrate(item, handle)
        if integrated:
            finish_integrated(item, handle, reason)
            records.append(
                {"id6": item.get("id6"), "outcome": "integrated", "detail": reason}
            )
            continue

        attempts = item.get("attempts") or [{}]
        decision = record_integration_refusal(
            run_dir=run_dir,
            state=state,
            item=item,
            attempt=attempts[-1] if attempts else {},
            integ_kind=kind,
            integ_reason=reason,
            branch=getattr(handle, "branch", None),
            save_state=save_state,
            append_jsonl=append_jsonl,
        )
        if not decision.deferred and ask and interactive:
            # RUNG 3, reached only when rungs 1 and 2 are exhausted. `interactive` is the CALLER's
            # `is_interactive_run`, so an unattended run never arrives here with `ask` honored.
            answer = ask_operator_about_integration(
                str(item.get("id6") or ""), reason, interactive=interactive
            )
            item["integration_ask"] = {
                "asked": answer.asked,
                "retry": answer.retry,
                "detail": answer.detail,
            }
            if answer.retry:
                # One more attempt, still through the full gate. It does NOT reopen the budget: on
                # refusal the decision below re-derives from the same exhausted count and goes terminal.
                integrated, reason, kind = integrate(item, handle)
                if integrated:
                    finish_integrated(item, handle, reason)
                    records.append(
                        {
                            "id6": item.get("id6"),
                            "outcome": "integrated-after-ask",
                            "detail": reason,
                        }
                    )
                    continue
            save_state(run_dir, state)
        records.append(
            {
                "id6": item.get("id6"),
                "outcome": "deferred" if decision.deferred else "terminal",
                "detail": decision.reason,
            }
        )
    return records


def resolve_exhausted_deferrals(
    run_dir: Path,
    state: MutableMapping[str, Any],
    *,
    save_state: Callable[..., Any],
    append_jsonl: Callable[..., Any],
) -> list[str]:
    """OQ-03: no run may END with an item still in the non-terminal deferred state.

    WHY THIS IS A REQUIREMENT AND NOT TIDINESS. `integration-deferred` is BY DEFINITION not a
    disposition: a run that ends on one has fabricated neither success nor failure, leaving the
    operator with no signal and the next resume with an ambiguous item. So once every rung is
    exhausted each remaining deferred item is resolved to TERMINAL `integration-blocked`, with the lane
    preserved - which is precisely today's outcome, reached LAST instead of FIRST. That is honest, and
    it is also what makes the deferral safe to add: the worst case is the behavior we already had.

    The recovery route from there is unchanged and already documented: `--retry-incomplete` re-queues an
    `integration-blocked` item, and child 04 (`rl67b0`) adds the `integrate` verb.

    Returns the id6s it resolved, so the caller can report them.
    """

    resolved: list[str] = []
    for item in deferred_integration_items(state):
        ladder = dict(item.get("integration_ladder") or {})
        item["status"] = INTEGRATION_BLOCKED_STATUS
        ladder.update(
            {
                "status": INTEGRATION_BLOCKED_STATUS,
                "deferred": False,
                "verdict": (
                    "every rung of the deferral ladder was exhausted (re-attempts, the bounded "
                    "poll, and the bounded operator question), so the item is resolved to the "
                    "TERMINAL state with its lane preserved rather than left non-terminal: a run "
                    "must never end on a status that is not a disposition"
                ),
            }
        )
        item["integration_ladder"] = ladder
        attempts = item.get("attempts") or []
        if attempts:
            attempts[-1]["disposition"] = INTEGRATION_BLOCKED_STATUS
        resolved.append(str(item.get("id6") or ""))
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "ipd-integration-blocked",
                "id6": item.get("id6"),
                "setid": item.get("setid"),
                "detail": item.get("integration_deferral"),
                "verdict": ladder["verdict"],
                "attempts_used": item.get("integration_attempts"),
                "poll": item.get("integration_poll"),
                "ask": item.get("integration_ask"),
            },
        )
    if resolved:
        save_state(run_dir, state)
    return resolved


class AskOutcome(NamedTuple):
    """The result of rung 3's operator question. `asked` is False when it was SUPPRESSED."""

    asked: bool
    answer: str | None
    retry: bool
    detail: str


def ask_operator_about_integration(
    id6: str,
    reason: str,
    *,
    interactive: bool,
    timeout: float | None = None,
    prompt: Callable[..., str | None] | None = None,
) -> AskOutcome:
    """RUNG 3: ask the operator whether to retry once more, WITHOUT the ability to hang the run.

    TWO HARD CONSTRAINTS, both of which have already been paid for once in this repository:

    * SUPPRESSED WITHOUT AN ANSWER CHANNEL. `interactive` comes from
      :func:`is_interactive_run`, which tests BOTH a real TTY and the absence of `--unattended`
      (the operator declaring nobody is there, which must win over a TTY that happens to exist).
      An unattended overnight run must NEVER stop on a question nobody will see; that is strictly
      worse than today's terminal refusal. No second TTY test is written here.
    * IT CANNOT WAIT FOREVER. The prompt is :func:`prompt_for_gate_phrase`, which uses `select`
      with a bounded timeout and never a blocking read, and on no answer this returns
      `retry=False` so the caller goes TERMINAL with the lane preserved. An unbounded ask would
      rebuild exactly the deadlock `qyaime` closed, whose own honest limit was that the ask is
      "bounded and recorded, not architecturally prevented" - so the bound is the architecture here.

    Returns an :class:`AskOutcome`; `retry=True` only on an explicit affirmative answer.
    """

    if not interactive:
        return AskOutcome(
            asked=False,
            answer=None,
            retry=False,
            detail=(
                "the operator question was SUPPRESSED: this run has no interactive answer channel "
                "(no TTY, or --unattended), so it must not stop on a question nobody will see"
            ),
        )
    # Resolved HERE rather than as a default argument because `GATE_PROMPT_TIMEOUT` is defined further
    # down this module (with the gate prompt it belongs to) and this section sits with the integration
    # code it serves. Reusing that constant is deliberate: the two prompts in this package must not
    # disagree about how long a run may wait for a human.
    if timeout is None:
        timeout = GATE_PROMPT_TIMEOUT
    _prompt = prompt_for_gate_phrase if prompt is None else prompt
    question = (
        f"  ? lane {id6} cannot integrate: {reason}\n"
        f"    Retry the integration now? [y/N] (no answer in {timeout}s = give up, "
        "lane preserved): "
    )
    answer = _prompt(question, timeout=timeout)
    if answer is None:
        return AskOutcome(
            asked=True,
            answer=None,
            retry=False,
            detail=(
                f"the operator question TIMED OUT after {timeout}s with no answer, so the item is "
                "terminal and the lane is preserved; no code path waits on this prompt indefinitely"
            ),
        )
    typed = answer.strip().lower()
    if typed[:1] == "y":
        return AskOutcome(
            asked=True,
            answer=typed,
            retry=True,
            detail="the operator asked for one more integration attempt",
        )
    return AskOutcome(
        asked=True,
        answer=typed,
        retry=False,
        detail=(
            f"the operator declined a further attempt ({typed!r}), so the item is terminal and the "
            "lane is preserved"
        ),
    )


# ==================================================================================================
# integpath-04 (`rl67b0`): RE-INTEGRATING A VERIFIED LANE WITH NO AGENT TURN
# ==================================================================================================
#
# THE DEFECT, MEASURED RATHER THAN REASONED. A lane that finished, verified, finalized, and then failed
# to integrate had NO cheap recovery route. A bare `resume` did nothing (`integration-blocked` sits in
# both runners' `TERMINAL_STATES`, so the item is never `queued` and never selected), and
# `--retry-incomplete` RE-DISPATCHED the finished work as a full agent turn, which `allocate_worktree`
# then attempt-scoped into a SECOND lane because the first one classifies `HOLDS-WORK`. Measured in
# this repository: `mm6wuz` accumulated `aw/lane/mm6wuz`, `_attempt2` and `_attempt3`, and $39.42 of
# verified work was recovered by hand from the third; run `run-20260905T050043Z-639569` stranded four
# verified lanes that all merged clean against main afterwards. In both cases a `git merge` would have
# finished in seconds.
#
# SO THIS SECTION IS ONE IMPLEMENTATION WITH TWO ENTRY POINTS: the operator-facing verb
# (`aw <host> integrate <id6>`, plus the driver subcommand it aliases) and the automatic pass a resume
# makes before any item can be re-dispatched. Both go through `reintegrate_lane` below, which goes
# through `integrate_lane_branch` above, which goes through
# `orchestrate_isolation.execute_merge_and_revalidate_gate`. There is deliberately no second merge
# path and no fast route that takes a clean `git merge-tree` as sufficient: cleanliness proves the
# absence of a TEXTUAL conflict and says nothing about whether the suite still passes.
#
# THREE CONSTRAINTS THAT ARE NOT OBVIOUS, each measured rather than reasoned:
#
#   1. THE LANE IDENTITY IS PERSISTED, NOT DERIVABLE. `integrate_lane_branch` reads a LIVE
#      `WorktreeHandle` that `allocate_isolation_worktree` returned in the same process; a fresh
#      `integrate` process has no such object. It is rebuilt from the durable
#      `preserved_lane_id`/`preserved_base`/`preserved_branch` fields through `resolve_prior_lane`,
#      and NEVER by reconstructing `aw/lane/<id6>` from the id6, which `lane_branch_name`'s docstring
#      forbids because allocation may have attempt-scoped the name. `mm6wuz`'s three lanes are the
#      live proof that a guessed name can designate the WRONG lane.
#   2. ROUTING THROUGH THE GATE DOES NOT BY ITSELF RE-VERIFY ANYTHING. The shipped
#      `make_integration_validation_runner` returns a constant `True`, so for a single lane the gate's
#      revalidation step is inert and the attempt passes unconditionally. A verb built on that alone
#      would be a way to land an UNVALIDATED lane on main while pasting a green gate result as proof
#      of verification. So `reintegrate_lane` supplies a REAL validation runner, whose body runs the
#      repository suite in the PRIMARY checkout, and refuses on a non-passing result.
#   3. THE SUITE CHECK IS INJECTED, NEVER IMPORTED. `run_suite_check` is defined in `oc_runipd`, and
#      `tests/test_runner_shared.py::NoRunnerImportTests` AST-walks THIS module and fails on any
#      import naming `runipd`, at module level or lazily inside a function. Copying its body would
#      fork its fail-closed reading of exit 124/127. So it is a PARAMETER, exactly as `run_checked`
#      and `host_label` already are on `integrate_lane_branch` (see this module's docstring).
#
# AND THE INTEGRATION BASE IS THE LANE'S OWN DECLARED BASE, exactly as the in-run path passes it.
# `orchestrate_isolation.stale_base_check` compares the FIRST lane outcome's own `base_commit` to the
# `integration_base_commit` the CALLER passed: it is a consistency assertion on the caller's two
# arguments, not a freshness test against main, and no argument makes it into one. Measured in a
# throwaway repository whose main was one commit ahead of the lane base: passing main's current head
# refuses EVERY recovered lane (`integration_failed_stale_base`), and rebuilding the `LaneOutcome`
# against main's head to satisfy the check revalidates a combined diff that contains main's own
# intervening file as a DELETION, i.e. a diff that REVERTS main - precisely the mis-attribution
# `worktree_lease`'s `LANE_STALE` rationale forbids by name. The freshness signal is the suite run in
# constraint 2, and it is the only thing here that plays that role.

#: WHY the attempt refused, as a closed vocabulary rather than a message a caller has to match on.
#: Each value is a DISTINCT condition with its own operator-facing sentence; none is a silent no-op.
REINTEGRATE_OK = "integrated"
REINTEGRATE_NO_LANE_RECORD = "no-lane-record"
REINTEGRATE_AMBIGUOUS_LANE = "ambiguous-lane"
REINTEGRATE_LANE_ABSENT = "lane-absent"
REINTEGRATE_LANE_EMPTY = "lane-holds-no-commits"
REINTEGRATE_LANE_FOREIGN = "lane-foreign"
REINTEGRATE_LANE_LIVE = "lane-owned-by-live-process"
REINTEGRATE_PLAN_NOT_FINALIZED = "plan-not-finalized-on-lane"
REINTEGRATE_GATE_REFUSED = "gate-refused"
REINTEGRATE_ERROR = "attempt-errored"

#: The item statuses a re-integration attempt is legitimate for. BOTH, per OQ-01: `merge-conflict`
#: means the gate found a real conflict against the main OF THAT MOMENT, main has since moved, and the
#: only way to learn whether the conflict is gone is to run the gate again. The attempt costs one gate
#: run and no agent turn, and a refusal leaves the item exactly as it was with its lane preserved, so
#: declining to retry the more-likely-to-need-help case would leave a paid re-dispatch that ORPHANS the
#: lane as its only route.
REINTEGRATABLE_STATUSES: tuple[str, ...] = (
    INTEGRATION_BLOCKED_STATUS,
    INTEGRATION_REFUSAL_CONFLICT,
)


class LaneCandidate(NamedTuple):
    """One re-integratable lane, as read back from DURABLE run state (never from a branch guess)."""

    run_id: str
    run_dir: Path
    id6: str
    lane_id: str
    branch: str
    base_commit: str
    worktree: str | None
    item_status: str

    def describe(self) -> str:
        return "{0} (run {1}, branch {2}, status {3})".format(
            self.id6, self.run_id or "?", self.branch, self.item_status or "?"
        )


class ReintegrationOutcome(NamedTuple):
    """What ONE re-integration attempt did, as data, so both entry points report it identically."""

    integrated: bool
    code: str
    reason: str
    #: `integrate_lane_branch`'s own kind when the gate actually ran, else None. Preserved because the
    #: caller's status write depends on it (the transient `integration-blocked` arm is deferrable and
    #: `merge-conflict` is not), and re-deriving it from the message text would be a locale bug.
    kind: str | None = None
    candidate: LaneCandidate | None = None
    #: The suite result the INJECTED checker returned, so a caller can report what was actually run.
    suite: Any | None = None
    #: Populated only for `REINTEGRATE_AMBIGUOUS_LANE`: the candidates the operator must choose from.
    candidates: tuple[LaneCandidate, ...] = ()


def iter_run_states(repo: Path) -> list[tuple[Path, dict[str, Any]]]:
    """Every readable `(run_dir, state)` pair under this repository's runs root, newest name last.

    A verb invoked OUT OF BAND has no run in hand, so the run records ARE its index. Unreadable or
    partial records are SKIPPED rather than raised on: one corrupt state.json must not make recovery
    impossible for every other run.
    """

    root = state_root(repo)
    if not root.is_dir():
        return []
    out: list[tuple[Path, dict[str, Any]]] = []
    for run_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        path = run_dir / "state.json"
        if not path.is_file():
            continue
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(state, dict):
            out.append((run_dir, state))
    return out


def find_lane_candidates(
    repo: Path, id6: str, *, run_id: str | None = None
) -> list[LaneCandidate]:
    """Every recorded lane for ``id6``, most recent run last. OQ-02: the id6 alone is enough.

    THE RUN ID IS OPTIONAL BY DESIGN. The item's strongest use case is a lane stranded by an OLDER
    run, where the operator may no longer have the run id, so requiring it would make the verb useless
    in exactly the case it exists for. It is accepted to DISAMBIGUATE attempt-scoped lanes
    (`_attempt2`, `_attempt3`), which `mm6wuz` proves can exist; the caller REFUSES and lists the
    candidates rather than guessing when several match and no run id was given, because integrating the
    wrong lane would land the wrong work on main.

    De-duplicated by branch, keeping the LAST (most recent run) record for a branch, because that is
    the record whose base and status describe the lane as it now stands.
    """

    by_branch: dict[str, LaneCandidate] = {}
    for run_dir, state in iter_run_states(repo):
        this_run = str(state.get("run_id") or run_dir.name)
        if run_id and this_run != run_id and run_dir.name != run_id:
            continue
        for item in state.get("queue") or []:
            if not isinstance(item, dict) or str(item.get("id6") or "") != id6:
                continue
            lane_id, base, branch = resolve_prior_lane(item)
            if not branch:
                continue
            by_branch[str(branch)] = LaneCandidate(
                run_id=this_run,
                run_dir=run_dir,
                id6=id6,
                lane_id=str(lane_id or id6),
                branch=str(branch),
                base_commit=str(base or ""),
                worktree=(
                    str(item.get("preserved_worktree"))
                    if item.get("preserved_worktree")
                    else None
                ),
                item_status=str(item.get("status") or ""),
            )
    return list(by_branch.values())


def lane_holds_finalized_plan(repo: Path, branch: str, id6: str) -> tuple[bool, str]:
    """Is ``id6``'s plan in `executed/` ON ``branch``? Returns (answer, operator-facing detail).

    "The plan is not finalized on the lane" is NOT one of `worktree_lease`'s five lane states and
    cannot be read off the classifier, so it gets its own check (F-16). It is answered against the
    BRANCH TREE rather than the lane worktree, because a lane branch can outlive its worktree and the
    work would then be silently unrecoverable through a worktree-only test.

    A LIFECYCLE BUCKET IS A DIRECTORY (see `plan_bucket`), so this is a path question about the lane's
    own tree, never a re-reading of the plan's `- Status:` field.
    """

    rc, out, err = _run_git(repo, ["ls-tree", "-r", "--name-only", branch])
    if rc != 0:
        return False, "could not read the lane branch tree: {0}".format(
            (err or out).strip()
        )
    needle = "-{0}-".format(id6)
    seen: list[str] = []
    for line in out.splitlines():
        name = line.strip()
        if not name.endswith(".ipd.md") or needle not in Path(name).name:
            continue
        seen.append(name)
        if plan_bucket(Path(name)) == "executed":
            return True, "the plan is finalized on the lane at {0}".format(name)
    if not seen:
        return False, (
            "no plan file for {0} exists on the lane at all, so this lane never finalized "
            "it".format(id6)
        )
    return False, (
        "the plan for {0} is on the lane but NOT in executed/ ({1}), so the lane's turn never "
        "finalized it and there is no verified work to integrate".format(
            id6, ", ".join(sorted(seen))
        )
    )


def reintegrate_lane(
    repo: Path,
    id6: str,
    *,
    integrate: Callable[[Path, Any, str, Any], tuple[bool, str, str]],
    suite_check: Callable[..., Any],
    run_id: str | None = None,
    candidate: LaneCandidate | None = None,
) -> ReintegrationOutcome:
    """Re-attempt integration for ONE named verified lane, with NO agent turn.

    integpath-04 (`rl67b0`) E-01. THE single implementation behind BOTH the operator verb
    (`aw <host> integrate <id6>` and `aw <host> run integrate <id6>`) and the automatic pass a resume
    makes (:func:`integrate_stranded_lanes`), so the two spellings and the two triggers cannot drift.

    WHAT IT DOES, in order, and every step is a refusal point:

      1. RESOLVE the lane from DURABLE state (`find_lane_candidates` -> `resolve_prior_lane`), never
         from a branch name reconstructed out of the id6. Several matching lanes with no run id given
         is a REFUSAL that lists them (OQ-02), not a guess.
      2. CLASSIFY it with `worktree_lease.inspect_lane`, the existing classifier, rather than writing a
         second one. Its five states do NOT map one-to-one onto the refusal cases, so the mapping is
         explicit here: `ABSENT` is its own refusal; `EMPTY`/`STALE` both mean "holds no commits";
         `HOLDS-WORK` alone does NOT prove there is committed work, because a merely DIRTY lane with
         zero commits also classifies that way, so `commits_ahead > 0` is required; `FOREIGN` is
         refused rather than handled.
      3. REFUSE a lane a LIVE process still owns. This is an OUT-OF-BAND command holding no run lock,
         so integrating a lane a running driver is still working in would be a race that could merge a
         half-finished tree. `inspect_lane` already reports `owner_live`; no second liveness probe.
      4. REFUSE when the plan is not finalized ON the lane (see `lane_holds_finalized_plan`). An
         unfinalized lane is not verified work, whatever its commits say.
      5. RE-VERIFY AND MERGE through `integrate` (each host's `integrate_lane_branch` wrapper, so the
         merge subject still names the right driver), passing the lane's own DECLARED base and a REAL
         validation runner that runs the repository suite in the PRIMARY checkout. A non-passing suite
         makes the gate refuse, main is left untouched, and the lane is preserved. This is the whole
         safety argument: a lane verified against yesterday's main is not verified against today's.

    ``suite_check`` is INJECTED (F-17) and is called as ``suite_check(repo, run_id)``, returning an
    object with a ``passing`` bool and a ``reason`` string (each host binds its own `run_suite_check`).
    It is called from INSIDE the gate's `full_validation_runner`, which is what makes the suite result
    the gate's verdict rather than a separate opinion beside it. ``integrate`` is injected for the same
    reason `integrate_lane_branch` takes `run_checked` and `host_label`.

    NEVER RAISES for an expected condition: every failure is a `ReintegrationOutcome` carrying a code,
    because the resume caller must be able to continue with the rest of its queue (E-03) and a verb
    must exit nonzero with a sentence rather than a traceback.
    """

    from agent_workflows import worktree_lease

    if candidate is None:
        found = find_lane_candidates(repo, id6, run_id=run_id)
        if not found:
            return ReintegrationOutcome(
                integrated=False,
                code=REINTEGRATE_NO_LANE_RECORD,
                reason=(
                    "no run record names a preserved lane for {0}, so there is no lane identity to "
                    "integrate. The lane branch is read from the run record's preserved_lane_id / "
                    "preserved_base / preserved_branch fields and is deliberately NOT reconstructed "
                    "from the id6, because allocation may have attempt-scoped the name".format(
                        id6
                    )
                ),
            )
        if len(found) > 1:
            return ReintegrationOutcome(
                integrated=False,
                code=REINTEGRATE_AMBIGUOUS_LANE,
                reason=(
                    "{0} has {1} recorded lanes and no run id was given; refusing rather than "
                    "guessing, because integrating the wrong lane would land the wrong work on "
                    "main. Re-run naming one: {2}".format(
                        id6,
                        len(found),
                        "; ".join(c.describe() for c in found),
                    )
                ),
                candidates=tuple(found),
            )
        candidate = found[0]

    lane = worktree_lease.inspect_lane(
        repo,
        worktree_lease.lane_id_from_branch(candidate.branch) or candidate.lane_id,
        base_commit=candidate.base_commit or "HEAD",
    )

    if lane.state == worktree_lease.LANE_ABSENT:
        return ReintegrationOutcome(
            integrated=False,
            code=REINTEGRATE_LANE_ABSENT,
            reason=(
                "lane {0} no longer exists (no branch and no registered worktree), so there is "
                "nothing to integrate; whatever the run recorded has been removed out of "
                "band".format(candidate.branch)
            ),
            candidate=candidate,
        )
    # `owner_live` is Optional[bool]: None means UNKNOWN owner and must never be read as "not live".
    if lane.owner_live is True:
        return ReintegrationOutcome(
            integrated=False,
            code=REINTEGRATE_LANE_LIVE,
            reason=(
                "lane {0} is owned by a LIVE process, and this command holds no run lock; "
                "integrating it now could merge a half-finished tree. Let that run finish (or stop "
                "it) and try again".format(candidate.branch)
            ),
            candidate=candidate,
        )
    if lane.state == worktree_lease.LANE_FOREIGN:
        return ReintegrationOutcome(
            integrated=False,
            code=REINTEGRATE_LANE_FOREIGN,
            reason=(
                "lane {0} classifies FOREIGN (its base is not an ancestor of the base recorded for "
                "it), so it is not this run's lane to integrate; refusing rather than "
                "guessing".format(candidate.branch)
            ),
            candidate=candidate,
        )
    if lane.commits_ahead <= 0:
        # HOLDS-WORK alone does NOT prove committed work: a merely DIRTY lane with zero commits also
        # classifies that way (F-16), and a dirty tree is not something a merge can carry.
        return ReintegrationOutcome(
            integrated=False,
            code=REINTEGRATE_LANE_EMPTY,
            reason=(
                "lane {0} holds no commits beyond its base (classified {1}{2}), so there is no "
                "verified work to integrate".format(
                    candidate.branch,
                    lane.state,
                    "; its tree is dirty, and uncommitted changes are invisible to a merge"
                    if lane.dirty
                    else "",
                )
            ),
            candidate=candidate,
        )

    finalized, detail = lane_holds_finalized_plan(repo, candidate.branch, candidate.id6)
    if not finalized:
        return ReintegrationOutcome(
            integrated=False,
            code=REINTEGRATE_PLAN_NOT_FINALIZED,
            reason="lane {0} is not a finalized lane: {1}".format(
                candidate.branch, detail
            ),
            candidate=candidate,
        )

    handle = worktree_lease.WorktreeHandle(
        lane_id=candidate.lane_id,
        path=Path(candidate.worktree) if candidate.worktree else Path(""),
        branch=candidate.branch,
        # THE LANE'S OWN DECLARED BASE, exactly as the in-run path passes it. See this section's
        # header for why main's current head is wrong in BOTH directions.
        base_commit=candidate.base_commit or (lane.base_sha or ""),
    )

    suite_holder: dict[str, Any] = {}

    def _validation_runner(_combined_diff: str, _merged_files: Any) -> bool:
        """THE REAL revalidation, and the only freshness signal in this path.

        Runs the repository suite in the PRIMARY checkout through the INJECTED checker and returns its
        verdict, so a red suite makes the GATE refuse (`integration_failed_combined_red`) rather than
        being a second opinion the merge could ignore. Contrast the shipped
        `make_integration_validation_runner`, whose whole body is `return True`: with that runner a
        single-lane attempt passes unconditionally, which would make this verb a way to land an
        unvalidated lane on main while reporting a green gate.
        """
        result = suite_check(repo, run_id or candidate.run_id)
        suite_holder["result"] = result
        return bool(getattr(result, "passing", False))

    try:
        integrated, reason, kind = integrate(
            repo, handle, candidate.id6, _validation_runner
        )
    except Exception as exc:  # noqa: BLE001
        # DELIBERATE blind catch: an exception from git or from the suite must be an honest REFUSAL
        # that leaves the item and its lane exactly as they were, never an abort of the resume that
        # called this (E-03) and never a traceback at an operator.
        return ReintegrationOutcome(
            integrated=False,
            code=REINTEGRATE_ERROR,
            reason="the re-integration attempt for {0} errored (nothing was integrated): {1}".format(
                candidate.branch, exc
            ),
            candidate=candidate,
            suite=suite_holder.get("result"),
        )

    suite = suite_holder.get("result")
    if not integrated:
        suffix = ""
        if suite is not None and not bool(getattr(suite, "passing", False)):
            suffix = "; {0}".format(
                getattr(suite, "reason", "") or "the suite did not pass"
            )
        return ReintegrationOutcome(
            integrated=False,
            code=REINTEGRATE_GATE_REFUSED,
            reason="{0}{1}".format(reason, suffix),
            kind=kind,
            candidate=candidate,
            suite=suite,
        )
    return ReintegrationOutcome(
        integrated=True,
        code=REINTEGRATE_OK,
        reason=reason,
        kind=kind,
        candidate=candidate,
        suite=suite,
    )


def finish_reintegrated_item(
    *,
    repo: Path,
    run_dir: Path,
    state: MutableMapping[str, Any],
    item: MutableMapping[str, Any],
    outcome: ReintegrationOutcome,
    save_state: Callable[..., Any],
    append_jsonl: Callable[..., Any],
    process_backlog_close: Callable[..., Any] | None = None,
) -> None:
    """Record a SUCCESSFUL re-integration exactly as the in-run success path records one.

    integpath-04 (`rl67b0`) E-03. NO INVENTED DISPOSITION: the item reaches `executed`, the same
    `ipd-finalized` event is appended, `last_plan_path` is RE-RESOLVED (the plan now lives in
    `executed/` on main, which is what a later reader resolves against), and the backlog close is
    attempted, because that is what the in-run path does AFTER integrating and a recovered lane has
    earned exactly the same bookkeeping.

    `recovery_next` IS CLEARED, and that is load-bearing rather than tidy: `--retry-incomplete` may
    ALREADY have flipped this item to `queued` with `recovery_next=True` before the integration pass
    could legally run (the requeue precedes the indeterminate refusal, which precedes the pass), so
    leaving the flag set would let the dispatch loop pay for a turn to redo work that just landed.

    `process_backlog_close` is INJECTED for the F-17 reason: it lives in `oc_runipd` (agy re-exports
    it), and this module may not import either runner. Passing None simply skips the close.
    """

    item["status"] = "executed"
    item["integrated"] = outcome.reason
    item.pop("recovery_next", None)
    item.pop("requeue_from_status", None)
    attempts = item.get("attempts") or []
    if attempts:
        attempts[-1]["disposition"] = "executed"
        attempts[-1]["integrated"] = outcome.reason
    with contextlib.suppress(DriverError, OSError):
        item["last_plan_path"] = str(
            resolve_plan_path(
                repo, str(item.get("configured_file") or ""), str(item["id6"])
            )
        )
    save_state(run_dir, state)
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "at": utc_now(),
            "event": "ipd-finalized",
            "id6": item.get("id6"),
            "setid": item.get("setid"),
            "integration": outcome.reason,
            # ADDITIVE, so every existing consumer of `ipd-finalized` is untouched: this names the
            # route, so an audit can tell a merge-only recovery from a paid turn.
            "reintegrated": True,
            "suite": getattr(outcome.suite, "reason", None),
        },
    )
    if process_backlog_close is not None and not (item.get("backlog_close") or {}).get(
        "closed"
    ):
        # Skip when the lane-side close already succeeded: re-evaluating would answer `item is
        # already done` (close=False) and OVERWRITE the success record with a refusal, reporting a
        # correct close as "left open".
        with contextlib.suppress(Exception):
            process_backlog_close(run_dir, state, item)
        save_state(run_dir, state)


def stranded_integration_candidates(
    repo: Path, state: Mapping[str, Any]
) -> list[tuple[dict[str, Any], LaneCandidate, str]]:
    """Every queue item whose verified lane is merely UNINTEGRATED, with its lane and prior status.

    integpath-04 (`rl67b0`) E-03/E-04. SELECTION IS ON DURABLE LANE FACTS, NOT ON `item["status"]`,
    and that is not a stylistic preference: `--retry-incomplete` runs BEFORE the point where the
    integration pass may legally sit, so by then the flag has already rewritten a stranded item's
    status to `queued`. A status test would therefore see nothing and the cheap path would be lost in
    exactly the case it exists for. So an item qualifies when its RECORDED disposition (live status, or
    the `requeue_from_status` the flag wrote when it rewrote that status) is re-integratable AND its
    recorded lane still holds committed work.

    Returns `(item, candidate, prior_status)` triples, so a caller can integrate, or restore the exact
    status the flag overwrote (E-04's hold-back), without re-deriving either fact.
    """

    from agent_workflows import worktree_lease

    out: list[tuple[dict[str, Any], LaneCandidate, str]] = []
    run_id = str(state.get("run_id") or "")
    run_dir_value = state.get("run_dir")
    for item in state.get("queue") or []:
        if not isinstance(item, dict):
            continue
        live = str(item.get("status") or "")
        prior = str(item.get("requeue_from_status") or "")
        effective = (
            live
            if live in REINTEGRATABLE_STATUSES
            else (prior if prior in REINTEGRATABLE_STATUSES else "")
        )
        if not effective:
            continue
        lane_id, base, branch = resolve_prior_lane(item)
        if not branch:
            continue
        lane = worktree_lease.inspect_lane(
            repo,
            worktree_lease.lane_id_from_branch(str(branch)) or str(lane_id or ""),
            base_commit=str(base or "HEAD"),
        )
        if lane.commits_ahead <= 0:
            # Nothing a merge could carry. Left for `--retry-incomplete` to handle as it always has,
            # which is right: an item with no committed lane work genuinely needs a turn.
            continue
        out.append(
            (
                item,
                LaneCandidate(
                    run_id=run_id,
                    run_dir=Path(str(run_dir_value)) if run_dir_value else Path("."),
                    id6=str(item.get("id6") or ""),
                    lane_id=str(lane_id or item.get("id6") or ""),
                    branch=str(branch),
                    base_commit=str(base or ""),
                    worktree=(
                        str(item.get("preserved_worktree"))
                        if item.get("preserved_worktree")
                        else None
                    ),
                    item_status=effective,
                ),
                effective,
            )
        )
    return out


def integrate_stranded_lanes(
    *,
    repo: Path,
    run_dir: Path,
    state: MutableMapping[str, Any],
    integrate: Callable[[Path, Any, str, Any], tuple[bool, str, str]],
    suite_check: Callable[..., Any],
    save_state: Callable[..., Any],
    append_jsonl: Callable[..., Any],
    process_backlog_close: Callable[..., Any] | None = None,
    report: Callable[[str], None] | None = None,
) -> list[dict[str, Any]]:
    """THE RESUME PASS: merge every already-verified lane instead of re-dispatching it (E-03/E-04).

    Called from `run_queue` AFTER the indeterminate refusal and BEFORE any item is dispatched, which
    is the one placement that satisfies both of this plan's ordering constraints. The refusal `return
    1`s before any turn, so nothing is integrated during a resume the driver is about to decline; and
    the `--retry-incomplete` requeue only rewrites `status`/`recovery_next` in memory-plus-state
    without dispatching anything, so acting after it is still strictly before any turn is launched.
    `run_queue` is only ever entered under `locked_run`, so this already holds the run lock and must
    NOT acquire a second one.

    THIS IS NOT BEHIND A FLAG, deliberately. The alternative default is silent re-dispatch of finished
    work, which is strictly worse and is the measured defect; empirically this alone would have
    resolved all four items of run `run-20260905T050043Z-639569`.

    TWO OUTCOMES PER ITEM, and both are honest:

      * INTEGRATED -> `finish_reintegrated_item` writes the same state and the same records the in-run
        success path writes, and clears `recovery_next` so the flag cannot re-dispatch work that just
        landed.
      * REFUSED    -> E-04's HOLD-BACK. The item is restored to the exact terminal status
        `--retry-incomplete` overwrote and is NOT re-dispatched, because dispatching it would
        attempt-scope a SECOND lane (`_attempt2`) and abandon the finished one, which is the measured
        `mm6wuz` failure. The operator is TOLD which item was held back, why, and what to do; a silent
        skip would reproduce the "a bare resume does nothing" trap one level up. NO lane is ever
        deleted or reclaimed to achieve this: the lane is the preserved evidence.

    IT CANNOT ABORT THE RESUME. A refusal, an exception from git, or a red suite records itself and the
    loop continues to the next item; `reintegrate_lane` converts every failure into an outcome rather
    than raising. A resume that died because one stranded lane could not be merged would be worse than
    the do-nothing behavior this replaces.

    NOTE THE COST THIS INHERITS: the attempt runs the suite in the primary checkout, so a resume with
    stranded lanes now spends a suite run per lane before dispatching anything. That is the right trade
    against a paid agent turn, but it is not free, which is why it is reported rather than silent.

    Returns one record per attempted item, for the caller's report.
    """

    def _say(message: str) -> None:
        if report is not None:
            report(message)

    records: list[dict[str, Any]] = []
    for item, candidate, prior in stranded_integration_candidates(repo, state):
        id6 = candidate.id6
        _say(
            "  integrating already-verified lane {0} for IPD {1} (no agent turn; runs the suite in "
            "{2})".format(candidate.branch, id6, repo)
        )
        outcome = reintegrate_lane(
            repo,
            id6,
            integrate=integrate,
            suite_check=suite_check,
            run_id=str(state.get("run_id") or ""),
            candidate=candidate,
        )
        if outcome.integrated:
            finish_reintegrated_item(
                repo=repo,
                run_dir=run_dir,
                state=state,
                item=item,
                outcome=outcome,
                save_state=save_state,
                append_jsonl=append_jsonl,
                process_backlog_close=process_backlog_close,
            )
            _say(
                "  \u2713 IPD {0} integrated to main from its existing lane {1} with NO agent turn "
                "({2})".format(id6, candidate.branch, outcome.reason)
            )
            records.append(
                {
                    "id6": id6,
                    "branch": candidate.branch,
                    "outcome": "integrated",
                    "detail": outcome.reason,
                }
            )
            continue

        # E-04: HELD BACK, not silently skipped, and not re-dispatched.
        item["status"] = prior
        item.pop("recovery_next", None)
        item["reintegration_refusal"] = {
            "code": outcome.code,
            "reason": outcome.reason,
            "branch": candidate.branch,
            "at": utc_now(),
        }
        save_state(run_dir, state)
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "ipd-reintegration-refused",
                "id6": id6,
                "setid": item.get("setid"),
                "code": outcome.code,
                "detail": outcome.reason,
                "branch": candidate.branch,
                "held_back_from_status": prior,
            },
        )
        _say(
            "  ! IPD {0} was NOT re-dispatched: its verified lane {1} still holds unintegrated work, "
            "and re-running it would allocate a SECOND lane and abandon that one. The integration "
            "re-attempt refused ({2}): {3}\n"
            "    -> left at status {4} with its lane intact. Fix the cause and re-run "
            "`integrate {0}`, or resolve on the preserved lane branch.".format(
                id6, candidate.branch, outcome.code, outcome.reason, prior
            )
        )
        records.append(
            {
                "id6": id6,
                "branch": candidate.branch,
                "outcome": "held-back",
                "code": outcome.code,
                "detail": outcome.reason,
            }
        )
    return records


def render_reintegration_result(outcome: ReintegrationOutcome, *, id6: str) -> str:
    """The verb's operator-facing sentence for one attempt. ONE renderer, so both hosts agree."""

    if outcome.integrated:
        branch = outcome.candidate.branch if outcome.candidate else "?"
        suite = getattr(outcome.suite, "reason", None)
        return "integrated {0} from lane {1} to main with no agent turn: {2}{3}".format(
            id6, branch, outcome.reason, "\n  {0}".format(suite) if suite else ""
        )
    return "integrate {0} REFUSED ({1}): {2}".format(id6, outcome.code, outcome.reason)


#: The verb's `--help` text. Shared so the driver subcommand and the `cli.py` host-noun alias cannot
#: describe the same command differently, and because WHAT IT COSTS is the reason an operator reaches
#: for it instead of a re-run: no agent turn, but a real gate run and a real suite run.
INTEGRATE_VERB_HELP = (
    "Re-attempt integration for an already verified lane, with NO agent turn "
    "(re-runs the merge-and-revalidate gate and the repository suite)"
)

INTEGRATE_VERB_DESCRIPTION = """Merge a lane that already finished, verified and finalized, but failed to integrate.

COSTS NO AGENT TURN. This is the whole point: recovering a stranded lane costs one merge instead of
one paid re-run. What it DOES cost is a re-verification, and that is deliberate: the attempt runs the
repository suite in the PRIMARY checkout and routes the merge through the same merge-and-revalidate
gate an in-run integration uses, because a lane verified against yesterday's main is not verified
against today's. A red suite, a real conflict, or a dirty overlapping base REFUSES, leaves main
untouched, and preserves the lane.

The lane is read from the run record's preserved lane fields, never reconstructed from the id6, so an
attempt-scoped lane (`aw/lane/<id6>_attempt2`) is integrated as itself. Pass --run-id to disambiguate
when an id6 has more than one recorded lane; without it, several candidates is a refusal that lists
them rather than a guess.
"""


def add_integrate_parser(sub: Any, *, command: str = "aw oc run") -> Any:
    """Declare the `integrate` subcommand on `sub`. ONE declaration, both drivers.

    It is declared on the RUNNER's own parser (where `start` already lives) for the reason
    `add_stop_parser` records: `aw oc run` / `aw agy run` forward `argparse.REMAINDER` verbatim to the
    runner's `main`, so re-declaring the flags at the `aw` layer would drift AND would bypass the
    implicit-start shim, which lives in `main()` rather than `build_parser()`.

    THE VERB MUST ALSO BE REGISTERED IN THAT SHIM'S SUBCOMMAND SET, in both drivers and in the test's
    inline third copy. Declaring the subparser alone is NOT enough: an unregistered first token is
    rewritten into `start <token>`, so a bare `integrate <id6>` would LAUNCH A RUN with `integrate` as
    a selector. That hazard is recorded for `stop` and is the same one here.
    """

    import argparse

    integrate = sub.add_parser(
        "integrate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help=INTEGRATE_VERB_HELP,
        description=INTEGRATE_VERB_DESCRIPTION,
        epilog="EXAMPLES:\n  {0} integrate mm6wuz\n  {0} integrate mm6wuz --run-id "
        "run-20260905T050043Z-639569\n".format(command),
    )
    integrate.add_argument(
        "id6", help="The 6-character IPD id whose lane should be integrated"
    )
    integrate.add_argument("--repo", default=".", help="Target Git repository root")
    integrate.add_argument(
        "--run-id",
        dest="run_id",
        default=None,
        help="Disambiguate when the id6 has more than one recorded lane (e.g. an attempt-scoped one)",
    )
    return integrate


def reconcile_item_on_interrupt(
    repo: Path,
    run_dir: Path,
    state: dict[str, Any],
    item: dict[str, Any],
    attempt: dict[str, Any],
    attempt_no: int,
    work_dir: str | None,
    msg: str,
    *,
    save_state_fn: Callable[[Path, dict[str, Any]], None],
    seq: int = 1,
    total: int = 1,
) -> None:
    """Handle per-item state reconciliation when KeyboardInterrupt is raised during execute_item.

    If msg == "just-terminate-no-cleanup":
        Leaves worktrees and lanes untouched on disk, records item status as interrupted.
    If msg == "clean-up-and-terminate" (or default interrupt cleanup):
        If NO files were changed:
            Tears down empty worktree, removes lane branch, unlinks begin receipt,
            resets item status to queued, and removes uncompleted attempt so next time
            aw run runs it executes as if it never ran before.
        If files WERE changed:
            Snapshots dirty work onto lane branch, marks item interrupted with certainty: known,
            so it can be resumed or re-run without refusal.
    """
    from agent_workflows import ipd_lifecycle, runner_stop, worktree_lease

    now = utc_now()
    if "just-terminate-no-cleanup" in msg:
        attempt["interrupted_at"] = now
        attempt["ended_at"] = now
        attempt["interrupt_reason"] = "just-terminate-no-cleanup"
        item["status"] = "interrupted"
        item["recovery_next"] = True
        save_state_fn(run_dir, state)
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": now,
                "event": "ipd-interrupted",
                "subevent": "no-cleanup",
                "id6": item["id6"],
            },
        )
        return

    # Option 1: Clean up and terminate
    lane_id = attempt.get("worktree_lane_id", item["id6"])
    base_commit = attempt.get("worktree_base", "")
    lane_rec = {
        "id6": item["id6"],
        "lane_id": lane_id,
        "base_commit": base_commit,
        "worktree": work_dir,
    }
    lane = describe_lane(repo, lane_rec) if work_dir else None

    # Check whether files were changed:
    if lane is not None:
        holds_work = bool(lane["holds_work"])
    else:
        status_out = _run_git(repo, ["status", "--porcelain"])
        holds_work = bool(status_out.strip())

    if not holds_work:
        # NO files were changed: clean up completely so it can be resumed or re-run fresh
        if work_dir and lane is not None:
            handle = worktree_lease.WorktreeHandle(
                lane_id=lane["lane_id"],
                path=Path(lane["worktree"]) if lane["worktree"] else Path(work_dir),
                branch=lane["branch"],
                base_commit=lane["base_sha"] or "",
            )
            with contextlib.suppress(Exception):
                worktree_lease.teardown_worktree(repo, handle, force=True)

        # Unlink begin receipt if present
        rcpt = ipd_lifecycle.receipt_path_for(repo, item["id6"])
        with contextlib.suppress(OSError):
            if rcpt.is_file():
                rcpt.unlink()

        # Reset item to queued as if it never ran
        item["status"] = "queued"
        item.pop("recovery_next", None)
        item.pop("stopped", None)
        item.pop("requires_reconciliation", None)
        item.pop("last_outcome", None)
        item.pop("verification_status", None)

        # Remove the unfinished attempt
        attempts = item.get("attempts", [])
        if attempts and attempts[-1].get("attempt") == attempt_no:
            attempts.pop()

        save_state_fn(run_dir, state)
        append_jsonl(
            run_dir / "events.jsonl",
            {"at": now, "event": "ipd-cleaned-up-no-changes", "id6": item["id6"]},
        )
        print(
            f"  (IPD {seq:02d}/{total} {item['id6']} had no files changed; cleaned up so it can run fresh)",
            file=sys.stderr,
        )
    else:
        # Files WERE changed: snapshot dirty work and preserve on lane branch
        snapshot = None
        branch_name = ""
        if work_dir and lane is not None:
            branch_name = lane["branch"]
            handle = worktree_lease.WorktreeHandle(
                lane_id=lane["lane_id"],
                path=Path(lane["worktree"]) if lane["worktree"] else Path(work_dir),
                branch=lane["branch"],
                base_commit=lane["base_sha"] or "",
            )
            if lane["dirty"]:
                with contextlib.suppress(Exception):
                    snapshot = worktree_lease.snapshot_lane_dirty_work(
                        repo, handle, note="Reason: clean-up-and-terminate."
                    )

        attempt["interrupted_at"] = now
        attempt["ended_at"] = now
        attempt["interrupt_reason"] = "clean-up-and-terminate"
        if snapshot:
            attempt["snapshot_commit"] = snapshot
        item["status"] = "interrupted"
        item["recovery_next"] = True
        item["stopped"] = {
            "at": now,
            "level": 4,
            "level_name": "now-force",
            "certainty": runner_stop.CERTAINTY_KNOWN,
            "disposition": "interrupted",
            "requester": "Ctrl-C",
        }
        item.pop("requires_reconciliation", None)
        save_state_fn(run_dir, state)
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": now,
                "event": "ipd-interrupted",
                "subevent": "work-preserved",
                "id6": item["id6"],
                "branch": branch_name,
            },
        )
        branch_info = f" on {branch_name}" if branch_name else ""
        print(
            f"  (IPD {seq:02d}/{total} {item['id6']} has changes preserved{branch_info}; ready to resume or re-run)",
            file=sys.stderr,
        )


# ---- plans / selectors ---------------------------------------------------------------------------


def _read_set(text: str) -> str | None:
    m = _SET_RE.search(text)
    if not m:
        return None
    raw = m.group(1).split("(")[0].strip()
    if not raw:
        return None
    token = raw.split()[0].strip("\"'").strip()
    return token if token else None


def _read_order(text: str) -> int | None:
    m = _ORDER_RE.search(text)
    return int(m.group(1)) if m else None


# ==================================================================================================
# rununify 06 (`sy7uwh`): THE ONE PLAN RECORD AND ITS ONE READER.
#
# WHAT THIS SECTION ENDS. Until now the two runners built DIFFERENT `PlanRecord` NamedTuples - oc's
# carried a `kind` field agy's lacked - which forced `parse_plan_file` and `build_dynamic_manifest` to
# stay forked and forced agy to RE-READ `- Kind:` from disk (through a private `_plan_kind` helper) for
# information oc already had in hand. `818uru` pinned that split deliberately and wrote a test
# forbidding unification, saying in the test itself that unifying "is a class (c) reconciliation for a
# later child". THIS IS THAT CHILD, authorized by the maintainer's 2026-09-14 unify-toward-oc ruling.
#
# WHY THE PREMISE DISSOLVED, which is what makes the override legitimate rather than a reversal for its
# own sake. When `818uru` pinned the split, agy had NO use for `kind`. It now imports the shared
# `action_for`, which READS `kind` to detect an orchestrator, so the split had stopped buying anything
# and cost a redundant disk read per plan. Measured at execution: oc's field set is a STRICT SUPERSET
# of agy's differing in exactly `kind`, and the two `parse_plan_file` bodies differed in exactly the
# two lines that read and pass it. So the merge loses nothing.
#
# THE FAILURE MODE HERE IS SILENT AND TYPE-SHAPED, and `818uru`'s own test says so: a shared
# constructor that DROPPED `kind` "would silently disable orchestrator detection" rather than crash.
# That is why the guard for this section (`tests/test_rununify_record.py`) asserts the orchestrator
# DERIVATION end to end on both hosts rather than merely that a field exists.
#
# BOTH PINS WERE INVERTED, NOT DELETED, following this repo's precedent for a pinned decision a later
# phase deliberately reverses (`tests/test_wtiso_characterization.py`):
# `tests/test_runner_shared.py::DiscoverPlansRecordTypeTests` and the single assertion at
# `tests/test_orchestrator_retirement.py`'s `test_the_agy_queue_entry_carries_kind`. Each now guards
# the UNIFIED shape and cites `sy7uwh` as the authorizing plan.
#
# THE THIRD `PlanRecord` IN THE PACKAGE IS UNRELATED AND MUST STAY THAT WAY. `agent_workflows/plans.py`
# defines its own `PlanRecord` (`path`/`area`/`disposition`/`status`/`set_id`/`order`), a different
# concept with no importers of that name. A repo-wide single-definition scan WILL find it; it is
# ALLOWLISTED with that reason rather than "fixed", because unifying two unrelated types that merely
# share a name would be a behavior change wearing a de-duplication's clothes.
# ==================================================================================================


def _read_kind(text: str) -> str | None:
    """Read the IPD's `- Kind:` metadata (orchestrator|child). This is the RELIABLE
    signal for 'is this an orchestrator' - NOT the Order number - matching
    ipd_schema.KIND_ORCHESTRATOR/KIND_CHILD."""
    m = _KIND_RE.search(text)
    return m.group(1).lower() if m else None


def _read_item_dependencies(text: str) -> tuple[list[str], str | None]:
    """Read the plan's canonical `- Item-Dependencies:` statement as CANONICAL TYPED edge tokens.

    Returns ``(edges, error)`` where ``edges`` is the list of canonical edge strings (e.g.
    ``["executed:af7i6p", "exists:spec:d4e5f6", "state:backlog:done:g7h8j9"]``) and ``error`` is the
    shared parser's message for a malformed statement (else None). `none`, `unresolved`, an empty
    value, and an absent field all yield ``([], None)``; the MISSING-vs-`none` distinction is NOT the
    runner's to judge (see `preflight_dependency_findings` and 8guhs0 OQ-02).

    THE QUALIFIER IS PRESERVED, NOT STRIPPED. The deleted `_read_deps` kept only bare id6 tokens,
    which would have silently degraded `exists:spec:<id6>` into an untyped id6 with different
    release semantics (plan finding F4). The satisfaction rule depends on the kind, so the typed
    token is what the record and the frozen queue must carry.

    Two shared authorities, no private parsing: the field NAME is `ipd_schema`'s constant and the
    metadata block is read by `ipd_lint.parse` (the same structural, fence-aware reader the lint and
    lifecycle surfaces use, measured byte-identical to `check_engine`'s extraction across the whole
    plans tree); the VALUE grammar is `ipd_schema.parse_item_dependencies`.
    """
    from agent_workflows import ipd_lint as _lint
    from agent_workflows import ipd_schema as _schema

    try:
        fields = _lint.parse(text).meta_fields
    except Exception:
        return [], None
    raw = fields.get(_schema.META_ITEM_DEPENDENCIES)
    if raw is None:
        return [], None
    edges, _ready, err = _schema.parse_item_dependencies(raw)
    if err:
        return [], err
    return [edge.canonical() for edge in edges], None


def _read_from_backlog(text: str) -> str | None:
    """The plan's `- From-Backlog:` id6, or None when the field is absent/empty.

    THE FIELD NAME IS THE SCHEMA'S, NOT A LOCAL REGEX (zhr6mc E-01). `ipd_schema.META_FROM_BACKLOG`
    is the single authority the checkers already use, so the runner and `aw check` cannot come to
    disagree about what the field is called. The metadata block is read by `ipd_lint.parse`, the same
    structural fence-aware reader the lint and lifecycle surfaces use -- identical in form to how
    `_read_item_dependencies` reads its own field, and for the identical reason.
    """
    from agent_workflows import ipd_lint as _lint
    from agent_workflows import ipd_schema as _schema

    try:
        fields = _lint.parse(text).meta_fields
    except Exception:
        return None
    raw = (fields.get(_schema.META_FROM_BACKLOG) or "").strip()
    if not raw or raw in {"-", "none", "unresolved"}:
        return None
    token = raw.split()[0].strip("\"'").strip()
    return token if ID6_RE.fullmatch(token) else None


class PlanRecord(NamedTuple):
    """ONE plan record for BOTH hosts (rununify 06, `sy7uwh`).

    THE FIELD SET IS oc's, because it was measured to be a strict SUPERSET of agy's differing in
    exactly `kind`, so the merge loses nothing and the Set's standing "oc is preferred" ruling
    applies cleanly. NOTHING WAS REDESIGNED: this is a merge of two existing shapes, so no field was
    renamed, no type changed, and no field nobody reads today was added.

    DO NOT DROP `kind` to "simplify" this. It is what `action_for` reads to detect an orchestrator,
    and losing it disables orchestrator detection SILENTLY and type-shapedly rather than crashing -
    the failure mode `818uru`'s pinned test warned about and the reason
    `tests/test_rununify_record.py` asserts the derivation end to end.
    """

    id6: str
    setid: str
    status: str
    order: int
    path: Path
    rel_path: str
    # CANONICAL TYPED edge tokens (`executed:<id6>` / `exists:<type>:<id6>` /
    # `state:<type>:<status>:<id6>`), never bare id6 strings: the qualifier decides the satisfaction
    # rule (`dependency_status`). `dependency_error` carries the shared parser's message when the
    # statement is malformed, so preflight can fail closed instead of silently seeing no edges.
    dependencies: list[str]
    # orchretire-03 (`pgq326`) / rununify 06 (`sy7uwh`): the plan's `- Kind:`. Present for BOTH hosts
    # now; agy used to lack it and re-read the file per plan to compensate.
    kind: str | None = None
    dependency_error: str | None = None
    # bkclose (zhr6mc) E-01: the plan's `- From-Backlog:` id6, or None when the field is absent.
    # Without this the runner could not know a backlog item was involved at all, so no automation
    # could ever advance a `graduated` item to `done`. Read via `ipd_schema.META_FROM_BACKLOG`, never
    # a local regex, so the runner and the checkers cannot disagree about the field name.
    from_backlog: str | None = None


def parse_plan_file(path: Path, repo: Path) -> PlanRecord | None:
    """Read ONE plan file into the ONE shared :class:`PlanRecord`, or None when unreadable.

    oc's body, verbatim apart from nothing: agy's differed in exactly the two lines that read and
    pass `kind`, which the unified record now carries for both hosts.

    WHY THE `selectors` IMPORT IS FUNCTION-LOCAL, since a module-level one would read more naturally.
    `runner_shared` keeps exactly ONE module-level first-party import (`render_stream`) plus the
    designated peer `runner_profiles`, and reaches `ipd_lint`/`ipd_schema`/`selectors` from inside the
    functions that need them - a rule enforced by
    `tests/test_orchestrator_probe_cache.py::TheRowWalkIsSharedWithTheRetirementGate`, because a
    module-level import here changes the import graph for BOTH host drivers and for the twelve other
    modules that import this one. Measured: five of those (`attention`, `completion`, `ipd_lifecycle`,
    `ipd_set_plan`, `runner_shutdown`) do NOT currently reach `selectors` at all, so a module-level
    import would newly tax them. `_read_item_dependencies` and `_read_from_backlog` above take the same
    approach for the same reason, so this is the module's convention rather than an exception to it.

    THE ALIASES ARE THE PERMISSIVE PUBLIC READERS, which is a behavior decision and not a naming one.
    Both runners' historical private copies tolerated any whitespace after the `-` while `selectors`'
    STRICT internal readers require exactly one space, and that strictness is a documented `aw find`
    matching contract. rununify 01 (`2r306y`) resolved this by binding the permissive public aliases,
    and `tests/test_runner_refork_guard.py::FrontMatterReaderBehaviorTests` pins BOTH halves, so
    swapping to the strict readers here would silently narrow which front-matter spellings both drivers
    accept.
    """
    from agent_workflows.selectors import read_front_matter_id as _read_id
    from agent_workflows.selectors import read_front_matter_status as _read_status

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    id6 = _read_id(text)
    setid = _read_set(text)
    status = _read_status(text)
    order = _read_order(text)
    deps, dep_err = _read_item_dependencies(text)
    kind = _read_kind(text)
    from_backlog = _read_from_backlog(text)
    m = _PLAN_FILENAME_RE.match(path.name)
    if m:
        if not setid:
            setid = m.group(1)
        if order is None:
            order = int(m.group(2))
        if not id6:
            id6 = m.group(3)
    if not id6:
        for part in path.name.split("-"):
            if ID6_RE.fullmatch(part):
                id6 = part
                break
    if not id6:
        try:
            rel = str(path.relative_to(repo))
        except ValueError:
            rel = str(path)
        id6 = hashlib.sha256(rel.encode("utf-8")).hexdigest()[:6]
    if not setid:
        setid = "standalone"
    if order is None:
        order = 99
    if not status:
        bucket = plan_bucket(path)
        status = bucket or "to-review"
    try:
        rel = str(path.relative_to(repo))
    except ValueError:
        rel = str(path)
    return PlanRecord(
        id6=id6,
        setid=setid,
        status=status,
        order=order,
        path=path.resolve(),
        rel_path=rel,
        dependencies=deps,
        kind=kind,
        dependency_error=dep_err,
        from_backlog=from_backlog,
    )


def plan_kind_from_file(path: Path) -> str | None:
    """The plan's `- Kind:` value, read from disk. THE LEGACY-MANIFEST FALLBACK.

    orchretire-03 (`pgq326`) E-04 introduced this on the antigravity host as `_plan_kind`, where it
    served TWO unrelated callers. rununify 06 (`sy7uwh`) removed the first (a workaround for the
    record split this section ends, now simply `rec.kind`) and lifted the second HERE, so BOTH hosts
    reach it.

    WHAT IT IS FOR, which is NOT the record split. A runner can be pointed at a HAND-WRITTEN manifest
    (the shipped `tools/ipdrunner/*-driver-manifest.json` is one). If such a manifest predates the
    `kind` key, the plan's kind is absent from it, and deriving `execute` for an APPROVED
    ORCHESTRATOR means spending a paid agent turn executing a plan that authors no code - precisely
    the defect `pgq326` fixed. So the manifest-then-file fallback re-reads `- Kind:` instead, the same
    shape `from_backlog` already uses.

    WHY BOTH HOSTS NOW HAVE IT (`sy7uwh` OQ-03, resolved by the maintainer 2026-09-16). Only agy had
    it, so the two hosts DISAGREED about a correctness gate, in oc's DISFAVOR: measured at execution,
    given a legacy manifest naming an approved orchestrator, `aw agy run` derived `orchestrate` and
    correctly retired it while `aw oc run` derived `execute`. Under the maintainer's directive that
    "there should be one code base shared by the two runners that contains 100% of the otherwise
    redundant code", the fallback was lifted here rather than preserved as agy-only (which would
    leave the disagreement standing) or dropped from both (which would knowingly reintroduce
    `pgq326`'s defect). The behavior change to oc is authorized by that ruling and is a FIX.

    Returns None when the file is unreadable, which makes `action_for` fall back to
    `determine_action` -- the pre-`pgq326` behavior, and the safe direction (a plan is agent-handled,
    never silently retired).
    """
    try:
        return _read_kind(path.read_text(encoding="utf-8"))
    except OSError:
        return None


def resolve_manifest_kind(
    entry: Mapping[str, Any], plan_path: Path | None
) -> str | None:
    """The plan's kind from a manifest ENTRY, falling back to the plan FILE when the key is absent.

    The ONE manifest-then-file resolution both hosts now use at their queue-build site, so a legacy
    hand-written manifest cannot make one host retire an approved orchestrator while the other spends
    an agent turn on it (`sy7uwh` OQ-03; see :func:`plan_kind_from_file`).

    `None` from the entry means "the manifest does not say", NOT "the plan has no kind": a generated
    manifest always carries the key (`build_dynamic_manifest` writes `rec.kind`), so an absent key
    means the manifest predates it. A present-but-None value is treated the same way, which is the
    safe direction: it costs one file read and can only ever ADD information.
    """
    kind = entry.get("kind")
    if kind is None and plan_path is not None:
        return plan_kind_from_file(plan_path)
    return kind


def build_dynamic_manifest(
    repo: Path, discovered: dict[str, PlanRecord]
) -> dict[str, Any]:
    """Compile discovered plans into a manifest dictionary.

    ONE implementation for both hosts (rununify 06, `sy7uwh`). The two versions differed in exactly
    one expression - `'kind': rec.kind` versus `'kind': _plan_kind(rec.path)` - so unifying the
    record collapsed this symbol for free, and the surviving form is oc's, which was already the one
    in production on that host.
    """
    plans_dict: dict[str, Any] = {}
    sets_dict: dict[str, list[PlanRecord]] = {}
    for id6, rec in discovered.items():
        plans_dict[id6] = {
            "set": rec.setid,
            "file": rec.rel_path,
            "status": rec.status,
            "order": rec.order,
            "dependencies": rec.dependencies,
            # orchretire-03 (`pgq326`) E-04: `kind` carried through the manifest so the SHARED
            # `action_for` can see it. Without this key every plan derived `execute` and an approved
            # orchestrator was AGENT-EXECUTED.
            "kind": rec.kind,
            # bkclose (zhr6mc) E-01: carried through the manifest so the frozen queue entry can hold
            # it. Additive; a hand-written manifest lacking the key simply links no item.
            "from_backlog": rec.from_backlog,
        }
        sets_dict.setdefault(rec.setid, []).append(rec)
    sorted_sets: dict[str, Any] = {}
    for setid, plist in sets_dict.items():
        plist_sorted = sorted(plist, key=lambda x: (x.order, x.path.name))
        sorted_sets[setid] = {"order": [x.id6 for x in plist_sorted]}
    return {
        "schema_version": SCHEMA_VERSION,
        "plans": plans_dict,
        "sets": sorted_sets,
    }


def discover_plans(
    repo: Path,
    *,
    parse_plan_file: Callable[[Path, Path], Any],
) -> dict[str, Any]:
    """Scan the repository for all IPD files, returning id6 -> PlanRecord."""
    plans: dict[str, Any] = {}
    search_dirs = [
        repo / ".aw" / "records" / "plans",
        repo / ".agents" / "plans",
    ]
    seen: set[Path] = set()
    for sdir in search_dirs:
        if not sdir.exists():
            continue
        for path in sdir.rglob("*.md"):
            if path.name in {"README.md", "INDEX.md", "STATUS.md"}:
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            rec = parse_plan_file(resolved, repo)
            if rec:
                plans[rec.id6] = rec
    return plans


# ==================================================================================================
# revsweep-04 (`5slbpi`) E-05: CROSS-TYPE needs-review DISCOVERY (spec `6m4kow` R-15).
#
# WHAT WAS MISSING, precisely. `6ypimw` made the needs-review PREDICATE type-aware and said so at its
# own definition: "TYPE-AWARE BY SIGNATURE AND IPD-ONLY BY REACH ... NOTHING IN THE PACKAGE CAN
# CURRENTLY HAND IT ONE - `runner_shared.discover_plans` walks only the two plans trees ... That gap
# is real and is owned by `5slbpi`". This section closes exactly that gap and nothing wider: it
# supplies the SPECS ENUMERATION the predicate was shaped to consume. It does NOT touch the
# predicate's logic (that is `6ypimw`'s) and it does NOT register `--type` on either runner (that is
# `uyeko5`, which has not landed; verified: `grep '"--type"'` finds no registration in either driver).
#
# SO BE HONEST ABOUT REACH. After this change a CALLER passing `spec_type="spec"` resolves real specs.
# An OPERATOR typing `--type spec` still cannot, because the flag does not exist yet. Reporting the
# latter as working would be the false claim this comment exists to prevent.
#
# NO NEW PATH LITERAL. Enumeration goes through `check_engine._iter_spec_records`, the same iterator
# `check.review-dangling` and `check.from-spec-dangling` already use, exactly as `review_findings
# .review_dirs` deliberately routes through the record-path authority rather than hardcoding a second
# reviews path. A second "where do specs live" mechanism is the drift GUIDING_PRINCIPLES P8 forbids.
#
# WHY NOT `aw find specs --status` (`5slbpi` DECISION D4). Because it is BROKEN and silently so:
# `cli._find_type_records`'s "All other types" branch (`cli.py:8487-8512`) never consults
# `explicit_flags.status`, unlike the `plans` and `research` branches which both call a `query(...)`
# helper. Re-verified at implementation: `aw find specs --status draft`, `--status to-review`, and
# unfiltered `aw find specs` each return all 27 specs. This plan AVOIDS the filter rather than fixing
# it, because the fix lives in `cli.py` (outside this plan's Scope-Paths) and would change the
# behavior of seven record types at once.
# ==================================================================================================


class SpecRecord(NamedTuple):
    """The minimum a needs-review decision needs about ONE spec: its id, status, and path.

    Deliberately NOT the runner `PlanRecord`. That record carries plan-shaped fields (`kind`,
    `order`, `dependencies`) a spec does not have. A spec needs none of them: the dispatch table
    (`run_selection_policy._SPEC_ACTIONS`) keys on STATUS alone, so this record carries status and
    identity and stops there rather than inventing spec analogues of plan fields.

    CORRECTED BY rununify 06 (`sy7uwh`). This docstring used to add that the runner records were
    "per-runner NamedTuples" and that `discover_plans` injects `parse_plan_file` "precisely because
    the two runners' records disagree". Both halves are now FALSE: there is ONE `PlanRecord` above
    and ONE `parse_plan_file`, and the surviving injection parameter is vestigial (see the module
    docstring). The distinction this class draws is unaffected, because it was never about the split -
    it is about a spec having no plan fields.

    ``file`` is repo-relative POSIX, matching the `file` key a manifest plan entry carries, so the
    same terminal-directory exclusion in `run_selection_policy.needs_review` applies unchanged.
    """

    id6: str
    status: str
    file: str
    path: Path


def discover_specs(repo: Path) -> dict[str, SpecRecord]:
    """Scan the repository's specs tree(s), returning id6 -> :class:`SpecRecord`.

    The SPEC sibling of :func:`discover_plans`, and the piece `6ypimw` named as this plan's job. It
    takes NO injected parser, unlike `discover_plans`: there is one spec record shape (above) rather
    than two divergent per-runner ones, so there is nothing to inject.

    Identity and status are read through the SHARED authorities, not by fresh regexes:
    `check_engine._iter_spec_records` enumerates (no new path literal), `check_engine._ITEM_ID_RE`
    reads `- Id:`, and `selectors.read_front_matter_status` reads `- Status:`. That last one matters:
    it returns None for a MULTI-WORD status, so a legacy free-form status line yields no status rather
    than a mis-parsed token, and an item with no status is simply not swept.

    A spec with no `- Id:` is SKIPPED rather than keyed under an empty string. Without an id6 it
    cannot be named by a selector, cannot carry a review record (which joins on `Subject-Id`), and
    cannot be attested, so admitting it would put an unreviewable item in a review sweep.

    THAT SKIP IS NOT HYPOTHETICALLY SAFE, IT IS MEASURED SAFE, and the number is recorded here because
    a reader who sees "8 discovered" against "27 spec files" will otherwise assume a bug. At
    implementation, 19 of 27 specs carried no `- Id:`: every one is a PRE-CUTOVER legacy
    `YYYYMMDD-HHMM-NN-<slug>.spec.md` name that predates `check_engine.SPEC_ID6_CUTOVER_DATE`
    (`20260828`), which grandfathers exactly those. Verified that the skip costs no review coverage:
    all 19 sit at `implemented` (15), `approved` (1), `deferred` (2), or `superseded` (1), and asking
    `run_selection_policy.needs_review` about each returned False for ALL of them, so ZERO id-less
    specs would have been review-eligible even had they been admitted. A legacy spec that ever needs
    reviewing is converted first with `aw rename specs <legacy> --to-id6`, which is the documented
    forward path and mints the `- Id:` this function requires.

    Never raises: an absent or unreadable specs tree yields an empty dict, which is the fail-safe
    direction (nothing swept) rather than an exception inside selector expansion.
    """
    specs: dict[str, SpecRecord] = {}
    try:
        from agent_workflows import check_engine as _ce
        from agent_workflows import selectors as _sel
    except Exception:
        return specs

    root = Path(repo).resolve()
    try:
        records = list(_ce._iter_spec_records(Path(repo)))
    except Exception:
        return specs

    for path, text in records:
        m = _ce._ITEM_ID_RE.search(text)
        if not m:
            continue  # no id6 -> unnameable, unattestable; see docstring.
        id6 = m.group(1)
        if id6 in specs:
            continue  # first wins, matching `discover_plans`'s de-duplication by resolved path.
        status = (_sel.read_front_matter_status(text) or "").strip().lower()
        try:
            rel = str(path.resolve().relative_to(root)).replace("\\", "/")
        except (ValueError, OSError):
            rel = path.name
        specs[id6] = SpecRecord(id6=id6, status=status, file=rel, path=path)
    return specs


def sweep_review_candidates_for_type(
    repo: Path,
    spec_type: str,
    *,
    manifest: dict[str, Any] | None = None,
) -> list[str]:
    """The needs-review sweep for ONE artifact type. The type-scoped entry point (spec 2.4a).

    TYPE SCOPING IS NORMATIVE AND FIXED BY SPEC `25kzda` 2.4a PROPERTY 1: with no `--type`, `reviews`
    selects IPDs ONLY, and a type added later never joins the sweep implicitly. So this function
    requires ``spec_type`` EXPLICITLY and has no default: a defaulted parameter is precisely how a
    later caller would silently widen the default sweep. `sweep_review_candidates` remains the
    IPD-only entry point and is unchanged, so no existing caller's behavior moves.

    MEMBERSHIP IS STILL THE ONE PREDICATE. For `ipd` this delegates to the existing
    :func:`sweep_review_candidates` verbatim (same manifest walk, same Set ordering, same memoized
    decision), so this function adds no second copy of the IPD path. For `spec` it enumerates through
    :func:`discover_specs` and asks the SAME `run_selection_policy.needs_review`, so the sweep and
    the dispatch table agree BY CONSTRUCTION (spec `6m4kow` R-16) for specs exactly as they now do
    for plans.

    ``manifest`` is required for `ipd` (that path is manifest-driven) and IGNORED for `spec` (specs
    have no manifest; the tree is the source). Passing None for `ipd` yields an empty list rather
    than raising, matching the fail-safe posture of the rest of selector expansion.

    Returns id6s in deterministic order. The CALLER decides what an empty result means; spec 2.4a
    property 3 makes an empty `reviews` a success that exits 0.
    """
    from agent_workflows import run_selection_policy as _policy

    norm = (spec_type or "").strip().lower()
    if norm == "ipd":
        return sweep_review_candidates(manifest or {}, repo=repo)
    if norm != "spec":
        # An unknown type sweeps NOTHING rather than guessing a tree. Fail-safe, and it keeps this
        # function from becoming the place a new type is quietly admitted without amending the
        # dispatch table it must agree with.
        return []

    out: list[str] = []
    for id6, rec in sorted(discover_specs(repo).items(), key=lambda kv: kv[1].file):
        # No completeness input is supplied for a spec `draft`, so an undetermined draft is NOT swept
        # (`needs_review`'s documented fail-safe: `bool(None)` is False). The deterministic SPEC
        # completeness parser that spec `25kzda` 3.3 names does not exist yet; inventing a second
        # heuristic here would make the sweep and that future parser disagree about the same draft,
        # which is the exact defect `6ypimw` was written to remove. A spec at `to-review` - the case
        # this plan exists to serve - needs no completeness answer.
        if _policy.needs_review("spec", rec.status, file_path=rec.file):
            out.append(id6)
    return out


def resolve_plan_path(repo: Path, configured: str, id6: str) -> Path:
    from agent_workflows import selectors

    if id6:
        try:
            matched = selectors.resolve_selectors(repo, "plans", [id6])
            if len(matched) == 1 and matched[0].is_file():
                return matched[0].resolve()
        except Exception:
            pass

    if configured:
        direct = (repo / configured).resolve()
        if direct.is_file():
            return direct
    roots = [repo / ".aw" / "records" / "plans", repo / ".agents" / "plans", repo]
    matches: list[Path] = []
    for root in roots:
        if root.exists():
            matches.extend(
                path for path in root.rglob(f"*-{id6}-*.ipd.md") if path.is_file()
            )
    unique = sorted(set(matches))
    if len(unique) == 1:
        return unique[0].resolve()
    if not unique:
        raise DriverError(f"Cannot locate IPD {id6}; configured path was {configured}")
    raise DriverError(f"Ambiguous IPD {id6}: {', '.join(str(path) for path in unique)}")


def plan_bucket(path: Path) -> str | None:
    """Which lifecycle DIRECTORY is this plan path in? Returns the segment name, or None.

    A BUCKET IS A DIRECTORY; READINESS IS A FIELD. That distinction is the whole contract of this
    function and getting it wrong has already cost one defect (depreview 03ie04). In this layout a
    plan STAYS in `pending/` for its entire non-terminal life, moving through `- Status: draft` ->
    `to-review` -> `reviewed` -> `approved`, and only a TERMINAL state moves the file. So a caller
    that wants to know "is this plan reviewed/approved yet" CANNOT learn it here: it must read the
    `- Status:` front-matter field with `selectors.read_front_matter_status`. `oc_runipd.edge_satisfied`
    is the worked precedent, and the reason it had to change: it compared this function's result
    against `("executed", "reviewed", "approved")`, which made two thirds of that tuple DEAD CODE
    because every non-terminal plan buckets as `pending`.

    `reviewed`, `approved` and `active` ARE RECOGNIZED DEFENSIVELY AND DO NOT OCCUR IN THIS LAYOUT.
    `.aw/records/plans/` holds only `executed`, `not-executed`, `pending`, `reusable` and
    `superseded`, and `run_selection_policy.TERMINAL_DIRECTORY_SEGMENTS` corroborates that in code by
    naming exactly the four terminal ones (`executed`, `superseded`, `not-executed`, `reusable`) and
    neither `reviewed` nor `approved`. They are kept rather than removed because the members are
    PINNED by `tests/test_oc_runipd.py::PlanBucketRecognitionTests` and because two callers (each
    driver's `parse_plan_file`) consume the result AS a default status (`status = bucket or
    "to-review"`) rather than comparing it, so deleting a member would silently change a DERIVED
    STATUS rather than merely skip a comparison.

    This function does no IO and must not learn to: teaching a path inspector to read file contents
    would change the meaning of every one of its call sites (OQ-03).
    """
    parts = path.parts
    for bucket in (
        "executed",
        "active",
        "pending",
        "reviewed",
        "approved",
        "reusable",
        "superseded",
        "not-executed",
    ):
        if bucket in parts:
            return bucket
    return None


# --- dirtygates-03 (`9iq461`): the two facts a LANE-SIDE backlog close needs ---------------------
#
# WHY THESE LIVE HERE AND NOT IN `oc_runipd`. Both hosts perform the lane-side close, so a symbol
# defined in `oc_runipd` and imported by `agy_runipd` would deepen exactly the coupling backlog
# `cnwy8g` tracks and that `test_the_oc_to_agy_import_count_did_not_increase` measures. That guard
# states the rule plainly ("both hosts must reach it through runner_shared"), so these are defined in
# the shared module from the start rather than re-baselined later. They need nothing host-specific
# except `run_checked`, which is already injected here for the same reason.


def lane_executed_carrier_override(
    repo: Path,
    lane_repo: Path,
    item: Mapping[str, Any],
) -> dict[str, str]:
    """Map this item's own plan from the path MAIN shows it at to the path THE LANE shows it at.

    dirtygates-03 (`9iq461`) E-03. Returns `{}` for a non-isolated turn, for a turn whose plan cannot
    be resolved in either tree, or whenever the two views AGREE (nothing to override then, so the
    ordinary main-side read already answers correctly).

    THE ONE FACT THIS SUPPLIES is "the caller's own plan is terminal `executed`", which is true on the
    lane branch and not yet true in `repo` because the merge has not happened. Everything else about
    the verdict is still read from `repo`, which is what keeps the multi-carrier protection intact.
    Best-effort and never raising: an empty map can only ever WITHHOLD a close, the safe direction.

    NOTE THE DIFFERENCE BETWEEN THE TWO TREES IS A DIRECTORY DIFFERENCE, NOT A CONTENT ONE
    (`plan_bucket` is a pure path inspector and "does no IO and must not learn to"). So do NOT later
    "fix" this by reading file contents: the whole question is which lifecycle DIRECTORY the carrier
    file sits in within the tree being scanned.
    """
    if Path(lane_repo).resolve() == Path(repo).resolve():
        return {}
    configured = item.get("configured_file", "") or ""
    id6 = item.get("id6") or ""
    if not id6:
        return {}
    try:
        lane_plan = resolve_plan_path(Path(lane_repo), configured, id6)
    except (DriverError, OSError):
        return {}
    if plan_bucket(lane_plan) != "executed":
        # Nothing to assert: the lane does not show it executed either, so the ordinary read is right.
        return {}
    try:
        main_plan = resolve_plan_path(Path(repo), configured, id6)
    except (DriverError, OSError):
        return {}

    def _rel(path: Path, root: Path) -> str:
        try:
            return str(Path(path).resolve().relative_to(Path(root).resolve()))
        except ValueError:
            return str(path)

    main_rel = _rel(main_plan, repo)
    lane_rel = _rel(lane_plan, lane_repo)
    if main_rel == lane_rel:
        return {}
    return {main_rel: lane_rel}


def collect_lane_earned_paths(
    repo: Path, handle: Any, *, run_checked: Callable[..., str]
) -> list[str]:
    """The repo-relative paths a LANE BRANCH produced: `git diff --name-only <base>..<branch>`.

    dirtygates-03 (`9iq461`) E-03, and the fix for a hazard that plan's F-7 named but mis-diagnosed.

    F-7 SAID the earned-paths diff would fail or return nothing in main because the lane's commits
    live on the lane branch. MEASURED IN A SCRATCH REPO, BOTH HALVES OF THAT ARE WRONG AND ONE REAL
    PROBLEM IS LEFT. A linked worktree SHARES the object database and the ref namespace with its
    parent, so `git diff <sha>..<sha>` over lane commits resolves IDENTICALLY from either cwd (both
    printed the same path, rc=0); the cwd was never the problem. The real problem is the RANGE:
    `collect_earned_paths` diffs the ATTEMPT's `starting_head..ending_head`, and both of those are
    `git_head(repo)` -- MAIN's HEAD, sampled before and after the turn. For an isolated turn main's
    HEAD does not move, so that range is `X..X`, which is EMPTY (measured). Nothing in it fails
    loudly; the earned set is simply empty, and since the earned gate can only ever WITHHOLD a close,
    the result would be a close that silently NEVER happens. So the fix is to name the range that
    holds the work, which is the lane's `base_commit..branch`.

    ``run_checked`` is INJECTED for the reason this module's docstring gives: the shared `run_checked`
    takes a host-specific `env_builder`, so this body cannot resolve a module-level one. Do NOT
    "simplify" it onto `_run_git`: that would stop a failed `git diff` raising and would make an
    UNPARSEABLE range indistinguishable from an empty one.

    Best-effort and never raising, exactly like `collect_earned_paths`: an empty result withholds a
    close rather than manufacturing one.
    """
    base = getattr(handle, "base_commit", None)
    branch = getattr(handle, "branch", None)
    if not base or not branch:
        return []
    try:
        out = run_checked(
            ["git", "diff", "--name-only", f"{base}..{branch}"], cwd=Path(repo)
        )
    except (DriverError, OSError):
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def describe_unresolved_plan_selector(repo: Path | None, sel_str: str) -> str:
    """Provide an informative, context-aware error message when a plan selector cannot be resolved."""
    r = repo or Path(".")
    try:
        from agent_workflows import selectors

        for rtype in selectors.KNOWN_PRIMARY_TYPES:
            if rtype == "plans":
                continue
            res = selectors.resolve(r, rtype, sel_str)
            if res.is_match:
                rel_paths = []
                for p in res.paths:
                    try:
                        rel_paths.append(str(p.resolve().relative_to(r.resolve())))
                    except ValueError:
                        rel_paths.append(str(p))
                joined_paths = ", ".join(rel_paths)
                type_label = {
                    "backlog": "backlog item",
                    "specs": "spec",
                    "research": "research document",
                    "releases": "release record",
                    "walkthroughs": "walkthrough",
                    "roadmaps": "roadmap document",
                    "prompts": "prompt document",
                    "comms": "comms message",
                }.get(rtype, f"{rtype} record")
                return (
                    f"'{sel_str}' is a {type_label} ({joined_paths}), not an IPD plan."
                )
    except Exception:
        pass

    fc = Path(sel_str)
    rfc = r / sel_str if not fc.is_absolute() else fc
    if fc.is_file() or rfc.is_file():
        target = fc if fc.is_file() else rfc
        try:
            rel_target = str(target.resolve().relative_to(r.resolve()))
        except ValueError:
            rel_target = str(target)
        return (
            f"File '{sel_str}' exists ({rel_target}) but is not a valid IPD plan "
            "(missing front-matter or invalid format)."
        )
    if "/" in sel_str or "\\" in sel_str or sel_str.endswith(".md"):
        return f"Plan file not found: '{sel_str}'"

    if ID6_RE.fullmatch(sel_str):
        return f"No IPD plan found with id6 '{sel_str}' under .aw/records/plans/."

    return f"No IPD plan, Set, or file matching '{sel_str}' found under .aw/records/plans/."


# ==================================================================================================
# revsweep-02 (`6ypimw`) E-02: THE `reviews` SWEEP'S MEMBERSHIP, ONCE (spec 25kzda 2.4a property 2)
# ==================================================================================================
#
# WHAT THIS REPLACES. Each host runner's `expand_selectors` carried its OWN `_needs_review` closure,
# and the two were VERBATIM duplicates (they diffed to one hunk: a `setid`/`_setid` loop variable).
# Both tested `status == "to-review"`, while `determine_action` routed `to-review` AND `draft` to
# `review`, so the sweep and the router disagreed and a complete draft named EXPLICITLY was reviewed
# while the SAME draft was silently absent from the sweep. Two copies is what made the divergence
# survivable: a one-sided fix leaves the other host wrong.
#
# THE POLICY IS NOT HERE. `run_selection_policy.needs_review` decides; this function only ASSEMBLES
# the inputs that predicate cannot see, because it is pure by design and the manifest cannot answer
# authoring completeness.
#
# WHY THE FILE READ IS HERE AND WHY IT IS BOUNDED. `build_dynamic_manifest` stores only `set`, `file`,
# `status`, `order`, `dependencies`, `kind`, and `from_backlog` - no plan TEXT - while
# `ipd_authoring.authoring_placeholders_resolved` needs text. So the CALLER must read it, and reads
# ONLY the `draft`-status candidates the dispatch table says need the answer (asked through
# `review_depends_on_completeness`, so the "which rows need content" rule stays in one place too).
# Every other status is answered by the table alone and costs no I/O.
#
# IT FAILS SAFE, WHICH IS THE HALF THAT MATTERS. `expand_selectors`'s `repo` is `Path | None = None`
# and the sweep branch never used it, so an absent repo or an unreadable file must yield "not swept"
# rather than crashing or optimistically including. An optimistic include would sweep an incomplete
# stub into a review turn, which is exactly what spec 3.2's draft split exists to prevent.


#: The STATUS selector spellings both hosts accept. Named once so the sweep branch, the draft gate's
#: applicability test, and any future status selector cannot drift apart.
STATUS_SELECTOR_TOKENS: frozenset = frozenset({"reviews", "review", "to-review", "all"})

#: The subset that is the needs-review sweep specifically (spec 2.4a: "`review` and `to-review` are
#: accepted spellings of `reviews`").
REVIEW_SELECTOR_TOKENS: frozenset = frozenset({"reviews", "review", "to-review"})


def is_status_selector(selectors: Any) -> bool:
    """True when the selection was reached through a STATUS selector rather than a named item.

    THIS IS WHAT MAKES SPEC 2.5a's BULLET 2 REAL: "a draft named EXPLICITLY by path or id6 is admitted
    without gating. The operator named it; asking is noise." Only the status sweeps (`reviews`, `all`)
    admit a draft the operator did not name, so only they are gated. Derived from the SAME token set
    the sweep branches match on, so the gate cannot apply to a spelling the sweep does not accept (or
    fail to apply to one it does).
    """

    tokens = [str(s).strip().lower() for s in (selectors or [])]
    return len(tokens) == 1 and tokens[0] in STATUS_SELECTOR_TOKENS


def is_review_selector(selectors: Any) -> bool:
    """True for the needs-review sweep specifically (`reviews`/`review`/`to-review`), not `all`.

    The two status selectors differ in what an EMPTY result MEANS: spec 2.4a property 3 makes an empty
    `reviews` a SUCCESS that exits 0 ("a repository with nothing awaiting review is the healthy
    state"), while `all` has always raised the plain error that exits 2. Keeping them distinguishable
    is what lets the draft gate empty a selection without silently changing `all`'s exit code.
    """

    tokens = [str(s).strip().lower() for s in (selectors or [])]
    return len(tokens) == 1 and tokens[0] in REVIEW_SELECTOR_TOKENS


def plan_authoring_complete(repo: Path | None, rel_or_abs_file: str) -> bool | None:
    """The deterministic authoring-completeness answer for ONE plan file, or `None` if unknowable.

    CONSUMES `ipd_authoring.authoring_placeholders_resolved`, the shipped anchored check that the
    `check.ipd-draft-ready-to-review` rule already uses; a second heuristic here would let the nudge
    and the sweep disagree about the same draft.

    `None` (not `False`) when the repo is absent or the file cannot be read, so a caller can tell
    "incomplete" from "not determined". Both exclude, but only one is a fact about the plan.
    """

    if repo is None or not str(rel_or_abs_file or "").strip():
        return None
    try:
        from agent_workflows import ipd_authoring

        path = Path(rel_or_abs_file)
        if not path.is_absolute():
            path = Path(repo) / path
        return ipd_authoring.authoring_placeholders_resolved(
            path.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError):
        return None


def manifest_entry_needs_review(
    plan_info: dict[str, Any],
    *,
    repo: Path | None = None,
    spec_type: str = "ipd",
) -> bool:
    """Whether ONE manifest plan entry is in the `reviews` sweep. THE single membership test.

    ``spec_type`` is threaded through to the pure predicate rather than hardcoded at its call, so
    widening discovery to specs (`5slbpi`) does not have to reopen this function. It defaults to
    `"ipd"` because that is all `discover_plans` can produce today.
    """

    from agent_workflows import run_selection_policy as _policy

    status = str(plan_info.get("status", "")).lower().strip()
    file_str = str(plan_info.get("file", ""))
    complete: bool | None = None
    if _policy.review_depends_on_completeness(spec_type, status):
        # The ONLY branch that touches the filesystem, and only for the rows the table says need it.
        complete = plan_authoring_complete(repo, file_str)
    return _policy.needs_review(
        spec_type,
        status,
        authoring_complete=complete,
        file_path=file_str,
    )


def sweep_review_candidates(
    manifest: dict[str, Any],
    *,
    repo: Path | None = None,
) -> list[str]:
    """The `reviews` sweep, in manifest Set order then standalone order. Shared by both hosts.

    Returns the id6 list; the CALLER decides what an empty result means (both hosts raise
    `EmptyStatusSelection`, which spec 2.4a property 3 makes a success that exits 0).
    """

    plans = manifest.get("plans", {})
    sets = manifest.get("sets", {})
    expanded: list[str] = []
    seen: set[str] = set()
    # DECIDED ONCE PER PLAN, memoized, because the two walks below visit a set member twice and the
    # decision can involve a FILE READ (the draft rows). Without this a repository with N drafts pays
    # 2N reads for N answers, and the answers could in principle differ if the file changed between
    # them - a selection that is not even self-consistent.
    decided: dict[str, bool] = {}

    def _needs(id6: str) -> bool:
        if id6 not in decided:
            decided[id6] = manifest_entry_needs_review(plans.get(id6, {}), repo=repo)
        return decided[id6]

    # 1. Walk sets in manifest in defined order.
    for _setid, group in sets.items():
        for id6 in group.get("order", []):
            if id6 in seen:
                continue
            if _needs(id6):
                expanded.append(id6)
                seen.add(id6)

    # 2. Standalone plans in manifest.
    for id6 in plans:
        if id6 in seen:
            continue
        if _needs(id6):
            expanded.append(id6)
            seen.add(id6)

    return expanded


def sweep_draft_candidates(
    manifest: dict[str, Any],
    *,
    repo: Path | None = None,
    spec_type: str = "ipd",
) -> list[Any]:
    """Every `draft` item a STATUS selector can REACH, each with its completeness answer.

    The input to spec 2.5a's admission gate (`run_selection_policy.decide_draft_admission`). Built
    here rather than in the pure module for the same reason the completeness read is: it needs the
    manifest and the filesystem.

    SCOPED TO THE MANIFEST, NOT TO THE RESOLVED QUEUE, and that distinction is the subtle one. An
    INCOMPLETE draft is deliberately NOT a member of the `reviews` sweep (the dispatch table skips it),
    so it never appears in the resolved queue - yet spec 2.5a REQUIRES it to be reported: its preview
    ends "Also skipping 1 incomplete draft (findings will be reported)", and bullet 1 makes the skip a
    findings report rather than silence. Gathering candidates from the resolved queue would drop
    exactly the items the operator most needs told about. This is only ever called for a status
    selector, which sweeps the whole repository, so the manifest IS the reachable set.

    Terminal-directory entries are excluded: a `draft` status inside `executed/` is a
    directory/status mismatch, which spec 3.2 makes a red abort rather than an admission question.
    """

    from agent_workflows import run_selection_policy as _policy

    candidates: list[Any] = []
    for id6, info in manifest.get("plans", {}).items():
        status = str(info.get("status", "")).lower().strip()
        if not _policy.review_depends_on_completeness(spec_type, status):
            continue
        file_str = str(info.get("file", ""))
        if _policy.is_in_terminal_directory(file_str):
            continue
        candidates.append(
            _policy.DraftCandidate(
                identity=id6,
                spec_type=spec_type,
                complete=plan_authoring_complete(repo, file_str),
            )
        )
    return sorted(candidates, key=lambda c: c.identity)


def validate_manifest(
    manifest: dict[str, Any],
    *,
    parse_dependency_token: Callable[[str], Any],
) -> None:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise DriverError("Unsupported manifest schema_version")
    plans = manifest.get("plans")
    sets = manifest.get("sets")
    if not isinstance(plans, dict) or not isinstance(sets, dict):
        raise DriverError("Manifest must contain object-valued 'plans' and 'sets'")
    for id6, plan in plans.items():
        if not ID6_RE.fullmatch(id6):
            raise DriverError(f"Invalid id6 in manifest: {id6}")
        if not isinstance(plan, dict) or not plan.get("file") or not plan.get("set"):
            raise DriverError(f"Plan {id6} requires file and set")
        dependencies = plan.get("dependencies", [])
        if not isinstance(dependencies, list):
            raise DriverError(f"Plan {id6} dependencies must be a list")
        # 8guhs0 E-01: a dependency token is a SHARED-grammar typed edge (or a bare id6 in a legacy
        # hand-written manifest, normalized to `executed:`). Only IPD-typed targets must name a plan
        # in the manifest; a `spec`/`backlog` target is a graph LEAF (spec 25kzda 2.10) and is
        # resolved against the repository, not the queue.
        malformed = [dep for dep in dependencies if parse_dependency_token(dep) is None]
        if malformed:
            raise DriverError(
                f"Plan {id6} has malformed Item-Dependencies edges: {malformed}"
            )
        unknown = []
        for dep in dependencies:
            edge = parse_dependency_token(dep)
            if edge.target_type == "ipd" and edge.id6 not in plans:
                unknown.append(dep)
        if unknown:
            raise DriverError(f"Plan {id6} has unknown dependencies: {unknown}")
    for setid, group in sets.items():
        if not isinstance(group, dict) or not isinstance(group.get("order"), list):
            raise DriverError(f"Set {setid} requires an order list")
        unknown = [id6 for id6 in group["order"] if id6 not in plans]
        if unknown:
            raise DriverError(f"Set {setid} contains unknown plans: {unknown}")
        wrong = [id6 for id6 in group["order"] if plans[id6]["set"] != setid]
        if wrong:
            raise DriverError(f"Set {setid} contains plans assigned elsewhere: {wrong}")


# ==================================================================================================
# SPEC 25kzda 2.1: THE RUN POLICY FLAG SURFACE (runflags-01, `uyeko5`)
# ==================================================================================================
#
# WHAT THIS SECTION FIXES. Spec `25kzda` 2.1 declares `aw <host> run`'s invocation surface as a closed
# flag list. Measured at HEAD `bd91909e`, SEVEN of its eight policy flags were unreachable from either
# runner's command line: only `--full-auto` was registered. Two of the seven (`--allow-mixed`,
# `--unattended`) had WORKING policy behind them with no flag to reach it, which is worse than a
# missing feature - `run_selection_policy.decide` had ZERO callers anywhere in the package, so the
# entire mixed-type gate executed plan `6lu3rq` built and tested was DEAD CODE.
#
# THE ONE PRINCIPLE HERE: THIS MODULE CREATES NO POLICY. Where a predicate already ships it is CALLED
# (`run_selection_policy.decide`, `run_evidence.aggregate_run_exit`, `run_recovery.validate_retry_budget`);
# where none ships, the flag is registered and REFUSES HONESTLY rather than silently accepting. A flag
# that parses and silently does nothing is strictly WORSE than no flag, because the operator believes
# a policy was applied when it was not, which is a correctness failure and not a UX one.
#
# WHY THE FLAG LIST IS DATA AND NOT EIGHT `add_argument` CALLS. The recurring failure this section
# exists to end is not "a flag is missing", it is "the documented contract and the shipped command
# drifted and nothing noticed". A hand-written registration per flag reproduces that: the ninth flag
# the spec grows is added to the spec, not to two parsers, and no test fails. Driving registration
# AND the contract test from ONE table makes the drift a test failure instead of an archaeology
# project.


class RunPolicyFlag(NamedTuple):
    """One row of spec 25kzda 2.1's policy flag list.

    Fields:
      * ``flag``        - the exact operator-facing spelling (what the spec declares).
      * ``dest``        - the argparse destination, hence the run-state option key.
      * ``kind``        - ``"bool"`` (a `BooleanOptionalAction`, matching shipped `--full-auto`),
                          ``"int"``, or ``"choice"`` (a closed string vocabulary carried in
                          ``choices``). ``"choice"`` arrived with integpath-03's
                          `--on-integration-blocked`, whose value SELECTS A POLICY rather than
                          toggling one, so argparse must reject an unrecognized spelling at parse
                          time instead of leaving a typo to be discovered mid-run.
      * ``implemented`` - whether the flag's BEHAVIOR ships. False means registered-and-refusing:
                          the flag parses, appears in `--help`, and REFUSES with `not yet
                          implemented`. Carried as data so the contract test can assert the refusal
                          rather than trusting the help text.
      * ``owner``       - the artifact that owns the behavior, named in the refusal so an operator
                          who hits it can find the work item rather than filing a duplicate.
      * ``help``        - the `--help` text. Where the shipped semantics DIVERGE from the spec (an
                          unimplemented flag, or `--retry-budget`'s missing repository-policy tier),
                          the divergence is stated HERE, because an operator reads `--help` and never
                          reads an IPD.
      * ``freeze``      - whether the value is frozen into run state at queue build.
      * ``resume_rule`` - ``"refuse"`` (spec `:131` freezes the value, so passing it with `resume` is
                          an error) or ``"none-default"`` (re-declared with ``default=None`` so an
                          OMITTED flag cannot clobber the frozen value; the shipped `--full-auto`
                          pattern).
    """

    flag: str
    dest: str
    kind: str
    implemented: bool
    owner: str
    help: str
    freeze: bool = True
    resume_rule: str = "none-default"
    #: The closed vocabulary for a ``kind="choice"`` row; empty for every other kind. Carried as DATA
    #: for this table's founding reason: a vocabulary spelled at the `add_argument` call instead would
    #: have to be repeated on both hosts' parsers, which is the duplication this table exists to end.
    choices: tuple = ()


#: The `resume` re-declaration rules, named rather than spelled inline at each comparison.
RESUME_REFUSE = "refuse"
RESUME_NONE_DEFAULT = "none-default"

#: Spec 25kzda 2.1's policy flags, in the order the spec's grammar block lists them.
#:
#: `--allow-drafts` JOINED THIS TABLE with `revsweep-02` (`6ypimw`), which implemented spec 2.5a's
#: draft admission gate. `uyeko5` deliberately left it out (it owned the other eight and registering a
#: ninth as a refusal would have collided on these lines for no gain); it is registered here now that
#: its BEHAVIOR ships, which is this table's own rule - a flag never parses and silently does nothing.
#:
#: `--allow-dirty-base` JOINED with dirtybase Order 01 (`3i0aaz`), which added the dirty-base refusal
#: on the shared-tree path and therefore needed the CONSENT half in the same change: shipping a
#: refusal with no sanctioned override is how an operator learns to work around a gate instead of
#: through it. Spec 2.1 declares it in the same commit, because `tests/test_run_flag_surface.py` reads
#: the spec FILE in BOTH directions and a row here that 2.1 does not declare fails the suite.
#:
#: THE COUNT IS DELIBERATELY NOT STATED. It said "NINE" and was already one edit behind by the time a
#: tenth arrived; the contract test derives the expected set from the spec for exactly this reason.
RUN_POLICY_FLAGS: tuple = (
    RunPolicyFlag(
        flag="--allow-mixed",
        dest="allow_mixed",
        kind="bool",
        implemented=True,
        owner="run_selection_policy.decide",
        help=(
            "Acknowledge that the selection spans MORE THAN ONE work-item type, unattended. "
            "Acknowledges type mixing ONLY: every status, approval, prompt-verifiability, scope, "
            "and safety gate still applies"
        ),
    ),
    RunPolicyFlag(
        flag="--allow-drafts",
        dest="allow_drafts",
        kind="bool",
        implemented=True,
        owner="run_selection_policy.decide_draft_admission",
        help=(
            "Admit COMPLETE draft items reached through a status selector (`reviews`/`all`), "
            "promoting them to 'to-review' and reviewing them in this run. It CANNOT admit an "
            "INCOMPLETE draft: a draft that fails the deterministic authoring-completeness check is "
            "skipped with findings at every setting of this flag. It waives no other gate - a "
            "promoted draft still faces the approval gate. A draft named EXPLICITLY by id6 or path "
            "needs no flag"
        ),
    ),
    RunPolicyFlag(
        flag="--unattended",
        dest="unattended",
        kind="bool",
        implemented=True,
        owner="run_selection_policy.decide",
        help=(
            "Declare that NO interactive answer channel is available, so a gate that would prompt "
            "refuses instead of waiting. Implied by --full-auto"
        ),
    ),
    RunPolicyFlag(
        flag="--full-auto",
        dest="full_auto",
        kind="bool",
        implemented=True,
        owner="plan_readiness.is_plan_review_approved",
        help=(
            "Clear a plan that is already 'Status: reviewed' to 'auto-approved' and execute it "
            "immediately. The decision reads the plan's structured '- Readiness:' field "
            "(go|go-pending-approval clears; no-go, an unrecognized value, or an absent field with "
            "no approving review verdict does not). This records an AUTOMATED clear, NOT human "
            "approval: no --by-human attestation is asserted. Implies --unattended"
        ),
    ),
    RunPolicyFlag(
        flag="--allow-unverifiable",
        dest="allow_unverifiable",
        kind="bool",
        implemented=True,
        owner="run_evidence.aggregate_run_exit",
        help=(
            "Admit contractless prompts (a prompt with no parseable run contract), whose "
            "verification stays 'unavailable'. This is the ADMISSION --unverifiable-ok requires; it "
            "does not by itself make such an item aggregate-neutral"
        ),
    ),
    RunPolicyFlag(
        flag="--unverifiable-ok",
        dest="unverifiable_ok",
        kind="bool",
        implemented=True,
        owner="run_evidence.aggregate_run_exit",
        help=(
            "Treat an acknowledged, completed contractless prompt as NEUTRAL for the aggregate exit "
            "code, without relabeling it verified. LEGAL ONLY with --allow-unverifiable (or the "
            "interactive `run unverifiable` confirmation); passed alone it is refused"
        ),
    ),
    RunPolicyFlag(
        flag="--follow-generated",
        dest="follow_generated",
        kind="bool",
        implemented=False,
        owner="backlog x8diyb (rundepflags-01)",
        help=(
            "NOT YET IMPLEMENTED (refuses; backlog x8diyb owns the behavior). Would add newly "
            "generated IPDs to THIS frozen run as child queue entries instead of reporting them as "
            "generated next actions"
        ),
    ),
    RunPolicyFlag(
        flag="--with-dependencies",
        dest="with_dependencies",
        kind="bool",
        implemented=False,
        owner="backlog x8diyb (rundepflags-01)",
        help=(
            "NOT YET IMPLEMENTED (refuses; backlog x8diyb owns the behavior). Would expand the "
            "selection to the transitive declared dependency closure BEFORE the queue is frozen, "
            "subjecting any newly introduced type to the mixed-type gate"
        ),
    ),
    RunPolicyFlag(
        flag="--retry-budget",
        dest="retry_budget",
        kind="int",
        implemented=True,
        owner="run_recovery.validate_retry_budget",
        help=(
            "Automatic correction attempts after the initial attempt, an integer 0..10 inclusive "
            "(0 means no retries). The CLI value overrides the default of 2. NOTE: spec 2.1's "
            "MIDDLE precedence tier (repository policy) is NOT IMPLEMENTED - no repository-policy "
            "home exists yet (backlog dh3us4) - so precedence today is CLI over default. Cannot be "
            "changed on --resume: the frozen value stands"
        ),
        resume_rule=RESUME_REFUSE,
    ),
    RunPolicyFlag(
        flag="--allow-dirty-base",
        dest="allow_dirty_base",
        kind="bool",
        implemented=True,
        owner="runner_shared.clean_base_launch_decision",
        help=(
            "Acknowledge that the target checkout has uncommitted changes to TRACKED files and "
            "launch anyway. Without it, such a base is REFUSED before anything is spawned, naming "
            "the paths. Consent covers this run's base ONLY: the approval, scope, and V-evidence "
            "gates still apply, and a lane whose changed files OVERLAP a dirty path is still "
            "refused at integration. It does not apply to UNTRACKED content, which is reported at "
            "run start and refuses on nothing, and it does not silence that report"
        ),
    ),
    # integpath-03 (`51vw4y`) E-02/E-05: the integration deferral ladder's two flags. They are in
    # THIS table, and not on each host's parser, on the maintainer's 2026-09-07 OQ-04 ruling: the
    # shared spec-governed table is what stops the two hosts diverging, which is the failure
    # `--full-auto` already demonstrated (default `False` on one host, `True` on the other). Spec
    # `25kzda` 2.1 was amended to DECLARE both in the same change that registers them here, because
    # `tests/test_run_flag_surface.py` reads that section as a FILE in BOTH directions.
    RunPolicyFlag(
        flag="--integration-retry-limit",
        dest="integration_retry_limit",
        kind="int",
        implemented=True,
        owner="runner_shared.decide_integration_deferral",
        help=(
            "Integration RE-ATTEMPTS allowed for a lane refused because main holds un-owned dirty "
            "paths overlapping the incoming change, a non-negative integer defaulting to 10. THIS "
            "IS NOT --retry-budget: that counts paid agent correction turns and is bounded 0..10; "
            "this counts integration re-attempts, is not bounded by that range, and neither moves "
            "the other. Repetition genuinely can succeed here, because the blocker is another "
            "writer's transient uncommitted file, and each re-attempt costs one git status plus one "
            "git merge-tree and no agent turn. Every re-attempt runs the full merge-and-revalidate "
            "gate. Cannot be changed on --resume: the frozen value stands"
        ),
        resume_rule=RESUME_REFUSE,
    ),
    RunPolicyFlag(
        flag="--on-integration-blocked",
        dest="on_integration_blocked",
        kind="choice",
        implemented=True,
        owner="runner_shared.decide_integration_deferral",
        help=(
            "What to do when an integration is refused because main holds un-owned dirty paths "
            "overlapping the incoming change. 'defer' (the default) re-attempts while other work "
            "remains, then polls, then asks, then goes terminal; 'poll' starts at the bounded poll; "
            "'ask' starts at the bounded question; 'block' REPRODUCES THE PREVIOUS BEHAVIOR exactly, "
            "marking the item terminal integration-blocked on the first refusal. No setting "
            "integrates over a contaminated base, and none stashes, resets, or cleans another "
            "writer's work. The ask is suppressed with no TTY or under --unattended, and carries its "
            "own timeout, so no setting can wait indefinitely"
        ),
        choices=ON_INTEGRATION_BLOCKED_CHOICES,
    ),
)

#: `{flag: RunPolicyFlag}`, for a caller that has a spelling and wants the row.
RUN_POLICY_FLAGS_BY_FLAG: dict = {row.flag: row for row in RUN_POLICY_FLAGS}

#: `{dest: RunPolicyFlag}`, for a caller reading an `argparse.Namespace` or a frozen options dict.
RUN_POLICY_FLAGS_BY_DEST: dict = {row.dest: row for row in RUN_POLICY_FLAGS}

#: Spec 2.1's default retry budget. NOT a second definition of the value: it is read FROM
#: `run_recovery.DEFAULT_RETRY_LIMIT` at call time (see `resolve_retry_budget`), and this name exists
#: only so a reader of this section knows where the number lives.
RETRY_BUDGET_OWNER = "run_recovery.DEFAULT_RETRY_LIMIT"


class RunFlagRefusal(DriverError):
    """A run flag was passed that cannot be honored, with WHY and WHO owns the missing half.

    A `DriverError` subclass and not a new exception hierarchy, because both runners' `main` already
    catches `DriverError`, prints it, and exits 2 without touching durable state. That is exactly the
    behavior a refused flag needs: fail before any run directory, session, or lease exists.
    """


def register_run_policy_flags(
    parser: Any,
    *,
    resume: bool = False,
    skip: Any = (),
) -> None:
    """Register spec 2.1's policy flags on ONE parser, from :data:`RUN_POLICY_FLAGS` as data.

    ``resume=False`` is the `run`/`start` parser: each flag carries its real default (``False`` for a
    bool, ``None`` for `--retry-budget`, meaning "not supplied" so the default tier can apply).

    ``resume=True`` is the `resume` parser, and every flag is re-declared with ``default=None``. That
    is the SHIPPED `--full-auto` pattern and it exists so an OMITTED flag cannot clobber a frozen
    value: `resume` cannot distinguish "the operator passed `--no-allow-mixed`" from "the operator
    passed nothing" if the default is `False`. A flag whose ``resume_rule`` is :data:`RESUME_REFUSE`
    is still REGISTERED on `resume`, deliberately: refusing it needs argparse to accept it first, so
    that `aw oc run resume <id> --retry-budget 5` fails with the spec's reason rather than argparse's
    `unrecognized arguments`, which would tell the operator the flag does not exist.

    ``skip`` names dests this caller registers itself. It exists for `--full-auto`, whose long help
    text and BooleanOptionalAction both runners already declare; passing it through here would be a
    second registration and argparse would raise. Every skipped dest must still BE in the table, so
    the contract test can prove it is registered by SOMEONE.
    """

    import argparse as _argparse

    skipped = set(skip)
    unknown = skipped - set(RUN_POLICY_FLAGS_BY_DEST)
    if unknown:
        raise ValueError(
            "register_run_policy_flags(skip=...) names dests that are not spec 2.1 flags: "
            f"{sorted(unknown)}"
        )
    for row in RUN_POLICY_FLAGS:
        if row.dest in skipped:
            continue
        if row.kind == "bool":
            parser.add_argument(
                row.flag,
                dest=row.dest,
                action=_argparse.BooleanOptionalAction,
                default=None if resume else False,
                help=row.help,
            )
        elif row.kind == "int":
            parser.add_argument(
                row.flag,
                dest=row.dest,
                type=int,
                default=None,
                metavar="N",
                help=row.help,
            )
        elif row.kind == "choice":
            # `default=None` on BOTH parsers, not only on `resume`. For a choice flag `None` means
            # "the operator said nothing", which is what lets the resolver apply the documented
            # default in ONE place (`resolve_on_integration_blocked`) rather than argparse baking a
            # second copy of it into two parsers.
            parser.add_argument(
                row.flag,
                dest=row.dest,
                choices=list(row.choices),
                default=None,
                help=row.help,
            )
        else:  # pragma: no cover - the table is closed; a new kind is a programming error
            raise ValueError(
                f"unknown run policy flag kind {row.kind!r} for {row.flag}"
            )


def resolve_retry_budget(cli_value: Any) -> int:
    """Spec 2.1's retry-budget precedence, and the ONE place the range bound is reached.

    Precedence per spec 2.1 is CLI > repository policy > default 2. The MIDDLE TIER IS NOT
    IMPLEMENTED and is not faked here: no repository-policy home exists (backlog `dh3us4` tracks it),
    so this resolves CLI-over-default and the gap is stated in `--retry-budget`'s own `--help` rather
    than left for an operator to discover.

    The 0..10 bound is `run_recovery.validate_retry_budget`'s, CALLED and never re-checked here:
    executed plan `sq61qd` made that the single definition of the bound precisely so the flag layer
    could reach it at PARSE time, when no `RunEngine` and no step exist. A second comparison here is
    the off-by-one that gets fixed in one place.
    """

    from agent_workflows import run_recovery

    if cli_value is None:
        return run_recovery.DEFAULT_RETRY_LIMIT
    try:
        return run_recovery.validate_retry_budget(cli_value)
    except run_recovery.InvalidRetryBudgetError as exc:
        raise RunFlagRefusal(f"--retry-budget: {exc}") from exc


def refuse_unimplemented_run_flags(args: Any) -> None:
    """REFUSE any flag whose behavior does not ship (`implemented=False`), before anything happens.

    Called from `initialize_run` before the run directory exists, so a refusal leaves nothing durable
    behind - the same "No work started" property the mixed-type refusal has, for the same reason.

    This is the honest end state for `--follow-generated` and `--with-dependencies`, whose behavior
    nobody has built. The alternative that must never be chosen is accepting them as silent no-ops:
    an operator who passes `--with-dependencies` and gets no closure expansion has been told a
    falsehood about what the run enforced.
    """

    for row in RUN_POLICY_FLAGS:
        if row.implemented:
            continue
        if getattr(args, row.dest, None):
            raise RunFlagRefusal(
                f"{row.flag} is not yet implemented: {row.owner} owns the behavior. "
                f"The flag is registered so it fails HERE, loudly, rather than parsing and "
                f"silently doing nothing"
            )


# ---- dirtybase Order 01 (`3i0aaz`): the dirty-base cases a LANE guard cannot reach ----------------
#
# THREE QUESTIONS ABOUT A DIRTY TREE ARE ASKED IN THIS REPOSITORY, and confusing any two of them is
# the failure this section exists to prevent. They are listed once, here, because the distinction is
# what makes each one's scope defensible:
#
#   1. INTEGRATION TIME, RELATIVE (`dirty_tree_overlap` above): does an INCOMING lane's
#      `changed_files` INTERSECT main's dirty paths, i.e. would merging clobber an un-owned edit?
#      Answered only after a lane's work exists. Empty when the sets are disjoint.
#   2. PER ITEM, PRE-LAUNCH, TRACKED ONLY (`lane_containment.evaluate_clean_base`, plan `nna8yz`
#      E-05): is the TRACKED tree clean, i.e. is HEAD a complete base? REFUSES. Runs once per queue
#      entry, inside `execute_item`.
#   3. ONCE PER RUN, UNTRACKED (`evaluate_untracked_dirt` below): what UNTRACKED content is sitting
#      in the tree the operator is about to spend hours against? REPORTS, and deliberately does not
#      refuse.
#
# WHY (3) REPORTS RATHER THAN REFUSING, since the asymmetry looks like an oversight and is not.
# Refusing on untracked content would make an unattended run unstartable in essentially any working
# checkout (`evaluate_clean_base`'s own docstring says so, and `tests/test_lane_clean_base.py
# ::test_case_3_an_untracked_file_does_NOT_refuse` pins it), and a gate that false-positives on
# correct behavior trains operators to bypass it. The measured incident is the other half: a stray
# `aw install` wrote 130+ uncommitted, largely UNTRACKED files into a working tree and on at least two
# occasions an agent did not realize the pollution was its own. Reporting puts that in front of the
# operator before any spend without making the run unstartable.


#: `git status` arguments for the once-per-run untracked report.
#:
#: `--untracked-files=all` IS LOAD-BEARING and is not a stylistic preference. Git's DEFAULT porcelain
#: collapses an untracked DIRECTORY to a single directory entry, so the 130-file `aw install` case
#: would report as a handful of directory names and hide exactly the scale this report exists to
#: surface. This repository has already been bitten by that default elsewhere and says so.
UNTRACKED_REPORT_STATUS_ARGS = ("status", "--porcelain", "--untracked-files=all")

#: How many untracked paths the report ENUMERATES before it stops and states the total instead.
#:
#: Bounded because a 130-path wall of text at 05:00 is the unread log this report is replacing. The
#: TOTAL is always stated exactly; only the enumeration is sampled.
UNTRACKED_REPORT_SAMPLE_LIMIT = 12


class UntrackedDirtReport(NamedTuple):
    """What UNTRACKED content a checkout holds at run start (dirtybase `3i0aaz` E-02)."""

    total: int
    sample: tuple[str, ...]

    @property
    def clean(self) -> bool:
        return self.total == 0

    @property
    def notice(self) -> str:
        """The operator-facing report, stating the CONSEQUENCE and not merely the fact.

        THE CONSEQUENCE IS CONDITIONAL, and overstating it is how an operator is trained to ignore a
        report. Integration refuses a lane only when that lane's `changed_files` INTERSECT a dirty
        path (`dirty_tree_overlap` returns `[]` for disjoint sets), so "your lanes will be refused" is
        false. For UNTRACKED paths it is doubly conditional: a lane is built from a COMMIT, so it does
        not carry them and normally cannot overlap them at all.

        THE REAL HAZARD IS THE MEASURED ONE, so it is the one named: an agent reading this tree can
        mistake another party's uncommitted pollution, or its OWN, for the repository's real state.

        NO REMEDY THAT TOUCHES UN-OWNED WORK IS SUGGESTED. This says what is there; deciding whose it
        is and what to do about it belongs to the human. Nothing here tells anyone to commit, stash,
        reset, or clean.
        """
        if self.clean:
            return "run start: no untracked content in the target checkout"
        shown = ", ".join(self.sample)
        more = self.total - len(self.sample)
        listed = shown if more <= 0 else f"{shown}, and {more} more"
        return (
            f"run start: the target checkout holds {self.total} UNTRACKED path(s), which this run "
            "does NOT refuse on and does NOT touch: "
            f"{listed}. Any lane whose changed files OVERLAP one of these paths will be refused at "
            "integration; a lane whose changes are disjoint from them will not. Untracked paths are "
            "normally disjoint from a lane by construction, because a lane is created from a commit "
            "and does not carry them. The hazard worth your attention is a different one: an agent "
            "reading this tree can mistake this content for the repository's real state, so if you "
            "did not expect it, decide whose it is before spending a run against it."
        )


class TrackedDirtReport(NamedTuple):
    """What DIRTY TRACKED content a checkout holds at run start (dirtygates `d7qoxv` E-01).

    THE SIBLING OF `UntrackedDirtReport`, AND DELIBERATELY A SEPARATE TYPE. The untracked report
    answers "what is sitting here that git does not track?"; this answers "which tracked paths is HEAD
    missing?". They were kept apart because `3i0aaz` pins the untracked rule to untracked entries ONLY
    (`test_tracked_dirt_is_NOT_in_this_report`), and folding tracked paths into that total would break
    the very distinction that plan established.

    WHY THIS EXISTS AT ALL, given the per-item guard already records the same paths. The guard runs
    once per QUEUE ENTRY inside `execute_item`, so an operator-facing line there says the same thing N
    times - the exact defect `3i0aaz`'s own review rejected in its PR-005. The RECORD stays per
    attempt, so each attempt is self-describing; the OPERATOR-FACING sentence is emitted ONCE, here.
    """

    total: int
    sample: tuple[str, ...]

    @property
    def clean(self) -> bool:
        return self.total == 0

    @property
    def notice(self) -> str:
        """The operator-facing run-start line, stating the CONSEQUENCE and not merely the fact.

        IT MUST NOT PROMISE A REFUSAL, because after `d7qoxv` an isolated turn is no longer refused
        over these paths. It also must not imply they are harmless: a lane is cut from HEAD, so it
        genuinely does not carry them, and that can surface later as a test failure at
        merge-and-revalidate time. Both halves are stated, and which one bites depends on isolation.

        NO REMEDY THAT TOUCHES UN-OWNED WORK IS SUGGESTED, the same discipline `z2isfg` established
        and the untracked report keeps: nothing here tells anyone to commit, stash, reset, or clean.
        """
        if self.clean:
            return "run start: no dirty tracked paths in the target checkout"
        shown = ", ".join(self.sample)
        more = self.total - len(self.sample)
        listed = shown if more <= 0 else f"{shown}, and {more} more"
        return (
            f"run start: the target checkout has {self.total} dirty TRACKED path(s), which an "
            "isolated turn's lane does NOT carry because a lane is created from HEAD: "
            f"{listed}. This does NOT refuse an isolated turn: a lane cut from a commit fails in "
            "exactly the same way whether or not it was refused first, so validation at "
            "merge-and-revalidate time is what surfaces a genuinely stale base, with real evidence. "
            "A turn sharing this checkout (--no-isolate-worktree) IS still refused, because its own "
            "changes could not be told apart from the uncommitted work already here. If you did not "
            "expect these paths, decide whose they are before spending a run against them."
        )


def evaluate_tracked_dirt(
    porcelain: str,
    *,
    sample_limit: int = UNTRACKED_REPORT_SAMPLE_LIMIT,
) -> TrackedDirtReport:
    """Classify porcelain output for the once-per-run TRACKED-dirt report (`d7qoxv` E-01).

    PURE, taking the text rather than running git, exactly as its untracked sibling and
    `lane_containment.evaluate_clean_base` are, so every case is reachable with no repository.

    THE PARSER IS THE SHARED ONE and this function holds NO porcelain format knowledge: it calls
    `lane_containment.parse_porcelain_entries`, the declared single decoder, and reuses that module's
    own status constants rather than re-spelling them.

    IT MUST NOT RE-DECIDE WHAT "DIRTY TRACKED" MEANS, and it does not: the R5.4 verdict remains
    `lane_containment.evaluate_clean_base`'s. This is a REPORTING projection over the same porcelain,
    which is why it takes the `--untracked-files=all` text the run-start report already fetched rather
    than issuing a second `git status`.

    IGNORED ENTRIES ARE EXCLUDED for the same reason the untracked report excludes them: `!!` is
    configuration, not pollution. In practice they are absent anyway, since the run-start invocation
    does not pass `--ignored`.
    """

    from agent_workflows import lane_containment

    tracked = sorted(
        {
            path
            for status, path in lane_containment.parse_porcelain_entries(porcelain)
            if status
            not in (
                lane_containment.PORCELAIN_UNTRACKED,
                lane_containment.PORCELAIN_IGNORED,
            )
        }
    )
    limit = max(0, int(sample_limit))
    return TrackedDirtReport(total=len(tracked), sample=tuple(tracked[:limit]))


def evaluate_untracked_dirt(
    porcelain: str,
    *,
    sample_limit: int = UNTRACKED_REPORT_SAMPLE_LIMIT,
) -> UntrackedDirtReport:
    """Classify `git status --porcelain --untracked-files=all` output for the E-02 report.

    PURE, taking the text rather than running git, exactly as `lane_containment.evaluate_clean_base`
    is: both hosts share the RULE while each supplies its own git runner, and a test can drive every
    case with no repository.

    THE PARSER IS THE SHARED ONE and this function holds NO porcelain format knowledge: no
    `splitlines`, no column slicing, no ` -> ` handling. It calls `lane_containment
    .parse_porcelain_entries`, which is that module's declared single decoder of the format, and it
    reuses that module's own `??` status constant rather than re-spelling it.

    WHY THE DECODER AND NOT ITS `parse_porcelain_paths` PROJECTION, since the projection is the more
    commonly cited name: this report must include UNTRACKED entries and EXCLUDE tracked ones, and
    that distinction lives ENTIRELY in the two status columns the projection discards by construction
    (`parse_porcelain_paths` is literally `{path for _status, path in parse_porcelain_entries(...)}`).
    Using the projection would report dirty TRACKED paths too, which is question (2)'s business - it
    REFUSES on them - and would restate that refusal as a report.

    THE IMPORT IS LAZY because `lane_containment` imports THIS module at module scope, so a
    module-level import here would be circular. That is the established idiom in this file for a peer
    module it cannot import at module scope (`worktree_lease`, `orchestrate_isolation`,
    `ipd_lifecycle`, `run_recovery`, `selectors` are all imported this way).
    """

    from agent_workflows import lane_containment

    untracked = sorted(
        path
        for status, path in lane_containment.parse_porcelain_entries(porcelain)
        if status == lane_containment.PORCELAIN_UNTRACKED
    )
    limit = max(0, int(sample_limit))
    return UntrackedDirtReport(total=len(untracked), sample=tuple(untracked[:limit]))


def report_untracked_dirt_at_run_start(
    repo: Path,
    *,
    git_runner: Callable[..., tuple[int, str, str]] | None = None,
    stream: Any = None,
) -> UntrackedDirtReport:
    """Emit the E-02 untracked report for `repo`, ONCE per run, and return what it found.

    CALLED FROM `initialize_run` ON BOTH HOSTS, beside `refuse_unimplemented_run_flags`, and that
    placement is the whole point of the item. "Run start" has exactly one home: the `nna8yz` E-05
    guard is PER ITEM inside `execute_item`, so a report placed beside THAT would fire once per queue
    entry and say the same thing N times. This seam also runs before the run directory exists, so the
    report cannot be mistaken for durable run state.

    IT NEVER RAISES AND NEVER REFUSES. A report that could fail the run would be question (2) wearing
    a report's clothes. An unreadable tree yields an empty report rather than an exception, because
    failing a run over an inability to describe untracked content would be a strictly worse outcome
    than the silence this replaces (and question (2) fails closed on an unreadable tree already).

    IT ALSO EMITS THE TRACKED-DIRT LINE (dirtygates `d7qoxv` E-01), EXTENDING THIS REPORT RATHER THAN
    ADDING A SECOND ONE. That is deliberate and was the coordination `d7qoxv` E-01 required: two
    adjacent dirty-tree reports at run start would make the operator read the same tree described
    twice. The two lines answer different questions (untracked pollution versus an incomplete base)
    and are emitted from ONE `git status`, so there is no second subprocess either.

    THE RETURN VALUE IS STILL THE UNTRACKED REPORT, so every existing caller and assertion is
    unchanged; the tracked report is available through `evaluate_tracked_dirt` for a test that wants
    it. Widening the return type would have been a breaking change for a reporting nicety.
    """

    runner = git_runner or _run_git
    try:
        rc, out, _err = runner(Path(repo), list(UNTRACKED_REPORT_STATUS_ARGS))
    except Exception:  # pragma: no cover - defensive: a report must not fail a run
        return UntrackedDirtReport(total=0, sample=())
    if rc != 0:
        return UntrackedDirtReport(total=0, sample=())
    report = evaluate_untracked_dirt(out)
    if not report.clean:
        print(report.notice, file=stream if stream is not None else sys.stderr)
    # ORDERED AFTER the untracked line, and silent on a clean tracked tree for the same reason: a
    # report that always fires is a report nobody reads.
    tracked = evaluate_tracked_dirt(out)
    if not tracked.clean:
        print(tracked.notice, file=stream if stream is not None else sys.stderr)
    return report


#: The verdicts a pre-launch clean-base decision can reach (dirtybase `3i0aaz` E-03/E-05).
CLEAN_BASE_PROCEED = "proceed"
CLEAN_BASE_CONSENTED = "consented"
CLEAN_BASE_REFUSE = "refuse"
#: dirtygates Order 01 (`d7qoxv`) E-01: a dirty base that is REPORTED and proceeds anyway.
#:
#: DISTINCT FROM `CLEAN_BASE_CONSENTED`, and conflating the two would destroy the consent flag's
#: signal value. Consent means the OPERATOR passed `--allow-dirty-base` over a refusal that still
#: stands (the shared-tree case); this verdict means the rule never refused in the first place, so
#: there was nothing to consent to. An audit must be able to tell "a human overrode a guard" from "no
#: guard applied here", which is exactly the distinction a single merged verdict would erase.
CLEAN_BASE_WARN = "warn"


class CleanBaseDecision(NamedTuple):
    """WHETHER a turn may launch against this base, and WHY (dirtybase `3i0aaz`).

    ONE DECISION REACHED FROM BOTH HOSTS. The `--full-auto` default diverged between the two drivers
    precisely because each decided a policy question in its own body, so the policy lives here and
    each `execute_item` consumes the verdict. What stays per host is only the durable bookkeeping
    (its own attempt record, its own event log), which is host state and not policy.
    """

    verdict: str
    dirty_paths: tuple[str, ...]
    reason: str

    @property
    def refused(self) -> bool:
        return self.verdict == CLEAN_BASE_REFUSE

    @property
    def consented(self) -> bool:
        return self.verdict == CLEAN_BASE_CONSENTED

    @property
    def warned(self) -> bool:
        """A dirty base that is REPORTED and launched anyway (dirtygates `d7qoxv`, isolated path)."""
        return self.verdict == CLEAN_BASE_WARN


def clean_base_launch_decision(
    base: Any,
    *,
    allow_dirty_base: bool = False,
) -> CleanBaseDecision:
    """Turn a `lane_containment.CleanBaseResult` plus the operator's consent into a launch verdict.

    THE RULE IS NOT RE-DECIDED HERE. What is dirty, how a refusal reads, and WHETHER this path refuses
    at all are all `lane_containment.evaluate_clean_base`'s (plan `nna8yz` E-05, extended by `3i0aaz`
    E-03 with a shared-tree message variant, amended by dirtygates `d7qoxv` E-01/E-03 so the isolated
    path REPORTS). This adds exactly one thing: `--allow-dirty-base` turns a REFUSAL into a recorded
    CONSENT.

    THE WARN VERDICT IS READ FROM THE RULE, NEVER DECIDED HERE (`d7qoxv` E-01). `CleanBaseResult
    .refuses` answers "does this dirty base refuse?", so a dirty ISOLATED base reaches
    `CLEAN_BASE_WARN` and a dirty SHARED tree still reaches `CLEAN_BASE_REFUSE`. Writing that split as
    an `if isolate` in either driver's body is the failure this whole function exists to prevent: that
    is precisely how the `--full-auto` default came to differ between the two runners.

    CONSENT IS NOT CONSULTED ON A PATH THAT DOES NOT REFUSE, and the ordering below is load-bearing.
    `--allow-dirty-base` exists to override a REFUSAL; reporting `consented` where nothing was refused
    would claim the operator overrode a guard that never fired, which is a false audit record in the
    one direction an audit most needs to trust.

    WHAT CONSENT DOES NOT WAIVE, which is the sentence a future reader will rely on. It acknowledges
    a dirty TRACKED base for THIS run and nothing else. It does not waive the approval gate, the
    scope gate, the V-evidence checks, or the integration-time dirty-overlap refusal - that last one
    protects a DIFFERENT party's work at a DIFFERENT time and is not this flag's to waive. It also
    does not suppress the once-per-run untracked report: consenting to proceed is not a request to be
    told less.
    """

    if base.clean:
        return CleanBaseDecision(
            verdict=CLEAN_BASE_PROCEED, dirty_paths=(), reason=base.reason
        )
    if not base.refuses:
        # The isolated path: the base IS dirty and is NOT clean, but it does not refuse, so this is a
        # report. The paths ride along so the caller records them without re-deriving anything.
        return CleanBaseDecision(
            verdict=CLEAN_BASE_WARN,
            dirty_paths=tuple(base.dirty_paths),
            reason=base.reason,
        )
    if allow_dirty_base:
        return CleanBaseDecision(
            verdict=CLEAN_BASE_CONSENTED,
            dirty_paths=tuple(base.dirty_paths),
            reason=(
                "--allow-dirty-base: proceeding over "
                f"{len(base.dirty_paths)} dirty TRACKED path(s) by explicit operator consent: "
                + ", ".join(base.dirty_paths)
                + ". Consent covers this base for this run ONLY: the approval, scope, and "
                "V-evidence gates still apply, and a lane whose changed files overlap one of these "
                "paths will still be refused at integration"
            ),
        )
    return CleanBaseDecision(
        verdict=CLEAN_BASE_REFUSE,
        dirty_paths=tuple(base.dirty_paths),
        reason=base.reason,
    )


def refuse_frozen_flags_on_resume(args: Any) -> None:
    """REFUSE a flag spec 2.1 freezes when it is passed with `resume` (spec `25kzda` :131).

    SCOPED DELIBERATELY, and the scope is the interesting part. Spec `:129` says `--resume` is
    mutually exclusive with "flags that would change the frozen queue or policy", but the SHIPPED
    `--full-auto` on resume does not refuse - it OVERWRITES the frozen option and saves it. So the
    blanket reading and the shipped behavior disagree, and only ONE flag is unambiguous: `:131` says
    of `--retry-budget` that "the frozen value cannot change on resume". That one is refused here.
    Converting `--full-auto`'s shipped override into a refusal would be a behavior change to a
    shipped flag, which belongs to whoever reconciles `:129` with `:131`, not to a plan whose fence is
    flag registration.
    """

    for row in RUN_POLICY_FLAGS:
        if row.resume_rule != RESUME_REFUSE:
            continue
        if getattr(args, row.dest, None) is not None:
            raise RunFlagRefusal(
                f"{row.flag} cannot be changed on --resume: spec 25kzda 2.1 freezes it at queue "
                f"build ('the frozen value cannot change on resume'). Resume the run without it, "
                f"or start a new run"
            )


def freeze_run_policy_flags(args: Any) -> dict:
    """The spec 2.1 flag values to FREEZE into run state at queue build, as `{dest: value}`.

    Frozen because spec 2.1 makes resume use "the original host, queue, and options": a policy read
    from `args` on every resume would silently change meaning between the first turn and the last.

    Two values are NORMALIZED here rather than at their read sites, so no consumer has to remember:

      * `--full-auto` IMPLIES `--unattended` (spec `:134`), and implying nothing else. Implemented
        explicitly instead of being left to chance, because "unattended" is what makes a gate refuse
        rather than prompt, and a `--full-auto` run has no one to prompt by construction.
      * `--retry-budget` is resolved to its EFFECTIVE integer through
        :func:`resolve_retry_budget`, so the frozen state holds the value that will actually be used
        (never a bare `None` that a later reader has to re-resolve, and re-resolve differently).
    """

    def _supplied(dest: str) -> Any:
        """The value for a NON-BOOL row, with a placeholder `bool` read as NOT SUPPLIED.

        WHY THIS EXISTS RATHER THAN A BARE `getattr`. A namespace built GENERICALLY over this table -
        `{row.dest: False for row in RUN_POLICY_FLAGS}`, the idiom the shipped contract test uses in
        four places - hands every row `False`, including the int and choice rows. That value never
        comes from argparse, which declares `default=None` for them precisely so "absent" is
        distinguishable, so a `bool` here can only mean "this namespace was filled in generically"
        and the correct reading is ABSENT.

        The RESOLVERS stay strict on purpose: a negative count and an unrecognized policy word are
        still refused, because those are real operator errors. Only the placeholder is tolerated, and
        only here, where the placeholder is actually produced.
        """

        value = getattr(args, dest, None)
        return None if isinstance(value, bool) else value

    frozen: dict = {}
    for row in RUN_POLICY_FLAGS:
        if not row.freeze:
            continue
        if row.dest == "retry_budget":
            frozen[row.dest] = resolve_retry_budget(getattr(args, row.dest, None))
        elif row.dest == "integration_retry_limit":
            # integpath-03 (`51vw4y`) E-02: resolved to its EFFECTIVE integer here, exactly as
            # `retry_budget` is, so no later reader has to re-resolve a bare `None` (and re-resolve it
            # differently). Its own resolver, NOT `resolve_retry_budget`: the two count different
            # quantities and this one is deliberately not clamped to spec 2.1's 0..10 range.
            frozen[row.dest] = resolve_integration_retry_limit(_supplied(row.dest))
        elif row.dest == "on_integration_blocked":
            frozen[row.dest] = resolve_on_integration_blocked(_supplied(row.dest))
        else:
            frozen[row.dest] = bool(getattr(args, row.dest, False) or False)
    if frozen.get("full_auto"):
        frozen["unattended"] = True
    return frozen


class VerificationDecision(NamedTuple):
    """WHETHER a verifier turn runs for this run, plus WHICH tier decided it.

    Deliberately host-NEUTRAL. `validate` is the decision in its POSITIVE sense ("verify"), never a
    host's frozen key: `oc_runipd` freezes `validate` and gates on it, while `agy_runipd` freezes
    `no_verify` and gates on `not no_verify`, so the two hosts' keys are OPPOSITE IN POLARITY. Each
    driver negates (or does not) at its OWN freeze site, which keeps the inversion in one place per
    host and makes it directly assertable; returning a `no_verify`-shaped value from here would put
    the same negation in two places, which is the hazard superseded plan `mn3gwr` F-5 measured.

    `provenance` is the resolver's tier for the `validate` field, drawn from its closed vocabulary
    (`explicit`, `profile`, `default-profile`, `defaults`, `shipped-default`), so a reader can tell
    an operator's flag from a stored default from the shipped per-host posture.
    """

    validate: bool
    provenance: str


def resolve_verification_decision(
    *,
    runner: str,
    profile: Optional[str] = None,
    validate: Optional[bool] = None,
) -> VerificationDecision:
    """Resolve the per-host verification decision from the runner-profile store (`ybkmzp` E-01).

    The whole precedence decision belongs to `runner_profiles.resolve`, so this asks it rather than
    re-implementing the chain: `explicit flag > the named profile's own validate >
    defaults.validate > the RESOLVED RUNNER's `validate_default` registry row`. Tier 4 is per host
    (`hostdefault-01` E-02), which is why `runner` is required and never guessed.

    `validate` IS A TRI-STATE and the caller must preserve it. `None` means "the operator said
    nothing", which FALLS THROUGH to the configured tiers; `False` means "the operator said do not
    verify" and WINS. Collapsing absent into `False` at a call site would make a stored default
    unreachable, which is the whole defect this helper exists to close.

    IMPORTING `runner_profiles` HERE IS PERMITTED. This module's admission rules forbid importing
    either RUNNER (enforced by AST in `tests/test_runner_shared.py::NoRunnerImportTests`, which
    rejects any module name containing `runipd`); `runner_profiles` is a peer module that imports
    only `agent_workflows.config`, so there is no cycle and no guard to trip.

    Raises :class:`DriverError` (which both runners' `main` already catches, printing the message
    and exiting 2) carrying the resolver's own diagnostic. NO per-driver translation wrapper is
    needed or wanted: there is exactly ONE `DriverError` class in this package since `rununify`
    Order 02 (`818uru`), and both runners bind THIS one.
    """

    try:
        cfg = runner_profiles.load()
        resolved = runner_profiles.resolve(
            cfg, runner=runner, profile=profile, validate=validate
        )
    except runner_profiles.RunnerProfileError as exc:
        raise DriverError(f"runner profile: {exc}") from exc
    return VerificationDecision(
        validate=bool(resolved.validate),
        provenance=str(resolved.provenance.get("validate", "")),
    )


def is_interactive_run(args: Any = None, *, stream: TextIO | None = None) -> bool:
    """Whether a gate may PROMPT: a real TTY on stdin and stderr, and no `--unattended`.

    Both halves are load-bearing. `--unattended` (and `--full-auto`, which implies it) is the
    operator DECLARING there is nobody to answer, and it wins over a TTY that happens to exist -
    an unattended run launched from a terminal must still refuse rather than block forever. And with
    no `--unattended`, the TTY test is still required, because these runs are non-interactive by
    design; `_lane_reclaim_prompt` in both runners already establishes exactly this precedent (no
    TTY means no prompt and no waiting, EVER).
    """

    if args is not None and getattr(args, "unattended", False):
        return False
    if args is not None and getattr(args, "full_auto", False):
        return False
    stdin = sys.stdin
    err = stream if stream is not None else sys.stderr
    for target in (stdin, err):
        if target is None:
            return False
        if not (getattr(target, "isatty", None) and target.isatty()):
            return False
    return True


def enforce_mixed_type_gate(
    repo: Path,
    plan_paths: Any,
    *,
    allow_mixed: bool,
    interactive: bool,
    host: str,
    selector: str,
    response: Any = None,
) -> Any:
    """CALL executed plan `6lu3rq`'s mixed-type gate, and act on its verdict (spec 25kzda 2.5).

    THE DEFECT THIS FIXES IS NOT A MISSING FLAG, IT IS A GATE NOBODY CALLED. `6lu3rq` built the whole
    gate - the exact-phrase confirmation, the counts preview, the verbatim `RUN-MIXED-TYPES` refusal -
    and `run_selection_policy` was imported by NO module in the package while `decide` had ZERO call
    sites. A fully tested, importable, completely unreachable gate is indistinguishable from no gate
    at all from the operator's seat, and a green suite proved nothing about it.

    So this function is a CALL SITE and not a second gate. It classifies, it calls `decide`, it prints
    what `decide` composed, and it raises on refusal. It composes no message and re-derives no
    counts: a second copy of the refusal text is the fork this repository keeps paying for.

    AN HONEST LIMIT, stated here because a reader will otherwise take this call site as proof of more
    than it delivers: NO REAL `aw <host> run` INVOCATION CAN YET PRODUCE A MIXED SELECTION. Discovery
    walks only the two plans trees and returns plan records (`discover_plans`), the manifest is
    compiled from those alone, selectors resolve against that IPD-only manifest, and NEITHER runner
    registers `--type` (spec 2.2/2.3 work, explicitly out of `uyeko5`'s scope). So `decide` is now
    reached on every run and its gate correctly does not APPLY, because the classification is
    single-type. The wiring is proven correct; a live mixed selection being gated is NOT proven, and
    must not be reported as if it were.

    Returns the `Verdict` so the caller can record spec 2.5 bullet 4's four facts in the run ledger.
    """

    from agent_workflows import run_selection_policy

    classification = run_selection_policy.classify_paths(repo, list(plan_paths))
    verdict = run_selection_policy.decide(
        classification,
        interactive=interactive,
        allow_mixed=allow_mixed,
        response=response,
        host=host,
        selector=selector,
    )
    if verdict.gate_applied and verdict.message is None:
        # Gate applied and PASSED: the operator authorized a genuinely mixed selection, so show them
        # the preview they authorized rather than letting it pass silently.
        print(verdict.record.action_preview, file=sys.stderr)
    if not verdict.proceed:
        # The refusal TEXT is `run_selection_policy`'s, verbatim from the spec, never recomposed here.
        raise DriverError(verdict.message or verdict.reason)
    return verdict


#: The shipped lane prompt's timeout, reused so the two prompts in this package cannot disagree about
#: how long a run may wait for a human. `_lane_reclaim_prompt` uses 10s in both runners.
GATE_PROMPT_TIMEOUT: float = 10.0


def prompt_for_gate_phrase(
    question: str,
    *,
    timeout: float = GATE_PROMPT_TIMEOUT,
    stdin: Any = None,
    stderr: Any = None,
) -> str | None:
    """Ask ONE gate question, honoring the SAME HARD CONSTRAINTS the shipped lane prompt does.

    THE HAZARD THIS FUNCTION IS SHAPED BY, because getting it wrong is expensive and silent: these
    runs are non-interactive by design and usually unattended. Both runners hand the child process
    `stdin=subprocess.DEVNULL` expressly because "a nested `aw` sees the operator's TTY, believes it
    may prompt, and blocks on input() forever", and that comment records a MEASURED 1h49m wedge. So a
    bare blocking `input()` in the queue-build path could hang an overnight run with no output
    explaining why. Neither runner calls `input()` anywhere, and this function does not either.

    THE CONSTRAINTS, all four load-bearing and all inherited from `_lane_reclaim_prompt`:

    * NO TTY, NO PROMPT. Both stdin and stderr must be a real TTY. The caller normally establishes
      this through :func:`is_interactive_run` (which also honors the operator's `--unattended`
      declaration); the check is repeated here so this function is safe called directly.
    * IT NEVER BLOCKS. `select` with a bounded timeout, never a plain read.
    * AN UNANSWERED PROMPT FALLS THROUGH, returning `None` so the caller takes its automatic
      decision. For an exact-phrase gate `None` is REFUSED by
      :func:`run_selection_policy.is_confirmation_accepted`, so a timeout can only ever produce the
      same outcome as the unattended path - it can never grant an admission.
    * THE AUTOMATIC DECISION IS THE AUTHORITY. This only front-runs it.

    Returns the raw typed line (the caller does the exact-phrase comparison, so the phrase has ONE
    definition), or `None` when there was no prompt or no answer.
    """

    import select

    stream_in = sys.stdin if stdin is None else stdin
    stream_err = sys.stderr if stderr is None else stderr
    for target in (stream_in, stream_err):
        if target is None:
            return None
        if not (getattr(target, "isatty", None) and target.isatty()):
            return None
    print(question, end="", file=stream_err, flush=True)
    try:
        ready, _w, _x = select.select([stream_in], [], [], timeout)
    except Exception:
        print(file=stream_err)
        return None
    if not ready:
        print(
            "\n  (no answer in {0}s; taking the automatic decision)".format(timeout),
            file=stream_err,
        )
        return None
    try:
        return stream_in.readline()
    except Exception:
        return None


def enforce_draft_admission_gate(
    manifest: dict,
    queue_ids: Any,
    *,
    repo: Path | None,
    allow_drafts: bool,
    interactive: bool,
    host: str,
    selector: str,
    response: Any = None,
    prompt: Any = None,
) -> tuple:
    """CALL spec 25kzda 2.5a's draft admission gate and act on its verdict. Both hosts, one seam.

    Returns ``(kept_queue_ids, verdict)``. The gate EXCLUDES items; it never refuses the run (see
    :func:`run_selection_policy.decide_draft_admission` for why that asymmetry with the mixed-type
    gate is deliberate), so the returned queue is the original minus any withheld complete draft.

    THE INTERACTIVE HALF IS IMPLEMENTED, FENCED (the plan's E-04 option (a)). Spec 2.5a requires the
    exact phrase `run drafts` in an interactive terminal, and rather than declaring that unreachable
    on this driver, the prompt follows the shipped `_lane_reclaim_prompt` precedent exactly: it needs
    a real TTY on BOTH streams, it never blocks, and an unanswered prompt falls through to the
    automatic decision. That automatic decision is EXCLUDE-and-proceed, which is bit-for-bit the
    unattended no-flag outcome, so a timeout cannot silently admit a draft. `--allow-drafts` remains
    the unattended half. No `input()` is added to either runner.

    ``response`` short-circuits the prompt (tests, and any caller that already has an answer).
    ``prompt`` overrides the prompt function, so the TTY fence itself is testable.
    """

    from agent_workflows import run_selection_policy

    candidates = sweep_draft_candidates(manifest, repo=repo)
    ids = list(queue_ids)
    draft_ids = {c.identity for c in candidates}
    remaining_count = len([i for i in ids if i not in draft_ids])

    answer = response
    if answer is None and interactive and any(c.complete for c in candidates):
        # Only prompt when there is something to admit, and only after the preview is composed by the
        # pure module, so the operator is shown the same text the ledger records.
        preview = run_selection_policy.decide_draft_admission(
            candidates,
            interactive=False,
            allow_drafts=True,
            remaining_count=remaining_count,
            host=host,
            selector=selector,
        ).record.preview
        asker = prompt if prompt is not None else prompt_for_gate_phrase
        answer = asker(
            "{0}\nType '{1}' to admit them, anything else to skip them: ".format(
                preview, run_selection_policy.DRAFTS_CONFIRM_PHRASE
            )
        )

    verdict = run_selection_policy.decide_draft_admission(
        candidates,
        interactive=interactive,
        allow_drafts=allow_drafts,
        response=answer,
        remaining_count=remaining_count,
        host=host,
        selector=selector,
    )
    if verdict.gate_applied:
        # Print the preview whether admitted or excluded: an operator must be able to see WHICH
        # drafts a run promoted, and (on the exclusion path) that something was withheld.
        print(verdict.record.preview, file=sys.stderr)
    if verdict.message:
        # The exclusion NOTICE is `run_selection_policy`'s, verbatim from spec 2.5a, never recomposed
        # here. Printed, NOT raised: this gate excludes items and the rest of the queue proceeds.
        print(verdict.message, file=sys.stderr)
    if verdict.skipped_incomplete:
        # spec 2.5a bullet 1: an incomplete draft is a skip WITH FINDINGS at every flag setting.
        # Naming them is the "findings will be reported" half; silence would look like an omission.
        print(
            "  incomplete draft(s) skipped (never admissible, no flag admits them): {0}".format(
                ", ".join(verdict.skipped_incomplete)
            ),
            file=sys.stderr,
        )
    # ADMIT, not merely permit. An admitted draft has to ENTER the queue, because the sweep never put
    # it there: membership excludes a draft until this gate admits it (`needs_review` is handed
    # `authoring_complete` and answers False for an unadmitted one), which is exactly what makes the
    # question a real gate rather than a formality. Appended in manifest order after the swept items,
    # and de-duplicated so a selector that already resolved the draft explicitly cannot double it.
    withheld = set(verdict.excluded_complete)
    kept = [i for i in ids if i not in withheld]
    for identity in verdict.admitted:
        if identity not in kept:
            kept.append(identity)
    return kept, verdict


def evaluate_unverifiable_admission(args: Any) -> Any:
    """Check `--unverifiable-ok`'s precondition by CALLING `zub5f1`'s predicate (spec 2.1 `:136`).

    Spec 2.1: `--unverifiable-ok` is legal ONLY when contractless prompts were explicitly admitted by
    `--allow-unverifiable` or the interactive `run unverifiable` confirmation. The rule is already
    implemented and tested in `run_evidence.aggregate_run_exit`, which returns the refusal as DATA
    (`RunAggregation.refusals` names the missing precondition and `unverifiable_ok_applied` is False),
    so this function ASKS IT and never re-decides.

    That indirection is the whole point rather than an affectation. Executed plan `zub5f1` took the
    admission as a PARAMETER precisely because these flags did not exist; the flags now exist, and
    binding them to that parameter closes the seam. Writing an `if unverifiable_ok and not
    allow_unverifiable` here instead would put one aggregate rule in two places, and two
    implementations of one rule is worse than one missing flag.

    Called with an EMPTY item list on purpose: the precondition is a property of the INVOCATION, so it
    is answerable before any item has run, which is where an operator wants to learn their command was
    malformed. `aggregate_run_exit` is pure, so asking it costs nothing.

    Returns the `RunAggregation`. Raises :class:`RunFlagRefusal` when the flag was passed without its
    admission, carrying the predicate's OWN message.
    """

    from agent_workflows import run_evidence

    aggregation = run_evidence.aggregate_run_exit(
        [],
        unverifiable_ok=bool(getattr(args, "unverifiable_ok", False)),
        unverifiable_admitted=bool(getattr(args, "allow_unverifiable", False)),
    )
    for refusal in aggregation.refusals:
        if refusal.name == run_evidence.REFUSAL_UNVERIFIABLE_OK_UNADMITTED:
            raise RunFlagRefusal(f"--unverifiable-ok: {refusal.details}")
    return aggregation


def apply_run_policy_flags_on_resume(state: dict, args: Any) -> bool:
    """Apply the spec 2.1 policy flags an operator PASSED with `resume`; ignore the omitted ones.

    Returns True when anything changed, so the caller can decide whether to save.

    THE RULE IS THE SHIPPED `--full-auto` ONE, applied uniformly rather than to one flag: a value of
    `None` means the flag was ABSENT, so the frozen value stands; any other value was explicitly typed
    and OVERWRITES it. That is what `default=None` on the `resume` parser buys, and it is why the
    default matters: with `default=False` this function could not tell `--no-allow-mixed` from silence
    and would clobber frozen policy on every resume.

    Two things this deliberately does NOT do:

    * It does not touch a flag whose ``resume_rule`` is :data:`RESUME_REFUSE`. `--retry-budget` is
      refused earlier by :func:`refuse_frozen_flags_on_resume`, so reaching here with a value set
      would mean that refusal was skipped; ignoring it is the fail-safe direction.
    * It does not re-apply `--full-auto`'s implication of `--unattended`. On a resume the operator is
      adjusting one policy on an already-frozen run, and silently flipping a SECOND frozen option they
      did not name is the kind of hidden write the freeze exists to prevent. The implication is applied
      once, at queue build, by :func:`freeze_run_policy_flags`.
    """

    options = state.setdefault("options", {})
    changed = False
    for row in RUN_POLICY_FLAGS:
        if row.resume_rule == RESUME_REFUSE:
            continue
        value = getattr(args, row.dest, None)
        if value is None:
            continue
        if options.get(row.dest) != value:
            options[row.dest] = value
            changed = True
    return changed


# ==================================================================================================
# orchretire-01 (`5942n7`): THE SHARED ON-DISK SET-COMPLETENESS DECISION PREDICATE
# (spec `77tr3o` R-1, R-2, R-3, R-9, R-10)
# ==================================================================================================
#
# WHAT THIS REPLACES, AND WHY THE OLD ANSWER COULD NOT BE FIXED IN PLACE.
# `oc_runipd._set_children_all_executed` inspects `state["queue"]` ONLY. That makes the maintainer's
# requirement - "retire the orchestrator when the Set's LAST outstanding child completes" -
# UNIMPLEMENTABLE, because a run that executes only that last child holds ONE child in its queue
# while the Set on disk holds several. Measured: `wslayout` passed its queue-scoped check only
# INCIDENTALLY (child `wpu5zu` executed in an earlier run and was absent from the queue, and the four
# children that happened to be present were all `executed`). So the fix is not a better queue scan;
# it is reading the PLANS TREE, which is what this section does.
#
# THE QUEUE KEEPS ITS JOB. It remains the source of what to DISPATCH. It is simply not the source of
# Set MEMBERSHIP. Those are two different questions that one function used to answer with one input.
#
# THIS SECTION DECIDES ONLY. It performs no transition and writes no status. `ueg5cf` (child 02) owns
# the retirement transition and `pgq326` (child 03) owns the dispatch wiring, so a wrong decision here
# cannot move a plan. `_set_children_all_executed` and its callers are deliberately UNTOUCHED.
#
# THE FAILURE DIRECTION IS THE WHOLE DESIGN, and it is asymmetric ON PURPOSE:
#   * a FALSE REFUSAL leaves an orchestrator lingering in `pending/`, which is exactly today's status
#     quo and costs nothing new; while
#   * a FALSE ELIGIBILITY retires a plan whose Set is not done, asserting a completion that never
#     happened - the same class of never-true claim this Set exists to correct.
# So wherever the code cannot tell, it REFUSES. That single rule explains every conservative choice
# below (the `executed` allowlist, the unparseable-table refusal, the non-numeric row token refusal).
#
# NO THIRD "WHICH PLANS EXIST" MECHANISM. Membership goes through `selectors.resolve(repo, "plans",
# setid)`, which already returns members across `pending/` and `executed/`, and each member's fields
# through `ipd_lint.parse(text).meta_fields`. Adding a plans-tree path literal here would be the drift
# GUIDING_PRINCIPLES P8 forbids. `discover_plans` still does not serve, but the REASON has changed and
# the old one is retracted rather than left standing: this used to say it "INJECTS the host's
# `parse_plan_file` precisely because the two runners' `PlanRecord` types disagree", which rununify 06
# (`sy7uwh`) made false - there is ONE record and ONE parser now. What remains true is narrower:
# `discover_plans` walks the plans TREES and reads every plan's full record, where a retirement
# decision needs the Set's MEMBERS and only three of their fields, so `selectors.resolve` is the
# cheaper and more direct authority.
#
# WHY THE TWO IMPORTS ARE LOCAL rather than at module scope. `ipd_lint`'s import closure is 52 modules
# and pulls in `check_engine`/`attention`; paying that on every `import runner_shared` would tax every
# runner start for a function most runs never call. Neither module reaches a runner (verified by
# closure walk: `runner_shared` is absent from `ipd_lint`'s and `selectors`' transitive imports), so
# this is a cost decision and NOT an evasion of the no-runner-import rule, which
# `tests/test_runner_shared.py::NoRunnerImportTests` enforces at module AND lazy scope.


#: The ONLY member status that counts as done for RETIREMENT purposes (spec R-2).
#:
#: AN ALLOWLIST, NOT A DENYLIST, and the difference is load-bearing. A denylist of known-bad values
#: (`substantially-complete`, `blocked`, `dependency-blocked`, ...) silently ACCEPTS any status added
#: to the vocabulary later, which is how a conservative gate quietly stops gating. One accepted value
#: cannot do that: a new status is refused until someone deliberately admits it here.
#:
#: DELIBERATELY NOT `EXECUTION_SUCCESS_STATES`. That set (`oc_runipd.py:274`) includes
#: `substantially-complete` for DEPENDENCY-EDGE purposes and is out of scope (spec Section 4). This
#: predicate simply does not consult it; nothing about it is changed here.
SET_RETIREMENT_DONE_STATUS = "executed"

#: The typed refusal reasons (spec R-9). Four distinct facts that MUST NOT share one message: today
#: they all surface as "dependency-blocked (unmet dependencies)", which named no dependency at all in
#: `5e4sb6`'s recorded event (`unfinished_children: []`).
RETIRE_ELIGIBLE = "eligible"
RETIRE_REFUSED_UNFINISHED_CHILDREN = "unfinished-children"
RETIRE_REFUSED_NO_CHILDREN = "no-children"
RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS = "unauthored-child-rows"
RETIRE_REFUSED_NO_ORCHESTRATOR = "no-orchestrator"

#: The `## Child IPDs, sequence, and dependencies` heading, taken from the SCHEMA rather than spelled
#: again here. The heading is schema-enforced (`ipd_schema.H_CHILD_IPDS`) and measured IDENTICAL in
#: all five live orchestrators, so keying on it is safe. The table BODY is not, per spec OQ-2.
_CHILD_IPDS_HEADING = "Child IPDs, sequence, and dependencies"

#: A table row: a line that starts and (modulo trailing space) ends with a pipe.
_TABLE_ROW_RE = re.compile(r"^\s*\|(?P<body>.*)\|\s*$")

#: A markdown alignment/separator row (`|---|:--:|---:|`), which is layout and not a declared child.
_TABLE_SEPARATOR_CELL_RE = re.compile(r"^:?-{2,}:?$")

#: An Order token that resolves to a definite child number. EXACTLY digits, nothing else. `03+` and
#: `last` deliberately do NOT match; see `parse_declared_child_orders`.
_ORDER_TOKEN_RE = re.compile(r"^(?P<order>\d{1,3})$")


class SetMember(NamedTuple):
    """ONE member of a Set as it exists in the PLANS TREE.

    Deliberately NOT the runner `PlanRecord`, and the reason is now a SHAPE reason rather than a
    host-split one. This docstring used to say the runner records were "per-host NamedTuples (oc's
    carries a `kind` agy's lacks), which is exactly why `discover_plans` has to inject
    `parse_plan_file`"; rununify 06 (`sy7uwh`) unified both, so that claim is retracted. What survives
    is that a retirement decision needs only a member's id, order and kind, so it carries those three
    and not a plan's whole record.

    `status` is the plan file's own `- Status:` bullet, NOT a run-state disposition. The distinction
    matters: `substantially-complete` is a RUN-STATE value and never appears in a plan file's
    `Status:` (measured: `nna8yz`'s plan file carries `approved`, while `substantially-complete`
    appears for it only in a run's `state.json`).
    """

    id6: str
    order: int | None
    kind: str
    status: str
    path: Path

    @property
    def is_orchestrator(self) -> bool:
        """True for the Set's Order-0 coordinating plan.

        Reads `Kind` FIRST and falls back to `Order == 0`, because 74 legacy plans in this repo carry
        an `Order: 0` with NO `Kind:` bullet at all (measured). Falling back keeps those recognized
        as orchestrators instead of miscounting them as children, which would make an old Set look
        like it had an extra unfinished member forever.
        """

        if self.kind:
            return self.kind == "orchestrator"
        return self.order == 0


class SetMembership(NamedTuple):
    """A Set's members read from disk, split into its orchestrator and its children."""

    setid: str
    orchestrator: SetMember | None
    children: tuple[SetMember, ...]
    #: Why an EMPTY membership is empty, when the reason is something other than "no such Set".
    #: Populated only for the id6-collision case below, so a refusal can explain itself instead of
    #: reporting a bare "no orchestrator" for a Set the operator can plainly see on disk.
    resolution_note: str = ""

    @property
    def members(self) -> tuple[SetMember, ...]:
        head = (self.orchestrator,) if self.orchestrator is not None else ()
        return head + self.children


class RetirementDecision(NamedTuple):
    """The typed answer to "may this Set's orchestrator be retired now?".

    NOT a bare bool, and not a `(bool, list)` pair either. The old shape returned `(False, [])` for
    BOTH "children exist and are unfinished" and "there are no children at all", which is how
    `5e4sb6`'s durable event came to say "dependency-blocked (unmet dependencies)" while naming no
    dependency. `reason` distinguishes every refusal cause and `detail` carries the specifics the
    record needs, so a caller cannot write a message it cannot substantiate.
    """

    eligible: bool
    reason: str
    setid: str
    #: `(id6, actual_status)` for each child that is not `executed`. Carries the STATUS as well as the
    #: id so the record can say WHY a child does not count rather than only that it does not.
    unfinished: tuple[tuple[str, str], ...] = ()
    #: Order tokens the orchestrator's child table declares that resolve to no plan (spec R-3).
    unauthored_rows: tuple[str, ...] = ()
    #: One human-readable sentence, always populated, safe to put straight into an event.
    detail: str = ""


def read_set_membership(repo: Path, setid: str) -> SetMembership:
    """Return every member of `setid` FROM THE PLANS TREE, with its Id/Order/Kind/Status.

    THIS IS THE FIX FOR spec R-1. Because it reads disk rather than a run queue, a Set whose earlier
    children were executed in PREVIOUS runs is returned IN FULL, which is precisely the case a
    queue-scoped check cannot see.

    Resolution is pinned to the `setid` selector kind. `selectors.resolve`'s precedence puts `id6`
    ABOVE `setid`, and this repo really does contain id6-shaped setids (`awhelp`, `clianx`, `detrun`,
    `agyrun`, `ackme8`, `ocsync`, `awuiux`, `rstodo`), so an unpinned resolve could match a PLAN whose
    id6 equals the setid and return one file where the Set has six. Pinning makes that a clean
    no-match instead of a wrong answer.

    THE PIN HAS ONE HONEST COST, recorded rather than hidden. When a setid collides with some OTHER
    plan's `Id`, the pinned resolve reports `rejected_kind == "id6"` and returns NOTHING, so the Set
    becomes invisible instead of misread. That is still the safe direction - a Set nobody can resolve
    is never retired - but a bare "this Set has no orchestrator" would be a misleading way to say it
    about a Set sitting plainly on disk. So the reason is carried in `resolution_note` and surfaces in
    the refusal detail. No live Set collides today (checked: all eight id6-shaped setids resolve via
    `setid`), so this is a guard, not an observed failure.

    A member whose file cannot be read or parsed is SKIPPED here rather than guessed at. It then
    cannot appear as `executed`, so the predicate refuses - the safe direction.
    """

    from agent_workflows import (
        selectors as _selectors,
    )  # local: see the section note above
    from agent_workflows import ipd_lint as _ipd_lint

    token = (setid or "").strip()
    if not token:
        return SetMembership(setid=token, orchestrator=None, children=())

    resolution = _selectors.resolve(
        repo, "plans", token, allow=frozenset({_selectors.MATCH_SETID})
    )
    note = ""
    if resolution.rejected_kind:
        note = (
            f"selector {token!r} resolved only as a "
            f"{resolution.rejected_kind!r} match, not as a Set name; Set membership was "
            "not resolved (refusing rather than reading one plan as a whole Set)"
        )

    orchestrator: SetMember | None = None
    children: list[SetMember] = []
    for path in sorted(resolution.paths):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta = _ipd_lint.parse(text).meta_fields
        id6 = (meta.get("Id") or "").strip()
        if not id6:
            continue
        raw_order = (meta.get("Order") or "").strip()
        try:
            order: int | None = int(raw_order)
        except ValueError:
            order = None
        member = SetMember(
            id6=id6,
            order=order,
            kind=(meta.get("Kind") or "").strip(),
            status=(meta.get("Status") or "").strip(),
            path=path,
        )
        if member.is_orchestrator:
            # A Set with two Order-0 plans is malformed; keep the FIRST deterministically (paths are
            # sorted) and treat the rest as children, so the extra one shows up as an unfinished
            # member rather than being silently dropped.
            if orchestrator is None:
                orchestrator = member
            else:
                children.append(member)
        else:
            children.append(member)

    children.sort(key=lambda m: (m.order is None, m.order or 0, m.id6))
    return SetMembership(
        setid=token,
        orchestrator=orchestrator,
        children=tuple(children),
        resolution_note=note,
    )


def _split_table_row_naive(line: str) -> list[str]:
    """Split a `| a | b |` row on every pipe, exactly as this module has always done.

    Kept as a named function ONLY so :func:`child_table_rows` can take a splitter and both consumers
    can share ONE row-walk. It is NOT backtick-aware: a pipe inside a backtick span shifts every
    later column, which is why the digest uses the other splitter (see :func:`child_table_rows`).
    """

    match = _TABLE_ROW_RE.match(line)
    body = match.group("body") if match else line
    return [c.strip() for c in body.split("|")]


def _split_table_row_backtick_aware(line: str) -> list[str]:
    """Split a row WITHOUT breaking on a pipe inside a backtick span.

    THE SPLITTER ITSELF IS NOT RE-IMPLEMENTED HERE. ``ipd_set_plan._split_table_row`` already exists
    for exactly this reason (``setgraph`` E-01: a backticked pipe silently rejected four
    orchestrators whose header was canonical), and this Set spends an item per child on NOT forking a
    symbol. So this is a thin adapter over that one definition, imported LAZILY for the reason the
    section note above gives (that module's closure is heavy and most runs never reach this code).
    Importing a private name across modules is the deliberate trade: the alternative is a second copy
    of a 25-line parser whose two versions would silently disagree, which is precisely the failure
    ``2r306y``/``818uru`` made this module's admission rule about. ``ipd_set_plan`` imports
    ``runner_shared`` only lazily inside one CLI function, so there is no module-level cycle.

    Falls back to the naive split if that private helper is ever renamed, because a digest that
    RAISES would take down a run over a table-formatting detail; a digest computed with the naive
    split is still stable and still child-table sensitive, merely coarser on a backticked pipe.
    """

    try:
        from agent_workflows.ipd_set_plan import (  # noqa: PLC0415 - see the docstring
            _split_table_row,
        )
    except Exception:  # pragma: no cover - defensive: never fail a run over a splitter
        return _split_table_row_naive(line)
    return [c.strip() for c in _split_table_row(line)]


def child_table_rows(
    orchestrator_text: str, *, backtick_aware: bool = True
) -> tuple[tuple[str, ...], ...]:
    """Every row of an orchestrator's `## Child IPDs...` table, as FULL CELL TUPLES.

    THE HEADER ROW IS INCLUDED and rows come back in DOCUMENT ORDER; only the markdown
    alignment/separator row (`|---|:--:|`) is dropped, because it is layout rather than content.
    Nothing else is filtered: a caller that wants only Order tokens takes cell 0 itself, which is
    what :func:`parse_declared_child_orders` now does.

    WHY THIS EXISTS AS ITS OWN FUNCTION (orchprobe-02 `8tgg6g` E-01). `parse_declared_child_orders`
    already located this section by schema heading, matched its rows and skipped its alignment row,
    and then discarded every cell but the first. The probe cache needs the SAME rows with ALL their
    cells, and a second scanner would give the retirement gate and the cache two different
    definitions of "a child row". So the row-walk is factored here and BOTH call it.

    WHY THE CELL TEXT AND NOT A PARSED GRAPH, which is the whole reason the probe digest can exist.
    ``ipd_set_plan.parse_child_table`` returns ``{order: (dep_orders,)}`` and nothing else, so
    swapping a child's Id or rewriting its description leaves its result BYTE-IDENTICAL (measured on
    `yeh7gc`: ``{'1': (), '2': (), '3': ()}`` before and after both edits). A cache keyed on that
    would be blind to exactly the edits a coverage question turns on, and since the probe SENDS the
    child table as its payload, an edit the key ignores would serve a STALE verdict under apparent
    authority. Keyed on cell text, all three edits move the key.

    ``backtick_aware`` selects the splitter, and the DEFAULT is the safe one:

      * ``True``  -> ``ipd_set_plan._split_table_row``, which does not break on a pipe inside a
        backtick span. Required for an ALL-CELLS consumer: measured 2026-09-14, three live
        orchestrators (`94dhrt`, `mvz3d2`, `rreixg`) contain such a row, one splitting 12 cells
        instead of 4, so a backticked plan filename would fragment into bogus columns.
      * ``False`` -> the historical naive ``split("|")``, preserved for
        :func:`parse_declared_child_orders`, which reads only cell 0. Measured on the same corpus,
        cell 0 is IDENTICAL under both splitters for every row of every orchestrator, so that
        function's behavior is bit-for-bit what it was; it is deliberately left on the naive split
        rather than being changed by a plan whose subject is the cache.
    """

    from agent_workflows import (
        ipd_schema as _ipd_schema,
    )  # local: see the section note above

    heading = getattr(_ipd_schema, "H_CHILD_IPDS", _CHILD_IPDS_HEADING)
    split = (
        _split_table_row_backtick_aware if backtick_aware else _split_table_row_naive
    )
    rows: list[tuple[str, ...]] = []
    in_section = False
    for raw in (orchestrator_text or "").splitlines():
        if raw.startswith("## "):
            in_section = raw[3:].strip() == heading
            continue
        if not in_section:
            continue
        if not _TABLE_ROW_RE.match(raw):
            continue
        cells = split(raw)
        if not cells:
            continue
        if all(_TABLE_SEPARATOR_CELL_RE.match(c or "-") for c in cells if c != ""):
            continue  # alignment row: layout, not a declared child
        rows.append(tuple(cells))
    return tuple(rows)


def parse_declared_child_orders(orchestrator_text: str) -> tuple[tuple[str, ...], bool]:
    """Read the Order tokens an orchestrator's child table DECLARES.

    Returns `(tokens, parsed)`. `parsed` is False when no table row could be recognized at all, which
    the caller MUST treat as a refusal (spec R-3 + OQ-2): an unparseable table is not evidence that a
    Set is fully authored.

    WHY THIS IS PARSED POSITIONALLY, WITH MEASUREMENTS, because assuming one column layout is exactly
    how this check would silently pass everything. The five live orchestrators use FIVE layouts and
    share ONLY the first column:

        orchretire  | Order | Id | Child | Depends on |
        wslayout    | Order | Id | What it does | Set dependencies |
        runprofile  | Order | Id | Child | Responsibility | Depends on |
        lanectn     | Order | Id | Depth | Requirements owned | Prerequisite | What it delivers |
        rununify    | Order | What it does | Depends on |          <- NO `Id` COLUMN AT ALL

    So a parser that located a named `Id` header would CRASH or vacuously pass on `rununify`, the one
    Set this check exists for. The Order token is therefore read from the FIRST cell, positionally,
    and no `Id` column is required.

    ROW TOKENS ARE NOT ALL NUMERIC, also measured: `rununify` declares a row `03+` AND a row whose
    token is the word `last`. Those are returned as tokens like any other; the CALLER resolves them,
    and since neither can ever resolve to an Order they refuse. That keeps this function a parser and
    puts the policy in one place.

    THE ROW-WALK IS NOW SHARED with the probe cache's digest (orchprobe-02 `8tgg6g` E-01): it comes
    from :func:`child_table_rows`, so the retirement gate and the cache cannot disagree about what a
    child row IS. This function keeps its OWN behavior exactly: it asks for the historical naive
    split (`backtick_aware=False`), because it reads only cell 0 and cell 0 is measured IDENTICAL
    under both splitters across every live orchestrator, so a plan about the cache does not get to
    change what this gate parses.
    """

    tokens: list[str] = []
    saw_row = False
    for cells in child_table_rows(orchestrator_text, backtick_aware=False):
        first = cells[0] if cells else ""
        if not first:
            continue
        saw_row = True
        # Strip the decorations a prose table uses around a token (`` `01` ``, `**01**`).
        token = first.strip("`*_ ").strip()
        if not token:
            continue
        if token.lower() in {"order", "orders"}:
            continue  # the header row itself
        tokens.append(token)
    return tuple(tokens), saw_row


def find_unauthored_child_rows(
    orchestrator_text: str, membership: SetMembership
) -> tuple[tuple[str, ...], bool]:
    """Return `(unauthored_tokens, parsed)`: the declared rows that resolve to NO plan (spec R-3).

    THE COMPARISON IS ONE-DIRECTIONAL AND MUST STAY THAT WAY. It refuses only when a DECLARED row
    resolves to nothing. It does NOT refuse when a resolved child has no declared row, because disk
    can legitimately hold MORE children than the table lists: `runprofile` declares Orders 01-05 and
    has SIX children on disk (`kgpptv`, Order 6). A symmetric "table and disk must match" rule would
    refuse a legitimately-extended Set forever. That direction is R-2's business anyway - an extra
    child is simply not `executed` yet - not R-3's.

    A non-numeric or open-ended token (`03+`, `last`) can never resolve to an Order, so it lands in
    `unauthored_tokens` and refuses. Per spec OQ-2 the maintainer accepted that explicitly: the worst
    case is a FALSE REFUSAL, in which an orchestrator lingers exactly as it does today.
    """

    declared, parsed = parse_declared_child_orders(orchestrator_text)
    if not parsed:
        return (), False
    present = {m.order for m in membership.children if m.order is not None}
    unauthored: list[str] = []
    for token in declared:
        match = _ORDER_TOKEN_RE.match(token)
        if match is None:
            unauthored.append(token)  # `03+`, `last`, or anything else unresolvable
            continue
        if int(match.group("order")) not in present:
            unauthored.append(token)
    return tuple(unauthored), True


def evaluate_set_retirement(repo: Path, setid: str) -> RetirementDecision:
    """Decide whether `setid`'s orchestrator may be retired, with a TYPED reason for any refusal.

    Eligible ONLY when ALL of the following hold (spec R-1/R-2/R-3):
      1. the Set has an orchestrator on disk;
      2. the Set has at least one child;
      3. EVERY child's on-disk `Status:` is exactly `executed` (an allowlist, per
         :data:`SET_RETIREMENT_DONE_STATUS`); and
      4. the orchestrator's child table declares no row that resolves to no plan, and its table was
         parseable at all.

    Refusals are checked in that order so the reported reason is the most fundamental one, and each
    carries the specifics: unfinished children come back WITH their actual statuses, unauthored rows
    WITH their literal tokens.

    DECIDES ONLY. It writes nothing, moves nothing, and calls no transition.
    """

    membership = read_set_membership(repo, setid)
    token = membership.setid

    if membership.orchestrator is None:
        detail = (
            f"Set {token!r} has no Order-0 orchestrator plan on disk, so there is "
            "nothing to retire"
        )
        if membership.resolution_note:
            detail = f"Set {token!r}: {membership.resolution_note}"
        return RetirementDecision(
            eligible=False,
            reason=RETIRE_REFUSED_NO_ORCHESTRATOR,
            setid=token,
            detail=detail,
        )

    if not membership.children:
        return RetirementDecision(
            eligible=False,
            reason=RETIRE_REFUSED_NO_CHILDREN,
            setid=token,
            detail=(
                f"Set {token!r} has no child plans on disk; retirement is gated on children "
                "being executed, and a Set with none has demonstrated nothing"
            ),
        )

    unfinished = tuple(
        (m.id6, m.status or "<no Status:>")
        for m in membership.children
        if m.status != SET_RETIREMENT_DONE_STATUS
    )
    if unfinished:
        listed = ", ".join(f"{i} ({s})" for i, s in unfinished)
        return RetirementDecision(
            eligible=False,
            reason=RETIRE_REFUSED_UNFINISHED_CHILDREN,
            setid=token,
            unfinished=unfinished,
            detail=(
                f"Set {token!r} has {len(unfinished)} child(ren) that are not "
                f"{SET_RETIREMENT_DONE_STATUS!r}: {listed}"
            ),
        )

    try:
        orch_text = membership.orchestrator.path.read_text(
            encoding="utf-8", errors="replace"
        )
    except OSError as exc:
        return RetirementDecision(
            eligible=False,
            reason=RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS,
            setid=token,
            detail=(
                f"Set {token!r}: the orchestrator's child table could not be read "
                f"({exc}), so whether the child set is fully authored is unknown"
            ),
        )

    unauthored, parsed = find_unauthored_child_rows(orch_text, membership)
    if not parsed:
        return RetirementDecision(
            eligible=False,
            reason=RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS,
            setid=token,
            detail=(
                f"Set {token!r}: no rows could be parsed from the orchestrator's "
                f"'{_CHILD_IPDS_HEADING}' table, so whether the child set is fully authored "
                "is unknown; refusing rather than assuming it is"
            ),
        )
    if unauthored:
        return RetirementDecision(
            eligible=False,
            reason=RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS,
            setid=token,
            unauthored_rows=unauthored,
            detail=(
                f"Set {token!r}: the orchestrator's child table declares row(s) "
                f"{', '.join(repr(t) for t in unauthored)} that resolve to no plan, so the "
                "child set is not fully authored"
            ),
        )

    executed = ", ".join(m.id6 for m in membership.children)
    return RetirementDecision(
        eligible=True,
        reason=RETIRE_ELIGIBLE,
        setid=token,
        detail=(
            f"Set {token!r} is complete on disk: all {len(membership.children)} "
            f"child(ren) are {SET_RETIREMENT_DONE_STATUS} ({executed}), and every row of the "
            "orchestrator's child table resolves to a plan"
        ),
    )


# ==================================================================================================
# orchprobe-02 (`8tgg6g`): THE ORCHESTRATOR PROBE VERDICT CACHE, KEYED ON CONTENT
# ==================================================================================================
#
# WHAT THIS IS FOR. Child 03 (`m7gvuz`) asks a MODEL whether an orchestrator carries work no child
# covers. That answer costs tokens and time, and re-asking it about an UNMODIFIED orchestrator buys
# nothing, so the verdict is cached against a digest of the orchestrator's content.
#
# WHY NOT A WHOLE-FILE HASH, which is the obvious key and a MEASURED dead end. `ipd_lifecycle`
# already tried it: `plan_content_digest` hashes exact bytes, and `frozen_region_digest` exists
# precisely because that made a begin receipt "go stale on every CORRECT execution" (backlog
# `xmqv5l`). A conforming executor MUST tick checkboxes, fill `Observed evidence` and append
# `## Workflow history`, so the byte digest changed while the reviewed contract had not. A
# byte-keyed probe cache would repeat that error and re-spend on every tick.
#
# WHY NOT REUSE `frozen_region_digest`, since it already solves most of this. Measured at review and
# RE-MEASURED at execution: it is UNCHANGED by a checkbox tick, a filled `Observed evidence`, an
# appended history line and a prose edit, and it DOES change on an E-item action edit. Four of the
# five properties this cache needs already hold. The ONE gap is the one that matters here: a
# CHILD-TABLE edit leaves it unchanged, because `_requirements_from_plan` reads only `Scope-Paths`,
# E-item text and V-item text. Child-table sensitivity is therefore the SOLE reason this function
# exists, which is why `probe_cache_digest` includes the child table's ROW CELLS and why the test
# module proves that specific difference rather than asserting parity.
#
# AND WHY THE ROW CELLS RATHER THAN A PARSED GRAPH. `ipd_set_plan.parse_child_table` returns
# `{order: (dep_orders,)}`, so an Id swap and a description rewrite leave it BYTE-IDENTICAL while
# only adding or removing a row moves it. Since child 03 SENDS the child table as the probe payload,
# a row edit the key ignored would serve a STALE verdict under apparent authority - the one way this
# cache can be actively wrong rather than merely useless. Payload and key are the same two inputs
# BY CONSTRUCTION: `probe_cache_payload` is what both read.
#
# WHAT IS DELIBERATELY DROPPED relative to `frozen_region_digest`: `Scope-Paths` and V-item text.
# The probe reasons about neither (it asks whether the parent's ACTIONS are covered by children), so
# including them would re-probe on an edit that cannot change the answer.
#
# THE TWO EXISTING DIGESTS ARE NOT TOUCHED. `frozen_region_digest` is a begin-receipt gate input and
# `plan_content_digest` is the receipt's identity; changing either would alter an unrelated safety
# check. This is a THIRD function with a different purpose.

#: The tri-state a cache read returns. `unknown` is what a MISS resolves to, and child 03 must treat
#: it as blocking: the entire point of the gate is that silence stops meaning safe. A tri-state
#: rather than `Optional[bool]` because a cached FAIL and an absent entry are different facts and a
#: caller that cannot tell them apart cannot report the right thing.
PROBE_VERDICT_PASS = "pass"
PROBE_VERDICT_FAIL = "fail"
PROBE_VERDICT_UNKNOWN = "unknown"

#: The store's schema version, so a later shape change can be detected rather than mis-parsed.
PROBE_VERDICT_STORE_SCHEMA_VERSION = 1

#: The store's filename under the checkout's `.aw/state/runtime/` control tree.
_PROBE_VERDICT_STORE_NAME = "orchestrator-probe-verdicts.json"

#: How long a recorded verdict stays trustworthy, in days.
#:
#: WHY A BOUND AT ALL, given the digest already proves the orchestrator has not changed: a digest
#: match says nothing about whether the ANSWER is still trustworthy. This cache stores LLM output,
#: and an unbounded cache of LLM verdicts eventually answers for a model nobody would ask. The store
#: records WHICH model answered for that reason, and this bound is what makes that record actionable
#: instead of decorative.
#:
#: WHY 30 DAYS. It is long enough that the cache actually saves the re-probes it exists to save
#: (an orchestrator typically sits in `pending/` for days to weeks), and short enough that a verdict
#: cannot outlive the model generation that produced it by much - vendor model turnover here is
#: measured in weeks. Callers may override per read; nothing hardcodes it at a call site.
DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS = 30

#: Why a stored verdict was NOT served, so a caller can say which guard rejected it rather than only
#: that something did. Empty when the verdict WAS served.
PROBE_STALE_MISS = "no-entry"
PROBE_STALE_CORRUPT = "unreadable-entry"
PROBE_STALE_MODEL_CHANGED = "model-changed"
PROBE_STALE_TOO_OLD = "older-than-bound"


class ProbeVerdict(NamedTuple):
    """A cache READ result: the verdict actually served, plus what the store held.

    `verdict` is one of the three `PROBE_VERDICT_*` values and is the ONLY field a gate may act on.
    `recorded_verdict`, `recorded_at` and `model` describe the stored entry (empty when there was
    none), so a caller can report "a fail was recorded by <model> on <date> but is past the bound"
    rather than a bare `unknown`. `stale_reason` is one of the `PROBE_STALE_*` values, or empty when
    the stored verdict was served as-is.

    READS ONLY. Nothing here writes, and a read never repairs the store.
    """

    verdict: str
    recorded_verdict: str = ""
    recorded_at: str = ""
    model: str = ""
    stale_reason: str = ""

    @property
    def is_hit(self) -> bool:
        """True iff a stored verdict was SERVED (not merely present)."""
        return not self.stale_reason


def probe_cache_payload(orchestrator_text: str) -> dict[str, Any]:
    """The exact two inputs the probe reasons about: E-item ACTION TEXT and child-table ROW CELLS.

    Returned as a mapping rather than a string so child 03 can render the SAME object into its
    prompt that :func:`probe_cache_digest` hashes. That identity is a requirement, not a
    convenience: if the probe reads something the key does not cover, editing that thing serves a
    stale verdict.

    Deterministic by construction: E-item texts are SORTED (the digest must not depend on document
    order of two textually identical items) and rows are kept in DOCUMENT ORDER as tuples-of-cells,
    since a table's order is part of what it says.

    THE ACTION TEXT IS TAKEN STRUCTURALLY, not by a text rule: `ipd_lint.parse` puts a leaf's
    indented `- Key: value` sub-fields in `Leaf.fields` and its checkbox in `Leaf.checked`, while
    `Leaf.text` is the action alone. That is why ticking a box, filling `Observed evidence` or
    appending history CANNOT move this payload - the same structural exclusion
    `ipd_lifecycle.frozen_region_digest` relies on, for the same `xmqv5l` reason.
    """

    from agent_workflows import ipd_lint as _lint  # local: see the section note above

    doc = _lint.parse(orchestrator_text or "")
    return {
        "e_items": sorted(
            lf.text for lf in doc.exec_leaves if lf.kind == "E" and lf.text.strip()
        ),
        "child_table_rows": [list(row) for row in child_table_rows(orchestrator_text)],
    }


def probe_cache_digest(orchestrator_text: str) -> str:
    """A stable sha256 over ONLY what an orchestrator-coverage probe's answer depends on.

    COVERED (a change here re-probes): each E-item's action text, and the child table's row cells
    (header row included, in document order).

    NOT COVERED (a change here must NOT re-probe): the `[ ]`/`[x]` checkbox marks, `Execution
    state:`, `Result:`, `Observed evidence:`, `## Workflow history`, and every prose section -
    INCLUDING the explanatory paragraphs that sit inside the `## Child IPDs...` section beside its
    table, which are not the table.

    DELIBERATE DIVERGENCE FROM :func:`ipd_lifecycle.frozen_region_digest`, stated because the
    overlap is large and the difference is the entire justification for a second function:

      * CHILD-TABLE ROWS ARE IN here and are OUT there. That is the only new sensitivity, and it is
        why this exists: `_requirements_from_plan` reads only `Scope-Paths`, E-item text and V-item
        text, so a child-table edit does not move the frozen digest (measured).
      * `Scope-Paths` and V-ITEM TEXT ARE OUT here and are IN there. The probe asks whether the
        parent's ACTIONS are covered by children; neither a scope entry nor a validation row can
        change that answer, so including them would re-probe for nothing.

    Serialization is deterministic (`sort_keys=True` over the payload above), so the digest is
    stable across processes and dict-ordering changes.
    """

    serialized = json.dumps(
        probe_cache_payload(orchestrator_text), sort_keys=True, ensure_ascii=True
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def probe_verdict_store_path(repo_root: Path) -> Path:
    """The verdict store: `<checkout>/.aw/state/runtime/orchestrator-probe-verdicts.json`.

    ROUTED THROUGH `ipd_lifecycle.checkout_control_root`, never composed as `repo_root/".aw"/...`,
    for the reason backlog `dh0uno` recorded: an in-lane invocation's `repo_root` is the LANE, so
    hand-composition produced a SECOND control store the driver could not see and lane teardown then
    deleted. Every linked worktree of a checkout therefore resolves to ONE store, which is what makes
    a verdict recorded inside a lane visible to the driver that launched it.

    Sited beside the begin receipts and the finalize journals (`state/`), which is machine-local by
    framework policy: `install_wizard` raises `InvalidPolicyError` for a policy that would TRACK
    `state_runtime`, and the framework-owned `.aw/.gitignore` ships an anchored `/state/` entry in
    BOTH `_AW_GITIGNORE_TEMPLATE` and the `_ensure_aw_gitignore` back-fill (landed 2026-09-12,
    commit `ee38864c`), so the file is ignored in a fresh ADOPTER and not only here. That matters
    because the entries record LLM verdicts against machine-local plan content; a tracked store would
    be a leak-sanitizer concern, not merely untidiness.
    """

    from agent_workflows import (
        ipd_lifecycle as _lifecycle,
    )  # local: see the section note above

    return (
        _lifecycle.checkout_control_root(repo_root)
        / "state"
        / "runtime"
        / _PROBE_VERDICT_STORE_NAME
    )


def _read_probe_verdict_store(repo_root: Path) -> dict[str, Any]:
    """The store's `entries` mapping, or `{}` when it is absent, unreadable or malformed.

    A CORRUPT STORE READS AS EMPTY rather than raising. The cache is an optimization: a caller that
    crashes because a JSON file was truncated by a power loss has converted a saved token into a
    failed run, and the fail-closed direction here is a MISS, which blocks. So every error path
    returns `{}` and the gate re-probes.
    """

    path = probe_verdict_store_path(repo_root)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(raw, dict):
        return {}
    entries = raw.get("entries")
    if not isinstance(entries, dict):
        return {}
    return entries


def record_probe_verdict(
    repo_root: Path,
    digest: str,
    verdict: str,
    *,
    model: str | None,
    recorded_at: str | None = None,
) -> Path:
    """Store `verdict` under `digest`, with WHEN and WHICH MODEL answered. Returns the store path.

    BOTH POLARITIES ARE CACHED, per the maintainer's OQ-01 ruling, and re-evaluate-on-change is what
    makes a cached FAIL safe: the remedy for "this orchestrator carries uncovered work" is to move
    that work into a new child, which edits BOTH the parent's checklist text and its child table,
    and the digest covers both. So a genuine fix changes the key and discards the entry; a stale
    complaint cannot be served. `tests/test_orchestrator_probe_cache.py` proves that with the fixture
    the ruling specified, and proves the test can FAIL by mutating the digest to ignore the rows.

    `model` may be `None`. That is not defensive: `runner_profiles.resolve` returns `model=None` with
    provenance `host-default` whenever no flag, named profile or per-runner default supplies one, and
    the runner prints `model=(host default)` for it, so a run frequently cannot name the model it is
    about to use. It is recorded as an empty string and :func:`read_probe_verdict` decides what an
    absent model means (see its docstring).

    Writes ATOMICALLY through :func:`atomic_write_json` (the module's existing helper), so a crash
    mid-write cannot leave a half-written store; and it merges rather than replaces, so recording one
    verdict never discards another orchestrator's.
    """

    if verdict not in (PROBE_VERDICT_PASS, PROBE_VERDICT_FAIL):
        raise ValueError(
            "a probe verdict store holds only "
            f"{PROBE_VERDICT_PASS!r} or {PROBE_VERDICT_FAIL!r}; refusing to record "
            f"{verdict!r}. {PROBE_VERDICT_UNKNOWN!r} is the ABSENCE of an answer and "
            "recording it would turn 'not probed' into a stored fact"
        )
    entries = dict(_read_probe_verdict_store(repo_root))
    entries[str(digest)] = {
        "verdict": verdict,
        "recorded_at": recorded_at or utc_now(),
        "model": model or "",
    }
    path = probe_verdict_store_path(repo_root)
    atomic_write_json(
        path,
        {
            "schema_version": PROBE_VERDICT_STORE_SCHEMA_VERSION,
            "entries": entries,
        },
    )
    return path


def read_probe_verdict(
    repo_root: Path,
    digest: str,
    *,
    model: str | None = None,
    max_age_days: int = DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS,
    now: "dt.datetime | None" = None,
) -> ProbeVerdict:
    """Read the verdict for `digest`, FAILING CLOSED to `unknown`.

    A MISS IS `unknown`, NEVER `pass`. "Not probed" and "probed and cleared" are different facts,
    and a cache whose miss looked like a pass would silently restore the exact
    silence-means-safe behavior this gate exists to end.

    THE STALENESS RULE, and it discriminates rather than rejecting everything:

      1. NO ENTRY, or an entry that is not a usable object / carries no recognized verdict ->
         `unknown` (`no-entry` / `unreadable-entry`).
      2. OLDER THAN `max_age_days` -> `unknown` (`older-than-bound`). This is the guard that ALWAYS
         applies, deliberately, and see (3) for why that phrasing is load-bearing.
      3. RECORDED BY A DIFFERENT MODEL than the caller names -> `unknown` (`model-changed`).
         A verdict is only as good as its author, so a run using a different model re-probes.
      4. Otherwise the recorded verdict is served as-is.

    THE `model=None` CASE IS DECIDED, NOT DISCOVERED, because it is the COMMON case: measured,
    `runner_profiles.resolve` returns `model=None` with provenance `host-default` whenever nothing
    supplies one. DECISION: when EITHER side's model is unknown (the caller passes `None`/empty, or
    the entry recorded none), the model comparison is SKIPPED and the TIME BOUND alone decides.
    The rejected alternative was "an unknown model never matches", i.e. re-probe: it is superficially
    the fail-closed choice, but since the host-default case is routine it would make the cache miss
    almost always, which is a cache that does not exist. It would also be a rule whose primary key is
    a value that is usually absent. The time bound still applies in full, so an unnameable model
    buys age tolerance and nothing else; the honest limit, stated rather than hidden, is that a
    verdict from an unnamed model A can be served to a run that is also using an unnamed model B
    within the bound.

    An unparseable `recorded_at` is treated as INFINITELY OLD (`older-than-bound`), never as fresh:
    the failure direction for a timestamp we cannot read is to re-probe.
    """

    entries = _read_probe_verdict_store(repo_root)
    raw = entries.get(str(digest))
    if raw is None:
        return ProbeVerdict(
            verdict=PROBE_VERDICT_UNKNOWN, stale_reason=PROBE_STALE_MISS
        )
    if not isinstance(raw, dict):
        return ProbeVerdict(
            verdict=PROBE_VERDICT_UNKNOWN, stale_reason=PROBE_STALE_CORRUPT
        )
    recorded = str(raw.get("verdict") or "")
    recorded_at = str(raw.get("recorded_at") or "")
    recorded_model = str(raw.get("model") or "")
    if recorded not in (PROBE_VERDICT_PASS, PROBE_VERDICT_FAIL):
        return ProbeVerdict(
            verdict=PROBE_VERDICT_UNKNOWN,
            recorded_verdict=recorded,
            recorded_at=recorded_at,
            model=recorded_model,
            stale_reason=PROBE_STALE_CORRUPT,
        )

    stale = ProbeVerdict(
        verdict=PROBE_VERDICT_UNKNOWN,
        recorded_verdict=recorded,
        recorded_at=recorded_at,
        model=recorded_model,
    )

    # (2) The bound that always applies.
    moment = now or dt.datetime.now(dt.timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=dt.timezone.utc)
    try:
        stamped = dt.datetime.fromisoformat(recorded_at)
    except ValueError:
        return stale._replace(stale_reason=PROBE_STALE_TOO_OLD)
    if stamped.tzinfo is None:
        stamped = stamped.replace(tzinfo=dt.timezone.utc)
    if (moment - stamped) > dt.timedelta(days=max_age_days):
        return stale._replace(stale_reason=PROBE_STALE_TOO_OLD)

    # (3) The model guard, skipped when either side cannot name a model (see the docstring).
    current_model = (model or "").strip()
    if current_model and recorded_model and current_model != recorded_model:
        return stale._replace(stale_reason=PROBE_STALE_MODEL_CHANGED)

    return ProbeVerdict(
        verdict=recorded,
        recorded_verdict=recorded,
        recorded_at=recorded_at,
        model=recorded_model,
    )


# ==================================================================================================
# orchretire-03 (`pgq326`): THE SHARED ACTION DECIDER AND THE SHARED DISPATCH OUTCOME
# (spec `77tr3o` R-7, R-8, R-9, R-10)
# ==================================================================================================
#
# THE TWO THINGS THIS SECTION OWNS, and why they are one section rather than two.
#
# FIRST, THE ACTION DECISION (`determine_action` / `action_for`, E-04). It was defined in `oc_runipd`
# only. `agy_runipd` had its own `determine_action` and NO `action_for` at all, so measured at HEAD
# `844d195c`: `agy.determine_action('approved')` returned `'execute'` where
# `oc.action_for('orchestrator','approved')` returned `'orchestrate'`. `aw agy run` would therefore
# AGENT-EXECUTE an approved orchestrator - spending a turn authoring against a plan whose entire
# coordination role the runner has already superseded. That is a worse failure than oc's lingering
# orchestrator, because it produces work rather than merely omitting it.
#
# SECOND, THE DISPATCH OUTCOME (`decide_orchestrator_dispatch`, E-01/E-02/E-07). Deciding the action
# is not enough: a host that DECIDES `orchestrate` and then has no branch reading it spends the agent
# turn anyway. So the OUTCOME of dispatching an `orchestrate` item lives here too, and both hosts call
# it. Keeping the pair together is deliberate: `action_for` is what makes an item reach this outcome,
# so a reader who finds one immediately sees the other.
#
# WHY BOTH LIVE HERE RATHER THAN IN `oc_runipd`. The anti-re-fork discipline `2r306y`/`818uru`
# established is binding: shared runner logic has ONE definition in this module and is IMPORTED by
# both hosts. `agy_runipd` already imports ~40 names FROM `oc_runipd` (tracked as backlog `cnwy8g`),
# so adding to that pile would deepen a layering defect the repo is actively paying down. And a
# COPY is the specific failure spec R-10 names: two identical bodies have no disagreement today, which
# is exactly why nothing signals when one is edited.
#
# ---- THE THREE-WAY OUTCOME, WHICH REPLACES ONE `else` --------------------------------------------
#
# The pre-`pgq326` dispatch branch (`oc_runipd.py:6993-7031`) wrote ONE status on ANY failure:
#
#     else:
#         runnable["status"] = "dependency-blocked"
#
# `dependency-blocked` is in `TERMINAL_STATES`, and the selection filter admits only `queued`, so the
# orchestrator was excluded FOREVER - even when its children all finished later in the SAME run. The
# event was literally named `orchestrator-deferred`, and a deferral is by definition something you
# return to.
#
# But "just leave it queued" (backlog `kxkc04`'s prescription) is correct for only ONE of the failures
# that `else` covered. Two distinct reasons were recorded on a single real run: `5e4sb6 |
# not-all-children-executed` and `rh5tt6 | finalize-refused`. Leaving the SECOND reconsiderable would
# retry a structural refusal on every loop iteration and SPIN FOREVER, which is the one regression
# worse than the bug. Hence three outcomes, not two:
#
#   * RETIRE      - eligible per child 01's predicate; perform child 02's transition.
#   * RECONSIDER  - children merely UNFINISHED. Write NO status, exactly as an item skipped by the
#                   inner selection pass already does, so a later iteration re-tests it.
#   * TERMINATE   - it can never become eligible: a child reached a non-success terminal state, the
#                   child set is unauthored, the Set has no children, or the transition itself
#                   refused. Say so terminally rather than spinning.
#
# RECONSIDER IS A CLAIM ABOUT RE-SELECTION, NOT MERELY ABOUT NOT WRITING A STATUS. "Not terminal" and
# "reachable again" are different properties and only the second one fixes the bug; see
# `ORCH_DISPATCH_RECONSIDER` below for the two mechanisms that were checked.

#: The three dispatch outcomes. A typed vocabulary rather than prose, for the same reason child 01's
#: `RetirementDecision.reason` is one: a caller must not have to string-match a message to know what
#: happened, and a host that switches on these cannot silently mishandle a case it does not know.
ORCH_DISPATCH_RETIRE = "retire"
#: Leave the item `queued` so a LATER ITERATION OF THE SAME RUN re-tests it (spec R-7).
#:
#: WHAT WAS VERIFIED, because writing no status is necessary and NOT sufficient. Two mechanisms sit
#: between "unlabelled" and "re-selected", and both were checked rather than assumed (E-01/V-01):
#:   1. THE SELECTION PASS admits an item only when `dependency_status(item, state)` reports
#:      satisfied. For an `orchestrate` item that predicate consults the children itself, so once the
#:      last child reaches `executed` the orchestrator becomes satisfiable and IS re-selected.
#:   2. `cascade_dependency_blocked` runs at the TOP of every iteration and propagates
#:      `dependency-blocked` over reverse edges to a fixed point. It reads only the item's DECLARED
#:      `dependencies` edges, and an orchestrator's implicit child-set relationship is not one, so it
#:      does not relabel an orchestrator left `queued` on account of its children. It WILL relabel one
#:      whose own declared edge died, which is correct and is TERMINATE's job anyway.
ORCH_DISPATCH_RECONSIDER = "reconsider"
#: Write a terminal status: this orchestrator can NEVER become eligible (spec R-8).
ORCH_DISPATCH_TERMINATE = "terminate"

#: The refusal causes, kept DISTINGUISHABLE in the durable record (spec R-9). Before this, all four
#: collapsed into `dependency-blocked` plus an `unsatisfied_dependencies` list that was EMPTY for both
#: observed cases, producing a run summary reading "dependency-blocked (unmet dependencies)" while
#: naming no dependency at all. Each value below is carried in the `orchestrator-deferred` event's
#: `reason` field, so the record names the actual cause.
ORCH_REASON_UNFINISHED_CHILDREN = "children-unfinished"
ORCH_REASON_DEAD_CHILDREN = "children-terminally-failed"
#: Unfinished children that THIS RUN will not act on (absent from its queue, or already terminal in it
#: without reaching `executed` on disk). A FIFTH reason beyond the spec's four, added because E-03
#: MEASURED a spin the spec's four could not express: the run cannot finish them, so reconsidering
#: would repeat the same decision every iteration, and the drain path never sees it because the
#: orchestrator stays selectable. Terminating names the real obstacle instead.
ORCH_REASON_CHILDREN_NOT_IN_RUN = "children-not-in-this-run"
ORCH_REASON_NO_CHILDREN = "no-children"
ORCH_REASON_UNAUTHORED_CHILD_ROWS = "unauthored-child-rows"
ORCH_REASON_FINALIZE_REFUSED = "finalize-refused"
ORCH_REASON_NO_ORCHESTRATOR = "no-orchestrator"


class OrchestratorDispatch(NamedTuple):
    """What a host should DO with an `orchestrate` item, with a reason it can substantiate.

    `outcome` is one of the three `ORCH_DISPATCH_*` values. `reason` is one of the `ORCH_REASON_*`
    values (empty for RETIRE). `detail` is one human-readable sentence, always populated, safe to put
    straight into an event payload. `unfinished` carries `(id6, status)` pairs so the record can say
    WHY a child does not count rather than only that it does not - the `5e4sb6` defect.

    DECIDES ONLY. It writes no status, performs no transition, and touches no file.
    """

    outcome: str
    reason: str
    detail: str
    unfinished: tuple[tuple[str, str], ...] = ()
    unauthored_rows: tuple[str, ...] = ()
    #: The eligibility verdict this decision was derived from, passed on to the transition so it
    #: VALIDATES the same verdict rather than recomputing a possibly-different one.
    eligibility: RetirementDecision | None = None


def determine_action(status: str) -> str:
    """Return 'review' for to-review/draft plans; 'execute' for approved/ready plans."""
    norm = (status or "").lower().strip()
    if norm in ("to-review", "draft"):
        return "review"
    return "execute"


#: Statuses that mean "this plan still has work to do in this run", so its queue entry starts
#: `queued` and the selection loop may dispatch it. Everything else is already TERMINAL on disk.
NON_TERMINAL_QUEUE_STATUSES: frozenset[str] = frozenset(
    ("to-review", "draft", "approved", "auto-approved", "reusable")
)

#: On-disk terminal statuses that are PRESERVED verbatim onto the queue entry.
#:
#: DELIBERATELY `executed` ALONE, and the omissions were verified rather than assumed. A queue status
#: is only safe to write if BOTH vocabularies already admit it: the drivers' `TERMINAL_STATES` (or the
#: cascade cannot act on it) and `runner_shutdown.KNOWN_ITEM_STATUSES` (or Phase 0's R3 ledger
#: -coherence check calls the run "in an undefined state" and refuses its own resume). Measured:
#: `executed` is in both; `superseded` and `not-executed` are in NEITHER. So preserving those two
#: would trade a cascade bug for a resume-refusing ledger, which is strictly worse.
#:
#: They therefore keep falling back to `reviewed`, which is CORRECT FOR THEM BY OUTCOME even though
#: the name is imprecise: both are non-success terminal states, `reviewed` is not in
#: `EXECUTION_SUCCESS_STATES`, so a dependent of a superseded plan still refuses to run. Only
#: `executed` was being given the WRONG OUTCOME, and only `executed` needs to change.
TERMINAL_QUEUE_STATUSES: frozenset[str] = frozenset(("executed",))


def initial_queue_status(status: str | None) -> str:
    """The status a queue entry is BORN with, given the plan's `- Status:`. SHARED BY BOTH HOSTS.

    THE DEFECT THIS FIXES, measured across 13 runs. Both hosts built this inline as an ALLOWLIST with
    no `executed` arm::

        "status": "queued" if status in ("to-review","draft","approved","auto-approved") else "reviewed"

    so EVERY terminal status fell through to the `else` and an already-`executed` plan was relabeled
    `reviewed` on its queue entry. That is not a cosmetic mislabel, because `cascade_dependency_blocked`
    reads THIS field: `reviewed` is in `TERMINAL_STATES` but NOT in `EXECUTION_SUCCESS_STATES`, so the
    executed plan became a DEAD PREREQUISITE and every dependent died without a session. In run
    `run-20260917T033138Z-557584` nine mislabeled parents killed six approved children and both
    orchestrators at queue build, before any agent turn, for zero tokens; three `20260913` runs lost
    10, 12 and 16 items the same way.

    IT ALSO VIOLATED A WRITTEN PROHIBITION. Spec `20260826-0718-01` 2.9 requires an `executed:` edge to
    be decided "by the consuming action and by nothing else: not by queue membership ... An
    implementation that lets the same edge be satisfied or refused depending on queue membership is the
    evadability defect this section exists to prevent." `edge_satisfied`'s EXTERNAL branch reads the
    terminal directory and correctly returns satisfied for these same plans, so membership in the queue
    was the only thing flipping the verdict.

    THE FIX IS DELIBERATELY NARROW: `executed` is preserved, and no other terminal status is. See
    `TERMINAL_QUEUE_STATUSES` for the measured reason (`superseded`/`not-executed` are absent from
    BOTH `TERMINAL_STATES` and `runner_shutdown.KNOWN_ITEM_STATUSES`, so writing them would refuse the
    run's own resume). Those two keep falling back to `reviewed`, which already yields the RIGHT
    OUTCOME for them: they are non-success terminal states and `reviewed` is not in
    `EXECUTION_SUCCESS_STATES`, so a dependent still correctly refuses to run. Only `executed` was
    getting the wrong outcome, so only `executed` changes.

    `reviewed` REMAINS THE FALLBACK for anything else (notably a plan whose status is `reviewed`, and
    the `None` case an older hand-written manifest produces), which is why the review-mode fixture at
    `tests/test_oc_runipd.py` keeps passing: this function changes the answer ONLY for a status that is
    terminal on disk.
    """
    norm = (status or "").lower().strip()
    if norm in NON_TERMINAL_QUEUE_STATUSES:
        return "queued"
    if norm in TERMINAL_QUEUE_STATUSES:
        return norm
    return "reviewed"


def action_for(kind: str | None, status: str) -> str:
    """Decide the driver action for a plan given its Kind + Status. SHARED BY BOTH HOSTS (spec R-10).

    Orchestrators are special ONLY once past review: an approved/auto-approved orchestrator authors no
    code, so it is not agent-executed ('orchestrate' -> the runner retires it once every child of its
    Set reached `executed`). But a draft/to-review orchestrator still needs its own /plan-review to
    advance (the orchestrator artifact must be review-complete whether the Set is driven by a runner
    OR executed manually), so it takes the normal 'review' action. Everything else uses
    `determine_action` (review for to-review/draft, execute otherwise).

    THE `orchestrate` RETURN STARTS AT `reviewed`, NOT AT `approved`, which matters to any caller
    treating this as authority: it is a DISPATCH decision, not a retirement authorization. The
    retirement transition therefore re-checks eligibility itself rather than trusting Kind
    (`ipd_lifecycle.retire_orchestrator`), and this function must not be read as a permission.
    """
    norm = (status or "approved").lower().strip()
    if (kind or "").lower() == "orchestrator" and norm not in ("to-review", "draft"):
        return "orchestrate"
    return determine_action(status or "approved")


def decide_orchestrator_dispatch(
    repo: Path,
    setid: str,
    orchestrator_id6: str,
    queue: Sequence[Mapping[str, Any]],
    *,
    terminal_states: Container[str],
    success_states: Container[str],
) -> OrchestratorDispatch:
    """Decide RETIRE / RECONSIDER / TERMINATE for one `orchestrate` item (spec R-7/R-8/R-9).

    Consumes child 01's `evaluate_set_retirement` for the ON-DISK verdict, then uses the RUN QUEUE for
    the one question disk cannot answer: is an unfinished child still LIVE, or did it reach a
    non-success terminal state and become permanently unfinishable? That split is deliberate and is
    the whole reason both inputs are needed:

      * DISK decides ELIGIBILITY (spec R-1: a Set whose earlier children executed in previous runs is
        still complete, which a queue-scoped check cannot see).
      * THE QUEUE decides LIVENESS (whether waiting can still pay off inside THIS run).

    A child that is unfinished on disk and ABSENT from the queue is treated as LIVE-but-not-here,
    which resolves to RECONSIDER and then, when nothing else is runnable, to the drain path's honest
    terminal labelling. That is the conservative direction: the run ends rather than spins, and the
    orchestrator is never retired on a Set that is not done.

    `terminal_states`/`success_states` are INJECTED rather than imported because each host owns its
    own copy of those sets (they are byte-identical today, but this module must not pick a side for
    them; that is a different plan's decision). Passing them keeps this decision host-neutral.

    DECIDES ONLY: no status write, no transition, no file touched.
    """

    decision = evaluate_set_retirement(repo, setid)
    if decision.eligible:
        return OrchestratorDispatch(
            outcome=ORCH_DISPATCH_RETIRE,
            reason="",
            detail=decision.detail,
            eligibility=decision,
        )

    if decision.reason == RETIRE_REFUSED_NO_CHILDREN:
        # TERMINATE, not RECONSIDER. A Set with no children on disk will not grow one during a run,
        # and retirement is gated on children being executed, so waiting cannot pay off.
        return OrchestratorDispatch(
            outcome=ORCH_DISPATCH_TERMINATE,
            reason=ORCH_REASON_NO_CHILDREN,
            detail=decision.detail,
            eligibility=decision,
        )

    if decision.reason == RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS:
        # TERMINATE. The orchestrator's own child table declares a row resolving to no plan (the
        # `rununify` case, whose row token is literally `03+`). Authoring the missing child is a
        # HUMAN act outside any run, so no amount of waiting inside this run changes the answer.
        return OrchestratorDispatch(
            outcome=ORCH_DISPATCH_TERMINATE,
            reason=ORCH_REASON_UNAUTHORED_CHILD_ROWS,
            detail=decision.detail,
            unauthored_rows=decision.unauthored_rows,
            eligibility=decision,
        )

    if decision.reason == RETIRE_REFUSED_NO_ORCHESTRATOR:
        # TERMINATE. The dispatching item claims to BE this Set's orchestrator, so a Set that resolves
        # without one means the selector could not be read as a Set at all (child 01's pinned-resolve
        # cost, carried in `resolution_note`). Refuse terminally and say which, rather than retrying a
        # resolution that will fail identically every iteration.
        return OrchestratorDispatch(
            outcome=ORCH_DISPATCH_TERMINATE,
            reason=ORCH_REASON_NO_ORCHESTRATOR,
            detail=decision.detail,
            eligibility=decision,
        )

    # RETIRE_REFUSED_UNFINISHED_CHILDREN: the ONE refusal that can still clear inside this run, and
    # the one whose premature terminal write is the defect this plan exists to fix. Split it THREE
    # ways, on whether THIS RUN can still change the answer.
    #
    # RECONSIDER IS GATED ON ACTIONABILITY, NOT MERELY ON "NOT DEAD", and that gate is what makes the
    # outcome spin-free. It was added after MEASURING the spin rather than reasoning about it: with the
    # naive rule (reconsider whenever no child is terminally dead) a scripted `run_queue` over a Set
    # whose unfinished child was ON DISK but ABSENT FROM THE QUEUE dispatched the orchestrator 201
    # times without terminating, and the existing drain path could not catch it because the drain is
    # reached only when NOTHING is selectable while this orchestrator remained selectable forever.
    # (E-03/OQ-01: the maintainer's instruction was to verify the existing net FIRST and add a
    # termination only if it did not cover the case. It did not.)
    #
    # SO: a child counts as ACTIONABLE only when it is IN THIS RUN'S QUEUE in a non-terminal state,
    # because that is precisely the condition under which the run will still act on it. Waiting is then
    # bounded, for a reason that follows from the scheduler rather than from hope: `queue_sort_key`
    # ranks `dependency_depth` FIRST and `dependency_depth` treats every non-orchestrator member of a
    # Set as a prerequisite of its orchestrator, so an actionable child is always dispatched BEFORE the
    # orchestrator is re-dispatched. Each iteration therefore either advances that child or gives it a
    # terminal status, and the second flips this decision to TERMINATE. Neither branch repeats forever.
    by_id = {str(entry.get("id6")): entry for entry in queue}
    dead: list[tuple[str, str]] = []
    actionable: list[tuple[str, str]] = []
    stranded: list[tuple[str, str]] = []
    for child_id6, disk_status in decision.unfinished:
        entry = by_id.get(child_id6)
        if entry is None:
            # Unfinished on disk and not in this run at all. Nothing this run does can finish it.
            stranded.append((child_id6, disk_status))
            continue
        run_status = str(entry.get("status") or "")
        if run_status in terminal_states and run_status not in success_states:
            dead.append((child_id6, run_status))
        elif run_status in terminal_states:
            # A TERMINAL SUCCESS that is still not `executed` ON DISK. `EXECUTION_SUCCESS_STATES`
            # admits `substantially-complete` for dependency-edge purposes, but retirement accepts
            # ONLY `executed` (spec R-2, deliberately narrower). The run is done with this child, so
            # waiting cannot help: stranded, not actionable.
            stranded.append((child_id6, f"{run_status} in run, {disk_status} on disk"))
        else:
            actionable.append((child_id6, run_status or disk_status))

    if dead:
        listed = ", ".join(f"{i} ({s})" for i, s in dead)
        rest = actionable + stranded
        also = f"; {len(rest)} other child(ren) are also unfinished" if rest else ""
        return OrchestratorDispatch(
            outcome=ORCH_DISPATCH_TERMINATE,
            reason=ORCH_REASON_DEAD_CHILDREN,
            detail=(
                f"Set {decision.setid!r} can never complete in this run: child(ren) {listed} "
                f"reached a non-success terminal state, so they cannot become "
                f"{SET_RETIREMENT_DONE_STATUS}{also}"
            ),
            unfinished=tuple(dead) + tuple(rest),
            eligibility=decision,
        )

    if actionable:
        listed = ", ".join(f"{i} ({s})" for i, s in actionable)
        return OrchestratorDispatch(
            outcome=ORCH_DISPATCH_RECONSIDER,
            reason=ORCH_REASON_UNFINISHED_CHILDREN,
            detail=(
                f"Set {decision.setid!r} has {len(actionable)} child(ren) not yet "
                f"{SET_RETIREMENT_DONE_STATUS} that THIS RUN will still act on: {listed}. Left "
                "RECONSIDERABLE (no status written), so this orchestrator is re-tested on a later "
                "iteration once they complete"
            ),
            unfinished=tuple(actionable) + tuple(stranded),
            eligibility=decision,
        )

    listed = ", ".join(f"{i} ({s})" for i, s in stranded)
    return OrchestratorDispatch(
        outcome=ORCH_DISPATCH_TERMINATE,
        reason=ORCH_REASON_CHILDREN_NOT_IN_RUN,
        detail=(
            f"Set {decision.setid!r} has {len(stranded)} child(ren) not yet "
            f"{SET_RETIREMENT_DONE_STATUS} that this run will NOT act on: {listed}. Nothing in this "
            "run can finish them, so waiting would repeat this decision unchanged; run them (or the "
            "whole Set) and the orchestrator is retired then"
        ),
        unfinished=tuple(stranded),
        eligibility=decision,
    )


def dispatch_orchestrator_item(
    repo: Path,
    run_dir: Path,
    state: MutableMapping[str, Any],
    item: MutableMapping[str, Any],
    *,
    actor: str,
    terminal_states: Container[str],
    success_states: Container[str],
    terminal_status: str = "dependency-blocked",
) -> OrchestratorDispatch:
    """PERFORM the retire/reconsider/terminate outcome for one `orchestrate` item. BOTH HOSTS.

    This is the function `aw oc run` and `aw agy run` both call in place of an agent turn, and sharing
    the OUTCOME (not merely the DECISION) is the point of spec R-10 as `pgq326` E-07 reads it: E-04
    makes agy DECIDE `orchestrate`, and without a shared performer agy would still have to grow its own
    branch, which is the second copy the anti-re-fork discipline forbids.

    WHAT IT DOES, per outcome:

      * RETIRE     - call `ipd_lifecycle.retire_orchestrator` (child 02's transition), passing the
                     eligibility verdict so the transition VALIDATES the same decision rather than
                     recomputing a possibly-different one. On success the item becomes `executed` and
                     an `orchestrator-finalized` event is written. On REFUSAL the outcome is rewritten
                     to TERMINATE with reason `finalize-refused`, never to RECONSIDER: `rh5tt6` proves
                     a refusal can be structural, and retrying it every iteration would SPIN, which is
                     the one regression worse than the bug this plan fixes.
      * RECONSIDER - write NO status. The item stays `queued` and a later iteration re-tests it.
      * TERMINATE  - write `terminal_status` with the SPECIFIC reason, so the record never claims an
                     unmet dependency it cannot name (the `5e4sb6` defect).

    THE EVENT NAME `orchestrator-deferred` IS KEPT for continuity with the 28 already on disk, but its
    `reason` now carries one of the `ORCH_REASON_*` values instead of collapsing four distinct facts
    into one message. `terminated` says plainly which of the two dispositions the record got, so a
    reader need not infer it from the status.

    Returns the (possibly rewritten) dispatch decision. Does NOT save state: the caller owns that, as
    it owns the surrounding loop.
    """
    from agent_workflows import ipd_lifecycle as _lifecycle

    setid = str(item.get("setid") or "")
    id6 = str(item.get("id6") or "")
    decision = decide_orchestrator_dispatch(
        repo,
        setid,
        id6,
        list(state.get("queue") or []),
        terminal_states=terminal_states,
        success_states=success_states,
    )

    if decision.outcome == ORCH_DISPATCH_RETIRE:
        eligibility = decision.eligibility
        plan_path: Path | None = None
        with contextlib.suppress(Exception):
            membership = read_set_membership(repo, setid)
            if membership.orchestrator is not None:
                plan_path = membership.orchestrator.path
        result = None
        if plan_path is not None:
            result = _lifecycle.retire_orchestrator(
                repo,
                plan_path,
                actor,
                setid=setid,
                run_id=str(state.get("run_id") or "") or None,
                children=[m.id6 for m in read_set_membership(repo, setid).children],
                eligibility=eligibility,
                apply=True,
            )
        if result is not None and result.exit_code == 0:
            item["status"] = "executed"
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "orchestrator-finalized",
                    "id6": id6,
                    "setid": setid,
                    "reason": ORCH_DISPATCH_RETIRE,
                    "detail": decision.detail,
                },
            )
            return decision
        # The transition REFUSED (or the orchestrator's own file could not be located). TERMINATE:
        # a refusal here is structural, so retrying it on the next iteration would spin forever.
        why = (
            result.message
            if result is not None
            else f"the orchestrator plan file for Set {setid!r} could not be located on disk"
        )
        decision = decision._replace(
            outcome=ORCH_DISPATCH_TERMINATE,
            reason=ORCH_REASON_FINALIZE_REFUSED,
            detail=f"retirement transition refused: {why}",
        )

    if decision.outcome == ORCH_DISPATCH_RECONSIDER:
        # WRITE NO STATUS. The item stays `queued`, exactly as one skipped by the inner selection pass
        # does, so it is RE-SELECTED when its children complete. Recording the deferral is still
        # required: an unlabelled item with no event would be indistinguishable from one never reached.
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "orchestrator-deferred",
                "id6": id6,
                "setid": setid,
                "reason": decision.reason,
                "detail": decision.detail,
                "terminated": False,
                "unfinished_children": [list(pair) for pair in decision.unfinished],
            },
        )
        return decision

    item["status"] = terminal_status
    # The flat list keeps its existing shape (`list[str]`) for every existing consumer, and it is now
    # NON-EMPTY whenever a child is nameable, which is the `5e4sb6` fix: its event carried
    # `unfinished_children: []` and its summary still read "dependency-blocked (unmet dependencies)".
    item["unsatisfied_dependencies"] = [
        f"executed:{child}" for child, _st in decision.unfinished
    ]
    item["unsatisfied_dependency_reasons"] = {
        f"executed:{child}": f"child {child} is {st or 'unfinished'}"
        for child, st in decision.unfinished
    }
    # The typed cause, additive, so a consumer need not parse prose to learn WHICH refusal happened.
    item["orchestrator_refusal_reason"] = decision.reason
    item["orchestrator_refusal_detail"] = decision.detail
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "at": utc_now(),
            "event": "orchestrator-deferred",
            "id6": id6,
            "setid": setid,
            "reason": decision.reason,
            "detail": decision.detail,
            "terminated": True,
            "status": terminal_status,
            "unfinished_children": [list(pair) for pair in decision.unfinished],
            "unauthored_rows": list(decision.unauthored_rows),
        },
    )
    return decision


# ---- per-invocation telemetry: the ONE host-neutral seam (runanalytics Order 04, `5f2h8i`) --------
#
# WHAT THIS SECTION OWNS, AND WHAT IT DELIBERATELY DOES NOT. It owns the SEAM: where a telemetry
# stream lives, what an invocation's identity is, and the one context manager both drivers open
# around their agent turn. It owns NONE of the collector: the event schema, the probes, the node
# pseudonym, the sampler and the configuration model are all
# `agent_workflows.run_analytics_telemetry` and `run_analytics_config` (runanalytics Order 03,
# `lhccjf`). This section constructs those objects and reimplements nothing in them.
#
# WHY THE SEAM IS HERE RATHER THAN IN EITHER DRIVER, which is the whole point of the placement.
# `agy_runipd` already imports dozens of names from `oc_runipd`, and
# `tests/test_runner_refork_guard.py` pins that no runner REDEFINES an extracted symbol and that
# every runner attribute IS the owning module's object. A telemetry helper written in `oc_runipd`
# and imported by `agy_runipd` would satisfy a reviewer reading for parity of BEHAVIOR while
# forking the code, which is the exact defect that guard exists to catch. So both hosts reach
# telemetry through THIS module, and neither through the other's driver.
#
# THE PATH IS RESOLVED, NEVER COMPOSED. The run root comes from `state_root` above, which consults
# the project-context authority so a `records_backend` of `repository`, `companion` or `home` each
# resolves correctly; Order 01 (`xbwq8n`) exists precisely to remove the hardcoded
# `.aw/records/runs` literal, so this section adds no new one. Callers pass the run directory they
# were already given and this section appends ONE named constant.
#
# TELEMETRY IS NOT ANALYTICS, and the distinction is load-bearing rather than pedantic. Order 01
# RESERVED `analytics/` under the runs root for the DISPOSABLE derived cache
# (`ANALYTICS_DIRNAME` above, with `path_is_within_analytics` as its containment predicate, and
# consumers such as `completion.run_id_candidates` and `run_cli` deliberately EXCLUDE that tree
# when enumerating runs). Telemetry is a per-RUN observation written INSIDE the run directory
# beside `events.jsonl` and `outcomes/`, so it lives at `<run>/telemetry/` and MUST NOT be filed
# under `analytics/`: putting it there would place a run's own primary record inside a tree whose
# documented contract is that deleting it loses nothing.

#: The subdirectory, inside ONE run directory, holding that run's per-invocation telemetry streams.
#: A directory rather than a single file because there is one stream per INVOCATION (see
#: `TelemetryIdentity`), and one file per invocation is what lets a reader attribute an observation
#: to an attempt and a phase without parsing an interleaved stream.
TELEMETRY_DIRNAME: str = "telemetry"

#: The phase vocabulary this seam may emit, and the reason it is a SUBSET of the collector's.
#: `run_analytics_telemetry` enumerates eight phases for the whole toolkit; a DRIVER TURN is only
#: ever one of these two, because the driver launches an agent for exactly two purposes. Naming the
#: subset here (rather than passing whatever string a call site holds) is what makes phase an
#: explicit FIELD instead of something inferred from a filename.
TELEMETRY_PHASE_EXECUTE: str = "execute"
TELEMETRY_PHASE_VALIDATE: str = "validate"
TELEMETRY_TURN_PHASES: tuple[str, ...] = (
    TELEMETRY_PHASE_EXECUTE,
    TELEMETRY_PHASE_VALIDATE,
)


def telemetry_dir(run_dir: Path | str) -> Path:
    """The telemetry directory for ONE run, derived from the run directory it is given.

    Pure and side-effect free: it creates nothing, so a caller that only wants to KNOW the path
    (a test, a reader, an ingestion pass) cannot accidentally materialize a telemetry tree for a
    run that has none. "Telemetry disabled" is defined as *no directory and no file*, and a
    path-returning helper that mkdir'd would make that state unobservable.
    """

    return Path(run_dir) / TELEMETRY_DIRNAME


def telemetry_stream_path(run_dir: Path | str, execution_id: str) -> Path:
    """The JSONL stream for ONE invocation: `<run>/telemetry/<execution-id>.jsonl`.

    One file per invocation, keyed on the identity minted by :func:`telemetry_identity`, so two
    attempts of one item, an executor and its verifier, and a pre- and post-resume invocation of
    the same attempt each own a distinct stream.
    """

    return telemetry_dir(run_dir) / f"{execution_id}.jsonl"


class TelemetryIdentity(NamedTuple):
    """WHAT MAKES ONE INVOCATION DISTINGUISHABLE FROM EVERY OTHER.

    THE HAZARD THIS TYPE EXISTS TO CLOSE, measured rather than supposed. The obvious identity is
    `(position, id6, attempt, phase)`, and it is WRONG. `attempt_no` is derived in both drivers as
    `len(item.get("attempts", [])) + 1` over a list that is PERSISTED in `state.json`, so it does
    not reset when a run is resumed; that is correct for attempt NUMBERING and it means the tuple
    above is STABLE across a resume. Two invocations of the same item, attempt and phase separated
    by a resume would therefore mint one id, collide on one stream file, and produce a single
    interleaved record with two `start` events - defeating the requirement that an invocation's
    identity not be reconstructible from a single run-level snapshot.

    SO THE ID CARRIES A PER-INVOCATION COMPONENT (`token`), and the uniqueness argument is: the
    token is 8 hex characters from `secrets.token_hex`, drawn INSIDE the invocation rather than
    derived from any persisted state, so it is independent of `attempts`, of the run directory, of
    the clock, and of the process id. Two invocations cannot share one unless a 32-bit random draw
    repeats, and (unlike a timestamp) it cannot collide from two invocations starting inside the
    same clock tick, nor (unlike a pid) from a pid being reused by a resumed run.
    WHY NOT A COUNTER: a counter would have to be persisted somewhere, and any persisted counter
    is exactly the thing that fails to reset (or fails to advance) across the resume boundary,
    which is the defect being fixed. WHY NOT A TIME COMPONENT ALONE: `time.time()` is not
    monotonic and a resumed run on a clock-corrected box can legitimately produce an earlier
    timestamp, so it is neither unique nor ordered.

    PHASE IS AN EXPLICIT FIELD, never inferred. Today the two drivers distinguish an executor turn
    from a verifier turn ONLY by a `suffix="verify"` string handed to their log-path builders, so
    the phase is recoverable from a FILENAME. Deriving telemetry's phase the same way would couple
    a data field to a presentation detail, and it would break silently the day a log filename
    changes. The call site states the phase.
    """

    run_id: str
    position: int
    id6: str
    setid: str
    phase: str
    attempt: int
    token: str
    host: str

    @property
    def execution_id(self) -> str:
        """The stream's key, and the event field every later Order joins on.

        Shaped to satisfy the collector's own `execution_id` pattern (leading alphanumeric, then
        alphanumerics/underscore/hyphen, no dot, slash or colon), because that schema REFUSES an
        out-of-shape id rather than dropping it, and a refusal here would silently produce an
        empty stream.
        """

        return (
            f"{self.position:02d}-{self.id6}-a{self.attempt}-{self.phase}-{self.token}"
        )

    def context(self) -> dict[str, Any]:
        """The allowlisted correlation fields the collector stamps onto every event.

        Only keys the telemetry schema already allows are returned; the collector refuses an
        unknown key, so inventing one here would drop every event. `model`/`provider` are
        deliberately NOT set from this type: they are launch options the caller holds, and a
        caller supplies them through `extra_context`.
        """

        return {
            "run_id": self.run_id,
            "ipd_id6": self.id6,
            "set_id": self.setid,
            "position": self.position,
            "attempt": self.attempt,
            "phase": self.phase,
            "host": self.host,
        }


def telemetry_identity(
    *,
    run_id: str,
    item: Mapping[str, Any],
    attempt_no: int,
    phase: str,
    host: str,
    token: str | None = None,
) -> TelemetryIdentity:
    """Mint the identity for ONE agent invocation. See :class:`TelemetryIdentity` for the why.

    `token` is injectable so a test can pin the id deterministically; production never passes it.
    Every field is coerced to the shape the telemetry schema accepts, and an out-of-vocabulary
    `phase` falls back to `execute` rather than raising: an identity helper that could raise would
    put a telemetry concern on the critical path of launching an agent, which is precisely the
    non-interference property this plan must preserve.
    """

    resolved_phase = (
        phase if phase in TELEMETRY_TURN_PHASES else TELEMETRY_PHASE_EXECUTE
    )
    try:
        position = int(item.get("position") or 0)
    except (TypeError, ValueError):
        position = 0
    id6 = str(item.get("id6") or "unknown")
    setid = str(item.get("setid") or "unknown")
    return TelemetryIdentity(
        run_id=str(run_id or ""),
        position=position,
        id6=id6,
        setid=setid,
        phase=resolved_phase,
        attempt=max(1, int(attempt_no or 1)),
        token=token if token else secrets.token_hex(4),
        host=str(host or "unknown"),
    )


def telemetry_safe_context(
    context: Mapping[str, Any],
    *,
    validate: Callable[[Mapping[str, Any]], Any] | None = None,
) -> dict[str, Any]:
    """Keep only the correlation fields the telemetry schema will ACCEPT, dropping the rest.

    WHY THIS IS NECESSARY AND NOT DEFENSIVE PADDING, measured during integration. The collector's
    `validate_event` REFUSES a whole event when ANY field fails its rule, and the collector then
    records `telemetry-event-refused` and drops the event. That refusal direction is correct for the
    collector (a silent per-key drop would let a producer believe its record was persisted whole),
    but at THIS seam it has a bad consequence: one out-of-shape correlation value would discard
    EVERY event for that invocation, leaving no stream at all. Observed with a `run_id` of `"r"`,
    which fails the schema's `run-<UTC stamp>-<pid>` pattern: both the `start` and the `end` event
    were refused and nothing was written.

    That is exactly backwards for an observability feature. The RESOURCE observations do not depend
    on a correlation label being well formed, and losing them because a caller passed an unusual run
    id trades a complete record for nothing. So the seam PRE-FILTERS: each field is offered to the
    schema on its own, a field the schema rejects is omitted, and the remaining event is written and
    is valid by construction. The collector's own refusal stays untouched and remains the authority;
    this only stops the seam from handing it an event it will reject.

    `validate` is injectable so a test can drive the filter without the real schema.
    """

    if validate is None:
        from agent_workflows.run_analytics_telemetry import (
            TELEMETRY_SCHEMA_VERSION,
            validate_event,
        )

        version = TELEMETRY_SCHEMA_VERSION
        checker = validate_event
    else:  # pragma: no cover - test seam
        version = 1
        checker = validate

    kept: dict[str, Any] = {}
    for key, value in context.items():
        if value is None:
            continue
        probe = {
            "schema_version": version,
            "event_kind": "start",
            "execution_id": "probe",
            "wall_timestamp": "2026-01-01T00:00:00Z",
            "monotonic_offset_seconds": 0.0,
            key: value,
        }
        try:
            checker(probe)
        except Exception:  # noqa: BLE001 - an unacceptable field is DROPPED, never fatal
            continue
        kept[key] = value
    return kept


def _launch_safe_probe_adapter(telemetry_mod: Any, config: Any) -> Any:
    """The probe adapter this seam uses: the real one, with its SHELL-OUT SUPPRESSED.

    MEASURED DEFECT THIS EXISTS TO FIX, and it is the sharpest non-interference lesson of this
    integration. Every probe in `run_analytics_telemetry` is read-only and process-free EXCEPT
    `accelerators`, which shells out to a vendor tool (`nvidia-smi`, then `rocm-smi`) through
    `subprocess.run`. Wrapping the agent launch therefore added a SECOND subprocess invocation
    inside the very function whose one `Popen` several suites patch in order to capture the agent's
    argv. Result, measured on a machine that HAS `nvidia-smi`: 18 tests across five files began
    capturing the PROBE's argv instead of the agent's, and the two `LaunchProfileFrozenTurnArgvTests`
    failures read `(None, None, None) == (None, None, None)` because the captured argv was the
    probe's and carried no `--model` at all. On a machine without a vendor tool the suites would have
    stayed green and the interference would have shipped, which is exactly the kind of
    environment-dependent coupling that must not sit on an agent-launch path.

    THE FIX IS AT THE SEAM AND USES ORDER 03'S OWN INJECTION POINT, not a change to its probe:
    `SystemResourceProbeAdapter` already accepts a `runner` precisely so its one shell-out can be
    replaced, and a suppressed runner makes `accelerators` report the ordinary `unavailable` outcome
    the probe layer is designed to produce on a host with no vendor tool. Nothing else changes: every
    other field (cpu, memory, load, process, disk, tool versions) is unaffected, verified
    field-for-field against the unsuppressed adapter.

    WHY NOT JUST DISABLE THE PROBE UPSTREAM: accelerator data is legitimately wanted, and an
    ANALYSIS pass reading a run directory can shell out freely because it is not inside a turn. The
    constraint is specific to this call site (during a live agent launch), so the narrowing belongs
    here rather than in the collector, which other callers share.

    A construction failure returns `None`, which makes the collector build its own default adapter:
    degraded telemetry, never a broken turn.
    """

    try:
        return telemetry_mod.SystemResourceProbeAdapter(
            max_probe_seconds=config.max_probe_seconds,
            # The suppression itself. `(-2, "")` is the code the probe's own bounded runner returns
            # for a missing tool, so `accelerators` takes its documented `unavailable` path rather
            # than a new one.
            runner=lambda _argv, _timeout: (-2, ""),
        )
    except Exception:  # noqa: BLE001 - fall back to the collector's default rather than failing
        return None


@contextlib.contextmanager
def turn_telemetry(
    run_dir: Path | str,
    identity: TelemetryIdentity,
    *,
    repo: Path | str | None = None,
    extra_context: Mapping[str, Any] | None = None,
    collector_factory: Callable[..., Any] | None = None,
    sampler_factory: Callable[..., Any] | None = None,
) -> "Any":
    """Wrap ONE agent turn in per-invocation telemetry. NEVER raises, NEVER changes the outcome.

    Yields a small record with `.collector` and `.sampler` (either may be `None`), so a caller can
    assert what was created without reaching into this function. Both are `None` when telemetry is
    disabled by configuration, and no directory or file is created in that case.

    EVERY FAILURE MODE IS SWALLOWED, and that is the requirement rather than defensive habit. This
    wraps the launch of the agent process that does the actual work, so a telemetry fault must not
    turn a successful run into a failure nor mask a real one: an unwritable tree, a raising
    constructor, a probe that explodes, a close that fails, all leave the caller's control flow
    byte-identical to an uninstrumented run. The caller's own exception ALWAYS propagates
    unchanged, which is what makes the stall-timeout, checkpoint-stop, force-stop and
    KeyboardInterrupt paths behave exactly as they did before instrumentation.

    THE SAMPLER IS STOPPED THROUGH THE `finally` HERE AND THROUGH THE ALREADY-EXISTING SHUTDOWN
    FUNNEL, and through NOTHING ELSE. No signal handler is registered (four executed plans' guards
    assert `signal.signal(` appears in neither driver, and `runstop` Phase 5 owns SIGINT/SIGTERM
    registration) and no second cleanup routine is added (spec `c4gd2h` R5 requires exactly one).
    `runner_shutdown.clean_shutdown` learns to stop a REGISTERED sampler, which is an extension of
    the one routine that exists rather than a new path; see `register_active_sampler`.
    """

    collector: Any = None
    sampler: Any = None
    record = _TurnTelemetry()
    try:
        from agent_workflows import run_analytics_config, run_analytics_privacy
        from agent_workflows import run_analytics_telemetry as telemetry_mod

        config = run_analytics_config.read_telemetry_config(
            repo if repo is not None else Path.cwd()
        )
        if config.enabled:
            stream = telemetry_stream_path(run_dir, identity.execution_id)
            stream.parent.mkdir(parents=True, exist_ok=True)
            # The salt lives with the DISPOSABLE analytics cache by design (rotating it
            # invalidates correlation), so this is the one legitimate read of that tree from the
            # runner: telemetry consumes the pseudonym authority, it does not write analytics.
            salt = run_analytics_privacy.load_or_create_salt(
                analytics_cache_dir(repo) if repo is not None else stream.parent
            )
            context = dict(identity.context())
            for key, value in (extra_context or {}).items():
                if value is not None:
                    context[key] = value
            # PRE-FILTER, so one malformed correlation label cannot cost the whole stream. See
            # `telemetry_safe_context` for the measurement that made this necessary.
            context = telemetry_safe_context(context)
            factory = (
                collector_factory
                if collector_factory is not None
                else telemetry_mod.TelemetryCollector
            )
            collector_kwargs: dict[str, Any] = {
                "execution_id": identity.execution_id,
                "salt": salt,
                "config": config,
                "context": context,
                "disk_path": run_dir,
            }
            # ONLY when construction succeeded. Passing `adapter=None` would be WORSE than omitting
            # it: the collector reads `None` as "build the default", which is the very shell-out
            # this narrowing exists to avoid, so a failed construction must leave the key absent and
            # let the collector make that choice explicitly.
            launch_safe_adapter = _launch_safe_probe_adapter(telemetry_mod, config)
            if launch_safe_adapter is not None:
                collector_kwargs["adapter"] = launch_safe_adapter
            collector = factory(stream, **collector_kwargs)
            collector.start()
            sampler_ctor = (
                sampler_factory
                if sampler_factory is not None
                else telemetry_mod.ResourceSampler
            )
            sampler = sampler_ctor(collector)
            sampler.start()
            register_active_sampler(sampler)
    except Exception:  # noqa: BLE001 - telemetry may never affect the work it observes
        collector = None
        sampler = None
    record.collector = collector
    record.sampler = sampler
    try:
        yield record
    finally:
        # BOTH stops are best-effort AND idempotent: `ResourceSampler.stop` and
        # `TelemetryCollector.close` are each documented idempotent by Order 03, so the shared
        # shutdown routine reaching the same sampler first is harmless and cannot emit a second
        # `end` event (which would corrupt every duration computed from the stream).
        if sampler is not None:
            with contextlib.suppress(Exception):
                sampler.stop()
            unregister_active_sampler(sampler)
        if collector is not None:
            with contextlib.suppress(Exception):
                collector.close()


class _TurnTelemetry:
    """What :func:`turn_telemetry` yields: the created objects, or `None` for each.

    A tiny mutable holder rather than a tuple, so the yielded value is assigned AFTER construction
    succeeds or fails and a caller always receives the same shape.
    """

    __slots__ = ("collector", "sampler")

    def __init__(self) -> None:
        self.collector: Any = None
        self.sampler: Any = None

    @property
    def enabled(self) -> bool:
        return self.collector is not None


# ---- the sampler registry the EXISTING shutdown routine consults ---------------------------------
#
# WHY A REGISTRY AND NOT A HANDLER. A sampler is a daemon thread bounded by its own `stop()`, and
# the teardown paths that must stop it (normal return, exception, stall kill, deliberate stop,
# SIGINT via `except KeyboardInterrupt`) ALREADY funnel through either `turn_telemetry`'s `finally`
# above or `runner_shutdown.clean_shutdown`. So the correct wiring is to let the ONE existing
# cleanup routine see the live samplers, exactly as it already sees live child processes through
# `runner_shutdown.track_child`. That is the shape being copied, deliberately: same weak-reference
# discipline, same "already finished entries are skipped" property, same absence of unregister
# bookkeeping that could leak.
#
# NOTE WHERE THIS LIVES AND WHY IT IS NOT IN `runner_shutdown`: `runner_shutdown` is imported by
# both drivers and must stay free of a dependency on the analytics modules. Keeping the registry
# here (and having the shutdown routine consult it through a lazy import) means an installation
# that never touches telemetry pays nothing, and `runner_shutdown` keeps importing only stdlib plus
# `platform_lock`.

_ACTIVE_SAMPLERS: "MutableMapping[int, Any]" = {}
_ACTIVE_SAMPLERS_LOCK = threading.Lock()


def register_active_sampler(sampler: Any) -> Any:
    """Record a running sampler so the SHARED clean-shutdown routine can stop it (E-05).

    Returns the sampler so the call can be made inline. Keyed by `id()` under a lock rather than
    stored in a list, so registering the same object twice cannot produce two stop calls and
    unregistering is exact.
    """

    with _ACTIVE_SAMPLERS_LOCK:
        _ACTIVE_SAMPLERS[id(sampler)] = sampler
    return sampler


def unregister_active_sampler(sampler: Any) -> None:
    """Forget a sampler that has already been stopped. Never raises."""

    with _ACTIVE_SAMPLERS_LOCK:
        _ACTIVE_SAMPLERS.pop(id(sampler), None)


def active_samplers() -> list[Any]:
    """Every registered, not-yet-unregistered sampler, as a snapshot."""

    with _ACTIVE_SAMPLERS_LOCK:
        return list(_ACTIVE_SAMPLERS.values())


def stop_active_samplers() -> int:
    """Stop every registered sampler best-effort; return how many were stopped.

    Called by `runner_shutdown.clean_shutdown` as part of the invariant it ALREADY performs, not as
    a new invariant and not as a second cleanup path. Best-effort by contract: a sampler that
    refuses to stop must not prevent the remaining shutdown invariants from running (spec `c4gd2h`
    R6), and it cannot keep the process alive because the thread is a daemon joined with a timeout.
    """

    stopped = 0
    for sampler in active_samplers():
        with contextlib.suppress(Exception):
            sampler.stop()
            stopped += 1
        unregister_active_sampler(sampler)
    return stopped


# ---- THE DEFECT REPORT (defreport 01, `b7xarm`) --------------------------------------------------
#
# THE DEFECT THIS CLOSES. An execute turn's outcome JSON already carries
# `incomplete_requirements`, and the run viewer already renders it, but an EMPTY list means BOTH "I
# checked and found nothing" and "I never looked", and no code path asks which. Measured at
# authoring across the execute-turn outcome corpus: a majority of files carry an empty list, and no
# reader can tell an affirmative "nothing to report" from an unasked question. So an agent that
# stumbles across a real bug and says nothing is INDISTINGUISHABLE from one that verified there was
# nothing to say.
#
# WHY A SECOND FIELD RATHER THAN REUSING THE FIRST. `incomplete_requirements` is scoped to THIS
# plan's own unmet requirements and has a live reader (`run_viewer`). A bug in ADJACENT code, a gap
# between a spec and its implementation, or a design concern worked around is none of those, so it
# has no typed home today. Overloading the existing field would break a working display; adding a
# differently-scoped field does not.
#
# THE STATE IS CARRIED BY AN EXPLICIT VALUE, NEVER BY EMPTINESS. That is the whole point: a missing
# key and a considered "none" must be DIFFERENT BYTES. `DEFECT_REPORT_NONE_FOUND` is an affirmative
# claim; `DEFECT_REPORT_ABSENT` is the state the re-ask fires on.
#
# SIZE IS A BINDING CONSTRAINT, NOT A PREFERENCE (plan OQ-02). The maintainer accepted JSON for this
# report ON THE EXPRESS CONDITION that it stay SMALL, because the format concern (agents emitting
# rigorous JSON less reliably than structured markdown) applies to LARGER payloads. So the budget
# below is a contract, not a style note:
#
#   * FOUR keys at the top level (`state`, `findings`, plus nothing else the agent must write), and
#     TWO keys per finding (`what`, `where`). Nothing nested beyond one list of small objects.
#   * NO severity taxonomy, NO reproduction steps, NO triage fields. Every added field is a field an
#     agent can get wrong, and none of them is needed to decide the only question the report feeds:
#     should a backlog item exist? A later author who wants a fifth key should re-open OQ-02 first,
#     because accretion is exactly how the format decision would be answered by default rather than
#     on purpose.
#   * The rendered prompt block is measured against the prompt baseline in
#     `tests/test_defect_report.py::PromptSizeBudgetTests`, so the small-payload condition is
#     checkable as a NUMBER rather than asserted as an adjective.
#
# ONE SCHEMA, BOTH HOSTS. Defined ONCE here and referenced by `oc_runipd` and `agy_runipd`, on the
# `reporting_contract` precedent (one canonical constant plus an accessor, with a test asserting both
# drivers reference rather than inline it). The two prompt builders are a known divergence surface
# and a second copy of a schema literal is how they silently disagree.

#: The report's key inside the agent-written outcome JSON.
DEFECT_REPORT_KEY: str = "defect_report"

#: One or more findings were reported.
DEFECT_REPORT_FOUND: str = "found"

#: The agent AFFIRMATIVELY states it looked and found nothing. Accepted silently; never re-asked.
DEFECT_REPORT_NONE_FOUND: str = "none-found"

#: Neither statement is present. This is the ONLY state that triggers the re-ask.
DEFECT_REPORT_ABSENT: str = "absent"

DEFECT_REPORT_STATES: tuple[str, ...] = (
    DEFECT_REPORT_FOUND,
    DEFECT_REPORT_NONE_FOUND,
    DEFECT_REPORT_ABSENT,
)

#: The validator's three verdicts. Kept DISTINCT deliberately: collapsing COERCED into VALID hides
#: how often the schema is missed, and collapsing it into the re-ask case throws away real findings.
DEFECT_VERDICT_VALID: str = "valid"
DEFECT_VERDICT_COERCED: str = "coerced"
DEFECT_VERDICT_ABSENT_OR_AMBIGUOUS: str = "absent-or-ambiguous"

DEFECT_VERDICTS: tuple[str, ...] = (
    DEFECT_VERDICT_VALID,
    DEFECT_VERDICT_COERCED,
    DEFECT_VERDICT_ABSENT_OR_AMBIGUOUS,
)

#: The two keys a finding carries, and the complete budget for one. `what` is the defect; `where` is
#: enough to find it again. That is exactly what a carrier decision needs.
DEFECT_FINDING_KEYS: tuple[str, ...] = ("what", "where")

#: What a coerced bare string's missing `where` becomes, so a normalized finding always has both keys
#: and a consumer never has to branch on absence.
DEFECT_WHERE_UNSPECIFIED: str = "unspecified"


def defect_report_schema_literal() -> str:
    """The report as it appears INSIDE the execute prompt's outcome-JSON literal.

    SHOWS A FILLED EXAMPLE ELEMENT ON PURPOSE, and that is the single most load-bearing detail in
    this function. Measured across the execute-turn outcome corpus: EVERY entry agents wrote into
    `incomplete_requirements` was a BARE STRING and none was an object, because the literal shows
    `[]` and never an element. An element shape the prompt does not SHOW is missed every time, so
    showing one is what makes the object form reachable at all.

    Returned as a fragment to be interpolated into each host's existing outcome literal (there is
    exactly one legal insertion region in those prompts; see `defect_report_prompt_block`).
    """

    return (
        f'  "{DEFECT_REPORT_KEY}": {{\n'
        f'    "state": "{DEFECT_REPORT_FOUND}|{DEFECT_REPORT_NONE_FOUND}",\n'
        f'    "findings": [\n'
        f'      {{"what": "what is wrong, in one sentence", '
        f'"where": "file/symbol or artifact id"}}\n'
        f"    ]\n"
        f"  }},"
    )


def defect_report_prompt_block() -> str:
    """The demand itself: state findings AFFIRMATIVELY AND NEGATIVELY, and file a carrier.

    THE WORDING IS IDENTICAL ON BOTH HOSTS BY CONSTRUCTION, because both call this one function.
    `tests/test_defect_report.py` asserts neither driver inlines the prose, which turns host symmetry
    into a structural property rather than a diff someone has to eyeball.

    WHERE THIS MAY BE PLACED, stated here because "append it to the prompt" is the obvious wrong
    move and it BREAKS THE SUITE. `tests/test_reporting_contract.py` asserts that everything from the
    reporting-contract heading TO THE END of each built prompt is byte-equal to
    `reporting_contract.contract_text()`, on both hosts. So this block must go BEFORE
    `reporting_contract.prompt_block()`, which must remain the LAST thing in the prompt.
    `tests/test_lane_prompt_purity.py` additionally digest-pins a bounded EARLY block (from
    `Plan file at launch:` to `Prior attempt:`), so this must not land inside that window either.
    The region around the outcome-JSON literal satisfies both.

    THE CARRIER RULE IS THE MAINTAINER'S RULING AND DELEGATES NO JUDGEMENT (plan E-03). ALWAYS file
    a backlog item; a spec is supporting material and NEVER the carrier. The wording deliberately
    contains no branch inviting the agent to decide a case is "just a spec": that judgement is the
    failure mode the rule exists to prevent, and the maintainer said plainly they do not know when
    "just a spec" would be enough.

    REPORTING OUTRANKS FILING, also deliberately. An unreported finding is the defect this whole
    mechanism closes, so a reported-but-unfiled finding is strictly better than silence.
    """

    return f"""
## Defect report (REQUIRED, both directions)

State whether this turn found any bugs, gaps or concerns. Finding NOTHING is a REPORTABLE RESULT
that you must state affirmatively, not an absence you may leave implicit: write
`"state": "{DEFECT_REPORT_NONE_FOUND}"` with an empty `findings` list. Omitting the report is not
the same answer and will cost you a follow-up question.

WHAT COUNTS, beyond this plan's own unmet requirements (which stay in `incomplete_requirements`): a
bug in adjacent code, a gap between a spec and its implementation, and a design concern you had to
work around. Keep each finding to `what` and `where`.

FOR EACH FINDING, FILE A BACKLOG ITEM with `aw backlog new`, so the defect has a durable carrier a
gate can see. Write a spec too where a spec is genuinely what the work needs, and reference it, but
a spec is supporting material and is NEVER the carrier. If filing fails or is outside your scope,
STILL REPORT THE FINDING: reporting outranks filing.
"""


class DefectReportVerdict(NamedTuple):
    """The validator's structured answer. NEVER an exception (see `validate_defect_report`).

    Fields:
      * `verdict`: one of :data:`DEFECT_VERDICTS`.
      * `state`: one of :data:`DEFECT_REPORT_STATES`, the TRI-STATE a consumer branches on.
      * `findings`: the NORMALIZED findings, each a dict with exactly :data:`DEFECT_FINDING_KEYS`.
      * `coerced`: whether any input had to be coerced into the normalized form.
      * `coercions`: WHAT was coerced, so a silent coercion cannot hide a schema miss.
      * `violation`: a short statement of what was missing or ambiguous, fed back verbatim to the
        agent by the re-ask. Empty when the report was usable.
    """

    verdict: str
    state: str
    findings: tuple[dict[str, str], ...]
    coerced: bool
    coercions: tuple[str, ...]
    violation: str

    @property
    def needs_reask(self) -> bool:
        """True only for ABSENT-OR-AMBIGUOUS. An affirmative NONE-FOUND is never re-asked.

        Plan OQ-03, resolved: distrusting "I found nothing" after a large turn would punish the
        honest affirmative answer this mechanism exists to elicit (the omitter gets the same
        treatment, so the incentive to answer disappears) and would convert a bounded one-shot into a
        routine second turn on most items.
        """

        return self.verdict == DEFECT_VERDICT_ABSENT_OR_AMBIGUOUS


def _normalize_finding(raw: Any) -> tuple[dict[str, str] | None, str | None]:
    """One finding, normalized. Returns `(finding, coercion_note)`; `finding` is None if unusable.

    COERCION IS THE EXPECTED PATH, NOT A TOLERATED EXCEPTION. Measured: every entry agents wrote
    into the sibling list field was a bare string, because the literal never showed an element. A
    bare string carries the SAME FACT in prose, so it is accepted into the normalized form and the
    coercion is RECORDED. Discarding it would throw away a real finding on a formatting technicality
    and reproduce the silence this whole mechanism exists to end.
    """

    if isinstance(raw, dict):
        what = str(raw.get("what") or "").strip()
        where = str(raw.get("where") or "").strip()
        if not what:
            # A dict with no `what` says nothing. Fall back to any single scalar it does carry
            # rather than dropping it, and record the coercion.
            scalars = [
                str(v).strip()
                for v in raw.values()
                if isinstance(v, (str, int, float)) and str(v).strip()
            ]
            if not scalars:
                return None, "a finding object carried no readable text"
            what = scalars[0]
            return (
                {"what": what, "where": where or DEFECT_WHERE_UNSPECIFIED},
                f"a finding object had no `what`; used {what!r}",
            )
        if not where:
            return (
                {"what": what, "where": DEFECT_WHERE_UNSPECIFIED},
                f"a finding object had no `where`; recorded as {DEFECT_WHERE_UNSPECIFIED!r}",
            )
        return {"what": what, "where": where}, None
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None, "a finding was an empty string"
        return (
            {"what": text, "where": DEFECT_WHERE_UNSPECIFIED},
            f"a finding was a bare string rather than an object: {text[:80]!r}",
        )
    if isinstance(raw, (int, float, bool)):
        return (
            {"what": str(raw), "where": DEFECT_WHERE_UNSPECIFIED},
            f"a finding was a bare {type(raw).__name__} rather than an object",
        )
    return None, f"a finding was an unusable {type(raw).__name__}"


def validate_defect_report(outcome: Any) -> DefectReportVerdict:
    """Validate the defect report PER FIELD, tolerantly, and NEVER raise.

    THE MEASURED DEFECT IS SHAPE, NOT SYNTAX, and that decides the design. Across the agent-written
    outcome corpus there were ZERO malformed JSON files, ZERO markdown fences and ZERO unterminated
    strings, while the intended ELEMENT shape of a list field was missed in every single entry. So
    this validates TYPES and coerces what is safely coercible; it does not re-parse or reformat.

    NEVER RAISES, AND NEVER FAILS THE TURN BY ITSELF. A validator that crashes on unexpected input is
    a validator that gets wrapped in a bare `except` and neutered, which is exactly what happened to
    the spec-edit announcement in `oc_runipd` (and why plan `st5klo` exists to undo it). It returns a
    verdict for every input, including `None`, a string, or a list.

    Accepts either the whole outcome dict or the report itself, because a caller holding one should
    not have to know which shape the other expects.
    """

    report: Any = None
    if isinstance(outcome, dict):
        if DEFECT_REPORT_KEY in outcome:
            report = outcome.get(DEFECT_REPORT_KEY)
        elif "state" in outcome or "findings" in outcome:
            report = outcome
        else:
            return DefectReportVerdict(
                verdict=DEFECT_VERDICT_ABSENT_OR_AMBIGUOUS,
                state=DEFECT_REPORT_ABSENT,
                findings=(),
                coerced=False,
                coercions=(),
                violation=(
                    f"the outcome JSON carries no `{DEFECT_REPORT_KEY}` key, so it is unknown "
                    "whether you looked for bugs, gaps or concerns and found none, or never looked"
                ),
            )
    else:
        report = outcome

    if report is None:
        return DefectReportVerdict(
            verdict=DEFECT_VERDICT_ABSENT_OR_AMBIGUOUS,
            state=DEFECT_REPORT_ABSENT,
            findings=(),
            coerced=False,
            coercions=(),
            violation=(
                f"`{DEFECT_REPORT_KEY}` was null, which does not say whether you found nothing or "
                "never looked"
            ),
        )

    coercions: list[str] = []

    # A bare string or a bare list where the object was expected: the SAME tolerance the element
    # shape gets, for the same reason. `"defect_report": "none found"` is a real answer.
    if isinstance(report, str):
        text = report.strip()
        lowered = text.lower()
        if not text:
            return DefectReportVerdict(
                verdict=DEFECT_VERDICT_ABSENT_OR_AMBIGUOUS,
                state=DEFECT_REPORT_ABSENT,
                findings=(),
                coerced=False,
                coercions=(),
                violation=(
                    f"`{DEFECT_REPORT_KEY}` was an empty string, which states neither findings nor "
                    "an affirmative none-found"
                ),
            )
        if _reads_as_none_found(lowered):
            return DefectReportVerdict(
                verdict=DEFECT_VERDICT_COERCED,
                state=DEFECT_REPORT_NONE_FOUND,
                findings=(),
                coerced=True,
                coercions=(
                    f"`{DEFECT_REPORT_KEY}` was the bare string {text[:80]!r}, read as an "
                    f"affirmative {DEFECT_REPORT_NONE_FOUND}",
                ),
                violation="",
            )
        report = {"state": DEFECT_REPORT_FOUND, "findings": [text]}
        coercions.append(
            f"`{DEFECT_REPORT_KEY}` was a bare string rather than an object; read as one finding"
        )
    elif isinstance(report, list):
        report = {
            "state": DEFECT_REPORT_FOUND if report else DEFECT_REPORT_ABSENT,
            "findings": report,
        }
        coercions.append(
            f"`{DEFECT_REPORT_KEY}` was a bare list rather than an object; read as `findings`"
        )

    if not isinstance(report, dict):
        return DefectReportVerdict(
            verdict=DEFECT_VERDICT_ABSENT_OR_AMBIGUOUS,
            state=DEFECT_REPORT_ABSENT,
            findings=(),
            coerced=False,
            coercions=(),
            violation=(
                f"`{DEFECT_REPORT_KEY}` was a {type(report).__name__}; it must be an object with "
                "`state` and `findings`"
            ),
        )

    raw_findings = report.get("findings")
    findings: list[dict[str, str]] = []
    if raw_findings is None:
        pass
    elif isinstance(raw_findings, list):
        for entry in raw_findings:
            normalized, note = _normalize_finding(entry)
            if note:
                coercions.append(note)
            if normalized is not None:
                findings.append(normalized)
    else:
        normalized, note = _normalize_finding(raw_findings)
        coercions.append(
            f"`findings` was a {type(raw_findings).__name__} rather than a list"
            + (f"; {note}" if note else "")
        )
        if normalized is not None:
            findings.append(normalized)

    raw_state = report.get("state")
    state = str(raw_state).strip().lower() if raw_state is not None else ""

    if state in (DEFECT_REPORT_FOUND, DEFECT_REPORT_NONE_FOUND):
        pass
    elif state and _reads_as_none_found(state):
        coercions.append(f"`state` was {state!r}, read as {DEFECT_REPORT_NONE_FOUND}")
        state = DEFECT_REPORT_NONE_FOUND
    elif state and findings:
        coercions.append(f"`state` was {state!r}, read as {DEFECT_REPORT_FOUND}")
        state = DEFECT_REPORT_FOUND
    elif not state and findings:
        # Findings without a state is unambiguous in substance: something WAS found.
        coercions.append(
            f"`state` was missing but {len(findings)} finding(s) were present; read as "
            f"{DEFECT_REPORT_FOUND}"
        )
        state = DEFECT_REPORT_FOUND
    else:
        # No usable state AND no findings. This is EXACTLY the ambiguity the whole mechanism
        # exists to end, so it must not be quietly read as none-found.
        return DefectReportVerdict(
            verdict=DEFECT_VERDICT_ABSENT_OR_AMBIGUOUS,
            state=DEFECT_REPORT_ABSENT,
            findings=(),
            coerced=bool(coercions),
            coercions=tuple(coercions),
            violation=(
                f"`{DEFECT_REPORT_KEY}` carried no findings and no explicit "
                f'`"state": "{DEFECT_REPORT_NONE_FOUND}"`, so an empty report is '
                "indistinguishable from an unasked question"
            ),
        )

    if state == DEFECT_REPORT_NONE_FOUND and findings:
        # A contradiction, resolved TOWARD the findings: they are the evidence, the label is not.
        coercions.append(
            f"`state` said {DEFECT_REPORT_NONE_FOUND} while {len(findings)} finding(s) were "
            f"present; read as {DEFECT_REPORT_FOUND}"
        )
        state = DEFECT_REPORT_FOUND

    if state == DEFECT_REPORT_FOUND and not findings:
        return DefectReportVerdict(
            verdict=DEFECT_VERDICT_ABSENT_OR_AMBIGUOUS,
            state=DEFECT_REPORT_ABSENT,
            findings=(),
            coerced=bool(coercions),
            coercions=tuple(coercions),
            violation=(
                f"`state` said {DEFECT_REPORT_FOUND} but `findings` was empty, so what was found "
                "is unknown"
            ),
        )

    return DefectReportVerdict(
        verdict=DEFECT_VERDICT_COERCED if coercions else DEFECT_VERDICT_VALID,
        state=state,
        findings=tuple(findings),
        coerced=bool(coercions),
        coercions=tuple(coercions),
        violation="",
    )


#: Phrases a bare "nothing to report" answer takes. Kept SMALL and used only where the alternative is
#: discarding an answer the agent plainly gave; it is never used to invent a none-found from silence.
_NONE_FOUND_PHRASES: tuple[str, ...] = (
    "none-found",
    "none found",
    "none",
    "no findings",
    "nothing found",
    "nothing to report",
    "no defects",
    "no bugs",
    "no issues",
    "clean",
)


def _reads_as_none_found(lowered: str) -> bool:
    """Whether a lowercased scalar is an affirmative none-found rather than a finding."""

    text = lowered.strip().strip(".!").strip()
    if text in _NONE_FOUND_PHRASES:
        return True
    return len(text) <= 40 and any(p in text for p in _NONE_FOUND_PHRASES)


def defect_reask_message(verdict: DefectReportVerdict) -> str:
    """The re-ask, naming the SPECIFIC violation rather than repeating the original instruction.

    A generic re-ask invites the same output again, so the violation the validator recorded is fed
    back verbatim. This is also where a SHAPE violation gets its second chance to be stated
    correctly.
    """

    return f"""Your turn is finished and its outcome file is written, but the REQUIRED defect report
is missing or unusable, so one question remains.

WHAT WAS WRONG: {verdict.violation}

Answer it now by REWRITING ONLY the `{DEFECT_REPORT_KEY}` object in the outcome JSON you already
wrote. Change nothing else in that file, make no further code edits, and create no commit.

If you found bugs, gaps or concerns, say so:

{defect_report_schema_literal()}

If you looked and found nothing, say THAT, affirmatively:

  "{DEFECT_REPORT_KEY}": {{"state": "{DEFECT_REPORT_NONE_FOUND}", "findings": []}},

An empty or missing report is not an answer: it cannot be told apart from never having looked.
"""


#: Item statuses for which a re-ask is NOT billed, because the turn has nothing to report ON.
#: A turn that never started work, was stopped, or was blocked before doing anything should not be
#: charged for a follow-up question about findings it had no opportunity to make.
DEFECT_REASK_SKIPPED_STATUSES: frozenset[str] = frozenset(
    {
        "blocked",
        "dependency-blocked",
        "not-attempted",
        "interrupted",
        "unknown_outcome",
        "queued",
        "running",
    }
)


def defect_reask_is_warranted(
    verdict: DefectReportVerdict,
    *,
    disposition: str | None,
    session_id: str | None,
    already_reasked: bool = False,
) -> tuple[bool, str]:
    """Decide whether to spend ONE follow-up turn. Returns `(warranted, reason)`.

    BOUNDED AT EXACTLY ONE ATTEMPT, by contract. An unbounded or multi-attempt loop converts a
    missing field into an open-ended spend, so `already_reasked` closes the gate permanently for this
    item. If the single re-ask also yields nothing, THAT fact is recorded durably: "the agent was
    asked and did not answer" is itself a finding a human should see, and it is materially different
    from "nobody asked".

    THE THREE EXISTING SESSION RULES ARE OBEYED HERE RATHER THAN REDISCOVERED AT RUNTIME:

      1. AN ISOLATED TURN IS ALWAYS A FRESH SESSION, by deliberate decision (`isolated_turn =
         bool(work_dir)` in `oc_runipd.run_opencode`, mirrored in `agy_runipd.execute_item`), because
         an opencode session carries its own project binding that OVERRIDES `--dir`; four consecutive
         lanes were lost proving it. So on an isolated lane turn there may be NO session to resume.
         This function therefore REFUSES when no session id was observed rather than resuming into
         the wrong worktree: no session, no re-ask. The report is still recorded ABSENT, which is
         itself the honest observation.
      2. `max_items_per_session` (default 4) ROTATES a session once its turn count is reached, so the
         session a re-ask wants may already have been rotated away. The caller passes the session id
         it ACTUALLY observed for THIS attempt (`attempt["session_id"]`), never a set-wide one, so a
         rotated-away session cannot be resumed by accident.
      3. A RE-ASK CONSUMES A TURN AGAINST THAT ROTATION BUDGET, and it is COUNTED: the callers reuse
         their normal launch path, which is what increments `session_turn_counts`. Stated explicitly
         because an unstated answer here is a live-run bug, not a detail. The consequence is
         deliberate and acceptable: a re-asked item may rotate its session one item earlier.
    """

    if not verdict.needs_reask:
        return False, "the report was usable; no follow-up needed"
    if already_reasked:
        return False, "the single permitted re-ask has already been spent"
    status = (disposition or "").strip()
    if status in DEFECT_REASK_SKIPPED_STATUSES:
        return False, f"the turn did no reportable work (disposition {status!r})"
    if not session_id:
        return (
            False,
            "no resumable session was observed for this turn, so the same-session re-ask is "
            "impossible (an isolated turn is always a fresh session by design)",
        )
    return True, "the report is absent or ambiguous and the turn's session is resumable"


def read_defect_report_outcome(outcome_path: Path | str | None) -> Any:
    """Re-read an agent-written outcome file, returning `None` rather than raising on any failure.

    Used by the re-ask to see what the follow-up produced. Absence, invalid JSON and an unreadable
    file are all legitimate OBSERVATIONS here (each ends up recorded as a still-absent report), so
    none of them may propagate as an exception and kill the turn.
    """

    if outcome_path is None:
        return None
    path = Path(outcome_path)
    try:
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def resume_via_launcher(
    launcher: Callable[..., Any],
    launch_args: Sequence[Any],
    launch_kwargs: dict[str, Any],
) -> Any:
    """Call a host's OWN launcher for the follow-up turn, by NAME injection.

    THE INJECTION IS THE POINT, and it is the established local pattern rather than a novelty: five
    symbols in this module already receive a host dependency as a parameter (`run_checked` gets
    `env_builder`, `save_state` gets `write_report`, and so on) precisely so a shared body can reach
    host-specific behavior without either driver forking the body.

    IT ALSO KEEPS A MEASURED PROMISE. `tests/test_oc_runipd.py::...
    test_one_argv_builder_serves_both_call_sites` and the telemetry wiring tests pin that each host's
    launcher has EXACTLY TWO callers (the executor and the verifier), so no third launch path can
    appear unnoticed and inherit the wrong frozen launch profile. A re-ask that CALLED
    `run_opencode(...)` inside the driver would be that third caller; passing the launcher as a NAME
    satisfies the re-ask without adding one.

    THE POSITIONAL SHAPE IS PRESERVED DELIBERATELY, and this is not a style choice. Every existing
    driver test double replaces the launcher with a function whose leading parameters are POSITIONAL
    (`def fake_run(state, rd, item, plan_path, prompt_path, attempt_no, **kwargs)`), so a shared
    caller that passed those by keyword would raise `TypeError` against a dozen existing fakes:
    measured, ten integration tests broke that way on the first attempt. `launch_args` therefore
    carries the host's own positional prefix and `launch_kwargs` only what each host spells
    differently (OpenCode's `resume_session=<id>` versus Antigravity's `session_id=<id>` plus
    `use_continue=False`), so this function holds no host knowledge at all.
    """

    return launcher(*launch_args, **launch_kwargs)


def perform_defect_reask(
    *,
    verdict: DefectReportVerdict,
    prompt_path: Path,
    outcome_path: Path | str | None,
    resume: Callable[..., Any],
    recollect: Callable[[], Any] | None = None,
    session_turn_counts: dict[str, int] | None = None,
    session_id: str | None = None,
) -> tuple[DefectReportVerdict, int]:
    """Spend the ONE permitted follow-up turn in the SAME session, then re-validate.

    Returns `(verdict_after, exit_code)`. `verdict_after` is the re-validated report, which may still
    be ABSENT-OR-AMBIGUOUS: that outcome is RECORDED rather than retried, because "the agent was
    asked and did not answer" is itself a finding a human should see and is materially different from
    "nobody asked". THIS FUNCTION NEVER LOOPS; boundedness is structural, not a counter.

    THE RESUME PRIMITIVE IS THE HOST'S OWN, INJECTED AS A NAME. `oc_runipd` resumes with
    `--session <id>` and `agy_runipd` with `--conversation <id>` (falling back to `--continue`), so a
    single hardcoded flag here would silently fail on one host: precisely the one-sided-guard defect
    class this repository has been bitten by. The caller therefore binds its OWN launcher (with
    `functools.partial` over `resume_via_launcher`, so the launcher appears as a NAME and no launcher
    call-site count moves, exactly as `run_checked` is injected), and this function calls
    `resume(prompt_path)` with the follow-up prompt as its ONE argument.

    `recollect` exists for an ISOLATED turn: the worker rewrites the outcome file inside its lane, so
    the driver must collect it again before re-reading. Bound by the caller to its lane collection,
    `None` for a non-isolated turn.

    `session_turn_counts` implements the third session rule EXPLICITLY: a re-ask CONSUMES a turn
    against `max_items_per_session`, so the caller passes the live counter for a non-isolated turn and
    the bump happens HERE, in one place, rather than being an unstated live-run behavior.
    """

    exit_code = 0
    result = resume(prompt_path)
    if isinstance(result, tuple) and result:
        try:
            exit_code = int(result[0])
        except (TypeError, ValueError):
            exit_code = 0
    elif isinstance(result, int):
        exit_code = result

    if session_turn_counts is not None and session_id:
        session_turn_counts[session_id] = session_turn_counts.get(session_id, 0) + 1

    if recollect is not None:
        # A failed collection must not discard the turn: the re-read below simply finds the older
        # copy and the report stays recorded as absent, which is the honest observation.
        with contextlib.suppress(Exception):
            recollect()

    after = validate_defect_report(read_defect_report_outcome(outcome_path))
    if after.needs_reask:
        # Preserve WHY the follow-up failed, so the record names the second violation and not the
        # first: "asked, still silent" is the fact a human needs.
        after = after._replace(
            violation=(
                f"re-asked once and the report is still unusable: {after.violation}"
                if after.violation
                else "re-asked once and the report is still unusable"
            )
        )
    return after, exit_code


def defect_report_record(
    verdict: DefectReportVerdict,
    *,
    reasked: bool = False,
    reask_reason: str = "",
    reask_verdict: DefectReportVerdict | None = None,
) -> dict[str, Any]:
    """The NORMALIZED record persisted on the run record, beside the other per-item results.

    THE LOCATION AND SHAPE, written down here because this is the CONTRACT a consumer codes against
    (plan `rnkqrc`, `durablecapture-01`, is the transition gate that will read it):

      * LOCATION: `state["queue"][i]["defect_report"]` in `<run_dir>/state.json`, written at the
        SAME per-item seam as `item["last_outcome"]`/`item["status"]`/`item["verification_status"]`,
        by BOTH host drivers. `<run_dir>` is `.aw/records/runs/<run-id>/`, which is GITIGNORED, so a
        TEST must build its records in a tmp_path fixture and never assert against the live tree.
      * SHAPE: `{"state", "verdict", "findings", "coerced", "coercions", "reasked",
        "reask_reason", "reask_state", "reask_verdict"}`.

    ALL FOUR FACTS A GATE NEEDS ARE PRESENT AND SEPARATE: the tri-state (`state`), the normalized
    findings (`findings`), whether a coercion occurred (`coerced`/`coercions`), and whether a re-ask
    happened and what it produced (`reasked`/`reask_state`/`reask_verdict`). A gate that must
    distinguish "no defects found" from "never asked" needs all four, and it must be able to tell
    "asked and answered" from "asked and still silent".

    NO GATE LOGIC LIVES HERE. This function produces the record; refusing a transition against it is
    `rnkqrc`'s job. HONEST LIMIT worth stating: that plan declares only `check_engine.py`,
    `ipd_lint.py`, `ipd_schema.py` and its test file, and its checks read the PLAN FILE's typed
    fields, so nothing it has scoped reads a run record yet. This record is therefore NECESSARY but
    not SUFFICIENT for that handoff, and the reader is unscoped on ITS side of the seam.
    """

    final = reask_verdict or verdict
    return {
        "state": final.state,
        "verdict": final.verdict,
        "findings": [dict(f) for f in final.findings],
        "coerced": bool(verdict.coerced or final.coerced),
        "coercions": list(verdict.coercions)
        + list(reask_verdict.coercions if reask_verdict else ()),
        "reasked": bool(reasked),
        "reask_reason": reask_reason,
        "reask_state": (reask_verdict.state if reask_verdict is not None else None),
        "reask_verdict": (reask_verdict.verdict if reask_verdict is not None else None),
    }


# ---- rununify 03 (`i3d6ml`): the LIFTED host-neutral helpers -------------------------------------
#
# NINE symbols that were defined in BOTH runners and are now defined ONCE here. They are admitted
# under the module's admission rule with ONE DELIBERATE WIDENING, stated so the rule is not read as
# having been bent silently: the rule as written above admits bodies "PROVEN identical by AST
# comparison", and four of these nine had bodies that were NOT identical. They are admitted anyway
# because the measurement that matters for a lift is CLOSURE, not body equality, and because for each
# of the four the disagreement was resolved by the maintainer's 2026-09-14 standing ruling that
# `oc_runipd` is the preferred version absent a significant behavioral difference.
#
# WHY BODY EQUALITY IS THE WRONG TEST, since this module's own docstring leads with it. A definition
# can MOVE here only if every module-level free name its body closes over resolves here. Body equality
# says the two hosts AGREE; it says nothing about whether the code can be relocated. Measured at
# `i3d6ml`'s execution HEAD: of the 48 symbols that carried no behavioral disagreement, only 9 were
# closure-clean, 11 must never move, and 28 close over a name this module cannot yet reach. So the
# admission question for a lift is closure FIRST and agreement SECOND, and this section records both
# for each symbol.
#
# THE FOUR OBSERVABLE CHANGES, disclosed rather than absorbed, each at its own definition below:
#   * `attempt_log_path`  - agy's verifier log filename changes shape. This REPAIRS a live defect.
#   * `write_prompt`      - agy's suffixed prompt filename changes shape (a SEMANTIC difference, not
#                           a tag reordering).
#   * `build_review_prompt` - agy reached the isolation notice through its own `build_isolation_notice`
#                           wrapper; both now call `lane_containment.isolation_notice` directly, which
#                           is the same function that wrapper called.
#   * `resolve_prior_lane` - agy was a delegating stub importing oc, so this DELETES a runner-to-runner
#                           import rather than changing output.
#
# WHAT IS DELIBERATELY NOT HERE, because an absence is what a later reader "completes" by mistake:
# the 10 `INJECTED` symbols above keep their one-line host wrapper (that wrapper IS the de-duplicated
# form, ruled by the maintainer in `818uru` OQ-02), and `disable_lane_prompt` stays defined in both
# runners because it writes a module-level flag through `global`. Both exclusions are asserted, in the
# INVERSE direction, by `tests/test_rununify_lift.py`.


def _findings_block_reason(repo: Path, dep: str) -> str | None:
    """Return an operator-facing reason ``dep``'s review blocks its dependents, else None.

    revgate Order 03 (7nkcgp) E-01/E-02. Delegates ENTIRELY to
    ``review_findings.subject_gating_blocks``, the ONE shared predicate, which both host runners, the
    `aw check` evaluator, and the `/exec-set` Set compiler consume. This function re-implements no
    severity comparison and holds no threshold of its own, so the four surfaces cannot drift.

    SHARED SINCE rununify 03 (`i3d6ml`). Both runners held an AST-identical copy of this wrapper, and
    both docstrings said the same thing about why: "this wrapper exists only because neither runner
    imports the other (the duplication the in-flight `rununify` Set exists to fix)". That reason is
    now discharged - the wrapper lives in the shared module both runners already import, so there is
    one wrapper in front of one predicate. `agy_runipd` keeps the NAME bound (a re-export) because
    `tests/test_review_findings_cascade.py::SharedPredicateTests` asserts the attribute exists on that
    module and that its source names `subject_gating_blocks`; the import line satisfies both.

    Fail-open on import/IO error: a crashing gate is a disabled gate, and this must never wedge a run.
    """
    try:
        from agent_workflows import review_findings as _rf

        blocks = _rf.subject_gating_blocks(repo, dep)
    except Exception:
        return None
    if not blocks:
        return None
    return "; ".join(b.describe() for b in blocks)


def make_integration_validation_runner(
    state: dict[str, Any], run_dir: Path, item: dict[str, Any]
) -> Any:
    """Build the `full_validation_runner(combined_diff, merged_files) -> bool` the integration gate
    calls to REVALIDATE the combined HEAD (per-lane green never implies integrated green).

    For a serial run each IPD is a SINGLE lane, so the combined diff == the lane diff the driver's
    independent verifier turn already validated (verify_disp == "verified" is the gate precondition for
    reaching integration). The runner therefore returns True on the already-verified single-lane case.

    SHARED SINCE rununify 03 (`i3d6ml`), with one consequence a caller must know. Tests PATCH THIS
    FUNCTION to exercise a combined-red path, and there is now ONE function to patch. A test that
    patched `oc_runipd.make_integration_validation_runner` still works, because that name is a
    re-export bound in the runner's namespace and patching the runner's attribute is what the call site
    resolves; but a test patching it on one runner no longer leaves the other host's copy unpatched,
    because there is no other copy.
    """

    def _runner(_combined_diff: str, _merged_files: Any) -> bool:
        return True

    return _runner


def build_review_prompt(
    item: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
    plan_path: Path,
    repo: Path,
    lane_root: Path | None = None,
) -> str:
    """Return the slash command for a review turn: `/plan-review <relative path>`, plus - for an
    ISOLATED review - the in-lane statement on its OWN LINES after it.

    Deliberately prose-free ON THE COMMAND LINE (terseout `ntf6sx` E-05). This value is handed to the
    host as ONE argv element after `--`, so anything appended to the COMMAND LINE is absorbed by the
    slash command's `$ARGUMENTS` and parsed as additional path arguments. That constraint is about the
    LINE, not about the string: prose goes on a separate line AFTER the command, never on the command
    line itself, which is exactly the shape used below.

    dirtygates Order 05 (`ajxr5d`) E-02: `lane_root` makes the two halves an isolated turn needs BOTH
    true. FIRST the path: it is resolved against the LANE, so the command names the lane's own copy of
    the plan. SECOND the statement: the shared `lane_containment.isolation_notice` is appended, and it
    is MANDATORY rather than decorative. The guard it satisfies exists because of a measured incident
    (run `run-20260831T153226Z-3424176`, plan `y6mfgo`) in which the prompt carried MAIN's absolute plan
    path with no statement of isolation, and the agent read `../../../DECISIONS.md` and committed 18
    files into MAIN while its lane stayed at zero commits. `--dir` alone does not convey isolation, so
    the path fix WITHOUT the statement is the half-fix that was already measured insufficient.

    A NON-isolated review (`lane_root is None`) returns the byte-identical single line it always did,
    which is spec R1.3's requirement that non-isolated execution not be degraded by isolation work.

    SHARED SINCE rununify 03 (`i3d6ml`), and the two hosts' bodies were NOT byte-identical: oc called
    `lane_containment.isolation_notice` directly while agy called its own `build_isolation_notice`,
    whose entire body is `return lane_containment.isolation_notice(lane_root)`. So the two produced the
    same string through a different number of hops, and taking oc's form changes no output. THE IMPORT
    IS FUNCTION-LOCAL and must stay that way: `lane_containment` imports THIS module at its own top
    level (`agent_workflows/lane_containment.py:55`), so a module-level import here is an import cycle.
    That is the convention this module already uses in 20-plus places.
    """

    from agent_workflows import lane_containment

    root = lane_root if lane_root is not None else repo
    try:
        rel_path = str(plan_path.relative_to(root))
    except ValueError:
        rel_path = str(plan_path)
    command = f"/plan-review {rel_path}"
    if lane_root is None:
        return command
    return command + "\n" + lane_containment.isolation_notice(lane_root)


def resolve_prior_lane(
    item: dict[str, Any],
) -> tuple[str | None, str | None, str | None]:
    """The PRIOR attempt's lane identity from DURABLE state: (lane_id, base_commit, branch).

    Reads the record, and NEVER reconstructs a branch name from the id6: `lane_branch_name`'s
    docstring forbids exactly that, because allocation may have attempt-scoped the name, so a
    reconstructed name can silently designate a different lane than the one that holds the work.

    Order, most to least authoritative:
      1. `preserved_lane_id`/`preserved_base`, written when a lane is preserved for precisely this
         purpose (a later turn finding a preserved lane).
      2. the newest `attempts[]` entry carrying `worktree_lane_id`, for an attempt interrupted before
         it reached the preservation path.
      3. the newest attempt's `worktree_displaced_from`, which names the lane a fresh allocation was
         displaced from.

    Returns (None, None, None) when nothing is recorded, which is the honest first-attempt answer and
    routes to fresh execution.

    SHARED SINCE rununify 03 (`i3d6ml`). This is the case where the lift DELETES A RUNNER-TO-RUNNER
    IMPORT rather than changing behavior: `agy_runipd.resolve_prior_lane` was a stub whose body was
    `from agent_workflows.oc_runipd import resolve_prior_lane as _shared; return _shared(item)`, i.e.
    the antigravity driver reached into the opencode driver at call time. There was already only one
    implementation; what changes is WHERE it lives, and the shared module is a place agy may import
    without `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import` having to be
    satisfied on a technicality.
    """
    lane_id = item.get("preserved_lane_id")
    if lane_id:
        return (
            str(lane_id),
            item.get("preserved_base"),
            item.get("preserved_branch"),
        )
    for attempt in reversed(item.get("attempts", []) or []):
        if attempt.get("worktree_lane_id"):
            return (
                str(attempt["worktree_lane_id"]),
                attempt.get("worktree_base"),
                attempt.get("worktree_branch"),
            )
    for attempt in reversed(item.get("attempts", []) or []):
        displaced = attempt.get("worktree_displaced_from")
        if displaced:
            # `displaced_from` records a BRANCH name, not a lane id, so it MUST be converted.
            # Measured: passing `aw/lane/ntf6sx` to `inspect_lane` as a lane id re-sanitizes it into
            # branch `aw/lane/aw_lane_ntf6sx`, which does not exist and classifies ABSENT - i.e. the
            # work would be silently invisible. `lane_id_from_branch` is the exact inverse.
            from agent_workflows import worktree_lease

            lane = worktree_lease.lane_id_from_branch(str(displaced))
            if lane:
                return lane, attempt.get("worktree_base"), str(displaced)
    return None, None, None


def sync_receipt_into_worktree(repo: Path, worktree: Path, id6: str) -> None:
    """DEPRECATED NO-OP. Retired as the correctness mechanism by the ``dh0uno`` control-root fix.

    This used to COPY the main checkout's begin receipt into the lane worktree so that an in-worktree
    ``aw ipd finalize`` could find it. Research x03wgn Section 7 lists that copy as its own hazard -
    "Receipt copied into lane -> two authorities diverge or are consumed independently" - and the
    prescribed guard is "One central driver-created receipt bound to attempt; delete receipt-copy
    path."

    The copy is no longer load-bearing because ``ipd_lifecycle.receipt_path_for`` now resolves to the
    CHECKOUT's control root (every linked worktree shares one git common dir) instead of to whatever
    tree it was handed. An in-lane finalize therefore reads the ONE receipt the driver wrote, from the
    lane, with no copy in existence. Copying now would actively RE-CREATE the fork this fix closed,
    and in fact src and dst are the SAME path, so the old body raised ``shutil.SameFileError``.

    Kept as an explicit no-op rather than deleted so that no caller breaks: both drivers call it at
    their lane-launch site, and the call is now correctly redundant rather than wrong.

    SHARED SINCE rununify 03 (`i3d6ml`). Both runners' bodies were `return None`, so this lift is the
    cheapest in the set; it is included because two no-ops are still two places a future author could
    "restore" the copy into, and the hazard research says the copy must not come back.
    """
    return None


def write_prompt(
    run_dir: Path, item: dict[str, Any], prompt: str, attempt_no: int, suffix: str = ""
) -> Path:
    """Write ``prompt`` to the run's `prompts/` directory and return the path.

    THE FILENAME IS `<NN>-<id6>-<prefix>-attempt-<n>.md`, where `prefix` is `suffix` when a suffix is
    given and otherwise `review`/`exec` from the item's action.

    SHARED SINCE rununify 03 (`i3d6ml`), AND THIS CHANGES ANTIGRAVITY'S FILENAMES. The two hosts
    disagreed SEMANTICALLY about what `suffix` means, which is why this is disclosed rather than filed
    as a mechanical merge:

      * oc treated `suffix` as REPLACING the action prefix   -> `03-abc123-verify-attempt-1.md`
      * agy treated `suffix` as an ADDITIONAL tag after it   -> `03-abc123-exec-verify-attempt-1.md`

    oc's form is adopted, per the maintainer's 2026-09-14 standing ruling that `oc_runipd` is the
    preferred version absent a significant behavioral difference, and a prompt filename is not one:
    nothing in the package parses a PROMPT filename (unlike the session log next door, whose shape the
    analytics do parse - see `attempt_log_path`). The consequence is bounded and stated: an antigravity
    run started after this change writes a verifier prompt under the oc name, and an operator reading
    an OLD run directory still sees the old name, because nothing renames history.
    """
    prefix = suffix or ("review" if item.get("action") == "review" else "exec")
    path = (
        run_dir
        / "prompts"
        / f"{item['position']:02d}-{item['id6']}-{prefix}-attempt-{attempt_no}.md"
    )
    path.write_text(prompt, encoding="utf-8")
    return path


def attempt_log_path(
    run_dir: Path, item: dict[str, Any], attempt_no: int, suffix: str = ""
) -> Path:
    """The session-log path for one attempt: `<NN>-<id6>-attempt-<n>[-<suffix>].jsonl`.

    SHARED SINCE rununify 03 (`i3d6ml`), AND THIS REPAIRS A LIVE DEFECT ON THE ANTIGRAVITY SIDE. It is
    the one user-visible improvement in that plan, so it is recorded here rather than in a commit
    message. The two hosts placed the suffix on opposite sides of the attempt number:

      * oc  -> `03-abc123-attempt-1-verify.jsonl`
      * agy -> `03-abc123-verify-attempt-1.jsonl`

    `run_analytics_statistics._VERIFY_LOG_RE` is anchored `-attempt-\\d+-verify\\.jsonl$`, which ONLY
    oc's form satisfies. A verifier session log is the sole signal of the verifier phase (measured:
    zero attempt records carry `verify_cost`/`verify_tokens`), so every antigravity verifier log was
    being classified `execute` by `verifier_phase_of_log` and its cost attributed to the wrong phase.
    Adopting oc's shape makes those logs classify `verify`.

    HONEST LIMIT: this fixes logs written from now on. Antigravity logs ALREADY on disk keep the old
    name and stay misclassified, because nothing renames history. `run_viewer.py` was never broken by
    the divergence - it looks for the oc-shaped name first and falls back to a loose glob - so it
    degrades to correct rather than needing a change here.
    """
    tag = f"-{suffix}" if suffix else ""
    return (
        run_dir
        / "sessions"
        / f"{item['position']:02d}-{item['id6']}-attempt-{attempt_no}{tag}.jsonl"
    )


# ---- rununify 05 (`ct4w0a`): the TWO genuine behavior conflicts ----------------------------------
#
# TWO symbols whose host definitions genuinely DISAGREED about behavior rather than about strings or
# style, resolved per the maintainer's 2026-09-14 per-symbol rulings and lifted here. They were held
# back from `i3d6ml` for exactly that reason: lifting a symbol whose two bodies disagree requires
# first DECIDING which behavior is correct, and that decision is recorded at each definition below.
#
# `extract_session_id` - UNION, not "oc wins". This is the one place in the whole Set where the
#   standing oc-preferred ruling had to be EXCEPTED, and the exception is measurable rather than
#   stylistic: oc's reader read three flat `session*` keys, while agy's read those plus
#   `conversation_id` and also looked INSIDE a nested `result`/`init` object. `conversation_id` IS
#   Antigravity's wire format, so adopting oc outright left agy unable to find its OWN session id.
#   Verified by execution: oc's reader returned `None` on an agy-shaped log where agy's returned the
#   id. Losing that silently disables session RESUME, and with it the `b7xarm` one-shot defect-report
#   re-ask, which refuses to fire when no session was observed.
#
# `driver_begin` - ADOPT OC, because agy was measurably DEFICIENT. oc accepts `isolated` and layers
#   `begin_baseline_env(isolated)` onto the child env, which tells `aw ipd begin` WHICH baseline to
#   gate on; agy sent only the pinned env, so an ISOLATED agy turn asked begin to measure the MAIN
#   tree when the turn would execute in a LANE. That is the "one does A, the other NOT A" case the
#   standing ruling resolves toward oc, so agy GAINS a correctness feature here.
#
# WHY `driver_begin` TAKES TWO INJECTED DEPENDENCIES, since the plan that ordered this lift expected
# none. `pinned_child_env` and `pinned_module_argv` are defined in `oc_runipd` and are the ONLY
# definitions in the package; agy reaches them by IMPORTING them from `oc_runipd`, which makes them
# the SAME OBJECT in both hosts but does NOT make them reachable from HERE. This module may never
# import a runner (see the prohibition at the top, enforced by
# `tests/test_runner_shared.py::NoRunnerImportTests`), so the lift condition is closure over names
# THIS module can resolve, and neither name is one. They are therefore INJECTED, which is the
# maintainer's ruled mechanism for this exact situation (`818uru` OQ-02) and is already how
# `run_checked` -- the OTHER nested-`aw` launcher, sitting in this same module -- consumes this SAME
# `pinned_child_env` dependency. Each host keeps a one-line wrapper at the original name and
# signature, so no call site in either driver was rewritten, and the duplicated LAUNCHER BODY (the
# thing this Set exists to remove) now exists exactly once.
#
# THE SESSION-ID KEY LIST IS SHARED TOO, and that matters more than it looks. It was defined TWICE
# with DIFFERENT contents (oc three keys, agy four), so a reader who found either copy first would
# re-fork the disagreement. There is one tuple now.

# The four wire-format keys either host may see, and the ONE definition of that list.
#
# WHY ALL FOUR ARE KEPT DESPITE THREE BEING UNOBSERVED. A census of 627 real session logs (taken at
# the 2026-09-16 review; this lane has no `.aw/records/runs` corpus, see V-01) found `sessionID`
# 167,921 times and `conversation_id` twice, while `sessionId`, `session_id` and the whole `init`
# nesting appeared ZERO times. The authoring plan's own rule would have DELETED those on that
# evidence, and doing so would be wrong twice over. First, 627 logs cannot prove a wire format never
# emits a shape; narrowing a READER on absence-of-evidence is irreversible in the direction that
# loses data. Second, this tuple has a SECOND consumer: `oc_runipd._event_session_id` reads it LIVE
# during a turn to hand the subagent-progress observer a parent session id, so narrowing it would
# quietly change that path too. Widening it to four is INERT for that consumer, which hard-filters on
# a `ses_` prefix that a `conversation_id` value never carries.
_SESSION_ID_KEYS = ("sessionID", "sessionId", "session_id", "conversation_id")

# The nested objects agy's launcher may wrap its id in, checked after the flat keys.
_SESSION_ID_NESTS = ("result", "init")


def extract_session_id(log_path: Path) -> str | None:
    """Return the session / conversation id from a streamed JSONL log, for EITHER host.

    THE UNION of what the two hosts read: all four keys of `_SESSION_ID_KEYS`, checked flat AND inside
    a nested `result`/`init` mapping, with a non-dict event skipped rather than raising.

    PRECEDENCE IS A DECISION, NOT AN EMERGENT PROPERTY (decision `06-ct4w0a-D1`). The two readers
    disagreed about RETURN DISCIPLINE as well as about keys, and no union can keep both: agy returned
    the FIRST non-empty hit immediately, while oc scanned the WHOLE file and kept a non-`ses_` value
    only as a FALLBACK. This adopts OC's discipline, so on a log carrying agy's `conversation_id`
    EARLY and a `ses_`-prefixed value LATER, this returns the `ses_` value where agy's reader returned
    the `conversation_id`. Three reasons that is the right side to keep: oc's preference is a SHIPPED
    TESTED CONTRACT (`tests/test_oc_runipd.py::test_extract_session_id_prefers_ses_prefixed_over_nonprefixed`)
    whereas nothing anywhere pinned agy's ordering; the standing maintainer ruling prefers oc absent a
    significant behavioral difference; and the affected shape needs an unprefixed id EARLY plus a
    `ses_` id LATER in the SAME log, which is an OpenCode id appearing in an Antigravity log and
    occurred in 0 of the 627 logs censused. `tests/test_rununify_conflicts.py` pins this answer so a
    future change to it is a visible test edit rather than a silent drift.

    A NOTE ON WHAT WAS DELETED: agy's body carried a dead `fallback` local, initialized to `None` and
    returned at the end while every branch that could assign it returned immediately instead. It could
    never be non-`None` at that return. Here `fallback` is LIVE and load-bearing (it is oc's
    discipline), which is precisely why the dead twin had to go rather than be copied forward: a
    reader comparing the two would otherwise conclude agy had a fallback discipline it did not have.
    """
    if not log_path.exists():
        return None
    fallback: str | None = None
    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            # agy's guard, kept: a JSONL line may legitimately be a list or a scalar, and `.get` on
            # one raises. oc's reader had no such guard and would crash on an agy-shaped log.
            if not isinstance(event, dict):
                continue
            scopes: list[Mapping[str, Any]] = [event]
            for nest in _SESSION_ID_NESTS:
                nested = event.get(nest)
                if isinstance(nested, dict):
                    scopes.append(nested)
            for scope in scopes:
                for key in _SESSION_ID_KEYS:
                    value = scope.get(key)
                    if not isinstance(value, str) or not value.strip():
                        continue
                    if value.startswith("ses_"):
                        return value
                    if fallback is None:
                        fallback = value
    return fallback


def begin_baseline_env(isolated: bool) -> dict[str, str]:
    """The child-env overlay declaring WHICH baseline `aw ipd begin` should measure.

    lanetruth Order 02 (z2isfg). `begin` gates execution authority on this plan's in-scope paths being
    unambiguous in the baseline the turn will EXECUTE against. For an isolated turn that baseline is a
    fresh worktree cut at the frozen base commit, which is clean by construction, so uncommitted work
    in the MAIN tree cannot reach it. Measuring the main tree there refused unrelated lanes over a
    co-worker's edit to a commonly-scoped file, and the message's own remedy (commit or stash it) is
    one the shared-checkout contract forbids. Only the DRIVER knows which case applies, so it declares
    it here; a non-isolated turn sends nothing and the existing main-tree refusal is preserved verbatim.

    Env rather than a CLI flag: `--dir` must keep meaning "the repo root" (the receipt stays under the
    MAIN repo's state root even for an isolated turn) and a new flag would have to be declared in
    `agent_workflows/cli.py`, which the plan that introduced this excluded.

    SHARED SINCE rununify 05 (`ct4w0a`): it was defined in `oc_runipd` only, and lifting `driver_begin`
    without it would have left the shared launcher reaching into a host. Note the ASYMMETRY it removes:
    agy never called this, so an isolated `aw agy run` turn declared nothing and begin measured the
    wrong tree."""
    return {"AW_ISOLATED_BASELINE": "1"} if isolated else {}


def driver_begin(
    repo: Path,
    id6: str,
    actor: str,
    *,
    isolated: bool = False,
    env_builder: Callable[[], Mapping[str, str]] | None = None,
    argv_builder: Callable[[Sequence[str]], list[str]] | None = None,
) -> tuple[int, str]:
    """Run the fail-closed `aw ipd begin <id6> --actor` gate before an execute turn.

    Reuses the packaged `aw ipd begin` surface (subprocess to `python -m agent_workflows`, mirroring
    `set_plan_approved`/`finalize_orchestrator`); begin writes the gitignored
    `.aw/state/ipd-lifecycle/<id6>.receipt.json` receipt (execution authority) itself. Returns
    (exit_code, stderr): exit 0 = receipt written; nonzero = refusal (no execution authority).

    `isolated` declares that the gated turn will execute in a fresh isolated worktree rather than in
    `repo` itself, which selects the baseline begin measures (see `begin_baseline_env`). It does NOT
    change where the receipt lives, nor the receipt's frozen `base_head`, which is always this repo's
    HEAD because finalize consumes it as a git revision.

    THE ONE DEFINITION SINCE rununify 05 (`ct4w0a`), previously one per host with agy's silently
    lacking the `isolated` declaration. `env_builder` and `argv_builder` are INJECTED because the pin
    helpers they bind (`pinned_child_env`, `pinned_module_argv`) are defined in `oc_runipd` and this
    module may not import a runner; see the section header for the full reasoning and the
    `818uru` OQ-02 ruling that prescribes this mechanism. Each host wraps this at the original name and
    signature and binds its own, so both hosts still reach the SAME pin objects they did before."""
    # lanetruth Order 01 (af7i6p): pinned to the runner's OWN tooling. NOTE this particular site
    # is NOT itself lane-shadowed -- it runs with `cwd=str(repo)` (the MAIN tree) and the lane is
    # allocated only AFTER begin returns -- but it is pinned anyway so exactly one shape exists
    # across all launch sites and no future refactor can quietly make it lane-relative.
    if argv_builder is None:
        argv_builder = globals()["pinned_module_argv"]
    if env_builder is None:
        env_builder = globals()["pinned_child_env"]
    cmd = argv_builder(
        [
            "ipd",
            "begin",
            id6,
            "--actor",
            actor,
            "--dir",
            str(repo),
        ]
    )
    result = subprocess.run(
        cmd,
        cwd=str(repo),
        # lanetruth Order 01 (af7i6p) + Order 02 (z2isfg): the pinned env is the BASE and the
        # baseline declaration is layered on top, so the turn measures the tree it will really
        # execute in WITHOUT unpinning the tooling. The pin's arrival at the child is asserted
        # BEHAVIORALLY by `tests/test_lane_tool_identity.py` (it reads the env this builds and
        # checks the pin's markers), which is strictly stronger than the source-text search that
        # guard used before this symbol was shared -- that search was measurably satisfiable by a
        # COMMENT, and on oc a comment is what satisfied it.
        env={**env_builder(), **begin_baseline_env(isolated)},
        text=True,
        # ttywedge Order 01 (g40w37): DENY the child a terminal. Without this, stdin is INHERITED, so a
        # nested `aw` sees the operator's TTY, believes it may prompt, and blocks on input() forever
        # while its prompt goes into the pipe below. Verified: a finalize wedged 1h49m this way.
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode, (result.stderr or result.stdout or "").strip()


# ---- THE HOST DESCRIPTOR (rununify Order 04, `tx6q0h`) -------------------------------------------
# Eight symbols were defined TWICE and their difference was dominated by a host-identifying string.
# They now have ONE definition each, below, and the host string arrives as DATA through `HostLabels`
# rather than being baked into a second copy of the logic.
#
# WHY A DESCRIPTOR AND NOT AN IMPORT, restated because the module docstring's prohibition applies
# with full force here: shared code must not import a runner, so it cannot ASK which host it is
# running for. The caller says. That is the same shape `integrate_lane_branch(..., host_label=)`
# already uses (integpath-02 `6sb3yu`), and this generalizes it from one field to the set the lifted
# bodies provably read.
#
# EVERY FIELD IS JUSTIFIED BY A CALL SITE, per the plan's own rule that a field without a named
# consumer is a parameter nobody reads. The consumers are named in the field docstrings below and
# asserted by `tests/test_rununify_host_descriptor.py`.
#
# WHAT IS DELIBERATELY *NOT* A FIELD: a variant/profile flag. `driver_actor` reads
# `options.variant`/`options.launch_profile`, which only the OpenCode host's profile subsystem
# populates (`runner_profiles`, `resolve_launch_profile`, `launch_profile` occur 0 times in
# `agy_runipd.py`). That is a host CAPABILITY, not a label, and the shared body simply finds those
# keys absent on the Antigravity host. Measured before the lift, across every state shape that host
# can produce, oc's logic returns exactly what agy's returned, modulo the label. The `- Launch:`
# REPORT LINE is a different matter and stays OpenCode-only: it renders `profile=(none recorded)` on
# any Antigravity state, so emitting it there would be permanently misleading output rather than
# additive disclosure (plan `tx6q0h` OQ-01, resolved AGAINST adopting it).


class HostLabels(NamedTuple):
    """Every host-varying STRING the lifted runner symbols need, supplied by the calling host.

    NO DEFAULTS, on purpose, and the reason is the same one `integrate_lane_branch`'s `host_label`
    docstring gives, only broader: `command` reaches a plan's PERMANENT finalize record as the
    auto-reconciliation reason, so a defaulted or empty value would misattribute in durable history
    which driver reconciled a scope, and that misattribution is invisible until someone audits the
    record. A `NamedTuple` raises `TypeError` on a missing field at construction and `AttributeError`
    on a missing attribute, so a field can never silently read as empty; a plain mapping with
    `.get()` is the one form this must not be (plan `tx6q0h` OQ-02).
    """

    #: The operator-facing command prefix, e.g. `"aw oc run"`. Consumed by
    #: `_compute_scope_reconciliation` (the finalize record's reason/ack strings),
    #: `_detect_driver_command` (its fallback return) and `driver_actor` (the actor prefix an
    #: `attention_contract` gate then validates).
    command: str

    #: The operator-facing REVIEW command, e.g. `"aw oc review"`. A field of its own rather than a
    #: substitution on `command`, because deriving one operator-facing command from another by string
    #: surgery is exactly the kind of implicit coupling this descriptor exists to remove: it would
    #: break silently the day a host's command is spelled differently. Consumed by
    #: `enforce_requested_action`'s two refusal messages, which are spec `25kzda` 2.6's enforcement.
    review_command: str

    #: The argv tokens naming this driver, e.g. `("oc", "opencode")`. A LIST and not one token
    #: because the Antigravity host accepts `agy` and `antigravity`. Consumed by
    #: `_detect_driver_command`.
    argv_tokens: tuple[str, ...]

    #: The argv subcommand tokens that follow one of `argv_tokens`, e.g. `("run", "runipd")`. Also a
    #: list per host: the Antigravity host additionally accepts `runagy`, and collapsing this to one
    #: token would silently drop that invocation spelling. Consumed by `_detect_driver_command`.
    argv_subcommands: tuple[str, ...]

    #: The host's own product name, e.g. `"OpenCode"`. Consumed by `render_continuation_hint` (the
    #: session-continuity banner and its no-session line), `build_prompt` (the turn title) and
    #: `build_verifier_prompt` ("running in a fresh <name> session").
    product: str

    #: The execution report's H1. Consumed by `write_report`. The two hosts spell this differently
    #: (`"# Execution Report: <run-id>"` vs `"# Antigravity IPD Driver Execution Report: <run-id>"`),
    #: so it is the whole prefix before the run id rather than a bare name.
    report_title: str

    #: The name of the shell tool this host's agent actually has, e.g. `"run_command"` on
    #: Antigravity (mapped at `agy_runipd.py:503`), or None where the host names no tool. Consumed by
    #: `build_verifier_prompt`, whose Antigravity copy told the agent to run tests "using
    #: `run_command`" - a tool an OpenCode agent does not have, so this cannot be a shared literal.
    shell_tool: str | None

    #: True where the report's `- Launch:` line is meaningful, i.e. where the host has the profile
    #: subsystem that populates it. False on Antigravity, where `render_launch_identity` renders
    #: `profile=(none recorded)` for every state (plan `tx6q0h` OQ-01). Consumed by `write_report`.
    #: This is a CAPABILITY switch rather than a string, and it is the only one: it exists because
    #: the alternative measured worse than the duplication it removes.
    emits_launch_identity: bool


#: The OpenCode host's labels. Bound by `oc_runipd`'s wrappers.
OC_HOST_LABELS = HostLabels(
    command="aw oc run",
    review_command="aw oc review",
    argv_tokens=("oc", "opencode"),
    argv_subcommands=("run", "runipd"),
    product="OpenCode",
    report_title="# Execution Report:",
    shell_tool=None,
    emits_launch_identity=True,
)

#: The Antigravity host's labels. Bound by `agy_runipd`'s wrappers.
AGY_HOST_LABELS = HostLabels(
    command="aw agy run",
    review_command="aw agy review",
    argv_tokens=("agy", "antigravity"),
    argv_subcommands=("run", "runipd", "runagy"),
    product="Antigravity",
    report_title="# Antigravity IPD Driver Execution Report:",
    shell_tool="run_command",
    emits_launch_identity=False,
)


# ---- constants the lifted bodies close over ------------------------------------------------------
# All three were BYTE-IDENTICAL in both runners, so this is a relocation and not a reconciliation.
# Each runner re-exports its name, leaving its other call sites untouched.

#: Item statuses that mean the queue finished that item successfully. Read by
#: `render_continuation_hint` to choose between the "inspect" and "resume" hint.
SUCCESS_STATES = {"executed", "reviewed", "approved"}

#: The `--action` values the CLI accepts, and the subset actually implemented. Read by
#: `enforce_requested_action`, which is spec `25kzda` 2.6's enforcement point.
ACTION_CHOICES = ("review", "plan", "execute")
ACTION_IMPLEMENTED = frozenset(("review",))


def compute_scope_reconciliation(
    repo: Path, plan_path: Path, *, labels: HostLabels
) -> tuple[dict[str, str], dict[str, str]]:
    """Compute the two-way scope reconciliation (Order 05) the driver will hand to finalize.

    Reuses the authoritative, read-only `ipd_lifecycle.finalize_precheck` (which validates the
    begin receipt and computes `evidence['scope_audit']` without mutating) rather than
    re-implementing the diff. Returns ({out-of-scope path: reason}, {declared-but-unmodified
    path: ack}). An empty pair means a clean delta (nothing to reconcile).

    `labels.command` names the driver INSIDE A PLAN'S PERMANENT FINALIZE RECORD, which is why
    `HostLabels` carries no defaults: a blank host name here is a durable history defect, not a
    cosmetic one.
    """
    from agent_workflows import ipd_lifecycle

    exit_code, _msg, evidence, _findings = ipd_lifecycle.finalize_precheck(
        repo, plan_path
    )
    if exit_code != 0:
        # The precheck itself refused (bad/missing receipt, failing pre-transition lint). Return
        # empty maps; the finalize call below will surface the same refusal authoritatively.
        return {}, {}
    audit = evidence.get("scope_audit", {}) or {}
    out_of_scope = list(audit.get("out_of_scope_paths", []) or [])
    in_scope_unmodified = list(audit.get("in_scope_unmodified", []) or [])
    # rcptwiden `63425h` E-04 (F-10): paths the execution ADDED to `Scope-Paths` after begin, under the
    # accepted additive widening, ALSO demand a `--scope-reason` each, and they are NOT a subset of
    # `out_of_scope_paths`. WHY THIS BRANCH IS LOAD-BEARING RATHER THAN DEFENSIVE: `finalize_precheck`
    # judges out-of-scope against the RECEIPT's OLD fence, so an added path that is only UNCOMMITTED
    # never appears there (measured: `out_of_scope_paths: []`, `disregarded_unowned_paths: [<path>]`).
    # All three incidents the widening accept exists to fix were finalized by the RUNNER, so without
    # this the lifecycle change converts a STALE refusal into a MISSING-REASON refusal and strands
    # exactly the same lanes.
    widened = list(audit.get("widened_paths", []) or [])
    reasons = {
        p: f"changed by the plan's approved execution (auto-reconciled by {labels.command})"
        for p in out_of_scope
    }
    for p in widened:
        # ONE reason per path: a path that is BOTH widened and out-of-scope (the committed-cohesive
        # case) keeps the widening wording, which is the more accurate description of what happened.
        reasons[p] = (
            "declared in Scope-Paths during execution because the approved work required it "
            f"(additive widening, auto-reconciled by {labels.command})"
        )
    acks = {
        p: f"declared-but-unmodified (auto-acknowledged by {labels.command})"
        for p in in_scope_unmodified
        if p not in set(widened)
    }
    return reasons, acks


def detect_driver_command(*, labels: HostLabels) -> str:
    """Detect the command prefix used to invoke the runner, defaulting to `labels.command`.

    Matches a `labels.argv_tokens` entry followed by a `labels.argv_subcommands` entry, so a host
    that accepts several spellings keeps all of them: the Antigravity driver answers to `runagy` as
    well as `run`/`runipd`, and collapsing either list to a single token would silently drop an
    invocation spelling operators use.
    """
    argv = sys.argv
    for i in range(len(argv) - 1):
        if argv[i] in labels.argv_tokens and argv[i + 1] in labels.argv_subcommands:
            return f"aw {argv[i]} {argv[i + 1]}"
    return labels.command


def driver_actor(state: dict[str, Any], *, labels: HostLabels) -> str:
    """The actor string the driver writes into a lifecycle transition, e.g. `aw oc run model=opus`.

    NO PARENTHESES, and that is a live gate rather than a convention: `attention_contract`'s
    `actor_refusal` (`attention_contract.py:590`) refuses any `(` or `)` and refuses an EMPTY actor
    too, so both the shape and the non-emptiness of this string are checked downstream.

    `variant` and `profile` are emitted only when the frozen state carries them, which in practice
    means only on a host with the profile subsystem that populates them (`runner_profiles` occurs 0
    times in `agy_runipd.py`). On a host without it those keys are simply absent and the branches do
    not run: measured across every state shape that host produces, this returns exactly what its own
    copy returned before the lift, modulo `labels.command`. That measurement, not an assumption, is
    why the capability difference did not need a descriptor field.
    """
    options = state.get("options", {}) or {}
    model = options.get("model")
    parts = [f"model={model}"] if model else []
    variant = options.get("variant")
    if variant:
        parts.append(f"variant={variant}")
    applied_profile = (options.get("launch_profile") or {}).get("applied")
    if applied_profile:
        parts.append(f"profile={applied_profile}")
    return f"{labels.command} " + " ".join(parts) if parts else labels.command


def render_continuation_hint(
    state: dict[str, Any],
    run_dir: Path,
    driver_cmd: str | None = None,
    *,
    labels: HostLabels,
) -> str:
    """Print, on exit, the captured session id(s) and the exact commands to reuse them (run a NEW
    plan in the same session context) or resume / inspect THIS run.

    Sessions are captured even when --session was not passed (extract_session_id reads them from the
    child's streamed JSONL), so this surfaces them without a hand-read of state.json. Handles 0, 1,
    and N captured sessions (a multi-Set run has one session per Set)."""
    pal = Palette(should_color(sys.stdout))
    cmd = driver_cmd or detect_driver_command(labels=labels)
    repo = state.get("repo", ".")
    run_id = state.get("run_id", "run-...")
    sessions = state.get("set_sessions", {})
    captured: list[tuple[str, str]] = [
        (s, sid) for s, sid in sessions.items() if sid and isinstance(sid, str)
    ]

    lines = ["", pal(f"--- {labels.product} Session Continuity ---", "bold")]
    if not captured:
        lines.append(f"No {labels.product} session was captured for this run.")
    elif len(captured) == 1:
        setid, sid = captured[0]
        lines.append(f"Captured session: {pal(sid, 'cyan')} (Set: {setid})")
        lines.append("To run a new plan under the same session:")
        lines.append(f"  {cmd} --session {sid} <selector>")
    else:
        lines.append("Captured sessions by Set:")
        for setid, sid in captured:
            lines.append(f"  - {pal(setid, 'bold')}: {pal(sid, 'cyan')}")
        last_sid = captured[-1][1]
        lines.append("To run a new plan under the most recent session:")
        lines.append(f"  {cmd} --session {last_sid} <selector>")

    queue = state.get("queue", [])
    all_success = all(item.get("status") in SUCCESS_STATES for item in queue)

    if all_success:
        lines.append("To inspect run summary:")
        lines.append(f"  aw runs {run_id}")
    else:
        lines.append("To resume this run:")
        lines.append(f"  {cmd} resume --repo {repo} {run_id}")
    lines.append("")
    return "\n".join(lines)


def enforce_requested_action(
    requested: str | None,
    items: Sequence[tuple[str, str, str]],
    *,
    labels: HostLabels,
) -> None:
    """FAIL CLOSED when `--action <a>` is illegal for any selected item. Raises `DriverError`.

    `items` is [(id6, status, derived_action)], derived by `action_for` exactly as the queue builder
    derives it, so this cannot disagree with what would actually run.

    THIS IS THE SAFETY CONTENT OF `--action`, NOT PLUMBING (revsweep 76gsmv F-9). `action_for`
    returns `execute` for BOTH `approved` AND `reviewed`, the queue builder calls it unconditionally,
    and under `--full-auto` a `reviewed` plan carrying an approving `- Readiness:` is cleared to
    `auto-approved` and EXECUTED. So `aw oc review <approved-id6>` with the flag merely accepted and
    ignored would EXECUTE that plan while the operator typed the word "review". Spec 25kzda 2.6
    forbids exactly that: `--action` "cannot force a status transition, execute an unapproved item,
    or turn a non-runnable record into a runnable one", and 2.1 permits it only when "the requested
    action is legal from every item's current status".

    REFUSED BEFORE THE QUEUE IS FROZEN, matching the fail-closed dependency preflight: the caller
    invokes this from `initialize_run` ahead of the run directory's creation, so a refused run leaves
    no host session, no run directory, and no durable state to reconcile.

    An `orchestrate` item satisfies `--action review` NEVER: an orchestrator past review is not
    agent-executed, so asking to review it is asking for something the driver cannot do at that
    status, and silently including it would put a non-review turn in a review-spelled run.

    TWO NOTES ON THE PROSE, because the Antigravity copy of this docstring carried both claims
    wrongly and lifting it verbatim would have promoted them to shared truth. FIRST, the derived
    action comes from `action_for`, NOT from `determine_action`: both already live in this module and
    are DIFFERENT functions (`action_for` adds orchestrator dispatch and delegates the rest), and both
    hosts' `initialize_run` call `action_for`. SECOND, `--full-auto` does NOT default to True on
    either host; measured, `build_parser().parse_args(['start', 'x']).full_auto` is False on BOTH,
    per the 2026-09-04 maintainer ruling.
    """
    if requested is None:
        return
    action = str(requested).lower().strip()
    if action not in ACTION_CHOICES:
        raise DriverError(
            f"Unknown --action {action!r}; expected one of: {', '.join(ACTION_CHOICES)}"
        )
    if action not in ACTION_IMPLEMENTED:
        raise DriverError(
            f"--action {action} is not implemented yet. Only --action review is available; "
            f"{action}'s per-type legality table (spec 25kzda 2.6) needs the per-type dispatch "
            "this runner does not have. No run was started. To review instead, run: "
            f"{labels.review_command} <selector>"
        )
    illegal = [
        (id6, status, derived) for id6, status, derived in items if derived != action
    ]
    if illegal:
        detail = ", ".join(
            f"{id6} (status {status!r} -> action {derived!r})"
            for id6, status, derived in illegal
        )
        raise DriverError(
            f"--action review is illegal for {len(illegal)} selected item(s): {detail}. "
            "Review is the next legal action only for a to-review or draft plan; an approved or "
            "reviewed plan would EXECUTE, which is not what 'review' asks for. No run was started "
            "and no session launched. To sweep only what actually awaits review, run: "
            f"{labels.review_command}"
        )


def write_report(
    run_dir: Path,
    state: dict[str, Any],
    *,
    labels: HostLabels,
    render_launch_identity: Callable[[dict[str, Any]], str] | None = None,
) -> None:
    """Render the run's operator-facing `execution-report.md`.

    THIS UNIFICATION CHANGED THE ANTIGRAVITY REPORT IN THREE WAYS, all disclosed rather than
    incidental (plan `tx6q0h` E-04, findings F-8 and F-12):

      1. The H1 keeps each host's own spelling, through `labels.report_title`.
      2. The verification column header becomes `Verify` on both (it was `Verification` on
         Antigravity).
      3. THE VERIFY CELL IS NO LONGER BACKTICKED, and this one is a BUG FIX rather than cosmetics.
         `run_viewer.load_run_summary` strips backticks for the id6, setid, action and session
         columns but NOT for the verification column (`run_viewer.py:1008` takes `cols[5].strip()`
         verbatim), and `run_viewer.py:1370` then tests `verification_status == "verified"`.
         Antigravity emitted `` `verified` ``, which never equals `verified`, so NO Antigravity run
         has ever rendered the `[verified]` badge. Emitting it bare repairs that. An executor
         changing this column must keep it BARE.
      4. The empty-verify placeholder becomes an empty cell (it was `N/A` on Antigravity).

    `render_launch_identity` IS INJECTED AND OPTIONAL, and its absence is the point. The `- Launch:`
    line reads `options.variant`/`options.launch_profile`, which only a host with the profile
    subsystem populates; on a host without one it renders `profile=(none recorded)` for EVERY run,
    which is a permanently misleading line rather than additive disclosure. So the line is emitted
    only where `labels.emits_launch_identity` is true AND a renderer was supplied (plan `tx6q0h`
    OQ-01, resolved AGAINST giving it to the Antigravity host).
    """
    counts: dict[str, int] = {}
    for item in state["queue"]:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    lines = [
        f"{labels.report_title} {state.get('run_id', '')}",
        "",
        f"- Repository: `{state.get('repo', '')}`",
        f"- Created: {state.get('created_at', '')}",
        f"- Updated: {state.get('updated_at', '')}",
        f"- Selectors: `{' '.join(state.get('selectors', []))}`",
        f"- Set sessions: `{json.dumps(state.get('set_sessions', {}), sort_keys=True)}`",
        f"- Counts: `{json.dumps(counts, sort_keys=True)}`",
        "- Pushed: no (required; verify independently in outcomes)",
    ]
    # runprofile-03 (`3cm15q`) E-03: the launch identity in the report an operator actually reads,
    # so "which model produced this run" needs no `state.json` archaeology. Appended as its own
    # line ABOVE the table so the table's column contract is unchanged.
    if labels.emits_launch_identity and render_launch_identity is not None:
        lines.append(f"- Launch: {render_launch_identity(state)}")
    lines.extend(
        [
            "",
            "| # | id6 | Set | Action | Status | Verify | Attempts | Last session |",
            "|---:|---|---|---|---|---|---:|---|",
        ]
    )
    for item in state["queue"]:
        attempts = item.get("attempts", [])
        session = attempts[-1].get("session_id", "") if attempts else ""
        action = item.get("action", "execute")
        verify = item.get("verification_status") or ""
        lines.append(
            f"| {item['position']} | `{item['id6']}` | `{item['setid']}` | `{action}` | "
            f"{item['status']} | {verify} | {len(attempts)} | `{session}` |"
        )
    # revgate Order 03 (7nkcgp) E-04: name the ROOT CAUSE in the report an operator actually reads,
    # not only in events.jsonl. Emitted as its own section so the table's column contract is unchanged.
    blocked = [
        item
        for item in state["queue"]
        if item.get("status") == "dependency-blocked"
        and (
            item.get("unsatisfied_dependencies")
            or item.get("unsatisfied_dependency_reasons")
        )
    ]
    if blocked:
        lines.extend(["", "## Dependency blocks (why)", ""])
        for item in blocked:
            reasons = item.get("unsatisfied_dependency_reasons") or {}
            lines.append(f"- `{item['id6']}` (position {item['position']}):")
            for dep in item.get("unsatisfied_dependencies") or []:
                detail = reasons.get(dep) or "dependency not satisfied"
                lines.append(f"  - `{dep}`: {detail}")
            hint = item.get("dependency_block_recovery")
            if hint:
                lines.append(f"  - Recovery: {hint}")
    # lanectn xdr83v E-03 (spec R5.6a): NAME EVERY PRESERVED LANE AND ITS REASON IN THE SUMMARY A HUMAN
    # READS, not only in events.jsonl. Measured basis for making this a requirement rather than polish:
    # run `run-20260901T042331Z-118022` preserved TWO lanes and mentioned it ZERO times here, five
    # preserved lanes were on disk, and the maintainer learned work had been stranded by ASKING. The
    # renderer is SHARED so the two reports cannot disagree about which lanes survived, and it returns
    # [] when nothing was preserved, so an unaffected run's report is byte-identical to before.
    from agent_workflows import lane_containment

    lines.extend(lane_containment.format_preserved_lanes(state))
    lines.extend(
        [
            "",
            "## Review",
            "",
            "Review `decisions-and-questions.md` first, then `outcomes/` and `sessions/`.",
            "",
        ]
    )
    (run_dir / "execution-report.md").write_text("\n".join(lines), encoding="utf-8")


def build_verifier_prompt(
    item: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
    plan_path: Path,
    *,
    labels: HostLabels,
) -> str:
    """The independent-verifier turn prompt, one definition for both hosts.

    TWO THINGS ARE PARAMETERIZED and one was a live safety gap.

    `labels.product` names the host in "running in a fresh <product> session".

    `labels.shell_tool` names the shell tool THAT HOST'S AGENT ACTUALLY HAS. The Antigravity
    copy told the agent to run tests "using `run_command`", which is an Antigravity tool
    (mapped at `agy_runipd.py:503`) and names nothing an OpenCode agent can call, so this could
    not be a shared literal. Where a host names no tool the clause is simply omitted.

    THE SAFETY GAP, fixed here rather than deferred (plan `tx6q0h` F-13): the Antigravity copy
    of this prompt contained NO push prohibition at all while instructing the agent to commit,
    where the OpenCode copy ended the same sentence with "Never push." Counted before the fix:
    1 occurrence on OpenCode, 0 on Antigravity. Both hosts' EXECUTION prompts already carried
    one, so the omission was specific to the VERIFIER path. It now reaches both hosts because
    there is one definition.
    """
    from agent_workflows import reporting_contract

    test_tool = f" using `{labels.shell_tool}`" if labels.shell_tool else ""
    outcome = run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
    verify_outcome = (
        run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}-verification.json"
    )
    return f"""# Independent Rigorous Verification of Executed IPD

Plan: `{plan_path}`
Id: `{item["id6"]}`
Set: `{item["setid"]}`
Run ID: `{state["run_id"]}`
Execution Outcome JSON: `{outcome}`
Verification Outcome JSON to write: `{verify_outcome}`

## Concurrent Work

Other agents may modify this repository concurrently. Work only on files required for your task. Ignore unrelated changes, commits, and untracked files.

Do not alter, revert, stage, or commit another agent's work. Stage only your files; never use `git add .` or `git add -A`.

Before EVERY commit, verify what you are actually about to commit: run `git diff --cached --name-only` and confirm every path listed is one YOU modified for this task; `git restore --staged <path>` anything that is not yours. Path-scoping is NOT by itself sufficient, because `git commit -- <paths>` still commits whatever is ALREADY STAGED for those paths, including a co-worker's edits to the same file.

Stop only if another agent changes a file you are editing or must edit and the changes cannot be safely combined. Never discard their work.

You are an independent, skeptical verifier running in a fresh {labels.product} session to audit
the execution of this IPD. Your goal is to rigorously verify whether the code, tests,
and documentation satisfy every requirement before this plan can be considered executed.

## Verification Requirements:

1. **Inspect Concrete Diffs & Commits**:
   - Inspect the git commits and working tree diffs produced for this IPD.
   - Verify that real functional changes were made, not just cosmetic/vocabulary additions.
   - Ensure all referenced files and symbols in the plan's Scope-Paths actually exist and are wired correctly.

2. **Evidence Table (E-* and V-*)**:
   - Check every Execution item (`E-*`) and every Validation item (`V-*`) in the IPD.
   - Check if the recorded observed evidence matches real code and passing tests.

3. **Run and Verify Test Suite**:
   - Run the required tests and validation commands for this IPD{test_tool} (e.g. `python3 -m pytest <test_file> -v` or `python3 -m unittest ...`).
   - Paste the actual runner output with exit code.
   - Confirm that tests are genuine and testing real assertions (not trivial passes).

4. **In-Scope Fixes**:
   - If you discover safely correctable defects, regressions, or missing test cases within the approved scope, fix them, re-run validation, and commit path-scoped (`git commit -m msg -- <paths>`). Never push.
   - If any unresolvable defect or scope gap remains, report it clearly.

5. **Write Verification Outcome**:
   Before exiting, write valid JSON to `{verify_outcome}`:
   {{
     "schema_version": 1,
     "id6": "{item["id6"]}",
     "verdict": "VERIFIED|CORRECTION_REQUIRED|BLOCKED",
     "summary": "...",
     "evidence": [],
     "tests_run": [],
     "corrections_made": []
   }}

Begin independent verification now.
{reporting_contract.prompt_block()}"""


def build_isolation_notice(lane_root: Path | None) -> str:
    """The WORK HERE block for an isolated turn, or "" for a main-checkout turn."""
    from agent_workflows import lane_containment

    return lane_containment.isolation_notice(lane_root)


def build_verify_and_continue_notice(repo: Path, decision: Any) -> str:
    """The prompt block asking a resumed turn to VERIFY AND COMPLETE prior work (E-04)."""
    if not getattr(decision, "verify_and_continue", False):
        return ""
    branch = getattr(decision, "inspected_branch", None) or "(unknown)"
    lines = [
        "",
        "",
        "## A PRIOR ATTEMPT ALREADY COMMITTED WORK FOR THIS PLAN: verify and continue it",
        "",
        "Do NOT implement this plan from scratch. A previous attempt at this same IPD already",
        f"committed work, and the driver has READ that work: {decision.reason}.",
        "",
        f"THAT WORK IS ON A DIFFERENT BRANCH THAN YOUR WORKING DIRECTORY. It is on `{branch}`,",
        "which is NOT the lane you are running in. Your own lane is where you must produce your",
        "commits; that other branch is READ-ONLY for you.",
        "",
        f"Commits already on `{branch}` (newest first):",
    ]
    for sha, subject in getattr(decision, "real_commits", []):
        lines.append(f"  - {sha} {subject}")
    if getattr(decision, "dirty", False):
        lines.append("")
        lines.append(
            "That lane ALSO has uncommitted changes in its working tree; a commit there whose"
        )
        lines.append(
            "subject says INTERRUPTED SNAPSHOT is preserved mid-edit work, not finished work."
        )
    diffstat = ""
    base_ref = ""
    newest_sha = ""
    real_commits = getattr(decision, "real_commits", [])
    if real_commits:
        base_ref = f"{real_commits[-1][0]}~1"
        newest_sha = real_commits[0][0]
        rc, out, _err = _run_git(repo, ["diff", "--stat", base_ref, newest_sha])
        if rc == 0 and out.strip():
            diffstat = out.strip()
    if diffstat:
        diff_cmd = f"git diff --stat {base_ref} {newest_sha}"
        lines.extend(
            [
                "",
                f"Diffstat of that work against its base (`{diff_cmd}`):",
                "",
            ]
        )
        lines.extend("    " + line for line in diffstat.splitlines())
    lines.extend(
        [
            "",
            "WHAT TO DO, in this order:",
            "",
            f"1. READ that work first. `git log {branch}` and `git diff` against that ref show you",
            "   exactly what exists. Read it before you write anything.",
            "2. Judge it against the plan: which `E-*` items does it actually perform, which `V-*`",
            "   items does it evidence, and what is still missing or wrong.",
            "3. BRING FORWARD what is still correct INTO YOUR OWN LANE, then finish the remainder",
            "   there. Re-authoring work that is already correct produces a duplicate sibling commit",
            "   and is the exact waste this routing exists to prevent.",
            f"4. Do NOT `git checkout`, merge, cherry-pick onto, rebase, or commit to `{branch}`, and",
            "   do not amend or delete anything on it. It may hold another attempt's preserved work",
            "   and must be left byte-identical. Read it; never write it.",
            "5. If you conclude the work is ALREADY COMPLETE, you still may not simply assert that:",
            "   fill each `V-*` item's `Observed evidence:` with the prior work's ACTUAL output (run",
            "   the tests yourself and paste what they print). A finalize gate checks the checklists",
            "   and their evidence, not your conclusion.",
        ]
    )
    return "\n".join(lines)


def build_prompt(
    item: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
    plan_path: Path,
    recovery: bool,
    lane_root: Path | None = None,
    routing: Any = None,
    *,
    labels: HostLabels,
    build_isolation_notice: Callable[[Path | None], str] = build_isolation_notice,
    build_verify_and_continue_notice: Callable[
        [Path, Any], str
    ] = build_verify_and_continue_notice,
) -> str:
    """The execution turn prompt, ONE definition for both hosts.

    ONLY `labels.product` (the turn title) varies by host. Everything else is INSTRUCTION TEXT and is
    now identical on both, which is a DELIBERATE BEHAVIOR CHANGE authorized by the maintainer and
    recorded in plan `tx6q0h` OQ-03, not an incidental effect of de-duplication. State it plainly,
    because a later reader will otherwise read it as a refactor: the two hosts previously handed their
    agents different rulebooks. Rendering both from one fixture, 34 lines differed and 32 carried no
    host token, and the Antigravity agent was told NONE of the following, all of which it now receives:

      * preserve partial work through "the repository-supported nonterminal checkpoint mechanism or an
        attributable isolated branch/worktree";
      * "Leave every checkout you did not own safe for subsequent turns";
      * "Never claim executed unless the real terminal state and acceptance criteria support it";
      * "If no material question arose, say so in the summary".

    So this REMOVES a safety asymmetry rather than creating one: the host whose agents were likelier
    to strand partial work and to over-claim completion now gets the same instructions as the other.
    The maintainer's directive ("one code base shared by the two runners that contains 100% of the
    otherwise redundant code") selected this over the alternatives of deferring the change or keeping
    two prose variants behind a parameter, the latter being duplication wearing a parameter.

    `build_isolation_notice` and `build_verify_and_continue_notice` are INJECTED rather than imported,
    per this module's standing rule: a shared module must not import a runner, and these two still
    live per host at this point in the Set's sequence.
    """
    from agent_workflows import lane_containment, reporting_contract

    setid = item["setid"]
    # lanectn `cqx5v7` E-01 (spec R1.1, R1.3): every worker-facing path is projected through the ONE
    # host-neutral rule. For an ISOLATED turn they come back lane-relative, so the emitted prompt
    # names no absolute path outside the lane; for a non-isolated turn (`lane_root is None`) the
    # projection returns exactly the absolute paths this function interpolated before, so that branch
    # is byte-identical.
    paths = lane_containment.project_worker_paths(
        item=item,
        run_id=state["run_id"],
        run_dir=run_dir,
        plan_path=plan_path,
        lane_root=lane_root,
    )
    lane_containment.prepare_lane_submission_dir(paths)
    decisions = paths.prompt_decisions
    outcome = paths.prompt_outcome
    report = paths.prompt_report
    report_label = paths.prompt_report_label
    run_dir_line = paths.prompt_run_dir
    run_dir_label = paths.prompt_run_dir_label
    plan_line = paths.prompt_plan
    mode = "RECOVERY/CONTINUATION" if recovery else "NORMAL EXECUTION"
    prior = item.get("attempts", [])[-1] if recovery and item.get("attempts") else None
    # A prior-attempt record carries `prompt`, `log`, and `worktree` as ABSOLUTE driver-side paths, so
    # dumping it whole re-introduced out-of-lane paths on every RECOVERY turn through a route the
    # path projection does not touch. Non-isolated turns still get the full record (R1.3).
    prior = lane_containment.prior_attempt_summary(prior, lane_root)
    # The recovery notice legitimately describes a PREVIOUS attempt's lane, which may be a different
    # directory (an attempt-scoped lane), hence out-of-lane for this turn. Narrow scrub, notice only.
    lane_notice = build_recovery_lane_notice(item, state, recovery)
    if lane_root is not None:
        lane_notice = lane_containment.scrub_out_of_lane_paths(lane_notice, lane_root)
    # resumedupe (`txc9l1`) E-04: when the driver has ALREADY READ the prior attempt's lane and found
    # finished work there, ADD the verify-and-continue block. The existing recovery notice is kept
    # rather than replaced: it carries the interrupt facts, and this adds the routing instruction. A
    # `fresh-execution` recovery prompt and every first-attempt prompt are therefore unchanged.
    verify_notice = (
        build_verify_and_continue_notice(Path(state["repo"]), routing)
        if routing is not None and recovery
        else ""
    )
    isolation_notice = build_isolation_notice(lane_root)
    return f"""# {labels.product} IPD Driver Turn

Mode: {mode}{lane_notice}{verify_notice}{isolation_notice}
Run ID: {state["run_id"]}
Queue position: {item["position"]}
Assigned IPD: {item["id6"]}
Assigned Set: {setid}
Plan file at launch: {plan_line}
{run_dir_label}: {run_dir_line}
Decisions/questions register: {decisions}
Required JSON outcome: {outcome}
{report_label}: {report}
Prior attempt: {json.dumps(prior, sort_keys=True) if prior else "none"}

## Concurrent Work

Other agents may modify this repository concurrently. Work only on files required for your task. Ignore unrelated changes, commits, and untracked files.

Do not alter, revert, stage, or commit another agent's work. Stage only your files; never use `git add .` or `git add -A`.

Before EVERY commit, verify what you are actually about to commit: run `git diff --cached --name-only` and confirm every path listed is one YOU modified for this task; `git restore --staged <path>` anything that is not yours. Path-scoping is NOT by itself sufficient, because `git commit -- <paths>` still commits whatever is ALREADY STAGED for those paths, including a co-worker's edits to the same file.

Stop only if another agent changes a file you are editing or must edit and the changes cannot be safely combined. Never discard their work.

Execute only IPD {item["id6"]}. Read the attached driver runbook, every applicable
repository instruction, the assigned IPD in full, its current orchestrator, current
repository state, and completed prerequisite artifacts before editing. Do not implement
another IPD in this turn.

All target IPDs are already human-approved. Do not ask for approval. This run is
non-interactive: do not invoke an interactive question tool or wait for human input.
When a material question arises, investigate the approved plans, repository decisions,
source, tests, history, and current primary documentation. If a reasonable recommended
approach exists, choose it, record it in the decisions/questions register with evidence,
alternatives, rationale, confidence, scope, reversibility, and validation, then continue.
If no reasonable approach exists, record a DEFERRED question with the work completed,
work blocked, dependency effect, exact preserved state, and recommended human action.
Continue every independent part of this IPD despite a deferred question.

Maximize safe forward progress. A local failure or unanswered question is not permission
to abandon independent work. Do not weaken checks, fabricate evidence, broaden approved
scope, bypass lifecycle controls, discard unrelated work, or push. Do not use git add -A,
git add ., git commit -a, --no-verify, destructive reset/clean, or stashing that could hide
ownership. Use the lifecycle available at this bootstrap stage and path-scoped commits.

If the IPD cannot validly finalize, preserve partial work using the repository-supported
nonterminal checkpoint mechanism or an attributable isolated branch/worktree. Leave every
checkout you did not own safe for subsequent turns. Never claim executed unless the real
terminal state and acceptance criteria support it.

Run every command you need the RESULT of in the FOREGROUND and wait for it to finish. Do not
start a long command as a background or scheduled task and then end your turn: your turn's
processes are terminated when it ends, so a backgrounded test suite is killed unfinished and
you will have produced nothing. This applies above all to the validation suite, which takes
minutes in this repository. Never end your turn while waiting for a command you started. If a
command genuinely cannot finish in this turn, treat that as a deferred question and record the
preserved state, rather than exiting with the work outstanding.

Before exiting, write valid JSON to {outcome} with at least:
{{
  "schema_version": 1,
  "run_id": "{state["run_id"]}",
  "position": {item["position"]},
  "id6": "{item["id6"]}",
  "setid": "{setid}",
  "disposition": "executed|substantially-complete|partial|blocked|failed-safely",
  "summary": "...",
  "starting_head": "...",
  "ending_head": "...",
  "commits": [],
  "files_changed": [],
  "tests": [],
  "decision_ids": [],
  "deferred_question_ids": [],
  "incomplete_requirements": [],
{defect_report_schema_literal()}
  "partial_work_location": null,
  "recommended_next_action": "...",
  "pushed": false
}}

The disposition must describe the actual repository result, not merely your effort. If no
material question arose, say so in the summary. Explicitly confirm pushed=false.
{defect_report_prompt_block()}{reporting_contract.prompt_block()}"""


def initialize_run_core(
    args: argparse.Namespace,
    *,
    host: str,
    driver_path: Path,
    host_options: dict[str, Any],
    expand_selectors_fn: Any = None,
    enforce_dependency_preflight_fn: Any = None,
    set_plan_approved_fn: Any = None,
    announce_run_order_fn: Any = None,
    is_plan_review_approved_fn: Any = None,
    run_order_rationale_fn: Any = None,
    write_report_fn: Any = None,
    git_common_dir_fn: Any = None,
    parse_dependency_token_fn: Any = None,
    default_runbook_text: str | None = None,
    default_stall_timeout: float | None = None,
) -> Path:
    """Shared core initialization for all runner hosts.

    Unifies the common runner initialization: repo validation, early flag refusals,
    manifest/runbook discovery, selector expansion, draft admission gate, dependency
    preflight, action legality checks, mixed-type gate, run directory creation, queue
    building, state/events persistence, and execution report emission.
    """
    repo = Path(args.repo).expanduser().resolve()
    if not (repo / ".git").exists():
        try:
            common_dir_exists = (
                git_common_dir_fn(repo).exists() if git_common_dir_fn else False
            )
        except DriverError:
            common_dir_exists = False
        if not common_dir_exists:
            raise DriverError(f"Not a Git repository: {repo}")

    if getattr(args, "manifest", None):
        manifest_path = Path(args.manifest).expanduser().resolve()
        manifest = load_json(manifest_path)
        validate_manifest(manifest, parse_dependency_token=parse_dependency_token_fn)
    else:
        discovered = discover_plans(repo, parse_plan_file=parse_plan_file)
        manifest = build_dynamic_manifest(repo, discovered)
        manifest_path = None

    if getattr(args, "runbook", None):
        runbook_path = Path(args.runbook).expanduser().resolve()
    else:
        default_rb = (
            repo
            / "tools"
            / "ipdrunner"
            / "20260823-pending-ipds-overnight-execution-runbook.md"
        )
        if default_rb.is_file():
            runbook_path = default_rb.resolve()
        else:
            runbook_path = None

    refuse_unimplemented_run_flags(args)
    evaluate_unverifiable_admission(args)
    resolve_retry_budget(getattr(args, "retry_budget", None))
    resolve_integration_retry_limit(getattr(args, "integration_retry_limit", None))
    resolve_on_integration_blocked(getattr(args, "on_integration_blocked", None))
    report_untracked_dirt_at_run_start(repo)

    queue_ids = expand_selectors_fn(manifest, args.selectors, repo=repo)

    if is_status_selector(args.selectors):
        queue_ids, draft_verdict = enforce_draft_admission_gate(
            manifest,
            queue_ids,
            repo=repo,
            allow_drafts=bool(getattr(args, "allow_drafts", False)),
            interactive=is_interactive_run(args),
            host=host,
            selector=" ".join(str(s) for s in args.selectors),
        )
        if not queue_ids:
            raise (
                EmptyStatusSelection(
                    "No items in 'to-review' state found in repository"
                )
                if is_review_selector(args.selectors)
                else DriverError("No actionable pending IPDs found in repository")
            )
    else:
        draft_verdict = None

    selected_plan_paths: list[Path] = []
    for id6 in queue_ids:
        try:
            selected_plan_paths.append(
                resolve_plan_path(repo, manifest["plans"][id6].get("file", ""), id6)
            )
        except (DriverError, KeyError):
            continue
    enforce_dependency_preflight_fn(repo, selected_plan_paths)

    requested_action = getattr(args, "action", None)
    if requested_action is not None:
        preflight_items: list[tuple[str, str, str]] = []
        for id6 in queue_ids:
            plan_info = manifest["plans"].get(id6, {})
            st = plan_info.get("status")
            probe_path = None
            try:
                probe_path = resolve_plan_path(repo, plan_info.get("file", ""), id6)
            except Exception:
                probe_path = None
            if not st and probe_path is not None:
                try:
                    rec_probe = parse_plan_file(probe_path, repo)
                    st = rec_probe.status if rec_probe else None
                except Exception:
                    st = None
            st = st or "approved"
            preflight_items.append(
                (id6, st, action_for(resolve_manifest_kind(plan_info, probe_path), st))
            )
        labels = AGY_HOST_LABELS if host == "agy" else OC_HOST_LABELS
        enforce_requested_action(requested_action, preflight_items, labels=labels)

    mixed_verdict = enforce_mixed_type_gate(
        repo,
        selected_plan_paths,
        allow_mixed=bool(getattr(args, "allow_mixed", False)),
        interactive=is_interactive_run(args),
        host=host,
        selector=" ".join(str(s) for s in args.selectors),
    )

    run_id = getattr(args, "run_id", None) or new_run_id()
    run_dir = state_root(repo) / run_id
    if run_dir.exists():
        raise DriverError(f"Run already exists: {run_id}")
    for name in ("sessions", "outcomes", "prompts"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    (run_dir / "decisions-and-questions.md").write_text(
        f"# Decisions and Questions for {run_id}\n\n", encoding="utf-8"
    )

    if manifest_path is None:
        manifest_path = run_dir / "manifest.json"
        atomic_write_json(manifest_path, manifest)

    if runbook_path is None:
        runbook_path = run_dir / "runbook.md"
        runbook_text = (
            default_runbook_text
            if default_runbook_text is not None
            else (
                "# IPD Autonomous Execution Runbook\n\n"
                "This runbook guides automated execution.\n"
            )
        )
        runbook_path.write_text(runbook_text, encoding="utf-8")

    initial_session = getattr(args, "session", None)
    set_sessions: dict[str, str] = {}
    queue: list[dict[str, Any]] = []
    full_auto = getattr(args, "full_auto", False)
    for position, id6 in enumerate(queue_ids, start=1):
        plan = manifest["plans"][id6]
        setid = plan["set"]
        if initial_session:
            set_sessions[setid] = initial_session

        status = plan.get("status")
        p_path = None
        rec = None
        try:
            p_path = resolve_plan_path(repo, plan.get("file", ""), id6)
            rec = parse_plan_file(p_path, repo)
            if rec and not status:
                status = rec.status
        except Exception:
            if not status:
                status = "approved"

        if status == "reviewed" and full_auto and p_path:
            try:
                if is_plan_review_approved_fn(p_path):
                    set_plan_approved_fn(repo, id6)
                    status = "auto-approved"
            except Exception:
                pass

        kind = resolve_manifest_kind(plan, p_path)
        action = action_for(kind, status or "approved")
        queue.append(
            {
                "position": position,
                "id6": id6,
                "setid": setid,
                "configured_file": plan["file"],
                "dependencies": plan.get("dependencies", []),
                "kind": kind,
                "order": plan.get("order"),
                "from_backlog": plan.get("from_backlog")
                or (getattr(rec, "from_backlog", None) if p_path else None),
                "initial_status": status or "approved",
                "action": action,
                "status": initial_queue_status(status),
                "attempts": [],
            }
        )

    stall_timeout = (
        getattr(args, "stall_timeout", default_stall_timeout)
        if default_stall_timeout is not None
        else getattr(args, "stall_timeout", 600.0)
    )

    state = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "repo": str(repo),
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "runbook": str(runbook_path),
        "runbook_sha256": sha256_file(runbook_path),
        "selectors": list(args.selectors),
        "queue": queue,
        "run_order": run_order_rationale_fn(queue, list(args.selectors)),
        "session_id": initial_session,
        "set_sessions": set_sessions,
        "session_turn_counts": {},
        "options": {
            "session": initial_session,
            "output_mode": getattr(args, "output_mode", "clean"),
            "verbosity": getattr(args, "verbosity", 0) or 0,
            "stall_timeout": stall_timeout,
            "full_auto": full_auto,
            "self_finalize": getattr(args, "self_finalize", True),
            "isolate_worktree": getattr(args, "isolate_worktree", True),
            "max_items_per_session": getattr(args, "max_items_per_session", 4),
            "action": requested_action,
            **freeze_run_policy_flags(args),
            **host_options,
        },
        "driver": {
            "path": str(driver_path.resolve()),
            "sha256": sha256_file(driver_path),
        },
    }
    atomic_write_json(run_dir / "state.json", state)
    append_jsonl(
        run_dir / "events.jsonl",
        {"at": utc_now(), "event": "run-created", "run_id": run_id, "queue": queue_ids},
    )
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "at": utc_now(),
            "event": "mixed-type-gate",
            "gate_applied": mixed_verdict.gate_applied,
            "proceed": mixed_verdict.proceed,
            "reason": mixed_verdict.reason,
            **mixed_verdict.record.as_dict(),
        },
    )
    if draft_verdict is not None:
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "draft-admission-gate",
                "gate_applied": draft_verdict.gate_applied,
                "reason": draft_verdict.reason,
                "excluded_complete": list(draft_verdict.excluded_complete),
                "skipped_incomplete": list(draft_verdict.skipped_incomplete),
                **draft_verdict.record.as_dict(),
            },
        )
    write_report_fn(run_dir, state)
    announce_run_order_fn(run_dir, state)
    return run_dir


# ---- rununify: tool identity & child pinning -----------------------------------------------------

_AW_PIN_STRIP = (
    "import os,sys\n"
    "_cwd=os.getcwd()\n"
    "_drop={'',os.curdir,_cwd,os.path.realpath(_cwd)}\n"
    "_keep=os.environ.get('AW_PIN_KEEP_ROOT') or ''\n"
    "_drop-={_keep,os.path.realpath(_keep)} if _keep else set()\n"
    "sys.path[:]=[p for p in sys.path if p not in _drop]\n"
)

_AW_PIN_BOOTSTRAP = (
    _AW_PIN_STRIP
    + "import runpy\n"
    + 'runpy.run_module("agent_workflows",run_name="__main__",alter_sys=True)\n'
)

_AW_PIN_PROBE = _AW_PIN_STRIP + (
    "import agent_workflows as _a\n"
    "_f=getattr(_a,'__file__',None) or (list(getattr(_a,'__path__',[]))+[None])[0]\n"
    "print(os.path.realpath(_f) if _f else 'UNRESOLVED')\n"
    "print(getattr(_a,'__version__',''))\n"
)


class ToolIdentityError(DriverError):
    pass


_TOOL_IDENTITY_VERIFIED: dict[str, Any] = {}


def runner_package_root() -> str:
    """Absolute path of the directory CONTAINING the runner's own ``agent_workflows`` package."""
    return str(Path(__file__).resolve().parent.parent)


def pinned_child_env(env: dict[str, str] | None = None) -> dict[str, str]:
    """Child environment with the runner's own package root PREPENDED to ``PYTHONPATH``."""
    merged = os.environ.copy()
    root = runner_package_root()
    current = merged.get("PYTHONPATH", "")
    if root not in current.split(os.pathsep):
        merged["PYTHONPATH"] = f"{root}{os.pathsep}{current}".rstrip(os.pathsep)
    merged["AW_PIN_KEEP_ROOT"] = root
    if env:
        merged.update(env)
    return merged


def pinned_module_argv(args: Sequence[str]) -> list[str]:
    """argv invoking the RUNNER's OWN ``agent_workflows`` CLI with ``args``."""
    argv = [sys.executable]
    if sys.version_info >= (3, 11):
        argv.append("-P")
    argv.extend(["-c", _AW_PIN_BOOTSTRAP])
    argv.extend(args)
    return argv


def assert_child_tool_identity(
    events_path: Path | None = None, cwd: Path | None = None
) -> dict[str, Any]:
    """Verify a pinned child resolves ``agent_workflows`` to the RUNNER's OWN copy; fail closed."""
    if _TOOL_IDENTITY_VERIFIED:
        return _TOOL_IDENTITY_VERIFIED
    parent_file = str(Path(__file__).resolve().parent / "__init__.py")
    probe_argv = [sys.executable]
    if sys.version_info >= (3, 11):
        probe_argv.append("-P")
    probe_argv.extend(["-c", _AW_PIN_PROBE])
    result = subprocess.run(
        probe_argv,
        cwd=str(cwd) if cwd else None,
        env=pinned_child_env(),
        text=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    lines = [ln.strip() for ln in (result.stdout or "").splitlines() if ln.strip()]
    child_file = lines[0] if lines else ""
    child_version = lines[1] if len(lines) > 1 else ""
    expected = os.path.realpath(parent_file)
    record: dict[str, Any] = {
        "at": utc_now(),
        "event": "tool-identity-verified",
        "expected_module": expected,
        "child_module": child_file,
        "child_version": child_version,
        "parent_version": globals().get("__version__", ""),
        "probe_cwd": str(cwd) if cwd else os.getcwd(),
    }
    if child_file != expected:
        record["event"] = "tool-identity-mismatch"
        record["detail"] = (result.stderr or "").strip()[:500]
        if events_path is not None:
            append_jsonl(events_path, record)
        raise ToolIdentityError(
            "ABORTING RUN: nested `aw` tool-identity mismatch. A nested `aw` would execute "
            "code OTHER than this runner's own installation, so every lifecycle transition "
            "this run performs would be gated by tooling the runner is not.\n"
            f"  expected module: {expected}\n"
            f"  child resolved : {child_file or '<no output>'}\n"
            f"  probe cwd      : {record['probe_cwd']}\n"
            f"  child version  : {child_version or '<unknown>'}\n"
            "This is run-fatal by design (plan af7i6p OQ-02; spec 25kzda 1.4/A1 reserves "
            "ABORT RUN for the identity/integrity class). Marking a single item blocked would "
            "be misleading, since the remaining items would run under the same wrong tooling."
        )
    if events_path is not None:
        append_jsonl(events_path, record)
    _TOOL_IDENTITY_VERIFIED.update(record)
    return record


# ---- rununify: constants and shared models -------------------------------------------------------

FULL_AUTO_APPROVAL_MESSAGE = "Auto-approved via --full-auto (review passed all gates)"
FULL_AUTO_ACTOR = "aw-driver/full-auto"

DEFAULT_STALL_TIMEOUT: float = 600.0

TERMINAL_STATES = frozenset(
    {
        "substantially-complete",
        "not-attempted",
        "dependency-blocked",
        "integration-blocked",
        "executed",
        "approved",
        "partial",
        "merge-conflict",
        "blocked",
        "reviewed",
        "failed-safely",
    }
)


# ---- rununify: recovery routing ------------------------------------------------------------------

DISPOSITION_FRESH_EXECUTION = "fresh-execution"
DISPOSITION_VERIFY_AND_CONTINUE = "verify-and-continue"
DISPOSITION_UNDETERMINED = "undetermined"

RECOVERY_DISPOSITIONS: tuple[str, ...] = (
    DISPOSITION_FRESH_EXECUTION,
    DISPOSITION_VERIFY_AND_CONTINUE,
    DISPOSITION_UNDETERMINED,
)


class RecoveryDisposition(NamedTuple):
    disposition: str
    reason: str
    inspected_lane_id: str | None
    inspected_branch: str | None
    inspected_worktree: str | None
    lane_state: str | None
    commits_ahead: int
    dirty: bool
    snapshot_only: bool
    real_commits: tuple[tuple[str, str], ...] = ()

    @property
    def verify_and_continue(self) -> bool:
        return self.disposition == DISPOSITION_VERIFY_AND_CONTINUE


def _lane_commit_subjects(
    repo: Path, base_sha: str, head_sha: str
) -> list[tuple[str, str]]:
    rc, out, _err = _run_git(
        repo, ["log", "--format=%H%x1f%s", f"{base_sha}..{head_sha}"]
    )
    if rc != 0:
        return []
    commits: list[tuple[str, str]] = []
    for line in out.splitlines():
        if "\x1f" not in line:
            continue
        sha, subject = line.split("\x1f", 1)
        commits.append((sha.strip(), subject.strip()))
    return commits


def classify_recovery_disposition(
    repo: Path, item: dict[str, Any], state: dict[str, Any]
) -> RecoveryDisposition:
    from agent_workflows import worktree_lease

    lane_id, lane_base, _lane_branch = resolve_prior_lane(item)
    if not lane_id:
        return RecoveryDisposition(
            disposition=DISPOSITION_FRESH_EXECUTION,
            reason="no prior lane is recorded for this item; nothing to verify",
            inspected_lane_id=None,
            inspected_branch=None,
            inspected_worktree=None,
            lane_state=None,
            commits_ahead=0,
            dirty=False,
            snapshot_only=False,
        )

    try:
        st = worktree_lease.inspect_lane(repo, lane_id, base_commit=lane_base or "HEAD")
    except Exception as exc:
        return RecoveryDisposition(
            disposition=DISPOSITION_UNDETERMINED,
            reason=f"prior lane {lane_id} could not be inspected: {exc}",
            inspected_lane_id=lane_id,
            inspected_branch=None,
            inspected_worktree=None,
            lane_state=None,
            commits_ahead=0,
            dirty=False,
            snapshot_only=False,
        )

    branch_head = lane_branch_tip(repo, st.branch) if st.branch else None
    if not branch_head:
        return RecoveryDisposition(
            disposition=DISPOSITION_FRESH_EXECUTION,
            reason=f"prior lane {lane_id} exists but has no commit tip",
            inspected_lane_id=lane_id,
            inspected_branch=st.branch,
            inspected_worktree=str(st.path) if st.path else None,
            lane_state=st.state,
            commits_ahead=0,
            dirty=False,
            snapshot_only=False,
        )

    base_sha = lane_base or st.base_commit or "HEAD"
    commits = _lane_commit_subjects(repo, base_sha, branch_head)
    non_snapshot = [
        (sha, subj) for sha, subj in commits if not subj.startswith("wip(snapshot):")
    ]
    snapshot_only = bool(commits) and not non_snapshot
    if non_snapshot:
        return RecoveryDisposition(
            disposition=DISPOSITION_VERIFY_AND_CONTINUE,
            reason=(
                f"prior lane {lane_id} holds {len(non_snapshot)} real commit(s) "
                f"beyond base {base_sha[:8]}"
            ),
            inspected_lane_id=lane_id,
            inspected_branch=st.branch,
            inspected_worktree=str(st.path) if st.path else None,
            lane_state=st.state,
            commits_ahead=len(commits),
            dirty=False,
            snapshot_only=False,
            real_commits=tuple(non_snapshot),
        )

    reason = (
        f"prior lane {lane_id} holds only wip snapshot commit(s); discarding and re-executing"
        if snapshot_only
        else f"prior lane {lane_id} holds no commits beyond base; re-executing fresh"
    )
    return RecoveryDisposition(
        disposition=DISPOSITION_FRESH_EXECUTION,
        reason=reason,
        inspected_lane_id=lane_id,
        inspected_branch=st.branch,
        inspected_worktree=str(st.path) if st.path else None,
        lane_state=st.state,
        commits_ahead=len(commits),
        dirty=False,
        snapshot_only=snapshot_only,
    )


def route_recovery_turn(
    run_dir: Path,
    state: dict[str, Any],
    item: dict[str, Any],
    recovery: bool,
) -> RecoveryDisposition | None:
    if not recovery:
        return None
    repo = Path(state["repo"])
    decision = classify_recovery_disposition(repo, item, state)
    effective = (
        DISPOSITION_FRESH_EXECUTION
        if decision.disposition == DISPOSITION_UNDETERMINED
        else decision.disposition
    )
    record = {
        "disposition": decision.disposition,
        "dispatched_as": effective,
        "reason": decision.reason,
        "inspected_lane_id": decision.inspected_lane_id,
        "inspected_branch": decision.inspected_branch,
        "inspected_worktree": decision.inspected_worktree,
        "lane_state": decision.lane_state,
        "commits_ahead": decision.commits_ahead,
        "dirty": decision.dirty,
        "snapshot_only": decision.snapshot_only,
        "real_commits": [
            {"sha": sha, "subject": subject} for sha, subject in decision.real_commits
        ],
        "at": utc_now(),
    }
    item["recovery_routing"] = record
    save_state(run_dir, state)
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "at": utc_now(),
            "event": "recovery-routed",
            "id6": item.get("id6"),
            **{k: v for k, v in record.items() if k != "at"},
        },
    )
    pal = Palette(should_color(sys.stdout))
    if decision.verify_and_continue:
        print(
            pal(
                f"  \u21ba recovery routed VERIFY-AND-CONTINUE: {decision.reason}",
                "cyan",
            )
        )
    elif decision.disposition == DISPOSITION_UNDETERMINED:
        print(
            pal(
                f"  ! recovery routing undetermined; dispatching a FRESH EXECUTION "
                f"(never a skip): {decision.reason}",
                "yellow",
            ),
            file=sys.stderr,
        )
    return decision


# ---- rununify: sub-helpers formerly in both runners ----------------------------------------------

_compute_scope_reconciliation = compute_scope_reconciliation


def evaluate_clean_base_for_launch(
    repo: Path,
    *,
    shared_tree: bool = False,
) -> Any:
    from agent_workflows import lane_containment

    _rc, out, _err = _run_git(repo, ["status", "--porcelain", "--untracked-files=no"])
    return lane_containment.evaluate_clean_base(out, shared_tree=shared_tree)


def _record_checkpoint_stop(
    run_dir: Path,
    state: dict[str, Any],
    item: dict[str, Any],
    checkpoint_observer: Any,
    *,
    work_dir: str | Path | None = None,
) -> dict[str, Any]:
    from agent_workflows import runner_stop

    effective_dir = (
        work_dir
        or item.get("worktree")
        or (
            item.get("attempts", [{}])[-1].get("worktree")
            if item.get("attempts")
            else None
        )
    )
    repo = Path(effective_dir) if effective_dir else Path(state["repo"])
    try:
        observed_git = git_status(repo)
    except Exception as exc:  # noqa: BLE001
        observed_git = f"<unobserved: {exc}>"
    record = runner_stop.stopped_disposition(
        level=checkpoint_observer.requested_level or runner_stop.LEVEL_NOW,
        requester=checkpoint_observer.requester,
        last_completed_index=checkpoint_observer.last_checkpoint_index,
        last_completed_label=checkpoint_observer.last_checkpoint_label,
        git_state=observed_git,
        events_seen=checkpoint_observer.events_seen,
        at=utc_now(),
    )
    item["stopped"] = record
    append_jsonl(
        run_dir / "events.jsonl",
        runner_stop.stopped_stop_event(record, id6=item.get("id6", ""), at=utc_now()),
    )
    return record


def _record_forced_stop(
    run_dir: Path,
    state: dict[str, Any],
    item: dict[str, Any],
    stop: Any,
    *,
    work_dir: str | Path | None = None,
) -> dict[str, Any]:
    from agent_workflows import runner_stop

    effective_dir = (
        work_dir
        or item.get("worktree")
        or (
            item.get("attempts", [{}])[-1].get("worktree")
            if item.get("attempts")
            else None
        )
    )
    repo = Path(effective_dir) if effective_dir else Path(state["repo"])
    try:
        observed_git = git_status(repo)
    except Exception as exc:  # noqa: BLE001
        observed_git = f"<unobserved: {exc}>"
    record = runner_stop.forced_disposition(
        level=stop.level,
        requester=stop.requester,
        git_state=observed_git,
        events_seen=stop.events_seen,
        prior_completed_index=stop.prior_completed_index,
        prior_completed_label=stop.prior_completed_label,
        at=utc_now(),
    )
    item["stopped"] = record
    append_jsonl(
        run_dir / "events.jsonl",
        runner_stop.forced_stop_event(record, id6=item.get("id6", ""), at=utc_now()),
    )
    return record


def reconcile_disposition(
    repo: Path,
    item: dict[str, Any],
    run_dir: Path,
    exit_code: int,
    plan_repo: Path | None = None,
) -> tuple[str, dict[str, Any] | None]:
    from agent_workflows import runner_stop
    from agent_workflows.selectors import read_front_matter_status as _read_status

    stopped = item.get("stopped")
    if isinstance(stopped, dict) and stopped.get("stopped_deliberately"):
        return runner_stop.STOPPED_DISPOSITION, None
    if item.get("action") == "review":
        source = plan_repo or repo
        try:
            current_plan = resolve_plan_path(
                source, item.get("configured_file", ""), item["id6"]
            )
            text = current_plan.read_text(encoding="utf-8")
            status = _read_status(text)
        except Exception:
            status = None
        if exit_code == 0:
            if status in ("reviewed", "approved"):
                return status, None
            return "reviewed", None
        return "failed-safely", None

    outcome_path = run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
    outcome: dict[str, Any] | None = None
    if outcome_path.exists():
        try:
            outcome = load_json(outcome_path)
        except DriverError:
            outcome = None
    try:
        current_plan = resolve_plan_path(
            repo, item.get("configured_file", ""), item["id6"]
        )
        bucket = plan_bucket(current_plan)
    except DriverError:
        bucket = None
    if bucket == "executed":
        return "executed", outcome
    if outcome:
        disposition = outcome.get("disposition")
        if disposition == "executed":
            return "substantially-complete", outcome
        if disposition in TERMINAL_STATES - {"dependency-blocked", "not-attempted"}:
            return disposition, outcome
    if item.get("status") == INTEGRATION_DEFERRED_STATUS:
        return INTEGRATION_DEFERRED_STATUS, outcome
    return ("partial" if exit_code == 0 else "failed-safely"), outcome


def record_item_spec_edits(
    repo: Path,
    plan_path: Path,
    item: MutableMapping[str, Any],
    *,
    reconcile: Callable[[Path, Path], tuple[Mapping[str, str], Mapping[str, str]]],
) -> dict[str, Any]:
    reasons: Mapping[str, str] = {}
    acks: Mapping[str, str] = {}
    refused = False
    try:
        reasons, acks = reconcile(repo, plan_path)
    except Exception:
        refused = True
    else:
        if not reasons and not acks:
            try:
                from agent_workflows import ipd_lifecycle

                rc, _msg, _ev, _find = ipd_lifecycle.finalize_precheck(repo, plan_path)
                if rc != 0:
                    refused = True
            except Exception:
                refused = True
    record: dict[str, Any] = {
        "reconciled": not refused,
        "reasons": dict(reasons),
        "acks": dict(acks),
        "refused": refused,
    }
    item["spec_edits_reconciliation"] = record
    return record


# ---- rununify: execute_item_core -----------------------------------------------------------------


def execute_item_core(
    run_dir: Path,
    state: dict[str, Any],
    item: dict[str, Any],
    recovery: bool,
    *,
    host_labels: HostLabels,
    spawn_executor: Callable[..., tuple[int, str | None, Path, list[str]]],
    spawn_verifier: Callable[..., tuple[int, str | None, Path, list[str]]],
    raw_launcher: Callable[..., Any],
    run_suite_check: Callable[[Path, str], Any],
    process_backlog_close: Callable[..., Any],
    driver_module: Any = None,
    tracker: StreamTracker | None = None,
) -> None:
    """Unified execution loop for one plan item, driving all 16 safety gates identically on both hosts."""
    from agent_workflows import lane_containment, runner_stop, worktree_lease
    from agent_workflows.plan_readiness import is_plan_review_approved

    write_report = getattr(
        driver_module,
        "write_report",
        lambda rd, st: globals()["write_report"](rd, st, labels=host_labels),
    )
    save_state = getattr(
        driver_module,
        "save_state",
        lambda r, s: globals()["save_state"](r, s, write_report=write_report),
    )
    integration_is_earned = getattr(driver_module, "integration_is_earned", None)

    driver_begin = getattr(driver_module, "driver_begin", globals().get("driver_begin"))
    driver_finalize = getattr(driver_module, "driver_finalize", None)
    assert_child_tool_identity = getattr(
        driver_module,
        "assert_child_tool_identity",
        globals().get("assert_child_tool_identity"),
    )
    allocate_isolation_worktree = getattr(
        driver_module,
        "allocate_isolation_worktree",
        globals().get("allocate_isolation_worktree"),
    )
    clean_base_launch_decision = getattr(
        driver_module,
        "clean_base_launch_decision",
        globals().get("clean_base_launch_decision"),
    )
    evaluate_clean_base_for_launch = getattr(
        driver_module,
        "evaluate_clean_base_for_launch",
        globals().get("evaluate_clean_base_for_launch"),
    )
    reconcile_disposition = getattr(
        driver_module, "reconcile_disposition", globals().get("reconcile_disposition")
    )
    integrate_lane_branch = getattr(
        driver_module, "integrate_lane_branch", globals().get("integrate_lane_branch")
    )
    integrate_review_lane_branch = getattr(
        driver_module,
        "integrate_review_lane_branch",
        globals().get("integrate_review_lane_branch"),
    )
    acquire_review_sweep_lane = getattr(
        driver_module,
        "acquire_review_sweep_lane",
        globals().get("acquire_review_sweep_lane"),
    )
    route_recovery_turn = getattr(
        driver_module, "route_recovery_turn", globals().get("route_recovery_turn")
    )
    make_integration_validation_runner = getattr(
        driver_module,
        "make_integration_validation_runner",
        globals().get("make_integration_validation_runner"),
    )
    set_plan_approved = getattr(driver_module, "set_plan_approved", None)
    is_plan_review_approved = getattr(
        driver_module, "is_plan_review_approved", is_plan_review_approved
    )
    git_head = getattr(driver_module, "git_head", globals().get("git_head"))
    git_status = getattr(driver_module, "git_status", globals().get("git_status"))
    run_suite_check = getattr(driver_module, "run_suite_check", run_suite_check)
    process_backlog_close = getattr(
        driver_module, "process_backlog_close", process_backlog_close
    )

    repo = Path(state["repo"])
    pal = Palette(should_color(sys.stdout))
    plan_path = resolve_plan_path(repo, item.get("configured_file", ""), item["id6"])
    attempt_no = len(item.get("attempts", [])) + 1
    action = item.get("action", "execute")
    is_review = action == "review"

    routing = None if is_review else route_recovery_turn(run_dir, state, item, recovery)
    if is_review:
        prompt_text = build_review_prompt(item, state, run_dir, plan_path, repo)
    else:
        prompt_text = build_prompt(
            item,
            state,
            run_dir,
            plan_path,
            recovery=recovery,
            routing=routing,
            labels=host_labels,
        )

    prompt_path = write_prompt(run_dir, item, prompt_text, attempt_no)

    max_items = state.get("options", {}).get("max_items_per_session", 4)
    review_uses_sweep_session = is_review and bool(
        state.get("options", {}).get("isolate_worktree", True)
    )
    raw_session = (
        state.get(REVIEW_SWEEP_SESSION_KEY) or state.get("options", {}).get("session")
        if review_uses_sweep_session
        else (
            state.get("session_id")
            or state.get("set_sessions", {}).get(item["setid"])
            or state.get("options", {}).get("session")
        )
    )
    is_rotation = False
    if raw_session and max_items and max_items > 0:
        session_turns = state.get("session_turn_counts", {}).get(raw_session, 0)
        if session_turns >= max_items:
            is_rotation = True
            raw_session = None

    session_id = raw_session
    use_continue = (
        False
        if (state.get("options", {}).get("new_session") or is_rotation)
        else (session_id is None)
    )

    attempt: dict[str, Any] = {
        "number": attempt_no,
        "started_at": utc_now(),
        "starting_head": git_head(repo),
        "starting_branch": git_branch(repo),
        "starting_status": git_status(repo),
        "prompt": str(prompt_path),
        "prompt_sha256": sha256_file(prompt_path),
        "session_id": None,
        "log": str(attempt_log_path(run_dir, item, attempt_no)),
        "recovery": recovery,
        "action": action,
    }
    item.setdefault("attempts", []).append(attempt)
    item["status"] = "running"
    save_state(run_dir, state)
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "at": utc_now(),
            "event": "ipd-started",
            "id6": item["id6"],
            "action": action,
            "attempt": attempt_no,
        },
    )

    total = len(state["queue"])
    mode_note = " (recovery)" if recovery else ""
    action_str = f"action={action}"
    seq = execution_index(item, state)
    banner = (
        pal("\u25b6 ", "cyan")
        + pal(f"IPD {seq:02d}/{total} {item['id6']}", "bold", "cyan")
        + pal(
            f"  set={item['setid']}  {action_str}  attempt {attempt_no}{mode_note}",
            "dim",
        )
    )
    print(banner)
    print(pal(f"  plan: {plan_path}", "dim"))

    self_finalize = state.get("options", {}).get("self_finalize", True)
    isolate = state.get("options", {}).get("isolate_worktree", True)
    wt_handle = None
    work_dir: str | None = None

    if self_finalize and not is_review:
        base = evaluate_clean_base_for_launch(repo, shared_tree=not isolate)
        decision = clean_base_launch_decision(
            base,
            allow_dirty_base=bool(
                state.get("options", {}).get("allow_dirty_base", False)
            ),
        )
        if decision.warned:
            attempt["clean_base_warning"] = decision.reason
            attempt["clean_base_dirty_paths"] = list(decision.dirty_paths)
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "clean-base-warning",
                    "id6": item["id6"],
                    "dirty_paths": list(decision.dirty_paths),
                    "detail": decision.reason,
                },
            )
        elif decision.consented:
            attempt["clean_base_consented"] = decision.reason
            attempt["clean_base_dirty_paths"] = list(decision.dirty_paths)
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "clean-base-consented",
                    "id6": item["id6"],
                    "dirty_paths": list(decision.dirty_paths),
                    "detail": decision.reason,
                },
            )
            print(pal(f"  {decision.reason}", "yellow"), file=sys.stderr)
        elif decision.refused:
            attempt["ended_at"] = utc_now()
            attempt["clean_base_refused"] = decision.reason
            attempt["clean_base_dirty_paths"] = list(decision.dirty_paths)
            attempt["disposition"] = "blocked"
            item["status"] = "blocked"
            item["clean_base_refusal"] = decision.reason
            save_state(run_dir, state)
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "clean-base-refused",
                    "id6": item["id6"],
                    "dirty_paths": list(decision.dirty_paths),
                    "detail": decision.reason,
                },
            )
            print(
                pal(
                    f"\u2717 IPD {seq:02d}/{total} {item['id6']} refused: {decision.reason}",
                    "red",
                ),
                file=sys.stderr,
            )
            return

    sweep_refresh = None
    if is_review and isolate:
        try:
            wt_handle, sweep_refresh = acquire_review_sweep_lane(
                repo, run_dir, state, save_state=save_state
            )
            work_dir = str(wt_handle.path)
            attempt["worktree"] = work_dir
            attempt["worktree_branch"] = wt_handle.branch
            attempt["worktree_lane_id"] = wt_handle.lane_id
            attempt["worktree_base"] = wt_handle.base_commit
            attempt["worktree_disposition"] = getattr(
                wt_handle, "disposition", "created"
            )
            attempt["review_sweep_lane"] = True
            attempt["review_lane_tip_before"] = lane_branch_tip(repo, wt_handle)
            if sweep_refresh is not None:
                attempt["review_sweep_lane_refreshed"] = sweep_refresh.refreshed
                attempt["review_sweep_lane_refresh_reason"] = sweep_refresh.reason
            save_state(run_dir, state)
            print(
                pal(
                    f"  \u2713 review sweep lane {wt_handle.branch} at {work_dir}"
                    + (
                        ""
                        if sweep_refresh is None
                        else (
                            " (refreshed to main)"
                            if sweep_refresh.refreshed
                            else f" ({sweep_refresh.reason})"
                        )
                    ),
                    "cyan",
                )
            )
        except Exception as exc:
            attempt["ended_at"] = utc_now()
            attempt["disposition"] = "blocked"
            item["status"] = "blocked"
            item["worktree_error"] = str(exc)
            save_state(run_dir, state)
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "review-sweep-lane-alloc-failed",
                    "id6": item["id6"],
                    "detail": str(exc),
                },
            )
            print(
                pal(
                    f"\u2717 IPD {seq:02d}/{total} {item['id6']} review sweep lane "
                    f"allocation failed; not launching. {exc}",
                    "red",
                ),
                file=sys.stderr,
            )
            return

    if self_finalize and not is_review:
        actor = driver_actor(state, labels=host_labels)
        assert_child_tool_identity(run_dir / "events.jsonl", cwd=repo)
        if isolate:
            begin_rc, begin_msg = driver_begin(repo, item["id6"], actor, isolated=True)
        else:
            begin_rc, begin_msg = driver_begin(repo, item["id6"], actor)
        if begin_rc != 0:
            attempt["ended_at"] = utc_now()
            attempt["begin_refused"] = begin_msg
            attempt["disposition"] = "blocked"
            item["status"] = "blocked"
            item["begin_refusal"] = begin_msg
            save_state(run_dir, state)
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "ipd-begin-refused",
                    "id6": item["id6"],
                    "exit_code": begin_rc,
                    "detail": begin_msg,
                },
            )
            print(
                pal(
                    f"\u2717 IPD {seq:02d}/{total} {item['id6']} begin refused "
                    f"(no execution authority); not launching. {begin_msg}",
                    "red",
                ),
                file=sys.stderr,
            )
            return
        if isolate:
            try:
                wt_handle = allocate_isolation_worktree(repo, item["id6"])
                work_dir = str(wt_handle.path)
                # lanesess (xd9sll): this turn now runs in its OWN tree, so it must NOT inherit a
                # session bound to a DIFFERENT tree. Sessions were keyed per SET while worktrees are
                # per ITEM, so lanes 2..N inherited lane 1's conversation and, with it, lane 1's
                # directory, silently executing in the wrong worktree. Drop the inherited session and
                # do NOT fall back to `--continue` (which resumes the previous conversation and would
                # reintroduce the same carryover). Kept symmetric with oc_runipd.run_opencode; a
                # one-driver-only fix is asserted against in tests.
                session_id = None
                use_continue = False
                attempt["worktree"] = work_dir
                attempt["worktree_branch"] = wt_handle.branch
                attempt["worktree_lane_id"] = wt_handle.lane_id
                attempt["worktree_base"] = wt_handle.base_commit
                attempt["worktree_disposition"] = getattr(
                    wt_handle, "disposition", "created"
                )
                attempt["worktree_displaced_from"] = getattr(
                    wt_handle, "displaced_from", None
                )
                save_state(run_dir, state)
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "worktree-allocated",
                        "id6": item["id6"],
                        "worktree": work_dir,
                        "branch": wt_handle.branch,
                        "lane_id": wt_handle.lane_id,
                        "base_commit": wt_handle.base_commit,
                        "disposition": getattr(wt_handle, "disposition", "created"),
                        "displaced_from": getattr(wt_handle, "displaced_from", None),
                    },
                )
                disp = getattr(wt_handle, "disposition", "created")
                suffix = "" if disp == "created" else f" ({disp})"
                print(
                    pal(
                        f"  \u2713 isolated worktree {wt_handle.branch} at {work_dir}{suffix}",
                        "cyan",
                    )
                )
            except Exception as exc:
                attempt["ended_at"] = utc_now()
                attempt["disposition"] = "blocked"
                item["status"] = "blocked"
                item["worktree_error"] = str(exc)
                save_state(run_dir, state)
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "worktree-alloc-failed",
                        "id6": item["id6"],
                        "detail": str(exc),
                    },
                )
                print(
                    pal(
                        f"\u2717 IPD {seq:02d}/{total} {item['id6']} worktree "
                        f"allocation failed; not launching. {exc}",
                        "red",
                    ),
                    file=sys.stderr,
                )
                return

    if work_dir and not is_review:
        lane_root = Path(work_dir)
        try:
            lane_plan_path = resolve_plan_path(
                lane_root, item.get("configured_file", ""), item["id6"]
            )
        except DriverError:
            lane_plan_path = plan_path
        prompt_text = build_prompt(
            item,
            state,
            run_dir,
            lane_plan_path,
            recovery=recovery,
            lane_root=lane_root,
            routing=routing,
            labels=host_labels,
        )
        prompt_path = write_prompt(run_dir, item, prompt_text, attempt_no)
        attempt["prompt"] = str(prompt_path)
        attempt["prompt_sha256"] = sha256_file(prompt_path)
        attempt["lane_plan_path"] = str(lane_plan_path)
        lane_manifest = lane_containment.materialize_lane_inputs(
            lane_root=lane_root,
            plan_path=lane_plan_path,
            runbook_path=(
                Path(state["runbook"])
                if state.get("runbook") and Path(state["runbook"]).exists()
                else None
            ),
            repo=lane_root,
        )
        attempt["lane_input_manifest"] = str(lane_manifest.manifest_path)
        attempt["lane_input_revision"] = lane_manifest.revision
        runbook_entry = lane_manifest.entry(lane_containment.INPUT_CLASS_RUNBOOK)
        if runbook_entry is not None:
            attempt["lane_runbook_path"] = str(lane_root / runbook_entry.path)
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "lane-inputs-materialized",
                "id6": item["id6"],
                "revision": lane_manifest.revision,
                "manifest": str(lane_manifest.manifest_path),
                "inputs": [entry.path for entry in lane_manifest.entries],
            },
        )
        save_state(run_dir, state)
    if work_dir and is_review:
        lane_root = Path(work_dir)
        try:
            lane_plan_path = resolve_plan_path(
                lane_root, item.get("configured_file", ""), item["id6"]
            )
        except DriverError:
            lane_plan_path = plan_path
        prompt_text = build_review_prompt(
            item, state, run_dir, lane_plan_path, repo, lane_root=lane_root
        )
        prompt_path = write_prompt(run_dir, item, prompt_text, attempt_no)
        attempt["prompt"] = str(prompt_path)
        attempt["prompt_sha256"] = sha256_file(prompt_path)
        attempt["lane_plan_path"] = str(lane_plan_path)
        lane_manifest = lane_containment.materialize_lane_inputs(
            lane_root=lane_root,
            plan_path=lane_plan_path,
            runbook_path=None,
            repo=lane_root,
            revision=int(item["position"]),
        )
        attempt["lane_input_manifest"] = str(lane_manifest.manifest_path)
        attempt["lane_input_revision"] = lane_manifest.revision
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "lane-inputs-materialized",
                "id6": item["id6"],
                "revision": lane_manifest.revision,
                "manifest": str(lane_manifest.manifest_path),
                "inputs": [entry.path for entry in lane_manifest.entries],
            },
        )
        save_state(run_dir, state)

    try:
        exit_code, session_id, log_path, argv = spawn_executor(
            prompt_path,
            work_dir,
            tracker,
            plan_path,
            attempt_no,
            session_id,
            use_continue,
        )
    except runner_stop.StopNowForce as stop:
        now = utc_now()
        record = _record_forced_stop(run_dir, state, item, stop, work_dir=work_dir)
        attempt["interrupted_at"] = now
        attempt["ended_at"] = now
        attempt["interrupt_reason"] = "deliberate-stop-now-force"
        attempt["exit_code"] = stop.exit_code
        attempt["stopped"] = record
        attempt["disposition"] = runner_stop.FORCED_DISPOSITION
        item["status"] = runner_stop.FORCED_DISPOSITION
        save_state(run_dir, state)
        print(
            pal(
                f"  \u25cf IPD {item['id6']} interrupted by deliberate force stop",
                "yellow",
            ),
            file=sys.stderr,
        )
        return
    except runner_stop.StopAtCheckpoint as stop:
        now = utc_now()
        record = _record_checkpoint_stop(
            run_dir, state, item, stop.observer, work_dir=work_dir
        )
        attempt["interrupted_at"] = now
        attempt["ended_at"] = now
        attempt["interrupt_reason"] = "deliberate-stop-at-checkpoint"
        attempt["exit_code"] = stop.exit_code
        attempt["stopped"] = record
        attempt["disposition"] = runner_stop.STOPPED_DISPOSITION
        item["status"] = runner_stop.STOPPED_DISPOSITION
        save_state(run_dir, state)
        print(
            pal(
                f"  \u25cf IPD {item['id6']} stopped cleanly at checkpoint: "
                f"{stop.observer.last_checkpoint_label}",
                "yellow",
            ),
            file=sys.stderr,
        )
        return
    except StallTimeout:
        from agent_workflows import lane_containment, worktree_lease

        now = utc_now()
        attempt["interrupted_at"] = now
        attempt["ended_at"] = now
        attempt["interrupt_reason"] = "stall_timeout"
        stall_sec = state.get("options", {}).get("stall_timeout", DEFAULT_STALL_TIMEOUT)
        attempt["stall_timeout"] = stall_sec
        item["status"] = "interrupted"
        if wt_handle is not None:
            try:
                worktree_lease.snapshot_lane_dirty_work(
                    repo, wt_handle, note="Reason: stall_timeout."
                )
            except Exception:
                pass
            lane_containment.record_lane_preserved(
                run_dir=run_dir,
                item=item,
                handle=wt_handle,
                reason="turn stalled; lane preserved for recovery",
                reason_codes=("stall-timeout",),
            )
        save_state(run_dir, state)
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": now,
                "event": "ipd-stalled",
                "id6": item["id6"],
                "stall_timeout": stall_sec,
                "attempt": attempt_no,
            },
        )
        print(
            pal(
                f"\u2717 IPD {seq:02d}/{total} {item['id6']} stalled (no output for {int(stall_sec) if stall_sec else 0}s); turn terminated",
                "red",
            ),
            file=sys.stderr,
        )
        return

    if session_id:
        attempt["session_id"] = session_id
        if turn_runs_in_review_sweep_lane(state, work_dir):
            counts = state.setdefault("session_turn_counts", {})
            existing_sweep = state.get(REVIEW_SWEEP_SESSION_KEY)
            existing_turns = counts.get(existing_sweep, 0) if existing_sweep else 0
            sweep_rotation = bool(
                max_items and max_items > 0 and existing_turns >= max_items
            )
            if existing_sweep and existing_sweep != session_id and not sweep_rotation:
                raise DriverError(
                    f"Review sweep changed session unexpectedly: {existing_sweep} -> {session_id}"
                )
            state[REVIEW_SWEEP_SESSION_KEY] = session_id
            counts[session_id] = counts.get(session_id, 0) + 1
        if not work_dir:
            counts = state.setdefault("session_turn_counts", {})
            existing = state.setdefault("set_sessions", {}).get(item["setid"])
            existing_turns = counts.get(existing, 0) if existing else 0
            is_planned_rotation = bool(
                max_items and max_items > 0 and existing_turns >= max_items
            )
            if existing and existing != session_id and not is_planned_rotation:
                raise DriverError(
                    f"Set {item['setid']} changed session unexpectedly: {existing} -> {session_id}"
                )
            state["set_sessions"][item["setid"]] = session_id
            state["session_id"] = session_id
            counts[session_id] = counts.get(session_id, 0) + 1

    attempt.update(
        {
            "ended_at": utc_now(),
            "exit_code": exit_code,
            "ending_head": git_head(repo),
            "ending_branch": git_branch(repo),
            "ending_status": git_status(repo),
            "log": str(log_path),
            "argv": argv,
        }
    )
    from agent_workflows.run_viewer import extract_log_metrics

    att_cost, att_toks = extract_log_metrics(log_path)
    if att_cost is not None:
        attempt["cost"] = att_cost
    if att_toks:
        attempt["tokens"] = att_toks

    if work_dir and (not is_review or turn_runs_in_review_sweep_lane(state, work_dir)):
        try:
            collection = lane_containment.collect_lane_submissions(
                run_dir=run_dir,
                item=item,
                run_id=state["run_id"],
                lane_root=Path(work_dir),
                plan_path=plan_path,
                attempt=attempt_no,
            )
        except (
            Exception
        ) as exc:  # pragma: no cover - defensive; collection must never kill a turn
            collection = None
            attempt["collection_error"] = f"{type(exc).__name__}: {exc}"
        if collection is not None:
            attempt["collection"] = {
                "status": collection.get("status"),
                "collected": collection.get("collected"),
                "failed": collection.get("failed"),
                "receipt": str(
                    lane_containment.collection_receipt_path(run_dir, item, attempt_no)
                ),
            }
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "lane-submissions-collected",
                    "id6": item["id6"],
                    "attempt": attempt_no,
                    "collected": collection.get("collected"),
                    "failed": collection.get("failed"),
                },
            )

    disposition, outcome = reconcile_disposition(
        repo,
        item,
        run_dir,
        exit_code,
        plan_repo=Path(work_dir) if work_dir else None,
    )

    verify_disp = None
    opts = state.get("options", {})
    validate = opts.get("validate", False)
    if "validate" not in opts:
        validate = not (opts.get("no_verify") or opts.get("no_audit"))
    if (
        not is_review
        and disposition in ("executed", "substantially-complete")
        and validate
    ):
        plan_repo = Path(work_dir) if work_dir else repo
        try:
            current_plan_path = resolve_plan_path(
                plan_repo, item.get("configured_file", ""), item["id6"]
            )
        except DriverError:
            current_plan_path = plan_path
        v_prompt = build_verifier_prompt(
            item, state, run_dir, current_plan_path, labels=host_labels
        )
        v_prompt_file = write_prompt(
            run_dir, item, v_prompt, attempt_no, suffix="verify"
        )
        print(
            pal(
                f"  \u25b6 Verifying {item['id6']} ({current_plan_path})...",
                "cyan",
            ),
            flush=True,
        )
        try:
            v_rc, _v_session, _v_log, _v_argv = spawn_verifier(
                v_prompt_file,
                current_plan_path,
                work_dir,
                tracker,
                attempt_no,
            )
            if _v_log:
                attempt["verify_log"] = str(_v_log)
                v_cost, v_toks = extract_log_metrics(_v_log)
                if v_cost is not None:
                    attempt["verify_cost"] = v_cost
                if v_toks:
                    attempt["verify_tokens"] = v_toks
            v_outcome_file = (
                run_dir
                / "outcomes"
                / f"{item['position']:02d}-{item['id6']}-verification.json"
            )
            if v_outcome_file.is_file():
                try:
                    v_data = json.loads(v_outcome_file.read_text(encoding="utf-8"))
                    verify_verdict = str(v_data.get("verdict", "")).strip().upper()
                    if (
                        "BLOCKED" in verify_verdict
                        or "NOT CONFORMING" in verify_verdict
                    ):
                        verify_disp = "blocked"
                        disposition = "partial"
                    elif verify_verdict == "VERIFIED":
                        verify_disp = "verified"
                    else:
                        verify_disp = "unverified"
                        disposition = "partial"
                except Exception:
                    verify_disp = "unverified"
                    disposition = "partial"
            else:
                verify_disp = "unverified"
                disposition = "partial"
        except runner_stop.StopNowForce as stop:
            now = utc_now()
            attempt["interrupted_at"] = now
            attempt["ended_at"] = now
            attempt["interrupt_reason"] = "deliberate-stop-now-force"
            record = _record_forced_stop(run_dir, state, item, stop, work_dir=work_dir)
            attempt["stopped"] = record
            attempt["disposition"] = runner_stop.FORCED_DISPOSITION
            item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)
            raise
        except runner_stop.StopAtCheckpoint as stop:
            now = utc_now()
            attempt["interrupted_at"] = now
            attempt["ended_at"] = now
            attempt["interrupt_reason"] = "deliberate-stop-at-checkpoint"
            record = _record_checkpoint_stop(
                run_dir, state, item, stop.observer, work_dir=work_dir
            )
            attempt["stopped"] = record
            attempt["disposition"] = runner_stop.STOPPED_DISPOSITION
            item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)
            raise
        except StallTimeout:
            verify_disp = "unverified"
            disposition = "partial"

    attempt["disposition"] = disposition
    attempt["verification"] = verify_disp
    attempt["verification_status"] = verify_disp
    item["status"] = disposition
    item["last_outcome"] = outcome
    item["verification_status"] = verify_disp

    if not is_review:
        defect_verdict = validate_defect_report(outcome)
        reask_session = attempt.get("session_id")
        warranted, reask_reason = defect_reask_is_warranted(
            defect_verdict,
            disposition=disposition,
            session_id=reask_session,
            already_reasked=bool(attempt.get("defect_reasked")),
        )
        reask_verdict = None
        if warranted:
            reask_prompt = write_prompt(
                run_dir,
                item,
                defect_reask_message(defect_verdict),
                attempt_no,
                suffix="defect-reask",
            )
            attempt["defect_reask_prompt"] = str(reask_prompt)
            attempt["defect_reasked"] = True
            try:
                reask_verdict, reask_rc = perform_defect_reask(
                    verdict=defect_verdict,
                    prompt_path=reask_prompt,
                    outcome_path=run_dir
                    / "outcomes"
                    / f"{item['position']:02d}-{item['id6']}.json",
                    resume=(
                        (
                            lambda reask_prompt_path: resume_via_launcher(
                                raw_launcher,
                                (
                                    state,
                                    run_dir,
                                    item,
                                    plan_path,
                                    reask_prompt_path,
                                    attempt_no,
                                ),
                                {
                                    "log_suffix": "defect-reask",
                                    "label_suffix": "defect-reask",
                                    "tracker": tracker,
                                    "work_dir": work_dir,
                                    "resume_session": reask_session,
                                },
                            )
                        )
                        if host_labels == OC_HOST_LABELS
                        else (
                            lambda reask_prompt_path: resume_via_launcher(
                                raw_launcher,
                                (
                                    state,
                                    run_dir,
                                    item,
                                    reask_prompt_path,
                                    attempt_no,
                                ),
                                {
                                    "session_id": reask_session,
                                    "use_continue": False,
                                    "log_suffix": "defect-reask",
                                    "label_suffix": "defect-reask",
                                    "work_dir": work_dir,
                                    "tracker": tracker,
                                },
                            )
                        )
                    ),
                    recollect=(
                        functools.partial(
                            lane_containment.collect_lane_submissions,
                            run_dir=run_dir,
                            item=item,
                            run_id=state["run_id"],
                            lane_root=Path(work_dir),
                            plan_path=plan_path,
                            attempt=attempt_no,
                        )
                        if work_dir
                        else None
                    ),
                    session_turn_counts=(
                        None
                        if work_dir
                        else state.setdefault("session_turn_counts", {})
                    ),
                    session_id=reask_session,
                )
                attempt["defect_reask_exit_code"] = reask_rc
            except (KeyboardInterrupt, StallTimeout):
                reask_verdict = None
        record = defect_report_record(
            defect_verdict,
            reasked=warranted,
            reask_reason=reask_reason,
            reask_verdict=reask_verdict,
        )
        attempt["defect_report"] = record
        item["defect_report"] = record
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "defect-report-recorded",
                "id6": item["id6"],
                "disposition": disposition,
                "reasked": warranted,
                "reask_reason": reask_reason,
                "verdict": record["verdict"],
                "state": record["state"],
                "coerced": record["coerced"],
                "findings_count": len(record["findings"]),
            },
        )

    suite_result: Any = None
    integration_gate_relevant = (
        self_finalize
        and not is_review
        and disposition in ("executed", "substantially-complete")
    )
    if integration_gate_relevant and not validate:
        suite_result = run_suite_check(repo, str(state.get("run_id") or ""))
        attempt["suite_check"] = {
            "passing": suite_result.passing,
            "exit_code": suite_result.exit_code,
            "summary": suite_result.summary,
            "cwd": suite_result.cwd,
            "timeout_seconds": suite_result.timeout_seconds,
            "elapsed_seconds": round(suite_result.elapsed_seconds, 3),
        }
    integration = integration_is_earned(
        validate=validate, verify_disp=verify_disp, suite_result=suite_result
    )
    if integration_gate_relevant:
        attempt["integration_signal"] = integration.signal
        attempt["integration_detail"] = integration.detail
        item["integration_signal"] = integration.signal
        item["verifier_ran"] = bool(validate)
    save_state(run_dir, state)

    if is_review and wt_handle is not None:
        review_commit, review_committed_paths = commit_review_lane_output(
            repo, wt_handle, item["id6"], host_label=host_labels.command
        )
        if review_commit:
            attempt["review_lane_commit"] = review_commit
            attempt["review_lane_committed_paths"] = list(review_committed_paths)
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "review-lane-output-committed",
                    "id6": item["id6"],
                    "attempt": attempt_no,
                    "commit": review_commit,
                    "paths": list(review_committed_paths),
                },
            )
        elif review_committed_paths:
            attempt["review_lane_commit_refused"] = list(review_committed_paths)
        review_scope = None
        try:
            lane_changed = review_turn_changed_files(
                repo, wt_handle, since_commit=attempt.get("review_lane_tip_before")
            )
        except (
            Exception
        ) as exc:  # pragma: no cover - defensive; never kill a turn over reporting
            lane_changed = ()
            attempt["review_scope_error"] = f"{type(exc).__name__}: {exc}"
        if lane_changed:
            review_scope = classify_review_writes(
                lane_changed,
                id6=item["id6"],
                queued_id6s=[
                    entry.get("id6", "")
                    for entry in state.get("queue", [])
                    if entry.get("status") == "queued"
                ],
            )
            attempt["review_write_scope"] = {
                "changed": list(review_scope.changed),
                "allowed": list(review_scope.allowed),
                "out_of_scope": list(review_scope.out_of_scope),
                "queued_siblings": list(review_scope.queued_siblings),
            }
            item["review_write_scope"] = attempt["review_write_scope"]
            if not review_scope.clean:
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "review-wrote-out-of-scope-paths",
                        "id6": item["id6"],
                        "out_of_scope": list(review_scope.out_of_scope),
                        "queued_siblings": list(review_scope.queued_siblings),
                        "detail": describe_review_write_scope(
                            review_scope, id6=item["id6"]
                        ),
                    },
                )
                print(
                    pal(
                        "  ! "
                        + describe_review_write_scope(review_scope, id6=item["id6"]),
                        "yellow",
                    ),
                    file=sys.stderr,
                )
            save_state(run_dir, state)

        review_integrated, review_reason, review_kind = integrate_review_lane_branch(
            repo, wt_handle, item["id6"]
        )
        attempt["review_integrated"] = review_integrated
        attempt["review_integration_reason"] = review_reason
        attempt["review_integration_kind"] = review_kind
        item["review_integrated"] = review_integrated
        save_state(run_dir, state)
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": (
                    "review-lane-integrated"
                    if review_integrated
                    else "review-lane-not-integrated"
                ),
                "id6": item["id6"],
                "branch": wt_handle.branch,
                "kind": review_kind,
                "detail": review_reason,
            },
        )
        if not review_integrated:
            item["review_integration_refusal"] = review_reason
            save_state(run_dir, state)
            print(
                pal(
                    f"  ! review {item['id6']} was NOT integrated to main ({review_kind}): "
                    f"{review_reason}. Its work is preserved on {wt_handle.branch}.",
                    "yellow",
                ),
                file=sys.stderr,
            )
        else:
            print(
                pal(
                    f"  \u2713 review {item['id6']} integrated to main ({review_reason})",
                    "cyan",
                )
            )

    if not is_review and disposition in ("executed", "substantially-complete"):
        if self_finalize and work_dir and wt_handle is not None and integration.earned:
            finalize_repo = Path(work_dir)
            try:
                current_plan_for_finalize = resolve_plan_path(
                    finalize_repo, item.get("configured_file", ""), item["id6"]
                )
            except DriverError:
                current_plan_for_finalize = plan_path
            actor = driver_actor(state, labels=host_labels)
            fin_message = (
                f"{host_labels.command} self-finalize: {item['id6']} verified "
                f"(set {item['setid']}, attempt {attempt_no})."
            )
            record_item_spec_edits(
                finalize_repo,
                current_plan_for_finalize,
                item,
                reconcile=lambda r, p: compute_scope_reconciliation(
                    r, p, labels=host_labels
                ),
            )
            sync_receipt_into_worktree(repo, finalize_repo, item["id6"])
            fin_rc, fin_msg = driver_finalize(
                finalize_repo,
                current_plan_for_finalize,
                item["id6"],
                actor,
                fin_message,
            )
            if fin_rc == 0:
                process_backlog_close(
                    run_dir,
                    state,
                    item,
                    lane_handle=wt_handle,
                    lane_repo=Path(work_dir),
                )
                val_runner = make_integration_validation_runner(state, run_dir, item)
                try:
                    integrated, integ_reason, integ_kind = integrate_lane_branch(
                        repo, wt_handle, item["id6"], val_runner
                    )
                except TypeError:
                    integrated, integ_reason, integ_kind = integrate_lane_branch(
                        repo,
                        wt_handle,
                        item["id6"],
                        val_runner,
                        host_label=host_labels.command,
                        run_checked=globals()["run_checked"],
                        action_kind="execute",
                    )
                if not integrated:
                    with contextlib.suppress(Exception):
                        item["integration_changed_files"] = list(
                            build_lane_outcome(
                                repo, wt_handle, item["id6"]
                            ).changed_files
                        )
                    decision = record_integration_refusal(
                        run_dir=run_dir,
                        state=state,
                        item=item,
                        attempt=attempt,
                        integ_kind=integ_kind,
                        integ_reason=integ_reason,
                        branch=wt_handle.branch if wt_handle else None,
                        save_state=save_state,
                        append_jsonl=append_jsonl,
                    )
                    fail_status = decision.status
                    render_record_integration_refusal(
                        item,
                        code=fail_status,
                        reason=integ_reason,
                        branch=wt_handle.branch if wt_handle else None,
                    )
                    lane_branch = wt_handle.branch if wt_handle else "(none)"
                    print(
                        pal(
                            f"  ! IPD {item['id6']} finalized on lane {lane_branch} but NOT "
                            f"integrated to main ({fail_status}): {integ_reason}",
                            "yellow",
                        ),
                        file=sys.stderr,
                    )
                    if decision.deferred:
                        print(
                            pal(
                                f"    -> {decision.reason}",
                                "cyan",
                            ),
                            file=sys.stderr,
                        )
                    disposition = fail_status
                else:
                    attempt["ending_head"] = git_head(repo)
                    attempt["ending_status"] = git_status(repo)
                    if (
                        wt_handle is not None
                        and lane_containment.lane_preserved_for_missing_input(item)
                    ):
                        missing_input_reason = (
                            "a missing-input report was refused; the lane is preserved and "
                            "paused (spec 7ckptx R3.2) so its evidence is not destroyed"
                        )
                        append_jsonl(
                            run_dir / "events.jsonl",
                            {
                                "at": utc_now(),
                                "event": "lane-preserved-for-missing-input",
                                "id6": item["id6"],
                                "branch": wt_handle.branch,
                                "worktree": str(wt_handle.path),
                                "reason": missing_input_reason,
                            },
                        )
                        lane_containment.record_preserved_lane_state(
                            item=item,
                            handle=wt_handle,
                            reason=missing_input_reason,
                            reason_codes=("missing-input-refused",),
                        )
                        print(
                            pal(
                                f"  ! lane {wt_handle.branch} PRESERVED: a missing-input report was "
                                f"refused (paused per spec R3.2); the lane was not torn down",
                                "yellow",
                            ),
                            file=sys.stderr,
                        )
                    elif wt_handle is not None:
                        decision = lane_containment.teardown_lane_if_classified(
                            repo=repo,
                            handle=wt_handle,
                            run_dir=run_dir,
                            item=item,
                        )
                        if decision.torn_down:
                            wt_handle = None
                        else:
                            lane_containment.record_lane_preserved(
                                run_dir=run_dir,
                                item=item,
                                handle=wt_handle,
                                reason=decision.reason,
                                reason_codes=decision.reason_codes,
                                detail=decision.inventory.as_dict(),
                            )
                            print(
                                pal(
                                    f"  ! lane {wt_handle.branch} PRESERVED (not torn down): "
                                    f"{decision.reason}",
                                    "yellow",
                                ),
                                file=sys.stderr,
                            )
                    disposition = "executed"
                    attempt["disposition"] = "executed"
                    attempt["finalized"] = True
                    attempt["integrated"] = integ_reason
                    item["status"] = "executed"
                    try:
                        item["last_plan_path"] = str(
                            resolve_plan_path(
                                repo, item.get("configured_file", ""), item["id6"]
                            )
                        )
                    except DriverError:
                        pass
                    save_state(run_dir, state)
                    append_jsonl(
                        run_dir / "events.jsonl",
                        {
                            "at": utc_now(),
                            "event": "ipd-finalized",
                            "id6": item["id6"],
                            "setid": item["setid"],
                            "integration": integ_reason,
                        },
                    )
            else:
                attempt["ending_head"] = git_head(repo)
                attempt["ending_status"] = git_status(repo)
                attempt["finalize_refused"] = fin_msg
                item["finalize_refusal"] = fin_msg
                save_state(run_dir, state)
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "ipd-finalize-refused",
                        "id6": item["id6"],
                        "exit_code": fin_rc,
                        "detail": fin_msg,
                    },
                )
                print(
                    pal(
                        f"  ! IPD {item['id6']} finalize refused (left {disposition}, not forced): "
                        f"{fin_msg}",
                        "yellow",
                    ),
                    file=sys.stderr,
                )
        elif self_finalize and not work_dir and integration.earned:
            try:
                current_plan_for_finalize = resolve_plan_path(
                    repo, item.get("configured_file", ""), item["id6"]
                )
            except DriverError:
                current_plan_for_finalize = plan_path
            actor = driver_actor(state, labels=host_labels)
            fin_message = (
                f"{host_labels.command} self-finalize: {item['id6']} verified "
                f"(set {item['setid']}, attempt {attempt_no})."
            )
            record_item_spec_edits(
                repo,
                current_plan_for_finalize,
                item,
                reconcile=lambda r, p: compute_scope_reconciliation(
                    r, p, labels=host_labels
                ),
            )
            fin_rc, fin_msg = driver_finalize(
                repo, current_plan_for_finalize, item["id6"], actor, fin_message
            )
            attempt["ending_head"] = git_head(repo)
            attempt["ending_status"] = git_status(repo)
            if fin_rc == 0:
                attempt["disposition"] = "executed"
                attempt["finalized"] = True
                disposition = "executed"
                try:
                    plan_path = resolve_plan_path(
                        repo, item.get("configured_file", ""), item["id6"]
                    )
                except DriverError:
                    pass
            else:
                attempt["finalize_refused"] = fin_msg
                item["finalize_refusal"] = fin_msg
                save_state(run_dir, state)
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "ipd-finalize-refused",
                        "id6": item["id6"],
                        "exit_code": fin_rc,
                        "detail": fin_msg,
                    },
                )
                print(
                    pal(
                        f"  ! IPD {item['id6']} finalize refused (left {disposition}, not forced): "
                        f"{fin_msg}",
                        "yellow",
                    ),
                    file=sys.stderr,
                )
        if disposition == "executed":
            if not (item.get("backlog_close") or {}).get("closed"):
                process_backlog_close(run_dir, state, item)

    if wt_handle is not None and not is_review and item.get("status") != "executed":
        lane_containment.record_lane_preserved(
            run_dir=run_dir,
            item=item,
            handle=wt_handle,
            reason=(
                f"the item finished {item.get('status')!r} rather than executed, so its work was "
                "never integrated; the lane is kept attributably for a later turn"
            ),
            reason_codes=("not-integrated",),
        )
        save_state(run_dir, state)
        print(
            pal(
                f"  • IPD {item['id6']} work preserved on lane {wt_handle.branch} "
                f"at {wt_handle.path} (not integrated; attributable for a later turn/child-03)",
                "dim",
            ),
            file=sys.stderr,
        )

    item["status"] = disposition
    save_state(run_dir, state)

    full_auto = state.get("options", {}).get("full_auto", False)
    auto_approved = False
    if is_review and disposition in ("reviewed", "approved") and full_auto:
        plan_curr = resolve_plan_path(
            repo, item.get("configured_file", ""), item["id6"]
        )
        if is_plan_review_approved(plan_curr):
            try:
                set_plan_approved(repo, item["id6"])
                run_action = state.get("options", {}).get("action")
                if run_action != "review":
                    item["action"] = "execute"
                    item["status"] = "queued"
                item["auto_approved"] = True
                auto_approved = True
                save_state(run_dir, state)
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "ipd-auto-approved",
                        "id6": item["id6"],
                    },
                )
            except Exception as exc:
                print(
                    pal(
                        f"  ! Failed to auto-approve IPD {item['id6']}: {exc}",
                        "yellow",
                    ),
                    file=sys.stderr,
                )

    glyph = "\u2713" if disposition in SUCCESS_STATES else "\u25cf"
    glyph_color = (
        "green"
        if disposition in SUCCESS_STATES
        else (_STATUS_COLOR.get(disposition, "yellow"))
    )
    finish = (
        pal(f"{glyph} ", glyph_color)
        + pal(f"IPD {seq:02d}/{total} {item['id6']}", "bold")
        + pal(f" ({action})", "dim")
        + " -> "
        + pal(disposition, glyph_color)
        + pal(f"  (exit {exit_code})", "dim")
    )
    print(finish)
    if auto_approved:
        print(
            pal(
                f"  \u2713 IPD {item['id6']} auto-approved (review readiness cleared, "
                "NOT human approval); progressing to execution",
                "cyan",
            )
        )
    print()
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "at": utc_now(),
            "event": "ipd-finished",
            "id6": item["id6"],
            "action": action,
            "attempt": attempt_no,
            "exit_code": exit_code,
            "status": disposition,
            "session_id": session_id,
            "verification_status": verify_disp,
        },
    )

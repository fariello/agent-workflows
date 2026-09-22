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
from typing import (
    Any,
    Collection,
    Dict,
    FrozenSet,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
)

# --------------------------------------------------------------------------------------
# Execution ROLE (wtiso-03 `rchpms` E-04). x03wgn Section 2 "Receipt ownership does not mean agent
# tool compliance" + Section 3 `AW-LIFECYCLE-ROLE-001`.
#
# The runner owns begin/finalize for a managed lane. Receipt OWNERSHIP alone does not stop an in-lane
# agent from running `aw ipd begin`/`aw ipd finalize` itself, which forks a SECOND receipt and a second
# lifecycle transaction the driver cannot see; the in-lane receipt copy then hides the split. So a
# process that identifies as a managed WORKER refuses these two verbs outright and says what to do
# instead.
#
# HONEST LIMIT: this is an environment SELECTOR, i.e. the operational-default guidance layer, not a
# hardened boundary. A same-user worker with shell access can unset the variable. Hard enforcement is
# an OS sandbox / separate principal (x03wgn, Phase 6 `1o4eif`).
# --------------------------------------------------------------------------------------

# The env selector the runner exports into a managed worker's child environment.
EXECUTION_ROLE_ENV = "AW_EXECUTION_ROLE"
ROLE_WORKER = "worker"

LIFECYCLE_ROLE_ERROR = (
    "AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes; a worker-role "
    "process must not run them"
)


def runner_owns_lifecycle_notice(driver_owns_transition: bool) -> str:
    """The turn-start ADVERTISEMENT of the rule :data:`LIFECYCLE_ROLE_ERROR` enforces at turn end.

    roleadv-01 (`8b9ufm`) E-02/E-03, from backlog `fvl44r`. Returns the prompt block when the DRIVER
    owns the lifecycle transition, and ``""`` when it does not. ONE definition, so every prompt
    surface on every host renders byte-identical text and no host can drift from the other on an
    AUTHORITY rule.

    WHY IT IS ADVERTISED AT ALL, since the rule was already enforced. `_refuse_worker_role_verb`
    states the rule correctly but only at the END of a turn, in the agent's face, after the work is
    done; the prompt that OPENED the turn said nothing about who owns the transition and its only
    mention of finalize presupposed the agent performed it. Measured cost: plan `03ie04` completed
    every `E-*` and `V-*` item with evidence and then spent its terminal output reasoning at length
    about a refusal that is the expected path. Enforcement and advertisement are not alternatives;
    enforcing an unadvertised rule bills a whole agent turn to teach it.

    WHY IT IS CONDITIONAL, which is the load-bearing half. `--no-self-finalize` is a shipped run
    option whose own help text says "the agent must move the plan itself", and under it the runner
    never calls `driver_begin`/`driver_finalize`. An UNCONDITIONAL statement would therefore tell the
    one agent that MUST transition its own plan not to, leaving the plan in `pending/` transitioned by
    nobody: strictly worse than the wasted turn this fixes. The caller passes the run's OWN frozen
    `options.self_finalize` (default True, matching the shipped default), never an environment probe:
    at prompt-build time `os.environ` is the DRIVER's environment, not the child's, and
    `lane_root is not None` answers "am I isolated", which is a different question (a non-isolated
    turn under `--no-isolate-worktree` still gets a driver finalize).

    WHAT IT DELIBERATELY DOES NOT SAY: that the driver WILL transition the plan. Ownership is not
    outcome. A driver finalize additionally requires the integration gate to be earned, which under
    the default `--validate=false` needs a passing driver-run suite; measured over 47 runs whose
    outcomes mention this token, 22 items never reached `executed`. So this states OWNERSHIP and the
    agent's own terminal OBLIGATION, and promises nothing about the result.

    Pure and ASCII-only: the prompts that embed it are asserted pure ASCII
    (`tests/test_reporting_contract.py::DriverPromptTests::test_prompts_are_pure_ascii`).
    """
    if not driver_owns_transition:
        return ""
    return (
        "## Who performs the lifecycle transition\n"
        "\n"
        "The runner performs `aw ipd begin` and `aw ipd finalize` for this run. Do NOT run them\n"
        "yourself: a worker-role process is refused with `AW-LIFECYCLE-ROLE-001`, because a second\n"
        "receipt and a second lifecycle transaction the driver cannot see would fork the plan's\n"
        "authority. Your terminal obligation is to write the outcome file named above and stop.\n"
    )


def worker_role_active(env: "Mapping[str, str]") -> bool:
    """True iff ``env`` marks this process as a MANAGED WORKER lane (``AW_EXECUTION_ROLE=worker``).

    Pure: reads the passed mapping only, never ``os.environ`` directly, so the predicate is testable
    without mutating global process state. Any other value (absent, empty, ``coordinator``) is NOT a
    worker, so a normal human/agent invocation outside a managed lane is unaffected.
    """
    return str(env.get(EXECUTION_ROLE_ENV) or "").strip() == ROLE_WORKER


def _refuse_worker_role_verb(verb: str) -> int:
    """Emit the deterministic ``AW-LIFECYCLE-ROLE-001`` refusal for a driver-only lifecycle verb.

    Writes the corrective error to STDERR (the diagnostic channel, so a caller parsing stdout for
    structured output is unaffected) and returns :data:`EXIT_CANNOT_RUN`. Called BEFORE any selector
    resolution, gate, receipt write, or plan mutation, so a refused invocation has NO side effect
    whatsoever - that is the point: a forked worker receipt is exactly what this prevents.

    THE EXPECTED-PATH FRAMING (roleadv-01 `8b9ufm` E-05) exists because this is a NON-ERROR path for a
    managed lane that READS as a hard failure: stderr plus a nonzero exit. An agent that hits it after
    doing everything right has historically spent its terminal output explaining a refusal that was
    simply the normal handoff (measured: plan `03ie04` reported `substantially-complete` with a long
    `incomplete_requirements` entry, every word correct and none of it necessary).

    IT SAYS OBLIGATION DISCHARGED, NEVER OUTCOME GUARANTEED, and the distinction is deliberate. This
    function runs in the AGENT's process, which cannot see the run's options, and a driver finalize
    needs more than ownership: the integration gate must be earned, which under the default
    `--validate=false` requires a passing driver-run suite. Measured over 47 runs whose outcomes
    mention this token, 22 items never reached `executed`. So "you have nothing further to do" is true
    (the agent genuinely may not act), while "the driver will now transition the plan" would be a
    promise broken in roughly a fifth of real cases, and an agent that believed it would claim success
    it did not earn.

    THE CHANNEL AND THE EXIT CODE ARE UNCHANGED AND LOAD-BEARING. A "this is fine" message on exit 0
    would be a real regression: the verb genuinely did not do what was asked, and a scripted
    `aw ipd finalize` inside a lane must fail rather than appear to succeed.
    """
    import sys as _sys

    print(
        f"{LIFECYCLE_ROLE_ERROR} (refused: aw ipd {verb}). "
        "The runner performs begin/finalize for this lane; report your result instead "
        "(write the outcome file the prompt names) and let the driver transition the plan. "
        "THIS IS THE EXPECTED PATH FOR A MANAGED LANE, not a failure of your work: once your "
        "outcome file is written your obligation is discharged and NO FURTHER ACTION is required "
        "from you here.",
        file=_sys.stderr,
    )
    return EXIT_CANNOT_RUN


# Receipt schema version (bump on an incompatible receipt-shape change).
#
# v2 (wtiso-03 `rchpms` E-02): adds ``frozen_region_digest``, which REPLACES ``plan_content_digest``
# as the receipt's validity key (see :func:`frozen_region_digest` and backlog `xmqv5l`).
# ``plan_content_digest`` is still WRITTEN, so the shape is additive and every existing reader keeps
# working; a v1 receipt that predates the field falls back to the old whole-file rule in
# :func:`receipt_is_current`, so an old receipt is never spuriously accepted.
RECEIPT_SCHEMA_VERSION = 2

# Exit-code convention shared with `aw ipd lint` (0 ok / 1 findings / 2 cannot-run).
EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_CANNOT_RUN = 2

_RECEIPT_SUBDIR = ("state", "ipd-lifecycle")

# --------------------------------------------------------------------------------------
# Finalize transaction journal + lock (Order 3xh53a). Reuses the repository's canonical
# crash-safe pattern from layout_migration.MigrationManager: an exclusive writer lock + an
# atomically-checkpointed transaction journal under the gitignored .aw/state/runtime/ tree, with
# idempotent resume/rollback driven by the persisted phase (never volatile in-memory snapshots).
# --------------------------------------------------------------------------------------

FINALIZE_JOURNAL_SCHEMA_VERSION = 1

# Journal phases (a monotonic-ish enum; ``unknown-outcome`` is a fail-closed terminal-ambiguous
# state). BEFORE the lifecycle commit everything is recoverable to the pre-finalize state; AFTER a
# commit the transaction is either ``committed-incomplete`` (resumable, no history rewrite) or
# ``complete``.
PHASE_PREPARED = "prepared"  # journal written, no mutation yet
PHASE_MUTATING = (
    "mutating"  # plan bytes/status/move/index being written (working-tree only)
)
PHASE_READY_TO_COMMIT = (
    "ready-to-commit"  # all pre-commit mutations staged; about to commit
)
PHASE_COMMITTED_INCOMPLETE = (
    "committed-incomplete"  # lifecycle commit exists; post-lint pending
)
PHASE_UNKNOWN_OUTCOME = (
    "unknown-outcome"  # ambiguous/corrupt evidence; fail closed, never success
)
PHASE_COMPLETE = "complete"  # post-transition passed; receipt + journal finalized

_PRE_COMMIT_PHASES = frozenset((PHASE_PREPARED, PHASE_MUTATING, PHASE_READY_TO_COMMIT))


class TransactionLockError(RuntimeError):
    """Raised when the finalize writer lock is held by another live process."""


class _InjectedFault(RuntimeError):
    """Test-only fault injected at a named finalize checkpoint to exercise rollback/recovery."""


class _CommitRefused(RuntimeError):
    """The lifecycle commit itself was REJECTED (a hook said no), as distinct from an internal error.

    Carried as its own type so the transaction can hand a hook rejection to the SAME observed-state
    classification a git failure has always taken (which diagnoses a concurrent-writer cause and fails
    closed), instead of collapsing it into the generic "mutation failed" branch and losing that
    diagnosis.
    """


# Memoized checkout -> control-root resolutions (E-07). Keyed on the RESOLVED ``start`` path, so two
# different start paths that resolve differently can never share an entry; the value is the resolved
# control root. Only a POSITIVE resolution (git answered and a main worktree was established) is
# cached, deliberately:
#
# * a FALLBACK must stay recomputable, because it can mean "this directory is not a git checkout YET"
#   (a test that later runs `git init` in it) or "the git spawn transiently failed" (E-06's EAGAIN
#   path). Caching either would turn a momentary condition into a permanent wrong answer.
# * a positive resolution is stable for the life of a checkout, which is what makes it safe to keep.
#
# HONEST LIMIT: a cached entry is stale if the very same absolute path stops being that checkout (a
# temp dir removed and recreated at an identical name, which is what a per-case real-worktree test
# fixture effectively does). Such tests must call :func:`clear_checkout_control_root_cache` in
# ``setUp``; the cache is process-local, so nothing persists past the process.
_CONTROL_ROOT_CACHE: Dict[str, Path] = {}

# Bound the cache so a long test session that builds thousands of throwaway checkouts cannot grow it
# without limit. A real process sees a handful of checkouts, so the cap is never reached in practice
# and a plain clear-on-overflow is adequate (no LRU bookkeeping for a cache this small).
_CONTROL_ROOT_CACHE_MAX = 256


def clear_checkout_control_root_cache() -> None:
    """Drop every memoized checkout->control-root entry (see :func:`checkout_control_root`).

    Call this from a test fixture that creates a FRESH checkout or ``git worktree`` per case, so a
    new tree at a previously-seen path cannot read the earlier tree's cached answer. Production code
    should not need it: a checkout's control root does not move while the process runs.
    """
    _CONTROL_ROOT_CACHE.clear()


def checkout_control_root(start: Path) -> Path:
    """The checkout's ONE ``.aw`` control root for any path inside it (backlog ``dh0uno``).

    Control state (begin receipts, the finalize writer lock, finalize transaction journals) belongs
    to the CHECKOUT, not to whichever worktree happens to be the caller's cwd. This function is the
    single place that decides where that root lives, so a linked ``git worktree`` (a driver "lane")
    and the main tree resolve to the SAME location.

    WHY THIS EXISTS: these paths used to be composed as ``repo_root/".aw"/...`` by each caller, and
    ``repo_root`` for an in-lane invocation is the LANE. So an inner ``aw`` running inside a lane
    wrote its receipt/lock/journal to ``<lane>/.aw/state/...`` - a second control store the driver
    (running from the main tree) could not see and lane teardown then deleted. Measured before this
    fix: ``receipt_dir(<main>)`` and ``receipt_dir(<lane>)`` returned two different directories.

    Behavior, and the honest limits of it:

    * INSIDE a Git checkout -> the MAIN worktree's ``.aw``, derived from ``git rev-parse
      --git-common-dir`` (every linked worktree of a checkout shares one common dir). That collapse
      IS the fix.
    * NOT in a Git checkout, or a bare/exotic ``GIT_DIR`` where no main worktree can be established
      -> ``start/.aw`` unchanged. There is no checkout identity to collapse to, hence no fork to
      fix, and this keeps temp-directory callers (much of the test suite) byte-compatible.
    * GIT COULD NOT EVEN BE SPAWNED (git absent, or the OS refused a fork) -> ``start/.aw``, the same
      fallback the nonzero-returncode branch takes. This function must be TOTAL: its callers
      (:func:`receipt_dir`, :func:`finalize_lock_path`, :func:`finalize_journal_path`) were PURE path
      composition before ``dh0uno`` and are called from loops and from error-message formatting, so a
      raise here would surface in places that cannot handle it. The case that matters most is
      :func:`release_finalize_lock`, which runs from a ``finally:`` during finalize: a raise there
      both LEAKS the writer lock and REPLACES the real in-flight exception with a confusing git
      error. Only ``OSError`` is caught (it covers ``FileNotFoundError`` for a missing git and
      ``BlockingIOError``/EAGAIN for a fork failure), so a genuine programming error still surfaces.

    Nothing is invented and no worktree path is hashed: the fallback is "use exactly what you were
    given", which cannot fork because only one tree is involved.

    The resolution is MEMOIZED (see :data:`_CONTROL_ROOT_CACHE`), so a repeated lookup does not spawn
    a git subprocess; only a positive resolution is cached, and
    :func:`clear_checkout_control_root_cache` drops the memo.
    """
    base = Path(start)
    if not base.is_dir():
        return base / ".aw"
    try:
        key = str(base.resolve())
    except OSError:
        # A path that cannot be resolved is simply not cacheable; fall through uncached rather than
        # fail a path accessor.
        key = ""
    if key:
        cached = _CONTROL_ROOT_CACHE.get(key)
        if cached is not None:
            return cached
    try:
        rc, out, _err = _git(
            base, ["rev-parse", "--path-format=absolute", "--git-common-dir"]
        )
    except OSError:
        # git is absent or the OS refused to spawn it. Not cached: the condition is transient in the
        # EAGAIN case, and a permanently cached fallback would be a worse failure than a retry.
        return base / ".aw"
    if rc != 0:
        return base / ".aw"
    raw = (out or "").strip()
    if not raw:
        return base / ".aw"
    common_dir = Path(raw)
    # For a normal (non-bare) checkout the common dir is `<main>/.git`, so the main worktree is its
    # parent. Anything else (bare repo, GIT_DIR override) has no product worktree to anchor on, so
    # fall back rather than guess a location.
    if common_dir.name == ".git" and common_dir.parent.is_dir():
        resolved = common_dir.parent / ".aw"
        if key:
            if len(_CONTROL_ROOT_CACHE) >= _CONTROL_ROOT_CACHE_MAX:
                _CONTROL_ROOT_CACHE.clear()
            _CONTROL_ROOT_CACHE[key] = resolved
        return resolved
    return base / ".aw"


def _runtime_dir(repo_root: Path) -> Path:
    """``<checkout control root>/state/runtime`` - the finalize lock and transaction journals.

    Routed through :func:`checkout_control_root` (``dh0uno``): the old ``repo_root/.aw/state/runtime``
    gave each linked worktree its OWN lock and journal directory, so two lanes could each hold "the"
    exclusive finalize lock at once and neither could observe the other's in-flight transaction.
    """
    return checkout_control_root(repo_root) / "state" / "runtime"


def finalize_lock_path(repo_root: Path) -> Path:
    """The exclusive finalize writer lock over the shared plan manifest."""
    return _runtime_dir(repo_root) / "locks" / "ipd_finalize_writer.lock"


def finalize_journal_path(repo_root: Path, plan_id: str) -> Path:
    """The per-plan finalize transaction journal under the runtime transaction area."""
    return _runtime_dir(repo_root) / "transactions" / f"ipd_finalize_{plan_id}.json"


def _atomic_write_json_at(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
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


def acquire_finalize_lock(repo_root: Path, plan_id: str) -> None:
    """Acquire the exclusive finalize lock, reclaiming a STALE lock (dead PID) after consulting it.

    Raises TransactionLockError with an actionable owner/retry diagnostic when a LIVE process holds
    it. A stale lock (its recorded PID is not alive) is reclaimed rather than blindly deleted.
    """
    lock = finalize_lock_path(repo_root)
    lock.parent.mkdir(parents=True, exist_ok=True)
    if lock.exists():
        try:
            data = json.loads(lock.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        pid = data.get("pid")
        if pid and pid != os.getpid():
            alive = True
            try:
                os.kill(int(pid), 0)
            except ValueError:
                alive = False
            except PermissionError:
                alive = True  # EPERM: the process EXISTS (owned by another user), so it is alive
            except ProcessLookupError:
                alive = False  # ESRCH: no such process -> stale
            except OSError:
                alive = False
            if alive:
                raise TransactionLockError(
                    "ipd finalize writer lock held by active PID {0} (plan {1}); wait for it to "
                    "finish or, if that process is dead, remove {2}".format(
                        pid, data.get("plan_id"), lock
                    )
                )
        # else: stale (dead PID) - reclaim below (recovery consults the journal, not this file).
    payload = {
        "plan_id": plan_id,
        "pid": os.getpid(),
        "timestamp": _utc_now(),
    }
    _atomic_write_json_at(lock, payload)


def release_finalize_lock(repo_root: Path) -> None:
    """Release the finalize lock iff this process owns it."""
    lock = finalize_lock_path(repo_root)
    if not lock.exists():
        return
    try:
        data = json.loads(lock.read_text(encoding="utf-8"))
        if data.get("pid") == os.getpid():
            lock.unlink()
    except (OSError, ValueError):
        try:
            lock.unlink()
        except OSError:
            pass


def read_finalize_journal(repo_root: Path, plan_id: str) -> Optional[Dict[str, Any]]:
    """Load the finalize journal for ``plan_id`` (None if absent/unreadable)."""
    p = finalize_journal_path(repo_root, plan_id)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write_finalize_journal(repo_root: Path, journal: Dict[str, Any]) -> None:
    """Persist the journal atomically, appending the phase to a phase-history trail."""
    journal["updated_at"] = _utc_now()
    _atomic_write_json_at(finalize_journal_path(repo_root, journal["plan_id"]), journal)


def _clear_finalize_journal(repo_root: Path, plan_id: str) -> None:
    p = finalize_journal_path(repo_root, plan_id)
    try:
        p.unlink()
    except OSError:
        pass


def _git_index_entries(repo_root: Path, paths: List[str]) -> Dict[str, str]:
    """The exact staged Git-index entry line (`git ls-files --stage`) for each owned path.

    Captures ``<mode> <object> <stage>\\t<path>`` so rollback can restore precisely the prior index
    state for lifecycle-owned paths without touching any disjoint staged/dirty work.
    """
    out: Dict[str, str] = {}
    if not paths:
        return out
    rc, text, _err = _git(repo_root, ["ls-files", "--stage", "--", *paths])
    if rc != 0:
        return out
    for line in text.splitlines():
        if "\t" in line:
            _meta, p = line.split("\t", 1)
            out[p.strip()] = line
    return out


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
    """Resolve the PRODUCT tree for ``start``: the git worktree top-level, or ``start`` if not a repo.

    This deliberately returns the WORKTREE, and for a managed lane that is CORRECT: callers use it for
    product operations that must target the tree the agent actually edited (resolving the plan file,
    freezing ``HEAD``, the path-scoped finalize commit, the plan's own ``git mv``). Collapsing this to
    the main checkout would make finalize commit into the wrong tree.

    What it must NOT decide is the CONTROL root. That is :func:`checkout_control_root`; see ``dh0uno``.
    Before that split, the value returned here was also concatenated into ``.aw/state/...``, so a
    lane's product tree silently became its control root.
    """
    from agent_workflows.run_evidence import get_worktree_path

    return Path(get_worktree_path(str(start)))


def receipt_dir(repo_root: Path) -> Path:
    """The gitignored directory holding begin receipts: ``<checkout>/.aw/state/ipd-lifecycle/``.

    Anchored on the CHECKOUT via :func:`checkout_control_root`, not on the passed tree. Called with a
    linked lane worktree this used to return ``<lane>/.aw/state/ipd-lifecycle/``, i.e. a second
    receipt store the driver could not see and teardown destroyed (backlog ``dh0uno``). Outside a Git
    checkout it still returns ``repo_root/.aw/state/ipd-lifecycle/``, unchanged.
    """
    return checkout_control_root(repo_root).joinpath(*_RECEIPT_SUBDIR)


def receipt_path_for(repo_root: Path, plan_id: str) -> Path:
    """The receipt path for a plan id6: ``.aw/state/ipd-lifecycle/<id6>.receipt.json``."""
    return receipt_dir(repo_root) / f"{plan_id}.receipt.json"


def plan_content_digest(text: str) -> str:
    """A stable sha256 over the plan's exact bytes (identity of the plan content at begin time)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def frozen_region_digest(text: str) -> str:
    """A stable sha256 over ONLY the plan invariants that must not change mid-execution.

    wtiso-03 (`rchpms`) E-01, fixing backlog `xmqv5l`. The receipt's ORIGINAL validity key was the
    whole-file ``plan_content_digest``, which made the receipt go stale on every CORRECT execution: a
    conforming executor MUST edit the plan it is executing (mark each E item performed, fill each V
    ``Observed evidence``/``Result``, append a ``## Workflow history`` line), so the byte digest always
    changed and ``finalize_precheck`` refused with "the begin receipt ... is STALE". The frozen
    CONTRACT, however, did not change at all.

    So this digest covers the reviewed contract and nothing else:

      * the frozen ``Scope-Paths`` allowlist (via :func:`_frozen_scope_paths`), and
      * the requirement categories (via :func:`_requirements_from_plan`): scope, each E-item's action
        text, and each V-item's row text.

    It DELIBERATELY excludes the mutable execution/validation STATE (``Execution state:``,
    ``Result:``, ``Observed evidence:``), the ``## Workflow history``, and the ``[ ]``/``[x]`` checkbox
    marks. Those exclusions are structural rather than textual: ``ipd_lint.parse`` puts a leaf's
    indented ``- Key: value`` sub-fields in ``Leaf.fields`` and its checkbox in ``Leaf.checked``, while
    ``Leaf.text`` is the action text alone, and ``_requirements_from_plan`` reads only ``.text``. Prose
    sections (``## Findings``, ``## Proposed changes``) are likewise outside the requirement set, so
    editing them does not invalidate a receipt (OQ-01: they are not part of the reviewed contract).

    The result is a guard that stays TIGHT on what matters - changing a ``Scope-Paths`` entry or an
    E/V requirement line DOES invalidate the receipt, because that is a different plan than the one
    the gate approved - while no longer punishing a legitimate self-execution.

    Serialization is deterministic (``sort_keys=True`` over a mapping of sorted category lists) so the
    digest is stable across runs and dict-ordering changes.

    THE PAYLOAD IS BUILT BY :func:`_frozen_region_payload`, NOT INLINE (rcptwiden `63425h` E-03), and
    that indirection is load-bearing rather than tidy: :func:`frozen_region_comparison` reproduces this
    exact payload with the RECEIPT's stored scope substituted in, and a second hand-written copy of the
    literal would silently drift from this one. A drifted copy would make the substitution never
    reproduce the stored digest, so the widening accept would never fire and the drift would present as
    "the feature does not work" rather than as a diff.
    """
    serialized = json.dumps(
        _frozen_region_payload(text), sort_keys=True, ensure_ascii=True
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _frozen_region_payload(
    text: str,
    *,
    scope_paths_override: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """THE ONE payload shape the frozen-region digest hashes (rcptwiden `63425h` E-03).

    Extracted from :func:`frozen_region_digest` so exactly one construction of the
    ``{"scope_paths": ..., "requirements": {...}}`` literal exists. Two callers share it and MUST
    share it:

    * :func:`frozen_region_digest`, with no override, which is the receipt's validity key; and
    * :func:`frozen_region_comparison`, with ``scope_paths_override`` set to the RECEIPT's stored
      ``scope_paths``, which is the SUBSTITUTION TEST that decides whether anything OTHER than scope
      changed.

    ``scope_paths_override`` replaces BOTH scope inputs, and that is deliberate: the digest hashes the
    scope twice, once as the top-level ``scope_paths`` allowlist and once inside
    ``requirements["scope"]``, and for a non-grandfathered plan those two carry the same entries.
    Substituting only one would leave the other reflecting the CURRENT plan, so the comparison would
    never reproduce the stored digest and every widening would read as a requirement change. See
    :func:`frozen_region_comparison` for why a GRANDFATHERED plan (where the two are NOT the same
    field) is excluded from the substitution entirely rather than reasoned about here.
    """
    requirements = {
        category: sorted(values)
        for category, values in sorted(_requirements_from_plan(text).items())
    }
    scope_paths = sorted(_frozen_scope_paths(text))
    if scope_paths_override is not None:
        scope_paths = sorted(scope_paths_override)
        # The `scope` requirement category mirrors the allowlist for a non-grandfathered plan, so it
        # must be substituted in lockstep. `_requirements_from_plan` omits an EMPTY category, so an
        # override of `[]` removes the key rather than writing an empty list, matching what
        # `frozen_region_digest` would have produced for a plan with no declared allowlist.
        if scope_paths:
            requirements["scope"] = list(scope_paths)
        else:
            requirements.pop("scope", None)
    return {"scope_paths": scope_paths, "requirements": requirements}


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


# --------------------------------------------------------------------------------------
# Event-derived lifecycle state (agentadhere Phase 3, IPD wqj1ne E-01).
#
# Findings bu9yij 7.3: a freely-editable `- Status:` is trivially hand-editable, so the lifecycle
# state should be DERIVED from a validated event stream. We build ON the EXISTING history (no
# parallel log, DECISION 16-wqj1ne-D1): for a PLAN the events are its inline `## Workflow history`
# records (record_history owns/defers to them; plans are excluded from the sidecar), for other
# trees they are the sidecar records. The derived status runs ALONGSIDE the authoritative
# `- Status:` read (OQ-01) - it validates/cross-checks, it does not replace the field this phase.
#
# HONEST LIMIT (findings 5.4/7.3): the local event stream is FORGEABLE by a privileged local agent
# (it can rewrite the inline history or the sidecar). This derivation is a consistency + validity
# check, NOT a tamper-proof authority boundary; non-forgeable provenance is the deferred
# external-signing set.

# The logical lifecycle stages (findings 7.3), mapped from the concrete plan status vocabulary.
LIFECYCLE_EVENTS: Tuple[str, ...] = (
    "IPD_CREATED",
    "WORK_STARTED",
    "TEST_EVIDENCE_RECORDED",
    "REVIEWED",
    "FINALIZED",
)

# The canonical plan status RANKS (a status may only advance forward through these ranks; the
# terminal `executed` state closes the sequence). Mirrors the plan status vocabulary used by
# `aw set`/`aw ipd set` and ipd_schema. `approved` and `auto-approved` share a rank (they are two
# ways to reach the ready-to-execute stage, NOT sequential steps), so `approved -> executed` is a
# valid single forward step, not a skip.
_PLAN_STATUS_RANKS: Dict[str, int] = {
    "draft": 0,
    "to-review": 1,
    "reviewed": 2,
    "approved": 3,
    "auto-approved": 3,
    "executed": 4,
}
# The rank-ordered status labels (one representative per rank) for skip-diagnostic messages.
_PLAN_STATUS_ORDER: Tuple[str, ...] = (
    "draft",
    "to-review",
    "reviewed",
    "approved",
    "executed",
)
# Terminal statuses whose transition is AUTHORITATIVE (only `aw ipd finalize` may perform it).
_TERMINAL_STATUSES: FrozenSet[str] = frozenset(("executed",))
# The actor `aw ipd finalize` records for the terminal transition; a terminal transition by any
# other actor path is an UNAUTHORIZED terminal transition (rejected).
_FINALIZE_ACTORS: FrozenSet[str] = frozenset(
    ("aw ipd finalize", "aw finalize", "ipd finalize")
)


class TransitionCheck(NamedTuple):
    """Result of validating one lifecycle transition (E-01)."""

    ok: bool
    reason: str  # "" when ok; else the specific rejection reason


def _status_rank(status: str) -> int:
    """The rank of a plan status, or -1 for an unknown/off-sequence status."""
    return _PLAN_STATUS_RANKS.get(status, -1)


def validate_transition(
    from_status: Optional[str],
    to_status: str,
    *,
    actor: Optional[str] = None,
    tree_id_current: Optional[str] = None,
    tree_id_evidence: Optional[str] = None,
    evidence: Optional[Dict[str, Any]] = None,
    require_evidence: bool = False,
) -> TransitionCheck:
    """Validate ONE lifecycle transition; return (ok, reason). Rejects (findings 7.3):

    * MISSING PREDECESSOR - a transition that skips a required earlier status (e.g. draft -> executed
      without the intervening reviewed/approved), or a backwards move.
    * STALE TREE ID - the transition cites evidence bound to a tree that is not the current tree.
    * INVALID ACTOR - an empty/malformed actor string.
    * MALFORMED EVIDENCE - ``require_evidence`` is set but the evidence is absent/not a mapping/lacks
      a bound ``git_tree``.
    * UNAUTHORIZED TERMINAL - a terminal (``executed``) transition performed by an actor that is not
      the finalize path.

    This is a pure validity predicate over ALREADY-known facts; it is NOT tamper-proof (the caller's
    inputs are locally forgeable). Order matters: actor and terminal-authority are checked first so
    an unauthorized terminal transition is reported as such rather than as a predecessor gap.
    """
    to_status = (to_status or "").strip()
    from_status = (from_status or "").strip() or None

    # INVALID ACTOR: an empty/whitespace actor is never a valid transition author.
    if actor is not None and not actor.strip():
        return TransitionCheck(False, "invalid actor: empty actor string")

    # UNAUTHORIZED TERMINAL: only the finalize path may perform the terminal transition.
    if to_status in _TERMINAL_STATUSES:
        if actor is not None and actor.strip() not in _FINALIZE_ACTORS:
            return TransitionCheck(
                False,
                f"unauthorized terminal transition to {to_status!r} by actor "
                f"{actor.strip()!r}: only `aw ipd finalize` may perform it",
            )

    # STALE TREE ID: evidence must be bound to the current tree.
    if tree_id_evidence is not None and tree_id_current is not None:
        if tree_id_evidence != tree_id_current:
            return TransitionCheck(
                False,
                f"stale tree id: evidence bound to {tree_id_evidence[:12]!r} but current tree is "
                f"{tree_id_current[:12]!r}",
            )

    # MALFORMED EVIDENCE: when evidence is required, it must be a mapping with a bound git_tree.
    if require_evidence:
        if not isinstance(evidence, dict) or not evidence.get("git_tree"):
            return TransitionCheck(
                False,
                "malformed evidence: missing or non-mapping evidence with no bound git_tree",
            )

    # MISSING PREDECESSOR: the lifecycle only moves FORWARD. A forward move MAY skip an optional
    # intermediate stage (real workflows go `draft -> reviewed` directly when `/plan-review` sets
    # reviewed without a separate `to-review` step), so a forward skip is ALLOWED; only a BACKWARDS
    # move is a missing-predecessor violation. The one exception is the terminal `executed`
    # transition, which additionally REQUIRES a sufficiently-advanced predecessor (at least
    # `reviewed`) so a raw `draft -> executed` jump is caught. An unknown target is off-sequence.
    to_rank = _status_rank(to_status)
    if to_rank < 0:
        return TransitionCheck(False, f"unknown target status {to_status!r}")
    from_rank = _status_rank(from_status) if from_status else -1
    if from_status is None:
        # A first recorded event must start at the sequence head (draft); starting mid-sequence with
        # no predecessor is a missing-predecessor violation.
        if to_rank != 0:
            return TransitionCheck(
                False,
                f"missing predecessor: cannot start the lifecycle at {to_status!r} "
                f"(expected {_PLAN_STATUS_ORDER[0]!r})",
            )
        return TransitionCheck(True, "")
    if to_rank < from_rank:
        return TransitionCheck(
            False,
            f"missing predecessor: backwards transition {from_status!r} -> {to_status!r}",
        )
    # Terminal `executed` requires a sufficiently-advanced predecessor (>= reviewed).
    if to_status in _TERMINAL_STATUSES and from_rank < _PLAN_STATUS_RANKS["reviewed"]:
        return TransitionCheck(
            False,
            f"missing predecessor: terminal transition {from_status!r} -> {to_status!r} "
            f"requires at least 'reviewed'",
        )
    return TransitionCheck(True, "")


# The full plan status vocabulary a history line's leading token may legitimately be (a STATUS
# transition). A history line whose token is NOT one of these is a workflow NOTE (e.g.
# `/plan-review:`, `authored`, `note`, `created`), NOT a status transition, and is IGNORED by the
# event derivation - so annotations never masquerade as (invalid) transitions.
_PLAN_STATUS_VOCAB: FrozenSet[str] = frozenset(
    (
        "draft",
        "to-review",
        "reviewed",
        "approved",
        "auto-approved",
        "executed",
        "superseded",
        "not-executed",
        "reusable",
        "parked",
    )
)


def _plan_status_events(text: str) -> List[Tuple[str, str, str]]:
    """The plan's STATUS-TRANSITION events as (date, status, actor), OLDEST-first, from its INLINE
    history.

    Reuses ``record_history``'s inline parser (no parallel log). A plan history line
    ``- <date> <status> (<actor>): <msg>`` yields (date, status, actor); the ``workflow`` token in
    that grammar is the new status ONLY when it is a known plan status (``_PLAN_STATUS_VOCAB``). A
    line whose token is a workflow NOTE (``/plan-review``, ``authored``, ``note``, ``created`` with a
    non-status shape, ...) is NOT a transition and is skipped, so annotations never masquerade as
    transitions.
    """
    from agent_workflows import record_history as _rh

    events: List[Tuple[str, str, str]] = []
    for line in _rh._inline_history_records(text):
        date, workflow, actor, _msg = _rh._parse_record_line(line)
        token = (workflow or "").strip()
        if token in _PLAN_STATUS_VOCAB:
            events.append((date, token, actor.strip()))
    # Inline history is stored newest-first; reverse to oldest-first for derivation.
    events.reverse()
    return events


def derive_status_from_events(events: List[Tuple[str, str, str]]) -> Optional[str]:
    """Derive the visible lifecycle status from an OLDEST-first (date, status, actor) event list.

    The derived status is the LAST status in the event stream that lies on the canonical plan-status
    sequence (an off-sequence token such as a `parked`/`superseded` note is ignored for the forward
    derivation). Returns None for an empty/derivation-less stream. This is the DERIVED cross-check of
    the authoritative `- Status:` field; it never mutates anything.
    """
    derived: Optional[str] = None
    for _date, status, _actor in events:
        if _status_rank(status) >= 0:
            derived = status
    return derived


def derive_plan_status(text: str) -> Optional[str]:
    """Convenience: derive a plan's status from its inline history events (E-01)."""
    return derive_status_from_events(_plan_status_events(text))


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
    """True when ``receipt`` still matches the plan's FROZEN REQUIREMENT+SCOPE contract.

    INVARIANT (wtiso-03 `rchpms` E-03, fixing backlog `xmqv5l`): a receipt is current iff the plan's
    reviewed CONTRACT is unchanged - its frozen ``Scope-Paths`` plus its E/V requirement text - NOT
    iff the plan's bytes are unchanged.

    Why this changed: the previous whole-file ``plan_content_digest`` key was self-defeating. A
    CORRECT execution is REQUIRED to edit its own plan (mark each E item performed, fill each V
    ``Observed evidence``/``Result``, append a ``## Workflow history`` line), which always changed the
    byte digest, so :func:`finalize_precheck` refused every self-finalizing run with "the begin receipt
    ... is STALE" and left the work substantially-complete. Keying on the frozen region instead means a
    legitimate self-execution stays valid while a change to the reviewed contract - a different
    ``Scope-Paths`` entry, a rewritten E/V requirement - still invalidates the receipt, because that is
    genuinely a different plan than the one the pre-execution gate approved.

    LEGACY FALLBACK: a v1 receipt written before the field existed carries no
    ``frozen_region_digest``, so it is judged by the OLD whole-file rule. That is deliberate - a
    pre-Phase-2 receipt must not be spuriously ACCEPTED by a rule it was never bound under.

    OQ-01 rule (a) (digest invalidation) is what this predicate enforces; the path-overlap collision
    rule (b) remains Order 04's finalize responsibility, not this function's.

    UNCHANGED BY rcptwiden `63425h`, deliberately. That plan lets finalize ACCEPT one specific class of
    difference (an additive scope widening) with a recorded reason, but it does so by asking
    :func:`frozen_region_comparison` a SECOND question AFTER this predicate has already said False. This
    predicate keeps meaning exactly "is the frozen contract byte-identical", so every other caller
    (`wtiso_gate`'s receipt-vs-attempt narrative, the `check.scope-drift` liveness read, every existing
    test) sees what it always saw.
    """
    stored_frozen = receipt.get("frozen_region_digest")
    if stored_frozen is None:
        # Legacy (schema v1) receipt: no frozen-region binding to compare, so fall back to the
        # original whole-file rule rather than accepting it under a key it never recorded.
        return receipt.get("plan_content_digest") == plan_content_digest(plan_text)
    return stored_frozen == frozen_region_digest(plan_text)


# --------------------------------------------------------------------------------------
# The additive-widening comparison (rcptwiden `63425h` E-03/E-08/E-09)
# --------------------------------------------------------------------------------------
#
# WHY THIS EXISTS. `frozen_region_digest` hashes ONE opaque payload, so a plan that honestly DECLARED a
# newly-needed path and a plan that REWROTE its reviewed requirements are indistinguishable: both yield
# one False from `receipt_is_current` and both are refused as STALE. Measured 2026-09-16/17 in run
# `run-20260917T023628Z-4108757`, that refusal stranded three of twelve items (`i3d6ml`, `tx6q0h`,
# `sy7uwh`) whose ONLY frozen difference was an ADDED `Scope-Paths` entry, costing $95.71 and 3h10m and
# cascading into a `dependency-blocked` orchestrator. Meanwhile the CONCEALED edit finalized: an
# undeclared uncommitted path is DISREGARDED as unowned and demands no reason at all (measured:
# `out_of_scope_paths: []`, `disregarded_unowned_paths: ['tests/test_extra.py']`, precheck rc=0). So the
# system refused the honest act and waved through the concealed one.
#
# THE FIX IS A NARROWING, NOT A REMOVAL, exactly as `receipt_is_current`'s own history was: the original
# whole-file digest "refused every self-finalizing run" and was narrowed to the frozen region. This
# finishes that narrowing for the one false-positive class it left.


class FrozenRegionComparison(NamedTuple):
    """WHICH frozen-region categories differ, instead of one opaque boolean.

    ``added`` / ``removed`` are the ``Scope-Paths`` entry-set delta between the receipt's stored scope
    and the plan's CURRENT scope, compared AS SETS OF ENTRY STRINGS (E-05): the declared order is not
    semantic, so a pure reordering must read as unchanged rather than as a removal-plus-addition.

    ``non_scope_identical`` is the SUBSTITUTION TEST's answer: True iff substituting the receipt's
    stored ``scope_paths`` into the current plan's payload reproduces the stored
    ``frozen_region_digest``. Because that digest is a collision-resistant hash over the WHOLE payload,
    equality PROVES every non-scope requirement category (each E-item's action text, each V-item's row)
    is byte-identical, without storing anything new.

    ``eligible`` is the fail-closed gate on whether an additive-widening ACCEPT may even be considered,
    and ``ineligible_reason`` names why not. It is False for every receipt/plan SHAPE this was not
    reasoned about (E-09) and for a fence-neutering addition (E-08). When it is False the caller must
    behave exactly as it did before this existed.
    """

    added: Tuple[str, ...]
    removed: Tuple[str, ...]
    non_scope_identical: bool
    eligible: bool
    ineligible_reason: str


def scope_entry_is_literal_file(entry: str) -> bool:
    """Is this ``Scope-Paths`` entry a LITERAL FILE PATH (the only widening-eligible shape)?

    E-08, from F-11: a STRICT SUPERSET is not a safe accept condition on its own, because ONE added
    entry can neuter the entire fence. Measured against :func:`_scope_match`: adding ``tests/`` admits
    every file under ``tests/``; adding the bare directory ``agent_workflows`` admits the whole package
    (a literal entry matches by PREFIX, see that function's last line); adding ``*`` admits
    ``tests/test_secret.py``, ``agent_workflows/check_engine.py``, ``RELEASING.md`` and a spec file all
    at once. An agent could therefore convert a four-file fence into a repo-wide one with one added
    entry and one reason string, after which nothing is out of scope and nothing demands a reason. That
    is strictly WORSE than the bug being fixed, because today's refusal at least stops.

    So eligibility mirrors the CLASSIFICATION :func:`_scope_match` branches on, rather than inventing a
    parallel notion of "looks like a file":

    * a trailing ``/`` (``tests/``) is directory-bounded -> NOT eligible;
    * a trailing ``/**`` (``agent_workflows/**``) is directory-bounded -> NOT eligible;
    * any of ``*``, ``?``, ``[`` is a glob (``*``, ``tests/test_*.py``) -> NOT eligible;
    * a BARE DIRECTORY (``agent_workflows``) contains no glob character yet matches by prefix, so it is
      NOT eligible either. This is the case a naive "has no glob char" rule gets wrong, and it is
      checked by the caller (which alone can see the filesystem) via :func:`_entry_is_bare_directory`.

    Everything else is a literal file path and IS eligible. Pure: takes no filesystem.
    """
    e = entry.strip().replace("\\", "/")
    if not e:
        return False
    if e.endswith("/") or e.endswith("/**"):
        return False
    if any(ch in e for ch in "*?["):
        return False
    return True


def _entry_is_bare_directory(repo_root: Optional[Path], entry: str) -> bool:
    """Does ``entry`` name an existing DIRECTORY, so ``_scope_match`` would admit the tree under it?

    Separated from :func:`scope_entry_is_literal_file` because it is the one part of the eligibility
    question that needs the filesystem, and the pure classifier must stay unit-testable without one.
    Fails CLOSED in the direction that matters: with no ``repo_root`` to consult, an entry that cannot
    be checked is NOT treated as a directory here, because the pure classifier has already rejected
    every SHAPE that is directory-bounded without a filesystem (``tests/``, ``agent_workflows/**``,
    globs); this only catches a bare name that HAPPENS to be a directory on disk.
    """
    if repo_root is None:
        return False
    e = entry.strip().replace("\\", "/")
    if not e:
        return False
    try:
        return (Path(repo_root) / e).is_dir()
    except OSError:
        return False


def frozen_region_comparison(
    receipt: Dict[str, Any],
    plan_text: str,
    *,
    repo_root: Optional[Path] = None,
) -> FrozenRegionComparison:
    """Decompose a frozen-region MISMATCH into scope delta + "did anything else change?" (E-03).

    PURE apart from the optional directory probe: takes the receipt dict and the plan TEXT, so it is
    unit-testable with no git fixture. ``repo_root`` is used ONLY by
    :func:`_entry_is_bare_directory` and may be omitted.

    THE SUBSTITUTION TEST, and why it needs no new receipt state. ``begin`` already writes the frozen
    ``scope_paths`` VERBATIM beside the digest, and ``finalize_precheck`` already reads that field. So
    take the CURRENT plan text, replace its scope with the RECEIPT's stored scope, re-serialize with
    :func:`_frozen_region_payload` (the SAME builder :func:`frozen_region_digest` uses, never a second
    copy), and compare to the stored digest. Equality proves every non-scope category is byte-identical.
    Verified against all three measured incidents: the substitution reproduces the stored digest for
    `i3d6ml`, `tx6q0h` and `sy7uwh`, while a control that also rewrites an E-item's action text does not.

    THE THREE INELIGIBLE SHAPES (E-09), each fail-closed and each named in ``ineligible_reason``:

    (a) A LEGACY v1 receipt carries no ``frozen_region_digest`` and is deliberately bound to the
        whole-file rule, which must "not be spuriously ACCEPTED by a rule it was never bound under".
        The substitution is not even ATTEMPTED on it.
    (b) A GRANDFATHERED plan has ``_frozen_scope_paths() == []`` while ``requirements["scope"]`` is
        ``["grandfathered", <the free-form Scope prose>]``, so the two scope inputs are NOT the same
        field. "Adding a path" there is not a widening of an allowlist, it is a CONVERSION from
        no-fence to fence, i.e. a changed scope MODEL rather than an extended one.
    (c) The MIRROR of (b): a plan that BECOMES grandfathered mid-execution empties the allowlist. That
        must read as a REMOVAL, never as an unchanged empty set.

    AND THE FENCE-NEUTERING CASE (E-08): if any ADDED entry is a directory or a glob, the comparison is
    ineligible, so the caller refuses with today's message. See :func:`scope_entry_is_literal_file`.

    A REMOVAL is reported but never eligible-by-itself (E-05): a contract REDUCTION can retroactively
    make an already-made edit out-of-scope and is how a plan could be quietly re-fenced around whatever
    it happened to touch. The caller's accept condition therefore also demands ``not removed``.
    """
    stored_digest = receipt.get("frozen_region_digest")
    if stored_digest is None:
        # (a) legacy v1: bound to the whole-file rule. Do NOT run the substitution at all.
        return FrozenRegionComparison(
            (),
            (),
            False,
            False,
            "legacy v1 receipt (no frozen_region_digest): bound to the whole-file rule",
        )

    stored_scope = list(receipt.get("scope_paths") or [])
    current_scope = _frozen_scope_paths(plan_text)
    current_is_grandfathered = _plan_is_grandfathered(plan_text)

    added = tuple(sorted(set(current_scope) - set(stored_scope)))
    removed = tuple(sorted(set(stored_scope) - set(current_scope)))

    if current_is_grandfathered:
        # (c) the plan BECAME grandfathered: the allowlist is gone. `_frozen_scope_paths` returns []
        #     for a grandfathered plan, so `removed` above already names every previously declared
        #     path; report that rather than an unchanged empty set, and refuse.
        return FrozenRegionComparison(
            (),
            tuple(sorted(stored_scope)),
            False,
            False,
            "the plan BECAME grandfathered mid-execution: its declared allowlist was emptied, "
            "which is a scope REMOVAL and a changed scope model",
        )
    if not stored_scope and added:
        # (b) the receipt was issued for a plan with NO machine allowlist (grandfathered or absent).
        #     Declaring paths now CONVERTS the scope model rather than extending an allowlist.
        return FrozenRegionComparison(
            added,
            removed,
            False,
            False,
            "the receipt was issued for a plan with no declared allowlist (grandfathered/absent): "
            "declaring paths now CHANGES the scope model rather than widening it",
        )

    # The substitution test: does anything OTHER than scope differ?
    substituted = json.dumps(
        _frozen_region_payload(plan_text, scope_paths_override=stored_scope),
        sort_keys=True,
        ensure_ascii=True,
    )
    non_scope_identical = (
        hashlib.sha256(substituted.encode("utf-8")).hexdigest() == stored_digest
    )

    ineligible: List[str] = []
    for entry in added:
        if not scope_entry_is_literal_file(entry):
            ineligible.append(entry)
        elif _entry_is_bare_directory(repo_root, entry):
            ineligible.append(entry)
    if ineligible:
        return FrozenRegionComparison(
            added,
            removed,
            non_scope_identical,
            False,
            "added Scope-Paths entr"
            + ("ies" if len(ineligible) > 1 else "y")
            + " would widen the fence to a DIRECTORY or GLOB rather than a literal file: "
            + ", ".join(ineligible),
        )

    return FrozenRegionComparison(added, removed, non_scope_identical, True, "")


def _plan_is_grandfathered(text: str) -> bool:
    """True when the plan's ``Scope-Paths`` is exactly the reserved ``grandfathered`` sentinel.

    Needed because :func:`_frozen_scope_paths` returns ``[]`` for BOTH a grandfathered plan and a plan
    with no ``Scope-Paths`` field at all, and the widening comparison must tell those apart from a plan
    that genuinely declares nothing.
    """
    from agent_workflows import ipd_lint as _lint
    from agent_workflows import ipd_schema as _schema

    doc = _lint.parse(text)
    sp_value = doc.meta_fields.get(_schema.META_SCOPE_PATHS)
    if not sp_value:
        return False
    _paths, is_grandfathered, _errs = _schema.parse_scope_paths(sp_value)
    return bool(is_grandfathered)


def widening_is_acceptable(cmp_result: FrozenRegionComparison) -> bool:
    """THE accept condition, stated in ONE place so no caller can paraphrase it loosely.

    An additive widening is acceptable iff ALL of:

    * ``eligible`` - the receipt/plan shape was reasoned about and no added entry neuters the fence;
    * ``non_scope_identical`` - the substitution test proved nothing but scope changed;
    * ``not removed`` - no contract REDUCTION, including inside a mixed add-and-remove (E-05); and
    * ``added`` - there IS something added, so this never excuses a mismatch with no scope delta.

    A reason per added path is demanded SEPARATELY, by the finalize path, because this predicate is pure
    and knows nothing about the supplied ``--scope-reason`` map.
    """
    return bool(
        cmp_result.eligible
        and cmp_result.non_scope_identical
        and not cmp_result.removed
        and cmp_result.added
    )


# --------------------------------------------------------------------------------------
# The begin transaction
# --------------------------------------------------------------------------------------


def _baseline_ambiguity(
    repo_root: Path,
    scope_paths: List[str],
    *,
    isolated_baseline: bool = False,
) -> str:
    """Is this plan's frozen ``scope_paths`` content AMBIGUOUS in the baseline the turn will use?

    Returns the same three-way vocabulary as :func:`run_evidence.dirty_within` so ``begin``'s ordered
    checks are unchanged: ``"clean"``, ``"unversioned"`` (fail-closed), or a ``\\n``-joined list of the
    offending in-scope paths.

    Two baselines, selected by the CALLER because only the caller knows where the turn will run
    (lanetruth-02, z2isfg):

      * ``isolated_baseline=False`` - the turn executes in THIS working tree, so the tree is the
        baseline and its in-scope uncommitted state is the ambiguity. This delegates to ``dirty_within``
        against ``repo_root`` exactly as ``begin`` always has.
      * ``isolated_baseline=True`` - the turn executes in a FRESH worktree cut at this repository's
        current commit (``worktree_lease.allocate_worktree`` runs ``git worktree add -b <branch> <path>
        <base_sha>``), whose tracked content therefore IS that commit. Uncommitted work in THIS tree
        cannot reach that lane and so cannot make its baseline ambiguous; measuring it would withhold
        authority over state the turn will never see. What CAN make a commit-shaped baseline ambiguous
        is the commit itself being unreadable, so that is what is measured. Git is still consulted (a
        non-repo still fails closed as ``unversioned``); this is a different measurement, not a skipped
        one.

    Note the asymmetry is deliberate and narrow: an isolated turn is NOT exempted from scope
    discipline. Its writes are still reconciled against the frozen ``scope_paths`` by ``finalize``, and
    an intervening commit touching an in-scope path is still refused there.
    """
    from agent_workflows.run_evidence import dirty_within

    if not isolated_baseline:
        return dirty_within(str(repo_root), scope_paths, _scope_match)
    if not scope_paths:
        return "clean"
    # Fail closed identically to dirty_within when git cannot speak for this tree: without a readable
    # commit there is no frozen base to cut a lane from, so the baseline IS ambiguous.
    rc, _out, _err = _git(repo_root, ["rev-parse", "--verify", "HEAD"])
    if rc != 0:
        return "unversioned"
    return "clean"


def begin(
    repo_root: Path,
    plan_path: Path,
    actor: str,
    *,
    timestamp: str,
    isolated_baseline: bool = False,
) -> BeginResult:
    """Run the fail-closed pre-execution gate and, on success, write the atomic begin receipt.

    Ordered fail-closed checks (each leaves NO valid receipt on failure):
      1. ``--actor`` is present and non-empty;
      2. the plan file exists and parses to a valid ``- Id:`` id6;
      3. the ``pre-execution`` lint disposition is ``conforming`` (else exit 1; an unrunnable lint or
         internal error is exit 2);
      4. the base HEAD is versioned and unambiguous (an unversioned/absent HEAD is refused);
      5. the plan requirements + ``Scope-Paths`` freeze successfully;
      6. the baseline is clean WITHIN this plan's frozen ``Scope-Paths`` (path-overlap rule,
         ipdgates-03 OQ-01): an uncommitted change to an in-scope path is refused, while disjoint
         uncommitted work elsewhere is IGNORED so a concurrent multi-agent workflow is not thrashed.
         The finalize scope reconciliation remains the enforcement point for the out-of-scope changes
         THIS execution owns (scopeattrib Order 01 aligned it with this same disjoint-unowned rule).
    Only when all pass is the receipt built and written atomically. Steps 5 and 6 are ordered so the
    baseline check can scope itself to the frozen ``Scope-Paths``.

    ``isolated_baseline`` (lanetruth-02, z2isfg) selects WHICH BASELINE step 6 measures, separating
    "where the receipt lives" from "what the turn will actually execute against":

      * ``False`` (the default, and every non-isolated turn): the caller's own WORKING TREE at
        ``repo_root`` is the execution tree, so its in-scope uncommitted state genuinely does make the
        frozen base ambiguous and is refused, exactly as before. Behavior is unchanged.
      * ``True``: the caller declares the turn will execute in a FRESH worktree cut at the frozen base
        COMMIT (``git worktree add -b <branch> <path> <base_sha>``), not in this working tree. Such a
        tree's tracked content IS that commit and is clean by construction, so uncommitted work in
        THIS tree cannot make that baseline ambiguous and must not withhold execution authority. The
        commit-shaped baseline is measured instead (see :func:`_baseline_ambiguity`), which is a real
        measurement rather than a skipped check.

    ``isolated_baseline`` deliberately does NOT influence ``base_head``. The receipt's ``base_head`` is
    always captured from ``repo_root`` because finalize consumes it as a GIT REVISION
    (``_paths_changed_by_this_execution`` diffs ``base..HEAD``, and ``_intervening_commits_touching``
    re-diffs the same range); a lane's HEAD is not this tree's HEAD and is not even its ancestor, so
    sourcing both from one "execution tree" would silently corrupt the finalize delta.
    """
    from agent_workflows import ipd_lint as _lint
    from agent_workflows import ipd_schema as _schema
    from agent_workflows import run_freeze
    from agent_workflows.run_evidence import get_git_head

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

    # 4. unambiguous, versioned base HEAD.
    head = get_git_head(str(repo_root))
    if head == "unversioned":
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            rcpt_path,
            "cannot capture a base HEAD (not a git repo, or git unavailable); baseline is "
            "ambiguous, refusing to issue a receipt.",
        )

    # 5. freeze requirements + Scope-Paths (BEFORE the baseline check, which scopes to these paths).
    try:
        frozen = run_freeze.freeze_requirements(_requirements_from_plan(plan_text))
    except ValueError as exc:
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            rcpt_path,
            f"cannot freeze the plan's requirements/scope: {exc}",
        )

    # 6. baseline clean WITHIN this plan's frozen Scope-Paths (path-overlap rule, ipdgates-03 OQ-01).
    #    Disjoint uncommitted work elsewhere is intentionally ignored so a concurrent multi-agent
    #    workflow is not thrashed. Finalize's scope reconciliation still catches the out-of-scope
    #    changes THIS EXECUTION made (its commits since the frozen base, plus dirty paths it can be
    #    shown to own); since scopeattrib Order 01 it no longer demands a reason for a disjoint
    #    UNOWNED dirty path, which is exactly the rule applied here, so the two gates now agree.
    #    WHICH baseline is measured depends on `isolated_baseline` (lanetruth-02, z2isfg): this tree
    #    when the turn will execute here, the frozen base COMMIT when it will execute in a fresh lane.
    scope_paths = _frozen_scope_paths(plan_text)
    in_scope_dirty = _baseline_ambiguity(
        repo_root, scope_paths, isolated_baseline=isolated_baseline
    )
    if in_scope_dirty == "unversioned":
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            rcpt_path,
            "cannot read the worktree status (not a git repo, or git unavailable); baseline is "
            "ambiguous, refusing to issue a receipt.",
        )
    if in_scope_dirty != "clean":
        offending = in_scope_dirty.replace("\n", ", ")
        measured = (
            "the frozen base commit this turn will execute against"
            if isolated_baseline
            else f"the working tree at {repo_root}"
        )
        return BeginResult(
            EXIT_CANNOT_RUN,
            None,
            rcpt_path,
            "refusing to begin: uncommitted changes to paths INSIDE this plan's Scope-Paths make "
            f"the frozen base ambiguous: {offending}. Measured baseline: {measured}. If those "
            "changes are YOURS, land or set them aside and re-run `aw ipd begin`. If they belong to "
            "another agent or human sharing this checkout, do NOT touch their work: either re-run "
            "this plan under worktree isolation, so the turn executes against a clean frozen base, "
            "or wait for the owning party to land it. (Uncommitted work on paths OUTSIDE this "
            "plan's Scope-Paths is allowed and does not block begin.)",
        )

    receipt: Dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "kind": "ipd_begin_receipt",
        "plan_id": plan_id,
        "plan_path": _repo_relative(repo_root, plan_path),
        # Retained for readers/tests and for the legacy fallback, but NO LONGER the validity key.
        "plan_content_digest": plan_content_digest(plan_text),
        # The validity key as of schema v2 (wtiso-03 E-02, fixing xmqv5l): the frozen
        # requirements+scope contract, which a correct self-execution does not change.
        "frozen_region_digest": frozen_region_digest(plan_text),
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
    """Run a git command in ``repo_root``; return (returncode, stdout, stderr).

    Delegates to the single canonical git-subprocess runner in ``git_commit_helper`` (the shared
    "commit-what-I-changed" leaf) so there is exactly one git wrapper across the codebase.
    """
    from .git_commit_helper import _git as _shared_git

    return _shared_git(repo_root, args)


class ChangedPathSources(NamedTuple):
    """The two SOURCES of "paths this execution changed", kept apart by OWNERSHIP EVIDENCE.

    They are not interchangeable, which is why they are no longer collapsed at the point of
    collection (scopeattrib Order 01, lbgzxg E-01):

    * ``committed`` - `git diff --name-only <base>..HEAD`. A commit EXISTS for each of these paths,
      so the change is durably attributable (to *someone*: see the honest bound below).
    * ``working_tree`` - `git status --porcelain` (staged + unstaged + untracked). Carries NO
      author at all. In a SHARED checkout a concurrent agent's dirty file is indistinguishable
      from this execution's own, which is the whole defect scopeattrib Order 01 fixes.

    HONEST BOUND: ``committed`` is attributable to a COMMIT, not to an AGENT. Every agent in a
    shared checkout may commit under one git identity, so this split does NOT let finalize tell a
    co-worker's commit from its own.

    WHAT SCOPEATTR `h9cn0y` DID ABOUT THAT BOUND, since Order 01 left it open (backlog `a8eufb`): it
    does not lift it, and no honest reading of git can. Instead it uses the one thing a commit DOES
    record, the COMMIT BOUNDARY, to decide whether a committed path belongs to this execution's work
    (see :func:`_execution_cohesive_committed_paths`). That is a heuristic with a stated cost, not the
    proof a commit trailer would give, so `a8eufb` remains the real fix.
    """

    committed: Tuple[str, ...]
    working_tree: Tuple[str, ...]

    def union(self) -> List[str]:
        """The sorted union - byte-identical to the pre-split ``_paths_changed_by_this_execution``."""
        return sorted(set(self.committed) | set(self.working_tree))


def _changed_path_sources(repo_root: Path, base_head: str) -> ChangedPathSources:
    """Collect the committed and working-tree change sources SEPARATELY (no union here).

    Asks git for exactly what the pre-split implementation asked for; only the shape of the result
    changes. See :class:`ChangedPathSources` for why the two halves must stay distinguishable.
    """
    committed: set = set()
    rc, out, _err = _git(repo_root, ["diff", "--name-only", f"{base_head}..HEAD"])
    if rc == 0:
        committed.update(ln.strip() for ln in out.splitlines() if ln.strip())
    working_tree: set = set()
    rc, out, _err = _git(repo_root, ["status", "--porcelain"])
    if rc == 0:
        for ln in out.splitlines():
            # porcelain: 'XY <path>' or 'XY <old> -> <new>' for renames.
            body = ln[3:] if len(ln) > 3 else ln.strip()
            if " -> " in body:
                body = body.split(" -> ", 1)[1]
            p = body.strip().strip('"')
            if p:
                working_tree.add(p)
    return ChangedPathSources(tuple(sorted(committed)), tuple(sorted(working_tree)))


def _paths_changed_by_this_execution(repo_root: Path, base_head: str) -> List[str]:
    """Repo-relative paths this execution changed: committed since base + current working tree.

    Union of `git diff --name-only <base>..HEAD` (commits made since the frozen base) and
    `git status --porcelain` (staged + unstaged + untracked working-tree changes). This is the set
    of paths the CURRENT worktree presents relative to the frozen base.

    IT IS A TIME WINDOW, NOT AN ATTRIBUTION, and callers must not read it as one. In a shared
    checkout the range ``base..HEAD`` also contains every concurrent agent's commit, and the porcelain
    also contains their dirty files, so this set OVERSTATES what this execution produced. It said so
    itself before scopeattr `h9cn0y` ("unrelated concurrent commits on disjoint paths are handled by
    the intervening-commit collision check, not here"), and that concession was the defect: MEASURED
    2026-09-07, finalizing `mm6wuz` demanded ten scope reasons of which eight were other agents'
    commits. Attribution now happens where the two halves are still distinguishable, using
    :func:`_changed_path_sources` plus :func:`_working_tree_path_is_owned` and
    :func:`_execution_cohesive_committed_paths`.

    Kept as the UNION-returning surface, unchanged in SHAPE and in VALUE, so every existing caller
    (notably ``check_engine.check_scope_drift``, which wants the broad time window and is deliberately
    NOT ownership-filtered) is unaffected. Callers that must distinguish the two halves by ownership
    evidence use :func:`_changed_path_sources` instead.
    """
    return _changed_path_sources(repo_root, base_head).union()


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


class CommittedAttribution(NamedTuple):
    """What COMMIT COHESION could establish about the committed half. See the helper below.

    ``anchored`` is the FAIL-CLOSED switch and is the reason this is a pair rather than a bare set. It
    is True only when at least one commit in ``base..HEAD`` touched a declared path, i.e. when this
    execution has a recognizable commit footprint at all. When it is False the caller must NOT filter
    the committed half: an empty ``paths`` would otherwise mean "nothing is owned", which would excuse
    EVERY committed path on no evidence whatsoever, the exact inversion of what this is for.
    """

    anchored: bool
    paths: FrozenSet[str]


def _run_record_committed_paths(
    repo_root: Path, id6: str, base_head: str
) -> CommittedAttribution:
    """Committed paths attributable to THIS execution by its RUN RECORD's exact SHAs (`gys47u` E-01).

    THE EVIDENCE COHESION LACKS. :func:`_execution_cohesive_committed_paths` infers ownership from the
    commit BOUNDARY, because it has no channel naming this execution's commits. But the driver ALREADY
    WRITES exactly that: each run's ``outcomes/<pos>-<id6>.json`` carries ``commits[]`` for that item.
    Reading it turns a heuristic into an exact answer for any tree that has a run corpus.

    MEASURED 2026-09-14, the incident that motivated this. Ten lanes stranded by an unrelated red test
    were recovered into `main` in one pass. Finalizing `8tgg6g` (declaring its plan file,
    ``agent_workflows/runner_shared.py`` and ``tests/test_orchestrator_probe_cache.py``) demanded ~19
    ``--scope-reason`` answers, because FIVE non-merge commits in range touched the shared hot file
    ``runner_shared.py`` and FOUR of them belong to other plans (`zexed1`, `3i0aaz`, `51vw4y`,
    `b7xarm`). Cohesion therefore attributed all four foreign commits' full path sets to `8tgg6g`.
    Answering that demand would have written into `8tgg6g`'s PERMANENT finalize record a claim that it
    deliberately edited ``cli.py`` and ``run_viewer.py``, which it never touched. This function reduces
    that same case to the three paths that are genuinely its own.

    WHY THE RUN CORPUS IS REACHABLE AT ALL, since it is gitignored: :func:`checkout_control_root`
    resolves a linked worktree (a driver "lane") to the MAIN worktree's ``.aw`` (backlog ``dh0uno``),
    so an in-lane finalize reads the same records the driver wrote. This adds no new state location and
    uses the accessor `8tgg6g`'s probe store already uses.

    TWO FILTERS, both load-bearing, neither cosmetic:

    * ANCESTOR OF HEAD. A run record may name a SHA from an abandoned or unmerged lane attempt
      (measured: `mm5p3v` records SEVEN SHAs across two attempts). An abandoned attempt must not be
      able to launder a path into "owned", so a SHA that is not an ancestor of HEAD contributes
      nothing.
    * INSIDE ``base_head..HEAD``. Attribution answers a question about THIS execution's window. A SHA
      predating the frozen base is already in the baseline and is not part of what finalize is
      reconciling.

    FAIL-CLOSED, PRESERVING :class:`CommittedAttribution`'s inversion-guard EXACTLY. ``anchored`` is
    True only when at least one qualifying SHA was found. A missing corpus (fresh clone, CI, a tree
    that never ran a driver), an unreadable or malformed record, or a record naming zero commits for
    this ``id6`` all return ``anchored=False``, which makes the caller fall through to cohesion rather
    than treat an empty set as "nothing is owned". That distinction is the whole reason this returns a
    pair: a bare empty set would excuse EVERY committed path on absent evidence, the precise inversion
    of the gate's purpose.

    HONEST LIMIT (`gys47u` OQ-02). The run record is locally writable, so this is not tamper-proof
    provenance. That is acceptable HERE and only because this gate is already explicitly "a
    deterministic consistency check, NOT a tamper-proof authority boundary" (see the derived-status
    note above), and because the failure mode is ASYMMETRIC: a corrupted record can only cause a
    MISSING demand for a path the plan did commit, which is the same false EXCUSE cohesion already
    accepts and documents, never a false CLAIM written into permanent history. Non-forgeable
    attribution stays the deferred item it already is (commit trailers, backlog ``a8eufb``, whose
    WRITER is plan ``wao266``; when those land they become a third and better source ahead of this one).
    """
    if not id6:
        return CommittedAttribution(False, frozenset())
    runs_root = checkout_control_root(repo_root) / "records" / "runs"
    if not runs_root.is_dir():
        return CommittedAttribution(False, frozenset())

    # Collect every SHA any run recorded for THIS item. A plan can legitimately appear in several runs
    # (a re-dispatch, a resume, a retried attempt), so this is a union across the corpus rather than a
    # single lookup, and the two filters below are what keep that union honest.
    shas: Set[str] = set()
    try:
        outcome_files = sorted(runs_root.glob("*/outcomes/*.json"))
    except OSError:
        return CommittedAttribution(False, frozenset())
    for path in outcome_files:
        # Cheap name filter first: the file is `<position>-<id6>.json`, so a corpus of hundreds is
        # narrowed without parsing JSON for every entry.
        if not path.stem.endswith(f"-{id6}"):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            # A single malformed record must not deny attribution that other records can still supply.
            continue
        if not isinstance(payload, Mapping) or str(payload.get("id6") or "") != id6:
            continue
        for entry in payload.get("commits") or ():
            # BOTH SHAPES ARE REAL in the shipped corpus: some records write a bare string (sometimes
            # "<sha> <subject>"), others a mapping. Measured across the 2026-09-14 runs. Reading only
            # one shape would silently attribute nothing for half the corpus.
            if isinstance(entry, Mapping):
                raw = entry.get("sha") or entry.get("commit") or ""
            else:
                raw = str(entry or "").strip().split(" ", 1)[0]
            token = str(raw or "").strip()
            if token:
                shas.add(token)
    if not shas:
        return CommittedAttribution(False, frozenset())

    owned: Set[str] = set()
    anchored = False
    for sha in sorted(shas):
        # FILTER 1: must be an ancestor of HEAD (it actually landed on this branch).
        rc, _out, _err = _git(repo_root, ["merge-base", "--is-ancestor", sha, "HEAD"])
        if rc != 0:
            continue
        # FILTER 2: must be inside this execution's WINDOW, i.e. reachable from HEAD but NOT already
        # in the frozen baseline. Expressed as "not an ancestor of base_head", which combined with
        # FILTER 1 is exactly membership of `base_head..HEAD`.
        #
        # DO NOT "SIMPLIFY" THIS TO `rev-list -1 base..HEAD <sha>`. That was the first implementation
        # and it is WRONG: a trailing revision argument is an additional START-POINT for the walk, not
        # a filter, so it prints a commit for a PRE-BASE sha and silently admits paths from before the
        # window. Caught by `test_a_sha_predating_the_frozen_base_contributes_nothing`, which is why
        # that test exists.
        rc, _out, _err = _git(
            repo_root, ["merge-base", "--is-ancestor", sha, base_head]
        )
        if rc == 0:
            continue
        rc, out, _err = _git(
            repo_root, ["show", "--no-merges", "--format=", "--name-only", sha]
        )
        if rc != 0:
            continue
        anchored = True
        owned.update(ln.strip() for ln in out.splitlines() if ln.strip())
    # `anchored` is True when a qualifying commit was READ, even if it listed no files (a merge or an
    # empty commit), because "this execution's commit footprint was found" is the question. Returning
    # False there would fall back to cohesion and re-admit the foreign paths.
    return CommittedAttribution(anchored, frozenset(owned))


def _execution_cohesive_committed_paths(
    repo_root: Path, base_head: str, scope_paths: Sequence[str]
) -> CommittedAttribution:
    """Committed paths attributable to THIS execution by COMMIT COHESION (scopeattr `h9cn0y` E-02).

    THE PROBLEM THIS SOLVES, and why the obvious answers are all unavailable. A committed path in
    ``base..HEAD`` may belong to this execution or to a co-worker who committed to the same tree, and
    finalize has no channel that says which:

    * git AUTHORSHIP cannot partition actors here, because every agent commits under the maintainer's
      identity (measured: identical ``%an``/``%ae`` across the incident's own and foreign commits);
    * the RUN RECORD (``last_outcome.commits[].sha``) is unreachable, being gitignored, absent from a
      lane worktree, and never handed a run id by finalize; and
    * COMMIT TRAILERS (``AW-Run:``/``AW-Item:``) would settle it exactly, but essentially no commit in
      history carries one yet, so nothing can be consumed today (backlog ``a8eufb``).

    WHAT GIT DOES RECORD is the COMMIT BOUNDARY, and that is enough to be useful. A commit is one
    atomic act by one actor, so the paths inside it share an author whoever that author was. This
    execution DECLARED its territory in the frozen ``Scope-Paths``, so a commit that touched a
    declared path is this execution's commit, and every path in that commit is therefore attributable
    to it, including the ones outside the fence. Those are exactly the paths a ``--scope-reason``
    should be demanded for. A commit that touched NO declared path is not this execution's, and its
    paths are not this plan's to justify.

    So this returns the union of the paths of every ANCHORED commit in ``base..HEAD``: anchored
    meaning it touched at least one path matching ``scope_paths``. Merges are excluded
    (``--no-merges``): a merge's name-only listing is not a single actor's edit.

    ACCEPTED COST, stated because it is real and is the reason the fail-closed tests matter. Cohesion
    is a HEURISTIC, not proof of authorship, and it errs in both directions. A co-worker who touches
    one of this plan's declared paths in the same commit as unrelated files makes those files look
    like this plan's (a false DEMAND, which is fail-closed and merely annoying). An executor who
    commits an out-of-scope path in a commit containing NO declared path escapes the reason
    requirement (a false EXCUSE, and the genuine weakening). The mitigation is the execution
    contract's path-scoped commits, which keep a plan's work in commits anchored by its declared
    paths. This is the same shape of trade the working-tree half already accepted and documented.

    FAIL-CLOSED WHEN THERE IS NO FOOTPRINT, which is why the result carries ``anchored`` alongside the
    paths. If NO commit in the range touched a declared path, this execution has no recognizable commit
    footprint and cohesion knows NOTHING; the caller must then leave the committed half unfiltered.
    Returning a bare empty set here would read as "nothing is owned" and excuse every committed path on
    no evidence at all. MEASURED: without this switch, a plan whose ONLY commit was out-of-scope (the
    ``p7dqwz`` counterexample, ``tests/test_ipd_lifecycle_cli.py``) stopped being refused, which is the
    precise inversion of the gate's purpose. The same applies when there is no fence (a grandfathered
    plan has nothing to anchor to) or when git fails.
    """
    if not scope_paths:
        return CommittedAttribution(False, frozenset())
    rc, out, _err = _git(
        repo_root,
        ["log", "--no-merges", "--format=%H", "--name-only", f"{base_head}..HEAD"],
    )
    if rc != 0:
        return CommittedAttribution(False, frozenset())

    cohesive: Set[str] = set()
    current: List[str] = []

    def _flush(paths: List[str]) -> None:
        if paths and any(_scope_match(p, pat) for p in paths for pat in scope_paths):
            cohesive.update(paths)

    for raw in out.splitlines():
        line = raw.strip()
        if not line:
            continue
        # A 40-char hex line is a commit header (`--format=%H`), not a path; a path never looks like
        # one, because git prints paths relative to the repo root and they always carry an extension
        # or a separator in practice. Checked structurally rather than by position so a commit with
        # NO files (possible with `--name-only`) does not desynchronize the grouping.
        if len(line) == 40 and all(c in "0123456789abcdef" for c in line):
            _flush(current)
            current = []
            continue
        current.append(line)
    _flush(current)
    # `anchored` is exactly "at least one commit touched declared territory", which is what a non-empty
    # cohesive set means: `_flush` only ever adds paths from an anchored commit.
    return CommittedAttribution(bool(cohesive), frozenset(cohesive))


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


def _working_tree_path_is_owned(
    path: str,
    *,
    scope_paths: List[str],
    committed: Sequence[str],
    plan_rel: str,
    cohesive_committed: Optional[Collection[str]] = None,
) -> bool:
    """Is this changed path attributable to THIS execution? (Order 01 E-02; scopeattr `h9cn0y` E-02.)

    NOW JUDGES BOTH HALVES, so the name is a historical misnomer kept deliberately: it is asserted as
    a source substring by the ownership test-suite and renaming it would churn a proven surface for
    cosmetics. Read it as "path is owned", not "working-tree path is owned".

    Neither change source carries an author that finalize can use. A ``git status --porcelain`` entry
    has none at all, and a COMMIT has one that does not discriminate, because every agent in this
    repository commits under the maintainer's identity. So ownership is inferred from POSITIVE
    EVIDENCE in both halves. This execution OWNS a path when any of the following holds:

    * it matches the plan's frozen ``Scope-Paths`` (the plan declared this territory);
    * it also appears in the COMMITTED half (this execution already committed that path, so a dirty
      entry is a further edit of its own work). This clause is why a caller judging the COMMITTED
      half must NOT pass that half as ``committed``: doing so is a tautology that would excuse every
      committed path. Such a caller passes ``committed=()`` and supplies ``cohesive_committed``;
    * it is COHESIVE with this execution's commits, i.e. it shares a commit with a declared path (see
      :func:`_execution_cohesive_committed_paths`); or
    * it is an implicit lifecycle allowance (the plan file, the plans index).

    A path matching NONE of those is UNOWNED: in a shared checkout it is almost certainly a concurrent
    agent's work, and demanding a ``--scope-reason`` for it would force this plan to either write a
    false claim into its permanent record or block on a condition it does not control. Note this only
    ever REMOVES paths from the out-of-scope set; it never adds any.

    ACCEPTED COST, in two parts, both mitigated by the same thing and both kept VISIBLE in the
    evidence rather than silently dropped:

    * (Order 01 OQ-01/F3) an executor's OWN uncommitted out-of-scope edit is byte-identical to a
      co-worker's, so it is disregarded too; and
    * (scopeattr `h9cn0y`) an executor's own COMMITTED out-of-scope path escapes the reason
      requirement when it rides in a commit containing no declared path.

    The mitigation for both is the execution contract's path-scoped commits, which keep a plan's real
    work in commits anchored by its declared paths, where the reason requirement still fires. The
    exact fix that would remove the second cost is commit trailers (backlog ``a8eufb``); until those
    exist, this is the strongest attribution available, and it is deliberately weaker than a proof.
    """
    if _is_implicitly_allowed(path, plan_rel):
        return True
    if path in set(committed):
        return True
    if cohesive_committed is not None and path in set(cohesive_committed):
        return True
    return any(_scope_match(path, pat) for pat in scope_paths)


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
    widened_paths: List[str] = []
    if not receipt_is_current(receipt, plan_text):
        # THE ONE MISMATCH CLASS THAT IS A DECLARATION, NOT A CONTRACT REWRITE (rcptwiden `63425h`
        # E-04). The digest is still the fast path and still the authority for "unchanged"; this
        # structural comparison runs ONLY here, after the digest has already said "different", so an
        # unchanged plan costs nothing new. An ADDITIVE widening of `Scope-Paths` whose every other
        # frozen category is byte-identical is the honest declaration of a path the execution turned
        # out to need, and refusing it is what stranded three lanes in run
        # `run-20260917T023628Z-4108757` while the CONCEALED equivalent finalized. Every other
        # mismatch - a removal, a mixed add-and-remove, a rewritten requirement, a directory/glob
        # addition, an ineligible receipt shape - still refuses with the identical message below.
        cmp_result = frozen_region_comparison(receipt, plan_text, repo_root=repo_root)
        if not widening_is_acceptable(cmp_result):
            stale_findings: List[str] = [
                "plan content digest no longer matches the receipt"
            ]
            if cmp_result.ineligible_reason:
                stale_findings.append(cmp_result.ineligible_reason)
            if cmp_result.removed:
                # E-05: a contract REDUCTION is named, because it can retroactively make an
                # already-made edit out-of-scope and is how a plan could be quietly re-fenced.
                stale_findings.append(
                    "Scope-Paths entr"
                    + ("ies" if len(cmp_result.removed) > 1 else "y")
                    + " REMOVED since begin (a contract reduction, never accepted as a widening): "
                    + ", ".join(cmp_result.removed)
                )
            if cmp_result.added and not cmp_result.non_scope_identical:
                stale_findings.append(
                    "Scope-Paths gained "
                    + ", ".join(cmp_result.added)
                    + " but a frozen REQUIREMENT also changed, so this is a contract rewrite rather "
                    "than an additive widening"
                )
            return (
                EXIT_FINDINGS,
                f"the begin receipt for {plan_id} is STALE: the plan content changed since begin; "
                "re-run `aw ipd begin`.",
                evidence,
                tuple(stale_findings),
            )
        widened_paths = list(cmp_result.added)
        evidence["frozen_region_widening"] = {
            "accepted": True,
            "added_paths": list(cmp_result.added),
            "non_scope_identical": True,
            "note": (
                "ADDITIVE Scope-Paths widening accepted: every frozen requirement category is "
                "byte-identical and no declared path was removed. Each added path requires its own "
                "--scope-reason (rcptwiden 63425h)."
            ),
        }
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
    sources = _changed_path_sources(repo_root, base_head)
    changed = sources.union()
    evidence["changed_paths"] = changed

    # (a) OUT-OF-SCOPE paths: paths THIS execution changed that are outside Scope-Paths. Order 04
    #     refused these outright; Order 05 (qmt3yk) turns that into two-way RECONCILIATION - a
    #     recorded per-path REASON legitimizes the edit (proceed), an empty/missing reason refuses.
    #     A grandfathered plan (empty literal allowlist) has NO machine path fence, so there is no
    #     out-of-scope set (Order oorry1: grandfathered = advisory); only implicit lifecycle
    #     allowances + free-form scope apply.
    #
    #     ATTRIBUTE BY OWNERSHIP, NOT BY A TIME WINDOW (scopeattrib Order 01 lbgzxg E-02, extended to
    #     the committed half by scopeattr `h9cn0y` E-02). BOTH change sources are now judged by the
    #     SAME ownership predicate, because neither carries an author finalize can use: a porcelain
    #     entry has none, and a commit's author is the maintainer for EVERY agent here. What differs
    #     is the positive evidence each half can offer:
    #       * WORKING-TREE half: owned when the path matches Scope-Paths, appears in the COMMITTED
    #         half, or is an implicit lifecycle allowance. Otherwise DISREGARDED, because in a shared
    #         checkout it belongs to a concurrent agent and this plan can neither honestly justify it
    #         nor wait it out.
    #       * COMMITTED half: owned when the path matches Scope-Paths, is an implicit allowance, or is
    #         COHESIVE with this execution's commits (it shares a commit with a declared path, so the
    #         same atomic act produced both). Otherwise DISREGARDED, for the same reason: demanding a
    #         reason for another agent's commit forces a FALSE claim into this plan's permanent record.
    #         Note `committed=()` for this half deliberately: passing the committed half as its own
    #         ownership evidence is a tautology that would excuse every committed path.
    #     WHY THIS MATTERS BEYOND ANNOYANCE (measured 2026-09-07 finalizing `mm6wuz`): the gate
    #     demanded TEN reasons of which EIGHT were other agents' commits, and those reasons are
    #     written into the plan's permanent finalize evidence, so an executed plan asserted it edited
    #     files it never touched. Cohesion reduces that same case to the TWO genuinely its own.
    #     ACCEPTED COST (the honest bound, see `_working_tree_path_is_owned`): cohesion is a heuristic,
    #     not proof of authorship, so an executor's OWN committed out-of-scope path escapes the reason
    #     requirement when it rides in a commit containing no declared path. The mitigation is
    #     path-scoped commits; the real fix is commit trailers (backlog `a8eufb`).
    #     This is also what makes finalize CONSISTENT with begin, which already ignores disjoint
    #     uncommitted work so a concurrent multi-agent workflow is not thrashed.
    out_of_scope: List[str] = []
    disregarded_unowned: List[str] = []
    if scope_paths:
        committed_set = set(sources.committed)
        # EXACT ATTRIBUTION FIRST, COHESION AS THE FALLBACK (`gys47u` E-02). The run record names this
        # execution's own commits, so when it is available it answers the ownership question outright
        # and cohesion's commit-boundary heuristic is not consulted at all.
        #
        # IT DECIDES ALONE RATHER THAN BEING UNIONED WITH COHESION (`gys47u` OQ-01). A union would
        # re-admit every foreign path the exact source exists to exclude: measured on the 2026-09-14
        # recovery, unioning keeps all ~19 demanded paths for `8tgg6g` while the exact source alone
        # yields its 3. Strictly better evidence must not be diluted by weaker evidence.
        #
        # THE FALL-THROUGH IS THE FAIL-CLOSED DIRECTION, not a convenience: an absent, unreadable, or
        # empty run record leaves `anchored` False and lands on exactly today's behavior, so a tree
        # with no run corpus (fresh clone, CI) is unaffected and no gate is weakened.
        exact = _run_record_committed_paths(repo_root, plan_id, base_head)
        cohesive = (
            exact
            if exact.anchored
            else _execution_cohesive_committed_paths(repo_root, base_head, scope_paths)
        )
        # E-03: record WHICH evidence decided, so a human reading a demanded `--scope-reason` can tell
        # an exact attribution from a heuristic one. A demand backed by cohesion may legitimately name
        # a co-worker's path and is worth a second look; one backed by the run record should not.
        evidence["attribution_source"] = (
            "run-record-exact"
            if exact.anchored
            else ("commit-cohesion" if cohesive.anchored else "none-fail-closed")
        )
        for p in changed:
            if _is_implicitly_allowed(p, plan_rel):
                continue
            if any(_scope_match(p, pat) for pat in scope_paths):
                continue
            if p in committed_set:
                # COMMITTED half: cohesion is the only positive evidence available. `committed=()`
                # avoids the self-referential clause (see the predicate's docstring).
                #
                # FAIL CLOSED WHEN COHESION KNOWS NOTHING. With no anchored commit this execution has
                # no recognizable commit footprint, so treat the committed path exactly as before the
                # fix (owned, therefore reason required) rather than excusing it on absent evidence.
                # This is what keeps a plan whose ONLY commit is out-of-scope refused.
                owned = (
                    _working_tree_path_is_owned(
                        p,
                        scope_paths=scope_paths,
                        committed=(),
                        plan_rel=plan_rel,
                        cohesive_committed=cohesive.paths,
                    )
                    if cohesive.anchored
                    else True
                )
            else:
                owned = _working_tree_path_is_owned(
                    p,
                    scope_paths=scope_paths,
                    committed=sources.committed,
                    plan_rel=plan_rel,
                )
            if not owned:
                # Not attributable to this execution: not this plan's to justify.
                disregarded_unowned.append(p)
                continue
            out_of_scope.append(p)
    # (b') IN-SCOPE-UNMODIFIED paths (Order 05, the MISSING-work direction): a Scope-Paths entry the
    #      execution did NOT touch. Requires the receipt's LITERAL declared Scope-Paths (Order 03/04).
    #      Acknowledge-and-proceed (a declared-but-unneeded file is normal, not a failure).
    in_scope_unmodified: List[str] = []
    if scope_paths:
        for pat in scope_paths:
            if not any(_scope_match(c, pat) for c in changed):
                in_scope_unmodified.append(pat)
    # (b) intervening-commit COMPUTATION: which in-Scope-Paths paths were touched by a commit since
    #     base. Substrate for Order 06's authorship-aware collision enforcement; COMPUTED + surfaced
    #     here (not a blanket refusal, so the normal single-actor begin->commit->finalize flow works).
    collisions = _intervening_commits_touching(repo_root, base_head, scope_paths)
    collisions = [c for c in collisions if not _is_implicitly_allowed(c, plan_rel)]

    evidence["scope_audit"] = {
        "grandfathered": not scope_paths,
        "in_scope": bool(scope_paths) and not out_of_scope,
        "out_of_scope_paths": list(out_of_scope),
        "in_scope_unmodified": list(in_scope_unmodified),
        "intervening_in_scope_commits": collisions,
        # E-03: what the ownership filter DISREGARDED, kept visible rather than silently dropped.
        # Paths this execution cannot be shown to own: a concurrent agent's in-flight work, or (since
        # scopeattr `h9cn0y`) a commit that touched none of this plan's declared paths. They demand no
        # reason, but they stay on the record. ONE key covers BOTH halves deliberately, so the audit
        # trail has a single shape; `committed_paths`/`working_tree_paths` below already say which
        # half any given path came from, so no second key is needed to tell them apart.
        "disregarded_unowned_paths": list(disregarded_unowned),
        "committed_paths": list(sources.committed),
        "working_tree_paths": list(sources.working_tree),
        # rcptwiden `63425h` E-04: the paths this execution ADDED to `Scope-Paths` after begin, under
        # the accepted additive widening. Its OWN key, for two reasons measured rather than assumed.
        # FIRST, the demand cannot ride on `out_of_scope_paths`: this whole audit judges paths against
        # the RECEIPT's frozen fence, so a newly-added path that is only UNCOMMITTED lands in
        # `disregarded_unowned_paths` and `out_of_scope_paths` is EMPTY (measured), which would make a
        # reason requirement expressed through that set silently vacuous. SECOND, the runner reads this
        # key to auto-reason the widening (`runner_shared.compute_scope_reconciliation`), because all
        # three incidents this fixes were finalized by the RUNNER and not by hand.
        "widened_paths": list(widened_paths),
    }
    # The precheck itself no longer REFUSES on out-of-scope paths; that decision now belongs to the
    # two-way reconciliation in `finalize` (Order 05), which legitimizes an out-of-scope edit with a
    # recorded reason and refuses only a MISSING reason. The precheck returns EXIT_OK with the
    # computed two-way delta in evidence so `finalize` can reconcile it.
    msg = "precheck passed (receipt valid, pre-transition conforming; scope delta computed)."
    if disregarded_unowned:
        # OPERATOR-FACING, so it states only what the code can substantiate: that the path is outside
        # this plan's declared Scope-Paths and could not be attributed to this execution. It names NO
        # sha and blames NO actor, because nothing available here identifies who committed a path
        # (every agent commits under one git identity), and asserting otherwise would be a fabricated
        # attribution claim. The word "uncommitted" was dropped when the committed half became
        # filterable too; the wording now holds for both halves.
        msg += (
            " Disregarded "
            + str(len(disregarded_unowned))
            + " path(s) not owned by this execution (no reason required, recorded in "
            "the scope audit): " + ", ".join(disregarded_unowned) + "."
        )
    return (
        EXIT_OK,
        msg,
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


def _pre_commit_phase_leaves_manifests_untouched() -> str:
    """The invariant that lets :func:`_rollback_precommit` restore the manifests by NOT writing them.

    Stated as one named, testable claim rather than left implicit in a comment, because the whole
    correctness of plan `4xt6u4`'s fix rests on it and a future change could silently break it. If the
    pre-commit phase ever starts writing the shared `INDEX.json`/`INDEX.md` again, this claim becomes
    false and a rollback would once more have real damage to repair - at which point the journal
    snapshot that `4xt6u4` OQ-01 considered (`index_json_before`/`index_md_before`) becomes the right
    mechanism after all. The test that pins this is what should fail first in that future.

    THE CLAIM: between `PHASE_PREPARED` and the ff-only merge, nothing writes the SHARED checkout's
    plans manifests. It holds for two independent reasons, both structural:

    * the status edit and the `git mv` happen in a coordinator-owned WORKTREE (`u23gbn`), not the
      shared checkout; and
    * the manifests are GITIGNORED, so a fresh worktree never receives them and any regeneration
      inside one is discarded with the worktree (see :func:`_finalize_transaction`).

    So the only shared-tree manifest write in the transaction is
    :func:`_refresh_plans_index_fail_loud`, and it is called on the SUCCESS path only, deliberately
    AFTER the reconciliation.
    """
    return (
        "the pre-commit phase performs its mutations in a coordinator worktree and the plans "
        "manifests are gitignored, so the SHARED INDEX.json/INDEX.md are untouched until the "
        "post-reconciliation refresh; a rollback therefore restores them by not writing them."
    )


# --------------------------------------------------------------------------------------
# Landing a lifecycle commit made in a coordinator-owned worktree (plan `u23gbn`).
#
# WHAT THIS BUYS AND WHAT IT DOES NOT. The transaction's status edit, plan move and commit happen in a
# throwaway worktree on its own branch, so the SHARED checkout is never mid-move and is never the tree
# `pre-commit` stashes. But a ref that advanced with the shared working tree left behind is WORSE than
# today's window, not better: measured, HEAD then says `executed/` while the tree still holds
# `pending/`, which reads as an unexplained REVERSE rename. So the shared tree must still be brought
# into line, and the honest mechanism is a fast-forward that GIT performs and that REFUSES rather than
# clobbers.
#
# THE FF-ONLY MERGE MUST BE THE THING THAT ADVANCES THE BRANCH. Do not move the ref first and then
# reconcile: measured twice, `git merge --ff-only <landed>` after the ref already points at `<landed>`
# prints "Already up to date." and exits 0 WITHOUT touching the working tree, leaving a staged
# `D `/`A ` pair for the plan's two paths while REPORTING SUCCESS, and git never performs the
# would-be-overwritten check, so the peer-protecting refusal becomes unreachable.
# --------------------------------------------------------------------------------------

#: The shared checkout was fast-forwarded onto the landed commit; the branch advanced.
RECONCILED_OK = "reconciled"
#: Git REFUSED because landing would overwrite a local change (or an untracked squatter) in the shared
#: tree. rc=1, `error:` prefix, tree DIRTY at the objecting path, branch NOT advanced, commit NOT
#: reachable from the branch. The peer's bytes are intact and MUST be left that way.
RECONCILED_REFUSED = "refused-would-overwrite"
#: A peer COMMIT landed on the branch since the worktree's snapshot, so no fast-forward exists. rc=128,
#: `fatal:` prefix, tree typically CLEAN, branch NOT advanced. Same condition `commit_isolated` reports
#: as `ISO_RACED`, so the vocabulary is deliberately reused: the work exists as a reachable commit and
#: the operator retries.
RECONCILED_RACED = "raced"


class ReconcileLanding(NamedTuple):
    """The outcome of landing a worktree commit into the shared checkout by fast-forward.

    ``status`` is one of :data:`RECONCILED_OK`, :data:`RECONCILED_REFUSED`, :data:`RECONCILED_RACED`.
    ``returncode`` is git's OWN exit code, which is how the two failure arms are told apart (1 for the
    would-be-overwritten refusal, 128 for divergence); never string-match git's prose, which differs
    between them and across versions. ``paths`` names what git objected to on the refusal arm.
    """

    status: str
    returncode: int
    detail: str
    paths: Tuple[str, ...] = ()


_MERGE_REFUSAL_MARKERS = (
    "would be overwritten by merge",
    "would be overwritten by checkout",
)


def _parse_merge_refusal_paths(text: str) -> Tuple[str, ...]:
    """The paths git named in a would-be-overwritten refusal (best effort, for the operator).

    Deliberately best-effort and NEVER load-bearing: the ARM is decided by the exit code, and this
    only enriches the message a human reads. Git lists the offending paths one per line, tab-indented,
    between its `error:` line and its `Please ...` advice.
    """
    paths: List[str] = []
    collecting = False
    for line in (text or "").splitlines():
        low = line.lower()
        if any(marker in low for marker in _MERGE_REFUSAL_MARKERS):
            collecting = True
            continue
        if collecting:
            if line.startswith(("\t", "    ")):
                candidate = line.strip()
                if candidate:
                    paths.append(candidate)
                continue
            break
    return tuple(paths)


def _release_own_plan_edit_before_landing(
    repo_root: Path,
    plan_rel: str,
    *,
    landed: str,
    dest_rel: str,
    mirrored_bytes: str,
    committed_bytes: Optional[str],
) -> Optional[str]:
    """Clear the transaction's OWN uncommitted plan edit from the shared tree, or leave it alone.

    WHY THIS IS NECESSARY AND IS NOT A FORCED MERGE. THIS WAS FOUND BY A TEST WRITTEN FOR THIS CHANGE,
    not predicted: an executing agent normally ticks its own `E-*` items and fills its `V-*` evidence
    and has NOT COMMITTED those edits when finalize runs. MEASURED on the pre-change code, finalize
    succeeded and carried those uncommitted bytes into the lifecycle commit. With the mutation moved
    into a coordinator worktree, the shared tree still holds that dirty plan file, so
    `git merge --ff-only` REFUSES ("Your local changes to the following files would be overwritten by
    merge"), and the single most common finalize in the repository would start failing.

    THE DISTINCTION THAT MAKES THIS SAFE, and it is the whole point. The refusal exists to protect
    bytes that would be LOST. Here they cannot be lost, and that is PROVED rather than assumed before
    anything is written:

    * the shared tree's bytes at the plan's original path are EXACTLY the bytes this transaction
      mirrored into its worktree, i.e. the INPUT to the commit that just landed; and
    * the landed commit's blob at the plan's destination path is EXACTLY what the worktree produced
      from those bytes.

    So the content is already durable in a commit, and dropping the working-tree copy at the OLD path
    is precisely what "the plan moved" means. If EITHER check fails the bytes are somebody else's (or
    are not accounted for), and this function writes NOTHING and returns None, leaving
    :func:`land_worktree_commit` to refuse and report - which is exactly the contended arm, and it must
    keep refusing.

    NARROW BY CONSTRUCTION: it touches ONE path, the plan's own original path, and never inspects or
    clears anything else in the tree. A co-worker's unrelated dirty file needs no clearing anyway,
    because a fast-forward that does not write it does not care that it is dirty (measured).

    Returns the operation performed (for the record), or None when nothing was cleared.
    """
    plan_abs = repo_root / plan_rel
    try:
        current = plan_abs.read_text(encoding="utf-8")
    except OSError:
        return None  # absent: nothing of ours to clear, and the merge decides
    if current != mirrored_bytes:
        return None  # somebody else's content: refuse to touch it
    if committed_bytes is None:
        return None
    rc, blob, _err = _git(repo_root, ["show", f"{landed}:{dest_rel}"])
    if rc != 0 or blob != committed_bytes:
        # The landed commit does not demonstrably carry these bytes, so clearing them could lose
        # content. Fail closed: leave the tree alone and let the merge refuse.
        return None
    # THE MINIMAL OPERATION: restore this ONE path to what HEAD already says, which is the state the
    # fast-forward expects to rename FROM. It is not `reset --hard`, not `checkout -f`, and not a
    # forced merge: it is a single path whose current content is provably carried by the commit about
    # to land, so nothing can be lost.
    rc, _out, _err = _git(repo_root, ["checkout", "HEAD", "--", plan_rel])
    if rc == 0:
        return f"released this transaction's own uncommitted edit at {plan_rel}"
    return None


def land_worktree_commit(
    repo_root: Path, landed: str, *, expected_base: Optional[str] = None
) -> ReconcileLanding:
    """Advance the shared checkout onto ``landed`` with a REFUSING fast-forward, and classify.

    THE SINGLE OPERATION, deliberately: `git merge --ff-only <landed>` moves the ref AND updates the
    working tree at once, and it is the operation whose refusal protects a co-worker. Never
    `update-ref` first (see the module comment above), and never resolve a refusal by forcing it
    (`git checkout -f`, `git reset --hard`, or a manual file move): git's refusal is protecting a
    co-worker's uncommitted bytes and destroying them is the exact harm this change exists to stop.

    THE THREE ARMS, each measured rather than inferred:

    * CLEAN (rc=0): "Updating <old>..<new> / Fast-forward". An unrelated peer's dirty or staged file
      is untouched and its bytes are verbatim.
    * REFUSED (rc=1, `error:`): a local change to (or an untracked squatter at) a path the merge would
      write. HEAD is NOT advanced and the working tree keeps the peer's content.
    * RACED (rc=128, `fatal: Not possible to fast-forward`): a peer commit landed since the snapshot,
      so the branch DIVERGED and no fast-forward exists. HEAD is NOT advanced and the tree is clean.

    ``expected_base`` is optional and diagnostic only: when given and the branch has already moved off
    it, the RACED detail says so explicitly instead of leaving the operator to infer it.
    """
    rc, out, err = _git(repo_root, ["merge", "--ff-only", landed])
    combined = f"{out}\n{err}".strip()
    if rc == 0:
        # "Already up to date." means the ref ALREADY pointed at (or past) `landed`, so this call did
        # not land anything and the working tree was not touched. That is the no-op ordering bug, and
        # it must not be reported as a successful reconciliation.
        if "already up to date" in combined.lower():
            return ReconcileLanding(
                RECONCILED_RACED,
                rc,
                (
                    f"the branch already pointed at or past {landed[:12]}, so the fast-forward was a "
                    "NO-OP and the shared working tree was NOT updated. Something advanced the ref "
                    "before this reconciliation ran (a separate `update-ref` is the classic cause); "
                    f"git said: {combined}"
                ),
            )
        return ReconcileLanding(RECONCILED_OK, rc, combined or "fast-forwarded")

    lowered = combined.lower()
    if any(marker in lowered for marker in _MERGE_REFUSAL_MARKERS):
        paths = _parse_merge_refusal_paths(combined)
        named = ", ".join(paths) if paths else "(git named no path)"
        return ReconcileLanding(
            RECONCILED_REFUSED,
            rc,
            (
                f"git REFUSED to fast-forward the shared checkout onto {landed[:12]} because landing "
                f"it would overwrite local changes at: {named}. The branch was NOT advanced and those "
                "bytes are intact; that refusal is CORRECT and must not be forced. Land or set that "
                f"edit aside and re-run. git said: {combined}"
            ),
            paths,
        )

    detail = (
        f"the shared branch could not be fast-forwarded onto {landed[:12]}: it has DIVERGED, so a peer "
        f"commit landed since this transaction's snapshot. The work is preserved as commit "
        f"{landed[:12]} (cherry-pick or retry); the branch was NOT moved. git said: {combined}"
    )
    if expected_base:
        rc_now, now, _e = _git(repo_root, ["rev-parse", "HEAD"])
        current = now.strip() if rc_now == 0 else ""
        if current and current != expected_base:
            detail += f" The branch moved from {expected_base[:12]} to {current[:12]} meanwhile."
    return ReconcileLanding(RECONCILED_RACED, rc, detail)


class ReconcileOutcome(NamedTuple):
    """The result of the two-way scope reconciliation (Order 05, qmt3yk).

    ``ok`` is True when every out-of-scope path has a recorded reason and every in-scope-unmodified
    path has an acknowledgment (so finalize may proceed). ``reasons``/``acks`` are the collected
    answers to write verbatim into the terminal record. ``missing`` lists the unanswered items when
    ``ok`` is False (headless fail-closed). ``needs_input_command`` is the exact re-invocation to
    supply them.
    """

    ok: bool
    reasons: Dict[str, str]
    acks: Dict[str, str]
    missing_reasons: Tuple[str, ...]
    missing_acks: Tuple[str, ...]
    needs_input_command: str


def _reconcile_scope(
    plan_selector: str,
    actor: str,
    message: str,
    out_of_scope: List[str],
    in_scope_unmodified: List[str],
    *,
    scope_reasons: Optional[Dict[str, str]] = None,
    scope_acks: Optional[Dict[str, str]] = None,
    interactive: bool = False,
    prompt=None,
    widened: Optional[Sequence[str]] = None,
) -> ReconcileOutcome:
    """Reconcile the two-way scope delta (Order 05 qmt3yk). SURFACES + ATTRIBUTES; does not judge.

    For each OUT-OF-SCOPE changed path a non-empty REASON is required (recorded -> proceed; empty ->
    refuse). For each IN-SCOPE-UNMODIFIED declared path a one-word ACKNOWLEDGMENT is required
    (acknowledge -> proceed). Answers come from the ``--scope-reason``/``--scope-ack`` flag maps
    (headless) or, on a TTY, from ONE batched ``prompt`` callback. A headless run with a non-empty
    delta and MISSING answers is fail-closed (``ok=False``) and names the exact re-invocation.

    ``widened`` (rcptwiden `63425h` E-04) is the set of paths this execution ADDED to ``Scope-Paths``
    after begin, under the accepted additive widening. Each one requires a reason UNCONDITIONALLY,
    which is a demand this function must make ITSELF rather than inherit from ``out_of_scope``:
    ``finalize_precheck`` judges out-of-scope against the RECEIPT's OLD fence, so an added path that is
    only UNCOMMITTED never enters ``out_of_scope`` at all (measured: ``out_of_scope_paths: []``,
    ``disregarded_unowned_paths: ['tests/test_extra.py']``). Expressing the requirement through that
    set would therefore have shipped the LENIENT form while the plan claimed the strict one.

    IT MUST ALSO NOT DOUBLE-DEMAND. In the COMMITTED-cohesive case the same path DOES appear in
    ``out_of_scope``, so the two demands would otherwise both fire for one path and the terminal record
    would name it twice. The requirement is therefore an ORDERED UNION, keyed by path, so ONE
    ``--scope-reason`` per path satisfies both in either variant.
    """
    reasons: Dict[str, str] = dict(scope_reasons or {})
    acks: Dict[str, str] = dict(scope_acks or {})
    widened_paths: List[str] = list(widened or [])

    # ONE demand per path: every out-of-scope path plus every widened path, order-stable, deduped.
    reason_required: List[str] = list(out_of_scope)
    for p in widened_paths:
        if p not in reason_required:
            reason_required.append(p)

    # Clean delta: nothing to reconcile.
    if not reason_required and not in_scope_unmodified:
        return ReconcileOutcome(True, {}, {}, (), (), "")

    # Interactive: collect any missing answers via ONE batched prompt (TTY).
    if interactive and prompt is not None:
        collected = prompt(list(reason_required), list(in_scope_unmodified))
        # prompt returns ({path: reason}, {path: ack}); empty/None reason means "not given".
        for p, why in (collected.get("reasons") or {}).items():
            if why is not None and str(why).strip():
                reasons[p] = str(why).strip()
        for p, note in (collected.get("acks") or {}).items():
            acks[p] = (
                str(note).strip()
                if note is not None and str(note).strip()
                else "acknowledged"
            )

    missing_reasons = tuple(
        p for p in reason_required if not reasons.get(p, "").strip()
    )
    # An in-scope-unmodified path is acknowledge-and-proceed; a missing ack in headless mode is
    # still surfaced (fail-closed) so the deviation cannot be silently skipped, but any non-empty
    # note (default "not-needed"/"acknowledged") satisfies it.
    #
    # A WIDENED path is NEVER also demanded as an ack. It was added to `Scope-Paths` precisely because
    # the execution needed to touch it, so it is by construction not "declared but unmodified"; and if
    # it somehow were, the widening reason already covers it. Demanding both for one path would make
    # the honest declaration cost two answers where the concealed edit costs none.
    missing_acks = tuple(
        p for p in in_scope_unmodified if p not in acks and p not in set(widened_paths)
    )

    # Build the exact re-invocation to supply the missing answers headlessly.
    parts = [
        f"aw ipd finalize {plan_selector} --actor {actor!r} --message {message!r} --apply"
    ]
    widened_set = set(widened_paths)
    for p in missing_reasons:
        if p in widened_set:
            parts.append(
                f"--scope-reason {p}=<why-this-path-had-to-be-added-to-Scope-Paths>"
            )
        else:
            parts.append(f"--scope-reason {p}=<why-this-out-of-scope-edit-was-needed>")
    for p in missing_acks:
        parts.append(f"--scope-ack {p}[=not-needed]")
    needs_cmd = " ".join(parts)

    ok = not missing_reasons and not missing_acks
    return ReconcileOutcome(ok, reasons, acks, missing_reasons, missing_acks, needs_cmd)


def _reconciliation_history_note(
    reasons: Dict[str, str],
    acks: Dict[str, str],
    widened: Optional[Sequence[str]] = None,
) -> str:
    """Render the reconciliation answers as a compact, verbatim note for the terminal record.

    A path this execution ADDED to ``Scope-Paths`` is labelled ``widened-scope`` rather than
    ``out-of-scope`` (rcptwiden `63425h` E-04), because those are different acts and the permanent
    record should not conflate them: an out-of-scope edit went OUTSIDE the declared fence, while a
    widened path was DECLARED before the finalize that accepted it. Each path appears exactly ONCE
    even when it is both (the committed-cohesive case), so one supplied reason reads as one record.
    """
    widened_set = set(widened or [])
    bits: List[str] = []
    for p in sorted(reasons):
        label = "widened-scope" if p in widened_set else "out-of-scope"
        bits.append(f"{label} {p}: {reasons[p]}")
    for p in sorted(acks):
        bits.append(f"in-scope-unmodified {p}: {acks[p]}")
    if not bits:
        return ""
    return "Scope reconciliation - " + "; ".join(bits)


def classify_commit_refusal(
    repo_root: Path, git_stderr: str, staged: Sequence[str]
) -> Optional[str]:
    """Name a commit failure caused by something OTHER than this transaction, or None.

    WHY THIS EXISTS (measured 2026-09-06, run `run-20260906T222302Z-2985274`). Orchestrator `84j8d7`
    was fully eligible for retirement, the transition ran, and its lifecycle commit was rejected by
    `pre-commit` with `local-leaks ... Failed - files were modified by this hook` while that hook's own
    output said `No local leaks found.` The refusal was recorded as the generic `finalize-refused`, so
    the operator could not tell an eligibility problem from an unrelated one, and the honest retry was
    invisible. The actual cause was a CONCURRENT AGENT writing an unrelated plan file inside
    `pre-commit`'s stash/restore window: pre-commit stashes unstaged changes, runs the hooks, and
    compares tree state afterwards, so a co-worker's write during that window is attributed to
    whichever hook happened to be running. `local-leaks` was an innocent bystander (it is
    `always_run: true, pass_filenames: false`, exits nonzero only on real findings, and its only file
    write is behind `--fix`, which the hook never passes).

    This DIAGNOSES only. The caller still fails closed and still rolls back; the point is that the
    recorded reason names a transient, unrelated cause and says a retry is safe, instead of implying
    the plan or its Set was at fault. Returns a human-readable cause, or None when the failure is not
    recognizably foreign (in which case the caller keeps its existing generic message: an unrecognized
    failure must NEVER be reported as a benign race).
    """
    text = git_stderr or ""
    owned = {str(p) for p in staged}

    # pre-commit's own signature for "the tree changed under me". Its wording is stable across
    # versions; match the distinctive half rather than the full sentence.
    hook_modified = "files were modified by this hook" in text
    if not hook_modified:
        return None

    # A hook that legitimately REWRITES an owned path (a formatter fixing our own file) is NOT a
    # foreign cause: the correct response there is to re-stage and retry, which the operator does by
    # re-running. Only claim a foreign cause when a path OUTSIDE the staged set is dirty.
    rc, out, _err = _git(repo_root, ["status", "--porcelain", "--untracked-files=no"])
    if rc != 0:
        return None
    foreign: List[str] = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        entry = line[3:].strip()
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1].strip()
        if entry and entry not in owned:
            foreign.append(entry)
    if not foreign:
        return None

    shown = ", ".join(sorted(foreign)[:4])
    more = "" if len(foreign) <= 4 else f" (+{len(foreign) - 4} more)"
    return (
        "the pre-commit hooks reported the working tree changed while they ran, and "
        f"{len(foreign)} dirty path(s) outside this transaction's staged set are present: "
        f"{shown}{more}. That is the signature of a CONCURRENT WRITER (another agent or a running "
        "driver) editing a file inside pre-commit's stash/restore window, not a problem with this "
        "plan or its Set. Nothing was committed and the transaction rolled back cleanly, so a RETRY "
        "is safe once the tree settles. Note the hook named in the pre-commit output is whichever one "
        "was running when the tree changed; it is not necessarily the cause."
    )


def _lifecycle_commit_exists(
    repo_root: Path, pre_head: str, plan_id: str
) -> Optional[str]:
    """Return the lifecycle commit hash if HEAD advanced past ``pre_head`` with our commit, else None.

    Observed-state classification (E-03): we identify OUR lifecycle commit by (a) HEAD != pre_head
    and (b) the tip commit's subject carrying the deterministic `lifecycle(<id>): finalize ...`
    marker. This reads repository evidence rather than trusting that the commit subprocess ran.

    The marker grammar is `artifact_core.lifecycle_commit_prefix` (IPD `zexed1` E-02), shared with the
    producer, the pre-commit gate's matcher and the run viewer's evidence reader. Deliberately the
    PREFIX and not the full finalize subject: this classifier recognizes any lifecycle verb's own
    commit, which is looser than the gate's finalize-only demand and must stay so.
    """
    from agent_workflows import artifact_core as _core

    rc, head, _err = _git(repo_root, ["rev-parse", "HEAD"])
    if rc != 0:
        return None
    head = head.strip()
    if head == pre_head:
        return None
    rc, subj, _err = _git(repo_root, ["log", "-1", "--format=%s", head])
    if rc == 0 and subj.strip().startswith(_core.lifecycle_commit_prefix(plan_id)):
        return head
    # HEAD moved but not via our marker: ambiguous - the caller classifies unknown-outcome.
    return None


def _rollback_precommit(repo_root: Path, journal: Dict[str, Any]) -> Tuple[bool, str]:
    """Idempotent pre-commit rollback driven by the journal (E-02). Returns (ok, message).

    Restores the plan to its original bytes+path, removes the moved destination, and restores the
    exact prior Git-index entries for lifecycle-owned paths (never touching disjoint staged/dirty
    work). Byte-equality with the snapshot is required only when no concurrent plan-state change
    occurred; an incompatible concurrent change is classified `unknown-outcome` and stopped WITHOUT
    a destructive restore.

    IT DELIBERATELY DOES NOT TOUCH THE PLANS MANIFESTS, AND THAT IS WHAT MAKES A FAILED TRANSITION
    LEAVE NO TRACE (plan `4xt6u4`). It used to "regenerate the plans index from the CURRENT corpus"
    as its last step, which WROTE `INDEX.json`/`INDEX.md` rather than restoring whatever state they
    were in. MEASURED at HEAD `daa48f42` with `fault_injection="after_move"` against a tree that had
    no manifests: the plan was correctly restored to `pending/`, the `executed/` copy was removed and
    HEAD was unmoved, yet `git status --porcelain` went from `''` to
    `?? .aw/records/plans/INDEX.json` + `?? .aw/records/plans/INDEX.md`. A rollback whose documented
    job is to restore the tree it started from was itself the only thing changing it.

    WHY NOT WRITING IS THE COMPLETE FIX, rather than snapshotting the manifests in the journal and
    restoring them. Since the mutations moved into a coordinator-owned worktree (`u23gbn`) and the
    manifests are GITIGNORED (so a fresh worktree never receives them and a regeneration there dies
    with it), NOTHING in the pre-commit phase writes the shared manifests. MEASURED at all three
    pre-commit fault points x both prior-state cases: at the instant this function is ENTERED the
    shared manifests are still byte-identical to their pre-attempt state in every case (absent stays
    absent, present stays byte-identical). So there is no damage here to repair, this step was the
    SOLE creator of the residue, and "restore the prior state" and "do not write" have the same
    postcondition - the second needing no journal keys, no three-state absent/present logic and no
    delete-to-restore. `_pre_commit_phase_leaves_manifests_untouched` states that invariant for the
    test that pins it, so a future change that makes the pre-commit phase write them FAILS here
    instead of silently restoring this bug.

    IT ALSO STOPS A MEASURED PEER-CLOBBER, which a restore would not have. Pre-fix, a peer that wrote
    the manifests inside the transaction window had those bytes replaced by the regeneration
    (measured: peer content gone). Not writing leaves them intact, and unlike a guarded restore it
    does not have to REFUSE (`unknown-outcome`) over a regenerable generated view, which would wedge
    an otherwise clean rollback on the last-resort path.

    CONSEQUENCE, STATED PLAINLY (plan `4xt6u4` E-01): a rollback NO LONGER FAILS because of manifest
    trouble. The old step 4 raised through `_refresh_plans_index_fail_loud` and became
    `(False, "rollback index regeneration failed: ...")`; that arm is gone with its subject. This is
    deliberate and is not a weakened gate: the SUCCESS path's fail-loud refresh is untouched (it
    still runs after the reconciliation and still raises, see :func:`_finalize_transaction`), an
    absent manifest is only `check.stale-index-missing` at severity `info`, and escalating a rollback
    to `PHASE_UNKNOWN_OUTCOME` over a file `aw index plans` regenerates would block an operator for
    no safety gain. This function's own failure arms (destination changed, origin holds a peer's
    content, cannot remove/restore) are unaffected and still report `unknown-outcome`.

    IT DOES NOT UNDO THE FF-ONLY MERGE, AND MUST NOT LEARN TO (plan `u23gbn` E-08). Two cases, both
    already settled elsewhere: if the reconciliation SUCCEEDED then the lifecycle commit has landed and
    this is not the right tool at all (`_resume_post_commit` resumes a landed commit and deliberately
    never reverts one); if it REFUSED then nothing was written to the shared tree and there is nothing
    to restore. So do not add a "helpful" `git reset`/`checkout` here.

    BOTH RESTORES ARE NOW CONCURRENCY-GUARDED, which the destination's always was and the ORIGIN's was
    not. Since the transaction performs its mutations in a coordinator-owned worktree, the shared-tree
    file at ``original_path`` is NEVER TOUCHED by this transaction, so an unconditional write there
    would overwrite whatever a peer currently has. MEASURED before the guard existed: a peer's
    uncommitted edit (`- Status: approved\\nPEER EDIT IN FLIGHT, uncommitted\\n`) was replaced by the
    snapshot bytes and the peer's content was gone, and because the destructive write happens before
    the later steps, even a rollback that REPORTS failure had already destroyed it.
    """
    orig_rel = journal["original_path"]
    dest_rel = journal.get("dest_path")
    orig_abs = repo_root / orig_rel
    orig_bytes = journal["original_bytes"]
    # The bytes this transaction believes it left at the ORIGIN. Absent (the ordinary case now) means
    # the transaction never wrote there, so the correct default is to leave the file alone entirely.
    origin_written = journal.get("origin_written_bytes")

    # 1. Remove the moved destination (if the move happened) unless a concurrent change altered it.
    if dest_rel and dest_rel != orig_rel:
        dest_abs = repo_root / dest_rel
        if dest_abs.exists():
            # Only remove a destination that matches what THIS transaction wrote (our plan bytes),
            # so we never clobber a concurrent writer that legitimately owns that path.
            try:
                cur = dest_abs.read_text(encoding="utf-8")
            except OSError:
                cur = None
            expected = journal.get("moved_bytes")
            if expected is not None and cur is not None and cur != expected:
                return (
                    False,
                    "unknown-outcome: the finalize destination {0} changed since the checkpoint; "
                    "refusing a destructive restore.".format(dest_rel),
                )
            try:
                dest_abs.unlink()
            except OSError as exc:
                return (False, f"rollback could not remove {dest_rel}: {exc}")

    # 2. Restore the plan's original bytes at its original path (atomic) - but ONLY when this
    #    transaction is the party that changed that path, or the file is simply missing.
    #
    #    THE GUARD, and why it is the same shape step 1 already had. Step 1 refuses to delete a
    #    DESTINATION whose bytes are not the ones it wrote, so it cannot clobber a concurrent writer
    #    that legitimately owns that path. The ORIGIN needed no such guard while the transaction moved
    #    the file itself: nothing else could be there. Now that the move happens in a coordinator
    #    worktree, the shared-tree origin is untouched by us, so an unconditional write is an
    #    unconditional overwrite of a peer's in-flight edit. Restore only when (a) the file is absent
    #    (a genuine half-move to undo), (b) the current bytes are already what we would write (a no-op
    #    that keeps the rollback idempotent), or (c) the current bytes are exactly what THIS
    #    transaction recorded writing there. Anything else is somebody else's content: refuse with
    #    unknown-outcome naming the path, exactly as step 1 does, rather than destroy it.
    try:
        current_origin: Optional[str] = orig_abs.read_text(encoding="utf-8")
    except OSError:
        current_origin = None
    if current_origin is None:
        restore_origin = True
    elif current_origin == orig_bytes:
        restore_origin = False  # already correct; writing would be a no-op
    elif origin_written is not None and current_origin == origin_written:
        restore_origin = True  # our own mutation, so undoing it is ours to do
    else:
        return (
            False,
            "unknown-outcome: the plan's original path {0} holds content this transaction did not "
            "write (a concurrent writer's in-flight edit); refusing a destructive restore. Those "
            "bytes are intact and were NOT overwritten.".format(orig_rel),
        )
    if restore_origin:
        try:
            orig_abs.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(
                dir=str(orig_abs.parent), prefix=".rb-", suffix=".md"
            )
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(orig_bytes)
            os.replace(tmp, str(orig_abs))
        except OSError as exc:
            return (False, f"rollback could not restore {orig_rel}: {exc}")

    # 3. Restore the exact prior Git-index entries for lifecycle-owned paths (no disjoint work).
    owned = journal.get("owned_paths", [])
    prior_index = journal.get("git_index_entries", {})
    for p in owned:
        # Reset the index entry for this owned path to its recorded state without staging others.
        if p in prior_index:
            _git(repo_root, ["restore", "--staged", "--", p])
        else:
            _git(repo_root, ["restore", "--staged", "--", p])

    # 4. The plans manifests are DELIBERATELY NOT TOUCHED. See this function's docstring for the
    #    measurement: nothing in the pre-commit phase writes the shared `INDEX.json`/`INDEX.md`, so
    #    they are already in their pre-attempt state by the time we get here, and regenerating them
    #    (which is what this step used to do) is the ONLY thing that made a failed transition leave
    #    `?? INDEX.json` / `?? INDEX.md` behind in a tree that had none. Do not "helpfully" restore
    #    the refresh here: a rollback that writes a generated view cannot leave the tree as it found
    #    it, and on the ABSENT path it cannot even tell created-and-ignored from never-existed.
    #    The success path's fail-loud refresh is the one that matters and is untouched.
    return (
        True,
        "pre-commit state restored (plan bytes/path + owned Git-index; plans manifests left "
        "untouched, so the tree is as it was found).",
    )


def _early_recovery_result(
    repo_root: Path, plan_path: Path, evidence: Dict[str, Any]
) -> Optional[FinalizeResult]:
    """EARLY CRASH RECOVERY, shared by `finalize` and `retire_orchestrator` (Order 3xh53a).

    Resolve the plan id from whatever path resolved (a committed-incomplete plan lives in
    ``executed/``, where precheck/begin do not apply) and resume/rollback a prior interrupted
    transaction BEFORE any fresh precheck. Returns a `FinalizeResult` when the caller must STOP and
    return it; None when there is nothing to recover and the caller should proceed.

    EXTRACTED rather than duplicated (orchretire-02 `ueg5cf`). The rollup transition must perform
    this same recovery, and OQ-01's accepted cost of a second transition path is that the two can
    DRIFT; sharing the one implementation removes this gate from the drift surface entirely instead of
    relying on a test to notice a copy going stale.

    A PRE-COMMIT phase deliberately returns None: the plan is still in its origin directory, and the
    transaction's own resume-rollback (in `_finalize_transaction`) handles it.
    """
    from agent_workflows import ipd_lint as _lint0

    try:
        plan_text = plan_path.read_text(encoding="utf-8")
    except OSError:
        return None
    early_id = (_lint0.parse(plan_text).meta_fields.get("Id") or "").strip()
    if not early_id:
        return None
    journal = read_finalize_journal(repo_root, early_id)
    if journal is None:
        return None
    phase = journal.get("phase")
    if phase == PHASE_COMMITTED_INCOMPLETE:
        try:
            acquire_finalize_lock(repo_root, early_id)
        except TransactionLockError as exc:
            return FinalizeResult(EXIT_CANNOT_RUN, None, str(exc), evidence)
        try:
            return _resume_post_commit(repo_root, journal, early_id, evidence)
        finally:
            release_finalize_lock(repo_root)
    if phase == PHASE_UNKNOWN_OUTCOME:
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"finalize journal for {early_id} is in unknown-outcome (ambiguous prior "
            f"attempt); resolve manually and clear "
            f"{finalize_journal_path(repo_root, early_id)}.",
            evidence,
            tuple(journal.get("findings", ())),
        )
    return None


# --------------------------------------------------------------------------------------
# The RUNNER-OWNED ORCHESTRATOR ROLLUP RETIREMENT (orchretire-02 `ueg5cf`; spec `77tr3o` R-4/R-5/R-6)
#
# WHY A SEPARATE TRANSITION EXISTS AT ALL, and why `ipd_lint.py` was deliberately NOT touched.
#
# Under `aw oc|agy run` an Order-0 orchestrator is NEVER agent-executed: the runner itself enforces
# the ordering, the isolation and the per-child merge gate that the orchestrator's own `E-*`/`V-*`
# items describe. So those items are, by design, performed by NOBODY. Two gates on the main
# `finalize` path are therefore unpassable for it, and both are structural rather than incidental:
#
#   1. the `pre-transition` E/V checkpoint (`ipd_lint.check_checkpoint`) requires EVERY `E-*`
#      `performed` and EVERY `V-*` `pass` with nonempty evidence, UNCONDITIONALLY; and
#   2. `finalize_precheck` requires a `begin` receipt, which nothing ever mints for a plan no agent
#      executes.
#
# Measured consequence: across 102 durable run records, `orchestrator-finalized` fired 0 times and
# `orchestrator-deferred` fired 28 times across 15 orchestrators. The rollup has never once worked.
#
# SPEC `77tr3o` OQ-1 offered two shapes and THE MAINTAINER CHOSE (b), THIS ONE: a separate
# runner-owned transition. He REJECTED (a), teaching `ipd_lint.py` a `Kind: orchestrator` exemption,
# for a stated reason: a safety check that learns one narrow exception is how it quietly stops
# protecting anything, because a later reader sees the exception and widens it. `ipd_lint.py` is
# consequently OUT OF BOUNDS for this plan and its diff is asserted EMPTY by
# `tests/test_orchestrator_retirement.py`. DO NOT "simplify" this into the linter exemption that was
# rejected, and do not merge it back into `finalize`: if you believe (a) is better, raise it with the
# maintainer rather than substituting your judgement for his.
#
# HE ALSO ACCEPTED THE COST EXPLICITLY: two transition paths CAN DRIFT. Two things manage that. The
# gates that can be SHARED are shared as code (`_early_recovery_result`, `acquire_finalize_lock`,
# `_refresh_plans_index_fail_loud`, `_finalize_transaction`, `_complete_after_commit`), so they are
# not on the drift surface at all; and `ROLLUP_SHARED_GATES` / `ROLLUP_OMITTED_GATES` below name the
# full gate set explicitly so a test can FAIL when one path gains a gate the other lacks.
# --------------------------------------------------------------------------------------

#: The gates the rollup transition performs, SHARED with the main `finalize` path. Named explicitly
#: (not derived by inspection) so `tests/test_orchestrator_retirement.py` can assert the two paths
#: agree, and so a reviewer can read the contract without re-deriving it from control flow.
#:
#: THIS ENUMERATION IS LONGER THAN IT LOOKS, and the length is the point. An earlier draft of this
#: plan listed five gates (status legality, the plan move, the index refresh, the commit, the
#: post-transition lint); `finalize` performs at least nine. A drift test built from the short list
#: would have PASSED while the rollup silently ran with no exclusive lock, no transaction journal and
#: no crash recovery, inside a live runner sharing this checkout with other agents.
ROLLUP_SHARED_GATES: Tuple[str, ...] = (
    # A worker-role process may not create lifecycle authority (wtiso-03 `rchpms` E-05). NOT
    # inherited: `worker_role_active` is checked in the CLI wrappers `run_begin`/`run_finalize`, not
    # inside `finalize()`, so this path had to check it itself. See E-06.
    "worker-role-refusal",
    # Non-empty actor and message (`finalize` :1730-1737): an unattributed terminal record is not a
    # record.
    "actor-and-message-required",
    # EARLY CRASH RECOVERY: resume or roll back a prior interrupted transaction BEFORE anything else
    # (`_early_recovery_result`, shared code).
    "early-crash-recovery",
    # The EXCLUSIVE finalize writer lock over the shared plans tree (`acquire_finalize_lock`),
    # released in a `finally:`. Mandatory here, not optional: the rollup runs INSIDE a live runner
    # that may be finalizing a child concurrently, in a checkout shared with other agents.
    "exclusive-finalize-lock",
    # The two-phase transaction JOURNAL (prepared -> mutating -> ready-to-commit ->
    # committed-incomplete -> complete) with idempotent pre-commit rollback
    # (`_finalize_transaction`, `_rollback_precommit`), shared code.
    "transaction-journal",
    # Status legality: the plan must not ALREADY be terminal
    # (`ipd_schema.checkpoint_allows_status('pre-transition', ...)`).
    "status-legality",
    # The plan file move into `executed/` (`status_set.apply_status_change`). PERFORMED IN A
    # COORDINATOR-OWNED WORKTREE since plan `u23gbn`, not in the shared checkout, so the shared tree is
    # never mid-move; the shared tree is then brought into line by the refusing fast-forward below.
    "plan-move",
    # The FAIL-LOUD owned plans-index refresh, which re-runs `--check` and RAISES if it did not
    # converge (`_refresh_plans_index_fail_loud`), so a stale index is a transaction failure. It runs
    # AFTER the reconciliation (plan `u23gbn` E-07): with the move relocated to the worktree, refreshing
    # earlier scanned a shared disk that did not yet reflect the transition, so the manifest converged
    # against the OLD layout and the gate PASSED while leaving the repository in the exact
    # `check.stale-index-stale` state it exists to prevent. Being post-commit, a failure here is
    # committed-incomplete rather than a rollback; it is still fail-loud and still refuses.
    "plans-index-refresh-fail-loud",
    # The single PATH-SCOPED lifecycle commit over exactly `owned_paths` (never `git add -A`), produced
    # in the coordinator worktree and landed in the shared checkout by the fast-forward below.
    "path-scoped-lifecycle-commit",
    # The REFUSING fast-forward that lands that commit (`land_worktree_commit`, plan `u23gbn` E-06).
    # It is the SINGLE step that advances the branch AND updates the shared working tree, and it is
    # deliberately the operation whose REFUSAL protects a co-worker's uncommitted bytes: never forced,
    # and never preceded by an `update-ref` (which makes it a no-op that reports success and makes the
    # refusal unreachable). Named as a gate because a change that forced it, or that advanced the ref
    # some other way, would silently remove the protection while every other gate still passed.
    "refusing-fast-forward-reconciliation",
    # `post-transition` lint on the committed plan, INCLUDING the terminal attribution rule
    # (`_check_terminal_attribution`), which is what forces the honest history entry of E-04.
    "post-transition-lint",
)

#: The gates the rollup DELIBERATELY does not perform, each with the reason. A gate may appear here
#: ONLY with a justification; that is the whole discipline this pair of tuples enforces.
ROLLUP_OMITTED_GATES: Dict[str, str] = {
    "pre-transition-ev-checkpoint": (
        "THE ONE DELIBERATE DIFFERENCE, and the entire reason this transition exists. The "
        "`pre-transition` checkpoint requires every `E-*` performed and every `V-*` evidenced. Under "
        "`aw run` an orchestrator's items are performed by NOBODY (the runner supersedes its "
        "coordination role), so the requirement is unsatisfiable by construction rather than "
        "unsatisfied by neglect. Spec `77tr3o` R-5, resolved by the maintainer to shape (b): skip the "
        "checkpoint HERE, in one narrowly-gated place, rather than teach `ipd_lint.py` an exemption "
        "that a later reader would widen. Every OTHER `pre-transition` structural check still runs "
        "via the `post-transition` lint after the commit, and the E/V requirement is untouched for "
        "CHILD plans, which this route refuses outright."
    ),
    "begin-receipt-requirement": (
        "Spec `77tr3o` R-6. An orchestrator has no `begin` receipt BY CONSTRUCTION: nothing calls "
        "`aw ipd begin` for a plan no agent executes, which is the literal refusal measured today "
        "('no begin receipt for rh5tt6'). The rollup does not require one and MINTS NONE, so no "
        "artifact is left behind claiming an execution that did not happen."
    ),
    "scope-delta-reconciliation": (
        "A CONSEQUENCE of omitting the receipt, stated rather than discovered. `finalize_precheck` "
        "reads `base_head` FROM the receipt (:1355-1364) and that is the baseline the entire scope "
        "delta is computed against (`_changed_path_sources`), plus the receipt's frozen "
        "`scope_paths`. No receipt therefore means no scope reconciliation. That is SAFE here only "
        "because a rollup makes NO code edits at all: its only changed paths are the lifecycle "
        "artifacts the transaction itself owns. The rollup does not merely ASSUME that - "
        "`_assert_rollup_touched_only_owned_paths` VERIFIES it before committing and refuses if the "
        "orchestrator's own file was edited, so the property that makes dropping `base_head` safe is "
        "checked rather than trusted."
    ),
}

#: The refusal reasons `retire_orchestrator` can return, as a typed vocabulary (the same discipline
#: child 01 applied to `RetirementDecision.reason`: a caller must not have to string-match prose).
ROLLUP_REFUSED_NOT_ORCHESTRATOR = "not-an-orchestrator"
ROLLUP_REFUSED_SET_INELIGIBLE = "set-ineligible"
ROLLUP_REFUSED_ALREADY_TERMINAL = "already-terminal"
ROLLUP_REFUSED_WORKER_ROLE = "worker-role"
ROLLUP_REFUSED_UNOWNED_EDIT = "unowned-edit-to-plan"


def rollup_history_message(
    *,
    setid: str,
    run_id: Optional[str],
    children: Sequence[str],
) -> str:
    """The HONEST terminal history summary for a retired orchestrator (spec `77tr3o` R-4).

    It must say three things and must NOT say a fourth:
      * that the plan was RETIRED as a rollup step of a runner Set completion, not executed;
      * the RUN ID that retired it (so the durable run record can be found); and
      * the CHILDREN whose execution justified it (the actual evidence).
    It must NOT claim the orchestrator's own `E-*`/`V-*` items were performed, because under
    `aw run` they were not. The word "retired" is deliberately first; a reader skimming history sees
    the nature of the transition before its justification.

    There is NO wording to preserve: the existing string in `oc_runipd.finalize_orchestrator`
    ("Orchestrator rollup: all children of set X executed ...") has never once been written to a
    plan, because the transition it belongs to has never succeeded. Note that string also overstated
    the case, asserting "all children of set X executed" without naming them.

    PARENTHESIS-FREE BY CONTRACT, in the ACTOR the caller pairs with this message. The terminal
    history line is `- <date> <status> (<actor>): <msg>`, and the actor is rendered `key=value`-style
    as `driver_actor` does. The MESSAGE may contain parentheses safely (it is the trailing capture),
    but the actor may not.

    THE REASON CHANGED, and the rule did not (plan fn2l1u). This used to say the readers' actor
    capture was bounded by `[^)]*` so a parenthesized actor MISPARSED; that is no longer true -
    `ipd_lint._HISTORY_ATTRIB_RE`, `plan_readiness._HISTORY_RECORD_PARTS_RE` and
    `record_history._TAIL_RE` all capture the actor LAZILY now and parse either shape. The
    parenthesis-free rule stands anyway, and is now ENFORCED at the setter
    (`attention_contract.actor_refusal`): every writer in the toolkit emits one shape, one shape is
    cheaper to read and grep than two, and refusing at the setter keeps the failure BEFORE the
    lifecycle commit instead of after it.
    """
    named = ", ".join(children) if children else "none"
    run_part = f"run {run_id}" if run_id else "an unrecorded run"
    return (
        f"RETIRED as the orchestrator rollup step of a runner Set completion, not executed by an "
        f"agent: every child of Set {setid} reached executed, so the runner ({run_part}) retired "
        f"this Order-0 plan as bookkeeping. Its own E-*/V-* items were NOT performed; the runner "
        f"superseded them by enforcing the ordering, the isolation and the per-child merge gate. "
        f"Justifying children: {named}."
    )


def _assert_rollup_touched_only_owned_paths(
    repo_root: Path, plan_rel: str
) -> Optional[str]:
    """Refuse if the orchestrator's own plan file is DIRTY before the rollup mutates anything.

    THE PROPERTY THIS DEFENDS, per `ROLLUP_OMITTED_GATES['scope-delta-reconciliation']`. Dropping the
    receipt drops `base_head`, hence the whole scope delta. That is safe only because a rollup makes
    no code edits, so its only changed paths are the lifecycle artifacts the transaction owns. This
    verifies the one part of that which could be false: someone (an agent mid-edit, a human) having
    uncommitted changes to the very plan the rollup is about to rewrite and commit. Committing that
    would sweep another party's work into a lifecycle commit and attribute it to the runner.

    Deliberately NARROW. It does NOT inspect the rest of the working tree, because in a shared
    checkout a co-worker's unrelated dirty file is expected, is not the rollup's business, and is
    exactly what `_working_tree_path_is_owned` already declines to judge on the main path. Returns a
    refusal string, or None when clean.
    """
    rc, out, _err = _git(repo_root, ["status", "--porcelain", "--", plan_rel])
    if rc != 0:
        return None  # not a git repo / git unavailable: the commit step reports authoritatively
    dirty = [ln for ln in out.splitlines() if ln.strip()]
    if not dirty:
        return None
    return (
        f"the orchestrator's own plan file {plan_rel} has UNCOMMITTED changes "
        f"({'; '.join(s.strip() for s in dirty)}). A rollup makes no code edits, so it performs no "
        "scope reconciliation (it has no begin receipt and therefore no base_head to diff against); "
        "committing a dirty plan file would sweep someone else's in-flight edit into a lifecycle "
        "commit and attribute it to the runner. Land or set that edit aside and re-run."
    )


def retire_orchestrator(
    repo_root: Path,
    plan_path: Path,
    actor: str,
    *,
    setid: str,
    run_id: Optional[str] = None,
    children: Sequence[str] = (),
    eligibility=None,
    apply: bool = False,
    fault_injection: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> FinalizeResult:
    """RETIRE an Order-0 orchestrator as a runner rollup step (spec `77tr3o` R-4/R-5/R-6).

    THIS IS NOT `finalize` WITH A GATE REMOVED, it is a narrower transition for a plan the main path
    structurally cannot serve. It performs every gate in :data:`ROLLUP_SHARED_GATES` and omits
    exactly those in :data:`ROLLUP_OMITTED_GATES`, each for a recorded reason.

    IT IS GATED ON TWO INDEPENDENT FACTS, and requiring both is the point:

      * ``Kind: orchestrator``. A `Kind: child` plan is REFUSED outright, so this route cannot be
        aimed at an ordinary plan at all and adds NO path by which one reaches `executed` without
        evidence.
      * The Set is ELIGIBLE per child 01's `runner_shared.evaluate_set_retirement`, re-checked HERE
        rather than trusted from the caller. Kind alone is NOT authority: `oc_runipd.action_for`
        returns `orchestrate` from `reviewed` onward, so a Kind-only route would retire whatever it
        was pointed at and the only thing preventing a premature retirement would be a caller
        remembering to ask. Defense in depth is cheap; the failure it prevents (asserting a
        completion that never happened) is the one this Set must never cause. Pass ``eligibility`` to
        reuse a decision the caller already computed; it is VALIDATED, not trusted, and a
        non-eligible verdict refuses.

    ``apply=False`` (the default) is a dry run: every gate is evaluated and NOTHING is mutated.

    ``env`` defaults to ``os.environ`` and exists so the worker-role refusal is testable without
    mutating global process state, mirroring `worker_role_active`'s own design.

    WHERE THE WRITES HAPPEN, AND WHAT REMAINS IN THE SHARED CHECKOUT (plan `u23gbn`). The status edit,
    the plan move and the commit all happen in a THROWAWAY WORKTREE ON ITS OWN BRANCH, created and
    owned by the COORDINATOR, so the shared checkout is never mid-move and is never the tree
    ``pre-commit`` stashes. Two shared-checkout writes REMAIN, and this docstring names them rather
    than letting a reader infer a stronger property than is true:

    * the ``git merge --ff-only`` that LANDS the commit, which is the single step that advances the
      branch and updates the working tree together, and which REFUSES rather than clobbers when a
      peer's uncommitted change is in the way (:func:`land_worktree_commit`); and
    * the post-reconciliation plans-manifest refresh, which writes only GITIGNORED generated views.

    THE ROLE IS STILL ``coordinator``, and the worktree does not change that. The first gate below
    refuses when ``AW_EXECUTION_ROLE=worker``; the scratch worktree is a coordinator-owned tree, NOT a
    worker lane, and the role variable is neither set nor emulated in it.

    DO NOT REINTRODUCE SHARED-TREE MUTATION, and do not read this as atomicity: a ref update alone was
    MEASURED to leave the shared tree dirty in the INVERSE direction (HEAD at ``executed/`` while the
    working tree still holds ``pending/``), which is worse than the window it replaces. The window is
    SHORTER and its one remaining write is git's own refusing fast-forward; it is not gone.
    """
    from agent_workflows import ipd_lint as _lint
    from agent_workflows import ipd_schema as _schema
    from agent_workflows import runner_shared as _rs
    from agent_workflows import status_set as _ss

    evidence: Dict[str, Any] = {"transition": "orchestrator-rollup", "setid": setid}

    # --- GATE: worker role. FIRST, before selector resolution, any other gate, or any mutation, so a
    # refused invocation has NO side effect (E-06). The refusal is NOT inherited from the CLI
    # wrappers: `worker_role_active` is called in `run_begin` (:2223) and `run_finalize` (:2403), NOT
    # in `finalize()`, so a new transition function starts with no role guard whatsoever and a
    # managed worker could otherwise create lifecycle authority through it.
    if worker_role_active(os.environ if env is None else env):
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"{LIFECYCLE_ROLE_ERROR} (refused: orchestrator rollup retirement). The runner "
            "performs this transition from the coordinator role; a worker-role process must not.",
            evidence,
            (ROLLUP_REFUSED_WORKER_ROLE,),
        )

    # --- GATE: actor required (mirrors `finalize`). The message is DERIVED here rather than passed
    # in, because R-4 fixes what it must say; there is no caller-supplied wording to validate.
    #
    # The empty-actor wording stays LOCAL because it names this transition ("orchestrator rollup
    # retirement requires..."), which is more useful than a generic string and is pinned by
    # `tests/test_orchestrator_retirement.py::test_an_empty_actor_is_refused`. The PARENTHESIS refusal
    # now comes from the ONE shared validator (`attention_contract.actor_refusal`, plan fn2l1u E-01)
    # so that this path, `finalize`, and the shared history writer cannot drift into two definitions
    # of a valid actor. See that helper for why the refusal remains correct now that the READERS
    # tolerate a parenthesized actor.
    if not actor or not actor.strip():
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            "orchestrator rollup retirement requires a non-empty --actor.",
            evidence,
        )
    actor = actor.strip()
    from agent_workflows import attention_contract as _ac

    _actor_problem = _ac.actor_refusal(actor)
    if _actor_problem is not None:
        return FinalizeResult(EXIT_CANNOT_RUN, None, _actor_problem, evidence)
    if not plan_path.is_file():
        return FinalizeResult(
            EXIT_CANNOT_RUN, None, f"plan file not found: {plan_path}", evidence
        )

    try:
        plan_text = plan_path.read_text(encoding="utf-8")
    except OSError as exc:
        return FinalizeResult(
            EXIT_CANNOT_RUN, None, f"cannot read plan: {exc}", evidence
        )
    meta = _lint.parse(plan_text).meta_fields
    plan_id = (meta.get("Id") or "").strip()
    if not plan_id:
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"plan {plan_path} has no '- Id:' handle.",
            evidence,
        )
    evidence["plan_id"] = plan_id

    # --- GATE: Kind must be `orchestrator`. Reads `Kind` first and falls back to `Order == 0` for
    # the 74 legacy plans in this repo that carry `Order: 0` with no `Kind:` bullet (the same rule
    # child 01's `SetMember.is_orchestrator` applies, kept consistent deliberately).
    kind = (meta.get("Kind") or "").strip()
    raw_order = (meta.get("Order") or "").strip()
    is_orchestrator = (
        kind == _schema.KIND_ORCHESTRATOR if kind else raw_order in ("0", "00")
    )
    if not is_orchestrator:
        return FinalizeResult(
            EXIT_FINDINGS,
            None,
            f"REFUSED: {plan_id} is not an orchestrator (Kind={kind or '<absent>'!r}, "
            f"Order={raw_order or '<absent>'!r}). The rollup retirement exists ONLY for an Order-0 "
            "plan whose E-*/V-* items the runner supersedes; an ordinary plan must earn `executed` "
            "through `aw ipd finalize`, with its evidence.",
            evidence,
            (ROLLUP_REFUSED_NOT_ORCHESTRATOR,),
        )

    # --- GATE: status legality. `pre-transition`'s own coarse rule (`checkpoint_allows_status`):
    # the plan must not ALREADY be terminal. Shared as the same predicate, not a re-listed tuple.
    status = (meta.get("Status") or "").strip()
    if not _schema.checkpoint_allows_status("pre-transition", status):
        return FinalizeResult(
            EXIT_FINDINGS,
            None,
            f"REFUSED: {plan_id} carries Status {status!r}, which is already terminal; there is "
            "nothing to retire.",
            evidence,
            (ROLLUP_REFUSED_ALREADY_TERMINAL,),
        )

    # --- GATE: the Set must be ELIGIBLE. Re-checked here even when the caller supplies a verdict.
    decision = eligibility
    if decision is None:
        decision = _rs.evaluate_set_retirement(repo_root, setid)
    evidence["eligibility"] = {
        "eligible": bool(getattr(decision, "eligible", False)),
        "reason": getattr(decision, "reason", "<no reason>"),
        "detail": getattr(decision, "detail", ""),
        "unfinished": list(getattr(decision, "unfinished", ()) or ()),
        "unauthored_rows": list(getattr(decision, "unauthored_rows", ()) or ()),
    }
    if not getattr(decision, "eligible", False):
        return FinalizeResult(
            EXIT_FINDINGS,
            None,
            f"REFUSED: Set {setid!r} is not retirement-eligible "
            f"({getattr(decision, 'reason', 'unknown')}): "
            f"{getattr(decision, 'detail', '')}",
            evidence,
            (ROLLUP_REFUSED_SET_INELIGIBLE,),
        )

    # --- GATE: early crash recovery, via the SAME shared helper `finalize` uses.
    early = _early_recovery_result(repo_root, plan_path, evidence)
    if early is not None:
        return early

    # --- The scope-delta consequence, ASSERTED rather than assumed (see ROLLUP_OMITTED_GATES).
    plan_rel = _repo_relative(repo_root, plan_path)
    unowned = _assert_rollup_touched_only_owned_paths(repo_root, plan_rel)
    if unowned is not None:
        return FinalizeResult(
            EXIT_FINDINGS,
            None,
            f"REFUSED: {unowned}",
            evidence,
            (ROLLUP_REFUSED_UNOWNED_EDIT,),
        )

    # The honest R-4 record. Children default to the eligibility decision's own evidence, so the
    # named children are the ones the predicate actually verified rather than a caller's assertion.
    justifying = list(children) or [
        m.id6 for m in _rs.read_set_membership(repo_root, setid).children
    ]
    message = rollup_history_message(setid=setid, run_id=run_id, children=justifying)
    evidence["history_message"] = message
    evidence["shared_gates"] = list(ROLLUP_SHARED_GATES)
    evidence["omitted_gates"] = dict(ROLLUP_OMITTED_GATES)

    if not apply:
        return FinalizeResult(
            EXIT_OK,
            None,
            f"rollup retirement gates PASSED for orchestrator {plan_id} of Set {setid} "
            f"({len(justifying)} executed child(ren)); re-run with apply=True to perform it.",
            evidence,
            (),
        )

    rec = _ss.read_artifact_record(plan_path, repo_root)
    if rec is None:
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"could not read plan record for {plan_path}.",
            evidence,
        )

    # --- GATE: the EXCLUSIVE finalize writer lock, then the SAME journaled two-phase transaction the
    # main path runs (`_finalize_transaction` performs the journal, the plan move, the fail-loud index
    # refresh, the path-scoped commit and the post-transition lint). Taking the same lock is
    # mandatory, not defensive: this runs inside a live runner that may be finalizing a child at the
    # same moment, in a checkout shared with other agents.
    try:
        acquire_finalize_lock(repo_root, plan_id)
    except TransactionLockError as exc:
        return FinalizeResult(EXIT_CANNOT_RUN, None, str(exc), evidence)
    try:
        return _finalize_transaction(
            repo_root,
            plan_path,
            plan_rel,
            plan_id,
            rec,
            actor,
            message,
            evidence,
            fault_injection,
        )
    finally:
        release_finalize_lock(repo_root)


def finalize(
    repo_root: Path,
    plan_path: Path,
    actor: str,
    message: str,
    *,
    apply: bool = False,
    scope_reasons: Optional[Dict[str, str]] = None,
    scope_acks: Optional[Dict[str, str]] = None,
    interactive: bool = False,
    prompt=None,
    plan_selector: Optional[str] = None,
    fault_injection: Optional[str] = None,
) -> FinalizeResult:
    """The atomic terminal transaction for one IPD (precheck + two-way reconciliation + transition).

    On the happy path (``apply=True``): validate receipt + pre-transition lint + scope-delta
    computation (Order 04); reconcile the two-way scope delta (Order 05: out-of-scope edits need a
    recorded reason, in-scope-unmodified declared paths need an acknowledgment - via ``scope_reasons``
    / ``scope_acks`` or the TTY ``prompt``); then append the attributed history entry (INCLUDING the
    verbatim reconciliation note), set terminal status, move the plan, refresh the owned index
    fail-loud, create the path-scoped lifecycle commit, run post-transition lint, and report the
    commit + three-phase gate evidence. A missing reason/ack fails closed naming the exact
    re-invocation. (Rollback/failure semantics are Order 06.)
    """
    from agent_workflows import status_set as _ss

    evidence: Dict[str, Any] = {}
    if not actor or not actor.strip():
        return FinalizeResult(
            EXIT_CANNOT_RUN, None, "finalize requires a non-empty --actor."
        )
    # THE FINALIZE CHOKE POINT (plan fn2l1u E-02). This one site covers all THREE callers - the CLI
    # (`run_finalize`), `retire_orchestrator`'s rollup path, and `status_set`'s
    # `_delegate_plan_executed_to_finalize`, which is what `aw set executed` / `aw ipd set executed`
    # take - and it sits BEFORE any journal write, status write, move, or commit, which is the
    # property that matters: the defect being closed is a formatting failure detected AFTER the
    # lifecycle commit, leaving the transaction `committed-incomplete` with a resume instruction that
    # could not succeed. `finalize_precheck` is deliberately NOT guarded: it receives no actor at all,
    # so it never was a hole.
    from agent_workflows import attention_contract as _ac

    _actor_problem = _ac.actor_refusal(actor)
    if _actor_problem is not None:
        return FinalizeResult(EXIT_CANNOT_RUN, None, f"finalize: {_actor_problem}")
    if not message or not message.strip():
        return FinalizeResult(
            EXIT_CANNOT_RUN, None, "finalize requires a non-empty --message."
        )
    if not plan_path.is_file():
        return FinalizeResult(
            EXIT_CANNOT_RUN, None, f"plan file not found: {plan_path}"
        )

    # --- Early recovery: a prior interrupted/committed-incomplete transaction (Order 3xh53a). ---
    # EXTRACTED into `_early_recovery_result` (orchretire-02 `ueg5cf` E-01/E-02) so the runner-owned
    # rollup transition performs the IDENTICAL recovery, shared by construction rather than by a
    # second copy that could drift from this one.
    early = _early_recovery_result(repo_root, plan_path, evidence)
    if early is not None:
        return early

    exit_code, msg, evidence, findings = finalize_precheck(repo_root, plan_path)
    if exit_code != EXIT_OK:
        return FinalizeResult(exit_code, None, msg, evidence, findings)

    # --- Order 05: two-way scope reconciliation (surfaces + attributes both deltas) ---
    audit = evidence.get("scope_audit", {})
    out_of_scope = list(audit.get("out_of_scope_paths", []))
    in_scope_unmodified = list(audit.get("in_scope_unmodified", []))
    # rcptwiden `63425h` E-04: paths ADDED to `Scope-Paths` under an accepted additive widening each
    # demand their own reason, unconditionally and independently of `out_of_scope`.
    widened = list(audit.get("widened_paths", []))
    reconcile = _reconcile_scope(
        plan_selector or (plan_path.name),
        actor,
        message,
        out_of_scope,
        in_scope_unmodified,
        scope_reasons=scope_reasons,
        scope_acks=scope_acks,
        interactive=interactive,
        prompt=prompt,
        widened=widened,
    )
    evidence["scope_reconciliation"] = {
        "reasons": reconcile.reasons,
        "acks": reconcile.acks,
        "resolved": reconcile.ok,
        "widened_paths": list(widened),
    }
    if not reconcile.ok:
        findings_list: List[str] = []
        widened_set = set(widened)
        for p in reconcile.missing_reasons:
            if p in widened_set:
                # rcptwiden `63425h` E-04: name the act accurately. This path was DECLARED, so calling
                # it out-of-scope would misdescribe the honest thing the executor did.
                findings_list.append(
                    "path ADDED to Scope-Paths after begin needs a --scope-reason: " + p
                )
            else:
                findings_list.append(f"out-of-scope path needs a --scope-reason: {p}")
        for p in reconcile.missing_acks:
            findings_list.append(
                f"declared-but-unmodified path needs a --scope-ack: {p}"
            )
        # `gys47u` E-03: name the evidence that produced the demand. A demand backed by
        # `commit-cohesion` may legitimately include a CO-WORKER's path (the heuristic's documented
        # false-DEMAND cost), so a reader who knows that can check before writing a reason they would
        # be asserting falsely. A demand backed by `run-record-exact` came from this execution's own
        # recorded commits and needs no such second look. Appended to the refusal a human actually
        # reads, not only to the evidence dict, because the whole point is to inform the person
        # composing the reasons.
        source = str(evidence.get("attribution_source") or "unknown")
        source_note = {
            "run-record-exact": (
                "attribution: run-record-exact (this execution's own recorded commit SHAs; "
                "every path below is genuinely this plan's)"
            ),
            "commit-cohesion": (
                "attribution: commit-cohesion (HEURISTIC fallback, no run record for this item). "
                "A path below MAY belong to a concurrent agent whose commit touched one of this "
                "plan's declared paths; verify before writing a reason you would be asserting"
            ),
            "none-fail-closed": (
                "attribution: none (fail-closed). No ownership evidence was available, so every "
                "out-of-scope path is demanded rather than excused"
            ),
        }.get(source, f"attribution: {source}")
        return FinalizeResult(
            EXIT_FINDINGS,
            None,
            "finalize needs scope reconciliation answers (plan left unmoved).\n  "
            + source_note
            + "\nSupply them with:\n  "
            + reconcile.needs_input_command,
            evidence,
            tuple(findings_list),
        )

    if not apply:
        return FinalizeResult(
            EXIT_OK,
            None,
            "precheck + reconciliation passed; re-run with --apply to perform the terminal transaction.",
            evidence,
            (),
        )

    # Fold the verbatim reconciliation note into the attributed history message so the deviation is
    # permanently on the record and attributable.
    recon_note = _reconciliation_history_note(
        reconcile.reasons, reconcile.acks, widened
    )
    if recon_note:
        message = f"{message} [{recon_note}]"

    # --- E-02/E-03 forward transition, wrapped in the durable two-phase journal (Order 3xh53a) ---
    rec = _ss.read_artifact_record(plan_path, repo_root)
    if rec is None:
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"could not read plan record for {plan_path}.",
            evidence,
        )
    plan_id = (rec.id6 or "").strip() or Path(plan_path).name
    plan_rel = _repo_relative(repo_root, plan_path)

    # Acquire the exclusive finalize lock (a live second finalizer fails with a retry diagnostic).
    try:
        acquire_finalize_lock(repo_root, plan_id)
    except TransactionLockError as exc:
        return FinalizeResult(EXIT_CANNOT_RUN, None, str(exc), evidence)

    try:
        return _finalize_transaction(
            repo_root,
            plan_path,
            plan_rel,
            plan_id,
            rec,
            actor,
            message,
            evidence,
            fault_injection,
        )
    finally:
        release_finalize_lock(repo_root)


def _finalize_transaction(
    repo_root: Path,
    plan_path: Path,
    plan_rel: str,
    plan_id: str,
    rec,
    actor: str,
    message: str,
    evidence: Dict[str, Any],
    fault_injection: Optional[str],
) -> FinalizeResult:
    """The journaled two-phase terminal transaction (called under the finalize lock).

    Phases: PREPARED (snapshot) -> MUTATING (status edit + plan move, IN A COORDINATOR-OWNED
    WORKTREE) -> READY_TO_COMMIT -> commit THERE -> land in the shared checkout by a REFUSING
    fast-forward -> classify by OBSERVED state -> post-reconciliation index refresh ->
    post-transition -> COMPLETE. Any pre-commit failure/interrupt rolls back idempotently; a
    committed-incomplete transaction resumes via the SAME command with no history rewrite; ambiguous
    evidence is unknown-outcome (fail closed).

    WHERE THE MUTATIONS HAPPEN, AND WHAT THAT DOES AND DOES NOT BUY (plan `u23gbn`). The status edit,
    the plan move and the commit all happen in a throwaway worktree on its OWN branch, created and
    owned by the coordinator, so the SHARED checkout is never mid-move and is never the tree
    ``pre-commit`` stashes. MEASURED BEFORE the change, sampling `git status --porcelain` in the
    shared tree at two instants of a successful retirement: post-move it read
    ``RM <pending> -> <executed>`` and pre-commit ``R  <same>`` plus the two untracked manifests.

    THE WINDOW SHRINKS, IT DOES NOT VANISH, and this docstring says so because the stronger claim was
    measured FALSE. A ref that advances while the shared working tree still holds the old layout is
    WORSE than the window it replaces: HEAD says ``executed/`` while the tree holds ``pending/``,
    which reads as an unexplained REVERSE rename. So the shared tree is still written, by exactly ONE
    step: a ``git merge --ff-only`` that git itself performs, that updates the ref and the tree
    together, and that REFUSES rather than clobbers when a peer's uncommitted change is in the way
    (see :func:`land_worktree_commit`). Plus the post-reconciliation manifest refresh, which writes
    only gitignored generated views.

    WHICH LAYER COVERS WHICH FAILURE, since the journal and the worktree are complementary and
    deleting either would be a mistake:

    * THE WORKTREE shortens the WITHIN-INVOCATION exposure of the shared checkout. It cannot classify
      anything, and it does not survive the process.
    * THE JOURNAL covers ACROSS-INVOCATION crashes. ``PHASE_PREPARED``/``PHASE_MUTATING``/
      ``PHASE_READY_TO_COMMIT`` are rolled back idempotently on the next invocation;
      ``PHASE_COMMITTED_INCOMPLETE`` is RESUMED, never reverted; ``PHASE_UNKNOWN_OUTCOME`` fails
      closed. A compare-and-swap or a fast-forward can express none of that.

    A REFUSED RECONCILIATION IS NOT ``PHASE_COMMITTED_INCOMPLETE``. In this ordering the ff-only merge
    IS the branch advance, so a refusal leaves the lifecycle commit UNREACHABLE from the branch:
    nothing is committed as far as the branch is concerned, so the transaction rolls back and reports
    the refusal (or the race) honestly. ``PHASE_COMMITTED_INCOMPLETE`` is reached only AFTER the merge
    succeeded, which is also why a post-commit manifest-refresh failure lands there rather than being
    rolled back.
    """
    import argparse

    from agent_workflows import artifact_core as _core
    from agent_workflows import status_set as _ss

    plans_dir = _plans_dir_of(repo_root, plan_path)
    dest_rel = _repo_relative(repo_root, plans_dir / "executed" / Path(plan_path).name)
    # The generated plans manifests (INDEX.json/INDEX.md) are deliberately ABSENT here. They are
    # still REGENERATED by the MUTATING phase below (`_refresh_plans_index_fail_loud`, a fail-loud
    # gate), but they are generated output and are no longer committed by any `aw` verb, so naming
    # them here would (a) put a gitignored path in the `git add` set, which exits 1 and stages
    # NOTHING, wedging the whole transaction, and (b) make `_rollback_precommit`'s
    # `git restore --staged -- <p>` emit a spurious "pathspec did not match" error for an untracked
    # path, precisely when something has already gone wrong. `aw index plans --check` byte-compares
    # a rebuild against the file ON DISK, never against git, so it is unaffected.
    owned_paths = [plan_rel, dest_rel]

    def _fault(tag: str) -> None:
        if fault_injection == tag:
            raise _InjectedFault(tag)

    # --- RESUME: an existing journal means a prior attempt was interrupted. ---
    existing = read_finalize_journal(repo_root, plan_id)
    if existing is not None:
        phase = existing.get("phase")
        if phase in _PRE_COMMIT_PHASES:
            # Interrupted before the commit: finish rollback idempotently, then start fresh below.
            ok, msg = _rollback_precommit(repo_root, existing)
            if not ok:
                existing["phase"] = PHASE_UNKNOWN_OUTCOME
                existing["rollback_error"] = msg
                _write_finalize_journal(repo_root, existing)
                return FinalizeResult(
                    EXIT_CANNOT_RUN,
                    None,
                    f"prior interrupted finalize could not be rolled back ({msg}); journal retained "
                    "for recovery. NOT restored.",
                    evidence,
                )
            _clear_finalize_journal(repo_root, plan_id)
            # fall through to a fresh attempt
        elif phase == PHASE_COMMITTED_INCOMPLETE:
            return _resume_post_commit(repo_root, existing, plan_id, evidence)
        elif phase == PHASE_UNKNOWN_OUTCOME:
            return FinalizeResult(
                EXIT_CANNOT_RUN,
                None,
                f"finalize journal for {plan_id} is in unknown-outcome (ambiguous prior attempt); "
                f"resolve manually and clear {finalize_journal_path(repo_root, plan_id)}.",
                evidence,
                tuple(existing.get("findings", ())),
            )
        # PHASE_COMPLETE: a stale complete journal - clear and proceed fresh.
        else:
            _clear_finalize_journal(repo_root, plan_id)

    # --- PREPARED: snapshot everything needed to roll back, atomically, before any mutation. ---
    rc, pre_head, _err = _git(repo_root, ["rev-parse", "HEAD"])
    pre_head = pre_head.strip() if rc == 0 else "unversioned"
    try:
        original_bytes = plan_path.read_text(encoding="utf-8")
    except OSError as exc:
        return FinalizeResult(
            EXIT_CANNOT_RUN, None, f"cannot read plan: {exc}", evidence
        )

    # NOTE: the journal deliberately carries no `index_json_before`/`index_md_before` content
    # snapshot, and it STILL does not need one after plan `4xt6u4` - but the REASON changed, so read
    # this before reinstating them. Those keys once existed to restore the plans manifests on
    # rollback and nothing read them, because rollback regenerated the manifests from the corpus
    # instead; they were dead weight describing a restore that never happened, and they were removed
    # in `674f2c68`. `4xt6u4` then measured that the REGENERATION was itself the bug: it left
    # `?? INDEX.json` / `?? INDEX.md` in a tree that had none, so a failed transition did not leave
    # the tree as it found it. The fix removed the regeneration rather than adding a restore, because
    # NOTHING in the pre-commit phase writes the shared manifests (they are gitignored and the
    # mutations happen in a coordinator worktree - see
    # `_pre_commit_phase_leaves_manifests_untouched`), so there is nothing to restore and a snapshot
    # would be ~200 KB rewritten on every one of the journal's phase transitions.
    # WHEN A SNAPSHOT WOULD BECOME CORRECT: only if that invariant is broken, i.e. if some future
    # step writes the shared manifests BEFORE the commit. The test pinning the invariant is designed
    # to fail first in that case; do not add the keys back without breaking it.
    journal: Dict[str, Any] = {
        "schema_version": FINALIZE_JOURNAL_SCHEMA_VERSION,
        "plan_id": plan_id,
        "plan_digest": plan_content_digest(original_bytes),
        "original_path": plan_rel,
        "original_bytes": original_bytes,
        "dest_path": dest_rel,
        "pre_head": pre_head,
        "owned_paths": owned_paths,
        "git_index_entries": _git_index_entries(repo_root, owned_paths),
        "receipt_id": plan_id,
        "actor": actor,
        "message": message,
        "phase": PHASE_PREPARED,
        "created_at": _utc_now(),
    }
    _write_finalize_journal(repo_root, journal)

    def _rollback_and_return(
        reason: str, exit_code: int = EXIT_CANNOT_RUN
    ) -> FinalizeResult:
        cur = read_finalize_journal(repo_root, plan_id) or journal
        ok, msg = _rollback_precommit(repo_root, cur)
        if not ok:
            cur["phase"] = PHASE_UNKNOWN_OUTCOME
            cur["rollback_error"] = msg
            _write_finalize_journal(repo_root, cur)
            return FinalizeResult(
                exit_code,
                None,
                f"{reason}; rollback FAILED ({msg}); journal retained, repository NOT reported "
                "restored.",
                evidence,
            )
        _clear_finalize_journal(repo_root, plan_id)
        return FinalizeResult(
            exit_code, None, f"{reason}; rolled back to pre-finalize state.", evidence
        )

    # The subject grammar is `artifact_core`'s (IPD `zexed1` E-02), not a local literal: the pre-commit
    # gate and the run viewer's discrepancy classifier both MATCH what is produced here, and a
    # hand-written copy in any one of them drifts silently (see `artifact_core.finalize_commit_subject`).
    commit_msg = (
        f"{_core.finalize_commit_subject(plan_id)} {plan_id} -> executed"
        f"\n\n{message}\n\n"
        f"Executed by {actor} via aw ipd finalize."
    )

    # --- MUTATING + READY_TO_COMMIT + the commit, ALL IN A COORDINATOR-OWNED WORKTREE (`u23gbn`). ---
    #
    # WHAT MOVED AND WHY. These three used to happen in the SHARED checkout: the status edit and the
    # `git mv` there, then `commit_isolated` copying those paths into a private DETACHED worktree to
    # keep `pre-commit`'s stash off the shared tree. That left a real window in which the shared tree
    # held a moved-but-uncommitted plan (measured: `RM <pending> -> <executed>` at the post-move
    # instant). Now the mutation happens in the worktree too, so the shared tree is never mid-move.
    #
    # WHY NOT `commit_isolated`, which already exists for this. Its copy direction is SHARED ->
    # WORKTREE (`shutil.copy2(src, dst)` per named path, propagating a deletion when the shared source
    # is absent), so a mutation performed in a DIFFERENT worktree is invisible to it and the paths it
    # would be told to commit do not exist in the shared tree at all. MEASURED: it returns
    # `error` / "git add failed in isolated worktree: fatal: pathspec '<executed path>' did not match
    # any files", HEAD unmoved, nothing committed. It also performs the ref advance itself, under a
    # CAS, which is precisely the step that must NOT precede the fast-forward below. It is therefore
    # left entirely alone (it still backs `git_commit_helper.offer_commit`, the shared self-commit path
    # behind every other `aw` verb) and this path uses the `coordinator_worktree` sibling instead.
    #
    # THE PLAN'S CURRENT BYTES ARE MIRRORED IN, not read from HEAD, and that is behavior-preserving
    # rather than a nicety: MEASURED on the pre-change code, an executing agent's UNCOMMITTED evidence
    # edits to its own plan file are carried into the lifecycle commit today. Snapshotting HEAD instead
    # would silently drop them.
    from agent_workflows import commit_lock as _clock

    journal["phase"] = PHASE_MUTATING
    _write_finalize_journal(repo_root, journal)

    landed: Optional[str] = None
    landing: Optional[ReconcileLanding] = None
    stage = list(owned_paths)
    try:
        with _clock.coordinator_worktree(
            repo_root, label=plan_id, base=pre_head
        ) as coord:
            _fault("before_mutation")
            # Mirror the plan's CURRENT shared-tree bytes to the worktree copy, so an uncommitted
            # in-progress edit rides the transition exactly as it does today.
            wt_plan = coord.path / plan_rel
            wt_plan.parent.mkdir(parents=True, exist_ok=True)
            wt_plan.write_text(original_bytes, encoding="utf-8")
            wt_rec = _ss.read_artifact_record(wt_plan, coord.path)
            if wt_rec is None:
                raise RuntimeError(
                    f"could not read the plan record inside the coordinator worktree ({wt_plan})"
                )
            ns = argparse.Namespace(actor=actor, message=message, by_human=False)
            wt_dest, _norm = _ss.apply_status_change(wt_rec, "executed", coord.path, ns)
            dest_rel = _repo_relative(coord.path, wt_dest)
            # Record the moved bytes so rollback can distinguish our write from a concurrent one, and
            # so the post-reconciliation checks read the same content the commit carries.
            try:
                journal["moved_bytes"] = wt_dest.read_text(encoding="utf-8")
            except OSError:
                journal["moved_bytes"] = None
            journal["dest_path"] = dest_rel
            journal["worktree_branch"] = coord.branch
            _write_finalize_journal(repo_root, journal)
            _fault("after_move")

            # Stage only paths that still EXIST: `git mv` already staged the rename and removed the
            # old path from disk, and `git add` on a vanished path exits 128 ("pathspec did not match
            # any files"), which would abort the whole transaction. The rename is already in this
            # worktree's index, so the commit carries BOTH halves of the move.
            owned_paths = [plan_rel, dest_rel]
            stage = list(owned_paths)
            add_paths = [p for p in owned_paths if (coord.path / p).exists()]
            if add_paths:
                rc, _out, err = _git(coord.path, ["add", "--", *add_paths])
                if rc != 0:
                    raise RuntimeError(
                        f"git add failed in the coordinator worktree ({err.strip()})"
                    )
            journal["phase"] = PHASE_READY_TO_COMMIT
            journal["staged"] = stage
            journal["owned_paths"] = owned_paths
            _write_finalize_journal(repo_root, journal)
            _fault("before_commit")

            # The REAL commit, hooks and all, in a tree nothing else writes to. `pre-commit` stashes
            # and restores HERE, so a peer's in-flight write in the shared tree cannot be clobbered by
            # us. NO pathspec: this worktree's index holds exactly our own rename.
            rc, out, err = _git(coord.path, ["commit", "-m", commit_msg])
            if rc != 0:
                combined = f"{out}\n{err}".strip()
                raise _CommitRefused(
                    f"the lifecycle commit was rejected in the coordinator worktree (hooks ran): "
                    f"{combined}"
                )
            rc, sha, err = _git(coord.path, ["rev-parse", "HEAD"])
            if rc != 0:
                raise RuntimeError(f"cannot resolve the worktree commit: {err.strip()}")
            landed = sha.strip()
            journal["worktree_commit"] = landed
            _write_finalize_journal(repo_root, journal)

            # Release THIS TRANSACTION'S OWN uncommitted edit to the plan file, and nothing else, so
            # the fast-forward is not blocked by the very bytes it is landing. Provably lossless (the
            # bytes are verified to be our own mirror input AND to be carried by the landed commit) and
            # a no-op in every other case, including a peer's edit, which must keep refusing below.
            released = _release_own_plan_edit_before_landing(
                repo_root,
                plan_rel,
                landed=landed,
                dest_rel=dest_rel,
                mirrored_bytes=original_bytes,
                committed_bytes=journal.get("moved_bytes"),
            )
            if released:
                evidence.setdefault("reconciliation_prep", []).append(released)

            # --- LAND IT: the ff-only merge is the SINGLE step that advances the branch AND updates
            # the shared working tree. Never `update-ref` first (that makes this a reporting-success
            # no-op and hides the peer-protecting refusal), and never force a refusal.
            landing = land_worktree_commit(repo_root, landed, expected_base=pre_head)
    except _InjectedFault as exc:
        return _rollback_and_return(f"fault-injected finalize failure ({exc})")
    except _CommitRefused as exc:
        # A hook rejection. Nothing landed and the branch never moved, so the shape the classification
        # below expects is a nonzero rc plus operator-facing text.
        rc, err = 1, str(exc)
    except Exception as exc:
        return _rollback_and_return(f"finalize mutation failed ({exc})")
    else:
        assert landing is not None
        if landing.status == RECONCILED_OK:
            rc, err = 0, ""
        else:
            # REFUSED or RACED. In this ordering the ff-only merge IS the branch advance, so the
            # lifecycle commit is NOT reachable from the branch and nothing is committed as far as the
            # branch is concerned: rolling back is correct and loses nothing, because the coordinator
            # worktree's commit was deliberately abandoned with its branch.
            rc, err = 1, landing.detail
            evidence["reconciliation"] = {
                "status": landing.status,
                "returncode": landing.returncode,
                "paths": list(landing.paths),
                "detail": landing.detail,
            }

    dest_path = repo_root / journal["dest_path"]

    # --- CLASSIFY the commit boundary by OBSERVED repository state (E-03). ---
    lifecycle_commit = _lifecycle_commit_exists(repo_root, pre_head, plan_id)
    rc_head, cur_head, _e = _git(repo_root, ["rev-parse", "HEAD"])
    cur_head = cur_head.strip() if rc_head == 0 else pre_head
    if lifecycle_commit is None:
        if cur_head == pre_head:
            # No lifecycle commit: pure pre-commit failure -> rollback.
            # Diagnose a FOREIGN cause (a concurrent writer inside pre-commit's stash window) so the
            # recorded reason does not imply this plan or its Set was at fault. Still fails closed.
            foreign = classify_commit_refusal(repo_root, err, stage)
            base = f"lifecycle commit did not happen (git rc={rc}: {err.strip()})"
            return _rollback_and_return(
                f"{base}\nDIAGNOSIS: {foreign}" if foreign else base,
                EXIT_CANNOT_RUN,
            )
        # HEAD moved but not via our marker: ambiguous -> unknown-outcome (fail closed).
        journal["phase"] = PHASE_UNKNOWN_OUTCOME
        journal["observed_head"] = cur_head
        _write_finalize_journal(repo_root, journal)
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"unknown-outcome: HEAD moved to {cur_head[:12]} but not via this finalize's lifecycle "
            f"commit; journal retained at {finalize_journal_path(repo_root, plan_id)}.",
            evidence,
        )

    # The lifecycle commit exists -> committed-incomplete until post-transition passes.
    journal["phase"] = PHASE_COMMITTED_INCOMPLETE
    journal["lifecycle_commit"] = lifecycle_commit
    _write_finalize_journal(repo_root, journal)

    # --- THE FAIL-LOUD PLANS-INDEX REFRESH, DELIBERATELY AFTER THE RECONCILIATION (`u23gbn` E-07). ---
    #
    # THIS ORDERING IS LOAD-BEARING, NOT TIDINESS. The refresh regenerates the manifests by SCANNING
    # THE PLANS TREE ON DISK and then re-runs `--check`, RAISING if it did not converge. While the
    # relocation happened in the shared tree, running it inside the mutating phase was correct: the
    # disk already showed the plan at `executed/`. Once the relocation moved into the coordinator
    # worktree, the shared disk still showed `pending/` at that point, so the manifest was generated
    # describing the OLD layout, converged against it, and the gate PASSED -- and then the merge
    # relocated the file and the manifest was instantly stale. MEASURED: the manifest named the
    # `pending/` path and not the `executed/` one, and `aw index plans --check` returned rc=1 with
    # `check.stale-index-stale` on BOTH manifests, which is exactly the state the gate exists to
    # prevent, reported as success. So the gate did not merely mis-order, it INVERTED.
    #
    # DO NOT INSTEAD REGENERATE IN THE WORKTREE. The manifests are GITIGNORED, so a fresh worktree
    # never receives them, a regeneration there is discarded with the worktree, and the shared copies
    # keep their stale bytes.
    #
    # A FAILURE HERE IS NOW POST-COMMIT, hence COMMITTED-INCOMPLETE rather than a rollback: the journal
    # is already in that phase above, the commit has LANDED, and a landed lifecycle commit is resumed,
    # never reverted. The remedy is mechanical and local (`aw index plans`), because the manifests are
    # gitignored generated views that no `aw` verb commits.
    try:
        _refresh_plans_index_fail_loud(repo_root)
        _fault("after_index")
    except Exception as exc:
        evidence["plans_index_refresh"] = {"error": str(exc)}
        return FinalizeResult(
            EXIT_FINDINGS,
            lifecycle_commit,
            f"finalize is COMMITTED-INCOMPLETE for {plan_id}: the lifecycle commit "
            f"{lifecycle_commit[:12]} LANDED, but the fail-loud plans-index refresh did not converge "
            f"({exc}). The commit is NOT rolled back (a landed lifecycle commit is resumed, never "
            "reverted) and the manifests are gitignored generated views, so the remedy is to run "
            f"`aw index plans` and then re-run the SAME command to resume.",
            evidence,
            (f"plans-index refresh failed after the lifecycle commit: {exc}",),
        )

    return _complete_after_commit(
        repo_root, dest_path, plan_id, lifecycle_commit, actor, evidence
    )


def _complete_after_commit(
    repo_root: Path,
    dest_path: Path,
    plan_id: str,
    commit_hash: str,
    actor: str,
    evidence: Dict[str, Any],
) -> FinalizeResult:
    """Run post-transition lint on the committed plan; mark COMPLETE on pass, else committed-incomplete."""
    from agent_workflows import ipd_lint as _lint

    try:
        post = _lint.lint_file(dest_path, checkpoint="post-transition")
        evidence["post_transition"] = {
            "disposition": post.disposition,
            "diagnostics": [f"{d.code} {d.message}" for d in post.diagnostics],
        }
        post_ok = post.passing
    except Exception as exc:
        evidence["post_transition"] = {"error": str(exc)}
        post_ok = False

    if not post_ok:
        # committed-incomplete: do NOT amend/reset/re-commit; report the same-command resume.
        return FinalizeResult(
            EXIT_FINDINGS,
            commit_hash,
            f"finalize is COMMITTED-INCOMPLETE for {plan_id}: the lifecycle commit {commit_hash[:12]} "
            "exists but post-transition validation failed. Re-run the SAME command "
            f"`aw ipd finalize {plan_id} --actor <a> --message <m> --apply` to resume (no second "
            "commit); if it still fails, open a corrective follow-up IPD citing it.",
            evidence,
            tuple(evidence.get("post_transition", {}).get("diagnostics", ())),
        )

    # COMPLETE: post-transition passed. Finalize the journal + consume the receipt.
    journal = read_finalize_journal(repo_root, plan_id)
    if journal is not None:
        journal["phase"] = PHASE_COMPLETE
        _write_finalize_journal(repo_root, journal)
    _clear_finalize_journal(repo_root, plan_id)
    # Consume the begin receipt (the transaction is cleanly complete).
    try:
        receipt_path_for(repo_root, plan_id).unlink()
    except OSError:
        pass

    return FinalizeResult(
        EXIT_OK,
        commit_hash,
        f"finalized {plan_id} -> executed at {commit_hash[:12]} (actor {actor})."
        + _disregarded_unowned_note(evidence),
        evidence,
        (),
    )


def _disregarded_unowned_note(evidence: Dict[str, Any]) -> str:
    """Render the E-03 disregarded-unowned paths for a human message (empty when there are none).

    Surfaces what the ownership filter set aside so it is visible in the terminal output, not only
    in the recorded scope audit. Says DISREGARDED, not "in scope": these paths were neither
    justified nor attributed to this execution.

    Like the precheck's twin message, it states only what the code can substantiate: that the path is
    outside the declared ``Scope-Paths`` and could not be attributed to this execution. It names no
    sha and blames no actor, because nothing available identifies who committed a path. The word
    "uncommitted" was dropped when scopeattr `h9cn0y` made the COMMITTED half filterable too.
    """
    paths = list(
        (evidence.get("scope_audit", {}) or {}).get("disregarded_unowned_paths", [])
        or []
    )
    if not paths:
        return ""
    return (
        " Disregarded "
        + str(len(paths))
        + " path(s) not owned by this execution (left untouched, recorded in the scope "
        "audit): " + ", ".join(paths) + "."
    )


def _resume_post_commit(
    repo_root: Path, journal: Dict[str, Any], plan_id: str, evidence: Dict[str, Any]
) -> FinalizeResult:
    """Resume a COMMITTED-INCOMPLETE transaction by the SAME command: verify + re-run post-transition.

    Performs NO second lifecycle mutation/commit. Verifies the recorded commit still exists, then
    reruns only post-transition validation on the executed plan; marks complete on pass.
    """
    commit_hash = journal.get("lifecycle_commit")
    dest_rel = journal.get("dest_path")
    if not commit_hash or not dest_rel:
        journal["phase"] = PHASE_UNKNOWN_OUTCOME
        _write_finalize_journal(repo_root, journal)
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"committed-incomplete journal for {plan_id} is missing commit/dest evidence; "
            "unknown-outcome (fail closed).",
            evidence,
        )
    # Verify the recorded lifecycle commit still exists in history.
    rc, _out, _err = _git(repo_root, ["cat-file", "-e", f"{commit_hash}^{{commit}}"])
    if rc != 0:
        journal["phase"] = PHASE_UNKNOWN_OUTCOME
        _write_finalize_journal(repo_root, journal)
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"recorded lifecycle commit {commit_hash[:12]} for {plan_id} not found; unknown-outcome.",
            evidence,
        )
    dest_path = repo_root / dest_rel
    if not dest_path.is_file():
        journal["phase"] = PHASE_UNKNOWN_OUTCOME
        _write_finalize_journal(repo_root, journal)
        return FinalizeResult(
            EXIT_CANNOT_RUN,
            None,
            f"executed plan {dest_rel} not found on resume; unknown-outcome.",
            evidence,
        )
    return _complete_after_commit(
        repo_root,
        dest_path,
        plan_id,
        commit_hash,
        journal.get("actor", "unknown"),
        evidence,
    )


def _plans_dir_of(repo_root: Path, plan_path: Path) -> Path:
    """The plans root (parent of the disposition dir) for ``plan_path``."""
    return plan_path.parent.parent


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

    # wtiso-03 E-05: a managed WORKER may not create lifecycle authority. Checked FIRST, before any
    # selector resolution / gate / receipt write, so the refusal has no side effect at all. The
    # driver's own in-process `driver_begin` runs in the COORDINATOR role and is unaffected.
    if worker_role_active(os.environ):
        return _refuse_worker_role_verb("begin")

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

    # lanetruth-02 (z2isfg): the DRIVER, not this process, knows whether the turn it is gating will
    # execute in a fresh isolated worktree or in this very tree, so the caller must be able to declare
    # it. The transport is the `AW_ISOLATED_BASELINE` env var rather than a new CLI flag: OQ-02
    # resolved that `--dir` must keep meaning "the repo root" (the receipt stays under the main repo's
    # state root), and this plan's scope fence excludes `agent_workflows/cli.py`, where a new flag
    # would have to be declared. Absent or any value other than "1" means today's behavior, so an
    # operator's plain `aw ipd begin` is unaffected and the gate stays fail-closed by default.
    isolated_baseline = os.environ.get("AW_ISOLATED_BASELINE") == "1"

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

    result = begin(
        repo_root,
        plan_path,
        actor or "",
        timestamp=now,
        isolated_baseline=isolated_baseline,
    )

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


def _parse_scope_reason_flags(values: Optional[List[str]]) -> Dict[str, str]:
    """Parse repeatable ``--scope-reason <path>=<why>`` flags into {path: why}."""
    out: Dict[str, str] = {}
    for raw in values or []:
        if "=" not in raw:
            continue
        path, why = raw.split("=", 1)
        path = path.strip()
        why = why.strip()
        if path and why:
            out[path] = why
    return out


def _parse_scope_ack_flags(values: Optional[List[str]]) -> Dict[str, str]:
    """Parse repeatable ``--scope-ack <path>[=<note>]`` flags into {path: note-or-'acknowledged'}."""
    out: Dict[str, str] = {}
    for raw in values or []:
        if "=" in raw:
            path, note = raw.split("=", 1)
            path = path.strip()
            note = note.strip() or "acknowledged"
        else:
            path = raw.strip()
            note = "acknowledged"
        if path:
            out[path] = note
    return out


def _tty_scope_prompt(
    out_of_scope: List[str], in_scope_unmodified: List[str]
) -> Dict[str, Any]:
    """ONE batched TTY prompt collecting all reasons (out-of-scope) + acks (in-scope-unmodified)."""
    reasons: Dict[str, str] = {}
    acks: Dict[str, str] = {}
    if out_of_scope:
        print(
            "Scope reconciliation - these paths were changed but are OUTSIDE the reviewed "
            "Scope-Paths. Give a short reason for each (empty = refuse):"
        )
        for p in out_of_scope:
            try:
                why = input(f"  reason for {p}: ").strip()
            except EOFError:
                why = ""
            if why:
                reasons[p] = why
    if in_scope_unmodified:
        print(
            "These paths were DECLARED in Scope-Paths but NOT modified. Acknowledge each "
            "(e.g. 'not-needed'; blank = 'acknowledged'):"
        )
        for p in in_scope_unmodified:
            try:
                note = input(f"  acknowledge {p}: ").strip()
            except EOFError:
                note = ""
            acks[p] = note or "acknowledged"
    return {"reasons": reasons, "acks": acks}


def run_finalize(args) -> int:
    """Entry point for `aw ipd finalize <plan> --actor --message [--apply]`. Returns 0/1/2."""
    from agent_workflows import selectors
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic as OutDiag,
        select_output,
    )

    # wtiso-03 E-05: see `run_begin`. Checked FIRST so a worker-role finalize performs NO transition,
    # commit, or plan move. The driver's own `driver_finalize` runs in the coordinator role.
    if worker_role_active(os.environ):
        return _refuse_worker_role_verb("finalize")

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

    # Order 05: collect the non-interactive reconciliation answers from repeatable flags.
    scope_reasons = _parse_scope_reason_flags(getattr(args, "scope_reason", None))
    scope_acks = _parse_scope_ack_flags(getattr(args, "scope_ack", None))
    # Interactive ONLY on a real TTY in the human (non-agent/json) output mode.
    #
    # ttywedge Order 01 (g40w37): stdin.isatty() ALONE is not consent. A driver spawns this command
    # with stdout/stderr piped but stdin INHERITED, so the child sees the operator's terminal, decides
    # it may prompt, and blocks on input() forever for an answer nobody can type, because the prompt
    # itself went into a pipe. That wedged a real finalize for 1h49m holding its run lock, leaving the
    # plan `approved` in pending/ while the run reported `complete`. Hence two extra conditions:
    #   - stdout must ALSO be a TTY: if the prompt is not readable by a human, do not ask.
    #   - an explicit AW_NONINTERACTIVE/CI signal forces non-interactive regardless of the streams.
    # These only ADD conditions, so a genuine human terminal session still prompts exactly as before.
    # Non-interactive here is fail-CLOSED: finalize returns the scope-reconciliation refusal naming the
    # required --scope-reason/--scope-ack flags, which is recoverable, instead of hanging, which is not.
    import os as _os
    import sys as _sys

    def _is_tty(stream: object) -> bool:
        try:
            return bool(getattr(stream, "isatty", None) and stream.isatty())  # type: ignore[union-attr]
        except (ValueError, OSError):
            # A detached/closed stream is not a terminal.
            return False

    forced_noninteractive = any(
        str(_os.environ.get(var, "")).strip().lower() not in ("", "0", "false", "no")
        for var in ("AW_NONINTERACTIVE", "CI")
    )
    interactive = (
        not (ctx.is_agent or ctx.is_json)
        and not forced_noninteractive
        and _is_tty(_sys.stdin)
        and _is_tty(_sys.stdout)
    )
    prompt = _tty_scope_prompt if interactive else None

    result = finalize(
        repo_root,
        plan_path,
        actor or "",
        message or "",
        apply=apply,
        scope_reasons=scope_reasons,
        scope_acks=scope_acks,
        interactive=interactive,
        prompt=prompt,
        plan_selector=selector,
    )

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

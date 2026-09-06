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

EIGHT symbols call something they cannot reach from here. Each takes it as a keyword-only parameter;
each runner wraps it at the original name and signature, so NO call site in either runner was
rewritten. The parenthetical says why the dependency could not simply move too:

  * `run_checked(..., env_builder=)`         <- `pinned_child_env`   (opencode-only, host-specific)
  * `save_state(..., write_report=)`         <- `write_report`       (DIVERGED)
  * `discover_plans(..., parse_plan_file=)`  <- `parse_plan_file`    (DIVERGED; and it is also what
                                                 constructs each runner's OWN `PlanRecord`, which are
                                                 different NamedTuples - oc's carries a `kind` field
                                                 agy's lacks - so injecting the parser is what keeps
                                                 each driver's record type its own)
  * `validate_manifest(..., parse_dependency_token=)`               (opencode-only)
  * `print_status(..., driver_label=)`       <- the host's own name  (the sole host-naming-only symbol
                                                 of the 34: the two bodies differed ONLY by the
                                                 literal 'opencode' vs 'antigravity')
  * `git_head(..., run_checked=)`            <- `run_checked`        (see below)
  * `git_status(..., run_checked=)`          <- `run_checked`        (see below)
  * `git_common_dir(..., run_checked=)`      <- `run_checked`        (see below)

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

import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, NamedTuple, Sequence, TextIO

from agent_workflows.render_stream import Palette, render_run_summary_table

# ---- module constants the moved bodies close over ------------------------------------------------
# Byte-identical in both runners (verified by comparing the assignment VALUES at the AST level), so
# they move rather than being injected. Both runners re-export them, leaving their other call sites
# unchanged.

SCHEMA_VERSION = 1

ID6_RE = re.compile(r"^[a-z0-9]{6}$")

_SET_RE = re.compile(r"(?m)^-\s*Set:\s*(.+?)\s*$")
_ORDER_RE = re.compile(r"(?m)^-\s*Order:\s*(\d+)\s*$")


# ---- errors --------------------------------------------------------------------------------------
# ONE `DriverError` for the package. It was previously defined in BOTH runners as two DISTINCT
# classes, which is why `agy_runipd` carried a wrapper whose only job was to catch oc's class and
# re-raise its own as a translation. `StallTimeout` subclasses it in each runner (their docstrings
# differ, so those classes are DIVERGED and stay put); re-parenting them onto this ONE class is what
# makes every `except DriverError` in either runner catch the other's stall.


class DriverError(RuntimeError):
    pass


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


def state_root(repo: Path) -> Path:
    return repo / ".aw" / "records" / "runs"


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


def _run_git(repo: Path, args: list[str]) -> tuple[int, str, str]:
    """Run a git command in ``repo``; return (returncode, stdout, stderr)."""
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.returncode, proc.stdout, proc.stderr


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

    Deliberately NOT a runner `PlanRecord`. Those are per-runner NamedTuples with plan-shaped fields
    (`kind`, `order`, `dependencies`) that a spec does not have, and `discover_plans` has to INJECT
    `parse_plan_file` precisely because the two runners' records disagree. A spec needs none of that:
    the dispatch table (`run_selection_policy._SPEC_ACTIONS`) keys on STATUS alone, so this record
    carries status and identity and stops there rather than inventing spec analogues of plan fields.

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
      * ``kind``        - ``"bool"`` (a `BooleanOptionalAction`, matching shipped `--full-auto`) or
                          ``"int"``.
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


#: The `resume` re-declaration rules, named rather than spelled inline at each comparison.
RESUME_REFUSE = "refuse"
RESUME_NONE_DEFAULT = "none-default"

#: Spec 25kzda 2.1's NINE policy flags, in the order the spec's grammar block lists them.
#:
#: `--allow-drafts` JOINED THIS TABLE with `revsweep-02` (`6ypimw`), which implemented spec 2.5a's
#: draft admission gate. `uyeko5` deliberately left it out (it owned the other eight and registering a
#: ninth as a refusal would have collided on these lines for no gain); it is registered here now that
#: its BEHAVIOR ships, which is this table's own rule - a flag never parses and silently does nothing.
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

    frozen: dict = {}
    for row in RUN_POLICY_FLAGS:
        if not row.freeze:
            continue
        if row.dest == "retry_budget":
            frozen[row.dest] = resolve_retry_budget(getattr(args, row.dest, None))
        else:
            frozen[row.dest] = bool(getattr(args, row.dest, False) or False)
    if frozen.get("full_auto"):
        frozen["unattended"] = True
    return frozen


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
# GUIDING_PRINCIPLES P8 forbids, and `discover_plans` above cannot serve: it INJECTS the host's
# `parse_plan_file` precisely because the two runners' `PlanRecord` types disagree, and a shared
# decision must not depend on which host called it.
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

    Deliberately NOT a runner `PlanRecord`: those are per-host NamedTuples (oc's carries a `kind`
    agy's lacks), which is exactly why `discover_plans` has to inject `parse_plan_file`. A retirement
    DECISION must be identical on both hosts, so it reads a host-neutral record of its own.

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
    """

    from agent_workflows import (
        ipd_schema as _ipd_schema,
    )  # local: see the section note above

    heading = getattr(_ipd_schema, "H_CHILD_IPDS", _CHILD_IPDS_HEADING)
    tokens: list[str] = []
    in_section = False
    saw_row = False
    for raw in (orchestrator_text or "").splitlines():
        if raw.startswith("## "):
            in_section = raw[3:].strip() == heading
            continue
        if not in_section:
            continue
        row = _TABLE_ROW_RE.match(raw)
        if not row:
            continue
        cells = [c.strip() for c in row.group("body").split("|")]
        if not cells:
            continue
        first = cells[0]
        if not first:
            continue
        if all(_TABLE_SEPARATOR_CELL_RE.match(c or "-") for c in cells if c != ""):
            continue  # alignment row: layout, not a declared child
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

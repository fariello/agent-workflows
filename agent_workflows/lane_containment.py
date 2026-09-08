"""The ONE host-neutral home for lane containment rules both host drivers consume.

Spec `7ckptx` R2.6 requires this module to EXIST AND BE DECLARED rather than improvised into one
driver and imported from the other (which would make one host the de-facto shared library, i.e. the
opposite of host-neutral). Plan `cqx5v7` is the first plan of Set `lanectn` and therefore CREATES it;
later children of that Set EXTEND it.

WHAT LIVES HERE (and what deliberately does not):

  * R1.1/R1.3 the projection of every WORKER-FACING path into the lane, so an isolated turn's prompt
    names nothing outside its own workspace, while a NON-isolated turn is untouched.
  * R1.2/R1.4 the isolation notice text: cwd is the whole authorized workspace, no exception clause,
    and the ONE missing-input token form so the strictness ships with its escape hatch.
  * R2.1/R2.2/R2.4 collection of the worker's lane-side submissions back to the paths the driver's own
    readers already use, by COPY, tolerating a turn that submitted nothing.
  * R2.3 idempotent merge of the lane's contribution into the RUN-WIDE decisions register.
  * R2.5 the attempt-keyed collection receipt, which is the AUTHORITATIVE answer to "was this lane's
    submission collected?" (child `xdr83v`'s retention classification consumes it).

  * R3 the missing-input REPORT-AND-REFUSE cycle (child `y5od1h`): the token emit/parse, the
    coordinator-side classification, the refusal record, and the lane pause.

    UPDATED BY `604wra` (spec R6.1), because the note here used to point the wrong way. It said the
    emit/parse bodies lived in `wtiso_gate` and that this module carried "only the token's DOCUMENTED
    FORM". The DIRECTION IS NOW THE REVERSE: `format_missing_input_token` /
    `parse_missing_input_token` BELOW are the single definitions, and
    `wtiso_gate.format_missing_input` / `parse_missing_input` are one-line DELEGATIONS to them, so
    the gate library's stable-code surface and this rule cannot fork. What `wtiso_gate` does own is
    the stable ERROR CODE `AW_MISSING_INPUT`, which this module imports for
    `MISSING_INPUT_TOKEN_FORM` rather than retyping.

HONEST LIMIT, stated because spec Goal 5 requires it and because overstating it is the failure mode:
everything here is SIGNAL PURITY plus DRIVER-SIDE BOOKKEEPING, not a boundary. Nothing in this module
prevents a worker with shell access from writing outside its lane; `host_sandbox_profile`'s own
docstring records that prose, hooks, environment variables and Python role checks cannot enforce that.
What this module guarantees is that the instructions no longer ASK the worker to leave the lane, and
that a worker which stays inside it does not lose its work.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, NamedTuple

from agent_workflows import runner_shared

# The STABLE ERROR CODE for a missing-input report, imported rather than retyped (`604wra`, spec
# R6.1). `wtiso_gate` declares the code vocabulary a hook prints and a driver matches on; this module
# composes the worker-facing token form around it (see `MISSING_INPUT_TOKEN_FORM`). Import-safe in
# this direction: `wtiso_gate` has NO runtime module-level imports of its own, so there is no cycle,
# and its own delegations to this module are deliberately function-local for the same reason.
from agent_workflows.wtiso_gate import AW_MISSING_INPUT as _AW_MISSING_INPUT

# ---- where a worker's submissions live, inside the lane -------------------------------------------

#: Lane-relative home for everything an isolated worker submits back to the driver.
#:
#: Under `.aw/state/` ON PURPOSE: that prefix is gitignored (see `.gitignore`), and the lane is a
#: `git worktree` of the same commit, so the ignore rule applies inside the lane too. A submission
#: therefore never shows up as a dirty TRACKED path in the lane and cannot contaminate the
#: integration diff. Contrast `.aw/lane-scratch/` (the hardened profile's channel), which is NOT
#: ignored; that difference is why this does not reuse it.
LANE_SUBMISSION_SUBDIR = ".aw/state/lane-submissions"

#: The literal token form an isolated worker uses to report a genuinely missing input (spec R1.4,
#: R3.1). The PROMPT text and the parser both derive from this one constant, so the instruction a
#: worker reads and the code that reads its output cannot disagree about the shape.
#:
#: THE LEADING CODE IS IMPORTED, NOT RETYPED (`604wra`, spec R6.1). `wtiso_gate.AW_MISSING_INPUT` is
#: the STABLE ERROR CODE, declared there with the rest of the contract a hook prints and a driver
#: matches on; this composes the human-facing form around it. It was previously spelled out here as a
#: literal, which is the fork R6.1 forbids even while the copies agree: renaming the code would have
#: left this prompt text publishing the old spelling, and a worker following the prompt would emit a
#: token no parser recognized. `_token_prefix()` reads the prefix back OUT of this string, so all
#: three surfaces - the code, the prompt, the parser - now trace to a single definition.
MISSING_INPUT_TOKEN_FORM = (
    _AW_MISSING_INPUT + ":<repo-relative-path>:<why it is required>"
)

#: Names of the submission files a worker may write inside its lane, and the driver-side reader each
#: one feeds. Kept as data so the projection, the collection, and the receipt cannot disagree about
#: the set.
DECISIONS_NAME = "decisions-and-questions.md"
REPORT_NAME = "execution-report.md"


class WorkerPaths(NamedTuple):
    """The paths a turn's prompt names, plus the lane-side sources collection reads.

    `prompt_*` fields are what the WORKER is told. For an isolated turn they are LANE-RELATIVE
    (relative to the worker's cwd, which is the lane root), so the emitted prompt contains no
    absolute path outside the lane. For a non-isolated turn they are exactly the absolute driver-side
    paths that shipped before this change, byte for byte (spec R1.3).

    `lane_*` fields are absolute lane-side paths and are `None` for a non-isolated turn. They exist
    so collection reads the same locations the prompt named, from one computation rather than two.
    """

    prompt_run_dir: str
    prompt_run_dir_label: str
    prompt_decisions: str
    prompt_outcome: str
    prompt_report: str
    prompt_report_label: str
    prompt_plan: str
    lane_root: Path | None
    lane_submission_root: Path | None
    lane_decisions: Path | None
    lane_outcome: Path | None
    lane_report: Path | None


def attempt_key(item: dict[str, Any]) -> int:
    """The 1-based attempt number this turn's lane paths are keyed by (spec R2.3).

    Read from the item's own attempt ledger rather than passed in, so the driver's prompt build and
    its later collection derive the SAME key without a second parameter to keep in sync. `execute_item`
    appends the current attempt BEFORE building the lane prompt, so this equals that attempt's number;
    a caller with no ledger (a unit test, a `--prepare-only` inspection) gets 1.
    """
    attempts = item.get("attempts") or []
    return max(len(attempts), 1)


def item_slug(item: dict[str, Any]) -> str:
    """`<NN>-<id6>`, the existing driver-side outcome file stem, reused as the lane key."""
    return f"{int(item['position']):02d}-{item['id6']}"


def lane_submission_root(
    lane_root: Path, run_id: str, item: dict[str, Any], attempt: int | None = None
) -> Path:
    """`<lane>/.aw/state/lane-submissions/<run-id>/<NN>-<id6>/attempt-<N>`.

    KEYED ON ALL THREE of run, item, and attempt (spec R2.3, plan E-01) because all three can
    legitimately collide otherwise: a RESUMED run re-enters with the same item, `requeue_interrupted`
    RETRIES an interrupted item in the same run, and `allocate_worktree` may ADOPT an existing lane
    directory whose previous occupant left submissions behind. A shared directory would let a retry
    read the previous attempt's outcome and report it as this attempt's result.
    """
    n = attempt_key(item) if attempt is None else attempt
    return (
        Path(lane_root)
        / LANE_SUBMISSION_SUBDIR
        / str(run_id)
        / item_slug(item)
        / f"attempt-{n}"
    )


def prepare_lane_submission_dir(paths: WorkerPaths) -> None:
    """Create the lane-side submission tree BEFORE the turn, so the worker only has to write files.

    Called by the driver right after it projects the paths. Tolerates a non-isolated turn (nothing to
    create) and an already-existing tree (an adopted lane, a retry). It creates the `outcomes/`
    subdirectory too, because the outcome path the prompt names is nested and a worker that has to
    `mkdir -p` first is a worker that can get that wrong.
    """
    if paths.lane_submission_root is None or paths.lane_outcome is None:
        return
    paths.lane_outcome.parent.mkdir(parents=True, exist_ok=True)


#: Keys of a prior-attempt record that are safe to show an ISOLATED worker: none of them can carry a
#: filesystem path. Everything else is dropped rather than rewritten, because a truncated or
#: relativized path would be a claim about a location the worker cannot reach.
_PRIOR_ATTEMPT_SAFE_KEYS = (
    "number",
    "started_at",
    "ended_at",
    "interrupted_at",
    "interrupt_reason",
    "exit_code",
    "disposition",
    "verification",
    "recovery",
    "action",
    "stall_timeout",
    "starting_head",
    "ending_head",
    "starting_branch",
    "ending_branch",
    "worktree_branch",
    "worktree_lane_id",
    "worktree_base",
    "worktree_disposition",
    "integration_signal",
    "integration_detail",
    "finalize_refused",
    "begin_refused",
    "cost",
    "tokens",
)


def prior_attempt_summary(
    prior: dict[str, Any] | None, lane_root: Path | None
) -> dict[str, Any] | None:
    """The prior-attempt facts a RECOVERY prompt may state (spec R1.1).

    WHY THIS EXISTS, and it is not cosmetic: the recovery prompt interpolated the WHOLE prior attempt
    record, which carries `prompt`, `log`, and `worktree` as ABSOLUTE driver-side paths. So a resumed
    isolated turn emitted out-of-lane paths through a route the projection above never touches, and a
    check that only looked at the five named path lines would have reported R1.1 satisfied while the
    prompt still named the main checkout several times.

    A non-isolated turn gets the record UNCHANGED (spec R1.3). An isolated turn gets an allow-listed
    projection: timing, exit code, disposition, commit shas, and the lane BRANCH identity, which are
    the facts a resuming worker can actually act on. Path-valued keys are DROPPED, not rewritten.
    """
    if prior is None:
        return None
    if lane_root is None:
        return prior
    return {k: prior[k] for k in _PRIOR_ATTEMPT_SAFE_KEYS if k in prior}


def project_worker_paths(
    *,
    item: dict[str, Any],
    run_id: str,
    run_dir: Path,
    plan_path: Path,
    lane_root: Path | None,
) -> WorkerPaths:
    """Compute every worker-facing path for one turn (spec R1.1, R1.3; plan E-01).

    NON-ISOLATED (`lane_root is None`): returns the absolute driver-side paths unchanged, so the
    emitted prompt is byte-identical to the pre-change output for the same inputs. That branch is
    protected by spec R1.3 and by `V-01`'s digest comparison.

    ISOLATED: returns POSIX-style paths RELATIVE to the lane root. Relative rather than
    lane-absolute for two reasons: it satisfies R1.1 by construction (a relative path cannot BE an
    absolute out-of-lane path), and it reinforces R1.4's statement that the cwd is the whole
    workspace. The plan file is projected too when it lies inside the lane; if it somehow does not,
    the absolute path is returned rather than a fabricated one, because inventing a lane path for a
    file that is not there would send the worker to a nonexistent file.
    """
    outcomes_rel = f"outcomes/{item_slug(item)}.json"
    if lane_root is None:
        return WorkerPaths(
            prompt_run_dir=str(run_dir),
            prompt_run_dir_label="External run directory",
            prompt_decisions=str(run_dir / DECISIONS_NAME),
            prompt_outcome=str(run_dir / "outcomes" / f"{item_slug(item)}.json"),
            prompt_report=str(run_dir / REPORT_NAME),
            prompt_report_label="Driver report",
            prompt_plan=str(plan_path),
            lane_root=None,
            lane_submission_root=None,
            lane_decisions=None,
            lane_outcome=None,
            lane_report=None,
        )

    lane_root = Path(lane_root)
    sub_root = lane_submission_root(lane_root, run_id, item)
    rel_root = sub_root.relative_to(lane_root).as_posix()
    try:
        plan_rel = Path(plan_path).relative_to(lane_root).as_posix()
    except ValueError:
        plan_rel = str(plan_path)
    return WorkerPaths(
        prompt_run_dir=rel_root,
        # The label changes with the branch ON PURPOSE. "External run directory" was accurate for a
        # main-checkout turn and is a CONTRADICTION for an isolated one, where the directory is inside
        # the worker's own workspace; leaving the word "External" over a lane-relative path would
        # re-create in the label the confusion R1.1 removes from the value.
        prompt_run_dir_label="Your submission directory (relative to your workspace)",
        prompt_decisions=f"{rel_root}/{DECISIONS_NAME}",
        prompt_outcome=f"{rel_root}/{outcomes_rel}",
        prompt_report=f"{rel_root}/{REPORT_NAME}",
        # Likewise relabelled: the driver's own run-wide report is NOT this path. An isolated
        # worker's report is collected to a per-attempt destination (see `collect_lane_submissions`),
        # because the driver regenerates its report from durable state and a worker copy landing on
        # that path would destroy the run-wide record. Calling this "Driver report" would invite the
        # worker to believe it is writing the driver's file.
        prompt_report_label="Your report for this turn (relative to your workspace)",
        prompt_plan=plan_rel,
        lane_root=lane_root,
        lane_submission_root=sub_root,
        lane_decisions=sub_root / DECISIONS_NAME,
        lane_outcome=sub_root / "outcomes" / f"{item_slug(item)}.json",
        lane_report=sub_root / REPORT_NAME,
    )


# ---- R1.1 verification helper (used by tests AND by the drivers' own self-check) -------------------

#: Matches an absolute POSIX path token. Deliberately permissive about what a path may contain and
#: deliberately anchored on a leading `/` that is not part of a longer word, because the property
#: under test is "does the emitted TEXT name an absolute path", not "is that path well-formed".
_ABS_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_.~/-])/(?:[A-Za-z0-9_.~+-]+/)*[A-Za-z0-9_.~+-]+"
)


def absolute_paths_outside_lane(text: str, lane_root: Path | str) -> list[str]:
    """Every absolute path token in `text` that is not the lane root or under it (spec R1.1, A1).

    A PROPERTY CHECK OVER THE EMITTED TEXT, which is what the spec requires and what a wording
    assertion cannot give: a reworded violation, a newly added line, or a future path interpolation
    all fail it, because it never mentions any specific sentence. Returned in first-appearance order
    with duplicates removed so a caller can report the offenders rather than only a boolean.
    """
    root = str(Path(lane_root))
    found: list[str] = []
    for match in _ABS_PATH_RE.finditer(text):
        token = match.group(0)
        if token == root or token.startswith(root.rstrip("/") + "/"):
            continue
        if token not in found:
            found.append(token)
    return found


def scrub_out_of_lane_paths(text: str, lane_root: Path | str) -> str:
    """Replace absolute out-of-lane path tokens in ONE narrow input with a plain-language marker.

    SCOPE IS DELIBERATELY NARROW AND MUST STAY THAT WAY. This is applied ONLY to the recovery lane
    notice, which legitimately describes a PREVIOUS attempt's lane. That lane may be a DIFFERENT
    directory (`allocate_worktree` returns an attempt-scoped lane when the original holds work), so
    its absolute path is out-of-lane for this turn and would violate R1.1 while telling the worker
    about a tree it must not touch anyway. The branch name is kept, because that is the part a human
    or a later turn needs.

    DO NOT APPLY THIS TO THE WHOLE PROMPT. A global scrub would make R1.1 hold trivially and would
    defeat the sabotage check the plan's `V-01` requires: a re-introduced absolute path would be
    silently rewritten instead of failing, so the test would stop being able to fail. The projection
    in `project_worker_paths` is the real mechanism; this is a targeted fix for one inherited string.
    """
    marker = "(a lane outside this workspace; not reachable from this turn)"
    result = text
    for token in absolute_paths_outside_lane(text, lane_root):
        result = result.replace(f"`{token}`", marker).replace(token, marker)
    return result


# ---- R1.2 / R1.4: the isolation notice ------------------------------------------------------------


def isolation_notice(lane_root: Path | None) -> str:
    """The WORK HERE block for an isolated turn, or "" for a main-checkout turn.

    HISTORY, because the block itself is not the defect. It was added for a MEASURED escape
    (run-20260831T153226Z-3424176, plan y6mfgo): the driver allocated a lane, launched with
    `--dir <lane>`, and the agent still read `../../../DECISIONS.md` and committed 18 files into MAIN
    while the lane branch stayed at zero commits. `--dir` alone does not convey isolation.

    WHAT CHANGED HERE (spec R1.2, plan E-02): the block used to end with an EXCEPTION CLAUSE naming
    the driver-owned control paths as "the only exceptions ... you write them exactly as given". That
    sentence re-introduced the contradiction it sat nine lines below, and it is DELETED rather than
    reworded. It is now unnecessary as well as non-conforming: `project_worker_paths` gives the worker
    lane-relative paths, so there is no out-of-lane path left to except.

    WHAT REPLACED IT (spec R1.4): a plain statement that the cwd is the COMPLETE authorized
    workspace, plus the ONE token form for reporting a genuinely missing input. R1.1 without R1.4 is
    a strictness increase with no escape hatch, which turns a recoverable situation into a failure.

    HONEST LIMIT: this is the cheap layer. `host_sandbox_profile`'s own docstring records that a
    same-user agent with shell access "cannot be cryptographically or filesystem-enforced from
    prompts, hooks, environment variables, or Python role checks alone". So it stops a FORGETFUL
    agent, not a determined one; the enforcing layer is the opt-in hardened profile.
    """
    if lane_root is None:
        return ""
    return f"""

## Work here

You are running in an ISOLATED GIT WORKTREE (a "lane"), not the main checkout:

    {lane_root}

That directory is your COMPLETE authorized workspace and it is your working directory. It is a
full checkout of this repository on its own branch, so the whole tree you need is already there.
Do EVERY edit, test run, and commit inside it, and write every path this prompt gives you exactly
as given: they are relative to that directory.

Do NOT read or write the main checkout, and do NOT climb out with a relative path such as
`../../../<file>`. If you need a repository file, use the copy inside your workspace.

If you genuinely need an input that is NOT present in your workspace, do not go looking for it
outside. Report it on its own line in exactly this form, then continue with every independent part
of your task:

    {MISSING_INPUT_TOKEN_FORM}

The driver integrates your lane back into the main checkout after this turn, and collects
everything you write under the submission directory named below. Leaving work outside your
workspace defeats that integration and can corrupt another agent's tree."""


# ---- R2: collection -------------------------------------------------------------------------------


class CollectedSubmission(NamedTuple):
    """One submission's collection outcome, as recorded in the receipt (spec R2.5)."""

    name: str
    source: str
    destination: str
    result: str  # "collected" | "absent" | "failed"
    source_sha256: str | None = None
    reason: str | None = None


#: Receipt status values. `in-progress` is written BEFORE any copy, so a crash mid-collection is
#: distinguishable from a lane that submitted nothing (which has NO receipt at all) and from a
#: completed collection (spec R2.5, A5b).
RECEIPT_IN_PROGRESS = "in-progress"
RECEIPT_COMPLETE = "complete"


def collection_receipt_path(run_dir: Path, item: dict[str, Any], attempt: int) -> Path:
    """`<run_dir>/collections/<NN>-<id6>-attempt-<N>.json`, the attempt-keyed receipt (R2.5).

    ATTEMPT-KEYED, not item-keyed: a retry must not overwrite the record of what the previous attempt
    did or did not submit, or the retention classification in child `xdr83v` would read one attempt's
    outcome as another's.
    """
    return run_dir / "collections" / f"{item_slug(item)}-attempt-{attempt}.json"


def read_collection_receipt(
    run_dir: Path, item: dict[str, Any], attempt: int
) -> dict[str, Any] | None:
    """The receipt for one attempt, or `None` meaning NOT COLLECTED (spec R2.5).

    ABSENCE MEANS NOT COLLECTED and must never be inferred from a file existing somewhere: a
    submission can be present at the driver-side path because a PREVIOUS attempt put it there, and a
    collection can have FAILED after the destination directory was created. The receipt is the only
    authoritative source.
    """
    path = collection_receipt_path(run_dir, item, attempt)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    """Replace `path` atomically, so a crash never leaves a half-written register or receipt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _copy_file(source: Path, destination: Path) -> None:
    """COPY (spec R2.2), never move: the lane keeps its own evidence for the R5 retention rules."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_bytes(destination, source.read_bytes())


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


# ---- R2.3: the run-wide decisions register ---------------------------------------------------------

_BLOCK_OPEN = "<!-- aw:lane-decisions {key} -->"
_BLOCK_CLOSE = "<!-- /aw:lane-decisions {key} -->"


def decisions_block_key(item: dict[str, Any], attempt: int) -> str:
    """The attempt-scoped key that makes a re-run of collection idempotent (spec R2.3)."""
    return f"{item_slug(item)}-attempt-{attempt}"


def merge_decisions_block(register_text: str, key: str, contribution: str) -> str:
    """Insert or REPLACE one lane's delimited block in the run-wide register text (spec R2.3).

    MECHANISM CHOSEN: ATTEMPT-KEYED DEDUP by HTML-comment delimiters, not deterministic per-lane
    files concatenated on read. Recorded here because plan `cqx5v7` OQ-01 leaves the choice to the
    executor and requires the choice be stated where a later reader will find it. Two reasons it won:
    the register is an EXISTING single file that humans and `aw oc run status` already read, so
    switching to a fan-in directory would change a read surface this plan is not chartered to change;
    and the delimiters make the idempotency observable in the artifact itself rather than implied by
    the writer's behavior.

    The invariant is exactly the one spec A4 tests: re-running the SAME attempt's collection leaves
    that attempt's contribution present EXACTLY ONCE, and never disturbs a sibling lane's block or
    any hand-written prose outside the blocks.
    """
    open_marker = _BLOCK_OPEN.format(key=key)
    close_marker = _BLOCK_CLOSE.format(key=key)
    body = contribution.strip("\n")
    block = f"{open_marker}\n{body}\n{close_marker}\n"
    start = register_text.find(open_marker)
    if start != -1:
        end = register_text.find(close_marker, start)
        if end != -1:
            end += len(close_marker)
            # Absorb a single trailing newline so repeated merges cannot grow blank lines.
            if register_text[end : end + 1] == "\n":
                end += 1
            return register_text[:start] + block + register_text[end:]
    prefix = register_text
    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    if prefix and not prefix.endswith("\n\n"):
        prefix += "\n"
    return prefix + block


def collect_lane_submissions(
    *,
    run_dir: Path,
    item: dict[str, Any],
    run_id: str,
    lane_root: Path | str | None,
    plan_path: Path,
    attempt: int | None = None,
) -> dict[str, Any] | None:
    """Copy an isolated turn's lane-side submissions to the driver's own read locations.

    THIS IS THE OTHER HALF OF R1 AND MUST SHIP WITH IT (spec R2.1, and the reason the plan forbids
    splitting): a lane-relative instruction whose output nobody collects fails INVISIBLY. The worker
    writes its outcome inside the lane, `reconcile_disposition` reads `<run_dir>/outcomes/...`, finds
    nothing, and scores the turn from the empty-outcome fallback; that disposition is outside the set
    that gates verification and self-finalize, so a fully successful turn silently never finalizes.

    CALLED IMMEDIATELY BEFORE `reconcile_disposition`, which is the whole point of its placement.

    Behavior:
      * returns `None` for a NON-isolated turn (nothing to collect, no receipt written);
      * writes an `in-progress` receipt BEFORE the first copy, so an interruption mid-collection is
        distinguishable from a lane that submitted nothing (R2.5);
      * COPIES, never moves (R2.2);
      * records an ABSENT submission as `absent` and a FAILED one as `failed` with its reason, rather
        than omitting either, because a silent omission is indistinguishable from a lane that wrote
        nothing (R2.5);
      * merges the decisions contribution idempotently (R2.3); and
      * never raises for a turn that submitted nothing (R2.4).

    The driver's OWN `execution-report.md` is never overwritten. A worker-written report is collected
    to `<run_dir>/lane-reports/<NN>-<id6>-attempt-<N>-execution-report.md` instead, because the
    driver regenerates its report from durable state on every save and a worker copy landing on that
    path would destroy the run-wide record. The receipt names the real destination, so nothing about
    this is implicit.
    """
    if lane_root is None:
        return None
    n = attempt_key(item) if attempt is None else attempt
    paths = project_worker_paths(
        item=item,
        run_id=run_id,
        run_dir=run_dir,
        plan_path=plan_path,
        lane_root=Path(lane_root),
    )
    receipt_path = collection_receipt_path(run_dir, item, n)
    previous = read_collection_receipt(run_dir, item, n)
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "run_id": str(run_id),
        "position": int(item["position"]),
        "id6": item["id6"],
        "attempt": n,
        "lane_root": str(paths.lane_root),
        "lane_submission_root": str(paths.lane_submission_root),
        "status": RECEIPT_IN_PROGRESS,
        "collection_runs": int((previous or {}).get("collection_runs", 0)) + 1,
        "submissions": [],
    }
    _atomic_write_text(
        receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )

    results: list[CollectedSubmission] = []

    # 1. The outcome JSON: the submission `reconcile_disposition` actually reads.
    assert paths.lane_outcome is not None  # narrowed by the lane_root branch above
    results.append(
        _collect_one(
            name="outcome",
            source=paths.lane_outcome,
            destination=run_dir / "outcomes" / f"{item_slug(item)}.json",
        )
    )

    # 2. The worker's report copy, to its OWN destination (never the driver's report).
    assert paths.lane_report is not None
    results.append(
        _collect_one(
            name="report",
            source=paths.lane_report,
            destination=run_dir
            / "lane-reports"
            / f"{item_slug(item)}-attempt-{n}-{REPORT_NAME}",
        )
    )

    # 3. The decisions contribution, merged idempotently into the RUN-WIDE register (R2.3).
    assert paths.lane_decisions is not None
    results.append(
        _collect_decisions(
            source=paths.lane_decisions,
            register=run_dir / DECISIONS_NAME,
            key=decisions_block_key(item, n),
        )
    )

    receipt["submissions"] = [dict(r._asdict()) for r in results]
    receipt["status"] = RECEIPT_COMPLETE
    receipt["collected"] = [r.name for r in results if r.result == "collected"]
    receipt["failed"] = [r.name for r in results if r.result == "failed"]
    _atomic_write_text(
        receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    return receipt


def _collect_one(*, name: str, source: Path, destination: Path) -> CollectedSubmission:
    if not source.is_file():
        return CollectedSubmission(
            name=name,
            source=str(source),
            destination=str(destination),
            result="absent",
            reason="the lane holds no such submission",
        )
    try:
        digest = _sha256_file(source)
        _copy_file(source, destination)
    except OSError as exc:
        return CollectedSubmission(
            name=name,
            source=str(source),
            destination=str(destination),
            result="failed",
            reason=f"{type(exc).__name__}: {exc}",
        )
    return CollectedSubmission(
        name=name,
        source=str(source),
        destination=str(destination),
        result="collected",
        source_sha256=digest,
    )


def _collect_decisions(
    *, source: Path, register: Path, key: str
) -> CollectedSubmission:
    if not source.is_file():
        return CollectedSubmission(
            name="decisions",
            source=str(source),
            destination=str(register),
            result="absent",
            reason="the lane recorded no decisions or deferred questions",
        )
    try:
        digest = _sha256_file(source)
        contribution = source.read_text(encoding="utf-8")
        try:
            existing = register.read_text(encoding="utf-8")
        except OSError:
            existing = ""
        _atomic_write_text(register, merge_decisions_block(existing, key, contribution))
    except OSError as exc:
        return CollectedSubmission(
            name="decisions",
            source=str(source),
            destination=str(register),
            result="failed",
            reason=f"{type(exc).__name__}: {exc}",
        )
    return CollectedSubmission(
        name="decisions",
        source=str(source),
        destination=str(register),
        result="collected",
        source_sha256=digest,
    )


# ==================================================================================================
# lanectn Order 03 (`lhmrhx`): HOST PERMISSION POSTURE AND DRIVER-SIDE TURN BOUNDS (spec R4)
# ==================================================================================================
#
# WHY THIS LIVES HERE AND NOT IN A DRIVER. Spec R2.6 requires one definition for every rule both
# drivers consume, and plan `lhmrhx`'s review (finding PR-001) established that the agy side is NOT a
# mechanical mirror of the oc side: that host has NO denial posture by design (R4.1), so a
# "mirror this into the twin" instruction would have hidden an omitted seam. The bounds, the honest
# per-host reporting, and the safe-failure recording are therefore HOST-NEUTRAL functions here, and
# each driver keeps only a thin adapter for its own event shapes and its own argv.
#
# WHAT IS NOT UNIFORM, stated so no reader infers parity that does not exist (R4.1a):
#
#   OPENCODE     a real denial. `permission.external_directory` and `permission.question` are set to
#                `deny` through the runner-supplied runtime config, so the host itself refuses.
#   ANTIGRAVITY  NO denial posture exists, permanently and by design (R4.1, R4.1c). Auto-approve is
#                the REQUIRED setting there, because the only alternative needs interactive
#                permissions an unattended turn cannot answer and was measured to deadlock. On that
#                host the host layer contributes NOTHING, and containment rests entirely on R1
#                (the prompt names nothing outside the lane) and on the bounds below.

#: OpenCode's runtime-config environment variable. Chosen over `OPENCODE_CONFIG` (a FILE path)
#: because R4.1 forbids supplying the posture by editing repository configuration: inline content is
#: owned by the runner process and vanishes with it, whereas a file would be a durable artifact
#: somebody could later mistake for project config.
OPENCODE_RUNTIME_CONFIG_ENV = "OPENCODE_CONFIG_CONTENT"

#: The two permission classes R4.1 names for the opencode case, and the action requested for each.
#:
#: `external_directory` is the ask that produced the measured deadlock (a non-interactive
#: `opencode run` with a nested-subagent external-directory ask has no answerer). `question` is the
#: interactive-question class, equally unanswerable in an unattended turn. DENY rather than a broad
#: allow, deliberately: an unexpected out-of-lane path is normally a lane-containment DEFECT, and a
#: denial produces a repairable tool failure where a blanket allow could mutate the main checkout or
#: a sibling lane.
LANE_PERMISSION_POLICY: dict[str, str] = {
    "external_directory": "deny",
    "question": "deny",
}

#: How an operator-supplied value for `OPENCODE_CONFIG_CONTENT` was handled (R4.3). Recorded on the
#: attempt so the choice is never silent.
POLICY_SOURCE_RUNNER = "runner"  # no operator value was present
POLICY_SOURCE_MERGED = "merged-with-operator"  # operator JSON parsed and merged
POLICY_SOURCE_OVERRIDE = (
    "override-unparseable-operator"  # operator value could not be honored
)


class PermissionPolicyRequest(NamedTuple):
    """The policy the runner asked the host for, and HOW an operator value was handled.

    `env_value` is what belongs in the child environment. `source` records which of the three R4.3
    dispositions applied, and `operator_value` preserves the original so a loud override is
    auditable rather than a silent discard.
    """

    env_value: str
    source: str
    policy: dict[str, str]
    operator_value: str | None = None
    note: str = ""


def build_permission_policy_env(
    operator_value: str | None,
    policy: dict[str, str] | None = None,
) -> PermissionPolicyRequest:
    """The runtime-config value requesting `policy`, PRESERVING any operator-supplied value (R4.3).

    R4.3 forbids a BLIND OVERWRITE, and the risk is real rather than hypothetical: the child
    environment is built from a copy of the process environment, so assigning this key
    unconditionally would silently discard whatever an operator had exported. Three dispositions,
    each recorded on the returned request so the attempt record can carry it:

    1. NO operator value  -> the runner's policy alone (`POLICY_SOURCE_RUNNER`).
    2. Operator value that PARSES as a JSON object -> DEEP-ENOUGH MERGE
       (`POLICY_SOURCE_MERGED`): every operator key survives, and the operator's own
       `permission` entries survive too EXCEPT the two classes R4.1 requires be denied. The
       runner's two keys win on conflict, because they are the requirement, and the conflict is
       recorded in `note` so the override is visible.
    3. Operator value that does NOT parse as a JSON object -> EXPLICIT LOUD OVERRIDE
       (`POLICY_SOURCE_OVERRIDE`). It cannot be merged, and honoring it would hand the host a
       broken config; the original is preserved on the request and the reason is in `note`.

    Note what is deliberately NOT done: the operator value is never dropped without a record, and
    the function never raises. An unusable operator value must not abort a turn (the same reasoning
    as the R4.2 probe: the bounds below hold regardless of what the host decided).
    """

    requested = dict(policy if policy is not None else LANE_PERMISSION_POLICY)
    if not operator_value or not operator_value.strip():
        return PermissionPolicyRequest(
            env_value=json.dumps({"permission": requested}, sort_keys=True),
            source=POLICY_SOURCE_RUNNER,
            policy=requested,
            operator_value=None,
            note="no operator value present; runner policy supplied alone",
        )

    try:
        parsed = json.loads(operator_value)
    except (ValueError, TypeError) as exc:
        return PermissionPolicyRequest(
            env_value=json.dumps({"permission": requested}, sort_keys=True),
            source=POLICY_SOURCE_OVERRIDE,
            policy=requested,
            operator_value=operator_value,
            note=(
                "operator value OVERRIDDEN (not silently dropped): it is not parseable JSON "
                f"({type(exc).__name__}: {exc}); the original is preserved in this record"
            ),
        )
    if not isinstance(parsed, dict):
        return PermissionPolicyRequest(
            env_value=json.dumps({"permission": requested}, sort_keys=True),
            source=POLICY_SOURCE_OVERRIDE,
            policy=requested,
            operator_value=operator_value,
            note=(
                "operator value OVERRIDDEN (not silently dropped): it parses as "
                f"{type(parsed).__name__}, not a JSON object; the original is preserved here"
            ),
        )

    merged = dict(parsed)
    operator_permission = merged.get("permission")
    permission: dict[str, Any] = (
        dict(operator_permission) if isinstance(operator_permission, dict) else {}
    )
    clobbered = sorted(
        key
        for key, value in permission.items()
        if key in requested and value != requested[key]
    )
    permission.update(requested)
    merged["permission"] = permission
    note = "operator value MERGED; every operator key preserved"
    if clobbered:
        note += (
            "; the runner's required denials won on these operator keys "
            f"(spec R4.1): {', '.join(clobbered)}"
        )
    if not isinstance(operator_permission, dict) and operator_permission is not None:
        note += (
            "; the operator's `permission` value was not an object "
            f"({type(operator_permission).__name__}) and could not be merged into"
        )
    return PermissionPolicyRequest(
        env_value=json.dumps(merged, sort_keys=True),
        source=POLICY_SOURCE_MERGED,
        policy=requested,
        operator_value=operator_value,
        note=note,
    )


#: The three capability tiers R4.1a distinguishes. `DENIED` is the only one that may be described as
#: a denial; the other two must name the layers that DO apply instead.
HOST_POSTURE_DENIED = "denied"
HOST_POSTURE_NONE = "no-denial-posture"

#: The layers carrying containment when the HOST layer contributes nothing (R4.1a). Named as data so
#: the record and any rendered summary read from ONE list and cannot drift.
CONTAINMENT_LAYERS_WITHOUT_HOST_DENIAL = (
    "R1 prompt purity: the emitted prompt names no path outside the lane",
    "R4.4 driver-side bounds: MAX_TURN_TIMEOUT (and PERMISSION_TIMEOUT when armed) "
    "terminate the turn regardless of the host's permission decision",
)


class HostPostureRecord(NamedTuple):
    """The per-host capability statement R4.1a requires on every attempt.

    An artifact MUST NOT describe a host without a denial posture as "denied"; it must say
    `no-denial-posture` and name the layers that do apply. `as_dict` is what goes on the attempt.
    """

    host: str
    posture: str
    reason: str
    layers: tuple[str, ...]
    requested: dict[str, str] | None = None
    policy_source: str | None = None
    policy_note: str = ""

    def as_dict(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "host": self.host,
            "posture": self.posture,
            "reason": self.reason,
            "containment_layers": list(self.layers),
        }
        if self.requested is not None:
            record["requested_policy"] = dict(self.requested)
        if self.policy_source is not None:
            record["policy_source"] = self.policy_source
        if self.policy_note:
            record["policy_note"] = self.policy_note
        return record


def opencode_posture_record(request: PermissionPolicyRequest) -> HostPostureRecord:
    """The R4.1a capability statement for OPENCODE, which HAS a real denial posture."""

    return HostPostureRecord(
        host="opencode",
        posture=HOST_POSTURE_DENIED,
        reason=(
            "the runner supplied `permission.external_directory=deny` and "
            "`permission.question=deny` through the host's runtime config, so the host itself "
            "refuses both request classes"
        ),
        layers=(
            "R4.1 host denial: external-directory and interactive-question asks are denied",
        )
        + CONTAINMENT_LAYERS_WITHOUT_HOST_DENIAL,
        requested=dict(request.policy),
        policy_source=request.source,
        policy_note=request.note,
    )


def antigravity_posture_record() -> HostPostureRecord:
    """The R4.1a capability statement for ANTIGRAVITY, which has NO denial posture.

    This is NOT an unclosed gap awaiting work (R4.1b, spec Non-goal 7): auto-approve is the REQUIRED
    setting on that host, because running without `--dangerously-skip-permissions` needs interactive
    permissions an unattended turn has no answerer for and was measured to fail or deadlock
    repeatedly. So the honest record says `no-denial-posture` and names the layers that carry the
    whole guarantee there.
    """

    return HostPostureRecord(
        host="antigravity",
        posture=HOST_POSTURE_NONE,
        reason=(
            "no denial posture exists on this host, by design and permanently (spec R4.1, R4.1c): "
            "auto-approve is the required setting because the only alternative requires "
            "interactive permissions an unattended turn cannot answer, and was measured to "
            "deadlock. The host layer therefore contributes nothing to containment here"
        ),
        layers=CONTAINMENT_LAYERS_WITHOUT_HOST_DENIAL,
    )


#: R4.2 observation outcomes. `unverified` is a first-class result, not an error: an unobservable
#: policy is RECORDED as unverified and the turn CONTINUES, because the bounds below hold regardless.
POLICY_OBSERVED = "observed"
POLICY_UNVERIFIED = "unverified"


class PolicyObservation(NamedTuple):
    """What the host says its EFFECTIVE policy is, or an explicit unverified marker (R4.2).

    Recording nothing is what R4.2 forbids: host configuration precedence can place a managed source
    ABOVE the runner's request, so a run that only SET the policy can believe it is protected when it
    is not. Either the observed values or a marker naming the reason must reach the attempt.
    """

    result: str
    effective: dict[str, Any] | None = None
    host_version: str | None = None
    reason: str = ""
    conforms: bool | None = None

    def as_dict(self) -> dict[str, Any]:
        record: dict[str, Any] = {"result": self.result}
        if self.effective is not None:
            record["effective_policy"] = dict(self.effective)
        if self.host_version is not None:
            record["host_version"] = self.host_version
        if self.reason:
            record["reason"] = self.reason
        if self.conforms is not None:
            record["conforms_to_request"] = self.conforms
        return record


def evaluate_policy_observation(
    raw_config: str | None,
    requested: dict[str, str],
    host_version: str | None = None,
    failure_reason: str = "",
) -> PolicyObservation:
    """Decide R4.2's outcome from the host's OWN resolved configuration.

    Pure, so the probe's I/O (which host, which subprocess, which flag) stays in the driver adapter
    while the DECISION stays host-neutral and unit-testable. `raw_config` is the host's resolved
    configuration as JSON text; `None` or unparseable text yields an `unverified` marker with the
    reason rather than raising, because R4.2's observation is a DIAGNOSTIC and OQ-01 resolved that a
    probe failure must never abort a turn.

    `conforms` is the load-bearing field: it is False when the host reports an effective value that
    DISAGREES with what the runner asked for, which is exactly the higher-precedence-override case
    that motivates R4.2 at all.
    """

    if raw_config is None:
        return PolicyObservation(
            result=POLICY_UNVERIFIED,
            host_version=host_version,
            reason=failure_reason
            or "the host's resolved configuration could not be read",
        )
    try:
        parsed = json.loads(raw_config)
    except (ValueError, TypeError) as exc:
        return PolicyObservation(
            result=POLICY_UNVERIFIED,
            host_version=host_version,
            reason=(
                failure_reason
                or f"the host's resolved configuration is not parseable JSON ({type(exc).__name__}: {exc})"
            ),
        )
    if not isinstance(parsed, dict):
        return PolicyObservation(
            result=POLICY_UNVERIFIED,
            host_version=host_version,
            reason=f"the host's resolved configuration is a {type(parsed).__name__}, not an object",
        )
    permission = parsed.get("permission")
    if not isinstance(permission, dict):
        return PolicyObservation(
            result=POLICY_UNVERIFIED,
            host_version=host_version,
            reason="the host's resolved configuration carries no `permission` object",
        )
    effective = {key: permission.get(key) for key in requested}
    return PolicyObservation(
        result=POLICY_OBSERVED,
        effective=effective,
        host_version=host_version,
        conforms=all(effective.get(key) == value for key, value in requested.items()),
        reason=""
        if all(effective.get(key) == value for key, value in requested.items())
        else (
            "the host's EFFECTIVE policy disagrees with the runner's request, so a "
            "higher-precedence configuration source overrode it"
        ),
    )


# ---- R4.4: the two driver-side bounds that do not trust the host ----------------------------------
#
# ARMED FOR EVERY UNATTENDED TURN, isolated or not (R4.4a, maintainer ruling). That uniformity is a
# deliberate exception to the conservatism asked for elsewhere, and it is safe because these are
# driver-side SUPERVISION and change no instruction an agent ever reads: R1.3 protects the
# NON-ISOLATED PROMPT TEXT, which stays byte-identical.
#
# NO CONFIG ENTRY AND NO CLI FLAG (R4.4c, maintainer KISS ruling). Both are in-code constants that
# accept `0` to disable. Evidence behind the ruling: across 87 recorded runs `--stall-timeout`
# appears with exactly ONE distinct value (its default) and `--timeout` in none, so no timeout has
# ever been overridden in practice, while the parser already fails
# `test_command_surface_declarations::test_zero_undeclared_parser_leaves` with undeclared leaves.

#: Seconds to wait after a permission request is OBSERVED before terminating the turn.
#:
#: MEASURED FROM: the instant a permission request is observed on the child's stream, including a
#: nested child-session request (the shape the measured deadlock actually took).
#: RESET BY: observed progress, which clears the pending ask and disarms the bound. RESETTABLE.
#:
#: SHIPS AT `0`, MEANING DISABLED, and that is a REQUIREMENT rather than caution (R4.4b). Detection
#: would be PATTERN MATCHING on the child's stdout, not a deterministic signal, and it is UNVERIFIED
#: against a real ask: the last real run's stdout carried ZERO permission-typed events, and the
#: evidence that motivated a plain-text pattern came from opencode's LOG FILE rather than stdout.
#: Shipping it armed on an unproven detector is non-conforming, because a false positive kills a
#: healthy turn. CONSEQUENCE, stated plainly: `MAX_TURN_TIMEOUT` is currently the ONLY bound covering
#: a permission deadlock. Set this to 30 only together with a captured stream from a real provoked
#: ask showing the line the detector matched.
PERMISSION_TIMEOUT: float = 0.0

#: Seconds from child-process start after which the turn is terminated no matter what.
#:
#: MEASURED FROM: child process start, ONCE.
#: RESET BY: NOTHING. That is its entire reason for existing alongside the no-progress watchdog: a
#: chatty-but-wedged turn keeps resetting a no-progress window forever and cannot reset this.
#:
#: DEFAULT 4 HOURS. Measured when it was chosen: across 263 recorded turns the longest was 2.46
#: hours, so this is roughly 1.6x the observed worst case. Accepts `0` to disable.
#:
#: SCOPE IS ONE TURN, NOT ONE RUN. Each queue item gets its own fresh budget, so a 22-item run has no
#: run-wide ceiling and could legitimately span days; a run-wide ceiling does not exist in this design
#: and is explicitly not required (spec Non-goal 8). Expiry terminates the CHILD, not the driver: the
#: driver records the safe-failure disposition and proceeds to the next item.
#:
#: ANTIGRAVITY OVERLAP, stated rather than discovered (R4.4d). That host ALREADY enforces a per-turn
#: ceiling of `240m` via `--print-timeout`, numerically the same 4 hours, so two timers with different
#: owners would fire at the same nominal instant. RESOLUTION: the driver bound is deliberately OFFSET
#: to fire FIRST on that host (see `driver_bound_for_host`), so a termination is attributable to the
#: driver, which records WHICH bound fired, rather than to an opaque host timeout. OpenCode has no
#: host-enforced equivalent, so here the bound is genuinely new.
MAX_TURN_TIMEOUT: float = 4 * 60 * 60.0

#: Seconds by which the driver's own ceiling is pulled in AHEAD of a host-enforced one, so the two
#: cannot fire at the same nominal instant and a post-mortem can attribute the kill (R4.4d).
HOST_CEILING_OFFSET_SECONDS: float = 5 * 60.0

#: Which bound fired, recorded on the safe-failure disposition so a post-mortem can tell a permission
#: deadlock from an over-long turn from a silent stall (R4.4).
BOUND_PERMISSION = "permission-timeout"
BOUND_MAX_TURN = "max-turn-timeout"

#: The disposition an expiry records. `failed-safely` is an EXISTING terminal state in both drivers'
#: vocabulary, so a bound expiry stays visible to the reconcile/report machinery without new states.
BOUND_EXPIRY_DISPOSITION = "failed-safely"


def driver_bound_for_host(host_ceiling_seconds: float | None) -> float:
    """`MAX_TURN_TIMEOUT`, pulled in ahead of a HOST-ENFORCED ceiling when one exists (R4.4d).

    Returns the driver's own ceiling in seconds, or `0.0` when disabled. When the host enforces its
    own per-turn ceiling at nominally the same instant (antigravity's `240m` `--print-timeout` versus
    this bound's 4 hours), the driver's fires FIRST by `HOST_CEILING_OFFSET_SECONDS`, so the
    termination is attributable to the driver, which names the bound, rather than to an opaque host
    timeout. WHICH IS EXPECTED TO WIN: the driver's, by construction. The host timer remains the
    backstop for the case where the driver's own supervision thread dies.
    """

    if MAX_TURN_TIMEOUT <= 0:
        return 0.0
    if not host_ceiling_seconds or host_ceiling_seconds <= 0:
        return MAX_TURN_TIMEOUT
    offset = max(0.0, host_ceiling_seconds - HOST_CEILING_OFFSET_SECONDS)
    if offset <= 0:
        return min(MAX_TURN_TIMEOUT, host_ceiling_seconds)
    return min(MAX_TURN_TIMEOUT, offset)


def bound_expiry_record(bound: str, timeout: float, at: str) -> dict[str, Any]:
    """The safe-failure record for an expired bound, NAMING WHICH ONE FIRED (R4.4).

    Naming the bound is the requirement, not a nicety: without it a post-mortem cannot distinguish a
    permission deadlock from an over-long turn from a silent stall, and all three arrive as the same
    terminated child.
    """

    return {
        "bound": bound,
        "timeout_seconds": timeout,
        "disposition": BOUND_EXPIRY_DISPOSITION,
        "at": at,
        "scope": "one turn (not one run)",
        "detail": (
            f"the driver's {bound} bound expired after {timeout:.0f}s and terminated the child "
            "through the one shared reaper; the driver continues with the next item"
        ),
    }


def bound_expiry_reaper(
    process: Any,
    run_dir: Path,
    item: dict[str, Any],
    *,
    reap: Callable[[Any, Path], Any] | None = None,
) -> Callable[[str, float], None]:
    """The `TurnBoundWatch` reap callback: RECORD WHICH BOUND FIRED, then reap. HOST-NEUTRAL.

    Both drivers call THIS, rather than each keeping an identical adapter, because spec R2.6 requires
    one definition for every rule both drivers consume and there is nothing host-specific in it: the
    child process, the run directory, and the item are the same three things on either host.

    ORDER IS LOAD-BEARING, not incidental. Reaping closes the child's stdout, which unblocks the
    driver's read loop and lets the turn unwind; recording AFTER the reap could race that unwind and a
    post-mortem would then see a terminated child with no reason attached, which is exactly the
    "cannot say which timer killed it" outcome R4.4d exists to prevent. So the record is written first
    and its failure is suppressed, because a bookkeeping error must not stop the child being reaped.

    THE REAP IS THE ONE SHARED REAPER. `runner_shutdown.clean_shutdown` is the single reaper and the
    single process-group escalation (spec `c4gd2h` R5 forbids a second): NOT a bare kill, NOT a local
    `terminate_process`, and NOT a per-host copy. It is injectable ONLY so a test can observe the call
    without spawning a real process; the default is the shared routine, and a caller that passes
    something else is introducing the second reaper the spec forbids.
    """

    from agent_workflows import runner_shutdown

    reaper = reap if reap is not None else runner_shutdown.clean_shutdown

    def _expire(bound: str, timeout: float) -> None:
        with contextlib.suppress(Exception):
            record = bound_expiry_record(bound, timeout, runner_shared.utc_now())
            item["turn_bound_expiry"] = record
            runner_shared.append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": record["at"],
                    "event": "turn-bound-expired",
                    "id6": item.get("id6", ""),
                    **record,
                },
            )
        report = reaper(process, run_dir=run_dir)
        render = getattr(report, "render", None)
        if render is not None and not getattr(report, "all_satisfied", True):
            print(render(), file=sys.stderr)

    return _expire


class TurnBoundWatch:
    """Out-of-band supervisor enforcing `MAX_TURN_TIMEOUT` and, when armed, `PERMISSION_TIMEOUT`.

    HOST-NEUTRAL BY CONSTRUCTION. It is handed a `reap` callable and an `is_alive` callable rather
    than a process, so the ONE shared reaper (`runner_shutdown.clean_shutdown`, which spec `c4gd2h`
    R5 makes the only reaper) stays in the driver adapter and this class introduces no second
    termination path. Both drivers construct it identically; neither owns a private copy.

    WHY A THREAD AND NOT AN IN-LOOP CHECK, which is the same measured reason every other watch in
    this codebase is out of band: the driver's read loop blocks in `for line in process.stdout`, so a
    ceiling on a SILENT child could never be noticed from the main thread. A wedged turn is exactly
    the case these bounds exist for.

    THE TWO BOUNDS DIFFER IN RESET SEMANTICS, and that difference is the whole design:

      * `MAX_TURN_TIMEOUT` is measured from `__enter__` (child start) ONCE and NOTHING resets it.
      * `PERMISSION_TIMEOUT` is measured from `note_permission_request()` and IS reset by
        `note_progress()`, which clears the pending ask.

    HONEST LIMIT: this bounds the turn, it does not contain the worker. A terminated child may
    already have written outside its lane. Containment is R1 (the prompt names nothing outside the
    lane) plus, on a host that has one, the R4.1 denial.
    """

    def __init__(
        self,
        *,
        reap: Callable[[str, float], None],
        is_alive: Callable[[], bool] | None = None,
        max_turn_timeout: float | None = None,
        permission_timeout: float | None = None,
        check_interval: float = 1.0,
    ) -> None:
        self.max_turn_timeout = (
            MAX_TURN_TIMEOUT if max_turn_timeout is None else float(max_turn_timeout)
        )
        self.permission_timeout = (
            PERMISSION_TIMEOUT
            if permission_timeout is None
            else float(permission_timeout)
        )
        if self.max_turn_timeout < 0:
            self.max_turn_timeout = 0.0
        if self.permission_timeout < 0:
            self.permission_timeout = 0.0
        self._reap = reap
        self._is_alive = is_alive
        # Never sleep past the nearer bound, or a short injected timeout (as tests use) would be
        # reported late. Mirrors `StallWatchdog`'s own timeout/4 clamp.
        candidates = [
            t for t in (self.max_turn_timeout, self.permission_timeout) if t > 0
        ]
        nearest = min(candidates) if candidates else 0.0
        self.check_interval = (
            max(0.005, min(check_interval, nearest / 4.0))
            if nearest
            else check_interval
        )
        self._started: float | None = None
        self._permission_pending_since: float | None = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.fired: str | None = None
        self.fired_timeout: float = 0.0

    @property
    def enabled(self) -> bool:
        """True when at least one bound is armed. `0` disables a bound (R4.4c)."""

        return self.max_turn_timeout > 0 or self.permission_timeout > 0

    def note_permission_request(self) -> None:
        """Arm `PERMISSION_TIMEOUT` from THIS instant (a permission request was observed).

        Idempotent while an ask is already pending, so a repeated observation does not extend the
        window: the bound measures from the FIRST observed ask, which is when waiting began.
        """

        if self.permission_timeout <= 0:
            return
        with self._lock:
            if self._permission_pending_since is None:
                self._permission_pending_since = time.monotonic()

    def note_progress(self) -> None:
        """Clear a pending permission ask, DISARMING `PERMISSION_TIMEOUT` (it is RESETTABLE).

        Deliberately does NOT touch `MAX_TURN_TIMEOUT`: nothing resets that one, which is why it
        catches the chatty-but-wedged turn a no-progress window never can.
        """

        with self._lock:
            self._permission_pending_since = None

    def _expired(self, now: float) -> tuple[str, float] | None:
        if self._started is not None and self.max_turn_timeout > 0:
            if now - self._started >= self.max_turn_timeout:
                return BOUND_MAX_TURN, self.max_turn_timeout
        with self._lock:
            pending = self._permission_pending_since
        if pending is not None and self.permission_timeout > 0:
            if now - pending >= self.permission_timeout:
                return BOUND_PERMISSION, self.permission_timeout
        return None

    def _run(self) -> None:
        while not self._stop.wait(self.check_interval):
            if self._is_alive is not None and not self._is_alive():
                return
            expiry = self._expired(time.monotonic())
            if expiry is None:
                continue
            self.fired, self.fired_timeout = expiry
            # Through the caller-supplied reaper, which is the ONE shared `clean_shutdown` (spec
            # `c4gd2h` R5): never a bare kill, never a second reaper.
            try:
                self._reap(self.fired, self.fired_timeout)
            except (
                Exception
            ):  # pragma: no cover - a reaper failure must not kill the thread
                pass
            return

    def __enter__(self) -> "TurnBoundWatch":
        self._started = time.monotonic()
        if self.enabled:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)


def record_host_posture(
    run_dir: Path,
    item: dict[str, Any],
    attempt_no: int,
    posture: HostPostureRecord,
    observation: PolicyObservation | None = None,
) -> dict[str, Any]:
    """Write the per-host capability statement and the policy observation ONTO THE ATTEMPT (R4.1a).

    HOST-NEUTRAL, and that is a requirement rather than tidiness (spec R2.6, plan finding PR-001).
    Both drivers call THIS function with their own `posture`, so the record SHAPE cannot drift between
    hosts and an artifact reader is never misled by a per-host layout. The posture VALUE itself comes
    from `opencode_posture_record` / `antigravity_posture_record` rather than being assembled at each
    call site, because R4.1a forbids describing a host without a denial posture as "denied" and a call
    site can get that wording wrong where a shared constructor cannot.

    `observation` is OPTIONAL on purpose: a host with no denial posture has no policy to observe, so
    passing `None` there is correct rather than a missing field. On a host that DOES deny, R4.2
    requires either the observed values or an explicit unverified marker, and omitting it would leave
    a run silently believing it is protected.

    Recorded on the ATTEMPT (falling back to the item when the attempt is not yet present) AND emitted
    as an event, so the statement survives in durable state and in the chronological log.
    """

    record = posture.as_dict()
    if observation is not None:
        record["policy_observation"] = observation.as_dict()
    for attempt in item.get("attempts") or []:
        if attempt.get("number") == attempt_no:
            attempt["host_posture"] = record
            break
    else:
        item["host_posture"] = record
    with contextlib.suppress(Exception):
        runner_shared.append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": runner_shared.utc_now(),
                "event": "host-permission-posture",
                "id6": item.get("id6", ""),
                "attempt": attempt_no,
                **record,
            },
        )
    return record


#: Suffix multipliers for a host-enforced duration string. Antigravity's `--print-timeout` is written
#: as `"240m"`, so a bare-seconds parse would read it as 240 SECONDS and pull the driver's ceiling in
#: to nothing, killing every turn after four minutes. Parsing it correctly is what makes R4.4d's
#: deliberate offset land at the intended instant.
_DURATION_SUFFIXES = {"s": 1.0, "m": 60.0, "h": 3600.0}


def parse_host_ceiling_seconds(value: Any) -> float | None:
    """Seconds from a host ceiling written as `"240m"` / `"90s"` / `"4h"` / a bare number.

    Returns `None` for anything unrecognized, and NEVER raises: an unparseable host ceiling must not
    abort a turn, it must simply mean "no known host ceiling", which leaves the driver bound at its
    own default rather than at some value derived from a misread string. Fail-safe in the direction of
    the LONGER bound, deliberately: guessing short would kill healthy turns, which is the same
    reasoning R4.4b applies to the permission detector.
    """

    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value) if value > 0 else None
    if not isinstance(value, str):
        return None
    text = value.strip().lower()
    if not text:
        return None
    multiplier = 1.0
    if text[-1] in _DURATION_SUFFIXES:
        multiplier = _DURATION_SUFFIXES[text[-1]]
        text = text[:-1]
    try:
        seconds = float(text) * multiplier
    except ValueError:
        return None
    return seconds if seconds > 0 else None


# ==================================================================================================
# lanectn Order 04 (`y5od1h`): THE MISSING-INPUT REPORT-AND-REFUSE CYCLE (spec R3)
# ==================================================================================================
#
# WHAT THIS IS, in one sentence: a worker that genuinely lacks a file has a deterministic, auditable
# way to SAY SO, and the driver answers with a precise REFUSAL RECORD rather than a copy.
#
# READ THE AMENDMENT FIRST, because the obvious reading of "repair" is now WRONG. Spec `R3.3a`
# (maintainer decision, 2026-09-01) WITHDREW the permit-and-copy branch and the secret vocabulary
# that gated it. Three reasons, the third decisive:
#
#   (a) Policing secrets invites blame for a miss, while `gitleaks` (commit hook) and `aw sanitize`
#       already cover them where it matters.
#   (b) The research (`x03wgn`) said do-not-COPY, not adjudicate-requests; building a
#       secret-detection vocabulary was an over-extension at authoring time.
#   (c) DECISIVELY, THE BRANCH WAS INERT. A lane is a `git worktree` at a commit, so it ALREADY
#       contains every TRACKED file (measured 2026-09-01: 0 of 1470 absent), and `R3.3b` permitted
#       ONLY tracked files - so the copy branch could only ever copy a file the lane already had.
#       The inputs the research actually worries about (`.venv`, `node_modules`, generated schemas)
#       are IGNORED or UNTRACKED, which is exactly the category it REFUSED.
#
# SO NOTHING HERE COPIES ANYTHING INTO A LANE, and there is no permitted path to test. A test
# asserting a successful copy would assert behavior the spec now FORBIDS. What is PRESERVED is the
# escape hatch that makes R1.1's strictness survivable: the worker still reports (R3.1) and the
# driver still preserves and pauses the lane rather than prompting (R3.2). Only the ANSWER changed.
#
# HONEST CONSEQUENCE, recorded rather than hidden (spec R3.3a): a turn genuinely blocked on a missing
# IGNORED input now fails with a precise record instead of self-repairing. That is the intended
# trade. The conforming fix, if it ever proves an operational problem, is UP-FRONT lane assembly
# under an explicit policy - not a request-time copy.
#
# HOST-NEUTRAL BY CONSTRUCTION (spec R2.6). The token parse, the classification, the refusal record,
# and the pause all live HERE; each driver contributes only a per-line call and its own event shape,
# so neither host is the de-facto shared library and the rule cannot fork (R6.1, CID-2/CID-3).


#: The two channels a refusal can arrive through, recorded on the decision so an artifact reader can
#: tell them apart WITHOUT changing the verdict. R3.7's whole point is that both reach the SAME
#: classification path, so this field is provenance only and is never an input to the rule.
MISSING_INPUT_SOURCE_TOKEN = "worker-token"  # the worker emitted `AW_MISSING_INPUT:...`
MISSING_INPUT_SOURCE_PERMISSION = (
    "denied-permission-event"  # the host denied an ask (R3.7)
)

#: THE ONLY VERDICT THIS CYCLE HAS (spec R3.3a as amended, R3.6).
#:
#: There is deliberately NO `GRANTED`/`PERMITTED` sibling constant, and adding one is how R3.6's
#: guarantee would die: the requirement is that the decision TYPE cannot represent a live grant, not
#: that a boolean happens to be False. `tests/test_missing_input_repair.py` enumerates this module's
#: `MISSING_INPUT_VERDICT_*` names and `MissingInputDecision._fields`, so introducing either a second
#: verdict or a grant-shaped field FAILS the suite rather than silently widening the rule.
MISSING_INPUT_VERDICT_REFUSED = "refused"

#: Why a request was refused. EVERY request is refused (R3.3a), so these distinguish the RULE that
#: fired, which is what makes the record "precise" in R3.5's sense rather than a bare failure.
#:
#: `withdrawn-repair-path` is the one that fires for a path with nothing wrong with it: it exists,
#: it is inside the checkout, it is a regular file, and it is STILL refused, because no permitted
#: path exists any more. Naming it explicitly (rather than reusing a shape rejection) is what keeps
#: the artifact honest about WHY - a reader must not conclude the path was malformed.
REJECT_ABSOLUTE = "absolute-path"
REJECT_ESCAPES_CHECKOUT = "escapes-checkout"
REJECT_COORDINATOR_SURFACE = "coordinator-owned-surface"
REJECT_SIBLING_LANE = "sibling-lane-or-worktrees-root"
REJECT_MACHINE_STATE = "machine-local-state"
REJECT_GIT_ADMIN = "git-administration-directory"
REJECT_DIRECTORY = "directory-not-a-file"
REJECT_ABSENT = "path-does-not-exist"
REJECT_WITHDRAWN_REPAIR = "withdrawn-repair-path"
REJECT_MALFORMED_TOKEN = "malformed-report"

#: Machine-local state R3.3 names as its own reject class. Derived from the ONE existing spelling of
#: the run/state prefixes where one exists, so a rename cannot leave this list behind.
#:
#: NOT a secret vocabulary, and it must never become one: R3.3a WITHDREW that, and adding
#: credentials families here would ship the liability the maintainer explicitly declined. These are
#: MACHINE-LOCAL paths (a lane's own scratch, a driver's durable run state, per-lane worktree owner
#: records), which are refused because they are not repository content at all.
MACHINE_LOCAL_PREFIXES: tuple[str, ...] = (
    ".aw/state/",
    LANE_SUBMISSION_SUBDIR + "/",
    ".aw/lane-scratch/",
)


class MissingInputDecision(NamedTuple):
    """The coordinator's answer to a missing-input report: ALWAYS a refusal (spec R3.3a, R3.5, R3.6).

    STRUCTURALLY INCAPABLE OF GRANTING ACCESS, which R3.6 requires to be a property of the TYPE and
    not a convention. Concretely, and each absence is deliberate:

      * there is NO `granted`/`permitted`/`allowed` field, so no call site can flip one;
      * there is NO field naming a location OUTSIDE the lane (no source path, no absolute path, no
        original-checkout path), so even a careless `as_dict()` cannot leak one into an artifact;
      * `verdict` has exactly ONE legal value, `MISSING_INPUT_VERDICT_REFUSED`, because the module
        defines no other verdict constant.

    `rule` names WHICH reject class fired and `detail` carries the worker's own stated reason, so the
    record is precise (R3.5) rather than a bare failure. `source` is provenance only: a worker token
    and a denied permission event produce the SAME verdict through the SAME path (R3.7).

    HONEST LIMIT, stated because spec Goal 5 requires it: Python has no sealed types, so this is an
    ACCIDENT GUARD plus a test that fails on a grant-shaped field, not a proof that no future edit
    could add one. What it does guarantee is that such an edit cannot be silent.
    """

    path: str
    reason: str
    rule: str
    source: str = MISSING_INPUT_SOURCE_TOKEN
    detail: str = ""
    verdict: str = MISSING_INPUT_VERDICT_REFUSED

    def as_dict(self) -> dict[str, Any]:
        """The refusal exactly as it is recorded on the attempt and in the event log (R3.5)."""

        record: dict[str, Any] = {
            "path": self.path,
            "verdict": self.verdict,
            "rule": self.rule,
            "reason": self.reason,
            "source": self.source,
            # Stated on EVERY record, not merely implied by the absence of a copy: an auditor reading
            # one refusal must be able to see that no materialization happened without cross-checking
            # the filesystem (spec R3.3a, R3.6).
            "copied_into_lane": False,
            "granted_original_checkout_access": False,
        }
        if self.detail:
            record["worker_stated_reason"] = self.detail
        return record


def format_missing_input_token(path: str, why: str) -> str:
    """Render the ONE report token form (spec R3.1), the same shape the prompt names.

    Paired with `parse_missing_input_token` so emit and parse cannot drift, and BOTH derive their
    separator and prefix from `MISSING_INPUT_TOKEN_FORM` - the constant `cqx5v7` already publishes
    into the prompt (R1.4) - rather than hardcoding a second spelling of the shape. That constant in
    turn composes around `wtiso_gate.AW_MISSING_INPUT`, so the stable error code, the prompt text, and
    this emitter all trace to ONE definition (`604wra`, R6.1).

    THIS IS THE SINGLE DEFINITION. `wtiso_gate.format_missing_input` delegates here; it does not hold
    a second implementation. Do not "simplify" either side into a local render.
    """

    return "{0}:{1}:{2}".format(_token_prefix(), path, why)


def _token_prefix() -> str:
    """The token's leading code, READ OUT OF `MISSING_INPUT_TOKEN_FORM` rather than duplicated.

    Deriving it is the point: the prompt text and the parser are then provably the same shape, so a
    change to the published form cannot leave the parser matching the old one.
    """

    return MISSING_INPUT_TOKEN_FORM.split(":", 1)[0]


def parse_missing_input_token(line: str) -> "tuple[str, str] | None":
    """Parse one `AW_MISSING_INPUT:<repo-relative-path>:<why>` line into `(path, why)`, else `None`.

    Returns `None` for any line that is not a report, because this is called on EVERY line of a
    child's stdout: a driver must not raise on ordinary output. A line that IS a report but carries
    an empty path or no reason is a MALFORMED report, and the caller
    (`classify_missing_input_report`) refuses it with `REJECT_MALFORMED_TOKEN` rather than ignoring
    it - silently dropping a malformed report is how a worker's genuine need disappears.

    THE REASON MAY CONTAIN COLONS (`split` with `maxsplit=2`), because a worker writes prose there.
    """

    prefix = _token_prefix()
    text = line.strip()
    if not text.startswith(prefix + ":"):
        return None
    parts = text.split(":", 2)
    if len(parts) < 3:
        return "", ""
    return parts[1].strip(), parts[2].strip()


def _relative_to_checkout(path: str, checkout: Path) -> "Path | None":
    """Resolve a repo-relative request against the checkout, or `None` if it escapes it.

    Uses `os.path.normpath` on the RELATIVE text before joining, so `a/../../etc/passwd` is caught by
    the escape rule rather than by whatever the filesystem happens to contain. Symlinks are resolved
    afterwards, so a link inside the checkout that points out of it is an escape too.
    """

    normalized = os.path.normpath(path)
    if normalized.startswith("..") or os.path.isabs(normalized):
        return None
    candidate = (checkout / normalized).resolve()
    try:
        checkout_resolved = checkout.resolve()
    except OSError:
        checkout_resolved = checkout
    if candidate != checkout_resolved and checkout_resolved not in candidate.parents:
        return None
    return candidate


def classify_missing_input_report(
    path: str,
    why: str = "",
    *,
    checkout: Path | str,
    source: str = MISSING_INPUT_SOURCE_TOKEN,
) -> MissingInputDecision:
    """THE ONE classification path for a missing-input report (spec R3.3, R3.5, R3.6, R3.7).

    COORDINATOR-SIDE ONLY, which is R3.3's first clause: this runs in the driver process, never in
    the lane, so resolving the request never hands the worker a path it could not already see.

    ALWAYS REFUSES (R3.3a as amended). The reject SHAPES still matter, because R3.5 requires the
    record to name WHY, and an auditor must be able to tell "you asked for something malformed" from
    "your request was well-formed but no permitted path exists". The eight R3.3 shapes are checked
    first, in the order the spec lists them, and a well-formed survivor is refused with
    `REJECT_WITHDRAWN_REPAIR`.

    THE COORDINATOR-SURFACE CLASS COMES FROM THE SHARED PREDICATE, by CALL (spec R3.3's last clause,
    CID-2). `worktree_lease.path_is_worker_forbidden` owns the question "is this a coordinator-owned
    surface?" and is consulted for it rather than having its five hints copied here, so the two
    cannot drift. The OTHER classes are properties of a requested PATH (absolute, escaping, a
    directory, absent) rather than a list of protected surfaces, so they are checked beside it; they
    are deliberately NOT pushed into that predicate, because it is also consulted by
    `assert_worker_scope` to validate a lane's declared WRITES and widening it would change a
    sibling's rule (see the walkthrough's note for `604wra`, which owns R6 consolidation).

    NEVER RAISES on a bad request. Every failure mode is a refusal RECORD, because this is called
    from a driver's stdout loop where an exception would kill a healthy turn.
    """

    from agent_workflows import worktree_lease

    root = Path(checkout)
    requested = (path or "").strip()
    detail = (why or "").strip()

    if not requested:
        return MissingInputDecision(
            path=requested,
            rule=REJECT_MALFORMED_TOKEN,
            reason=(
                "the report named no path, so there is nothing to resolve; the required form is "
                + MISSING_INPUT_TOKEN_FORM
            ),
            source=source,
            detail=detail,
        )
    normalized = requested.replace("\\", "/")

    if os.path.isabs(requested) or _looks_absolute(normalized):
        return MissingInputDecision(
            path=requested,
            rule=REJECT_ABSOLUTE,
            reason=(
                "an absolute path is refused: a report must name a REPO-RELATIVE path, and honoring "
                "an absolute one would describe a location outside the lane"
            ),
            source=source,
            detail=detail,
        )

    # ORDER MATTERS from here. The surface/lane/state/git classes are decided from the PATH TEXT, so
    # they are reported even for a path that does not exist - which is the honest answer: "you may
    # not ask for that" is more precise than "that is missing".
    if worktree_lease.path_is_worker_forbidden(normalized):
        return MissingInputDecision(
            path=requested,
            rule=REJECT_COORDINATOR_SURFACE,
            reason=(
                "the path is a COORDINATOR-OWNED surface (refused by the shared "
                "`worktree_lease.path_is_worker_forbidden` predicate), which the driver owns and a "
                "worker never reads or writes"
            ),
            source=source,
            detail=detail,
        )
    if normalized == worktree_lease.WORKTREES_SUBDIR or normalized.startswith(
        worktree_lease.WORKTREES_SUBDIR + "/"
    ):
        return MissingInputDecision(
            path=requested,
            rule=REJECT_SIBLING_LANE,
            reason=(
                "the path is inside the per-lane worktrees root, so it names either a SIBLING LANE's "
                "workspace or the root itself; a lane is isolated from every other lane"
            ),
            source=source,
            detail=detail,
        )
    if any(normalized.startswith(prefix) for prefix in MACHINE_LOCAL_PREFIXES):
        return MissingInputDecision(
            path=requested,
            rule=REJECT_MACHINE_STATE,
            reason=(
                "the path is MACHINE-LOCAL state (driver run state, lane submissions, or lane "
                "scratch) rather than repository content, so it is not a lane input at all"
            ),
            source=source,
            detail=detail,
        )
    if normalized == ".git" or normalized.startswith(".git/"):
        return MissingInputDecision(
            path=requested,
            rule=REJECT_GIT_ADMIN,
            reason=(
                "the path is the GIT ADMINISTRATION directory; the driver performs every git "
                "mutation after the worker exits, so a worker never needs it"
            ),
            source=source,
            detail=detail,
        )

    resolved = _relative_to_checkout(requested, root)
    if resolved is None:
        return MissingInputDecision(
            path=requested,
            rule=REJECT_ESCAPES_CHECKOUT,
            reason=(
                "the path ESCAPES the checkout once normalized, so it names a location outside the "
                "repository the lane is a worktree of"
            ),
            source=source,
            detail=detail,
        )
    if resolved.is_dir():
        return MissingInputDecision(
            path=requested,
            rule=REJECT_DIRECTORY,
            reason=(
                "the path names a DIRECTORY rather than a file; a report must name one specific "
                "required file so the need is unambiguous"
            ),
            source=source,
            detail=detail,
        )
    if not resolved.exists():
        return MissingInputDecision(
            path=requested,
            rule=REJECT_ABSENT,
            reason=(
                "the path DOES NOT EXIST in the checkout, so no input could satisfy the report even "
                "if a permitted path existed"
            ),
            source=source,
            detail=detail,
        )

    # WELL-FORMED AND STILL REFUSED, and this is the branch the amendment created. Nothing is wrong
    # with the path; there is simply no permitted path any more (spec R3.3a). Saying so precisely is
    # what R3.5 requires: an auditor must not read this as a malformed request.
    return MissingInputDecision(
        path=requested,
        rule=REJECT_WITHDRAWN_REPAIR,
        reason=(
            "the request is well-formed, but NOTHING is materialized into a lane on request: spec "
            "7ckptx R3.3a withdrew the permit-and-copy branch, so the driver RECORDS the need for a "
            "human or a follow-up instead of satisfying it inline. If this input is genuinely "
            "required, the conforming fix is UP-FRONT lane assembly under an explicit policy, not a "
            "request-time copy"
        ),
        source=source,
        detail=detail,
    )


def _looks_absolute(normalized: str) -> bool:
    """True for a POSIX or Windows-style absolute path, checked on the SLASH-NORMALIZED text.

    `os.path.isabs` is platform-dependent (`C:/x` is not absolute on POSIX), and a report is
    classified by the COORDINATOR, which may run on a different platform than the text was written
    on. Refusing both spellings everywhere is the fail-closed direction.
    """

    if normalized.startswith("/"):
        return True
    return len(normalized) >= 3 and normalized[1] == ":" and normalized[2] == "/"


def classify_denied_permission_path(
    path: str,
    why: str = "",
    *,
    checkout: Path | str,
) -> MissingInputDecision:
    """R3.7: route a DENIED host permission event through the SAME path, so there is ONE rule.

    This is deliberately a thin call to `classify_missing_input_report` with a different `source`,
    and NOT a second classifier. The requirement is that a denied event pointing into the original
    checkout produces the SAME decision as the equivalent worker token for that path (criterion A19),
    so the only difference the record may carry is PROVENANCE.

    WHY IT MATTERS THAT THIS IS ONE LINE: child `lhmrhx` produces the denial (the opencode host is
    configured with `permission.external_directory=deny`), and this plan classifies what that catches.
    Two classifiers would let the driver refuse an ask one way and a report another, which is exactly
    the "hook rule differs from driver" hazard the shared-predicate rule exists to prevent.
    """

    return classify_missing_input_report(
        path,
        why,
        checkout=checkout,
        source=MISSING_INPUT_SOURCE_PERMISSION,
    )


class MissingInputObserver:
    """The per-turn, host-neutral observer both drivers feed their child's stdout to (spec R3).

    ONE PER TURN, constructed by the driver adapter with the turn's own `checkout`. `observe_line` is
    called for EVERY line, exactly like `TurnBoundWatch.note_progress` already is, and returns the
    decision it recorded (or `None` for an ordinary line) so a caller can react without re-parsing.

    IT DOES NOT BLOCK THE WORKER, which is R3.1's explicit requirement: observing a report records a
    refusal and marks the lane paused; it never waits for an answer, and it never opens an
    interactive prompt (R3.2 - there is no answerer in an unattended turn, which is the measured
    deadlock this whole Set exists to prevent).

    `paused` is the PRESERVE-AND-PAUSE signal (R3.2). It is advisory state the driver reads AFTER the
    turn to keep the lane rather than reclaim it; nothing here tears a lane down, and nothing here
    copies a file into one.
    """

    def __init__(self, checkout: Path | str) -> None:
        self.checkout = Path(checkout)
        self.decisions: list[MissingInputDecision] = []
        self.paused = False
        self.pause_reason = ""

    def observe_line(self, line: str) -> "MissingInputDecision | None":
        """Classify one line of worker output; record and pause if it is a report."""

        parsed = parse_missing_input_token(line)
        if parsed is None:
            return None
        path, why = parsed
        return self.record(
            classify_missing_input_report(
                path, why, checkout=self.checkout, source=MISSING_INPUT_SOURCE_TOKEN
            )
        )

    def note_line(
        self,
        line: str,
        run_dir: Path,
        item: dict[str, Any],
        attempt_no: int,
    ) -> "MissingInputDecision | None":
        """Observe one line AND record any refusal: the whole per-line duty in ONE call.

        THE REASON THIS EXISTS rather than leaving each driver to do both steps: with `observe_line`
        and `record_missing_input_refusal` called separately, every driver carried a four-line
        `if`-block, and two hand-written copies of a two-step sequence is precisely the drift CID-3
        warns about (one host could observe while the other also recorded). Collapsing it here leaves
        each driver with a SINGLE call, so the twins cannot diverge on the STEPS - only on the fact of
        being wired at all, which `TwinParityTests` checks directly.

        Returns the recorded decision, or `None` for an ordinary line.
        """

        decision = self.observe_line(line)
        if decision is not None:
            record_missing_input_refusal(run_dir, item, attempt_no, decision)
        return decision

    def observe_denied_permission(
        self, path: str, why: str = ""
    ) -> MissingInputDecision:
        """R3.7's entry point: a denied host permission event for `path`, same rule as a token."""

        return self.record(
            classify_denied_permission_path(path, why, checkout=self.checkout)
        )

    def record(self, decision: MissingInputDecision) -> MissingInputDecision:
        """Record a refusal and PRESERVE-AND-PAUSE the lane (R3.2), without blocking the worker."""

        self.decisions.append(decision)
        self.paused = True
        self.pause_reason = "missing-input refused: {0} ({1})".format(
            decision.path or "<no path>", decision.rule
        )
        return decision

    def as_record(self) -> dict[str, Any]:
        """The attempt-level summary: every refusal, plus the pause state (R3.2, R3.5)."""

        return {
            "paused": self.paused,
            "pause_reason": self.pause_reason,
            "refusals": [d.as_dict() for d in self.decisions],
        }


def record_missing_input_refusal(
    run_dir: Path,
    item: dict[str, Any],
    attempt_no: int,
    decision: MissingInputDecision,
) -> dict[str, Any]:
    """Write ONE refusal onto the attempt AND to the event log (spec R3.5).

    HOST-NEUTRAL for the same reason `record_host_posture` is (R2.6): both drivers call THIS, so the
    record SHAPE cannot drift between hosts and an artifact reader is never misled by a per-host
    layout. The event is best-effort (`suppress`) because a logging failure must never escalate into
    killing a turn that is otherwise making progress - but the ATTEMPT record is written first, so
    the refusal survives even when the event write fails.
    """

    record = decision.as_dict()
    for attempt in item.get("attempts") or []:
        if attempt.get("number") == attempt_no:
            attempt.setdefault("missing_input_refusals", []).append(record)
            attempt["lane_paused_for_missing_input"] = True
            break
    else:
        item.setdefault("missing_input_refusals", []).append(record)
        item["lane_paused_for_missing_input"] = True
    with contextlib.suppress(Exception):
        runner_shared.append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": runner_shared.utc_now(),
                "event": "missing-input-refused",
                "id6": item.get("id6", ""),
                "attempt": attempt_no,
                **record,
            },
        )
    return record


def lane_preserved_for_missing_input(item: dict[str, Any]) -> bool:
    """True when a refused missing-input report means this lane MUST NOT be torn down (spec R3.2).

    THIS IS WHAT MAKES "PRESERVE AND PAUSE" REAL RATHER THAN A LOG LINE, and it is the half that is
    easy to omit: recording a refusal while the success path still force-removes the lane would
    destroy the very evidence the refusal points at. `teardown_worktree(force=True)` deletes the lane
    BRANCH and its uncommitted files unrecoverably (measured, see that function's own warning), so a
    lane holding a refusal is exactly the "classify first, tear down only a provably-empty lane" case.

    HOST-NEUTRAL and read from the ITEM (not from a live observer), so it answers correctly on a
    RESUMED run whose observer object is long gone: the flag is durable state written by
    `record_missing_input_refusal`, which is why that function writes the attempt record BEFORE the
    best-effort event.

    Checked at BOTH levels because `record_missing_input_refusal` writes at whichever exists: the
    attempt when the run has one, otherwise the item.
    """

    if item.get("lane_paused_for_missing_input"):
        return True
    for attempt in item.get("attempts") or []:
        if attempt.get("lane_paused_for_missing_input"):
            return True
    return False


# ---- R5.1 / R5.1a / R5.2: lane input materialization -----------------------------------------------
#
# WHY A MATERIALIZER EXISTS AT ALL, since a lane is already a `git worktree` at a commit and therefore
# already holds every TRACKED file. The inputs a turn needs are not all tracked. The driver RUNBOOK is
# the measured case: `runipd start` accepts `--runbook <path>` pointing anywhere on the operator's
# disk, and when none is given it SYNTHESIZES one into the run directory (`<run_dir>/runbook.md`),
# which lives under the coordinator's `.aw/records/runs/` and is NOT in the lane at any commit. So the
# one input every execute turn is handed was, before this, guaranteed NOT to be in the lane.
#
# THE MODE IS COPY, AND ONLY COPY (spec R5.1). A symlink would resolve back into the coordinator's
# tree, which reintroduces exactly the coupling the lane exists to remove; a HARD link would pass both
# a symlink check and a digest comparison while still sharing an inode with the original, so a later
# in-place write through either name would mutate the other (spec R5.2, plan F-1). `materialize_lane_inputs`
# therefore writes fresh bytes and `verify_link_independence` establishes INODE IDENTITY, not merely
# `not islink`.

#: Lane-relative home for materialized inputs and their manifest.
#:
#: Under `.aw/state/` for the same reason `LANE_SUBMISSION_SUBDIR` is: that prefix is gitignored, and
#: the lane is a worktree of the same commit, so a materialized input never appears as a dirty TRACKED
#: path in the lane and cannot contaminate the integration diff. This matters MORE here than for
#: submissions, because a materialized input is a COPY OF A TRACKED FILE in some cases (the plan
#: snapshot), and landing one at its natural tracked path would look like the worker edited it.
LANE_INPUT_SUBDIR = ".aw/state/lane-inputs"

#: The manifest filename inside `LANE_INPUT_SUBDIR/<revision>/`.
LANE_INPUT_MANIFEST_NAME = "manifest.json"

#: The ONLY materialization mode this module writes (spec R5.1). Present as a recorded FIELD rather
#: than implied by the manifest's existence, so a future mode cannot be introduced without the
#: manifest saying so and `verify_lane_input_manifest` refusing what it does not recognize.
MATERIALIZATION_MODE_COPY = "copy"

#: Input CLASSES a manifest entry may carry. The class is what lets a reader answer "was the runbook
#: materialized?" without pattern-matching a filename.
INPUT_CLASS_PLAN = "plan"
INPUT_CLASS_RUNBOOK = "runbook"
_INPUT_CLASSES = (INPUT_CLASS_PLAN, INPUT_CLASS_RUNBOOK)

#: Permission bits a sealed file carries: owner/group/other READ, no write bit anywhere (spec R5.1a
#: parts (i) and (ii)).
#:
#: HONEST LIMIT, and it must be stated wherever this is used (spec R5.1a, plan E-03 / V-03): this is
#: an ACCIDENT GUARD, NOT IMMUTABILITY and NOT a boundary. The owning user can restore the write bit
#: with one `chmod`, and the worker RUNS AS the owning user. What it buys is that an accidental
#: in-lane write - a stray editor save, a script that rewrites what it meant to read - FAILS LOUDLY
#: instead of silently rewriting the record of what was authorized. Under the threat model in spec 0.2
#: (an honest worker that can be confused, not an adversary) that is the whole intent. Any artifact
#: describing this as immutability is WRONG and spec R5.1a forbids it.
SEALED_FILE_MODE = 0o444


class MaterializedInput(NamedTuple):
    """One manifest entry (spec R5.1): what was copied, from where, and how.

    `path` is LANE-RELATIVE and POSIX-style, so the manifest names nothing outside the lane and is
    the same on any host (spec R1.1's discipline applied to the manifest itself). `source_path` is the
    repo-relative path the bytes CAME from when that is knowable, and `None` for a coordinator-owned
    input (a synthesized runbook under the run directory) which has no repo-relative location; it is
    never an absolute coordinator path, for the same containment reason.
    """

    path: str
    input_class: str
    source_sha256: str
    mode: str
    bytes: int
    source_path: str | None = None


class LaneInputManifest(NamedTuple):
    """The result of materializing one lane's inputs."""

    revision: int
    manifest_path: Path
    root: Path
    entries: tuple[MaterializedInput, ...]

    def entry(self, input_class: str) -> MaterializedInput | None:
        """The single entry of `input_class`, or `None`. Convenience for a caller that needs the
        lane-local path of a specific input (E-04's attachment localization uses this)."""
        for item in self.entries:
            if item.input_class == input_class:
                return item
        return None


def lane_input_root(lane_root: Path, revision: int) -> Path:
    """`<lane>/.aw/state/lane-inputs/rev-<N>`, the home of ONE revision's inputs and manifest.

    REVISION-SCOPED DIRECTORY, which is what makes spec R5.1a part (iii) mechanical rather than
    aspirational: because a revision's inputs live in their own directory, adding an input CANNOT
    require editing an existing entry - the new revision is a new directory with a new manifest, and
    the old one stays exactly as it was written. See `revise_lane_inputs`.
    """
    return Path(lane_root) / LANE_INPUT_SUBDIR / f"rev-{int(revision)}"


def lane_input_manifest_path(lane_root: Path, revision: int) -> Path:
    return lane_input_root(lane_root, revision) / LANE_INPUT_MANIFEST_NAME


def latest_lane_input_revision(lane_root: Path) -> int | None:
    """The highest revision materialized into this lane, or `None` if none has been.

    Read from the DIRECTORY NAMES rather than from a pointer file, so there is no second piece of
    state that can disagree with what is actually on disk.
    """
    base = Path(lane_root) / LANE_INPUT_SUBDIR
    revisions: list[int] = []
    try:
        children = list(base.iterdir())
    except OSError:
        return None
    for child in children:
        if not child.is_dir() or not child.name.startswith("rev-"):
            continue
        try:
            revisions.append(int(child.name[4:]))
        except ValueError:
            continue
    return max(revisions) if revisions else None


def _seal_file(path: Path) -> None:
    """Drop every write bit on `path` (spec R5.1a (i)/(ii)). An accident guard, NOT immutability."""
    os.chmod(path, SEALED_FILE_MODE)


def _unseal_for_write(path: Path) -> None:
    """Restore the owner write bit so the DRIVER can replace a file it owns.

    Needed because sealing is applied per revision and a caller may legitimately rewrite within the
    revision it is currently building (an interrupted materialization re-run over the same directory).
    That the driver can do this is not a hole in the seal: it is the same capability spec R5.1a
    concedes the owning user has, which is precisely why the seal is documented as an accident guard.
    """
    with contextlib.suppress(OSError):
        os.chmod(path, 0o644)


def materialize_lane_inputs(
    *,
    lane_root: Path,
    plan_path: Path | None = None,
    runbook_path: Path | None = None,
    repo: Path | None = None,
    revision: int = 1,
) -> LaneInputManifest:
    """COPY the turn's required inputs into the lane and write a SEALED manifest (spec R5.1, R5.1a, R5.2).

    Host-neutral by construction (spec R2.6, plan CID-2/CID-3): both drivers call THIS, and neither
    reimplements any part of it. A rule implemented once per host is a forked rule even while the
    copies agree.

    WHAT IS COPIED. Each of `plan_path` and `runbook_path` when supplied and readable. A source that
    does not exist is SKIPPED rather than fabricated, because writing an entry for a file whose bytes
    we never read would make the manifest a claim we cannot support - and the manifest is consumed as
    evidence of what the worker was authorized to use.

    HOW IT IS COPIED. Fresh bytes through `_atomic_write_bytes`, never `os.link`, never `os.symlink`,
    and never `shutil.copy2` (which would carry the source's mode across and fight the seal below).
    The digest recorded is computed from the bytes ACTUALLY WRITTEN, not from the source, so a
    truncated or partially-written copy cannot be recorded as a faithful one.

    THE SEAL. Every copied input, and then the manifest itself, is left mode `0444` (R5.1a (i)/(ii)),
    with the manifest sealed LAST so an interrupted run leaves an unsealed manifest rather than a
    sealed one describing files that were never finished.

    Returns the manifest. Idempotent for a given revision: re-running over an existing revision
    directory replaces its contents, which is what recovery of an interrupted materialization needs.
    """
    lane_root = Path(lane_root)
    root = lane_input_root(lane_root, revision)
    root.mkdir(parents=True, exist_ok=True)

    requested: list[tuple[str, Path]] = []
    if plan_path is not None:
        requested.append((INPUT_CLASS_PLAN, Path(plan_path)))
    if runbook_path is not None:
        requested.append((INPUT_CLASS_RUNBOOK, Path(runbook_path)))

    entries: list[MaterializedInput] = []
    for input_class, source in requested:
        try:
            payload = source.read_bytes()
        except OSError:
            # Absent or unreadable: record NOTHING. The missing-input cycle (spec R3, child `y5od1h`)
            # owns reporting a genuinely required input that is not there; inventing a manifest entry
            # here would hide it behind a record that looks satisfied.
            continue
        destination = root / f"{input_class}-{source.name}"
        if destination.exists():
            _unseal_for_write(destination)
        _atomic_write_bytes(destination, payload)
        # Digest the BYTES ON DISK, not `payload`: this is what makes the entry evidence about the
        # lane's file rather than about a variable in this process.
        written_digest = _sha256_file(destination)
        source_rel: str | None = None
        if repo is not None:
            with contextlib.suppress(ValueError):
                source_rel = (
                    Path(source).resolve().relative_to(Path(repo).resolve()).as_posix()
                )
        entries.append(
            MaterializedInput(
                path=destination.relative_to(lane_root).as_posix(),
                input_class=input_class,
                source_sha256=written_digest,
                mode=MATERIALIZATION_MODE_COPY,
                bytes=len(payload),
                source_path=source_rel,
            )
        )
        _seal_file(destination)

    manifest_path = root / LANE_INPUT_MANIFEST_NAME
    document = {
        "schema_version": 1,
        "revision": int(revision),
        "sealed": True,
        # Stated IN the artifact because spec R5.1a requires the honest limit to travel with the
        # claim, not only in this module's source.
        "seal_note": (
            "Read-only is an ACCIDENT GUARD, not immutability and not a boundary: the owning user "
            "can restore the write bit. A legitimate change to the input set is a NEW REVISION, "
            "never an in-place edit of an existing entry."
        ),
        "inputs": [entry._asdict() for entry in entries],
    }
    if manifest_path.exists():
        _unseal_for_write(manifest_path)
    _atomic_write_text(
        manifest_path, json.dumps(document, indent=2, sort_keys=True) + "\n"
    )
    # Sealed LAST, deliberately: see the docstring. An interrupt before this line leaves a writable
    # manifest, which is recoverable; the reverse would leave a sealed record of unfinished work.
    _seal_file(manifest_path)

    return LaneInputManifest(
        revision=int(revision),
        manifest_path=manifest_path,
        root=root,
        entries=tuple(entries),
    )


def read_lane_input_manifest(
    lane_root: Path, revision: int | None = None
) -> dict[str, Any] | None:
    """One revision's manifest document, or `None`. `revision=None` reads the LATEST."""
    if revision is None:
        revision = latest_lane_input_revision(lane_root)
        if revision is None:
            return None
    try:
        return json.loads(
            lane_input_manifest_path(lane_root, revision).read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return None


def revise_lane_inputs(
    *,
    lane_root: Path,
    plan_path: Path | None = None,
    runbook_path: Path | None = None,
    repo: Path | None = None,
) -> LaneInputManifest:
    """Materialize a NEW REVISION rather than editing an existing entry (spec R5.1a part (iii)).

    NO PRODUCT CALLER, AND THAT IS STATED RATHER THAN IMPLIED, because spec R3.4 requires it. R3.4
    ("copy on request") was WITHDRAWN by R3.3a: the repair cycle is now report-and-refuse only, so
    nothing is ever materialized into a lane in response to a worker request and no caller needs to
    revise a manifest today. R3.4 explicitly permits the MECHANISM to be built by the plan that owns
    the manifest - this plan - on the condition that it "MUST state that it has no consumer rather
    than implying one". This is that statement. The mechanism exists so R5.1a part (iii) is testable
    and so a future lane-assembly change (the conforming fix R3.3a points at) has one correct way to
    add an input; it is NOT evidence that a request-time copy path exists.

    Mechanically it is just "next revision, new directory", which is what makes part (iii) hold: an
    existing revision's manifest and inputs are never reopened, so there is no in-place edit to
    forbid.
    """
    current = latest_lane_input_revision(lane_root)
    return materialize_lane_inputs(
        lane_root=lane_root,
        plan_path=plan_path,
        runbook_path=runbook_path,
        repo=repo,
        revision=1 if current is None else current + 1,
    )


class LinkIndependenceResult(NamedTuple):
    """Whether every manifest-listed lane file has storage independent of its source (spec R5.2)."""

    independent: bool
    violations: tuple[str, ...]

    @property
    def reason(self) -> str:
        if self.independent:
            return "every manifest-listed lane path is an independent copy"
        return "; ".join(self.violations)


def verify_link_independence(
    lane_root: Path, revision: int | None = None
) -> LinkIndependenceResult:
    """Establish LINK INDEPENDENCE for every manifest-listed lane file (spec R5.2, criterion A12).

    WHY THIS IS NOT `not islink`, which is the whole point of R5.2 and of plan finding F-1. A HARD
    LINK is not a symlink and its bytes are identical to the source, so a check asserting
    `not os.path.islink(p)` AND `sha256(p) == sha256(src)` PASSES while `p` and the source share one
    inode - meaning a later write through EITHER name mutates the other, which is exactly the coupling
    the lane exists to remove. Digest equality is therefore evidence of FIDELITY and says nothing
    whatsoever about INDEPENDENCE.

    WHAT IS CHECKED, per entry, and all three are required:

      1. the lane path is not a symlink (the easy case, still necessary);
      2. its `st_nlink` is 1, so no OTHER name anywhere refers to this inode; and
      3. when the entry records a `source_path` that still exists in the surrounding checkout, its
         `(st_dev, st_ino)` differs from that source's, which catches the hard link DIRECTLY rather
         than inferring it from a link count.

    Check 2 is what makes this hold even when the source is GONE or unknown (a synthesized runbook
    under the coordinator's run directory has no repo-relative source at all): a link count of 1 is
    sufficient on its own to prove no second name shares the storage, whoever that second name might
    have been. Check 3 is kept because it names the actual counterparty in the failure message, which
    is what a human debugging a violation needs.
    """
    document = read_lane_input_manifest(lane_root, revision)
    if document is None:
        return LinkIndependenceResult(
            independent=False, violations=("no lane input manifest to verify",)
        )
    lane_root = Path(lane_root)
    violations: list[str] = []
    entries = document.get("inputs") or []
    if not entries:
        return LinkIndependenceResult(
            independent=False, violations=("manifest lists no inputs",)
        )
    for entry in entries:
        rel = entry.get("path") or ""
        target = lane_root / rel
        if target.is_symlink():
            violations.append(f"{rel}: is a symlink")
            continue
        try:
            stat_result = os.stat(target, follow_symlinks=False)
        except OSError as exc:
            violations.append(f"{rel}: cannot stat ({exc})")
            continue
        if stat_result.st_nlink != 1:
            violations.append(
                f"{rel}: st_nlink={stat_result.st_nlink} (expected 1); another name shares this "
                "inode, so it is a hard link and not an independent copy"
            )
        source_rel = entry.get("source_path")
        if source_rel:
            source = lane_root / source_rel
            try:
                source_stat = os.stat(source, follow_symlinks=False)
            except OSError:
                source_stat = None
            if source_stat is not None and (
                (stat_result.st_dev, stat_result.st_ino)
                == (source_stat.st_dev, source_stat.st_ino)
            ):
                violations.append(
                    f"{rel}: shares inode {stat_result.st_ino} with {source_rel}"
                )
    return LinkIndependenceResult(
        independent=not violations, violations=tuple(violations)
    )


class SealResult(NamedTuple):
    """Whether a revision satisfies all three parts of the seal definition (spec R5.1a)."""

    sealed: bool
    violations: tuple[str, ...]

    @property
    def reason(self) -> str:
        if self.sealed:
            return "manifest and every listed input carry no write bit"
        return "; ".join(self.violations)


def verify_lane_input_seal(lane_root: Path, revision: int | None = None) -> SealResult:
    """Check seal parts (i) and (ii): no write bit on the manifest or on any listed input (R5.1a).

    Part (iii) (a change arrives as a NEW REVISION, never an in-place edit) is STRUCTURAL and is not
    checked here because it cannot be read off a single revision's permissions: it is established by
    `revise_lane_inputs` writing a new `rev-<N>` directory and by `latest_lane_input_revision`
    reporting it, which is what the test exercises.

    NO WRITE BIT FOR ANYONE, not merely for the owner. R5.1a says "no write bit for the owning user",
    which is the part that matters since the worker RUNS AS the owner; group/other are dropped too
    because leaving them would make the mode misleading to a reader without weakening or strengthening
    the actual guard.

    STILL AN ACCIDENT GUARD. A passing result means an accidental write FAILS; it does not mean the
    bytes cannot be changed, because the owner can `chmod` first. Do not describe a passing result as
    immutability (R5.1a).
    """
    document = read_lane_input_manifest(lane_root, revision)
    if document is None:
        return SealResult(
            sealed=False, violations=("no lane input manifest to verify",)
        )
    if revision is None:
        revision = int(document.get("revision", 0))
    lane_root = Path(lane_root)
    violations: list[str] = []

    manifest_path = lane_input_manifest_path(lane_root, revision)
    try:
        manifest_mode = os.stat(manifest_path).st_mode & 0o777
    except OSError as exc:
        return SealResult(sealed=False, violations=(f"cannot stat manifest ({exc})",))
    if manifest_mode & 0o222:
        violations.append(
            f"{LANE_INPUT_MANIFEST_NAME}: mode {manifest_mode:04o} carries a write bit"
        )

    for entry in document.get("inputs") or []:
        rel = entry.get("path") or ""
        try:
            mode = os.stat(lane_root / rel).st_mode & 0o777
        except OSError as exc:
            violations.append(f"{rel}: cannot stat ({exc})")
            continue
        if mode & 0o222:
            violations.append(f"{rel}: mode {mode:04o} carries a write bit")

    return SealResult(sealed=not violations, violations=tuple(violations))


class ManifestVerification(NamedTuple):
    """The composed R5.1/R5.1a/R5.2 verdict for one revision."""

    conforming: bool
    violations: tuple[str, ...]

    @property
    def reason(self) -> str:
        if self.conforming:
            return "manifest conforms: every entry a digested copy, sealed, link-independent"
        return "; ".join(self.violations)


def verify_lane_input_manifest(
    lane_root: Path, revision: int | None = None
) -> ManifestVerification:
    """The whole R5 input contract for one revision, in ONE predicate (spec R6.1).

    Composed rather than duplicated: the drivers, the tests, and any later retention reader all call
    THIS, so "is this lane's input set conforming?" has one answer. It checks that every entry records
    mode `copy` with a non-empty digest that matches the bytes on disk (R5.1), that the seal holds
    (R5.1a i/ii), and that storage is independent (R5.2).
    """
    document = read_lane_input_manifest(lane_root, revision)
    if document is None:
        return ManifestVerification(
            conforming=False, violations=("no lane input manifest",)
        )
    lane_root = Path(lane_root)
    violations: list[str] = []
    entries = document.get("inputs") or []
    if not entries:
        violations.append("manifest lists no inputs")
    for entry in entries:
        rel = entry.get("path") or "<unnamed>"
        if entry.get("mode") != MATERIALIZATION_MODE_COPY:
            violations.append(
                f"{rel}: mode {entry.get('mode')!r} is not {MATERIALIZATION_MODE_COPY!r}"
            )
        if entry.get("input_class") not in _INPUT_CLASSES:
            violations.append(f"{rel}: unrecognized class {entry.get('input_class')!r}")
        digest = entry.get("source_sha256") or ""
        if not digest:
            violations.append(f"{rel}: records no source digest")
            continue
        target = lane_root / rel
        try:
            actual = _sha256_file(target)
        except OSError as exc:
            violations.append(f"{rel}: cannot read to digest ({exc})")
            continue
        if actual != digest:
            violations.append(
                f"{rel}: recorded digest {digest[:12]} does not match on-disk {actual[:12]}"
            )
    seal = verify_lane_input_seal(lane_root, revision)
    if not seal.sealed:
        violations.extend(seal.violations)
    links = verify_link_independence(lane_root, revision)
    if not links.independent:
        violations.extend(links.violations)
    return ManifestVerification(conforming=not violations, violations=tuple(violations))


# ---- R5.4: the clean-base guard ---------------------------------------------------------------------


def parse_porcelain_paths(porcelain: str) -> set[str]:
    """Every path named by `git status --short`/`--porcelain` output.

    THE ONE PORCELAIN PARSER (spec R6.1). It was previously written TWICE, inline and identically, in
    `oc_runipd.dirty_tree_overlap` and `agy_runipd.dirty_tree_overlap`; both now delegate here, and
    the clean-base guard below uses it rather than adding a third copy. Forking a rule is
    non-conforming even while the copies agree (R6.1), and this one had already been copied once.

    Format: `XY<space><path>`, where a rename or copy renders as `orig -> dest`. BOTH endpoints of a
    rename are returned, because a rename dirties the origin and the destination and a caller asking
    "is this path dirty?" must get `True` for either.
    """
    paths: set[str] = set()
    for line in porcelain.splitlines():
        if not line.strip():
            continue
        # Strip the two status columns and the following space: entries are `XY path` (min 3 chars).
        entry = line[3:] if len(line) > 3 else line.strip()
        if " -> " in entry:
            orig, dest = entry.split(" -> ", 1)
            paths.add(orig.strip())
            paths.add(dest.strip())
        else:
            paths.add(entry.strip())
    return {p for p in paths if p}


class CleanBaseResult(NamedTuple):
    """Whether a checkout is a valid base for an unattended isolated turn (spec R5.4)."""

    clean: bool
    dirty_paths: tuple[str, ...]

    @property
    def reason(self) -> str:
        if self.clean:
            return "target checkout has no dirty tracked paths"
        return (
            "refusing to launch an unattended isolated turn: the target checkout has "
            f"{len(self.dirty_paths)} dirty TRACKED path(s), which a lane created from HEAD would "
            "silently omit: " + ", ".join(self.dirty_paths)
        )


def evaluate_clean_base(
    porcelain: str,
) -> CleanBaseResult:
    """Classify `git status --porcelain --untracked-files=no` output for the R5.4 guard.

    PURE, taking the text rather than running git, so both drivers share the RULE while each supplies
    its own runner (the two modules deliberately keep separate git wrappers), and so a test can drive
    every case without a repository.

    UNTRACKED FILES ARE EXCLUDED BY THE CALLER'S `--untracked-files=no`, and that exclusion is
    DELIBERATE (spec R5.4, plan finding F-4). A lane is created from a COMMIT, so an untracked file's
    absence from the lane is CORRECT and expected - nothing was silently omitted. An uncommitted
    TRACKED edit is the opposite: it is a change to a file the lane DOES have, at a version the lane
    does NOT, so the worker would silently work against a base missing it. Tightening this to include
    untracked files would make an unattended run unstartable in essentially any working checkout, which
    is why it must not be "fixed".

    HOW THIS DIFFERS FROM THE INTEGRATION-TIME OVERLAP CHECK (`dirty_tree_overlap`), since both read
    porcelain and the two are easy to confuse. That one runs AFTER a lane's work exists and asks a
    NARROW, RELATIVE question: does the incoming lane's `changed_files` INTERSECT main's dirty paths,
    i.e. would merging clobber an un-owned edit to those specific paths? This one runs BEFORE any
    worker is spawned and asks a BROAD, ABSOLUTE question: is the whole tracked tree clean, i.e. is
    HEAD a complete base? Neither subsumes the other: a dirty file OUTSIDE the incoming change is
    irrelevant to integration but still makes the base incomplete here, and this check cannot run at
    integration time because there is no `changed_files` yet.
    """
    dirty = sorted(parse_porcelain_paths(porcelain))
    return CleanBaseResult(clean=not dirty, dirty_paths=tuple(dirty))


# ---- R5.3: attachment localization ------------------------------------------------------------------


def localize_attachment(
    *,
    lane_root: Path | None,
    fallback: Path | str,
    input_class: str,
    revision: int | None = None,
) -> str:
    """The path an isolated turn's `--file` attachment must use (spec R5.3).

    Returns the MATERIALIZED lane-local copy of `input_class` when this is an isolated turn and the
    manifest lists one; otherwise returns `fallback` unchanged. So a NON-isolated turn is byte-for-byte
    untouched (the same discipline spec R1.3 imposes on the prompt), and an isolated turn attaches only
    what is provably inside its lane.

    FALLBACK IS DELIBERATE AND IS NOT A HOLE IN R5.3. If materialization did not record this class, the
    honest options are to attach the out-of-lane original or to attach nothing. Attaching nothing would
    silently drop an input the turn was designed to have, so the caller keeps the original and the
    R5.3 assertion FAILS LOUDLY in test rather than a missing attachment failing mysteriously at
    runtime. In the product path the materializer runs immediately before this, so the fallback is
    reached only when the source itself was absent - which is the missing-input cycle's business
    (spec R3), not this function's.
    """
    if lane_root is None:
        return str(fallback)
    document = read_lane_input_manifest(lane_root, revision)
    if document is None:
        return str(fallback)
    for entry in document.get("inputs") or []:
        if entry.get("input_class") == input_class:
            return str(Path(lane_root) / entry["path"])
    return str(fallback)


def attachment_values(argv: Sequence[str]) -> list[str]:
    """Every `--file` value in a constructed argv, in order.

    Exists so the R5.3 check reads the ARGV THE CHILD ACTUALLY RECEIVES rather than re-deriving what
    it should have been, and so it covers ALL attachments instead of the one a test happened to think
    of (spec A13 requires the assertion over every value, with at least two present).
    """
    values: list[str] = []
    for index, token in enumerate(argv):
        if token == "--file" and index + 1 < len(argv):
            values.append(argv[index + 1])
    return values


def attachments_outside_lane(argv: Sequence[str], lane_root: Path) -> list[str]:
    """The `--file` values that do NOT resolve inside `lane_root` (spec R5.3, criterion A13).

    Resolved with `os.path.realpath` on BOTH sides before comparing, so a symlinked lane path or a
    `..` segment cannot make an out-of-lane target look contained. A value that resolves to the lane
    root itself is not an attachment to a file and counts as outside.
    """
    lane_real = Path(os.path.realpath(str(lane_root)))
    outside: list[str] = []
    for value in attachment_values(argv):
        target = Path(os.path.realpath(value))
        if target == lane_real or lane_real not in target.parents:
            outside.append(value)
    return outside

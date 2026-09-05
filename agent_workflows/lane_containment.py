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

  * NOT the missing-input CLASSIFIER, and not `wtiso_gate.format_missing_input` /
    `parse_missing_input`. Those bodies are owned by the missing-input child (`y5od1h`, spec R3), and
    spec R6.3 forbids a plan from implementing a body it is not chartered for. This module carries
    only the token's DOCUMENTED FORM, as prompt text, so R1.4 can be satisfied without forking R3's
    rule. A reader looking for the parse/emit implementation must go to `wtiso_gate`.

HONEST LIMIT, stated because spec Goal 5 requires it and because overstating it is the failure mode:
everything here is SIGNAL PURITY plus DRIVER-SIDE BOOKKEEPING, not a boundary. Nothing in this module
prevents a worker with shell access from writing outside its lane; `host_sandbox_profile`'s own
docstring records that prose, hooks, environment variables and Python role checks cannot enforce that.
What this module guarantees is that the instructions no longer ASK the worker to leave the lane, and
that a worker which stays inside it does not lose its work.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, NamedTuple

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
#: R3.1). This is DOCUMENTATION TEXT for the prompt, not an implementation of the token: emit/parse
#: are `wtiso_gate.format_missing_input` / `parse_missing_input`, owned by child `y5od1h` (spec R3),
#: and R6.3 forbids implementing a body this plan is not chartered to own. The form is stated in one
#: place so the prompt and that later implementation cannot disagree about the shape.
MISSING_INPUT_TOKEN_FORM = "AW_MISSING_INPUT:<repo-relative-path>:<why it is required>"

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

"""The ONE artifact location-and-status audit: "is this artifact where its recorded status says it
should be, and does its own front matter agree?"

BOTH `aw runs` AND `aw doctor` CALL THIS MODULE, so the two diagnosis surfaces cannot drift apart.
That wording is deliberate and follows `check_engine.evaluate_review_finding_escalation`, whose
docstring exists for the same reason: an audit VERDICT that two tools compute separately is an audit
two tools will eventually disagree about. Before IPD `6ltz1y` this predicate lived privately in
`run_viewer.py`, so `aw runs` could tell an operator that a step's plan was in the wrong directory
while `aw doctor`, the tool a human actually reaches for, could not see it at all. The in-repo
precedent for the failure this prevents is `render_stream` plus `tests/test_runner_refork_guard.py`,
which pins 28 (runner, symbol) pairs because two host drivers had already re-forked the same helpers.

WHY THE FILE LOOKUP RESOLVES THROUGH ``selectors`` RATHER THAN A PRIVATE DIRECTORY LIST.
The extracted implementation hardcoded nine directories and returned the FIRST filename containing
the queried id6. Two measured defects came with that, and carrying either into a second consumer is
what this module exists to avoid:

* THE TYPE SET. The list covered plans and specs ONLY, so an artifact of any other type carrying the
  queried id6 was invisible: a `backlog` record returned ``None``. Latent for `aw runs` (whose steps
  are plans today) and live for any second consumer. NOTE, because the motivation is easy to get
  wrong: the old list was NOT blind to archived plans. `aw plans archive` writes MONTHLY ``YYYYMM/``
  shards INSIDE the terminal directories (`plans_archive`; `artifact_core.shard_for_date` returns
  ``cleaned[:6]``), those directories were in the list, and the loop used ``rglob``, so a plan at
  ``executed/202608/...`` was already found. The nonexistent ``plans/archive`` entry and the two
  legacy ``.agents/`` paths were dead weight in a list, not blind spots.
* FIRST-MATCH-WINS WITH NO COLLISION POLICY. ``selectors.resolve`` treats an id6 matching several
  files as "a data bug to fix, not overridable by --force" (``MATCH_ID6`` is in ``UNIQUE_KINDS``);
  the private loop silently picked one. :func:`find_artifact` therefore reports a collision through
  :attr:`ArtifactLookup.collisions` instead of hiding it behind an arbitrary pick.

MATCHING SEMANTICS: EXACT DECLARED ``- Id:`` FIRST, FILENAME ID6 SECOND, and both halves are
load-bearing. The exact rule is what makes widening the type set SAFE: the old substring rule would
also match a REVIEW record, because a review carries its SUBJECT's id6 in its filename, and reviews
were previously unreachable only because the hardcoded list never searched them. A review declares
``- Subject-Id:`` and not ``- Id:``, so the exact rule skips it for free. But an exact-only rule
would REGRESS the audit, which is why the filename tier exists. HISTORICAL REASON, NOW FIXED AT THE
SOURCE: ``selectors`` used to read a HARD-CAPPED 4096-byte header, and measured on this repository
268 of 1202 records declare an ``- Id:`` BEYOND that cap (this plan's own file declares it at byte
6485), so an exact-only lookup reported 268 artifacts as ``missing_entirely`` that were plainly on
disk. That truncation was a BUG and was fixed: ``selectors._read_header`` now reads to the end of the
metadata block (see its note, and the `runnoop`/`7ewc74` incident it records), so the exact tier no
longer loses a late ``- Id:``. The filename tier is KEPT regardless, because it covers a record with
no declared ``- Id:`` at all, which is a different gap than truncation. The filename tier is
restricted to the id6 field of the clustered naming grammar (``artifact_naming.parse_clustered``),
never a bare substring, so it cannot match a review record either.

WHY IT IS LIVENESS-AWARE, and do not remove the guard. The audit maps a recorded status onto an
expected directory (terminal statuses onto their terminal directory, everything pre-terminal onto
``pending/``). A step that is RUNNING RIGHT NOW legitimately has its plan in ``pending/`` with a
status that is neither terminal nor ``pending``, so a liveness-blind consumer reports every in-flight
run as drift, which is the fastest way to make a new diagnostic ignored. Liveness is an INPUT here,
never a derivation: it is computed from a RUN DIRECTORY's PID and lock holder
(``run_viewer.inspect_run_pid_and_runtime``, ``is_live=(holder != HOLDER_NONE)``) and this module only
carries it through. ``check_engine._receipt_is_live`` is the in-repo precedent, including its
FAIL-SAFE direction: when liveness cannot be determined, do NOT report.

THE ``aw check`` DECISION (IPD `6ltz1y` E-05, maintainer ruling 2026-09-08): NO, `aw check` does not
gain this audit as a rule, and the tracked-only alternative is not the right shape either.
`aw check` is FAIL-CLOSED in CI, while this audit's expected status comes from a RUN's recorded step
status, and run records live under ``.aw/records/runs/``, which is GITIGNORED and absent from a fresh
clone and from every isolated lane worktree the runner allocates. The same commit would therefore
produce different `aw check` results in CI than locally, and a repository-level gate whose answer
depends on untracked local state is not a gate. WHAT WOULD MAKE A CHECK RULE VIABLE is an audit keyed
ONLY on tracked artifacts (comparing a record's own ``- Status:`` against its directory, with no run
input) - but that predicate ALREADY SHIPS as ``ipd_schema._check_path_status``, surfaced as lint rule
``IPD-M105``, so building it here would duplicate a working rule. The honest remaining gap is
REACHABILITY (getting ``IPD-M105`` into the sweep), which plan `k9awrq` owns. The same
run-record-coupling objection applies to `aw doctor`, which is why the doctor consumer here is
TRACKED-ONLY: see :func:`audit_tracked_artifact`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_naming as _naming
from agent_workflows import selectors as _sel

# The status bullet as this audit reads it. Kept byte-identical to the pattern that shipped inside
# `run_viewer` (`^- Status:\s*(\S+)\s*$`) so the extraction changes no verdict: a multi-word status
# yields NO match here, exactly as before, which matches `selectors._STATUS_RE`'s documented parity
# constraint rather than `plans_index._META_RE`'s looser reading.
_STATUS_LINE_RE = re.compile(r"(?m)^- Status:\s*(\S+)\s*$")

# Every record type whose tree may hold an artifact this audit is asked about. `selectors.resolve`
# takes ONE `record_type` per call and there is deliberately no all-types entry point, so a caller
# that does not know the type loops this vocabulary. Ordered by PRECEDENCE, which matters only for
# the filename tier (an exact `- Id:` match is unique by contract, and a multi-type exact match is
# reported as a collision rather than silently resolved). `plans` leads because every caller today
# audits plans; `other` is last because it is a catch-all.
TYPE_PRECEDENCE: tuple[str, ...] = (
    "plans",
    "specs",
    "backlog",
    "releases",
    "roadmaps",
    "research",
    "prompts",
    "walkthroughs",
    "comms",
    "other",
)

# The recorded status values that expect their artifact in a TERMINAL directory of the same name,
# mapped onto that directory. Everything else expects `pending/`.
_TERMINAL_EXPECTED_DIR = {
    "executed": "executed",
    "superseded": "superseded",
    "not-executed": "not-executed",
    "reusable": "reusable",
}

# The recorded statuses that mean THE RUN BELIEVED IT SUCCEEDED. A difference under one of these is
# backwards-looking: the run says done, so the artifact had better be terminal.
_RUN_SUCCESS_STATUSES = frozenset({"executed"})

# The terminal dispositions that are a RETIREMENT rather than an execution. Reaching one of these is
# forward progress, but of a kind that leaves NO finalize commit (see `CLASS_RETIRED`).
_RETIREMENT_DIRS = frozenset({"superseded", "not-executed"})


# --------------------------------------------------------------------------------------
# THE DIRECTIONAL CLASSIFICATION (IPD `zexed1` E-03)
# --------------------------------------------------------------------------------------
#
# WHY DIRECTION AT ALL. The three booleans above answer "do the run record and the tree differ", which
# is not the question an operator has. A run record is IMMUTABLE HISTORY: gitignored, box-local state
# whose statuses were TRUE WHEN THE RUN ENDED. When reality legitimately moves on - a lane that was
# `integration-blocked` at 11:47Z gets integrated at 14:00Z - the booleans report the CORRECT new state
# as a defect, in red. Measured on the live corpus at review: 508 rows in that table, of which
# `('reviewed','executed','executed')` was 172 and `('queued','executed','executed')` 153, both
# legitimate post-run progress. A warning that is mostly false is already being ignored, so its true
# positives are already lost.
#
# THE ONE WAY TO GET THIS WRONG IS TO CLASSIFY ON DIRECTION ALONE, and a previous design was abandoned
# for exactly that on a recorded maintainer ruling (2026-09-05). This audit reads only a parent
# directory name and one `- Status:` line, so A LEGITIMATE FINALIZE AND A HAND-EDITED
# `- Status: executed` PLUS `git mv` ARE BYTE-IDENTICAL TO IT. Inferring "resolved" from direction
# would print a reassuring verdict for precisely the bypass `hooks/executed_transition_gate` exists to
# catch. So `CLASS_RESOLVED` requires BOTH direction AND read git evidence, and everything unprovable
# is a VISIBLE `CLASS_UNKNOWN`, never a quiet pass.

#: Forward: the run had not finished with this artifact, and it has since reached `executed/` with a
#: `lifecycle(<id6>): finalize` commit inside the after-the-run range. The ONLY class that asserts a
#: difference is benign, and the only one that requires evidence.
CLASS_RESOLVED = "resolved"

#: Forward into a RETIREMENT directory (`superseded/`/`not-executed/`), evidenced by the artifact's own
#: `RETIRED` banner plus its `- Status:` agreeing with its directory.
CLASS_RETIRED = "retired"

#: Backwards: the run recorded a SUCCESS but the artifact is in neither `executed/` nor a retirement
#: directory. Evidence the finalize did not stick. This is what the red styling is FOR.
CLASS_REGRESSED = "regressed"

#: No artifact could be found at all (or an id6 collision made the lookup refuse to pick).
CLASS_MISSING = "missing"

#: The run record and the tree agree. A POSITIVE finding.
CLASS_UNCHANGED = "unchanged"

#: A difference this audit CANNOT PROVE either way. A CONFESSION, not a finding, and deliberately
#: never collapsible into `CLASS_UNCHANGED` and never suppressible: an invisible confession is
#: indistinguishable from a clean pass to every reader, which is the whole point of the 2026-09-05
#: ruling.
CLASS_UNKNOWN = "unknown"

#: Every class, in report order.
ALL_CLASSES: Tuple[str, ...] = (
    CLASS_REGRESSED,
    CLASS_MISSING,
    CLASS_UNKNOWN,
    CLASS_RESOLVED,
    CLASS_RETIRED,
    CLASS_UNCHANGED,
)

#: The classes that mean SOMETHING IS ACTUALLY WRONG. Reserved for the alarming styling, and NO code
#: path may hide a row in one of these.
ALARMING_CLASSES: frozenset = frozenset({CLASS_REGRESSED, CLASS_MISSING})

#: The classes a consumer may suppress BY DEFAULT (counts still reported). Both HAVE evidence behind
#: them. `CLASS_UNKNOWN` is deliberately absent (OQ-01).
SUPPRESSIBLE_CLASSES: frozenset = frozenset({CLASS_RESOLVED, CLASS_RETIRED})

# The `CLASS_UNKNOWN` reasons, each a DISTINCT OPERATOR SITUATION. A bare `unknown` teaches nothing,
# and collapsing two of these would assert a search that never ran.
UNKNOWN_NO_EVIDENCE = "no lifecycle finalize commit in the after-the-run range"
UNKNOWN_NO_ENDING_HEAD = (
    "the run record carries no ending_head, so the range cannot be formed"
)
UNKNOWN_HEAD_UNREACHABLE = "the run record's ending_head is not in this repository's history, so the range cannot be formed"
UNKNOWN_GIT_UNAVAILABLE = (
    "git history could not be read (not a repository, git absent, or it failed)"
)
UNKNOWN_UNATTRIBUTABLE = "the artifact found could not be attributed to this step's id6"
UNKNOWN_NO_DIRECTION = (
    "the difference has no lifecycle direction (status disagreement in place)"
)
UNKNOWN_NOT_CLASSIFIED = (
    "no evidence index was supplied, so direction could not be evidenced"
)
UNKNOWN_TRACKED_ONLY = (
    "a tracked-only sweep cannot see a run record, so direction is unknowable"
)


# --------------------------------------------------------------------------------------
# The READ, TIME-BOUND git evidence for a forward lifecycle move (IPD `zexed1` E-02)
# --------------------------------------------------------------------------------------


@dataclass
class FinalizeEvidenceIndex:
    """One git pass worth of `lifecycle(<id6>): finalize` facts, answering every row in Python.

    ONE PASS, NOT ONE PER ROW, and that is a usability requirement rather than an optimization.
    Measured at review on the live repository (2885 commits): a full `git log --format=%s` pass is
    ~46ms and a single `--grep` ~50ms, so per-row spawning across the measured 508 rows costs roughly
    25 SECONDS for a read-only view an operator runs interactively. Re-measured in this lane (3094
    commits): the combined `%H %P %s` pass this class uses is 42ms for the WHOLE table.

    * ``available``   - False when git could not be read at all. Every row then classifies
                        `CLASS_UNKNOWN` with :data:`UNKNOWN_GIT_UNAVAILABLE`; never a quiet pass.
    * ``unavailable_detail`` - what went wrong, for the row's reason text.
    * ``finalize_commits``   - id6 -> every commit whose SUBJECT is that plan's finalize subject.
                        A LIST, never a first match: `--grep` matches the message BODY, and the manual
                        merge commits in this repository QUOTE the gate's demand in their bodies, so a
                        body grep matches them and a `head -1` hides the real finalize commit
                        underneath. This index matches on the SUBJECT only, exactly as
                        `hooks/executed_transition_gate._intree_finalize_evidence_ok` does.
    * ``parents``     - commit -> its parents, so the ancestry needed for the TIME BOUND is computed
                        in Python instead of spawning `git merge-base --is-ancestor` per row.
    * ``head_reachable`` - every commit reachable from HEAD at index time.
    """

    available: bool = False
    unavailable_detail: str = ""
    finalize_commits: Dict[str, List[str]] = field(default_factory=dict)
    parents: Dict[str, List[str]] = field(default_factory=dict)
    head_reachable: Set[str] = field(default_factory=set)
    _ancestor_cache: Dict[str, Set[str]] = field(default_factory=dict, repr=False)

    def _ancestors_of(self, commit: str) -> Set[str]:
        """``commit`` plus everything reachable FROM it, memoized per distinct commit.

        Memoized because rows SHARE an ``ending_head``: a run's attempts write the same head for every
        item it dispatched, so the number of distinct heads in a table is far smaller than the number
        of rows, and this walk therefore runs a handful of times rather than 508.
        """
        cached = self._ancestor_cache.get(commit)
        if cached is not None:
            return cached
        seen: Set[str] = set()
        stack = [commit]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(self.parents.get(cur, ()))
        self._ancestor_cache[commit] = seen
        return seen

    def finalize_after(self, id6: str, ending_head: str) -> Tuple[Optional[str], str]:
        """Is there a finalize commit for ``id6`` AFTER ``ending_head``? Returns (commit, reason).

        THE RANGE IS ``<ending_head>..HEAD``, MIRRORING THE HOOK'S ``HEAD..<incoming>``, and the bound
        is mandatory rather than a refinement. "Is a finalize commit reachable from HEAD" is the WRONG
        QUESTION and the gate's own suite says so: `test_finalize_commit_already_on_head_is_not_evidence`
        (`tests/test_executed_transition_gate.py`) exists because AN OLD FINALIZE MUST NOT AUTHORIZE A
        NEW TRANSITION. An unbounded check would accept a plan that was finalized long ago, later
        hand-reverted to `pending/`, and then hand-re-`git mv`d into `executed/` - its old finalize
        commit is still reachable, so the viewer would call that bypass `resolved`.

        Every unprovable case returns ``(None, <reason>)`` and NEVER falls back to the weaker
        unbounded check.
        """
        if not self.available:
            return None, self.unavailable_detail or UNKNOWN_GIT_UNAVAILABLE
        if not ending_head:
            return None, UNKNOWN_NO_ENDING_HEAD
        if ending_head not in self.head_reachable:
            # A recorded head this repository cannot see (a squashed or discarded lane, a shallow
            # clone). The range genuinely cannot be formed, which is a DIFFERENT operator situation
            # from "the range was searched and held no finalize", so it gets its own reason.
            return None, UNKNOWN_HEAD_UNREACHABLE
        before = self._ancestors_of(ending_head)
        for commit in self.finalize_commits.get(
            id6, ()
        ):  # SUBJECT matches, in history order
            if commit in self.head_reachable and commit not in before:
                return commit, ""
        return None, UNKNOWN_NO_EVIDENCE


#: How long the ONE history read may take. Small on purpose: this is a read-only viewer an operator
#: runs interactively, and `runner_shared._run_git` passes no timeout of its own, so a wedged git
#: would otherwise hang the view forever. A timeout is an `unknown`, never a pass.
GIT_READ_TIMEOUT_SECONDS: float = 20.0

#: The record separator inside one `git log` line. `\x1f` (ASCII US) cannot occur in a commit subject
#: written by any `aw` verb and is not special to git's pretty formats.
_LOG_SEP = "\x1f"

_FINALIZE_SUBJECT_RE = re.compile(
    r"\A"
    + re.escape(_core.LIFECYCLE_SUBJECT_KEYWORD)
    + r"\((?P<id6>[^)]+)\):\s*finalize\b"
)


def build_finalize_evidence_index(repo_root: Path) -> FinalizeEvidenceIndex:
    """ONE read-only git pass collecting every finalize commit and the parent graph.

    THIS IS THE AUDIT'S FIRST AND ONLY GIT DEPENDENCY, so every failure mode is handled and every one
    of them resolves to an `unknown`: not a git repository, `git` absent from PATH, a shallow clone, a
    detached HEAD, a nonzero exit, a timeout. There is deliberately no path on which an unreadable
    history produces a reassuring verdict.

    Reuses ``runner_shared._run_git`` rather than adding a fourth same-named variant (that module's own
    comment documents three genuinely different `_run_git` functions and says not to unify them), and
    imports it LAZILY so this module stays cheap for the tracked-only doctor consumer, which needs no
    git at all.
    """
    idx = FinalizeEvidenceIndex()
    try:
        from agent_workflows.runner_shared import _run_git
    except Exception as exc:  # pragma: no cover - import-time environment failure
        idx.unavailable_detail = f"{UNKNOWN_GIT_UNAVAILABLE} ({type(exc).__name__})"
        return idx

    root = Path(repo_root)
    try:
        rc, out, err = _run_git(
            root,
            [
                "log",
                f"--format=%H{_LOG_SEP}%P{_LOG_SEP}%s",
                "--all",
                "--no-color",
            ],
            timeout=GIT_READ_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        # FileNotFoundError (git absent), TimeoutExpired, NotADirectoryError, any OSError.
        idx.unavailable_detail = f"{UNKNOWN_GIT_UNAVAILABLE}: {type(exc).__name__}"
        return idx
    if rc != 0:
        detail = (err or "").strip().splitlines()
        idx.unavailable_detail = f"{UNKNOWN_GIT_UNAVAILABLE}: git exited {rc}" + (
            f" ({detail[0][:120]})" if detail else ""
        )
        return idx

    for line in out.splitlines():
        parts = line.split(_LOG_SEP)
        if len(parts) != 3:
            continue
        sha, parents_raw, subject = parts
        sha = sha.strip()
        if not sha:
            continue
        idx.parents[sha] = [p for p in parents_raw.split() if p]
        m = _FINALIZE_SUBJECT_RE.match(subject.strip())
        if m:
            idx.finalize_commits.setdefault(m.group("id6"), []).append(sha)

    # HEAD's reachable set, from the SAME pass's parent graph rather than a second subprocess. A
    # detached HEAD resolves like any other commit; a HEAD that does not resolve (an empty repository)
    # leaves the set empty, so every row is `unknown` rather than silently evidenced.
    try:
        rc_head, head_out, _e = _run_git(
            root, ["rev-parse", "HEAD"], timeout=GIT_READ_TIMEOUT_SECONDS
        )
    except Exception as exc:
        idx.unavailable_detail = f"{UNKNOWN_GIT_UNAVAILABLE}: {type(exc).__name__}"
        return idx
    if rc_head != 0 or not head_out.strip():
        idx.unavailable_detail = f"{UNKNOWN_GIT_UNAVAILABLE}: HEAD did not resolve"
        return idx
    head = head_out.strip()
    idx.available = True
    idx.head_reachable = idx._ancestors_of(head)
    return idx


@dataclass
class ArtifactLookup:
    """The result of locating one artifact, carrying the COLLISION verdict rather than hiding it.

    * ``path``       - the resolved file, or None when nothing matched.
    * ``collisions`` - every path a UNIQUE-by-contract match landed on when there was more than one.
                       Non-empty means the repository has a data bug (one id6 declared by several
                       records); ``path`` is then None, because picking one arbitrarily is exactly
                       the silent behavior this module was extracted to remove.
    * ``kind``       - how it was found: ``id6`` (exact declared ``- Id:``), ``filename-id6`` (the
                       clustered grammar's id6 field), ``configured`` (a caller-supplied path that
                       exists), or None.
    """

    path: Optional[Path] = None
    collisions: List[Path] = None  # type: ignore[assignment]
    kind: Optional[str] = None

    def __post_init__(self) -> None:
        if self.collisions is None:
            self.collisions = []

    @property
    def is_collision(self) -> bool:
        return len(self.collisions) > 1


@dataclass
class ArtifactAudit:
    """One artifact's location/status verdict.

    Field names and semantics are those of the ``StepArtifactAudit`` this replaces, so the run
    viewer's three call sites render byte-identically. ``is_live`` is carried THROUGH from the
    caller and is never derived here (see the module docstring).
    """

    id6: str
    stem: str
    run_status: str
    missing_entirely: bool = False
    location_mismatch: bool = False
    status_mismatch: bool = False
    actual_dir: Optional[str] = None
    expected_dir: Optional[str] = None
    file_status: Optional[str] = None
    actual_path: Optional[Path] = None
    is_live: bool = False
    collisions: List[Path] = None  # type: ignore[assignment]
    # THE DIRECTIONAL CLASS IS ADDED BESIDE THE THREE BOOLEANS, NEVER INSTEAD OF THEM (IPD `zexed1`
    # E-03, review PR-204). `aw runs --json` and `aw runs --agent` `asdict()` this dataclass straight
    # into PUBLISHED records, and `docs/cli-agent-protocol.md`'s stability rule makes an added optional
    # field backward compatible while REMOVING `missing_entirely`/`location_mismatch`/`status_mismatch`
    # would be a breaking change requiring an `aw.agent/v2` bump. So the booleans stay populated
    # exactly as before and a consumer pinned to them keeps working unchanged.
    #
    # Defaults to `CLASS_UNKNOWN` with a reason saying WHY, so an audit built by a caller that supplies
    # no evidence index (the tracked-only doctor route, or any older construction site) can never read
    # as a reassuring `CLASS_UNCHANGED` it did not earn.
    difference_class: str = CLASS_UNKNOWN
    class_reason: str = UNKNOWN_NOT_CLASSIFIED
    #: The `lifecycle(<id6>): finalize` commit that evidenced `CLASS_RESOLVED`, when there is one.
    evidence_commit: Optional[str] = None
    #: The run attempt's `ending_head`, i.e. the time bound this row's evidence was searched against.
    evidence_range_from: Optional[str] = None

    def __post_init__(self) -> None:
        if self.collisions is None:
            self.collisions = []

    @property
    def has_discrepancy(self) -> bool:
        """True when this audit found ANY drift worth reporting.

        DELIBERATELY UNCHANGED by the directional classification: this is the predicate the published
        `--json`/`--agent` records and the human table have always selected rows with, so narrowing it
        would change WHICH rows a machine consumer receives. What changed is how a selected row is
        CLASSIFIED and STYLED, not whether it appears (IPD `zexed1` E-05).
        """
        return bool(
            self.missing_entirely or self.location_mismatch or self.status_mismatch
        )

    @property
    def is_alarming(self) -> bool:
        """True when this row means SOMETHING IS ACTUALLY WRONG, i.e. earns the red styling."""
        return self.has_discrepancy and self.difference_class in ALARMING_CLASSES


def expected_dir_for_status(status: str) -> str:
    """The directory a record with this recorded ``status`` is expected to sit in.

    Terminal and standing statuses expect their own directory; everything else (draft, to-review,
    reviewed, approved, queued, running, blocked, ...) expects ``pending/``. THE PRE-TERMINAL FALLBACK
    IS WHY A CONSUMER MUST BE LIVENESS-AWARE: a running step's plan is legitimately in ``pending/``
    while its recorded status is ``running``, so the expectation holds only because ``pending/`` is
    the catch-all.
    """
    from agent_workflows.runner_shared import canonical_terminal_status

    st = canonical_terminal_status(status)
    return _TERMINAL_EXPECTED_DIR.get(st, "pending")


def run_status_is_nonterminal(status: str) -> bool:
    """Did the run record's ``status`` mean THIS RUN WAS NOT DONE WITH THIS ARTIFACT?

    DERIVED, NOT ENUMERATED, and that is the correction that makes this plan work at all (IPD `zexed1`
    E-03, review PR-201). The forward direction is defined as "the recorded status expected the
    artifact in `pending/`", read straight off :func:`expected_dir_for_status`, rather than as a
    hand-written list of statuses.

    WHY THE ENUMERATED FORM FAILS. Measured at review, the live table carried 508 rows; the
    `integration-blocked` shape the item was filed about was 4 of them, while
    `('reviewed','executed','executed')` was 172 and `('queued','executed','executed')` 153. Both of
    those dominant shapes are the SAME false alarm arriving by a different route: `initialize_run`
    DERIVES a queue entry's status as `reviewed` for anything not `to-review`/`draft`/`approved`/
    `auto-approved`, and `queued` simply means the run never dispatched the item, so a plan that
    executed in a LATER run reads as a discrepancy forever. An enumeration of the three statuses the
    item mentioned would have left 325+ of those rows exactly as red as they are today, i.e. the fix
    would not have achieved its own goal.
    WHY THE DERIVATION CATCHES THEM FOR FREE: neither `reviewed` nor `queued` is in
    ``_TERMINAL_EXPECTED_DIR``, so both map to `pending` and are forward-eligible without being named.

    `tests/test_artifact_audit.py` pins this against BOTH host drivers' `TERMINAL_STATES`, in the style
    of `runner_shutdown.KNOWN_ITEM_STATUSES`, so a driver adding a status cannot drift silently.
    """
    return expected_dir_for_status(status) == "pending"


def _disposition_dir(path: Path) -> str:
    """The DISPOSITION directory a record sits in, climbing a monthly shard (`executed/202608/`)."""
    parent = path.parent.name
    if re.fullmatch(r"\d{6}", parent):
        return path.parent.parent.name
    return parent


def _has_retired_banner(path: Path) -> bool:
    """Does this record carry a `RETIRED` banner near the top?

    The banner is the retirement's OWN evidence, and it is what makes `CLASS_RETIRED` an evidenced
    class rather than an inference (see :func:`classify_difference`). Read from a bounded header, in
    the several shapes the corpus actually uses: bare, HTML-commented, blockquoted, or bolded.
    Measured on this repository: 36 of 40 records in `superseded/`/`not-executed/` carry it within the
    first 4096 bytes (the four that do not are the two trees' `README.md` files, which are not
    records, and two plans retired without a banner).
    """
    try:
        with open(path, "rb") as fh:
            header = fh.read(4096).decode("utf-8", errors="ignore")
    except OSError:
        return False
    return bool(_RETIRED_BANNER_RE.search(header))


#: The `RETIRED` banner, in the shapes the live corpus uses (bare, `<!-- -->`, `>`, `**`).
_RETIRED_BANNER_RE = re.compile(r"(?m)^[ \t]*(?:<!--[ \t]*)?(?:>[ \t]*)?\**RETIRED\b")


def classify_difference(
    audit: "ArtifactAudit",
    *,
    evidence: Optional[FinalizeEvidenceIndex] = None,
    ending_head: str = "",
) -> Tuple[str, str, Optional[str]]:
    """Classify one audit BY DIRECTION, on READ evidence. Returns (class, reason, evidence_commit).

    `CLASS_RESOLVED` REQUIRES EVIDENCE, NOT DIRECTION, and this is the entire reason the previous
    attempt at this feature was abandoned on a maintainer ruling (2026-09-05). A row earns `resolved`
    only when BOTH the lifecycle direction is forward AND a `lifecycle(<id6>): finalize` commit is found
    inside the ``ending_head..HEAD`` range. DIRECTION ALONE YIELDS `CLASS_UNKNOWN`, because a legitimate
    finalize and a hand-edited `- Status: executed` plus `git mv` are BYTE-IDENTICAL to this audit
    (it reads a parent directory name and one `- Status:` line, nothing else), so treating direction as
    proof would print a reassuring verdict for exactly the bypass
    `hooks/executed_transition_gate` exists to catch. DO NOT "simplify" the evidence check away.

    `CLASS_RETIRED` IS EVIDENCED DIFFERENTLY ON PURPOSE, and demanding a finalize commit for it would be
    wrong rather than merely strict: RETIREMENT WRITES NO FINALIZE COMMIT. Measured at review, history
    carried 190 `lifecycle(ID): finalize` subjects against exactly ONE `lifecycle(ID): retire`, while 82
    of the 508 rows had their artifact in `superseded/` (74) or `not-executed/` (8). Under a
    finalize-only evidence rule every legitimate retirement would be permanently `unknown`, and under
    the item's original `regressed` rule the six that recorded `complete` would render RED forever. Its
    evidence is instead the artifact's own `RETIRED` banner plus its `- Status:` agreeing with its
    directory.
    """
    if audit.missing_entirely:
        # Includes the id6-COLLISION case, where the lookup refused to pick between several files.
        # Either way there is no artifact to reason about, and a run pointing at nothing is a real
        # finding rather than an unprovable one.
        detail = (
            f"{len(audit.collisions)} records claim this id6"
            if audit.collisions
            else "no artifact found for this step"
        )
        return CLASS_MISSING, detail, None
    if not audit.has_discrepancy:
        return CLASS_UNCHANGED, "the run record and the artifact agree", None

    # THE DISPOSITION, NOT THE LITERAL PARENT. `audit.actual_dir` is the parent directory NAME, which
    # for an archived plan is its monthly shard (`executed/202608/` -> `202608`); the pre-existing
    # `location_mismatch` compares that raw name and therefore already flags an archived plan. The
    # CLASSIFICATION must not repeat that: a plan archived under `executed/202608/` reached `executed`,
    # so it is classified against the disposition it actually sits in.
    actual = (
        _disposition_dir(Path(audit.actual_path))
        if audit.actual_path is not None
        else (audit.actual_dir or "")
    )
    forward = run_status_is_nonterminal(audit.run_status)

    # UNATTRIBUTABLE ROWS ARE NEVER `regressed` (review PR-202/F-6e). `find_artifact`'s filename tier
    # resolves an id6 that appears in the grammar's id6 FIELD, but a caller may still hand this audit a
    # stem-resolved file, and one live row is a measured mis-resolution (step `nna8yz` resolving to plan
    # `3i0aaz`, whose SLUG contains `nna8yz`). Calling that `regressed` would make a lookup defect look
    # like lost work, and under the narrowed rule below it would be the ONLY red row. `6ltz1y` E-03
    # owns the resolver fix; this refuses to slander the row in the meantime.
    if audit.id6 and audit.actual_path is not None:
        found_id6 = _filename_id6(Path(audit.actual_path).name)
        if found_id6 and found_id6 != audit.id6:
            return CLASS_UNKNOWN, UNKNOWN_UNATTRIBUTABLE, None

    if actual in _RETIREMENT_DIRS:
        # A retirement carries its OWN evidence, so it is checked BEFORE the direction gate and does not
        # require a forward run status. THIS IS THE SIX-ROW CASE PR-205 MEASURED: those rows recorded a
        # run status of `complete` against a `superseded/` artifact, which is not forward at all, yet
        # every one was a legitimate banner-carrying retirement. Requiring forwardness here would leave
        # them permanently red (under the item's original `regressed` rule) or permanently `unknown`,
        # which is what this branch's placement prevents. Verified on the fixture corpus: with the
        # direction gate in front of this test, a `('complete','superseded','superseded')` row fell all
        # the way through to `unknown` with a "no lifecycle direction" reason.
        declared = audit.file_status or ""
        banner = audit.actual_path is not None and _has_retired_banner(
            Path(audit.actual_path)
        )
        if banner and declared == actual:
            return (
                CLASS_RETIRED,
                f"retired into {actual}/ with a RETIRED banner and an agreeing - Status:",
                None,
            )
        # A retirement directory WITHOUT that evidence is not something this audit can vouch for.
        missing_bits = []
        if not banner:
            missing_bits.append("no RETIRED banner")
        if declared != actual:
            missing_bits.append(
                f"- Status: {declared or '(none)'} does not match {actual}/"
            )
        return (
            CLASS_UNKNOWN,
            f"in {actual}/ but the retirement is unevidenced ({'; '.join(missing_bits)})",
            None,
        )

    if forward and actual == "executed":
        # THE ONE CLASS THAT NEEDS READ GIT EVIDENCE, TIME-BOUND to after this run ended.
        if evidence is None:
            return CLASS_UNKNOWN, UNKNOWN_NOT_CLASSIFIED, None
        commit, why = evidence.finalize_after(audit.id6, ending_head)
        if commit:
            return (
                CLASS_RESOLVED,
                f"finalized after the run ended (commit {commit[:12]})",
                commit,
            )
        return CLASS_UNKNOWN, why, None

    if audit.run_status in _RUN_SUCCESS_STATUSES and actual not in (
        "executed",
        *_RETIREMENT_DIRS,
    ):
        # BACKWARDS: the run recorded a SUCCESS and the artifact is in neither `executed/` nor a
        # retirement directory. Evidence the finalize did not stick, which is what the red is FOR.
        # NARROWER THAN THE ITEM'S RULE deliberately: a retirement is excluded above, and an
        # unattributable row was excluded further up.
        return (
            CLASS_REGRESSED,
            f"the run recorded {audit.run_status} but the artifact is in {actual or '(nowhere)'}/",
            None,
        )

    if forward and actual == "reusable":
        # `reusable/` is a STANDING disposition, not an execution outcome, and no lifecycle commit
        # marks entry into it. Unprovable rather than wrong.
        return CLASS_UNKNOWN, f"in the standing {actual}/ disposition", None

    # Everything else is a difference with no lifecycle DIRECTION to read: most often a `- Status:`
    # disagreement inside the SAME directory, where nothing moved at all.
    return CLASS_UNKNOWN, UNKNOWN_NO_DIRECTION, None


def _filename_id6(name: str) -> Optional[str]:
    """The id6 field of a clustered artifact filename, or None when the name does not parse.

    Deliberately NOT a substring test. A bare substring would also match a review record, which
    carries its SUBJECT's id6 in its filename by convention; parsing the grammar's id6 FIELD cannot.
    """
    m = _naming.parse_clustered(name)
    if not m:
        return None
    try:
        return m.groupdict().get("id6")
    except (AttributeError, IndexError):
        return None


@dataclass
class ArtifactIndex:
    """One traversal's worth of lookup facts: every record path, and the id6 maps built from them.

    * ``paths``           - every record file found, in type-precedence order.
    * ``by_declared_id``  - id6 -> paths whose front matter DECLARES that ``- Id:`` (exact).
    * ``by_filename_id``  - id6 -> paths whose CLUSTERED FILENAME carries that id6 field.

    A map value with more than one path is a COLLISION, which the caller reports rather than
    resolving arbitrarily.
    """

    paths: List[Path]
    by_declared_id: dict
    by_filename_id: dict


# ONE TRAVERSAL PER (root, type-vocabulary), MEMOIZED, because the run viewer audits EVERY step of
# EVERY displayed run and the enumeration is what costs. Measured on this repository: a full
# multi-type walk is ~560ms (of which the `other` catch-all alone is ~330ms for 4 files, since it
# sweeps the whole records tree to find what no type owns), so a per-step walk made
# `tests/test_run_viewer.py` go from 2.4s to 35s. With this cache it is 2.5s.
#
# THE CACHE IS KEYED ON THE RESOLVED ROOT PLUS THE TYPE VOCABULARY AND IS INVALIDATED BY MTIME of
# every record directory in scope, so a test (or a finalize) that MOVES an artifact and re-audits
# sees the move. Directory mtime changes when an entry is added, removed or renamed within it, which
# is exactly the class of change that relocates an artifact; an in-place EDIT of a file's `- Status:`
# does not change its directory's mtime, which is why only the PATH facts are cached here and the
# status is always read fresh in `audit_artifact`.
_INDEX_CACHE: dict = {}
_INDEX_CACHE_MAX = 8


def _dir_signature(repo_root: Path, record_types: Sequence[str]) -> tuple:
    """A cheap invalidation signature: the mtime of every record directory in scope.

    Walks the LITERAL layout (``.aw/records/<type>`` plus legacy ``.agents/<type>``) rather than
    calling ``selectors.record_dirs`` per type. That is deliberate and measured: ``record_dirs``
    consults the project/registry backend on every call (~1.6ms each, ~16ms per signature across the
    vocabulary), which would cost more than the traversal this cache exists to avoid. The signature
    only has to CHANGE when an artifact moves, so covering the literal trees is sufficient; a
    registry-redirected tree simply re-indexes on its own directory mtimes via the same scan below.
    """
    sig: List[tuple] = []
    for base in (repo_root / ".aw" / "records", repo_root / ".agents"):
        for rt in record_types:
            d = base / rt
            try:
                sig.append((str(d), d.stat().st_mtime_ns))
            except OSError:
                continue
            # Disposition subdirectories (and their monthly shards) are where an artifact MOVES to,
            # so their mtimes matter as much as the tree root's.
            try:
                for child in d.iterdir():
                    if child.is_dir():
                        sig.append((str(child), child.stat().st_mtime_ns))
                        for grand in child.iterdir():
                            if grand.is_dir():
                                sig.append((str(grand), grand.stat().st_mtime_ns))
            except OSError:
                continue
    return tuple(sorted(sig))


def build_index(
    repo_root: Path, *, record_types: Sequence[str] = TYPE_PRECEDENCE
) -> ArtifactIndex:
    """Enumerate every record of ``record_types`` ONCE and build both id6 maps.

    Enumeration goes through ``selectors._iter_paths``, so the dual ``.aw/``/``.agents/`` roots, the
    monthly-shard recursion and the traversal exclusions are the resolver's rather than a private
    walk's; the exact ``- Id:`` reading uses ``selectors``' own bounded header reader, so this module
    matches what ``aw find <id6>`` matches.
    """
    repo_root = Path(repo_root)
    try:
        key = (str(repo_root.resolve()), tuple(record_types))
    except OSError:
        key = (str(repo_root), tuple(record_types))
    sig = _dir_signature(repo_root, record_types)
    cached = _INDEX_CACHE.get(key)
    if cached is not None and cached[0] == sig:
        return cached[1]

    paths: List[Path] = []
    by_declared: dict = {}
    by_filename: dict = {}
    seen: set = set()
    for rt in record_types:
        try:
            candidates = list(_sel._iter_paths(repo_root, rt))
        except Exception:
            continue
        for p in candidates:
            k = str(p)
            if k in seen:
                continue
            seen.add(k)
            paths.append(p)
            fid = _filename_id6(p.name)
            if fid:
                by_filename.setdefault(fid, []).append(p)
            header = _sel._read_header(p)
            if header:
                did = _sel._read_id(header)
                if did:
                    by_declared.setdefault(did, []).append(p)

    index = ArtifactIndex(
        paths=paths, by_declared_id=by_declared, by_filename_id=by_filename
    )
    if len(_INDEX_CACHE) >= _INDEX_CACHE_MAX:
        _INDEX_CACHE.clear()
    _INDEX_CACHE[key] = (sig, index)
    return index


def find_artifact(
    repo_root: Path,
    id6: str,
    stem: str = "",
    *,
    record_types: Sequence[str] = TYPE_PRECEDENCE,
) -> ArtifactLookup:
    """Locate the artifact declaring ``id6`` (or named by ``stem``), through ``selectors``.

    TWO TIERS, IN THIS ORDER, and both are needed. TIER ONE asks ``selectors.resolve`` for an EXACT
    declared ``- Id:`` match, restricted to ``MATCH_ID6`` so no other selector kind can win; a
    multi-file result is returned as a COLLISION rather than resolved. TIER TWO falls back to the
    clustered filename's id6 FIELD, because ``selectors`` reads only a bounded 4096-byte header and
    measured on this repository 268 of 1202 records declare their ``- Id:`` below that cap, so an
    exact-only lookup would report those as missing. ``stem`` is matched on the filename as a last
    resort, preserving the extracted behavior for a caller that knows a stem but no id6.

    Never raises for a missing tree or an unreadable file; an absent artifact is a verdict, not an
    error. ``selectors`` is CONSUMED here and never modified.
    """
    repo_root = Path(repo_root)
    if not id6 and not stem:
        return ArtifactLookup()

    index = build_index(repo_root, record_types=record_types)

    # TIER ONE: exact declared `- Id:`. Hits are accumulated ACROSS types, so a cross-type id6
    # collision is reported rather than masked by the type ordering.
    if id6:
        exact = index.by_declared_id.get(id6, ())
        if len(exact) == 1:
            return ArtifactLookup(path=exact[0], kind="id6")
        if len(exact) > 1:
            return ArtifactLookup(
                path=None, collisions=sorted(exact, key=str), kind="id6"
            )

        # TIER TWO: the clustered filename's id6 FIELD (never a bare substring), which the bounded
        # header read makes necessary; see the module docstring's 268-of-1202 measurement.
        by_name = index.by_filename_id.get(id6, ())
        if len(by_name) == 1:
            return ArtifactLookup(path=by_name[0], kind="filename-id6")
        if len(by_name) > 1:
            return ArtifactLookup(
                path=None, collisions=sorted(by_name, key=str), kind="filename-id6"
            )

    # TIER THREE: the stem as a filename substring, the extracted behavior's last resort, kept for a
    # caller that knows a stem but no id6.
    if stem:
        by_stem = [p for p in index.paths if stem in p.name]
        if by_stem:
            return ArtifactLookup(path=sorted(by_stem, key=str)[0], kind="stem")
    return ArtifactLookup()


def read_declared_status(path: Path) -> Optional[str]:
    """The record's own single-token ``- Status:`` value, or None when absent/unreadable.

    A multi-word status yields None, matching the pattern that shipped inside `run_viewer` and
    `selectors._STATUS_RE`'s documented parity constraint.
    """
    try:
        txt = Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    m = _STATUS_LINE_RE.search(txt)
    return m.group(1).strip() if m else None


def _status_disagrees(recorded: str, declared: str) -> bool:
    """Does a record's own ``declared`` status disagree with the ``recorded`` one?

    The tolerance bands are the extracted ones, plus ``interrupted`` (IPD `vdabn5`): an
    executed/complete record must read executed or complete; a ``reviewed`` record may read reviewed
    OR approved; a queued/running/blocked/dependency-blocked/interrupted record may read any
    pre-terminal value, because a plan that has not finished legitimately still carries its authoring
    status; otherwise the two must be equal.

    WHY ``interrupted`` BELONGS IN THE IN-FLIGHT ARM, and read this reason rather than the shorter one
    it replaced. It is NOT that an interrupted item's plan cannot have moved: that claim is FALSE and
    was refuted by measurement (IPD `vdabn5` F-9). ``oc_runipd.reconcile_interrupted``'s spec-R22
    fabricated-success gate DELIBERATELY leaves an item at ``interrupted`` while its plan sits in
    ``executed/`` reading ``- Status: executed``, because for a force-cut turn the driver never
    established that the work completed. That state is produced BY DESIGN and must keep being flagged.

    The correct and sufficient reason is about THIS ARM's breadth: the accepted ``declared`` values
    below are all PRE-TERMINAL and ``executed`` is not among them. So tolerating ``interrupted`` here
    suppresses the row EXACTLY when the plan has not moved, and the R22 moved-plan case keeps flagging
    on both axes (``status_mismatch`` here and ``location_mismatch`` independently, since
    :func:`expected_dir_for_status` maps ``interrupted`` to ``pending``). Do not widen the accepted
    values to admit ``executed``; that would suppress the one row that most needs an operator's eyes.

    EXTENDING THIS LIST IS THE DELIBERATE CHOICE over introducing a classification vocabulary. The
    list is admittedly not a general solution, and a direction-aware classifier would be, which is
    what backlog `1f9m2j` wanted before it proved unsound without evidence this module cannot read
    (it reads a parent directory name and a ``- Status:`` regex, nothing else). Adding one value to a
    list that already encodes exactly this idea is the minimal honest change.

    ONE VALUE WAS ADDED, NOT THE SEVEN SIBLINGS. ``failed``, ``failed-safely``, ``partial``,
    ``not-attempted``, ``merge-conflict``, ``integration-blocked``/``merge-needs-human`` and
    ``cancelled`` all fall through to the final equality with the identical
    ``location_mismatch=False status_mismatch=True`` signature (IPD `vdabn5` F-10). They are excluded
    on purpose: each is a TERMINAL failure state needing its own measured argument about which
    declared values are legitimate for it, and ``integration-blocked`` is backlog `1f9m2j`, BLOCKED.
    ``substantially-complete`` is excluded too, for a different reason: it is NORMALIZED to
    ``complete`` two lines below, so the first arm intercepts it and a status-list entry could not
    express the intent anyway (F-4).
    """
    from agent_workflows.runner_shared import canonical_terminal_status

    rec = canonical_terminal_status(recorded)
    dec = canonical_terminal_status(declared)
    if rec in ("executed", "complete"):
        return dec not in ("executed", "complete")
    if rec == "reviewed":
        return dec not in ("reviewed", "approved")
    if recorded in (
        "queued",
        "running",
        "dependency-blocked",
        "blocked",
        "interrupted",
    ):
        return dec not in (
            "approved",
            "to-review",
            "draft",
            "reviewed",
            "queued",
            "running",
        )
    return dec != rec


def audit_artifact(
    repo_root: Path,
    id6: str,
    stem: str = "",
    *,
    status: str = "",
    configured_file: str = "",
    is_live: bool = False,
    record_types: Sequence[str] = TYPE_PRECEDENCE,
    evidence: Optional[FinalizeEvidenceIndex] = None,
    ending_head: str = "",
) -> ArtifactAudit:
    """THE audit predicate: is the artifact for ``id6`` where ``status`` says it should be?

    Takes PRIMITIVE FACTS rather than a run-viewer ``StepSummary`` (IPD `6ltz1y` OQ-01): a step is a
    run-viewer concept carrying run-specific fields, and a doctor-side consumer has no steps and
    would have to fabricate one. Keeping the signature primitive is what makes the dependency
    one-directional; this module must never import `run_viewer`.

    ``configured_file`` short-circuits the search when the caller already knows the path and it
    exists. ``is_live`` is recorded, never derived, and never suppresses a verdict here: the CONSUMER
    decides what to do with an in-flight artifact, and the run viewer's choice (render it, tagged
    ``[in flight]``) differs from the doctor rule's (do not report it at all).

    ``evidence`` and ``ending_head`` add the DIRECTIONAL CLASSIFICATION (IPD `zexed1`): the caller
    builds the evidence index ONCE for the whole table (:func:`build_finalize_evidence_index`) and
    passes each row's own run-attempt ``ending_head`` as the time bound. Both are OPTIONAL and their
    absence is safe by construction: a caller that omits them gets `CLASS_UNKNOWN` with a reason saying
    so, never a `CLASS_UNCHANGED` or `CLASS_RESOLVED` it did not earn.
    """
    stem = stem or id6
    from agent_workflows.runner_shared import canonical_terminal_status

    recorded = canonical_terminal_status(status)
    expected = expected_dir_for_status(status)

    actual_file: Optional[Path] = None
    collisions: List[Path] = []
    if configured_file and (Path(repo_root) / configured_file).is_file():
        actual_file = Path(repo_root) / configured_file
    else:
        lookup = find_artifact(repo_root, id6, stem, record_types=record_types)
        actual_file = lookup.path
        collisions = list(lookup.collisions)

    if actual_file is None:
        return _classified(
            ArtifactAudit(
                id6=id6,
                stem=stem,
                run_status=recorded,
                missing_entirely=True,
                expected_dir=expected,
                is_live=is_live,
                collisions=collisions,
            ),
            evidence=evidence,
            ending_head=ending_head,
        )

    actual_dir = actual_file.parent.name
    file_status = read_declared_status(actual_file)
    return _classified(
        ArtifactAudit(
            id6=id6,
            stem=stem,
            run_status=recorded,
            missing_entirely=False,
            location_mismatch=actual_dir != expected,
            status_mismatch=bool(
                file_status is not None and _status_disagrees(recorded, file_status)
            ),
            actual_dir=actual_dir,
            expected_dir=expected,
            file_status=file_status,
            actual_path=actual_file,
            is_live=is_live,
            collisions=collisions,
        ),
        evidence=evidence,
        ending_head=ending_head,
    )


def _classified(
    audit: ArtifactAudit,
    *,
    evidence: Optional[FinalizeEvidenceIndex],
    ending_head: str,
) -> ArtifactAudit:
    """Fill ``difference_class``/``class_reason``/``evidence_commit`` on a freshly built audit.

    One place, so no construction site can forget and leave the default `CLASS_UNKNOWN` on a row it
    could have classified.
    """
    cls, reason, commit = classify_difference(
        audit, evidence=evidence, ending_head=ending_head
    )
    audit.difference_class = cls
    audit.class_reason = reason
    audit.evidence_commit = commit
    audit.evidence_range_from = ending_head or None
    return audit


def audit_tracked_artifact(repo_root: Path, path: Path) -> Optional[ArtifactAudit]:
    """The TRACKED-ONLY audit a fail-safe sweeper may run: does a record's OWN declared status agree
    with the directory it sits in?

    THIS IS THE CANNOT-BE-LIVE ROUTE, and the restriction is the whole point (IPD `6ltz1y` E-04
    route (b)). The run-shaped :func:`audit_artifact` compares a RUN's recorded step status against
    the tree, which requires reading ``.aw/records/runs/`` - gitignored, box-local state that
    `doctor.py` reads nowhere. Coupling a tracked-record sweeper to untracked state is the objection
    OQ-03 accepts as decisive against `aw check`, and it applies to `aw doctor` for the same reason:
    the rule would report nothing in a fresh clone or a lane worktree. So the doctor consumer asks
    only what a TRACKED file can answer by itself.

    Returns None (never a finding) in every case where the question cannot be answered safely:

    * the record declares no single-token ``- Status:`` (nothing to compare);
    * the record already sits where its declared status expects it;
    * the record sits in a directory this audit has no expectation about;
    * the record's declared status is PRE-TERMINAL. Such a record may be mid-flight (a running
      execution's plan legitimately carries ``approved`` in ``pending/``), and liveness cannot be
      read from tracked state at all. This is the fail-safe direction
      ``check_engine._receipt_is_live`` establishes: undeterminable means skip.
    * THE RECORD IS STILL IN ``pending/``, even with a terminal declared status. That is the shape of
      a plan CAUGHT MID-FINALIZE - ``ipd_lifecycle.finalize`` writes the status and moves the file,
      and a sweep that runs between the two would report a transaction in progress as drift. It is
      also precisely the direction the shipped ``IPD-M105`` already covers, so skipping it here costs
      no coverage and avoids duplicating a working rule.

    A finding is returned ONLY for the unambiguous, complementary case: a record sitting in a
    TERMINAL directory while its own declared status names a DIFFERENT terminal (or standing)
    disposition. That cannot describe work in progress, because a live execution has not reached a
    terminal status yet and a finalize moves a file only once. THIS IS EXACTLY THE ``IPD-M105`` BLIND
    SPOT, which is what the doctor rule adds rather than duplicates: measured 2026-09-13,
    ``ipd_lint.lint_file`` on a plan in ``executed/`` declaring ``- Status: superseded`` returns
    disposition ``legacy/not evaluated`` with ZERO diagnostics (the whole terminal tree is exempt),
    while the same file in ``pending/`` declaring ``- Status: executed`` does yield ``IPD-M105``.
    """
    path = Path(path)
    declared = read_declared_status(path)
    if not declared:
        return None
    expected = expected_dir_for_status(declared)
    actual_dir = path.parent.name
    # A shard directory (`executed/202608/`) is named for the month, so climb to the disposition.
    if re.fullmatch(r"\d{6}", actual_dir):
        actual_dir = path.parent.parent.name
    if actual_dir == expected:
        return None
    # FAIL SAFE: only a TERMINAL/standing declared status licenses a finding. A pre-terminal record
    # in an unexpected directory may be mid-flight, and liveness cannot be read from tracked state.
    if expected == "pending":
        return None
    # FAIL SAFE: a record still in `pending/` may be mid-finalize, and `IPD-M105` owns that direction.
    if actual_dir == "pending":
        return None
    # Only judge a record that actually lives in a terminal/standing disposition tree.
    if actual_dir not in set(_TERMINAL_EXPECTED_DIR.values()):
        return None
    # THIS ROUTE DELIBERATELY CARRIES NO DIRECTIONAL CLASS (IPD `zexed1`). Direction is a comparison
    # between a RUN RECORD's recorded status and the tree, and this route reads no run record at all
    # (that coupling is exactly what E-04 route (b) refuses). So the class stays the honest
    # `CLASS_UNKNOWN` with a reason naming the limitation, rather than a class computed from a status
    # that is the record's OWN and therefore cannot disagree with itself directionally. `aw doctor`
    # renders these as advisory findings and does not read the class.
    return ArtifactAudit(
        difference_class=CLASS_UNKNOWN,
        class_reason=UNKNOWN_TRACKED_ONLY,
        id6=_filename_id6(path.name) or "",
        stem=path.name,
        run_status=declared,
        missing_entirely=False,
        location_mismatch=True,
        status_mismatch=False,
        actual_dir=actual_dir,
        expected_dir=expected,
        file_status=declared,
        actual_path=path,
        is_live=False,
    )

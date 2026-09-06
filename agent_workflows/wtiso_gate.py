"""The ONE pure gate/predicate library + stable error codes for the wtiso migration (Phase 0,
`8zgybk` E-09; research x03wgn Section 8 Phase 0 item 5 and Section 5 Layer 5).

WHY THIS MODULE EXISTS AS A SKELETON. x03wgn Section 7 records the hazard "Hook rule differs from
driver: agent repairs one gate but fails another" and prescribes ONE pure policy library with stable
error codes, called by the pre-commit hook, the read-only `aw lane status`, the driver, finalize, and
integration. If each of those grew its own copy of a rule, the rules would drift and an agent could
satisfy one gate while violating another. Seeding the import surface in Phase 0 means every later
phase has exactly one place to add a rule, so drift is structurally impossible rather than merely
discouraged.

CURRENT STATE, MEASURED AND PER PREDICATE (`lanectn` child `604wra`, spec `7ckptx` R6.1/R6.2/R6.3).
This module is no longer a pure skeleton: four bodies are real and five still raise. Read this table
before touching anything here, because a stub's `Owner:` line is NOT a to-do assignment you may pick
up (see THE OWNER LABELS ARE STALE below).

  REAL, and each DELEGATES to the single definition rather than restating the rule:
    * `format_missing_input`      -> `lane_containment.format_missing_input_token`     (R3.1)
    * `parse_missing_input`       -> `lane_containment.parse_missing_input_token`      (R3.1)
    * `check_permission_deadline` -> pure over the event stream; the ENFORCING bound is
                                     `lane_containment.TurnBoundWatch`                 (R4.4)
    * `check_scope`               -> `ipd_lifecycle._scope_match`                       (R6.3 body)

  STILL RAISING, with NO owner in flight (`check_lifecycle_role`, `check_hook_bypass`,
  `classify_retention`, `check_receipt`, `check_protected_refs`). Spec R6.2 requires they keep
  raising, and `tests/test_containment_predicates.py` CALLS each one to prove it does. A permissive
  default here would convert a loud gap into a silent hole in a gate.

WIRING IS SEPARATE FROM THE BODY (spec R6.3), and one predicate here proves it. `check_scope` has a
real body and ZERO product callers ON PURPOSE. Its consumers (the pre-commit hook, `aw lane status`,
the driver, finalize, integration) are the wtiso Phase-2 deliverable that was RETIRED unlanded, so
there is no plan in flight to wire it. That is a body waiting for a consumer, NOT an incomplete
implementation; `tests/test_containment_predicates.py` asserts the zero-caller state structurally so
a future wiring is a deliberate, reviewed act. Meanwhile the scope rule that IS enforced today runs
through `ipd_lifecycle.finalize_precheck`, which this body delegates to, so the two cannot disagree.

THE OWNER LABELS ARE STALE, AND THAT IS RECORDED RATHER THAN QUIETLY FIXED. Every `Owner:` line
below named a wtiso phase (`qcqhj7` Phase 1, `rchpms` Phase 2, `2c122z` Phase 5), and ALL THREE were
RETIRED on 2026-09-02: `qcqhj7` superseded by the `lanectn` Set, `rchpms` partly landed then retired,
`2c122z` retired unlanded. So no named owner is coming. Each label now states which `lanectn` child
superseded it, or says plainly that its owner is retired and the predicate has NO successor plan, so
a reader is never sent to a plan that will never run. An unowned predicate is a gap to re-propose on
merit, not work to absorb silently.

STABLE ERROR CODES are the contract. They are the strings a hook prints, `aw lane status` reports,
and the driver matches on. They must not be renamed once a phase depends on one; add a new code
instead. Each is `AW_`-prefixed and uppercase so it is greppable in logs and diffs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only, no runtime import cost
    from pathlib import Path
    from typing import Any, Mapping, Sequence

# ---- stable error codes ---------------------------------------------------------------------------
# Format contract: an emitted violation is rendered as `<CODE>:<subject>:<why>`, matching the
# `AW_MISSING_INPUT:<path>:<why>` shape research x03wgn Section 4 specifies. Callers parse the code
# by exact string match; never by prefix or substring of a longer code.

#: A write touched a path outside the lane's declared scope (Scope-Paths / lease).
AW_GATE_SCOPE = "AW_GATE_SCOPE"

#: A worker attempted a driver-only lifecycle verb (begin/finalize/receipt/ledger write).
AW_LIFECYCLE_ROLE = "AW_LIFECYCLE_ROLE"

#: A required local input is absent from the lane. Emitted as `AW_MISSING_INPUT:<path>:<why>`;
#: the driver classifies it, materializes a safe copy if policy allows, and resumes. The original
#: checkout path is never granted (x03wgn Section 4, "Missing-input recovery").
AW_MISSING_INPUT = "AW_MISSING_INPUT"

#: A commit reached the tree without the hook's checks (for example `git commit --no-verify`).
#: Hooks are feedback only; the driver re-checks the same predicate over observable state.
AW_GATE_HOOK_BYPASS = "AW_GATE_HOOK_BYPASS"

#: A protected ref, git configuration, hook path, or another worktree's administration was mutated.
AW_GATE_PROTECTED_REF = "AW_GATE_PROTECTED_REF"

#: A permission ask (root or nested child session) went unanswered past its deadline.
AW_PERMISSION_DEADLINE = "AW_PERMISSION_DEADLINE"

#: A changed or created artifact could not be placed in exactly one retention class. `unknown`
#: retention blocks teardown (x03wgn Section 2 retention table).
AW_RETENTION_UNKNOWN = "AW_RETENTION_UNKNOWN"

#: A begin receipt is absent, forked, stale, or bound to a different attempt than the one running.
AW_RECEIPT_INVALID = "AW_RECEIPT_INVALID"

#: The tuple of every stable code this library defines, for exhaustive tests and docs.
ERROR_CODES: tuple[str, ...] = (
    AW_GATE_SCOPE,
    AW_LIFECYCLE_ROLE,
    AW_MISSING_INPUT,
    AW_GATE_HOOK_BYPASS,
    AW_GATE_PROTECTED_REF,
    AW_PERMISSION_DEADLINE,
    AW_RETENTION_UNKNOWN,
    AW_RECEIPT_INVALID,
)


# ---- predicate surface (bodies owned by later phases) ---------------------------------------------


def _unimplemented(predicate: str, owner: str) -> "NotImplementedError":
    """Build the uniform NotImplementedError an UNIMPLEMENTED predicate raises (spec R6.2).

    Failing loudly (rather than returning a permissive default) is the point: a caller wired up
    before a body exists must break visibly, never silently allow. A gate that returns "no
    violations" because its rule is missing is worse than no gate, because it reports success.

    THE MESSAGE NAMES THE OWNER AND ITS DISPOSITION, both required (spec R6.2 requires the owner;
    `604wra` added the disposition). Every original owner phase here is RETIRED, so a message naming
    only the phase would send a reader to a plan that will never run. `owner` therefore carries the
    phase AND its state, e.g. "`rchpms` (Phase 2, RETIRED 2026-09-02; no successor plan)".
    """

    return NotImplementedError(
        "wtiso_gate.{0} has no rule body; its owner is {1}. It raises rather than returning a "
        "permissive default (spec 7ckptx R6.2), so a caller wired up before a body exists fails "
        "loudly instead of silently allowing. Do not soften this to a default: implement the body "
        "under a plan that owns it.".format(predicate, owner)
    )


def check_scope(
    changed_paths: "Sequence[str]", scope_paths: "Sequence[str]"
) -> "list[str]":
    """Return `AW_GATE_SCOPE` violations for changed paths outside `scope_paths`.

    BODY IMPLEMENTED, CALLERS DELIBERATELY ABSENT - the spec R6.3 split, and the one predicate here
    that demonstrates it. Body implemented by `lanectn` child `604wra`; WIRING is NOT its work. The
    original labels read "`qcqhj7` (Phase 1) for the pure predicate; `rchpms` (Phase 2) wires the
    hook, `aw lane status`, the driver, and finalize", and BOTH those phases were RETIRED on
    2026-09-02, so no plan is in flight to wire this. Its zero-caller state is therefore CORRECT, and
    `tests/test_containment_predicates.py` asserts it structurally so a future wiring must be a
    deliberate, reviewed act rather than a drive-by import.

    THE MATCHING RULE IS NOT RESTATED HERE. `ipd_lifecycle._scope_match` owns the Scope-Paths grammar
    (literal file, bare or trailing-slash directory, `dir/**`, and fnmatch globs), and this calls it.
    That call is the entire point of the predicate under R6.1: the scope rule is ALREADY enforced
    today through `ipd_lifecycle.finalize_precheck`, so a second matcher here would be a fork that
    lets an agent satisfy this gate while failing finalize - the precise hazard x03wgn Section 7
    names. If the grammar changes, both surfaces change together because there is only one.

    NOT THE SAME QUESTION AS FINALIZE'S AUDIT, and the difference matters to a future wirer. This is
    a PURE set-difference over paths a caller already collected. `finalize_precheck` additionally
    applies the implicit lifecycle allowances (the plan's own file, the index refresh) and attributes
    working-tree changes BY OWNERSHIP, so it correctly disregards a concurrent agent's dirty path in a
    shared checkout. So this predicate is the stricter, context-free half; a caller that needs those
    allowances must use the lifecycle surface, and a hook wired to this one would need to supply them.
    Stated because a wirer who assumed equivalence would produce false violations.

    Returns one `AW_GATE_SCOPE` per offending path, in first-appearance order, so a caller can report
    which paths offended rather than only that some did. An EMPTY `scope_paths` yields NO violations,
    matching the lifecycle's `grandfathered` case: a plan that declared no scope is unfenced, and
    inventing violations for it would flag every legacy plan.
    """

    from agent_workflows import ipd_lifecycle

    patterns = [p for p in (scope_paths or ()) if str(p).strip()]
    if not patterns:
        return []
    violations: "list[str]" = []
    for path in changed_paths or ():
        text = str(path).strip()
        if not text:
            continue
        if not any(ipd_lifecycle._scope_match(text, pat) for pat in patterns):
            violations.append(AW_GATE_SCOPE)
    return violations


def check_lifecycle_role(verb: str, role: str) -> "list[str]":
    """Return `AW_LIFECYCLE_ROLE` violations when a `worker` role invokes a driver-only verb.

    STILL RAISES (spec R6.2), and this one is the most likely to be filled by mistake, so read on.
    Owner label was `rchpms` (Phase 2), RETIRED 2026-09-02 as PARTLY LANDED - and the part that
    landed is exactly this rule: `ipd_lifecycle.worker_role_active` plus the `AW-LIFECYCLE-ROLE-001`
    refusal (`ipd_lifecycle.LIFECYCLE_ROLE_ERROR`) already ship and are already enforced by both
    drivers' `begin`/`finalize`.

    SO WHY NOT DELEGATE TO IT, as `check_scope` delegates to `_scope_match`? Because the enforced rule
    is not this function's shape. It reads the ENVIRONMENT to decide the role and REFUSES with an exit
    code plus operator-facing guidance; this signature takes a role as a STRING and returns a
    violation list. Wrapping one in the other would mean choosing a mapping from `(verb, role)` to a
    refusal that no caller has asked for, i.e. inventing a contract to satisfy a stub. `604wra` is
    chartered to consolidate rules that EXIST and to leave unowned predicates raising, not to design
    a second entry point into a rule that is already single-defined and already wired. Leaving it
    raising is the conforming outcome, and the honest one: there is nothing here that a caller needs.

    If a surface ever needs a pure `(verb, role)` predicate, the conforming fix is to re-propose it on
    merit and have it DELEGATE to `ipd_lifecycle`, never to restate the role rule here.
    """

    raise _unimplemented(
        "check_lifecycle_role",
        "`rchpms` (Phase 2, RETIRED 2026-09-02, partly landed). The rule itself DOES ship, as "
        "`ipd_lifecycle.worker_role_active` + the AW-LIFECYCLE-ROLE-001 refusal, and both drivers "
        "already enforce it; this pure-predicate SHAPE has no caller, so no body is written here",
    )


def format_missing_input(path: str, why: str) -> str:
    """Render the `AW_MISSING_INPUT:<path>:<why>` token from x03wgn Section 4.

    IMPLEMENTED by `lanectn` child `604wra` (spec R6.1). Owner label was `qcqhj7` (Phase 1), which is
    RETIRED (superseded 2026-09-02 by the `lanectn` Set); child `y5od1h` shipped the rule under spec
    R3.1 and this delegates to it.

    A ONE-LINE DELEGATION, DELIBERATELY. `lane_containment.format_missing_input_token` is the single
    definition, and it derives the token's prefix and separator from `MISSING_INPUT_TOKEN_FORM` - the
    same constant the worker's prompt publishes - so the prompt, the emitter, and the parser are
    provably one shape. Re-rendering the token here (even correctly) would be the fork R6.1 forbids:
    two spellings that agree today and drift the first time the published form changes.
    """

    from agent_workflows import lane_containment

    return lane_containment.format_missing_input_token(path, why)


def parse_missing_input(token: str) -> "tuple[str, str] | None":
    """Parse an `AW_MISSING_INPUT:<path>:<why>` token back into `(path, why)`, else `None`.

    IMPLEMENTED by `lanectn` child `604wra` (spec R6.1). Owner label was `qcqhj7` (Phase 1), RETIRED;
    the rule shipped in child `y5od1h` under spec R3.1 and this delegates to it.

    Paired with `format_missing_input` THROUGH THE SHARED DEFINITION rather than beside it, so emit
    and parse cannot drift. Returns `None` for any line that is not a report, because a driver calls
    this on every line of a child's stdout and must not raise on ordinary output. A line that IS a
    report but carries an empty path or reason parses to `("", "")`: that is a MALFORMED report for
    `lane_containment.classify_missing_input_report` to refuse precisely, not a non-report to drop,
    because silently discarding one is how a worker's genuine need disappears.
    """

    from agent_workflows import lane_containment

    return lane_containment.parse_missing_input_token(token)


def check_hook_bypass(
    repo: "Path", commit: str, scope_paths: "Sequence[str]"
) -> "list[str]":
    """Return `AW_GATE_HOOK_BYPASS` violations found by re-checking a commit the hook may have skipped.

    Hooks are corrective feedback, not authority (x03wgn Section 5 Layer 5): `--no-verify`,
    plumbing, and "no commit at all" all evade them, so the driver re-runs the SAME predicate over
    the observable end state.

    STILL RAISES (spec R6.2). Owner label was `rchpms` (Phase 2), RETIRED 2026-09-02; the half that
    would have built this (derive the lane outcome from observed git+process facts, E-07/E-08) is
    explicitly listed as NOT LANDED, and it has no successor plan. `604wra` implements no body here:
    doing so would take a retired phase's design work rather than consolidate an existing rule.

    THE PREMISE IS PROVEN EVEN THOUGH THE GUARD IS ABSENT, which is why this is a gap and not a dead
    end: `tests/test_wtiso_adversarial.py::HookBypassTests::test_hook_bypass_detectable_from_git_now`
    demonstrates that a `--no-verify` commit's paths remain fully visible to `git show --name-only`.
    So a future implementation has everything it needs; what is missing is the driver-side re-check,
    which should be re-proposed on merit.
    """

    raise _unimplemented(
        "check_hook_bypass",
        "`rchpms` (Phase 2, RETIRED 2026-09-02; its observed-from-git half never landed and has NO "
        "successor plan). The bypass IS observable from git today (proven by "
        "tests/test_wtiso_adversarial.py HookBypassTests); the driver-side re-check is an open gap",
    )


def check_protected_refs(
    before: "Mapping[str, str]", after: "Mapping[str, str]"
) -> "list[str]":
    """Return `AW_GATE_PROTECTED_REF` violations by diffing before/after protected-ref snapshots.

    STILL RAISES (spec R6.2). Owner labels were `2c122z` (Phase 5) for the integration block and
    `1o4eif` (Phase 6) for the hardened OS-denied half. `2c122z` was RETIRED UNLANDED on 2026-09-02,
    the single largest loss in that retirement, and its recovery surface (`aw recover`,
    `aw doctor --lanes`) is recorded there as having NO successor. So this predicate has no owner in
    flight.

    WHAT DID LAND SEPARATELY, so a reader does not assume a total gap: `main` already has an
    integration gate and dirty-overlap refusal (`oc_runipd.integrate_lane_branch`,
    `oc_runipd.dirty_tree_overlap`), and cross-platform locking shipped under its own plan. What is
    genuinely absent is protected-REF snapshot diffing, whose raw mechanism is nonetheless proven by
    `tests/test_wtiso_adversarial.py::ProtectedRefTests::test_protected_ref_mutation_detectable_now`.
    """

    raise _unimplemented(
        "check_protected_refs",
        "`2c122z` (Phase 5, RETIRED UNLANDED 2026-09-02) and `1o4eif` (Phase 6) - NEITHER is in "
        "flight and the recovery surface has no successor. The integration gate and dirty-overlap "
        "refusal DID land separately (oc_runipd.integrate_lane_branch, dirty_tree_overlap); "
        "protected-ref snapshot diffing is an open gap",
    )


def check_permission_deadline(
    events: "Sequence[Mapping[str, Any]]", deadline_seconds: float
) -> "list[str]":
    """Return `AW_PERMISSION_DEADLINE` violations for asks unanswered past `deadline_seconds`.

    IMPLEMENTED by `lanectn` child `604wra` (spec R6.1). Owner label was `qcqhj7` (Phase 1), RETIRED;
    child `lhmrhx` shipped the ENFORCING half under spec R4.4 and this is the pure predicate over a
    recorded stream.

    SESSION-AGNOSTIC BY CONSTRUCTION, which is the requirement rather than a simplification. x03wgn
    Section 6 Layer 6 records that the measured deadlock arrived on a NESTED CHILD session, so a
    root-only parser would miss it entirely. This never compares a `sessionID` to a root id: an ask
    is matched to an answer by its OWN session, so a child ask can only be answered within that
    child, and a root-session answer cannot mask it.

    WHAT COUNTS AS AN ANSWER, and why keepalive does not. Only a permission-typed reply on the SAME
    session clears the ask. Ordinary progress does NOT, because the deadlock's whole shape is a
    session that keeps emitting while blocked on an unanswered ask - which is exactly why the coarse
    no-output stall watchdog could not catch it. Contrast
    `lane_containment.TurnBoundWatch.note_progress`, where progress DOES disarm the live bound: that
    is a deliberate difference, not an inconsistency. This function judges a FINISHED stream after
    the fact and can see that the ask was never answered; the live watch cannot see the future, so it
    treats progress as evidence the turn is not wedged and accepts the false-negative rather than
    killing a healthy turn.

    ONE VIOLATION PER UNANSWERED ASK, in first-appearance order, so a caller can count them. A
    missing or unparseable timestamp yields NO violation: `deadline_seconds <= 0` disables the check
    entirely (matching `PERMISSION_TIMEOUT`'s `0`-disables convention), and an undatable ask cannot be
    shown to have exceeded anything. Fail-safe in the permissive direction DELIBERATELY, for the
    reason `lane_containment.PERMISSION_TIMEOUT` records: a false positive kills a healthy turn.

    HONEST LIMIT, and it is the load-bearing caveat. This is a PURE PREDICATE OVER A RECORDED STREAM,
    not a bound. It cannot terminate anything, it needs the ask's END to be observable, and it has
    NO product caller (see the module docstring): `PERMISSION_TIMEOUT` ships at `0` precisely because
    the detector that would feed a live version of this is UNVERIFIED against a real provoked ask.
    So the enforcing bound today is `MAX_TURN_TIMEOUT` alone. Use this for post-mortem analysis of a
    captured stream; do not read its existence as a live guard.
    """

    if deadline_seconds <= 0:
        return []

    asked: "dict[str, list[float]]" = {}
    order: "list[tuple[str, float]]" = []
    for event in events or ():
        if not isinstance(event, dict):
            continue
        kind = str(event.get("type") or event.get("event") or "")
        if not kind.startswith("permission"):
            continue
        session = str(event.get("sessionID") or event.get("session_id") or "")
        stamp = event.get("time", event.get("at"))
        if not isinstance(stamp, (int, float)) or isinstance(stamp, bool):
            continue
        when = float(stamp)
        # An ASK opens a window on its own session; anything else permission-typed on that session
        # (answer/reply/deny/grant/response) closes the OLDEST open one, so a burst of asks is
        # matched in order rather than all cleared by a single reply.
        if kind.endswith((".ask", ".request", ".requested", ".asked")):
            asked.setdefault(session, []).append(when)
            order.append((session, when))
        elif asked.get(session):
            asked[session].pop(0)

    if not any(asked.values()):
        return []

    # The stream's LAST timestamp is the only "now" a recorded stream has. Deriving it from the
    # events (rather than the wall clock) keeps the predicate pure and its result reproducible for
    # the same input, which is what makes it usable in a test and in a post-mortem alike.
    stamps = [
        float(e["time"] if "time" in e else e["at"])
        for e in events or ()
        if isinstance(e, dict)
        and isinstance(e.get("time", e.get("at")), (int, float))
        and not isinstance(e.get("time", e.get("at")), bool)
    ]
    if not stamps:
        return []
    now = max(stamps)

    violations: "list[str]" = []
    for session, when in order:
        if when in asked.get(session, []) and now - when >= deadline_seconds:
            violations.append(AW_PERMISSION_DEADLINE)
    return violations


def classify_retention(repo: "Path", path: str) -> str:
    """Return the retention class for `path`, one of the x03wgn Section 2 retention values.

    An unclassifiable artifact is `unknown`, which BLOCKS teardown; ignored status alone never
    authorizes deletion.

    STILL RAISES (spec R6.2), AND THIS IS THE DELIBERATE NEAR-MISS - read before "finishing" it.
    Owner label was `rchpms` (Phase 2), RETIRED. Sibling `lanectn` child `xdr83v` implements retention
    CLASSIFICATION for that Set under spec R5, so it is tempting to point this at it. `604wra` is NOT
    chartered to, and its own plan names this predicate explicitly as LEAVE RAISING: filling it would
    be scope creep into another phase's charter, and worse, it would assert an equivalence between
    x03wgn's Section 2 retention vocabulary and `xdr83v`'s R5 classes that nobody has verified.

    Note the SIGNATURE MISMATCH that makes the temptation a real hazard rather than a formality: this
    returns a single class string for one path against a repo, which is not the shape a lane-wide
    retention decision takes. A wrapper would therefore be a new contract, not a delegation. If these
    two vocabularies should be unified, that is a reviewed decision with its own plan; a stub is not
    the place to make it silently.
    """

    raise _unimplemented(
        "classify_retention",
        "`rchpms` (Phase 2, RETIRED 2026-09-02; its retention half never landed). NOTE the near-miss: "
        "`lanectn` child `xdr83v` implements retention classification for THAT Set under spec R5, but "
        "it is a different vocabulary and a different signature, and no plan is chartered to declare "
        "them equivalent - so this stays raising rather than guessing a mapping",
    )


def check_receipt(
    receipt: "Mapping[str, Any]", expected: "Mapping[str, Any]"
) -> "list[str]":
    """Return `AW_RECEIPT_INVALID` violations when a receipt does not authorize the exact attempt.

    STILL RAISES (spec R6.2). Owner labels were `rchpms` (Phase 2, sole receipt creator) and `58ha43`
    (Phase 4, relocate the canonical receipt store); both RETIRED 2026-09-02.

    WHAT LANDED FROM `rchpms`, since it changes what is actually missing: keying the begin receipt on
    the plan's FROZEN REGION rather than the whole file (`ipd_lifecycle.frozen_region_digest`) DID
    land, and it was the real fix - a whole-file digest invalidated itself on every correct run,
    because a conforming executor must edit the plan it executes. The worker-role refusal landed too,
    which in practice stops an in-lane agent forking a second receipt.

    So what remains unbuilt is this PURE receipt-vs-expected-attempt predicate as a shared surface,
    which has no caller and no owner. `lane_containment`'s attempt-keyed COLLECTION receipt (spec
    R2.5) is a DIFFERENT artifact - it records whether a lane's submissions were collected - and must
    not be confused with the lifecycle BEGIN receipt this predicate is about.
    """

    raise _unimplemented(
        "check_receipt",
        "`rchpms` (Phase 2) and `58ha43` (Phase 4), BOTH RETIRED 2026-09-02. The frozen-region receipt "
        "digest (`ipd_lifecycle.frozen_region_digest`) DID land; this pure receipt-vs-attempt "
        "predicate has no caller and no owner in flight",
    )

# Review findings: plan 9bq5o4

- Subject-Id: 9bq5o4
- Subject-Type: ipd
- Reviewed-At: 2026-09-27
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `f9842508` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`, and `--detail` reported no `IPD-Z602`
advisory) and `--phase review-finalize` conforms after with `findings: 0`. No pre-review snapshot was
needed: the plan was committed and unmodified, and the lane-input copy at `.aw/state/lane-inputs/rev-2/`
is byte-identical to the tracked file (`diff` reported no difference).

THE GOAL IS RIGHT AND THE MAINTAINER'S RULING IS NOT SECOND-GUESSED. Five code-only waits with five
ad-hoc timings is real duplication, the harm is measured, and one shared helper with one set of
constants is the correct shape. Two of the five changes are unambiguous improvements: E-06's
`ISO_RACED` retry (which I verified WORKS unchanged) and E-05's closing of the unserialized-commit
degradation.

WHAT REVIEW FOUND IS THAT TWO ITEMS WOULD HAVE DAMAGED WORKING BEHAVIOR, and in both cases the
evidence was already in the repository.

**E-02 WOULD HAVE SILENTLY REVERSED AN EXECUTED PLAN AND BROKEN TWO SHIPPED TESTS (PR-001).** It said
to "remove the runner's extra loop in `runner_shared.finalize_with_contention_retry` ... or reduce it
to a single call". That loop is not incidental: plan `y2vzit` built it deliberately and executed on
2026-09-27 (`0df75988`), and two tests pin its behavior.
`test_contention_reattempt_succeeds_leaves_item_executed_with_budget_unchanged` asserts
`call_count == 2` and exactly one `ipd-finalize-lock-wait` event;
`test_lane_arm_reattempt_keeps_lane_repo_argument` asserts four calls, three events, and that every
attempt keeps the LANE repo argument. Measured: `tests/test_finalize_sendback.py` -> `57 passed in
0.58s`. The loop is also not a duplicate of the lock wait: `acquire_finalize_lock` waits for the LOCK
while the loop re-runs the whole `driver_finalize` subprocess including the pre-transition gate, so a
holder appearing between lock release and transaction start is covered only by the loop. Reversing an
executed decision is legitimate, but it must be argued, not done as a side effect of sharing a
constant.

**THE 10 SECOND POLL IS MEASURABLY WRONG FOR THESE LOCKS (PR-002).** The ordinary hold on this lock is
SUB-SECOND, which is the entire reason `y2vzit` gave it a 0.1 s poll. Simulating
`acquire_finalize_lock`'s loop: against a holder releasing at 0.5 s the lock is taken at 0.5 s with a
0.1 s poll and only at 10.0 s with a 10 s poll, a twentyfold stall added to the common case. Worse,
`test_two_process_lock_wait_succeeds` (child holds ~1.0 s, `timeout=5.0`, asserts `elapsed > 0.7`)
TIMES OUT entirely under a 10 s poll. And `test_finalize_lock_WAITS_for_a_short_lived_live_holder`
asserts `waited < 5` against a 0.5 s hold, which a 10 s poll violates. Both spawn REAL subprocesses and
are measured at 0.55 s and 1.10 s, so an injected clock cannot rescue them. The resolution is that the
maintainer's "check every 10 seconds" is the REPORT cadence, which is what the ruling's other two
numbers are also about (what the operator sees, what the wait costs); read that way every promised
property is delivered in full.

**THE STALENESS BOUND WAS BEING FOLDED AWAY (PR-004).** E-04 listed
`DEFAULT_INTEGRATION_STALENESS_LIMIT` among the constants to replace "as the timing source". That
constant is 3600 s, LONGER than the proposed 1800 s timeout, and it answers a different question: not
"have I waited long enough?" but "is anyone working in this tree at all?". The function's own docstring
states both bounds are required and that the count bound alone makes the wait ARBITRARY.

**THE TWO LOCKS ARE ONE FILE, WHICH THE PLAN NEVER SAID (PR-003).** `ipd_lifecycle.finalize_lock_path`
and `commit_lock.lock_path` both return `.aw/state/runtime/locks/ipd_finalize_writer.lock` (verified by
calling both). So E-05's 5 s -> 30 min fail-closed change means an `aw set` queued behind a long
finalize blocks for half an hour and then fails, across seven `offer_commit` call sites including
interactive ones. Closing the unserialized-commit hole is right; the blast radius has to be stated for
the human approving it.

**AND THE WORK ALREADY HAS AN OPEN BACKLOG ITEM (PR-005).** `bqz8kn` (`open`, `Work-Kind: bug`,
`Blocks-Release: next`) is precisely E-05's defect, split out of `duac3v` when `y2vzit` graduated and
deliberately left by that plan. The plan mentions none of `y2vzit`, `duac3v` or `bqz8kn` (grep count
0), so executing it would leave a release-gating bug item open against code it had already fixed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | BLOCKER | IN-SCOPE | D. Anti-regression / C. Architecture | E-02 as authored ("remove the runner's extra loop ... or reduce it to a single call"); executed plan `y2vzit` (`0df75988`, 2026-09-27); `tests/test_finalize_sendback.py::...::test_contention_reattempt_succeeds_leaves_item_executed_with_budget_unchanged` (`call_count == 2`, one event) and `::test_lane_arm_reattempt_keeps_lane_repo_argument` ("initial attempt + 3 reattempts", 3 events, lane repo); measured `57 passed in 0.58s` | **IT WOULD REVERSE AN EXECUTED PLAN WITHOUT SAYING SO, AND BREAK TWO SHIPPED TESTS.** The loop is also NOT redundant with the lock wait: the lock wait waits for the LOCK, the loop re-runs the whole `driver_finalize` subprocess (re-reading the plan, re-running the pre-transition gate, re-attempting the transaction), so a holder that appears between lock release and transaction start is covered only by the loop. Removing it on the reasoning "finalize itself now waits" conflates the two. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | E-02 now explicitly KEEPS the loop, states all three reasons with the measured test baseline, and raises only `FINALIZE_LOCK_WAIT_SECONDS` (120 -> 1800). It also requires the refusal message shape stay byte-compatible, since `finalize_refusal_is_lock_contention` and `parse_finalize_lock_holder` classify on that text. V-02 now demands `rg FINALIZE_LOCK_REATTEMPTS` show the loop still present plus an unchanged `git diff` of that test file. Recorded as F-7. |
| PR-002 | BLOCKER | IN-SCOPE | A. Correctness / E. Testing | E-01 as authored (`POLL_SECONDS = 10.0`); simulation of `acquire_finalize_lock`'s loop: 0.5 s hold -> acquired 0.5 s at poll 0.1, acquired 10.0 s at poll 10.0; 1.0 s hold under `timeout=5.0` -> acquired 1.1 s at poll 0.1, TIMED OUT at poll 10.0; `tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests` measured 0.55 s and 1.10 s with real subprocesses | **A 10 SECOND SLEEP BREAKS THE COMMON CASE AND TWO SHIPPED TESTS.** The ordinary hold on this lock is sub-second, which is why `y2vzit` chose a 0.1 s poll; a 10 s poll adds a twentyfold stall to the case that actually happens and makes `test_two_process_lock_wait_succeeds` time out and `test_finalize_lock_WAITS_for_a_short_lived_live_holder` violate `waited < 5`. Both spawn REAL subprocesses and assert REAL elapsed time, so no injected clock can rescue them. | C:Low; U:Medium; S:Low; F:High; Overall:Low | FIXED | E-01 separates the two numbers: `POLL_SECONDS = 0.1` (responsiveness, today's finalize value) and `REPORT_SECONDS = 60.0` (what the operator was promised). New OQ-02 records the narrow reading of the ruling's "check every 10 s" clause with the measurements, marked `Owner: plan-review`, non-blocking, and surfaced in the gate so approval is informed. E-07 gains cases (d) and (e) pinning the silent fast path and the poll/report independence. Recorded as F-5 and F-6. |
| PR-003 | HIGH | UNDER-SCOPE | B. Security / C. Operability | verified `ipd_lifecycle.finalize_lock_path(r) == commit_lock.lock_path(r)` -> `.aw/state/runtime/locks/ipd_finalize_writer.lock`; `commit_lock.lock_path` docstring "identical to `ipd_lifecycle.finalize_lock_path`"; `offer_commit` census: 7 callers (`cli.py`, `plans_archive.py`, `research_archive.py`, `runner_shared.py`, `specs.py`, `status_set.py`, `work_cmd.py`) | **E-05's BLAST RADIUS WAS UNSTATED AND IT IS LARGE.** The writer lock is the SAME FILE as the finalize lock, so raising 5 s to 30 min AND making it fail-closed means an `aw set`/`aw commit`/`aw specs` queued behind a long finalize now blocks for up to 30 minutes and then FAILS, where today it degrades after 5 s. The item described this as affecting "the main caller". Closing the unserialized hole is correct, but a human approving this is approving a new 30-minute interactive block, and nothing required proving the 60 s progress line actually reaches a terminal. | C:Low; U:High; S:Low; F:Medium; Overall:Medium | FIXED | E-05 now states the shared-lock fact, requires the 7 call sites enumerated with the blocking change per site, requires PROOF the progress line reaches the operator's stderr, and requires a re-verified self-deadlock check (recorded at review: `_finalize_transaction` uses the `coordinator_worktree` path and NOT `offer_commit`, so no current path holds the lock then re-enters the wait). It also corrects the docstring's false "well under a second" premise, which is the argument the 5 s budget rests on. V-05 demands all of it. Recorded as F-8 and F-14. |
| PR-004 | HIGH | IN-SCOPE | A. Correctness | E-04 as authored (replace `DEFAULT_INTEGRATION_STALENESS_LIMIT` "as the timing source"); `DEFAULT_INTEGRATION_STALENESS_LIMIT = 3600.0` versus the proposed 1800 s timeout; `poll_for_integration_window` docstring ("TWO INDEPENDENT BOUNDS, BOTH REQUIRED ... bound (i) alone makes the wait ARBITRARY") | **FOLDING THE STALENESS BOUND INTO THE TIMEOUT DISCARDS THE BOUND THAT MAKES THE WAIT EVIDENCE-BASED.** It is 3600 s, LONGER than the new timeout, and answers a different question ("is anyone working here at all?" versus "have I waited long enough?"). It also fires fail-closed on an UNMEASURABLE age and is checked BEFORE the first sleep so an abandoned tree costs no wait. Separately, `POLL_BOUND_COUNT`'s detail text names a poll count that would cease to be the bound, leaving a recorded outcome describing a bound that no longer exists. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now requires the staleness bound and its 3600 s VALUE to survive untouched, keeps all three `PollOutcome.bound` values, requires `POLL_BOUND_COUNT`'s detail re-worded to name elapsed wall time if the count ceases to bound, and requires `PollOutcome.polls` still counted (the runner writes it into `item["integration_poll"]` and the `ipd-integration-poll` event). It also flags the now-possibly-inert `state["options"]["integration_poll_limit"]` read. V-04 demands both halves separately. Recorded as F-10. |
| PR-005 | HIGH | UNDER-SCOPE | G. Plan executability / release gates | backlog `bqz8kn` (`open`, `Work-Kind: bug`, `Blocks-Release: next`, set `wlockbudget`), whose body is E-05's defect verbatim; `grep -c "bqz8kn\|y2vzit\|duac3v"` on the plan -> 0 | **THE PLAN RESOLVES AN OPEN RELEASE-GATING BUG ITEM AND NEVER MENTIONS IT, NOR ANY OF THE PRIOR WORK ON THIS GROUND.** `bqz8kn` was split out of `duac3v` when `y2vzit` graduated, precisely because that plan deliberately left the shared budget alone. Executing this plan without closing it leaves the release gated on a bug this plan fixed, and a reader of either artifact cannot see the other. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 states that it resolves `bqz8kn`; the gate's closing instruction now requires `aw backlog set done bqz8kn --evidence <executed plan>` alongside `ibk7bt`, with the reason. The conventions section now records `y2vzit`, `duac3v` and `bqz8kn` and the fact that `y2vzit`'s review already MEASURED the long-default-wait hazard this plan re-introduced (its F-5 is the precedent for E-08 (f)/(g)). Recorded as F-9. |
| PR-006 | MEDIUM | UNDER-SCOPE | A. Correctness / C. Operability | E-06 as authored; measured in a scratch repo: forcing one `ISO_RACED` then re-calling `commit_isolated` -> `committed`, peer commit intact beneath, only `mine.txt` in our commit; `offer_commit`'s `git reset --quiet HEAD -- <our_staged>` on every non-success path; hook cost 10.6 s (backlog `bqz8kn`) | **THE RETRY MECHANISM WORKS BUT ITS SITING AND ITS COST WERE UNSPECIFIED.** Two facts decide it: `offer_commit` UNSTAGES before classifying the status, so a retry sited after that reset has nothing left staged; and each retry re-runs the full pre-commit hook set (10.6 s measured), so a 30-minute wall bound alone permits on the order of a hundred hook runs, held INSIDE the writer lock E-05 makes fail-closed, blocking every other `aw` verb and any finalize for that whole period. | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | E-06 now carries the measured proof the mechanism works (so no new copy logic is written), requires the loop sited BEFORE the reset, requires an attempt CAP beside the time bound with its value stated, and states the lock-holding consequence. V-06 demands the cap and the siting diff. Recorded as F-11 and F-12. |
| PR-007 | MEDIUM | UNDER-SCOPE | G. Right-sizing and conceptual density | E-07 as authored: six test cases across two fixture kinds, an existing-test adjustment, a CHANGELOG line, a suite run and a sanitizer run in one item; rubric G diagnostics (a), (b), (c) | **ONE E-ITEM CARRIED THREE DELIVERABLES AND TWO INCOMPATIBLE TEST HARNESSES.** Cases (a)/(b) are pure-helper with an injected clock; (c)/(d)/(e)/(f) need real lock files, real subprocesses and a patched `commit_isolated`. It also bundled the record (CHANGELOG) with the tests. The count-based lint passed with no `IPD-Z602`, which is exactly the case the semantic right-sizing check exists for. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split three ways: E-07 (five pure-helper cases), E-08 (call-site cases PLUS the four named regression guards), E-09 (CHANGELOG and suite). `Highest E allocated` raised to 09; V-07, V-08 and V-09 added; dependency edges re-pointed (E-07 on E-01, E-08 on E-02..E-07, E-09 on E-08). Bijection 9/9, linter still `conforming` with no advisory. |
| PR-008 | MEDIUM | UNDER-SCOPE | E. Testing / G. executability | `- Scope-Paths:` as authored (no `tests/test_ipd_lifecycle_cli.py`, no `tests/test_finalize_sendback.py`) while E-02's change reaches assertions in both | **THE TWO TEST FILES THE CHANGE ACTUALLY TOUCHES WERE NOT DECLARED.** `y2vzit` hit the identical problem and its review recorded it ("it is why `tests/test_ipd_lifecycle_cli.py` is already in `- Scope-Paths:`"), so the precedent was one plan old. An undeclared path means the finalize scope gate refuses without a `--scope-reason` and the executor discovers the coupling mid-run. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both files added to `- Scope-Paths:`. E-08's guards (e)-(h) name each affected test with its measured baseline so the executor knows before starting which assertions are load-bearing and which timings must not move. |
| PR-009 | LOW | IN-SCOPE | A. Correctness (provenance) / F. honest documentation | plan F-3 citing `kkzgrk`, `oc3mhb`; verified `kkzgrk` is a `done` BACKLOG item and `oc3mhb` a `graduated` one; the operator-visible string is `warning: self-commit skipped: ...` in `cli.py`/`plans_archive.py` | Two id6s were cited as though they were run items ("seen twice on 2026-09-26/27"). They are backlog artifacts, so the true claim is about the setter commits that moved THEM. A reader trying to verify the measurement against run records would find nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 and F-13 now state they are backlog artifacts and name the actual operator-visible leftover string and its two source files. Recorded as F-13. |
| PR-010 | LOW | IN-SCOPE | F. Honest documentation | E-07's CHANGELOG wording as authored ("checking every 10 seconds"); two `## ... (pending)` sections exist in `CHANGELOG.md` (`2.0.0` and `1.3.0`) | The CHANGELOG line would have published a 10 second check interval that, after PR-002, the code does not use, making a public claim false on its first day. The plan did name `2.0.0 (pending)` correctly, but the two-pending-section trap is one this repository has hit and is worth stating beside the line. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-09 drops the interval claim, keeps the report cadence and the 30 minute bound, and explicitly forbids writing "checking every 10 seconds"; it also names `## 2.0.0 (pending)` against `## 1.3.0 (pending)` explicitly. V-09 requires the diff show the right section and the absent claim. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | Does "check every 10 seconds" mean the sleep between probes or the operator report cadence? | The REPORT cadence; `POLL_SECONDS` stays 0.1. | (a) Literal 10 s sleep: rejected on measurement, it adds a twentyfold stall to the sub-second common case and makes one shipped test time out and another violate its bound. (b) 10 s sleep with the three real-time tests rewritten to an injected clock: rejected because those tests spawn REAL subprocesses precisely to prove the wait works against a real live holder, and converting them would delete the coverage rather than adapt it. | Simulation of `acquire_finalize_lock`'s loop (0.5 s hold: 0.5 s vs 10.0 s; 1.0 s hold under 5.0 s timeout: 1.1 s vs TIMEOUT); measured test durations 0.55 s and 1.10 s; `y2vzit` chose 0.1 s for this lock for exactly this reason. Every operator-visible property of the ruling is still delivered. | yes |
| D-2 | Remove `finalize_with_contention_retry`'s loop, as E-02 proposed? | KEEP it; raise only the lock budget. | (a) Remove it and update the two tests: rejected, it silently reverses executed plan `y2vzit` and the loop covers a case the inner wait cannot (a holder appearing between lock release and transaction start). (b) Reduce to a single call: same objection, and it still breaks both tests. | `y2vzit` executed 2026-09-27 (`0df75988`) building the loop deliberately; `tests/test_finalize_sendback.py` pins `call_count == 2` and the 4-call lane variant, measured `57 passed in 0.58s`; the two mechanisms wait for different things (`acquire_finalize_lock` for the LOCK, the loop re-runs the whole `driver_finalize` subprocess). | yes |
| D-3 | Fold the 3600 s staleness bound into the new 1800 s timeout? | No; keep it and its value. | Reduce it to the timeout; drop it as redundant. | The function's own docstring: "TWO INDEPENDENT BOUNDS, BOTH REQUIRED", and bound (i) alone "makes the wait ARBITRARY". It is also LONGER than the timeout and fires fail-closed on an unmeasurable age, so it is not expressible as a shorter time bound. | yes |
| D-4 | Is E-05's fail-closed 30 min writer lock safe to approve, given it shares a file with the finalize lock? | Yes, but the blast radius must be stated in the gate and the progress line proven to reach the operator. | (a) Leave `required=False`: rejected, that IS the bug (`bqz8kn`) and it re-opens the pre-commit stash race. (b) A shorter fail-closed budget (say 60 s): a defensible alternative I did NOT substitute, because the maintainer's ruling names 30 minutes for all five and the 60 s progress line is what makes a long wait tolerable; noted here so the maintainer can choose it. | Verified the two lock paths are identical and that 7 call sites inherit the change; verified no current path holds the lock and then re-enters the wait (`_finalize_transaction` uses `coordinator_worktree`, not `offer_commit`), so a deadlock is not introduced; backlog `bqz8kn` documents the harm the current default causes. | yes |
| D-5 | Should `bqz8kn` be closed by this plan? | Yes; close it with `--evidence` alongside `ibk7bt`. | Leave it open as parallel work. | Its body is E-05's defect verbatim and it carries `Blocks-Release: next`, so leaving it open gates the release on code this plan fixes. `From-Backlog` cannot carry two ids, so the obligation is recorded in E-05 and in the gate instead. | yes |
| D-6 | Split E-07, given the count-based lint reported no `IPD-Z602`? | Split three ways (E-07 helper / E-08 call sites and guards / E-09 record). | Accept the density; split two ways (tests / record). | The workflow states a passing count-based size lint does NOT clear conceptual density, and rubric G (b) and (c) are both met: the pure-helper cases need only an injected clock while the call-site cases need real lock files, real subprocesses and a patched `commit_isolated`, and the CHANGELOG is a third independent deliverable. A two-way split would leave the two incompatible harnesses bundled. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 is owed. Every
finding is `FIXED`; none was deferred or left open, so no `- Blocking: yes` escalation under Step 4 is
owed either. D-1 narrows one clause of the maintainer's OQ-01 ruling, so it is recorded as the plan's
own OQ-02 (`Owner: plan-review`, non-blocking) AND surfaced as point 3 of the gate's approval summary,
which is the honest path for a reviewer's own choice that touches a human decision: it is visible at
the moment of approval and costs one constant to reverse.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`. `--detail`
  reported `conforming` with no `IPD-Z602` advisory, which is why PR-007's density finding is a
  semantic one the linter did not raise.
- `aw ipd lint --phase review-finalize --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`
  after all edits (the E-07/E-08/E-09 split, the V rebuild to 9 items, the `Scope-Paths` widening and
  the new OQ-02).
- Lane input identity: `diff .aw/state/lane-inputs/rev-2/plan-20260927-uniwait-01-9bq5o4-....ipd.md
  .aw/records/plans/pending/20260927-uniwait-01-9bq5o4-....ipd.md` -> no difference; `git status
  --porcelain` clean before editing, so no pre-review snapshot was owed.
- Shared lock path, verified by calling both functions:
  `ipd_lifecycle.finalize_lock_path(r)` and `commit_lock.lock_path(r)` both return
  `<r>/.aw/state/runtime/locks/ipd_finalize_writer.lock`; equality `True`.
- Poll simulation of `acquire_finalize_lock`'s loop (check holder, raise past deadline, else sleep):
  - holder releases at 0.5 s, `timeout=10`: poll 0.1 -> acquired at 0.5 s; poll 10.0 -> acquired at 10.0 s.
  - holder releases at 1.0 s, `timeout=5.0`: poll 0.1 -> acquired at 1.1 s; poll 10.0 -> RAISED at 10.0 s.
  So `test_finalize_lock_WAITS_for_a_short_lived_live_holder`'s `waited < 5` fails and
  `test_two_process_lock_wait_succeeds` times out under a 10 s poll.
- Measured test baselines (all green at review):
  - `python3 -m pytest -o addopts="" tests/test_finalize_sendback.py -q` -> `57 passed in 0.58s`.
  - `python3 -m pytest -o addopts="" tests/test_ipd_lifecycle_cli.py -q -k lock` -> `6 passed, 39
    deselected in 2.42s`.
  - `--durations=5` on the two real-time tests -> `1.10s call ...test_two_process_lock_wait_succeeds`,
    `0.55s call ...test_finalize_lock_WAITS_for_a_short_lived_live_holder`.
- `ISO_RACED` retry proved to work, in a scratch repo under the gitignored `tmp/` tree: patched
  `commit_lock._git` to land a peer commit immediately before `update-ref`, once. Attempt 1 returned
  `raced`; `mine.txt` still held `my change` on disk; the branch tip was `peer commit`. Calling
  `commit_isolated` again UNCHANGED returned `committed f6485b3f0d39`, the log read
  `f6485b3 my commit` / `69bd599 peer commit` / `3898ce1 base` (peer's work intact beneath ours), and
  `git show --name-only HEAD` listed only `mine.txt`.
- `offer_commit` call-site census (AST-free grep, `offer_commit(` excluding the definition): 7 callers,
  `cli.py:6474`, `plans_archive.py:295`, `research_archive.py:554`, `runner_shared.py:31156`,
  `specs.py:902`, `status_set.py:1592`, `work_cmd.py:712`.
- Self-deadlock check: `_finalize_transaction` holds `acquire_finalize_lock` and uses the
  `coordinator_worktree` path, NOT `offer_commit` (its own comment explains why `commit_isolated` is
  unusable there), and `offer_commit` appears nowhere in `ipd_lifecycle`'s transaction body. So no
  current path holds the shared lock and then re-enters the wait under a different process identity.
- `writer_lock(timeout=5.0, poll=0.05, required=False)` and its dead-holder takeover via `try_acquire`
  confirmed at the symbol; `required=False`'s degrade-to-unserialized arm confirmed; the docstring's
  "well under a second" premise confirmed present and contradicted by `bqz8kn`'s 10.6 s measurement.
- Prior-work artifacts confirmed by `aw find`: `y2vzit` executed (`.aw/records/plans/executed/...`),
  `duac3v` `done`, `bqz8kn` `open` with `Work-Kind: bug` and `Blocks-Release: next`, `ibk7bt`
  `graduated`, `kkzgrk` `done` (backlog), `oc3mhb` `graduated` (backlog).
- Spec check: `25kzda` Section 2.1 fixes `--integration-retry-limit`'s MEANING and the
  `--on-integration-blocked` ladder's shape ("the bounded poll") but no INTERVAL, and its
  `--allow-concurrent-driver` bullet requires the integration-lock wait to be bounded, name the holder,
  report progress, and DEFER rather than fail on expiry. E-03 preserves all four. No amendment owed.
- `CHANGELOG.md` has TWO pending sections (`## 2.0.0 (pending)` line 7, `## 1.3.0 (pending)` line 80).
- No code, test, or configuration file was modified. This review edited the plan and wrote this record;
  all scratch repositories were created under the gitignored `tmp/` tree and removed afterwards.

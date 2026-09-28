# Review findings: plan pjuoyj

- Subject-Id: pjuoyj
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `9f5753e7` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` CONFORMS
after revision (exit 0, `findings: 0`). No pre-review snapshot was owed: `git status --porcelain --`
on the plan path was empty, so the plan was committed and unmodified.

THE PLAN'S DIAGNOSIS IS CORRECT AND ITS DISCIPLINE IS HIGH. Every premise claim reproduces. The
defect is real: `retry_deferred_integrations._finish` calls `lane_containment.teardown_lane_if_classified`
and pops the `preserved_*` keys EARLIER IN THE SAME BODY than its guarded `process_backlog_close`
call, so F-04 holds exactly and there is genuinely no lane to write in. F-02 reproduces verbatim: with
a rejecting `pre-commit` hook, `commit_backlog_close` returns None and main is left reading
`D <graduated>` plus `?? <done>` while `git ls-tree -r HEAD` still records the item at `graduated/`.
F-08's narrowness reproduces (the guard and its comment are exactly as quoted). F-03 holds
(`commit_lock.coordinator_worktree` ships with `ipd_lifecycle._finalize_transaction` as its caller).
The three-arm vocabulary F-06/E-06 relies on is real and exit-code-driven as claimed, and all three
arms reproduced on demand (`reconciled` rc=0 with a peer's unrelated dirty file byte-for-byte intact;
`refused-would-overwrite` rc=1 naming the objecting path with main's tip unmoved; `raced` rc=128 with
main's tree clean). The choice to reuse the shipped coordinator-worktree mechanism rather than fork it
is right, and the deferral rows are honest, each carrying a real carrier that exists on disk.

WHAT REVIEW FOUND IS ONE REGRESSION THE PLAN WOULD HAVE SHIPPED, ONE DUPLICATION IT WOULD HAVE
WRITTEN, ONE UNWRITABLE ASSERTION, AND ONE FIELD THAT WOULD HAVE LIED TO AN OPERATOR.

**THE RACED ARM AS SPECIFIED WOULD HAVE MADE THIS PATH WORSE THAN THE CODE IT REPLACES (PR-001,
HIGH, and the finding this review exists for).** E-05 as authored said to RECORD all three arms and
continue. Measured: re-calling `land_worktree_commit` on the same coordinator commit after a peer
commit advanced main returns `raced` rc=128 on attempts 1, 2 AND 3, with
`git merge-base --is-ancestor <landed> HEAD` false throughout and main's tip never moving. That is
structural, not transient: the coordinator commit's parent is the stale tip, so no fast-forward
exists however often it is retried. Meanwhile TODAY's path SURVIVES that same race, because
`commit_backlog_close` reaches `git_commit_helper.offer_commit` -> `commit_lock.commit_isolated`,
whose `ISO_RACED` arm re-snapshots the new tip and rebuilds under `contention_wait` bounded by
`ISO_RACED_MAX_ATTEMPTS`. Verified by inducing a REAL race (a `pre-commit` hook advancing `main` once
from inside the isolated worktree, i.e. between the HEAD snapshot and the compare-and-swap): the
close LANDED, main's tip became the close commit, and the peer commit was preserved as its parent.
So a record-only raced arm would trade a working concurrent close for a reported non-close, on
exactly the concurrency this Set exists to handle. The plan's own OQ-01 rested on the opposite
premise, asserting the new design "costs a reported refusal and never a lost write; that is strictly
better than today", whose second clause is false as originally scoped. This is the sharpest finding
because the plan was thorough enough to identify the arm and its exit code, and still drew the wrong
conclusion about what to DO with it.

**THE DECIDE-AGAINST-MAIN / WRITE-ELSEWHERE SPLIT ALREADY EXISTS AND ACCEPTS A COORDINATOR WORKTREE
(PR-002, MEDIUM).** E-03 specified a new shared performer that "performs only the move plus the
commit". But `process_backlog_close` already takes `lane_repo` and its own docstring already declares
"THE DECISION AND THE WRITE HAPPEN IN DIFFERENT TREES, DELIBERATELY". Measured by passing a live
`coordinator_worktree` path as `lane_repo` to the REAL function with real closers: the verdict was
taken against main, BOTH `close_backlog_item` and `commit_backlog_close` received the coordinator
worktree, the coordinator branch advanced, main's tip did not move while the close ran, main's
porcelain held no backlog path at any instant, and a following `land_worktree_commit` returned
`reconciled` rc=0 with the item at `done/` and gone from `graduated/`. So the performer is a THIN
CALLER, not a second close implementation, and writing one from scratch would have duplicated the
release-gated `--status done` spelling, the two-sided porcelain fail-closed check, the id6 path
filter and the integrity self-check - every one of which carries a measured incident in its own
comment. Three couplings the seam brings with it are now named in the plan rather than left to be
discovered.

**E-02's MANDATED SUCCESS-ARM ASSERTION IS NOT WRITABLE (PR-003, MEDIUM).** E-02 required case (1) to
assert "the close reaching main as a fast-forward of a commit whose parent chain does not start at a
commit authored in the shared tree". Measured by building both shapes over one base: a commit
authored directly on main and a coordinator-worktree commit landed by `git merge --ff-only` are
INDISTINGUISHABLE in the commit graph - each is a one-parent commit whose single parent IS main's
pre-call tip. The only observable difference is the reflog (`commit: close` versus
`merge <sha>: Fast-forward`), which is local, prunable and outside published history, so pinning
behavior to it would pin a diagnostic rather than a contract. An executor would have burned a cycle
discovering this, or worse, written a reflog assertion. The success arm is now pinned on tree
cleanliness plus the new `wrote_in` value, and the landing shape is pinned where it is genuinely
observable: the failure arms.

**THE RECORD WOULD HAVE MISREPORTED THE TREE (PR-004, MEDIUM).** `process_backlog_close` writes
`"wrote_in": "lane" if isolated else "main"`, a two-valued field derived from one boolean and also
emitted on the `backlog-item-closed` event. Measured: a close performed in a real coordinator
worktree records `wrote_in: "lane"`, which is false at a call site whose defining premise (F-04) is
that no lane exists. The field's own comment says it is there so "an operator (and V-01) can tell
from the run's own state WHICH tree performed the write", so a wrong value defeats its stated
purpose. It is pinned by NO test (`grep -rn wrote_in tests/` returns nothing at this HEAD), which is
why this was silent, and the new E-item must add the assertion it never had.

Every other claim was checked and HELD. Two upgrades to the plan's own framing are worth naming: the
plan's `Deferred` row for `integrate_retired_lane` is accurate (its teardown genuinely precedes its
close, and it genuinely lacks the `backlog_close.closed` guard, so it fires unconditionally on its
arm), and its carrier `sj4zte` exists `open` on disk; and F-09's observation that the close runs
outside the held integration lock is correct as read (`do_finish` is called after
`integrate_under_repository_lock` returns), which is precisely what makes PR-001's race reachable
rather than theoretical. The plan's refusal to touch `evaluate_backlog_close`, `check_engine` or the
`--status done` spelling is right and is left intact.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | HIGH | IN-SCOPE | A. Correctness and data integrity / D. Anti-regression | MEASURED at HEAD `9f5753e7`: `ipd_lifecycle.land_worktree_commit` on the same coordinator commit after a peer commit -> `raced` rc=128 on attempts 1, 2 and 3, `git merge-base --is-ancestor <landed> HEAD` false throughout, main's tip unmoved; a rebuild on the new tip -> `reconciled` rc=0 with the peer commit an ancestor. TODAY: `runner_shared.commit_backlog_close` -> `git_commit_helper.offer_commit` -> `commit_lock.commit_isolated`, whose `ISO_RACED` arm re-snapshots and rebuilds under `contention_wait`/`ISO_RACED_MAX_ATTEMPTS`; with a `pre-commit` hook advancing `main` once from inside the isolated worktree the close LANDED and the peer commit was preserved as its parent. Plan E-05 as authored: "ON EITHER FAILURE ARM the item must be left with its `backlog_close` record naming the arm and its reason ... and the run must CONTINUE" | **A RECORD-ONLY `RECONCILED_RACED` ARM IS A REGRESSION, NOT A SAFE FALLBACK.** Re-merging the same coordinator commit can NEVER land, because its parent is the stale tip; so recording and continuing leaves the close permanently undone on a peer-commit race that today's `commit_isolated` path survives by rebuilding. The plan's OQ-01 explicitly rested on the contrary premise ("never a lost write ... strictly better than today"). The REFUSED arm is genuinely different and must still be left alone, since it protects a co-worker's uncommitted bytes; RACED destroys nothing and is merely a stale base. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-06 now REQUIRES the raced arm to re-open a coordinator worktree on the NEW tip, re-perform the move and commit, and re-land, bounded by an attempt cap reusing `contention_wait`, with cap exhaustion as the only recorded-failure outcome and an explicit prohibition on re-merging the stale commit. New E-07 pins the non-regression with a test that must be shown FAILING against a record-only arm. E-01 gains fact (f) re-measuring both halves with a stated correction path if the second half stops holding. New F-10/F-11. V-06 rewritten to demand the landed-after-rebuild evidence; new V-07. The gate gains a THIRD refusal distinguishing RACED from REFUSED. OQ-01 resolved accordingly (D-1). |
| PR-002 | MEDIUM | IN-SCOPE | C. Architecture (avoid duplicate paths) / F. KISS | MEASURED at HEAD `9f5753e7`: `runner_shared.process_backlog_close(..., lane_repo=<live coordinator_worktree>, lane_handle=None)` with real closers -> verdict taken against main, `close_backlog_item` AND `commit_backlog_close` both received the coordinator worktree path, coordinator branch advanced, main's tip unmoved during the close, main porcelain free of any backlog path, then `land_worktree_commit` -> `reconciled` rc=0, item at `done/` and absent from `graduated/`. That function's own docstring: "THE DECISION AND THE WRITE HAPPEN IN DIFFERENT TREES, DELIBERATELY". Plan E-03 as authored: "a new shared function that ... performs the move and commit in a throwaway worktree" | **THE SEAM E-03 WOULD HAVE REBUILT ALREADY EXISTS AND ALREADY ACCEPTS A COORDINATOR WORKTREE.** A from-scratch performer would duplicate the release-gated `--status done` spelling, the two-sided porcelain fail-closed check, the id6 basename filter and the integrity self-check, each of which carries a measured incident in its own comment. Three couplings needed naming rather than discovery: `lane_executed_carrier_override` correctly returns `{}` for a worktree based on main's tip (its own `main_rel == lane_rel` arm), `wrote_in` is misreported (PR-004), and `lane_handle` must stay None since `collect_lane_earned_paths` describes a lane branch range. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now requires the performer to DELEGATE through the existing `lane_repo` seam and states the measurement; its Expected outcome says so explicitly; the three couplings are enumerated with the confirm-rather-than-assume instruction. New F-12. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing and verification | MEASURED at HEAD `9f5753e7` over one base: a commit authored on main and a coordinator-worktree commit landed by `git merge --ff-only` both yield `git rev-list --parents -1` with exactly ONE parent and `git rev-parse <sha>^` equal to the base. `git reflog show main` differs (`commit: close` vs `merge <sha>: Fast-forward`). Plan E-02 as authored: assert "a fast-forward of a commit whose parent chain does not start at a commit authored in the shared tree" | **THAT ASSERTION HAS NO OBSERVABLE REFERENT.** The two shapes are graph-identical, so the success arm cannot discriminate them; only the reflog can, and a reflog is local, prunable and not published history, so pinning to it pins a diagnostic rather than a contract. As written the item sends the executor after an unwritable test, or to a reflog assertion that would rot. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 carries a CORRECTION APPLIED AT REVIEW paragraph with the measurement, repoints case (1) at tree cleanliness plus the new `wrote_in` value, and states that the landing shape is pinned on the FAILURE arms where it is genuinely observable; the Expected outcome no longer demands case (1) fail. New F-14. |
| PR-004 | MEDIUM | IN-SCOPE | A. Correctness / F. Prevent silent failure | MEASURED at HEAD `9f5753e7`: a close performed in a real coordinator worktree recorded `"wrote_in": "lane"`. Source: `record` is built with `"wrote_in": "lane" if isolated else "main"` and the value is re-emitted on the `backlog-item-closed` event; its own comment says it exists so "an operator (and V-01) can tell from the run's own state WHICH tree performed the write". `grep -rn wrote_in tests/` -> no match | **THE RECORD WOULD TELL AN OPERATOR A LANE PERFORMED THE WRITE AT A CALL SITE WHOSE PREMISE IS THAT NO LANE EXISTS** (F-04). A two-valued field derived from one boolean cannot express a third tree, and the field is pinned by no test, which is why this would have shipped silently. | C:Low; U:Medium; S:Low; F:Low; Overall:Low | FIXED | New E-04 extends the vocabulary with a third value threaded from the caller rather than re-derived from a path comparison, and requires the assertion the field never had; new V-04 demands the record, the event line, and the FAILING output when the value is reverted. New F-13. Required tests updated. |
| PR-005 | LOW | IN-SCOPE | G. Executability | Plan `Required tests / validation` as authored named only the three E-02 cases, the agy binding test, the bare suite and the baseline | The two highest-value new tests (the `wrote_in` assertion and the race non-regression) were not listed among the required validations, so a reader scanning that section alone would not see that the plan's single most important test exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `Required tests / validation` now lists the E-04 `wrote_in` assertion and names the E-07 race non-regression test as the most important test in the plan, with the requirement that it be shown FAILING against a record-only arm rather than merely passing. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | OQ-01 asked whether the close should be performed INSIDE the repository integration lock. The plan left it `open` and non-blocking on the premise that the unlocked window "costs a reported refusal and never a lost write". Measurement falsified that premise (PR-001). Resolve it, or escalate it? | RESOLVE: do NOT widen the lock, and instead make the RACED arm rebuild on the new tip (E-06) and pin that with a test (E-07). OQ-01 moves to `resolved` with the falsification recorded. | (a) WIDEN THE LOCK to cover the close, which `AGENTS.md` favors for a publish generally: rejected as unnecessary once the raced arm lands, and costly - the lock is repository-scoped and shared with peer drivers and the `aw integration-lock` verb, so lengthening it slows every driver for a close F-08 measures as rare. (b) LEAVE IT OPEN as the plan had it: rejected, because the stated reason for it being safe to leave open is the very claim measurement falsified, so leaving it would preserve a rationale known to be wrong. (c) ESCALATE to the maintainer as blocking: rejected, because this is not a public-contract or risk-appetite judgement - the repository has ALREADY answered this exact condition in code, in `commit_isolated`'s `ISO_RACED` arm, so the evidence resolves it. | `commit_lock.commit_isolated`'s `ISO_RACED` arm with `ISO_RACED_MAX_ATTEMPTS` and `contention_wait` as the shipped precedent for this condition; the three-attempt `raced` rc=128 measurement plus the successful rebuild-on-new-tip measurement at HEAD `9f5753e7`; the induced-race measurement showing today's close lands; `runner_shared.reattempt_deferred_integrations` calling `do_finish` after `integrate_under_repository_lock` returns (F-09). | yes |
| D-2 | PR-002: is reusing `process_backlog_close`'s `lane_repo` seam for a COORDINATOR worktree a legitimate use of a parameter named for a lane, or does it need its own parameter? | REUSE THE SEAM, and fix the misreporting it causes (PR-004) rather than duplicating the close. | (a) Add a distinct parameter for a coordinator worktree: rejected as an API change with no behavioral difference - the function only ever uses `write_repo` as "the tree the move and commit happen in", which is exactly what a coordinator worktree is. (b) Write an independent performer as E-03 originally said: rejected, it would duplicate four fail-closed mechanisms each carrying its own measured incident. The honest residue is the parameter's NAME, which is why PR-004 fixes the operator-visible half rather than leaving the record to say `lane`. | The measured end-to-end run through the real `process_backlog_close` with a coordinator worktree as `lane_repo`; that function's own docstring declaring the decide/write split as deliberate; `lane_executed_carrier_override`'s `main_rel == lane_rel` early return making the override inert for a main-based worktree. | yes |
| D-3 | PR-003: the success-arm graph assertion E-02 mandates is unwritable. Drop the success-arm assertion entirely, or repoint it? | REPOINT it at tree cleanliness plus the new `wrote_in` value, and state plainly that the landing shape is pinned on the FAILURE arms. | (a) Assert on the reflog: rejected, a reflog is local, prunable and outside published history, so a test on it pins a diagnostic and would rot. (b) Drop case (1) altogether: rejected, the success arm still needs to assert that main's tree is never left holding a backlog path, which is the property the incident in `process_backlog_close`'s docstring is about. | The measured graph identity of the two shapes at HEAD `9f5753e7`; `git reflog show main` as the only differing observable; the plan's own F-02, which locates the discriminating behavior on the failure arm. | yes |

Every finding is `FIXED`; none is left `OPEN` or `DEFERRED`, so no escalation to a `- Blocking: yes`
question is owed and the repository's `HIGH` gate threshold is satisfied without one. PR-001 is `HIGH`
and was FIXED in place rather than escalated, which is the correct disposition under the Fix Bar: its
overall Remediation Risk is Medium (a bounded, local change with a clear verification path, whose
mechanism is already shipped in `commit_isolated` and whose success was measured), not Medium-High. No
decision above is `Reversible: no`, so no decision requires escalation either. OQ-01 moves from `open`
to `resolved` (D-1); no new open question is created.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- `aw ipd lint --phase review-finalize --agent <plan>` -> exit 0, `"outcome":"clean"`,
  `"findings":0`.
- AN INTERMEDIATE DIAGNOSTIC WAS HIT AND FIXED, recorded because it is a mechanical contract a
  reviewer can get wrong: adding the two new items as SUFFIXED ids (`E-03b`, `E-05b`, with the
  matching `V-03b`/`V-05b`) made `review-finalize` report exit 1 with six diagnostics - four
  `IPD-I302` ("execution-section leaf must be a valid E-* item", "validation-section leaf must be a
  valid V-* item") and two `IPD-I304` ("Highest E allocated must be an integer"). Suffixed ids are not
  in the schema. Fixed by renumbering to plain integers (the new items became E-04 and E-07, with
  E-04..E-07 shifting to E-05..E-09), setting `- Highest E allocated: 09`, and re-checking every
  in-prose `E-NN` cross-reference after the shift.
- No pre-review snapshot was owed: `git status --porcelain -- <plan>` was EMPTY before editing, so the
  plan was committed and unmodified.
- **F-02 REPRODUCED VERBATIM.** Driving the real `runner_shared.commit_backlog_close` in a scratch
  repo with a `pre-commit` hook that exits 1: returned `None`, and main's `git status --porcelain
  -uall` read `D .aw/records/backlog/graduated/<item>` plus `?? .aw/records/backlog/done/<item>`,
  with `git ls-tree -r --name-only HEAD` still recording the item at `graduated/` while the file was
  on disk at `done/`.
- **F-04 REPRODUCED.** Read in `runner_shared.retry_deferred_integrations._finish`: the
  `lane_containment.teardown_lane_if_classified` call and the `preserved_*` pop block both precede the
  `if not (item.get("backlog_close") or {}).get("closed"): process_backlog_close(run_dir, state, item)`
  call in the same function body.
- **F-08 REPRODUCED.** The guard and its comment are verbatim as the plan quotes them ("re-evaluating
  would answer `item is already done` (close=False) and OVERWRITE the success record with a refusal").
- **F-03 REPRODUCED.** `commit_lock.coordinator_worktree` exists with `COORDINATOR_WORKTREE_PREFIX`,
  yields `WorktreeCommit(path, branch, base)`, and unconditionally removes both worktree and branch in
  its `finally`; `ipd_lifecycle._finalize_transaction` is its live caller and performs exactly the
  mutate-in-`coord.path` / commit-there / `land_worktree_commit` sequence the plan describes.
- **ALL THREE LANDING ARMS REPRODUCED ON DEMAND** at HEAD `9f5753e7`. OK: `reconciled` rc=0,
  "Updating .. / Fast-forward", main ended reading exactly `M peer.txt` with the peer's in-flight
  bytes verbatim, and the coordinator worktree and branch were both cleaned up (`git worktree list`
  showed 1 entry, `git branch --list 'aw/coordinator/*'` empty). REFUSED: `refused-would-overwrite`
  rc=1 with `landing.paths == ('sub/item.md',)`, main's tip unmoved and the local edit intact. RACED:
  `raced` rc=128, main's tip at the peer commit, tree clean, the coordinator commit NOT an ancestor.
- **PR-001, THE REGRESSION MEASUREMENT.** Three consecutive `land_worktree_commit` calls on the same
  coordinator commit after a peer commit -> `raced 128`, `raced 128`, `raced 128`;
  `git merge-base --is-ancestor <landed> HEAD` false after all three; main's tip unchanged. Rebuilding
  the same content in a SECOND coordinator worktree based on the new tip and landing that ->
  `reconciled 0`, main advanced, content correct, peer commit still an ancestor. Today's path under a
  genuinely induced race (a `pre-commit` hook advancing `main` exactly once from inside the isolated
  worktree, placing the peer commit between `commit_isolated`'s HEAD snapshot and its
  compare-and-swap) -> the close LANDED: `commit_backlog_close` returned a sha, main's tip equalled
  it, `git log --oneline` showed `probe close` on top of `peer commit`, the item was at `done/`, and
  the tree was clean apart from the probe's own marker file. Recorded explicitly that an earlier probe
  landing the peer commit BEFORE the close was NOT a race (no CAS ever lost) and does not test this.
- **PR-002, THE SEAM MEASUREMENT.** The real `runner_shared.process_backlog_close` called with
  `lane_repo=<live coordinator worktree>`, `lane_handle=None` and real `close_backlog_item` /
  `commit_backlog_close` closers: the record came back `closed: true` with `rule: "ipd"`, both spies
  confirmed the coordinator worktree path was what each closer received, main's porcelain during the
  close contained no backlog path, main's tip did not move, the coordinator branch advanced, and the
  following `land_worktree_commit` returned `reconciled 0` leaving the item at `done/` in main and
  absent from `graduated/`. Also confirmed the verdict is taken against MAIN, since the first run of
  this probe (before the carrier was genuinely earned) was correctly REFUSED with "this run executed
  none of its carriers, so the close was not earned".
- **PR-003, THE UNWRITABILITY MEASUREMENT.** Over one base: shape A (commit authored on main) and
  shape B (coordinator worktree + `merge --ff-only`) both produced `rev-list --parents -1` with a
  single parent and `rev-parse <sha>^` equal to the base. `git reflog show main` differed:
  `commit: close` versus `merge <sha>: Fast-forward`.
- **PR-004, THE MISREPORTING MEASUREMENT.** The coordinator-worktree close recorded
  `"wrote_in": "lane"`. `grep -rn wrote_in tests/` returns no match, and the only producers are the
  `record` construction and the `backlog-item-closed` event payload.
- **F-07's SIDECAR SHAPE CONFIRMED (adjusted detail).** `.aw/.gitignore` does carry
  `records/history.jsonl`, and `lane_containment` does classify exactly that path as discardable with
  the rationale the plan quotes. The coordinator tree's pre-commit porcelain showed the sidecar
  present-and-untracked in every probe, and `commit_backlog_close`'s id6 basename filter excludes it
  structurally, so E-05's requirement is satisfiable as written.
- **F-09 CONFIRMED AS READ.** `reattempt_deferred_integrations` calls
  `integrate_under_repository_lock(...)` and then, on the `if integrated:` branch, calls
  `do_finish(item, handle, reason)` - i.e. the close runs after the lock is released, which is what
  makes PR-001's race reachable rather than theoretical.
- **DEFERRAL ROWS CHECKED.** `integrate_retired_lane`'s `teardown_lane_if_classified` call does
  precede its `process_backlog_close(run_dir, state, item)` call in the same body, and that call is
  NOT guarded by the `backlog_close.closed` predicate, exactly as the plan's row states; its carrier
  `sj4zte` exists at `.aw/records/backlog/open/20260928-reattclose-01-sj4zte-retired-lane-close-writes-main.backlog.md`.
  Carriers `10pcd5`, `lsbd32` and `hf76th` all resolve to real records, and pending plan `9vglxd`
  exists and does declare `agent_workflows/runner_shared.py`, so the stated file overlap is real and
  the plan's reasoning about it (handled by worktree isolation, not an instruction conflict) is
  correct.
- **BOTH-HOSTS CLAIM CONFIRMED.** `retry_deferred_integrations` is defined in `runner_shared` and both
  `oc_runipd.retry_deferred_integrations` and `agy_runipd.retry_deferred_integrations` delegate to it
  with their own `process_backlog_close=process_backlog_close` binding, so E-06 is genuinely one edit
  and E-08's agy-side binding test is genuinely necessary rather than ceremonial.
- Post-revision suite re-check: `python3 -m pytest` -> `2935 passed, 2 skipped, 3 warnings in 45.78s`
  (plus the standard `201 tests were deselected` notice), confirming this review touched no code (it
  edited only the plan and this record).
- `aw sanitize --agent` -> exit 0, no findings.

### Probe scripts

The five probe scripts backing the measurements above were written under
`.aw/workflow-artifacts/plan-review-pjuoyj/` (gitignored, so they are not committed): `probe_land.py`
(the three landing arms plus cleanup and abandoned-object reachability), `probe_close.py` (the real
`commit_backlog_close` inside a coordinator worktree, and which branch its CAS advances),
`probe_raced_today.py` (today's close under a peer commit; a hook rejection inside a coordinator
worktree; today's hook-rejection baseline), `probe_race_retry.py` (three re-merge attempts plus the
rebuild remedy), `probe_true_race.py` (the induced true race against today's path) and
`probe_observable.py` (the graph-identity comparison).

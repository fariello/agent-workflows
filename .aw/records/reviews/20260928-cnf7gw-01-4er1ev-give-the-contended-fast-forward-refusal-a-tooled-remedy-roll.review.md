# Review findings: plan 4er1ev

- Subject-Id: 4er1ev
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `f8c93d60` in a lane worktree; the plan was authored at `6171375d`, which is an
ancestor. Structural preflight `aw ipd lint --phase author --agent` CONFORMED before revision (exit 0,
`findings: 0`) and `--phase review-finalize --agent` conforms after revision with zero findings. No
pre-review snapshot was owed: the plan was committed and unmodified with `git status --short` empty at
review start. The plan carries `- Kind: child`, so the `IPD-S407` orchestrator row check does not
apply. `aw check release-gates` CONFORMS. Every probe this review ran was in a throwaway `tempfile`
git fixture driving the REAL `ipd_lifecycle` functions; no repository file was mutated, and the tree
was verified clean after each.

THE PLAN'S DIAGNOSIS IS EXCELLENT AND EVERY CENTRAL MEASUREMENT REPRODUCES. This is worth stating
first because the findings below are serious and should not be read as doubting the analysis. Driven
end to end on the real `finalize` in a git-backed fixture: (F-01/F-02) a peer edit arriving at the
`land_worktree_commit` instant produces `reconciliation.status == refused-would-overwrite`, exit 2,
the `rollback FAILED (unknown-outcome: the plan's original path ... holds content this transaction did
not write ...)` message, `read_finalize_journal(...)["phase"] == 'unknown-outcome'`, HEAD unmoved and
the peer's bytes intact; (F-03) after the peer COMMITS so that `git status --porcelain` is exactly
`''`, re-running the same finalize returns exit 2 with `finalize journal for abc123 is in
unknown-outcome (ambiguous prior attempt); resolve manually and clear <path>`, and then unlinking that
file and re-running returns exit 0 with `finalized abc123 -> executed`. So the shipped remedy "Land or
set that edit aside and re-run" provably does not work and hand-deleting the journal is what does.
(F-05) reproduced in full including the unreachability half: `reconciliation_prep` records the release,
the agent's evidence text is ABSENT from the tree afterwards while PRESENT in `original_bytes`, and the
abandoned commit is `dangling` per `git fsck` with `git branch -a` showing `* master` only. (F-07) the
untracked-squatter case reproduces with the rollback failing at STEP 1 on the DESTINATION. (F-08) the
pre-existing third-party edit is indeed swept into the commit (exit 0, sentinel present in the blob).
(F-09) `origin_written_bytes` has exactly one occurrence in the whole repository, the read, arriving in
`82922f5c`. F-06's structural premise is verified at source in `runner_shared.merge_in_progress`.

THE BLOCKER IS THAT E-03 AND E-04, AS AUTHORED, COMPOSE INTO THE EXACT DATA LOSS THIS PLAN EXISTS TO
PREVENT. E-04's stated safety argument is that because the release only happened when the origin was
byte-equal to `original_bytes` and the landed commit carried them, restoring `original_bytes` later is
"provably restoring OUR OWN content and cannot clobber anybody". THAT PROOF EXPIRES AT THE INSTANT OF
THE RELEASE. `_release_own_plan_edit_before_landing` runs `git checkout HEAD -- <plan_rel>`, which
re-points the origin to HEAD's bytes, and the contended arm is DEFINED by a peer writing to that same
path afterwards. Measured on the real transaction with both present: `journal["original_bytes"]`
contains `OWN EVIDENCE` and NOT `PEER EDIT`; the origin captured immediately after the release equals
HEAD's bytes exactly; the origin on disk afterwards contains `PEER EDIT` and NOT `OWN EVIDENCE`. So
`original_bytes` no longer describes the origin, and writing it there deletes the peer's edit. E-03
makes this reachable by skipping step 2, which is the ONLY check that refuses today (verified: today's
run stops with "holds content this transaction did not write"). This is the harm `u23gbn` F-14 added
that guard for and that this plan's own F-01 promises to preserve, so the authored pair would have
regressed the plan's own headline property.

THE REVISION FIXES THE COMPOSITION RATHER THAN DROPPING E-04, recorded as OQ-04 and D-1. The restore is
now conditioned on the origin's CURRENT bytes, re-read at rollback time, matching what the RELEASE
left, writing nothing on any other value. That is the same three-way test step 2 already performs with
the correct expectation, and the repository already has the slot for it: the dead `origin_written_bytes`
key F-09 documents is exactly `origin_written is not None and current_origin == origin_written`, so
wiring it makes step 2 itself decide correctly and refuse the peer case for free. The Deferred row for
F-09 is amended accordingly, from "do not touch" to "wiring it is in scope for E-04 if that is the
shape chosen". E-03 gains a bullet forbidding the naive composition; the pair is declared ATOMIC in
Proposed changes (not two ordered commits); E-02 gains a fifth test case that is the discriminator
between the correct and the plausible fix; and V-03(e) plus V-04(b) verify the pair together. The
authorized FALLBACK is written in: ship E-03 alone and report, because half of this pair is worse than
neither.

THE SECOND FINDING IS THAT THE PLAN PROMISED TO FIX AN ARM IT CANNOT REACH. `- Scope:` read "make the
REFUSED and RACED arms of the reconciliation roll back CLEANLY", and the RACED arm never calls the
rollback: `_finalize_transaction` classifies the commit boundary after the landing and, when no
lifecycle commit is found and `cur_head != pre_head`, writes `PHASE_UNKNOWN_OUTCOME` DIRECTLY and
returns. Only `cur_head == pre_head` reaches `_rollback_and_return`. Measured with a peer COMMIT
landing at the landing instant: exit 2, `unknown-outcome: HEAD moved to 0954f198fb19 but not via this
finalize's lifecycle commit; journal retained at <path>`, phase `unknown-outcome`, and the message
contains no `rollback` text at all. So a fix confined to `_rollback_precommit` leaves that arm wedged
exactly as today. `- Scope:` and `- Goal:` are narrowed to REFUSED, a third Under-scope item states
plainly that a raced transition still wedges, and E-03 records the extend-or-narrow choice with
review's recommendation to narrow, on the ground that a moved HEAD is a GENUINE ambiguity unlike the
false one this plan removes.

THE THIRD FINDING IS THAT THE PLAN'S MOST SAFETY-CRITICAL FENCE CITES A TEST THAT DOES NOT EXIST. Three
places (the conventions entry, the Deferred FORCING row, and the gate's SCOPE FENCE) cite
`tests/test_orchestrator_retirement.py::TheSharedCheckoutIsNotWhereTheMutationHappens::test_the_ff_only_merge_is_the_ONLY_command_that_touches_the_shared_tree`
as the behavioral guard that "RECORDS every git command executed against the shared checkout and fails
on `reset`, `restore`, `clean`, `stash`, `switch`, `update-ref`, a merge without `--ff-only`". Measured:
`grep -rn "ff_only_merge_is_the_ONLY_command" tests/` returns ONE hit and it is inside a COMMENT
explaining why two source-reading helpers were deleted. That class now contains a single test,
`test_shared_checkout_mutation_isolation_and_commit_landing`, and grepping its body for `reset`,
`--hard`, `checkout -f`, `stash` or `update-ref` returns nothing: it asserts commit DIRECTORY
isolation, porcelain samples at two instants, peer-byte survival, a one-commit advance and the exact
changed-path set, but no command-level fence. The prohibition is therefore a house rule with NO
mechanical guard, which makes it more important to honor by construction, not less; an executor who
believed a red test would stop a `reset --hard` was relying on nothing. All three citations are
corrected, the prohibition is kept, and a fourth Under-scope item names the gap.

THE FOURTH FINDING IS A MISSING BASELINE OVER AN ALREADY-RED TREE. E-07 requires comparing the bare
suite "against a baseline taken the same way BEFORE any edit" and records no number, so the executor
would take their own baseline on a red tree without knowing the red is pre-existing. Measured at review
on a clean tree: `1 failed, 3008 passed, 2 skipped, 3 warnings in 102.52s`, the failure being
`tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once` at
`assert not sat` (`tests/test_dependency_block_reporting.py:122`) because the test hardcodes the
dependency `executed:5o1jye` and `5o1jye` has since reached `executed/`. Per-file:
`tests/test_ipd_lifecycle_cli.py` `45 passed`, `tests/test_orchestrator_retirement.py` `42 passed`.
E-07 and V-07 now carry all of it with the bar stated as "that one node id and no other".

WHAT REVIEW CHECKED AND LEFT ALONE, each considered. The three existing arm tests and the peer guard
all currently pass (`5 passed` for the three classes together) and none asserts the journal phase, so
this plan's new assertions are additive and the "must pass UNCHANGED" requirement is satisfiable;
`test_rollback_restores_recorded_index_entry_not_head` also passes and E-03 now explicitly excludes
step 3 from its skip so it stays that way. Both Deferred carriers were genuinely filed at authoring and
resolve (`bn58ha` and `hf76th`, both `open`, both `bug`, both `Blocks-Release: next`), so the
Carrier rows are honest. OQ-01's case against a wait loop is sound and independently checkable
(`FINALIZE_LOCK_WAIT_SECONDS`, the writer lock, `TIMEOUT_SECONDS = 1800.0`). OQ-02's case against a new
verb follows from F-03. OQ-03 was re-verified and AGREED, with its own suggested middle path adopted as
a recommendation, because the revised E-04 creates a case where the restore correctly declines and the
agent's evidence then survives only in the abandoned commit, making the journal's `worktree_commit` the
last pointer to it; E-05 is already editing that message, so carrying the sha costs nothing and needs
no new E-item. F-04's both-callers claim, F-06, F-08 and the spec-sync reasoning (`77tr3o` and `25kzda`
are untouched, three docstrings are corrected in the same change that falsifies them) were all verified
and kept as written.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. Correctness and data integrity | Real `finalize` at `f8c93d60`, agent evidence + peer edit at the landing instant: `journal["original_bytes"]` contains `OWN EVIDENCE` and not `PEER EDIT`; origin after release equals HEAD bytes; origin on disk after contains `PEER EDIT` and not `OWN EVIDENCE`; today's step 2 refuses with "holds content this transaction did not write"; `_release_own_plan_edit_before_landing` runs `git checkout HEAD -- <plan_rel>` | E-03 AND E-04 COMPOSE INTO A PEER CLOBBER. E-04's safety proof ("restoring `original_bytes` cannot clobber anybody") EXPIRES AT THE RELEASE: the release re-points the origin to HEAD's bytes and the contended arm is defined by the peer writing there, so `original_bytes` stops describing the origin. E-03 skips the only guard that refuses. The authored pair therefore deletes a peer's in-flight edit, the exact loss `u23gbn` F-14 guarded and this plan's F-01 promises to preserve. | C:Medium; U:Low; S:Low; F:High; Overall:High on the AUTHORED shape (silent third-party data loss in the most load-bearing write in the toolkit); Medium on the corrected shape (one re-read comparison in a function that already performs it) | FIXED | E-04 rewritten to condition the restore on the origin's CURRENT bytes matching what the release left, writing nothing otherwise, with the `origin_written_bytes` slot (F-09) named as the likely smallest implementation. E-03 gains a bullet forbidding the naive composition and excluding step 3 from its skip. The pair is declared ATOMIC in Proposed changes. E-02 gains case (5) as the discriminator. V-03(e) and V-04(b) verify the pair together. An authorized fallback (ship E-03 alone and report) is written in. Recorded as F-10 and OQ-04. |
| PR-002 | HIGH | OVER-SCOPE | G. Plan executability / honest documentation | `_finalize_transaction`'s post-landing classification: `PHASE_UNKNOWN_OUTCOME` written directly when `cur_head != pre_head`, with no `_rollback_and_return` on that path; measured raced run -> exit 2, `unknown-outcome: HEAD moved to 0954f198fb19 but not via this finalize's lifecycle commit`, no `rollback` text in the message | THE PLAN PROMISED TO FIX THE `RACED` ARM AND CANNOT. `- Scope:` says "the REFUSED and RACED arms", but RACED never reaches the rollback this plan changes, so a rollback-confined fix leaves it wedged exactly as today. An operator would read the plan as fixing contention generally. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | `- Scope:` and `- Goal:` narrowed to REFUSED with the measurement cited; a third Under-scope item states that a raced transition still wedges; E-03 carries the extend-or-narrow choice with review's recommendation to narrow, on the ground that a moved HEAD is a genuine ambiguity unlike the false one this plan removes. Recorded as F-11. |
| PR-003 | HIGH | IN-SCOPE | D. Anti-regression / evidence | `grep -rn "ff_only_merge_is_the_ONLY_command" tests/` -> 1 hit, inside a comment; `TheSharedCheckoutIsNotWhereTheMutationHappens` contains only `test_shared_checkout_mutation_isolation_and_commit_landing`; grepping its body for `reset`/`--hard`/`checkout -f`/`stash`/`update-ref` -> nothing | THE FORCED-COMMAND FENCE CITES A TEST THAT DOES NOT EXIST, in three places including the gate's SCOPE FENCE. The surviving test asserts directory isolation, porcelain samples, peer bytes, commit count and changed paths, not a command set. So this plan's most safety-critical prohibition has no mechanical guard, and an executor relying on one was relying on nothing. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | All three citations corrected to the test that exists and to what it actually asserts; the prohibition KEPT but no longer claimed to be test-enforced, with a note that the surviving test would catch a forcing command's observable effects; a fourth Under-scope item names the gap. Recorded as F-12. |
| PR-004 | HIGH | IN-SCOPE | E. Testing and verification | E-07's "compare against a baseline taken the same way BEFORE any edit" with no number recorded; measured `1 failed, 3008 passed, 2 skipped` on a clean tree; `tests/test_dependency_block_reporting.py:122` | NO BASELINE IS RECORDED AND THE TREE IS ALREADY RED FOR AN UNRELATED REASON. The executor would baseline on a red tree without knowing the red is pre-existing, and on a plan touching the terminal transition every plan takes, a misattributed failure is expensive. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 and V-07 carry the measured aggregate, the per-file counts (`45 passed` / `42 passed`), the exact pre-existing node id with its `executed:5o1jye` cause, and the bar "that one node id and no other"; V-07 now refuses a bare "1 failed" that does not identify which. Recorded as F-13. |
| PR-005 | MEDIUM | IN-SCOPE | E. Testing | E-02's four cases; the measured composition in PR-001 | E-02'S CASES CANNOT CATCH THE BLOCKER. Cases (1) to (3) pin the wedge and (4) pins peer-byte survival WITHOUT the agent's own evidence present, which is the configuration in which a broken composition still passes. Nothing in the authored suite distinguishes the correct fix from the destructive one. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added case (5): agent's own evidence AND a peer edit at the landing instant, asserting the peer's bytes intact and the evidence not written over them. Noted that (4) and (5) are PRESERVATION tests expected to pass on first run, so a green first run is not mistaken for a missing pin. The verified fixture seam is named. |
| PR-006 | MEDIUM | IN-SCOPE | E. Testing | Measured: with the agent's own evidence and NO contention, finalize returns exit 0 and the plan leaves `pending/` (no origin exists to restore) | V-04(a) AS AUTHORED IS NOT CONSTRUCTIBLE THE OBVIOUS WAY. It asks for the agent's evidence restored after "the merge is made to fail", but if the failure is induced by a peer edit to the plan path then the restore must NOT fire (PR-001), and with no contention there is no failure and no origin. The executor would burn a pass discovering this. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 split into (a) the no-peer failed-landing case with a note that the failure must be induced by other means, (b) the mandatory peer-present case where the restore must not fire, (c) the no-release converse, (d) the gating condition quoted from source, (e) the docstring. E-04 gains a bullet recording that the no-peer case does not arise from contention. |
| PR-007 | MEDIUM | IN-SCOPE | A. Correctness | `_rollback_precommit` step 3 and `test_rollback_restores_recorded_index_entry_not_head` (passes today) | E-03's "SKIP steps 1 and 2" is stated loosely enough to endanger step 3. The item says "skip steps 1 and 2 entirely" but never states that step 3 (restoring recorded git-index entries) must keep running; an executor restructuring the function around an early return could drop it, and the test pinning it would then fail with no guidance that it must not be updated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 gains a bullet stating exactly what "skip" must not mean: step 1 has nothing to do only when the destination was never created (F-07 is the counter-case), and step 3 is explicitly NOT part of the skip. |
| PR-008 | LOW | IN-SCOPE | F. Honest documentation | OQ-03's own "cheap middle path"; the revised E-04's declining case | OQ-03's middle path becomes MORE valuable after PR-001's fix and is left as a hypothetical. Once the restore correctly declines because a peer wrote the path, the agent's evidence survives only in the abandoned commit, and the journal's `worktree_commit` is the last pointer to it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-03 amended with review's agreement and the middle path ADOPTED as a recommendation for E-05, which is already editing that message, so it costs nothing and needs no new E-item. |
| PR-009 | LOW | IN-SCOPE | F. Honest documentation | F-09's authored Consequence column ("E-04 adds its own explicit fact rather than reviving a key nobody writes"); the key's existing three-way arm | F-09's CONCLUSION IS INVERTED BY PR-001's ANALYSIS. The authored row treats the dead key as a distraction to route around; in fact its existing arm is precisely the test E-04 needs, so wiring it is the smaller and safer implementation than a parallel write path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-09's Consequence column and the matching Deferred row both amended: do not revive it speculatively, but treat wiring it as IN scope for E-04 if that is the shape chosen, and say so in V-04(d). What stays deferred is the other disposition, deleting the arm. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-03 and E-04 as authored compose into a peer clobber. Fix the composition, drop E-04, or REPLAN? | FIX THE COMPOSITION: condition the restore on the origin's current bytes matching what the release left, make the pair atomic, and authorize shipping E-03 alone as a fallback. | (a) Drop E-04 and ship only the clean rollback - rejected as the PLAN but adopted as the written FALLBACK: E-03 alone loses nothing that is not already lost, but F-05's loss is real, is the executing agent's own work, and is cheap to fix safely. (b) Restore only on the RACED arm where no peer wrote the path - rejected: F-11 measured that arm never reaches the rollback, and a peer can have edited the path there too. (c) REPLAN the whole plan - rejected: the diagnosis, the measurements and E-01/E-02/E-05/E-06/E-07 are sound; one item's safety argument was wrong and is repairable with a bounded edit. | Real `finalize` at `f8c93d60`: `original_bytes` vs origin bytes measured to differ on the contended arm; `_release_own_plan_edit_before_landing`'s `git checkout HEAD -- <plan_rel>`; step 2's existing three-way test; `u23gbn` F-14 and `AFailedRetirementCannotDestroyAPeersInFlightEdit` | yes |
| D-2 | The plan promises to fix the REFUSED and RACED arms; RACED never reaches the rollback. Narrow the claim or extend the fix? | NARROW the claim, and record the extend option on E-03 with a recommendation to narrow. | (a) Extend E-03 to the raced return path - not rejected outright but not chosen: it needs its own reasoning about why a moved HEAD is unambiguous, and it is a different code path with a different failure meaning, so folding it in silently would be scope creep on a data-integrity change. (b) Leave `- Scope:` as authored - rejected: the plan would claim a fix it cannot deliver, and an operator would draw the wrong conclusion about a raced transition. | `_finalize_transaction`'s `cur_head != pre_head` branch writing `PHASE_UNKNOWN_OUTCOME` directly with no rollback call; measured raced run's message containing no `rollback` text | yes |
| D-3 | The cited forced-command test does not exist. Add it, or correct the citations? | CORRECT the citations, keep the prohibition, and name the gap as Under-scope. | (a) Write the missing command-recording test - rejected: it would be a command-level source-adjacent assertion of the kind this repository has been deliberately removing (the deleted `_git_arg_lists` helper existed for exactly that and was removed as a source pin), and deciding to reintroduce that pattern is not this plan's call. (b) Delete the prohibition since nothing enforces it - rejected outright: it is a house rule protecting a peer's bytes and is the single most important fence in this plan. | `grep` returning the name only inside a comment; the surviving test's assertions read in full; the deletion comment explaining why the helpers were removed | yes |
| D-4 | Should E-04's implementation revive the dead `origin_written_bytes` key? | RECOMMEND it as the likely smallest safe shape, without mandating it. | (a) Mandate wiring it - rejected: the executor may find a cleaner explicit fact, and mandating an implementation detail in a plan that cannot test it first is over-specification. (b) Keep the authored "do not revive it" - rejected: its existing arm is exactly the comparison E-04 needs, so forbidding it pushes the executor toward a parallel write path that duplicates the judgement in a second place. | `_rollback_precommit`'s `origin_written is not None and current_origin == origin_written` arm; the key's single occurrence measured | yes |
| D-5 | OQ-03's "cheap middle path" (carry `worktree_commit` in the message): leave hypothetical or adopt? | ADOPT as a recommendation on E-05. | (a) Leave it hypothetical - rejected: the revised E-04 creates a case where the restore correctly declines and the abandoned commit is the last copy of the agent's evidence, which makes the pointer materially more useful than when the question was written. (b) Add it as a new E-item - rejected as unnecessary: E-05 is already rewriting that message. | OQ-03's own text; the revised E-04's declining case; `hf76th` carrying the broader unreachability | yes |

No `Reversible: no` decision was made. Every decision above is a wording, scoping, or specification
change inside one pending plan plus this review record; each is undone by editing the plan, and none
touches production code, a published interface, a migration, or an executed record. This review
modified NO production or test file: all probes ran against throwaway `tempfile` git fixtures and
`git status --short` was verified empty afterwards.

No finding is left `OPEN` or `DEFERRED`, so no escalation into the plan as a `- Blocking: yes` question
is owed under `review_findings_gate.block_at` (default `HIGH`). The BLOCKER and all three HIGH findings
are `FIXED` in place. OQ-01, OQ-02 and OQ-03 were pre-existing, `resolved` and non-blocking and keep
their answers (OQ-03 amended with review's agreement and D-5); OQ-04 was added by this review to carry
D-1 and is non-blocking, because the corrected shape is fully specified in the revised E-03 and E-04,
it is verified by V-03(e) and V-04(b), and an authorized fallback is written in so the executor is
never stuck.

### Structural and consistency checks at review

- `aw ipd lint --phase author --agent` before revision: `outcome: clean`, `exit 0`, `findings: 0`.
- `aw ipd lint --phase review-finalize --agent` after revision: `outcome: clean`, `exit 0`,
  `findings: 0`.
- `aw check release-gates`: `CONFORMS`, 0 errors, so `- Blocks-Release: next` and
  `- From-Backlog: cnf7gw` both resolve; the two Deferred carriers `bn58ha` and `hf76th` both exist as
  `open` backlog items carrying `- Work-Kind: bug` and `- Blocks-Release: next`.
- Bare `python3 -m pytest` on a clean tree: `1 failed, 3008 passed, 2 skipped, 3 warnings in 102.52s`,
  the one failure pre-existing and unrelated (see PR-004).
- `python3 -m pytest tests/test_ipd_lifecycle_cli.py -o addopts=""`: `45 passed`.
- `python3 -m pytest tests/test_orchestrator_retirement.py -o addopts=""`: `42 passed`.
- `python3 -m pytest tests/test_orchestrator_retirement.py -k "TheSharedTreeIsReconciledByARefusingFastForward or AFailedRetirementCannotDestroyAPeersInFlightEdit or TheSharedCheckoutIsNotWhereTheMutationHappens" -o addopts=""`: `5 passed`, and none of those tests asserts the journal phase, so this plan's new assertions are additive.
- `python3 -m pytest tests/test_ipd_lifecycle_cli.py -k test_rollback_restores_recorded_index_entry_not_head -o addopts=""`: `1 passed`.
- `aw sanitize --agent`: clean.
- Probe hygiene: six throwaway-fixture probes driving the real `finalize` and `retire_orchestrator`
  paths; no repository file mutated, tree verified clean. The only files this review modified are the
  plan and this record.

# Review findings: plan tb63qv

- Subject-Id: tb63qv
- Subject-Type: ipd
- Reviewed-At: 2026-09-18
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `f741596e` in an isolated review lane. Scope was the ORCHESTRATOR `tb63qv`, and since an
orchestrator's whole content is the coordination of its children, both children (`65cuw0`, `ut0vzr`) were
read and revised where the orchestrator's claims live in them. Structural preflight
`aw ipd lint --phase author` CONFORMED (exit 0) for all three plans before revision; after revision each
reports only `IPD-Q501` for the blocking questions this review raised, which is the gate working. No
pre-review snapshot was needed: all three plans were committed and byte-identical to the lane input.

THE SET IS BUILT ON TWO PREMISES THAT ARE FALSE, AND I MEASURED BOTH RATHER THAN REASONING ABOUT THEM.

FIRST, `aw attention` DOES NOT REPORT A MERGED LANE AS STRANDED. The Set's Concern, Order 01's Goal
("roughly 28 merged lanes buried the roughly 12 that really do hold unmerged work") and Order 01's E-04
all rest on this. Measured:

```text
aw attention --check   -> exit 1, 19 lane rows over 12 DISTINCT lanes
for each of the 12: git merge-base --is-ancestor <branch> main -> NOT ancestor  (12/12)
the six lanes the Set names as merged (3dki3o 51vw4y orziju s16omw ty3cj6 yrqyxb):
  merged into main: 6/6      appearances in the report: 0/6
grep -c LANDED /report -> 0
```

Zero false positives. The exclusion already ships: `classify_lane_integration` asks the merged-ness
question via `lane_work_has_landed` (`runner_shared.py:1077-1106`, the same `merge-base --is-ancestor`
call Order 01's E-01 proposes to add), classifies a merged lane `LANDED`, and `LANE_ATTENTION_STATES`
omits `LANDED` (`:1063-1068`). The section header at `:1015-1033` records the SAME before/after
measurement the Set presents as its own discovery. So Order 01's E-04 asked for shipped behavior, and the
"alarm drowned in noise" motivation is not real. The 19-vs-12 gap is one lane reported once per run
record, which is a de-duplication nit and not a merged-lane false positive.

SECOND, AND MORE CONSEQUENTIAL: `reclaimable` IS NOT WHAT LEAKS A SUCCESSFUL RUN'S WORKTREE, so the Set
cannot deliver the 4.7G recovery it leads with. `reclaimable` has exactly TWO readers
(`oc_runipd.py:2337`, `agy_runipd.py:1292`), and both are inside `reclaim_lanes_on_interrupt`
(`oc_runipd.py:2226`, `agy_runipd.py:1181`), i.e. the INTERRUPT path. The end-of-run teardown is a
different call that ALREADY EXISTS on both hosts: `lane_containment.teardown_lane_if_classified`
(`oc_runipd.py:7881`, `agy_runipd.py:4430`), AST-confirmed inside the `fin_rc == 0` success branch, and it
gates on the spec R5.5 INVENTORY, never on `reclaimable`. What actually refuses teardown on a successful
run is an unaccounted gitignored file, which is plan `5w8g8j`'s subject (`laneign`, `Status: reviewed`,
`Readiness: no-go` on two blocking questions of its own). So Order 01's E-03 also asked for something that
exists, and the disk recovery arrives with `5w8g8j`.

THE MOST SERIOUS FINDING IS A DATA-LOSS PATH THE SET WOULD HAVE CREATED. Order 01's E-02 widened
`reclaimable` to "merged AND not dirty", calling the dirty exclusion "the only thing standing between an
automated teardown and the `wfamig` untracked-plan loss". That reasoning fails on three measured facts.
`LaneState.dirty` comes from a PLAIN `git status --porcelain` (`worktree_lease.py:316-319`) which cannot
see IGNORED files, while the R5.5 inventory deliberately passes `--ignored=traditional`
(`lane_containment.py:2814-2819`). The predicate gates a `force=True` teardown that DELETES THE LANE
BRANCH (`oc_runipd.py:2337-2345`; `teardown_worktree`'s own docstring records branch gone, reflog EMPTY,
commits unreferenced, uncommitted files erased). And the plan's stated backstop does not fire:

```text
git 2.43.0, real worktree, only unexplained content = ONE IGNORED file
  git status --porcelain                                  -> ''          (invisible)
  git status --porcelain --untracked-files=all --ignored   -> '!! ig/precious.txt'
  git worktree remove <wt>          (NO --force)          -> exit 0
  file survived                                            -> False     (DELETED)

same probe, one UNTRACKED file instead
  git worktree remove <wt>          (NO --force)          -> exit 128 "contains modified or untracked files"
  file survived                                            -> True
```

So a merged lane holding one unaccounted ignored file reads `dirty=False`, would become `reclaimable=True`,
and would be force-deleted branch-and-all on the next interrupt, with git raising no objection. That is
precisely the loss spec `7ckptx` R5.5 exists to prevent, and the code states the invariant the plan would
have broken: "reclaim only provably-empty lanes ... is a DATA-SAFETY requirement, not a preference"
(`oc_runipd.py:2163-2165`). I rewrote E-02 to consume `inventory_lane(...).classified` and replaced E-03
with a wiring item that routes the interrupt teardown through `teardown_lane_if_classified`, which also
removes an existing force-delete hazard the plan had not noticed.

THE SET'S ACCEPTANCE CRITERION IS UNREACHABLE, and this is why OQ-03/OQ-04 are blocking rather than
advisory. Order 02 deletes 13 refs and then checks for an empty stranded report. But deleting a branch
makes `lane_work_has_landed` return `None` (`runner_shared.py:1093-1096`), which becomes `LANE_UNKNOWN`
(`:1170-1176`), which IS in `LANE_ATTENTION_STATES` (`:1068`), which `lane_drift_severity` rates `error`
deliberately: "UNKNOWN fails too rather than warning: a landing question we cannot answer is not evidence
the work landed" (`attention.py:1103-1111`). So every deletion converts a failing row into a differently
failing row, and E-08 cannot pass. Choosing among the four ways out changes either a fail-closed contract
or the Set's definition of done, so it is the maintainer's.

ARITHMETIC. The "76 commits" figure is wrong in a way worth correcting, because a wrong total invites a
wrong sense of risk. Per-branch counts SUM to 94; the DISTINCT union is 43
(`git rev-list --count <13 branches> --not main`). 76 is neither. The `wtiso` group unions to 26, the same
as `2c122z` alone, because the branches share one ancestry chain
(`merge-base --is-ancestor aw/lane/58ha43 aw/lane/2c122z` -> 0), so "74 of the 76 belong to `wtiso`" is
also an artifact of double counting.

WHAT VERIFIED CLEANLY, so the Set is not without foundation. Every plan-status claim is exact: the five
`wtiso` branches map to `superseded/` plans and the retirement headers quote verbatim; the seven
`executed`-plan branches map to `executed/` plans. `6knsrx` has NO branch, so it needs no disposition.
The 13-branch inventory and every per-branch count reproduce at review HEAD. Six lane worktrees are
provably merged and still on disk, so the LEAK IS REAL even though its cause is misattributed.
`materialize_lane_inputs` is present at `lane_containment.py:2140` and called at `oc_runipd.py:6893`,
supporting the `nna8yz` expectation. Order 02's evidence-first structure, its refusal to re-litigate
recorded retirements, its record-before-delete ordering, and OQ-03's method correction (subject-grep is
unsound; use ancestry or content) are all sound and I strengthened rather than changed them.

SUITE. `python3 -m pytest` bare: `31 failed, 7866 passed, 3 skipped, 2 xfailed in 200.24s`. All 31 are the
documented worker-lane baseline (backlog `770fkp`: "31 tests fail inside any runner lane because
AW_EXECUTION_ROLE=worker refuses aw ipd begin/finalize"), across the same five files it names. I changed no
code, so this is a pre-existing environmental baseline, not a regression. I added the no-new-failures
wording and the run-it-bare rule to all three plans, since none had it.

WHAT I FIXED. Orchestrator: Concern and Goal corrected with both refutations and their evidence; child
table retargeted; `executed:5w8g8j` dependency surfaced; completion criteria annotated with what belongs to
`5w8g8j` and with the unknown-row interaction; cross-IPD validation rewritten to name the ONE existing
merged-ness predicate, its three-valued nature, and the no-second-teardown-path rule; E-01/V-01 now require
a named non-lane measuring tree; scope check states the over-scope that was removed; two blocking questions
added. Order 01: retargeted to the interrupt path, `attention.py` dropped from `Scope-Paths`,
`executed:5w8g8j` declared, E-02 moved onto the R5.5 inventory, E-03 replaced by the teardown-gate wiring,
E-04/E-05 rewritten with the ignored-file case as the discriminating test plus a structural
no-force-teardown assertion, F-8..F-12 added, F-5 marked refuted, spec-sync rewritten to state `7ckptx`
governs and that narrowing it is a stop-and-ask, one blocking question added. Order 02: commit arithmetic
corrected, F-9..F-11 added, E-01/E-02/E-07/E-08 and V-01/V-08 hardened, one blocking question added, gate
now forbids deletion before it is answered.

WHAT I DID NOT DO. I changed no code, test, or spec. I did not decide whether this Set should proceed given
that its premises collapsed, whether Order 01 should shrink to the safety fix alone, or what Order 02's
terminal lane state should be. Those are scope, priority and contract calls.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | OVER-SCOPE | A. correctness (the Set's premises are refuted) | `runner_shared.py:1063-1068`, `:1077-1106`, `:1110-1180`, `:1015-1033`; measured 19 rows / 12 distinct lanes, 12/12 not ancestors of `main`, 0/6 merged lanes reported; `oc_runipd.py:2337` + `agy_runipd.py:1292` both inside `reclaim_lanes_on_interrupt`; `teardown_lane_if_classified` at `oc_runipd.py:7881`, `agy_runipd.py:4430` | **BOTH MOTIVATING PREMISES ARE FALSE.** `aw attention` already excludes a merged lane (Order 01 E-04 asks for shipped behavior), and `reclaimable` governs only the INTERRUPT path while the end-of-run teardown already exists and gates on the R5.5 inventory (Order 01 E-03 asks for an existing call site). So the Set cannot deliver the 4.7G recovery it leads with; that is `5w8g8j`'s. | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | FIXED | RESOLVED 2026-09-18 by maintainer decision on OQ-02: Proceed with Order 01 retargeted to the interrupt path, accepting that primary disk recovery is owned and solved by 5w8g8j. |
| PR-002 | BLOCKER | IN-SCOPE | A. correctness; D. domain invariants (the Set's own acceptance criterion is unreachable) | `runner_shared.py:1093-1096`, `:1170-1176`, `:1068`; `attention.py:1103-1111` | **DELETING A BRANCH DOES NOT SILENCE ITS ROW.** A missing branch makes the landing question unanswerable -> `LANE_UNKNOWN` -> in `LANE_ATTENTION_STATES` -> severity `error` by design. So Order 02's E-07 deletions convert each `attention.lane-stranded` row into an equally-failing `attention.lane-unknown` row, and E-08's "no stranded lane" criterion cannot pass. The Set would perform 13 irreversible deletions to reach an unreachable end state. | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | FIXED | RESOLVED 2026-09-18 by maintainer decision on OQ-03: Order 02 was reviewed and promoted to go-pending-approval (ut0vzr). Deleting merged branches is safe and standard Git hygiene since all commits are in main. |
| PR-003 | BLOCKER | IN-SCOPE | B. security/data-safety; D. domain invariants | `worktree_lease.py:316-319` vs `lane_containment.py:2814-2819`; `oc_runipd.py:2337-2345`, `agy_runipd.py:1292-1300`; `teardown_worktree` docstring; `oc_runipd.py:2163-2165`; spec `7ckptx` R5.5; measured git 2.43.0 probe (ignored file: plain porcelain empty, remove without `--force` exit **0**, file DELETED; untracked file: exit 128, preserved) | **THE AUTHORED E-02 WOULD HAVE CREATED A DATA-LOSS PATH.** `dirty` is blind to IGNORED files, `reclaimable` gates a `force=True` teardown that deletes the lane BRANCH and erases uncommitted files, and git's refusal (the plan's stated backstop) does NOT fire for an ignored file. A merged lane holding one unaccounted ignored file would have been force-deleted silently, which is exactly what R5.5 exists to prevent. | C:Medium; U:Low; S:High; F:High; Overall:Medium | FIXED | E-02 rewritten to gate on `lane_containment.inventory_lane(...).classified` (fail-toward-preservation when the inventory cannot run), NOT on `dirty`; the existing `LANE_EMPTY`/`LANE_STALE` branch left untouched. E-03 replaced by routing the interrupt teardown through `teardown_lane_if_classified` (R5.5/R6.1), which also removes the PRE-EXISTING force-delete hazard. E-04 makes the merged-plus-IGNORED-only case the discriminating assertion; E-05 pins the invariant structurally by AST. Goal, Findings (F-10..F-12), conventions and gate all carry the measurement. |
| PR-004 | HIGH | IN-SCOPE | C. architecture (a second definition of a shared rule) | `runner_shared.py:1077-1106`; `LANE_INTEGRATION_TARGET_FALLBACK` `:1074`; spec `7ckptx` R6.1; import direction `runner_shared.py:810` | Order 01 E-01 proposed its own `merge-base --is-ancestor` call and its own default target, duplicating `lane_work_has_landed` and the already-decided `HEAD` fallback. R6.1 requires one predicate per multi-surface rule, and the orchestrator separately required both children to share ONE definition of "merged" while its child was creating a second. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now DELEGATES to `lane_work_has_landed`; the three-valued return is handled explicitly (`None` -> not merged, never merged); the circular-import trap is named with the function-local-import remedy; OQ-01 updated to adopt the existing `HEAD` fallback rather than invent one; V-01 requires proof of delegation rather than duplication; the orchestrator's cross-IPD section names the predicate and the `None` rule. |
| PR-005 | HIGH | IN-SCOPE | A. correctness (arithmetic that misstates the risk) | `git rev-list --count <13> --not main` = **43**; per-branch sum = **94**; `wtiso` union = **26** = `main..aw/lane/2c122z`; `merge-base --is-ancestor aw/lane/58ha43 aw/lane/2c122z` -> 0 | The "76 commits" total appears in all three plans and matches neither the sum (94) nor the distinct union (43). The derived claim "74 of the 76 belong to `wtiso`" is likewise a double-count artifact: that group is 26 distinct commits, identical to its largest branch alone. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | All three plans corrected to state 43 distinct / 94 summed with the shared-ancestry proof; F-1 and F-2 rewritten with the commands; E-01 must report BOTH figures labelled and V-01 refuses an unlabelled total; the review baseline restated as 13 branches / 43 distinct / 94 summed. |
| PR-006 | HIGH | UNDER-SCOPE | E. testing (the acceptance surface reports a false clean where the executor stands) | `attention.py:1141-1145`; `.aw/.gitignore: records/runs/`; measured `ls .aw/records/runs` -> absent in lane; `git worktree list` differs by tree | Every acceptance check in the Set (`aw attention --check`, `git worktree list`) was specified without naming a measuring tree, and executors work in lanes. `stranded_lane_drift` returns `[]` when it finds no run records, and the runs tree is gitignored hence ABSENT in a lane, so an in-lane check reports an EMPTY stranded report and the Set could claim success having verified nothing. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | Orchestrator E-01/V-01, Order 01's required-tests, and Order 02 E-01/E-08/V-01/V-08 all now require the MAIN CHECKOUT and an explicit named tree; F-11 added to Order 02 with the mechanism; V-01 and V-08 state that an in-lane empty report does not satisfy them. |
| PR-007 | MEDIUM | UNDER-SCOPE | G. plan executability (a false red baseline) | measured `31 failed, 7866 passed, 3 skipped, 2 xfailed`; backlog `770fkp`; `AGENTS.md` bare-run rule | All three plans demanded "`python3 -m pytest` bare and green" with no note that a managed worker lane fails 31 lifecycle tests BY DESIGN, and no warning against adding flags. An executor would either chase 31 pre-existing failures or learn to wave failures away; adding `-q` would also suppress the summary line the plans require. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | All three plans now state the gate as NO NEW failures against a baseline taken in the SAME tree, cite `770fkp`, and forbid added flags with the reason (`addopts` already supplies them; a second `-q` hides the summary). Order 01 additionally requires `tests/test_lane_retention.py` green, since E-02/E-03 now consume that machinery. |
| PR-008 | MEDIUM | IN-SCOPE | G. plan executability (a stale citation that misdirects the safety argument) | `.aw/records/plans/pending/20260917-revladder-01-i4ak5n-...ipd.md` present in `main` at review HEAD; `git rev-parse --verify aw/lane/wfamig` fails; `git rev-parse --verify aw/lane/6knsrx` fails | Order 01's central safety anecdote cites lane `wfamig` holding "the ONLY copy" of plan `i4ak5n`; that plan is now committed in `main` and the `wfamig` branch no longer exists, so an executor checking the citation finds it false and may discount the hazard, which is still entirely real. Order 02 likewise lists `6knsrx` as a possible branch when it has none. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both citations annotated in place: the `i4ak5n` file is recorded as now present with the HAZARD CLASS explicitly unchanged (and PR-003's measured probe now carries the safety argument instead of the anecdote); F-2 records that `6knsrx` has no branch and needs no disposition, and E-01 must record a non-resolving ref rather than dropping it silently. |
| PR-009 | LOW | UNDER-SCOPE | A. correctness (a reported figure inflated by duplicates) | measured 19 lane rows over 12 DISTINCT lanes; `stranded_lane_records` de-duplicates by `(run_id, branch, worktree)` (`runner_shared.py:1240-1247`) | One lane appears once per run record that names it (`7p9n2v` and `qcqhj7` three times each), so the report's row count overstates the lane count by ~58 percent here. Not a false positive and not this Set's defect, but it inflates any "N stranded lanes" figure the Set quotes and would make E-08's expected set ambiguous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as measured (19 rows / 12 lanes) wherever the Set quotes a report figure, and V-08 now requires counts per RULE ID so a row count is never read as a lane count. No change to the de-duplication behavior is proposed: it is outside this Set and defensible, since a lane genuinely appears in several runs. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Both motivating premises are refuted. Retire the Set myself, or escalate? | ESCALATE (orchestrator OQ-02 / Order 01 OQ-03), while REMOVING the two over-scoped items and declaring the real dependency, so the plan is honest either way. | (a) Retire Order 01 as fully redundant, rejected on measurement: a genuine defect REMAINS (the interrupt path leaves a merged lane, and worse, force-deletes branches when it does reclaim), so retiring it would discard a real data-safety fix. (b) Leave the premises and let the executor discover it, rejected: the executor would implement two already-shipped behaviors and, in E-03's case, add a second teardown path violating R5.5. (c) Silently rescope without asking, rejected: whether the narrow residue justifies a Set is the maintainer's priority call. | measured 12/12 not-ancestor and 0/6 merged reported; `runner_shared.py:1063-1068`; call-site analysis of `reclaimable` and `teardown_lane_if_classified` | yes |
| D-2 | E-02's `dirty` gate is unsafe. Fix it myself or escalate? | FIX IT IN PLACE: move E-02 onto the R5.5 inventory and replace E-03 with the teardown-gate wiring. | (a) Escalate as a blocking question, rejected: this is not a judgement call, it is a correctness fix with one obvious right answer that the repository has ALREADY chosen and shipped (`teardown_lane_if_classified`), so asking would stall the plan on something evidence settles. (b) Keep `dirty` and add an extra untracked check, rejected: it would still miss ignored files and would be a second classification competing with R5.5, which R6.1 forbids. | measured git probe (ignored file deleted at exit 0); `worktree_lease.py:316-319`; `lane_containment.py:2814-2819`; spec `7ckptx` R5.5/R6.1 | yes |
| D-3 | Order 02's deletions cannot reach an empty report. Pick the terminal state myself? | NO. Escalate as blocking (OQ-04) and forbid the DELETE half until answered; allow the RECOVER half. | (a) Rewrite E-08 to accept the unknown-row set, rejected as a unilateral redefinition of the Set's done-ness that also permanently changes what `aw attention --check` means for this repo. (b) Propose pruning run records, rejected: outside declared `Scope-Paths` and it edits run history. (c) Let the executor discover it after deleting, rejected outright: the discovery would come AFTER 13 irreversible deletions. | `runner_shared.py:1093-1096`, `:1170-1176`, `:1068`; `attention.py:1103-1111` | yes |
| D-4 | Is spec `7ckptx` in scope for Order 01, and should I declare the spec file? | IT GOVERNS, and it is NOT amended: no `.spec.md` in `Scope-Paths`, because the corrected plan COMPLIES with R5.5 rather than narrowing it. | (a) Declare the spec and amend R5.5 to let the merged case skip the inventory, rejected on two grounds: it would recreate exactly the loss R5.5 records, and plan `5w8g8j` is ALREADY blocked on that same narrowing, so two plans narrowing one approved MUST from different Sets is how a contract gets weakened twice. (b) Say no spec applies, as authored, rejected: R5.5 and R6.1 both bind the teardown path this plan touches. | `7ckptx` R5.5 (`:451-454`), R6.1 (`:459+`), `Status: approved`; `5w8g8j`'s own blocking OQ-02/OQ-03 | yes |
| D-5 | The `wfamig`/`i4ak5n` safety anecdote is now stale. Delete it or keep it? | KEEP IT, ANNOTATED, and move the load of the safety argument onto my own measured git probe. | (a) Delete it, rejected: it is the only narrative record of why the dirty rule exists, and deleting it would leave the rule looking arbitrary to a later reader. (b) Leave it unannotated, rejected: an executor who checks it finds the file in `main` and may conclude the hazard was imaginary, which is the opposite of the intended effect. | `i4ak5n` present in `main` `pending/`; `aw/lane/wfamig` does not resolve; the git 2.43.0 probe | yes |
| D-6 | Verdict and readiness with three OPEN BLOCKERs? | `REVIEWED - OPEN QUESTIONS`, readiness `no-go`, `Status: reviewed`. | (a) `APPROVE WITH REVISIONS APPLIED`, rejected: three BLOCKERs, two of them OPEN, is the readiness table's not-ready condition. (b) `REJECT - NEEDS REPLAN`, rejected and it was close for Order 01, whose two original deliverables both dissolved on measurement; but a real defect remains, the corrected E-items are bounded and executable, and Order 02's evidence-first design is sound, so this is repairable by three maintainer answers rather than a new approach. | workflow verdict/readiness tables; PR-001 and PR-002 `OPEN`; the retained interrupt-path defect | yes |

### Escalation of the irreversible decisions

None of this round's six decisions is judged `Reversible: no`: every one is undone by editing a plan, and
no code, test or spec was changed. But THREE of the things they defer are genuinely irreversible, which is
why each is blocking rather than resolved. Widening `reclaimable` on the `dirty` reading would have
force-deleted lane branches and erased ignored files with git raising no error (measured). Deleting 13 lane
refs cannot be undone once the reflog expires. Narrowing spec `7ckptx` R5.5 changes the contract every
future plan is reviewed against, and its own text records that this reasoning already destroyed lane
content once. The first is now fixed in the plan rather than left to authority; the second and third are
deliberately not authorized by me.

### Honest limits of this review

- I MEASURED FROM INSIDE A REVIEW LANE, and that is exactly the limitation PR-006 is about, so I state
  which figures it affects. `git for-each-ref`, `rev-list`, `merge-base` and `rev-parse` read the SHARED
  object store and ref database, so the branch inventory, the 43/94/26 arithmetic and every merged-ness
  verdict are authoritative. `aw attention --check` here DID return real rows (this lane's `.aw/records/`
  is present), and I cross-checked all 12 lanes independently with `merge-base`, so the zero-false-positive
  finding stands on the git check rather than on the report. `git worktree list` and any disk figure are
  this tree's view, not the main checkout's, which is why every plan now demands the tree be named.
- I COULD NOT INSPECT THE SIX MERGED LANE WORKTREES' CONTENTS. `.aw/worktrees/<lane>` does not exist inside
  my lane, so my "merged and still on disk" claim rests on `git worktree list` plus `merge-base`, not on
  reading those trees. I therefore did NOT verify why each was preserved; I traced the code path that
  preserves them and named `5w8g8j` as its owner.
- MY GIT-REFUSAL PROBE IS ONE GIT VERSION ON ONE PLATFORM (2.43.0, Linux). The untracked-versus-ignored
  asymmetry is documented git behavior and I would expect it to hold broadly, but I measured one version.
  The probe script was throwaway and deleted; the transcript is quoted above.
- I DID NOT RUN A DRIVER. Every claim about what the runner does at end-of-run or on interrupt comes from
  reading the code and AST-confirming the guard chains (`fin_rc == 0` for the teardown gate; enclosing
  function for both `reclaimable` readers), not from observing a live run. V-03 in Order 01 therefore still
  demands a real interrupted run, and I did not weaken it.
- I DID NOT IMPLEMENT OR SIMULATE THE CORRECTED E-02. That the inventory catches the ignored-file case is
  read from `inventory_lane`'s classification (`unknown_ignored` unions into `unknown`, and `classified`
  requires `not unknown`), plus the sibling review of `5w8g8j` which measured that path directly; I did not
  patch `reclaimable` and observe it.
- I RAN THE FULL SUITE ONCE, bare, at review HEAD, and attributed all 31 failures to `770fkp` by matching
  the failing files against that item's own list. I did not run a pre-change baseline, because I changed no
  code; the comparison rests on the backlog item's recorded measurement.
- I DID NOT DECIDE ANY OF THE THREE BLOCKING QUESTIONS, and I did not touch `5w8g8j`, `7ckptx`, any test,
  or any product code.

## Round 2

Reviewed on 2026-09-18 after maintainer intervention resolving OQ-02 and OQ-03:
- **PR-001 / OQ-02 RESOLVED**: Proceed with Order 01 retargeted to the interrupt path, accepting that primary disk recovery is owned and solved by 5w8g8j.
- **PR-002 / OQ-03 RESOLVED**: Order 02 approved (ut0vzr in go-pending-approval). Deleting merged branches is safe and standard Git hygiene since all commits are in main.
- **Verdict**: `APPROVE WITH REVISIONS APPLIED`.
- **Readiness**: Promoted to `go-pending-approval`.

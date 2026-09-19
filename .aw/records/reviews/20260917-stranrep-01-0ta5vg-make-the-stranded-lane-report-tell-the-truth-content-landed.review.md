# Review findings: plan 0ta5vg

- Subject-Id: 0ta5vg
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `7562ca6c`. The plan on disk was byte-identical to the lane input (`diff -q` clean) and
`git status --porcelain` on its path was empty, so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0.

THREE OF THE FOUR DIAGNOSED DEFECTS ARE REAL, INDEPENDENT, AND WORTH FIXING, and I verified each in source
and against the live record set rather than trusting the plan. The dedup key really does include `run_id`;
`lane_worktree_display` really does emit a path for a directory that is gone; `lane_remedy_hint` really does
probe a symbol that has never existed. Measured live from inside this review lane:

```text
rows: 25   distinct lanes: 17
repeats: {58ha43: 2, 7p9n2v: 3, qcqhj7: 3, rchpms: 3, zz5yxq: 2}
rows naming a worktree: 25, nonexistent: 19  (6 DO exist)
lane_remedy_hint() -> "...then merge that branch (no `aw integrate` verb exists yet)."
hasattr(oc_runipd,'cmd_integrate')=False   hasattr(oc_runipd,'handle_integrate_command')=True
```

THE FOURTH DEFECT IS REAL BUT THE PROPOSED FIX HAS ZERO MEASURED YIELD, which is the substance of this
review. E-01/E-02 add a patch-id (`git cherry`) content reading to silence six re-executed lanes. I ran that
exact reading against every reported lane:

```text
03ie04  -0/+2      fn2l1u  -0/+2      mm5p3v  -0/+3
nna8yz  -0/+3      r2i1b1  -0/+1      ybkmzp  -0/+2
silenced = 0 of 17
```

Not one resolves. I established WHY rather than guessing, because the reason decides whether any reading can
work: the second attempts were REIMPLEMENTATIONS, not cherry-picks. `r2i1b1`'s lane commit `81323cd6` and the
commit that actually shipped its work, `ccc7e04c` ("feat(runs): surface every refusal with its remedy...
(r2i1b1)"), carry different patch ids over 1602 versus 1235 diff lines. Stronger: a blob-identity check over
every file each lane touched found **0 of 7** (`r2i1b1`), **0 of 5** (`03ie04`) and **0 of 19** (`fn2l1u`)
files whose lane content matches HEAD. The plan's own F-6 anticipated this for `03ie04` at 8% overlap;
measurement extends it to all six. The work landed, as different bytes. No patch-id or content-identity test
can see that.

I ALSO FOUND A REPRODUCIBLE DATA-LOSS HAZARD IN E-02, which is the one finding that would have made this plan
worse than the status quo. `holds_work` is `commits_ahead > 0 OR dirty`, so a lane whose commits landed by
patch id but whose worktree still holds UNCOMMITTED files reaches the landing question. Built in a throwaway
repo:

```text
lane dirty: True -> '?? precious_uncommitted.txt'
ancestry  merge-base --is-ancestor rc = 1  -> STRANDED (reported TODAY)
content   git cherry main lane = '- bc8d8a76...' -> LANDED (SILENT AFTER THIS PLAN)
```

That untracked file exists nowhere else. Today's ancestry-only reading ACCIDENTALLY protects it and the plan
removes the protection. Related and also measured: `git cherry` exits 0 with EMPTY output when there is
nothing to compare, and the plan's stated rule ("every line begins `-`") is VACUOUSLY TRUE on an empty list,
so a zero-commit dirty lane would read LANDED; and `git cherry <target> nosuchbranch` exits 128, so the return
code must be checked before parsing.

TWO MECHANISM CLAIMS WERE WRONG IN WAYS THAT WOULD HAVE STRANDED THEIR ITEMS. E-05 blamed
`lane_worktree_display`'s EXCEPT branch, but of 25 records carrying a worktree **25 take the SUCCESS path and
0 take the except branch**, because `Path.resolve()` does not require existence so `relative_to(root)` succeeds
for an absent directory (confirmed: the helper returns `.aw/worktrees/03ie04` while that directory is gone).
Patching the named branch would have fixed nothing. And Step 0's convention that `aw attention` "CANNOT BE
MEASURED FROM INSIDE A LANE" is false: `stranded_lane_drift` resolves through `_resolve_runs_repo_root`, which
escaped this lane to the main checkout and returned 25 rows, not `[]`.

THE GOAL AS WRITTEN WAS NOT ACHIEVABLE. It asked for `--check` to be silent. All 17 reported lanes hold commits
genuinely absent by BOTH readings, so 17 non-`info` drifts remain and `drift_exit_code` returns 1 after every
item lands. That is fail-closed behavior working correctly on a corpus of genuinely unlanded work. Silence
requires the lanes' DISPOSITION, which is `ut0vzr`'s. I corrected the Goal and the acceptance criterion so the
executor is not chasing an exit code that cannot happen, and so an exit of 0 is correctly read as evidence of a
false LANDED bug.

VERIFIED AND LEFT ALONE. F3a's wording is verbatim as quoted and the violation framing is right. The
fingerprint pin claim is exactly right: `describe_lane` IS in the pin's `symbols` list while
`lane_work_has_landed`, `classify_lane_integration`, `stranded_lane_records` and `lane_worktree_display` are
NOT, so new helpers are the correct route. `LANE_INTEGRATION_TARGET_FALLBACK` is `HEAD` and the caller passes
no target. `render_json`'s `stranded_lanes` entries are `{branch, rule, detail}` only and `SCHEMA_VERSION` is
4, so F-8's no-bump reasoning holds. All six claimed finalize commits exist. The six lanes ARE still reported,
which means this plan's premise stands and the sibling `tb63qv` review's claim that they "appear ZERO times" is
what is wrong. The suite is fully green here (`8258 passed, 3 skipped, 2 xfailed`), so the 31-failure baseline
that review recorded must not be carried in.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. correctness; D. anti-regression | `worktree_lease` `holds_work` = `commits_ahead > 0 or dirty`; throwaway-repo reproduction above (ancestry rc=1 vs `git cherry` all-`-`); `classify_lane_integration`'s landing branch | **E-02 WOULD SILENCE A LANE HOLDING UNCOMMITTED WORK, LOSING IT.** A lane whose commits landed by patch id but whose worktree is DIRTY reaches the landing question, and the content reading answers for the COMMITS while saying nothing about uncommitted files. Reproduced: ancestry says STRANDED (reported today), `git cherry` says LANDED (silent after this plan), and the untracked file exists nowhere else. Today's ancestry-only reading accidentally protects that work; this plan removes the protection. Compounding it, `git cherry` returns EMPTY output with exit 0 when there is nothing to compare, and the plan's rule "every line begins `-`" is vacuously true on empty, so a zero-commit dirty lane also reads LANDED. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-02 now REQUIRES gating the content-landed conclusion on `not dirty` and keeping a dirty lane reportable, with the reproduction recorded inline; V-02 makes the cherry-picked-and-DIRTY case a MANDATORY assertion. E-01 now requires at least one `-` line AND no `+` line (empty output is NOT landed) and a return-code check before parsing (`git cherry` on a bad ref exits 128). F-7's caution sharpened: `65cuw0` gates a DESTRUCTIVE teardown off the same family of predicate, so the content reading must stay out of any path that can delete. |
| PR-002 | HIGH | IN-SCOPE | A. correctness; F. KISS (work with no measured effect) | `git cherry` run per lane (all six `-0/+N`, 0 of 17 silenced); `r2i1b1` `81323cd6` vs shipping `ccc7e04c` patch ids differ (1602 vs 1235 diff lines); blob-identity 0/7, 0/5, 0/19 for `r2i1b1`/`03ie04`/`fn2l1u` | **THE PLAN'S HEADLINE MECHANISM RESOLVES NOTHING ON THIS CORPUS.** E-01/E-02/E-03 exist to silence six re-executed lanes. Patch-id equality holds for NONE of the six and silences 0 of all 17 reported lanes, because the second attempts were REIMPLEMENTATIONS rather than cherry-picks: no file in the sampled lanes has content matching HEAD. So as authored these three items add a predicate, a record field, a spec clause and three test surfaces that change no row in this repository, while E-04/E-05/E-06 deliver real measured improvements independently. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added E-08/V-08 as a MEASUREMENT GATE that E-01/E-02/E-03 now depend on: re-measure the yield over every reported lane and record an explicit choice among (i) drop E-01/E-02/E-03 and land the rest, (ii) keep them as a forward-looking guard for a genuine cherry-pick or rebase with the zero present yield stated, or (iii) stop and take the disposition question to the maintainer. Explicitly forbade loosening the predicate to manufacture a nonzero figure (the exact failure OQ-02 warns of). The gate's approval note tells the executor that "drop" is a legitimate completion, not a failure. |
| PR-003 | HIGH | IN-SCOPE | G. executability (unachievable acceptance criterion) | 17 non-`info` drifts measured after simulating every fix; `artifact_core.drift_exit_code` returns 1; the authored Goal and the whole-plan evidence clause | **THE GOAL AND THE ACCEPTANCE CRITERION DEMANDED AN EXIT CODE THAT CANNOT HAPPEN.** The Goal was "make `aw attention --check` silent when every lane's work is accounted for" and the whole-plan evidence required exit 0. But every one of the 17 reported lanes holds commits genuinely absent by BOTH readings, so `--check` still exits 1 after this plan. An executor holding that criterion either reports failure for correct behavior or, worse, loosens a predicate until the gate goes quiet, which is precisely the false-LANDED outcome PR-001 is about. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Goal rewritten to what the plan can deliver (a report that is true: one row per lane, no phantom worktree, a live remedy) with the correction and its measurement stated. Whole-plan evidence now says the expected exit is **1, and that is a PASS**, requiring instead that the failure got smaller and truer (row count down, no absent worktree named, real remedy, every remaining row genuinely unlanded), and states that an exit of 0 would be evidence of a BUG. Scope check gained an explicit "what remains reported" paragraph so the residue is not read as a defect. Added F-9. |
| PR-004 | HIGH | IN-SCOPE | G. executability (wrong mechanism named) | 25 of 25 worktree-carrying records take the SUCCESS path, 0 the except branch; `lane_worktree_display(repo, "<repo>/.aw/worktrees/03ie04")` returns `.aw/worktrees/03ie04` for an absent directory | **E-05 NAMED THE WRONG CODE BRANCH, SO THE PRESCRIBED EDIT WOULD HAVE FIXED NOTHING.** The item blamed the except-branch `.aw/worktrees/<name>` reconstruction. In fact `Path.resolve()` does not require existence, so `relative_to(root)` SUCCEEDS for an absent path and every one of the 25 records returns through the normal success path. Separately, the item implied all rows name an absent worktree; 19 are absent but **6 EXIST**, so an unconditional omission would delete true information. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 corrected to guard the SUCCESS return (and the reconstruction for completeness), with the 25/0 measurement and the direct confirmation recorded inline, plus the 19-absent/6-present split so omission is conditional. V-05 now requires the existing-worktree case (real, not hypothetical) and requires pasting the guard's source to prove it protects the success path. Added F-4a. |
| PR-005 | HIGH | IN-SCOPE | A. correctness (a stated premise refuted) | 25 rows / 17 lanes measured vs the authored 19/12; `git cherry` finds `+` commits for all 17; blob-identity 0/N for three sampled lanes | **THE CONCERN'S CENTRAL CLAIM ("NOT ONE of the reported lanes holds work that needs recovering") IS FALSE.** By the very test this plan proposes, all 17 reported lanes hold at least one commit genuinely absent from the target. The six re-execution lanes ARE wrongly reported (the premise that they should be silent stands, and `tb63qv`'s review claim that they appear zero times is the wrong one), but their work reached `main` as different bytes, so no content reading recovers them. Leaving the claim would license an executor to treat any remaining row as a bug. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Concern annotated with a dated correction stating both wrong quantities (counts moved to 25/17; "not one holds work" refuted with the per-lane and blob-identity evidence) and separating what survives: defects (2)(3)(4) are real and independently fixable, defect (1) is a real spec violation whose proposed fix has zero yield on today's corpus. F-1, F-2 and F-4 re-measured; F-2a added. |
| PR-006 | MEDIUM | IN-SCOPE | G. executability; E. testing | `attention._resolve_runs_repo_root` walks out of `.aw/worktrees/...`; run from inside this lane it resolved to the main checkout and `stranded_lane_drift` returned 25 rows | **A STEP 0 CONVENTION IS FACTUALLY WRONG AND WOULD MISDIRECT EVERY ACCEPTANCE MEASUREMENT.** The plan asserts `aw attention` cannot be measured from inside a lane (inherited from `ut0vzr`'s PR-006) and therefore requires a "NON-LANE tree" for every check. But the resolver escapes the lane, and the in-lane measurement returns real numbers. The convention would send the executor hunting for a tree it does not have, since `aw oc run` executes in exactly such a lane, and would invite distrusting a number that is correct. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Convention rewritten with the measurement and the resolver named, requiring measurements to PRINT the resolved run-root so they are self-describing and a genuine empty case is distinguishable from a lane artifact. The "NON-LANE tree" requirement removed from V-04 and the whole-plan evidence. Added F-10. |
| PR-007 | MEDIUM | IN-SCOPE | G. executability; spec sync | `SPEC_TRANSITIONS['implemented']` = `{superseded, deferred}`; the spec's `- Status: implemented` | **E-07 RISKED AN IMPOSSIBLE SPEC TRANSITION, AND COULD HAVE WRITTEN A CLAUSE THE CODE DOES NOT IMPLEMENT.** The target spec is `implemented`, whose only legal onward transitions are `superseded` and `deferred`, so any status set is refused (and would be wrong: this is an amendment, not a reversion). Worse, E-07 would amend F3a for a content-landed rule even in the case where E-08 decides to DROP the content reading, leaving the spec asserting a reading that does not exist. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-07 now records the measured transition table, forbids attempting a transition, and makes the content-landed clause CONDITIONAL on E-01/E-02 actually shipping while the one-row rule is stated unconditionally (E-04 delivers it regardless). Depends-on extended to E-08. V-07 requires the `- Status:` pasted before and after showing it unchanged, `aw specs note` output, a statement of whether a content clause was written, and `aw check specs`. |
| PR-008 | MEDIUM | IN-SCOPE | G. executability; D. anti-regression | `aw check plans`: `check.lifecycle-transition-invalid` at `error` on this plan, pre-existing at HEAD; `E-00` has zero precedent as a leaf id across `executed/`; spec 5.1 allocation-watermark rule | Two structural defects, one pre-existing and one I introduced and then corrected. (a) The plan's `## Workflow history` was OLDEST-FIRST, so `aw check plans` reported an `error`-severity invalid `to-review -> draft` transition (present at HEAD, not caused by this review). (b) My measurement gate was first numbered `E-00`, which has no precedent as a leaf id and violates 5.1's rule that a new item takes the next unused suffix ABOVE the watermark. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | History reordered to newest-first (the documented convention); `aw check plans` now reports only the corpus-wide `info` carrier advisory for this plan, with the `error` cleared. The gate renumbered `E-00` -> **E-08** with the watermark raised 07 -> 08, keeping the E/V bijection intact (verified: 8 E-leaves, 8 V-leaves, `aw ipd lint --phase review-finalize` conforming). |
| PR-009 | LOW | IN-SCOPE | E. testing; G. executability | bare `python3 -m pytest` in this lane: `8258 passed, 3 skipped, 2 xfailed`; `tb63qv`'s review records a 31-failure "documented worker-lane baseline (`770fkp`)"; `lane_remedy_hint()` takes no arguments and has one caller | Two small executability gaps. (a) The sibling review's 31-failure lane baseline is stale here (the suite is fully green), and an executor carrying that expectation could mistake a real regression for the baseline. (b) E-06 asks the remedy to name the record's `id6`, but `lane_remedy_hint()` takes no arguments and V-06's own evidence line calls it with none, so the signature change was unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Whole-plan evidence now forbids carrying a failure-count expectation from another plan, records the measured green baseline, and requires capturing the baseline in the EXECUTING tree compared by failing node id (which the plan already asked for). E-06 now specifies an OPTIONAL id6 parameter preserving the no-argument call, and notes both hosts have `handle_integrate_command` so the hint must not hardcode `oc`. Added F-11. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The content reading resolves 0 of 17 lanes. Drop E-01/E-02/E-03 outright at review, keep them, or escalate to the maintainer? | NEITHER drop nor escalate: add E-08, a measurement gate that re-derives the yield at execution time and forces an explicit, recorded keep/drop/stop choice, with "drop" pre-blessed as a legitimate completion. | (a) Delete E-01/E-02/E-03 now: rejected, because the corpus moves (the authored 19/12 became 25/17 in a day) and a genuine cherry-pick or rebase IS an integration shape the drivers can produce, so the predicate may have real forward value; deleting on one day's measurement would discard it on evidence that expires. (b) Raise it as `Blocking: yes` and stop the plan: rejected, because E-04/E-05/E-06 are independently valid and measurably fix live defects, and blocking the whole plan on the weakest quarter of it would strand three real fixes behind a question that E-08 can answer with evidence at execution time. (c) Leave the items unchanged and let the executor discover the zero yield: rejected, that is how a predicate gets loosened until the gate goes quiet. | `git cherry` per lane (all six `-0/+N`, 0 of 17 silenced); patch ids differ for `r2i1b1` (`81323cd6` vs `ccc7e04c`, 1602 vs 1235 diff lines); blob-identity 0/7, 0/5, 0/19; and F-6's own 8%-overlap finding, which anticipated this for one lane. | yes |
| D-2 | E-02 would silence a dirty lane and lose uncommitted work. Escalate as a blocking question or fix it in place? | FIX IN PLACE: gate the content conclusion on `not dirty`, keep the lane reportable, and make the dirty case a mandatory V-02 assertion. Not escalated. | (a) Escalate `Blocking: yes`: rejected, no maintainer judgement is needed; `dirty` is already computed, already carried on the record, and already rendered as "uncommitted changes", so the fix is mechanical and the plan's own stated fail-closed principle ("a false LANDED hides real loss and is strictly worse than the false STRANDED") dictates the direction. (b) Drop the content reading because of this hazard: rejected, it conflates a fixable guard with the separate yield question D-1 handles. (c) Rely on `dirty` as a complete safety net: rejected and stated as an honest limit in the plan, since `dirty` is a plain `git status --porcelain` blind to IGNORED files, which is exactly what made `65cuw0`'s force-delete hazard real. | Reproduced in a throwaway repo: dirty lane, ancestry rc=1 (reported) vs `git cherry` all-`-` (silent); `holds_work` = `commits_ahead > 0 or dirty`; `attention.py`'s row builder already emits "uncommitted changes" from `rec["dirty"]`. | yes |
| D-3 | The Goal demands an exit code that cannot be reached. Rewrite the Goal, or flag it and leave the human to restate the objective? | REWRITE the Goal and the acceptance criterion to what the plan delivers, and state explicitly that exit 1 is the expected pass and exit 0 would indicate a bug. | (a) Leave the Goal and note the gap: rejected, an unachievable acceptance criterion is the single most likely cause of a false "done" claim or of a loosened predicate, and the workflow's fix-by-default bar applies. (b) Ask the maintainer to restate the objective: rejected, the objective did not change; only the measurement of what achieves it did, and the repository supplies that measurement. (c) Expand scope to include lane disposition so silence IS reachable: rejected, disposition is explicitly `ut0vzr`'s and this plan is read-only by contract. | 17 non-`info` drifts remain after simulating every fix; `artifact_core.drift_exit_code` returns 1; the plan's own Deferred section already assigns disposition to `ut0vzr`. | yes |
| D-4 | Step 0 asserts `aw attention` cannot be measured inside a lane; measurement says it can. Correct the convention or preserve it as a conservative safety margin? | CORRECT it, and require every measurement to print the resolved run-root. | (a) Leave the conservative convention: rejected, it is not conservative in effect. It directs the executor to a non-lane tree that `aw oc run` does not provide, and it teaches distrust of a number that is in fact correct, which is how a real measurement gets discarded. (b) Correct it silently: rejected, the claim came from a sibling review (`ut0vzr` PR-006) and will be re-inherited unless the refutation is recorded where the next reader sees it. | `attention._resolve_runs_repo_root` walks out of a `.aw/worktrees/...` path to the first ancestor with a state root; run from inside this lane it returned the main checkout and `stranded_lane_drift` returned 25 rows, not `[]`. | yes |
| D-5 | My added measurement gate was numbered `E-00`. Keep it (it sorts first and reads as a prerequisite) or renumber? | RENUMBER to `E-08`, raising the watermark 07 -> 08, and express the ordering through `Depends on:` and its position in the group instead. | (a) Keep `E-00`: rejected. Spec 5.1 requires a new item to take the next unused suffix ABOVE the allocation watermark, `E-00` has zero precedent as a leaf id anywhere in `executed/`, and borrowing the orchestrator's `Order: 0` convention for a leaf id invents a second meaning for the number. (b) Renumber the whole checklist so the gate is `E-01`: rejected outright, 5.1 states an identifier is stable once assigned and reordering MUST NOT change it. | Spec 5.1 ("New items receive the next unused numeric suffix greater than the highest suffix EVER assigned ... not merely the highest currently present"; "An identifier is stable once assigned"); zero `^- [ ] E-00` leaves across `executed/`; post-change lint conforming with an intact 8/8 bijection. | yes |

### Honest limits of this review

- I did NOT determine whether a landing test exists that WOULD resolve these six lanes. I refuted patch-id
  equality and blob identity; a semantic-equivalence test is what the plan's own Deferred section calls
  "probably not tractable", and I agree but did not prove it. If one exists, E-08's option (iii) is where that
  conversation belongs.
- The `git cherry` behaviors I rely on were measured on THIS machine's git (the partial `-`/`+` mix, the empty
  output for nothing-to-compare, the 128 on a bad ref, and the identical-sha result when cherry-picking onto an
  unadvanced target). They are documented git behavior, but the plan's tests should pin them rather than trust
  this paragraph, which is why V-01 now enumerates five cases including the one that only differs when the
  target has advanced independently.
- I did not execute any part of the plan. Everything above is measurement against the unmodified tree plus
  throwaway repositories; no `agent_workflows/` file was touched by this review.
- The 25/17 figures are a snapshot and will move, exactly as the authored 19/12 did within a day. Every count I
  wrote into the plan is marked for re-derivation. I did not attempt to determine which lanes SHOULD be
  retired; that is `ut0vzr`'s and I deliberately left it alone.
- I verified `describe_lane` is fingerprint-pinned and the other four helpers are not, but I did not run the
  fingerprint test to confirm it currently passes; the suite as a whole is green here, which covers it
  indirectly.
- PR-001's guard rests on `dirty`, which cannot see ignored files. I recorded that limit in the plan rather
  than solving it, because solving it means consuming `lane_containment.inventory_lane`, which is `65cuw0`'s
  declared surface and outside this plan's fence.

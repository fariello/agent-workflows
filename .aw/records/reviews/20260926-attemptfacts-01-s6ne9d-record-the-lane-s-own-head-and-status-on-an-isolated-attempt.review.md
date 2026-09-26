# Review findings: plan s6ne9d

- Subject-Id: s6ne9d
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `863220b8`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(exit 0, `findings: 0`) before revision. No pre-review snapshot was needed: the plan was committed
and unmodified (`git diff HEAD --stat` empty, and the lane-input copy is byte-identical to the
tracked file).

THE UNDERLYING DEFECT IS REAL AND THE CHOSEN SHAPE IS RIGHT. I reproduced a vacuous record by
driving a real isolated turn, and I confirmed the design constraint that forces the ADD-a-field
shape rather than redefining `ending_head`. The plan's OQ-01 reasoning is correct and independently
verified: `artifact_audit.FinalizeEvidence.finalize_after` returns `UNKNOWN_HEAD_UNREACHABLE` when
`ending_head not in self.head_reachable`, and `run_viewer` feeds it each attempt's `ending_head`, so
redefining the field to an unmerged lane head would degrade every isolated row of the audit. F-6, F-7
and F-8 all reproduced exactly as written, including the negative claim: `grep -n
'ending_head\|ending_status\|starting_head'` against spec `25kzda` returns only the Section 5.6
`starting_status` (a lifecycle status, not a git status) and one Section 4.6 "ending HEAD" prose
mention, so there is genuinely no attempt-field list to amend.

**THE PLAN'S CENTRAL FACTUAL CLAIM IS FALSE, AND FALSE IN THE DIRECTION THAT WOULD HAVE COST THE
EXECUTOR ITS FIRST TASK GROUP.** The `- Concern:` states that for an isolated turn "`starting_head ==
ending_head` and `ending_status == ""` BY CONSTRUCTION, even for a lane that committed substantial
work", and E-01 instructs the executor to reproduce exactly that. I drove the turn the plan
specifies, using the harness it names, and measured the opposite:

```text
### SHAPE 1: verified, integrated (the DEFAULT successful shape)
   item status           : executed   attempt disposition: executed
   main HEAD before turn : cd0412a4d39d741d7b7d20695f18925018b291f7
   starting_head         : cd0412a4d39d741d7b7d20695f18925018b291f7
   ending_head           : 11dac09e48a0c50cad581d06c4c6266e2f8a8ae5
   VACUOUS (start==end)? : False
   collect_earned_paths  : ['.aw/records/plans/executed/...-wir001-demo.ipd.md', 'src/demo.txt']
```

The reason is a sequencing fact the plan's own findings table walks right past. `ending_head` is
re-recorded in the lane-integration SUCCESS arm (F-3 counts that site), and that re-record happens
AFTER the lane has been merged to main, so main's HEAD has by then advanced to the lane tip. The
timeline I captured makes the mechanism explicit:

```text
  main HEAD before turn                      96c09f6e...
  main HEAD right after agent turn           96c09f6e...      <- vacuous HERE, transiently
  LANE HEAD right after agent turn           b737e5a8...
  -- before integrate_lane_branch --
  attempt ending_head                        96c09f6e...
  -- after integrate_lane_branch --   True
  main HEAD                                  c4c5ee0c...      <- re-recorded, now the lane tip
  attempt ending_head                        c4c5ee0c...
```

So on the SUCCESS path the record is self-correcting: `ending_head` ends up equal to the lane tip,
`starting_head..ending_head` spans exactly the lane's work, and `collect_earned_paths` already
returns the right paths from the attempt range alone. The plan asserts this shape is broken. It is
not.

**THE DEFECT IS REAL BUT ITS POPULATION IS THE NON-INTEGRATED SHAPES, WHICH THE PLAN NEVER NAMES.**
Driving the same turn with a red integration gate:

```text
=== NON-INTEGRATED (fail-merge) SHAPE ===
  item status                         : fail-merge
  attempt starting_head (main)        : 77e21dca6fb6abbdf983729ee15adb938314684e
  attempt ending_head   (main)        : 77e21dca6fb6abbdf983729ee15adb938314684e
  VACUOUS (start==end)?               : True
  attempt ending_status               : ''
  lane branch tip at END of turn      : 28e4e0a80c24d9c324a11db8e65ac616b4f3de05
  commits added to lane after sample  : 1
  subjects of those commits           :
    - lifecycle(wir001): finalize wir001 -> executed
  commits in lane vs base             : 2
  collect_earned_paths (today)        : []
```

THIS is the vacuous record, and it is where every consumer harm the backlog item describes actually
lives: a lane holding two commits including a finalize, reported as a turn that moved nothing and
earned nothing. The correction matters for three concrete reasons, not as a pedantic point:

1. E-01 as authored is UNSATISFIABLE on the shape it names. It tells the executor to drive the
   `WorktreeIsolationTests` happy-path fake and paste a vacuous record. That run produces a
   NON-vacuous record. An executor would either report the plan's premise unreproducible, or worse,
   quietly adjust until something looked vacuous.
2. E-03's site list is INCOMPLETE FOR THE ACTUAL DEFECT. It names the integration-SUCCESS arm and the
   finalize-REFUSAL arm. The shape I measured as vacuous reaches NEITHER: it goes through the `if not
   integrated:` arm (`record_integration_refusal`), which I confirmed by AST walk writes neither
   field. So the plan adds lane facts to two arms that were already self-correcting or nearly so, and
   omits the one arm where the record is actually empty.
3. E-07 case (1) pins the FALSE claim as a test. It requires asserting `ending_head`/`starting_head`
   "are still main-checkout values (`starting_head` equals main's HEAD before the turn)" on an
   integrated turn. `starting_head` does equal that, but the natural reading of the case, paired with
   the Concern, is that `ending_head` is unchanged; a test written to that belief would fail, and an
   executor debugging it would be debugging correct code.

**WHAT I FIXED.** I rewrote the `- Concern:` to state the defect by the shape it actually occurs in,
with the measured evidence. I rewrote E-01 to reproduce BOTH shapes and to make the non-integrated one
the reference case, so the reproduction is achievable and measures the real thing. I added the
integration-refusal arm to E-03 as the primary site and re-ordered the other two behind it. I
corrected E-07 case (1) to assert the integrated shape's ACTUAL values and added a case for the
refusal shape. I corrected F-2 and F-4 in place (retained rather than deleted, so the original premise
stays visible as a correction), and added F-9 naming the refusal arm and F-10 recording the
self-correcting success path. V-01, V-03 and V-07 now demand the two-shape evidence.

**ONE STALE CITATION, CORRECTED.** The plan's Project-conventions bullet and E-05 both lean on
`tests/test_runner_shared.py` counting `run_checked` call sites and instruct the executor to keep
`collect_earned_paths` at one so "the count is unchanged". That census is DEAD. `RELOCATED_RUN_CHECKED_CALLERS`
is still defined in the file, but the test that read it, `test_no_call_site_was_rewritten`, was
deleted in commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests");
`grep -rn 'def test_no_call_site_was_rewritten' tests/` finds nothing, and a collect-only run of the
whole suite matches the name nowhere. The table is now inert data. The one-call constraint it was
cited to justify is still GOOD ENGINEERING (one git invocation per attempt rather than two), so I kept
the constraint and corrected the reason, rather than dropping it and inviting a needless second call.
V-05's demand to paste `tests/test_runner_shared.py` passing is retained: it is a real suite (92 tests,
verified green) and a legitimate regression check, just not the census the plan claimed.

**WHAT I DID NOT CHANGE, DELIBERATELY.** The three-field ADD shape, OQ-01's resolution, the allowlist
addition (OQ-02 is correct: two commit hashes plus a lane-relative `git status --short`, and
`absolute_paths_outside_lane` is the property check that would catch a violation), and the decision to
keep `collect_lane_earned_paths` in `process_backlog_close`. All four are sound and well argued. The
plan's structure, right-sizing (7 E-items, one concern each), and its E/V bijection are good.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. correctness (a false premise); G. executability | measured: `SHAPE 1` above; `runner_shared.execute_item_core` lane-integration success arm re-recording `attempt["ending_head"] = git_head(repo)` AFTER `integrate_under_repository_lock` returns | **THE CONCERN'S "BY CONSTRUCTION" CLAIM IS FALSE FOR THE DEFAULT SUCCESSFUL SHAPE.** For a verified, integrated isolated turn I measured `starting_head != ending_head`, `ending_head` equal to the lane tip, and `collect_earned_paths` returning the lane's paths correctly. The success arm re-records `ending_head` AFTER the merge, by which time main's HEAD IS the lane tip, so that path is self-correcting. The plan asserts the opposite of what it measures, and E-01 instructs an executor to reproduce a vacuity that the named harness does not produce. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `- Concern:` rewritten to scope the defect to the shapes where it occurs, with the measured success-path timeline stated so the self-correction is not rediscovered as a surprise. F-2/F-4 corrected in place; F-10 added recording the success path. E-01 rewritten to reproduce BOTH shapes. |
| PR-002 | HIGH | UNDER-SCOPE | A. correctness; C. architecture (the wrong site) | measured: `NON-INTEGRATED (fail-merge) SHAPE` above; AST walk of `execute_item_core` showing the `if not integrated:` arm assigns neither `ending_head` nor `ending_status` | **E-03 OMITS THE ONE ARM WHERE THE RECORD IS ACTUALLY VACUOUS.** The plan lists the integration-SUCCESS arm and the finalize-REFUSAL arm. The shape I measured as genuinely vacuous (integration gate red -> `fail-merge`, lane preserved holding 2 commits including a finalize, `collect_earned_paths` returning `[]`) reaches the `if not integrated:` / `record_integration_refusal` arm, which writes NEITHER field and is not in the plan's site list. So as authored the plan instruments two arms that were already self-correcting and skips the defect's primary home. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-03 rewritten: the integration-REFUSAL arm is now site (1) and is called out as the primary one, with the measurement; the success arm and finalize-refusal arm follow as (2) and (3). F-9 added naming the arm and the measured lane state. E-07 gains a case asserting the refusal shape carries a non-vacuous lane range. V-03 requires the refusal-arm diff and a pasted refused attempt record. |
| PR-003 | MEDIUM | IN-SCOPE | E. testing (a test that would pin a false belief) | E-07 case (1) as authored, read against `SHAPE 1` | **E-07 CASE (1) WOULD PIN THE FALSE CLAIM.** It requires asserting on an integrated turn that "`ending_head`/`starting_head` are still main-checkout values". `starting_head` is; `ending_head` is the post-merge head, which equals the lane tip. A test written to the Concern's belief fails against correct code, and the executor would debug the code rather than the belief. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Case (1) now asserts the ACTUAL integrated-shape values (`starting_head` equals main's pre-turn HEAD; `ending_head` equals the lane tip because the success arm re-records post-merge; `lane_ending_head` equals the lane tip too) and states why the two coincide there. A new case (2) covers the refusal shape, where they diverge and the lane fields carry the only true reading. Subsequent case numbers shifted. |
| PR-004 | MEDIUM | IN-SCOPE | D. anti-regression (a citation to a deleted guard) | `git log -S'test_no_call_site_was_rewritten'` -> deleted in `19313eed`; `grep -rn 'def test_no_call_site_was_rewritten' tests/` -> no match; whole-suite collect matches the name nowhere | **THE CENSUS E-05 IS TOLD TO PROTECT NO LONGER EXISTS.** `RELOCATED_RUN_CHECKED_CALLERS["collect_earned_paths"] == 1` is still in the file, but its only reader was deleted, so the table is inert data and "so the count is unchanged" protects nothing. Left as written, an executor either wastes a pass hunting a test that cannot fail, or concludes the constraint is fictional and adds a second git call. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 keeps the ONE-CALL constraint and replaces its justification with the real one (one git invocation per attempt, a best-effort path an operator waits on), and states plainly that the census is inert with the commit that retired it. The Project-conventions bullet corrected the same way. V-05 still requires `tests/test_runner_shared.py` green (92 tests, a real suite) but no longer calls it a census check. |
| PR-005 | LOW | IN-SCOPE | A. correctness (an unstated ordering hazard) | measured: the refusal shape's lane gained `lifecycle(wir001): finalize wir001 -> executed` AFTER the post-turn sample | **THE POST-TURN SAMPLE IS TAKEN BEFORE THE LANE-SIDE FINALIZE COMMIT, AND THE PLAN SAYS SO ONLY IN PASSING.** E-03 mentions "the lane-side finalize adds a lifecycle commit to the lane after the post-turn sample" as a justification for refreshing, but does not state the consequence: on any path that does NOT reach a refresh site, `lane_ending_head` will be one commit short of the lane tip. I measured exactly one such commit. That is a silently incomplete field rather than a wrong one, so it needs saying. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now states the consequence explicitly and requires the refusal arm's refresh (site 1) precisely because that path would otherwise strand a one-commit-short value. E-07's refusal case asserts the finalize commit IS inside the recorded lane range. |
| PR-006 | LOW | IN-SCOPE | F. honest documentation | `- Scope:` and the gate paragraph as authored | **THE SCOPE AND GATE INHERIT THE FALSE PREMISE.** Both describe the change as making "a productive lane turn distinguishable from a no-op" without qualification, which overstates it: on the default successful path the record already distinguishes them. Leaving it would misdescribe the deliverable to the approving human. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Scope:`, the Goal, and the gate's WHAT A HUMAN IS APPROVING paragraph now say the change makes the lane's own facts available on EVERY isolated attempt and repairs the record on the NON-INTEGRATED shapes, naming the success path as already correct. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan's Concern states a "BY CONSTRUCTION" vacuity. Accept it from the backlog item's authority, or drive a turn and measure? | DRIVE IT AND MEASURE, and the measurement inverts the claim for the default shape. | (a) Accept it: the claim is repeated by the backlog item, the plan, and `turn_attempted_nothing`'s own docstring, so three sources agree. Rejected because all three trace to ONE observation, and the claim is exactly the kind a review exists to check; a plan whose first task group reproduces something is a plan whose reproduction I can run. (b) Reason about the code without running it: rejected, because the fact that decides it is an ORDERING between a re-record and a merge, which is precisely what static reading gets wrong. | Measured by driving `oc_runipd.execute_item` through the `WorktreeIsolationTests` harness the plan names, at HEAD `863220b8`: integrated shape `starting_head != ending_head` with `ending_head` equal to the lane tip; `collect_earned_paths` returned both lane paths. Timeline captured across `integrate_lane_branch`. | yes |
| D-2 | The claim is false for the integrated shape. Is the whole plan therefore invalid (REPLAN), or is the defect real elsewhere? | THE DEFECT IS REAL ELSEWHERE; revise rather than replan. The non-integrated shapes are genuinely vacuous. | (a) `REJECT - NEEDS REPLAN`: tempting because the headline premise is wrong. Rejected on measurement: the `fail-merge` shape leaves a lane holding 2 commits recorded as `start == end`, `ending_status == ""`, `collect_earned_paths() == []`, which is precisely the harm described, so the plan's SOLUTION (three additive lane fields) is right and only its DIAGNOSIS of the population is wrong. Replanning would discard correct design work over a correctable factual error. (b) Accept and let the executor discover it: rejected, that is the outcome this review exists to prevent. | Measured `fail-merge` shape above; `record_integration_refusal` arm confirmed by AST walk to write neither field; the plan's own OQ-01/OQ-02 resolutions independently verified correct. | yes |
| D-3 | E-05 cites a census test as the reason to keep one `run_checked` call. The test is deleted. Drop the constraint or keep it with a new reason? | KEEP the constraint, REPLACE the reason, and say the census is inert. | (a) Drop the one-call constraint since nothing enforces it: rejected, it is independently good (one git invocation per attempt on a best-effort path an operator waits on, and the repository treats user-perceptible waste as a defect). (b) Keep citing the census: rejected, it would send an executor to a test that cannot fail and teaches a false belief about what the suite guards. (c) Restore the deleted test: rejected as out of scope for this plan and not this reviewer's call; it was removed by a deliberate suite-trimming commit. | `git log -S'test_no_call_site_was_rewritten' -- tests/test_runner_shared.py` -> `19313eed` "test: trim test suite from 9,136 to under 2,000 tests"; `grep -rn 'def test_no_call_site_was_rewritten' tests/` -> no match; `RELOCATED_RUN_CHECKED_CALLERS` loaded only by `ALL_SHARED_RUN_CHECKED_CALLERS`, itself never read. | yes |
| D-4 | Should the review ADD the integration-refusal arm to E-03's scope, or raise it as a question for the author? | ADD IT. It is the same class of edit as the arms already listed and is required for the plan to fix the defect it names. | (a) Raise it as an open question: rejected, it is not a judgement call about scope or risk; it is the site the declared defect occurs at, and omitting it would ship a change that instruments everything except the defect. (b) Leave E-03 and note the gap in findings only: rejected, a finding whose remedy is one more site in an existing checklist item should be fixed, per the Fix Bar. | The arm is inside the same `self_finalize and work_dir and wt_handle is not None and integration.earned` branch the plan already edits, and `Scope-Paths` already declares `agent_workflows/runner_shared.py`, so no fence widening is needed. | yes |

### Deferred and open

- (none). Every finding was FIXED in place. No finding reached the Medium-High or High Remediation
  Risk that the Fix Bar requires for a deferral, and no question needed the human: PR-001 through
  PR-006 were each settled by a measurement against the repository, and each measurement is recorded
  above with the command or the captured output that produced it.

HONEST LIMIT, stated because it bounds what this round proves. I measured the OC host only. The plan
asserts both hosts share `execute_item_core`, and I verified that both `oc_runipd.execute_item` and
`agy_runipd.execute_item` call it, so the recording sites are provably common; but I did not drive an
AGY turn, so the agy-side reproduction remains E-07 case (3)'s obligation rather than a fact this
review establishes. I also did not survey historical run records for the real-world frequency of the
vacuous shape: `.aw/records/runs/` is absent from this review lane, so the population split between
integrated and non-integrated turns in practice is unmeasured here, and the plan should not be read as
claiming one.

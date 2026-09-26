# Review findings: plan slqvmx

- Subject-Id: slqvmx
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `027e2f69`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(exit 0, `findings: 0`) before revision. No pre-review snapshot was needed: the plan was committed
and unmodified, and the lane-input copy is byte-identical to the tracked file.

EVERY AUTHORED CLAIM REPRODUCED, WHICH IS WORTH SAYING FIRST. I ran the plan's own E-01 command
verbatim and got exactly its stated expected outcome: `False False True` and
`{'exit_code': 0, 'finalize_refused': 'r'}`, with one `rg` hit for the false phrase in
`runner_shared.turn_correction_packet`. F-1 is real and precisely located: the docstring says the
packet "is recorded on the ATTEMPT under the allowlisted `turn_correction` key, so it reaches the next
turn's prompt through that one channel", and `turn_correction` is not in the tuple. Spec `7ckptx`
R1.1 and R1.3 both exist in the approved spec as cited. The maintainer ruling the plan rests on is
genuine and recorded on backlog `ytrz7u`'s own history ("no source-scanning tests"), so OQ-01's
resolution is properly attributed rather than invented. All four E-02 quoted anchors resolve to
exactly one hit each, and all seven E-03 example keys exist as attempt assignments. The design
decision -- document the contract, change no behavior -- is the right one, and the plan's rejection of
the backlog's denylist option (it would invert the fail-closed direction R1.1 requires) is correct
reasoning that I would have had to supply if the author had not.

**THE CONTRACT AS DRAFTED WOULD HAVE LEFT THE TRAP ONE STEP FURTHER ON.** This is the finding that
justifies the review. The plan's whole purpose is to stop an author from writing an attempt key and
silently getting nothing, and its remedy is a contract saying "your key is driver-only unless you add
it here". But adding a key to the allowlist is NECESSARY AND NOT SUFFICIENT, because the projection's
single caller gates it a second time:

```python
prior = item.get("attempts", [])[-1] if recovery and item.get("attempts") else None
prior = lane_containment.prior_attempt_summary(prior, lane_root)
```

Measured: `prior_attempt_summary(None, Path('/tmp'))` returns `None`. So on a FIRST turn no
prior-attempt key reaches the agent at all, however the allowlist reads, and only `attempts[-1]` is
ever read. An author who follows the drafted contract, adds their key, and expects it on turn one gets
the same silent nothing the plan exists to prevent -- and would reasonably conclude the contract lied.
The word `recovery` appeared in the plan only inside E-02's quoted replacement text, never as a stated
condition. Added as F-5, given its own E-item (E-05), and made testable by an extra E-06
assertion that a first turn's prompt line reads `Prior attempt: none` even for an allowlisted key.
That assertion is the one that converts the contract from a statement into something a future change
can break loudly.

**E-02'S REPLACEMENT SPAN STARTS ONE SENTENCE TOO LATE.** The paragraph it repairs opens "WHICH
CONSTRUCTION PATH CARRIES IT, stated because the plan's E-04 demands the path be NAMED rather than
described." That "the plan" is `xipfy1`, executed 2026-09-08. E-02 replaces from the NEXT sentence
onward, so the dangling deictic would survive into shipped code, where a future maintainer reads "the
plan" as the current one and goes looking for an E-04 that is not there. Added as F-6 and folded into
E-02, which now requires naming `xipfy1` or dropping the clause, with an `rg` check in V-02.

**TWO AUTHORED FINDINGS HAD DRIFTED, AND THE DRIFT IS ITSELF THE LESSON.** F-2's census was 80 keys
assigned / 63 not allowlisted at `61ef21d8`; at review HEAD it is 85 / 68. I attributed the delta by
diffing the key sets: five keys landed in merged work (`accounting_error` and
`session_reconciliation_error` from `zrvtm2`, plus `review_shared_commit`,
`review_shared_commit_refused`, `review_shared_committed_paths`). The plan had already hedged these as
"indicative, not exact", which was honest, but a number that moved by five in a few days should not be
quoted as a bar at all; E-01 now re-derives it and V-01 requires the executor to state what they
measured rather than repeat either pair. Relatedly F-4 called `zrvtm2` a PENDING plan; it is EXECUTED
(`- Status: executed`), so its keys are already in the tree and its named risk is spent. F-4's
substance survives intact: `cost`/`tokens` are allowlisted, `session_id` is not.

**ONE AUTHORED FINDING UNDERSTATED ITS OWN CASE.** F-3 says the correct channel is documented in "two
other places"; I found FOUR descriptive references to `prior_attempt_summary` and all four are
correct (`build_correction_notice`'s docstring, `build_prompt`'s comment, the `finalback` section
header, and the inline note at the projection call). That strengthens the plan rather than weakening
it: one wrong description against four right ones is a typo-class defect, which is exactly the
docstring fix being proposed, and not evidence of a confused design. Corrected in place.

**WHAT I DID NOT CHANGE.** The no-behavior-change posture, the allowlist membership (untouched, per
R1.1), the three Carrier-Declined deferrals (all three reasons are sound; the denylist one is
materially correct about fail-closed direction), OQ-01's resolution, and the decision to add a drop-side
test complementing rather than duplicating `tests/test_finalize_sendback.py` -- which I verified is
today the ONLY test file touching the projection at all, and only on the keep-side, so the plan's gap
analysis was accurate.

I also verified the V-04 sabotage control actually bites before requiring it: adding `"session_id"` to
the tuple changes the projection's output from `{'exit_code': 0, 'finalize_refused': 'r'}` to
`{'exit_code': 0, 'finalize_refused': 'r', 'session_id': 's'}`, so the non-vacuity demonstration is
real rather than decorative. `tests/test_finalize_sendback.py` is green at 53 passed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | A. correctness (a live-artifact count quoted as a fact) | re-derived at review: 85 / 68 vs the authored 80 / 63; delta attributed by `comm` against the `61ef21d8` key set | **THE KEY CENSUS DRIFTED BY FIVE IN DAYS AND WAS QUOTED AS A MEASUREMENT.** Five keys landed in merged work (`accounting_error`, `session_reconciliation_error`, `review_shared_commit`, `review_shared_commit_refused`, `review_shared_committed_paths`). The plan hedged them as indicative, which was honest, but a drifting live count belongs in prose as context and must be re-derived at execution, never cited as the bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern and F-2 now carry both pairs with the delta explained; E-01 re-derives the census at the executing HEAD and V-01 requires the executor to state what they measured rather than repeat either pair. |
| PR-002 | MEDIUM | UNDER-SCOPE | A. correctness; F. self-documentation (an incomplete contract) | `build_prompt`: `prior = item.get("attempts", [])[-1] if recovery and item.get("attempts") else None`; `prior_attempt_summary(None, Path('/tmp'))` -> `None` | **ALLOWLIST MEMBERSHIP IS NECESSARY BUT NOT SUFFICIENT, AND THE DRAFTED CONTRACT DOCUMENTED ONLY THE ALLOWLIST GATE.** The projection is reached only on a RECOVERY turn and reads only `attempts[-1]`, so a FIRST turn carries no prior-attempt key however the allowlist reads. An author following the contract as drafted would add their key and still get silence on turn one -- the same trap the plan exists to close, one step further on. `recovery` appeared in the plan only inside E-02's quoted text, never as a stated condition. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-5 and given its own E-item, E-05, with V-05; the Concern was updated; E-06 gains a first-turn assertion (`Prior attempt: none` despite an allowlisted key) and V-06 a matching non-vacuity control, so the clause is testable rather than merely asserted. |
| PR-007 | LOW | IN-SCOPE | G. right-sizing and conceptual density | `aw ipd lint --phase review-finalize --long` reporting `IPD-Z602` at E-03 after the first revision pass, against `conforming` on the authored file | **MY OWN FIRST REVISION MADE E-03 MULTI-CONCERN, AND THE LINTER CAUGHT IT.** Folding the driver-only example list and the new second-gate clause into E-03 produced three semicolon-chained action clauses in one item (contract text, example inventory, and a distinct code-path fact), which is exactly the density the right-sizing rule forbids and which the authored plan did not have. Recorded rather than silently repaired, because a reviewer who introduces a finding and quietly removes it has still shipped an unreviewed judgement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 split into three one-concern items: E-03 (the four-point contract), E-04 (the driver-only example block), E-05 (the second gate plus the docstring pointer). The test item became E-06. `Highest E allocated` raised 04 -> 06, V-04 and V-05 added, and the dependency edges and ordered-changes list renumbered. Re-linted `conforming` with no advisory. |
| PR-003 | LOW | IN-SCOPE | F. honest documentation (a dangling reference shipped in code) | `rg -n "the plan's E-04" agent_workflows` -> 1 hit, positioned ABOVE E-02's quoted start anchor; `xipfy1` E-04 found in `.aw/records/plans/executed/` | **A STALE "the plan" DEICTIC SURVIVES THE PLANNED EDIT.** The repaired paragraph opens "stated because the plan's E-04 demands...", where "the plan" is `xipfy1`, executed 2026-09-08. E-02's replacement span begins at the following sentence, so the reference would remain in shipped code and read to a future maintainer as the CURRENT plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as F-6; E-02 now requires naming `xipfy1` explicitly or dropping the justification clause, and V-02 requires `rg -n "the plan's E-04" agent_workflows` to return nothing. |
| PR-004 | LOW | IN-SCOPE | A. correctness (a stale artifact status) | `find .aw/records/plans -name '*zrvtm2*'` -> `executed/...`; `- Status: executed` | **F-4 CALLS `zrvtm2` A PENDING PLAN; IT IS EXECUTED.** Its keys are already in the tree (they are two of the five explaining PR-001's drift), so the overlap it flags for future attention is already spent. The finding's substance is unaffected: `cost`/`tokens` allowlisted, `session_id` not. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-4 corrected in place with the executed path and status, and its still-valid membership claims re-measured and retained. |
| PR-005 | LOW | IN-SCOPE | F. honest documentation (an understated finding) | `rg -n 'prior_attempt_summary' agent_workflows/` -> 6 hits, 4 descriptive and all correct | **F-3 UNDERCOUNTS ITS OWN SUPPORTING EVIDENCE.** It claims two other places document the channel correctly; there are four. This matters because it is the evidence that the defect is typo-class rather than a design confusion, which is what makes a docstring-only fix the right remedy. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-3 corrected to four with all four named, and a Project-conventions bullet records the same, so the isolation of the wrong description is on the record. |
| PR-006 | LOW | UNDER-SCOPE | E. testing (an unverified non-vacuity control) | executed the V-04 sabotage at review: output gains `'session_id': 's'` | **THE V-04 CONTROL WAS UNVERIFIED AT AUTHORING.** A demanded sabotage that turns out not to change behavior makes a validation item decorative. I executed it: adding `"session_id"` to the tuple does change the projection's output, so the control is sound. The new first-turn assertion needed its own control, which did not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 records the verified sabotage output inline so the executor knows what a real red looks like, and gains a second control (force `prior` to populate on a first turn; the new test must go red). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan documents a contract for reaching an isolated agent. Is allowlist membership the whole contract, or is there another gate? | THERE IS A SECOND GATE (recovery-only, `attempts[-1]`), and the contract must state it or it misleads the very author it is written for. | (a) Accept the drafted contract: rejected, because a contract that is true-but-incomplete about a SILENT failure mode reproduces the defect it documents; the plan's own Concern calls the silence the defect, so a partial remedy is a partial fix at best. (b) File the gap as a separate backlog item: rejected, the remedy is two sentences in a comment block this plan is already rewriting, so deferring it would leave the trap live while the plan that owns the file ships. | Measured `build_prompt`'s guarded `prior` expression and `prior_attempt_summary(None, Path('/tmp')) -> None`; the plan's `- Scope-Paths:` already declares both files, so no fence widening is needed. | yes |
| D-2 | Should the first-turn gate be documented only, or also pinned by a test? | ALSO PINNED, by one added assertion in the new test file. | (a) Document only: rejected on the plan's own logic. Its Concern says the failure is silent precisely because "a unit test asserting on the attempt dict still passes", so a contract clause with no test is exactly the artifact that rots next. (b) A broader prompt-rendering suite: rejected as scope creep; one assertion on one rendered first-turn prompt is sufficient and cheap. | The plan already adds a behavioral test file and already renders prompts in `tests/test_finalize_sendback.py`, so the mechanism is proven and in scope. | yes |
| D-3 | Two authored findings carry stale numbers/status. Correct them in place, or delete them? | CORRECT IN PLACE, keeping both the authored and the re-measured values with the delta explained. | (a) Delete and re-state: rejected, it destroys the evidence that the census DRIFTS, which is the reason E-01 must re-derive rather than cite; showing 80/63 -> 85/68 teaches the executor something a single fresh number cannot. (b) Leave them: rejected, a stale "pending" status on an executed plan sends a reader to the wrong lifecycle directory. | Delta attributed by `comm` against the `61ef21d8` key set; `zrvtm2` located in `executed/` with `- Status: executed`. | yes |
| D-4 | The plan demands a sabotage control (V-04, now V-06) whose effect was not verified at authoring. Require it as written, or check it first? | CHECK IT FIRST, and record the verified output in the item. | (a) Require as written: rejected, an unverified control can be decorative, and an executor who sabotages and sees green cannot tell a broken control from a broken test. (b) Drop the control: rejected outright, non-vacuity demonstration is exactly what keeps a behavior-unchanged test honest. | Executed the sabotage at review: the projection's output gains `'session_id': 's'`, so the control bites. | yes |
| D-5 | My own revision tripped the `IPD-Z602` density advisory on E-03. Absorb it silently, or record it and split? | RECORD IT AS PR-007 AND SPLIT E-03 into three one-concern items. | (a) Ship with the advisory: rejected, the repository's own right-sizing rule says a multi-concern E-item should be split, and a reviewer waving that away for their own edit applies a standard they would enforce on an author. (b) Split but not record it: rejected, it hides a judgement the maintainer may disagree with (three items where one was authored), and the review record exists precisely so such calls are checkable. (c) Revert the second-gate addition to keep E-03 small: rejected, that trades a real completeness gap (PR-002) for a cosmetic one. | `aw ipd lint --phase review-finalize --long` reported `IPD-Z602` at E-03 after my first pass and `conforming` on the authored file, so the advisory was mine; re-linted `conforming` after the split. | yes |

### Deferred and open

- (none). All seven findings were FIXED in place. None reached Medium-High or High Remediation Risk, so
  the Fix Bar permitted no deferral, and no question required the human: the one open question the
  plan carries (OQ-01) was already resolved by a maintainer ruling I verified on backlog `ytrz7u`'s
  history, and every finding above was settled by a measurement recorded with the command that
  produced it.

HONEST LIMIT, stated because it bounds what this round proves. This plan changes documentation and
adds a test; I verified the CLAIMS it makes and the completeness of the contract it will write, but the
contract's usefulness to a future author is a judgement I cannot measure. I also did not verify that
the E-04 first-turn assertion is implementable exactly as worded against `build_prompt`'s full
signature (it takes a `state`, a `run_dir` and a `plan_path`, so the test needs the same harness
scaffolding `tests/test_finalize_sendback.py` already builds); the mechanism is proven to exist there,
but wiring it is the executor's task and may need a different fixture shape than the one sentence in
E-04 implies. Finally, the key census I re-derived shares the plan's own pattern-based limitation: it
misses dict-literal writes, so both the authored and the re-measured pairs understate the true count.

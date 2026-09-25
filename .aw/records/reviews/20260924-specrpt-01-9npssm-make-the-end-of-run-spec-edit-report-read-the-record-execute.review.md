# Review findings: plan 9npssm

- Subject-Id: 9npssm
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed Order 01 of Set `specrpt`, the sole child, graduated from backlog `tm5vnx` (`bug`,
`Blocks-Release: next`; gate correctly inherited). Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` (exit 0) BEFORE semantic review. After the revisions,
`--phase review-finalize` reports exactly ONE diagnostic, `IPD-Q501`, which is the escalated blocking
question below doing its job rather than a structural defect. The plan file was committed and unchanged
(byte-identical to the lane input), so no pre-review snapshot was needed.

DISCLOSURE: a sibling model of the same family authored this plan, so treat this as near-self-review.
The diagnosis is excellent and reproduces in full; the blocker below is something no single-plan review
would find by reading this plan alone, since it lives in the interaction with another pending plan.

WHAT HOLDS, AND IT IS THE ENTIRE DIAGNOSIS. F-1: the writer stores `spec_edits_reconciliation` in shape
`{acks, reasons, reconciled, refused}` and the only reader reads `spec_edits` expecting
`{state, declared, modified_not_declared, declared_not_modified}` - three greps, exact. F-2 reproduces
to the character: after one real `record_item_spec_edits` call on a plan declaring `docs/A.spec.md` with
a reconcile returning `docs/B.spec.md`, the report prints `Reconciled 0 item(s); ... 1 never finalized.`
and `NOT FINALIZED: aaaaaa.` F-3, the worst case, reproduces exactly and is correctly graded "worse than
filed": an undeclared-spec-only run returns `[]` and writes an EMPTY STRING, while the same queue with a
reader-shaped record prints `UNDECLARED SPEC CHANGE(S)` and `bbbbbb modified (undeclared) ->
docs/B.spec.md`. So the managed AGENTS.md sentence "silence means 'no declared spec edits'" is false
today. F-4: `oc_runipd.record_item_spec_edits` has zero call sites, the name is absent from
`execute_item_core`'s `getattr(driver_module, ...)` list so the bare name resolves to the shared copy,
and the identity probe gives `oc is shared -> False`, `agy is oc -> True`. F-6: no test mentions
`spec_edit` or `report_run_spec`, and both `st5klo` test files are gone. Root cause attribution is right:
`git log -S 'item["spec_edits_reconciliation"] = record'` names `70a2059f` and nothing else. The
orphaned-fixture claim holds (`grep -rn runnerlayer_rehomed --include=*.py` -> 0 hits, while the fixture
does contain `spec_edit_summary`), so editing the reader trips no gate. Both finalize sites call the
recorder BEFORE `driver_finalize`, so E-05's "finalize may be patched" is sound. E-02/E-03's instructions
match the real signatures, and E-03's lossless claim is correct because `spec_edit_record` reads only the
KEYS of `reasons`/`acks`; I ran the conversion and it renders all three sections plus the refused case.

WHAT DOES NOT HOLD. One blocker that is invisible from inside this plan, and two accuracy defects.

```text
PR-001  two release-gating pending plans edit ONE constant, with nothing ordering them
  AGY_IMPORTS_FROM_OC_RUNIPD now = build_verify_and_continue_notice, classify_recovery_disposition,
                                   record_item_spec_edits, route_recovery_turn
  cdxcbh E-05 expected outcome    AGY_IMPORTS_FROM_OC_RUNIPD == frozenset({"record_item_spec_edits"})
  9npssm E-04                     removes exactly "record_item_spec_edits"
  both plans                      - Item-Dependencies: none     -> no order imposed
  simulated 9npssm first          set -> frozenset()   -> cdxcbh's assertion FALSE on correct work
  simulated cdxcbh first          set -> {record_item_spec_edits} then frozenset()  -> both hold
  consumers of the constant       grep -rn AGY_IMPORTS_FROM_OC_RUNIPD tests/ agent_workflows/
                                  -> 1 hit, the definition itself (so an empty set breaks no code)

PR-002  F-5's evidence is unobtainable where this plan executes
  .aw/records/runs/ in this lane  ABSENT (gitignored)  -> the 146/32/4 scan is unrunnable
  E-01 as authored                asked for observations "matching the Findings table"

PR-003  F-7's count is wrong; its conclusion is right
  grep -i "spec.edit|SPEC EDITS|spec_edit" on 25kzda   -> 1 hit, not 0
  that hit                        "WHY IT EXISTS, recorded because a spec edit changes the contract
                                  every plan is reviewed against" (gate-2 adjudication prose)
  -> no report description in the spec; no amendment needed, as the plan concludes

F-2 / F-3 reproduced verbatim
  item keys after record          ['spec_edits_reconciliation']     shape ['acks','reasons','reconciled','refused']
  declared-plan report            "Reconciled 0 item(s); ... 1 never finalized." / "NOT FINALIZED: aaaaaa."
  undeclared-only run             returned []   stream ''
  same queue, reader-shaped       "UNDECLARED SPEC CHANGE(S)" / "bbbbbb modified (undeclared) -> docs/B.spec.md"
  E-03 conversion, by hand        {'state':'reconciled','declared':['docs/A.spec.md'],
                                   'modified_not_declared':['docs/B.spec.md'],
                                   'declared_not_modified':['docs/A.spec.md']}  -> renders all 3 sections
  legacy refused -> UNVERIFIED    "the finalize precheck refused for cccccc, so no spec-edit claim is made"
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A (correctness) / C (architecture) | plan `E-04`; pending plan `cdxcbh` (Set `recovone`) `E-05` expected outcome; `runner_shared.AGY_IMPORTS_FROM_OC_RUNIPD`; both plans' `- Item-Dependencies: none` | TWO RELEASE-GATING PENDING PLANS EDIT THE SAME CONSTANT AND ONE ORDER FALSIFIES THE OTHER'S RECORDED EXPECTED OUTCOME, WITH NOTHING ORDERING THEM. `cdxcbh` E-05 removes the three recovery names and states as its expected outcome `AGY_IMPORTS_FROM_OC_RUNIPD == frozenset({"record_item_spec_edits"})`; this plan's E-04 removes exactly that name. Measured: the constant holds all four today; simulating both orders, only `cdxcbh`-first leaves both assertions true, while this-plan-first empties the set and makes `cdxcbh`'s equality FALSE. Both declare `- Item-Dependencies: none`, so the runner's dependency-depth sort imposes no order and either sequence can occur unattended. This is NOT the file-overlap non-hazard (isolated lanes and merge-and-revalidate handle that): it is a CONTENT contradiction between two recorded expected outcomes, so the cost is an executor spending a turn to discover a failed validation on work that is actually correct. No code consumes the constant, so an empty set is harmless; only a plan's expectation breaks. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | OPEN | ESCALATED as `OQ-03` with `- Blocking: yes` and `- Finding: PR-001` (the REVIEW finding id, which is what `check.review-finding-unescalated` joins on; an in-plan `F-*` id does NOT satisfy it, measured at review), which makes `aw ipd lint` refuse the plan at every checkpoint (verified: `IPD-Q501`) so it cannot execute into the contradiction. E-04 gained the full collision note with both orders measured, the instruction to REPORT rather than edit another plan's record, and a measurement that no consumer reads the constant. E-01 now requires the constant's membership pasted so the executor knows which order it is in. NOT fixed unilaterally: the recommended remedy (add `- Item-Dependencies: executed:cdxcbh`) changes what the runner executes and when, and the alternative edits a plan already `reviewed`/`go-pending-approval`; both are the maintainer's call. F-8 added. |
| PR-002 | MEDIUM | IN-SCOPE | E (verification) | plan `F-5` and `E-01`; `.gitignore` carrying `.aw/records/runs/` | F-5'S EVIDENCE CANNOT BE RE-DERIVED WHERE THIS PLAN WILL EXECUTE, AND E-01 INVITED AN EXECUTOR TO TREAT THAT AS DRIFT. `.aw/records/runs/` is gitignored, so in a lane worktree or a fresh clone it is absent entirely (measured: the directory does not exist here), making the 146/32/4 counts a property of one machine rather than a repository fact. E-01 asked for observations "matching the Findings table", so an executor who cannot run the scan could reasonably STOP on a figure that was never reproducible. Nothing in E-02..E-07 depends on those counts: E-03's conversion is proven by E-07's SYNTHETIC legacy record, which needs no run directory. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-5 now states plainly that the counts are not re-verifiable in a lane, that they must never become a pass bar, and that the legacy SHAPE (not the volume) is what E-03/E-07 need. E-01 gained an explicit instruction not to attempt the scan, not to read the main checkout for it, and to report unobtainability in one line and continue; the gate lists this as explicitly NOT a stop condition. F-9 added. |
| PR-003 | LOW | IN-SCOPE | A (correctness) | plan `F-7`; spec `25kzda` | F-7'S MEASUREMENT IS WRONG WHILE ITS CONCLUSION IS RIGHT. It claims the grep returns 0 lines on spec `25kzda`; it returns 1. The hit is unrelated prose inside the gate-2 adjudication section ("WHY IT EXISTS, recorded because a spec edit changes the contract every plan is reviewed against") and describes no report, so the conclusion - no spec governs this surface, no amendment needed - stands. Worth correcting because "the grep returns 0" is the kind of claim a later reader re-runs, and a non-zero result would look like the finding had rotted when only the count had. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-7 rewritten: count corrected to 1, the hit quoted and located, and the conclusion restated as confirmed. |
| PR-004 | LOW | IN-SCOPE | G (executability) | plan `OQ-01`; `runner_shared.spec_edit_record`; `runner_shared.compute_scope_reconciliation`; `render_stream.format_spec_edit_report` | OQ-01 WAS LEFT `open` AND MAINTAINER-OWNED WITHOUT SAYING THAT NOTHING WAITS ON IT, and without the facts a maintainer needs to answer. It is correctly `Blocking: no` (the default is to do nothing, and the plan changes no wording), but a reader seeing an open maintainer-owned question on a release-gating plan cannot tell whether execution is waiting on it. The answer also has a cost the question did not state: a positive "declared and modified" line needs a NEW record field and a new computation, not just a new string, because `spec_edit_record` returns exactly four keys and a declared-and-modified path is absent from BOTH `reasons` and `acks` by construction. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 now states that the default needs no decision to execute and why it is non-blocking, and records the verified facts: the exact four keys `spec_edit_record` returns, the exactly three per-path sections the renderer has, and that `reasons`/`acks` come from `out_of_scope_paths`/`in_scope_unmodified` so a declared-and-modified path is in neither. F-10 added recording that this is what makes E-05's absence assertion sound by construction rather than by luck. |
| PR-005 | MEDIUM | UNDER-SCOPE | G (executability) | plan `## Approval and execution gate` | THE GATE WAS ONE PARAGRAPH AND CARRIED NO EXECUTION CONTRACT BEYOND COMMIT DISCIPLINE. Missing: any statement of what a human is approving; the coverage hole that makes E-05/E-06/E-07 the sole safety net and the reason it exists (the regression landed green); a scope fence in declaration form; the bare-suite instruction; and any stop conditions at all. Most consequentially, once PR-001 escalated a blocking question, the gate said nothing about the plan being unexecutable until it is answered, and a gate is the first thing an executor reads. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten keeping `Size assessment: standard`, LEADING with the OQ-03 block and the lint refusal that enforces it; then what is being approved (a data-shape fix to a reporting surface, no control-flow change) with the total-silence measurement; the coverage hole with the show-it-failing obligation; a declaration fence naming the deliberate exclusions including the orphaned fixture; the honesty rule with the bare-`pytest` prohibitions and "do not substitute a count comparison" for E-08's node-ID bar; and three genuine stop conditions plus the explicit note that F-5's unobtainable counts are NOT one. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001: should this review fix the cross-plan collision itself (by adding a dependency here, or by amending `cdxcbh`)? | NO. Escalate it as a `- Blocking: yes` question (`OQ-03`) with three concrete options and a recommendation, and let the maintainer decide. | (a) Add `- Item-Dependencies: executed:cdxcbh` here unilaterally. Rejected: it changes WHICH plans the runner may dispatch and WHEN, which is a scope/priority decision reserved to the human, and it would silently delay a release-gating plan. (b) Amend `cdxcbh`'s E-05 expected outcome to `frozenset()`. Rejected harder: that plan is another artifact, already `reviewed` with `Readiness: go-pending-approval`, so editing its recorded expectation would invalidate a completed review without its own sign-off. (c) Say nothing and let an executor discover it. Rejected: it spends a real agent turn on a known contradiction, which is the waste the escalation exists to prevent. | The workflow's own Step 4 requires an unfixed finding at or above the gate threshold (default `HIGH`, confirmed absent from `.aw/config/project.json`) to be raised as a `- Blocking: yes` question carrying `- Finding:`. Measured that the lint gate then refuses the plan (`IPD-Q501`), so the escalation has teeth. Both plans' `- Item-Dependencies: none` and the simulated orders establish the contradiction is real and order-dependent. | yes |
| D-2 | Does an empty `AGY_IMPORTS_FROM_OC_RUNIPD` break anything, independently of the ordering question? | No. Recorded in E-04 so the executor does not hesitate at an empty set. | Assuming a consumer exists and defensively leaving one name in. Rejected: that would defeat E-04's purpose and was disproven by measurement. | `grep -rn "AGY_IMPORTS_FROM_OC_RUNIPD" tests/ agent_workflows/` returns exactly one hit, the definition itself. The constant's own comment says "this set SHRINKING is progress". So the only casualty of emptying it is `cdxcbh`'s recorded expectation, which is precisely why PR-001 is an ordering question and not a code question. | yes |
| D-3 | OQ-02 chose `spec_edits` as the surviving key. Is that right? | Yes; confirmed, no change. | `spec_edits_reconciliation` as the survivor, teaching the reader the new key. Rejected: it would require editing the reader, `report_run_spec_edits`'s docstring, and leave the 32 older on-disk items in the other shape, converting one legacy problem into two. | Measured: `spec_edits` is read by `spec_edit_summary`, named in the reader's docstring ("An older run directory carrying no `spec_edits` key"), and written by the pre-dedup `oc_runipd` fork; `spec_edits_reconciliation` has NO reader anywhere in the package (grep). E-03's side-read covers the records written in between, and `spec_edit_record` reads only the keys of `reasons`/`acks`, so the conversion is lossless (verified by running it). | yes |
| D-4 | Does this plan need a spec amendment, given it restores contractually documented behavior? | No; F-7's conclusion is correct and no `.spec.md` is declared. | Amending `25kzda` to describe the end-of-run report. Rejected: the spec has never described this surface, so an amendment would be new contract text rather than a fix, and writing one is a scope decision needing its own review. | `grep -i` on `25kzda` yields one hit, unrelated gate-2 prose (PR-003), and no report description. The behavior is stated in the managed AGENTS.md text generated from `engine.py` ("BOTH RUNNERS ALSO REPORT AT RUN END ... INCLUDING a spec that was modified WITHOUT being declared"), which this plan makes true again rather than changes. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author          --agent 9npssm -> {"outcome":"clean","exit":0,"findings":0}
aw ipd lint --phase review-finalize --agent 9npssm -> IPD-Q501 only (the escalated OQ-03; by design)
aw check release-gates                             -> errors 0  warnings 0

HEAD at review                     0a06a2d6   (plan authored against 877545fc)
lane input vs pending/ copy         byte-identical -> no pre-review snapshot needed

AUTHORED FINDINGS
  F-1 writer/reader key+shape split                              reproduced (3 greps, exact)
  F-2 finalized item reported NOT FINALIZED                      reproduced verbatim
  F-3 undeclared-only run prints NOTHING; counterfactual prints   reproduced verbatim
  F-4 oc fork has no caller; not in the getattr rebind list;
      oc is shared False, agy is oc True                          reproduced
  F-5 on-disk legacy counts                                      UNVERIFIABLE here -> PR-002
  F-6 no test touches this surface; st5klo test files deleted     reproduced
  F-7 spec 25kzda does not describe the report                    conclusion holds, count 1 not 0 -> PR-003
  root cause 70a2059f (git log -S)                                reproduced
  orphaned fixture: 0 python readers, contains spec_edit_summary   reproduced

FOUND AT REVIEW
  cdxcbh E-05 vs 9npssm E-04 both edit AGY_IMPORTS, neither ordered  -> PR-001 (BLOCKER, escalated)
  .aw/records/runs/ absent in a lane (gitignored)                    -> PR-002
  25kzda grep returns 1 unrelated hit, not 0                        -> PR-003
  spec_edit_record returns exactly 4 keys; renderer has 3 sections;
    declared-and-modified is in neither reasons nor acks             -> PR-004 / F-10

SUPPORTING VERIFICATION
  signatures of record_item_spec_edits / spec_edit_record /
    report_run_spec_edits match E-02/E-03/E-05 instructions          confirmed
  SPEC_RECONCILED 'reconciled' / SPEC_RECONCILE_REFUSED 'refused' /
    SPEC_NOT_FINALIZED 'not-finalized'                               confirmed
  both finalize sites call the recorder BEFORE driver_finalize       confirmed (E-05's premise)
  six report sites, three per host                                   confirmed
  E-03 conversion run by hand: renders all three sections; legacy
    refused renders under UNVERIFIED                                 confirmed (E-07's expected strings)
  test harnesses E-05/E-06 cite (_init_repo_with_conforming_plan,
    SelfFinalizeWiringTests, agy _state_and_item, run_agy_turn)       all exist
```

No production file was modified at any point; `git status --porcelain` showed only the plan file.

### Verdict and readiness

REVIEWED - OPEN QUESTIONS. PR-002 through PR-005 are FIXED. PR-001 is a BLOCKER left OPEN and escalated
into the plan as `OQ-03` (`- Blocking: yes`, `- Finding: PR-001`), which the lint gate now enforces at every
checkpoint. OQ-02 was already resolved from evidence and was independently confirmed (D-3). OQ-01 remains
`open` but `Blocking: no` with a default that requires no decision to execute, and per the 2026-09-10
maintainer ruling a non-blocking question does not itself force `NO-GO`.

Readiness `no-go`, for exactly one reason: an unresolved BLOCKING open question. This is NOT a judgement
on the plan's quality, which is high - the diagnosis reproduces in full, including the exact report
strings, and the fix is small and correctly scoped. It needs ONE human answer: in which order must this
plan and `cdxcbh` execute, given both edit `AGY_IMPORTS_FROM_OC_RUNIPD` and this-plan-first makes
`cdxcbh`'s recorded expected outcome false. The recommended answer is to add
`- Item-Dependencies: executed:cdxcbh` to this plan, which is enforced at dispatch and edits no other
artifact. Once answered and the question set `resolved`, this plan should re-read as
`GO - PENDING HUMAN APPROVAL` with no further review work; `aw ipd recheck-readiness 9npssm` recomputes
that verdict rather than requiring a fresh review.

Worth the maintainer's attention beyond the question: this plan is `Blocks-Release: next` and the defect
it fixes is total rather than cosmetic (an undeclared spec change currently prints nothing on either
host), so the ordering decision is on the critical path to the release rather than a nicety.

## Round 2

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | blocker | IN-SCOPE | A (correctness) / C (architecture) | plan `E-04`; pending plan `cdxcbh` (Set `recovone`) `E-05` expected outcome; `runner_shared.AGY_IMPORTS_FROM_OC_RUNIPD`; both plans' `- Item-Dependencies: none` | TWO RELEASE-GATING PENDING PLANS EDIT THE SAME CONSTANT AND ONE ORDER FALSIFIES THE OTHER'S RECORDED EXPECTED OUTCOME, WITH NOTHING ORDERING THEM. `cdxcbh` E-05 removes the three recovery names and states as its expected outcome `AGY_IMPORTS_FROM_OC_RUNIPD == frozenset({"record_item_spec_edits"})`; this plan's E-04 removes exactly that name. Measured: the constant holds all four today; simulating both orders, only `cdxcbh`-first leaves both assertions true, while this-plan-first empties the set and makes `cdxcbh`'s equality FALSE. Both declare `- Item-Dependencies: none`, so the runner's dependency-depth sort imposes no order and either sequence can occur unattended. This is NOT the file-overlap non-hazard (isolated lanes and merge-and-revalidate handle that): it is a CONTENT contradiction between two recorded expected outcomes, so the cost is an executor spending a turn to discover a failed validation on work that is actually correct. No code consumes the constant, so an empty set is harmless; only a plan's expectation breaks. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | STALE ESCALATION CLOSED 2026-09-25 by opencode/its_direct/pt3-claude-opus-5.5-1m-us. The question this finding was escalated as (OQ-03) is `- Status: resolved`, so the finding it gated on has been answered and the record is caught up. NO FINDING WAS RE-DERIVED and no plan content was re-critiqued: the match was made on the question's declared `- Finding: PR-001` back-reference, not on a judgement about what the question was about. Previous decision: open. |

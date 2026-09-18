# Review findings: plan a5wdne

- Subject-Id: a5wdne
- Subject-Type: ipd
- Reviewed-At: 2026-09-17
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `84f140da` in an isolated review lane. Structural preflight `aw ipd lint --phase author`
CONFORMED (exit 0) before revision. After revision the linter reports `IPD-Q501` BY DESIGN, because the
blocking OQ-03 I raised is the escalation of the unfixed BLOCKER PR-001; that is the gate working, not a
structural defect. No pre-review snapshot was needed: the plan was committed and unmodified.

THE STRUCTURAL PREMISE IS SOUND AND REPRODUCES EXACTLY, which is worth saying first because the rest of this
record is about defects. An AST scan of both runners at review HEAD:

```text
symbols defined in BOTH runners: 55
thin (delegates to runner_shared, <=3 statements both hosts): 21
forked: 34
forked excluding the 5 large functions: 29   (= 17 byte-identical + 12 divergent)
```

That is the plan's decomposition, symbol for symbol. The 17 byte-identical set verifies under
`ast.unparse` with docstrings stripped; `HostLabels` is exactly as described (`runner_shared.py:8530`, a
no-defaults `NamedTuple`, `OC_HOST_LABELS` and `AGY_HOST_LABELS` both bound); all three agy stubs really do
`from agent_workflows.oc_runipd import ...` (I read all three bodies); all five `rununify` plans are
`executed` and each contains `NO SPLIT WAS PERFORMED`; the maintainer's 2026-09-16 "DO THE SPLIT" directive
and the 100-percent-de-duplication wording are quoted accurately; and the `cjefq5` motivating defect is real
(`ee99c41d`, one inline allowlist missing an `executed` arm in both hosts). Order 02's F-4 is also correct
and I proved it rather than reading it: `test_review_findings_cascade.py:313` asserts
`assertNotIn("import oc_runipd", agy_src)`, the 9 real imports are spelled
`from agent_workflows.oc_runipd import` (so the substring is absent), and the guard PASSES today.

THE BLOCKER IS THE SET'S OWN CROSS-IPD RULE, AND IT IS WRONG BY A FACTOR OF FOUR. The rule reads "ONE PIN
TABLE, EDITED TWICE" and names `tests/test_rununify_initialize_run.py`. Measured, `STILL_DOUBLE_DEFINED`
tables live in FOUR files:

```text
test_rununify_build_parser.py   ('_add_output_mode_flags', '_detect_driver_command')
test_rununify_execute_item.py   ('_record_checkpoint_stop', '_record_forced_stop', 'driver_finalize',
                                 'evaluate_clean_base_for_launch', 'reconcile_disposition',
                                 'route_recovery_turn', 'set_plan_approved')
test_rununify_initialize_run.py ('enforce_dependency_preflight', 'expand_selectors', 'set_plan_approved')
test_rununify_run_queue.py      ('_observe_between_turn_stop', '_record_deliberate_stop',
                                 'disable_lane_prompt', 'execute_item', 'reclaim_lanes_on_interrupt',
                                 'reconcile_interrupted', 'requeue_interrupted',
                                 'retry_deferred_integrations')
```

Intersecting those against each child's symbol tranche, Order 01 must edit three of them and Order 02 must
edit three (a different three, overlapping in two). Each declares exactly one. And these are not passive
tables: each file asserts `assertFalse(_is_pure_delegation(defs[name]))` for every pinned name. I verified
the predicate directly rather than inferring, by importing the guard module and calling its own helper on a
simulated lifted body:

```text
execute_item pin file STILL_DOUBLE_DEFINED: (..., 'set_plan_approved')
guard's _is_pure_delegation(simulated lifted body) -> True
```

The guard asserts False, so the moment Order 01 lifts `set_plan_approved` the test FAILS, in a file Order 01
never declared. All 95 tests across the four files pass at review HEAD, so the failure would be new and
attributable. The executor then faces a red suite plus an undeclared edit, and the tempting exit is to delete
the pin entry, which is precisely what the maintainer's 2026-09-16 "re-base deliberately, never weaken
silently" ruling forbids. I did NOT fix this: the remedy is an edit to three CHILD plans' `Scope-Paths`, and
those plans are outside this review's ledger. Editing a sibling's fence during its parent's review would be
the undeclared widening this Set exists to make visible. It is OQ-03, `Blocking: yes`, carrying `Finding:
PR-001`, with the exact per-file additions written out.

THE SAME DEFECT IS ALREADY ON THE BACKLOG, which is what makes it worth escalating rather than noting.
`3dg3dv` (open) records that sibling `yrqyxb`'s `Scope-Paths` omitted three test files carrying
`execute_item` source pins. It recurred one Set later, in a Set whose cross-IPD rule was written to prevent
it. Declaration, not memory, is the fix.

ORDER 03 CANNOT EXECUTE ITS OWN RESOLVED BLOCKING RULING. Its OQ-02 (`Blocking: yes`, `Status: resolved`, the
maintainer's) commits E-02 to adding a host-id field to `HostLabels` and re-pointing
`run_analytics_sources.driver_generation` and `run_viewer` at it, with a documented fallback for pre-cutover
records. Its `Scope-Paths` declares only `runner_shared.py`, one new test file and `.aw/records/research`,
while its execution contract says "commit only the declared `Scope-Paths`". Both consumers exist
(`run_analytics_sources.py:183`; `run_viewer.py:865-867`, which does `if "oc_runipd" in driver_path`), and
because `HostLabels` has NO DEFAULTS by design, adding a field also forces edits to both hosts' bindings in
`oc_runipd.py` and `agy_runipd.py`. Four files the fence excludes.

THE PINNED SUITE BASELINE IS UNREACHABLE IN THE ENVIRONMENT THE SET WILL RUN IN. The plan pins `7825 passed,
3 skipped, 2 xfailed`. Measured at review HEAD:

```text
AW_EXECUTION_ROLE=worker   ->  31 failed, 7824 passed, 3 skipped, 2 xfailed
env -u AW_EXECUTION_ROLE   ->  7855 passed, 3 skipped, 2 xfailed
```

Neither is 7825, and no plan in the Set mentions `AW_EXECUTION_ROLE`. An executor in a managed worker lane
would record a false failure or "fix" 31 tests that refuse by design.

THE SET SILENTLY GRADUATES AN OPEN BACKLOG ITEM. `dstnso` (`open`, `high`) names seven `execute_item` closure
forks "claimed by no plan in the Set at all"; all seven are covered by Orders 01 and 02. No plan mentions it
and none carries `From-Backlog`, so the graduation is invisible to `aw attention` and to the backlog's own
close-legitimacy predicate. Added `- From-Backlog: dstnso` to this orchestrator.

AND E-01 IS THE ONLY CHECK FOR FOUR CRITERIA THAT RETIREMENT WILL NOT PERFORM. I read
`runner_shared.dispatch_orchestrator_item`: it calls `ipd_lifecycle.retire_orchestrator` on a disk-state
eligibility verdict with no E/V checkpoint on that path. The plan's closing note gestures at this ("If
executed by hand instead, E-01 must be genuinely performed") but the runner path is the DEFAULT, so as
authored the cross-Set fork count, the strengthened-guard property, pre-cutover attribution and the research
record are checked by nobody. Per AGENTS.md the correct fix for work parked on a parent is a CHILD, but three
of the four are already child-owned in substance, so the applicable mitigation is to require each criterion to
be owned by a child `V-*` too, which the Completion criteria now say explicitly.

THREE OF FOUR LINE FIGURES ARE UNREPRODUCIBLE. Only one metric reproduces: `ast.unparse` with docstrings
stripped gives the five large functions 884 and matches all five per-function figures exactly. Under that
same metric the 34 forks are 1448 (claimed ~1752), the 17 identical are 196 (claimed 380), the 12 divergent
are 368 (claimed 488). Raw spans give 4841/583/1088; spans-minus-docstrings give 408/987. The symbol COUNTS
reproduce perfectly, so the plan now says to treat counts as the gate and lines as indicative.

WHAT I FIXED. Corrected the pin-table rule with the full four-file, per-symbol ownership map and the proof it
is a guaranteed failure; added the Order 03 fence contradiction and the worker-lane baseline rule to Cross-IPD
validation; added `From-Backlog: dstnso` and a deferral bullet recording the graduation and the `graduated`
(not `done`) disposition; corrected the Completion criteria (six, with the scanner caveat, the non-vacuous
guard requirement, and both measured suite numbers); rewrote E-01 to verify all six and to name the
retirement limitation; strengthened V-01 to reject a vacuous import grep and to require each child's fence to
cover the pin files it edited; added a verified-at-review block to the Goal with the reproducible
decomposition and the line-figure correction; added the ~33-concurrent-plan note with the explicit statement
that the runner's worktree isolation makes it an author-time cost and NOT a runtime hazard; expanded the
execution contract with the finalize-justification wording, the shared-checkout re-verification step and the
per-child lifecycle gate; raised OQ-03 `Blocking: yes` with `Finding: PR-001`; and set `Readiness: no-go`.

WHAT I DID NOT DO. I did not edit any child plan, any test, or any product code. I did not resolve OQ-01 or
OQ-03: the first is a lifecycle-authority call and the second needs three child-plan edits I am not
authorized to make from this ledger.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | D. anti-regression; E. testing; G. executability | four pin tables enumerated by AST; `_is_pure_delegation(simulated lift)` -> True; `assertFalse` at `test_rununify_execute_item.py:190`, `test_rununify_run_queue.py:306`; `95 passed` at review HEAD | **THE SET'S OWN CROSS-IPD RULE NAMES ONE PIN FILE WHERE FOUR EXIST, AND EACH CHILD MUST EDIT THREE.** Orders 01 and 02 each declare exactly one. Each file asserts every pinned name is NOT a delegation, so the first lift fails a guard in an undeclared file. The executor then either makes unjustified out-of-scope edits or deletes the pin, which the maintainer's re-base ruling forbids. | C:Low; U:Low; S:Low; F:High; Overall:Medium-High | OPEN | ESCALATED as OQ-03 (`Blocking: yes`, `Finding: PR-001`). NOT fixed here: the remedy is `Scope-Paths` edits in three CHILD plans outside this ledger, and each child also needs matching E/V text. The full per-file, per-symbol ownership map is now written into Cross-IPD validation, plus a Required-tests item running the four files together (review baseline `95 passed`) so the failure surfaces immediately if it is executed anyway. |
| PR-002 | HIGH | UNDER-SCOPE | G. executability; A. correctness | Order 03 `Scope-Paths` line 7; its E-02 line 50; `run_analytics_sources.py:183`; `run_viewer.py:865-867`; `HostLabels` no-defaults docstring `runner_shared.py:8531-8539` | **ORDER 03's FENCE EXCLUDES FOUR FILES ITS OWN RESOLVED BLOCKING RULING COMMITS IT TO EDITING.** E-02 must re-point two analytics consumers and add a no-defaults `HostLabels` field (which forces both hosts' bindings), while the fence lists only `runner_shared.py`, one test file and the research dir, and the contract says commit only declared paths. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Recorded as a Cross-IPD validation rule naming all four files and stating E-02 is unexecutable as written until Order 03 declares them. Fixed at the orchestrator level (which owns cross-IPD sequencing) rather than by editing the child, for the same ledger reason as PR-001; unlike PR-001 this needs no new E/V text in the child, so the declaration is the whole fix. |
| PR-003 | HIGH | UNDER-SCOPE | E. testing (a false baseline would be recorded) | measured `31 failed, 7824 passed` with `AW_EXECUTION_ROLE=worker`; `7855 passed` with `env -u`; no plan in the Set mentions the variable | **THE PINNED SUITE BASELINE IS UNREACHABLE IN A MANAGED WORKER LANE, AND MATCHES NEITHER MEASUREMENT.** The plan pins `7825 passed` and requires "bare and green". An executor in a worker lane would record a false failure or "fix" 31 tests that refuse by design. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added a Cross-IPD rule: state which form you ran, never edit those tests, and gate on NO NEW failures against a like-for-like baseline rather than an absolute count. Both measured numbers written into the Completion criteria, superseding the authored figure. |
| PR-004 | HIGH | UNDER-SCOPE | G. traceability; release-gate integrity | `dstnso` (`Status: open`, `Priority: high`) names 7 symbols; all 7 matched against Orders 01/02 tranches; no `From-Backlog` in any of the four plans | **THE SET GRADUATES AN OPEN BACKLOG ITEM WITH NO LINK.** `dstnso`'s seven "claimed by no plan" symbols are all covered here, but nothing records the handoff, so it is invisible to `aw attention` and to the backlog close-legitimacy predicate, and the item would sit `open` forever or be closed with no provable handoff. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added `- From-Backlog: dstnso` to this orchestrator and a deferral bullet naming all seven symbols with their owning Order, stating the item should move to `graduated` and NOT `done`, and recording that siblings `3dg3dv` and `9eiwnl` are NOT graduated by this Set. |
| PR-005 | HIGH | IN-SCOPE | A. correctness (a verification nobody performs) | `runner_shared.dispatch_orchestrator_item:6683-6760` calls `ipd_lifecycle.retire_orchestrator` on a disk-state verdict; no E/V checkpoint on that path | **FOUR COMPLETION CRITERIA ARE CHECKED ONLY BY E-01, WHICH RETIREMENT MARKS COMPLETE WITHOUT PERFORMING.** The runner path is the default, so the cross-Set fork count, the strengthened-guard property, pre-cutover attribution and the research record would be verified by nobody. The plan's closing note addresses only the hand-executed case. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 and the gate now state the retirement mechanism explicitly (read from the code, not inferred), and the Completion criteria require every criterion to ALSO be owned by a child `V-*` wherever possible, which is the mitigation available to a parent that must not hold work of its own. |
| PR-006 | MEDIUM | UNDER-SCOPE | E. testing (a criterion depending on a tool that does not exist) | no whole-runner fork scanner in `tests/`; the five `test_rununify_*` files pin per-function tables only | **"MEASURED BY THE SAME AST SCAN THAT PRODUCED THE BASELINE" NAMES A SCANNER THAT IS NOT COMMITTED.** The authoring scan was ad hoc, so the Set's headline criterion cannot be re-run as written, and E-01 would have to re-invent it and might measure something else. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Both the criterion and E-01 now require a COMMITTED scanner that STATES ITS METRIC, produced by Order 01's E-01, and pin the SYMBOL count as the gate. |
| PR-007 | MEDIUM | IN-SCOPE | A. correctness (unreproducible measurements presented as measured) | `ast.unparse` normalized: 34 forks = 1448 (claimed ~1752), 17 identical = 196 (claimed 380), 12 divergent = 368 (claimed 488); the 5 large = 884 EXACTLY as claimed; raw spans 4841/583/1088; spans-minus-doc 408/987 | **THREE OF FOUR LINE FIGURES MATCH NO METRIC I COULD REPRODUCE, while the fourth matches one exactly.** The Set repeats these figures in its Concern, Scope check and Deferred sections and in all three children, so a reader cannot tell which numbers are trustworthy. The symbol counts reproduce perfectly. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | A verified-at-review block in the Goal states which metric reproduces, gives all three alternative measurements, and directs the reader to treat symbol counts as load-bearing and line figures as indicative until Order 01's committed scanner re-derives them. The Scope check's "~1752 to ~884" mixed-metric claim corrected to the honest "34 -> 5 symbols". |
| PR-008 | MEDIUM | IN-SCOPE | G. executability (an incomplete verification list) | E-01 said "each of the four properties"; the Completion criteria list six | E-01's own expected outcome verified four properties while the Set defines six completion criteria, so pre-cutover attribution and the research record were in the criteria but in no execution item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 rewritten to verify all six explicitly; V-01 already listed six and now also requires the four-pin-file run and each child's fence coverage. |
| PR-009 | MEDIUM | UNDER-SCOPE | E. testing (a guard that proves nothing) | `test_review_findings_cascade.py:308-313`; 9 imports spelled `from agent_workflows.oc_runipd import`; guard run green at review | The strengthened runner-import guard Order 02 will write could pass both before and after and nobody would notice, since its predecessor passes today with 9 violations present. A guard not shown failing against unmodified HEAD is untested. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added a Required-tests item demanding the new guard be shown FAILING against unmodified HEAD, and V-01 now explicitly rejects a `grep "import oc_runipd"` as evidence, naming it as the vacuous form. |
| PR-010 | LOW | IN-SCOPE | C. operability (an unstated concurrency cost) | ~33 pending plans declare these runner files, most `approved`; 4 name `set_plan_approved`, 5 name `expand_selectors` | The Set relocates 29 symbols that other pending plans quote by location, and nothing recorded that. Worth stating so a reader does not discover it as a surprise. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as a Deferred bullet that also states plainly, per AGENTS.md, that this is NOT a runtime hazard (the runner isolates each item's worktree and merges through a revalidation gate) but an author-time staleness cost, and asks nothing of any child. Recorded this way deliberately to avoid the "author-time note read as a live operational hazard" failure AGENTS.md warns about. |
| PR-011 | LOW | UNDER-SCOPE | G. executability (missing execution-contract elements) | the authored gate had the worktree, path-scoped-commit and never-push clauses but no finalize-justification wording, no shared-checkout re-verification, no per-child lifecycle gate | The execution contract omitted three elements the repository requires: how an out-of-scope edit is justified at finalize, the `git diff --cached --name-only` re-verification for a shared checkout, and the per-child `aw ipd lint --phase pre-transition` gate before `executed`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three added, with the finalize wording in the DECLARE-and-JUSTIFY form (never "STOP and report" for a scope question) per the 2026-09-01 maintainer ruling. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001's fix is an edit to three CHILD plans. Make it, or escalate? | ESCALATE as a blocking open question, with the exact edits written out, and fix at the orchestrator level only what the orchestrator owns (the cross-IPD ownership map). | (a) Edit the three children's `Scope-Paths` myself, rejected: they are not in this review's ledger, each also needs matching E-item and V-item text to make the re-base deliberate, and silently widening a sibling's fence is the exact failure this Set exists to surface. (b) Note it as a MEDIUM and let each child's own review catch it, rejected: it is a guaranteed suite failure that stops execution, and the same defect class is ALREADY on the backlog as `3dg3dv` from one Set earlier, so "a later review will catch it" is a hypothesis the evidence refutes. | four pin tables enumerated by AST; `_is_pure_delegation` returning True on a simulated lift; `3dg3dv` recording the identical defect in sibling `yrqyxb` | yes |
| D-2 | Is PR-001 really a BLOCKER, or a HIGH? | BLOCKER. It causes a normal-path failure: the first lift turns a green suite red in a file the executor was never told to touch. | (a) HIGH, rejected: the workflow reserves BLOCKER for a normal-path failure or silent invariant violation, and this is both, since the tempting recovery (deleting a pin entry) silently removes the guard the maintainer ruled must be re-based. (b) MEDIUM, rejected outright given the measured predicate result. | workflow severity definitions; `assertFalse` guards in two files; the maintainer's 2026-09-16 re-base ruling quoted at `test_rununify_initialize_run.py:40-44` | yes |
| D-3 | PR-002 is also a child-plan fence defect. Why fix it here when PR-001 was escalated? | FIX IT HERE as a cross-IPD rule, because unlike PR-001 it needs no new E/V text in the child: E-02 already names both consumers, so only the DECLARATION is missing, and cross-IPD sequencing is what an orchestrator owns. | (a) Escalate it too, rejected: two blocking questions for one class of fix would make the maintainer adjudicate twice; the OQ-03 answer will cover both mechanically. (b) Edit Order 03's fence, rejected for the same ledger reason as D-1. | Order 03 E-02 already names `run_analytics_sources.driver_generation` and `run_viewer`; `HostLabels` no-defaults docstring forcing both host bindings | yes |
| D-4 | The line figures do not reproduce. Recompute and rewrite them, or flag them? | FLAG THEM with all three candidate metrics and pin the SYMBOL counts as the gate. | (a) Rewrite every figure to my `ast.unparse` numbers, rejected: I cannot know which metric the author used, the figures appear in three children too, and substituting mine would replace one unverifiable set with another while making the children inconsistent with their parent. (b) Say nothing since counts reproduce, rejected: the figures are quoted in the Concern as the cost argument, so a reader deciding whether the Set is worth funding is reading numbers nobody can reproduce. | four metrics computed at review; the 884 figure matching exactly under `ast.unparse` while three others match nothing | yes |
| D-5 | Should I raise the ~33 concurrent pending plans as a hazard? | RECORD IT AS AN AUTHOR-TIME COST AND EXPLICITLY NOT A RUNTIME HAZARD. | (a) Warn that the Set is unsafe to run concurrently, rejected and specifically forbidden: AGENTS.md records that the runner already isolates each execute item's worktree and merges through a revalidation gate, and that presenting file overlap as a runtime hazard wastes the maintainer's time on a settled question. (b) Omit it, rejected: 29 relocations against ~33 plans that quote symbol locations is a real staleness cost worth one bullet. | AGENTS.md runner-ownership paragraph; `isolate_worktree` default; measured 4 plans naming `set_plan_approved`, 5 naming `expand_selectors` | yes |
| D-6 | E-01 is the only check for four criteria the runner's retirement will not perform. Add children, or mitigate? | MITIGATE by requiring each criterion to be child-owned too, and state the retirement mechanism explicitly. | (a) Add child plans for the four criteria, rejected: three of the four are already child-owned in substance (Order 03 owns the third host and pre-cutover attribution and the research record; Order 02 owns the guard), so new children would duplicate them, and AGENTS.md's "add a child" rule targets work covered by NO child. (b) Delete E-01, rejected outright: AGENTS.md records that deleting an orchestrator's checklist causes the lost work it exists to prevent, since most Sets are executed by an agent told "execute <setid>" with no runner involved. | `dispatch_orchestrator_item` read at review (no E/V checkpoint); AGENTS.md orchestrator-checklist paragraph | yes |
| D-7 | Verdict and readiness, given one OPEN BLOCKER? | `REVIEWED - OPEN QUESTIONS`, readiness `no-go`, and `Status: reviewed`. | (a) `APPROVE WITH REVISIONS APPLIED` / `go-pending-approval`, rejected: PR-001 is left OPEN at BLOCKER severity, which is exactly the condition the readiness table calls a genuine not-ready state; claiming otherwise would greenwash a Set that cannot execute. (b) `REJECT - NEEDS REPLAN`, rejected: the approach is sound, the premise reproduces exactly, and the blocker is a three-line declaration fix in three sibling plans, which is a bounded edit and not a replan. | workflow verdict/readiness tables; PR-001 `Decision: OPEN`; `aw ipd lint` now refusing on OQ-03 by design | yes |

### Escalation of the irreversible decisions

None of this round's seven decisions is judged `Reversible: no`. Every one is undone by editing this plan
before it executes: nothing here publishes an interface, migrates data, deletes anything, or produces a
released artifact. The one decision that touches a durable record is D-1's escalation route, and it is
reversible in the safe direction: leaving OQ-03 blocking means the plan cannot execute until a human answers,
so a wrong call costs one round trip rather than a bad merge. Stated explicitly rather than left blank.

### Honest limits of this review

- I DID NOT REVIEW THE THREE CHILD PLANS. They were not in the invocation and no documented eligibility rule
  adds them, so I read them only as EVIDENCE about this orchestrator's claims. Each needs its own review
  round, and PR-001 and PR-002 will have to be applied there.
- I DID NOT SIMULATE A REAL LIFT. I proved PR-001 by importing each guard module and calling its own
  `_is_pure_delegation` helper on a synthetic delegating body, in-process, with no file modified (verified
  `git status --porcelain` clean afterwards). I did not perform the relocation and then run the suite, which
  is what the children's V-items must do.
- MY THIN-WRAPPER CLASSIFIER IS MY OWN HEURISTIC (body of at most three statements referencing
  `runner_shared`), not the repository's. It happens to reproduce the 21/34 split exactly, which is why I
  trust the decomposition, but a symbol classified differently by the committed scanner PR-006 asks for could
  move the boundary by one or two names.
- I DID NOT VERIFY THE `cjefq5` RUN-LEVEL IMPACT FIGURES (6 plans, 2 orchestrators, 13 runs, worst losing
  16 items). I verified the FIX commit `ee99c41d`, its message describing the same mechanism, and that the
  defect was one expression present in both hosts. The per-run counts remain the author's.
- I DID NOT RUN A DRIVER EXECUTION. The Set's own Required-tests section says structural verification is
  insufficient because it moves lock, stop-trigger, recovery and integration-retry machinery; I agree and did
  not attempt it, so nothing here validates the Set's runtime behavior.
- I DID RUN THE FULL SUITE TWICE, which is how PR-003 was found: `31 failed, 7824 passed, 3 skipped, 2
  xfailed` with `AW_EXECUTION_ROLE=worker`, and `7855 passed, 3 skipped, 2 xfailed` with `env -u`.
- I DID NOT RESOLVE OQ-01. The fate of the five `rununify` plans is a lifecycle-authority question and the
  plan is right that it blocks nothing here; I verified its factual account (all five `executed`, all five
  saying `NO SPLIT WAS PERFORMED`, the directive quoted accurately) and left the routes as stated.

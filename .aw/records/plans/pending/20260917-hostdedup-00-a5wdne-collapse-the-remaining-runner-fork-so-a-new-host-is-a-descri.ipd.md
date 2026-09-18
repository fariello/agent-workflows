# IPD: Collapse the remaining runner fork so a new host is a descriptor not a runner

- Date: 2026-09-17
- Kind: orchestrator
- Concern: `oc_runipd.py` (9588 lines) and `agy_runipd.py` (5784) still define 34 forked symbols totalling roughly 1752 lines, and the maintainer intends to add runners for codex, claude and hermes. At two hosts a duplicated symbol is written twice; at five it is written five times, and every fix must be remembered five times. This is already costing real defects rather than merely offending taste: `cjefq5`, fixed 2026-09-17, was ONE expression present byte-identically in both runners that mislabeled an executed plan `reviewed` and killed six approved plans plus two orchestrators at queue build across 13 separate runs. The `rununify` Set reduced the fork substantially (`runner_shared.py` grew 773 -> 9182 lines) but its last five children (07-11, the five large functions) were re-scoped at review into analysis-only and each records `NO SPLIT WAS PERFORMED`.
- Scope: Finish the job for everything except the five large functions, and PROVE the result by adding a third host that has no runner module. Order 01 lifts the 17 byte-identical symbols; Order 02 unifies the 12 divergent ones behind the existing `HostLabels` descriptor and fixes the inverted agy->oc dependency; Order 03 demonstrates a runner-less host end to end. The five large functions are deliberately NOT re-planned here (see OQ-01).
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: none
- Status: to-review
- Readiness: no-go
- From-Backlog: dstnso
- Set: hostdedup
- Order: 0
- Highest E allocated: 01
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: a5wdne

## Workflow history
- 2026-09-17 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001..PR-011; readiness `no-go` on ONE blocking finding I could not remediate inside this plan. Reviewed at HEAD `84f140da`; `aw ipd lint --phase author` conforming before and after. THE STRUCTURAL PREMISE IS SOUND AND REPRODUCES EXACTLY: an AST scan finds 55 symbols co-defined in both runners, 21 of them the sanctioned thin-wrapper form and 34 real forks, of which 5 are the large functions and 29 are this Set's targets, splitting 17 byte-identical + 12 divergent exactly as authored. `HostLabels` is as described (`runner_shared.py:8530`, no-defaults `NamedTuple`, both host instances bound). The three agy stubs really do `from agent_workflows.oc_runipd import ...` (inverted dependency, verified by reading all three bodies). The vacuous guard is real: `test_review_findings_cascade.py:313` asserts `assertNotIn("import oc_runipd", agy_src)` while 9 imports spelled `from agent_workflows.oc_runipd import` exist, and I ran the guard green to prove it. All five `rununify` plans are `executed` and each says `NO SPLIT WAS PERFORMED`; the maintainer's 2026-09-16 "DO THE SPLIT" directive is quoted accurately. The `cjefq5` motivating defect is real (`ee99c41d`). THE BLOCKER: the Set's own cross-IPD rule says "ONE PIN TABLE, EDITED TWICE" and names one file, but `STILL_DOUBLE_DEFINED` pin tables live in FOUR test files, and Orders 01 and 02 each must edit THREE of them while each declares only ONE. Proven with the guards' own predicate: `_is_pure_delegation` returns True for a lifted body and the guard asserts False for every pinned name, so lifting `set_plan_approved` fails `tests/test_rununify_execute_item.py` (undeclared by Order 01). Also: Order 03's E-02 mandates editing two analytics consumers its fence excludes; the pinned suite baseline is unreachable in a worker lane (measured 31 failed / 7824 passed with `AW_EXECUTION_ROLE=worker`, 7855 passed with it unset); the Set silently graduates open backlog `dstnso` with no `From-Backlog` link (added); the "same AST scan" the criteria rely on is not committed anywhere; and three of the four line figures are unreproducible under any metric. OQ-03 raised `Blocking: yes` carrying PR-001.
- 2026-09-17 to-review (aw set): Authored 2026-09-17 from an AST measurement at HEAD (34 forked symbols / ~1752 oc lines across the two runners); complete enough to critique

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Make "adding a host is writing a descriptor, not a runner" TRUE and DEMONSTRATED, before three more hosts
multiply the cost of it being false.

THE GOOD NEWS FIRST, because it shapes the whole Set: the abstraction already exists.
`runner_shared.HostLabels` (`runner_shared.py:8530`) is a no-defaults `NamedTuple` carrying every
host-varying string a lifted symbol needs (`command`, `review_command`, `argv_tokens`,
`argv_subcommands`, `product`, `report_title`, `shell_tool`) plus one capability flag
(`emits_launch_identity`), with `OC_HOST_LABELS` and an agy twin bound by each host's thin wrappers. 21
symbols already delegate to `runner_shared` on both hosts. So this Set is not designing a new
architecture; it is finishing the migration into one that is already load-bearing, and then testing it in
the direction it has never been tested: a host with no runner of its own.

THE ORDERING IS BY RISK, ASCENDING, which is deliberate. Order 01 is 17 byte-identical symbols where the
shared body is the current body verbatim and no decision exists to get wrong. Order 02 is 12 symbols that
genuinely differ and need per-symbol judgement. Order 03 is the experiment that can only be meaningful
once the first two have removed the noise. Doing them in the reverse order is roughly how `rununify` 07-11
stalled: hardest first, decisions unresolved, nothing landed.

VERIFIED AT REVIEW (2026-09-17, HEAD `84f140da`), so no child re-derives the decomposition and no reader
mistakes which numbers to trust. An AST scan of the two runners reproduces the structural claim EXACTLY:
55 symbols co-defined, 21 sanctioned thin wrappers, 34 real forks, of which the 5 large functions and 29
Set targets split 17 byte-identical (verified by `ast.unparse` with docstrings stripped) + 12 divergent.
`HostLabels` is exactly as described. The 3 agy stubs really do import from `oc_runipd`. The guard hole is
real and I ran it green while 9 such imports exist.

BUT THE LINE FIGURES ARE NOT ALL REPRODUCIBLE, and only one metric is: `ast.unparse`-normalized lines with
docstrings stripped gives the five large functions 884, matching this plan and each child exactly (436/133/
150/119/46). Under that SAME metric the other figures do not match: the 34 forks are 1448 lines not ~1752,
the 17 identical are 196 not 380, the 12 divergent are 368 not 488. Raw source spans give 4841 / 583 / 1088;
spans minus docstrings give 408 / 987. So THREE of the four figures match no metric I could reproduce.
Treat the SYMBOL COUNTS as the load-bearing numbers (they reproduce exactly and are what the criteria can
verify) and the line figures as indicative only, until E-01 of Order 01 re-derives them with a COMMITTED
scanner that states its metric.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Set-level acceptance

- [ ] E-01 After all three children are `executed`, verify and record the Set's combined result against ALL SIX completion criteria below, not four: the forked-symbol count has fallen from 34 to the five large functions alone; no runner imports the other runner AND the guard rejects the coupling rather than one spelling; a third host runs with no runner module of its own and attributes correctly; a PRE-CUTOVER run record still attributes correctly; the host contract is immortalized under `.aw/records/research/`; and the suite is green. This orchestrator holds no work of its own beyond this verification. READ THE RETIREMENT NOTE IN THE GATE FIRST: if the runner retires this Set, this item is marked complete WITHOUT being performed, so the criteria that only E-01 checks (the cross-Set fork count and the two Order-03 durability properties) are verified by nobody. That is a known limitation of orchestrator retirement, not something this plan can fix, and it is why each of the six criteria is ALSO owned by a child V-item wherever possible.
  - Depends on: none
  - Expected outcome: a measured before/after count using the COMMITTED scanner E-01 of Order 01 must produce (see PR-006: no such scanner exists in-tree today, so "the same AST scan" cannot be re-run as the criteria assume), stating its metric, against the 34-symbol baseline. Symbol counts are the gate; line figures are indicative (see the Goal). Evidence for each of the six properties. A regression in any one means the Set is not done regardless of the children's individual states.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | `.aw/records/plans/pending/20260917-hostdedup-01-li44r9-lift-the-seventeen-byte-identical-runner-symbols-into-runner.ipd.md` | Lift the 17 byte-identical symbols (380 oc lines) to one definition each; pure move, no behavior change; re-base the guard that pins them as forked | none |
| 02 | `.aw/records/plans/pending/20260917-hostdedup-02-nmlx47-unify-the-twelve-small-divergent-symbols-behind-hostlabels.ipd.md` | Unify the 12 divergent symbols (488 oc lines) per shape: reconcile 7 drifted, re-point 3 agy stubs off `oc_runipd`, express 2 real differences via `HostLabels`; close the vacuous runner-to-runner guard | `executed:li44r9` |
| 03 | `.aw/records/plans/pending/20260917-hostdedup-03-xdvglg-prove-the-descriptor-seam-by-adding-a-third-host-with-no-new.ipd.md` | Implement the maintainer's host-id ruling, then add a third host defined only by a descriptor and drive a real execution through it; classify whatever the seam cannot express | `executed:nmlx47` |

## Completion criteria (the whole Set is done only when)

- The forked-symbol count has fallen from 34 to the five large functions alone (17 lifted by Order 01, 12
  unified by Order 02), measured by a COMMITTED scanner that states its metric. NOTE (PR-006): "the same AST
  scan that produced the baseline" does not exist in-tree; the authoring scan was ad hoc and is not
  reproducible, so Order 01's E-01 must commit one and this criterion is measured with THAT. The gate is the
  SYMBOL COUNT (34 -> 5), which reproduced exactly at review; line figures are indicative only.
- No runner imports the other runner, and the guard that forbids it rejects the COUPLING rather than one
  spelling of it. Measured at review: 9 imports of the form `from agent_workflows.oc_runipd import` exist
  while `test_review_findings_cascade.py:313` asserts only `assertNotIn("import oc_runipd", agy_src)` and
  PASSES, so the strengthened guard must FAIL against today's source before it is trusted.
- A third host completes a real IPD execution with NO runner module of its own, and its run attributes to
  that host rather than `unknown`.
- Pre-cutover run records still attribute correctly, per the maintainer's host-id ruling.
- The measured host contract is immortalized under `.aw/records/research/`, so the codex/claude/hermes work
  starts from it.
- The suite shows NO NEW failures against a baseline taken THE SAME WAY (see the worker-lane rule in
  Cross-IPD validation). Re-measured at review HEAD `84f140da`: `env -u AW_EXECUTION_ROLE python3 -m pytest`
  gives `7855 passed, 3 skipped, 2 xfailed`; a bare run in a worker lane gives `31 failed, 7824 passed`. The
  authored `7825 passed` figure matched neither and is superseded by these two.

EACH OF THESE SIX IS ALSO OWNED BY A CHILD `V-*` WHEREVER POSSIBLE, deliberately, because of the retirement
limitation recorded in E-01 and the gate: a criterion checked ONLY here is a criterion nobody checks when
the runner retires the Set.

## Cross-IPD validation

- ORDER MATTERS AND IS DECLARED, not left to Set/Order (which is only a tiebreaker): Order 02 depends on
  `executed:li44r9` and Order 03 on `executed:nmlx47`. Order 02's reconciliations are easier to review once
  Order 01 has removed the 17 identical symbols from the diff, and Order 03's third-host experiment is only
  meaningful once the seam is the single path.
- FOUR PIN TABLES, NOT ONE, AND EACH CHILD MUST EDIT THREE OF THEM. **CORRECTED AT REVIEW; the authored
  version of this rule named one file and was the Set's most consequential defect (PR-001).** A
  `STILL_DOUBLE_DEFINED` table lives in FOUR test files, measured:
  - `tests/test_rununify_execute_item.py`: `_record_checkpoint_stop`, `_record_forced_stop`,
    `driver_finalize`, `evaluate_clean_base_for_launch`, `reconcile_disposition`, `route_recovery_turn`,
    `set_plan_approved`
  - `tests/test_rununify_run_queue.py`: `_observe_between_turn_stop`, `_record_deliberate_stop`,
    `disable_lane_prompt`, `execute_item`, `reclaim_lanes_on_interrupt`, `reconcile_interrupted`,
    `requeue_interrupted`, `retry_deferred_integrations`
  - `tests/test_rununify_initialize_run.py`: `enforce_dependency_preflight`, `expand_selectors`,
    `set_plan_approved`
  - `tests/test_rununify_build_parser.py`: `_add_output_mode_flags`, `_detect_driver_command`

  SO THE ACTUAL OWNERSHIP IS:
  - ORDER 01 must edit `test_rununify_execute_item.py` (`_record_checkpoint_stop`, `driver_finalize`,
    `evaluate_clean_base_for_launch`, `set_plan_approved`), `test_rununify_run_queue.py`
    (`_observe_between_turn_stop`, `_record_deliberate_stop`, `disable_lane_prompt`, `requeue_interrupted`)
    and `test_rununify_initialize_run.py` (`set_plan_approved`). It declares only the last.
  - ORDER 02 must edit `test_rununify_execute_item.py` (`_record_forced_stop`, `reconcile_disposition`,
    `route_recovery_turn`), `test_rununify_run_queue.py` (`reclaim_lanes_on_interrupt`,
    `reconcile_interrupted`, `retry_deferred_integrations`), `test_rununify_initialize_run.py`
    (`enforce_dependency_preflight`, `expand_selectors`) and `test_rununify_build_parser.py`
    (`_add_output_mode_flags`). It declares only the third.

  THIS IS NOT A DOCUMENTATION NIT, IT IS A GUARANTEED FAILURE, proven at review with the guards' OWN
  predicate rather than argued: each file asserts `assertFalse(_is_pure_delegation(defs[name]))` for every
  pinned name, and `_is_pure_delegation` returns True for a lifted delegating body (measured directly by
  importing the guard module and calling it on a simulated lift). So the moment Order 01 lifts
  `set_plan_approved`, `test_rununify_execute_item.py` FAILS, in a file Order 01 never declared, and the
  executor faces a red suite plus an out-of-scope edit it must justify at finalize. All 95 tests across the
  four files pass at review HEAD, so the failure would be NEW and attributable to the lift.
  EACH CHILD MUST ADD ITS THREE FILES TO `Scope-Paths` BEFORE EXECUTION. Each must edit only its own
  symbols and must not delete an assertion to make the suite pass: moving a name from
  `STILL_DOUBLE_DEFINED` to `THIN_WRAPPERS_OVER_RUNNER_SHARED` in the same change that lifts it is the
  sanctioned re-base (the maintainer's 2026-09-16 "re-base deliberately, never weaken silently" rule, quoted
  in `test_rununify_initialize_run.py:40-44`), and deleting the entry outright is not.
- NO CHILD MAY CHANGE BEHAVIOR TO ACHIEVE DE-DUPLICATION. Order 01 is a pure move. Order 02 preserves a
  real host difference through the descriptor rather than picking a winner. If either finds a behavior
  difference that spec `25kzda` governs, it stops and records a blocking question.
- THE THREE CHILDREN MUST NOT INVENT A SECOND HOST SEAM. `HostLabels` is the one descriptor; a child that
  needs a new host-varying value adds a FIELD to it, justified by a named consumer, rather than introducing
  a parallel mechanism.
- ORDER 03's FENCE IS NARROWER THAN ITS OWN MANDATE (PR-002, added at review). Its resolved `Blocking: yes`
  OQ-02 commits E-02 to re-pointing `run_analytics_sources.driver_generation` and `run_viewer` at an
  explicit host id, and to adding a host-id FIELD each host must then bind; but its `Scope-Paths` declares
  only `runner_shared.py`, one new test file and `.aw/records/research`, while its execution contract says
  "commit only the declared `Scope-Paths`". Both consumers exist (`run_analytics_sources.py:183`,
  `run_viewer.py:865-867`, which string-matches `"oc_runipd" in driver_path`), and binding a new no-defaults
  `NamedTuple` field requires editing `oc_runipd.py` and `agy_runipd.py` too, since `HostLabels` raises
  `TypeError` on a missing field by design. Order 03 must declare all four before execution, or its E-02 is
  unexecutable as written.
- NO CHILD MAY PIN A SUITE BASELINE IT CANNOT REPRODUCE (PR-003, added at review). Measured at review: a
  bare `python3 -m pytest` in a managed worker lane reports `31 failed, 7824 passed, 3 skipped, 2 xfailed`,
  because `AW_EXECUTION_ROLE=worker` makes lifecycle verbs refuse BY DESIGN; with `env -u AW_EXECUTION_ROLE`
  the same tree is `7855 passed, 3 skipped, 2 xfailed`. No plan in this Set mentions this. An executor in a
  worker lane comparing against the authored `7825 passed` baseline would either record a false failure or
  "fix" 31 tests that are not broken. Every child MUST state which form it ran and MUST NOT edit those
  tests. The gate is NO NEW failures against a baseline taken the same way, never an absolute count.

## Deferred / out of scope (with reason)

- THE FIVE LARGE FUNCTIONS (`execute_item` 436, `main` 133, `run_queue` 150, `initialize_run` 119,
  `build_parser` 46 `ast.unparse` lines; 884 total, the ONE figure in this Set that reproduced exactly at
  review) are deliberately NOT re-planned in this Set. See OQ-01: they already carry five approved plans, so
  what they need is a decision about those plans, not a sixth plan.
- Integrating any REAL vendor host (codex, claude, hermes) is out of scope. Order 03 proves the seam admits
  a runner-less host; each real host is its own work with its own credentials and spend.
- The 21 existing thin wrappers are left exactly as they are: they are the sanctioned form, not debt.
- THE OTHER PENDING PLANS THAT TOUCH THESE FILES ARE NOT RE-SEQUENCED HERE, and the reason is mechanical
  rather than optimistic. Measured at review: about 33 other pending plans declare `oc_runipd.py`,
  `agy_runipd.py` or `runner_shared.py` in `Scope-Paths`, most of them `approved`, and 4 of them name
  `set_plan_approved` while 5 name `expand_selectors`. This is NOT a runtime hazard: `aw oc run` gives each
  execute item its own isolated worktree and returns changes through the merge-and-revalidate gate, so
  overlap is handled by the runner and needs no human sequencing (AGENTS.md). It IS an author-time cost,
  because a plan whose text quotes a symbol's CURRENT location becomes stale the moment this Set relocates
  it. Recorded so a later reader knows it was considered; no action is asked of any child.
- BACKLOG `dstnso` IS THE SOURCE OF THIS SET AND IS NOW LINKED, not deferred (PR-004). Measured at review:
  `dstnso` (`Status: open`, `Priority: high`) names SEVEN `execute_item` closure forks "claimed by no plan in
  the Set at all", and ALL SEVEN are covered here (`driver_finalize`, `evaluate_clean_base_for_launch`,
  `set_plan_approved`, `_record_checkpoint_stop` by Order 01; `reconcile_disposition`, `route_recovery_turn`,
  `_record_forced_stop` by Order 02). No plan in the Set mentioned it, so the graduation was invisible to
  `aw attention` and to the backlog's own close-legitimacy check. This orchestrator now carries
  `- From-Backlog: dstnso`. The item should move to `graduated` when this Set is approved, NOT to `done`
  (design handed off, code not yet written). The two sibling items `3dg3dv` (undeclared pin files in
  `yrqyxb`) and `9eiwnl` (a missing behavioral equivalent for one ordering pin) are NOT graduated by this
  Set and stay open; note `3dg3dv` is the SAME defect class as PR-001 below, which is why PR-001 was worth
  finding rather than trusting the authored rule.

## Scope check

- Over-scope: none. This orchestrator holds one verification item plus the child table.
- Under-scope: knowingly, on the five large functions. After this Set they remain forked, so the fork is
  reduced from 34 symbols to 5, not to zero. Claiming otherwise would misrepresent the result; closing that
  last gap needs the OQ-01 decision. LINE FIGURES CORRECTED at review: the "from ~1752 to ~884" claim mixes
  metrics (the 884 is `ast.unparse`-normalized and reproduces; the ~1752 does not reproduce under any metric
  I could find, where the same normalization gives 1448). The honest statement is the SYMBOL count: 34 -> 5.
- Under-scope, closed at review: the pin-table ownership rule named one file where four exist (PR-001, and
  it remains OPEN because the fix belongs in the three child plans, which are outside this review's ledger);
  Order 03's fence excluded two files its own resolved blocking OQ commits it to editing (PR-002); the
  worker-lane suite baseline was unstated (PR-003); the `dstnso` graduation was unlinked (PR-004); and the
  "same AST scan" the criteria depend on is not committed (PR-006).

## Required tests / validation

Children own their own validation. This orchestrator's own check is E-01: the Set-level end state, evidenced
by a re-run of the fork-count scan against the 34-symbol baseline, the runner-to-runner import check, the
third host's run record, a pre-cutover attribution check, the research record, and a suite showing no NEW
failures against a like-for-like baseline. Note the Set is NOT verifiable structurally alone: it moves
lock, stop-trigger, recovery and integration-retry machinery, which unit tests exercise only partially, so a
real driver execution is required.

TWO ADDITIONS FROM REVIEW, both cheap and both catching a failure mode measured above:

1. THE FOUR PIN FILES MUST BE RUN TOGETHER after each child, not just the one it declared:
   `python3 -m pytest tests/test_rununify_execute_item.py tests/test_rununify_run_queue.py
   tests/test_rununify_initialize_run.py tests/test_rununify_build_parser.py`. Baseline at review HEAD
   `84f140da`: `95 passed`. This is the check that would have caught PR-001 immediately.
2. THE STRENGTHENED RUNNER-IMPORT GUARD MUST BE SHOWN FAILING against unmodified HEAD before it is
   trusted, since the guard it replaces passes today while 9 violations exist. A guard that passes both
   before and after proves nothing.

## Open questions

### OQ-01: What should happen to `rununify` 07-11, the five plans that were approved to split the five large functions but recorded `NO SPLIT WAS PERFORMED`?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN, and deliberately NOT resolved by filing another plan, because the
  authorization already exists and duplicating it would create two competing mandates for the same code.
  THE SITUATION, measured: each of `yrqyxb` (`execute_item`), `ty3cj6` (`run_queue`), `orziju`
  (`initialize_run`), `s16omw` (`build_parser`) and `3dki3o` (`main`) is filed `executed` in
  `.aw/records/plans/executed/`, and each contains the phrase `NO SPLIT WAS PERFORMED`. Each was re-scoped
  at review into measurement-and-analysis behind a blocking OQ-03, and each OQ-03 was then RESOLVED by the
  maintainer on 2026-09-16 as "ROUTE (A) AS THE OBJECTIVE ... So DO THE SPLIT", with the Set-wide directive
  that "at the end of the SET, there should be one code base shared by the two runners that contains 100% of
  the otherwise redundant code". So the splits are authorized but were not performed, and the plans that
  would have performed them are already terminal.
  THREE ROUTES, and the choice is the maintainer's because it is about lifecycle authority, not code: (a)
  file a NEW Set of five corrective plans citing the resolved OQ-03s as their authority, which is the option
  the conventions point to since a plan in `executed/` must not be reopened; (b) treat the five as
  incomplete and reopen them, which contradicts the rule against editing an executed plan; (c) accept the
  five large functions as permanently host-owned, which contradicts the 2026-09-16 directive and should be
  recorded as a superseding decision if chosen. This Set proceeds on the other 29 symbols either way, so
  this question blocks nothing here.

### OQ-02: Does the third host in Order 03 need to be a real AI host?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, a scripted/dry-run host answers the structural question completely
  and needs no vendor CLI, credentials or spend. The repository already does exactly this: `host_launchers`
  states "No live models are launched in tests (doubles only)" and `host_runner` takes an injectable runner.
  Recorded here because the cheaper answer is also the more rigorous one, and a reader might otherwise
  assume the Set was descoped for convenience.

### OQ-03: Each child must declare the three pin files it will actually edit. Who applies that fix?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: RAISED AT REVIEW 2026-09-17 and BLOCKING, because the Set cannot execute
  as authored and the fix is not mine to apply. THE FACT, measured and proven with the guards' own predicate:
  `STILL_DOUBLE_DEFINED` pin tables live in FOUR test files (`test_rununify_execute_item.py`,
  `test_rununify_run_queue.py`, `test_rununify_initialize_run.py`, `test_rununify_build_parser.py`), and each
  asserts `assertFalse(_is_pure_delegation(defs[name]))` for every name it pins. `_is_pure_delegation`
  returns True for a lifted delegating body (verified by importing the guard module and calling it directly).
  Orders 01 and 02 must therefore each edit THREE of those files, while each declares exactly ONE. All 95
  tests pass at review HEAD, so the failures would be NEW and caused by the lift. The per-file, per-symbol
  ownership is now written out in full in Cross-IPD validation above.
  WHY I DID NOT JUST FIX IT: the remedy is an edit to `- Scope-Paths:` in three CHILD plans, and this review's
  ledger is this orchestrator alone. Editing a sibling plan's fence during a review of its parent would be an
  undeclared widening of exactly the kind this Set exists to make visible, and each child needs its own review
  round to also carry the matching E-item and V-item text.
  WHAT IS NEEDED, and it is small: add to `20260917-hostdedup-01-li44r9`'s `Scope-Paths`
  `tests/test_rununify_execute_item.py` and `tests/test_rununify_run_queue.py`; add to
  `20260917-hostdedup-02-nmlx47`'s `Scope-Paths` `tests/test_rununify_execute_item.py`,
  `tests/test_rununify_run_queue.py` and `tests/test_rununify_build_parser.py`; and in each, extend the pin
  re-base E-item to name its three files and its own symbols. Either approve those three edits for a
  follow-up round, or direct an agent to make them; until then the Set's readiness is `no-go` on this alone.
  NOTE THIS IS THE SAME DEFECT CLASS AS OPEN BACKLOG `3dg3dv`, which records that sibling `yrqyxb`'s
  `Scope-Paths` omitted three test files carrying `execute_item` source pins. That it recurred one Set later,
  in a Set whose own cross-IPD rule was written to prevent it, is the argument for fixing it by declaration
  rather than by remembering.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the re-run fork-count scan against the 2026-09-17 SYMBOL baseline (34 forks, of which
    5 large; the line figures are indicative per the Goal), produced by the COMMITTED scanner with its metric
    stated, showing only the five large functions remain; evidence of no runner-to-runner import that would
    have CAUGHT the 9 imports present at review (a `grep` for `"import oc_runipd"` alone does NOT satisfy
    this, since that is the vacuous form measured in F-4); the third host's run record showing correct
    attribution; a pre-cutover record still attributing correctly; the research record path; the four pin
    files run TOGETHER and green (review baseline `95 passed`); and the suite showing no NEW failures against
    a baseline taken the same way, with the invocation form stated (`env -u AW_EXECUTION_ROLE` or bare) and
    both numbers pasted. Plus all three children shown `executed`, AND each child's `Scope-Paths` shown to
    include the three pin files it edited (OQ-03): a child that finalized with an unjustified out-of-scope
    edit to a pin file means this criterion is not met.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This Set requires explicit human approval before execution. One design decision is already recorded from
the maintainer (Order 03's OQ-02: the descriptor carries an explicit host id, and pre-cutover records must
keep attributing), and TWO questions remain open for the maintainer: OQ-01 (the fate of `rununify` 07-11),
which blocks nothing here, and OQ-03, which is `Blocking: yes` and MUST be answered before execution because
the Set cannot execute as authored.

DO NOT EXECUTE THIS SET UNTIL OQ-03 IS RESOLVED. Orders 01 and 02 each must edit three pin files while
declaring one, proven at review with the guards' own predicate. Executing anyway produces a red suite in
undeclared files and forces the executor to either justify out-of-scope edits it was never told about or
weaken a guard the maintainer explicitly ruled must be re-based rather than weakened.

Execution contract for every child: work in an isolated worktree, commit only declared `Scope-Paths`,
path-scoped, never `git add -A`, never push. An out-of-scope edit that is genuinely required must be MADE
and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and a declared path left
unmodified needs a `--scope-ack`; do not stop over a scope question. Before every commit run
`git diff --cached --name-only` and unstage anything not yours: this is a shared checkout, and about 33
other pending plans declare these same runner files. RUN THE SUITE per the worker-lane rule in Cross-IPD
validation, stating which form you ran. Paste ACTUAL command and test output for every V-item; a claim of
success without pasted evidence does not satisfy these gates, and no child may claim a green suite it did
not run. Each child moves to `.aw/records/plans/executed/` via `aw ipd finalize` only after
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence.

Post-gate lifecycle: this orchestrator is retired to `.aw/records/plans/executed/` by the runner once all
three children are `executed` on disk, spending no agent turn. THAT MEANS E-01 IS MARKED COMPLETE WITHOUT
BEING PERFORMED on the runner path, and it is not a hypothetical: `runner_shared.dispatch_orchestrator_item`
calls `ipd_lifecycle.retire_orchestrator` on a purely disk-state eligibility verdict, with no E/V checkpoint
anywhere in that path (read at review). So the four criteria that ONLY E-01 checks (the cross-Set fork count,
the strengthened-guard property, pre-cutover attribution, and the research record) would be verified by
nobody. The mitigation is the one this plan can actually apply and is now stated in the Completion criteria:
every criterion is ALSO owned by a child `V-*` wherever possible. If executed by hand instead, E-01 must be
genuinely performed rather than inferred from the children's states: three executed children can still leave
a regressed fork count if a later change re-forked a symbol.

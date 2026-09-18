# IPD: Make the driver finalize idempotent and tell a consumed receipt from a never-issued one

- Date: 2026-09-17
- Kind: child
- Concern: A begin receipt is a SINGLE-USE token with TWO consumers, so a completed item can be reported as unauthorized. Measured in run `run-20260917T210518Z-1714328`, IPD `63425h`: the driver ran `aw ipd begin` and it succeeded; the agent turn did its work and then finalized the plan ITSELF at 21:45:49Z (`575f0b32 lifecycle(63425h): finalize 63425h -> executed`); a successful finalize CONSUMES the receipt (`ipd_lifecycle.py:3570-3573`, "the transaction is cleanly complete"); the driver's own `driver_finalize` then ran finalize a SECOND time at 21:51:27Z, found no receipt, and refused with "no begin receipt for 63425h: run `aw ipd begin` first (fail-closed: no receipt = no execution authority)". The item was recorded `substantially-complete` and its lane PRESERVED as not-integrated while its work was complete, committed, and already in `executed/` on the lane. A human had to diagnose and merge it by hand (`2cfdb85d`).
- Scope: TWO changes, one per defect, in the two places that own them. (1) BEHAVIOR: make the driver's finalize step idempotent, so an already-finalized item proceeds to INTEGRATION instead of being refused. (2) DIAGNOSIS: make `finalize_precheck` distinguish a CONSUMED receipt (the transition already succeeded) from a NEVER-ISSUED one (genuinely no authority), with distinct findings a caller can branch on. THIRD ITEM AMENDED AT REVIEW: the transition owner is NOT undecided (the driver owns it whenever `self_finalize` is true, enforced since `cdef9c90` by the `AW_EXECUTION_ROLE=worker` guard, and APPROVED plan `8b9ufm` already states it at turn start), so E-06 no longer "decides and documents" an owner. It instead closes the measured DELEGATION HOLE in that guard: `worker_role_active` is checked only in the CLI wrappers, so `aw set executed` reaches `finalize()` from a worker lane unguarded.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_finidem_double_finalize.py, tests/test_ipd_lifecycle_cli.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- From-Backlog: 02371s
- Set: finidem
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: ld8lb3

## Workflow history
- 2026-09-18 reviewed (opencode/its_direct-pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 all FIXED; OQ-01 resolved from evidence; corrected a fail-open predicate, a false finding, and an E-06 that duplicated approved plan 8b9ufm
- 2026-09-17 to-review (aw set): Authored 2026-09-17 from run-20260917T210518Z-1714328 (IPD 63425h false refusal); graduates backlog 02371s and 894vzu; complete enough to critique

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Backlog provenance

This plan graduates TWO backlog items, and the machine-readable `- From-Backlog:` field can name only one:

- `02371s` (high) THE BEHAVIORAL DEFECT: two finalizers for a single-use receipt. Carried in front matter.
- `894vzu` (medium) THE DIAGNOSTIC DEFECT: a consumed receipt and a never-issued one are indistinguishable.
  Named here because the field cannot hold it.

They are graduated together because they share one measurement, one reproduction and one regression test;
see the Goal for why splitting them would invite two partial fixes. Neither carries a release gate, so no
`Blocks-Release` is inherited.

Verified at review: both items are in `.aw/records/backlog/graduated/`, so the handoff this plan claims is
recorded on both sides.

## Goal

Stop reporting finished work as unauthorized, and make the refusal message name the cause that is
actually true.

WHY BOTH HALVES ARE ONE PLAN. They are two backlog items (`02371s` behavioral, `894vzu` diagnostic)
because they are two defects, but they share one measurement, one reproduction and one regression test,
and fixing either alone leaves real harm: idempotence without the message fix leaves every other caller
of `finalize_precheck` reading "no execution authority" for a consumed receipt, and the message fix
without idempotence leaves the finished lane unintegrated with a clearer explanation of why. Splitting
them would duplicate the fixture and invite two partial fixes.

WHAT REVIEW CHANGED ABOUT THE DIAGNOSIS, stated here because it changes what a reader should believe
about the plan's third item. The authored plan concluded that no actor owns the terminal transition and
that the fix therefore includes deciding one. That is wrong: the driver already owns it under
`self_finalize`, a guard already enforces that, and the guard was installed for this exact failure
(`cdef9c90`). The measured incident is not an undecided-ownership failure; it is a guard that the agent
DEFEATED with `env -u AW_EXECUTION_ROLE` while following its plan's own instruction to finalize. Both
halves of the fix survive that correction unchanged - the false refusal and the misleading message are
real - but the third half became a narrower, genuinely unowned code fix (F-10a, F-10b, E-06).

THE DEEPER POINT, and the reason this is `high`: the receipt exists to be a fail-closed proof of
execution authority, and its single-use consumption is what makes it a PROOF rather than a flag. That
design is correct. What is wrong is that two independent actors both try to spend it, so the second
one's failure carries no information about authority at all. Making the driver merely tolerant of a
missing receipt would weaken the gate; the fix must instead let the driver observe that the transition
it wanted has ALREADY HAPPENED, which is a stronger claim than "the receipt is gone".

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Reproduce before changing anything

- [ ] E-01 Build a FAILING reproduction in `tests/test_finidem_double_finalize.py`: a scratch repo with a begin receipt, one successful finalize, then a SECOND finalize of the same plan. Assert the second refuses with the receipt message today. This is the falsifiable baseline every later item is measured against; write it first so the fix cannot be declared without it.
  - Depends on: none
  - Expected outcome: a test that FAILS to finalize on the second call and whose refusal text matches the message measured in run `run-20260917T210518Z-1714328` ("no begin receipt for ... no execution authority"). Paste the failure.
  - Execution state: pending

### Task group 2: Tell the three causes apart (894vzu)

- [ ] E-02 In `finalize_precheck`, replace the single `receipt is None` verdict with a classification, and return a DISTINCT finding id per cause: ALREADY-FINALIZED, NEVER-ISSUED (no receipt and the plan is still non-terminal), and keep today's STALE branch untouched.
  ALREADY-FINALIZED MUST BE RECOGNIZED BY A POSITIVE, PLAN-BOUND OBSERVATION, and specifically NOT by `run_selection_policy.is_in_terminal_directory`, which the authored plan named and which is WRONG here: it returns True for `/reusable/`, a disposition the runner re-dispatches (`_IPD_ACTIONS["reusable"] == ACTION_EXECUTE`), so it would read a never-issued receipt on a reusable plan as success. Use `runner_shared.plan_bucket(path) == "executed"`, and PREFER additionally requiring the plan-bound lifecycle commit `artifact_core.finalize_commit_subject(plan_id)` (already the pre-commit gate's proof of a genuine finalize). If you cannot get the commit signal cheaply, the `executed` bucket alone is acceptable; `is_in_terminal_directory` is NOT.
  - Depends on: E-01
  - Expected outcome: three distinguishable outcomes from `finalize_precheck`, each with its own finding id and message; the NEVER-ISSUED message keeps its current wording because it is correct for that case. Paste evidence that a `/reusable/` plan with no receipt classifies NEVER-ISSUED and still refuses.
  - Execution state: pending

- [ ] E-03 Make the ALREADY-FINALIZED message state the true situation and NOT prescribe `aw ipd begin`. Running begin on an already-finalized plan would mint authority for work that is complete, which is the actively harmful remedy today's message recommends.
  - Depends on: E-02
  - Expected outcome: the ALREADY-FINALIZED text names the terminal directory and the finalize commit if resolvable, and recommends no begin. Quote the before and after wording.
  - Execution state: pending

### Task group 3: Make the driver idempotent (02371s)

- [ ] E-04 At the driver's finalize site (`oc_runipd.py:7683` and its refusal arm at `:7925-7945`), treat ALREADY-FINALIZED as success: proceed to integration and record the item `executed`, rather than leaving it `substantially-complete` with a preserved lane. Do NOT treat a bare missing receipt as success, which would weaken the fail-closed gate.
  HOW THE DRIVER LEARNS THE CAUSE IS AN OPEN DESIGN CHOICE THIS ITEM MUST MAKE AND RECORD, because the authored instruction ("consume E-02's finding id") is not satisfiable through today's channel: `driver_finalize` returns only `(returncode, stderr_text)` and `aw ipd finalize` registers no `--agent`/`--json` on that path. Pick ONE and say which: (a) call the in-process classification predicate directly from the driver (no subprocess text parsing); or (b) add structured output to the finalize surface and DECLARE `agent_workflows/cli.py` in `Scope-Paths` first. Substring-matching the refusal prose is NOT acceptable.
  - Depends on: E-02
  - Expected outcome: an item whose agent self-finalized ends `executed` and INTEGRATED. A genuinely never-issued receipt still refuses exactly as it does today. State which of (a)/(b) was chosen and why.
  - Execution state: pending

- [ ] E-05 Apply the same change to the agy host. The "or prove it already shares the site" branch is DEAD and was removed at review: `driver_finalize` is duplicated per host (`oc_runipd.py:1294`, `agy_runipd.py:1037`) and so is the whole result-handling block (`oc_runipd.py:7651-7945`, `agy_runipd.py:4266-4490`). Only `driver_begin` is shared (`runner_shared.py:8440`). So this is TWO changed sites, and if lifting the shared logic into `runner_shared` is preferable, note that `hostdedup` (`li44r9`, `nmlx47`) and the `rununify` Set are already moving these same symbols; coordinate rather than lift unilaterally.
  - Depends on: E-04
  - Expected outcome: both hosts handle ALREADY-FINALIZED identically, evidenced by the two changed sites with matching behavior demonstrated per host.
  - Execution state: pending

### Task group 4: Remove the root cause, not just its symptom

- [ ] E-06 Close the ROLE-GUARD DELEGATION HOLE: move (or duplicate) the `worker_role_active` refusal from the CLI wrapper into `finalize()` itself, so `aw set executed` / `aw ipd set executed` cannot perform a terminal transaction from a worker lane.
  THIS ITEM WAS REWRITTEN AT REVIEW (PR-005/PR-006). It previously asked the executor to "decide and DOCUMENT one owner of the terminal transition", which is (i) ALREADY DECIDED - the driver owns it whenever `self_finalize` is true, enforced since commit `cdef9c90` by `AW_EXECUTION_ROLE=worker` (`oc_runipd.py:5843`, `agy_runipd.py:2750`) plus the `AW-LIFECYCLE-ROLE-001` refusal (`ipd_lifecycle.py:4285`); and (ii) ALREADY OWNED by APPROVED plan `8b9ufm` (roleadv-01), which states that role at turn start in all four prompt builders, correctly conditions it on the run's frozen `self_finalize`, and declares the same three source files this plan does. Doing it here would collide with an approved plan and re-decide a settled question.
  WHAT IS GENUINELY UNOWNED is the hole F-10b measures: the guard lives in `run_begin`/`run_finalize` and NOT in `finalize()`, and `status_set.py` never consults it, so the `aw set executed` delegation path (`status_set.py:1144`) is unguarded. Fix THAT. Follow the precedent already in the tree: `retire_orchestrator` had the identical gap and solved it by checking the predicate itself (`ipd_lifecycle.py:3177`), recorded in `ROLLUP_SHARED_GATES` as `"worker-role-refusal"` with the note "NOT inherited ... so this path had to check it itself".
  HONEST LIMIT TO STATE, NOT TO FIX HERE: the env marker is a SELECTOR, not a boundary (its own comment says so), and the measured incident defeated it with `env -u AW_EXECUTION_ROLE`. Closing THAT needs an OS sandbox or a separate principal and is explicitly out of scope; record it as a follow-on. Note also that the `env -u` habit is driven by a real defect (31 lifecycle tests fail in a lane, backlog `770fkp`/`s0303g`), so agents will keep reaching for it until that is fixed; say so rather than assuming instruction alone will hold.
  - Depends on: E-04
  - Expected outcome: `aw set executed <plan>` from a worker-role process refuses with `AW-LIFECYCLE-ROLE-001` and performs no status edit, no move, and no commit; the coordinator path is byte-identical. Paste both. Cite `8b9ufm` as the owner of the prompt-side statement and do NOT edit the prompt builders here.
  - Execution state: pending

- [ ] E-07 Extend `tests/test_finidem_double_finalize.py` to pin the end state: the E-01 reproduction now reaches `executed` and INTEGRATED; a never-issued receipt still refuses; a STALE receipt still refuses. Assert the three finding ids are distinct, so a future change cannot silently collapse them back into one verdict.
  ADDED AT REVIEW, and this case is the load-bearing one: include a REUSABLE-PLAN CONTROL. A plan in `.aw/records/plans/reusable/` with NO receipt must classify NEVER-ISSUED and REFUSE. Without this assertion the fail-open regression PR-001 identified can be reintroduced by one line (swapping the bucket test back to `is_in_terminal_directory`) with every other test in this file still green.
  - Depends on: E-03, E-05, E-06
  - Expected outcome: a guard covering all three causes, the reusable control, and the integration outcome, shown to fail if any two causes are merged AND shown to fail if the predicate is widened to `is_in_terminal_directory`.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- THE RECEIPT IS DELIBERATELY SINGLE-USE. `ipd_lifecycle.py:3989-3993` consumes it on success with the
  comment "Consume the begin receipt (the transaction is cleanly complete)". That is the design and this
  plan must NOT change it; single use is what makes the receipt a proof rather than a flag.
  (CITATION CORRECTED AT REVIEW, PR-002: the authored text said `:3570-3573`, which lands inside
  `_perform_terminal_transaction`'s docstring and contains no consumption.)
- THE FAIL-CLOSED RULE IS LOAD-BEARING: "no receipt = no execution authority". E-04 must therefore key on
  ALREADY-FINALIZED (a positive observation) and never on "the receipt is absent", or it would convert a
  fail-closed gate into a fail-open one.
- `run_selection_policy.is_in_terminal_directory` IS NOT USABLE AS THIS PLAN'S ALREADY-FINALIZED
  PREDICATE, and the authored text saying otherwise was WRONG (review PR-001, the highest-risk finding
  here). `TERMINAL_DIRECTORY_SEGMENTS` (`run_selection_policy.py:506-511`) contains FOUR segments, and
  the fourth is `/reusable/`, which is NOT a completed disposition: `.aw/records/plans/reusable/README.md`
  says "Not a terminal state", and `_IPD_ACTIONS["reusable"]` is `ACTION_EXECUTE`
  (`run_selection_policy.py:134`), so a reusable plan is a plan the runner DISPATCHES REPEATEDLY.
  Measured at review: `is_in_terminal_directory('.aw/records/plans/reusable/a.ipd.md')` returns True.
  So keying E-04 on this predicate would make EVERY reusable-plan run treat a missing receipt as
  "already finalized" and integrate with no execution authority at all - the exact fail-open inversion
  OQ-02 forbids, delivered by the very predicate the plan called safe. USE INSTEAD the `executed`
  BUCKET specifically (`runner_shared.plan_bucket(path) == "executed"`,
  `runner_shared.py:3719`), which is the discrimination this plan needs and which the driver's own
  `reconcile_disposition` already performs (`oc_runipd.py:6371-6373`).
- A STRONGER POSITIVE SIGNAL THAN THE DIRECTORY EXISTS, and it is already the repo's canonical
  finalize-happened evidence: the LIFECYCLE COMMIT SUBJECT `lifecycle(<id6>): finalize`, defined once in
  `artifact_core.finalize_commit_subject` (`artifact_core.py:150-158`) and already consumed as proof by
  the pre-commit gate (`hooks/executed_transition_gate.py:261-293`, "a COMMIT survives the lane
  branch"). It is plan-bound by construction, which the directory is not. E-02/E-04 SHOULD prefer it,
  or require BOTH it and the `executed` bucket; the directory alone is the weakest admissible signal.
- THE FINALIZE JOURNAL IS NOT AN AVAILABLE SIGNAL. `PHASE_COMPLETE` is written and then
  `_clear_finalize_journal` removes it in the same block (`:3984-3988`), so no journal survives a
  successful finalize. The terminal DIRECTORY is the durable evidence.
- `sync_receipt_into_worktree` IS A DELIBERATE NO-OP and must stay one. Its docstring records that copying
  the receipt into the lane was retired by the `dh0uno` control-root fix, that research `x03wgn` Section 7
  names the copy as its own hazard ("two authorities diverge or are consumed independently"), and that the
  prescribed guard is to DELETE the copy path. Restoring a copy is not an available fix here.
- `checkout_control_root` collapses a lane and the main tree to ONE control store, verified live. So the
  receipt was never split across trees in the measured incident; do not re-diagnose it that way.
- `driver_finalize` IS NOT SHARED; IT IS DUPLICATED PER HOST, and E-05's question is therefore already
  answered (review PR-004). `runner_shared.py:8440` is `driver_begin`, which IS shared. `driver_finalize`
  is defined TWICE, once per host, in near-identical bodies: `oc_runipd.py:1294` and
  `agy_runipd.py:1037`. The RESULT HANDLING is likewise duplicated: the success arm plus refusal arm at
  `oc_runipd.py:7651-7945` and its twin at `agy_runipd.py:4266-4490`. So this plan MUST change two
  sites, and E-05's "or prove it already shares the site" branch is dead.
- THE REFUSAL CHANNEL IS A BARE `(exit_code, stderr_text)` PAIR, which constrains E-02/E-04's contract.
  Both `driver_finalize` bodies return `result.returncode, (result.stderr or result.stdout or "").strip()`
  (`oc_runipd.py:1341`, `agy_runipd.py:1082`), and the caller stores that text as `fin_msg`. `aw ipd
  finalize` exposes NO structured-output flag on this path (no `--agent`/`--json` in its parser,
  `cli.py:1519-1571`), so today the driver's ONLY discriminator is the message STRING. E-04 says
  "Consume E-02's finding id; do NOT re-derive the condition", which is not achievable through this
  channel as it stands. E-04 must therefore either (a) have the driver call the in-process predicate
  directly rather than parse the subprocess text, or (b) add structured output to the finalize surface
  and declare `agent_workflows/cli.py` in `Scope-Paths`. Choose explicitly and record which; do NOT
  fall back to substring-matching the refusal prose, which is the fragile coupling E-07 exists to ban.
- The execution contract forbids `git add -A` and pushing; commit only declared `Scope-Paths`, path-scoped.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | A successful finalize consumes the receipt, by design | `ipd_lifecycle.py:3989-3993`, comment "the transaction is cleanly complete" (citation corrected at review) |
| F-2 | With `self_finalize=True` (this run's value, and the default) TWO actors finalize one item | run state `options.self_finalize: True`; the agent finalized at `575f0b32` and the driver's `driver_finalize` ran after |
| F-3 | Begin DID run and DID succeed, so "no execution authority" was false | no `ipd-begin-refused` event, no `begin_refused` key on the attempt, and the agent turn launched (a nonzero begin returns before launching) |
| F-4 | The refusal came 5m38s AFTER the agent's own successful finalize | agent finalize commit 2026-09-17T21:45:49Z; `ipd-finalize-refused` event 2026-09-17T21:51:27Z |
| F-5 | The item was left `substantially-complete` with its lane preserved while the work was complete | run state disposition; the lane held 3 commits and the plan already in `executed/`; merged by hand as `2cfdb85d` |
| F-6 | `finalize_precheck` maps ONE condition onto a message asserting ONE specific cause | `ipd_lifecycle.py:1905-1913`: `if receipt is None:` -> "no begin receipt ... no execution authority" (citation corrected at review; `:1602-1611` is unrelated docstring text) |
| F-7 | Absence has at least three causes with opposite meanings | never-issued (refuse, message correct); consumed by a successful finalize (work is DONE); the `dh0uno` split-store class (fixed, but the shape recurs) |
| F-8 | The remedy the message prescribes is harmful in the consumed case | running `aw ipd begin` again would mint fresh authority for work already finalized |
| F-9 | A durable ALREADY-FINALIZED signal EXISTS and is ignored | the plan sits in `executed/`. NARROWED AT REVIEW: the signal is the `executed` BUCKET (`plan_bucket`, `runner_shared.py:3719`) or the plan-bound lifecycle commit subject (`artifact_core.py:150`), NOT `is_in_terminal_directory`, which also returns True for the non-terminal `/reusable/` (see PR-001) |
| F-10 | ~~The agent finalized on its OWN initiative, not because the runbook said to~~ **WITHDRAWN AT REVIEW AS FALSE** (PR-003). The runbook clause is true but irrelevant: the ASSIGNED PLAN told the agent to finalize, in its own execution gate. `63425h`'s gate reads "After the gate, move this plan to `.aw/records/plans/executed/` via `aw ipd finalize`" and the token appears 5 times in that plan. The lane received the plan and the runbook (`lane-inputs-materialized` names both). So this was CONTRACT-FOLLOWING, not initiative | `git show 575f0b32:<63425h plan>` line 711; `grep -c 'aw ipd finalize'` on that plan = 5; run `events.jsonl` `lane-inputs-materialized` |
| F-10a | **THE ACTUAL ROOT CAUSE, found at review and NOT in the authored plan.** A shipped guard ALREADY assigns the transition to the driver and ALREADY refuses an in-lane finalize: `AW_EXECUTION_ROLE=worker` is set on every isolated turn's child env (`oc_runipd.py:5843`, `agy_runipd.py:2750`) and `run_finalize` refuses on it with `AW-LIFECYCLE-ROLE-001` (`ipd_lifecycle.py:4285`). It was installed by commit `cdef9c90` "fix(i452hf): stop stranding a lane the agent already finalized" - i.e. for THIS EXACT FAILURE. In the measured incident the agent DEFEATED it deliberately: it ran `env -u AW_EXECUTION_ROLE python3 -m agent_workflows ipd finalize 63425h --apply`, recorded verbatim in its own outcome JSON `tests[]`. It had adopted `env -u` legitimately for pytest (31 lifecycle tests fail under the role flag, backlog `770fkp`/`s0303g`) and then carried the habit into a lifecycle verb | outcome JSON `tests[]` entry; `git log -1 -S` on the env line; `tests/test_worker_role_refusal.py:142` |
| F-10b | The guard has a SECOND, unbypassed hole worth fixing here: `worker_role_active` is checked in the CLI wrappers `run_begin`/`run_finalize` ONLY, not inside `finalize()`, and `status_set` contains ZERO references to it. So `aw set executed <plan>`, which delegates straight into `_life.finalize` (`status_set.py:1144`), performs a full terminal transaction from a worker lane with no role refusal at all | measured: `worker_role_active` in `run_finalize` = True, in `finalize` = False, in `status_set` = False |
| F-11 | Restoring a receipt copy into the lane is NOT an available fix | `sync_receipt_into_worktree` is a deliberate no-op; research `x03wgn` S7 names the copy a hazard and prescribes deleting the path |
| F-12 | An APPROVED plan already owns E-06's deliverable, so E-06 as written duplicates it and would collide | `8b9ufm` (roleadv-01, `- Status: approved`, `Readiness: go-pending-approval`) states the runner-owns-begin/finalize role at TURN START in all four prompt builders, gated on the run's own frozen `self_finalize`, and declares `oc_runipd.py`, `agy_runipd.py`, `ipd_lifecycle.py`, `tests/test_worker_role_refusal.py`. It also already RESOLVED this plan's OQ-01: ownership is not a constant, it is the `--no-self-finalize` run option |

## Proposed changes (ordered, validatable)

1. Write the failing double-finalize reproduction first (E-01).
2. Classify receipt-absence in `finalize_precheck` into ALREADY-FINALIZED / NEVER-ISSUED, keeping STALE as
   is, with distinct finding ids (E-02) and an honest ALREADY-FINALIZED message (E-03). ALREADY-FINALIZED
   keys on the `executed` bucket (and preferably the lifecycle commit), NEVER on
   `is_in_terminal_directory`.
3. Make the driver treat ALREADY-FINALIZED as success and integrate (E-04), on both hosts, which are TWO
   separate sites (E-05).
4. Close the worker-role delegation hole so `aw set executed` cannot transition from a lane (E-06). This
   REPLACED an "decide the transition owner" item that review found already decided and already owned by
   approved plan `8b9ufm`.
5. Pin all three causes, the reusable-plan fail-open control, and the integration outcome (E-07).

## Deferred / out of scope (with reason)

- MAKING THE RECEIPT MULTI-USE is explicitly rejected, not deferred. Single-use consumption is what makes
  it a proof of a completed transaction; a reusable token would let two actors both believe they hold
  authority, which is the hazard `x03wgn` S7 already documents for the receipt-copy path.
- REPAIRING THE MEASURED RUN'S STATE FILE is out of scope. `63425h` still reads `substantially-complete`
  in `run-20260917T210518Z-1714328`'s state, and rewriting a historical run record would falsify history;
  the plan is correctly in `executed/` in main, so the durable record is right.
- The pre-existing duplicate-status backlog items (`egqt32`, `nuanaw`, tracked as `5bmq5f`) are unrelated
  and are the 2 violations `aw backlog check` reports today; do not "fix" them here.

## Scope check

- Over-scope: E-06 AS ORIGINALLY WRITTEN WAS OVER-SCOPE and was rewritten at review rather than kept.
  It asked the executor to decide an ownership question the repository has already decided and to write a
  statement APPROVED plan `8b9ufm` already owns, in the same three files `8b9ufm` declares. Two approved
  plans writing the same prompt text is a merge collision, not thoroughness. The rewritten E-06 is a code
  fix to a measured hole and is in-scope.
- Under-scope: this plan does not audit every other `finalize_precheck` caller for the same misreading. If
  E-02 reveals callers that branch on the refusal TEXT rather than a finding id, name them as a follow-on
  rather than widening here.
- Under-scope, ACCEPTED AT REVIEW AS A FOLLOW-ON RATHER THAN WIDENED HERE: the `env -u
  AW_EXECUTION_ROLE` bypass that actually caused the measured incident. The env marker is documented as a
  SELECTOR and not a boundary, so closing it needs an OS sandbox or a separate principal. It is also
  partly self-inflicted, because agents adopt `env -u` legitimately to get a trustworthy suite baseline
  (31 lifecycle tests fail in a lane: backlog `770fkp` high, `s0303g` medium). Fixing THOSE removes the
  incentive and is the higher-leverage change; it belongs to those items, not here.
- Sequencing note added at review: `oc_runipd.py` / `agy_runipd.py` / `ipd_lifecycle.py` are among the
  most contended files in the pending corpus (28 approved plans declare at least one of them, and
  `8b9ufm` declares three of the four this plan does). This is NOT a runtime hazard - the runner isolates
  each item in its own worktree and merges through a revalidation gate - but it does mean E-06 must stay
  off the prompt builders to avoid a semantic collision with `8b9ufm`.

## Required tests / validation

- `python3 -m pytest` bare and green with the actual summary line pasted (authoring baseline
  `7855 passed, 3 skipped, 2 xfailed`).
- The E-01 reproduction shown FAILING before the fix and PASSING after, both pasted. A test that passes in
  both states proves nothing here.
- Evidence the fail-closed property survives: a NEVER-ISSUED receipt still refuses, and the refusal text
  is unchanged for that case.
- A REAL driver execution in which the agent self-finalizes, ending `executed` and integrated with no
  preserved lane. This defect was invisible to the unit suite for as long as it existed, so an end-to-end
  demonstration is required rather than optional. SEE V-07 for the two acceptable forms and the
  feasibility constraint (a nested run from inside a lane is not one of them); if neither form is
  reachable, defer with evidence rather than passing the item.
- THE FAIL-OPEN CONTROL, added at review and non-negotiable: a plan in `reusable/` with no receipt must
  still REFUSE. This is the specific way a well-intentioned implementation of this plan breaks the gate,
  because the predicate the authored plan recommended admits `/reusable/` as terminal.

## Spec / documentation sync

No `.spec.md` is declared in `Scope-Paths`, and that is a deliberate claim rather than an omission: this
plan restores the intended behavior of an existing gate rather than changing a contract.

CHECKED AT REVIEW, since the authored text left it as a conditional for the executor to resolve. Spec
`25kzda` (`- Status: approved`, `- Blocks-Release: next`) assigns the terminal transition to tooling and
not to the executor, in terms this plan does not change: 1.1 says the deterministic checker "alone
authorizes `verified` and terminal transitions" and that the executor "may report what it did but cannot
mark the action verified"; 1.2 step 11 says "use the appropriate lifecycle setter or terminal
transaction". Its per-item action list includes `finalize` as a runner action (`:1059`). So the spec
already agrees with the driver-owned answer and needs NO amendment for E-02..E-05, nor for the rewritten
E-06, which only extends an existing refusal to a second entry point. If the executor nonetheless
concludes an amendment is needed, declare the spec path in `Scope-Paths` FIRST and record the reason here,
per the plan-may-amend-a-spec rule.

## Open questions

### OQ-01: Who should own the terminal transition, the agent or the driver?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW FROM REPOSITORY EVIDENCE, not by asking, because
  the repository already answers it and the answer is not "one of two defensible options". THE DRIVER
  OWNS IT WHENEVER `self_finalize` IS TRUE, AND THE AGENT OWNS IT UNDER `--no-self-finalize`; ownership is
  a RUN OPTION, not a constant. Evidence: both hosts export `AW_EXECUTION_ROLE=worker` for an isolated
  turn (`oc_runipd.py:5843`, `agy_runipd.py:2750`) and `run_finalize` refuses on it
  (`ipd_lifecycle.py:4285`), a guard installed by commit `cdef9c90` whose subject is literally
  "fix(i452hf): stop stranding a lane the agent already finalized"; `--no-self-finalize`'s own help text
  says "the agent must move the plan itself" (`oc_runipd.py:9013-9018`); and both `driver_begin` and
  `driver_finalize` sit inside `if self_finalize and not is_review:` (`oc_runipd.py:6682`).
  APPROVED plan `8b9ufm` states exactly this and gates the statement on the frozen option.
  The premise the authored question rested on (F-10: "the agent finalized on its own initiative") is
  FALSE and was withdrawn: the assigned plan's own gate instructed the finalize. What actually happened is
  narrower and worse: the agent defeated the shipped guard with `env -u AW_EXECUTION_ROLE` (F-10a). So the
  remaining work is not a decision, it is closing the delegation hole (F-10b), which is what E-06 now does.

### OQ-02: Should the driver treat a bare missing receipt as success if the plan is terminal?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, and the distinction is the whole safety argument of this plan. The
  driver must key on a POSITIVE observation (the plan is in a terminal directory, i.e. the transition
  demonstrably happened) and never on the ABSENCE of a receipt. Keying on absence would convert
  "no receipt = no execution authority" from fail-closed to fail-open: any path that lost or never wrote a
  receipt would be read as success. The terminal directory is evidence a finalize RAN; a missing receipt is
  evidence of nothing in particular (F-7 lists three causes). E-02 and E-04 are written in that direction
  deliberately.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the reproduction's FAILURE output pasted, showing the second finalize refused with
    the "no begin receipt ... no execution authority" text. A reproduction that does not fail at HEAD is not
    a reproduction of this defect.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the three outcomes demonstrated with their DISTINCT finding ids: ALREADY-FINALIZED,
    NEVER-ISSUED, STALE. Show that the STALE branch's behavior is unchanged from HEAD. PLUS the
    FAIL-OPEN CONTROL added at review: a plan in `reusable/` with no receipt classifies NEVER-ISSUED and
    REFUSES, with the output pasted. State in one line which predicate ALREADY-FINALIZED keys on and
    confirm it is not `is_in_terminal_directory`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the before and after ALREADY-FINALIZED message text, showing the new wording states
    the true situation and does NOT tell the operator to run `aw ipd begin`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the E-01 reproduction now reaching `executed` AND integrated; PLUS the fail-closed
    control, a never-issued receipt still refusing with unchanged text. Both pasted. The control is the
    load-bearing half: without it this item cannot be distinguished from weakening the gate.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the TWO changed sites (`oc_runipd.py`, `agy_runipd.py`) with matching behavior
    demonstrated per host. The "one shared code path" alternative was removed at review as
    counterfactual: `driver_finalize` is defined twice (`oc_runipd.py:1294`, `agy_runipd.py:1037`).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `aw set executed <plan>` run with `AW_EXECUTION_ROLE=worker` set, pasted, showing
    the `AW-LIFECYCLE-ROLE-001` refusal AND showing the plan unmoved with no new commit (paste
    `git status --porcelain` and `git log -1 --format=%s` after). PLUS the coordinator control: the same
    command without the variable behaves exactly as it does at HEAD. PLUS a one-line citation that
    `8b9ufm` owns the prompt-side statement and that no prompt builder was edited here.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: `python3 -m pytest tests/test_finidem_double_finalize.py` green; evidence it FAILS if
    two of the three causes are collapsed into one verdict (make the edit, paste the failure, revert);
    evidence it FAILS if the ALREADY-FINALIZED predicate is widened to `is_in_terminal_directory` (same
    make-paste-revert); `python3 -m pytest` bare and green with the summary line pasted.
  - PLUS the end-to-end demonstration. NOTE THE FEASIBILITY CONSTRAINT recorded at review: a nested real
    `aw oc run` from inside a lane is not a reliable evidence path, because the lane exports
    `AW_EXECUTION_ROLE=worker` (which refuses the very lifecycle verbs the demonstration needs) and
    because 31 lifecycle tests already fail in that environment (backlog `770fkp`, `s0303g`). So the
    ACCEPTABLE forms, in preference order, are: (1) a real driver run performed OUTSIDE any lane, with
    its run directory and `ipd-finalized` event pasted; or (2) a harness test that drives the real
    `execute_item` finalize-and-integrate path in a scratch repo, exercising the driver code rather than
    re-asserting the predicate. What is NOT acceptable is a unit test that only re-checks E-02's
    classification and is then described as an end-to-end run.
  - IF NEITHER FORM IS REACHABLE in the execution environment, record that as a DEFERRED question with
    the evidence, do NOT mark this V-item pass, and do NOT finalize the plan on structural green alone.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. It touches a FAIL-CLOSED SAFETY GATE, so the
executor carries one non-negotiable constraint: the fix must key on the positive observation that a
transition already happened, never on the absence of a receipt (OQ-02). Any diff that makes a missing
receipt sufficient for success is out of scope even if the suite passes.

CONCRETELY, AND THIS IS THE ONE THING MOST LIKELY TO GO WRONG (review PR-001): do NOT use
`run_selection_policy.is_in_terminal_directory` as the ALREADY-FINALIZED predicate, even though the
plan's own conventions section originally told you to. It admits `/reusable/`, which is a plan the runner
RE-DISPATCHES, so it would convert a never-issued receipt into "success" on every reusable run. Key on
the `executed` bucket, ideally together with the plan-bound `lifecycle(<id6>): finalize` commit subject.
V-02 and V-07 both demand the reusable-plan control as pasted evidence for this reason.

SCOPE FENCE, declared so the runner can reconcile it afterwards: this plan declares
`agent_workflows/ipd_lifecycle.py`, `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`,
`agent_workflows/runner_shared.py`, `tests/test_finidem_double_finalize.py` and
`tests/test_ipd_lifecycle_cli.py`. If E-04 takes option (b) (structured finalize output), add
`agent_workflows/cli.py` to `Scope-Paths` BEFORE editing it; an additive widening is accepted at finalize
with a recorded `--scope-reason` per added path (`63425h`, spec `25kzda` 5.5a). Do NOT edit the prompt
builders' role text: APPROVED plan `8b9ufm` owns it. Do NOT edit `agent_workflows/status_set.py` unless
E-06's chosen shape requires it, and declare it first if so.

Execution contract: work in an isolated worktree, commit only the declared `Scope-Paths`, path-scoped,
never `git add -A`, never push. Paste ACTUAL runner output for every V-item.

Post-gate lifecycle: `aw ipd finalize` moves this plan to `.aw/records/plans/executed/` only after
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries observed evidence. V-04's fail-closed
control and V-07's real driver execution are both mandatory: this defect passed the entire unit suite for
as long as it existed, so structural green is not evidence that it is fixed.

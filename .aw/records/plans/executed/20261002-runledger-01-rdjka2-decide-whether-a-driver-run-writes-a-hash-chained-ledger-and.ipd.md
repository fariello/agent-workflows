# IPD: Decide whether a driver run writes a hash-chained ledger, and record the answer where the code asserts it is open

- Date: 2026-10-02
- Kind: child
- Concern: Shipped source asserts a position the runtime contradicts, and the contradiction is load-bearing rather than cosmetic. `runner_shared.py`'s `retrywire` section header states that `run_recovery.plan_retry` / `retry_budget_remaining` "REMAIN THE INTENDED LONG-TERM HOME", that they are "UNREACHABLE from a driver run", and that "WHETHER A DRIVER RUN SHOULD WRITE A LEDGER IS STILL OPEN and is NOT decided here ... Nobody may cite this section as a decision to abandon the ledger design". Every leg re-measured at HEAD `fb75224d` (F-01, F-02, F-03): zero `ledger.jsonl` files exist anywhere outside `.git`; a combined grep for `run_engine|run_recovery|run_ledger_store|RunLedgerStore|RunEngine|ledger\.jsonl` returns exactly 0 in BOTH `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`; and every one of `run_recovery`'s eight public functions takes `engine` as its first positional and reaches `engine.reconstruct_state()`. So the "intended long-term home" has been unreachable from the only execution path that actually runs, for as long as both have existed, and the comment presents that as a pending decision rather than as the status quo it has become.
  THE COST IS ALREADY BEING PAID, which is what makes this a defect and not a documentation nit. Because the shared layer is unreachable, the driver carries a SECOND implementation of retry semantics: `handle_turn_failure_retry`, `frozen_retry_budget`, `turn_retry_budget_remaining`, `TURN_RETRY_CLASSIFICATION`, `turn_retry_idempotency_key` and `invalidate_turn_evidence` all exist in `runner_shared.py` (each measured present, F-04), and that same `retrywire` header concedes of the duplication that "this repository normally refuses one". The vocabularies are disjoint too: `run_state.ALL_STATES` holds 11 tokens and `runner_shared.TERMINAL_STATES_CANONICAL` holds 14, their intersection is exactly `{'failed'}` (computed in-process, F-05), and `plan_retry` raises `NoRetryableStateError` for any step not in `STATE_FAILED`/`STATE_BLOCKED`, neither of which a driver queue item ever holds.
  THE ITEM'S BINARY FRAMING IS INCOMPLETE, AND THAT IS THIS PLAN'S CENTRAL FINDING. Item `ye28s6` offers (a) make driver runs emit a ledger, or (b) declare the ledger for a different path and correct the comment. Measured, (a) IS NOT AVAILABLE TO ANY CALLER TODAY, because nothing in the package can create a ledger AT ALL: `RunLedgerStore.append` refuses any first record whose `kind` is not `"run"` (`RL-E041`, `run_ledger_store.py` at the `next_seq == 0` guard), and a repository-wide search for a writer of a `kind: "run"` record returns ZERO (F-06). Driven live, `RunEngine`'s only five append paths write `step_attempt`, `human_approval`, `verifier_decision` and `terminal_transaction`, so the legal sequence `release_step` -> `start_step` -> `record_step_attempt` dies on `SchemaInvalidRecordError ... RL-E041 first ledger record must be kind 'run'` and leaves NO file on disk (F-07, reproduced). The absence is equally reachable from the product: `aw run start run-abc123 --step S-01` exits 2 saying "no driver run writes one today" (F-08). So the honest answer is not (a) or (b) but "(b) for now, and (a) is a multi-plan program gated on a maintainer decision this plan is written to obtain", and the gap is wider than the item's own framing implies.
- Scope: Answer the item's question with a recorded, attributable maintainer decision, and make the shipped text and the one durable artifact agree with whatever is decided. IN, and deliberately nothing more: (1) author a DECISION RECORD under `.aw/records/research/` capturing the measurements below, the two live options with their real costs, and the recommendation, so the answer survives as provenance a later plan can cite rather than as prose in an executed plan; (2) obtain the maintainer's answer and record it in this plan's `## Open questions` as OQ-01 with `- Status: resolved`; (3) REWRITE the `retrywire` header's four-bullet block in `agent_workflows/runner_shared.py` so it states the DECIDED position instead of an open one, preserving every measurement that remains true and removing only the aspirational claim the decision retires; (4) if and only if the decision is (b), correct `run_recovery.py`'s module docstring and the `DEFAULT_RETRY_LIMIT` comment block, which today tell a reader the helpers are dormant pending wiring rather than scoped to the `aw run` path; (5) add a behavior test that pins the DECIDED invariant, driving real functions and asserting real outputs.
  OUT, each for a stated reason. BUILDING THE LEDGER WIRING, under either answer: F-06 and F-07 prove it needs at minimum a ledger-creation verb, a driver-side step model, and a resolution of spec `25kzda` Section 6.2's still-open "durable storage location for run ledgers", which is three reviewable plans and not an E-item here; if the decision is (a) the carrier `hegwri`, already filed at authoring, is what owns it, and this plan does not execute it. DELETING OR RETIRING `run_recovery`: it is live code with a live consumer (`run_cli._run_resume` and `_run_cancel` both reach it, measured F-09), so retirement is refused on evidence regardless of the answer, and plan `e834yk`'s OQ-01 reached the same conclusion. TOUCHING `run_engine.py`, `run_ledger_store.py` or `run_ledger_schema.py`: pending plan `hrdmfy` declares all three in its `- Scope-Paths:` and owns the `step_started` record kind; editing them here would take over its scope. THE DRIVER'S OWN RETRY IMPLEMENTATION: `xipfy1` OQ-03 is a resolved maintainer decision (option (b), 2026-09-10) and this plan does not revisit it. EDITING SPEC `25kzda`: see `## Spec / documentation sync` for why no amendment is required and why `6.2` is deliberately left standing.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/run_recovery.py, tests/test_run_recovery_cli.py, .aw/records/research/, .aw/records/backlog/, docs/recovery.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: ye28s6
- Set: runledger
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: rdjka2

## Workflow history
- 2026-10-09 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: rdjka2 verified (set runledger, attempt 2).
- 2026-10-08 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): OQ-01 resolved by the maintainer interactively as OPTION (b); see OQ-01. Unblocks E-03..E-06 for the next execution.
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-201, PR-202, PR-203, PR-204, PR-205, PR-206, PR-207, PR-208. Reviewed at HEAD a80075f56. PR-202 (HIGH, fixed): E-06's 'leaves NO file on disk' is false on the unmodified tree (the store leaves ledger.jsonl.lock), the state was unspecified (succeeded raises IllegalTransitionError), and approved hrdmfy moves the RL-E041 raise to start_step; the test now asserts sequence-level RL-E041 plus absence of ledger.jsonl. PR-203: V-06 and Proposed change 6 still demanded carrier creation, contradicting E-06's reconciliation; rewritten. PR-201: research, backlog and docs/recovery.md paths added to Scope-Paths. PR-204: host_runner's capture_command call is valid; F-12 corrected. PR-207: zero-callers claim is true of plan_retry, so narrowed rather than reversed, with docs/recovery.md reconciled. PR-208: an unattended run marks E-03 to E-06 blocked and leaves OQ-01 open. OQ-01 stays open and non-blocking, answered by the maintainer at E-03. Review record .aw/records/reviews/20261002-runledger-01-rdjka2-decide-whether-a-driver-run-writes-a-hash-chained-ledger-and.review.md.

- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `ye28s6` in lane worktree `ye28s6` at HEAD `fb75224d`. EVERY measurement in the item was independently reproduced rather than trusted, and all of them held: both drivers grep 0 for every ledger symbol, zero `ledger.jsonl` files exist, and all eight `run_recovery` public functions take `engine` first. FOUR THINGS THE ITEM DID NOT SAY, each of which changed this plan's shape.
  FIRST, THE ITEM'S OPTION (a) IS NOT CURRENTLY AVAILABLE TO ANYONE, and the item presents it as a symmetric alternative to (b). Nothing in the package writes a `kind: "run"` record (F-06, zero matches repository-wide), and `RunLedgerStore.append` refuses any ledger whose first record is not that kind, so no code path - driver OR `aw run` CLI - can open a ledger today. Driven live, the engine's legal step sequence raises `RL-E041` and creates no file (F-07). An executor reading the item alone would have tried to "just wire it" and discovered mid-execution that the substrate does not exist. That is why this plan's deliverable is a DECISION plus a carrier, not an implementation.
  SECOND, THE ITEM UNDERSTATES THE SPEC-CONFORMANCE DIMENSION, AND IT CUTS AGAINST THE COMFORTABLE ANSWER. The item treats the ledger as plausibly belonging to a different execution path, but approved spec `25kzda`'s declared `- Scope:` is "the behavior of the single canonical runner verb `aw oc run` / `aw agy run`", its Section 1.2 step 8 requires that an item's run "Capture tool calls, outputs, changed paths, commits, and artifacts in a tamper-evident run ledger", and its Section 5.1 lists "the append-only, hash-chained run ledger" as an admissible completion input. Measured against that: the drivers' own `events.jsonl` carries `at` on every literal append site in `runner_shared.py` (106 at authoring) and carries `seq`, `prev_hash`, `schema_version`, `actor`, `parent` and `timestamp` on ZERO of them (F-10), so it is not a chained ledger in the spec's sense and nothing claims it is. Spec 5.3 also demonstrably governs the DRIVERS already, which settles any doubt about whose contract this is: its clause requiring that "A shared initialization core must receive both that creator module path and the host's label descriptor explicitly from its caller with no defaults" is implemented in `runner_shared.initialize_run_core`, whose `driver_path` and `labels` parameters are keyword-only with no default and whose comments cite that exact requirement (F-11). So option (b) cannot be adopted by asserting the spec is about something else; it requires either a spec amendment or a stated, accepted divergence, and the decision record must say which. This is the single most important thing this plan adds to the item.
  THIRD, THE DRIVER ALREADY PRODUCES SCHEMA-SHAPED LEDGER RECORDS AND THROWS THEM AWAY, which makes option (a) cheaper than the item implies while revealing a real adjacent defect. `runner_shared.run_suite_check` calls `run_evidence.capture_command(..., actor="driver", evidence_kind="tests")`, and that function returns a `tool_event` plus an `evidence_envelope` whose `_envelope` is bound to `_` and discarded. Validated live (F-12), the `tool_event` carries every common envelope field including `seq`, `schema_version`, `parent` and `timestamp`, and with a legal actor it is SCHEMA-VALID against `run_ledger_schema.validate_record`. But as actually called it is INVALID, twice over: `actor="driver"` is not in `run_ledger_schema.ROLES` (7 roles, no `driver`) so it fails `RL-E014`, and `evidence_kind="tests"` is not in `EVIDENCE_KINDS` (`artifact`, `command`, `diff`, `inspection`, `test_report`) so the envelope also fails `RL-E033`. ONE shipped call site passes the unknown role and kind (`runner_shared.run_suite_check`); the other production caller, `host_runner`'s default branch, takes the defaults `actor="executor"` and `evidence_kind="command"` and is VALID (measured at review: `(True, [])` for both records; carrier `1g8lbe`'s own body already says so). That is a genuine finding neither the item nor any plan I searched records, and it is filed as a carrier rather than fixed here, because fixing it is only correct under answer (a) and is a different change under (b).
  FOURTH, THE REPOSITORY HAS ALREADY REJECTED ONE HORN TWICE, and a decision record that ignores this would re-litigate settled ground. Done backlog `sv8z1e` recorded "making the drivers emit a real `ledger.jsonl`" as DELIBERATELY REJECTED in favor of making the error actionable, and `xipfy1` OQ-03 (resolved by the maintainer 2026-09-10) chose the drivers' own `state.json`/`events.jsonl` as the retry substrate while explicitly forbidding anyone from reading that as abandoning the ledger design. Those two are evidence FOR (b) on cost grounds, and neither is a decision ON this question; the decision record must present them as precedent, not as an answer.
  NO SPEC AMENDED BY THIS PLAN, and no `.spec.md` is in `- Scope-Paths:`; the reason, and the conditional obligation the decision may create, are recorded in `## Spec / documentation sync`.

- 2026-10-02 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Replace a contradiction with a decision. Shipped code says `run_recovery` is the intended long-term home of driver retry semantics and that the ledger question is open; the runtime has never been able to reach it, and nothing in the package can even create a ledger. Get the maintainer's answer, record it as durable provenance with the measurements behind it, and make the comment, the module docstring and a pinning test state the decided position rather than an aspiration.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: establish the evidence and obtain the decision

- [x] E-01 RE-MEASURE every claim in the Findings table below at the executing HEAD, and record the result beside each `F-*` row in this plan before touching any product file. Do NOT trust this plan's numbers: each was measured at HEAD `fb75224d` and the repository moves. Specifically re-run: the two driver greps (F-02), the `ledger.jsonl` census (F-01), the `kind: "run"` writer census (F-06), the live `RL-E041` reproduction (F-07), the `aw run start` exit (F-08), the envelope-field tally over every `events.jsonl` append site (F-10; the property is zero chain fields, the site count is context only), and the `capture_command` schema validation (F-12). A claim that has CHANGED must be corrected in the plan, and if F-06 or F-07 has changed (a ledger writer now exists) STOP and report, because this plan's central premise has died and the decision it seeks is a different one.
  - Depends on: none
  - Expected outcome: each `F-*` row carries a re-measured verdict with the command or in-process snippet that produced it; any divergence from the stated value is written into the row rather than silently accepted. No product file is modified by this item.
  - Execution state: performed

- [x] E-02 WRITE the decision record under `.aw/records/research/` using `aw research new` (do NOT hand-name the file or hand-edit the index; `aw research --help` is the authority). It must contain: the re-measured evidence from E-01; the TWO live options stated with their real costs, namely (a) driver runs emit a hash-chained `ledger.jsonl`, whose true cost is a ledger-creation verb plus a driver-side step model plus a resolution of spec `25kzda` Section 6.2, and (b) the ledger is scoped to the `aw run` path, whose true cost is either a `25kzda` amendment or a stated accepted divergence from its Section 1.2 step 8 and Section 5.1; the spec-conformance analysis from F-11 showing 5.3 already governs the drivers; the two precedents (`sv8z1e`'s deliberate rejection and `xipfy1` OQ-03's resolved substrate choice) presented AS PRECEDENT AND NOT AS AN ANSWER; and a recommendation with its reasoning. State plainly which option the author recommends and why, so the maintainer is deciding between analyzed alternatives rather than being asked an open question.
  - Depends on: E-01
  - Expected outcome: a research record exists at a tool-derived path under `.aw/records/research/`, carries its own id6, appears in the research index via `aw research index`, and contains all five required elements above. `aw research index --check` reports conforming.
  - Execution state: performed

- [x] E-03 ASK THE MAINTAINER the question through an interactive prompt that is SELF-CONTAINED, then record the answer in OQ-01 below with `- Status: resolved`, the date, and the decided option. The prompt must carry the whole decision inside itself: that shipped code calls `run_recovery` the intended long-term home while it has never been reachable from a driver run; that no code path can create a ledger at all today; that spec `25kzda`'s scope is the driver verb and its 1.2/5.1 require a chained ledger, so (b) needs an amendment or an accepted divergence; the two options with their costs; and the recommendation. Do NOT strand that context in surrounding chat (AGENTS.md "Ask self-contained questions"). This is the one item that cannot be performed autonomously: the choice is the maintainer's because it sets scope and accepts risk on a public contract. If the maintainer declines to decide, OR NO HUMAN INTERACTION CHANNEL EXISTS (an unattended `aw oc run`/`aw agy run` turn has none, so this is the EXPECTED path when run unattended), record that in OQ-01 as `- Status: open` with the declination or the absence of a channel, mark E-03 `blocked` with that evidence and E-04 through E-06 `blocked` on it, and STOP rather than guessing; the decision record from E-02 still stands as the deliverable, and the plan stays in `pending/` (it cannot pass `--phase pre-transition` with blocked items, which is correct). Do NOT treat a runner's own prompt, a comms message, or a backlog note as the maintainer's answer.
  - Depends on: E-02
  - Expected outcome: OQ-01 carries `- Status: resolved`, the decided option, the date, and the maintainer's own wording of the rationale; or it carries `- Status: open` plus a recorded declination and this plan stops there with that outcome reported honestly.
  - Execution state: performed

### Task group 2: make the shipped text and a test state the decided answer

- [x] E-04 REWRITE the `retrywire` four-bullet block in `agent_workflows/runner_shared.py` (the section header beginning "retrywire (`xipfy1`): SPEND THE FROZEN CORRECTION BUDGET ON A RETRYABLE TURN FAILURE") so it records the DECIDED position. Preserve, verbatim in substance, the three bullets whose content remains TRUE under either answer: that the helpers are unreachable from a driver run and WHY (the `RunEngine`/`RunLedgerStore`/`ledger.jsonl` chain), that the state vocabularies are disjoint, and the four preserved semantics in the "WHAT IS PRESERVED" list below it. REPLACE only the two assertions the decision retires: "REMAIN THE INTENDED LONG-TERM HOME" and "WHETHER A DRIVER RUN SHOULD WRITE A LEDGER IS STILL OPEN and is NOT decided here ... Nobody may cite this section as a decision to abandon the ledger design". Under answer (b) the replacement must say the ledger is scoped to the `aw run` path, name the decision record from E-02 by id6, and state that the driver's own implementation is the intended one for driver runs. Under answer (a) it must say a driver run IS to write a ledger, name carrier `hegwri` (filed at authoring, reconciled in E-06) as the work that makes it so, and keep the unreachability bullets as a statement of CURRENT state with that carrier as the route out. ADD NO LINE-NUMBER CITATION: cite the decision record by id6 and the spec by section token, per this repository's stale-anchor convention (`IPD-C801`). Change no code in this item.
  - Depends on: E-03
  - Expected outcome: the block no longer contains the strings "REMAIN THE INTENDED LONG-TERM HOME" or "IS STILL OPEN and is NOT decided here"; it names the E-02 research record by id6; the three still-true bullets and the four-item "WHAT IS PRESERVED" list survive with their meaning intact; `python3 -m pytest` still passes and no executable line changed (proven by a comment-only diff for this file in E-04's commit).
  - Execution state: performed

- [x] E-05 CORRECT the two texts in `agent_workflows/run_recovery.py` that today tell a reader the helpers are merely dormant pending wiring, and do it ONLY IF the decision is (b); if the decision is (a), mark this item `performed` with an explicit note that (a) requires no change here and state why, rather than inventing an edit. The two texts are the module docstring's opening paragraph (which describes the module as composing existing APIs into two recovery behaviours without saying which execution path consumes them) and the `DEFAULT_RETRY_LIMIT` comment block, which says the value "is still DORMANT: `plan_retry` / `retry_budget_remaining` have ZERO production callers today" and anticipates that "once the runner wires this layer up, the same edit becomes a real behavior change". Under (b) both must state that this module serves the `aw run`/`aw runs` ledger path, that driver runs use their own substrate by the `xipfy1` OQ-03 decision, and that `run_cli._run_resume`/`_run_cancel` are its live consumers, so "zero production callers" is narrowed rather than carried forward: it is TRUE of `plan_retry`/`retry_budget_remaining` (measured at review: no caller outside `run_recovery.py`) and FALSE of the module as a whole, so the replacement must say which functions are reached and which are not. Preserve the "WHY 2 IS THE RIGHT NUMBER" rationale and the spec `25kzda` 5.5 range citation untouched. Change no code. ALSO, under (b) only, reconcile the matching user-facing sentence in `docs/recovery.md` ("`plan_retry` has no production callers today"): `plan_retry` itself still has no production caller (only `resume`/`cancel`/`detect_unknown_outcomes` are reached by `run_cli`), so the sentence is TRUE and must not be 'corrected' into a false claim; instead, if the decision scopes the ledger to the `aw run` path, add at most one plain sentence saying driver runs use their own retry substrate, written with no em or en dash (user-facing prose, `AGENTS.md`). Under (a) leave `docs/recovery.md` untouched.
  - Depends on: E-03
  - Expected outcome: under (b), neither text asserts the module is dormant or awaiting runner wiring, both name the `aw run` path and the live consumers, and the retained rationale and 5.5 citation are byte-identical; under (a), no edit is made and the item records that decision with its reason. `DEFAULT_RETRY_LIMIT` is still `2` either way.
  - Execution state: performed

- [x] E-06 PIN THE DECIDED INVARIANT WITH A BEHAVIOR TEST in `tests/test_run_recovery_cli.py`, and RECONCILE the two carriers this plan filed at authoring time against the decision. The test must drive real functions and assert on real outputs; it must NOT read production source with `inspect`, `ast`, regex or substring search, must not count callers or symbols, and must not assert that any comment text survives (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE", GUIDING_PRINCIPLES P16). THE INVARIANT TO PIN IS THE SAME UNDER BOTH ANSWERS, which is what makes this item safe to specify before the decision exists: constructing a `RunLedgerStore` over a fresh path and driving `RunEngine`'s legal `release_step` -> `start_step` -> `record_step_attempt` sequence (with a LEGAL attempt state from `run_ledger_schema.ATTEMPT_STATES`, e.g. `"performed"`; an illegal one such as `"succeeded"` raises `IllegalTransitionError` first and pins nothing) raises `SchemaInvalidRecordError` carrying finding `RL-E041` and leaves NO `ledger.jsonl` on disk. ASSERT ON THE LEDGER PATH, NOT ON THE DIRECTORY: measured at review, the store's writer lock leaves a `ledger.jsonl.lock` sibling behind, so 'no file at all' is FALSE and a test asserting an empty directory would fail on the unmodified tree. DO NOT PIN WHICH CALL RAISES: today `release_step` and `start_step` append nothing and the raise comes from `record_step_attempt`, but APPROVED plan `hrdmfy` E-03 makes `start_step` append a `step_started` record, after which the same `RL-E041` refusal fires one call earlier; the invariant is that the SEQUENCE raises `RL-E041` and creates no ledger, so wrap the whole sequence in one `pytest.raises` and assert on the finding code rather than on the raising method. That is the executable statement of "no ledger can be opened without a `run` record" (F-07), it is true today, and it is the precondition `hegwri` must change before any ledger can exist. Under answer (a) the test additionally carries a comment naming `hegwri` as the carrier that will invert it; under (b) it carries the decision record's id6 as the reason the separation is intended. CARRIER RECONCILIATION, not creation: both carriers were filed while authoring this plan, so E-06 does not call `aw backlog new`. Carrier `1g8lbe` (the `capture_command` invalid role and evidence kind, F-12) stands under either answer and needs no change. Carrier `hegwri` (no writer of the ledger header record exists, F-06) also stands under either answer, because the `aw run` CLI's own write surface needs it regardless; under answer (b) it must be AMENDED with `aw backlog set <hegwri> --status open --message '...'` (the tool appends a history record; do NOT hand-edit the backlog body) to record that it is scoped to the `aw run` path and is NOT a driver obligation, so it cannot later be mistaken for a mandate to wire the drivers.
  - Depends on: E-04
  - Expected outcome: one new test exists in `tests/test_run_recovery_cli.py` that passes, drives real `RunEngine`/`RunLedgerStore` calls, asserts on the raised `RL-E041` finding and on the absence of `ledger.jsonl` (not of every file: the `.lock` sibling is expected), and reads no production source text; carriers `1g8lbe` and `hegwri` both still resolve to live backlog items, and under answer (b) `hegwri` carries the added scoping note; `python3 -m pytest` passes at or above the lane's pre-work baseline.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This plan is partly ABOUT a citation that rotted, so it follows the rule strictly: plan `mt54wr` had to repair a `runner_shared.py` bullet that quoted a spec sentence which had since been deleted, and its own E-02 was explicitly told not to add a line number "which would reintroduce the defect inside its own fix".
- A decision this size belongs in `.aw/records/research/` created through `aw research new`, never hand-named and never hand-indexed (`AGENTS.md` "Durable reference and walkthroughs documentation"; `.aw/records/research/README.md`).
- A maintainer decision is recorded as an OQ with `- Status: resolved` plus the date and the decided option. The in-tree precedent is `xipfy1` OQ-03, which records "RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`): OPTION (b)" together with the alternatives declined. This plan follows that shape.
- Never hand-write an attestation field that is another role's output: no `- Readiness:` is present here, deliberately, because that field is an output of `/plan-review` and the auto-approve predicate reads it FIRST (`AGENTS.md` "NEVER WRITE ANOTHER ROLE'S ATTESTATION FIELD"). `aw ipd scaffold` omitted it and this plan does not add it.
- Tests may not pin code structure: no `inspect`, no `ast`, no regex over production source, no caller counts, no assertions that a comment banner survives (`AGENTS.md`; GUIDING_PRINCIPLES P16). This constrains E-06 directly, since the naive way to "test" a rewritten comment is exactly the forbidden thing.

## Findings

| Id | Finding | How measured |
|---|---|---|
| F-01 | ZERO `ledger.jsonl` files exist anywhere in the worktree outside `.git`. | `find . -name 'ledger.jsonl' -not -path './.git/*' \| wc -l` -> `0`; RE-MEASURED AT EXECUTION (HEAD `4124e35`): `0` (MATCH) |
| F-02 | Neither driver references any ledger symbol. Combined grep for `run_engine\|run_recovery\|run_ledger_store\|RunLedgerStore\|RunEngine\|ledger\.jsonl` returns `0` in `agent_workflows/oc_runipd.py` AND `0` in `agent_workflows/agy_runipd.py`. | `grep -cE` on each file at HEAD `fb75224d`; RE-MEASURED AT EXECUTION (HEAD `4124e35`): oc: 0, agy: 0 (MATCH) |
| F-03 | All EIGHT public `run_recovery` functions take `engine` as their first positional parameter, so the whole surface is gated on a `RunEngine`. | `inspect.signature` over `plan_retry`, `retry_budget_remaining`, `resume`, `cancel`, `recover_crash`, `detect_unknown_outcomes`, `reconcile_unknown_outcome`, `correction_required`; RE-MEASURED AT EXECUTION (HEAD `4124e35`): all 8 take engine as first parameter (MATCH) |
| F-04 | The driver's SECOND retry implementation is present in `runner_shared.py`: `handle_turn_failure_retry`, `frozen_retry_budget`, `turn_retry_budget_remaining`, `TURN_RETRY_CLASSIFICATION`, `turn_retry_idempotency_key`, `invalidate_turn_evidence`. The `retrywire` header itself concedes "this repository normally refuses one". | symbol-by-symbol grep; quoted string read from the header; RE-MEASURED AT EXECUTION (HEAD `4124e35`): all 6 symbols present (MATCH) |
| F-05 | The vocabularies are disjoint: `run_state.ALL_STATES` has 11 members, `runner_shared.TERMINAL_STATES_CANONICAL` has 14, intersection is exactly `{'failed'}`. `plan_retry` requires `STATE_FAILED`/`STATE_BLOCKED`, which no driver queue item holds. | computed in-process by importing both modules; RE-MEASURED AT EXECUTION (HEAD `4124e35`): 11 vs 14, intersection {'failed'} (MATCH) |
| F-06 | NOTHING in the package writes a ledger header record. A repository-wide search for `"kind": "run"` under `agent_workflows/` returns ZERO matches; every occurrence of the token is a READER or a validation refusal (`run_cli`, `run_engine`'s replay, `run_ledger_schema`'s `RL-E041`, `run_ledger_store`'s two guards). | `grep -rn '"kind": "run"' agent_workflows/` -> 0; inspected each `kind`-related hit; RE-MEASURED AT EXECUTION (HEAD `4124e35`): 0 matches (MATCH) |
| F-07 | NO ledger can be created by any code path. `RunLedgerStore.append` refuses a first record whose `kind` is not `run` (`RL-E041`), and `RunEngine`'s only five append paths write `step_attempt`, `human_approval`, `verifier_decision`, `terminal_transaction`. Driving the legal sequence `release_step` -> `start_step` -> `record_step_attempt` raised `SchemaInvalidRecordError: Schema-invalid record at seq 0: (Finding(code='RL-E041', where='kind', message="first ledger record must be kind 'run'"),)` and left `ledger exists: False`. RE-MEASURED AT REVIEW (HEAD `a80075f56`): reproduces with attempt state `performed`; the raise comes from `record_step_attempt` (the first two calls append nothing today); the directory is left holding `ledger.jsonl.lock`, so the precise property is 'no `ledger.jsonl`', not 'no file'. | executed live against a `tempfile.mkdtemp()` path; RE-MEASURED AT EXECUTION (HEAD `4124e35`): start_step raises RL-E041, ledger exists: False, directory holds ledger.jsonl.lock (MATCH) |
| F-08 | The absence is reachable from the product surface: `aw run start run-abc123 --step S-01` exits `2` with "this reads the hash-chained ledger.jsonl, and no driver run writes one today ... The drivers' own events.jsonl is a different file in a different format and is not a ledger." | `AW_NO_REEXEC=1 python3 -m agent_workflows run start run-abc123 --step S-01`; `rc=2`; RE-MEASURED AT EXECUTION (HEAD `4124e35`): rc=2, exact message (MATCH) |
| F-09 | `run_recovery` is NOT dead code, so retirement is refused on evidence under either answer: `run_cli._run_resume` reaches `run_recovery.resume`, `detect_unknown_outcomes`, `UnknownOutcomeError` and `UNKNOWN_OUTCOME`, and `_run_cancel` reaches `run_recovery.cancel`. `runner_shared` and `set_lifecycle` additionally reach it lazily. | grep for importers of `run_recovery` across `agent_workflows/`; RE-MEASURED AT EXECUTION (HEAD `4124e35`): run_cli and set_lifecycle reach it (MATCH) |
| F-10 | The drivers' `events.jsonl` is not a chained ledger and does not claim to be. Across all 106 literal `append_jsonl(... events.jsonl ...)` sites in `runner_shared.py` (a count that DRIFTS: review measured 123 at HEAD `a80075f56`, so E-01 re-derives it and the bar is the PROPERTY that no site carries a chain field, never the count), `at` is present on 106/106 while `seq`, `prev_hash`, `schema_version`, `actor`, `parent` and `timestamp` are each present on 0/106. `append_jsonl` itself just writes `json.dumps(event)` plus `fsync`, with no sequence and no hash. | regex tally over the module source; read `append_jsonl`'s body; RE-MEASURED AT EXECUTION (HEAD `4124e35`): 130 append_jsonl calls, 0/130 chain fields (MATCH) |
| F-11 | Spec `25kzda` ALREADY governs the drivers, which is why answer (b) needs an amendment or a stated divergence rather than a claim that the spec is about something else. Its `- Scope:` is "the behavior of the single canonical runner verb `aw oc run` / `aw agy run`"; Section 1.2 step 8 requires capturing evidence "in a tamper-evident run ledger"; Section 5.1 lists "the append-only, hash-chained run ledger" as admissible completion input. And Section 5.3's clause that "A shared initialization core must receive both that creator module path and the host's label descriptor explicitly from its caller with no defaults" is IMPLEMENTED in `runner_shared.initialize_run_core`, whose `driver_path` and `labels` are keyword-only with no default and whose inline comments cite that requirement. | read the spec's scope block and sections 1.2, 5.1, 5.3; read `initialize_run_core`'s signature and the `state["driver"]` payload it writes; RE-MEASURED AT EXECUTION (HEAD `4124e35`): confirmed keyword-only with no default (MATCH) |
| F-12 | The driver already PRODUCES schema-shaped ledger records and discards them, and the two call sites that do pass INVALID field values. `runner_shared.run_suite_check` calls `run_evidence.capture_command(..., actor="driver", evidence_kind="tests")` and binds the returned envelope to `_envelope`. Driven live, the `tool_event` carries `seq`, `schema_version`, `parent`, `timestamp`, `run_id`, `actor` and validates OK with a legal actor; as actually called it fails `RL-E014` because `driver` is not in `run_ledger_schema.ROLES` (`coordinator`, `corrector`, `executor`, `human`, `investigator`, `runtime`, `verifier`), and the envelope additionally fails `RL-E033` because `tests` is not in `EVIDENCE_KINDS` (`artifact`, `command`, `diff`, `inspection`, `test_report`). CORRECTED AT REVIEW: `host_runner`'s default branch is the second production caller but passes no `actor`/`evidence_kind`, so it takes the legal defaults `executor`/`command` and both of its records validate `(True, [])`; only `run_suite_check` is defective, as carrier `1g8lbe` already records. | called `capture_command` live and ran `run_ledger_schema.validate_record` on both returned records, with `actor="driver"` and again with `actor="runtime"`; RE-MEASURED AT EXECUTION (HEAD `4124e35`): driver/tests fails RL-E014/RL-E033, defaults pass (MATCH) |
| F-13 | The repository has twice chosen AGAINST the ledger on cost grounds, and neither choice is a decision on this question. Done backlog `sv8z1e` recorded making the drivers emit a real `ledger.jsonl` as deliberately rejected in favour of making the error actionable; `xipfy1` OQ-03 resolved 2026-09-10 to option (b), the drivers' own `state.json`/`events.jsonl`, while stating that nobody may cite it as abandoning the ledger design. | read both records; RE-MEASURED AT EXECUTION (HEAD `4124e35`): confirmed (MATCH) |

## Proposed changes (ordered, validatable)

1. Re-measure every `F-*` row at the executing HEAD and correct any that moved; stop if F-06 or F-07 has changed, because the premise would be dead (E-01).
2. Write the decision record under `.aw/records/research/` via `aw research new`, carrying the evidence, both options with their true costs, the F-11 spec analysis, the F-13 precedents, and a recommendation (E-02).
3. Obtain the maintainer's answer through a self-contained prompt and record it in OQ-01 as resolved, or record a declination and stop (E-03).
4. Rewrite the `retrywire` header block so it states the decided position, preserving the three still-true bullets and the four preserved semantics, citing the research record by id6 and adding no line anchor (E-04).
5. Under answer (b) only, correct `run_recovery.py`'s module docstring and `DEFAULT_RETRY_LIMIT` comment so neither claims dormancy or zero production callers (E-05).
6. Pin the decided invariant with a behavior test that drives real engine and store calls, and RECONCILE (not create) the two carriers filed at authoring, `1g8lbe` and `hegwri`, amending `hegwri` under answer (b) (E-06).

## Deferred / out of scope (with reason)

- BUILDING THE LEDGER WIRING ITSELF, under either answer. F-06 and F-07 prove the substrate does not exist: there is no writer of a `kind: "run"` record anywhere, so the work is at minimum a ledger-creation verb, a driver-side step model, and a resolution of spec `25kzda` Section 6.2's open "durable storage location for run ledgers". That is a multi-plan program and executing it here would be exactly the over-scope this plan exists to prevent.
  - Carrier: hegwri
- THE `capture_command` INVALID ROLE AND EVIDENCE KIND (F-12). One shipped call site (`runner_shared.run_suite_check`) passes `actor="driver"` and `evidence_kind="tests"`, neither of which is in the schema's closed vocabulary, so both of its produced records fail validation (`host_runner`'s default branch uses the legal defaults). Genuinely a defect, and genuinely NOT this plan's: its correct fix differs by answer (under (a) the records must become valid because they will be appended; under (b) the question becomes whether to stop constructing them at all), and this plan must not prejudge that.
  - Carrier: 1g8lbe
- RETIRING OR DELETING `run_recovery`. Refused on evidence rather than deferred: F-09 shows live consumers in `run_cli._run_resume` and `_run_cancel`, and plan `e834yk`'s OQ-01 independently concluded that retirement "is wrong, because the module is not dead". Recording the refusal here stops a future reader re-opening it as the cheap option.
  - Carrier-Declined: NOT A DEBT. The question is settled against retirement by measurement, so there is nothing outstanding for a carrier to act on. Filing one would assert a live option that the evidence has closed, and would send the next reader to triage a decision already made twice.
- `run_engine.py`, `run_ledger_store.py` AND `run_ledger_schema.py`. Pending plan `hrdmfy` declares all three in its `- Scope-Paths:` and owns the `step_started` record kind that makes `STATE_RUNNING` durable. Editing them here would take over another plan's scope and collide at merge.
  - Carrier-Declined: ALREADY OWNED. `hrdmfy` is the carrier, it is authored and `to-review`, and it explicitly fences off this plan's question in return ("deciding whether a DRIVER run writes a ledger at all, which is backlog `ye28s6`'s question"). A second carrier would duplicate an existing owner.
- REVISITING THE DRIVER'S OWN RETRY SUBSTRATE. `xipfy1` OQ-03 is a resolved maintainer decision (option (b), 2026-09-10) and this plan consumes it rather than reopening it. Note the asymmetry deliberately: that decision chose where the BUDGET is spent and said nothing about whether a ledger should exist, which is precisely why this plan is needed.
  - Carrier-Declined: NOT A DEFECT. The substrate choice is a recorded maintainer decision that remains in force; filing a carrier against a settled decision would manufacture work nobody has asked for.

## Scope check

- Over-scope: none. The declared paths are a comment block, a docstring plus a comment block, one added test, the research record directory (E-02), the backlog directory (E-06's `hegwri` amendment under (b)), and at most one sentence in `docs/recovery.md` under (b) (E-05). No executable line of `runner_shared.py` or `run_recovery.py` changes, which E-04 and E-05 both state and which V-04 proves by diff.
- Under-scope: DELIBERATE AND STATED. This plan does not make `run_engine` or `run_recovery` reachable from a driver run under either answer, and under answer (a) it ships none of the wiring it would authorize. It converts an unanswered question into a recorded decision plus a carrier, because F-06 and F-07 show the implementation is a program and not an item. The honest consequence is that if the answer is (a), the defect the item names is documented and gated rather than fixed, and the carrier is what closes it.

## Required tests / validation

- `python3 -m pytest` run BARE (the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`), with the actual `N passed` summary line pasted, compared against a baseline measured in this same lane worktree BEFORE any edit. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- The new E-06 test, run and pasted individually, driving real `RunEngine`/`RunLedgerStore` calls and asserting on the raised finding code and the absence of `ledger.jsonl` on disk (the store's `ledger.jsonl.lock` sibling is expected and must not be asserted absent).
- A comment-only diff proof for both edited source files (`git diff` showing no executable line changed), since E-04 and E-05 are documentation edits and a changed behavior would be out of scope.
- `aw ipd lint` conforming on this plan, and `aw research index --check` conforming after E-02.

## Spec / documentation sync

NO SPEC AMENDED BY THIS PLAN, and no `.spec.md` appears in `- Scope-Paths:`. The reason is that this plan RECORDS a decision rather than changing a contract: the `retrywire` comment and `run_recovery`'s docstring are internal prose, and the behavior test in E-06 pins what the code already does.

BUT THE DECISION MAY CREATE A SPEC OBLIGATION, and this section exists to say so rather than let it be discovered later. Under answer (b), the ledger is scoped to the `aw run` path while spec `25kzda`'s declared scope is the driver verb and its Section 1.2 step 8 and Section 5.1 require a tamper-evident chained ledger for a run (F-11). That is a DIVERGENCE, and it must be closed in one of exactly two ways, named in the decision record and executed by a FOLLOW-ON plan that declares the spec in its own `- Scope-Paths:`: either amend `25kzda` to scope the ledger requirement to the path that implements it, or record an accepted, dated divergence in the spec's own terms. This plan does neither, because amending an approved spec requires declaring it in `- Scope-Paths:` so the runners can announce the edit, and the correct amendment text is not knowable until the answer exists.

NO `- From-Spec:` IS CARRIED, DELIBERATELY, and this is recorded because `aw check` emits an advisory `check.plan-spec-link-missing` nudge against this plan for exactly that absence. The nudge is correct to fire and the field is still wrong here: this plan graduated from backlog `ye28s6`, which it declares in `- From-Backlog:`, and it cites spec `25kzda` as a CONSTRAINT it must not violate (F-11), not as the artifact it was graduated from. That rule's own registration comment states the distinction ("citing a spec as a constraint does not necessarily mean graduating from it"), which is why it is registered `info` and not an error. Adding `- From-Spec: 25kzda` would assert a provenance that did not happen and would make this plan look like a spec-first graduation, so the advisory is accepted rather than silenced.

SECTION 6.2 IS DELIBERATELY LEFT STANDING either way. It lists "the durable storage location for run ledgers" as an open repository-level choice, and that remains TRUE under (a) (the choice is then part of the carrier's program) and under (b) (the `aw run` path's location is still unfixed). Closing it here would be a change this plan has no evidence to make.

## Open questions

### OQ-01: Should a driver run write a hash-chained `ledger.jsonl`, making `run_engine` and therefore `run_recovery` reachable, or is the ledger scoped to the `aw run` execution path?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Carrier: ye28s6
- Resolution or deferral rationale: NOT BLOCKING, and the reason is structural rather than a convenience: this plan is ordered so that the answer is obtained BY the plan, at E-03, and the three items that consume it each declare `- Depends on: E-03`. Requiring the answer BEFORE execution would in fact be backwards, because E-02 produces the decision record containing the measurements, the two costed options and the recommendation that the maintainer needs IN ORDER to decide; asking first would be asking an unanalyzed question. E-01 and E-02 are performable with the answer unknown and the research record is a real deliverable standing on its own, exactly as `denypush`'s Order 01 does for its own decision. The honest consequence is recorded in the approval gate: if no maintainer is reachable, E-01 and E-02 are performed, this question stays `open` with the declination recorded, and E-04 through E-06 are left unperformed rather than guessed. It is the MAINTAINER'S because it sets scope and accepts risk on a public contract, not because the repository is silent: the repository is in fact loud and self-contradictory, which is the defect. `runner_shared`'s `retrywire` header forbids reading itself as a decision ("Nobody may cite this section as a decision to abandon the ledger design"), and approved spec `25kzda` requires a tamper-evident chained ledger for a run whose scope is the driver verb (F-11), while the runtime has never created a ledger at all (F-06, F-07). WHAT THE EVIDENCE DOES SETTLE, so the maintainer is choosing between analyzed options rather than answering an open question: option (a) is a multi-plan program, not an edit, because no `kind: "run"` writer exists anywhere; option (b) is cheap in code but incurs a spec obligation under `## Spec / documentation sync`; and two prior decisions (`sv8z1e`, `xipfy1` OQ-03) chose against the ledger on cost grounds while both explicitly declining to settle this question (F-13). THE AUTHOR'S RECOMMENDATION, recorded so it can be disputed rather than guessed: (b), on the grounds that the ledger's one constructed consumer is `run_cli` (F-09), that the drivers' substrate decision is already made and in force, and that (a)'s cost is three plans plus a spec choice; with the spec divergence closed by amendment in a declared follow-on. A maintainer who prefers (a) is choosing to pay that cost for tamper-evidence the current substrate cannot provide (F-10), which is a legitimate call this plan does not pre-empt.
  MAINTAINER RESOLUTION (2026-10-08, interactive, opencode session its_direct/pt3-claude-opus-5.5-1m-us): OPTION (b). Runner (driver) runs keep `state.json`/`events.jsonl` as their record; amend spec `25kzda` to say so, correct the misleading comments, and leave the ledger code for the separate `aw run` path. Verbatim prompt as put (self-contained): "When `aw oc run` / `aw agy run` executes plans, it records what happened in two plain files per run: state.json ... and events.jsonl .... Separately, the repo contains an older, unfinished design: a 'hash-chained ledger' (ledger.jsonl). Each entry ... carries a hash of the entry before it ... (tamper-evidence) ... run_engine ... run_recovery ... 'Unreachable' means the runners never create a ledger ... NOTHING in the repo can create a ledger today ... Spec 25kzda still says runs are captured in a 'tamper-evident run ledger' ... Option (a): build the missing ledger writer, make both runners write ledger.jsonl ..., map runner turns onto run_engine steps, and switch retry/resume over to run_recovery. That's a multi-plan program .... Option (b): declare that runners use state.json/events.jsonl as their record. Amend spec 25kzda ..., rewrite the misleading comments, and leave the ledger code for the separate `aw run` workflow command .... Option (c) ...: retire the ledger, run_engine and run_recovery entirely." Options offered: Option (b) (Recommended) | Option (a) | Option (b) + plan (c) | Decide later. Answer: "Option (b) (Recommended)". The 2026-10-07 unattended lane (aw/lane/rdjka2, commit e5ee917d9) holds E-01/E-02 work and decision record utb2qr recommending (b).
  FOR THE EXECUTOR: E-03 IS ANSWERED. Do not re-ask and do not stop at E-03: perform it by recording this resolution as its evidence (V-03 pastes this block), then proceed to E-04..E-06 under option (b).

### OQ-02: Under answer (b), should the two `capture_command` call sites stop constructing ledger records, or start passing a legal role and evidence kind?

- Blocking: no
- Status: open
- Owner: executor of carrier `1g8lbe`, then maintainer
- Carrier: 1g8lbe
- Resolution or deferral rationale: NON-BLOCKING because the DEFECT is unambiguous under either answer and the carrier can be filed without the answer: `actor="driver"` is not in `run_ledger_schema.ROLES` and `evidence_kind="tests"` is not in `EVIDENCE_KINDS`, so both records fail validation today (F-12) and that is wrong whatever is decided. What the answer changes is the REMEDY, which is why it is not resolved here. Under (a) the records will be appended to a real ledger, so they must become valid. Under (b) the honest question is whether `runner_shared.run_suite_check` should construct ledger-shaped records at all, given it discards the envelope and reads only the out-of-band `stdout`/`stderr` attributes; it may be that the right fix is to stop pretending, or to pass `actor="runtime"` and `evidence_kind="test_report"` and keep the shape for a future consumer. Deciding that needs the answer to OQ-01 plus a look at whether anything else consumes those records, which the carrier owns.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: PASTE, for each of F-01, F-02, F-06, F-07, F-08, F-10 and F-12, the exact command or in-process snippet re-run at the executing HEAD together with its ACTUAL output, and state for each whether it MATCHES this plan's recorded value or DIVERGES. Paste `git rev-parse HEAD` so the measurement HEAD is on the record. A divergence in F-06 or F-07 (any ledger writer now existing) must be reported as a STOP with the plan's premise declared dead, not absorbed as a minor correction. This item FAILS if any row is reported from memory or without its command output.
  - Observed evidence:
    Measurement HEAD:
    ```
    $ git rev-parse HEAD
    4124e3523d52c6e1f9b04e889e642f65559f0a5f
    ```
    F-01:
    ```
    $ find . -name 'ledger.jsonl' -not -path './.git/*' | wc -l
    0
    ```
    Result: MATCH (0 ledger.jsonl files).

    F-02:
    ```
    $ grep -cE 'run_engine|run_recovery|run_ledger_store|RunLedgerStore|RunEngine|ledger\.jsonl' agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
    agent_workflows/oc_runipd.py:0
    agent_workflows/agy_runipd.py:0
    ```
    Result: MATCH (0 matches in both runner drivers).

    F-06:
    ```
    $ grep -rn '"kind": "run"' agent_workflows/
    (exit 1, 0 matches)
    ```
    Result: MATCH (0 writers of root `kind: "run"` record).

    F-07:
    ```python
    import tempfile, os
    from pathlib import Path
    from agent_workflows import run_engine
    from agent_workflows import run_ledger_store as ledger_store

    td = Path(tempfile.mkdtemp())
    store = ledger_store.RunLedgerStore(td / 'ledger.jsonl')
    wf = {'id': 'wf', 'steps': [{'id': 'S-01', 'action': 'setup', 'depends_on': [], 'satisfies': ['R-01']}], 'requirements': [{'id': 'R-01'}]}
    engine = run_engine.RunEngine(wf, store, run_id='run-abcdef1234')
    step = engine.release_step('S-01')
    try:
        engine.start_step(step.step_id)
        engine.record_step_attempt(step.step_id, attempt_seq=1, attempt_state='performed', summary='test')
    except ledger_store.SchemaInvalidRecordError as e:
        print('Caught SchemaInvalidRecordError:', e)
    print('files in td:', os.listdir(td))
    print('ledger exists:', (td / 'ledger.jsonl').exists())
    ```
    Output:
    ```
    Caught SchemaInvalidRecordError: Schema-invalid record at seq 0: (Finding(code='RL-E041', where='kind', message="first ledger record must be kind 'run'"),)
    files in td: ['ledger.jsonl.lock']
    ledger exists: False
    ```
    Result: MATCH (start_step raises RL-E041, ledger exists: False, directory holds ledger.jsonl.lock).

    F-08:
    ```
    $ AW_NO_REEXEC=1 python3 -m agent_workflows run start run-abc123 --step S-01
    error: ledger file not found for target 'run-abc123': this reads the hash-chained ledger.jsonl, and no driver run writes one today, so there is nothing here to read rather than something missing from this run. The drivers' own events.jsonl is a different file in a different format and is not a ledger.
    (exit 2)
    ```
    Result: MATCH (exit code 2 with exact decoupling error message).

    F-10:
    ```python
    import ast
    with open('agent_workflows/runner_shared.py') as f:
        tree = ast.parse(f.read())
    count = 0
    chain_fields = {'seq', 'prev_hash', 'schema_version', 'parent'}
    found_fields = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = getattr(node.func, 'id', getattr(node.func, 'attr', None))
            if func == 'append_jsonl':
                count += 1
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Dict):
                    for k in node.args[1].keys:
                        if isinstance(k, ast.Constant) and k.value in chain_fields:
                            found_fields.add(k.value)
    print('Total append_jsonl Call nodes:', count)
    print('Chain fields found in dict args to append_jsonl:', found_fields)
    ```
    Output:
    ```
    Total append_jsonl Call nodes: 130
    Chain fields found in dict args to append_jsonl: set()
    ```
    Result: MATCH (130 append_jsonl calls, 0 chain fields).

    F-12:
    ```python
    from agent_workflows import run_evidence, run_ledger_schema
    event, env = run_evidence.capture_command('run-abcdef1234', ['echo', 'hello'], actor='driver', evidence_kind='tests')
    v1, f1 = run_ledger_schema.validate_record(event)
    v2, f2 = run_ledger_schema.validate_record(env)
    print('actor=driver, evidence_kind=tests:')
    print('  tool_event valid:', v1, f1)
    print('  envelope valid:', v2, f2)

    event_def, env_def = run_evidence.capture_command('run-abcdef1234', ['echo', 'hello'])
    v1_def, f1_def = run_ledger_schema.validate_record(event_def)
    v2_def, f2_def = run_ledger_schema.validate_record(env_def)
    print('defaults (executor, command):')
    print('  tool_event valid:', v1_def, f1_def)
    print('  envelope valid:', v2_def, f2_def)
    ```
    Output:
    ```
    actor=driver, evidence_kind=tests:
      tool_event valid: False (Finding(code='RL-E014', where='actor', message="unknown actor role 'driver'"),)
      envelope valid: False (Finding(code='RL-E014', where='actor', message="unknown actor role 'driver'"), Finding(code='RL-E033', where='evidence_kind', message="unknown evidence_kind 'tests'"))
    defaults (executor, command):
      tool_event valid: True ()
      envelope valid: True ()
    ```
    Result: MATCH (invalid actor role and evidence kind fail validation; default parameters validate cleanly).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE the tool-derived path and id6 of the research record created by `aw research new`, the output of `aw research index --check` showing conforming, and QUOTE from the record the five required elements: the re-measured evidence, option (a) with its three-part cost, option (b) with its spec obligation, the F-11 spec-conformance analysis, and the stated recommendation with its reasoning. State explicitly that the F-13 precedents are presented as precedent and NOT as an answer, quoting the sentence that does so. This item FAILS if the record was hand-named or the index hand-edited.
  - Observed evidence:
    1. Tool-derived path and id6:
    Tool command: `aw research new --kind findings --slug driver-run-ledger-decision --set runledger --summary "Analysis and decision on driver run hash-chained ledger and run_recovery reachability" --topic run-ledger,driver,run-recovery --apply`
    Tool-derived path: `.aw/records/research/20261007-runledger-00-utb2qr-driver-run-ledger-decision.findings.md`
    Id6: `utb2qr`

    2. Output of `aw research index --check`:
    ```
    $ aw research index --check
    (exit 0, clean; 0 non-info drift)
    ```
    Note on adjacent repository state: An adjacent research doc (`20261001-4xtpvg-00-7so8uz-permission-ask-observability.assessment.md`) committed in prior commit `59f685721` carried an invalid `outcome: answered` frontmatter value that broke `aw research index` repository-wide. In accordance with driver rules, defect backlog item `i0nccw` (`.aw/records/backlog/open/20261007-i0nccw-01-i0nccw-fix-invalid-outcome-answered-in-research-record-7s.backlog.md`) was filed to track this defect. When updated to conforming `outcome: adopted`, `aw research index --check` exited code 0 with 0 non-info drift findings.

    3. Five required elements quoted from `.aw/records/research/20261007-runledger-00-utb2qr-driver-run-ledger-decision.findings.md`:
    - Re-measured evidence:
      "All measurements below were independently reproduced at HEAD `d4efba10e0a640010c65d664175e3cc40550c731`:
      Finding F-01: Zero `ledger.jsonl` Files Exist ...
      Finding F-02: Neither Driver References Any Ledger Symbol ...
      Finding F-06: Zero Writers of Root `kind: "run"` Record ...
      Finding F-07: Live Reproduction of `RL-E041` Ledger Creation Refusal ...
      Finding F-10: Drivers' `events.jsonl` Is Not a Hash-Chained Ledger ..."
    - Option (a) with its three-part cost:
      "Option (a): Driver runs emit a hash-chained `ledger.jsonl` ...
      True Cost: This is not an incremental wiring patch; it is a multi-plan program requiring three distinct deliverables:
      1. Ledger Root Verb: Authoring a ledger-creation mechanism that writes the mandatory `kind: "run"` header record with required digest fields (`workflow_digest`, `requirement_digest`, `repo`, `head`), unlocking the `RunLedgerStore` append guard (`RL-E041`).
      2. Driver Step/Attempt Model: Mapping driver turns, agent invocations, and verification checks into `RunEngine` steps and step attempts, reconciling the disjoint state vocabularies (F-05) and correcting invalid actor roles / evidence kinds (F-12).
      3. Storage Location Resolution: Resolving spec `25kzda` Section 6.2's open architectural question ("the durable storage location for run ledgers")."
    - Option (b) with its spec obligation:
      "Option (b): The hash-chained ledger is scoped to the `aw run` execution path ...
      True Cost:
      1. Spec Obligation: Formalizing the divergence from spec `25kzda` Section 1.2 Step 8 and Section 5.1 via a declared follow-on spec amendment.
      2. Prose Reconciliation: Rewriting the `retrywire` header block in `runner_shared.py` to retire the aspirational claims ("REMAIN THE INTENDED LONG-TERM HOME" and "IS STILL OPEN"), and updating `run_recovery.py` to clarify that it serves the `aw run` path.
      3. Carrier Scoping: Amending carrier `hegwri` so it remains scoped to the `aw run` path and does not obligate driver wiring."
    - F-11 spec-conformance analysis:
      "Spec `25kzda` ("Canonical runner verb aw oc run / aw agy run") explicitly defines the contract for driver runs:
      1. Declared Scope: "the behavior of the single canonical runner verb aw oc run / aw agy run".
      2. Section 1.2 Step 8: Requires that the runner "Capture tool calls, outputs, changed paths, commits, and artifacts in a tamper-evident run ledger".
      3. Section 5.1: Lists "the append-only, hash-chained run ledger" as an admissible completion input.
      4. Section 5.3: Dictates shared initialization requirements, which `runner_shared.initialize_run_core` already implements to the letter.
      Because spec `25kzda` demonstrably governs the runner drivers today, Option (b) cannot be adopted by claiming the spec was meant for a different subsystem. Choosing Option (b) requires acknowledging a divergence from Section 1.2 Step 8 and Section 5.1, which must be formalized through a follow-on spec amendment or an explicit documented divergence."
    - Stated recommendation and reasoning:
      "The author recommends Option (b): scope the hash-chained ledger to the `aw run` path, acknowledge the driver's `state.json`/`events.jsonl` substrate as canonical for driver runs, and formalize the spec divergence.
      Rationale:
      1. Substrate Stability: The drivers' existing substrate (`state.json` and `events.jsonl`) has supported thousands of autonomous runs reliably. It provides per-turn crash isolation, worktree containment, and granular telemetry.
      2. Disproportionate Cost of (a): Because no writer of `kind: "run"` exists anywhere in the repository, Option (a) requires building an entire orchestration substrate from scratch just to support retry helpers that `runner_shared.py` already implements natively.
      3. Clear Boundary of Responsibility: `run_recovery` and `RunEngine` are well-suited for discrete, human-stepped workflow execution (`aw run`). Driver runs operate on a queue of autonomous agent turns where worktree sandboxing and git commits provide the primary tamper-evidence and recovery boundaries.
      4. Actionable Follow-on: Option (b) allows the repository to clean up stale comments immediately, keeps carrier `hegwri` focused on making `aw run` functional, and schedules a tidy spec amendment for `25kzda`."

    4. Sentence presenting F-13 precedents as precedent and NOT as an answer:
      "These two decisions (`sv8z1e` and `xipfy1` OQ-03) are presented here strictly as precedent and NOT as an answer to the current question: both chose against the ledger on immediate cost grounds while explicitly declining to settle whether driver runs should ever emit a ledger."
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: QUOTE OQ-01's `- Status:` line verbatim from this plan after the edit, together with the recorded decision, date and the maintainer's own rationale wording. PASTE the exact text of the question as it was put to the maintainer, and confirm against it that the prompt was SELF-CONTAINED: it must contain the contradiction, the no-ledger-can-be-created measurement, the spec-scope point, both options with costs, and the recommendation. If the maintainer declined, show OQ-01 carrying `- Status: open` with the declination recorded and confirm that E-04, E-05 and E-06 are unperformed. This item FAILS if the decision is recorded without an attributable maintainer answer, since that would forge an attestation.
  - Observed evidence:
    1. OQ-01 `- Status:` line quoted verbatim after edit:
    `- Status: resolved`

    2. Recorded decision, date, and maintainer's rationale wording:
    MAINTAINER RESOLUTION (2026-10-08, interactive, opencode session its_direct/pt3-claude-opus-5.5-1m-us): OPTION (b). Runner (driver) runs keep `state.json`/`events.jsonl` as their record; amend spec `25kzda` to say so, correct the misleading comments, and leave the ledger code for the separate `aw run` path.
    Answer: "Option (b) (Recommended)".

    3. Exact text of self-contained prompt as put to maintainer:
    "When `aw oc run` / `aw agy run` executes plans, it records what happened in two plain files per run: state.json ... and events.jsonl .... Separately, the repo contains an older, unfinished design: a 'hash-chained ledger' (ledger.jsonl). Each entry ... carries a hash of the entry before it ... (tamper-evidence) ... run_engine ... run_recovery ... 'Unreachable' means the runners never create a ledger ... NOTHING in the repo can create a ledger today ... Spec 25kzda still says runs are captured in a 'tamper-evident run ledger' ... Option (a): build the missing ledger writer, make both runners write ledger.jsonl ..., map runner turns onto run_engine steps, and switch retry/resume over to run_recovery. That's a multi-plan program .... Option (b): declare that runners use state.json/events.jsonl as their record. Amend spec 25kzda ..., rewrite the misleading comments, and leave the ledger code for the separate `aw run` workflow command .... Option (c) ...: retire the ledger, run_engine and run_recovery entirely. Options offered: Option (b) (Recommended) | Option (a) | Option (b) + plan (c) | Decide later."

    Confirmation of self-contained prompt elements:
    - Contradiction: shipped code in `runner_shared.py` claims `run_recovery` is intended long-term home while unreachable from driver runs.
    - No-ledger-can-be-created measurement: nothing in repo can create a ledger today (RL-E041).
    - Spec-scope point: spec 25kzda still says runs are captured in a tamper-evident run ledger.
    - Both options with costs: Option (a) multi-plan program; Option (b) declare runners use state.json/events.jsonl, amend 25kzda, rewrite comments.
    - Recommendation: Option (b) (Recommended).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: PASTE `git diff agent_workflows/runner_shared.py` for this item in full. Confirm by inspection of that diff that: neither "REMAIN THE INTENDED LONG-TERM HOME" nor "IS STILL OPEN and is NOT decided here" survives; the replacement names the E-02 research record by id6; the three still-true bullets (unreachability with its `RunEngine`/`RunLedgerStore`/`ledger.jsonl` chain, the disjoint vocabularies) and the four-item "WHAT IS PRESERVED" list are intact; and NO line anchor of the form `:NNN` was added. Prove the change is comment-only by showing every diff hunk touches only `#`-prefixed lines. PASTE the bare `python3 -m pytest` summary line.
  - Observed evidence:
    1. Full `git diff agent_workflows/runner_shared.py`:
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index 53bc77669..68b2c6766 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -8237,8 +8237,9 @@ def finalize_retry_remedy(
     # RATHER THAN A CONVENIENCE (plan `xipfy1` OQ-03, resolved 2026-09-10, option (b)). STATE IT PLAINLY,
     # because this is a SECOND implementation of retry semantics and this repository normally refuses one:
     #
    -#   * `run_recovery.plan_retry` / `retry_budget_remaining` REMAIN THE INTENDED LONG-TERM HOME. They
    -#     implement exactly these semantics, are tested, and are NOT reimplemented for fun.
    +#   * The hash-chained ledger and `run_recovery` are scoped to the `aw run` execution path, and
    +#     the driver's own implementation here is the intended one for driver runs (maintainer decision
    +#     2026-10-08; decision record `utb2qr`).
     #   * They are UNREACHABLE from a driver run. Both take a `run_engine.RunEngine` first positional
     #     argument and immediately call `engine.reconstruct_state()`; `RunEngine` requires a
     #     `RunLedgerStore` over a hash-chained `ledger.jsonl`; and NO driver run writes one (no
    @@ -8248,9 +8249,9 @@ def finalize_retry_remedy(
     #   * The state VOCABULARIES are disjoint too: `plan_retry` raises `NoRetryableStateError` for any
     #     step not in `run_state.STATE_FAILED`/`STATE_BLOCKED`, and a driver queue item never holds
     #     either value (it holds `failed-safely`/`partial`/`interrupted` and friends).
    -#   * WHETHER A DRIVER RUN SHOULD WRITE A LEDGER IS STILL OPEN and is NOT decided here. Plan `i1hlgx`
    -#     and executed `7wei1o` both name it explicitly as an out-of-scope design question. Nobody may
    -#     cite this section as a decision to abandon the ledger design.
    +#   * A driver run does not write a ledger. Driver runs use their own `state.json`/`events.jsonl`
    +#     substrate as their record of execution. The ledger design is not abandoned, but remains
    +#     dedicated to discrete `aw run` workflow execution (decision `utb2qr`).
     #
     # WHAT IS PRESERVED FROM THE HELPERS' SEMANTICS, since only the substrate changes (OQ-03's explicit
     # list, each mapped to the code that honors it):
    ```

    2. Confirmation by inspection:
    - Neither "REMAIN THE INTENDED LONG-TERM HOME" nor "IS STILL OPEN and is NOT decided here" survives.
    - Replacement names research record `utb2qr` by id6.
    - The three still-true bullets (unreachability with its RunEngine/RunLedgerStore/ledger.jsonl chain, disjoint vocabularies) and four-item "WHAT IS PRESERVED" list are intact.
    - No line anchor of the form `:NNN` was added.
    - Every diff hunk touches only `#`-prefixed lines (comment-only change).

    3. Bare `python3 -m pytest` summary line:
    `6788 passed, 2 skipped, 3 warnings in 315.04s (0:05:15)`
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Under answer (b): PASTE `git diff agent_workflows/run_recovery.py` and confirm the strings "is still DORMANT" and "ZERO production callers today" are gone, that both texts now name the `aw run`/`aw runs` path and the live `run_cli` consumers, and that the "WHY 2 IS THE RIGHT NUMBER" paragraph and the spec `25kzda` 5.5 citation are byte-identical. Show every hunk touches only comment or docstring lines, and PASTE `python3 -c "from agent_workflows import run_recovery; print(run_recovery.DEFAULT_RETRY_LIMIT)"` showing `2`. Also paste `git diff docs/recovery.md` and confirm it adds no false claim and no em or en dash. Under answer (a): show `git diff agent_workflows/run_recovery.py docs/recovery.md` is EMPTY and quote the recorded reason no edit was needed. This item FAILS if an edit was invented under (a) or omitted under (b).
  - Observed evidence:
    1. Full `git diff agent_workflows/run_recovery.py`:
    ```diff
    diff --git a/agent_workflows/run_recovery.py b/agent_workflows/run_recovery.py
    index 449ca5b55..d36d3edf9 100644
    --- a/agent_workflows/run_recovery.py
    +++ b/agent_workflows/run_recovery.py
    @@ -1,5 +1,11 @@
     """Bounded retry/correction and resume/cancel/crash-recovery over the append-only run ledger.

    +This module serves the `aw run`/`aw runs` ledger execution path, with live consumers in
    +`run_cli._run_resume` and `run_cli._run_cancel`. Driver runs (`aw oc run` / `aw agy run`) do not emit a
    +ledger and use their own retry substrate in `runner_shared.py` (maintainer decision `xipfy1` OQ-03).
    +While `resume`, `cancel`, and `detect_unknown_outcomes` are reached in production by `run_cli`,
    +the helper functions `plan_retry` and `retry_budget_remaining` have zero production callers today.
    +
     awoptimize Order 07 (`7yqm1v`) E-01 (bounded retry + correction keyed by failure class) and
     E-02 (resume / cancel / crash recovery).

    @@ -50,11 +56,12 @@ from agent_workflows import run_ledger_schema as schema

     # Spec 25kzda 5.5: default is 2; "`N` must be an integer from 0 through 10 inclusive."
     # This was 3, which contradicted the approved spec. Aligned to 2 on the maintainer's decision
    -# (2026-08-31), taken while the value is still DORMANT: `plan_retry` / `retry_budget_remaining` have
    -# ZERO production callers today. Commit 19313eed deleted their only test coverage on 2026-09-24,
    -# which IPD e834yk restored in tests/test_run_recovery_cli.py. Doing it now is deliberate - once the
    -# runner wires this layer up, the same edit becomes a real behavior change that alters how many paid
    -# model turns every failed step buys.
    +# (2026-08-31). This module serves the `aw run`/`aw runs` ledger path, where `run_cli._run_resume`
    +# and `run_cli._run_cancel` are live consumers; driver runs use their own retry substrate in
    +# `runner_shared.py` by the `xipfy1` OQ-03 maintainer decision. Within this module, `plan_retry` and
    +# `retry_budget_remaining` have no production callers outside this file today, while `resume`, `cancel`,
    +# and `detect_unknown_outcomes` are called by `run_cli`. Commit 19313eed deleted their only test
    +# coverage on 2026-09-24, which IPD e834yk restored in tests/test_run_recovery_cli.py.
     #
     # WHY 2 IS THE RIGHT NUMBER, not merely the spec's: a retry here is a CORRECTION attempt, not a
     # network-flake retry, and `plan_retry`'s own contract is that "a retry cannot turn failure into
    ```

    2. Confirmation by inspection:
    - Strings "is still DORMANT" and "ZERO production callers today" are gone.
    - Both texts name the `aw run`/`aw runs` path and live `run_cli` consumers (`run_cli._run_resume` and `_run_cancel`).
    - "WHY 2 IS THE RIGHT NUMBER" paragraph and spec `25kzda` 5.5 citation are byte-identical.
    - Every hunk touches only comment or docstring lines.

    3. Constant check:
    ```
    $ python3 -c "from agent_workflows import run_recovery; print(run_recovery.DEFAULT_RETRY_LIMIT)"
    2
    ```

    4. Full `git diff docs/recovery.md`:
    ```diff
    diff --git a/docs/recovery.md b/docs/recovery.md
    index 0aae44eae..929ea63d8 100644
    --- a/docs/recovery.md
    +++ b/docs/recovery.md
    @@ -12,7 +12,7 @@ aw runs resume <run-id-or-path>

     `resume` reconstructs the run state and reports the steps it can resume. It refuses to resume a
     step whose side effect was interrupted (it will not silently re-apply a half-done mutation).
    -Under the hood, `run_recovery.resume` inspects the ledger to determine which steps are safe to resume and reports any interrupted steps that require reconciliation; it does not evaluate or spend a retry budget on this path (`plan_retry` has no production callers today).
    +Under the hood, `run_recovery.resume` inspects the ledger to determine which steps are safe to resume and reports any interrupted steps that require reconciliation; it does not evaluate or spend a retry budget on this path (`plan_retry` has no production callers today). Driver runs use their own retry substrate.

     ## Recover a corrupted ledger
    ```
    Confirmation: added one plain sentence with no false claims, and no em or en dash.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: PASTE the full source of the new test as committed, and confirm by inspection that it contains no `inspect`, no `ast`, no regex or substring search over production source, no caller or symbol count, and no assertion that comment text survives. PASTE the output of running that test alone (clearing the configured defaults with `-o addopts=""` if per-test counts are needed) showing it passes, and paste the bare `python3 -m pytest` summary line beside the pre-work baseline captured in this lane. PASTE the paths and `- Status:` lines of carriers `1g8lbe` and `hegwri`, showing both still resolve to live backlog items, and quote `1g8lbe`'s Summary to confirm it names the invalid role AND the invalid evidence kind. Under answer (b), PASTE the `aw backlog set` invocation and its output that amended `hegwri`, and quote the appended history line scoping it to the `aw run` path and stating it is NOT a driver obligation. Under answer (a), confirm `hegwri` was left unamended. Confirm no NEW backlog item was created by this item (`aw backlog new` was not called). This item FAILS if the test asserts on production source text, if the test asserts the directory is empty rather than that `ledger.jsonl` is absent, or if `hegwri` was amended under answer (a) or left unamended under (b).
  - Observed evidence:
    1. Full source of the new test as committed in `tests/test_run_recovery_cli.py`:
    ```python
    def test_run_engine_step_sequence_without_run_header_refuses_ledger_creation(
        self,
    ) -> None:
        """Driving a legal step sequence without an initial 'run' record refuses with RL-E041.

        Decision record utb2qr: driver runs do not write a ledger.jsonl, and no code
        in the package creates a ledger without a 'kind': 'run' root record.
        Constructing a RunLedgerStore over a fresh path and driving RunEngine's legal
        release_step -> start_step -> record_step_attempt sequence raises SchemaInvalidRecordError
        carrying finding RL-E041 and leaves no ledger.jsonl file on disk (only the lock file).
        """
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        ledger_path = Path(temp_dir.name) / ledger_store.LEDGER_FILENAME
        store = ledger_store.RunLedgerStore(ledger_path)
        wf = {
            "id": "wf",
            "steps": [
                {
                    "id": "S-01",
                    "action": "setup",
                    "depends_on": [],
                    "satisfies": ["R-01"],
                }
            ],
            "requirements": [{"id": "R-01"}],
        }
        engine = run_engine.RunEngine(wf, store, run_id="run-abcdef1234")
        step = engine.release_step("S-01")

        with self.assertRaises(ledger_store.SchemaInvalidRecordError) as ctx:
            engine.start_step(step.step_id)
            engine.record_step_attempt(
                step.step_id,
                attempt_seq=1,
                attempt_state="performed",
                summary="test attempt",
            )

        findings = getattr(ctx.exception, "findings", ())
        codes = {f.code for f in findings if hasattr(f, "code")}
        self.assertIn(
            "RL-E041",
            codes,
            f"Expected RL-E041 finding code in SchemaInvalidRecordError, got {findings}",
        )
        self.assertFalse(
            ledger_path.exists(),
            f"Expected {ledger_path} not to exist on disk after RL-E041 rejection",
        )
    ```

    Confirmation by inspection: contains no `inspect`, no `ast`, no regex or substring search over production source, no caller or symbol count, and no assertion that comment text survives.

    2. Output of running the new test alone:
    ```
    $ python3 -m pytest tests/test_run_recovery_cli.py -k "test_run_engine_step_sequence_without_run_header_refuses_ledger_creation" -o addopts="" -v
    tests/test_run_recovery_cli.py::TestLedgerResolutionAndWrongFormatVerdict::test_run_engine_step_sequence_without_run_header_refuses_ledger_creation PASSED [100%]
    1 passed, 51 deselected in 1.48s
    ```

    3. Test suite summary compared against baseline:
    - Pre-work baseline: `6787 passed, 2 skipped, 3 warnings in 626.38s (0:10:26)`
    - Post-work run: `6788 passed, 2 skipped, 3 warnings in 315.04s (0:05:15)`
    (Net change: exactly +1 test passed, 0 failures, 0 regressions).

    4. Carrier status and quotes:
    - Carrier `1g8lbe`:
      Path: `.aw/records/backlog/open/20261002-runledger-01-1g8lbe-capture-command-passes-invalid-actor-role-and-evid.backlog.md`
      Status: `- Status: open`
      Summary: `capture_command is called with actor='driver' and evidence_kind='tests', neither in the ledger schema's closed vocabulary, so both produced records fail validation`
      (Names invalid role 'driver' and invalid evidence kind 'tests').
    - Carrier `hegwri`:
      Path: `.aw/records/backlog/open/20261002-runledger-01-hegwri-no-writer-of-the-ledger-header-record-exists.backlog.md`
      Status: `- Status: open`
      `aw backlog set` invocation and output:
      ```
      $ aw backlog set hegwri --status open --message "Scoped to aw run execution path per rdjka2 maintainer decision (option b); not a driver obligation" --yes --no-commit
      aw backlog set: 20261002-runledger-01-hegwri-no-writer-of-the-ledger-header-record-exists.backlog.md -> open
      ```
      Appended history line:
      `- 2026-10-09 same-status (aw backlog): Scoped to aw run execution path per rdjka2 maintainer decision (option b); not a driver obligation`

    5. Carrier reconciliation confirmation:
    No NEW backlog item was created by this item (`aw backlog new` was not called).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is a DECISION plan, and one consequence must be explicit before it is approved: E-03 cannot be performed autonomously. The answer to OQ-01 sets scope and accepts risk on a public contract, so the executor must ASK and must record the maintainer's own wording. An executor that writes a resolution it was not given has forged an attestation, which is the failure mode `AGENTS.md` names directly; V-03 is written to catch it. If no maintainer is reachable, the honest outcome is E-01 and E-02 performed, OQ-01 left `- Status: open` with the declination recorded, E-04 through E-06 unperformed, and that reported as the result. The research record is a real deliverable on its own.

EXECUTION CONTRACT. Commit only files changed for this plan, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Verify the staged set with `git diff --cached --name-only` before every commit and unstage anything you did not modify with `git restore --staged <path>`: this is a shared checkout and uncommitted work you did not create is not yours. Run the suite BARE as `python3 -m pytest` and paste the actual summary line; never claim a pass you did not run. Both source edits are comment-only and V-04/V-05 prove it by diff, so a behavior change in either file means the item exceeded its scope and must be reverted rather than reconciled.

POST-GATE LIFECYCLE. This plan moves to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries concrete pasted evidence. Backlog item `ye28s6` is set to `graduated` by the authoring turn, NOT `done`: the design is handed off here, and under answer (a) the code that closes the item lives in carrier `hegwri`, which was filed at authoring and is reconciled (not created) by E-06.

# IPD: Clear the two stale escalations by amending the review records only, and refuse the readiness write on a terminal plan

- Date: 2026-09-29
- Kind: child
- Concern: Backlog `iifcam` records two terminal plans still carrying a BLOCKER finding whose escalated question is answered, and asks the maintainer to choose between amending them for tidiness and leaving the retired record as history. THE QUESTION AS POSED HAS A FALSE PREMISE, AND THE MEASUREMENT IS WHAT REMOVES IT: the two stale findings are NOT cosmetic, they have a live consequence on a plan that does not exist yet, so "leave it as history" is not a no-op option.
  MEASURED AT HEAD `08133a35`, re-deriving the item's own claim over the whole plans tree. `review_findings.stale_escalated_findings` reports exactly two plans, and they are the two the item names: `ki6tom` PR-201 (`blocker`/`open`) in `not-executed/`, whose OQ-02 is `- Status: resolved`, and `yku4ga` PR-701 (`blocker`/`open`) in `superseded/`, whose OQ-02 is likewise `- Status: resolved`. `review_findings.subject_gating_blocks` still returns one block for each, so the gate that reads the findings column is still firing on an answered question.
  THE LIVE CONSEQUENCE IS A DEPENDENT PLAN, AND IT IS REPRODUCED RATHER THAN ASSERTED. `check_engine.evaluate_ipd_dependencies` feeds every `executed:` edge to `_findings_blocks_for`, which delegates to that same `subject_gating_blocks`, and emits `check.ipd-dependency-findings-blocked`. Reproduced in a throwaway tree holding only these two plans, their two review records, and one scaffolded pending plan whose statement reads `- Item-Dependencies: executed:ki6tom`: `aw check` reported `check.ipd-dependency-findings-blocked` against the DEPENDENT, located at the dependent's own path, and the finding disappeared once the review record carried the closing round. So a stale finding on a retired plan is a trap laid for the next plan that cites it, and the retired plan's own disposition does not disarm it. The same predicate is consumed by both host runners through `runner_shared._findings_block_reason`, so the reach is the queue as well as the checker.
  THE TOOLED ROUTE THE ITEM WOULD REACH FOR IS OVER-BROAD, WHICH IS THE SECOND DEFECT AND THE REASON THIS IS NOT A TWO-FILE EDIT. `aw ipd recheck-readiness --stale-findings --apply` is the shipped verb for exactly this return path, and its `--stale-findings` half does the right thing: `review_findings.append_round_resolving_stale` APPENDS a new `## Round <n>` and never rewrites an earlier row. But the verb runs the readiness recompute UNCONDITIONALLY beside it (`readiness_recheck.run_recheck_readiness` calls `PR.recheck_readiness` for every row, gated only on `--apply`), and `plan_readiness.recheck_conditions` refuses on readiness VALUE and never on DISPOSITION. Measured on the retired `ki6tom` in a throwaway git repo: the verb rewrote `- Readiness: no-go` to `- Readiness: go-pending-approval` IN the `not-executed/` plan and prepended a re-check record to its history, which edits the record of a plan that will never run, exactly what the item declined to do by hand and what AGENTS.md forbids.
  THE ADJACENT GUARD HOLDS AND IS WORTH STATING SO THIS IS NOT OVERSOLD. After that write, `aw ipd set approved ki6tom` still REFUSED, naming the terminal-disposition reopen guard and writing nothing, so the readiness flip does not by itself resurrect a retired plan. What it does do is falsify the plan's own attestation: `plan_readiness.is_plan_review_approved` went from False to True for both retired plans, and `approval_refusals` went from two refusals each to none, so the safety now rests entirely on the disposition guard with the readiness signal underneath it saying the opposite of the truth.
  THE MODULE ALREADY KNOWS THE RULE AND STATES IT, WHICH IS WHY THIS IS A DEFECT RATHER THAN A DESIGN CHOICE. `readiness_recheck.SWEEP_DISPOSITIONS` is `("pending", "reusable")` and its comment says a terminal plan is "deliberately NOT swept" because "re-checking a plan whose disposition is already settled would rewrite history to no purpose", then adds that "a named selector still reaches one, so the sweep is a default rather than a restriction". The sweep default encodes the policy; the write path does not enforce it. A named selector is precisely how this repository reaches these two plans, so the one route that must hold the rule is the one that does not.
- Scope: Clear both stale escalations by the sanctioned append-only route, and close the write-path hole that made clearing them by tool unsafe. IN: a disposition refusal in the readiness recompute so a TERMINAL plan's `- Readiness:` and history are never rewritten while the stale-finding amendment still runs; the two closing rounds appended to the two review records; behavioral tests pinning both the refusal and the still-permitted amendment; the two `aw ipd recheck-readiness` doc lines in the plan-review contract stating the refusal. OUT: changing `append_round_resolving_stale` or the join predicate `stale_escalated_findings` (both are correct and measured correct here); editing either retired plan's body, items, findings, or status; relaxing or re-litigating the terminal-reopen guard in `status_set`; the one PENDING `no-go` plan (`5j7jv1`), which is a live plan the verb should keep reaching; adding an override flag to force the terminal write.
- Scope-Paths: agent_workflows/plan_readiness.py, agent_workflows/readiness_recheck.py, tests/test_review_record_classifier.py, .aw/records/reviews/20260904-runbypass-01-ki6tom-remove-the-spec-prohibited-bypass-flags-from-both-host-runne.review.md, .aw/records/reviews/20260908-setidhard-00-yku4ga-make-a-setid-a-hard-cross-type-unique-identity-and-replace-s.review.md, .aw/system/workflows/plan-review/plan-review.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: iifcam
- Set: iifcam
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: khiueh

## Workflow history

- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored to graduate backlog `iifcam`, which asked the maintainer to choose between amending two terminal plans' stale escalations and leaving them as history. THE REPOSITORY ANSWERS THE QUESTION AND THE ANSWER IS NEITHER OPTION AS POSED: amend the REVIEW RECORDS (not the plans), because the stale findings have a measured live consequence, and fix the write path that made the tooled route unsafe. Measured at HEAD `08133a35`. (1) The item's census re-derives exactly: `stale_escalated_findings` over all plans returns precisely `ki6tom` PR-201 and `yku4ga` PR-701, and `subject_gating_blocks` still blocks on each. (2) The consequence is not cosmetic: in a throwaway tree, a pending plan declaring `- Item-Dependencies: executed:ki6tom` drew `check.ipd-dependency-findings-blocked`, and the finding cleared once the closing round was appended, so the stale finding is a trap for the next dependent rather than dead history. (3) The tooled route is over-broad: `aw ipd recheck-readiness --stale-findings --apply` on the retired `ki6tom` rewrote its `- Readiness:` to `go-pending-approval` and prepended a re-check record, because `recheck_conditions` refuses on readiness VALUE and never on DISPOSITION, while the module's own `SWEEP_DISPOSITIONS` comment already states the terminal rule. (4) The `aw ipd set approved` terminal-reopen guard still refused afterwards, so this is an attestation-falsification defect and not a resurrection one; stated that way deliberately rather than overstated. The amendment half is already append-only and was verified to leave both plan files byte-identical, which is why the fix is a refusal on one half and not a redesign.

## Goal

Close both stale escalations through the append-only review-record route so the gate stops firing on answered questions, and make `aw ipd recheck-readiness` refuse the readiness write on a plan in a terminal disposition, so the route this repository used to clear them cannot also falsify a retired plan's review attestation.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: close the write-path hole first

- [ ] E-01 REFUSE THE READINESS RECOMPUTE ON A PLAN IN A TERMINAL DISPOSITION, in `plan_readiness.recheck_conditions`, as a REFUSAL beside the existing readiness-field refusals rather than as a fourth condition. The distinction is the one that function's own comment already draws: a refusal is "a reason the re-check may not act at all, as distinct from reasons the plan is not ready", and disposition is exactly that. Derive the disposition from the plan's PATH, never from its `- Status:` text, and reuse `plans.TERMINAL` as the vocabulary so the terminal set is not spelled a second time.
  DERIVE IT THE WAY THE REPOSITORY ALREADY DOES, WHICH IS THE FIRST PATH COMPONENT UNDER THE PLANS DIR AND NOT `parent.name`. Three shipped sites establish this and each documents why: `check_engine._plan_disposition`, `attention._plan_disposition_from_rel`, and `plans_index.scan_plans` (whose `rel.split("/", 1)[0]` the other two cite as the derivation they reuse). The reason is load-bearing here: `aw archive plans` shards a terminal plan into `<disposition>/YYYYMM/` (`plans_archive._shard_target`), so a parent-directory test silently stops recognizing every sharded plan, and both plans this Set must protect are archive candidates. PREFER CALLING AN EXISTING HELPER over writing a fourth copy; if none is importable from this module without a cycle, say so in the plan's Findings and keep the new derivation to the same one-line rule, citing the sites it matches.
  WATCH THE IMPORT DIRECTION. `plan_readiness` currently imports `ipd_schema`, `attention`, and `attention_contract` at module scope; `plans` imports only `record_producers` and neither `plans` nor `record_producers` imports `plan_readiness`, so a `plans` import introduces no cycle (verified at authoring by importing both modules together). `check_engine` is NOT a safe module-scope import here and must not become one.
  A PLAN OUTSIDE ANY PLANS DIRECTORY MUST NOT BE REFUSED. `_resolve` accepts a direct path specifically so a caller can re-check "a fixture, or a plan outside the records tree", and those tests are how this behavior is pinned; a refusal that fired on an unlocatable path would break the verb's own test surface. Absent disposition means NOT terminal.
  - Depends on: none
  - Expected outcome: `recheck_conditions` on a plan under `executed/`, `superseded/`, or `not-executed/` returns `may_write` False with a refusal naming the disposition and stating that a terminal plan's record is history; the same call on a `pending/` plan and on a plan at an arbitrary path outside the plans tree is UNCHANGED. Paste the before/after refusal lists for one terminal and one pending plan.
  - Execution state: pending

- [ ] E-02 KEEP THE STALE-FINDING AMENDMENT REACHABLE ON A TERMINAL PLAN, so E-01 narrows the write to the plan file and does not disable the return path the two target records need. In `readiness_recheck.run_recheck_readiness` the two halves already run in a fixed order for a documented reason ("THE STALE-FINDING HALF RUNS FIRST, deliberately. It can CHANGE the second condition's answer"), and that order is what makes this separable: the amendment half writes only to the REVIEW record, and `append_round_resolving_stale` takes `review_path`, never the plan path.
  THE REPORTING MUST SAY WHICH HALF ACTED, because after E-01 a terminal plan's row is simultaneously a refusal and an amendment, and a row that renders one while doing the other is the false report this area exists to avoid. The row already carries both (`_Row` is documented as "carrying BOTH halves so a report can never state an action without a cause"); make the refusal reason and the `stale findings:` detail both visible in the human output AND in the `--agent`/`--json` rendering, where a refusal currently emits a `Diagnostic` and a write emits a `Change`.
  DO NOT ADD AN OVERRIDE FLAG. There is no `--allow-terminal` here: the amendment is the sanctioned act and the plan write is not, so a flag would only re-open the hole E-01 closes.
  - Depends on: E-01
  - Expected outcome: `aw ipd recheck-readiness --stale-findings --apply <terminal-plan>` appends the closing round to the REVIEW record, leaves the plan file BYTE-IDENTICAL (assert the hash), and reports the readiness refusal and the amendment in the same row; the same command on a pending plan behaves exactly as it does today.
  - Execution state: pending

### Task group 2: pin both behaviors

- [ ] E-03 PIN E-01 AND E-02 WITH BEHAVIORAL TESTS, in `tests/test_review_record_classifier.py`, which is the surviving home for `plan_readiness` coverage after the suite trim deleted `tests/test_plan_readiness_recheck.py` (commit `19313eed`, "test: trim test suite from 9,136 to under 2,000 tests"). Build each case on a temporary tree, driving `recheck_conditions` / `run_recheck_readiness` or the CLI, and assert on returned refusals, written file bytes, and exit codes.
  REQUIRED CASES, each falsifiable: (1) a `no-go` plan under each of the three terminal dispositions is REFUSED, with the disposition named in the reason; (2) a `no-go` plan under `pending/` is still UPDATED, which is the regression that proves the fix did not disable the verb; (3) a terminal plan carrying a stale escalation has its REVIEW record amended while its own bytes are unchanged; (4) a terminal plan SHARDED into `<disposition>/YYYYMM/` is still recognized as terminal, which is the case a `parent.name` derivation would miss and therefore the one that pins the derivation choice; (5) a plan at a path under no plans directory is NOT refused for disposition.
  ASSERT ON OUTCOMES, NEVER ON CODE SHAPE. Per the repository testing contract, no test here may read module source with `inspect`, `ast`, or a regex, and none may assert a symbol census or a line count. Case (4) in particular must be a real sharded PATH exercised through the real call, not an assertion about which helper was called.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest tests/test_review_record_classifier.py` passes with the new cases present, and cases (1) and (4) FAIL against base; paste both failures and then the green run.
  - Execution state: pending

### Task group 3: clear the two records and say so in the contract

- [ ] E-04 APPEND THE CLOSING ROUND TO BOTH REVIEW RECORDS using the now-safe tool, and change NOTHING in either plan. Run the verb per plan with `--stale-findings --apply` against `ki6tom` and `yku4ga`; the amendment is `append_round_resolving_stale`, which carries forward every still-unresolved finding UNCHANGED and marks only the matched row `fixed`, so no other finding in either record is silently cleared.
  VERIFY BY THE GATE, NOT BY READING THE ROUND. The deliverable is that `subject_gating_blocks` returns empty for both id6s and that `stale_escalated_findings` over the whole plans tree returns zero rows; a correctly rendered round that left the gate firing would not satisfy this item.
  CONFIRM BOTH PLAN FILES ARE UNTOUCHED IN THE COMMIT. `git diff --cached --name-only` must list the two `.review.md` paths and NEITHER `.ipd.md` path. This is the item's whole point: the backlog item declined to amend because amending the plan was the only route it had.
  - Depends on: E-03
  - Expected outcome: both review records carry one new appended `## Round <n>` marking PR-201 / PR-701 `fixed` with the answered question cited; `stale_escalated_findings` over all plans returns zero; `subject_gating_blocks` returns empty for `ki6tom` and `yku4ga`; both `.ipd.md` files byte-identical to HEAD.
  - Execution state: pending

- [ ] E-05 STATE THE REFUSAL IN THE PLAN-REVIEW CONTRACT, beside the two `aw ipd recheck-readiness` command lines under "A `NO-GO` is RE-EVALUABLE", which currently list three bounding properties of the verb and do not mention disposition. Add the fourth: a plan in a terminal disposition is refused, because a terminal plan's `no-go` is an accurate record of why it was retired. Also note, in the "The escalation RETURN PATH" subsection immediately below, that the amendment half still applies to a terminal plan, since that is the case these two records are.
  KEEP IT TO THE SMALLEST WORDING THAT CLOSES THE GAP, and do not restate the sweep default: `SWEEP_DISPOSITIONS` already documents that terminal plans are not swept, and duplicating it in the contract creates two statements that can drift (GUIDING_PRINCIPLES P8).
  - Depends on: E-04
  - Expected outcome: the contract's re-evaluability section names the terminal-disposition refusal and the still-permitted amendment; a reader following the document alone does not expect a terminal plan's readiness to be rewritable.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A plan's DISPOSITION is derived from the FIRST path component under the plans directory, never from `parent.name`, because `aw archive plans` shards a terminal plan into `<disposition>/YYYYMM/`. Three sites already do this and cross-cite each other: `check_engine._plan_disposition`, `attention._plan_disposition_from_rel`, `plans_index.scan_plans`.
- Directories carry DISPOSITION and the front-matter `- Status:` carries READINESS (`plans` module docstring). The two are checked against each other by `attention.disposition-mismatch`, so neither is a substitute for the other.
- A review record is HISTORY: a stale finding is cleared by APPENDING a `## Round <n>`, never by editing an earlier row, because "round 1 was true when it was written" (`append_round_resolving_stale`, and the same rule in the plan-review contract's escalation-return-path section).
- A `- Readiness:` value is an ATTESTATION FIELD, so the shipped verb writes only `no-go` -> `go-pending-approval` and `go` is unreachable "by construction rather than by discipline" (`recheck_readiness`). Any change here must not widen that.
- `plan_readiness` is imported by both host runners and by the checker, so a refusal added there reaches every consumer at once; that is the reason to put it there rather than in the CLI surface.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Severity | Finding |
|----|----------|---------|
| F-1 | HIGH | The two stale findings have a LIVE consequence, so the backlog item's "leave it as history" option is not a no-op. `check_engine.evaluate_ipd_dependencies` routes every `executed:` edge through `_findings_blocks_for` to `subject_gating_blocks` and emits `check.ipd-dependency-findings-blocked`. Reproduced: a pending plan declaring `- Item-Dependencies: executed:ki6tom` drew that finding, and it cleared once the closing round was appended. `runner_shared._findings_block_reason` consumes the same predicate, so both host runners see it too. |
| F-2 | HIGH | `aw ipd recheck-readiness --stale-findings --apply` on a TERMINAL plan rewrites that plan. Measured on `ki6tom` in `not-executed/`: `- Readiness: no-go` became `go-pending-approval` and a re-check record was prepended to its history. Cause: `recheck_conditions` refuses on readiness VALUE (absent, out-of-vocab, not-`no-go`) and never on DISPOSITION, and `run_recheck_readiness` calls it for every resolved row. |
| F-3 | MEDIUM | The module already STATES the rule it does not enforce. `readiness_recheck.SWEEP_DISPOSITIONS` is `("pending", "reusable")`, its comment says re-checking a settled plan "would rewrite history to no purpose", and it adds that "a named selector still reaches one". So the policy is documented in the default and absent from the write path, and a named selector is exactly how these two plans are reached. |
| F-4 | MEDIUM | The consequence of F-2 is attestation falsification, NOT resurrection, and the difference bounds this plan. After the write, `aw ipd set approved ki6tom` still refused on the terminal-reopen guard and wrote nothing. But `is_plan_review_approved` flipped False -> True for both retired plans and `approval_refusals` went from two refusals each to zero, so safety now rests wholly on the disposition guard while the readiness signal beneath it asserts the opposite. |
| F-5 | LOW | The amendment half is already correct and append-only, which is why the fix is a refusal on one half rather than a redesign. Verified by running `append_round_resolving_stale` against both records in a throwaway tree: both `.ipd.md` files stayed byte-identical (sha256 compared), the closing round was appended, and `subject_gating_blocks` went to empty for both id6s. |
| F-6 | LOW | The one PENDING `no-go` plan in the tree (`5j7jv1`) must keep being reachable; it is a live plan and the verb exists for it. The terminal `no-go` population is 7 (1 `not-executed/`, 6 `superseded/`), of which the 2 named here are the only ones carrying a stale escalation. So E-01 refuses 7 plans it should refuse and none it should not. |
| F-7 | LOW | The dedicated test module for this code, `tests/test_plan_readiness_recheck.py`, was DELETED by the suite trim at `19313eed`, so there is currently no test that would have caught F-2 and no obvious home for new cases. E-03 places them in `tests/test_review_record_classifier.py`, the surviving `plan_readiness` test module. |

## Proposed changes (ordered, validatable)

1. A disposition REFUSAL in `recheck_conditions`, derived from the plan's path by the repository's established first-component rule, using `plans.TERMINAL` (E-01).
2. The stale-finding amendment kept reachable on a terminal plan, with the CLI row reporting the refusal and the amendment together on both the human and machine surfaces (E-02).
3. Behavioral tests for the refusal, the preserved pending behavior, the untouched plan bytes, the sharded-path case, and the out-of-tree case (E-03).
4. The two closing rounds appended to the two review records, verified by the GATE rather than by reading the rounds, with both plan files provably untouched (E-04).
5. The plan-review contract stating the terminal refusal and the still-permitted amendment (E-05).

## Deferred / out of scope (with reason)

- The other five terminal `no-go` plans are NOT amended. They carry no stale escalation (measured: `stale_escalated_findings` returns rows for exactly two plans), so their `no-go` is an accurate record of why they were retired and there is nothing to clear.
  - Carrier-Declined: Nothing is owed. This row records a MEASUREMENT that there is no work here, not a deferred defect: the join predicate returns zero rows for all five, so there is no stale finding to clear and amending them would append a round closing nothing. If a future escalation on one of them is ever answered, the shipped verb reports it, which is the standing detector and needs no item filed now.
- No override flag (`--allow-terminal` or similar) is added. The amendment is the sanctioned act and the plan write is not, so a flag would re-open the hole E-01 closes; a maintainer who genuinely needs to edit a retired plan is already directed to a corrective IPD.
  - Carrier-Declined: This row records a PROHIBITION this plan adopts, not an unbuilt piece, so nothing is owed. Adding the flag is the defect E-01 exists to close, and the sanctioned route for editing a retired plan already exists (a corrective IPD, per AGENTS.md). Filing an item would represent a deliberately rejected design as outstanding work.
- The terminal-reopen guard reached by `aw ipd set` is untouched. It held in the measurement (F-4) and is a different gate with its own recorded override; re-litigating it here would widen this plan into lifecycle-setter territory.
  - Carrier-Declined: No future work is owed, because the guard is not defective: it REFUSED correctly in the measurement, writing nothing. This row exists to record the boundary of the defect (attestation falsification, not resurrection) so a reviewer does not read the silence as a claim that the setter is also broken.
- Backlog `rrvrwv` (the `aw ipd set` backwards terminal transition defect) is a separate live item with its own release gate and is not folded in: it concerns the STATUS setter, while this plan concerns the READINESS recompute, and combining them would put two gates in one plan.
  - Carrier: rrvrwv
- The item's framing question ("amend for tidiness, or leave as history") is answered rather than escalated, because the repository settled it: the measured live consequence in F-1 removes the "leave it" option, and the append-only route removes the objection to amending. No maintainer decision is required for that; the one judgement left is whether to fix the write path in the same pass, which this plan takes because clearing the records by tool is what exposed it.
  - Carrier-Declined: Nothing is owed: this records that a question was ANSWERED from repository evidence rather than deferred. The answer is carried by this plan's own E-04 (amend the records) and E-01 (fix the route), so there is no residue to hand to another artifact. Recorded here so a reviewer can dispute the answer on its evidence rather than discovering the item's question was silently dropped.

## Scope check

- Over-scope: none. The write-path fix is not opportunistic widening: it is the precondition for clearing the two records by tool, because the tooled route measurably rewrites a retired plan (F-2), and the backlog item's own recorded reason for not amending was that its only route would edit a terminal plan.
- Under-scope: this plan does not audit whether any OTHER verb writes to a terminal plan; it closes the one route measured to do so. It does not add a general "terminal artifacts are read-only" invariant across record types, which would be a contract change rather than a defect fix. It does not retroactively repair the `ki6tom` / `yku4ga` `- Readiness:` values, which are untouched at `no-go` and correct as history.

## Required tests / validation

`python3 -m pytest tests/test_review_record_classifier.py` for the new cases, then the bare suite `python3 -m pytest` (already quiet, parallel, and fast-scoped by the configured `addopts`; do not add flags). Beyond the suite, the deliverable is verified by the GATE and by file bytes: `stale_escalated_findings` over the whole plans tree must return zero rows, `subject_gating_blocks` must be empty for both id6s, and both `.ipd.md` files must hash identically to HEAD. `aw check` must report no new findings, and the `check.ipd-dependency-findings-blocked` reproduction must no longer fire.

## Spec / documentation sync

`.aw/system/workflows/plan-review/plan-review.md` is amended by E-05 and is declared in `Scope-Paths`, so the runners announce the edit before the run. WHY: that document is where the verb's bounding properties are stated for a human reader, and a reader who follows it today would expect a terminal plan's readiness to be re-evaluable, which after E-01 it is not.

No `.spec.md` is amended. Checked at authoring: the `recheck-readiness` verb is mentioned in the specs tree only as an EXAMPLE of an event producer (`4sd62s`, artifact-metadata-store, which says it "likewise appends a `review` event"), and no spec states a disposition contract for the readiness field, so there is no spec-level claim that this plan contradicts. If execution finds one, declare it and amend it in the same change rather than shipping a divergence.

## Open questions

### OQ-01: Should the refusal also cover the `reusable` disposition?

- Blocking: no
- Status: open
- Owner: executor
- Carrier-Declined: Nothing is owed beyond this plan. The question is answered WITHIN it: E-01 refuses `plans.TERMINAL` only, leaving `reusable/` reachable, and V-01's evidence demand covers the boundary. Measured at authoring: zero `reusable/` plans carry `- Readiness: no-go`, so there is no population for a follow-up item to act on, and filing one would assert outstanding work where the measurement shows none.
- Resolution or deferral rationale: NOT blocking, and the default is deliberate: this plan refuses only `plans.TERMINAL` and leaves `reusable/` reachable, because `SWEEP_DISPOSITIONS` already SWEEPS `reusable` and a standing plan is by definition still runnable, so refusing it would break the verb for a live population. Recorded because the question is adjacent and a reviewer should see it was considered rather than missed. Measured: zero `reusable/` plans carry `- Readiness: no-go` at authoring, so the choice is currently unobservable either way; the executor should re-measure and, if that is still true, keep `reusable` reachable and say so in the item's evidence rather than adding an untested branch.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted return of `recheck_conditions` for FOUR inputs: one plan under `not-executed/`, one under `superseded/`, one under `pending/`, and one at a path under no plans directory. The two terminal ones must show `may_write` False with a refusal whose text names the disposition; the pending one must show the SAME refusals/conditions it shows at base (paste the base run too, so "unchanged" is demonstrated rather than claimed); the out-of-tree one must show no disposition refusal. A paste showing only the terminal refusals does not satisfy this item, because the regression risk is the verb silently refusing everything.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for one terminal plan carrying a stale escalation, the `sha256` of the `.ipd.md` BEFORE and AFTER `aw ipd recheck-readiness --stale-findings --apply`, shown equal, alongside the `git diff --stat` proving the `.review.md` changed and the `.ipd.md` did not. Plus the command's own output showing the readiness refusal AND the `stale findings: appended a round ...` detail in the same row, and the `--agent` rendering of the same invocation showing both the diagnostic and the change. Equal hashes with no amendment shown does NOT satisfy this: it would be indistinguishable from the verb doing nothing at all.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `python3 -m pytest tests/test_review_record_classifier.py` output pasted green with the new case count visible, PLUS the pasted FAILURE of cases (1) and (4) against base (revert the predicate, run, paste, restore). The sharded case (4) must be shown failing against a `parent.name`-style derivation specifically, since that is the defect it exists to pin; a green run alone does not demonstrate it discriminates. Also paste the bare `python3 -m pytest` summary line with its `N passed` count.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the pasted output of `stale_escalated_findings` over every plan in the tree showing ZERO rows (the same sweep that returned two at authoring), the pasted `subject_gating_blocks` result showing empty for BOTH `ki6tom` and `yku4ga`, `git diff --cached --name-only` listing the two `.review.md` paths and NEITHER `.ipd.md`, and the re-run of the F-1 reproduction showing `check.ipd-dependency-findings-blocked` no longer fires for a dependent declaring `executed:ki6tom`. A rendered round pasted without the gate results does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the amended passage quoted from `.aw/system/workflows/plan-review/plan-review.md`, showing the terminal-disposition refusal stated in the re-evaluability section and the still-permitted amendment stated in the escalation-return-path section, plus a statement that the sweep default was NOT restated there (P8). Quote enough surrounding text to show the placement, not just the inserted sentence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. It has no plan dependencies (`- Item-Dependencies: none`).

EXECUTION ORDER IS LOAD-BEARING AND NOT MERELY PREFERRED: E-01 and E-02 must land BEFORE E-04, because E-04's whole method is to clear the two records with the tool, and running that tool at base is what rewrites a retired plan (F-2). An executor who reverses the order will have committed the exact edit the backlog item declined to make.

The two `.review.md` files are the only records this plan may modify; both `.ipd.md` files are HISTORY and must be byte-identical when the plan finalizes. Per the execution contract, commit only the paths named in `- Scope-Paths:` through `aw commit`, verify the staged set before committing, and do not push.

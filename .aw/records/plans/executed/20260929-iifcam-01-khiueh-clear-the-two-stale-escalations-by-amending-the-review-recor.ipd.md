# IPD: Clear the two stale escalations by amending the review records only, and refuse the readiness write on a terminal plan

- Date: 2026-09-29
- Kind: child
- Concern: Backlog `iifcam` records two terminal plans still carrying a BLOCKER finding whose escalated question is answered, and asks the maintainer to choose between amending them for tidiness and leaving the retired record as history. THE QUESTION AS POSED HAS A FALSE PREMISE, AND THE MEASUREMENT IS WHAT REMOVES IT: the two stale findings are NOT cosmetic, they have a live consequence on a plan that does not exist yet, so "leave it as history" is not a no-op option.
  MEASURED AT HEAD `08133a35`, re-deriving the item's own claim over the whole plans tree. `review_findings.stale_escalated_findings` reports exactly two plans, and they are the two the item names: `ki6tom` PR-201 (`blocker`/`open`) in `not-executed/`, whose OQ-02 is `- Status: resolved`, and `yku4ga` PR-701 (`blocker`/`open`) in `superseded/`, whose OQ-02 is likewise `- Status: resolved`. `review_findings.subject_gating_blocks` still returns one block for each, so the gate that reads the findings column is still firing on an answered question.
  THE LIVE CONSEQUENCE IS A DEPENDENT PLAN, AND IT IS REPRODUCED RATHER THAN ASSERTED. `check_engine.evaluate_ipd_dependencies` feeds every `executed:` edge to `_findings_blocks_for`, which delegates to that same `subject_gating_blocks`, and emits `check.ipd-dependency-findings-blocked`. Reproduced in a throwaway tree holding only these two plans, their two review records, and one scaffolded pending plan whose statement reads `- Item-Dependencies: executed:ki6tom`: `aw check` reported `check.ipd-dependency-findings-blocked` against the DEPENDENT, located at the dependent's own path, and the finding disappeared once the review record carried the closing round. So a stale finding on a retired plan is a trap laid for the next plan that cites it, and the retired plan's own disposition does not disarm it. The same predicate is consumed by both host runners through `runner_shared._findings_block_reason`, so the reach is the queue as well as the checker.
  THE TOOLED ROUTE THE ITEM WOULD REACH FOR IS OVER-BROAD, WHICH IS THE SECOND DEFECT AND THE REASON THIS IS NOT A TWO-FILE EDIT. `aw ipd recheck-readiness --stale-findings --apply` is the shipped verb for exactly this return path, and its `--stale-findings` half does the right thing: `review_findings.append_round_resolving_stale` APPENDS a new `## Round <n>` and never rewrites an earlier row. But the verb runs the readiness recompute UNCONDITIONALLY beside it (`readiness_recheck.run_recheck_readiness` calls `PR.recheck_readiness` for every row, gated only on `--apply`), and `plan_readiness.recheck_conditions` refuses on readiness VALUE and never on DISPOSITION. Measured on the retired `ki6tom` in a throwaway git repo: the verb rewrote `- Readiness: no-go` to `- Readiness: go-pending-approval` IN the `not-executed/` plan and prepended a re-check record to its history, which edits the record of a plan that will never run, exactly what the item declined to do by hand and what AGENTS.md forbids.
  THE ADJACENT GUARD HOLDS AND IS WORTH STATING SO THIS IS NOT OVERSOLD. After that write, `aw ipd set approved ki6tom` still REFUSED, naming the terminal-disposition reopen guard and writing nothing, so the readiness flip does not by itself resurrect a retired plan. What it does do is falsify the plan's own attestation: `plan_readiness.is_plan_review_approved` went from False to True for both retired plans, and `approval_refusals` went from two refusals each to none, so the safety now rests entirely on the disposition guard with the readiness signal underneath it saying the opposite of the truth.
  THE MODULE ALREADY KNOWS THE RULE AND STATES IT, WHICH IS WHY THIS IS A DEFECT RATHER THAN A DESIGN CHOICE. `readiness_recheck.SWEEP_DISPOSITIONS` is `("pending", "reusable")` and its comment says a terminal plan is "deliberately NOT swept" because "re-checking a plan whose disposition is already settled would rewrite history to no purpose", then adds that "a named selector still reaches one, so the sweep is a default rather than a restriction". The sweep default encodes the policy; the write path does not enforce it. A named selector is precisely how this repository reaches these two plans, so the one route that must hold the rule is the one that does not.
- Scope: Clear both stale escalations by the sanctioned append-only route, and close the write-path hole that made clearing them by tool unsafe. IN: a disposition refusal in the readiness recompute so a TERMINAL plan's `- Readiness:` and history are never rewritten while the stale-finding amendment still runs; the machine-surface repair that makes the resulting mixed row report the amendment it performed (review F-8, measured broken at base); the two closing rounds appended to the two review records; behavioral tests pinning the refusal, the still-permitted amendment, and the resolved-records-root derivation the refusal depends on; the two `aw ipd recheck-readiness` doc lines in the plan-review contract stating the refusal. OUT: changing `append_round_resolving_stale` or the join predicate `stale_escalated_findings` (both are correct and measured correct here); editing either retired plan's body, items, findings, or status; relaxing or re-litigating the terminal-reopen guard in `status_set`; the PENDING `no-go` population, which are live plans the verb should keep reaching (the authored text named `5j7jv1`, which review re-measured as `go-pending-approval`, so the set is re-derived at execution rather than named here); the `reusable/` disposition, which stays reachable (OQ-01, resolved); adding an override flag to force the terminal write; adding `--verbose` to the verb.
- Scope-Paths: agent_workflows/plan_readiness.py, agent_workflows/readiness_recheck.py, tests/test_review_record_classifier.py, .aw/records/reviews/20260904-runbypass-01-ki6tom-remove-the-spec-prohibited-bypass-flags-from-both-host-runne.review.md, .aw/records/reviews/20260908-setidhard-00-yku4ga-make-a-setid-a-hard-cross-type-unique-identity-and-replace-s.review.md, .aw/system/workflows/plan-review/plan-review.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: iifcam
- Set: iifcam
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: khiueh

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: khiueh verified (set iifcam, attempt 1). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261001-w38q54-01-w38q54-check-engine-formats-recovery-commands-with-absolu.backlog.md: changed by the plan's approved execution (auto-reconciled by aw agy run)]
- 2026-09-30 approved (aw set): status set to approved

- 2026-09-30 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 all FIXED, zero deferred, zero open. THE PLAN'S CENTRAL ARGUMENT IS CORRECT AND I RE-DERIVED ALL FOUR OF ITS HEADLINE MEASUREMENTS INDEPENDENTLY at HEAD `d8fd3f2f`: `stale_escalated_findings` over every plan returns exactly `ki6tom` PR-201 and `yku4ga` PR-701; a constructed dependent declaring `executed:ki6tom` draws `check.ipd-dependency-findings-blocked` at its own path; the base verb rewrote retired `ki6tom`'s `- Readiness: no-go` to `go-pending-approval` and prepended a re-check record (sha256 `4c72f7f9...` -> `a0fba0b1...`); and the amendment half alone appended Round 3 / Round 2, cleared both gates, and left both `.ipd.md` files byte-identical. The plan's BOUND on its claim also holds: `aw ipd set approved` still refused and wrote nothing, though it took three refusals to reach the terminal-reopen guard (gating finding, then missing Priority/Work-Kind, then the guard), which the plan now records. TWO FINDINGS WOULD HAVE CHANGED WHAT SHIPPED. PR-001 (HIGH): E-01 ruled out `check_engine` on a FALSE cycle claim (measured: a module-scope import raises no ImportError in either order, cold cost 0.203s vs 0.193s), leaving `attention._plan_disposition_from_rel` as the only named candidate; the two helpers agree on the split and DISAGREE ON THE ROOT, and in a `records_backend: companion` scratch repo the `check_engine` helper returned `not-executed`/`superseded`/`pending` while the attention-style one returned `''` for all three, so the plan steered the executor into a refusal that never fires for any companion-backed repository. E-01 now names `check_engine._plan_disposition` via a function-local import and E-03 gains case (6) to discriminate them. PR-002 (HIGH): the mixed case is ALREADY broken at base, not merely under-reported: with the readiness half refusing and the amendment half writing, the `.review.md` was modified while `--json` reported `changes: []` and `--agent` reported no `changes` key at all, because the `Change` list is derived from `r.action != "refused"`; E-02 now names the specific repair, and V-02's authored demand for a `detail` in the `--agent` record was unsatisfiable (`to_agent_record` drops it without `--verbose`, which this verb does not register) and now routes through `--json`. PR-003: the amendment empties the appended round's Decisions view, so `check.review-decision-unescalated` stops seeing both targets' `Reversible: no` rows (measured invisible today); recorded with a prohibition on hand-copying the table forward. PR-004: `plans_index.scan_plans` corrected to `plan_entry`, the `plan-review-long` parity obligation measured as nil, the `done` alias closed via `normalize_status`. PR-005: the plan's live counts were stale in one day (`5j7jv1` no longer `no-go`; terminal `no-go` 7 -> 8) while the load-bearing census held exactly, and `aw check` "no new findings" now reads as a delta against a tree carrying 51 unrelated findings. PR-006: the gate gained the lifecycle transition, honesty rule, scope fence and approval summary. OQ-01 RESOLVED from evidence (`reusable/` stays reachable; `SWEEP_DISPOSITIONS` already sweeps it, `plans.STANDING` excludes it from `TERMINAL`, and the directory holds zero plans). Findings and decisions D-1..D-5 in `.aw/records/reviews/20260929-iifcam-01-khiueh-clear-the-two-stale-escalations-by-amending-the-review-recor.review.md`.
- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored to graduate backlog `iifcam`, which asked the maintainer to choose between amending two terminal plans' stale escalations and leaving them as history. THE REPOSITORY ANSWERS THE QUESTION AND THE ANSWER IS NEITHER OPTION AS POSED: amend the REVIEW RECORDS (not the plans), because the stale findings have a measured live consequence, and fix the write path that made the tooled route unsafe. Measured at HEAD `08133a35`. (1) The item's census re-derives exactly: `stale_escalated_findings` over all plans returns precisely `ki6tom` PR-201 and `yku4ga` PR-701, and `subject_gating_blocks` still blocks on each. (2) The consequence is not cosmetic: in a throwaway tree, a pending plan declaring `- Item-Dependencies: executed:ki6tom` drew `check.ipd-dependency-findings-blocked`, and the finding cleared once the closing round was appended, so the stale finding is a trap for the next dependent rather than dead history. (3) The tooled route is over-broad: `aw ipd recheck-readiness --stale-findings --apply` on the retired `ki6tom` rewrote its `- Readiness:` to `go-pending-approval` and prepended a re-check record, because `recheck_conditions` refuses on readiness VALUE and never on DISPOSITION, while the module's own `SWEEP_DISPOSITIONS` comment already states the terminal rule. (4) The `aw ipd set approved` terminal-reopen guard still refused afterwards, so this is an attestation-falsification defect and not a resurrection one; stated that way deliberately rather than overstated. The amendment half is already append-only and was verified to leave both plan files byte-identical, which is why the fix is a refusal on one half and not a redesign.

## Goal

Close both stale escalations through the append-only review-record route so the gate stops firing on answered questions, and make `aw ipd recheck-readiness` refuse the readiness write on a plan in a terminal disposition, so the route this repository used to clear them cannot also falsify a retired plan's review attestation.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: close the write-path hole first

- [x] E-01 REFUSE THE READINESS RECOMPUTE ON A PLAN IN A TERMINAL DISPOSITION, in `plan_readiness.recheck_conditions`, as a REFUSAL beside the existing readiness-field refusals rather than as a fourth condition. The distinction is the one that function's own comment already draws: a refusal is "a reason the re-check may not act at all, as distinct from reasons the plan is not ready", and disposition is exactly that. Derive the disposition from the plan's PATH, never from its `- Status:` text, and reuse `plans.TERMINAL` as the vocabulary so the terminal set is not spelled a second time.
  DERIVE IT THE WAY THE REPOSITORY ALREADY DOES, WHICH IS THE FIRST PATH COMPONENT UNDER THE PLANS DIR AND NOT `parent.name`. Three shipped sites establish this and each documents why: `check_engine._plan_disposition`, `attention._plan_disposition_from_rel`, and `plans_index.plan_entry` (whose `rel.split("/", 1)[0]` the other two cite as the derivation they reuse; the authored citation said `plans_index.scan_plans`, and review measured that the split lives in `plan_entry`, which `scan_plans` calls). The reason is load-bearing here: `aw archive plans` shards a terminal plan into `<disposition>/YYYYMM/` (`plans_archive._shard_target`), so a parent-directory test silently stops recognizing every sharded plan, and both plans this Set must protect are archive candidates.
  CALL `check_engine._plan_disposition` VIA A FUNCTION-LOCAL (LAZY) IMPORT. That choice is measured, not preferred, and this bullet fixes an authored instruction that would have produced the wrong code (review PR-001). THE ONLY TWO CANDIDATE HELPERS ARE NOT EQUIVALENT, because they resolve the plans root differently: `check_engine._plan_disposition` relativizes against `_type_dirs(repo_root, "plans")`, i.e. the RESOLVED records root, while `attention._plan_disposition_from_rel` matches the two hard-coded string prefixes `.aw/records/plans/` and `.agents/plans/`. Measured at review in a scratch repo configured `records_backend: companion` (records resolved to `<repo>.aw/records/plans`): `check_engine._plan_disposition` returned `not-executed`, `superseded` (sharded) and `pending` correctly for the three cases, while the attention-style derivation returned `''` for ALL THREE, because the plan is not relative to the repo at all. So the attention helper would silently treat every plan in a companion-backed repo as NON-terminal, which is precisely the fail-open this item exists to close.
  THE AUTHORED IMPORT WARNING IS FACTUALLY WRONG AND IS CORRECTED HERE. It said "`check_engine` is NOT a safe module-scope import here and must not become one". Measured at review: importing `check_engine` at `plan_readiness` module scope raises NO ImportError in either import order (probed by loading a patched copy of the module), so there is no cycle. The real objection is COST, which is smaller than implied: a cold `import agent_workflows.check_engine` measures 0.203s against 0.193s for `plan_readiness` itself. Use a FUNCTION-LOCAL import anyway, for the reason the module already uses one for `review_findings` in this very function ("Lazy import avoids any import cycle"), and because a 7839-line checker module has no business being on the import path of a predicate both host runners load. Do NOT write the instruction as "no cycle is possible"; write it as the deliberate cost-and-layering choice it is.
  A PLAN OUTSIDE ANY PLANS DIRECTORY MUST NOT BE REFUSED. `_resolve` accepts a direct path specifically so a caller can re-check "a fixture, or a plan outside the records tree", and those tests are how this behavior is pinned; a refusal that fired on an unlocatable path would break the verb's own test surface. `_plan_disposition` returns `None` for such a path AND for a plan sitting directly in the plans dir with no disposition component (both measured at review), and BOTH must mean NOT terminal.
  USE `plans.TERMINAL` FOR THE COMPARISON, AND NORMALIZE THE `done` ALIAS. `plans.DISPOSITION_DIRS` includes the legacy read alias `done`, which is NOT in `plans.TERMINAL` as a literal but which `plans.normalize_status("done")` maps to `executed` (measured). No `done/` directory exists in this tree today, so this is a latent case rather than a live one; compare `plans.normalize_status(disposition) in plans.TERMINAL` rather than testing raw membership, so a repository that still carries `done/` is not silently left writable. Measured at review: `normalize_status` maps `done`/`executed`/`superseded`/`not-executed` into `TERMINAL` and maps `pending`->`to-review`, `reusable`->`reusable`, and an archive shard name like `202609` -> `legacy/unknown`, none of which are terminal, so the normalization adds no false positive.
  - Depends on: none
  - Expected outcome: `recheck_conditions` on a plan under `executed/`, `superseded/`, or `not-executed/` returns `may_write` False with a refusal naming the disposition and stating that a terminal plan's record is history; the same call on a `pending/` plan and on a plan at an arbitrary path outside the plans tree is UNCHANGED. Paste the before/after refusal lists for one terminal and one pending plan.
  - Execution state: performed

- [x] E-02 KEEP THE STALE-FINDING AMENDMENT REACHABLE ON A TERMINAL PLAN, so E-01 narrows the write to the plan file and does not disable the return path the two target records need. In `readiness_recheck.run_recheck_readiness` the two halves already run in a fixed order for a documented reason ("THE STALE-FINDING HALF RUNS FIRST, deliberately. It can CHANGE the second condition's answer"), and that order is what makes this separable: the amendment half writes only to the REVIEW record, and `append_round_resolving_stale` takes `review_path`, never the plan path.
  THE REPORTING MUST SAY WHICH HALF ACTED, because after E-01 a terminal plan's row is simultaneously a refusal and an amendment, and a row that renders one while doing the other is the false report this area exists to avoid. The row already carries both (`_Row` is documented as "carrying BOTH halves so a report can never state an action without a cause").
  THE MACHINE SURFACE IS ALREADY BROKEN FOR THIS CASE, AND REVIEW MEASURED IT, so this is a repair with a named target rather than an open-ended "make it visible" (review PR-002). Driven at base against a terminal plan forced into the readiness-refusal branch (`- Readiness: go-pending-approval`) with `--stale-findings --apply`: the amendment WAS written to the `.review.md`, and `--json` reported `changes: []` with a single `readiness.recheck-refused` diagnostic whose `detail` carried the amendment only as trailing prose; the `--agent` compact record reported `"findings":1` and NO `changes` key at all, because `_Row.action` stays `"refused"` and `run_recheck_readiness` builds its `changes` list from `r.action != "refused"`. So an agent consuming `--agent` sees a file written and no `Change` naming it, which is exactly the false report the row's own docstring forbids. THE FIX IS THEREFORE SPECIFIC: emit a `Change` for the AMENDED `.review.md` path whenever `stale_applied` is true, INDEPENDENTLY of whether the readiness half refused, and keep the refusal as its own `Diagnostic`. A row must never report a write with no `Change`, nor a `Change` whose `path` is the plan when the plan was not written.
  NOTE THE `--agent` COMPACT RENDERING LIMIT, so V-02's evidence demand is satisfiable. `CommandResult.to_agent_record` drops each `Diagnostic`'s `detail` unless the context is verbose, and `aw ipd recheck-readiness` registers no `--verbose` flag (measured: its `--help` lists only the four shared presentation flags plus `--apply`, `--stale-findings`, `--actor`, `--dir`). So the compact `--agent` record can carry the rule NAME but not the reason text. Do NOT try to satisfy V-02 by pasting a `detail` from `--agent`; use `--json`, which carries `detail` in full (measured), and require `--agent` only to show a `Change` for the review path beside the `readiness.recheck-refused` diagnostic. Adding `--verbose` to this verb is OUT OF SCOPE.
  DO NOT ADD AN OVERRIDE FLAG. There is no `--allow-terminal` here: the amendment is the sanctioned act and the plan write is not, so a flag would only re-open the hole E-01 closes.
  - Depends on: E-01
  - Expected outcome: `aw ipd recheck-readiness --stale-findings --apply <terminal-plan>` appends the closing round to the REVIEW record, leaves the plan file BYTE-IDENTICAL (assert the hash), and reports the readiness refusal and the amendment in the same row; `--json` carries both the refusal `detail` and a `Change` for the `.review.md` path, and `--agent` carries that `Change` beside the `readiness.recheck-refused` diagnostic; the same command on a pending plan behaves exactly as it does today.
  - Execution state: performed

### Task group 2: pin both behaviors

- [x] E-03 PIN E-01 AND E-02 WITH BEHAVIORAL TESTS, in `tests/test_review_record_classifier.py`, which is the surviving home for `plan_readiness` coverage after the suite trim deleted `tests/test_plan_readiness_recheck.py` (commit `19313eed`, "test: trim test suite from 9,136 to under 2,000 tests"). Build each case on a temporary tree, driving `recheck_conditions` / `run_recheck_readiness` or the CLI, and assert on returned refusals, written file bytes, and exit codes.
  REQUIRED CASES, each falsifiable: (1) a `no-go` plan under each of the three terminal dispositions is REFUSED, with the disposition named in the reason; (2) a `no-go` plan under `pending/` is still UPDATED, which is the regression that proves the fix did not disable the verb; (3) a terminal plan carrying a stale escalation has its REVIEW record amended while its own bytes are unchanged; (4) a terminal plan SHARDED into `<disposition>/YYYYMM/` is still recognized as terminal, which is the case a `parent.name` derivation would miss and therefore the one that pins the derivation choice; (5) a plan at a path under no plans directory is NOT refused for disposition; (6) THE COMPANION-BACKED CASE, added at review (PR-001): in a scratch repo whose `.aw/config/project.json` sets `records_backend: companion`, a plan under the resolved records root (`<repo>.aw/records/plans/not-executed/`) is STILL refused. This is the case that discriminates the two candidate helpers, measured at review as `not-executed` from `check_engine._plan_disposition` versus `''` from the attention-style prefix match, so without it the fix could ship silently fail-open for every companion-backed repository.
  ASSERT ON OUTCOMES, NEVER ON CODE SHAPE. Per the repository testing contract, no test here may read module source with `inspect`, `ast`, or a regex, and none may assert a symbol census or a line count. Cases (4) and (6) in particular must be real PATHS exercised through the real call, never an assertion about which helper was called.
  CASE (4) NEEDS A CONSTRUCTED SHARD, because the live tree has none. Measured at review: zero plans in `.aw/records/plans/` currently sit under a `YYYYMM` shard directory, so the sharded case cannot be taken from the corpus and must be built under `tmp_path`. State that in the test's own docstring, so a later reader does not go looking for a real example and conclude the case is dead.
  DRIVE THE VERB THROUGH `run_recheck_readiness` WITH AN `argparse.Namespace`, not through a subprocess, and note the flag shape review measured: the namespace needs `dir`, `apply`, `stale_findings`, `selectors`, `actor`, and BOTH `agent` and `json` (they are read by `select_output`; omitting either raises). `recheck_conditions` takes `(repo_root, plan_path)` and accepts optional `plan_text`, but the path is still required even when text is supplied, so the terminal-disposition cases MUST write real files under `tmp_path` rather than passing text alone.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest tests/test_review_record_classifier.py` passes with the new cases present, and cases (1), (4) and (6) FAIL against base; paste all three failures and then the green run.
  - Execution state: performed

### Task group 3: clear the two records and say so in the contract

- [x] E-04 APPEND THE CLOSING ROUND TO BOTH REVIEW RECORDS using the now-safe tool, and change NOTHING in either plan. Run the verb per plan with `--stale-findings --apply` against `ki6tom` and `yku4ga`; the amendment is `append_round_resolving_stale`, which carries forward every still-unresolved finding UNCHANGED and marks only the matched row `fixed`, so no other finding in either record is silently cleared.
  VERIFY BY THE GATE, NOT BY READING THE ROUND. The deliverable is that `subject_gating_blocks` returns empty for both id6s and that `stale_escalated_findings` over the whole plans tree returns zero rows; a correctly rendered round that left the gate firing would not satisfy this item.
  CONFIRM BOTH PLAN FILES ARE UNTOUCHED IN THE COMMIT. `git diff --cached --name-only` must list the two `.review.md` paths and NEITHER `.ipd.md` path. This is the item's whole point: the backlog item declined to amend because amending the plan was the only route it had.
  EXPECT DIFFERENT ROUND NUMBERS, AND DO NOT TREAT THAT AS AN ERROR. Measured at review: `ki6tom`'s record is at Round 2 and gains Round 3; `yku4ga`'s is at Round 1 and gains Round 2. Both were driven end to end in throwaway trees and both left the `.ipd.md` byte-identical while clearing `subject_gating_blocks` to empty, so the expected outcome is known-achievable rather than hoped for.
  A SIDE EFFECT ON THE DECISIONS SECTION IS EXPECTED AND MUST BE STATED, added at review (PR-003). `append_round_resolving_stale` carries forward FINDINGS only; it writes no `### Decisions` table, so the new round's `current_decisions()` is EMPTY. That is a real consequence for a second checker: `check.review-decision-unescalated` reads CURRENT-ROUND decisions, and both target records carry an irreversible row in their present current round (`ki6tom` D-6 `Reversible: no`, `yku4ga` D-1 `Reversible: no`, both measured). After the amendment those rows stop being current, so the warning rule stops seeing them. Measured at review: that rule reported NOTHING for either plan before OR after (both are already satisfied, `yku4ga` through a blocking question and `ki6tom` by producing no drift at base), so this change is INVISIBLE in `aw check` today and the item loses nothing. It is recorded because the mechanism is a real narrowing of a checker's view, and a future record whose irreversible decision IS being reported would have that report silently cleared by an amendment that never examined it. Do NOT "fix" this by hand-copying the old Decisions table into the new round: that would forge decision rows into a round in which nobody made them. If the executor judges it worth closing, file a carrier rather than widening this plan.
  - Depends on: E-03
  - Expected outcome: both review records carry one new appended `## Round <n>` marking PR-201 / PR-701 `fixed` with the answered question cited (Round 3 for `ki6tom`, Round 2 for `yku4ga`, both measured at review); `stale_escalated_findings` over all plans returns zero; `subject_gating_blocks` returns empty for `ki6tom` and `yku4ga`; both `.ipd.md` files byte-identical to HEAD; `aw check reviews` still conforms.
  - Execution state: performed

- [x] E-05 STATE THE REFUSAL IN THE PLAN-REVIEW CONTRACT, beside the two `aw ipd recheck-readiness` command lines under "A `NO-GO` is RE-EVALUABLE", which currently list three bounding properties of the verb and do not mention disposition. Add the fourth: a plan in a terminal disposition is refused, because a terminal plan's `no-go` is an accurate record of why it was retired. Also note, in the "The escalation RETURN PATH" subsection immediately below, that the amendment half still applies to a terminal plan, since that is the case these two records are.
  KEEP IT TO THE SMALLEST WORDING THAT CLOSES THE GAP, and do not restate the sweep default: `SWEEP_DISPOSITIONS` already documents that terminal plans are not swept, and duplicating it in the contract creates two statements that can drift (GUIDING_PRINCIPLES P8).
  THE SINGLE-FILE VARIANT IS THE ONLY SITE, AND REVIEW VERIFIED THAT RATHER THAN ASSUMING IT (PR-004). `plan-review` ships a parallel multi-file variant (`.aw/system/workflows/plan-review-long/`) kept in "deliberate parity", so a parity obligation was the obvious risk. Measured at review: `recheck` appears in `.aw/system/workflows/` at exactly three lines, all in `plan-review/plan-review.md`, and the long variant contains NO re-evaluability section and NO escalation-return-path section to keep in sync. So editing the one declared path is complete, and no `plan-review-long` file needs adding to `- Scope-Paths:`. Record that measurement in the item's evidence so a later reader does not re-open the parity question.
  - Depends on: E-04
  - Expected outcome: the contract's re-evaluability section names the terminal-disposition refusal and the still-permitted amendment; a reader following the document alone does not expect a terminal plan's readiness to be rewritable; the `plan-review-long` variant is confirmed to contain no counterpart passage, so parity is satisfied by the single edit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A plan's DISPOSITION is derived from the FIRST path component under the plans directory, never from `parent.name`, because `aw archive plans` shards a terminal plan into `<disposition>/YYYYMM/`. Three sites already do this and cross-cite each other: `check_engine._plan_disposition`, `attention._plan_disposition_from_rel`, `plans_index.plan_entry` (the split lives in `plan_entry`, which `scan_plans` calls; corrected at review from the authored `plans_index.scan_plans`).
- THOSE THREE SITES AGREE ON THE SPLIT AND DISAGREE ON THE ROOT, which is the distinction that decides which one a new caller may reuse (added at review). `check_engine._plan_disposition` relativizes against the RESOLVED records root (`_type_dirs(repo_root, "plans")`), so it follows a `records_backend: companion` configuration out of the repository; `attention._plan_disposition_from_rel` matches the literal prefixes `.aw/records/plans/` and `.agents/plans/` against a repo-relative path, so it returns `""` for any records root outside the repo. Measured at review in a companion-backed scratch repo: `not-executed`/`superseded`/`pending` from the former, `''` for all three from the latter. Reuse the resolved-root derivation for any gate whose fail-open direction matters.
- `- Readiness:` is NOT the only attestation on a plan, and a terminal plan legitimately carries a non-`no-go` value: 434 terminal plans currently carry `go-pending-approval` or `go`, written while they were live. So a terminal plan is not identifiable by its readiness VALUE and the refusal must key on disposition, which is what E-01 does.
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
| F-4 | MEDIUM | The consequence of F-2 is attestation falsification, NOT resurrection, and the difference bounds this plan. After the write, `aw ipd set approved ki6tom` still refused on the terminal-reopen guard and wrote nothing. But `is_plan_review_approved` flipped False -> True and `approval_refusals` went from 2 to 0 for the retired plan, so safety now rests wholly on the disposition guard while the readiness signal beneath it asserts the opposite. VERIFIED AT REVIEW, with one precision the authored row omits: reaching the terminal-reopen guard required passing two EARLIER refusals first (`aw ipd set approved` refused on `the typed review artifact records an unresolved gating finding` before the amendment, then on `Priority is missing; Work-Kind is missing`), and only with those satisfied did it refuse with "refusing to move 1 plan(s) BACKWARDS out of a terminal disposition" and write nothing. So the guard does hold, and it is the LAST of several rather than the only one. |
| F-5 | LOW | The amendment half is already correct and append-only, which is why the fix is a refusal on one half rather than a redesign. Verified by running `append_round_resolving_stale` against both records in a throwaway tree: both `.ipd.md` files stayed byte-identical (sha256 compared), the closing round was appended, and `subject_gating_blocks` went to empty for both id6s. |
| F-6 | LOW | The PENDING `no-go` population must keep being reachable; those are live plans and the verb exists for them. THE AUTHORED CENSUS WAS ALREADY STALE ONE DAY LATER, which is why the bar is a property and not a number (review PR-005): the plan names `5j7jv1` as the one pending `no-go`, and re-measured at review `5j7jv1` is `go-pending-approval` while the pending `no-go` set is `a6i03f` and `t5txjk`; the terminal `no-go` count moved 7 -> 8 (1 `not-executed/`, 7 `superseded/`). The load-bearing part HELD EXACTLY: the 2 plans carrying a stale escalation are still `ki6tom` and `yku4ga` and no others. The executor must RE-DERIVE both populations at execution time and quote no number from this plan. |
| F-7 | LOW | The dedicated test module for this code, `tests/test_plan_readiness_recheck.py`, was DELETED by the suite trim at `19313eed` (917 lines, alongside `tests/test_plan_readiness.py` at 2548), so there is currently no test that would have caught F-2 and no obvious home for new cases. E-03 places them in `tests/test_review_record_classifier.py`, the surviving `plan_readiness` test module (verified at review: it imports `plan_readiness` and is the only non-runner test module that does, alongside `test_ipd_lint`, `test_attention_contract` and `test_spec_review_attestation` which touch it incidentally). |
| F-8 | HIGH | Added at review. THE MACHINE SURFACE MISREPORTS THE MIXED CASE TODAY, INDEPENDENTLY OF E-01, so E-02 is a live defect repair and not merely forward-compatibility work. Driven at base on a terminal plan whose readiness half refuses while its amendment half writes: the `.review.md` WAS modified, `--json` reported `changes: []`, and `--agent` reported `"findings":1` with no `changes` key at all. Cause: `_Row.action` remains `"refused"` and `run_recheck_readiness` derives its `Change` list from `r.action != "refused"`, so a written file produces no `Change`. After E-01 this becomes the NORMAL path for every terminal plan, including both of this plan's targets. |
| F-9 | MEDIUM | Added at review. The authored E-01 instruction "`check_engine` is NOT a safe module-scope import here and must not become one" is FACTUALLY WRONG: loading a patched `plan_readiness` that imports `check_engine` at module scope raises no ImportError in either order, and the cold import cost is 0.203s against `plan_readiness`'s own 0.193s. The correct instruction is a function-local import chosen for LAYERING and COST (the module already lazy-imports `review_findings` inside this very function), not for a cycle that does not exist. Left uncorrected, an executor would either believe a false fact or spend a pass proving it false. |
| F-10 | LOW | Added at review. `plans.DISPOSITION_DIRS` carries the legacy read alias `done`, which is absent from `plans.TERMINAL` as a literal but which `plans.normalize_status` maps to `executed`. No `done/` directory exists in this tree, so this is latent; a raw membership test against `TERMINAL` would nonetheless leave a `done/` plan writable, so E-01 now specifies `normalize_status(disposition) in plans.TERMINAL`. Measured: that normalization adds no false positive (`pending`->`to-review`, `reusable`->`reusable`, a `202609` shard name -> `legacy/unknown`). |
| F-11 | LOW | Added at review. The amendment NARROWS a second checker's view, and the plan did not say so. `check.review-decision-unescalated` reads CURRENT-ROUND decisions only; `append_round_resolving_stale` writes findings and no `### Decisions` table, so the new round has zero decisions and both targets' irreversible rows (`ki6tom` D-6, `yku4ga` D-1, both `Reversible: no`) stop being current. Measured: that rule reports nothing for either plan before or after, so nothing is lost here, but the mechanism is real. Recorded in E-04 with an explicit prohibition on hand-copying the old table forward, which would forge decision rows. |
| F-12 | LOW | Added at review. THE DEFECT HAS FIRED IN PRODUCTION ONCE ALREADY AND WAS CAUGHT BY HAND, which is the strongest available argument for E-01. `superseded/...dw7i3m` carries a `readiness re-check` history record that cleared it to `go-pending-approval`, followed by a hand-written `readiness REVERTED` record restoring `no-go` and stating that clearing the field "left a plan implementing a rejected design ONE APPROVAL away from executing, which is a worse failure than the stale mark it was fixing". That plan was live when re-checked and retired afterwards, so it is not a strict instance of F-2; it is evidence that the readiness field on a not-to-be-executed plan is load-bearing and that the only control today is a human noticing. |

## Proposed changes (ordered, validatable)

1. A disposition REFUSAL in `recheck_conditions`, derived from the plan's path via a function-local call to `check_engine._plan_disposition` (the resolved-records-root derivation), compared through `plans.normalize_status(...) in plans.TERMINAL` (E-01).
2. The stale-finding amendment kept reachable on a terminal plan, AND the measured machine-surface defect repaired: a `Change` is emitted for the amended `.review.md` whenever the amendment applied, independently of the readiness half's refusal (E-02, F-8).
3. Behavioral tests for the refusal, the preserved pending behavior, the untouched plan bytes, the sharded-path case, the out-of-tree case, and the companion-backed records-root case (E-03).
4. The two closing rounds appended to the two review records, verified by the GATE rather than by reading the rounds, with both plan files provably untouched (E-04).
5. The plan-review contract stating the terminal refusal and the still-permitted amendment (E-05).

## Deferred / out of scope (with reason)

- The OTHER terminal `no-go` plans are NOT amended. They carry no stale escalation (measured at review: `stale_escalated_findings` returns rows for exactly two plans out of the whole tree), so their `no-go` is an accurate record of why they were retired and there is nothing to clear. The authored wording said "the other five" and review re-measured the terminal `no-go` population at 8, so the count is deliberately not stated here; the PROPERTY (no stale escalation) is the bar, and the executor re-derives the set.
  - Carrier-Declined: Nothing is owed. This row records a MEASUREMENT that there is no work here, not a deferred defect: the join predicate returns zero rows for each of them, so there is no stale finding to clear and amending them would append a round closing nothing. If a future escalation on one of them is ever answered, the shipped verb reports it, which is the standing detector and needs no item filed now.
- The `### Decisions` carry-forward gap is NOT closed here (F-11). `append_round_resolving_stale` writes no decisions table, so an amended record's current round has zero decisions and `check.review-decision-unescalated` stops seeing any irreversible row that was current before. Measured as invisible on both targets today (that rule reports nothing before or after), and closing it means changing `append_round_resolving_stale`, which this plan's Scope explicitly excludes as correct-as-measured.
  - Carrier-Declined: Nothing is owed TODAY, and the reason is a measurement rather than a judgement: the affected rule produces no finding for either target in either state, so there is no live defect to hand off, and filing an item would assert outstanding work the tree does not exhibit. The mechanism is nonetheless recorded in F-11 and in E-04's prohibition, so a future record whose irreversible decision IS being reported can be traced to this cause instead of rediscovered. Changing the amendment function to carry decisions forward would also have to decide whether a carried decision is still "made in" the new round, which is a contract question and not a bug fix.
- No override flag (`--allow-terminal` or similar) is added. The amendment is the sanctioned act and the plan write is not, so a flag would re-open the hole E-01 closes; a maintainer who genuinely needs to edit a retired plan is already directed to a corrective IPD.
  - Carrier-Declined: This row records a PROHIBITION this plan adopts, not an unbuilt piece, so nothing is owed. Adding the flag is the defect E-01 exists to close, and the sanctioned route for editing a retired plan already exists (a corrective IPD, per AGENTS.md). Filing an item would represent a deliberately rejected design as outstanding work.
- The terminal-reopen guard reached by `aw ipd set` is untouched. It held in the measurement (F-4) and is a different gate with its own recorded override; re-litigating it here would widen this plan into lifecycle-setter territory.
  - Carrier-Declined: No future work is owed, because the guard is not defective: it REFUSED correctly in the measurement, writing nothing. This row exists to record the boundary of the defect (attestation falsification, not resurrection) so a reviewer does not read the silence as a claim that the setter is also broken.
- Backlog `rrvrwv` (the `aw ipd set` backwards terminal transition defect) is a separate live item with its own release gate and is not folded in: it concerns the STATUS setter, while this plan concerns the READINESS recompute, and combining them would put two gates in one plan.
  - Carrier: rrvrwv
- The item's framing question ("amend for tidiness, or leave as history") is answered rather than escalated, because the repository settled it: the measured live consequence in F-1 removes the "leave it" option, and the append-only route removes the objection to amending. No maintainer decision is required for that; the one judgement left is whether to fix the write path in the same pass, which this plan takes because clearing the records by tool is what exposed it.
  - Carrier-Declined: Nothing is owed: this records that a question was ANSWERED from repository evidence rather than deferred. The answer is carried by this plan's own E-04 (amend the records) and E-01 (fix the route), so there is no residue to hand to another artifact. Recorded here so a reviewer can dispute the answer on its evidence rather than discovering the item's question was silently dropped.

## Scope check

- Over-scope: none. The write-path fix is not opportunistic widening: it is the precondition for clearing the two records by tool, because the tooled route measurably rewrites a retired plan (F-2), and the backlog item's own recorded reason for not amending was that its only route would edit a terminal plan. E-02's machine-surface repair is likewise in scope rather than added scope: review measured it as a LIVE defect at base (F-8), and E-01 makes it the normal path for both of this plan's targets, so shipping E-01 without it would knowingly introduce a false machine report.
- Under-scope: this plan does not audit whether any OTHER verb writes to a terminal plan; it closes the one route measured to do so. It does not add a general "terminal artifacts are read-only" invariant across record types, which would be a contract change rather than a defect fix. It does not retroactively repair the `ki6tom` / `yku4ga` `- Readiness:` values, which are untouched at `no-go` and correct as history. It does not close the `### Decisions` carry-forward narrowing (F-11), measured as producing no finding on either target today. It does not add `--verbose` to `aw ipd recheck-readiness`, so the compact `--agent` record still omits diagnostic `detail`; V-02 routes around that with `--json` rather than widening the CLI.

## Required tests / validation

`python3 -m pytest tests/test_review_record_classifier.py` for the new cases, then the bare suite `python3 -m pytest` (already quiet, parallel, and fast-scoped by the configured `addopts`; do not add flags). Beyond the suite, the deliverable is verified by the GATE and by file bytes: `stale_escalated_findings` over the whole plans tree must return zero rows, `subject_gating_blocks` must be empty for both id6s, and both `.ipd.md` files must hash identically to HEAD. `aw check reviews` must conform, the `check.ipd-dependency-findings-blocked` reproduction must no longer fire, and `aw check` must report NO NEW findings.

MEASURE `aw check` AS A DELTA, NEVER AS A TOTAL (added at review). The tree is not clean at base: `aw check --agent` reports 51 findings at review HEAD, dominated by `check.plan-spec-link-missing` (31) and `check.ipd-uncarried-obligation` (11), none of them this plan's. So an executor who reads "no new findings" as "zero findings" will either believe the plan broke something it did not touch or start fixing unrelated rules. Capture the base finding set BEFORE the first edit and compare rule-by-rule afterwards; the bar is that no rule's count rises and no new rule appears, not that the total is zero. Do not quote the 51 as the baseline either: it is a live population and will have moved.

## Spec / documentation sync

`.aw/system/workflows/plan-review/plan-review.md` is amended by E-05 and is declared in `Scope-Paths`, so the runners announce the edit before the run. WHY: that document is where the verb's bounding properties are stated for a human reader, and a reader who follows it today would expect a terminal plan's readiness to be re-evaluable, which after E-01 it is not.

No `.spec.md` is amended. Checked at authoring: the `recheck-readiness` verb is mentioned in the specs tree only as an EXAMPLE of an event producer (`4sd62s`, artifact-metadata-store, which says it "likewise appends a `review` event"), and no spec states a disposition contract for the readiness field, so there is no spec-level claim that this plan contradicts. If execution finds one, declare it and amend it in the same change rather than shipping a divergence.

## Open questions

### OQ-01: Should the refusal also cover the `reusable` disposition?

- Blocking: no
- Status: resolved
- Owner: plan-review
- Carrier-Declined: Nothing is owed beyond this plan. The question is answered WITHIN it: E-01 refuses `plans.TERMINAL` only, leaving `reusable/` reachable, and V-01's evidence demand covers the boundary. Measured at review: the `.aw/records/plans/reusable/` directory contains ZERO `.ipd.md` files at all, so there is no population for a follow-up item to act on, and filing one would assert outstanding work where the measurement shows none.
- Resolution or deferral rationale: RESOLVED AT REVIEW 2026-09-30, NO: the refusal covers `plans.TERMINAL` only and `reusable/` stays reachable. The basis is repository evidence, not preference. FIRST, the code already states the policy in the opposite direction: `readiness_recheck.SWEEP_DISPOSITIONS` is `("pending", "reusable")`, i.e. `reusable` is SWEPT BY DEFAULT, so refusing it would put the write path in direct contradiction with the sweep default, which is the exact incoherence F-3 identifies as the defect. SECOND, `reusable` is not terminal by the repository's own vocabulary: `plans.STANDING = ("reusable",)` and `plans.normalize_status("reusable") -> "reusable"`, which is absent from `plans.TERMINAL` (measured), so including it would mean spelling a second, wider terminal set exactly as E-01 forbids. THIRD, a standing plan is by definition still runnable, so its `no-go` is a live signal rather than history, which is the whole distinction the refusal keys on. The authored text said the choice is "currently unobservable either way"; review re-measured and it is unobservable more strongly than stated, since `reusable/` holds no plans at all, not merely no `no-go` ones. The executor should NOT re-litigate this and should NOT add a `reusable` branch; V-01 already demands the pending-plan regression evidence that proves the refusal did not widen.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the pasted return of `recheck_conditions` for FIVE inputs: one plan under `not-executed/`, one under `superseded/`, one under `pending/`, one at a path under no plans directory, and one under a COMPANION-resolved records root (`records_backend: companion`, plan at `<repo>.aw/records/plans/not-executed/`). The three terminal ones (including the companion case) must show `may_write` False with a refusal whose text names the disposition; the pending one must show the SAME refusals/conditions it shows at base (paste the base run too, so "unchanged" is demonstrated rather than claimed); the out-of-tree one must show no disposition refusal. A paste showing only the terminal refusals does not satisfy this item, because the regression risk is the verb silently refusing everything. THE COMPANION CASE IS NOT OPTIONAL and is the one that discriminates the derivation (review PR-001): measured at review, the resolved-root helper returns `not-executed` there while the prefix-matching helper returns `''`, so omitting it would let a fail-open ship for every companion-backed repository. Also paste the `reusable/` boundary: a `no-go` plan under `reusable/` must NOT be refused, which is OQ-01's resolved answer.
  - Observed evidence: Pasted returns of `recheck_conditions` comparing base behavior to post-E01 for the five inputs plus the `reusable/` boundary:
    Base return (prior to E-01):
    === 1. ki6tom (not-executed) ===
    may_write: False
    refusals: ("the typed review artifact records an unresolved gating finding; `review_findings.subject_gating_blocks` -> 1 block(s)",)
    (Notice: NO terminal disposition refusal at base; writable once finding cleared)
    === 2. yku4ga (superseded) ===
    may_write: False
    refusals: ("the typed review artifact records an unresolved gating finding; `review_findings.subject_gating_blocks` -> 1 block(s)",)
    (Notice: NO terminal disposition refusal at base)
    === 3. nllamb (pending) ===
    may_write: False
    refusals: ('an unresolved BLOCKING open question remains (OQ-03); `has_unresolved_blocking_question` -> True',)
    conditions: (ConditionResult(name='unresolved-blocking-question', holds=True, reason='an unresolved BLOCKING open question remains (OQ-03); `has_unresolved_blocking_question` -> True'), ConditionResult(name='unresolved-gating-finding', holds=False, reason="no unresolved gating finding; `review_findings.subject_gating_blocks` -> empty (an ABSENT review artifact is silent by that predicate's documented contract)"), ConditionResult(name='negative-review-verdict', holds=False, reason="the newest review record's verdict is not negative; `newest_verdict` -> neutral"))
    === 4. out-of-tree ===
    may_write: False
    refusals: ('an unresolved BLOCKING open question remains (OQ-03); `has_unresolved_blocking_question` -> True',)
    === 5. companion not-executed (base prefix-matching derivation) ===
    may_write: False
    refusals: ('an unresolved BLOCKING open question remains (OQ-03); `has_unresolved_blocking_question` -> True',)
    (Notice: attention-style prefix match returns `''` for companion root, completely missing terminal disposition)
    === 6. reusable boundary ===
    may_write: False
    refusals: ('an unresolved BLOCKING open question remains (OQ-03); `has_unresolved_blocking_question` -> True',)

    Post-E01 return:
    === 1. ki6tom (not-executed) ===
    may_write: False
    refusals: ("the plan is in terminal disposition `not-executed`; a terminal plan's record is history and may not be rewritten.",)
    === 2. yku4ga (superseded) ===
    may_write: False
    refusals: ("the plan is in terminal disposition `superseded`; a terminal plan's record is history and may not be rewritten.",)
    === 3. nllamb (pending) ===
    may_write: False
    refusals: ('an unresolved BLOCKING open question remains (OQ-03); `has_unresolved_blocking_question` -> True',)
    conditions: (ConditionResult(name='unresolved-blocking-question', holds=True, reason='an unresolved BLOCKING open question remains (OQ-03); `has_unresolved_blocking_question` -> True'), ConditionResult(name='unresolved-gating-finding', holds=False, reason="no unresolved gating finding; `review_findings.subject_gating_blocks` -> empty (an ABSENT review artifact is silent by that predicate's documented contract)"), ConditionResult(name='negative-review-verdict', holds=False, reason="the newest review record's verdict is not negative; `newest_verdict` -> neutral"))
    (Unchanged from base: pending conditions and refusals match base exactly)
    === 4. out-of-tree ===
    may_write: False
    refusals: ('an unresolved BLOCKING open question remains (OQ-03); `has_unresolved_blocking_question` -> True',)
    conditions: (ConditionResult(name='unresolved-blocking-question', holds=True, reason='an unresolved BLOCKING open question remains (OQ-03); `has_unresolved_blocking_question` -> True'), ConditionResult(name='unresolved-gating-finding', holds=False, reason="no unresolved gating finding; `review_findings.subject_gating_blocks` -> empty (an ABSENT review artifact is silent by that predicate's documented contract)"), ConditionResult(name='negative-review-verdict', holds=False, reason="the newest review record's verdict is not negative; `newest_verdict` -> neutral"))
    (No disposition refusal for out-of-tree path)
    === 5. companion not-executed ===
    may_write: False
    refusals: ("the plan is in terminal disposition `not-executed`; a terminal plan's record is history and may not be rewritten.", 'an unresolved BLOCKING open question remains (OQ-03); `has_unresolved_blocking_question` -> True')
    (Terminal disposition correctly recognized and refused via resolved records root helper)
    === 6. reusable boundary ===
    may_write: False
    refusals: ('an unresolved BLOCKING open question remains (OQ-03); `has_unresolved_blocking_question` -> True',)
    (No disposition refusal for reusable/ path)
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: for one terminal plan carrying a stale escalation, the `sha256` of the `.ipd.md` BEFORE and AFTER `aw ipd recheck-readiness --stale-findings --apply`, shown equal, alongside the `git diff --stat` proving the `.review.md` changed and the `.ipd.md` did not. Plus the command's own HUMAN output showing the readiness refusal AND the `stale findings: appended a round ...` detail in the same row; the `--json` rendering showing the refusal `detail` in full AND a `Change` whose `path` is the `.review.md`; and the `--agent` rendering showing that same `Change` beside the `readiness.recheck-refused` diagnostic. Equal hashes with no amendment shown does NOT satisfy this: it would be indistinguishable from the verb doing nothing at all. ALSO PASTE THE BASE BEHAVIOR FOR THE SAME MIXED CASE, so F-8 is demonstrated rather than asserted: at base the `--agent` record carries `"findings":1` and NO `changes` key while the `.review.md` was written, which is the false report E-02 repairs. DO NOT expect a `detail` field in the `--agent` record: `to_agent_record` drops diagnostic `detail` unless verbose and this verb registers no `--verbose` (both measured at review), so use `--json` for the reason text.
  - Observed evidence: Demonstration of identical plan sha256 before/after, git diff stat, and command outputs across human, `--json`, and `--agent` alongside base reproduction:
    Plan sha256 before and after:
    HEAD hash: 4c72f7f924e4a89325f80dcb58079642480594eb6d7a69c0488fd3920a504cfa
    Disk hash: 4c72f7f924e4a89325f80dcb58079642480594eb6d7a69c0488fd3920a504cfa
    Equal: True

    `git diff --stat`:
    ```
     ...he-spec-prohibited-bypass-flags-from-both-host-runne.review.md | 8 ++++++++
     1 file changed, 8 insertions(+)
    ```
    (The .review.md changed with +8 lines; .ipd.md does not appear in diff)

    BASE BEHAVIOR REPRODUCTION (F-8):
    When running `aw ipd recheck-readiness --stale-findings --apply` on a terminal plan forced into refusal:
    Base `--json` output:
    ```json
    {
      "schema": "aw.agent/v1",
      "command": "ipd recheck-readiness",
      "status": "clean",
      "exit_code": 0,
      "summary": "1 plan(s) re-checked: 0 updated, 1 refused (each refusal names its surviving cause)",
      "verified": true,
      "complete": true,
      "diagnostics": [
        {
          "location": ".aw/records/plans/not-executed/20260904-runbypass-01-ki6tom-remove-the-spec-prohibited-bypass-flags-from-both-host-runne.ipd.md",
          "rule": "readiness.recheck-refused",
          "detail": "the plan's readiness is `go-pending-approval`, not `no-go`. This verb only ever re-evaluates a `no-go`; it has no path that lowers or re-asserts a readiness. | stale findings: appended a round to .../20260904-runbypass-01-ki6tom-remove-the-spec-prohibited-bypass-flags-from-both-host-runne.review.md marking PR-201 fixed",
          "severity": "info"
        }
      ],
      "changes": [],
      "evidence": [],
      "next_actions": [],
      "data": {}
    }
    ```
    (Note: `changes` was empty `[]` at base despite the `.review.md` file being written)

    Base `--agent` output:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"ipd recheck-readiness","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":1,"diagnostics":[{"location":".aw/records/plans/not-executed/20260904-runbypass-01-ki6tom-remove-the-spec-prohibited-bypass-flags-from-both-host-runne.ipd.md","rule":"readiness.recheck-refused"}],"next":null}
    ```
    (Note: `findings: 1` and NO `changes` key at all at base despite `.review.md` written)

    POST-FIX BEHAVIOR:
    Human output:
    ```
    ki6tom  [refused]
      path: .../.aw/records/plans/not-executed/20260904-runbypass-01-ki6tom-remove-the-spec-prohibited-bypass-flags-from-both-host-runne.ipd.md
      readiness: no-go
      clear  unresolved-blocking-question: no unresolved BLOCKING open question; `has_unresolved_blocking_question` -> False (a NON-blocking open question is deliberately not counted, per the maintainer's 2026-09-10 ruling on qhy3i3 OQ-01)
      clear  unresolved-gating-finding: no unresolved gating finding; `review_findings.subject_gating_blocks` -> empty (an ABSENT review artifact is silent by that predicate's documented contract)
      clear  negative-review-verdict: the newest review record's verdict is not negative; `newest_verdict` -> neutral
      stale-escalation: ki6tom: finding PR-201 (blocker/open) is STALE - the question it was escalated as (OQ-02) is `resolved`, so the finding's own record has not caught up
      REFUSED: the plan is in terminal disposition `not-executed`; a terminal plan's record is history and may not be rewritten.
      stale findings: appended a round to .../.aw/records/reviews/20260904-runbypass-01-ki6tom-remove-the-spec-prohibited-bypass-flags-from-both-host-runne.review.md marking PR-201 fixed

    1 plan(s) re-checked: 0 updated, 1 refused (each refusal names its surviving cause)
    ```
    (Notice: readiness REFUSED and stale findings amendment reported in the same row)

    Post-fix `--json` output:
    ```json
    {
      "schema": "aw.agent/v1",
      "command": "ipd recheck-readiness",
      "status": "clean",
      "exit_code": 0,
      "summary": "1 plan(s) re-checked: 0 updated, 1 refused (each refusal names its surviving cause)",
      "verified": true,
      "complete": true,
      "diagnostics": [
        {
          "location": ".aw/records/plans/not-executed/20260904-runbypass-01-ki6tom-remove-the-spec-prohibited-bypass-flags-from-both-host-runne.ipd.md",
          "rule": "readiness.recheck-refused",
          "detail": "the plan is in terminal disposition `not-executed`; a terminal plan's record is history and may not be rewritten. | stale findings: appended a round to .../.aw/records/reviews/20260904-runbypass-01-ki6tom-remove-the-spec-prohibited-bypass-flags-from-both-host-runne.review.md marking PR-201 fixed",
          "severity": "info"
        }
      ],
      "changes": [
        {
          "path": ".aw/records/reviews/20260904-runbypass-01-ki6tom-remove-the-spec-prohibited-bypass-flags-from-both-host-runne.review.md",
          "kind": "update",
          "detail": "appended a round to .../.aw/records/reviews/20260904-runbypass-01-ki6tom-remove-the-spec-prohibited-bypass-flags-from-both-host-runne.review.md marking PR-201 fixed",
          "applied": true
        }
      ],
      "evidence": [],
      "next_actions": [],
      "data": {}
    }
    ```
    (Notice: refusal detail present in full AND `changes` contains the `.review.md` update with `applied: true`)

    Post-fix `--agent` output:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"ipd recheck-readiness","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":1,"changes":[{"kind":"update","path":".aw/records/reviews/20260904-runbypass-01-ki6tom-remove-the-spec-prohibited-bypass-flags-from-both-host-runne.review.md"}],"diagnostics":[{"location":".aw/records/plans/not-executed/20260904-runbypass-01-ki6tom-remove-the-spec-prohibited-bypass-flags-from-both-host-runne.ipd.md","rule":"readiness.recheck-refused"}],"next":null}
    ```
    (Notice: `changes` list present with `.review.md` beside the `readiness.recheck-refused` diagnostic)
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: `python3 -m pytest tests/test_review_record_classifier.py` output pasted green with the new case count visible, PLUS the pasted FAILURE of cases (1), (4) and (6) against base (revert the predicate, run, paste, restore). The sharded case (4) must be shown failing against a `parent.name`-style derivation specifically, and the companion case (6) must be shown failing against the `attention._plan_disposition_from_rel` prefix-matching derivation specifically, since each exists to pin a different wrong derivation; a green run alone does not demonstrate either discriminates. Also paste the bare `python3 -m pytest` summary line with its `N passed` count. Per the repository contract, run the suite BARE: do not add `-n0`, a second `-q`, or `-p no:randomly`.
  - Observed evidence: Green test suite runs and demonstrated failure of cases (1), (4), and (6) against base and wrong derivations:
    PASSING RUN OF TARGET SUITE (`python3 -m pytest tests/test_review_record_classifier.py`):
    ```
    ............                                                             [100%]
    NOTE: 1 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    12 passed in 2.12s
    ```
    (All 6 new cases in `TestTerminalDispositionRefusal` plus 6 pre-existing tests passed)

    DEMONSTRATED FAILURE OF CASE 1 AGAINST BASE:
    With disposition check reverted:
    ```
    FAILED tests/test_review_record_classifier.py::TestTerminalDispositionRefusal::test_01_terminal_dispositions_refused - AssertionError: True is not false : not-executed plan must be refused for disposition
    ```

    DEMONSTRATED FAILURE OF CASE 4 AGAINST `parent.name` DERIVATION:
    With derivation replaced with `parent.name`:
    ```
    FAILED tests/test_review_record_classifier.py::TestTerminalDispositionRefusal::test_04_sharded_terminal_plan_refused - AssertionError: True is not false : Sharded terminal plan must not be writable
    ```

    DEMONSTRATED FAILURE OF CASE 6 AGAINST `attention._plan_disposition_from_rel` PREFIX DERIVATION:
    With derivation replaced with `attention._plan_disposition_from_rel`:
    ```
    FAILED tests/test_review_record_classifier.py::TestTerminalDispositionRefusal::test_06_companion_backed_terminal_plan_refused - AssertionError: True is not false : Companion terminal plan must not be writable
    ```

    FULL BARE SUITE RUN (`python3 -m pytest`):
    ```
    3878 passed, 2 skipped, 3 warnings in 89.02s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the pasted output of `stale_escalated_findings` over every plan in the tree showing ZERO rows (the same sweep that returned two at authoring and again at review), the pasted `subject_gating_blocks` result showing empty for BOTH `ki6tom` and `yku4ga`, `git diff --cached --name-only` listing the two `.review.md` paths and NEITHER `.ipd.md`, the `sha256` of both `.ipd.md` files shown equal to their HEAD blobs, `aw check reviews` pasted conforming, and the re-run of the F-1 reproduction showing `check.ipd-dependency-findings-blocked` no longer fires for a dependent declaring `executed:ki6tom`. A rendered round pasted without the gate results does not satisfy this item. ALSO STATE THE ROUND NUMBERS WRITTEN and confirm they match the review measurement (Round 3 for `ki6tom`, Round 2 for `yku4ga`); a different number is not necessarily wrong but must be explained, since it would mean a round was appended between review and execution.
  - Observed evidence: Gate sweep results, gating blocks check, file integrity verification, reviews check, and F-1 reproduction re-run:
    1. `stale_escalated_findings` over every plan in the repository:
       Total plans with stale findings: 0
       Rows: []
    2. `subject_gating_blocks` for targets:
       `review_findings.subject_gating_blocks(repo, 'ki6tom')` -> ()
       `review_findings.subject_gating_blocks(repo, 'yku4ga')` -> ()
    3. `git diff --cached --name-only` (committed scope paths):
       `.aw/records/reviews/20260904-runbypass-01-ki6tom-remove-the-spec-prohibited-bypass-flags-from-both-host-runne.review.md`
       `.aw/records/reviews/20260908-setidhard-00-yku4ga-make-a-setid-a-hard-cross-type-unique-identity-and-replace-s.review.md`
       (Neither `.ipd.md` path is staged or changed)
    4. `sha256` hash comparison with HEAD:
       ki6tom HEAD: 4c72f7f924e4a89325f80dcb58079642480594eb6d7a69c0488fd3920a504cfa
       ki6tom DISK: 4c72f7f924e4a89325f80dcb58079642480594eb6d7a69c0488fd3920a504cfa
       ki6tom Equal: True
       yku4ga HEAD: fd7fcd64755ab9dfe5b095d384a1a76f5df273d9dbdd0570bdb457c5d760be56
       yku4ga DISK: fd7fcd64755ab9dfe5b095d384a1a76f5df273d9dbdd0570bdb457c5d760be56
       yku4ga Equal: True
    5. `aw check reviews`:
       ```
       AW check  reviews                                                           0 ms
       ✓ CONFORMS  679 reviews checked

       Evidence
         checked  679
         errors  0   warnings  0
       Agent output: --agent (automatic when piped)
       ```
    6. F-1 reproduction re-run:
       `check_engine._findings_blocks_for(repo, 'executed', 'ki6tom', ki6_ipd)` -> []
       (No longer fires: dependency block cleared)
    7. Round numbers written:
       - `ki6tom`: Round 3 appended (previously Round 2).
       - `yku4ga`: Round 2 appended (previously Round 1).
       Both round numbers match the review measurement exactly.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the amended passage quoted from `.aw/system/workflows/plan-review/plan-review.md`, showing the terminal-disposition refusal stated in the re-evaluability section and the still-permitted amendment stated in the escalation-return-path section, plus a statement that the sweep default was NOT restated there (P8). Quote enough surrounding text to show the placement, not just the inserted sentence. ALSO PASTE THE PARITY CHECK: a search for `recheck` across `.aw/system/workflows/` showing the matches confined to `plan-review/plan-review.md`, confirming the `plan-review-long` variant needs no counterpart edit (measured at review, but re-derive rather than quote, since the long variant could gain such a section).
  - Observed evidence: Quoted amended passages from `.aw/system/workflows/plan-review/plan-review.md` and workflows parity search:
    1. Re-evaluability section (lines 636-653):
    ```markdown
    The verb RECOMPUTES the three `NO-GO` conditions above with the shipped predicates,
    reports each one individually with its reason, and writes only when all three are
    clear. Four properties bound it, and they are what make it something an agent may
    run at all:

    - It can reach ONLY `GO - PENDING HUMAN APPROVAL`. **Only a review may set `GO`**,
      and `GO` still requires human approval. The verb refuses an absent field (absence
      means no review recorded a signal, and minting a value would assert a review that
      never happened), an out-of-vocab field, and any readiness that is not `NO-GO`.
    - It refuses a plan in a terminal disposition (`executed/`, `superseded/`, `not-executed/`),
      because a terminal plan's `NO-GO` is an accurate record of why it was retired.
    - It RECORDS its computed evidence in the plan's `## Workflow history`, labelled a
      readiness re-check and containing no verdict token, so it is never read as a
      review and a reader can audit the claim without re-running anything.
    - It re-checks; it does NOT re-review. No finding is re-derived and no plan content
      is re-critiqued, so a plan needing fresh critique still needs `/plan-review`.
    ```
    (Note: The sweep default `SWEEP_DISPOSITIONS` was NOT restated here, respecting P8)

    2. Escalation return path section (lines 662-672):
    ```markdown
    A finding whose escalated question is now `- Status: resolved` is therefore STALE.
    Clear it by APPENDING a new `## Round <n>` to the review record that marks the
    finding `fixed` and cites the answered question and its date; never edit the
    earlier round in place, because round 1 was true when it was written and rewriting
    it destroys the audit trail. `aw ipd recheck-readiness --stale-findings` reports
    these (and writes the round under `--apply`), matching the question to the finding
    on the question's declared `- Finding: <ID>` back-reference rather than on a
    judgement about what the question was about. A question that is still open does NOT
    make its finding stale. This review-record amendment still applies to a terminal
    plan, clearing its stale gating finding without rewriting the plan file itself.
    ```

    3. Parity check across `.aw/system/workflows/`:
    `grep -rn "recheck" .aw/system/workflows/`
    Output:
    ```
    .aw/system/workflows/plan-review/plan-review.md:633:aw ipd recheck-readiness <id6>            # preview the per-condition verdict
    .aw/system/workflows/plan-review/plan-review.md:634:aw ipd recheck-readiness <id6> --apply    # write, when every condition is clear
    .aw/system/workflows/plan-review/plan-review.md:666:it destroys the audit trail. `aw ipd recheck-readiness --stale-findings` reports
    .aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md:100:adversarial surface). On a clean in-scope precheck it appends the attributed `<agent/model>` history
    ```
    (Confirmed: matches are strictly confined to `plan-review/plan-review.md`; `plan-review-long/` has zero occurrences and requires no edit)
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

`/plan-review` has run (see `## Workflow history` and the typed review record), so the `- Readiness:` field it wrote is the review's attestation; explicit human approval is still required before execution. The plan has no plan dependencies (`- Item-Dependencies: none`) and ONE open question, OQ-01, which is `- Blocking: no` and now `- Status: resolved` from repository evidence, so nothing is outstanding for a human to answer.

WHAT A HUMAN WOULD BE APPROVING, in one paragraph. Two production modules gain a refusal and a report fix, one test module gains six cases, two `.review.md` records gain one appended round each, and one workflow document gains two sentences. NO plan file is edited, which is the whole point: the backlog item declined to amend precisely because its only route rewrote a retired plan, and review reproduced that route rewriting `ki6tom`'s `- Readiness: no-go` to `go-pending-approval` and prepending a re-check record to a plan that will never run. After the fix the readiness half refuses on disposition while the amendment half still clears the two stale gates. The gates are real rather than cosmetic: a pending plan declaring `- Item-Dependencies: executed:ki6tom` draws `check.ipd-dependency-findings-blocked` today, and the same predicate is what both host runners consult. REVIEW CHANGED THREE THINGS A HUMAN SHOULD KNOW. FIRST, the authored derivation instruction would have produced a fail-open: the two candidate helpers are not equivalent, and in a `records_backend: companion` repository the one the plan implied returns no disposition at all, so every terminal plan there would stay writable; E-01 now names `check_engine._plan_disposition` and E-03 adds the case that discriminates them. SECOND, the machine surface is ALREADY wrong for the mixed case at base (a written `.review.md` reported with no `Change`, and `--agent` reporting no changes key at all), so E-02 is a defect repair, not future-proofing. THIRD, the plan's live counts were already stale one day after authoring (`5j7jv1` is no longer `no-go`; the terminal `no-go` set moved 7 to 8) while the load-bearing census held exactly at two stale escalations, so every count is now a re-derived property rather than a bar.

EXECUTION ORDER IS LOAD-BEARING AND NOT MERELY PREFERRED: E-01 and E-02 must land BEFORE E-04, because E-04's whole method is to clear the two records with the tool, and running that tool at base is what rewrites a retired plan (F-2). An executor who reverses the order will have committed the exact edit the backlog item declined to make.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*` item. A remembered result, a paraphrase, or a claim that a test passed without its runner output is a failed validation, not a completed one. Run the suite bare (`python3 -m pytest`); do not add `-n0`, a second `-q`, or `-p no:randomly`.

EXECUTION CONTRACT. Follow the tooled lifecycle: `aw ipd begin khiueh`, perform E-01 through E-05 in order, fill every `V-*` with the concrete pasted evidence named above, and confirm `aw ipd lint --phase pre-transition` reports conforming. The terminal transition is then UNCONDITIONALLY owed with a CONDITIONAL owner: in a managed lane the RUNNER owns it (`aw ipd begin`/`finalize` refuse an agent there with `AW-LIFECYCLE-ROLE-001`), and only in an unmanaged or manual run does the executor run `aw ipd finalize khiueh` itself. Never hand-roll the move with `git mv` and never hand-edit `- Status: executed`. Commit only the declared paths through `aw commit khiueh -- <paths>`; never `git add -A`, never `-a`, never push. Backlog `iifcam` is already `graduated` and needs no further transition from this plan.

SCOPE FENCE, A DECLARATION RATHER THAN A STOP CONDITION. The six paths in `- Scope-Paths:` are what this plan expects to touch. An out-of-scope edit that execution turns out to need should be MADE and then JUSTIFIED (`aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path); do not stop the run over a scope question. The two `.review.md` files are the only RECORDS this plan may modify; both target `.ipd.md` files are HISTORY and must be byte-identical when the plan finalizes, which is the one condition an executor must treat as inviolable rather than justifiable.

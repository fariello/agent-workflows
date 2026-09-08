# IPD: Report every matched artifact's disposition instead of exiting silently on an approval-blocked queue

- Date: 2026-09-08
- Kind: orchestrator
- Concern: A run can match artifacts, act on none of them, print nothing about why, and exit 0. MEASURED 2026-08-29 (backlog `em0z50`): `aw oc run wtiso` with all 8 `wtiso` plans at `- Status: reviewed` printed only the run id, the state dir, and `No OpenCode session was captured for this run.` The run directory WAS created, `aw runs <id>` showed `8 steps: 8 reviewed` with `action=execute` and `Attempts: 0` for every row, an empty `outcomes/`, and one `run-created` event. Nothing was attempted and nothing said why.
  RE-MEASURED AT HEAD `44d4950d`, so this is live and not historical. Running the three deciding expressions against the real symbols: the queue builder's ternary (`oc_runipd.py:3011`, `agy_runipd.py:2026`) maps a `reviewed` plan to queue status `"reviewed"` rather than `"queued"`, because `reviewed` is absent from the `("to-review", "draft", "approved", "auto-approved")` tuple; `action_for("child", "reviewed")` returns `"execute"` (`runner_shared.py:2735`, delegating to `determine_action` at `:2727`); and `"reviewed" in SUCCESS_STATES` is `True` (`oc_runipd.py:327`, `agy_runipd.py:388`). So `runner_stop.deliberate_stop_exit_code(["reviewed"], success_states=SUCCESS_STATES, stopped=False)` returns `0`. `reviewed` therefore means BOTH "route to execute" and "already succeeded": a dead zone where a plan is too advanced to re-review, not approved so nothing executes it, and counted as a success anyway.
  THE SUMMARY TABLE AGREES WITH THE WRONG ANSWER, which is why no reader could have caught this. Rendering `render_run_summary_table` with one `reviewed` item at HEAD prints `Outcome: COMPLETED`, `Progress: 1/1 [##########] 100% (1 reviewed)` and no diagnostic line at all, because the COMPLETED tuple contains `reviewed` (`render_stream.py:1872`) and the diagnostics block keys on a five-status allowlist that `reviewed` is not in (`render_stream.py:2152`). A green 100% for zero work performed.
  WHY IT MATTERS NOW: plans accumulate at `reviewed` whenever the `--full-auto` reviewed->auto-approved bridge does not fire, so every later `aw oc run <set>` silently no-ops while the operator believes work is queued.
- Scope: The three separable defects backlog `em0z50` names, one per child. IN: (a) the SEMANTICS, splitting "review succeeded" from "execution succeeded" so a `reviewed`-but-unapproved execute item is neither runnable nor a success; (b) the PER-ARTIFACT LINE, so every artifact the selector matched gets one output line carrying its disposition and, when skipped, the reason; (c) the END-OF-RUN SUMMARY, enumerating every matched artifact with per-disposition counts and the exact remedy command, printed even when nothing was acted on. OUT: adding any new refusal KIND (nothing here refuses anything that is not already refused); the `Issue` column and the `--json`/`--agent` payload plumbing, which pending plan `r2i1b1` owns; the auto-approval bridge itself.
- Scope-Paths: .aw/records/plans/pending/20260908-runnoop-01-zz5yxq-split-reviewed-out-of-the-run-success-bar-so-an-approval-blo.ipd.md, .aw/records/plans/pending/20260908-runnoop-02-m85gxh-report-a-per-artifact-disposition-line-and-reason-for-every.ipd.md, .aw/records/plans/pending/20260908-runnoop-03-bsc457-print-an-end-of-run-disposition-summary-with-per-disposition.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Set: runnoop
- Order: 0
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 7ewc74
- Blocks-Release: next
- From-Backlog: em0z50

## Workflow history
- 2026-09-08 reviewed (aw set): /plan-review round 1 complete: APPROVE WITH REVISIONS APPLIED; PR-801..PR-809, all FIXED in place, no open questions remain (OQ-01 resolved from spec 25kzda). Review record written; aw ipd lint --phase review-finalize conforms.
- 2026-09-08 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-801..PR-809. Reviewed at HEAD `146905d8`. Record: `.aw/records/reviews/20260908-runnoop-00-7ewc74-report-every-matched-artifact-s-disposition-instead-of-exiti.review.md`. `aw ipd lint --phase author` conformed CLEAN with no advisory. THE DEFECT IS CONFIRMED LIVE by re-executing all five deciding expressions, not by re-reading them: `oc.SUCCESS_STATES == agy.SUCCESS_STATES` is True while `is` is False, `'reviewed' in SUCCESS_STATES` is True, `action_for('child','reviewed')` is `'execute'`, `deliberate_stop_exit_code(["reviewed"], ...)` is `0`, and calling the REAL `render_run_summary_table` with one `reviewed` item prints `Outcome: COMPLETED` with `Progress: 1/1 [##########] 100% (1 reviewed)` and ZERO diagnostic bullets. `evaluate_set_retirement(repo, 'runnoop')` returns `unfinished-children` naming all three children with no unauthored rows, so the parent's table parses and its retirement is correctly gated. THE FINDING THAT MOST CHANGES THE WORK IS PR-801: this parent's central design premise, that spec `25kzda` "already REQUIRES most of what this Set builds" and that child 01 may CHOOSE between `needs_input` and a new token, is wrong in the operator's favour but wrong. §3.2's status table is PRESCRIPTIVE for exactly this case: a `reviewed` IPD unattended MUST "Stop `needs_input`. Exact recovery names the human approval command", and §5.6's closed outcome vocabulary already contains `needs_input` ("a human gate stopped the item") while containing no `needs-approval`. So the shipped behavior is not merely under-reported, it VIOLATES an approved spec, the token is DECIDED rather than open, and OQ-01 is resolved from the spec instead of deferred to a child executor. Also corrected: `r2i1b1` is `approved` and RUNNABLE now, not `to-review` blocked on its own OQ-02 as the fence claims, which flips the overlap paragraph from hypothetical to live and makes CID-5 a real ordering obligation; the `SUCCESS_STATES` call-site counts are 6 real uses in oc and 4 in agy, not 7 and 5; the oc-to-agy import count is 43 top-level and 48 including nested, not 47, so CID-1 as written was unsatisfiable; the diagnostics allowlist is 4 statuses across 3 branches, not five; and the two hosts print DIFFERENT continuation strings, so a child pinning the oc wording on both would fail.
- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `em0z50`, which carries `- Blocks-Release: next` and whose gate this Set inherits. Every claim in the item was re-measured against HEAD `44d4950d` rather than trusted, and three of them changed the design. FIRST, the item cites `SUCCESS_STATES` at `oc_runipd.py:90`; it is at `:327` today and duplicated (not shared) at `agy_runipd.py:388` (measured `oc.SUCCESS_STATES is agy.SUCCESS_STATES` -> `False`, `==` -> `True`), so child 01 must edit BOTH and pin the equality rather than assume a shared object. SECOND, the item's fix (a) says to "audit every `SUCCESS_STATES` use"; there are SEVEN in oc and FIVE in agy and they answer DIFFERENT questions (queue admission, exit code, glyph color, continuation hint, orchestrator dispatch), so a blanket substitution is wrong and child 01 classifies each. THIRD, the item asks for the summary to stop implying a turn was attempted; the misleading line is `render_continuation_hint`'s `No OpenCode session was captured for this run.` (`oc_runipd.py:7362`, agy twin `:4568`), and its `all_success` predicate (`:7377`, `:4583`) also reads `SUCCESS_STATES`, so the footer and the resume hint are BOTH decided by the constant child 01 changes; that coupling is recorded on child 03 rather than left for an executor to trip over.
  DELIBERATE OVERLAP FENCE with pending plan `r2i1b1` (`orchprobe` Order 01): that plan owns the REFUSAL RECORD type, the `render_stream` diagnostics allowlist, and the five copies of the `aw runs` issue predicate. This Set must not define a second refusal record or a second diagnostics branch. Children 02 and 03 therefore report from the DISPOSITION the runner already computes, and child 03's summary is a NEW block rather than an edit to the existing diagnostics block. CORRECTED AT REVIEW, and the correction matters: `r2i1b1` is `- Status: approved` with `- Readiness: go-pending-approval`, its OQ-01 and OQ-02 both `resolved`, and `- Item-Dependencies: none`, so it is RUNNABLE RIGHT NOW and the whole `orchprobe` Set except `8tgg6g` is approved. The plan described it as `to-review` blocked on its own OQ-02, which was true when the fence was written and is not true now. So "if `r2i1b1` lands first" is not a hypothetical to check at the end: it is the LIKELY ordering, since `r2i1b1` is approved while this Set is not. Two consequences the children inherit. FIRST, child 03 should EXPECT to consume `r2i1b1`'s refusal record and should check for it BEFORE authoring its summary block, not merely state at validation time whether it landed. SECOND, `r2i1b1`'s declared `Scope-Paths` include `render_stream.py`, `runner_shared.py`, `oc_runipd.py` and `agy_runipd.py`, which overlap all three children here; that is not a runtime hazard (the runner isolates each item in its own worktree and merges through the revalidate gate) but it IS a review-ordering fact, so a child that finds the record already present must consume it rather than re-deriving one.

## Goal

Make a run that acts on nothing say so, per artifact and in a closing summary, and stop counting a `reviewed`-but-unapproved execute item as a success.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: drive the three children in order

- [ ] E-01 CONFIRM CHILD 01 (`zz5yxq`) IS EXECUTED before either reporting child runs. It changes what a disposition MEANS; reporting a meaning that is about to change would pin the wrong strings in tests. Read the child's `- Status:` on disk rather than trusting this table. THE TOKEN IS FIXED BEFORE THAT CHILD BEGINS: spec `25kzda` decides it is `needs_input` (OQ-01, resolved), so this confirmation includes checking that child 01 emitted the spec's token and did not invent one.
  - Depends on: none
  - Expected outcome: `zz5yxq` reads `- Status: executed` and sits in `.aw/records/plans/executed/`.
  - Execution state: pending

- [ ] E-02 CONFIRM CHILD 02 (`m85gxh`) IS EXECUTED before child 03 runs. Child 03's summary enumerates the same dispositions child 02 names per artifact; authoring the summary first would fork the vocabulary.
  - Depends on: E-01
  - Expected outcome: `m85gxh` reads `- Status: executed` and sits in `.aw/records/plans/executed/`.
  - Execution state: pending

- [ ] E-03 CONFIRM CHILD 03 (`bsc457`) IS EXECUTED and that backlog `em0z50` was closed by it, not by this parent. `em0z50` carries `- Blocks-Release: next`, so its close is gated: the closing child must carry `- From-Backlog: em0z50` and the same `- Blocks-Release: next`, which all three children do.
  - Depends on: E-02
  - Expected outcome: `bsc457` reads `- Status: executed`; backlog `em0z50` reads `- Status: done` with its gate discharged by the handoff; `aw backlog check` clean.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

All THREE children are AUTHORED and `aw ipd lint` conforming, each `to-review`. There are NO placeholder rows: an orchestrator whose table declares a row resolving to no plan refuses retirement (`unauthored-child-rows`).

| Order | Id | What it does | Depends on |
|---|---|---|---|
| 01 | `zz5yxq` | Split "review succeeded" from "execution succeeded" so a `reviewed`-but-unapproved execute item is a NEEDS-APPROVAL disposition rather than a success. Classifies all seven oc and five agy `SUCCESS_STATES` call sites instead of bulk-substituting, and pins the cross-host equality of the two duplicated constants. FIRST because it changes what a disposition MEANS, and the two reporting children pin strings against that meaning. From `em0z50` fix (a). | none |
| 02 | `m85gxh` | Emit one output line per artifact the selector MATCHED, acted on or not, in the same shape either way, carrying the reason when skipped. From `em0z50` fix (b). | `executed:zz5yxq` |
| 03 | `bsc457` | Print the end-of-run disposition summary enumerating every matched artifact with per-disposition counts and the exact remedy command, printed even when zero artifacts were acted on, and stop the continuation footer implying a turn was attempted. CLOSES backlog `em0z50`. From `em0z50` fix (c). | `executed:m85gxh` |

Hard constraints every child inherits, stated once here:

- A CHILD MUST LAND IN BOTH RUNNERS OR IN NEITHER, and any guard it adds must assert over BOTH. A one-sided guard is how `render_stream` was extracted and then re-forked in the other driver with nothing noticing (see the note at `tests/test_render_stream.py`, and the symmetric guard in `tests/test_runner_refork_guard.py`).
- NO CHILD MAY ADD A SYMBOL TO `oc_runipd` FOR AGY TO IMPORT. `agy_runipd` already imports 43 names from `oc_runipd` at top level and 48 counting five function-local ones (AST-measured at HEAD `146905d8`; the plan's earlier "47" matched neither), and zero flow the other way. A shared symbol goes in `runner_shared` or `render_stream`. Backlog `cnwy8g` owns correcting the existing coupling; no child here may increase either count.
- IF A SHARED SYMBOL MUST BE READ BY `render_stream`, IT CANNOT LIVE IN `runner_shared`. `runner_shared.py:136` imports `render_stream` at module level while `render_stream` imports ZERO first-party modules (AST-verified), so the reverse edge would be a cycle. This is not hypothetical: `r2i1b1`'s review found exactly this latent cycle and re-sited its dataclass into `render_stream` for this reason. Any child here that needs the renderer to read its disposition vocabulary must site it in `render_stream`, and must not add a first-party import there.
- NO CHILD DEFINES A REFUSAL RECORD. Pending plan `r2i1b1` owns that type, the `render_stream` diagnostics allowlist, and the five `aw runs` issue-predicate copies. Children here report from the disposition the runner already computes.
- NO CHILD WIDENS OR NARROWS A GATE. This Set changes what the runner SAYS and what it COUNTS as success. It adds no refusal and removes none. In particular child 01 must not make a `reviewed` plan executable.
- CHILDREN ARE SEQUENTIAL because of the real dependency chain above (01 fixes the vocabulary, 02 uses it per artifact, 03 aggregates it), NOT because of file overlap. The runner isolates each item in its own worktree and returns changes through the merge-and-revalidate gate, so overlap with the other Sets declaring `oc_runipd.py`/`agy_runipd.py` is not a runtime hazard and must not be reported to a human as one.

## Completion criteria (the whole Set is done only when)

- A run whose selector resolves ONLY to `reviewed`-not-approved plans does NOT count those steps as successes and does not exit 0 silently, and the item's outcome is the spec's `needs_input` token (child 01).
- The two duplicated success constants are proven EQUAL across hosts by an assertion that fails if they drift (child 01).
- Every artifact the selector MATCHED produces exactly one output line, in the same shape whether or not it was acted on, naming the skip reason when skipped (child 02).
- A run that acted on ZERO artifacts still prints the end-of-run summary, with per-disposition counts summing to the number matched and the exact remedy command for each actionable disposition (child 03).
- The continuation footer no longer reads as a launch failure when no turn was attempted, on BOTH hosts, respecting that oc and agy print DIFFERENT strings (`No OpenCode session ...` versus `No Antigravity session ...`), so the fix is parameterized on the host label rather than pinning one literal (child 03).
- Both hosts are covered by every change, asserted symmetrically (all three children).
- Backlog `em0z50` is closed by child 03 with its release gate discharged through the `- From-Backlog:` handoff (child 03).

WHICH V-ITEM OWNS EACH CRITERION, stated because a criterion no `V-*` demands evidence for is an aspiration rather than a gate. THIS PARENT'S V-ITEMS OWN ONLY ORCHESTRATION: that each child reached `executed` in the fixed order, that child 02's and child 03's deliverables demonstrably exist, and that the backlog ledger was discharged by child 03 and not by this parent. EVERY SUBSTANTIVE CRITERION IS OWNED BY A CHILD's own `V-*`, where the pre-transition E/V checkpoint is enforced. This parent does NOT re-verify any of them; citing a child's pasted evidence is the correct discharge. A criterion this parent claims without a child having recorded it is a FAILED validation, not a shortcut.

## Cross-IPD validation

- CID-1: NO NEW oc-to-agy IMPORT. The AST-measured count is 43 names at TOP LEVEL and 48 distinct names counting five that arrive through function-local imports (`build_verify_and_continue_notice`, `classify_recovery_disposition`, `enforce_dependency_preflight`, `resolve_prior_lane`, `route_recovery_turn`), across 8 `ImportFrom` sites, measured at HEAD `146905d8`. The plan's earlier figure of 47 matched NEITHER count, so a child asked to prove it "47 or lower" could not have satisfied the assertion as written. STATE WHICH COUNT YOU MEASURE and report it before and after; neither may increase. Measured by AST walk over `ImportFrom` nodes (walking the whole tree, not just `Module.body`, or the five nested ones are invisible), never by grep.
- CID-2: SYMMETRY. For every behavior any child adds, the same behavior is asserted on BOTH hosts. A test that exercises only oc is a failed CID-2 even if the code is shared, because sharing is exactly what a re-fork silently undoes.
- CID-3: ONE DISPOSITION VOCABULARY. The set of disposition tokens child 02 prints per artifact and the set child 03 counts in the summary are the SAME set, demonstrated by a test that derives both from one definition rather than by inspection.
- CID-4: NO GATE MOVED. For each child, the conditions under which the runner refuses, defers, or admits an item are unchanged. Demonstrated per child, not asserted globally.
- CID-5: NO SECOND REFUSAL RECORD. Neither child 02 nor child 03 defines a per-item refusal record type. `r2i1b1` is APPROVED and runnable while this Set is not, so assume it lands FIRST and check for its record before authoring, rather than treating this as a validation-time contingency. If the record is present, consume it; if it is absent, report that it was checked for and say what was done instead.
- CID-6: ONE SPEC VOCABULARY. The disposition token is `needs_input`, fixed by spec `25kzda` §3.2/§5.6/§11 (OQ-01, resolved). No child invents a token, and no child amends the spec to add one; a child that believes a different token is required must STOP and escalate rather than choose. Demonstrated by a test asserting the emitted token is exactly the spec's.

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN. This parent's three items each CONFIRM a child's terminal state and nothing else; no deliverable, baseline, or reconciliation lives here. The runner retires an orchestrator once every child is `executed` and deliberately SKIPS the pre-transition E/V checkpoint, so work parked on a parent is marked complete having never been performed.
- THE TWO RUNNERS ARE NOT PEERS. `agy_runipd` imports 47 names from `oc_runipd` (AST-measured 2026-09-08) while `oc_runipd` imports zero from agy, so a symbol added for both hosts must be sited in a shared module (`runner_shared` or `render_stream`), never in `oc_runipd` for agy to import. Backlog `cnwy8g` owns that layering; no child here may deepen it.
- `render_stream.py` imports NO first-party module (stdlib only), verified by AST walk. That property is what lets both runners bind one renderer, and a child that adds an import there breaks it.
- Suite bare: `python3 -m pytest`. Work in an isolated worktree; this repo has concurrent agents.

## Findings

| Id | Severity | Location (measured at HEAD `44d4950d`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `oc_runipd.py:327`, `agy_runipd.py:388` | `SUCCESS_STATES = {"executed", "reviewed", "approved"}` is used to decide a step already succeeded, and `reviewed` is a member. Duplicated per host, equal but not the same object. | `python3 -c` on both modules: `is` -> False, `==` -> True |
| F-2 | HIGH | `oc_runipd.py:3011`, `agy_runipd.py:2026` | The queue builder admits only `to-review`/`draft`/`approved`/`auto-approved` as `"queued"`; a `reviewed` plan is frozen as queue status `"reviewed"`, so it is never dispatched. | source read, both hosts |
| F-3 | HIGH | `runner_shared.py:2727`, `:2735` | `determine_action` routes everything that is not `to-review`/`draft` to `execute`, so a `reviewed` plan gets `action=execute` while being unrunnable. | `action_for("child","reviewed")` -> `'execute'` |
| F-4 | HIGH | `oc_runipd.py:7296`, `agy_runipd.py:4509` | The exit code is computed against `SUCCESS_STATES`, so an all-`reviewed` queue exits 0. | `runner_stop.deliberate_stop_exit_code(["reviewed"], success_states=SUCCESS_STATES, stopped=False)` -> `0` |
| F-5 | HIGH | `render_stream.py:1872`, diagnostics block at `:2153-2172` | The summary calls it `COMPLETED` at 100% and prints no diagnostic, confirmed by RENDERING the real function: `Outcome: COMPLETED`, `Progress: 1/1 [##########] 100% (1 reviewed)`, zero diagnostic bullets. CORRECTED AT REVIEW: the COMPLETED tuple holds FOUR statuses (`executed`, `reviewed`, `approved`, `substantially-complete`), and the diagnostics block is not a "five-status allowlist" but THREE branches covering four statuses (`dependency-blocked`; `failed-safely`/`integration-blocked`/`merge-conflict` gated on `driver_error`; `interrupted` gated on `interrupt_reason`). The `driver_error`/`interrupt_reason` GATING is the sharper point and `r2i1b1` already owns it: two of those statuses render nothing even today. | `render_run_summary_table(state)` executed with one `reviewed` item, ANSI-stripped |
| F-6 | MED | `oc_runipd.py:7562` / `:7577`, `agy_runipd.py:4574` / `:4589` | The no-session line reads as a launch failure when in fact nothing was tried, and the same function's `all_success` predicate ALSO reads `SUCCESS_STATES`, so child 01's change moves the resume hint too. THE TWO HOSTS PRINT DIFFERENT STRINGS: oc says `No OpenCode session was captured for this run.` and agy says `No Antigravity session was captured for this run.` A child that pins the oc wording on both hosts fails CID-2, and a shared fix must be parameterized on the host label rather than on a literal. Citations re-resolved (the plan's `:7362`/`:7377`/`:4568`/`:4583` had all drifted). | source read, both hosts |
| F-7 | MED | `oc_runipd.py`, `agy_runipd.py` | `SUCCESS_STATES` is consulted for DIFFERENT questions, so it cannot be changed wholesale. COUNTS CORRECTED AT REVIEW: oc has 8 textual occurrences of the bare name, of which 1 is the definition (`:336`) and 1 is inside a comment (`:4243`), leaving SIX real uses (`:3377` dependency-edge bar, `:4275` dependency-blocked sweep, `:6943` and `:6946` glyph and glyph color, `:7496` exit code, `:7577` continuation hint). agy has 5, of which 1 is the definition (`:408`), leaving FOUR (`:4013`, `:4016`, `:4515`, `:4589`). The plan said seven and five. Note oc's two extra uses are the two DEPENDENCY sites, which agy lacks entirely, so the hosts are NOT symmetric here and a child must not assume a one-to-one mapping of call sites. | regex scan excluding `EXECUTION_SUCCESS_STATES`, then each site read and classified |
| F-9 | HIGH | spec `25kzda:484`, `:1035-1042`, `:1099` | THE SHIPPED BEHAVIOR VIOLATES AN APPROVED SPEC, which is a stronger warrant than the plan claimed. §3.2's status table requires that a `reviewed` IPD unattended "Stop `needs_input`. Exact recovery names the human approval command", and forbids "Self-approval or treating model approval as human approval". §5.6's closed outcome list contains `needs_input` ("a human gate stopped the item") and no `needs-approval`. §11 repeats it. So the disposition NAME is decided by the spec, not open to a child (OQ-01 now resolved), and child 03's remedy must be the literal approval command. | spec read at the three cited sections |
| F-10 | LOW | `evaluate_set_retirement(Path('.'), 'runnoop')` | The parent's child table PARSES and declares no unauthored row: the retirement evaluator returns `unfinished-children` naming all three children with their real statuses and `unauthored_rows: ()`. So the plan's claim that all three children are authored is verified by the same predicate the runner will use, and retirement is correctly gated rather than accidentally eligible. | executed the predicate |
| F-8 | MED | `.aw/records/plans/pending/20260907-orchprobe-01-r2i1b1-...ipd.md` | A pending plan already owns the refusal RECORD, the diagnostics allowlist, and the five `aw runs` issue-predicate copies. Overlapping it would produce two vocabularies for one fact. CORRECTED AT REVIEW: that plan is now `- Status: approved`, `- Readiness: go-pending-approval`, both its open questions `resolved`, and `- Item-Dependencies: none`, so it is RUNNABLE NOW while this Set is not approved. The plan described it as `to-review` blocked on OQ-02. It is therefore LIKELY to land first, which makes CID-5 an authoring instruction for child 03 rather than a validation-time check. | that plan's front matter and open questions read at HEAD `146905d8` |

## Proposed changes (ordered, validatable)

1. Child 01 (`zz5yxq`) splits the success bar: a `reviewed` execute item is a NEEDS-APPROVAL disposition, not a success, on both hosts, with the seven-plus-five call sites classified rather than bulk-substituted.
2. Child 02 (`m85gxh`) emits one line per MATCHED artifact, acted on or not, with the skip reason.
3. Child 03 (`bsc457`) prints the end-of-run disposition summary with counts and remedies, printed even for a zero-action run, and stops the continuation footer from implying an attempt.

## Deferred / out of scope (with reason)

- Adding a new refusal KIND, a refusal RECORD type, or a diagnostics-allowlist rewrite: pending plan `r2i1b1` owns all three. This Set reports dispositions the runner already computes.
- The `aw runs` `Issue` column and the `--json`/`--agent` payload fields: also `r2i1b1` (its E-03/E-04/E-05, which extract the five duplicated predicate copies first).
- The `--full-auto` reviewed->auto-approved bridge: shipped by executed plan `97df1z`; this Set does not widen or narrow it.
- Extending the same matched-vs-acted reporting to `aw runs`, `aw ipd set`, and `aw find`, which the backlog item raises as a question. Deferred deliberately: each has its own selector semantics and its own tests, and doing them here would make an already three-child Set unreviewable. Worth a follow-on item once the driver shape is proven.
- The `i2fjf8` phantom-run-id case the backlog item names as related: that is the no-run-directory-persisted variant and is not this Set's subject.

## Scope check

- Over-scope: none. This parent edits no source file; its `Scope-Paths` are the three children it authored. Verified at review: the parent carries no deliverable, no baseline, and no reconciliation of its own, so nothing here is work the runner would mark complete having never performed it.
- Under-scope: stated rather than left as `none`. This Set does not make a refusal MACHINE-readable (that is `r2i1b1`), and does not extend the discipline to non-driver verbs (deferred above).
- Under-scope, NAMED AT REVIEW so it is not mistaken for an oversight: the two DEPENDENCY call sites of `SUCCESS_STATES` exist in oc only (`:3377`, `:4275`) and have no agy counterpart, so the hosts are asymmetric on this constant. Child 01 must classify oc's SIX real uses and agy's FOUR without assuming a one-to-one mapping, and this Set does not unify that asymmetry.

## Required tests / validation

Each child carries its own tests. This parent runs none: its three items read child status from disk. `python3 -m pytest` bare is each child's obligation, with the baseline measured in the executing worktree and failing NODE IDS compared, never totals.

## Spec / documentation sync

Spec `25kzda` (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, `- Status: approved`) governs this surface, and REVIEW FOUND IT MORE PRESCRIPTIVE THAN THIS PLAN ORIGINALLY STATED. The plan said §5.6 "already REQUIRES most of what this Set builds" and left the disposition's NAME to child 01 as an open choice. Both halves understate the spec.

WHAT §3.2 ACTUALLY REQUIRES, and it decides the whole Set. Its per-status action table has a row for exactly this case: for a `reviewed` IPD, the UNATTENDED action is "Stop `needs_input`. Exact recovery names the human approval command", and the FORBIDDEN unattended action is "Self-approval or treating model approval as human approval" (spec `:484`). So the shipped behavior is not merely under-reported: a `reviewed` item that is silently counted as a success and exits 0 VIOLATES an approved spec requirement, and it does so on the exact axis this Set fixes. That is a stronger warrant than "moves the code toward the spec", and it is the sentence a reviewer of child 01 should be checking against.

WHAT §5.6 DECIDES, so no child has to. Its allowed per-item outcomes are a CLOSED list, `verified`/`ran`/`failed`/`skipped`/`needs_input`/`cancelled` (spec `:1035-1042`), and `needs_input` is glossed exactly as "a human gate stopped the item". §3.2 already NAMES that token for the `reviewed` case, and §11's summary table repeats it ("Reviewed IPD ... otherwise `needs_input`", spec `:1099`). A `needs-approval` token appears nowhere in the spec. THEREFORE the name is DECIDED, not open: use `needs_input`, no spec amendment is required, and no child declares the spec file in its `Scope-Paths`. See OQ-01, now resolved. If a child believes a different token is required, that is a spec amendment and a maintainer decision, not an executor's call.

Note the spec's §4.2 finding-code table must not be edited: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` under a byte-equality test.

ONE THING THAT REMAINS TO CHECK RATHER THAN ASSUME: §5.6 also mandates the final table carry a `reason code` and a `next command` per item, and §3.2 requires the recovery to name "the human approval command" EXACTLY. Child 03's remedy command must therefore be the literal approval command for the item, not a generic pointer; whichever child emits it should quote §3.2's requirement in its own validation rather than inventing wording.

## Open questions

### OQ-01: Does the new needs-approval disposition take the spec's `needs_input` name or a new one?

- Blocking: no
- Status: resolved
- Owner: reviewer (resolved at review 2026-09-08 from the approved spec)
- Resolution or deferral rationale: RESOLVED FROM THE SPEC, and it was never actually a choice. The question framed both options as "defensible", but spec `25kzda` names the token for THIS EXACT CASE in three places: §3.2's status table says a `reviewed` IPD unattended must "Stop `needs_input`. Exact recovery names the human approval command" (`:484`); §5.6's allowed per-item outcomes are a CLOSED list containing `needs_input` glossed as "a human gate stopped the item" (`:1035-1042`); and §11's summary repeats "Reviewed IPD ... otherwise `needs_input`" (`:1099`). `needs-approval` appears nowhere in the spec. USE `needs_input`. No amendment, no spec file in any child's `Scope-Paths`. This is recorded here rather than left to child 01 because leaving a spec-decided name to an executor invites a third vocabulary, which is the outcome the question itself warned against, and because CID-3 requires child 02's and child 03's vocabularies to be the same set derived from one definition; that definition is now fixed. If a child concludes a different token is genuinely required, that is a spec amendment and a maintainer decision, and it must STOP rather than invent one.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste child `zz5yxq`'s `- Status:` line and its path, read at validation time, showing `executed` and `.aw/records/plans/executed/`. Paste `aw ipd lint --phase post-transition` for that child reporting conforming (NOT `pre-transition`: once the plan is `executed` the pre-transition checkpoint no longer applies to it, so the plan's earlier instruction named a phase that cannot pass on a terminal file). ALSO paste the child's own V-item evidence for the `needs_input` token, cited rather than re-run, so the spec-fixed vocabulary is demonstrably what landed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste child `m85gxh`'s `- Status:` line and path showing `executed`. Paste one real per-artifact line from a run whose selector matched an item it did not act on, demonstrating the child's deliverable exists rather than only that its file moved. Paste the same line from BOTH hosts, or cite the child's own symmetric evidence, since CID-2 is a Set-level obligation and a one-host demonstration discharges nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste child `bsc457`'s `- Status:` line and path showing `executed`; paste the end-of-run summary from a run that acted on ZERO artifacts, showing the counts and the remedy command; paste backlog `em0z50`'s `- Status:` line showing `done` and name WHICH child closed it; paste `aw backlog check` clean. ALSO state whether `r2i1b1` has landed (it was `approved` and runnable at review, so expect YES) and paste proof child 03 consumed its refusal record rather than adding a parallel one. ALSO paste evidence the release gate was DISCHARGED THROUGH THE HANDOFF rather than dropped: `em0z50` carries `- Blocks-Release: next`, and `aw backlog set done` fails closed unless a plan carrying `- From-Backlog: em0z50` also carries the same `- Blocks-Release: next`; all three children do, so name which one satisfied the predicate and paste the setter's output rather than a hand-edit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: this parent commits nothing and edits no source file. Each child commits ONLY the files it changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved 7ewc74 --by-human --message ...`) before execution. The `- Readiness: go-pending-approval` field now present was written by `/plan-review` on 2026-09-08 as its attested output; do not hand-edit it. Note the three CHILDREN each need their own approval too: this parent's approval is not theirs, and `evaluate_set_retirement` reads each child's on-disk `- Status:`, so an approved parent with `to-review` children retires nothing (measured: it returns `unfinished-children` naming all three).

KNOW WHAT THE RUNNER WILL AND WILL NOT CHECK ON THIS PARENT, because it decides how much weight the V-items above carry. Retirement performs every gate in `ipd_lifecycle.ROLLUP_SHARED_GATES` (worker-role refusal, actor and message, early crash recovery, the exclusive finalize lock, the transaction journal, status legality, the plan move, the fail-loud index refresh, the commit, the post-transition lint) and deliberately OMITS exactly three, the first being `pre-transition-ev-checkpoint`, on the recorded ground that an orchestrator's items are "performed by NOBODY". So the three V-items above will NOT be machine-verified when the runner retires this plan. That is correct by design and it is also why they must stay purely evidentiary citations of the children's own gates: a claim written here is never checked. If a human retires the Set by hand, work the three E-items in order and actually paste the evidence.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN, including the corrected ones. Review re-resolved every citation and found the plan's `SUCCESS_STATES` (`:327`/`:388` -> `:336`/`:408`), the queue ternary (`:3011`/`:2026` -> `:2979`/`:2012`), the continuation hint (`:7362`/`:7377`/`:4568`/`:4583` -> `:7562`/`:7577`/`:4574`/`:4589`), and the diagnostics block (`:2152` -> `:2153`) had ALL drifted within a day. Find `SUCCESS_STATES`, `render_continuation_hint`, `render_run_summary_table`, `determine_action`, and the `# Failure / Dependency block diagnostics` comment by name.

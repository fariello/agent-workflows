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
- Status: to-review
- Set: runnoop
- Order: 0
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 7ewc74
- Blocks-Release: next
- From-Backlog: em0z50

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `em0z50`, which carries `- Blocks-Release: next` and whose gate this Set inherits. Every claim in the item was re-measured against HEAD `44d4950d` rather than trusted, and three of them changed the design. FIRST, the item cites `SUCCESS_STATES` at `oc_runipd.py:90`; it is at `:327` today and duplicated (not shared) at `agy_runipd.py:388` (measured `oc.SUCCESS_STATES is agy.SUCCESS_STATES` -> `False`, `==` -> `True`), so child 01 must edit BOTH and pin the equality rather than assume a shared object. SECOND, the item's fix (a) says to "audit every `SUCCESS_STATES` use"; there are SEVEN in oc and FIVE in agy and they answer DIFFERENT questions (queue admission, exit code, glyph color, continuation hint, orchestrator dispatch), so a blanket substitution is wrong and child 01 classifies each. THIRD, the item asks for the summary to stop implying a turn was attempted; the misleading line is `render_continuation_hint`'s `No OpenCode session was captured for this run.` (`oc_runipd.py:7362`, agy twin `:4568`), and its `all_success` predicate (`:7377`, `:4583`) also reads `SUCCESS_STATES`, so the footer and the resume hint are BOTH decided by the constant child 01 changes; that coupling is recorded on child 03 rather than left for an executor to trip over.
  DELIBERATE OVERLAP FENCE with pending plan `r2i1b1` (`orchprobe` Order 01, `to-review`, blocked on its own OQ-02): that plan owns the REFUSAL RECORD type, the `render_stream` diagnostics allowlist, and the five copies of the `aw runs` issue predicate. This Set must not define a second refusal record or a second diagnostics branch. Children 02 and 03 therefore report from the DISPOSITION the runner already computes, and child 03's summary is a NEW block rather than an edit to the existing diagnostics block. If `r2i1b1` lands first, child 03 must consume its record instead of adding a parallel one; V-03 requires that be checked and stated rather than assumed.

## Goal

Make a run that acts on nothing say so, per artifact and in a closing summary, and stop counting a `reviewed`-but-unapproved execute item as a success.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: drive the three children in order

- [ ] E-01 CONFIRM CHILD 01 (`zz5yxq`) IS EXECUTED before either reporting child runs. It changes what a disposition MEANS; reporting a meaning that is about to change would pin the wrong strings in tests. Read the child's `- Status:` on disk rather than trusting this table.
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
- NO CHILD MAY ADD A SYMBOL TO `oc_runipd` FOR AGY TO IMPORT. `agy_runipd` already imports 47 names from `oc_runipd` (AST-measured 2026-09-08) and zero flow the other way. A shared symbol goes in `runner_shared` or `render_stream`. Backlog `cnwy8g` owns correcting the existing 47; no child here may make it 48.
- NO CHILD DEFINES A REFUSAL RECORD. Pending plan `r2i1b1` owns that type, the `render_stream` diagnostics allowlist, and the five `aw runs` issue-predicate copies. Children here report from the disposition the runner already computes.
- NO CHILD WIDENS OR NARROWS A GATE. This Set changes what the runner SAYS and what it COUNTS as success. It adds no refusal and removes none. In particular child 01 must not make a `reviewed` plan executable.
- CHILDREN ARE SEQUENTIAL because of the real dependency chain above (01 fixes the vocabulary, 02 uses it per artifact, 03 aggregates it), NOT because of file overlap. The runner isolates each item in its own worktree and returns changes through the merge-and-revalidate gate, so overlap with the other Sets declaring `oc_runipd.py`/`agy_runipd.py` is not a runtime hazard and must not be reported to a human as one.

## Completion criteria (the whole Set is done only when)

- A run whose selector resolves ONLY to `reviewed`-not-approved plans does NOT count those steps as successes and does not exit 0 silently (child 01).
- The two duplicated success constants are proven EQUAL across hosts by an assertion that fails if they drift (child 01).
- Every artifact the selector MATCHED produces exactly one output line, in the same shape whether or not it was acted on, naming the skip reason when skipped (child 02).
- A run that acted on ZERO artifacts still prints the end-of-run summary, with per-disposition counts summing to the number matched and the exact remedy command for each actionable disposition (child 03).
- The continuation footer no longer reads as a launch failure when no turn was attempted (child 03).
- Both hosts are covered by every change, asserted symmetrically (all three children).
- Backlog `em0z50` is closed by child 03 with its release gate discharged through the `- From-Backlog:` handoff (child 03).

WHICH V-ITEM OWNS EACH CRITERION, stated because a criterion no `V-*` demands evidence for is an aspiration rather than a gate. THIS PARENT'S V-ITEMS OWN ONLY ORCHESTRATION: that each child reached `executed` in the fixed order, that child 02's and child 03's deliverables demonstrably exist, and that the backlog ledger was discharged by child 03 and not by this parent. EVERY SUBSTANTIVE CRITERION IS OWNED BY A CHILD's own `V-*`, where the pre-transition E/V checkpoint is enforced. This parent does NOT re-verify any of them; citing a child's pasted evidence is the correct discharge. A criterion this parent claims without a child having recorded it is a FAILED validation, not a shortcut.

## Cross-IPD validation

- CID-1: NO NEW oc-to-agy IMPORT. The AST-measured count of names `agy_runipd` imports from `oc_runipd` is 47 before this Set and must be 47 or lower after. Measured by AST walk over `ImportFrom` nodes, not grep.
- CID-2: SYMMETRY. For every behavior any child adds, the same behavior is asserted on BOTH hosts. A test that exercises only oc is a failed CID-2 even if the code is shared, because sharing is exactly what a re-fork silently undoes.
- CID-3: ONE DISPOSITION VOCABULARY. The set of disposition tokens child 02 prints per artifact and the set child 03 counts in the summary are the SAME set, demonstrated by a test that derives both from one definition rather than by inspection.
- CID-4: NO GATE MOVED. For each child, the conditions under which the runner refuses, defers, or admits an item are unchanged. Demonstrated per child, not asserted globally.
- CID-5: NO SECOND REFUSAL RECORD. Neither child 02 nor child 03 defines a per-item refusal record type; if `r2i1b1` has landed, they consume its record.

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
| F-5 | HIGH | `render_stream.py:1872`, `:2152` | The summary calls it `COMPLETED` at 100% and prints no diagnostic, because `reviewed` is in the COMPLETED tuple and absent from the five-status diagnostics allowlist. | rendered the real function with one `reviewed` item |
| F-6 | MED | `oc_runipd.py:7362` / `:7377`, `agy_runipd.py:4568` / `:4583` | `No OpenCode session was captured for this run.` reads as a launch failure when in fact nothing was tried, and the same function's `all_success` predicate ALSO reads `SUCCESS_STATES`, so child 01's change moves the resume hint too. | source read, both hosts |
| F-7 | MED | `oc_runipd.py` seven sites, `agy_runipd.py` five | `SUCCESS_STATES` is consulted for five DIFFERENT questions (queue admission, exit code, glyph, continuation hint, orchestrator dispatch bar), so it cannot be changed wholesale. | grep of both modules, classified per call site |
| F-8 | MED | `.aw/records/plans/pending/20260907-orchprobe-01-r2i1b1-...ipd.md` | A pending plan already owns the refusal RECORD, the diagnostics allowlist, and the five `aw runs` issue-predicate copies. Overlapping it would produce two vocabularies for one fact. | read that plan's E-01..E-05 |

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

- Over-scope: none. This parent edits no source file; its `Scope-Paths` are the three children it authored.
- Under-scope: stated rather than left as `none`. This Set does not make a refusal MACHINE-readable (that is `r2i1b1`), and does not extend the discipline to non-driver verbs (deferred above).

## Required tests / validation

Each child carries its own tests. This parent runs none: its three items read child status from disk. `python3 -m pytest` bare is each child's obligation, with the baseline measured in the executing worktree and failing NODE IDS compared, never totals.

## Spec / documentation sync

Spec `25kzda` (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, `- Status: approved`) governs the run's reporting surface, and its §5.6 already REQUIRES most of what this Set builds: "The final table includes position, ID/path, type, starting status, action trace, final item state, verification state, reason code, commit(s), and next command", and it enumerates allowed per-item outcomes including `skipped` "no execution was appropriate for the current valid state". So children 02 and 03 move the shipped code TOWARD the approved spec rather than amending it.
ONE THING TO CHECK RATHER THAN ASSUME, and it is child 01's to decide: §5.6's outcome vocabulary is `verified`/`ran`/`failed`/`skipped`/`needs_input`/`cancelled`, which does NOT include a `needs-approval` token, while the shipped runner's vocabulary is the `TERMINAL_STATES` set. If child 01's new disposition needs a name the spec does not have, either map it onto the spec's `needs_input` (whose §5.6 gloss is "a human gate stopped the item", which fits exactly) or amend §5.6 and declare that spec file in child 01's `- Scope-Paths:`. Do NOT invent a third vocabulary silently. Note the spec's §4.2 finding-code table must not be edited: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` under a byte-equality test.

## Open questions

### OQ-01: Does the new needs-approval disposition take the spec's `needs_input` name or a new one?

- Blocking: no
- Status: open
- Owner: child 01 (`zz5yxq`) executor, with the maintainer if a spec amendment is needed
- Resolution or deferral rationale: NOT blocking this parent, because the parent performs no work; it is child 01's first decision and is recorded there as that child's own OQ. Spec `25kzda` §5.6's `needs_input` ("a human gate stopped the item") is a precise fit and requires no amendment, which is the cheaper answer; a new token requires amending §5.6 and declaring the spec in child 01's `Scope-Paths`. Either is defensible; inventing a token that appears in neither the spec nor `TERMINAL_STATES` is not.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste child `zz5yxq`'s `- Status:` line and its path, read at validation time, showing `executed` and `.aw/records/plans/executed/`. Paste `aw ipd lint --phase pre-transition` for that child reporting conforming.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste child `m85gxh`'s `- Status:` line and path showing `executed`. Paste one real per-artifact line from a run whose selector matched an item it did not act on, demonstrating the child's deliverable exists rather than only that its file moved.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste child `bsc457`'s `- Status:` line and path showing `executed`; paste the end-of-run summary from a run that acted on ZERO artifacts, showing the counts and the remedy command; paste backlog `em0z50`'s `- Status:` line showing `done` and name WHICH child closed it; paste `aw backlog check` clean. ALSO state whether pending plan `r2i1b1` has landed, and if it has, paste proof that child 03 consumed its refusal record rather than adding a parallel one.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: this parent commits nothing and edits no source file. Each child commits ONLY the files it changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved 7ewc74 --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field. The runner retires this orchestrator automatically once all three children read `executed` on disk; if a human executes the Set by hand instead, work the three E-items above in order.

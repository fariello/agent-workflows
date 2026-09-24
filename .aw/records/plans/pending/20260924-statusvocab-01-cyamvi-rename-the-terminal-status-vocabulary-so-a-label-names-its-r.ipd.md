# IPD: Rename the terminal status vocabulary so a label names its refusing authority

- Date: 2026-09-24
- Kind: child
- Concern: THE RUN SUMMARY REPORTS "COMPLETE" FOR WORK THAT IS NOWHERE, AND AN OPERATOR CANNOT TELL THAT FROM SUCCESS. Measured on run `run-20260924T050407Z-3108751` (28 items): `substantially-complete` was reported for BOTH `xdvglg`, whose 6 of 6 items were genuinely performed and whose work landed once a stale receipt was re-issued, AND `7p3tt8`, which performed ZERO of 5 items and whose validation evidence was empty. One word, two opposite outcomes. Meanwhile `failed-safely` was reported for `m7gvuz`, the only plan in the run that behaved impeccably: it REFUSED ITSELF rather than tick a V-item it could not honor, and its work landed unchanged. The word an operator reads is therefore anti-correlated with what happened. THE MEASURED PREDICTOR is the plan's directory on disk: across all 28 items, `executed` predicted "in `main`" with no false positives and no false negatives, while every other label was uninformative about it. THE CONCRETE HARM IS NOT COSMETIC: `substantially-complete` is a member of `runner_shared.EXECUTION_SUCCESS_STATES`, which is the DEPENDENCY BAR that `edge_satisfied` consults, so a plan whose work never reached `main` can today satisfy another plan's `executed:` prerequisite. `runner_shared` already records the measured cost of exactly that class of defect in its own comment at `edge_satisfied`'s `executed` branch (run `run-20260919T194413Z-2056285`: `yaxr4i` finished outside `main`, `n4xq3l` was told its edge was met, dispatched into a tree with none of that work, and cascaded `dependency-blocked` to eight more items for "2h 10m and $55.02 for nothing integrated"). `artifact_audit` independently collapses the distinction in code, mapping `substantially-complete` to the literal string `complete` before choosing an expected directory, which is the same conflation expressed as a data transformation.
- Scope: Replace the eleven-value terminal status vocabulary with a ten-value one in which every non-`executed` label NAMES THE AUTHORITY THAT REFUSED, so the label answers "is it in `main`, and whose output do I read next". Renames `substantially-complete`/`blocked` -> `fail-gate`, `partial` -> `fail-verify`, `failed-safely` -> `fail-gate`, `dependency-blocked` -> `fail-depend`, `integration-blocked`/`merge-conflict`/`merge-needs-human`/`merge-refused` -> `fail-merge`, `not-attempted` -> `not-run`, and PROMOTES the already-shipped `runner_stop.STOPPED_DISPOSITION` (`interrupted`) into `TERMINAL_STATES`, which it is missing from today. Adds `failed` as the explicitly-named residual. REMOVES the renamed `substantially-complete` from `EXECUTION_SUCCESS_STATES`, which is a BEHAVIOR change and the reason this plan needs a spec amendment rather than a rename commit. EVERY READING SITE ACCEPTS BOTH VOCABULARIES PERMANENTLY, following the precedent `l2mzxn` set and for the same measured reason. IN: the shared vocabulary module, both runner hosts, the eleven reader modules, the viewer and attention surfaces, every test that pins a status literal, the seven specs that name one, and the `.aw/records/runs/` back-compatibility path. OUT: changing WHICH gate refuses what, changing any refusal message beyond the status token it carries, and rewriting historical run records or plan records in place.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/agy_runipd.py, agent_workflows/oc_runipd.py, agent_workflows/artifact_audit.py, agent_workflows/attention.py, agent_workflows/ipd_lint.py, agent_workflows/ipd_schema.py, agent_workflows/lifecycle_style.py, agent_workflows/run_cli.py, agent_workflows/run_engine.py, agent_workflows/run_recovery.py, agent_workflows/run_selection_policy.py, agent_workflows/run_state.py, agent_workflows/run_viewer.py, agent_workflows/runner_shutdown.py, agent_workflows/runner_stop.py, agent_workflows/render_stream.py, tests/, .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md, .aw/records/specs/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md, .aw/records/specs/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md, .aw/records/specs/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md, .aw/records/specs/20260912-6kwd2e-01-6kwd2e-midrun-question-surfacing.spec.md, .aw/records/specs/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md, .aw/records/specs/20260920-i4gpto-01-i4gpto-standalone-executed-plan-audit.spec.md
- Item-Dependencies: none
- Status: to-review
- Set: statusvocab
- Order: 1
- Highest E allocated: 09
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: cyamvi

## Workflow history

- 2026-09-24 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.
- 2026-09-24 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): authored from a maintainer-designed vocabulary. The maintainer specified the ten labels and rejected a two-column (landed + needs) design on the measured ground that no terminal state can be cleared without a human, so a second column would always read the same value and carry no information. Verified in code before accepting: the zero-work retry path requeues with `recovery_next` BEFORE terminality, so by the time any terminal label is displayed its budget is spent. Two corrections were made to the maintainer's draft list and are recorded in Findings: `fail-depend` and `not-run` overlapped, and `unknown` and `failed` were one bucket.

## Goal

Make the word an operator reads in `aw runs` answer the only two questions they have: is this work in `main`, and if not, whose output do I read next. Today the answer to the first is knowable only by listing `.aw/records/plans/executed/` by hand, and the answer to the second is not in the vocabulary at all.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: define the vocabulary once, then move every site to it

- [ ] E-01 DEFINE THE NEW VOCABULARY AND THE OLD-TO-NEW MAP IN ONE SHARED PLACE, in `runner_shared`, as data rather than as scattered comparisons. Add `TERMINAL_STATUS_ALIASES`, a mapping from every legacy token to its replacement, and `TERMINAL_STATES_CANONICAL`, the ten-value target set. DERIVE the existing `TERMINAL_STATES` as the union of both so nothing that reads it narrows. THE MAP IS THE DELIVERABLE: every later item consumes it rather than re-spelling a rename, which is what stops this landing half-done. Both hosts must re-export the same objects, per `cnwy8g`'s layering rule, and `tests/test_runner_refork_guard.py` must see one object and not two copies.
  - Depends on: none
  - Expected outcome: `runner_shared.TERMINAL_STATUS_ALIASES` maps all eleven legacy tokens; `oc.TERMINAL_STATES is agy.TERMINAL_STATES is runner_shared.TERMINAL_STATES` is True; no behavior changes yet.
  - Execution state: pending

- [ ] E-02 MAKE EVERY READER ACCEPT BOTH VOCABULARIES, PERMANENTLY, BEFORE ANY WRITER EMITS A NEW TOKEN. There are ELEVEN modules that read a status string (`grep -rl "TERMINAL_STATES\|EXECUTION_SUCCESS_STATES" agent_workflows/*.py`), and `.aw/records/runs/` IS GITIGNORED AND DURABLE, so a run directory written before this plan still carries the legacy spelling forever and a fresh clone has none of them to migrate. This is exactly the constraint `l2mzxn` met by listing BOTH spellings in `TERMINAL_STATES` with the comment "a pre-rename run directory still carries the old strings, and terminality must not depend on which vocabulary wrote the file". Normalize through the E-01 map at the READ boundary; do NOT add per-call-site comparisons.
  - Depends on: E-01
  - Expected outcome: every reader classifies a legacy token identically to its replacement; a synthetic run directory containing each of the eleven legacy tokens is read without error by `aw runs` and by `aw attention`.
  - Execution state: pending

- [ ] E-03 SWITCH THE WRITERS IN BOTH HOSTS TO EMIT THE CANONICAL TOKENS, which is the only item that changes what a new run records. `reconcile_disposition` in each host is the primary site; `runner_stop.STOPPED_DISPOSITION` already emits `interrupted` and needs no change, only promotion into the terminal set (E-04). Emit `fail-verify` where the verifier refused, `fail-gate` where a lifecycle gate refused, `fail-merge` where integration refused, `fail-depend` for an unmet prerequisite, `not-run` for never-reached, and `failed` only where none of the above applies.
  - Depends on: E-02
  - Expected outcome: a fresh run records only canonical tokens; the two hosts' mapping from cause to token is byte-identical, asserted by object identity rather than by parallel literals.
  - Execution state: pending

- [ ] E-04 PROMOTE `interrupted` INTO `TERMINAL_STATES`, WHICH IS A BUG FIX AND NOT PART OF THE RENAME. `runner_stop.STOPPED_DISPOSITION` is already the literal `interrupted` and is already returned by `reconcile_disposition`'s deliberate-stop branch, but the token is ABSENT from `TERMINAL_STATES`, so a deliberately stopped item is not recognized as terminal by anything that consults that set. Spec `c4gd2h` R21 forbids conflating a deliberate stop with breakage (`agy_runipd` records this verbatim as "the intent-versus-breakage conflation R21 forbids"), so the omission is a live gap in the very rule the code cites.
  - Depends on: E-01
  - Expected outcome: `interrupted` is in `TERMINAL_STATES`; a stopped item is terminal to every consumer; R21's distinction is preserved with `interrupted` separate from `fail-gate`.
  - Execution state: pending

### Task group 2: the behavior change, isolated so it can be reviewed on its own

- [ ] E-05 REMOVE THE RENAMED `substantially-complete` FROM `EXECUTION_SUCCESS_STATES`, AND DO IT AS ITS OWN ITEM BECAUSE IT IS THE ONLY BEHAVIOR CHANGE IN THIS PLAN. That set is the DEPENDENCY BAR read by `edge_satisfied`, so today a plan whose work never reached `main` can satisfy another plan's `executed:` prerequisite. After this item the bar is `{executed}` alone. THE DIRECTION OF RISK IS STATED: plans currently unblocked by a `substantially-complete` sibling will correctly stop being unblocked, which may mark items `fail-depend` that previously dispatched. That is the intended correction and it is the same failure `runner_shared` already documents costing "2h 10m and $55.02 for nothing integrated".
  - Depends on: E-03
  - Expected outcome: `EXECUTION_SUCCESS_STATES == {"executed"}`; an item whose prerequisite is `fail-gate` is `fail-depend` rather than dispatched; the legacy spelling maps to `fail-gate` and so is equally refused.
  - Execution state: pending

- [ ] E-06 FIX `artifact_audit`'s DATA-LEVEL CONFLATION, which is the same defect expressed as a transformation rather than as a word. It computes `st = "complete" if status == "substantially-complete" else status` before choosing an expected directory, i.e. it silently treats a plan whose work is stranded as complete. Replace it with a lookup through the E-01 map so a stranded status expects `pending/`, which is where such a plan actually sits.
  - Depends on: E-01
  - Expected outcome: no `"complete"` coercion remains in `artifact_audit`; a `fail-gate` item's expected directory is `pending/`; the audit flags rather than excuses a stranded plan.
  - Execution state: pending

### Task group 3: make a partial landing impossible to ship

- [ ] E-07 ADD AN EXHAUSTIVENESS GUARD THAT FAILS ON ANY UNMAPPED OR UNRENAMED TOKEN ANYWHERE IN THE TREE. This item exists because the recurring failure mode in this repository is a rename that reaches code and misses tests, docs, or one reader. Scan `agent_workflows/`, `tests/`, `.aw/records/specs/`, and the tracked markdown for every quoted legacy token, and assert each occurrence is either (a) inside the E-01 alias map, (b) inside an explicitly listed back-compatibility site, or (c) inside a historical record this plan must not rewrite. MEASURED SURFACE THE GUARD MUST COVER, counted as quoted string literals: `substantially-complete` 31 code / 81 tests, `partial` 39 / 94, `failed-safely` 32 / 88, `blocked` 83 / 112, `dependency-blocked` 30 / 48, `not-attempted` 14 / 15, `integration-blocked` 21 / 9, `merge-conflict` 20 / 7, `merge-needs-human` 16 / 28, `merge-refused` 16 / 40. The guard is what makes "we did not end up with a partial update" a checkable claim rather than an assurance.
  - Depends on: E-03, E-06
  - Expected outcome: the guard FAILS on the pre-E-03 tree naming the exact sites, and PASSES after; it is non-vacuous, demonstrated by re-introducing one legacy literal and observing a named failure.
  - Execution state: pending

- [ ] E-08 UPDATE THE SEVEN SPECS THAT NAME A LEGACY TOKEN, because a spec is the contract every other plan is reviewed against and a stale one silently re-authorizes the old vocabulary. The seven, measured: `aw-run-deterministic-run-and-verify` (`0718`), `77tr3o` runner-orchestrator-retirement, `7ckptx` worker-lane-containment, `uonrjg` cross-artifact-lifecycle-symbols, `6kwd2e` midrun-question-surfacing, `z7nbn1` universal-artifact-dispatch, `i4gpto` standalone-executed-plan-audit. State in each amendment that legacy tokens remain READABLE forever and are no longer WRITTEN, so a reader cannot conclude the old spelling is invalid input.
  - Depends on: E-03
  - Expected outcome: no spec names a legacy token as a value a runner writes; each amended spec carries the read-versus-write distinction; `aw specs check` conforming.
  - Execution state: pending

- [ ] E-09 ADD THE `Landed` COLUMN TO THE RUN SUMMARY TABLE, computed from the plan's directory on disk and never from a self-report. This is the operator-facing half of the concern: the table today has `Status`, `Item`, `Action`, `Verified` and `Issue` columns and NONE that answers "did this reach `main`". Derive it from the terminal directory, which is the one signal no agent can assert, and which measured as a perfect predictor across all 28 items of the cited run.
  - Depends on: E-03
  - Expected outcome: `aw runs` shows `Landed` per item; its value for every item of a replayed historical run agrees with whether that plan is in `executed/` today.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A RENAME IN THIS REPOSITORY KEEPS BOTH SPELLINGS FOREVER, and the precedent is explicit: `agy_runipd`'s `TERMINAL_STATES` lists `merge-needs-human` and `merge-refused` beside `integration-blocked` and `merge-conflict` under the comment "The post-rename spellings (`l2mzxn`). BOTH are listed: a pre-rename run directory still carries the old strings, and terminality must not depend on which vocabulary wrote the file." `attention` carries the same note at two sites. This plan follows that convention rather than inventing a migration.
- `.aw/records/runs/` IS GITIGNORED (`.aw/.gitignore` names `records/runs/`), which is what makes the above non-negotiable: historical run records cannot be migrated because they are not tracked, and a fresh clone has none of them at all. A reader that only understands the new vocabulary would be correct on a fresh clone and wrong on the maintainer's machine.
- THE SHARED-DEFINITION RULE, from backlog `cnwy8g` and spec `7ckptx` R2.6: a driver-consumed rule lives in one shared module and both hosts BIND the same object. `EXECUTION_SUCCESS_STATES` records in its own comment that each host once declared its own set literal so the two were "EQUAL BUT NOT IDENTICAL, and a one-sided edit was silent". The alias map must not repeat that mistake.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- F-01 THE VOCABULARY IS ANTI-CORRELATED WITH REALITY, not merely imprecise. Measured on run `run-20260924T050407Z-3108751`: the same token `substantially-complete` described `xdvglg` (6/6 items performed, work real, landed) and `7p3tt8` (0/5 items performed, empty evidence), while `failed-safely` described `m7gvuz`, which refused itself correctly and whose work landed unchanged. An operator scanning that table would triage the three in the wrong order.
- F-02 `executed` IS ALREADY A PERFECT PREDICTOR and needs no change. Across all 28 items of that run, membership in `.aw/records/plans/executed/` matched the `executed` status exactly. The fix is therefore additive to the good state and corrective only to the others.
- F-03 TWO CORRECTIONS TO THE MAINTAINER'S DRAFT LIST, both accepted. (1) `fail-depend` and `not-run` overlapped: the draft defined `fail-depend` as "dependency not met" while listing `dependency-blocked` as an example of `not-run`. Resolved by keeping `fail-depend` for an unmet prerequisite (it names the cause) and reserving `not-run` for never-reached. (2) `unknown` and `failed` were one bucket ("issue not covered by other labels" versus "broken in a way none of the above covers"). Resolved by keeping `failed` and dropping `unknown`, because an explicitly-named residual invites correct use while `unknown` invites a dumping ground, which is precisely how `substantially-complete` lost its meaning.
- F-04 THE TWO-COLUMN DESIGN WAS REJECTED ON EVIDENCE, and the maintainer's reasoning checks out in code. A `Needs` column (`none`/`retry`/`human`) would always read `human` at terminality, because the automatic retry paths (`zero-work-retry`, `requeue_interrupted`) requeue with `recovery_next` BEFORE an item becomes terminal, so a displayed terminal label has already exhausted its budget. A column with one possible value carries no information.
- F-05 `interrupted` IS ALREADY IMPLEMENTED AND MERELY UNREGISTERED. `runner_stop.STOPPED_DISPOSITION == "interrupted"` and `reconcile_disposition` returns it, but `TERMINAL_STATES` omits it, so nothing that consults the set treats a deliberate stop as terminal. This is a pre-existing bug this plan fixes in passing (E-04), not a new label.
- F-06 THE DEPENDENCY BAR IS THE REAL DEFECT, and it is documented in the codebase already. `EXECUTION_SUCCESS_STATES = {executed, substantially-complete}` is read by `edge_satisfied`, whose own comment records the measured cost of admitting a non-landed prerequisite: run `run-20260919T194413Z-2056285`, `yaxr4i` outside `main`, `n4xq3l` dispatched into a tree without that work, eight items cascaded, "2h 10m and $55.02 for nothing integrated". The maintainer already removed the in-run status shortcut for this reason on 2026-09-19; this plan removes the remaining half.

## Proposed changes (ordered, validatable)

1. E-01 define the canonical set and the alias map in `runner_shared`, bound by both hosts.
2. E-02 normalize at every read boundary so both vocabularies classify identically, before any writer changes.
3. E-03 switch both hosts' writers to the canonical tokens.
4. E-04 register `interrupted` as terminal.
5. E-05 narrow `EXECUTION_SUCCESS_STATES` to `{executed}` (the behavior change).
6. E-06 remove `artifact_audit`'s `"complete"` coercion.
7. E-07 add the tree-wide exhaustiveness guard.
8. E-08 amend the seven specs.
9. E-09 add the `Landed` column.

## Deferred / out of scope (with reason)

- Changing WHICH gate refuses what, or any refusal message beyond the status token it carries: this plan renames outcomes, it does not move gates. A reader comparing refusal text before and after should see the same sentences.
- Rewriting historical run directories or the `Workflow history` of existing plan records: run directories are gitignored and unmigratable, and editing a past history entry would assert a transition that did not happen in the words it was recorded in.
- Collapsing `reviewed` and `approved`: they answer a different question (did a review or approval action finish) and are members of `SUCCESS_STATES`, not of the execute-outcome family this plan governs.
- Making the gating work-kind set configurable, or any change to `Blocks-Release` semantics: backlog `0htqmm` owns that.

## Scope check

This plan changes the vocabulary a runner WRITES and every site that READS it, in one pass, with a guard that fails if any site is missed. It does not change which gate refuses, does not rewrite history, and does not touch the review/approve family. The one behavior change (E-05) is isolated in its own item so a reviewer can accept or reject it independently of the rename.

## Required tests / validation

Run the suite BARE (`python3 -m pytest`); `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Baseline to beat, measured at authoring on `main` `a631a1f6`: `8850 passed, 5 skipped, 2 xfailed`. Gate on NO NEW failures rather than an absolute count, since the corpus moves. Paste ACTUAL output for every `V-*`.

## Spec / documentation sync

SEVEN SPECS NAME A LEGACY TOKEN AND ALL SEVEN ARE DECLARED IN `Scope-Paths`, because a spec is the contract every other plan is reviewed against: leaving one stale would re-authorize the vocabulary this plan removes, and the finalize scope gate announces declared spec edits before a run starts so the amendment is visible rather than incidental. Each amendment must state that legacy tokens stay READABLE forever and are no longer WRITTEN; a spec that simply swaps the words would make the back-compatibility path look like a defect to a later reader.

## Open questions

- [ ] OQ-01 Should `blocked` map to `fail-gate`, or to its own label? Blocking: no. RECOMMENDATION, taken unless overridden: map to `fail-gate`. `blocked` today means the agent stopped and preserved its work, which from an operator's position is indistinguishable from a gate refusal - work on a lane, nothing in `main`, a human needed - and a separate label would reintroduce the "how much effort" axis this plan exists to remove. RECORDED because the agent's own stop is arguably a distinct authority from a gate's.
- [ ] OQ-02 Should the four `merge-*` states collapse to one `fail-merge`, losing the transient/permanent distinction that `integration-blocked` carries today? Blocking: no. RECOMMENDATION: collapse, and carry transience in the refusal RECORD rather than in the status token, which is where `l2mzxn` already put the verdict detail. The deferral ladder keys on its own record, not on the status string, so this does not change retry behavior - but that must be VERIFIED in E-02 rather than assumed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the alias map and the canonical set as the code defines them, plus `oc.TERMINAL_STATES is agy.TERMINAL_STATES is runner_shared.TERMINAL_STATES` evaluating True. Assert by OBJECT IDENTITY, not equality: equal-but-distinct sets are the exact defect `EXECUTION_SUCCESS_STATES` records having had.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: construct a synthetic run directory carrying ALL ELEVEN legacy tokens, then paste `aw runs` and `aw attention` reading it without error and classifying each identically to its replacement. Also paste the verification that the deferral ladder's retry decision is unchanged for a legacy `integration-blocked` record (OQ-02's assumption, verified rather than assumed).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a fresh run's recorded statuses showing only canonical tokens, and paste the cause-to-token mapping proven identical across both hosts by object identity.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `interrupted` present in `TERMINAL_STATES`, and paste a deliberately stopped item being treated as terminal by a consumer that previously did not. State explicitly that `interrupted` is NOT `fail-gate`, per spec `c4gd2h` R21.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `EXECUTION_SUCCESS_STATES` equal to `{"executed"}`, and paste a dependent item correctly refusing to dispatch when its prerequisite is `fail-gate` AND when it is the legacy `substantially-complete`. ALSO paste the count of currently-pending plans whose `Item-Dependencies` name a prerequisite that is `fail-gate` today, so the blast radius of the behavior change is measured rather than estimated.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the absence of any `"complete"` coercion in `artifact_audit`, and paste a `fail-gate` item's expected directory resolving to `pending/`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the guard FAILING on a tree with one legacy literal re-introduced, NAMING the file and token, and then PASSING on the finished tree. A guard shown only green has not been shown to work. Paste the final per-token occurrence counts beside the authoring measurements in E-07 so the delta is visible.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste each of the seven specs' amended section, and `aw specs check` conforming. Paste the read-versus-write sentence from at least two of them.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste `aw runs` output showing the `Landed` column, and paste the agreement check between that column and `.aw/records/plans/executed/` membership for every item of a replayed historical run. A disagreement is a failure of this item, not of the data.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

Human approval required before execution. The E-05 behavior change should be approved explicitly and separately in review, because it can turn currently-dispatchable items into `fail-depend`.

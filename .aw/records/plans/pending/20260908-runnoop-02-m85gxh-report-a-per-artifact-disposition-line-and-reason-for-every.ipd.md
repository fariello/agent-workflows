# IPD: Report a per-artifact disposition line and reason for every artifact the selector matched

- Date: 2026-09-08
- Kind: child
- Concern: A matched artifact the run does not act on produces NO output, so the only way to learn what a run ignored is to diff the ledger against the selector by hand. MEASURED 2026-08-29 (backlog `em0z50`): `aw oc run wtiso` matched 8 plans, acted on none, and printed three lines total, none of them naming an artifact. `aw runs <id>` later showed `8 steps: 8 reviewed`, `Attempts: 0` on every row, and an empty `outcomes/`. The information existed in run state the whole time and was never printed.
  THE RUN ALREADY ANNOUNCES ITS QUEUE, WHICH IS WHY THIS IS A SMALL CHANGE. `announce_run_order` (`oc_runipd.py:4122`) prints one line naming every queued id6 in execution order, UNCONDITIONALLY, and its docstring states the reason: "the order must be auditable in the log even when nothing was reordered". Its wording comes from the shared pure formatter `render_stream.format_run_order_announcement` (`render_stream.py:1530`). So the run already has, at start, the full matched list; what it lacks is a line per artifact at the point a DISPOSITION is known.
  THE SKIP REASONS ARE ALREADY COMPUTED, EACH IN A DIFFERENT PLACE, AND NONE IS PRINTED PER ARTIFACT. Verified at HEAD `44d4950d`: needs-approval is implicit in the queue builder's admission tuple (`oc_runipd.py:3011`, `agy_runipd.py:2026`); dependency-unsatisfied is computed with a reason string by `edge_satisfied` and stored as `unsatisfied_dependency_reasons` (consumed only by the summary's diagnostics block, `render_stream.py:2152`); already-executed and status-not-runnable are decided by `action_for` (`runner_shared.py:2735`); the draft exclusion is decided by `run_selection_policy.decide_draft_admission` (`:1004`) and already HAS a renderer (`render_drafts_exclusion`, `:966`). So four of the reasons this plan must report exist as data and one already renders; the defect is that there is no ONE surface where a reader sees all matched artifacts side by side with their outcome.
- Scope: Emit exactly ONE output line per artifact the selector MATCHED, in the SAME shape whether the run acted on it or not, carrying its disposition and, when it was skipped, the reason. Site the wording in a PURE module both hosts import, never in a driver. EXCLUDES the end-of-run aggregate summary and its counts and remedies (child 03 `bsc457`); excludes adding any new refusal kind or refusal RECORD type (pending plan `r2i1b1`); excludes the `aw runs` `Issue` column and the `--json`/`--agent` payloads (also `r2i1b1`); excludes changing any disposition's MEANING (child 01 `zz5yxq`, which must land first).
- Scope-Paths: agent_workflows/run_selection_policy.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_run_selection_policy.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: executed:zz5yxq
- Status: to-review
- Set: runnoop
- Order: 2
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: m85gxh
- Blocks-Release: next
- From-Backlog: em0z50

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `em0z50` fix (b), the GENERAL requirement rather than the `reviewed` special case; inherits the item's `- Blocks-Release: next`. Every claim was measured at HEAD `44d4950d`. THE FINDING THAT MOST SHAPES THIS PLAN, and it makes the work materially smaller than the item assumed: `run_selection_policy.py` ALREADY IS the pure renderer module for exactly this family of output. It holds `render_action_preview` (`:589`), `render_counts_inline` (`:634`), `render_refusal` (`:693`), `render_drafts_preview` (`:937`) and `render_drafts_exclusion` (`:966`); it imports only stdlib plus `selectors` and `status_set` (AST-verified, `:39-40`); and `render_action_preview`'s own docstring records WHY a second renderer was rejected when the draft gate needed a variant ("the alignment rule, the type order, the action order, and the untyped-tail line would then exist twice and drift once"). So this plan EXTENDS that module rather than creating a home, and the anti-second-renderer discipline is the module's own stated convention, not an imposition.
  SECOND FINDING, which decides the siting: `render_stream.py` is NOT the right home even though it holds the summary table, because `runner_shared` already imports `render_stream` at module level, so a renderer needing to read runner-computed selection data cannot live there without a cycle. `run_selection_policy` has no such constraint and already receives exactly this kind of input as plain data.
  THIRD, THE OVERLAP FENCE WITH `r2i1b1` IS REAL AND NARROW. That pending plan (`orchprobe` Order 01, `to-review`, blocked on its own OQ-02) owns the per-item REFUSAL RECORD, the `render_stream` diagnostics allowlist, and the five duplicated `aw runs` issue-predicate copies. This plan touches none of those three: it prints from the disposition the runner already computes, at the point the run reports progress. If `r2i1b1` lands first, this plan's line should CARRY its record's reason and remedy rather than duplicating them; E-05 requires that be checked at execution time rather than assumed either way.

## Goal

Make every artifact a selector matched produce one output line naming what happened to it, so a reader never has to reconstruct what a run ignored.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one pure renderer for the per-artifact line

- [ ] E-01 ADD ONE PURE RENDERER to `run_selection_policy.py` that formats a SINGLE per-artifact disposition line from plain data: the artifact identity, its action, its disposition, and an optional reason. Pure means it builds and returns a string, prints nothing, touches no filesystem, and imports no runner, exactly as `render_action_preview` (`:589`) and `render_refusal` (`:693`) already do in that module.
  ONE RENDERER, NOT ONE PER DISPOSITION. The line for an acted-on artifact and the line for a skipped one must come from the SAME function with the same alignment and field order, because the backlog item's requirement is that a skipped artifact is reported "in the SAME shape as an acted-on one". Two renderers would drift in exactly the way `render_action_preview`'s docstring records.
  DO NOT ADD A FIRST-PARTY IMPORT beyond the two the module already has (`selectors`, `status_set`, AST-verified at `:39-40`). If the line needs a fact the caller has and the module does not, pass it in as a parameter; that is what makes every branch testable without a run.
  - Depends on: none
  - Expected outcome: one function in `run_selection_policy.py` returning a formatted line for any (identity, action, disposition, reason) tuple; an AST walk shows the module's first-party imports unchanged; the acted-on and skipped forms are field-aligned and produced by this one function.
  - Execution state: pending

- [ ] E-02 ENUMERATE AND NAME THE SKIP REASONS the line must be able to carry, as a closed, documented set in the same module, so a reason is a value rather than an ad-hoc string at a call site. The backlog item names six: needs-approval, dependency unsatisfied (naming the unmet dependency), already executed, status not runnable, gate refused, and filtered out by a flag.
  READ EACH REASON FROM WHERE IT IS ALREADY COMPUTED; do NOT recompute any. Located at HEAD `44d4950d`: needs-approval from child 01's durable fact on the queue item (`zz5yxq` E-03), which is why this plan depends on that child; dependency-unsatisfied from `unsatisfied_dependencies` plus `unsatisfied_dependency_reasons`, which `edge_satisfied` already populates and which today reach only the summary diagnostics block (`render_stream.py:2152`); already-executed and status-not-runnable from the plan status and `action_for` (`runner_shared.py:2735`); the draft exclusion from `run_selection_policy.decide_draft_admission` (`:1004`), which already renders its own notice at `render_drafts_exclusion` (`:966`) and must be REUSED rather than reformatted.
  STATE WHAT YOU FIND FOR "GATE REFUSED" RATHER THAN INVENTING IT. That reason is the least well-defined of the six and the runner has several distinct gates (draft admission, mixed-type, dependency preflight, requested-action legality, host capability). Enumerate which of them can leave an artifact matched-but-unacted, and if one of them refuses the whole RUN rather than one artifact, say so and exclude it: a per-artifact line cannot report a run-wide refusal and pretending otherwise would produce a line that never renders.
  - Depends on: E-01
  - Expected outcome: a closed named set of skip reasons in `run_selection_policy.py`, each documented with WHERE its value is read from; the draft exclusion reuses the existing renderer; any of the six that turns out to be run-wide rather than per-artifact is excluded with the measurement that showed it.
  - Execution state: pending

### Task group 2: wire both hosts

- [ ] E-03 CALL THE RENDERER FROM BOTH HOSTS at the point a disposition becomes known, and ALSO for every matched artifact the run never dispatches. The second half is the defect: the existing finish line (`oc_runipd.py:6743-6757`, agy twin `:4013`) prints only for an item that RAN, so an item frozen as needs-approval never reaches it.
  DO NOT ADD A SYMBOL TO `oc_runipd` FOR AGY TO IMPORT. `agy_runipd` already imports 47 names from `oc_runipd` (AST-measured 2026-09-08) and zero flow back. Both hosts import the renderer from `run_selection_policy` directly.
  PRINT ONCE PER ARTIFACT, NOT ONCE PER ATTEMPT. An item with three attempts must still produce one disposition line, or the counts child 03 aggregates will not sum to the number matched. Decide where that one line is emitted (after the item reaches a terminal disposition, or in one pass over the queue at a defined point) and record the choice with its reason.
  - Depends on: E-02
  - Expected outcome: both hosts emit exactly one line per matched artifact, including artifacts never dispatched; neither host gained an import from the other; the once-per-artifact property holds for a multi-attempt item.
  - Execution state: pending

- [ ] E-04 PIN THE SHARING BY OBJECT IDENTITY AND SYMMETRICALLY. Every symbol this plan adds must resolve to the SAME object from `oc_runipd`, `agy_runipd` and `run_selection_policy`. Register it in `tests/test_runner_refork_guard.py`'s `REFORK_TABLE`, whose `test_the_table_covers_both_runners` already fails a one-sided table.
  THE GUARD MUST BE SYMMETRIC, and the reason is measured history rather than style: the one-sided versions of exactly this guard were RETIRED for being one-sided, which is how the `render_stream` re-fork went unnoticed. A table row naming only `oc_runipd` is a failed E-04 even if the code is correct today.
  - Depends on: E-03
  - Expected outcome: object-identity assertions for every added symbol across all three modules; a `REFORK_TABLE` row covering BOTH runners; the AST-measured oc-to-agy import count unchanged at 47 or lower.
  - Execution state: pending

- [ ] E-05 RECONCILE WITH PENDING PLAN `r2i1b1` AT EXECUTION TIME rather than at authoring time, and record the answer. Read that plan's current `- Status:` and location. If it has EXECUTED, its refusal record carries a reason and a REMEDY, and this plan's line must consume that record rather than formatting a parallel reason string. If it has NOT executed, this plan's line stands alone and must not define a record type that would collide with it.
  DO NOT DEFINE A REFUSAL RECORD HERE UNDER ANY BRANCH. Even if `r2i1b1` never lands, a record type is that plan's deliverable and defining a second one is how two vocabularies for one fact appear.
  - Depends on: E-04
  - Expected outcome: `r2i1b1`'s status read and recorded; the integration decision made and justified from that reading; no refusal record type defined in this plan under either branch.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `run_selection_policy.py` IS THE ESTABLISHED PURE-RENDERER HOME for run selection output, and it states its own anti-duplication rule: `render_action_preview`'s docstring records that a second renderer was rejected because "the alignment rule, the type order, the action order, and the untyped-tail line would then exist twice and drift once". Extending it is following that convention; adding a sibling module is not.
- THE MODULE'S PURITY IS A PROPERTY TO PRESERVE. AST-verified: its only first-party imports are `selectors` and `status_set` (`:39-40`). Every gate in it is pure and takes the answer as a parameter (`decide_draft_admission`'s docstring: "PURE: no TTY, no filesystem, no ledger. The caller performs the prompt ... which is what makes every branch testable").
- `render_stream.py` IS NOT AN ALTERNATIVE HOME for anything that reads runner selection data, because `runner_shared` imports `render_stream` at module level and the reverse edge would be a cycle. `render_stream` also imports no first-party module at all, a property another plan (`r2i1b1` E-01) explicitly depends on.
- THE UNCONDITIONAL-ANNOUNCEMENT PRECEDENT ALREADY EXISTS. `announce_run_order` prints the order whether or not anything was reordered, because "the order must be auditable in the log even when nothing was reordered". A per-artifact line printed only when something interesting happened would contradict a convention this repo already chose.
- THE IMPORT DIRECTION IS ONE-WAY: `agy_runipd` imports 47 names from `oc_runipd`; `oc_runipd` imports zero from agy. Shared symbols go in a shared module.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses), while a lane worktree shows roughly 32 environmental failures.

## Findings

| Id | Severity | Location (measured at HEAD `44d4950d`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `oc_runipd.py:6743-6757`, `agy_runipd.py:4013` | The per-item finish line prints only for an item that RAN, so a matched-but-never-dispatched artifact produces no line at all. | source read, both hosts |
| F-2 | HIGH | measured | A run matching 8 artifacts and acting on none printed three lines, none naming an artifact, and exited 0. | backlog `em0z50`, reproduced at HEAD by rendering the summary with one `reviewed` item: `Outcome: COMPLETED`, no diagnostic line |
| F-3 | MED | `oc_runipd.py:4122`, `render_stream.py:1530` | The run ALREADY announces every queued id6 unconditionally through a shared pure formatter, so the matched list is available at start and the precedent for unconditional reporting exists. | source read |
| F-4 | MED | `render_stream.py:2152` | `unsatisfied_dependencies` and `unsatisfied_dependency_reasons` are already populated with per-dependency reason strings, but reach only the summary diagnostics block, which itself keys on a five-status allowlist. | source read |
| F-5 | MED | `run_selection_policy.py:966`, `:1004` | The draft exclusion already has a pure decision function AND a renderer, so one of the six skip reasons must be reused rather than reformatted. | source read |
| F-6 | MED | `run_selection_policy.py:39-40`, `:589` | The module is pure (two first-party imports, AST-verified) and its docstring already forbids a second renderer for one shape. It is the correct home. | AST walk plus docstring |
| F-7 | LOW | `.aw/records/plans/pending/20260907-orchprobe-01-r2i1b1-...ipd.md` | A pending plan owns the refusal RECORD, the diagnostics allowlist, and the five `aw runs` issue-predicate copies. Its E-01 also depends on `render_stream` importing no first-party module. | read that plan |

## Proposed changes (ordered, validatable)

1. E-01 adds ONE pure per-artifact line renderer to `run_selection_policy.py`, preserving the module's purity.
2. E-02 enumerates the skip reasons as a closed named set, each documented with where its value is READ from, reusing the draft renderer and excluding any reason that turns out to be run-wide.
3. E-03 wires both hosts, including the never-dispatched case, once per artifact rather than once per attempt.
4. E-04 pins the sharing by object identity and registers a SYMMETRIC re-fork guard row.
5. E-05 reconciles with `r2i1b1` from its status read at execution time.

## Deferred / out of scope (with reason)

- The END-OF-RUN AGGREGATE SUMMARY, its per-disposition counts, and its remedy commands: child 03 (`bsc457`). This child owns the per-artifact line; that one owns the aggregate. Split deliberately, because the line and the summary have separate test surfaces and the summary must be provable for a zero-action run independently.
- Any NEW refusal kind, and the refusal RECORD type: pending plan `r2i1b1`.
- The `aw runs` `Issue` column, the artifact-discrepancy summary, and the `--json`/`--agent` payload fields: also `r2i1b1`, whose E-03 extracts the five duplicated predicate copies first. Adding a field here would extend one copy and make the surfaces disagree, which is precisely the defect that plan records.
- Changing what any disposition MEANS: child 01 (`zz5yxq`), which this plan declares as an `executed:` dependency.
- Extending the same matched-vs-acted discipline to `aw runs`, `aw ipd set`, and `aw find`, which the backlog item raises. Each has different selector semantics and its own tests; the driver shape should be proven first.
- The `render_stream` COMPLETED tuple (`:1872`), which also treats `reviewed` as a success. Recorded because a reader will notice it; it is the RENDERER's copy of child 01's question and is handled with the summary in child 03.

## Scope check

- Over-scope: `oc_runipd.py` and `agy_runipd.py` are in scope ONLY to CALL the renderer and to iterate the matched set. Do NOT change any gate, any disposition value, or any status. Do NOT edit `render_stream.py`.
- Under-scope: stated rather than left as `none`. This child does not aggregate, does not count, does not print a remedy, and does not make the disposition machine-readable. Those are child 03 and `r2i1b1`.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, baseline measured THERE and pasted, failing NODE IDS compared. `tests/test_run_selection_policy.py` is where the pure renderer's cases belong, because a pure function needs no run to test: cover each named skip reason, the acted-on form, and the field alignment between them. `tests/test_runner_refork_guard.py` holds the symmetric sharing guard. Note `tests/test_runner_shared.py::WrapperTests` counts per-runner call sites deliberately, so if wiring changes a counted site, reflect it rather than working around it.

## Spec / documentation sync

Spec `25kzda` (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, `- Status: approved`) §5.6 already REQUIRES what this child builds, so this is a move TOWARD the approved contract and NOT an amendment. Its exact words: "The final table includes position, ID/path, type, starting status, action trace, final item state, verification state, reason code, commit(s), and next command", and its allowed per-item outcomes include `skipped`, glossed "no execution was appropriate for the current valid state, including `dependency_not_met` with its explicit reason chain". No spec file is therefore declared in `- Scope-Paths:`.
ONE THING TO CHECK RATHER THAN ASSUME: §5.6 requires a REASON CODE per item, and this plan's E-02 produces a closed named set of reasons. Confirm whether the spec's `reason_code` vocabulary (it shows `IPD_EXECUTED_VERIFIED` and `dependency_not_met` by example, and §4.2 defines `RUN-*` codes) constrains those names. If it does, use its names; if the spec only requires that a code exist, say so. Do NOT edit §4.2's finding-code table: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Is the per-artifact line emitted at the point each item terminates, or in one closing pass over the queue?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because both satisfy the requirement and the trade-off is legible from the code. Emitting AT TERMINATION gives the operator live feedback and matches the existing finish line's placement (`oc_runipd.py:6743`), but a never-dispatched item has no termination point, so that shape needs a second pass anyway for exactly the case this plan exists to fix. Emitting in ONE CLOSING PASS guarantees the once-per-artifact property and that the counts sum, but delays feedback on a long run. A hybrid (live line at termination, plus a closing pass for everything that never terminated) is probably right and is what E-03 should record. Decide from the code and state the reason; do not leave it implicit.

### OQ-02: Should "gate refused" remain one of the six named skip reasons if every such gate refuses the whole run rather than one artifact?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-02 already instructs that a run-wide refusal be excluded with the measurement that showed it, so the plan is executable either way. The question is recorded because the backlog item lists the reason and an executor may feel obliged to produce it. Measured starting point: the draft admission gate EXCLUDES per artifact and rebinds the queue (`oc_runipd.py`, the `is_status_selector` branch), so at least one gate is genuinely per-artifact; the mixed-type gate and the dependency preflight RAISE before the run directory exists, so nothing is matched-but-unacted for them to report. Enumerate the rest before answering.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the renderer as written. Paste TWO rendered lines from it, one acted-on and one skipped, side by side, so the reader can SEE the shapes are identical rather than being told so. Paste an AST walk of `run_selection_policy.py`'s `Import`/`ImportFrom` nodes showing the first-party imports are still exactly `selectors` and `status_set`, and paste proof the function prints nothing and touches no filesystem (call it in a fresh interpreter with no repo present).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the closed reason set as written, with each entry's documented SOURCE. For each reason, paste one rendered line carrying it. For the dependency reason, paste a line that NAMES the unmet dependency, since the backlog item requires that specifically. Paste proof the draft exclusion REUSES `render_drafts_exclusion` rather than reformatting (show the call, not a similar string). For any of the six reasons excluded as run-wide, paste the measurement that showed it refuses before an artifact could be reported.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the ACTUAL stdout of a run whose selector matched artifacts it did not act on, showing one line per matched artifact. Paste the same for a MIXED run covering at least four distinct dispositions, and show the line count EQUALS the number matched. Paste a multi-attempt item's output showing exactly ONE disposition line for it. State where the line is emitted and why (OQ-01's answer). Paste the AST-measured oc-to-agy import count before and after, showing it did not increase from 47.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste object-identity output for every added symbol resolving to the same object from all three modules. Paste the new `REFORK_TABLE` row showing BOTH runners listed, and paste `tests/test_runner_refork_guard.py` passing. Then MUTATION-CHECK the guard: define a local copy of one added symbol in `agy_runipd`, show the guard FAILS, revert, show it passes. A guard that cannot fail is not evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `r2i1b1`'s `- Status:` line and its directory, read at validation time. State which branch applied and what was done. If it executed, paste the code showing this plan's line consumes its record; if it did not, paste proof this plan defines no refusal record type (a grep for a record/dataclass definition in the changed files, returning nothing).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the six paths in `- Scope-Paths:`. Do NOT define a refusal record type. Do NOT edit `render_stream.py`. Do NOT change any gate, disposition value, or plan status. Do NOT add a first-party import to `run_selection_policy.py` beyond the two it has. Do NOT add a symbol to `oc_runipd` for `agy_runipd` to import. Do NOT edit spec `25kzda`, and never its §4.2 finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. `oc_runipd.py` and `agy_runipd.py` are the highest-contention files in this repository and are being edited by live runs; measured, their line numbers moved roughly 70 and 95 lines in a single day. Find `announce_run_order`, `format_run_order_announcement`, `render_action_preview`, `render_drafts_exclusion`, `decide_draft_admission`, `edge_satisfied`, and `action_for` by name.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved m85gxh --by-human --message ...`) before execution, and child 01 (`zz5yxq`) must read `executed` first, which the declared `- Item-Dependencies: executed:zz5yxq` enforces. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. Do NOT close backlog `em0z50` here: its fix (c) ships in child 03, and closing it now would claim a summary no code yet prints.

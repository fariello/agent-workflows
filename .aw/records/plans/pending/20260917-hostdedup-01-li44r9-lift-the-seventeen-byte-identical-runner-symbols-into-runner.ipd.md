# IPD: Lift the seventeen byte-identical runner symbols into runner shared

- Date: 2026-09-17
- Kind: child
- Concern: SEVENTEEN top-level symbols are defined in BOTH `oc_runipd.py` and `agy_runipd.py` and are BYTE-IDENTICAL after AST normalization with docstrings stripped: StallWatchdog, _budget_breach_recorder, _escalation_recorder, _observe_between_turn_stop, _record_checkpoint_stop, _record_deliberate_stop, build_isolation_notice, disable_lane_prompt, driver_finalize, evaluate_clean_base_for_launch, handle_stop_command, install_stop_triggers, locked_run, requeue_interrupted, run_lock, set_plan_approved, terminate_process. That is 380 lines of pure copy-paste with zero host-specific content. Measured at HEAD 2026-09-17. Every fix to one copy is a fix the other silently misses, which is not hypothetical: the `cjefq5` defect fixed on 2026-09-17 was ONE expression present byte-identically in both hosts, mislabeled an executed plan `reviewed`, and killed six approved plans plus two orchestrators at queue build across 13 separate runs before anyone traced it. The cost is also about to multiply: at two hosts each duplicated symbol is written twice, at five hosts (codex, claude, hermes) it is written five times.
- Scope: Move these seventeen symbols to `runner_shared.py` as ONE definition each, and leave each host a thin delegating wrapper of the sanctioned form the repository already uses in 21 other places. This is the LOWEST-RISK tranche by construction: because the bodies are byte-identical, the shared definition is the existing body verbatim, with no parameterization to design and no behavior decision to make. Does NOT touch the twelve divergent symbols (Order 02) or the five large functions (out of Set; see Deferred).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_hostdedup_identical_lift.py, tests/test_rununify_initialize_run.py, tests/test_rununify_execute_item.py, tests/test_rununify_run_queue.py, tests/test_runner_shutdown.py, tests/test_runner_backlog_close.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- From-Backlog: dstnso
- Set: hostdedup
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: li44r9
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-18 reviewed (/plan-review Antigravity): approve with revisions applied; PR-001 resolved by maintainer decision on OQ-03 (Route a); readiness go-pending-approval
- 2026-09-18 reviewed (aw set): plan-review complete: REVIEWED - OPEN QUESTIONS; 12 findings, 11 FIXED, PR-001 left OPEN at BLOCKER (nine symbols close over module-level names, FULL_AUTO_ACTOR differs per host and reaches permanent workflow history) and escalated as blocking OQ-03; readiness no-go
- 2026-09-17 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001..PR-012; readiness `no-go` on ONE blocking finding. Reviewed at HEAD `a3c103d7`; `aw ipd lint --phase author` conforming before revision. THE 17-SYMBOL SET IS EXACTLY RIGHT: re-measured with the plan's own method (`ast.unparse`, docstrings stripped), 29 co-defined symbols are byte-identical and the 12 this plan excludes are all already-delegating wrappers, so the 17/12 partition verifies symbol for symbol. F-4 verifies (zero `__file__`). BUT THE CENTRAL PREMISE "identical bodies mean the shared version is the current body unchanged, with no decision to make" IS FALSE FOR NINE OF THE SEVENTEEN, and this is the whole finding: byte-identical bodies can reference module-level names that DIFFER. Measured, nine symbols close over nine module-level names absent from `runner_shared`, and one of them, `FULL_AUTO_ACTOR`, is `"aw oc run --full-auto"` on oc and `"aw agy run --full-auto"` on agy. `set_plan_approved` reads it TWICE and passes it as `--actor`, which lands in a plan's PERMANENT workflow history, so a verbatim lift would silently attribute every agy auto-approval to `aw oc run`. Three more (`_escalation_recorder`, `handle_stop_command`, `install_stop_triggers`) call `_detect_driver_command`, which is precisely each host's `HostLabels`-binding wrapper, so a verbatim lift binds them to one host's labels. That makes this a `HostLabels` tranche after all, which the plan says would be a signal the symbol belongs in Order 02. ALSO FOUND: F-5's "exactly two" host-token mentions is THREE (`locked_run`'s docstring names `run_opencode`), so E-03 as scoped leaves a host name in shared code; F-6 and E-04 cite the WRONG guard (`assertIn`, which a wrapper still satisfies) and quote its remedy message, while the assertion that actually fires is `assertFalse(is_pure_delegation(...))`, verified by calling the predicate; the pin tables live in THREE files this plan must edit, not one (the defect its own parent's review raised as PR-001, now fixed here); and FIVE assertions in TWO further undeclared files break on the lift, proven by reading them (`test_runner_shutdown.py:160` and `:173`, `test_runner_backlog_close.py:1145`). Four files added to the fence. E-01..E-05 revised, E-06..E-08 added, `Highest E allocated` 05 -> 08. OQ-03 raised `Blocking: yes` carrying PR-001.
- 2026-09-17 to-review (aw set): Authored 2026-09-17 from an AST measurement at HEAD (34 forked symbols / ~1752 oc lines across the two runners); complete enough to critique

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Delete 380 lines of duplicated runner code by giving seventeen symbols one definition each, so a fix to
any of them lands once instead of needing to be remembered twice.

WHY THIS TRANCHE FIRST. The five large functions (`execute_item`, `run_queue`, `initialize_run`,
`build_parser`, `main`) are what everyone reaches for, and they are where `rununify` 07-11 stalled: each
of those plans was re-scoped at review into analysis-only and every one records `NO SPLIT WAS PERFORMED`.
They stalled for a real reason (a 13-of-23 host-specific `options` dict, a `__file__` that changes meaning
on relocation), not for want of effort. Meanwhile these seventeen need NO such decision: identical bodies
mean the shared version is the current body unchanged. Taking the free tranche first removes a third of
the remaining fork with near-zero risk and proves the wrapper pattern at scale before Order 02 tackles the
symbols that genuinely differ.

VERIFIED SAFE TO LIFT VERBATIM -- **CORRECTED AT REVIEW: NINE OF THE SEVENTEEN ARE NOT.** The original
paragraph scanned for exactly two hazards, `__file__` and host tokens, and concluded the tranche needed no
decisions. It missed a THIRD hazard that is the reason `set_plan_approved` cannot be lifted verbatim:
A BYTE-IDENTICAL BODY CAN REFERENCE A MODULE-LEVEL NAME WHOSE VALUE DIFFERS PER HOST. AST comparison
matches on the NAME, so two bodies reading `FULL_AUTO_ACTOR` compare equal while resolving to different
strings. Measured at review, nine of the seventeen close over nine module-level names that do not exist in
`runner_shared`:

| lifted symbol | module-level names it closes over (absent from `runner_shared`) |
|---|---|
| `set_plan_approved` | `FULL_AUTO_ACTOR` (**DIFFERS PER HOST**), `FULL_AUTO_APPROVAL_MESSAGE` (same), `pinned_module_argv` |
| `_escalation_recorder` | `_detect_driver_command` (**the host-labels binding wrapper**) |
| `handle_stop_command` | `_detect_driver_command` (**same**) |
| `install_stop_triggers` | `_detect_driver_command` (**same**) |
| `driver_finalize` | `_compute_scope_reconciliation`, `pinned_child_env`, `pinned_module_argv` |
| `terminate_process` | `_SIGINT_GRACE_SECONDS`, `_SIGTERM_GRACE_SECONDS` (both same value) |
| `disable_lane_prompt` | `_LANE_PROMPT_DISABLED` (same value, but MUTABLE module state) |
| `StallWatchdog` | `terminate_process` (in this tranche) |
| `locked_run` | `run_lock` (in this tranche) |

TWO OF THOSE ARE REAL HOST DIVERGENCE AND CHANGE WHAT THIS PLAN IS.
1. `FULL_AUTO_ACTOR` is `"aw oc run --full-auto"` (`oc_runipd.py:817`) and `"aw agy run --full-auto"`
   (`agy_runipd.py:922`). `set_plan_approved` reads it at `:855` and `:886` and passes it as `--actor` to
   `aw set auto-approved`, which lands in a plan's PERMANENT `## Workflow history`. A verbatim lift makes
   every agy auto-approval claim it was done by `aw oc run`. That is durable-history misattribution, the
   exact harm `HostLabels`'s own docstring (`runner_shared.py:8533-8537`) says its no-defaults design exists
   to prevent.
2. `_detect_driver_command` is each host's ONE-LINE `HostLabels` BINDING (`oc_runipd.py:8768` binds
   `OC_HOST_LABELS`; `agy_runipd.py:5236` binds `AGY_HOST_LABELS`). Three lifted symbols call it. A shared
   body calling a shared `_detect_driver_command` would bind one host's labels for both.

SO THIS TRANCHE DOES NEED `HostLabels`, which by this plan's own convention note is "a signal that symbol
belongs in Order 02". The correct resolution is a decision, not a silent lift: see the revised E-02, the new
E-06, and OQ-03. The other seven closure deps are equal-valued or in-tranche and are mechanical, but they
still must MOVE, so even the easy cases are not "the body verbatim and nothing else".

THE TWO ORIGINAL HAZARDS, re-measured: zero `__file__` across all seventeen (F-4 CONFIRMED). Host tokens
are THREE, not two: `evaluate_clean_base_for_launch` ("the agy twin", `:2407`), `terminate_process`
("a child OpenCode process", `:5274`) and `locked_run` ("per-turn `run_opencode` handlers", `:8744`). All
three are prose-only with no host token in code, so the SAFETY conclusion stands; the COUNT does not, and
`locked_run` names a function (`run_opencode`) that will not exist for a third host.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Re-measure, then lift

- [ ] E-01 Re-measure the identical set at execution HEAD and REFUSE to proceed on a stale list. Parse both runners, normalize each top-level symbol with `ast.unparse` after stripping docstrings, and emit the set defined in both AND byte-identical. Re-run the hazard scan for `__file__` and host tokens, separating a token in CODE from a token in PROSE. COMMIT THE SCANNER rather than running it ad hoc: the parent Set's completion criteria depend on re-running "the same AST scan", and no such scanner exists in-tree (parent PR-006), so this item is where it comes from. State its metric explicitly, since the SPAN, the `ast.unparse` and the span-minus-docstring counts differ by more than 2x on this very set.
  - Depends on: none
  - Expected outcome: a COMMITTED scanner plus its output, compared against the review-verified baseline of SEVENTEEN symbols (the symbol set reproduced exactly at review; the "380 oc lines" figure did NOT, see E-07). A symbol that has since diverged moves to Order 02's tranche and is named; a newly identical symbol is added here. Zero `__file__` occurrences expected; THREE prose-only host-token mentions expected, not two (`evaluate_clean_base_for_launch`, `terminate_process`, `locked_run`).
  - Execution state: pending

- [ ] E-06 ENUMERATE THE CLOSURE OF ALL SEVENTEEN BEFORE LIFTING ANYTHING, and classify every module-level name each body reaches. This item exists because the plan's original safety scan checked only `__file__` and host tokens and therefore concluded, wrongly, that a byte-identical body implies a decision-free lift. Measured at review: nine symbols close over nine names absent from `runner_shared` (table in the Goal). Classify each as (a) IN-TRANCHE, moving anyway; (b) EQUAL-VALUED, a mechanical relocation; (c) HOST-DIVERGENT, needing `HostLabels`; or (d) A HOST BINDING, i.e. `_detect_driver_command`, which IS the labels seam. Do NOT lift any symbol whose closure lands in (c) or (d) until E-06 has said how the difference is carried. A symbol whose closure cannot be resolved without a per-host value is an ORDER 02 symbol by this plan's own convention note, and moving it here would be the silent behavior change the gate forbids.
  - Depends on: E-01
  - Expected outcome: a per-symbol closure table with each dependency classified (a)-(d), naming which symbols are cleared to lift in E-02, which need the E-08 treatment, and which (if any) are handed to Order 02 with the reason.
  - Execution state: pending

- [ ] E-02 Lift ONLY the symbols E-06 cleared as closure-clean into `runner_shared.py` as one definition each, replacing both hosts' copies with a delegating wrapper. Preserve each body EXACTLY; this item must contain no behavior change, so any diff beyond the move plus the wrapper is out of scope for it. THE EXPECTED COUNT IS NOT FIFTEEN: the original figure came from the host-token scan alone, and the closure scan cuts across it differently (`locked_run` mentions a host in prose AND closes over an in-tranche symbol, while `set_plan_approved` mentions no host and is the single most divergent case). E-06's table decides the membership, not this sentence.
  - Depends on: E-01, E-06
  - Expected outcome: each cleared symbol with one definition in `runner_shared`, two thin wrappers each, and no NEW suite failures. State the count and name any symbol E-06 held back.
  - Execution state: pending

- [ ] E-03 Lift the THREE prose-contaminated symbols (`evaluate_clean_base_for_launch`, `terminate_process`, `locked_run`), re-wording their docstrings so none names a specific host. A shared symbol whose docstring says "the agy twin", "a child OpenCode process" or "the per-turn `run_opencode` handlers" is misleading the moment a third host calls it, and the last is the worst of the three because `run_opencode` is a SYMBOL NAME that will not exist for that host. `locked_run` was missed by the authoring scan (F-5 said two).
  - Depends on: E-01, E-06
  - Expected outcome: all three lifted, with docstrings that describe the behavior host-neutrally. Quote the before and after wording for each.
  - Execution state: pending

- [ ] E-08 CARRY THE HOST-DIVERGENT CLOSURE THROUGH `HostLabels` RATHER THAN FORKING OR FLATTENING IT, for the two cases E-06 will classify (c)/(d). `FULL_AUTO_ACTOR` differs per host and reaches a plan's permanent `## Workflow history` through `--actor`, so the shared `set_plan_approved` must receive it from the CALLER (a `HostLabels` field, or the existing `command` field if the derivation is exact and stated) and must NOT default it: `HostLabels` is a no-defaults `NamedTuple` precisely so a missing host value raises instead of silently misattributing durable history (`runner_shared.py:8531-8539`). For `_detect_driver_command`, the shared bodies must reach the host's labels through the same parameter the 21 existing wrappers already use, never by calling a shared `_detect_driver_command` that binds one host. PIN THE ATTRIBUTION IN BOTH DIRECTIONS with a test: an oc auto-approval records `aw oc run --full-auto` and an agy one records `aw agy run --full-auto`. If E-06 concludes the difference cannot be carried without redesigning the seam, STOP and hand the symbol to Order 02 rather than inventing a mechanism here.
  - Depends on: E-06
  - Expected outcome: the divergent values carried by descriptor with no default, and a both-directions attribution test pasted green. Or a recorded hand-off to Order 02 with the reason.
  - Execution state: pending

### Task group 2: Re-base the guards that pin the duplication

- [ ] E-04 Update the `STILL_DOUBLE_DEFINED` / `THIN_WRAPPERS_OVER_RUNNER_SHARED` tables in ALL THREE FILES THAT CARRY THEM FOR THIS TRANCHE, in the SAME change, per the maintainer's re-base-deliberately rule. **CORRECTED AT REVIEW: the authored item named one file and cited the wrong assertion.** The three files and this plan's symbols in each, measured:
  - `tests/test_rununify_execute_item.py`: `_record_checkpoint_stop`, `driver_finalize`, `evaluate_clean_base_for_launch`, `set_plan_approved`
  - `tests/test_rununify_run_queue.py`: `_observe_between_turn_stop`, `_record_deliberate_stop`, `disable_lane_prompt`, `requeue_interrupted`
  - `tests/test_rununify_initialize_run.py`: `set_plan_approved`

  AND THE ASSERTION THAT ACTUALLY FIRES IS NOT THE ONE F-6 QUOTES. `test_every_still_double_defined_symbol_really_is_defined_in_both_runners` uses `assertIn(name, defs)`, which a WRAPPER still satisfies, so it keeps PASSING after a lift and its helpful failure message never appears. The one that fails is `test_every_still_double_defined_symbol_is_a_REAL_fork_not_a_thin_wrapper`, which asserts `assertFalse(is_pure_delegation(defs[name]))`; verified at review by calling the guard's own `is_pure_delegation` on a delegating body (returns True). Expect the failure there, in all three files.
  - Depends on: E-02, E-03, E-08
  - Expected outcome: the pin tables in all three files reflect the post-lift reality, with each moved symbol MOVED to the wrapper table rather than deleted from the guard entirely. Never weaken the guard silently: state which entries moved, in which file, and why. Run all four `test_rununify_*` pin files together (review baseline `95 passed`).
  - Execution state: pending

- [ ] E-07 RE-BASE THE FIVE NON-`rununify` ASSERTIONS A LIFT BREAKS, in the same change, and treat them exactly as E-04 treats the pin tables: re-based deliberately, never weakened. Found at review by reading them, all currently green:
  - `tests/test_runner_shutdown.py:160` asserts `inspect.getsource(mod.terminate_process)` CONTAINS `"runner_shutdown.terminate_process"`. After the lift each host's wrapper calls `runner_shared.terminate_process`, so this FAILS. Verified: the current oc body does contain that string.
  - `tests/test_runner_shutdown.py:173` sets `oc._SIGINT_GRACE_SECONDS = 0.11` and requires the value to reach the reaper. The shared body would read `runner_shared`'s constants, so the per-host tuning contract BREAKS unless the lift preserves it deliberately. This is a behavior contract, not a source pin, and it is the most important of the five.
  - `tests/test_runner_backlog_close.py:1145` asserts `inspect.getsource(mod.terminate_process)` contains `_SIGINT_GRACE_SECONDS` and `_SIGTERM_GRACE_SECONDS`, which a delegating wrapper does not.
  Both files are now declared. Two other pins survive a lift and need no edit, stated so they are not touched needlessly: `test_runner_stop_triggers.py:940` reads the CALL SITE `install_stop_triggers(run_dir)` in the runner source (unchanged by a lift) and `:2343` only asserts `hasattr`.
  - Depends on: E-02, E-03
  - Expected outcome: the three broken assertions re-based with a per-assertion reason, the grace-constant pass-through contract shown STILL HONORED by a behavioral test (not merely re-worded away), and `tests/test_runner_shutdown.py tests/test_runner_backlog_close.py` green (review baseline `74 passed`).
  - Execution state: pending

- [ ] E-05 Add `tests/test_hostdedup_identical_lift.py` asserting the invariant this plan establishes and the NEXT host inherits: for every lifted symbol, BOTH hosts' names resolve to the ONE `runner_shared` definition, and no runner re-forks it. NOTE THE IDENTITY FORM: with the wrapper design this plan chose, `oc_runipd.<sym> is agy_runipd.<sym>` is FALSE (verified at review on the existing wrapper `git_head`: both `oc.git_head is agy.git_head` and `oc.git_head is RS.git_head` are False), so assert DELEGATION (the wrapper body reaches the one shared definition), not object identity. Drive it from a named table so a re-fork fails loudly rather than drifting back.
  - Depends on: E-04, E-07
  - Expected outcome: a guard that fails if either host reintroduces a private copy of any of the seventeen, using a delegation predicate rather than an `is` comparison that the chosen design makes false.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `runner_shared.py` is the established home for host-neutral runner logic and imports NO runner, so it
  cannot ask which host it is serving; the CALLER supplies host-varying values. Grown 773 -> 9182 lines
  across `rununify` 01-06, so this is a well-trodden path, not a new pattern.
- THE WRAPPER FORM IS ALREADY SANCTIONED AND WIDESPREAD: 21 symbols are currently thin delegations over
  `runner_shared` on both hosts (e.g. `git_head`, `save_state`, `build_prompt`, `integrate_lane_branch`).
  A wrapper is explicitly NOT counted as a fork by `test_rununify_initialize_run.py`'s
  `is_pure_delegation` check, which is the precedent this plan follows.
- `runner_shared.HostLabels` (`runner_shared.py:8530`) already carries every host-varying STRING with
  `OC_HOST_LABELS` bound by oc's wrappers. Order 02 needs it; this tranche should NOT, and needing it for
  a supposedly identical symbol is a signal that symbol belongs in Order 02. **THAT SIGNAL FIRES: measured
  at review, `set_plan_approved` needs a host-divergent `FULL_AUTO_ACTOR` and three symbols call
  `_detect_driver_command`, which IS the labels binding. So either those four take the E-08 descriptor
  treatment here, or they are Order 02 symbols. OQ-03 asks which, because the convention note above makes
  it a real question rather than an executor's choice.**
- THE REPOSITORY ALREADY HAS A CATEGORY FOR THIS EXACT CASE, which is the strongest evidence the finding is
  real rather than pedantic: `tests/test_rununify_run_queue.py` carries `EQUAL_CONSTANTS` AND
  `DIVERGENT_CONSTANTS` (currently `('DEPENDENCY_BLOCK_RECOVERY_HINT',)`) alongside its symbol tables,
  precisely because a shared body reaching a per-host constant is a known hazard here. `FULL_AUTO_ACTOR`
  belongs in that category and is not yet in it.
- A WRAPPER IS NOT THE SAME OBJECT. Verified on the existing wrapper `git_head`: `oc.git_head is
  agy.git_head` is False and `oc.git_head is runner_shared.git_head` is also False. Any evidence
  requirement phrased as object identity is unsatisfiable under the wrapper design this plan chose (see
  E-05 and V-02).
- `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import` forbids a runner importing the
  other runner, so `agy` importing from `oc` is not an available shortcut.
- The maintainer's 2026-09-16 ruling (recorded in `orziju`'s history): TESTS ARE NOT IMMOVABLE. A
  source-reading guard is re-based deliberately as part of the work, never weakened silently. E-04 is that
  re-base.
- `__file__` IS NOT A SYMBOL AND DOES NOT RELOCATE: it evaluates in the defining module. `orziju`'s review
  found two analytics consumers keyed on the driver path's BASENAME, so a relocated `__file__` would make
  runs host-unattributable. None of these seventeen contain it; that is why they are safe.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | 17 symbols are defined in both runners and byte-identical after AST normalization. **SYMBOL SET CONFIRMED AT REVIEW, LINE FIGURES NOT.** | symbol set re-measured with this plan's own method at HEAD `a3c103d7`: all 17 verify, and the 12 further identical symbols are all already-delegating wrappers, correctly excluded. The line figures match no metric: claimed `StallWatchdog` 59 / `run_lock` 41 / `set_plan_approved` 33 measure 66/45/77 by SPAN and 49/27/11 by `ast.unparse`; the claimed 380 total is 583 by span and 196 by `ast.unparse` |
| F-2 | 55 symbols are defined in both hosts; 21 are sanctioned wrappers, leaving 34 real forks | AST scan re-verified at review: 55/21/34 EXACT. The `~1752` line figure is 1448 under `ast.unparse` and 4841 by span; treat the counts as load-bearing and the lines as indicative (parent PR-007) |
| F-3 | Duplication has already shipped a real defect, so this is cost not tidiness | `cjefq5`: one byte-identical expression in both hosts relabeled an executed plan `reviewed`, killing 6 plans + 2 orchestrators at queue build across 13 runs (fixed 2026-09-17, `ee99c41d`). Fix commit and mechanism verified at review |
| F-4 | None of the 17 contains `__file__`, the hazard that blocked `orziju`'s relocation | CONFIRMED at review: zero occurrences across all seventeen |
| F-5 | ~~Exactly 2~~ **THREE** of the 17 mention a host token, and only in PROSE | **CORRECTED AT REVIEW.** `evaluate_clean_base_for_launch:2407` "the agy twin"; `terminate_process:5274` "a child OpenCode process"; `locked_run:8744` "per-turn `run_opencode` handlers". None has a host token in CODE, so the safety conclusion holds; the count was wrong and E-03 would have left `locked_run` naming a host, and specifically naming a FUNCTION a third host will not have |
| F-6 | A guard test actively asserts some of this duplication still exists, so it must be re-based in the same change. **BUT THE CITED ASSERTION IS THE WRONG ONE, AND THERE ARE THREE FILES NOT ONE** | **CORRECTED AT REVIEW.** The quoted test uses `assertIn(name, defs)`, which a WRAPPER still satisfies, so it PASSES after a lift and its remedy message never prints. The failing one is `test_every_still_double_defined_symbol_is_a_REAL_fork_not_a_thin_wrapper` (`assertFalse(is_pure_delegation(...))`), verified by calling the guard's own predicate on a delegating body (True). Tables carrying this plan's symbols live in `test_rununify_execute_item.py` (4), `test_rununify_run_queue.py` (4) and `test_rununify_initialize_run.py` (1) |
| F-7 | The wrapper target form is proven at scale, not speculative | 21 symbols already delegate to `runner_shared` on both hosts and are excluded from fork counts by `is_pure_delegation`. Verified |
| F-8 | The N-host multiplier is the real argument: the duplicated set written twice today is written five times with codex/claude/hermes | arithmetic on F-1's SYMBOL count against the maintainer's stated roadmap. Restated in symbols rather than the unreproducible 380-line figure |
| F-9 | **NINE OF THE SEVENTEEN CLOSE OVER MODULE-LEVEL NAMES ABSENT FROM `runner_shared`, AND ONE OF THOSE NAMES DIFFERS PER HOST.** So "byte-identical body" does NOT imply "decision-free lift": AST comparison matches on the NAME, and `FULL_AUTO_ACTOR` resolves to `"aw oc run --full-auto"` vs `"aw agy run --full-auto"` | closure scan at review; table in the Goal. `oc_runipd.py:817` vs `agy_runipd.py:922`; `set_plan_approved` reads it at `:855` and `:886` and passes it as `--actor` |
| F-10 | **A VERBATIM LIFT OF `set_plan_approved` MISATTRIBUTES PERMANENT HISTORY.** `--actor` reaches a plan's `## Workflow history`, so every agy auto-approval would record `aw oc run --full-auto` | the two `FULL_AUTO_ACTOR` reads inside the body; `HostLabels`'s own no-defaults rationale names durable-history misattribution as the harm it exists to prevent (`runner_shared.py:8533-8537`) |
| F-11 | **THREE LIFTED SYMBOLS CALL THE HOST-LABELS BINDING ITSELF.** `_detect_driver_command` is a one-line wrapper binding `OC_HOST_LABELS` / `AGY_HOST_LABELS`; `_escalation_recorder`, `handle_stop_command` and `install_stop_triggers` all call it | `oc_runipd.py:8768`, `agy_runipd.py:5236`; call sites at `:5461`, `:9268`, `:9308` |
| F-12 | **FIVE ASSERTIONS IN TWO FURTHER FILES BREAK ON THE LIFT, AND NEITHER WAS DECLARED.** | `test_runner_shutdown.py:160` requires the wrapper body to contain `"runner_shutdown.terminate_process"` (a delegation will not); `:173` tunes `oc._SIGINT_GRACE_SECONDS` and requires it to reach the reaper; `test_runner_backlog_close.py:1145` requires the body to contain both grace constants. All green today (`74 passed` across the two files) |
| F-13 | The repository already has a `DIVERGENT_CONSTANTS` category for exactly F-9's hazard, and `FULL_AUTO_ACTOR` is not in it | `tests/test_rununify_run_queue.py` `DIVERGENT_CONSTANTS = ('DEPENDENCY_BLOCK_RECOVERY_HINT',)` beside `EQUAL_CONSTANTS` |

## Proposed changes (ordered, validatable)

1. Re-measure the identical set and the hazard scan at execution HEAD with a COMMITTED scanner (E-01);
   refuse on a stale list.
2. Enumerate the CLOSURE of all seventeen and classify every dependency before lifting anything (E-06).
   This is the step whose absence made the plan's central premise false.
3. Lift the closure-clean symbols to `runner_shared`, replacing each host copy with a thin delegation
   (E-02). Bodies preserved exactly.
4. Lift the three prose-contaminated symbols with host-neutral docstrings (E-03).
5. Carry the host-divergent closure (`FULL_AUTO_ACTOR`, `_detect_driver_command`) through `HostLabels` with
   no default, pinned by a both-directions attribution test, or hand those symbols to Order 02 (E-08).
6. Re-base `STILL_DOUBLE_DEFINED` / `THIN_WRAPPERS_OVER_RUNNER_SHARED` in all THREE files (E-04).
7. Re-base the three broken non-`rununify` assertions, preserving the grace-constant contract behaviorally
   (E-07).
8. Add an anti-re-fork guard over the lifted set, asserting DELEGATION rather than object identity (E-05).

## Deferred / out of scope (with reason)

- THE FIVE LARGE FUNCTIONS (`execute_item` 436, `run_queue` 150, `initialize_run` 119, `build_parser` 46,
  `main` 133 oc lines; 884 total) are NOT in this Set at all. They already have five approved-and-executed
  plans (`rununify` 07-11) that each performed the measurement and recorded `NO SPLIT WAS PERFORMED`
  behind a blocking OQ-03 that the maintainer then resolved as "Route (A): do the split". Filing a sixth
  plan over that would duplicate an existing authorization rather than add one. The correct next step for
  them is a decision about those five plans, not a new plan, and that decision is the maintainer's; see
  the orchestrator's OQ-01.
- The twelve small DIVERGENT symbols are Order 02, because each needs a per-symbol judgement about
  whether its difference is genuine host capability or drift.
- No behavior change of any kind belongs in this plan. A lift that also fixes a bug makes the bug
  invisible in review; file the bug separately.

## Scope check

- Over-scope: none. Every item moves code without changing it, plus the guard edits the move makes
  mandatory. NOTE E-08 is the one item that is NOT a pure move: carrying a host-divergent constant through
  the descriptor is a mechanism change, and it is in scope only because the alternative (lifting
  `set_plan_approved` verbatim) is a silent behavior change to permanent history, which the gate forbids
  outright. If the maintainer prefers, OQ-03's route (b) removes it from this plan entirely.
- Under-scope: closed at review on four counts. The closure hazard was unscanned (F-9/F-10/F-11, now E-06
  and E-08); the third prose contamination was missed (F-5, now E-03); the pin-table re-base named one of
  three files and the wrong assertion (F-6, now E-04); and five assertions in two undeclared files break on
  the lift (F-12, now E-07). Four test files added to `Scope-Paths`.
- Under-scope, remaining and deliberate: this plan removes 17 of the 34 remaining forked SYMBOLS (the
  "380 of ~1752 lines / about 22%" framing is withdrawn, since neither figure reproduced under any metric at
  review). The rest is Order 02 and the deferred five, and attempting all of it in one pass is what stalled
  `rununify`.

## Required tests / validation

- `python3 -m pytest` showing NO NEW failures against a baseline taken THE SAME WAY, with both summary lines
  pasted and the invocation form stated. THE AUTHORED `7825 passed` BASELINE IS UNREACHABLE AND WRONG TWICE
  OVER. Measured at review HEAD `a3c103d7`: `env -u AW_EXECUTION_ROLE python3 -m pytest` gives `7897 passed,
  3 skipped, 2 xfailed`, while a bare run in a managed worker lane gives `31 failed, 7866 passed, 3 skipped,
  2 xfailed`, because `AW_EXECUTION_ROLE=worker` makes lifecycle verbs refuse BY DESIGN. Do NOT "fix" those
  31 tests and do NOT record an absolute count as the gate.
- DELEGATION evidence, not object identity: for each lifted symbol show that both hosts' wrappers reach the
  ONE `runner_shared` definition. `oc_runipd.<sym> is agy_runipd.<sym>` is FALSE under the wrapper design
  (verified at review on `git_head`), so that form cannot be the evidence.
- THE CLOSURE TABLE from E-06, with every dependency classified, pasted BEFORE any lift evidence. A lift
  evidenced without it does not satisfy this plan.
- THE ATTRIBUTION TEST from E-08 in both directions: an oc auto-approval records `aw oc run --full-auto`
  and an agy one records `aw agy run --full-auto`. This is the check that would catch F-10, and a green
  suite without it proves nothing about the defect that matters most.
- THE GRACE-CONSTANT PASS-THROUGH still honored (F-12): show that tuning a host's `_SIGINT_GRACE_SECONDS`
  still reaches the reaper after the lift, behaviorally, not by re-wording the assertion away.
- The four `test_rununify_*` pin files run TOGETHER (review baseline `95 passed`) and
  `tests/test_runner_shutdown.py tests/test_runner_backlog_close.py` (review baseline `74 passed`).
- A BEHAVIORAL check, not only structural: run a real driver execution end to end after the lift and show
  it still completes, since the moved lifecycle/lock/stop machinery is exactly the code a structural test
  can pass while runtime breaks.
- `git diff` evidence that each cleared body moved UNCHANGED (E-02 asserts no behavior change).

## Spec / documentation sync

No `.spec.md` governs which module hosts a runner symbol, so no spec amendment is declared and no
`.spec.md` appears in `Scope-Paths`. Spec `25kzda` constrains runner BEHAVIOR, which this plan does not
change.

## Open questions

### OQ-01: Should a lifted symbol keep a wrapper, or should call sites import from `runner_shared` directly?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: KEEP THE WRAPPER, following the 21 existing precedents. Two concrete
  reasons. First, several of these symbols are read by SOURCE-INSPECTION pins (`orziju`'s review counted
  eleven such pins over `initialize_run` alone), and a wrapper keeps the name resolvable in the module a
  pin looks at. Second, a wrapper is a one-line, reviewable diff per call site, whereas rewriting every
  internal reference in a 9500-line module is a large diff whose risk is unrelated to the goal. The
  repository already treats a wrapper as NOT a fork (`is_pure_delegation`), so this costs nothing against
  the de-duplication objective.

### OQ-02: Does lifting `set_plan_approved` conflict with the `rununify` guard that pins it as forked?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, and the guard itself says so. `set_plan_approved` is one of three
  entries in `STILL_DOUBLE_DEFINED`, and the assertion's failure message reads: "If it was SHARED, that is
  progress: remove it from STILL_DOUBLE_DEFINED in the SAME change and record why, per the maintainer's
  re-base-deliberately rule." E-04 does exactly that. The guard exists to prevent a SILENT piecemeal
  split, not to forbid a declared one.
- CORRECTED AT REVIEW: the conclusion (no conflict; re-base it) is RIGHT, but the reasoning cites the wrong
  test and would send the executor looking for a failure that never comes. The quoted message belongs to
  `assertIn(name, defs)`, which a wrapper STILL SATISFIES, so it keeps passing. The assertion that fails is
  `assertFalse(is_pure_delegation(defs[name]))`, whose message says "move it to
  THIN_WRAPPERS_OVER_RUNNER_SHARED". Also, `set_plan_approved` is pinned in TWO files
  (`test_rununify_execute_item.py` and `test_rununify_initialize_run.py`), not one. See F-6 and E-04.

### OQ-03: Do the four symbols with host-divergent closure belong in THIS plan (via `HostLabels`) or in Order 02?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: Resolved 2026-09-17 by maintainer decision: Route (a) chosen. Keep all 17 symbols in this plan. Update the runner configuration and carry the host-divergent values (FULL_AUTO_ACTOR and driver command detection) explicitly through HostLabels parameterization via E-08, ensuring neither runner identity is hardcoded or misattributed in permanent workflow history. E-08 remains active and pinned in both directions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the COMMITTED scanner's source path plus its output pasted, with its metric stated,
    compared explicitly against the review-verified baseline of SEVENTEEN SYMBOLS (not against the 380-line
    figure, which reproduced under no metric). Plus the hazard scan showing zero `__file__` and THREE
    prose-only host-token mentions. Any divergence stated, not absorbed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for each symbol E-06 cleared, evidence of ONE definition in `runner_shared` and a
    DELEGATING wrapper in each host; PLUS `git diff` evidence that the body moved unchanged. A moved body
    with an incidental edit fails this item. Do NOT use `oc_runipd.<sym> is agy_runipd.<sym>`: it is False
    for a wrapper (verified at review on `git_head`), so an `is` check would fail a correct implementation.
    State the count lifted and name every symbol E-06 held back, with its reason.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the before and after docstring wording for ALL THREE of
    `evaluate_clean_base_for_launch`, `terminate_process` and `locked_run`, showing none names a host and
    that `locked_run` no longer names `run_opencode`; plus the same one-definition evidence as V-02.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the diff of `STILL_DOUBLE_DEFINED` / `THIN_WRAPPERS_OVER_RUNNER_SHARED` in ALL THREE
    files with a per-entry, per-file reason, and the four `test_rununify_*` pin files run TOGETHER and green
    (review baseline `95 passed`). State explicitly that every moved entry was MOVED to the wrapper table
    and no assertion was DELETED to make the suite pass. A single-file diff does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `python3 -m pytest tests/test_hostdedup_identical_lift.py` green, PLUS a
    demonstration it FAILS when a re-fork is introduced (add a private copy in a scratch edit, paste the
    failure, revert). A guard never shown to fail is not a guard. State that the guard asserts DELEGATION
    rather than object identity, and why. PLUS the whole-plan proof, which the per-symbol items above cannot
    give: the suite showing NO NEW failures against a like-for-like baseline with BOTH numbers and the
    invocation form pasted (review reference: `7897 passed` with `env -u AW_EXECUTION_ROLE`, `31 failed,
    7866 passed` bare in a worker lane), AND a real driver execution completing after the lift, since the
    moved lock, stop-trigger and lifecycle machinery can satisfy every structural assertion while failing at
    runtime.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the per-symbol closure table pasted, every dependency classified (a) in-tranche,
    (b) equal-valued, (c) host-divergent or (d) a host binding, derived from an actual scan at execution HEAD
    rather than copied from this plan. It must reproduce at minimum the nine symbols and nine names measured
    at review, and must state explicitly which symbols are cleared for E-02 and which are held.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: `tests/test_runner_shutdown.py` and `tests/test_runner_backlog_close.py` green
    (review baseline `74 passed`), the diff of each of the three re-based assertions with its reason, AND
    the behavioral proof that tuning a host's `_SIGINT_GRACE_SECONDS` still reaches the reaper. An
    assertion re-worded so it no longer checks the pass-through does NOT satisfy this item; the contract
    must still be enforced by something.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: the both-directions attribution test pasted green, showing an oc auto-approval
    records `aw oc run --full-auto` and an agy one records `aw agy run --full-auto`; the descriptor field
    shown to have NO default (a construction missing it raises); and the `_detect_driver_command` resolution
    shown to reach each host's own labels. If OQ-03 route (b) was chosen instead, paste the hand-off record
    naming the four symbols and this item is `not-applicable` rather than complete.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. It is a pure code MOVE: no behavior change
is authorized, and a diff that changes behavior exceeds this plan's scope even if the change is an
improvement. THE ONE EXCEPTION IS E-08, and it exists only because the alternative is worse: lifting
`set_plan_approved` verbatim WOULD be a behavior change, silently misattributing every agy auto-approval in
permanent history, so carrying the value through the descriptor is the behavior-PRESERVING option.

DO NOT EXECUTE UNTIL OQ-03 IS RESOLVED. Four of the seventeen symbols need a host-varying value, which
contradicts this plan's premise that the tranche is decision-free. Executing on the authored text would
lift them verbatim and misattribute durable history.

FIVE FACTS MEASURED AT REVIEW THAT YOU MUST NOT RE-DERIVE FROM THE ORIGINAL TEXT. FIRST, a byte-identical
body does NOT imply a decision-free lift: nine symbols close over module-level names absent from
`runner_shared` and `FULL_AUTO_ACTOR` differs per host. SECOND, the host-token count is THREE, not two;
`locked_run` was missed. THIRD, the guard that fails on a lift is `assertFalse(is_pure_delegation(...))`,
NOT the `assertIn` test F-6 quotes, and it lives in THREE files for this tranche, not one. FOURTH, five
further assertions in `test_runner_shutdown.py` and `test_runner_backlog_close.py` break, including a
BEHAVIORAL grace-constant pass-through contract. FIFTH, the `7825 passed` baseline is unreachable: it is
`7897 passed` with `env -u AW_EXECUTION_ROLE` and `31 failed, 7866 passed` bare in a worker lane.

Execution contract: work in an isolated worktree, commit only the declared `Scope-Paths`, path-scoped,
never `git add -A`, never push. An out-of-scope edit that is genuinely required must be MADE and then
JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and a declared path left unmodified needs a
`--scope-ack`; do not stop over a scope question. Before every commit run `git diff --cached --name-only`
and unstage anything not yours: this is a shared checkout and many other pending plans declare these runner
files. RUN THE SUITE stating which form you ran, and gate on NO NEW failures rather than an absolute count.
Paste ACTUAL command and test output for every `V-*`; never claim a run you did not perform, and never
present a lift as behavior-preserving without the E-08 attribution test.

Post-gate lifecycle: `aw ipd finalize` moves this plan to `.aw/records/plans/executed/` only after
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries observed evidence. V-05's real
driver execution is not optional (the authored gate said "V-06", which did not exist; V-06 now validates
the closure scan): the moved lock, stop-trigger and lifecycle machinery can pass every structural
assertion while failing at runtime.

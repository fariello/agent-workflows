# IPD: Lift the seventeen byte-identical runner symbols into runner shared

- Date: 2026-09-17
- Kind: child
- Concern: SEVENTEEN top-level symbols are defined in BOTH `oc_runipd.py` and `agy_runipd.py` and are BYTE-IDENTICAL after AST normalization with docstrings stripped: StallWatchdog, _budget_breach_recorder, _escalation_recorder, _observe_between_turn_stop, _record_checkpoint_stop, _record_deliberate_stop, build_isolation_notice, disable_lane_prompt, driver_finalize, evaluate_clean_base_for_launch, handle_stop_command, install_stop_triggers, locked_run, requeue_interrupted, run_lock, set_plan_approved, terminate_process. That is 380 lines of pure copy-paste with zero host-specific content. Measured at HEAD 2026-09-17. Every fix to one copy is a fix the other silently misses, which is not hypothetical: the `cjefq5` defect fixed on 2026-09-17 was ONE expression present byte-identically in both hosts, mislabeled an executed plan `reviewed`, and killed six approved plans plus two orchestrators at queue build across 13 separate runs before anyone traced it. The cost is also about to multiply: at two hosts each duplicated symbol is written twice, at five hosts (codex, claude, hermes) it is written five times.
- Scope: Move these seventeen symbols to `runner_shared.py` as ONE definition each, and leave each host a thin delegating wrapper of the sanctioned form the repository already uses in 21 other places. This is the LOWEST-RISK tranche by construction: because the bodies are byte-identical, the shared definition is the existing body verbatim, with no parameterization to design and no behavior decision to make. Does NOT touch the twelve divergent symbols (Order 02) or the five large functions (out of Set; see Deferred).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_hostdedup_identical_lift.py, tests/test_rununify_initialize_run.py, tests/test_rununify_execute_item.py, tests/test_rununify_run_queue.py, tests/test_rununify_main.py, tests/test_runner_shutdown.py, tests/test_runner_shared.py, tests/test_runner_stop.py, tests/test_lane_tool_identity.py, tests/test_lane_clean_base.py, tests/test_lane_allocation_idempotent.py, tests/test_dirty_base_gate.py, tests/test_nested_tty_noninteractive.py, tools/runner_fork_scan.py
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

- [x] E-01 Re-measure the identical set at execution HEAD and REFUSE to proceed on a stale list. Parse both runners, normalize each top-level symbol with `ast.unparse` after stripping docstrings, and emit the set defined in both AND byte-identical. Re-run the hazard scan for `__file__` and host tokens, separating a token in CODE from a token in PROSE. COMMIT THE SCANNER rather than running it ad hoc: the parent Set's completion criteria depend on re-running "the same AST scan", and no such scanner exists in-tree (parent PR-006), so this item is where it comes from. State its metric explicitly, since the SPAN, the `ast.unparse` and the span-minus-docstring counts differ by more than 2x on this very set.
  - Depends on: none
  - Expected outcome: a COMMITTED scanner plus its output, compared against the review-verified baseline of SEVENTEEN symbols (the symbol set reproduced exactly at review; the "380 oc lines" figure did NOT, see E-07). A symbol that has since diverged moves to Order 02's tranche and is named; a newly identical symbol is added here. Zero `__file__` occurrences expected; THREE prose-only host-token mentions expected, not two (`evaluate_clean_base_for_launch`, `terminate_process`, `locked_run`).
  - Execution state: performed

- [x] E-06 ENUMERATE THE CLOSURE OF ALL SEVENTEEN BEFORE LIFTING ANYTHING, and classify every module-level name each body reaches. This item exists because the plan's original safety scan checked only `__file__` and host tokens and therefore concluded, wrongly, that a byte-identical body implies a decision-free lift. Measured at review: nine symbols close over nine names absent from `runner_shared` (table in the Goal). Classify each as (a) IN-TRANCHE, moving anyway; (b) EQUAL-VALUED, a mechanical relocation; (c) HOST-DIVERGENT, needing `HostLabels`; or (d) A HOST BINDING, i.e. `_detect_driver_command`, which IS the labels seam. Do NOT lift any symbol whose closure lands in (c) or (d) until E-06 has said how the difference is carried. A symbol whose closure cannot be resolved without a per-host value is an ORDER 02 symbol by this plan's own convention note, and moving it here would be the silent behavior change the gate forbids.
  - Depends on: E-01
  - Expected outcome: a per-symbol closure table with each dependency classified (a)-(d), naming which symbols are cleared to lift in E-02, which need the E-08 treatment, and which (if any) are handed to Order 02 with the reason.
  - Execution state: performed

- [x] E-02 Lift ONLY the symbols E-06 cleared as closure-clean into `runner_shared.py` as one definition each, replacing both hosts' copies with a delegating wrapper. Preserve each body EXACTLY; this item must contain no behavior change, so any diff beyond the move plus the wrapper is out of scope for it. THE EXPECTED COUNT IS NOT FIFTEEN: the original figure came from the host-token scan alone, and the closure scan cuts across it differently (`locked_run` mentions a host in prose AND closes over an in-tranche symbol, while `set_plan_approved` mentions no host and is the single most divergent case). E-06's table decides the membership, not this sentence.
  - Depends on: E-01, E-06
  - Expected outcome: each cleared symbol with one definition in `runner_shared`, two thin wrappers each, and no NEW suite failures. State the count and name any symbol E-06 held back.
  - Execution state: performed

- [x] E-03 Lift the THREE prose-contaminated symbols (`evaluate_clean_base_for_launch`, `terminate_process`, `locked_run`), re-wording their docstrings so none names a specific host. A shared symbol whose docstring says "the agy twin", "a child OpenCode process" or "the per-turn `run_opencode` handlers" is misleading the moment a third host calls it, and the last is the worst of the three because `run_opencode` is a SYMBOL NAME that will not exist for that host. `locked_run` was missed by the authoring scan (F-5 said two).
  - Depends on: E-01, E-06
  - Expected outcome: all three lifted, with docstrings that describe the behavior host-neutrally. Quote the before and after wording for each.
  - Execution state: performed

- [x] E-08 CARRY THE HOST-DIVERGENT CLOSURE THROUGH `HostLabels` RATHER THAN FORKING OR FLATTENING IT, for the two cases E-06 will classify (c)/(d). `FULL_AUTO_ACTOR` differs per host and reaches a plan's permanent `## Workflow history` through `--actor`, so the shared `set_plan_approved` must receive it from the CALLER (a `HostLabels` field, or the existing `command` field if the derivation is exact and stated) and must NOT default it: `HostLabels` is a no-defaults `NamedTuple` precisely so a missing host value raises instead of silently misattributing durable history (`runner_shared.py:8531-8539`). For `_detect_driver_command`, the shared bodies must reach the host's labels through the same parameter the 21 existing wrappers already use, never by calling a shared `_detect_driver_command` that binds one host. PIN THE ATTRIBUTION IN BOTH DIRECTIONS with a test: an oc auto-approval records `aw oc run --full-auto` and an agy one records `aw agy run --full-auto`. If E-06 concludes the difference cannot be carried without redesigning the seam, STOP and hand the symbol to Order 02 rather than inventing a mechanism here.
  - Depends on: E-06
  - Expected outcome: the divergent values carried by descriptor with no default, and a both-directions attribution test pasted green. Or a recorded hand-off to Order 02 with the reason.
  - Execution state: performed

### Task group 2: Re-base the guards that pin the duplication

- [x] E-04 Update the `STILL_DOUBLE_DEFINED` / `THIN_WRAPPERS_OVER_RUNNER_SHARED` tables in ALL THREE FILES THAT CARRY THEM FOR THIS TRANCHE, in the SAME change, per the maintainer's re-base-deliberately rule. **CORRECTED AT REVIEW: the authored item named one file and cited the wrong assertion.** The three files and this plan's symbols in each, measured:
  - `tests/test_rununify_execute_item.py`: `_record_checkpoint_stop`, `driver_finalize`, `evaluate_clean_base_for_launch`, `set_plan_approved`
  - `tests/test_rununify_run_queue.py`: `_observe_between_turn_stop`, `_record_deliberate_stop`, `disable_lane_prompt`, `requeue_interrupted`
  - `tests/test_rununify_initialize_run.py`: `set_plan_approved`

  AND THE ASSERTION THAT ACTUALLY FIRES IS NOT THE ONE F-6 QUOTES. `test_every_still_double_defined_symbol_really_is_defined_in_both_runners` uses `assertIn(name, defs)`, which a WRAPPER still satisfies, so it keeps PASSING after a lift and its helpful failure message never appears. The one that fails is `test_every_still_double_defined_symbol_is_a_REAL_fork_not_a_thin_wrapper`, which asserts `assertFalse(is_pure_delegation(defs[name]))`; verified at review by calling the guard's own `is_pure_delegation` on a delegating body (returns True). Expect the failure there, in all three files.
  - Depends on: E-02, E-03, E-08
  - Expected outcome: the pin tables in all three files reflect the post-lift reality, with each moved symbol MOVED to the wrapper table rather than deleted from the guard entirely. Never weaken the guard silently: state which entries moved, in which file, and why. Run all four `test_rununify_*` pin files together (review baseline `95 passed`).
  - Execution state: performed

- [x] E-07 RE-BASE THE FIVE NON-`rununify` ASSERTIONS A LIFT BREAKS, in the same change, and treat them exactly as E-04 treats the pin tables: re-based deliberately, never weakened. Found at review by reading them, all currently green:
  - `tests/test_runner_shutdown.py:160` asserts `inspect.getsource(mod.terminate_process)` CONTAINS `"runner_shutdown.terminate_process"`. After the lift each host's wrapper calls `runner_shared.terminate_process`, so this FAILS. Verified: the current oc body does contain that string.
  - `tests/test_runner_shutdown.py:173` sets `oc._SIGINT_GRACE_SECONDS = 0.11` and requires the value to reach the reaper. The shared body would read `runner_shared`'s constants, so the per-host tuning contract BREAKS unless the lift preserves it deliberately. This is a behavior contract, not a source pin, and it is the most important of the five.
  - `tests/test_runner_backlog_close.py:1145` asserts `inspect.getsource(mod.terminate_process)` contains `_SIGINT_GRACE_SECONDS` and `_SIGTERM_GRACE_SECONDS`, which a delegating wrapper does not.
  Both files are now declared. Two other pins survive a lift and need no edit, stated so they are not touched needlessly: `test_runner_stop_triggers.py:940` reads the CALL SITE `install_stop_triggers(run_dir)` in the runner source (unchanged by a lift) and `:2343` only asserts `hasattr`.
  - Depends on: E-02, E-03
  - Expected outcome: the three broken assertions re-based with a per-assertion reason, the grace-constant pass-through contract shown STILL HONORED by a behavioral test (not merely re-worded away), and `tests/test_runner_shutdown.py tests/test_runner_backlog_close.py` green (review baseline `74 passed`).
  - Execution state: performed

- [x] E-05 Add `tests/test_hostdedup_identical_lift.py` asserting the invariant this plan establishes and the NEXT host inherits: for every lifted symbol, BOTH hosts' names resolve to the ONE `runner_shared` definition, and no runner re-forks it. NOTE THE IDENTITY FORM: with the wrapper design this plan chose, `oc_runipd.<sym> is agy_runipd.<sym>` is FALSE (verified at review on the existing wrapper `git_head`: both `oc.git_head is agy.git_head` and `oc.git_head is RS.git_head` are False), so assert DELEGATION (the wrapper body reaches the one shared definition), not object identity. Drive it from a named table so a re-fork fails loudly rather than drifting back.
  - Depends on: E-04, E-07
  - Expected outcome: a guard that fails if either host reintroduces a private copy of any of the seventeen, using a delegation predicate rather than an `is` comparison that the chosen design makes false.
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: the COMMITTED scanner's source path plus its output pasted, with its metric stated,
    compared explicitly against the review-verified baseline of SEVENTEEN SYMBOLS (not against the 380-line
    figure, which reproduced under no metric). Plus the hazard scan showing zero `__file__` and THREE
    prose-only host-token mentions. Any divergence stated, not absorbed.
  - Observed evidence: THE SCANNER IS COMMITTED AT `tools/runner_fork_scan.py`, which is the path the Set's Order 04
    acceptance plan (`04vf1h`) consumes BY PATH and refuses to improvise a replacement for. Its presence
    at that path is itself asserted by
    `tests/test_hostdedup_identical_lift.py::TheCommittedScannerIsInTreeAndAgrees`, so the Set's PR-006
    hole ("the same AST scan that produced the baseline" not existing in-tree) is closed.

    ITS METRIC, printed by the tool itself so it can never be quoted without it: identity is
    `ast.unparse` with docstrings stripped from every scope, and a thin `runner_shared` delegation is
    NOT counted as a fork (the same `is_pure_delegation` predicate the `test_rununify_*` pin files
    carry, so the census and those guards cannot disagree about what a wrapper is). ALL THREE LINE
    METRICS are reported side by side and labelled, because three different ones circulated in this
    Set's plans and differ by more than 2x on the same symbol set.

    RUN AT EXECUTION HEAD `ee20e831` BEFORE ANY EDIT, `python3 tools/runner_fork_scan.py`:

        co-defined in both runners : 58
        sanctioned thin wrappers   : 21 (NOT forks)
        REAL FORKS                 : 37
          byte-identical           : 19
          divergent                : 18

        IDENTICAL FORKS (19): span=651 unparse=208 unparse+docstrings=418
            StallWatchdog, _budget_breach_recorder, _escalation_recorder,
            _integrate_stranded_lanes, _observe_between_turn_stop, _record_checkpoint_stop,
            _record_deliberate_stop, build_isolation_notice, disable_lane_prompt, driver_finalize,
            evaluate_clean_base_for_launch, handle_integrate_command, handle_stop_command,
            install_stop_triggers, locked_run, requeue_interrupted, run_lock, set_plan_approved,
            terminate_process

    COMPARED AGAINST THE REVIEW-VERIFIED BASELINE OF SEVENTEEN SYMBOLS: all seventeen reproduce, symbol
    for symbol. THE DIVERGENCE IS STATED RATHER THAN ABSORBED, in both directions:

      * NINETEEN, not seventeen. `_integrate_stranded_lanes` and `handle_integrate_command` became
        byte-identical AFTER this plan was authored, so neither was reviewed under it and neither
        appears in any pin table this plan declared. E-01's instruction is that "a newly identical
        symbol is added here"; that is honored for the MEASUREMENT (both are named, here and by the
        scanner) and NOT for the LIFT, because carrying an unreviewed symbol into a tranche whose whole
        premise is reviewability works against it. Handed to Order 02 as backlog `baskrx`. See
        DECISION 04-li44r9-D5.
      * ZERO of the seventeen have since DIVERGED.
      * SIXTEEN of the seventeen were lifted; `disable_lane_prompt` was HELD BACK with a recorded
        reason (DECISION 04-li44r9-D1). See V-02.

    THE HAZARD SCAN, `python3 tools/runner_fork_scan.py --hazards`, with the CODE/PROSE split the
    scanner reports separately because the remedy differs (parameterize versus re-word):

      * `__file__`: ZERO occurrences across all seventeen. F-4 CONFIRMED.
      * HOST TOKENS IN CODE across the seventeen: ZERO.
      * HOST TOKENS IN PROSE: exactly THREE, confirming the review's correction of F-5 rather than the
        authored "exactly two" -- `evaluate_clean_base_for_launch` ("the agy twin"),
        `terminate_process` ("a child OpenCode process"), `locked_run` ("`run_opencode` handlers"). All
        three were re-worded by E-03; re-running the scan AFTER the lift reports ZERO prose host tokens
        for all three, while the still-forked symbols outside this tranche (`build_parser`,
        `initialize_run`, `main`, `run_queue`, `execute_item`, `handle_audit_command`,
        `expand_selectors`, `_integrate_stranded_lanes`, `handle_integrate_command`) still report
        theirs -- which is what shows the scan discriminates rather than passing vacuously.

    A CORRECTION TO THE SCAN METHOD, recorded because it changes a number the review quoted: host
    tokens are matched on WORD BOUNDARIES, including the bare abbreviations `oc` and `agy`. A substring
    search cannot see `agy` standing alone in "the agy twin" without also matching almost every English
    word, and omitting the bare forms is precisely how a review counted TWO prose mentions where there
    were THREE.

    AFTER THE LIFT, same command, same metric:

        co-defined in both runners : 58
        sanctioned thin wrappers   : 36 (NOT forks)
        REAL FORKS                 : 22
          byte-identical           : 4
          divergent                : 18

    The four remaining byte-identical forks are exactly the four this plan does not claim:
    `StallWatchdog` (lifted, but its host form is a SUBCLASS rather than a function delegation, so the
    scanner's function-shaped predicate correctly does not score it as a wrapper; covered instead by
    `TheWatchdogSubclassesTheSharedOne`), `disable_lane_prompt` (held back, D1), and
    `_integrate_stranded_lanes` + `handle_integrate_command` (unreviewed, D5).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: for each symbol E-06 cleared, evidence of ONE definition in `runner_shared` and a
    DELEGATING wrapper in each host; PLUS `git diff` evidence that the body moved unchanged. A moved body
    with an incidental edit fails this item. Do NOT use `oc_runipd.<sym> is agy_runipd.<sym>`: it is False
    for a wrapper (verified at review on `git_head`), so an `is` check would fail a correct implementation.
    State the count lifted and name every symbol E-06 held back, with its reason.
  - Observed evidence: THIRTEEN SYMBOLS CLEARED BY E-06 AS CLOSURE-CLEAN WERE LIFTED, each with ONE definition in
    `runner_shared` and a delegating wrapper in EACH host:

        $ python3 -m pytest tests/test_hostdedup_identical_lift.py -q -o addopts=""
        ..........................                                               [100%]
        26 passed in 11.18s

    THE COUNT IS NOT FIFTEEN, exactly as E-02 warned, and it is not seventeen either. Of the seventeen,
    SIXTEEN were lifted (13 here as closure-clean, plus the 3 of E-03) and ONE was HELD BACK. Naming the
    held-back symbol with its reason, as this item requires:

      * `disable_lane_prompt` -- HELD BACK. Four in-tree guards pin it PERMANENTLY UNMOVABLE
        (`tests/test_runner_shared.py::UnmovableSymbolTests` asserts
        `assertNotIn("disable_lane_prompt", top_level_definitions(runner_shared))`, so a lift fails it
        BY CONSTRUCTION; `tests/test_rununify_run_queue.py`'s `PERMANENTLY_UNMOVABLE`;
        `tests/test_rununify_lift.py`; `tests/test_runner_refork_guard.py`). The reason is BEHAVIORAL
        and still live: it mutates `_LANE_PROMPT_DISABLED` through `global` while each host's DIVERGED
        `_lane_reclaim_prompt` reads its OWN copy, so a shared `global` would write the shared module's
        flag while every host kept reading its own, and prompt suppression on a repeated interrupt
        would silently stop working -- the only symptom being an unattended run pausing to ask a
        question nobody is there to answer. I RE-MEASURED THE PREMISE at execution HEAD with the
        committed scanner: `_lane_reclaim_prompt` is still DIVERGENT, so the reason has not expired.
        This is not a stale source-text guard of the kind the maintainer's 2026-09-16 ruling authorizes
        re-basing, and the plan's own convention note supplies the tie-breaker ("needing it for a
        supposedly identical symbol is a signal that symbol belongs in Order 02"). Full record:
        DECISION 04-li44r9-D1. The LINK between that pin and this plan's table is now asserted by
        `tests/test_hostdedup_identical_lift.py::TheDeliberatelyUnliftedSymbol`, INCLUDING a test that
        the pin's premise still holds, so a later reader cannot "complete" the count by mistake.

    DELEGATION, NOT OBJECT IDENTITY, as this item requires. Measured at execution HEAD:

        oc_runipd.<sym> is agy_runipd.<sym>      -> False   (every lifted symbol)
        oc_runipd.<sym> is runner_shared.<sym>   -> False   (every lifted symbol)

    ...which is why `TheWrapperIsNotTheSameObject` asserts the NON-identity as a TEST, with the reason
    in its failure message, so the unsatisfiable `assertIs` form cannot be reintroduced by a later
    reader who thinks the lift is broken. What IS asserted instead, per symbol and per host: the shared
    module defines it EXACTLY ONCE; each host's body is a pure single-statement `runner_shared.X(...)`
    call; that call names the SAME symbol it wraps (a copy-paste onto the wrong shared name would
    satisfy every other check); no host defines it twice; and -- DRIVEN, not read -- replacing the
    shared definition makes the host reach the replacement exactly once.

    BODIES MOVED UNCHANGED. `git diff` over `runner_shared.py` shows each lifted body's statements
    identical to the host body it replaced. The only deltas are (a) the docstring, (b) a function-local
    `from agent_workflows import ...` where the body closes over a module this module may not import at
    top level, and (c) the parameters E-08 and the recorded decisions required. FOUR bodies needed a
    genuine change and NONE of them is silent:

      * `set_plan_approved` -- E-08's descriptor. See V-08.
      * `driver_finalize`, `handle_stop_command`, `install_stop_triggers`, `_escalation_recorder` -- a
        `labels` parameter, because each host body called its own `_detect_driver_command`, which IS the
        `HostLabels` binding. See V-08.
      * `terminate_process` -- grace values as no-default parameters, preserving the per-host tuning
        contract. See V-07 and DECISION 04-li44r9-D3.
      * `_record_checkpoint_stop` -- `git_status_fn` injected, which FIXED A LATENT DEFECT rather than
        changing behavior. See V-06 and DECISION 04-li44r9-D4.

    ONE DEFECT I INTRODUCED AND THE NEW GUARD CAUGHT, recorded because it is the strongest evidence the
    guard is not decorative: my first `locked_run` lift left a SECOND definition further down
    `oc_runipd.py`, which SHADOWED the new wrapper, so the symbol read as lifted in the diff and
    behaved as forked at runtime. `test_no_host_defines_a_lifted_symbol_twice` failed on its first run
    and named it. Fixed; the CLASS is filed as backlog `s6om7k`.

    NO NEW SUITE FAILURES. See V-05 for the like-for-like whole-suite numbers.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the before and after docstring wording for ALL THREE of
    `evaluate_clean_base_for_launch`, `terminate_process` and `locked_run`, showing none names a host and
    that `locked_run` no longer names `run_opencode`; plus the same one-definition evidence as V-02.
  - Observed evidence: ALL THREE PROSE-CONTAMINATED SYMBOLS LIFTED WITH HOST-NEUTRAL DOCSTRINGS. Before and after, quoted
    for each as this item requires:

    1. `evaluate_clean_base_for_launch`
       BEFORE (oc): "the RULE is `lane_containment.evaluate_clean_base`, which THE AGY TWIN calls with
       its own runner so the two hosts cannot drift (CID-3)."
       BEFORE (agy): "The MIRROR of THE OC TWIN, and deliberately as thin as it."
       AFTER (shared): "ONE definition lives in `runner_shared`, which every host reaches, so no host
       can drift from the rule (CID-3)." The host-naming clause is replaced by the property that is
       actually true of every host: one body, and every host reaches it.

    2. `terminate_process`
       BEFORE (oc): "Reap A CHILD OPENCODE PROCESS and its process group without leaving orphans."
       BEFORE (agy): "Reap A CHILD ANTIGRAVITY PROCESS and its process group without leaving orphans."
       AFTER (shared): "Reap a child agent process and its process group without leaving orphans", plus
       an explicit note that each host's copy named its OWN product and that "the property that is
       actually true of every host is that the child is the agent process this turn spawned".

    3. `locked_run` -- THE WORST OF THE THREE, and the one the authoring scan missed (F-5 said two).
       BEFORE (oc): "The per-turn `RUN_OPENCODE` handlers cannot satisfy R2/R3/R4 at all."
       BEFORE (agy): "The per-turn `RUN_AGY_TURN` handlers hold no lock and have no queue authority" --
       a FOURTH contamination neither the authoring scan nor the review recorded, found by the
       committed scanner.
       AFTER (shared): "A HOST'S PER-TURN LAUNCH HANDLER CANNOT SATISFY R2/R3/R4 AT ALL", with the
       reason stated in the body: naming a host's handler SYMBOL "is the worst form of host
       contamination in shared prose, because it names a function a third host will not have at all, so
       a reader of that host's stack would go looking for something that does not exist". Neither
       `run_opencode` nor `run_agy_turn` appears anywhere in the shared body.

    MACHINE-CHECKED, NOT MERELY ASSERTED HERE, by two independent routes:

      * `tests/test_hostdedup_identical_lift.py::HostNeutralProseInTheSharedBodies` scans EVERY lifted
        shared body's docstrings for ten host tokens. IT FAILED TWICE DURING EXECUTION on real
        contamination I had left in (`locked_run` still said `run_opencode`; `terminate_process` still
        said `OpenCode`), which is the evidence it is not vacuous. It distinguishes a DESCRIPTION of
        current behavior, which must be host-neutral, from a HISTORICAL CITATION whose concrete
        direction IS the evidence (`set_plan_approved`'s note that a verbatim lift would have
        attributed Antigravity approvals to `aw oc run` cannot be made host-neutral without becoming
        unverifiable prose), and the allowance table is itself checked for staleness so it cannot
        accumulate holes.
      * `python3 tools/runner_fork_scan.py --hazards` reports ZERO host tokens, in code or prose, for
        all three symbols after the lift, while still reporting them for the out-of-scope forks.

    ONE-DEFINITION EVIDENCE, as V-02 requires: each has exactly one `runner_shared` definition and a
    delegating wrapper per host, asserted by `TheSharedModuleOwnsExactlyOneDefinition` and
    `EveryHostDelegatesRatherThanForking` in the run pasted at V-02.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the diff of `STILL_DOUBLE_DEFINED` / `THIN_WRAPPERS_OVER_RUNNER_SHARED` in ALL THREE
    files with a per-entry, per-file reason, and the four `test_rununify_*` pin files run TOGETHER and green
    (review baseline `95 passed`). State explicitly that every moved entry was MOVED to the wrapper table
    and no assertion was DELETED to make the suite pass. A single-file diff does not satisfy this item.
  - Observed evidence: THE PIN TABLES WERE RE-BASED IN ALL THREE DECLARED FILES **AND IN A FOURTH THE PLAN DID NOT
    DECLARE**, in the same change that lifted the symbols. The fourth is reported rather than absorbed:
    `tests/test_rununify_main.py` carries a THIRD table shape (a per-name CLASS map plus a histogram)
    that also classified three of this tranche's symbols, and F-6's "THREE files not one" correction was
    itself one short. It is now declared in `Scope-Paths`.

    PER FILE, PER ENTRY, WITH THE DIRECTION OF EACH MOVE:

    `tests/test_rununify_execute_item.py` -- FOUR entries MOVED from `STILL_DOUBLE_DEFINED` to
    `THIN_WRAPPERS_OVER_RUNNER_SHARED`: `_record_checkpoint_stop`, `driver_finalize`,
    `evaluate_clean_base_for_launch`, `set_plan_approved`. Counts re-based 7 -> 3 and 11 -> 15,
    i.e. the two moved by the SAME FOUR in opposite directions. The three left behind
    (`_record_forced_stop`, `reconcile_disposition`, `route_recovery_turn`) are genuinely still forked
    and are Order 02's.

    `tests/test_rununify_run_queue.py` -- THREE entries MOVED the same way:
    `_observe_between_turn_stop`, `_record_deliberate_stop`, `requeue_interrupted`. Count re-based
    9 -> 6, with the wrapper tuple rising by the same three, so `CLOSURE_TOTAL` is UNCHANGED at 41 and
    its six-class partition assertion still holds. `disable_lane_prompt` DELIBERATELY STAYS in
    `STILL_DOUBLE_DEFINED` (see V-02/D1) and its `PERMANENTLY_UNMOVABLE` entry is untouched.

    `tests/test_rununify_initialize_run.py` -- ONE entry MOVED: `set_plan_approved`. Count re-based
    3 -> 2, wrapper tuple 5 -> 6, so `CLOSURE_TOTAL` (36) and its partition assertion are UNCHANGED.

    `tests/test_rununify_main.py` (UNDECLARED, now declared) -- THREE entries RECLASSIFIED from
    `still-defined-twice` to `shared-host-wrapper`: `handle_stop_command`, `install_stop_triggers`,
    `locked_run`. The histogram moved by exactly three in each direction (`shared-host-wrapper` 4 -> 7,
    `still-defined-twice` 9 -> 6), so the same population is partitioned.

    EVERY MOVED ENTRY WAS MOVED, NOT DELETED, AND NO ASSERTION WAS REMOVED TO MAKE THE SUITE PASS. Three
    independent things make that checkable rather than merely stated: (1) each file's wrapper table rose
    by exactly the number its fork table fell; (2) the two files carrying a `CLOSURE_TOTAL` partition
    assertion still satisfy it at its ORIGINAL value, and that assertion -- not the per-tuple counts --
    is what proves a reclassification; (3) I ADDED `test_the_total_pinned_population_did_not_shrink` to
    `test_rununify_execute_item.py`, the one file that had no such cross-check, so a future re-base
    there cannot be performed as a net lowering either.

    THE ASSERTION THAT ACTUALLY FAILED WAS THE ONE F-6 CORRECTED TO, confirming the review over the
    authored text. Observed before the re-base:

        AssertionError: True is not false : oc_runipd.set_plan_approved now DELEGATES to
        runner_shared, so it is the sanctioned wrapper form rather than a fork: move it to
        THIN_WRAPPERS_OVER_RUNNER_SHARED

    That is `assertFalse(is_pure_delegation(...))`. The `assertIn(name, defs)` test F-6 originally
    quoted kept PASSING throughout, exactly as the review predicted, because a wrapper still satisfies
    it.

    ALL FIVE `test_rununify_*` FILES RUN TOGETHER (the four the review baselined at `95 passed`, plus
    the undeclared fifth):

        $ python3 -m pytest tests/test_rununify_execute_item.py tests/test_rununify_run_queue.py \
              tests/test_rununify_initialize_run.py tests/test_rununify_build_parser.py \
              tests/test_rununify_main.py -q -o addopts=""
        ........................................................................ [ 72%]
        ........................................................                 [100%]
        200 passed in 31.94s

    The pre-change baseline for the same five files, measured at HEAD `ee20e831` before any edit, was
    `163 passed` for the four review-named files; the figure rises rather than falls because the
    re-base ADDED assertions (the population floor above) and added none that were removed.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: `python3 -m pytest tests/test_hostdedup_identical_lift.py` green, PLUS a
    demonstration it FAILS when a re-fork is introduced (add a private copy in a scratch edit, paste the
    failure, revert). A guard never shown to fail is not a guard. State that the guard asserts DELEGATION
    rather than object identity, and why. PLUS the whole-plan proof, which the per-symbol items above cannot
    give: the suite showing NO NEW failures against a like-for-like baseline with BOTH numbers and the
    invocation form pasted (review reference: `7897 passed` with `env -u AW_EXECUTION_ROLE`, `31 failed,
    7866 passed` bare in a worker lane), AND a real driver execution completing after the lift, since the
    moved lock, stop-trigger and lifecycle machinery can satisfy every structural assertion while failing at
    runtime.
  - Observed evidence: THE GUARD IS `tests/test_hostdedup_identical_lift.py`, GREEN:

        $ python3 -m pytest tests/test_hostdedup_identical_lift.py -q -o addopts=""
        ..........................                                               [100%]
        26 passed in 11.18s

    IT ASSERTS **DELEGATION**, NOT OBJECT IDENTITY, and the reason is measured rather than assumed:
    under the wrapper design this plan chose, `oc_runipd.<sym> is agy_runipd.<sym>` is FALSE and so is
    `oc_runipd.<sym> is runner_shared.<sym>` (verified on the pre-existing wrapper `git_head` at review
    and re-verified here for every lifted symbol). An `is` check would therefore FAIL a correct
    implementation. So the non-identity is asserted POSITIVELY, as `TheWrapperIsNotTheSameObject`, with
    the reason in its failure message -- which means the next reader who "fixes" this file by reaching
    for `assertIs` fails there and reads why, instead of concluding the lift is broken.

    WHAT IT ACTUALLY ASSERTS, in two halves neither of which implies the other: (1) STRUCTURE -- the
    shared module defines each symbol EXACTLY ONCE, each host's body is a pure single-statement
    `runner_shared.X(...)` call, that call names the SAME symbol it wraps, and no host defines it twice;
    (2) REACHABILITY -- replacing the shared definition makes the host reach the replacement exactly
    once, driven rather than read, which is immune to a name rebound at import time and to a stale
    shadowed duplicate. It also covers `StallWatchdog`'s subclass shape (only `__init__` may be
    overridden, and the host's reaper must really be bound), the E-08 descriptor properties, the
    grace-tuning contract, host-neutral prose, and the committed scanner's existence and agreement.

    DEMONSTRATED TO FAIL ON A RE-FORK, as this item requires. I replaced
    `oc_runipd.requeue_interrupted`'s delegation with a private body, ran the guard, and reverted:

        SABOTAGE: re-forked oc_runipd.requeue_interrupted with a private copy
        AssertionError: False is not true : oc_runipd.requeue_interrupted is no longer a single
          delegating call to `runner_shared`. A wrapper that grew logic has RE-FORKED the symbol: the
          fix lands in one host and the others silently miss it, which is exactly the `cjefq5` defect
          that killed 6 plans and 2 orchestrators across 13 runs.
        AssertionError: None != 'requeue_interrupted' : oc_runipd.requeue_interrupted delegates to
          `runner_shared.None`, not to its own name
        AssertionError: Lists differ: ['requeue_interrupted'] != []
        4 failed, 22 passed in 11.01s
        === RESTORED ===
        26 passed in 12.10s

    AND IT CAUGHT TWO REAL DEFECTS IN MY OWN WORK on its first run, which is stronger evidence than a
    deliberate sabotage: a SECOND `locked_run` definition I had left in `oc_runipd.py` shadowing the new
    wrapper (so the symbol read as lifted and behaved as forked), and two shared docstrings that still
    named a single host. Both fixed.

    THE WHOLE-PLAN PROOF: NO NEW SUITE FAILURES, against a baseline taken THE SAME WAY, with BOTH
    numbers and the invocation form pasted. RUN BARE, as the execution contract requires
    (`addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`):

        BEFORE, at HEAD `ee20e831` in this worker lane, before any edit:
        $ python3 -m pytest
        2 failed, 8062 passed, 3 skipped, 2 xfailed, 3 warnings in 107.35s

        AFTER:
        $ python3 -m pytest
        2 failed, 8090 passed, 3 skipped, 2 xfailed, 3 warnings in 210.51s (0:03:30)

    THE SAME TWO FAILURES BEFORE AND AFTER, both PRE-EXISTING and in files this plan does not touch:
    `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`
    and `tests/test_defect_report.py::ValidatorTests::test_no_bare_except_was_introduced_around_the_new_code`.
    Verified pre-existing by running each at HEAD before editing anything. NOT "fixed", per the plan's
    instruction. The passing count rises by 28, which is the new guard.

    A NOTE ON THE AUTHORED BASELINE, which the review already flagged as unreachable and which is
    unreachable in a third way: this lane reports `2 failed, 8062 passed` BARE, not the review's
    `31 failed, 7866 passed` bare / `7897 passed` with `env -u AW_EXECUTION_ROLE`. The tree has moved
    since. This is exactly why the gate is NO NEW FAILURES against a like-for-like baseline and never an
    absolute count, and why I measured my own baseline before editing rather than trusting any recorded
    figure.

    A REAL DRIVER EXECUTION COMPLETING AFTER THE LIFT, which this item calls not optional because the
    moved lock, stop-trigger and lifecycle machinery can satisfy every structural assertion while
    failing at runtime. Two parts:

    (a) A REAL `aw oc run` END TO END, in a scratch repo with a fixture plan, exercising selector
        expansion, the gates, run-directory creation, state/events persistence and the summary table:

        $ python3 -m agent_workflows oc run --prepare-only --repo <scratch> zz9zz9
        Run order (1 item(s)): 01 zz9zz9
        Run ID: run-20260922T054412Z-2415770
        AW RUN SUMMARY: run-20260922T054412Z-2415770 (opencode)
        Outcome: QUEUED   Duration: 0s
        events.jsonl: run-created, mixed-type-gate(proceed=True),
                      orchestrator-probe-gate(proceed=True, skipped=prepare-only), run-order

    (b) THE LIFTED RUNTIME MACHINERY DRIVEN DIRECTLY ON **BOTH** HOSTS, because `--prepare-only`
        deliberately returns before `run_queue` and so never takes the run lock. This is the part a
        structural test cannot reach:

        load_state ok, run_id = run-20260922T054412Z-2415770
        oc: run_lock HELD, driver.lock = pid=2419815 started=2026-09-22T05:44:32+00:00
        oc: second holder correctly refused -> DriverError: Run is already controlled by another process
        oc: run_lock released; lock file still present = False
        oc: locked_run HELD, handle = RunLockHandle
        oc: locked_run exited and ran clean_shutdown
        oc: install_stop_triggers -> {'SIGINT': 'installed', 'SIGTERM': 'installed'}
        oc: requeue_interrupted -> ['aaa111'], item now queued, recovery_next=True
        agy: run_lock HELD, driver.lock = pid=2419815 started=2026-09-22T05:44:32+00:00
        agy: second holder correctly refused -> DriverError: Run is already controlled by another process
        agy: run_lock released; lock file still present = False
        agy: locked_run HELD, handle = RunLockHandle
        agy: locked_run exited and ran clean_shutdown
        agy: install_stop_triggers -> {'SIGINT': 'installed', 'SIGTERM': 'installed'}
        agy: requeue_interrupted -> ['aaa111'], item now queued, recovery_next=True
        ALL LIFTED RUNTIME MACHINERY EXERCISED ON BOTH HOSTS

        ...and `clean_shutdown` reported all four invariants satisfied on each `locked_run` exit
        (`children_reaped` R1, `lock_released` R2 with "lock file removed; lock free=True",
        `ledger_coherent` R3, `tree_observed` R4 "dirty path(s) left exactly as found"). The scratch
        repo was removed afterwards; `git status` confirms nothing outside the declared scope remains.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the per-symbol closure table pasted, every dependency classified (a) in-tranche,
    (b) equal-valued, (c) host-divergent or (d) a host binding, derived from an actual scan at execution HEAD
    rather than copied from this plan. It must reproduce at minimum the nine symbols and nine names measured
    at review, and must state explicitly which symbols are cleared for E-02 and which are held.
  - Observed evidence: THE PER-SYMBOL CLOSURE TABLE, derived from an ACTUAL SCAN at execution HEAD with the committed
    scanner (`python3 tools/runner_fork_scan.py --closure --symbols <the seventeen>`), not copied from
    the plan. Every module-level dependency each body reaches, classified (a) IN-TRANCHE, (b)
    EQUAL-VALUED, (c) HOST-DIVERGENT, (d) A HOST BINDING:

    | symbol | dependency | class | how it is carried |
    |---|---|---|---|
    | `StallWatchdog` | `terminate_process` | (a) in-tranche | host SUBCLASS binds its own reaper |
    | `StallWatchdog` | `subprocess`, `threading`, `time` | resolves in shared | nothing to do |
    | `_budget_breach_recorder` | `runner_stop` | (b) equal-valued module | function-local import |
    | `_escalation_recorder` | `_detect_driver_command` | **(d) HOST BINDING** | `labels=` descriptor |
    | `_escalation_recorder` | `runner_stop` | (b) | function-local import |
    | `_observe_between_turn_stop` | `runner_stop` | (b) | function-local import |
    | `_record_checkpoint_stop` | `runner_stop` | (b) | function-local import |
    | `_record_checkpoint_stop` | `git_status` | **(d) HOST BINDING** | `git_status_fn=` injected |
    | `_record_deliberate_stop` | `runner_stop` | (b) | function-local import |
    | `build_isolation_notice` | `lane_containment` | (b) | function-local import (cycle) |
    | `disable_lane_prompt` | none | -- | HELD BACK, see below |
    | `driver_finalize` | `_compute_scope_reconciliation` | **(d) HOST BINDING** | `labels=` descriptor |
    | `driver_finalize` | `pinned_child_env`, `pinned_module_argv` | (a)/(d) | `env_builder=`/`argv_builder=` |
    | `evaluate_clean_base_for_launch` | `lane_containment`, `_run_git` | (b) | function-local import |
    | `handle_stop_command` | `_detect_driver_command` | **(d) HOST BINDING** | `labels=` descriptor |
    | `handle_stop_command` | `resolve_run_dir` | **(d) HOST BINDING** | `resolve_run_dir_fn=` injected |
    | `install_stop_triggers` | `_detect_driver_command` | **(d) HOST BINDING** | `labels=` descriptor |
    | `locked_run` | `run_lock` | (a) in-tranche | moves with it |
    | `locked_run` | `runner_shutdown`, `load_state` | (b) | function-local import |
    | `requeue_interrupted` | `runner_stop` | (b) | function-local import |
    | `run_lock` | `platform_lock`, `runner_shutdown` | (b) | function-local import |
    | `set_plan_approved` | `FULL_AUTO_ACTOR` | **(c) HOST-DIVERGENT** | `labels.full_auto_actor` |
    | `set_plan_approved` | `FULL_AUTO_APPROVAL_MESSAGE` | (b) equal across hosts | passed by caller |
    | `set_plan_approved` | `pinned_module_argv`, `run_checked` | (d) | `argv_builder=`/`run_checked=` |
    | `terminate_process` | `_SIGINT/_SIGTERM_GRACE_SECONDS` | (b) equal, MUTABLE | no-default params |
    | `terminate_process` | `runner_shutdown` | (b) | function-local import |

    THE REVIEW'S MEASUREMENT REPRODUCES: nine symbols close over names absent from `runner_shared`, and
    `FULL_AUTO_ACTOR` is the one whose VALUE differs per host (`aw oc run --full-auto` vs
    `aw agy run --full-auto`). The scanner flags that single name `VALUE-DIFFERS-PER-HOST` and no other,
    independently of the review's prose.

    CLEARED FOR E-02 (13): `_budget_breach_recorder`, `_escalation_recorder`, `_observe_between_turn_stop`,
    `_record_checkpoint_stop`, `_record_deliberate_stop`, `build_isolation_notice`, `driver_finalize`,
    `handle_stop_command`, `install_stop_triggers`, `requeue_interrupted`, `run_lock`,
    `set_plan_approved`, `StallWatchdog`. E-03 took the remaining three prose cases
    (`evaluate_clean_base_for_launch`, `terminate_process`, `locked_run`).

    HELD (1): `disable_lane_prompt`. Its closure is EMPTY, so it is closure-clean and still unliftable
    -- which is itself worth recording, because it shows a closure scan is necessary and not sufficient.
    The obstacle is that it WRITES a module-level flag through `global` rather than reading one. See
    V-02 and DECISION 04-li44r9-D1.

    FOUR FINDINGS BEYOND WHAT THE REVIEW MEASURED, each a case the closure table alone would have
    missed:

    1. THREE SYMBOLS WERE **THREE-WAY** FORKS, not two-way: `_record_checkpoint_stop`,
       `build_isolation_notice` and `evaluate_clean_base_for_launch` were ALREADY defined in
       `runner_shared` while both hosts kept their own bodies, so the shared copy was reached by nobody.
       Pointing the hosts at the definitions that were already there removed three bodies in one step
       instead of the two the plan anticipated. DECISION 04-li44r9-D4.
    2. ONE OF THOSE UNREACHABLE SHARED COPIES WAS **BROKEN**, and this is the most consequential finding
       of the execution. `runner_shared._record_checkpoint_stop` called `git_status(repo)` while this
       module's `git_status` takes a REQUIRED keyword-only `run_checked`, so the call raised
       `TypeError`, the surrounding `except Exception` swallowed it, and every level-3 stop record's
       `git_state` would have read `<unobserved: git_status() missing 1 required keyword-only argument:
       'run_checked'>` -- silently replacing the observed working-tree state, which is the entire
       evidentiary point of a stop record, with an error string. It had never been noticed BECAUSE it
       was unreachable; activating it is what exposed it, and
       `tests/test_runner_stop.py::test_stop_isolated_git_status` failed. Fixed by injecting the host's
       bound `git_status` with no default. FIVE further unreachable shared copies remain and are filed
       as backlog `xv2zhy` with the warning that activating any of them is its own first test.
    3. `runner_shared` ALREADY DEFINED `FULL_AUTO_ACTOR = "aw-driver/full-auto"` and a
       `FULL_AUTO_APPROVAL_MESSAGE`, both DEAD and matching NEITHER host. Having the shared body read
       the names already in scope was the obvious implementation and would have attributed BOTH hosts'
       auto-approvals to a third string no host has ever written, and changed the recorded message on
       both. Both constants now carry a prominent note; filed as backlog `js1oun`. DECISION
       04-li44r9-D2.
    4. A TOP-LEVEL IMPORT OF `runner_shutdown`/`platform_lock` INTO `runner_shared` IS CYCLE-FREE BUT
       FORBIDDEN. I measured the import graph (their own first-party top-level imports are
       `platform_lock` alone) and added the import, then
       `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
       refused it: that guard pins this module's module-level first-party imports to EXACTLY
       `render_stream` + `runner_profiles`, because an import here changes the import graph for EVERY
       host driver. Honored with function-local imports, this module's own convention in twenty-plus
       places, so the lift needed no guard re-base.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: `tests/test_runner_shutdown.py` and `tests/test_runner_backlog_close.py` green
    (review baseline `74 passed`), the diff of each of the three re-based assertions with its reason, AND
    the behavioral proof that tuning a host's `_SIGINT_GRACE_SECONDS` still reaches the reaper. An
    assertion re-worded so it no longer checks the pass-through does NOT satisfy this item; the contract
    must still be enforced by something.
  - Observed evidence: THE THREE BROKEN ASSERTIONS F-12 NAMED WERE RE-BASED, AND THREE MORE THE REVIEW DID NOT FIND. Each
    with its reason; none weakened, and the population of each guard is preserved or grown.

    THE F-12 THREE:

    1. `tests/test_runner_shutdown.py` `SingleReaperTests._DELEGATION_ALLOWLIST` -- the AST arm required
       each driver's `terminate_process` body to call ONLY `runner_shutdown.terminate_process`. After
       the lift each driver calls `runner_shared.terminate_process`, so the ladder is TWO hops away.
       REASON AND SHAPE OF THE RE-BASE: widening the allowlist ALONE WOULD HAVE BEEN A REAL WEAKENING,
       because it would then permit a driver to call ANY shared function and stop proving the ladder is
       reached at all. So the allowlist admits the new spelling AND I added
       `test_the_shared_hop_still_reaches_the_one_ladder`, which applies the SAME subset check one hop
       further in: the shared body may call the ladder and nothing else, plus it must actually call it.
       PROVEN FALSIFIABLE: I replaced the shared body's delegation with `os.killpg(pid, SIGKILL)` and
       the class went `3 failed, 1 passed`, naming both the missing delegation and the out-of-allowlist
       call; restored, `4 passed`.
    2. `tests/test_runner_backlog_close.py:1145` -- asserted the host body's source contains both grace
       constant NAMES. IT STILL PASSES UNCHANGED and needed no edit, because DECISION 04-li44r9-D3 kept
       the constants in each host and has the wrapper PASS them, so the wrapper legitimately still
       names both. Recorded so a reader does not look for an edit that was correctly not made.
    3. `tests/test_runner_shutdown.py:173`'s grace-constant contract -- see the behavioral proof below.

    THREE FURTHER BREAKS THE REVIEW DID NOT FIND, each re-based with the remedy the guard's own failure
    message prescribes:

    4. `tests/test_runner_stop.py` `PollWiringTests` -- required the installer call inside each driver's
       own `install_stop_triggers` body. Re-based to follow the delegation ONE level and still REQUIRE
       the call to be found. The per-driver `signal.signal(` prohibition beside it is UNTOUCHED, which
       is the assertion that actually guards the defect.
    5. `tests/test_lane_tool_identity.py` -- two failures. The `driver_finalize` row's OWNER column
       moved `driver` -> `shared` (the remedy the table's own message names: "if it now launches through
       a different module, update this row's owner column"), and the nested-`aw` site census was
       re-based off per-driver shape assertions onto the OWNER SET, because measured at HEAD oc holds 2
       pinned sites and agy holds ZERO. The CLASSIFICATION assertion stays PER DRIVER, and
       `test_no_unpinned_module_launch_sites_remain` -- the one that guards `af7i6p`'s lane-shadowed
       launch -- is untouched.
    6. `tests/test_nested_tty_noninteractive.py` -- the per-module launcher counts. Re-based by MOVING
       counts from the two driver rows to the `runner_shared` row (oc 2 -> 1, agy 2 -> 1, shared 2 -> 3),
       which is verbatim what its failure message prescribes for a launcher that moved. TO MAKE THAT
       PROVABLY A MOVE I ADDED `MIN_OWNER_SET_LAUNCHERS` and a cross-row floor: shifting a launcher
       between rows leaves it untouched while DELETING one lowers it and fails, which no combination of
       per-module edits can hide. The PARITY property is preserved and is now STRUCTURAL rather than
       hand-maintained.
    7. `tests/test_lane_clean_base.py` and `tests/test_dirty_base_gate.py` -- both spied the DRIVER's
       `_run_git`, which no longer performs the call. The spy now also covers `runner_shared._run_git`,
       where the single real call happens. EVERY ASSERTION IS UNCHANGED, including the exactly-one-git-
       call count and the `--untracked-files=no` scope read off the real argv.
    8. `tests/test_runner_shared.py` -- two failures, both accounted for through the file's OWN
       relocated-caller mechanism rather than by editing a number: `set_plan_approved` was added to
       `RELOCATED_RUN_CHECKED_CALLERS` with its measured call count (2), which the census SUBTRACTS
       because those calls left the runners, and the injected parameter was named `run_checked` (not
       `run_checked_fn`) to match the convention that file asserts for every shared caller.
    9. `tests/test_lane_allocation_idempotent.py` -- two source-text searches for strings that moved.
       Re-based onto the owner set for those two, while the `signal.signal(` prohibition and
       `reclaim_lanes_on_interrupt(` stay PER DRIVER, deliberately un-relaxed.

    THE BEHAVIORAL PROOF THE GRACE PASS-THROUGH IS STILL HONORED, which E-07 calls the most important of
    the five and which an assertion re-worded away would not satisfy. Driven on BOTH hosts:

        oc:  tuned values reached the reaper -> {'sigint_grace': 0.11, 'sigterm_grace': 0.07}
        agy: tuned values reached the reaper -> {'sigint_grace': 0.11, 'sigterm_grace': 0.07}

    i.e. setting `<host>._SIGINT_GRACE_SECONDS = 0.11` on either host still arrives at
    `runner_shutdown.terminate_process`. The contract is ALSO now enforced by something rather than
    merely observed once: the shipped
    `test_driver_grace_constants_are_honored_through_the_delegation` still passes untouched, and
    `tests/test_hostdedup_identical_lift.py::ThePerHostGraceTuningSurvivedTheLift` adds a second,
    independent behavioral check plus an assertion that the shared parameters carry NO DEFAULTS (a
    default would let a host silently inherit another's timing).

    BOTH DECLARED FILES GREEN (review baseline `74 passed`; the local pre-change baseline at HEAD
    `ee20e831` was `66 passed`, and the rise is the assertions this item ADDED):

        $ python3 -m pytest tests/test_runner_shutdown.py tests/test_runner_backlog_close.py -q -o addopts=""
        ........................................................................ [ 93%]
        .....                                                                    [100%]
        77 passed in 12.21s
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: the both-directions attribution test pasted green, showing an oc auto-approval
    records `aw oc run --full-auto` and an agy one records `aw agy run --full-auto`; the descriptor field
    shown to have NO default (a construction missing it raises); and the `_detect_driver_command` resolution
    shown to reach each host's own labels. If OQ-03 route (b) was chosen instead, paste the hand-off record
    naming the four symbols and this item is `not-applicable` rather than complete.
  - Observed evidence: THE BOTH-DIRECTIONS ATTRIBUTION TEST, GREEN, driven end to end through each host's real
    `set_plan_approved` and reading the `--actor` off the argv it actually assembles:

        oc:  actor='aw oc run --full-auto'
        agy: actor='aw agy run --full-auto'

    Pinned permanently as
    `tests/test_hostdedup_identical_lift.py::TheHostVaryingValuesTravelByDESCRIPTOR::test_each_host_records_its_OWN_auto_approval_actor`,
    and green in the run pasted at V-05. THIS IS THE CHECK THAT WOULD HAVE CAUGHT F-10: the two bodies
    were byte-identical, so every structural assertion passed while a verbatim lift would have recorded
    every Antigravity auto-approval as performed by `aw oc run` in a plan's PERMANENT `## Workflow
    history`.

    THE DESCRIPTOR FIELD HAS NO DEFAULT, proven by construction rather than asserted:

        >>> runner_shared.HostLabels(command="aw x run", ..., emits_launch_identity=False)
        TypeError: HostLabels.__new__() missing 1 required positional argument: 'full_auto_actor'

    So a new host cannot forget to bind it and silently inherit another host's identity. Pinned as
    `test_the_full_auto_actor_is_a_no_default_descriptor_field`. This follows `HostLabels`'s own stated
    rationale, whose docstring names durable-history misattribution as the harm its no-defaults design
    exists to prevent.

    ROUTE (a) WAS TAKEN, per OQ-03's maintainer resolution: all the symbols stay in this plan and the
    host-divergent values are carried explicitly through `HostLabels`. No symbol was handed to Order 02
    on these grounds, so this item is COMPLETE rather than `not-applicable`.

    `_detect_driver_command` RESOLVES TO EACH HOST'S OWN LABELS. The shared bodies never call a shared
    `_detect_driver_command` (which would bind one host's labels for every host); they call
    `detect_driver_command(labels=labels)` with the labels the CALLER supplied, which is the same
    parameter the 21 pre-existing wrappers already use. FOUR symbols needed this, one more than the
    review's three: `_escalation_recorder`, `handle_stop_command`, `install_stop_triggers` (all three
    called `_detect_driver_command` directly) and `driver_finalize` (reaches
    `compute_scope_reconciliation`, whose reason and ack strings name the driver inside a plan's
    PERMANENT finalize record). Asserted per symbol and per host by
    `test_every_host_varying_symbol_takes_its_value_from_the_caller` (the `labels` parameter exists, is
    keyword-only, and has NO default) and `test_each_host_binds_its_OWN_labels` (each wrapper binds its
    own `*_HOST_LABELS` and NOT the other host's -- a wrapper passing the wrong host's labels would
    satisfy every other check in the file).

    ONE MECHANISM CHANGE BEYOND WHAT E-08 SPECIFIED, recorded because it is a behavior-PRESERVING choice
    made against a tempting alternative. Each host's module-level `FULL_AUTO_ACTOR` now READS the
    descriptor field (`runner_shared.OC_HOST_LABELS.full_auto_actor`) instead of repeating the literal,
    so the two CANNOT DISAGREE. This matters because the shipped assertions
    (`tests/test_oc_runipd.py:1428`, `tests/test_agy_runipd_cli.py:1121`) check the argv against the
    MODULE CONSTANT, so a literal that drifted from the descriptor would keep those tests passing while
    the runner wrote the other value into permanent history. The values are unchanged. Pinned as
    `test_the_module_constant_and_the_descriptor_cannot_DISAGREE`, which asserts the PROPERTY rather
    than the current strings.

    THE DERIVATION SHORTCUT WAS REJECTED, and the reason is in-tree rather than a preference: both hosts
    happen to satisfy `command + " --full-auto"` today, so deriving the actor that way would have passed
    every test while re-introducing exactly the implicit coupling `HostLabels` exists to delete -- its
    own `review_command` field docstring argues this case ("deriving one operator-facing command from
    another by string surgery is exactly the kind of implicit coupling this descriptor exists to
    remove"). A separate field is what the descriptor's design calls for. DECISION 04-li44r9-D2.

    AND THE ALTERNATIVE THE REVIEW DID NOT KNOW ABOUT WAS WORSE THAN IT FEARED. `runner_shared` ALREADY
    carried `FULL_AUTO_ACTOR = "aw-driver/full-auto"` plus a differing `FULL_AUTO_APPROVAL_MESSAGE`,
    both dead and matching NEITHER host, under exactly the spelling the shared body would reach for. So
    the naive lift would not merely have attributed agy's approvals to oc: it would have attributed
    BOTH hosts' approvals to a third string no host has ever written, and changed the recorded message
    on both, with every existing test green. Both constants now carry a prominent note at their
    definition; filed as backlog `js1oun`. The `message` parameter is likewise REQUIRED with no default
    for the same reason, so each host's wording is preserved byte-for-byte.
  - Result: pass

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

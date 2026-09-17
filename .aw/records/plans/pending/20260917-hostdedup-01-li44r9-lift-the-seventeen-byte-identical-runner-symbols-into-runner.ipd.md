# IPD: Lift the seventeen byte-identical runner symbols into runner shared

- Date: 2026-09-17
- Kind: child
- Concern: SEVENTEEN top-level symbols are defined in BOTH `oc_runipd.py` and `agy_runipd.py` and are BYTE-IDENTICAL after AST normalization with docstrings stripped: StallWatchdog, _budget_breach_recorder, _escalation_recorder, _observe_between_turn_stop, _record_checkpoint_stop, _record_deliberate_stop, build_isolation_notice, disable_lane_prompt, driver_finalize, evaluate_clean_base_for_launch, handle_stop_command, install_stop_triggers, locked_run, requeue_interrupted, run_lock, set_plan_approved, terminate_process. That is 380 lines of pure copy-paste with zero host-specific content. Measured at HEAD 2026-09-17. Every fix to one copy is a fix the other silently misses, which is not hypothetical: the `cjefq5` defect fixed on 2026-09-17 was ONE expression present byte-identically in both hosts, mislabeled an executed plan `reviewed`, and killed six approved plans plus two orchestrators at queue build across 13 separate runs before anyone traced it. The cost is also about to multiply: at two hosts each duplicated symbol is written twice, at five hosts (codex, claude, hermes) it is written five times.
- Scope: Move these seventeen symbols to `runner_shared.py` as ONE definition each, and leave each host a thin delegating wrapper of the sanctioned form the repository already uses in 21 other places. This is the LOWEST-RISK tranche by construction: because the bodies are byte-identical, the shared definition is the existing body verbatim, with no parameterization to design and no behavior decision to make. Does NOT touch the twelve divergent symbols (Order 02) or the five large functions (out of Set; see Deferred).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_hostdedup_identical_lift.py, tests/test_rununify_initialize_run.py
- Item-Dependencies: none
- Status: to-review
- Set: hostdedup
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: li44r9

## Workflow history
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

VERIFIED SAFE TO LIFT VERBATIM. All seventeen were scanned for the two hazards that make a lift unsafe:
`__file__` (which is evaluated in the DEFINING module and so silently changes value on relocation, the
hazard that blocked `orziju`) and host tokens. Zero contain `__file__`. Two mention a host token
(`evaluate_clean_base_for_launch` says "the agy twin" and `terminate_process` says "OpenCode process") but
in PROSE ONLY, inside comments and docstrings, with no host token in code. Those two docstrings must be
re-worded on lift rather than carried across unchanged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Re-measure, then lift

- [ ] E-01 Re-measure the identical set at execution HEAD and REFUSE to proceed on a stale list. Parse both runners, normalize each top-level symbol with `ast.unparse` after stripping docstrings, and emit the set defined in both AND byte-identical. Re-run the hazard scan for `__file__` and host tokens, separating a token in CODE from a token in PROSE.
  - Depends on: none
  - Expected outcome: the list, compared against the 2026-09-17 baseline of seventeen symbols / 380 oc lines. A symbol that has since diverged moves to Order 02's tranche and is named; a newly identical symbol is added here. Zero `__file__` occurrences expected; exactly two prose-only host-token mentions expected.
  - Execution state: pending

- [ ] E-02 Lift the symbols with NO host-token mention (expected fifteen) into `runner_shared.py` as one definition each, replacing both hosts' copies with a delegating wrapper. Preserve each body EXACTLY; this item must contain no behavior change, so any diff beyond the move plus the wrapper is out of scope for it.
  - Depends on: E-01
  - Expected outcome: fifteen symbols with one definition in `runner_shared`, two thin wrappers each, and an unchanged full suite.
  - Execution state: pending

- [ ] E-03 Lift the two prose-contaminated symbols (`evaluate_clean_base_for_launch`, `terminate_process`), re-wording their docstrings so neither names a specific host. A shared symbol whose docstring says "the agy twin" or "a child OpenCode process" is misleading the moment a third host calls it.
  - Depends on: E-01
  - Expected outcome: both lifted, with docstrings that describe the behavior host-neutrally. Quote the before and after wording.
  - Execution state: pending

### Task group 2: Re-base the guard that pins the duplication

- [ ] E-04 Update `tests/test_rununify_initialize_run.py`'s `STILL_DOUBLE_DEFINED` / `THIN_WRAPPERS_OVER_RUNNER_SHARED` tables for every symbol this plan moves, in the SAME change, per the maintainer's re-base-deliberately rule. That file asserts the duplication STILL EXISTS (`test_every_still_double_defined_symbol_really_is_defined_in_both_runners`), so a lift without this edit fails a test that is doing its job. Its own failure message names this remedy.
  - Depends on: E-02, E-03
  - Expected outcome: the pin tables reflect the post-lift reality, with each moved symbol recorded as a sanctioned wrapper rather than deleted from the guard entirely. Never weaken the guard silently: state which entries moved and why.
  - Execution state: pending

- [ ] E-05 Add `tests/test_hostdedup_identical_lift.py` asserting the invariant this plan establishes and the NEXT host inherits: for every lifted symbol, `oc_runipd.<sym>` and `agy_runipd.<sym>` resolve to ONE object in `runner_shared`, and no runner re-forks it. Drive it from a named table so a re-fork fails loudly rather than drifting back.
  - Depends on: E-04
  - Expected outcome: a guard that fails if either host reintroduces a private copy of any of the seventeen.
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
  a supposedly identical symbol is a signal that symbol belongs in Order 02.
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
| F-1 | 17 symbols are defined in both runners and byte-identical after AST normalization | measured 2026-09-17; 380 oc lines. Largest: `StallWatchdog` 59, `run_lock` 41, `set_plan_approved` 33, `install_stop_triggers` 32, `requeue_interrupted` 32 |
| F-2 | 55 symbols are defined in both hosts; 21 are sanctioned wrappers, leaving 34 real forks (~1752 oc lines) | AST scan of both runners at HEAD |
| F-3 | Duplication has already shipped a real defect, so this is cost not tidiness | `cjefq5`: one byte-identical expression in both hosts relabeled an executed plan `reviewed`, killing 6 plans + 2 orchestrators at queue build across 13 runs (fixed 2026-09-17, `ee99c41d`) |
| F-4 | None of the 17 contains `__file__`, the hazard that blocked `orziju`'s relocation | hazard scan: zero occurrences across all seventeen |
| F-5 | Exactly 2 of the 17 mention a host token, and only in PROSE | `evaluate_clean_base_for_launch` docstring "the agy twin"; `terminate_process` docstring "a child OpenCode process". No host token in code in either |
| F-6 | A guard test actively asserts some of this duplication still exists, so it must be re-based in the same change | `tests/test_rununify_initialize_run.py:159` `STILL_DOUBLE_DEFINED` includes `set_plan_approved`, which this plan lifts; its failure message prescribes exactly this remedy |
| F-7 | The wrapper target form is proven at scale, not speculative | 21 symbols already delegate to `runner_shared` on both hosts and are excluded from fork counts by `is_pure_delegation` |
| F-8 | The N-host multiplier is the real argument: 380 lines duplicated twice today becomes 380 x 5 with codex/claude/hermes | arithmetic on F-1 against the maintainer's stated roadmap |

## Proposed changes (ordered, validatable)

1. Re-measure the identical set and the hazard scan at execution HEAD (E-01); refuse on a stale list.
2. Lift the fifteen clean symbols to `runner_shared`, replacing each host copy with a thin delegation
   (E-02). Bodies preserved exactly.
3. Lift the two prose-contaminated symbols with host-neutral docstrings (E-03).
4. Re-base `STILL_DOUBLE_DEFINED` / `THIN_WRAPPERS_OVER_RUNNER_SHARED` in the same change (E-04).
5. Add an anti-re-fork guard over the lifted set (E-05).

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

- Over-scope: none. Every item moves code without changing it, plus the two guard edits that the move
  makes mandatory.
- Under-scope: deliberate. This plan removes 380 of the ~1752 remaining forked lines (about 22%). The rest
  is Order 02 and the deferred five, and attempting all of it in one pass is what stalled `rununify`.

## Required tests / validation

- `python3 -m pytest` bare and green, with the actual summary line pasted. Baseline at authoring: `7825
  passed, 3 skipped, 2 xfailed`.
- Object-identity evidence: for each lifted symbol, show `oc_runipd.<sym> is agy_runipd.<sym>` or that both
  delegate to the one `runner_shared` definition.
- A BEHAVIORAL check, not only structural: run a real driver execution end to end after the lift and show
  it still completes, since 380 lines of moved lifecycle/lock/stop machinery is exactly the code a
  structural test can pass while runtime breaks.
- `git diff` evidence that the fifteen clean bodies moved UNCHANGED (E-02 asserts no behavior change).

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

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the re-measured identical set pasted, compared explicitly against the 2026-09-17
    baseline (17 symbols / 380 oc lines), plus the hazard scan output showing zero `__file__` and exactly
    two prose-only host-token mentions. Any divergence stated, not absorbed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for each of the fifteen, evidence of ONE definition in `runner_shared` and a
    delegating wrapper in each host; PLUS `git diff` evidence that the body moved unchanged. A moved body
    with an incidental edit fails this item.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the before and after docstring wording for `evaluate_clean_base_for_launch` and
    `terminate_process`, showing neither names a host, plus the same one-definition evidence as V-02.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the diff of `STILL_DOUBLE_DEFINED` / `THIN_WRAPPERS_OVER_RUNNER_SHARED` with a
    per-entry reason, and `python3 -m pytest tests/test_rununify_initialize_run.py` green. State
    explicitly that no assertion was DELETED to make the suite pass.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `python3 -m pytest tests/test_hostdedup_identical_lift.py` green, PLUS a
    demonstration it FAILS when a re-fork is introduced (add a private copy in a scratch edit, paste the
    failure, revert). A guard never shown to fail is not a guard. PLUS the whole-plan proof, which the
    per-symbol items above cannot give: `python3 -m pytest` bare and green with the summary line pasted
    (authoring baseline `7825 passed, 3 skipped, 2 xfailed`), AND a real driver execution completing after
    the lift, since 380 lines of lock, stop-trigger and lifecycle machinery can satisfy every structural
    assertion while failing at runtime.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. It is a pure code MOVE: no behavior change
is authorized, and a diff that changes behavior exceeds this plan's scope even if the change is an
improvement.

Execution contract: work in an isolated worktree, commit only the declared `Scope-Paths`, path-scoped,
never `git add -A`, never push. Paste ACTUAL runner output for every V-item.

Post-gate lifecycle: `aw ipd finalize` moves this plan to `.aw/records/plans/executed/` only after
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries observed evidence. V-06's real
driver execution is not optional: 380 lines of lock, stop-trigger and lifecycle machinery can pass every
structural assertion while failing at runtime.

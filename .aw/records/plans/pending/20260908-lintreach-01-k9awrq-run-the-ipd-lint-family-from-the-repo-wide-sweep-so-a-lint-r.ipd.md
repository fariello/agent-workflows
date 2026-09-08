# IPD: Run the IPD lint family from the repo-wide sweep so a lint-refusable defect cannot sit committed

- Date: 2026-09-08
- Kind: child
- Concern: `aw check plans` DOES NOT RUN `ipd_lint`, SO THE ENTIRE `IPD-*` DIAGNOSTIC FAMILY IS INVISIBLE TO THE REPO-WIDE SWEEP AND TO CI. REPRODUCED AT HEAD, not read from the item: a scaffolded plan given a fabricated `- Readiness: go-pending-approval` and no review in its history yields `IPD-M107` from `aw ipd lint <file> --phase author` (message: "Readiness ... is a REVIEW OUTPUT but no review verdict appears in `## Workflow history`"), while `aw check plans --agent` returns ZERO diagnostics mentioning that file. `check_engine` has its own targeted plan rules (draft-readiness, dependencies, naming, lifecycle transitions) but never calls `ipd_lint.lint_file`, so a defect the per-file verb REFUSES can be committed and will sit in the tree until someone lints that exact file or tries to execute it.
  WHY IT MATTERS BEYOND ONE RULE: `aw check` is what an agent and CI are pointed at for a tree-wide verdict, and `aw attention --check` is the fail-closed gate. A rule that only fires on a per-file verb is a rule that only fires when someone already suspects that file. `IPD-M107` exists precisely because an agent wrote a `Readiness` value it had not earned, and the auto-approve predicate reads that field FIRST, so the sweep's blindness sits directly upstream of a gate that promotes plans to `approved`.
  THE ITEM'S FIRST QUESTION IS NOW ANSWERED BY MEASUREMENT, AND THE ANSWER REMOVES ITS MAIN OBJECTION. The item says "Running the whole lint tree-wide may surface a large pre-existing backlog (the tree currently reports 45 `aw check` errors already), so this could be noisy. Measure the count BEFORE choosing". MEASURED across all 561 tracked plans by calling `ipd_lint.lint_file` directly: at the `author` checkpoint, ZERO diagnostics across ZERO files. The feared noise does not exist. So an `author`-phase sweep can be introduced BLOCKING on day one with no phased rollout and no pre-existing backlog to triage, which is a materially different plan from the one the item anticipated.
  THE ITEM'S SECOND QUESTION IS ALSO SETTLED, AND THE WRONG CHOICE WOULD BE CATASTROPHIC. It notes `pre-transition` "would mass-fail every unexecuted plan, which is why the phase must be chosen deliberately". MEASURED: at `pre-transition` the same corpus yields 1261 diagnostics across 74 files, ALL of them `IPD-S404` ("E-01: not 'performed' at pre-transition"), which is simply the correct and expected state of every plan that has not executed yet. So `author` is the only defensible phase for a tree-wide sweep, and the measurement quantifies exactly how bad the alternative is.
  ONE PART OF THE ITEM IS ALREADY OBSOLETE. Its closing note says the corpus guard `tests/test_ipd_lint.py::ReadinessAttestationTests::test_every_readiness_carrying_plan_in_the_tree_is_attested` "closes the gap for THIS ONE RULE by scanning all 488 plans in the suite". That test exists and still passes, but the corpus is now 561 plans, and more importantly the test is a STOPGAP the item itself calls "not a general answer": it lives in the test suite rather than the checker and covers one rule. This plan makes it redundant for its own rule while deliberately leaving it in place (see Deferred).
- Scope: Make the `IPD-*` family reachable from `aw check plans` at the `author` checkpoint, so CI and any agent running the sweep sees what `aw ipd lint` would refuse. The phase choice is settled by measurement and is not re-litigated here. EXCLUDES a pre-commit hook (the item's option 3, deferred with a reason), any change to lint RULES themselves, and any change to what `aw ipd lint` reports per file.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/ipd_lint.py, tests/test_check_engine_lint_reach.py, tests/test_ipd_lint.py
- Item-Dependencies: none
- Status: to-review
- Set: lintreach
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: k9awrq
- From-Backlog: q0h9ls

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `q0h9ls`. NOTHING IN THE ITEM'S CORE DEFECT IS OBSOLETE and it was REPRODUCED rather than trusted: a scaffolded plan with a fabricated `- Readiness:` and no review yields `IPD-M107` from `aw ipd lint --phase author` and ZERO findings from `aw check plans --agent`. TWO OF THE ITEM'S THREE OPEN DECISIONS ARE NOW SETTLED BY MEASUREMENT, which is what makes this graduable as a narrow plan rather than an exploration. Its question 1 asked for the noise count before choosing: measured ZERO author-phase diagnostics across all 561 tracked plans, so the feared pre-existing backlog does not exist and no phased rollout is needed. Its question 2 asked which checkpoint: measured 1261 `IPD-S404` diagnostics across 74 files at `pre-transition` (the correct state of any unexecuted plan), which settles `author` as the only defensible phase and quantifies the alternative's cost. Question 3 (a pre-commit hook instead) is DECLINED with a reason rather than left open: a local hook is skippable and not cloned, so it cannot be the portable authority the item itself says `aw check` is; it remains a legitimate ADDITION later. ALSO CORRECTED: the item's closing note cites 488 plans in the corpus guard; the corpus is now 561. That guard stays in place deliberately (see Deferred), because deleting a passing corpus test as part of adding a checker is how coverage silently narrows.

## Goal

Make the tree-wide verdict tell the truth about plans, so a defect `aw ipd lint` would refuse cannot be committed and then sit unnoticed until someone lints that specific file.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm the numbers before changing a gate

- [ ] E-01 RE-MEASURE BOTH CHECKPOINTS ACROSS THE WHOLE CORPUS AND WRITE THE COUNTS DOWN, before wiring anything. This plan's central claim is that an `author`-phase sweep is free today, and that claim is the difference between a blocking rule and a mass failure.
  MEASURE BY CALLING THE FUNCTION, not by parsing CLI text: `ipd_lint.lint_file(path, checkpoint="author")` over every `*.ipd.md` under `.aw/records/plans`, counting diagnostics by `Diagnostic.code`. Note the parameter is `checkpoint=`, NOT `phase=` (the CLI flag is `--phase`, the API keyword is `checkpoint`); a call using the wrong keyword raises and, if wrapped in a broad `except`, silently reports zero for every file, which looks exactly like success.
  AUTHORING BASELINE, to be re-measured and not trusted: 561 plans scanned; `author` -> 0 diagnostics across 0 files; `pre-transition` -> 1261 diagnostics across 74 files, all `IPD-S404`.
  IF THE AUTHOR-PHASE COUNT IS NO LONGER ZERO, STOP AND RE-SCOPE rather than proceeding. A nonzero count means either a real defect landed in the corpus or a lint rule changed, and in both cases making the sweep blocking would fail CI for reasons unrelated to this plan. Report the offending files and their codes, and treat introducing the rule as ADVISORY-first as the fallback the item anticipated.
  - Depends on: none
  - Expected outcome: measured per-checkpoint counts at your HEAD with the codes named, plus an explicit STOP-and-re-scope if the author-phase count is nonzero.
  - Execution state: pending

### Task group 2: wire the family into the sweep

- [ ] E-02 CALL `ipd_lint.lint_file` FROM `check_engine`'s PLAN SWEEP AT THE `author` CHECKPOINT, and translate each `Diagnostic` into the `Drift` shape the sweep already emits.
  THE IMPORT DIRECTION IS THE FIRST THING TO VERIFY, because it decides whether this is a two-line change or a redesign. `ipd_lint` imports `ipd_schema` and `term` plus stdlib; establish whether `check_engine` importing `ipd_lint` creates a cycle, and if it does, import lazily inside the function rather than restructuring either module. There is precedent for the lazy-import pattern in this file: `check_scope_drift` imports `ipd_lifecycle` inside the function body specifically to avoid a cycle.
  DO NOT FORK A SECOND LINT IMPLEMENTATION. The whole value of this change is that the sweep and the per-file verb agree; re-implementing even one rule inside `check_engine` recreates the drift this plan closes. `evaluate_review_finding_escalation` is the in-repo precedent for the right shape: its docstring states that `aw check` and `aw ipd lint` "both call THIS function, so the sweep and the checkpoint gate cannot drift apart in what they consider escalated". Follow that model in the other direction.
  MAP THE CODES INTO THE RULE TABLE DELIBERATELY. `check_engine` assigns severity, assurance class and determinism per rule code via `RuleSpec`; an emitted code with no table entry carries no contract. Decide whether every `IPD-*` code gets an entry or whether they share one umbrella `check.*` code carrying the underlying `IPD-*` in its detail, and say why. The umbrella is likely correct (the `IPD-*` family is large and owned by `ipd_lint`, not by the check catalog), but it must be a decision rather than an accident.
  PRESERVE THE PER-FILE VERB'S OUTPUT EXACTLY. `aw ipd lint` is what an author and the `begin` gate consume; this plan adds a READER of the same rules and must not change what that verb reports.
  - Depends on: E-01
  - Expected outcome: the sweep runs the real `lint_file` at `author`, no rule is re-implemented, every emitted code carries a registered contract, and `aw ipd lint`'s own output is byte-unchanged.
  - Execution state: pending

- [ ] E-03 SCOPE THE SWEEP TO THE FILES IT CAN HONESTLY JUDGE, and be explicit about which those are. The checkpoint is not a free parameter per file: `author` is the only phase valid for an arbitrary pending plan, which the item states and the measurement confirms.
  DO NOT LINT A TERMINAL PLAN AT `pre-transition`, and do not lint one at `author` if that produces noise: a plan in `executed/` has already passed its gate, its body is immutable by policy, and 1261 of the measured diagnostics come from applying the wrong phase to plans that simply have not executed. Establish what the sweep does for each disposition and record it.
  MIND THE RETIRED-PATH FILTER, which has bitten a sibling rule measurably. `_iter_type_files` excludes retired paths unless `include_retired=True`, and `executed/` counts as retired, which is why `aw check all` reported zero id6-collisions while `aw doctor` reported one. Decide deliberately whether the lint sweep sees terminal plans, and make `aw check` and `aw doctor` AGREE, since `doctor` passes `include_retired=True` unconditionally and would otherwise lint a different set than `check`.
  - Depends on: E-02
  - Expected outcome: a recorded, tested decision about which dispositions the lint sweep covers, with `aw check` and `aw doctor` covering the same set.
  - Execution state: pending

### Task group 3: prove it catches the motivating case and costs nothing

- [ ] E-04 PROVE THE MOTIVATING DEFECT IS NOW CAUGHT BY THE SWEEP, using the item's own reproduction, from a FIXTURE rather than the live tree.
  THE REPRODUCTION, which this graduation ran and which the plan requires re-running: scaffold a plan, inject `- Readiness: go-pending-approval` with a history containing no review verdict, then assert `aw check plans` REPORTS it. Before this plan, `aw ipd lint --phase author` reported `IPD-M107` and `aw check plans --agent` reported nothing; after, both must report.
  ASSERT THE BEFORE STATE TOO, not only the after. A test that only checks the fixed behavior would pass even if the wiring were inverted; the contrast is the evidence.
  USE A FIXTURE, NEVER A TRACKED FILE. Injecting a fabricated `Readiness` into a real tracked plan would commit a forged attestation if anything went wrong, and the corpus guard in `tests/test_ipd_lint.py` would (correctly) fail. Build the plan in a temporary directory.
  - Depends on: E-03
  - Expected outcome: a fixture test asserting the sweep now reports the fabricated-`Readiness` case, with the pre-change silence demonstrated for contrast.
  - Execution state: pending

- [ ] E-05 PROVE THE SWEEP'S EXISTING VERDICT DID NOT MOVE, which is what makes this safe to land while other work is in flight.
  THE EXPECTED RESULT IS ZERO NEW FINDINGS ON THE CURRENT TREE, because the author-phase corpus measured clean. If the sweep now reports anything on a tracked plan, that is either a real defect this plan just exposed (report it, do NOT fix it here, and do not edit another agent's plan) or a bug in the wiring. Distinguish the two explicitly.
  COMPARE PER RULE, NEVER BY TOTAL. `aw check all` reports 98 findings at HEAD across rules this plan does not touch, and several of those counts drift for unrelated reasons (`check.scope-drift` moves with live receipts; `check.lifecycle-transition-invalid` grows whenever any plan gains a history line). A total comparison would be unreadable.
  MEASURE THE COST. The sweep now parses every plan through the linter as well as through its existing rules. Time `aw check plans` before and after and state the difference, because a quiet slowdown in the verb CI runs is how a check gets removed later.
  RUN THE SUITE BARE and judge on the DELTA. Baseline on main 2026-09-08: `1 failed, 5648 passed`, the failure being the pre-existing `tests/test_orchestrator_retirement.py` case. Inside a lane worktree roughly 32 further failures are environmental. Criterion: AFTER minus BEFORE is EMPTY.
  - Depends on: E-04
  - Expected outcome: zero new findings on tracked plans with any exception explained and not silently fixed; per-rule comparison stated; the added wall-clock cost measured; bare-suite delta empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE API KEYWORD IS `checkpoint`, NOT `phase`. `lint_file(path, *, checkpoint="author", legacy=False)`. The CLI flag is `--phase`. A call with the wrong keyword raises, and inside a broad `except` it reports zero for every file, which is indistinguishable from success.
- THE AUTHOR-PHASE CORPUS IS CLEAN: 0 diagnostics across 561 tracked plans. This is what makes a blocking introduction possible with no phased rollout.
- `pre-transition` WOULD MASS-FAIL: 1261 diagnostics across 74 files, all `IPD-S404` ("not 'performed' at pre-transition"), which is the correct state of an unexecuted plan.
- THE SHARED-EVALUATOR PATTERN ALREADY EXISTS IN THE OTHER DIRECTION: `evaluate_review_finding_escalation` is called by BOTH `aw check` and `ipd_lint.lint_file` so "the sweep and the checkpoint gate cannot drift apart". Follow it; do not fork a rule.
- THE LAZY-IMPORT PRECEDENT IS IN THIS FILE: `check_scope_drift` imports `ipd_lifecycle` inside the function body to avoid a cycle.
- RULE CODES ARE CONTRACTS: `check_engine`'s `RuleSpec` table assigns severity, assurance class and determinism; an unregistered code carries none.
- THE RETIRED-PATH FILTER MAKES `check` AND `doctor` DISAGREE unless handled: `_iter_type_files` excludes retired paths unless `include_retired=True`, `executed/` counts as retired, and `doctor` passes `True` unconditionally. This measurably produced a zero-versus-one disagreement on the id6 twin.
- A CORPUS GUARD ALREADY COVERS ONE RULE: `tests/test_ipd_lint.py::ReadinessAttestationTests::test_every_readiness_carrying_plan_in_the_tree_is_attested` scans every plan for an unattested `Readiness`. The item calls it a deliberate stopgap.
- `aw check all` IS NOT GREEN (98 findings). Compare per RULE.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the defect is real and was reproduced | A scaffolded plan with a fabricated `- Readiness:` and no review yields `IPD-M107` from `aw ipd lint --phase author` and ZERO findings from `aw check plans --agent`. | reproduced at HEAD in the graduation worktree |
| F-2 | HIGH | the feared noise does not exist | The item required measuring before choosing. Measured: 0 author-phase diagnostics across 561 tracked plans, so a blocking introduction needs no phased rollout and no triage backlog. | `ipd_lint.lint_file(..., checkpoint="author")` over the corpus |
| F-3 | HIGH | the wrong phase would be catastrophic | `pre-transition` yields 1261 diagnostics across 74 files, ALL `IPD-S404`, which is the correct state of any unexecuted plan. This settles `author` as the only defensible phase and quantifies the alternative. | same scan at `checkpoint="pre-transition"` |
| F-4 | HIGH | the sweep genuinely never calls the linter | `check_engine` has its own plan rules but no `lint_file` call; the only `ipd_lint` mention is a docstring noting the SHARED review-escalation evaluator, which is one rule, not the family. | grep for `lint_file` in `check_engine.py` |
| F-5 | MEDIUM | a keyword trap can fake success | The API keyword is `checkpoint`; the CLI flag is `--phase`. A wrong-keyword call raises, and inside a broad `except` reports zero everywhere. Encountered while measuring. | `inspect.signature(ipd_lint.lint_file)`; the first measurement attempt returned 561 EXCEPTIONs |
| F-6 | MEDIUM | the right shape is already in the repo | `evaluate_review_finding_escalation`'s docstring states both surfaces call one function so they "cannot drift apart". This plan is the same idea applied to the whole family. | `check_engine.py`, that function's docstring |
| F-7 | MEDIUM | the retired filter would split the two surfaces | `check` and `doctor` pass different `include_retired` values, which already produced a zero-versus-one disagreement on the id6 collision rule. | `_iter_type_files`; `doctor.py`'s unconditional `include_retired=True` |
| F-8 | MEDIUM | the item's stopgap figure is stale | It cites 488 plans in the corpus guard; the corpus is now 561. The guard still passes and still covers one rule only. | corpus count at HEAD |
| F-9 | LOW | the upstream stake is a promotion gate | `IPD-M107` guards a field the auto-approve predicate reads FIRST, and `8v5pwa` is separately hardening that predicate. So the sweep's blindness sits upstream of `reviewed -> approved`. | `IPD-M107`'s message; plan `8v5pwa` |
| F-10 | LOW | cost is a real consideration | The sweep would parse every plan through the linter in addition to its existing rules, and a quiet slowdown in the verb CI runs is how a check gets dropped later. | E-05's measurement requirement |

## Proposed changes (ordered, validatable)

1. Re-measure both checkpoints across the corpus and stop if the author phase is no longer clean (E-01).
2. Call the real `lint_file` from the plan sweep at `author`, translating diagnostics into registered rule codes without forking a rule (E-02).
3. Decide and test which dispositions the sweep covers, keeping `aw check` and `aw doctor` in agreement (E-03).
4. Prove the motivating fabricated-`Readiness` case is now caught, with the pre-change silence shown for contrast (E-04).
5. Prove no new findings on tracked plans, measure the added cost, and keep the suite delta empty (E-05).

## Deferred / out of scope (with reason)

- A PRE-COMMIT HOOK ON STAGED PLANS (the item's option 3). DECLINED as a substitute, kept as a possible addition. The item's own framing answers it: a local hook "is feedback, not authority", is not cloned by default, and is skippable with `--no-verify`, so it cannot deliver what the item actually asks for, which is that CI and the tree-wide verdict see the rule. Adding one LATER on top of a correct checker is reasonable; adding one INSTEAD would leave `aw check` still blind.
- CHANGING ANY LINT RULE, or adding one. This plan changes REACHABILITY only. If the executor believes a rule is wrong, that is a separate plan; a rule change bundled into a reachability change makes both unreviewable.
- CHANGING WHAT `aw ipd lint` REPORTS PER FILE. It is consumed by authors and by the `begin` gate; this plan adds a second reader of the same rules.
- REMOVING THE CORPUS GUARD in `tests/test_ipd_lint.py`. This plan makes it redundant for its own rule, but deleting a passing corpus test while adding a checker is how coverage silently narrows, and the guard is cheap. Leave it; if it should go, that is a deliberate follow-up with its own evidence.
- FIXING ANY DEFECT THE NEW SWEEP EXPOSES. Expected to be none (F-2). If one appears on another agent's plan, REPORT it: four agents are authoring concurrently and editing their plan would violate the shared-checkout rule.
- MAKING `pre-transition` REACHABLE FROM THE SWEEP. Measured catastrophic (F-3) and correctly so, since an unexecuted plan legitimately has unperformed items. The per-file verb and `aw ipd begin` already apply that phase where it belongs.
- HARDENING THE AUTO-APPROVE PREDICATE. Plan `8v5pwa` (`rdattest-02`, `From-Backlog: 754txs`) owns that and is a different layer: it fixes the DECISION that reads the field, while this plan fixes the SWEEP that never saw it.

## Scope check

- Over-scope: none. One call site, one code-mapping decision, two test modules.
- Scope-Paths justification: `agent_workflows/check_engine.py` holds the plan sweep, the `RuleSpec` table and the `_iter_type_files` traversal, i.e. E-02 and E-03 in full; `agent_workflows/ipd_lint.py` is declared because the sweep needs a callable entry point and may need a small, additive accessor (a rules-subset or a corpus-safe wrapper), NOT a rule change, and if no edit proves necessary this path may finish UNCHANGED, which is the expected outcome and not an incomplete item; `tests/test_check_engine_lint_reach.py` is new and carries the reachability and no-regression tests; `tests/test_ipd_lint.py` holds the existing corpus guard that must still pass unchanged.
- Under-scope, stated rather than left as `none`: this plan adds no pre-commit hook, changes no lint rule, does not alter `aw ipd lint`'s per-file output, does not remove the corpus guard, does not make `pre-transition` sweep-reachable, does not touch the auto-approve predicate, and does not fix any defect the new sweep exposes. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- THE PER-CHECKPOINT CORPUS MEASUREMENT re-run at your HEAD and pasted, with the code breakdown. Authoring baseline: `author` 0 across 561 plans; `pre-transition` 1261 across 74 files, all `IPD-S404`.
- THE FIXTURE REPRODUCTION (E-04) showing `aw check plans` silent BEFORE and reporting AFTER, with the actual output of both.
- `aw check all --agent` PER-RULE counts before and after, showing no rule's count changed except the new one, which must be ZERO on the current tree.
- `aw doctor` and `aw check plans` covering the SAME plan set (E-03), demonstrated rather than asserted, given the measured retired-filter disagreement on the id6 twin.
- `aw ipd lint` PER-FILE OUTPUT byte-unchanged for at least one conforming and one non-conforming plan.
- `tests/test_ipd_lint.py`'s own summary line, showing the corpus guard still passes.
- WALL-CLOCK `aw check plans` before and after, stated.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`check_engine`'s module-level prose and the plan-sweep function's docstring must state that the sweep now runs the `IPD-*` family at the `author` checkpoint, and WHY that checkpoint specifically, citing the measured 1261-diagnostic cost of `pre-transition`. Without that reason recorded, a future reader will "improve" the sweep by making the phase configurable or by defaulting it to the stricter value, which is precisely the mass failure the item warned about.

If E-02 chooses an umbrella rule code, the mapping from that code to the underlying `IPD-*` diagnostic must be documented where the rule table lives, so an operator reading `aw check` output can find the per-file verb that explains it.

No spec change is expected: the `IPD-*` family and the checkpoint vocabulary are defined by the `ipd-spec` document, and this plan changes only which SURFACE consults them. If the executor finds spec text asserting that `aw check` already covers the lint family, that is a false claim; declare the spec file in `Scope-Paths` before editing it, per the spec-amendment rule, and record the reason here.

The corpus guard's docstring in `tests/test_ipd_lint.py` calls itself "the check that would have caught the original mistake at commit time". Once the sweep covers that rule, add one sentence noting the checker now covers it too, so the next reader does not assume the test is the only line of defense.

## Open questions

### OQ-01: Should the lint sweep emit one umbrella rule code or one per `IPD-*` diagnostic?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ONE UMBRELLA CODE CARRYING THE `IPD-*` CODE IN ITS DETAIL, decided on ownership rather than taste. The `IPD-*` family is large, is owned and versioned by `ipd_lint`/`ipd_schema`, and grows whenever a lint rule is added; registering each one in `check_engine`'s `RuleSpec` table would mean every new lint rule requires a second registration in a different module, and a missed one would emit a code with no severity contract. An umbrella code keeps the contract stable while the detail stays specific enough to act on, and it mirrors how the existing sweep already reports a specific message under a general rule. E-02 must still make this a recorded decision at the site, because the alternative is defensible and a reader deserves the reason.

### OQ-02: Should the sweep lint terminal plans?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: WHATEVER IT DOES, `aw check` AND `aw doctor` MUST DO THE SAME, and that constraint decides the design more than the answer does. The measured hazard is concrete: the id6 collision rule reported ZERO from `aw check all` and ONE from `aw doctor` purely because `executed/` counts as retired and the two surfaces pass different `include_retired` values. Repeating that here would mean an agent's tree-wide verdict disagreed with `doctor`'s about whether a plan lints clean. The defensible default is to cover the same set the sweep already covers for its other plan rules (so the lint family is not special-cased), and E-03 must TEST the agreement rather than assume it. Terminal plans are immutable by policy, so a finding on one is informational at best, which is another reason not to introduce an asymmetry for them.

### OQ-03: What if the author-phase corpus is not clean at execution time?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: STOP, REPORT, AND FALL BACK TO ADVISORY; DO NOT FIX THE OFFENDING PLANS. E-01 makes this an explicit gate. The reasoning: a nonzero count means either a genuine defect landed (which is exactly what this plan exists to surface, and which belongs to whoever authored it) or a lint rule changed (which changes this plan's premise). Neither is repaired by this plan editing plans it does not own, especially with four agents authoring concurrently. Advisory-first is the phased introduction the item itself anticipated, so it is a prepared fallback rather than an improvisation, and it still delivers the reachability the item asks for.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the ACTUAL per-checkpoint measurement at your HEAD: plans scanned, files with at least one diagnostic, total diagnostics, and the code breakdown, for BOTH `author` and `pre-transition`. Compare against the authoring baseline (561 / 0 / 0 and 561 / 74 / 1261 `IPD-S404`) and state the difference. Confirm you used the `checkpoint=` keyword and that no broad `except` could have masked an exception as a zero count (F-5).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the call site showing the REAL `lint_file` invoked at `author`. Paste NEGATIVE proof that no lint rule was re-implemented inside `check_engine` (show the searches). Paste the `RuleSpec` entry for whatever code is emitted, and quote the comment recording the umbrella-versus-per-code decision (OQ-01). THEN paste `aw ipd lint` output for one conforming and one non-conforming plan, before and after, proving the per-file verb is byte-unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: state which dispositions the lint sweep covers and paste the test asserting it. Paste evidence that `aw check plans` and `aw doctor` cover the SAME plan set, by comparing the file counts each linted (not merely their findings), since a zero-finding agreement proves nothing about coverage.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the fixture construction, then the ACTUAL output of `aw check plans` against it BEFORE the change (silent) and AFTER (reporting), plus the `aw ipd lint` output for the same fixture. Quote the assertion covering the before state, so it is visible the contrast is tested rather than assumed. Confirm in one sentence that no tracked plan was modified to build this fixture.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `aw check all --agent` PER-RULE counts before and after, showing the new code at ZERO on tracked plans and no other rule's count changed. If anything was reported, state explicitly whether it is a real exposed defect (and that you REPORTED rather than fixed it) or a wiring bug. Paste wall-clock timings for `aw check plans` before and after. Paste `tests/test_ipd_lint.py`'s own summary line. THEN paste the BARE `python3 -m pytest` summary lines before and after and state the failure-set delta explicitly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING OPEN QUESTION, and that is a deliberate consequence of the measurement rather than an omission. The item left three decisions open; two are settled by evidence gathered at graduation (the corpus is clean at `author`, so no phased rollout is needed; `pre-transition` would produce 1261 diagnostics, so the phase choice is forced), and the third (a hook instead of the checker) is declined with the item's own reasoning about local hooks not being authority. What remains is a narrow wiring change with a measured cost of zero new findings.

THE ONE CONDITION THAT WOULD CHANGE THAT is E-01's re-measurement. If the author-phase corpus is no longer clean at execution time, the plan must not proceed to a blocking rule: OQ-03 records the prepared fallback, and the offending plans belong to whoever authored them.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Do NOT edit any file under `.aw/records/plans/`: if the new sweep exposes a defect in another agent's plan, report it, because four agents are authoring concurrently. Build the reproduction from a FIXTURE in a temporary directory, never by injecting a fabricated `Readiness` into a tracked plan, which would both forge an attestation and trip the corpus guard. Re-locate every symbol by NAME rather than by the line numbers cited here. Paste ACTUAL command output and compare `aw check` findings PER RULE, never by total. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the before-and-after contrast on the fixture and the measured wall-clock cost.

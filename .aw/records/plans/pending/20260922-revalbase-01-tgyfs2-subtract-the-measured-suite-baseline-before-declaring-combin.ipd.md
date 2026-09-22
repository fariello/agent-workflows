# IPD: Subtract the measured suite baseline before declaring combined-red so a pre-existing failure cannot refuse a verified lane

- Date: 2026-09-22
- Kind: child
- Concern: The post-merge revalidation gate asks an ABSOLUTE question ("is the merged tree green?") when the only sound question is a RELATIVE one ("did this lane introduce a failure that was not already there?"), so any pre-existing red test refuses every lane in the run. MEASURED in run `run-20260922T024054Z-2245533`: items `ld8lb3` and `65cuw0` both ended `merge-refused` carrying `integration_deferral` "integration gate did not pass (integration_failed_combined_red)", and in BOTH cases `item["post_merge_revalidation"]["failures"]` is EXACTLY the one id that the SAME item's `attempts[0]["suite_baseline"]["failures"]` already recorded as failing before the work existed: `FAILED tests/test_defect_report.py::ValidatorTests::test_no_bare_except_was_introduced_around_the_new_code`. For `ld8lb3` the baseline summary is `1 failed, 8042 passed` and the post-merge summary is `1 failed, 8064 passed`; for `65cuw0` they are `1 failed, 8063 passed` and `1 failed, 8084 passed`. In both the failing SET is unchanged and the passing count ROSE by exactly the tests the lane adds, which is the definition of "introduced no failure". A third item in a sibling run reproduces it independently: `h90ij1` in `run-20260922T023434Z-2057475` refused with TWO failures, one of which was that same baseline id.
  THE MACHINERY TO ANSWER THE RELATIVE QUESTION ALREADY EXISTS, IS ALREADY POPULATED, AND IS ALREADY ON THE SAME OBJECT. `runner_shared.SuiteBaseline` carries `state`/`base_commit`/`failures`/`reason`/`summary`, is started per attempt by `runner_shared.start_suite_baseline`, and is persisted by the ONE shared seam `execute_item_core` via `attempt["suite_baseline"] = suite_baseline.as_record()`. Its docstring already states the three-valued discipline this fix depends on: "an empty tuple with `state == \"absent\"` means UNKNOWN, not 'nothing was failing'". The PER-LANE half of the system consumes it through `runner_shared.suite_baseline_context`, which is what lets an agent answer `not-mine`.
  THE POST-MERGE HALF NEVER CONSULTS IT, and that asymmetry is the whole defect. `runner_shared.make_integration_validation_runner` decides the verdict solely from the merged-tree suite run (`passed = bool(getattr(result, "passing", False))`), and its entire body contains ZERO references to any baseline: verified by `sed -n '15415,15660p' agent_workflows/runner_shared.py | grep -c baseline` -> `0`. So one half of the runner knows what was already red and the other half re-discovers it and blames the lane.
  THE SEAM IS ALREADY OPEN, so this needs no new injection. The factory is called as `make_integration_validation_runner(state, run_dir, item, suite_check=run_suite_check)` and therefore ALREADY RECEIVES the `item` whose `attempts[-1]["suite_baseline"]` holds the record; the write happens in `execute_item_core` strictly BEFORE the integration block that builds `val_runner`, so the value is present by the time the gate runs (confirmed on disk for both measured items, `state: completed`).
  COST OF THE DEFECT: two fully verified lanes were stranded across an 8.5-hour unattended run, which cascaded three further items to `dependency-blocked` (`ut0vzr` and `k311gw` behind `65cuw0`; `lkexaw` behind `8u6770`), and a human then re-merged them by hand where the combined suite passed on the first attempt (`8474 passed`), because there was never anything wrong with the work.
- Scope: Make the post-merge revalidation verdict RELATIVE to the attempt's own measured baseline: refuse only on failing ids ABSENT from that baseline, and keep today's fail-closed behavior whenever the baseline is not `completed`. Consume the EXISTING `SuiteBaseline` record and the EXISTING failure-line extractor; add no new vocabulary, no new status, and no new injection. EXCLUDES the inert `not-mine` release path (sibling backlog `c74dm7`, its own plan), excludes `reattempt_deferred_integrations`' discarded `validation_runner_for` (backlog `iv4n2c`), and excludes any change to `integration_is_earned`'s two-mode rule or to the per-lane gate-answer question.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_integration_revalidation_baseline.py
- Item-Dependencies: none
- Status: to-review
- Set: revalbase
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: tgyfs2
- Work-Kind: bug
- Priority: high
- Blocks-Release: next
- From-Backlog: fuk1mr

## Workflow history

- 2026-09-22 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `fuk1mr`, inheriting its `Blocks-Release: next` gate. Every claim here was measured from the two runs' own `state.json` rather than reasoned about, and the central asymmetry was verified directly in source (`grep -c baseline` over the factory body returns `0`). The plan deliberately consumes `SuiteBaseline` rather than re-measuring: the record is already written by one shared seam for both hosts, already carries the three-valued unknown discipline this fix needs, and is already reachable from the `item` the factory receives, so the change is a comparison and not new machinery.
- 2026-09-22 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop the runner blaming a lane for a test that was already failing before that lane existed. After this plan, an integration refuses only when the merged tree fails something the pre-work baseline did not, and a refusal names exactly which ids are NEW.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the comparison

- [ ] E-01 Add a pure predicate in `runner_shared` that takes the merged-tree failing ids and a `SuiteBaseline` and returns the NEW failing ids plus a three-valued judgement (`regressed` / `no-regression` / `unknown`). It MUST treat a baseline whose `state` is not `completed` as `unknown` and NEVER as an empty failing set, mirroring the discipline `SuiteBaseline.failures`' own docstring states. No I/O, no git, no suite run.
  - Depends on: none
  - Expected outcome: a function that, given the two measured `ld8lb3` inputs, returns `no-regression` with an empty new-id set; given one added id, returns `regressed` naming only that id; given an `absent` baseline, returns `unknown`.
  - Execution state: pending
- [ ] E-02 Compare failing ids by NORMALIZED NODE ID rather than by raw line equality, reusing the existing extractor's output shape (`oc_runipd.extract_suite_failures`, which both sides already flow through) so a formatting difference between the baseline run and the post-merge run cannot read as a regression. State in the code WHICH normalization is applied and why raw-string comparison was insufficient.
  - Depends on: E-01
  - Expected outcome: two runs reporting the same failure with differing surrounding text compare EQUAL; two genuinely different node ids compare UNEQUAL.
  - Execution state: pending

### Task group 2: the wiring

- [ ] E-03 Consume E-01's predicate inside `make_integration_validation_runner` so the returned verdict is relative: a measured red whose failing set introduces NOTHING new PASSES revalidation, and the recorded reason says so explicitly, naming the baseline commit it was compared against. A red with any new id keeps refusing. Read the baseline from the `item` the factory ALREADY receives; add no new parameter.
  - Depends on: E-01, E-02
  - Expected outcome: replaying `ld8lb3`'s recorded inputs through the factory yields `passed=True` with a reason naming base commit `301a1d8fbc15`; injecting one extra failing id yields `passed=False`.
  - Execution state: pending
- [ ] E-04 Extend the `_record_revalidation` record so an auditor can see the comparison rather than infer it: persist the baseline state, the baseline id set it was compared against, and the NEW ids that drove the verdict. Preserve every existing key and the existing `measured`/`skipped` honesty flags untouched.
  - Depends on: E-03
  - Expected outcome: `item["post_merge_revalidation"]` gains the comparison fields; an existing consumer reading only today's keys is unaffected.
  - Execution state: pending

### Task group 3: the guard

- [ ] E-05 Add a regression test file pinning the three behaviors and one anti-fail-open control: equal failing sets integrate; one new id refuses; a non-`completed` baseline refuses (fail closed); and a control that FAILS if a future edit makes an absent baseline read as an empty set. Drive the real factory, not a reimplementation of its logic.
  - Depends on: E-03, E-04
  - Expected outcome: the new file is RED against pre-fix source and GREEN after, with the pre-fix red demonstrated by reverting only the source file.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The three-valued unknown discipline is already the house rule for this exact data and is stated in `SuiteBaseline`'s own docstring: "an empty tuple with `state == \"absent\"` means UNKNOWN, not 'nothing was failing'". `suite_baseline_context` implements the same inversion-avoidance on the prompt side, stating absence as UNKNOWN in prose. This plan must not introduce a fourth spelling of that rule.
- The repository's standing preference is to CONSUME an existing vocabulary rather than mint a parallel one. `runner_shared` already separates "the gate measured and refused" (`INTEGRATION_REFUSAL_CONFLICT` / `merge-refused`) from "the gate could not measure" (`INTEGRATION_REFUSAL_UNMEASURED` / `merge-unchecked`), the latter added 2026-09-21 by `l2mzxn` after a near-identical incident stranded three verified lanes. This plan adds NO third kind: a no-regression red becomes a PASS, not a new refusal class.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The gate's verdict is absolute, not relative | `make_integration_validation_runner` sets `passed` from the merged-tree run alone; `grep -c baseline` over its body returns `0` |
| F-2 | The baseline was measured and available for both refused items | `attempts[0]["suite_baseline"]` has `state: completed`, `base_commit: 301a1d8fbc15`, and the one failing id, for `ld8lb3` and `65cuw0` alike |
| F-3 | The failing SET was unchanged in both refusals | baseline `1 failed, 8042 passed` vs post-merge `1 failed, 8064 passed` (`ld8lb3`); `1 failed, 8063 passed` vs `1 failed, 8084 passed` (`65cuw0`) |
| F-4 | The seam needs no new injection | the factory is already called with `item`, and `execute_item_core` writes `attempt["suite_baseline"]` BEFORE the integration block builds `val_runner` |
| F-5 | The defect is not confined to one run | `h90ij1` in `run-20260922T023434Z-2057475` refused with the same baseline id among its failures |
| F-6 | The blast radius is larger than the refused items | three further items reached `dependency-blocked` solely because their dependencies were refused (`ut0vzr`, `k311gw`, `lkexaw`) |

## Proposed changes (ordered, validatable)

1. A pure new-failure predicate over (merged failing ids, `SuiteBaseline`) returning new ids plus `regressed`/`no-regression`/`unknown` (E-01).
2. Normalized node-id comparison so formatting cannot masquerade as a regression (E-02).
3. `make_integration_validation_runner` consumes the predicate and passes a no-regression red, recording the baseline commit in its reason (E-03).
4. The revalidation record carries the comparison inputs and outputs for audit (E-04).
5. A regression file pinning all three verdicts plus a fail-open control (E-05).

## Deferred / out of scope (with reason)

- The inert `not-mine` release (backlog `c74dm7`): a separate defect with its own plan. Fixing this plan makes the question arise less often; it does NOT make the override work, and `not-mine` must keep covering what a baseline cannot (a failure that landed on main mid-turn, a flake, an order-dependence).
- `reattempt_deferred_integrations`' accepted-and-ignored `validation_runner_for` (backlog `iv4n2c`): latent today because both call sites build from the same factory, and widening this plan to it would mix an inert-injection fix into a verdict-correctness fix.
- Any change to `integration_is_earned`'s two-mode rule, to the verifier prompt, or to the per-lane gate-answer question text: this plan changes ONE verdict computation and deliberately touches no trust-signal vocabulary.
- Retroactively re-integrating the already-stranded lanes: they were merged by hand on 2026-09-22 (`ccbe22c1`, `f2410f75`, `8620c214`, `5c25bcd0`, `f38aeb4b`, `f7a25882`), so there is nothing left to recover and a re-run would assert work that already landed.

## Scope check

- Over-scope: none. Two paths, one of them a new test file.
- Under-scope: the fix corrects the VERDICT but not the operator-facing sentence `orchestrate_isolation` prints for `integration_failed_combined_red` ("Full test suite / revalidation failed after merging isolated lanes"), which remains accurate for a genuine regression and is not reached for a no-regression red once E-03 lands. If review judges that message must also distinguish the two, that is a one-line addition inside the declared paths.

## Required tests / validation

- `python3 -m pytest tests/test_integration_revalidation_baseline.py` GREEN after, and demonstrated RED before by reverting only `agent_workflows/runner_shared.py` while keeping the new tests.
- `python3 -m pytest` bare, with the count line pasted, showing no new failing node ids against a baseline taken in the same worktree before the change.
- The two REPLAY checks, driven through the real factory rather than a reimplementation: `ld8lb3`'s recorded (baseline ids, merged ids) integrates; the same inputs plus one synthetic new id refuses.
- The fail-open control from E-05 must FAIL if an absent baseline is ever made to read as an empty set.

## Spec / documentation sync

No `.spec.md` amendment. The relevant spec text (`25kzda`, and `l2mzxn`'s 2026-09-21 separation of measured-red from unmeasured) already requires the gate to state what it measured; this plan makes the verdict honor the measurement it already takes, which moves TOWARD that contract rather than changing it. The in-code comment block above `INTEGRATION_REFUSAL_CONFLICT` should gain one sentence noting that a measured red with no NEW failures is not a refusal, since that block is where a future reader will look for the refusal taxonomy.

## Open questions

### OQ-01: Should a no-regression red integrate silently, or integrate while emitting a visible warning?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: RESOLVED to integrate AND warn, with the warning naming the pre-existing failing ids and the baseline commit. Silence would hide a genuinely red tree, which is the opposite failure from the one this plan fixes; refusing would keep today's defect. The warning costs one line and preserves the operator's ability to see that main is not green. This does not require a new refusal kind because the item still integrates.

### OQ-02: If the baseline is `absent`, should the gate refuse or integrate?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: RESOLVED to REFUSE, i.e. keep today's behavior exactly. An absent baseline means nobody measured, and treating unknown as "nothing was failing" is precisely the inversion `SuiteBaseline`'s docstring and `suite_baseline_context` both exist to prevent. This keeps the change strictly a narrowing of when a refusal fires and guarantees the plan cannot make any currently-passing gate more permissive.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the predicate driven on the three cases with output pasted: `ld8lb3`'s real baseline+merged id sets returning `no-regression` with an empty new set; the same plus one synthetic id returning `regressed` naming ONLY that id; a `state: absent` baseline returning `unknown`. Paste the actual return values, not a description.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: two failing lines for the same node id differing in surrounding text, shown comparing EQUAL, and two different node ids shown comparing UNEQUAL, with the normalization function's actual output pasted for each input.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the REAL `make_integration_validation_runner` driven with `ld8lb3`'s recorded inputs, pasting `passed` and the full recorded `reason`, which must name base commit `301a1d8fbc15`; then the same call with one extra failing id, pasting `passed=False`. Both through the factory, not a copy of its logic.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: the resulting `item["post_merge_revalidation"]` dict pasted in full for a no-regression case, showing the new comparison fields AND every pre-existing key (`passed`, `reason`, `failures`, `measured`, `skipped`, `cached`, `tree`, `merged_files`) still present with unchanged meaning.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `python3 -m pytest tests/test_integration_revalidation_baseline.py` output pasted GREEN after the change and RED before it (the before-run produced by reverting only the source file), plus the bare `python3 -m pytest` count line showing no new failing node ids, plus the fail-open control demonstrated failing when an absent baseline is forced to read as empty.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is human-approved before execution and is executed under the repository's standing agent execution contract: commit ONLY the declared `Scope-Paths` through `aw commit`, never `git add -A` and never push; paste ACTUAL runner output for every test claim rather than asserting success; and do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete observed evidence. A worker-role lane may NOT perform the terminal transition (`AW-LIFECYCLE-ROLE-001`): the runner owns `aw ipd begin`/`aw ipd finalize`. Because this plan changes when an integration refuses, the executor must confirm the bare suite shows no new failing node ids before claiming the gate behaves correctly, since a fix here that made the gate MORE permissive in any other case would be worse than the defect it removes.

# IPD: Re-scope check.setid-collision to its within-type half and settle the include_retired split

- Date: 2026-09-10
- Kind: child
- Concern: `check.setid-collision` reports 38 findings on a DEFAULT `aw check` run and every one of them is CORRECT BEHAVIOR being flagged as an error. The maintainer ruled on 2026-09-10 (DECISIONS D153, spec `2lcqno`) that a setid is a SHARED cross-type TOPIC label, so a setid appearing under two record types is the endorsed normal state. The rule still treats it as drift at severity `error`, which is the "gate that false-positives on correct behavior TRAINS agents to bypass it" failure mode this repository has already recorded once (`gjadwm`).
  THE RULE IS NOT SIMPLY WRONG, WHICH IS WHY THIS IS A RE-SCOPE AND NOT A DELETION. It emits from two branches. The cross-type branch (`check_engine.py:897-905`) is now dead by ruling. The within-type conflicting-descriptive branch (`:906-915`) is a GENUINE defect: one setid carrying two different descriptives inside one type is a real inconsistency in that Set's own name. Measured at HEAD: 38 findings on the default scope are ALL cross-type, and the 5 genuine within-type cases appear ONLY under `--all`. Deleting the rule would silently drop those 5.
  AND THE RULE IS FILED UNDER THE WRONG INVARIANT, which must be corrected in the same change or the catalog and the code stay in provable disagreement. It is registered as `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-09")` (`check_engine.py:95-97`), but `I-09` is FILENAME-GRAMMAR conformance (spec `pqsx96` catalog row I-09) and setid semantics is not filename grammar. Spec `pqsx96` gained `I-16` for exactly this on 2026-09-10 and its Section 4 records that the code still says `I-09` deliberately, to be repointed HERE.
  A THIRD, INDEPENDENT DEFECT SITS IN THE SAME BLAST RADIUS AND EXPLAINS THE COUNTING CONFUSION: `doctor.py:530` hardcodes `include_retired=True` while `check_engine.py:1760` passes a flag defaulting to `False`, so ONE predicate reports two different populations to two surfaces. That is the entire 38-versus-86 gap. It predates the reversal and spec `2lcqno` Section 6 names it as work not to inherit, because acceptance criterion 3 ("both surfaces report the same population") cannot otherwise be evaluated.
- Scope: The setid-collision rule's emission, its registered invariant id, and the retired-record asymmetry between the two consuming surfaces. IN: removing the cross-type emission entirely (not relabelling it, not hiding it behind a flag); keeping and pinning the within-type conflicting-descriptive emission; repointing the `RuleSpec` invariant from `I-09` to `I-16`; settling which population `aw check` and `aw doctor` scan for this rule and making them agree; updating the two conformance golden fixtures and the one existing test that depends on the cross-type behavior. OUT: type-scoped selector resolution (Order 02, the sibling child); any change to `check.id6-collision` or `check.id6-identity-slot`, whose `I-09` home is defensible and deliberately untouched; any artifact rename, which the ruling forbids; the `Graduated-To` forward link (pending plan `bwgyum`).
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/doctor.py, tests/test_check_engine.py, tests/fixtures/conformance_goldens/check_findings.agent.golden, tests/fixtures/conformance_goldens/check_findings.json.golden, .aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md
- Item-Dependencies: none
- Status: to-review
- Set: setidfix
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 216rgg
- From-Spec: 2lcqno

## Workflow history

- 2026-09-10 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from spec `2lcqno` (`- Status: to-review`) as checklist item T-08, after the maintainer chose "write plans for both, ready for review" over coding directly. Every line number and count in this plan was MEASURED at HEAD rather than carried from the spec: the two emitting branches, the `RuleSpec` row, the two `include_retired` sites, the 38-versus-86 split with its 78/2/1/5 breakdown, and the two existing tests plus two golden fixtures that depend on current behavior. ONE FINDING CAME OUT OF THAT MEASUREMENT AND CHANGES THE TEST WORK (F-4): `test_all_runs_collisions_once` builds a plan AND a spec sharing setid `demo`, so it exercises the cross-type branch and must be retargeted, while `test_setid_collision` uses two PLANS with differing descriptives and stays green untouched. A plan that said only "update the tests" would have missed which of the two is which.
- 2026-09-10 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `aw check` stop reporting 38 errors for the repository's own endorsed naming convention, while keeping the 5 findings that are real, and leave the rule's catalog reference and the two surfaces' scan population in agreement rather than in provable conflict.

READ THE GOAL PRECISELY: this plan REMOVES a false signal and CHANGES NO ARTIFACT. Spec `2lcqno` acceptance criterion 1 requires the 38 findings to disappear WITHOUT any file being renamed; achieving silence by renaming would be the retired sweep plan (`drzbs9`) all over again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the rule

- [ ] E-01 REMOVE THE CROSS-TYPE EMISSION ENTIRELY from `check_engine.check_collisions`, at the branch that today reads `if prev_type != record_type:` and appends the `(different type: ...)` message (`check_engine.py:897-905`). Delete the emission; do NOT relabel it to `info`, do NOT keep it behind a flag or an env var, and do NOT leave a commented-out branch. Spec `2lcqno` OQ-01 resolved this explicitly from measurement: an `info` variant would add 38 lines across 28 distinct setids to a default run, three times its own stated threshold, and worse, narrating the NORMAL state trains a reader to treat cross-type sharing as remarkable, which is the belief that produced the reversed design. UPDATE THE DOCSTRING in the same edit: `:843-844` currently documents the rule as "the same setid under two different types, or the same setid with two different non-None descriptives", and the first clause becomes false. State positively that a cross-type setid is CORRECT per D153 and cite `2lcqno` N1, so the next reader does not re-add the branch as a "missing" check.
  - Depends on: none
  - Expected outcome: a default `aw check all` reports ZERO `check.setid-collision` findings; the tracked corpus is unchanged (no file renamed, no front matter edited).
  - Execution state: pending

- [ ] E-02 KEEP AND PIN THE WITHIN-TYPE CONFLICTING-DESCRIPTIVE EMISSION (`check_engine.py:906-915`, the `elif desc is not None and prev_desc is not None and desc != prev_desc:` branch). This is the half that is load-bearing and the reason this is a re-scope: one setid carrying two different descriptives inside ONE type is a genuine inconsistency, and 5 such cases exist at HEAD (visible only under `--all`). Leave its message and its recovery guidance intact. VERIFY, do not assume, that removing the cross-type branch does not change this branch's behavior: both branches read the same `seen_sets` dictionary, which stores `(record_type, descriptive, path)` keyed on the setid ALONE, so the FIRST file seen for a setid wins the stored slot regardless of type. That means a cross-type predecessor can currently occupy the slot and make a genuine within-type conflict compare against the WRONG descriptive. State whether that is possible after E-01 and, if it is, fix it here rather than deferring it.
  - Depends on: E-01
  - Expected outcome: the 5 within-type findings still report under `--all`, with their message and recovery unchanged, and each compares against a same-type predecessor.
  - Execution state: pending

- [ ] E-03 REPOINT THE REGISTERED INVARIANT from `I-09` to `I-16` in the `RuleSpec` row for `check.setid-collision` (`check_engine.py:95-97`), IN THIS SAME CHANGE. Spec `pqsx96` added catalog row `I-16` (setid semantics) on 2026-09-10 and its Section 4 states plainly that the code still says `I-09` on purpose, to be corrected by the commit that re-scopes the rule; leaving it would keep a documented, deliberate disagreement live. Then REMOVE that "they disagree until then" note from `pqsx96` Section 4, since it becomes false the moment this lands. DO NOT touch `check.id6-collision` or `check.id6-identity-slot`, which are also registered under `I-09`: the identity-slot rule genuinely concerns the filename slot, so that home is defensible and repointing it is out of scope.
  - Depends on: E-01
  - Expected outcome: `rule_spec("check.setid-collision").invariant == "I-16"`; the two id6 rules still read `I-09`; `pqsx96` Section 4 no longer claims a pending disagreement.
  - Execution state: pending

### Task group 2: make the two surfaces agree

- [ ] E-04 SETTLE THE `include_retired` ASYMMETRY AND MAKE IT DELIBERATE RATHER THAN ACCIDENTAL. `doctor.py:530` hardcodes `include_retired=True` (as do `:484` and `:499` for other probes) while `check_engine.py:1760` passes a flag whose default is `False` (`:507`, `:557`), so one predicate reports two populations to two surfaces and the same repository shows 38 findings to `aw check` and 86 to `aw doctor`. DECIDE WHICH IS AUTHORITATIVE AND SAY WHY IN THE CODE, rather than silently aligning one to the other: the argument for including retired records is that a superseded plan's name is still on disk and still collides; the argument against is that a retired record is not actionable, so reporting it is noise a reader cannot fix. Whichever is chosen, the two surfaces MUST agree for this rule, and the choice must be stated at the call site. NOTE this is a PRE-EXISTING defect that predates the reversal (spec `2lcqno` Section 6), so its fix must not be described as part of the reversal.
  - Depends on: E-01
  - Expected outcome: `aw check` and `aw doctor` report the SAME `check.setid-collision` population; the chosen population is justified in a code comment naming both arguments.
  - Execution state: pending

### Task group 3: the surfaces that encode today's behavior

- [ ] E-05 RETARGET THE ONE EXISTING TEST THAT DEPENDS ON THE CROSS-TYPE BRANCH, AND LEAVE THE OTHER ALONE. Measured, so the executor is confirming rather than exploring (F-4): `tests/test_check_engine.py::test_all_runs_collisions_once` (`:116-121`) builds a PLAN and a SPEC both on setid `demo`, which is a cross-type case; it currently asserts only on `check.id6-collision` counts, so establish whether it still passes after E-01 and, if its fixture's INTENT was to exercise the setid rule too, give it an explicit same-type fixture rather than relying on a side effect. By contrast `test_setid_collision` (`:106-114`) uses TWO PLANS with descriptives `Alpha` and `Beta`, which is the SURVIVING within-type case, so it must stay green UNTOUCHED and is the natural regression pin for E-02. ADD a case asserting a cross-type setid produces NO finding, since nothing currently pins the new behavior and without it a future change could re-add the branch silently.
  - Depends on: E-01, E-02
  - Expected outcome: a new test pins cross-type silence; `test_setid_collision` passes unedited; `test_all_runs_collisions_once` passes with its fixture's intent made explicit.
  - Execution state: pending

- [ ] E-06 UPDATE THE TWO CONFORMANCE GOLDEN FIXTURES, which are the surface most likely to be forgotten because they fail as an opaque diff rather than as a named assertion. `tests/fixtures/conformance_goldens/check_findings.json.golden` and `check_findings.agent.golden` each contain a `setid-collision` entry (measured: 1 occurrence each). Regenerate or hand-correct them per whatever mechanism owns them, and state WHICH mechanism you used. Also check `tests/test_cli_quality_gates.py` and `tests/test_agentadhere_policy_engine.py`, both of which reference the rule id: the policy-engine test asserts the rule belongs to an invariant FAMILY, so E-03's `I-16` repoint may break it, and that is exactly the kind of coupling a rule-id change breaks silently.
  - Depends on: E-01, E-03
  - Expected outcome: both goldens match the new output; every test referencing the rule id or its invariant passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- SEVERITY AND INVARIANT ARE REGISTRY CONCERNS, NOT PER-EMITTER ONES. `check_engine.RULE_REGISTRY` maps a rule id to a `RuleSpec`, `enrich_drift` stamps it onto the `Drift`, and `artifact_core.drift_exit_code` fails the gate for anything that is not `info`. So changing how loudly a check speaks means editing the registry row, never a message string.
- THE RULE FIRES ONLY ON THE FULL SWEEP. `check_collisions` runs from `check_types`'s `collisions` branch, entered only when `types == ["all"]`, so this rule reaches `aw check all` and NOT `aw check plans`. State that rather than implying every check validates it.
- `seen_sets` IS KEYED ON THE SETID ALONE and stores `(record_type, descriptive, path)` for the FIRST file seen. Both emitting branches read that one slot, which is why E-02 must verify the two halves are genuinely independent rather than assuming it.
- THE GOLDEN FIXTURES ARE A REAL TEST SURFACE for any rule-output change, and they fail as a diff rather than a named assertion, which is why E-06 exists as its own item.
- SUITE BARE: `python3 -m pytest`. `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals. Known environmental failure in the primary checkout only: `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, caused by a gitignored local `opencode-recovery/` dump; it passes in a clean worktree.

## Findings

| Id | Severity | Location (measured at HEAD) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `check_engine.py:897-905` | The cross-type branch emits 38 findings on the default scope, all for the endorsed normal state, at severity `error`. | `check_collisions` run; 38 findings, all `(different type: ...)`, across 28 distinct setids |
| F-2 | HIGH | `check_engine.py:906-915` | The within-type descriptive branch is GENUINE and must survive; 5 such cases exist and appear ONLY under `--all`. | default scope: 38 cross-type / 0 descriptive; `--all`: 86 total, 78+2+1 cross-type and 5 descriptive |
| F-3 | MEDIUM | `check_engine.py:95-97`; `pqsx96` catalog | The rule is registered under `I-09`, which is filename-grammar conformance; setid semantics is a different invariant, now catalogued as `I-16`. | `rule_spec("check.setid-collision").invariant == "I-09"`; `pqsx96` I-09 row reads "Filename-grammar conformance" |
| F-4 | MEDIUM | `tests/test_check_engine.py:106-121` | The two existing tests split cleanly and a naive "update the tests" would confuse them: `test_all_runs_collisions_once` uses a plan AND a spec on setid `demo` (cross-type, affected), while `test_setid_collision` uses two PLANS with differing descriptives (within-type, unaffected). | both fixtures read |
| F-5 | MEDIUM | `doctor.py:484,499,530` vs `check_engine.py:507,557,1760` | One predicate, two populations: doctor hardcodes `include_retired=True`, check defaults it `False`. This is the whole 38-versus-86 gap and predates the reversal. | source read; both counts measured |
| F-6 | LOW | `tests/fixtures/conformance_goldens/*.golden`; `tests/test_cli_quality_gates.py`; `tests/test_agentadhere_policy_engine.py` | Four further surfaces encode the rule id or its invariant family; the policy-engine test asserts an invariant family, so E-03's repoint may break it. | `grep -c setid-collision` on each |
| F-7 | INFO | spec `2lcqno` OQ-01 | The `info`-severity alternative was considered and rejected FROM MEASUREMENT (38 findings across 28 setids, three times its own threshold), so an executor must not reintroduce it as a compromise. | the spec's resolved OQ-01 |

## Proposed changes (ordered, validatable)

1. E-01 removes the cross-type emission and corrects the docstring that documents it.
2. E-02 keeps the within-type emission and verifies the two halves are independent given the shared `seen_sets` slot.
3. E-03 repoints the registered invariant to `I-16` and removes the now-false disagreement note from the catalog spec.
4. E-04 makes `aw check` and `aw doctor` agree on the scanned population, with the choice justified.
5. E-05 retargets the one affected test, leaves the unaffected one alone, and adds the missing cross-type-silence pin.
6. E-06 updates the two goldens and the two further rule-id-dependent tests.

## Deferred / out of scope (with reason)

- TYPE-SCOPED SELECTOR RESOLUTION: Order 02 of this Set (`w2y5ac`). It is the fix for the original `agentadhere` failure and is independent of this rule's severity, so the two are separable and separately reviewable.
- REPOINTING `check.id6-collision` / `check.id6-identity-slot` off `I-09`: deliberately not done. The identity-slot rule genuinely concerns the filename slot, so its home is defensible; only the setid rule is a clear mismatch (`pqsx96` Section 4 records this).
- RENAMING ANY ARTIFACT: forbidden by the ruling. The retired plan `drzbs9` was exactly this and is superseded.
- THE `Graduated-To` FORWARD LINK: pending plan `bwgyum`, which survives the reversal untouched.
- AUDITING EVERY OTHER RULE'S CATALOG HOME: a broader registry audit with its own blast radius. Only the rule whose meaning changed is corrected here.

## Scope check

- Over-scope: none. Every declared path is touched by a named E-item: `check_engine.py` (E-01/E-02/E-03), `doctor.py` (E-04), `tests/test_check_engine.py` (E-05), the two goldens (E-06), and `pqsx96` (E-03's note removal).
- Under-scope: none remaining. The review-time sweep added E-06's two extra test surfaces (F-6) and E-04's justification requirement; both were absent from the authored intent.

## Required tests / validation

`python3 -m pytest` bare, in an isolated worktree, baseline measured there and pasted, compared by failing NODE ID rather than by total. Beyond the suite: the finding COUNTS before and after on BOTH scopes (default and `--all`) and on BOTH surfaces (`aw check all` and `aw doctor`), since the whole deliverable is a count going to zero for one branch while another stays non-zero; plus `git status --porcelain` proving no artifact was renamed or edited to achieve it.

## Spec / documentation sync

`.aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md` is DECLARED IN SCOPE and edited by E-03, which removes the "the code still says I-09, to be repointed by the commit that re-scopes the rule" note once that becomes false. That is the only spec edit, and it deletes a statement rather than changing a requirement.

Spec `2lcqno` is the governing spec and is NOT edited: this plan implements its N1/N5 and its acceptance criteria 1, 2 and 3. Its `- Status:` is `to-review` at authoring time, which is why this plan is `to-review` and not `approved`: the spec should clear review before this executes.

## Open questions

### OQ-01: Which population should both surfaces scan, retired records included or excluded?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-04 states the REQUIREMENT (the two surfaces must AGREE, and the choice must be justified at the call site) and either answer satisfies it. Left open deliberately rather than pre-empted, because the deciding evidence is best gathered while making the change: count the findings under each choice for this rule, and check whether any OTHER doctor probe depends on `include_retired=True` such that changing it there would alter an unrelated finding. LEAN, offered as a lean and not a decision: EXCLUDE retired records for this rule, because a superseded plan's name is not actionable and the reader cannot fix it, which is the same reasoning that keeps `check.stale-index-missing` at `info`. Do not treat that lean as the answer; measure both.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `check.setid-collision` finding count on the DEFAULT scope before (expect 38) and after (expect 0), and paste `git status --porcelain` proving NO artifact was renamed or edited to achieve it. Also paste the corrected docstring showing the cross-type clause is gone and D153 / `2lcqno` N1 are cited. Confirm no commented-out branch and no flag-guarded remnant remains (`grep` for `different type`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `--all` scope count showing the 5 within-type descriptive findings STILL report, with one full message. Plus a MUTATION CHECK: break the descriptive comparison, show the new pin from E-05 FAILS, restore, show it passes. State explicitly whether a cross-type predecessor can still occupy the shared `seen_sets` slot and, if so, paste the fix and a fixture proving a within-type conflict compares against a same-type predecessor.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `rule_spec("check.setid-collision")` showing `invariant='I-16'`, AND `rule_spec` for both id6 rules showing they still read `I-09` (proving the repoint was surgical). Paste the `pqsx96` Section 4 diff showing the disagreement note removed.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste this rule's finding count from `aw check all` AND from `aw doctor` showing they now MATCH, with the before-values (38 and 86) stated for contrast. Paste the code comment justifying the chosen population and naming both arguments. Confirm no OTHER doctor probe's output changed, by pasting the doctor finding totals per rule before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new cross-type-silence test passing, and paste `test_setid_collision` passing WITHOUT having been edited (show it is unchanged in the diff). State what you did with `test_all_runs_collisions_once` and why. Include the mutation check required by V-02.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste both golden-consuming tests passing, and name the mechanism used to regenerate or correct each golden. Paste `tests/test_cli_quality_gates.py` and `tests/test_agentadhere_policy_engine.py` passing, since the latter asserts an invariant family and is the surface E-03 could break silently.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Size note: 6 E-leaves in 3 groups. Grown from an authored 4 by the measurement sweep, which added the golden/extra-test surface (F-6) and split the invariant repoint from the emission change because they have different failure modes.
- Cohesion rationale: E-01/E-02/E-03 are one rule's emission plus its registry row and must land together, because removing the cross-type branch without repointing the invariant leaves the catalog and code in a disagreement this plan is partly meant to close. E-04 is a separate pre-existing defect included ONLY because acceptance criterion 3 cannot be evaluated while the two surfaces count different populations. E-05/E-06 are the test surfaces the first three break.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since a rejected hook can leave paths in the index. When reporting tests passed, paste the ACTUAL runner output. This is a SHARED CHECKOUT: other agents are editing this tree concurrently, so never revert or commit a file you did not change.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved 216rgg --by-human --message ...`) before execution. Its governing spec `2lcqno` is `to-review`; prefer letting the spec clear review first, since a review could still change N5. On completion, transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

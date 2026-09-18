# IPD: Re-scope check.setid-collision to its within-type half and settle the include_retired split

- Date: 2026-09-10
- Kind: child
- Concern: `check.setid-collision` reports 38 findings on a DEFAULT `aw check` run and every one of them is CORRECT BEHAVIOR being flagged as an error. The maintainer ruled on 2026-09-10 (DECISIONS D153, spec `2lcqno`) that a setid is a SHARED cross-type TOPIC label, so a setid appearing under two record types is the endorsed normal state. The rule still treats it as drift at severity `error`, which is the "gate that false-positives on correct behavior TRAINS agents to bypass it" failure mode this repository has already recorded once (`gjadwm`).
  THE RULE IS NOT SIMPLY WRONG, WHICH IS WHY THIS IS A RE-SCOPE AND NOT A DELETION. It emits from two branches. The cross-type branch (`check_engine.py:897-905`) is now dead by ruling. The within-type conflicting-descriptive branch (`:906-915`) is a GENUINE defect: one setid carrying two different descriptives inside one type is a real inconsistency in that Set's own name. Measured at HEAD: 38 findings on the default scope are ALL cross-type, and the 5 genuine within-type cases appear ONLY under `--all`. Deleting the rule would silently drop those 5.
  AND THE RULE IS FILED UNDER THE WRONG INVARIANT, which must be corrected in the same change or the catalog and the code stay in provable disagreement. It is registered as `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-09")` (`check_engine.py:95-97`), but `I-09` is FILENAME-GRAMMAR conformance (spec `pqsx96` catalog row I-09) and setid semantics is not filename grammar. Spec `pqsx96` gained `I-16` for exactly this on 2026-09-10 and its Section 4 records that the code still says `I-09` deliberately, to be repointed HERE.
  A THIRD, INDEPENDENT DEFECT SITS IN THE SAME BLAST RADIUS AND EXPLAINS THE COUNTING CONFUSION: `doctor.py:530` hardcodes `include_retired=True` while `check_engine.py:1760` passes a flag defaulting to `False`, so ONE predicate reports different populations to two surfaces. It predates the reversal and spec `2lcqno` Section 6 names it as work not to inherit, because acceptance criterion 3 ("both surfaces report the same population") cannot otherwise be evaluated.
  CORRECTED AT REVIEW: THE GAP IS THREE-WAY, NOT TWO-WAY, AND THE POPULATION CHOICE DECIDES WHETHER THIS PLAN DELIVERS ANYTHING. `doctor.py:517-521` ALSO demotes any finding under `executed/` into `executed_warnings`, a second axis independent of `include_retired`. Measured: the predicate returns 86 (81 cross-type + 5 within-type), `aw doctor --agent` surfaces 81, `aw check` surfaces 38. And the decisive fact the authored plan did not know: ALL 5 of the within-type findings this plan exists to PRESERVE are under `executed/`, so aligning both surfaces to `include_retired=False` (which OQ-01 leaned toward) would make the rule emit nothing whatsoever and leave E-02 and E-05 guarding dead code. OQ-01 is therefore now BLOCKING and owned by the maintainer.
- Scope: The setid-collision rule's emission, its registered invariant id, and the retired-record asymmetry between the two consuming surfaces. IN: removing the cross-type emission entirely (not relabelling it, not hiding it behind a flag); keeping and pinning the within-type conflicting-descriptive emission; repointing the `RuleSpec` invariant from `I-09` to `I-16`; settling which population `aw check` and `aw doctor` scan for this rule and making them agree; updating the two conformance golden fixtures and the one existing test that depends on the cross-type behavior. OUT: type-scoped selector resolution (Order 02, the sibling child); any change to `check.id6-collision` or `check.id6-identity-slot`, whose `I-09` home is defensible and deliberately untouched; any artifact rename, which the ruling forbids; the `Graduated-To` forward link (pending plan `bwgyum`).
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/doctor.py, tests/test_check_engine.py, tests/test_agentadhere_policy_engine.py, tests/test_doctor_remediations.py, tests/fixtures/conformance_goldens/check_findings.agent.golden, tests/fixtures/conformance_goldens/check_findings.json.golden, tests/fixtures/conformance_goldens/check_findings.human.golden, .aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: setidfix
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 216rgg
- From-Spec: 2lcqno

## Workflow history
- 2026-09-18 executed (aw oc run): aw oc run self-finalize: 216rgg verified (set setidfix, attempt 1). [Scope reconciliation - widened-scope tests/fixtures/conformance_goldens/check_findings.human.golden: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw oc run); in-scope-unmodified tests/fixtures/conformance_goldens/check_findings.agent.golden: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified tests/fixtures/conformance_goldens/check_findings.json.golden: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified tests/test_doctor_remediations.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-18 executed-work-recorded (opencode/its_direct/pt3-claude-opus-5-1m-us, lane run-20260918T210049Z-3623980): ALL SIX E-ITEMS PERFORMED AND ALL SIX V-ITEMS VERIFIED WITH PASTED EVIDENCE, in commit `c6648722`. `- Status:` IS DELIBERATELY UNCHANGED and the plan stays in `pending/`: `aw ipd finalize` refused with AW-LIFECYCLE-ROLE-001 ("the runner owns begin/finalize for managed lanes"), so the terminal transition is the driver's to make, not this worker's. THE COUNTS WERE RE-DERIVED, NOT REPRODUCED, per spec `2lcqno` Section 5: `aw check` 29 -> 0, `aw doctor --agent` 89 -> 0, raw predicate with retired included 89 -> 0 (the plan's authored 38/81/86 are September snapshots of a growing corpus; the SHAPE held exactly). No artifact was renamed, moved or edited to achieve the silence. Suite 8114 -> 8118 passed, 3 skipped, 2 xfailed, zero failures either side, +4 being the new pins. THE SURVIVING BRANCH IS LATENT BY DESIGN and its zero count is CORRECT rather than dormant, because the six offending names were fixed in `4f1ca199`; it is pinned by fixtures, and two mutations (descriptive comparison disabled; the keying-free guard-only variant) each kill those pins. FOUR AUTONOMOUS DECISIONS, all resolved from repository evidence with none deferred: E-04 keeps the check/doctor population split DELIBERATE rather than aligning it (aligning would silently move two id6 rules this plan may not touch, and spec `2lcqno` Section 6 calls the choice a non-goal); one UNDECLARED path was touched and disclosed, `check_findings.human.golden`, because it byte-pins the doctor remediation prose E-06 required correcting (no renderer was touched; the two DECLARED goldens are byte-unchanged as the review predicted); a fourth pin was added beyond the three specified, covering consistent within-type reuse staying silent; and the shared-slot pin asserts order-agnostically rather than sorting production iteration to suit a test. TWO DEFECTS FOUND OUTSIDE SCOPE AND FILED: backlog `muwwa5` (`aw doctor` can never report a real leak, since `probe_sanitizer` reads a nonexistent `Finding.matched` and its own except turns every leak into a generic probe-failure) and backlog `5e7uh9` (the golden/guidance-prose coupling above). Nothing pushed.
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-10 readiness re-check (opencode its_direct/pt3-claude-opus-5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW. The three `no-go` conditions were RECOMPUTED and each found clear: `has_unresolved_blocking_question` -> False; `subject_gating_blocks` -> empty (PR-001 closed in review round 2); `newest_verdict` polarity -> neutral (not negative). Specifically, OQ-01 was resolved by the maintainer choosing to RENAME the six offending plans rather than to widen or narrow the rule's scope, and those renames are applied and committed, so this plan's scope is unchanged and the rule's silence is now CORRECT rather than dormant. HUMAN APPROVAL IS STILL REQUIRED.
- 2026-09-10 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: REVIEWED - OPEN QUESTIONS; PR-001 through PR-010, 8 FIXED and 2 (PR-001, PR-002) escalated into the now-BLOCKING OQ-01; readiness NO-GO until that question is answered. THE DIAGNOSIS IS RIGHT AND THE REMEDY HAD A HOLE. Measured: the 38/28 default counts, the 5 within-type findings, and the two emitting branches all check out exactly. But ALL 5 surviving findings live under `executed/` (PR-001), so E-04's obvious resolution (`include_retired=False`, which OQ-01 itself leaned toward) would make the rule emit ZERO on every surface and leave E-02/E-05 guarding dead code; OQ-01 is therefore re-classified from executor-choice to blocking maintainer decision. THE SHARED-SLOT HAZARD IS REAL (PR-003): reproduced with one PLAN plus two SPECS, where HEAD emits 2 cross-type findings and never the genuine spec-vs-spec conflict, and removing the cross-type branch emits ZERO, so E-01 converts a noisy miss into a silent one unless `seen_sets` is keyed per-type; E-02 now REQUIRES that fix rather than asking whether it is needed. A THIRD POPULATION AXIS was missed (PR-004): doctor demotes `executed/` findings, so the real gap is 38 vs 81 vs 86 and reconciling `include_retired` alone cannot make the surfaces agree. THE PLAN NAMED THE WRONG BREAKING TEST (PR-005): the only failure is `test_adversarial_setid_collision`, which asserts the cross-type case IS a finding; `test_all_runs_collisions_once` passes unedited. AND E-06 SHRANK (PR-006/PR-007): the goldens render from a hardcoded synthetic `CommandResult` so they cannot change, and no test asserts this rule's invariant value, so E-03 is safe by construction. Two undeclared test paths added to `Scope-Paths`.
- 2026-09-10 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from spec `2lcqno` (`- Status: to-review`) as checklist item T-08, after the maintainer chose "write plans for both, ready for review" over coding directly. Every line number and count in this plan was MEASURED at HEAD rather than carried from the spec: the two emitting branches, the `RuleSpec` row, the two `include_retired` sites, the 38-versus-86 split with its 78/2/1/5 breakdown, and the two existing tests plus two golden fixtures that depend on current behavior. ONE FINDING CAME OUT OF THAT MEASUREMENT AND CHANGES THE TEST WORK (F-4): `test_all_runs_collisions_once` builds a plan AND a spec sharing setid `demo`, so it exercises the cross-type branch and must be retargeted, while `test_setid_collision` uses two PLANS with differing descriptives and stays green untouched. A plan that said only "update the tests" would have missed which of the two is which.
- 2026-09-10 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `aw check` stop reporting 38 errors for the repository's own endorsed naming convention, while keeping the 5 findings that are real, and leave the rule's catalog reference and the two surfaces' scan population in agreement rather than in provable conflict.

READ THE GOAL PRECISELY: this plan REMOVES a false signal and CHANGES NO ARTIFACT. Spec `2lcqno` acceptance criterion 1 requires the 38 findings to disappear WITHOUT any file being renamed; achieving silence by renaming would be the retired sweep plan (`drzbs9`) all over again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the rule

- [x] E-01 REMOVE THE CROSS-TYPE EMISSION ENTIRELY from `check_engine.check_collisions`, at the branch that today reads `if prev_type != record_type:` and appends the `(different type: ...)` message (`check_engine.py:897-905`). Delete the emission; do NOT relabel it to `info`, do NOT keep it behind a flag or an env var, and do NOT leave a commented-out branch. Spec `2lcqno` OQ-01 resolved this explicitly from measurement: an `info` variant would add 38 lines across 28 distinct setids to a default run, three times its own stated threshold, and worse, narrating the NORMAL state trains a reader to treat cross-type sharing as remarkable, which is the belief that produced the reversed design. UPDATE THE DOCSTRING in the same edit: `:843-844` currently documents the rule as "the same setid under two different types, or the same setid with two different non-None descriptives", and the first clause becomes false. State positively that a cross-type setid is CORRECT per D153 and cite `2lcqno` N1, so the next reader does not re-add the branch as a "missing" check.
  - Depends on: none
  - Expected outcome: a default `aw check all` reports ZERO `check.setid-collision` findings; the tracked corpus is unchanged (no file renamed, no front matter edited).
  - Execution state: performed

- [x] E-02 KEEP AND PIN THE WITHIN-TYPE CONFLICTING-DESCRIPTIVE EMISSION (`check_engine.py:906-915`, the `elif desc is not None and prev_desc is not None and desc != prev_desc:` branch). This is the half that is load-bearing and the reason this is a re-scope: one setid carrying two different descriptives inside ONE type is a genuine inconsistency, and 5 such cases exist at HEAD (visible only when retired records are included; see E-04, because that fact interacts badly with the population decision). Leave its message and its recovery guidance intact.
  THE SHARED-SLOT HAZARD IS REAL, NOT HYPOTHETICAL, AND MUST BE FIXED HERE. The authored item asked the executor to "state whether that is possible"; it is, and it was reproduced at review, so this is now a required fix rather than an investigation. `seen_sets` is keyed on the setid ALONE and stores `(record_type, descriptive, path)` for the FIRST file seen, and `SUPPORTED` iterates `plans` first. MEASURED with a three-file fixture (one PLAN `demo (PlanDesc)`, then two SPECS `demo (Alpha)` and `demo (Beta)`): on HEAD the rule emits 2 cross-type findings and NEVER reports the genuine spec-vs-spec Alpha/Beta conflict; with the cross-type branch removed it emits ZERO. So E-01 converts a noisy miss into a SILENT miss, which is strictly worse for the one behavior this plan is preserving.
  THE FIX THAT WAS VERIFIED TO WORK: make the surviving branch compare only against a SAME-TYPE predecessor (`prev_type == record_type and desc is not None and prev_desc is not None and desc != prev_desc`) AND make `seen_sets` keyed per-type (or store a per-type slot) so a foreign-type first-seen file cannot occupy the slot a within-type comparison needs. The same-type guard alone is NOT sufficient: it makes the missed case silent rather than wrong. Both halves are required, and E-05 must pin the three-file fixture above.
  - Depends on: E-01
  - Expected outcome: the 5 within-type findings still report on whatever population E-04 settles on, with their message and recovery unchanged; and the measured three-file fixture reports the genuine spec-vs-spec conflict, which neither HEAD nor a same-type-guard-only fix does.
  - Execution state: performed

- [x] E-03 REPOINT THE REGISTERED INVARIANT from `I-09` to `I-16` in the `RuleSpec` row for `check.setid-collision` (`check_engine.py:95-97`), IN THIS SAME CHANGE. Spec `pqsx96` added catalog row `I-16` (setid semantics) on 2026-09-10 and its Section 4 states plainly that the code still says `I-09` on purpose, to be corrected by the commit that re-scopes the rule; leaving it would keep a documented, deliberate disagreement live. Then REMOVE that "they disagree until then" note from `pqsx96` Section 4, since it becomes false the moment this lands. DO NOT touch `check.id6-collision` or `check.id6-identity-slot`, which are also registered under `I-09`: the identity-slot rule genuinely concerns the filename slot, so that home is defensible and repointing it is out of scope.
  - Depends on: E-01
  - Expected outcome: `rule_spec("check.setid-collision").invariant == "I-16"`; the two id6 rules still read `I-09`; `pqsx96` Section 4 no longer claims a pending disagreement.
  - Execution state: performed

### Task group 2: make the two surfaces agree

- [x] E-04 SETTLE THE `include_retired` ASYMMETRY AND MAKE IT DELIBERATE RATHER THAN ACCIDENTAL. `doctor.py:530` hardcodes `include_retired=True` (as do `:484` and `:499` for other probes) while `check_engine.py:1760` passes a flag whose default is `False` (`:507`, `:557`), so one predicate reports two populations to two surfaces. DECIDE WHICH IS AUTHORITATIVE AND SAY WHY IN THE CODE, rather than silently aligning one to the other. NOTE this is a PRE-EXISTING defect that predates the reversal (spec `2lcqno` Section 6), so its fix must not be described as part of the reversal.
  READ THIS BEFORE CHOOSING, BECAUSE THE OBVIOUS CHOICE DELETES THIS PLAN'S ENTIRE SURVIVING DELIVERABLE. Measured at review with the production predicate: ALL 5 of the within-type descriptive findings that E-02 exists to preserve live under `executed/`, so they appear ONLY when retired records are included. If E-04 resolves the asymmetry by aligning BOTH surfaces to `include_retired=False` (the direction OQ-01 leans toward, and the direction that makes `aw check`'s current default authoritative), then `check.setid-collision` emits NOTHING, ever, on either surface, and the rule becomes dead code that E-02 and E-05 spend two items protecting. That outcome may still be the right call, but it MUST be made knowingly: if it is chosen, say plainly in the plan record that the rule is now latent-by-design (it fires only under `--all`, guarding future non-retired cases) rather than leaving E-02's "the 5 findings still report" outcome as an unmet claim.
  A THIRD ASYMMETRY THE AUTHORED ITEM MISSED, and it changes the numbers to reconcile: `doctor.py:517-521` DEMOTES any finding located under `executed/` into `res.executed_warnings` unless `include_executed` is set, so those same 5 findings are not in doctor's main drift either. MEASURED: the predicate returns 86 with retired included (81 cross-type + 5 descriptive), `aw doctor --agent` surfaces 81, and `aw check` surfaces 38. So the real gap is 38 versus 81 versus 86 across three populations, not the 38-versus-86 two-way gap the plan states, and reconciling `include_retired` alone will NOT make the two surfaces agree while the executed-demotion remains. Decide and state what the rule's population is on BOTH axes.
  - Depends on: E-01
  - Expected outcome: `aw check` and `aw doctor` report the SAME `check.setid-collision` population, with BOTH the `include_retired` choice and the executed-demotion interaction accounted for and justified in a code comment; and if the chosen population makes the rule emit nothing today, that is stated explicitly rather than left implied.
  - Execution state: performed

### Task group 3: the surfaces that encode today's behavior

- [x] E-05 FIX THE ONE TEST THAT ACTUALLY BREAKS, WHICH IS NOT THE ONE THIS PLAN PREDICTED, AND ADD THE THREE MISSING PINS. MEASURED at review by applying E-01 in an isolated worktree and running the suite bare: `1 failed, 5958 passed` against a `5959 passed` baseline, and the single failure is `tests/test_agentadhere_policy_engine.py::TestFixtureCorpus::test_adversarial_setid_collision` (`:190-204`), which builds a plan and a spec sharing setid `shared` and asserts `check.setid-collision` IS emitted. Its own comment calls cross-type reuse "adversarial", so the test encodes the pre-reversal belief and its INTENT is now wrong, not just its fixture: it must be REPOINTED to a within-type conflict (or renamed to assert cross-type SILENCE), never merely deleted, and the stale "(cross-type reuse) -> I-09 family" comment must be corrected in the same edit.
  THE TWO TESTS THIS PLAN NAMED BOTH PASS UNTOUCHED. `test_setid_collision` (`:106-114`, two PLANS with `Alpha`/`Beta`) is the surviving within-type case and stays green, as the plan predicted. But `test_all_runs_collisions_once` (`:116-121`) ALSO passes unedited: it asserts only `check.id6-collision` counts and its plan+spec fixture shares an id6, not a conflicting setid, so E-01 does not touch it. F-4's claim that it "must be retargeted" is WRONG and following it would produce a pointless edit; leave it alone and say so.
  ADD THREE PINS, none of which exist today: (a) a cross-type setid produces NO finding, so a future change cannot re-add the branch silently; (b) the E-02 three-file shared-slot fixture (a PLAN plus two SPECS with differing descriptives) reports the genuine spec-vs-spec conflict, which is the assertion that proves E-02's slot fix rather than just its guard; (c) a same-type conflict where the FIRST file seen is a foreign type, which is the exact case that silently regressed.
  - Depends on: E-01, E-02
  - Expected outcome: `test_adversarial_setid_collision` repointed with its comment corrected; `test_setid_collision` and `test_all_runs_collisions_once` both pass UNEDITED (state that you verified this rather than editing them); the three new pins present and passing; suite back to zero failures compared by node id.
  - Execution state: performed

- [x] E-06 VERIFY THE RULE-ID-DEPENDENT SURFACES, HAVING FIRST DROPPED TWO WRONG PREDICTIONS FROM THE AUTHORED ITEM. This item shrank at review from "update the goldens" to "confirm they need no update", because both of its premises were measured false. FIRST, THE GOLDENS DO NOT NEED REGENERATING: `check_findings.json.golden` and `check_findings.agent.golden` are rendered from a HARDCODED synthetic `CommandResult` in `tests/test_cli_quality_gates.py:68-82` (`Diagnostic("b.md", "check.setid-collision", "dup")`), not from a corpus scan, so no behavior change in `check_collisions` can alter them. Confirm that by reading the fixture source before touching either file, and if you find yourself regenerating a golden, stop: you have changed a renderer, which is outside this plan's scope. SECOND, `test_agentadhere_policy_engine.py` DOES NOT assert an invariant family for this rule: its only reference is the rule-id membership assertion at `:204` (which E-05 owns), and `grep` for `I-09`/`I-16` across `tests/` finds only two prose COMMENTS, no assertion on the value. So E-03's repoint breaks nothing, because the `RuleSpec.invariant` field is a free-text label with no validator and no consumer that checks it.
  WHAT REMAINS IS A GENUINE, NARROW VERIFICATION plus one surface the authored item missed entirely: `tests/test_doctor_remediations.py:132-144` (`test_setid_collision_remediation`) asserts the doctor remediation for this rule renders `aw group <type> <path> --set <new-set-id>`. That guidance is still correct for a within-type descriptive conflict but is now WRONG advice for the cross-type case the rule no longer reports, so read it and confirm the remediation text does not tell a reader to regroup for a reason that no longer exists.
  - Depends on: E-01, E-03
  - Expected outcome: both goldens confirmed UNCHANGED with the synthetic-fixture reason stated; `test_cli_quality_gates.py`, `test_agentadhere_policy_engine.py` and `test_doctor_remediations.py` all pass; the doctor remediation text checked for cross-type wording.
  - Execution state: performed

## Project conventions discovered (Step 0)

- SEVERITY AND INVARIANT ARE REGISTRY CONCERNS, NOT PER-EMITTER ONES. `check_engine.RULE_REGISTRY` maps a rule id to a `RuleSpec`, `enrich_drift` stamps it onto the `Drift`, and `artifact_core.drift_exit_code` fails the gate for anything that is not `info`. So changing how loudly a check speaks means editing the registry row, never a message string.
- THE RULE FIRES ONLY ON THE FULL SWEEP. `check_collisions` runs from `check_types`'s `collisions` branch, entered only when `types == ["all"]`, so this rule reaches `aw check all` and NOT `aw check plans`. State that rather than implying every check validates it.
- `seen_sets` IS KEYED ON THE SETID ALONE and stores `(record_type, descriptive, path)` for the FIRST file seen, and `SUPPORTED` iterates `plans` FIRST. Both emitting branches read that one slot, so a foreign-type predecessor can occupy it and hide a genuine within-type conflict. MEASURED at review (F-9), so E-02 must FIX the slot, not merely check it.
- THE GOLDEN FIXTURES ARE NOT DRIVEN BY THE CORPUS. `check_findings.json.golden` and `check_findings.agent.golden` render from a hardcoded synthetic `CommandResult` in `tests/test_cli_quality_gates.py:68-82`, so a change in what `check_collisions` emits cannot alter them. This is the opposite of what the authored plan assumed; if a golden ever needs regenerating for this change, a renderer was touched and that is out of scope.
- `RuleSpec.invariant` IS A FREE-TEXT LABEL WITH NO VALIDATOR AND NO VALUE-ASSERTING CONSUMER. `grep` for `I-09`/`I-16` across `tests/` finds only two prose comments. So E-03's repoint is safe by construction, and the authored worry that a test asserts an "invariant family" for this rule is unfounded.
- `aw check all` (POSITIONAL) AND `aw check --all` (FLAG) ARE DIFFERENT THINGS, and this plan's prose says "`--all`" where it means the retired-inclusive population. `all` is the TYPE scope (and is already the default), while `--all` is `include_retired`. Both are needed to see the within-type findings, and conflating them is how an executor could report "0 findings" as success while never having looked at the population the rule survives on.
- DOCTOR DEMOTES `executed/` FINDINGS to `executed_warnings` (`doctor.py:517-521`) unless `include_executed`, which is a SECOND population axis independent of `include_retired` (F-10).
- SUITE BARE: `python3 -m pytest`. `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals. Known environmental failure in the primary checkout only: `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, caused by a gitignored local `opencode-recovery/` dump; it passes in a clean worktree.

## Findings

| Id | Severity | Location (measured at HEAD) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `check_engine.py:897-905` | The cross-type branch emits 38 findings on the default scope, all for the endorsed normal state, at severity `error`. | `check_collisions` run; 38 findings, all `(different type: ...)`, across 28 distinct setids |
| F-2 | HIGH | `check_engine.py:906-915` | The within-type descriptive branch is GENUINE and must survive; 5 such cases exist and appear ONLY under `--all`. | default scope: 38 cross-type / 0 descriptive; `--all`: 86 total, 78+2+1 cross-type and 5 descriptive |
| F-3 | MEDIUM | `check_engine.py:95-97`; `pqsx96` catalog | The rule is registered under `I-09`, which is filename-grammar conformance; setid semantics is a different invariant, now catalogued as `I-16`. | `rule_spec("check.setid-collision").invariant == "I-09"`; `pqsx96` I-09 row reads "Filename-grammar conformance" |
| F-4 | MEDIUM | `tests/test_check_engine.py:106-121` | AUTHORED CLAIM, HALF WRONG, SUPERSEDED BY F-8. `test_setid_collision` is correctly identified as the surviving within-type case. But `test_all_runs_collisions_once` does NOT depend on the cross-type setid branch: it asserts only `check.id6-collision` counts and its fixture shares an id6, so it passes unedited and needs no retargeting. | both fixtures read; suite run with E-01 applied |
| F-5 | MEDIUM | `doctor.py:484,499,530` vs `check_engine.py:507,557,1760` | One predicate, two populations: doctor hardcodes `include_retired=True`, check defaults it `False`. Predates the reversal. THE STATED 38-versus-86 GAP IS INCOMPLETE: see F-10, there is a third population because doctor also demotes `executed/` findings. | source read; all three counts measured |
| F-6 | LOW | `tests/fixtures/conformance_goldens/*.golden`; `tests/test_cli_quality_gates.py`; `tests/test_agentadhere_policy_engine.py` | AUTHORED CLAIM, BOTH PREMISES FALSE, SUPERSEDED BY F-11/F-12. The goldens render from a hardcoded synthetic `CommandResult`, not a corpus scan, so they cannot change; and no test asserts this rule's invariant VALUE, so E-03's repoint breaks nothing. | fixture source at `test_cli_quality_gates.py:68-82`; `grep I-09\|I-16 tests/` finds only comments |
| F-7 | INFO | spec `2lcqno` OQ-01 | The `info`-severity alternative was considered and rejected FROM MEASUREMENT (38 findings across 28 setids, three times its own threshold), so an executor must not reintroduce it as a compromise. | the spec's resolved OQ-01 |
| F-8 | HIGH | `tests/test_agentadhere_policy_engine.py:190-204` | THE ONE TEST E-01 ACTUALLY BREAKS, and this plan did not name it. `test_adversarial_setid_collision` builds a plan and a spec sharing setid `shared` and asserts the rule IS emitted, calling cross-type reuse "adversarial" in its own comment. So it encodes the pre-reversal belief and its intent is now wrong. Suite with E-01 applied: `1 failed, 5958 passed` versus a `5959 passed` baseline, this being the only failure. | the pasted pytest failure (`AssertionError: 'check.setid-collision' not found in set()`) |
| F-9 | HIGH | `check_engine.py:893-915`; `SUPPORTED` iteration order | THE SHARED-SLOT HAZARD IS REAL AND E-01 MAKES IT SILENT. `seen_sets` is keyed on setid alone and `plans` iterates first, so a foreign-type first-seen file occupies the slot a within-type comparison needs. Measured with one PLAN `demo (PlanDesc)` plus two SPECS `demo (Alpha)`/`demo (Beta)`: HEAD emits 2 cross-type findings and never the genuine spec-vs-spec conflict; with the cross-type branch removed it emits ZERO. A same-type guard alone converts a noisy miss into a silent one, so the slot itself must be per-type. | the two scratch fixture runs (2 findings, then 0) |
| F-10 | HIGH | `doctor.py:517-521` | A THIRD POPULATION THE PLAN DOES NOT ACCOUNT FOR: doctor demotes any finding under `executed/` into `executed_warnings` unless `include_executed`. Measured: predicate 86 (81 cross + 5 descriptive), `aw doctor --agent` 81, `aw check` 38. So reconciling `include_retired` alone cannot make the surfaces agree, and E-04's outcome as authored is unreachable. | the three measured counts |
| F-11 | HIGH | this plan's E-02/E-04 read together | THE TWO ITEMS CONTRADICT EACH OTHER ON THE DELIVERABLE. All 5 surviving within-type findings are under `executed/`, so they exist ONLY with retired records included. If E-04 aligns both surfaces to `include_retired=False` (OQ-01's own lean), the rule emits nothing at all and E-02/E-05 protect dead code, while E-02's stated outcome ("the 5 findings still report") becomes false. The plan must choose knowingly and say which. | all 5 descriptive findings' locations under `executed/` |
| F-12 | LOW | `tests/test_doctor_remediations.py:132-144` | A FIFTH rule-id surface the plan missed: `test_setid_collision_remediation` asserts the doctor remediation renders `aw group <type> <path> --set <new-set-id>`, guidance that remains right for a within-type conflict but was written for the cross-type case too. | test source read |

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

- Over-scope: THE TWO GOLDEN FIXTURES ARE NOW DECLARED BUT EXPECTED TO BE UNCHANGED. They stay in `- Scope-Paths:` because E-06 must READ them and prove they need no edit (F-11 measured that they render from a synthetic fixture, not the corpus), and because a declared-but-unmodified path is reconciled by `aw ipd finalize` with a `--scope-ack`, which is the honest record of "checked, no change needed". Every other declared path is touched by a named E-item: `check_engine.py` (E-01/E-02/E-03), `doctor.py` (E-04), `tests/test_check_engine.py` (E-05's new pins), and `pqsx96` (E-03's note removal).
- Under-scope: `tests/test_agentadhere_policy_engine.py` and `tests/test_doctor_remediations.py` were UNDECLARED and are now in `- Scope-Paths:`: the former holds the one test E-01 actually breaks (F-8), the latter a fifth rule-id surface the plan missed (F-12). The review sweep also promoted E-02's slot hazard from an investigation to a required fix (F-9), added the third population axis to E-04 (F-10), and re-classified OQ-01 as blocking (F-11).
- AT EXECUTION, ONE FURTHER UNDECLARED PATH WAS TOUCHED AND IS DISCLOSED HERE RATHER THAN QUIETLY ADDED: `tests/fixtures/conformance_goldens/check_findings.human.golden`, added to `- Scope-Paths:` at execution time (DECISION `01-216rgg-D2`). The plan declared the `json` and `agent` goldens on the review's measurement that they render from a hardcoded synthetic `CommandResult` and therefore cannot move, which held exactly: both are byte-unchanged. But the HUMAN golden renders `doctor.build_remediation`'s title and `detailed_fix` too, so E-06's required correction of the remediation's cross-type wording necessarily moved 2 lines of it. NO RENDERER WAS TOUCHED, which is the actual tripwire E-06 names; the derived diff is exclusively the new guidance text, regenerated with the documented `AW_CONFORMANCE_UPDATE_GOLDENS=1`. The underlying coupling (guidance prose byte-pinned by a test named for renderer determinism) is filed as backlog `5e7uh9`.
- ALSO ADDED AT EXECUTION, as records the run itself produced rather than scope creep: two `.aw/records/backlog/open/` items (`muwwa5`, `5e7uh9`) filed under the defect-report contract, and this plan file.

## Required tests / validation

`python3 -m pytest` bare, in an isolated worktree, baseline measured there and pasted, compared by failing NODE ID rather than by total. THE BASELINE AND THE E-01 DELTA ARE ALREADY MEASURED at `a58d8f1b` and must be reproduced rather than re-derived: unpatched, `5959 passed, 3 skipped, 2 xfailed`; with the cross-type emission removed, `1 failed, 5958 passed`, the single failure being `tests/test_agentadhere_policy_engine.py::TestFixtureCorpus::test_adversarial_setid_collision`. A completed execution shows that node id green with no new failures. Note the plan's authored claim of an environmental `tests/test_reporting_contract.py` failure did NOT reproduce in a clean worktree.

Beyond the suite: the finding COUNTS before and after on ALL THREE measured populations (`aw check` = 38, `aw doctor` = 81, the predicate with retired included = 86), naming the exact invocation each time and distinguishing `aw check all` (type scope) from `aw check --all` (retired inclusion); the shared-slot fixture in its three states (HEAD, guard-only, fixed); and `git status --porcelain` proving no artifact was renamed or edited and neither golden was modified.

## Spec / documentation sync

`.aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md` is DECLARED IN SCOPE and edited by E-03, which removes the "the code still says I-09, to be repointed by the commit that re-scopes the rule" note once that becomes false. That is the only spec edit, and it deletes a statement rather than changing a requirement.

Spec `2lcqno` is the governing spec and is NOT edited: this plan implements its N1/N5 and its acceptance criteria 1, 2 and 3. Its `- Status:` is `to-review` at authoring time, which is why this plan is `to-review` and not `approved`: the spec should clear review before this executes.

## Open questions

### OQ-01: Which population should both surfaces scan, retired records included or excluded, given that excluding them makes the rule emit nothing at all?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`): LEAVE THE RULE'S DEFAULT SCOPE UNCHANGED (active work only), AND FIX THE FIVE OFFENDING NAMES INSTEAD. The maintainer dissolved the question rather than answering it as posed, by asking "Why not use the rename function to rename the files with new setid names like relrev01, relrev02, etc.?" That is better than either option the finding offered: once the names are correct the rule reports zero because NOTHING IS WRONG, not because it is looking away, so the include-versus-exclude trade disappears.
  THE SUGGESTION WAS VERIFIED BEFORE BEING ACCEPTED, in preview at HEAD `50c60393`: `aw group plans ez65jl --set relrev01 --rename` cleanly yields `20260711-release-review-00-ez65jl-...` -> `20260711-relrev01-00-ez65jl-...`, touching one file. Citation cost is small: each of the five id6s appears in only 2 to 4 TRACKED files (`git grep -l`), and the alarming first counts (159 to 179 files) were dominated by gitignored run logs and a lane worktree, not real citations.
  THE FIVE ARE, measured with `--all` (they are ABSENT from the default `aw check all`, which the maintainer correctly pointed out): `ez65jl`, `6cdker` and `s3axqd` all under setid `release-review` with different descriptives; `kq6akq` under `leak-sanitizer`; `g2payb` under `assess-documentation`; `hq4p3a` under `assess-bugs`. Note that is six plan files across four setids, not five findings-worth of distinct setids; the finding's "5" is the diagnostic count.
  THE TRAP THAT MUST BE PROVEN BEFORE APPLYING, and it is the reason this is not a trivial sweep: THESE SETIDS ARE ALSO LIVE WORKFLOW NAMES. `.aw/system/workflows/release-review/` exists and the token appears in 201 tracked files; `leak-sanitizer` appears in 58; `assess` is also a workflow. The rename must change ONLY the plan filenames and their handful of citations, and must never touch the workflow directory, its files, or prose referring to that workflow. The preview touching exactly one file per plan is evidence it behaves, but it is not proof, and `--no-refs` versus the default reference rewriting must be chosen deliberately.
  CONSEQUENCE FOR THIS PLAN: E-02 and E-05 keep the within-type emission as authored and the default scope is UNCHANGED, so no scope-widening work is needed and the second axis (the `aw doctor` executed-demotion) is NOT settled here and NOT required by this plan; it remains the separate defect filed as backlog `lmjc8h`. The plan should record that the rule's silence after the rename is CORRECT rather than dormant-by-design, which is a materially different statement from the one the finding's option (c) contemplated.
  THE RENAME ITSELF IS NOT THIS PLAN'S WORK and is carried by backlog `k16uuq`, filed 2026-09-10, per the rule that no defect may be raised without a carrier. STATUS AT RECORDING: the maintainer RAN all six `--apply` commands on 2026-09-10 and the on-disk renames plus the index rewrite SUCCEEDED (`release-review` -> `relrev01`/`relrev02`/`relrev03`, `leak-sanitizer` -> `leaksan01`, `assess-documentation` -> `assessdoc01`, `assess-bugs` -> `assessbug01`). The verb's OWN self-commit was REFUSED on all six by the executed-transition hook, which is a separate defect in `aw group`'s staging shape (it leaves the old path staged as a deletion and the new path untracked, so the gate cannot see a rename); filed as backlog `mqmlug` and the gate itself is CORRECT, returning exit 0 once both sides are staged and git reports `R099`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the `check.setid-collision` finding count on the DEFAULT scope before (expect 38) and after (expect 0), and paste `git status --porcelain` proving NO artifact was renamed or edited to achieve it. Also paste the corrected docstring showing the cross-type clause is gone and D153 / `2lcqno` N1 are cited. Confirm no commented-out branch and no flag-guarded remnant remains (`grep` for `different type`).
  - Observed evidence: MEASURED IN THIS LANE WORKTREE at starting HEAD `b616b123`. THE COUNTS MOVED SINCE AUTHORING AND THE PLAN SAID TO RE-DERIVE THEM (spec `2lcqno` Section 5), so the "expect 38" in the required-evidence line is a dated snapshot, not the bar; the SHAPE held exactly (cross-type dominates; within-type is empty).
    BEFORE, default type scope `all` with `include_retired=False`, via `check_engine.check_collisions`:
    ```
    include_retired=False: setid-collision total=29 cross=29 descriptive=0
    include_retired=True: setid-collision total=89 cross=89 descriptive=0
    ```
    AFTER, same two invocations:
    ```
    AFTER include_retired=False: setid-collision = 0
    AFTER include_retired=True: setid-collision = 0
    ```
    And through the CLI surface, `python3 -m agent_workflows check all --agent`, counting `check.setid-collision` diagnostics: BEFORE `29`, AFTER `0` (total diagnostics 421, so the sweep still reports everything else).
    NO ARTIFACT WAS RENAMED OR EDITED TO ACHIEVE IT. `git status --porcelain` at completion lists six modified files and NOT ONE renamed or moved record; the only `.aw/records/` path is the spec E-03 was licensed to edit plus this plan:
    ```
     M .aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md
     M agent_workflows/check_engine.py
     M agent_workflows/doctor.py
     M tests/fixtures/conformance_goldens/check_findings.human.golden
     M tests/test_agentadhere_policy_engine.py
     M tests/test_check_engine.py
    ```
    THE CORRECTED DOCSTRING, with the cross-type clause gone and D153 / `2lcqno` N1 cited positively:
    ```
    * setid: the same setid used WITHIN ONE type with two different non-None descriptives
      (``check.setid-collision``). A setid appearing under two DIFFERENT types is CORRECT and is
      NOT reported: DECISIONS D153 / spec ``2lcqno`` N1 rule that a setid is a SHARED cross-type
      TOPIC label, not an identity (identity is the id6, see ``check.id6-collision`` below), so
      research + specs + backlog + plans on one topic are MEANT to share the token. Do NOT re-add
      a cross-type branch as a "missing" check, and do not add an ``info`` variant of it either:
      spec ``2lcqno`` OQ-01 rejected that from measurement ...
    ```
    NO REMNANT. `grep -n "different type" agent_workflows/*.py` returns NOTHING: no live branch, no commented-out branch, no flag-guarded or env-guarded variant, and no `info` downgrade.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the retired-inclusive count showing the 5 within-type descriptive findings STILL report (or, if OQ-01 resolved to EXCLUDE, paste the zero count and the plan's explicit latent-by-design statement instead; do not report zero as if it satisfied the original outcome). Name the exact invocation and distinguish `aw check all` (type scope) from `aw check --all` (retired inclusion), since only the latter reaches this population. Paste the SHARED-SLOT fixture (one PLAN plus two SPECS with differing descriptives) reporting the genuine spec-vs-spec conflict, and paste the same fixture's HEAD behavior (2 cross-type findings, conflict missed) and same-type-guard-only behavior (0 findings) for contrast, since that contrast is what proves the slot itself was fixed rather than only guarded. Plus a MUTATION CHECK: break the descriptive comparison, show the E-05 pin FAILS, restore, show it passes.
  - Observed evidence: OQ-01 RESOLVED TO **LEAVE THE DEFAULT SCOPE UNCHANGED AND FIX THE NAMES INSTEAD**, so the branch's real-tree population is EMPTY and THE RULE IS LATENT BY DESIGN. I am stating that in those words rather than reporting zero as if it satisfied the authored "the 5 findings still report" outcome. The 5 cases were renamed away in `4f1ca199` (backlog `k16uuq`), which is WHY zero is correct here: nothing is wrong, the rule is not looking away. Spec `2lcqno` N5 and Section 1 finding 4 were both updated at spec review to say exactly this, and criterion 2 requires a FIXTURE instead of a live count.
    THE INVOCATIONS, distinguishing the two things the plan warns are conflated: `aw check all` is the TYPE scope (`all`, already the default) and `--all`/`include_retired=True` is RETIRED INCLUSION. Both were measured; both report 0 AFTER (29 and 89 BEFORE).
    THE SHARED-SLOT FIXTURE IN ITS THREE STATES, one PLAN `demo (PlanDesc)` plus two SPECS `demo (Alpha)` / `demo (Beta)`:
    1. HEAD (setid-keyed slot, cross-type branch live) - 2 cross-type findings, genuine conflict MISSED:
    ```
    HEAD behavior: count = 2
       20260101-demo-01-bbb222-s1.spec.md | different type: plans vs specs)
       20260101-demo-02-ccc333-s2.spec.md | different type: plans vs specs)
    ```
    2. SAME-TYPE GUARD ONLY (setid-keyed slot kept, guard added) - ZERO findings, i.e. the noisy miss turned SILENT. Reproduced by mutation, and the E-05 pin CATCHES it:
    ```
    MUTATION APPLIED: setid-only slot + same-type guard (the 'guard alone' variant)
    E       AssertionError: 0 != 1 : []
    FAILED tests/test_check_engine.py::CollisionTests::test_within_type_conflict_survives_a_foreign_type_predecessor
    ========================= 1 failed, 7 passed in 0.90s ==========================
    ```
    3. FIXED (slot keyed per `(type, setid)`) - the genuine spec-vs-spec conflict IS reported, and nothing is said about the plan:
    ```
    SHARED-SLOT fixture after fix: count = 1
       20260101-demo-02-ccc333-s2.spec.md | setid demo conflicts with .../20260101-demo-01-bbb222-s1.spec.md (descriptive: 'Alpha' vs 'Beta')
    ```
    That 2 -> 0 -> 1 contrast is what proves the SLOT was fixed and not merely guarded.
    MUTATION CHECK ON THE DESCRIPTIVE COMPARISON, as required. Broke it (`if False and desc is not None ...`), four pins FAILED:
    ```
    MUTATION APPLIED: descriptive comparison disabled
    FAILED tests/test_check_engine.py::CollisionTests::test_within_type_conflict_reports_under_one_type_only
    FAILED tests/test_check_engine.py::CollisionTests::test_setid_collision
    FAILED tests/test_check_engine.py::CollisionTests::test_within_type_conflict_survives_a_foreign_type_predecessor
    FAILED tests/test_agentadhere_policy_engine.py::TestFixtureCorpus::test_adversarial_setid_collision
    ========================= 4 failed, 5 passed in 1.26s ==========================
    ```
    Restored, and they pass:
    ```
    MUTATION REVERTED
    tests/test_check_engine.py ........                                      [ 88%]
    tests/test_agentadhere_policy_engine.py .                                [100%]
    ============================== 9 passed in 1.10s ===============================
    ```
    The message and recovery guidance of the surviving branch are unchanged (same `(descriptive: X vs Y)` detail string); only the doctor REMEDIATION PROSE around it changed, under E-06.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `rule_spec("check.setid-collision")` showing `invariant='I-16'`, AND `rule_spec` for both id6 rules showing they still read `I-09` (proving the repoint was surgical). Paste the `pqsx96` Section 4 diff showing the disagreement note removed.
  - Observed evidence: THE REPOINT IS SURGICAL. `rule_spec` for all three rules in one read:
    ```
    rule_spec: RuleSpec(severity='error', assurance='repository', determinism='deterministic', invariant='I-16')
    id6-collision: RuleSpec(severity='error', assurance='repository', determinism='deterministic', invariant='I-09')
    id6-identity-slot: RuleSpec(severity='error', assurance='repository', determinism='deterministic', invariant='I-09')
    ```
    Severity, assurance and determinism are UNCHANGED (`error` / `repository` / `deterministic`); only `invariant` moved, and only on the setid rule. A new regression test pins all three values, which nothing did before (the plan measured that `RuleSpec.invariant` had no value-asserting consumer): `tests/test_check_engine.py::CollisionTests::test_setid_rule_traces_to_the_setid_semantics_invariant`.
    THE `pqsx96` SECTION 4 DIFF, showing the disagreement note REMOVED:
    ```
    -  CONSEQUENCE FOR THE IMPLEMENTER: when `check.setid-collision` is re-scoped to its within-type half,
    -  update its `RuleSpec` invariant from `"I-09"` to `"I-16"` in the same change, so the code and this
    -  catalog agree. Until then they disagree, and this bullet is the record of why.
    +  WHAT THE RE-SCOPE ACTUALLY DID, recorded because I-16's "deterministically detectable in BOTH
    +  directions" column is now the whole rule rather than half of it: the cross-type emission was
    +  DELETED (not relabelled, not flag-guarded; spec `2lcqno` OQ-01 rejected an `info` variant from
    +  measurement), and the surviving within-type comparison was re-keyed per `(type, setid)`, without
    +  which removing the cross-type branch would have turned a noisy miss into a SILENT one.
    ```
    The "recorded rather than silently repointed because the code still carries the old value" opener was also corrected to "CORRECTED 2026-09-10 AND CLOSED IN THE CODE 2026-09-18", since that framing was equally false once the code moved. No requirement changed: both edits delete or update a statement ABOUT the code, and the I-16 catalog row itself is untouched.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste this rule's finding count from `aw check` AND from `aw doctor` showing they now MATCH, with the three measured before-values stated for contrast (`aw check` 38, `aw doctor` 81, predicate 86). Account for BOTH axes: state what you decided about `include_retired` AND about the `executed/` demotion at `doctor.py:517-521`, since reconciling only the first cannot make the surfaces agree. Paste the code comment justifying the chosen population and naming both arguments. Confirm no OTHER doctor probe's output changed, by pasting the doctor finding totals per rule before and after. If the chosen population makes this rule emit zero on both surfaces, say so in those words.
  - Observed evidence: THE TWO SURFACES NOW AGREE ON THIS RULE, AND THE ANSWER IS ZERO ON BOTH. Stating it in those words as the item demands: after the re-scope, `check.setid-collision` emits ZERO on `aw check`, ZERO on `aw doctor`, and ZERO from the raw predicate on both populations.
    ```
    === aw check all (type scope 'all', include_retired default False) ===
      setid-collision = 0  (total diagnostics 421 )
    === aw doctor --agent ===
      setid-collision = 0  (total diagnostics 475 )
    ```
    THE BEFORE-VALUES RE-DERIVED IN THIS WORKTREE, since the plan's three (38 / 81 / 86) are dated snapshots: `aw check` **29**, `aw doctor --agent` **89**, raw predicate with retired included **89**. Note the plan's third axis did NOT bite here: of the 89, ZERO are under `executed/`, so doctor's demotion had nothing to demote and its surfaced count equalled the predicate's rather than the 81-vs-86 split the plan measured in September.
    WHAT I DECIDED ON EACH AXIS. `include_retired`: the asymmetry is KEPT and made DELIBERATE rather than aligned, which is the resolution backlog `lmjc8h`'s own scope sentence offers ("make the parameter explicit at both call sites so the divergence cannot be accidental"). `aw doctor` stays `include_retired=True`, `aw check` stays flag-defaulting-False. `executed/` DEMOTION at `doctor.py`: LEFT AS IS, deliberately and with the reason recorded, because OQ-01's resolution removed the need to touch it (the maintainer chose to fix the six names rather than widen the rule, and the plan's own OQ-01 text says the second axis "is NOT settled here and NOT required by this plan; it remains the separate defect filed as backlog `lmjc8h`").
    WHY NOT ALIGN THEM, since the item demands a justification and not a preference: flipping either default would move `check.id6-collision` and `check.id6-identity-slot` too (measured: the predicate returns 2 and 3 with retired included versus 1 and 0 without), i.e. it would change two rules this plan is forbidden to touch. Spec `2lcqno` Section 6 calls that choice a product decision about whether retired records are in scope for ANY rule and declares it a non-goal, requiring only that the surfaces AGREE and that the choice be STATED. Both now hold for this rule.
    THE CODE COMMENT, naming both axes and both arguments, at `doctor.probe_artifacts`:
    ```
    # `include_retired=True` IS DELIBERATE AND ASYMMETRIC WITH `aw check`, which passes a flag
    # defaulting to False (`check_engine.check_types`). Stating the asymmetry rather than
    # silently aligning it is the fix setidfix 216rgg E-04 chose, on three grounds. (1) The two
    # surfaces answer DIFFERENT questions by design ... (2) Widening or narrowing either default is
    # a product decision ... (3) For `check.setid-collision` specifically the two surfaces now DO
    # agree: ... both report ZERO on the real tree ... That branch is therefore LATENT BY DESIGN,
    # pinned by a fixture ... The residual raw-population divergence (which still affects the two
    # id6 rules) is carried as backlog `lmjc8h` ...
    ```
    NO OTHER DOCTOR PROBE CHANGED, proven per rule rather than by a total. BEFORE (a pristine `git archive HEAD` export with the same records tree) versus AFTER:
    ```
    BEFORE                                  AFTER
        35  adopted-without-consumer            35  adopted-without-consumer
         2  check.id6-collision                  2  check.id6-collision
         3  check.id6-identity-slot              3  check.id6-identity-slot
       101  check.ipd-uncarried-obligation     101  check.ipd-uncarried-obligation
         5  check.lifecycle-transition-invalid   5  check.lifecycle-transition-invalid
         3  check.name-nonconformant             3  check.name-nonconformant
        89  check.setid-collision               (absent: 0)
         4  check.stale-index-missing            4  check.stale-index-missing
         1  check.system-layout-missing          1  check.system-layout-missing
         8  stale-state-to-promote               8  stale-state-to-promote
    ```
    Every rule is identical except `check.setid-collision` (89 -> 0). The two rows that differ for an unrelated reason are `doctor.git-untracked` / `doctor.git-dirty`, which report the export's own untracked state versus this worktree's, not a behavior change.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `test_adversarial_setid_collision` FAILING before your edit (the measured `AssertionError: 'check.setid-collision' not found in set()`) and passing after, plus the corrected comment showing the stale "(cross-type reuse) -> I-09 family" wording is gone. Paste `test_setid_collision` AND `test_all_runs_collisions_once` passing UNEDITED, and show both are absent from your diff, since the authored plan wrongly predicted the second needed retargeting. Paste the three new pins (cross-type silence; the shared-slot three-file fixture; a same-type conflict whose first-seen file is a foreign type). Paste the bare suite before and after, compared by NODE ID.
  - Observed evidence: THE PREDICTED FAILURE REPRODUCED EXACTLY, with the review's exact assertion text, before my edit:
    ```
        rules = {d.rule for d in ce.check_collisions(self.root)}
    >       self.assertIn("check.setid-collision", rules)
    E       AssertionError: 'check.setid-collision' not found in set()
    tests/test_agentadhere_policy_engine.py:204: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_agentadhere_policy_engine.py::TestFixtureCorpus::test_adversarial_setid_collision
    ============================== 1 failed in 0.41s ===============================
    ```
    REPOINTED, NOT DELETED: the fixture is now two SPECS sharing setid `shared` with conflicting descriptives (`Alpha` / `Beta`), so it still asserts the rule FIRES, on the half that is genuinely adversarial. The stale comment is gone; the replacement says why:
    ```
    # Two SPECS sharing one setid with CONFLICTING descriptives -> I-16 (setid semantics).
    # REPOINTED by setidfix 216rgg E-05 from a cross-type fixture ... which this test used to call
    # "adversarial". Under D153 / spec `2lcqno` N1 that is the endorsed NORMAL state ... so the old
    # fixture's INTENT was wrong, not merely its data ...
    ```
    `grep` confirms the old "(cross-type reuse) -> I-09 family" wording no longer exists anywhere in `tests/`.
    THE TWO PRE-EXISTING TESTS PASS UNEDITED, AND F-4 WAS WRONG ABOUT THE SECOND, WHICH I VERIFIED RATHER THAN EDITING. `git diff tests/test_check_engine.py` shows ONLY added `def test_` lines and no removed ones, so neither `test_setid_collision` nor `test_all_runs_collisions_once` appears in my diff at all:
    ```
    +    def test_cross_type_setid_is_not_a_finding(self) -> None:
    +    def test_within_type_conflict_survives_a_foreign_type_predecessor(self) -> None:
    +    def test_within_type_conflict_reports_under_one_type_only(self) -> None:
    +    def test_setid_rule_traces_to_the_setid_semantics_invariant(self) -> None:
    ```
    All seven relevant node ids green, the three new pins among them:
    ```
    tests/test_agentadhere_policy_engine.py::TestFixtureCorpus::test_adversarial_setid_collision PASSED
    tests/test_check_engine.py::CollisionTests::test_setid_rule_traces_to_the_setid_semantics_invariant PASSED
    tests/test_check_engine.py::CollisionTests::test_all_runs_collisions_once PASSED
    tests/test_check_engine.py::CollisionTests::test_cross_type_setid_is_not_a_finding PASSED
    tests/test_check_engine.py::CollisionTests::test_within_type_conflict_reports_under_one_type_only PASSED
    tests/test_check_engine.py::CollisionTests::test_setid_collision PASSED
    tests/test_check_engine.py::CollisionTests::test_within_type_conflict_survives_a_foreign_type_predecessor PASSED
    ============================== 7 passed in 0.45s ===============================
    ```
    A FOURTH PIN WAS ADDED beyond the three required (`test_within_type_conflict_reports_under_one_type_only`), because the three as specified never asserted that a setid reused within one type with a CONSISTENT descriptive stays silent, which is the false-positive direction.
    THE BARE SUITE, BEFORE AND AFTER IN THIS WORKTREE, compared by failing NODE ID (there are none on either side, so the comparison is trivially clean):
    ```
    BEFORE: 8114 passed, 3 skipped, 2 xfailed in 218.44s (0:03:38)
    AFTER:  8118 passed, 3 skipped, 2 xfailed in 226.25s (0:03:46)
    ```
    +4 is exactly the four new pins. NOTE the plan's authored baseline (`5959 passed`) is a September snapshot; the suite has grown. The plan's predicted environmental `test_reporting_contract.py` failure did not occur.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the fixture source at `tests/test_cli_quality_gates.py:68-82` showing the goldens come from a hardcoded synthetic `CommandResult`, and confirm BOTH golden files are byte-unchanged (`git status --porcelain` showing neither is modified). If either golden changed, explain what renderer you touched, because that is out of scope. Paste `test_cli_quality_gates.py`, `test_agentadhere_policy_engine.py` and `test_doctor_remediations.py` passing. State the result of reading the doctor remediation text for cross-type wording.
  - Observed evidence: THE TWO DECLARED GOLDENS ARE BYTE-UNCHANGED, EXACTLY AS THE REVIEW PREDICTED. The fixture source proves why they cannot move, at `tests/test_cli_quality_gates.py`:
    ```
    "check_findings": CommandResult(
        command="check", status="findings", exit_code=1,
        summary="2 findings across 41 checked",
        diagnostics=[
            Diagnostic("a.md", "check.name-nonconformant", "bad name"),
            Diagnostic("b.md", "check.setid-collision", "dup"),
        ],
        ...
    ```
    It is a HARDCODED synthetic `CommandResult`, not a corpus scan, so no change in `check_collisions` can reach it. `git status --porcelain tests/fixtures/conformance_goldens/` lists NEITHER `check_findings.json.golden` NOR `check_findings.agent.golden`: both are unmodified, and they are declared-but-unchanged paths for `aw ipd finalize --scope-ack`.
    ONE GOLDEN DID CHANGE, AND IT IS A THIRD FILE THE PLAN DID NOT NAME. `check_findings.human.golden` renders the doctor REMEDIATION PROSE (title + `detailed_fix`), which E-06 required me to read and correct, so editing that prose necessarily moved this golden. I did NOT touch a renderer, which is the out-of-scope tripwire the item names: the diff is only my own wording, regenerated deliberately with the documented switch `AW_CONFORMANCE_UPDATE_GOLDENS=1`:
    ```
    -  Issue: Set ID collision across artifact records
    +  Issue: One Set ID used with two different descriptives in one record type
    -    Fix: run 'aw group plans b.md --set <new-set-id>' to assign a unique Set ID.
    +    Fix: another record of the SAME type uses this Set ID with a different descriptive; run 'aw group plans b.md --set <new-set-id>' to regroup this record, or align the two descriptives. Sharing a Set ID with a different record type is correct and is not reported.
    ```
    THE RESULT OF READING THE REMEDIATION TEXT FOR CROSS-TYPE WORDING: IT WAS WRONG AND IS FIXED. The title read "Set ID collision ACROSS artifact records" and the fix read "assign a UNIQUE Set ID" - cross-type framing, and cross-type UNIQUENESS is the very invariant D153 reversed, so it told a reader to regroup for a reason the rule can no longer report. The `aw group ... --set <new-set-id>` COMMAND is unchanged and still correct for a within-type descriptive conflict, which is what `test_setid_collision_remediation` asserts, so that test passes unedited.
    All four affected test files pass:
    ```
    tests/test_check_engine.py ........................................ [ 87%]
    tests/test_agentadhere_policy_engine.py ....................
    tests/test_doctor_remediations.py ......................
    tests/test_cli_quality_gates.py ..............
    ============================== 82 passed in 2.46s ==============================
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Size note: 6 E-leaves in 3 groups, unchanged in COUNT by the review but materially changed in CONTENT: E-02 gained a required slot fix (was an investigation), E-04 gained a third population axis, E-05 was retargeted onto the test that actually breaks, and E-06 SHRANK to a verification once both of its premises measured false.
- Cohesion rationale: E-01/E-02/E-03 are one rule's emission plus its registry row and must land together, because removing the cross-type branch without repointing the invariant leaves the catalog and code in a disagreement this plan is partly meant to close. E-04 is a separate pre-existing defect included ONLY because acceptance criterion 3 cannot be evaluated while the surfaces count different populations; note that after review it is also the item that DECIDES whether E-02 and E-05 have any live effect, which is why OQ-01 gates the plan. E-05/E-06 are the test surfaces the first three touch.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since a rejected hook can leave paths in the index. When reporting tests passed, paste the ACTUAL runner output. This is a SHARED CHECKOUT: other agents are editing this tree concurrently, so never revert or commit a file you did not change.

Post-gate lifecycle: BLOCKED ON OQ-01 BEFORE APPROVAL IS EVEN MEANINGFUL. `aw ipd lint` refuses this plan at every checkpoint while OQ-01 is `Blocking: yes` and `open`, which is the intended fail-closed stop: the population decision determines whether E-02 and E-05 protect live behavior or dead code, so approving and executing before it is answered would produce work whose value is unknown. Answer OQ-01, record it in this plan, then take explicit human approval (`aw ipd set approved 216rgg --by-human --message ...`). Its governing spec `2lcqno` is also `to-review`; prefer letting the spec clear review first, since a review could still change N5. On completion, transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

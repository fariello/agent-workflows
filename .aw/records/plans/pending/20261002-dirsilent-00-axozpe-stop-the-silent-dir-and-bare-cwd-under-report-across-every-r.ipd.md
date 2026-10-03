# IPD: Stop the silent --dir and bare-cwd under-report across every resolver caller

- Date: 2026-10-02
- Kind: orchestrator
- Concern: Backlog `rgl2d4` reports that the ~35 `resolve_verb_repo_root` callers outside `aw attention` and `aw ipd board` fall back SILENTLY for a non-surveyable `--dir`, so `aw specs check` and `aw backlog check` announce conformance having examined ZERO artifacts at a project subdirectory. Measured at this lane's HEAD the item reproduces exactly, and the machine surface is worse than filed: both validators emit `"outcome":"clean","exit":0,"verified":true,"complete":true,"checked":0`, which is the Anti-Greenwashing Invariant violation `docs/cli-output-contract.md` names outright and is the field a CI step is told to trust. Measurement also found a defect class the item does not describe: SIX sites bypass the resolver entirely with their own `Path(getattr(args,"dir",None) or os.getcwd())`, so `aw check`, `aw find`, `aw search`, `aw record-history`, `aw graduation` and `aw doctor` under-report with NO FLAG AT ALL - a plain `cd src && aw check` reports `0 specs checked` where the same command at the root reports `1`, and `aw doctor` calls an installed project `not installed`. This Set sequences the remedy.
- Scope: ORCHESTRATION ONLY. This plan sequences four children and contributes no implementation, no test and no deliverable of its own. Every artifact is owned by exactly one child and named in the child table below. IN: the dependency order, the Set-level completion criteria, and the cross-child consistency checks. OUT: everything the children do, which is the shared refusal primitive (Order 01), the two fail-closed validators (Order 02), the six resolver-bypass sites (Order 03), and the shared read/write helper split plus the remaining read-class callers and the duplication retirement (Order 04). This plan also does NOT reopen the no-climb decision `lmyeas` OQ-01 settled, and does NOT add a refusal to any write-class verb.
- Scope-Paths: .aw/records/plans/pending/20261002-dirsilent-01-i6mby8-add-the-shared-non-surveyable-root-refusal-primitive-every-r.ipd.md, .aw/records/plans/pending/20261002-dirsilent-02-jei45f-convert-the-two-fail-closed-validators-specs-check-and-backl.ipd.md, .aw/records/plans/pending/20261002-dirsilent-03-sjsb04-route-the-six-resolver-bypass-sites-through-resolve-verb-rep.ipd.md, .aw/records/plans/pending/20261002-dirsilent-04-rlhmt9-split-the-shared-read-write-helpers-and-convert-the-remainin.ipd.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: rgl2d4
- Blocks-Release: next
- Set: dirsilent
- Order: 0
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: axozpe

## Workflow history

- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `rgl2d4`. GATE NOTE: item `rgl2d4` carries `- Blocks-Release: next`, which this plan and all four children INHERIT as required.
  THIS PLAN CARRIES ORCHESTRATION AND NOTHING ELSE. Its four `E-*` items are confirmations that each child reached `executed`; no item produces a deliverable, establishes a baseline, or reconciles records, because an orchestrator's own items are performed by nobody when a runner retires it. If a reviewer finds work here that no child covers, the correct remedy is a NEW CHILD, not an item on this plan.
  THE SET DEPARTS FROM THE ITEM'S FRAMING IN TWO MEASURED WAYS, both recorded so approval is informed. FIRST, the item says the remaining work "is adopting that classifier at the remaining callers", implying the predicate was the only missing piece; measured, the REFUSAL (message, path-free machine record, exit codes) is hand-rolled twice already and is the half that gets copied, which is why Order 01 adds a shared emitter before anything is converted. SECOND, the item names `doctor.run`'s resolver bypass as a single low-cost sub-case; measured, SIX sites share that bypass and three of them are `aw check`, `aw find` and `aw search`, which makes it a live false-clean-answer reachable with no flag rather than a latent inconsistency, and earns it its own Order.
  AND ONE ITEM CLAIM IS CORRECTED DOWNWARD BY MEASUREMENT: the item names six shared helpers needing a read/write split; reading each helper's callers, only THREE are genuinely mixed. Order 04 records that and re-derives it at execution rather than trusting this authoring.

## Goal

Make every read-class repo-scoped verb tell the truth about a directory it cannot survey, and make a bare invocation from a project subdirectory climb like its siblings. At the end of this Set no verb reports `conforms`, `clean` or `0 findings` for a tree it never examined, the refusal has exactly one definition in the package, and write-class verbs are exactly as safe as they are today.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: sequence the Set

- [ ] E-01 CONFIRM `i6mby8` (Order 01, the shared refusal primitive) REACHED `executed`, and that it shipped the primitive ADDITIVELY with no verb converted and the two existing hand-rolled call sites untouched. This is the dependency every later child declares, so a partial landing here silently weakens three plans.
  - Depends on: none
  - Expected outcome: `i6mby8` is in `.aw/records/plans/executed/` with `- Status: executed`, and the primitive exists in `project_context` with its regression test passing.
  - Execution state: pending

- [ ] E-02 CONFIRM `jei45f` (Order 02, the two fail-closed validators) REACHED `executed`, and that `aw specs check --dir <subdir>` and `aw backlog check --dir <subdir>` now refuse at exit 2 rather than announcing conformance over zero artifacts. This is the item's own named starting point and the highest-severity surface in the Set.
  - Depends on: E-01
  - Expected outcome: `jei45f` is in `.aw/records/plans/executed/` with `- Status: executed`, and both validators refuse a non-surveyable root on both surfaces while the single-file form and the empty-but-real project still behave as before.
  - Execution state: pending

- [ ] E-03 CONFIRM `sjsb04` (Order 03, the six resolver-bypass sites) REACHED `executed`, and that a BARE invocation from a project subdirectory now climbs for all six verbs, including `aw doctor` no longer reporting an installed project as `not installed`.
  - Depends on: E-02
  - Expected outcome: `sjsb04` is in `.aw/records/plans/executed/` with `- Status: executed`, and the bare-cwd climb matrix shows the subdirectory and root columns agreeing for `check`, `find`, `search`, `record-history`, `graduation` and `doctor`.
  - Execution state: pending

- [ ] E-04 CONFIRM `rlhmt9` (Order 04, the helper split, the remaining read-class callers and the duplication retirement) REACHED `executed`, and that no write-class verb gained a refusal. That negative is the Set's policy boundary and is the one outcome a careless execution could invert.
  - Depends on: E-03
  - Expected outcome: `rlhmt9` is in `.aw/records/plans/executed/` with `- Status: executed`; the mixed helpers are split, the read-class verbs refuse, `attention.run` and `cli._run_plans` call the shared primitive with byte-identical output, and every write-class verb behaves exactly as before.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Plan | Purpose | Depends on |
| --- | --- | --- | --- | --- |
| 01 | i6mby8 | `.aw/records/plans/pending/20261002-dirsilent-01-i6mby8-add-the-shared-non-surveyable-root-refusal-primitive-every-r.ipd.md` | Add the ONE shared refusal primitive the remaining conversions call, mapping a resolved root plus the explicit-`--dir` flag to may-proceed, the human text (reusing `no_project_message`), a path-free machine summary, and the correct next-action. Additive: ships with no callers so it cannot regress a shipped surface. | none |
| 02 | jei45f | `.aw/records/plans/pending/20261002-dirsilent-02-jei45f-convert-the-two-fail-closed-validators-specs-check-and-backl.ipd.md` | Convert the item's two named highest-value targets, `specs.run_check` and `backlog.run_check`, so a non-surveyable `--dir` refuses at exit 2 instead of emitting `outcome:clean, verified:true, checked:0`. Preserves the `specs check <path>` single-file form and the empty-but-real-project clean answer. | `executed:i6mby8` |
| 03 | sjsb04 | `.aw/records/plans/pending/20261002-dirsilent-03-sjsb04-route-the-six-resolver-bypass-sites-through-resolve-verb-rep.ipd.md` | Route the six sites that bypass the resolver (`cli._run_check`, `_run_find`, `_run_search`, `_run_record_history`, `_run_graduation`, `doctor.run`) through `resolve_verb_repo_root` so a BARE invocation climbs, then add the refusal to the five survey verbs. Fixes `aw doctor` calling an installed project not-installed; deliberately does not make `doctor` refuse. | `executed:i6mby8` |
| 04 | rlhmt9 | `.aw/records/plans/pending/20261002-dirsilent-04-rlhmt9-split-the-shared-read-write-helpers-and-convert-the-remainin.ipd.md` | Perform the prerequisite the item names: split the helpers whose callers genuinely mix read and write verbs, convert the read-class verbs behind them, and retire the two hand-rolled refusal copies by refactoring `attention.run` and `cli._run_plans` onto the primitive. Adds no refusal to any write verb and pins that as a negative control. | `executed:i6mby8`, `executed:jei45f`, `executed:sjsb04` |

## Completion criteria (the whole Set is done only when)

1. NO VERB REPORTS A POSITIVE OUTCOME FOR A TREE IT NEVER EXAMINED. Measured by driving each converted verb against a subdirectory of a seeded project, `cwd` outside any AW project, and confirming exit 2 with a `cannot-run` record rather than `outcome:clean` / `conforms` with `verified:true`. This is the Anti-Greenwashing Invariant in `docs/cli-output-contract.md` and it is the Set's reason for existing.
2. A BARE INVOCATION FROM A PROJECT SUBDIRECTORY AGREES WITH THE SAME COMMAND AT THE ROOT, for all six former bypass verbs, asserted against a NONZERO observable rather than against exit 0 (both the right and the wrong answer exit 0 today).
3. `aw doctor` NO LONGER CALLS AN INSTALLED PROJECT UNINSTALLED from a subdirectory, and still reports rather than refuses for a genuinely non-AW directory.
4. THE REFUSAL HAS EXACTLY ONE DEFINITION IN THE PACKAGE: every converted verb, plus `attention.run` and `cli._run_plans`, obtains its message, machine summary and next-action from Order 01's primitive, with the two previously hand-rolled copies retired.
5. EVERY WRITE-CLASS VERB BEHAVES EXACTLY AS IT DOES TODAY, including the path it proposes for a surveyable `--dir`, pinned as an explicit negative control with its own mutation proof. A write verb that gained a refusal is a Set FAILURE, not a bonus.
6. THE PRESERVED CASES ARE STILL PRESERVED: an EMPTY BUT REAL project still reports clean at exit 0; `aw specs check <file>` still checks that file with any `--dir`; a bare invocation from inside a project still climbs; and `attention --check` run bare with no project still returns 0 with `the view is valid`.
7. THE BARE SUITE SHOWS NO NEW FAILING NODE ID against a baseline the executor measured, at every child boundary rather than only at the end.

## Cross-IPD validation

- NO CHILD MAY HAND-ROLL THE REFUSAL. After Order 04, the message, machine summary and next-action for this condition are produced in exactly one place. Check by reading each converted call site for a call to the primitive rather than a locally built `summary` string or `NextAction`. This is the Set's central structural claim and the reason Order 01 precedes everything.
- NO CHILD MAY MAKE AN EXPLICIT `--dir` CLIMB. `lmyeas` OQ-01 decided this from measured evidence (a write-class census, a `shutil.rmtree` call site, `$HOME` being itself a project root, lane ancestry) and recorded it in `resolve_verb_repo_root`'s docstring. Order 03 routes six sites INTO the resolver, which is the opposite change and preserves the rule; confirm it did not relax it.
- NO CHILD MAY EDIT `resolve_verb_repo_root`'s BODY, and none may write a census figure into a source file. The figure in its docstring has now rotted four times (64/21 recorded, 78/24 at `lmyeas` authoring, 88/26 at its review, 91/25 with 46 AST invocations here), which is why Order 04 records its census in plan evidence only.
- THE THREE SHIPPED `--dir` TEST FILES MUST PASS UNMODIFIED THROUGHOUT (`tests/test_explicit_dir_subdir_resolution.py`, `tests/test_explicit_dir_non_project.py`, `tests/test_no_project_exit_is_cannot_run.py`). They pin the wording `lmyeas` E-03 corrected, including the removal of the false `agent-workflows is not installed in it` claim. Order 04 refactors the two surfaces those files cover, and its bar is byte-identical output with no test edited.
- THE `aw install .` OFFER MUST SURVIVE WHERE IT IS TRUE. A git repository with NO AW project must still be told to install; only the already-installed case must stop being told that. Order 01 pins this as a fourth message case precisely so a later child cannot delete it while generalizing.
- EACH CHILD RE-MEASURES ITS OWN SUITE BASELINE. Orders 03 and 04 execute after earlier children have changed shared files, so a baseline copied from this authoring would be wrong. Three failures were already present at authoring HEAD `9de38b09f` (`test_every_real_spec_in_this_repository_still_conforms`, `test_unreachable_binding_refusal_fires_under_perturbation`, `test_must_not_refuse_matrix`); the last of these exercises `find` / `check` selectors, so Order 03 must confirm it fails the SAME WAY rather than reading a pre-existing failure as its own regression.

## Deferred / out of scope (with reason)

- MAKING AN EXPLICIT `--dir` CLIMB. NOT deferred: DECIDED AGAINST by `lmyeas` OQ-01 with measured evidence, and re-measured in this Set (a write verb given a subdirectory `--dir` proposes a readable wrong path and writes nothing). NO CARRIER NEEDED: a settled decision recorded in the symbol an executor reads.
  - Carrier-Declined: decided and durably recorded by `lmyeas` E-02; this Set implements the remedy that decision implies
- ADDING A REFUSAL TO ANY WRITE-CLASS VERB. Deliberately excluded across the whole Set, and pinned as a negative control by Order 04 so the exclusion is enforced rather than merely intended. There is no greenwashing defect on that side: a write verb's wrong target is visible at a readable path and nothing enters the real records tree.
  - Carrier-Declined: decided by `lmyeas` OQ-01, re-measured in Orders 01 and 04, and enforced by Order 04's negative-control test
- MAKING `aw doctor` REFUSE a non-surveyable root. Order 03 fixes its RESOLUTION and deliberately leaves its REPORTING, because a health diagnostic asked about a non-AW directory should say so rather than refuse. Recorded here so the Set's title is not read as including it.
  - Carrier-Declined: decided in Order 03 OQ-02; `doctor` names the not-installed condition rather than claiming health
- WRITING A SPEC FOR THE RESOLUTION-AND-REFUSAL POLICY, plus a checker rule that would make a NEW unguarded read verb fail. Defensible once this Set lands and the policy is uniform, and deliberately not attempted inside it: a spec written now would be enforced only by this Set's tests, overstating the guarantee, and writing the spec plus its checker is larger than any child here. Recorded rather than filed because nobody has asked for it and filing a carrier for unrequested work would be scope invention.
  - Carrier-Declined: no defect; coherent follow-on work whose value depends on this Set landing first
- A COMPLETENESS CLAIM ABOUT THE BYPASS CENSUS. Order 03's six sites come from a STRING match on one exact expression, so a differently-spelled bypass would not appear. The Set fixes what it measured and says so.
  - Carrier: rlhmt9
- THE PRE-EXISTING SUITE FAILURES at authoring HEAD (`test_every_real_spec_in_this_repository_still_conforms`, `test_unreachable_binding_refusal_fires_under_perturbation`, `test_must_not_refuse_matrix`). Unrelated to this concern; recorded as the baseline each child reconciles against.
  - Carrier-Declined: pre-existing before any edit in this Set; the bar is the delta of failing node ids

## Scope check

- Over-scope: none. This plan's `- Scope-Paths:` lists only the four child plan files it sequences, which is what an orchestration-only plan touches. It declares no source file and no test file, because it ships neither.
- Under-scope: nothing is parked on this plan. Every deliverable the concern implies is assigned to exactly one child: the primitive to Order 01, the two validators to Order 02, the six bypass sites to Order 03, and the helper split, remaining read-class callers and duplication retirement to Order 04. The checklist above contains only child-completion confirmations, deliberately, because a runner retiring an orchestrator SKIPS the pre-transition checkpoint on the premise that a parent's own items are performed by nobody.
- IF A REVIEWER FINDS UNCOVERED WORK, the remedy is to ADD A CHILD and a row to the table, not to add an item here and not to delete the checklist.

## Required tests / validation

Each child validates itself with its own evidence; this plan runs no tests of its own and ships no code. The Set-level bar is that `python3 -m pytest` BARE shows no NEW failing node id at EVERY child boundary, with the baseline re-derived by each child at its own execution rather than trusted from this authoring (three failures were already present at HEAD `9de38b09f`, named in Cross-IPD validation).

THE SET IS ONLY DEMONSTRATED COMPLETE BY A FINAL CROSS-CHILD MEASUREMENT, which Order 04 carries as the last child rather than this plan performing it: the full before/after matrix across every converted verb, measured by subprocess with `cwd` outside any AW project against a project seeded with `--records-backend repository` and real artifacts, showing (i) every read-class verb refusing a non-surveyable `--dir` at exit 2 with a path-free `cannot-run` record, (ii) every former bypass verb agreeing between a bare subdirectory invocation and a bare root invocation, (iii) every write-class verb unchanged, and (iv) every preserved case still preserved.

## Open questions

### OQ-01: Should the Set be four children, or fewer?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: RESOLVED: FOUR, split by MECHANISM rather than by file, because the four pieces need different evidence and carry different risk. Order 01 is additive with no user-visible effect and can be validated in isolation. Order 02 is a behavior change on two fail-closed validators, where the evidence that matters is the greenwash negative. Order 03 is a DIFFERENT DEFECT CLASS (a resolver bypass, so the bare invocation under-reports too) and is the widest-blast-radius change in the Set, touching `aw check` and `aw find`. Order 04 depends on a measurement the other three do not need (which helpers genuinely mix read and write callers) and ends with a refactor of two shipped surfaces that should only happen once the primitive has been exercised. Merging 01 into 02 would put a new abstraction and a fail-closed behavior change in one unit; merging 03 into 02 would mix two mechanisms; merging 04 into anything would put a measurement-dependent refactor on the critical path of a straightforward guard.

### OQ-02: Is the item's `Blocks-Release: next` gate preserved correctly across four children?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: RESOLVED: YES, and the mechanism is explicit. All five plans in this Set carry `- From-Backlog: rgl2d4` and inherit `- Blocks-Release: next`, so the close-legitimacy predicate sees a MULTI-CARRIER item: every same-gate carrier must be `executed` before `rgl2d4` may close `done`. The item therefore stays `graduated` until Order 04, the last carrier, executes, which is what preserves the gate through the handoff rather than dropping it at the first child. No child may close the item, and each child's execution gate says so.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the `ls` or `aw find plans` output showing `i6mby8` under `.aw/records/plans/executed/` and its `- Status: executed` line. CONFIRM IT LANDED ADDITIVELY, which is the property three later children depend on: paste the primitive's signature from `project_context`, paste its regression test passing with its count, and CONFIRM no verb was converted by it (paste `git diff --stat` for its commit showing only `project_context.py` and its test file).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the lifecycle evidence showing `jei45f` `executed`. PASTE THE OUTCOME MEASUREMENT rather than trusting the child's own report: drive `aw specs check --dir <subdir>` and `aw backlog check --dir <subdir>` on a seeded fixture with `cwd` outside any AW project, and show exit 2 with a `cannot-run` record on both surfaces and no `outcome:"clean"` with `checked:0`. PASTE THE PRESERVED CASES: `aw specs check <file> --dir <subdir>` still checking that file at exit 0, and an empty-but-real project still reporting clean at exit 0.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the lifecycle evidence showing `sjsb04` `executed`. PASTE THE BARE-CWD CLIMB MATRIX for all six verbs, measured with `cwd` at a seeded project's subdirectory and at its root, asserting a NONZERO observable in each cell and showing the two columns AGREEING. PASTE THE `doctor` NEGATIVE: its bare subdirectory output no longer contains `not installed` and names the project root. CONFIRM `doctor` STILL REPORTS RATHER THAN REFUSES for a genuinely non-AW directory, which is OQ-02 of that child and not an oversight.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the lifecycle evidence showing `rlhmt9` `executed`. PASTE THE WRITE-SIDE NEGATIVE CONTROL, which is the Set's policy boundary: for each write-class verb served by a split helper, the behavior for a non-surveyable `--dir` before and after the Set, shown IDENTICAL in preview mode, plus the unchanged proposed path for a surveyable root. PASTE THE DUPLICATION-RETIREMENT EVIDENCE: `attention.run` and `cli._run_plans` calling the primitive, with their human and machine output byte-identical to before (a diff of captured outputs returning nothing) and the three shipped `--dir` test files passing UNMODIFIED (`git diff --stat` for them showing no change).
    THEN CONFIRM THE SEVEN COMPLETION CRITERIA ABOVE, one at a time, each with its own pasted measurement, and state plainly any criterion that is NOT met rather than reporting the Set complete.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan sequences four children and contributes nothing else. Each deliverable is owned by exactly one child and named in the child table; no implementation, test, baseline or record reconciliation is parked on this plan. That is deliberate: a runner retires an orchestrator once every child is `executed` and SKIPS the pre-transition checkpoint, on the premise that a parent's own items are performed by nobody, so work left here would be marked complete having never been performed or verified.

WHAT APPROVAL IS APPROVING AT THE SET LEVEL is a behavior change on roughly a dozen verbs: an input that today exits 0 claiming `conforms` will exit 2, and a bare invocation from a project subdirectory will survey the project rather than the subdirectory. Both are fixes, and the second is also a change any caller relying on the non-climbing cwd default would notice. The honest assessment of that risk is that such a caller is today being told a tree is clean when it was never examined, while that verb's own sibling (`aw specs check` beside `aw check`) already climbed from the same directory - so the inconsistency was itself the defect.

TWO DEPARTURES FROM THE BACKLOG ITEM SHOULD BE RATIFIED EXPLICITLY, both from measurement rather than preference. FIRST, the Set is wider than filed: the item names `doctor.run`'s resolver bypass as one low-cost sub-case, and measurement found SIX sites sharing that bypass, three of them `aw check`, `aw find` and `aw search`, under-reporting with no flag at all. SECOND, one prerequisite is narrower than filed: the item names six shared helpers needing a read/write split, and reading each helper's callers showed only three are genuinely mixed. A maintainer who prefers the item's literal scope can approve Order 02 alone, which is the item's own named starting point; the argument against that is that `aw check` is the surface CI runs and it is the one giving a false clean answer for free.

ALL FIVE PLANS CARRY `- From-Backlog: rgl2d4` AND INHERIT ITS `- Blocks-Release: next` GATE, which makes the item a MULTI-CARRIER item: it stays `graduated` until the LAST carrier (Order 04) executes, and only then is eligible to close `done` with its gate provably preserved. No child may close it, and no child's execution may set it `done`; the runner owns that transition.

ON COMPLETION OF EVERY CHILD, the runner retires this orchestrator automatically once all four are `executed` on disk, spending no agent turn. Executed by hand, the executor confirms the four child confirmations and the seven completion criteria with pasted evidence, then runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-roll the move with `git mv` to `executed/` and never hand-edit `- Status: executed`.

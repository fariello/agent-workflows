# IPD: Stop the silent --dir and bare-cwd under-report across every resolver caller

- Date: 2026-10-02
- Kind: orchestrator
- Concern: Backlog `rgl2d4` reports that the ~35 `resolve_verb_repo_root` callers outside `aw attention` and `aw ipd board` fall back SILENTLY for a non-surveyable `--dir`, so `aw specs check` and `aw backlog check` announce conformance having examined ZERO artifacts at a project subdirectory. Measured at this lane's HEAD the item reproduces exactly, and the machine surface is worse than filed: both validators emit `"outcome":"clean","exit":0,"verified":true,"complete":true,"checked":0`, which is the Anti-Greenwashing Invariant violation `docs/cli-output-contract.md` names outright and is the field a CI step is told to trust. Measurement also found a defect class the item does not describe: SIX sites bypass the resolver entirely with their own `Path(getattr(args,"dir",None) or os.getcwd())`, so `aw check`, `aw find`, `aw search`, `aw record-history`, `aw graduation` and `aw doctor` under-report with NO FLAG AT ALL - a plain `cd src && aw check` reports `0 specs checked` where the same command at the root reports `1`, and `aw doctor` calls an installed project `not installed`. This Set sequences the remedy.
- Scope: ORCHESTRATION ONLY. This plan sequences five children and contributes no implementation, no test and no deliverable of its own. Every artifact is owned by exactly one child and named in the child table below. IN: the dependency order, the Set-level completion criteria, and the cross-child consistency checks. OUT: everything the children do, which is the shared refusal primitive (Order 01), the two fail-closed validators (Order 02), the six resolver-bypass sites (Order 03), and the shared read/write helper split plus the remaining read-class callers and the duplication retirement (Order 04), and the seventh bypass site `cli._nv_backend_args` found at review (Order 05). This plan also does NOT reopen the no-climb decision `lmyeas` OQ-01 settled, and does NOT add a refusal to any write-class verb.
- Scope-Paths: .aw/records/plans/pending/20261002-dirsilent-01-i6mby8-add-the-shared-non-surveyable-root-refusal-primitive-every-r.ipd.md, .aw/records/plans/pending/20261002-dirsilent-02-jei45f-convert-the-two-fail-closed-validators-specs-check-and-backl.ipd.md, .aw/records/plans/pending/20261002-dirsilent-03-sjsb04-route-the-six-resolver-bypass-sites-through-resolve-verb-rep.ipd.md, .aw/records/plans/pending/20261002-dirsilent-04-rlhmt9-split-the-shared-read-write-helpers-and-convert-the-remainin.ipd.md, .aw/records/plans/pending/20261007-dirsilent-05-pua92o-route-the-noun-verb-backend-adapter-through-resolve-verb-rep.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: c757ac4e13ec027f412a09afa1109268f0b627c0c8dcbf0d6e78a7dc51f4abf1
- Coverage-Checked: 2026-10-07 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: bug
- Priority: medium
- From-Backlog: rgl2d4
- Blocks-Release: next
- Set: dirsilent
- Order: 0
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: axozpe
- Approval: 2026-10-08, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-08 approved (aw set): status set to approved
- 2026-10-07 reviewed (opencode uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (child pua92o added)
- 2026-10-07 coverage pass (aw oc run): fingerprint c757ac4e13ec, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 /plan-review (opencode uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; coverage-correction turn 1: PR-001 fixed by adding child Order 05 `pua92o` (owns `cli._nv_backend_args`), OQ-03 resolved non-blocking; PR-002..PR-005 fixed in round 1. Review record round 2.
- 2026-10-07 coverage fail (aw oc run): fingerprint 5cf3bb1cbeb9, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 /plan-review (opencode uri/its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 (OPEN, escalated as blocking OQ-03), PR-002..PR-005 fixed. Status left `to-review` and `- Readiness:` left ABSENT: `aw ipd coverage axozpe` now fails on the PR-001 gap, and closing it needs the maintainer's OQ-03 scope decision (IPD-S408 R6 path). Review record `.aw/records/reviews/20261007-dirsilent-00-axozpe-stop-the-silent-dir-and-bare-cwd.review.md`.
- 2026-10-07 to-review (aw set): returned to review: each Set-level check the coverage probe quoted now names its owning child; coverage pass recorded
- 2026-10-07 coverage pass (aw oc run): fingerprint e490f67c8c6c, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: Check by reading each converted call site for a call to the primitive

- 2026-10-06 coverage fail (aw oc run): fingerprint b59fda92b7d9, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `rgl2d4`. GATE NOTE: item `rgl2d4` carries `- Blocks-Release: next`, which this plan and all four children INHERIT as required.
  THIS PLAN CARRIES ORCHESTRATION AND NOTHING ELSE. Its four `E-*` items are confirmations that each child reached `executed`; no item produces a deliverable, establishes a baseline, or reconciles records, because an orchestrator's own items are performed by nobody when a runner retires it. If a reviewer finds work here that no child covers, the correct remedy is a NEW CHILD, not an item on this plan.
  THE SET DEPARTS FROM THE ITEM'S FRAMING IN TWO MEASURED WAYS, both recorded so approval is informed. FIRST, the item says the remaining work "is adopting that classifier at the remaining callers", implying the predicate was the only missing piece; measured, the REFUSAL (message, path-free machine record, exit codes) is hand-rolled twice already and is the half that gets copied, which is why Order 01 adds a shared emitter before anything is converted. SECOND, the item names `doctor.run`'s resolver bypass as a single low-cost sub-case; measured, SIX sites share that bypass and three of them are `aw check`, `aw find` and `aw search`, which makes it a live false-clean-answer reachable with no flag rather than a latent inconsistency, and earns it its own Order.
  AND ONE ITEM CLAIM IS CORRECTED DOWNWARD BY MEASUREMENT: the item names six shared helpers needing a read/write split; reading each helper's callers, only THREE are genuinely mixed. Order 04 records that and re-derives it at execution rather than trusting this authoring.

## Goal

Make every read-class repo-scoped verb tell the truth about a directory it cannot survey, and make a bare invocation from a project subdirectory climb like its siblings. At the end of this Set no verb reports `conforms`, `clean` or `0 findings` for a tree it never examined, the refusal has exactly one definition in the package, and write-class verbs are exactly as safe as they are today.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: sequence the Set

- [ ] E-01 CONFIRM i6mby8 REACHED executed
  Confirm child 01 (`i6mby8`, the shared refusal primitive) reached `executed`, and that it shipped the primitive ADDITIVELY with no verb converted and the two existing hand-rolled call sites untouched. This is the dependency every later child declares, so a partial landing here silently weakens three plans.
  - Depends on: none
  - Expected outcome: `i6mby8` is in `.aw/records/plans/executed/` with `- Status: executed`, and the primitive exists in `project_context` with its regression test passing.
  - Execution state: pending

- [ ] E-02 CONFIRM jei45f REACHED executed
  Confirm child 02 (`jei45f`, the two fail-closed validators) reached `executed`, and that `aw specs check --dir <subdir>` and `aw backlog check --dir <subdir>` now refuse at exit 2 rather than announcing conformance over zero artifacts. This is the item's own named starting point and the highest-severity surface in the Set.
  - Depends on: E-01
  - Expected outcome: `jei45f` is in `.aw/records/plans/executed/` with `- Status: executed`, and both validators refuse a non-surveyable root on both surfaces while the single-file form and the empty-but-real project still behave as before.
  - Execution state: pending

- [ ] E-03 CONFIRM sjsb04 REACHED executed
  Confirm child 03 (`sjsb04`, the six resolver-bypass sites) reached `executed`, and that a BARE invocation from a project subdirectory now climbs for all six verbs, including `aw doctor` no longer reporting an installed project as `not installed`.
  - Depends on: E-01
  - Expected outcome: `sjsb04` is in `.aw/records/plans/executed/` with `- Status: executed`, and the bare-cwd climb matrix shows the subdirectory and root columns agreeing for `check`, `find`, `search`, `record-history`, `graduation` and `doctor`.
  - Execution state: pending

- [ ] E-04 CONFIRM rlhmt9 REACHED executed
  Confirm child 04 (`rlhmt9`, the helper split, the remaining read-class callers and the duplication retirement) reached `executed`, and that no write-class verb gained a refusal. That negative is the Set's policy boundary and is the one outcome a careless execution could invert.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `rlhmt9` is in `.aw/records/plans/executed/` with `- Status: executed`; the mixed helpers are split, the read-class verbs refuse, `attention.run` and `cli._run_plans` call the shared primitive with byte-identical output, and every write-class verb behaves exactly as before.
  - Execution state: pending

- [ ] E-05 CONFIRM pua92o REACHED executed
  Confirm child 05 (`pua92o`, the seventh bypass site `cli._nv_backend_args`) reached `executed`, and that a bare `aw index|group|rename|archive <type>` from a project subdirectory now targets the project root while an explicit `--dir` still does not climb.
  - Depends on: E-03
  - Expected outcome: `pua92o` is in `.aw/records/plans/executed/` with `- Status: executed`, and its V-01 shows bare `index plans --check` and `index research --check` agreeing between subdirectory and root.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Plan | Purpose | Depends on |
| --- | --- | --- | --- | --- |
| 01 | i6mby8 | `.aw/records/plans/pending/20261002-dirsilent-01-i6mby8-add-the-shared-non-surveyable-root-refusal-primitive-every-r.ipd.md` | Add the ONE shared refusal primitive the remaining conversions call, mapping a resolved root plus the explicit-`--dir` flag to may-proceed, the human text (reusing `no_project_message`), a path-free machine summary, and the correct next-action. Additive: ships with no callers so it cannot regress a shipped surface. | none |
| 02 | jei45f | `.aw/records/plans/pending/20261002-dirsilent-02-jei45f-convert-the-two-fail-closed-validators-specs-check-and-backl.ipd.md` | Convert the item's two named highest-value targets, `specs.run_check` and `backlog.run_check`, so a non-surveyable `--dir` refuses at exit 2 instead of emitting `outcome:clean, verified:true, checked:0`. Preserves the `specs check <path>` single-file form and the empty-but-real-project clean answer. | `executed:i6mby8` |
| 03 | sjsb04 | `.aw/records/plans/pending/20261002-dirsilent-03-sjsb04-route-the-six-resolver-bypass-sites-through-resolve-verb-rep.ipd.md` | Route the six sites that bypass the resolver (`cli._run_check`, `_run_find`, `_run_search`, `_run_record_history`, `_run_graduation`, `doctor.run`) through `resolve_verb_repo_root` so a BARE invocation climbs, then add the refusal to the five survey verbs. Fixes `aw doctor` calling an installed project not-installed; deliberately does not make `doctor` refuse. | `executed:i6mby8` |
| 04 | rlhmt9 | `.aw/records/plans/pending/20261002-dirsilent-04-rlhmt9-split-the-shared-read-write-helpers-and-convert-the-remainin.ipd.md` | Perform the prerequisite the item names: split the helpers whose callers genuinely mix read and write verbs, convert the read-class verbs behind them, and retire the two hand-rolled refusal copies by refactoring `attention.run` and `cli._run_plans` onto the primitive. Adds no refusal to any write verb and pins that as a negative control. | `executed:i6mby8`, `executed:jei45f`, `executed:sjsb04` |
| 05 | pua92o | `.aw/records/plans/pending/20261007-dirsilent-05-pua92o-route-the-noun-verb-backend-adapter-through-resolve-verb-rep.ipd.md` | Route the seventh resolver bypass, `cli._nv_backend_args` (which turns a bare call into an explicit `--dir <cwd>` for every noun-verb backend), through `resolve_verb_repo_root` so a bare `aw index|group|rename|archive <type>` climbs. Adds no refusal; pins the bare climb (preview-only for write verbs) and the explicit-`--dir` no-climb rule. Found at review (PR-001). | `executed:sjsb04` |

## Completion criteria (the whole Set is done only when)

1. NO VERB REPORTS A POSITIVE OUTCOME FOR A TREE IT NEVER EXAMINED. Measured by driving each converted verb against a subdirectory of a seeded project, `cwd` outside any AW project, and confirming exit 2 with a `cannot-run` record rather than `outcome:clean` / `conforms` with `verified:true`. This is the Anti-Greenwashing Invariant in `docs/cli-output-contract.md` and it is the Set's reason for existing. Owner: each converting child for its own verbs (Order 02 `jei45f` V-01/V-02, Order 03 `sjsb04` V-03, Order 04 `rlhmt9` V-03, and Order 05 `pua92o` V-01 for the bare `index <type> --check` path through `cli._nv_backend_args`).
2. A BARE INVOCATION FROM A PROJECT SUBDIRECTORY AGREES WITH THE SAME COMMAND AT THE ROOT, for all six former bypass verbs and for the noun-verb backends behind `cli._nv_backend_args`, asserted against a NONZERO observable rather than against exit 0 (both the right and the wrong answer exit 0 today). Owner: Order 03 `sjsb04` (V-01, V-02, V-04) for the six sites; Order 05 `pua92o` (V-01, V-02) for the noun-verb backends.
3. `aw doctor` NO LONGER CALLS AN INSTALLED PROJECT UNINSTALLED from a subdirectory, and still reports rather than refuses for a genuinely non-AW directory. Owner: Order 03 `sjsb04` (V-02, V-03, V-04).
4. THE REFUSAL HAS EXACTLY ONE DEFINITION IN THE PACKAGE: every converted verb, plus `attention.run` and `cli._run_plans`, obtains its message, machine summary and next-action from Order 01's primitive, with the two previously hand-rolled copies retired. Owner: Order 04 `rlhmt9` (E-04, E-05).
5. EVERY WRITE-CLASS VERB BEHAVES EXACTLY AS IT DOES TODAY, including the path it proposes for a surveyable `--dir`, pinned as an explicit negative control with its own mutation proof. A write verb that gained a refusal is a Set FAILURE, not a bonus. Owner: Order 04 `rlhmt9` (V-03 write-side matrix, V-05 second mutation) for the write verbs behind the split helpers; write verbs no child touches are unchanged by construction and are covered by the bare suite (criterion 7).
6. THE PRESERVED CASES ARE STILL PRESERVED: an EMPTY BUT REAL project still reports clean at exit 0; `aw specs check <file>` still checks that file with any `--dir`; a bare invocation from inside a project still climbs; and `attention --check` run bare with no project still returns 0 with `the view is valid`. Owner: Order 02 `jei45f` V-01 (empty project, single-file form), Order 03 `sjsb04` V-01/V-04 (bare climb), Order 04 `rlhmt9` V-04 (`attention --check`).
7. THE BARE SUITE SHOWS NO NEW FAILING NODE ID against a baseline the executor measured, at every child boundary rather than only at the end. Owner: each child at its own boundary (Orders 01 `i6mby8`, 02 `jei45f` and 03 `sjsb04` in their final V-items), and Order 04 `rlhmt9` (V-05) for the final run.

## Cross-IPD validation

- NO CHILD MAY HAND-ROLL THE REFUSAL. After Order 04, the message, machine summary and next-action for this condition are produced in exactly one place. Owner: Order 04 `rlhmt9` performs this check (its E-04 retires the two hand-rolled copies and its E-05/V-05 prove every converted call site obtains the refusal from the primitive); Orders 02 `jei45f` and 03 `sjsb04` each confirm it for their own call sites in their V-items. This is the Set's central structural claim and the reason Order 01 precedes everything.
- NO CHILD MAY MAKE AN EXPLICIT `--dir` CLIMB. `lmyeas` OQ-01 decided this from measured evidence (a write-class census, a `shutil.rmtree` call site, `$HOME` being itself a project root, lane ancestry) and recorded it in `resolve_verb_repo_root`'s docstring. Order 03 routes six sites INTO the resolver, which is the opposite change and preserves the rule; Order 03 `sjsb04` confirms in its own validation that no explicit `--dir` climbs.
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
- A COMPLETENESS CLAIM ABOUT THE BYPASS CENSUS. Order 03's six sites come from a STRING match on one exact expression, so a differently-spelled bypass would not appear. The Set fixes what it measured and says so. CORRECTED AT REVIEW (PR-001): this row previously named `rlhmt9` as carrier, but `rlhmt9` contains no bypass audit, and a seventh, differently-spelled site WAS found: `cli._nv_backend_args` sets `sub.dir = getattr(args, "dir", None) or os.getcwd()`, which hands the cwd to every noun-verb backend as an EXPLICIT `--dir`, so a bare `aw index|group|rename|archive <type>` from a subdirectory does not climb. Now owned by Order 05 `pua92o` (OQ-03). Any further differently-spelled site remains unmeasured.
  - Carrier: pua92o
- THE PRE-EXISTING SUITE FAILURES at authoring HEAD (`test_every_real_spec_in_this_repository_still_conforms`, `test_unreachable_binding_refusal_fires_under_perturbation`, `test_must_not_refuse_matrix`). Unrelated to this concern; recorded as the baseline each child reconciles against.
  - Carrier-Declined: pre-existing before any edit in this Set; the bar is the delta of failing node ids

## Scope check

- Over-scope: none. This plan's `- Scope-Paths:` lists only the five child plan files it sequences, which is what an orchestration-only plan touches. It declares no source file and no test file, because it ships neither.
- Under-scope: nothing is parked on this plan. Every deliverable the concern implies is assigned to exactly one child: the primitive to Order 01, the two validators to Order 02, the six bypass sites to Order 03, and the helper split, remaining read-class callers and duplication retirement to Order 04, and the seventh bypass site `cli._nv_backend_args` to Order 05 `pua92o`. The checklist above contains only child-completion confirmations, deliberately, because a runner retiring an orchestrator SKIPS the pre-transition checkpoint on the premise that a parent's own items are performed by nobody.
- IF A REVIEWER FINDS UNCOVERED WORK, the remedy is to ADD A CHILD and a row to the table, not to add an item here and not to delete the checklist.

## Required tests / validation

Each child validates itself with its own evidence; this plan runs no tests of its own and ships no code. The Set-level bar is that `python3 -m pytest` BARE shows no NEW failing node id at EVERY child boundary, with the baseline re-derived by each child at its own execution rather than trusted from this authoring (three failures were already present at HEAD `9de38b09f`, named in Cross-IPD validation).

THE CROSS-CHILD DEMONSTRATION IS THE SUITE, NOT A SEPARATE MATRIX (corrected at review, PR-002: this paragraph previously said Order 04 carries a full cross-child before/after matrix, and `rlhmt9` carries no such item). Each child measures its own matrix by subprocess with `cwd` outside any AW project against a project seeded with `--records-backend repository` and real artifacts, and pins it in its own new regression test file (`tests/test_validator_nonsurveyable_dir.py`, `tests/test_resolver_bypass_sites_climb.py`, `tests/test_read_class_callers_refuse.py`, `tests/test_nv_backend_args_climb.py`, plus Order 01's `tests/test_nonsurveyable_root_refusal.py`). Order 04 `rlhmt9` V-05 and Order 05 `pua92o` V-02 each run the BARE suite after the children they depend on have landed, so a later child regressing an earlier child's (i) read-class refusal, (ii) bare-cwd climb, (iii) write-class negative control or (iv) preserved case surfaces there as a new failing node id. That run is the Set-level completion evidence; this plan re-runs nothing.

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
- Resolution or deferral rationale: RESOLVED: YES, and the mechanism is explicit. All five plans in this Set carry `- From-Backlog: rgl2d4` and inherit `- Blocks-Release: next`, so the close-legitimacy predicate sees a MULTI-CARRIER item: every same-gate carrier must be `executed` before `rgl2d4` may close `done`. The item therefore stays `graduated` until the last carrier (Order 04 or Order 05) executes, which is what preserves the gate through the handoff rather than dropping it at the first child. No child may close the item, and each child's execution gate says so.

### OQ-03: Who owns the seventh resolver-bypass site, `cli._nv_backend_args`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Finding: PR-001
- Context (measured at review, lane HEAD `ad22ff70a`): `cli._nv_backend_args` (the noun-verb adapter, `agent_workflows/cli.py`, "`sub.dir = getattr(args, "dir", None) or os.getcwd()`") converts a BARE invocation into an EXPLICIT `--dir <cwd>` before calling every `aw index|group|rename|archive <type>` backend and the `_run_check` fallback backend. Because the resolver never climbs an explicit `--dir`, a bare call from a subdirectory surveys the subdirectory. Reproduced in this worktree: `aw index research --check --agent` at the root returns `outcome:findings, exit 1, findings 179`; the same command from `docs/` returns `outcome:conforms, exit 0, verified:true, findings 2` (only `stale-index-missing`). That is the same false-clean answer this Set exists to remove, reachable with no flag. Order 03's census missed it because it matched one exact string, and no child covers it; this plan's Deferred row previously named `rlhmt9` as the carrier, which was false.
- Decision needed: (a) add a fifth child (Order 05) that routes `_nv_backend_args` through `resolve_verb_repo_root` and adds the refusal to its read-class verbs (`index ... --check`), with write-class `group`/`rename`/`archive` getting the climb but no refusal; (b) widen Order 03 `sjsb04` to include it as a seventh site; or (c) decline it for this Set and file a new backlog item inheriting `- Blocks-Release: next`. Reviewer recommendation: (a), because the site feeds WRITE verbs too (`group`/`rename`/`archive`), so changing its bare-case root is a write-target change that needs its own negative controls, which is outside Order 03's stated "single-expression" risk profile. This is a scope decision for the maintainer, so it is not resolved here.
- Resolution or deferral rationale: RESOLVED (coverage-correction turn 1, 2026-10-07): option (a). A new child, Order 05 `pua92o`, owns the site. It routes the adapter through the resolver so a bare call climbs and adds NO refusal, because the `index` backends sit behind helpers `rlhmt9` F-02 measured as single-class write, and the Set excludes write-side refusals (`lmyeas` OQ-01). The orchestrator coverage gate refused the plan until the site had an owner, and the AGENTS contract names adding a child as the remedy ("WHEN IT FIRES, ADD A CHILD"). Option (b) would have widened `sjsb04` past its single-expression risk profile. Option (c) would have left a known false-clean answer in a release-gated Set. The maintainer can still reject `pua92o` at approval, so this choice is reversible. OQ-01's FOUR-child answer is superseded to FIVE by this resolution: Order 05 is a distinct mechanism (one adapter feeding every noun-verb backend) whose evidence is a bare-climb matrix, consistent with OQ-01's split-by-mechanism rule.

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
    THEN CONFIRM THE SEVEN COMPLETION CRITERIA ABOVE, one at a time, by citing the OWNING CHILD'S V-item evidence named on each criterion (child plan id6 and V-id, with the line of pasted output that settles it), plus `rlhmt9` V-05's final bare-suite summary line for criterion 7. Do not re-measure here: this plan owns no measurement. State plainly any criterion whose owner's evidence is missing or does not settle it, and any criterion still marked unowned (OQ-03), rather than reporting the Set complete.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the lifecycle evidence showing `pua92o` `executed`, and cite its V-01 BEFORE/AFTER measurement (bare `index plans --check` and `index research --check` from subdirectory vs root, disagreeing before and agreeing after, with a nonzero observable at the root) and its V-02 mutation proof, quoting the settling lines.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan sequences five children and contributes nothing else. Each deliverable is owned by exactly one child and named in the child table; no implementation, test, baseline or record reconciliation is parked on this plan. That is deliberate: a runner retires an orchestrator once every child is `executed` and SKIPS the pre-transition checkpoint, on the premise that a parent's own items are performed by nobody, so work left here would be marked complete having never been performed or verified.

WHAT APPROVAL IS APPROVING AT THE SET LEVEL is a behavior change on roughly a dozen verbs: an input that today exits 0 claiming `conforms` will exit 2, and a bare invocation from a project subdirectory will survey the project rather than the subdirectory. Both are fixes, and the second is also a change any caller relying on the non-climbing cwd default would notice. The honest assessment of that risk is that such a caller is today being told a tree is clean when it was never examined, while that verb's own sibling (`aw specs check` beside `aw check`) already climbed from the same directory - so the inconsistency was itself the defect.

TWO DEPARTURES FROM THE BACKLOG ITEM SHOULD BE RATIFIED EXPLICITLY, both from measurement rather than preference. FIRST, the Set is wider than filed: the item names `doctor.run`'s resolver bypass as one low-cost sub-case, and measurement found SIX sites sharing that bypass, three of them `aw check`, `aw find` and `aw search`, under-reporting with no flag at all. SECOND, one prerequisite is narrower than filed: the item names six shared helpers needing a read/write split, and reading each helper's callers showed only three are genuinely mixed. A maintainer who prefers the item's literal scope can approve Order 02 alone, which is the item's own named starting point; the argument against that is that `aw check` is the surface CI runs and it is the one giving a false clean answer for free.

ALL FIVE PLANS CARRY `- From-Backlog: rgl2d4` AND INHERIT ITS `- Blocks-Release: next` GATE, which makes the item a MULTI-CARRIER item: it stays `graduated` until the LAST carrier (Order 04 or Order 05, whichever executes later) executes, and only then is eligible to close `done` with its gate provably preserved. No child may close it, and no child's execution may set it `done`; the runner owns that transition.

EXECUTION CONTRACT. Open questions: OQ-01, OQ-02 and OQ-03 are resolved (OQ-03 by adding Order 05 `pua92o`). SCOPE FENCE (a declaration for the runner to reconcile, not an instruction to stop): this plan modifies only its own file and, at most, the child plan paths in `- Scope-Paths:`; any out-of-scope edit is made and then justified with `aw ipd finalize --scope-reason`, and a declared path left unmodified needs `--scope-ack`. HONESTY RULE: every V-item MUST paste the ACTUAL command output it cites (never a paraphrase, never a claimed pass that was not run). COMMITS: commit only paths you changed, through `aw commit <plan> -- <paths>`, never `git add -A`, and NEVER push.

ON COMPLETION OF EVERY CHILD, the terminal transition is owed unconditionally but its owner is conditional. Under `aw oc run` / `aw agy run` the RUNNER retires this orchestrator automatically once every child is `executed` on disk, spending no agent turn, and the executor must NOT run `aw ipd finalize` itself. Executed by hand, the executor confirms the five child confirmations and the seven completion criteria with pasted evidence, then runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-roll the move with `git mv` to `executed/` and never hand-edit `- Status: executed`.

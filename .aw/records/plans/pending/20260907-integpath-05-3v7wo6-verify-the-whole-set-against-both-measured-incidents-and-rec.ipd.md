# IPD: Verify the whole Set against both measured incidents and record the residuals

- Date: 2026-09-07
- Kind: child
- Concern: The `integpath` Set's central claim is that verified work stops getting lost on the lane-to-main path. Four green child suites do NOT establish it: each child tests its own mechanism, while the failure the Set exists to prevent is an INTERACTION (a refusal that is terminal, times a recovery route the hook blocks, times a resume that orphans the lane). So the whole-Set verification is real execution work that somebody must perform.
  IT CANNOT LIVE ON THE ORCHESTRATOR, WHICH IS WHY THIS CHILD EXISTS. The runner-owned rollup deliberately OMITS the `pre-transition` E/V checkpoint for an orchestrator (`ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']`, spec `77tr3o` R-5 shape (b)) on the premise that an orchestrator's items are performed by NOBODY. Work parked on a parent is therefore marked complete having never been performed OR verified. MEASURED, not predicted: orchestrator `84j8d7` sits in `executed/` today carrying `Execution state: pending` on its E-01 and `Result: pending` on its V-01, rollup-retired by run `run-20260906T222606Z-2987341` (commit `52c2872a`), despite carrying an explicit forceful warning against exactly that. A warning addressed to a human does not constrain a code path (`k1nity`: informing an agent is necessary and not sufficient).
  THIS SHAPE MAKES IT UNSKIPPABLE. A `Kind: child` plan gets the enforced E/V checkpoint and `retire_orchestrator` REFUSES to retire a child, so the rollup cannot discharge this verification. Maintainer ruling 2026-09-07, option (b) of orchestrator `cczotj` OQ-04.
- Scope: Perform the whole-Set verification (both measured incidents, both hosts) and write the durable residuals record. Authors NO product code: every implementation belongs to children 01 through 04. This child is the Set's evidence, so its only deliverables are pasted observed evidence and one walkthrough artifact.
- Scope-Paths: .aw/records/walkthroughs/, .aw/records/plans/pending/20260907-integpath-05-3v7wo6-verify-the-whole-set-against-both-measured-incidents-and-rec.ipd.md
- Item-Dependencies: executed:29wvmj, executed:6sb3yu, executed:51vw4y, executed:rl67b0
- Status: approved
- Readiness: go-pending-approval
- Set: integpath
- Order: 5
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 3v7wo6
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
- From-Backlog: 5wdoze
- Blocks-Release: next

## Workflow history
- 2026-09-18 executed (opencode its_direct/pt3-claude-opus-5-1m-us): E-01 and E-02 performed, V-01 and V-02 verified with pasted evidence, at HEAD `36129255` in run `run-20260918T015435Z-84931`. All four implementing children (`29wvmj`, `6sb3yu`, `51vw4y`, `rl67b0`) confirmed `executed` on disk, so this child was dispatchable rather than dependency-blocked as F-5 predicted. BOTH measured incidents reproduced END TO END on BOTH hosts, 45 assertions, 0 failures: driving each host's OWN adapters (`retry_deferred_integrations`, `_integrate_stranded_lanes`) rather than the shared functions children 03/04 bind, in throwaway repositories carrying a REAL passing test so the gate's `run_suite_check` ran an actual suite. That last detail was load-bearing: with no test file present pytest exits 5 and the gate fails closed, which would have proven only that the gate fails closed. Asserted on synthetic ids `aa0001`/`bb0002`, never on `mm6wuz` here (its three `_attempt*` branches are another party's preserved work and none was deleted). TWO PREDICTIONS OF THIS PLAN WERE WRONG AT HEAD AND ARE CORRECTED, both because the plan told the executor to re-measure rather than trust: the startup dirty-base gate has LANDED (`3i0aaz` is now `executed`, `--allow-dirty-base` exists at `runner_shared.py:5232`), so it was EXERCISED, not recorded absent; and five cited siblings had moved status, including `h1ksy6` and `a8eufb`, which now have owning plans (`fujm0y`, `wao266`, both approved) rather than being unowned residuals. ONE DEFECT FOUND AND FILED, not in this Set: the runner exports `AW_EXECUTION_ROLE=worker` into an execution turn, which makes 31 suite tests fail for reasons unrelated to the plan (32 failures worker-marked versus 1 with the single variable unset, no code change), so both baselines were measured with it unset and the finding filed as backlog `1uq1cu`. A SECOND, smaller defect was found while writing the walkthrough and filed as `sovauj`: `check.setid-collision` reports a false cross-type collision when a walkthrough declares the Set of a plan still in `pending/`, because the rule skips `executed/` plans as retired. Bare suite `1 failed, 7906 passed` before and after with the after-minus-before failure set EMPTY by node id (the one failure a load-dependent `TimeoutExpired` that passes in isolation); the two slow declaration suites run separately under `-m ''` with the undeclared-leaf set still exactly the five pre-existing `oc profile *` entries. Walkthrough written at `.aw/records/walkthroughs/20260918-integpath-05-u8tiox-...walkthrough.md` with a freshly minted id6 and `Target-Id: 3v7wo6`; `aw check` reports zero identity-slot findings and zero findings against it. Lint conforming at `--phase pre-transition`. No product code authored, nothing pushed.
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-09 reviewed (aw set): /plan-review round 1 (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 all FIXED, no open questions. Reviewed by RUNNING the plan's own instructions rather than re-reading them, which produced both HIGH findings. PR-001: the walkthrough filename E-02 mandated put THIS plan's id6 in the walkthrough's own identity slot, violating DECISIONS.md D140 and failing check.id6-identity-slot (reproduced in a scratch repo); E-02 now mints a fresh id6, uses the canonical .walkthrough.md facet and links via Target-Id: 3v7wo6. PR-002: V-01's no-_attempt2 assertion fails on pre-existing history here (aw/lane/mm6wuz, _attempt2, _attempt3 all exist among 29 lane branches) and the only literal way to pass it was deleting a co-worker's preserved lanes; both incident reproductions are now explicitly synthetic, asserted on the synthetic id6 in a throwaway repo, with a do-not-delete-a-lane gate paragraph. PR-003: the inherited baseline failure was wrong (test_orchestrator_retirement is GREEN at 112 passed; the one bare-run failure is the environmental test_reporting_contract case caused by the gitignored opencode-recovery dump, proven causal by moving it aside for 53 passed). PR-004: added the -m '' slow-suite run the bare suite deselects, which children 03/04 already require. PR-005..PR-008: corrected stale citations (32ij2j/xtklpd superseded by daexj1/ys1dor, hyx1dg/yf9fj9 are backlog not plans, p8ni63 graduated to 3i0aaz), named the exact allow-dirty-base grep (returns nothing), re-measured 178/60 collection counts, narrowed Scope-Paths and fixed the 'respectively' closure claim. Lint conforming at author and review-finalize; typed review record written with four D-rows, all reversible.
- 2026-09-07 to-review (aw set): status set to to-review

- 2026-09-07 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created to carry orchestrator `cczotj`'s E-01/E-02, demoted here by maintainer ruling on that plan's OQ-04 (option (b)) so the whole-Set verification sits where the E/V checkpoint is ENFORCED rather than where the rollup omits it. The two E-items and their evidence requirements are carried over in substance from `cczotj` rather than rewritten, so nothing the review had already hardened is lost.

## Goal

Establish, with pasted evidence on both hosts, that the two measured incidents are survived end to end, and leave a durable record of exactly what this Set closed and what it deliberately did not.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This child authors NO product code. Its execution work is whole-Set verification and the durable record; children 01 through 04 carry every change.

### Task group 1: verify the Set's central claim

- [x] E-01 VERIFY THE WHOLE SET against the two MEASURED INCIDENTS, on BOTH hosts, after all four implementing children have executed. This is the Set's central claim and it must be falsifiable rather than asserted from four green child suites.
  REPRODUCE INCIDENT ONE (`run-20260905T050043Z-639569`): a lane finalizes, finds an overlapping dirty path in main, and the dirt clears while other work is still running. Assert the item DEFERS and later INTEGRATES with no agent turn spent, and that a `--no-verify` was NOT required at any point.
  REPRODUCE INCIDENT TWO (`mm6wuz`, 2026-09-06): an item holding a verified lane is resumed. Assert the FIRST lane is integrated rather than a second being allocated, and that `git branch --list 'aw/lane/<id6>*'` shows no `_attempt2`.
  RUN THAT BRANCH CHECK INSIDE THE SYNTHETIC REPOSITORY, AGAINST THE SYNTHETIC ITEM'S OWN id6, AND NEVER AGAINST `mm6wuz` IN THIS CHECKOUT. Both children reconstruct these incidents synthetically in a throwaway repository because the original lanes are historical, and the historical lanes are STILL PRESENT here: measured at review 2026-09-09, `git branch --list 'aw/lane/mm6wuz*'` returns `aw/lane/mm6wuz`, `aw/lane/mm6wuz_attempt2` and `aw/lane/mm6wuz_attempt3`, three of the 29 `aw/lane/*` branches this checkout carries. So running the assertion here would report FAILURE for pre-existing history no matter how well the fix works, and DELETING those branches to make it pass is forbidden: they are another party's preserved work in a SHARED CHECKOUT, and `nuanaw`/`ys1dor` treat exactly those attempt clusters as live evidence. State the synthetic id6 you asserted on.
  THE STARTUP GATE (`p8ni63`) IS CONDITIONAL AND IS NOT THIS SET'S TO DELIVER. It is NOT a child of this Set, so FIRST determine whether it has landed: run `grep -rn "allow-dirty-base\|allow_dirty_base" agent_workflows/` (the exact check, so the result is reproducible). If it HAS landed, assert it refuses a dirty base and honors its override. If it has NOT, record that plainly and MOVE ON; its absence must NOT be reported as this Set's failure, and this item is complete without it. Do not treat its absence as a reason to weaken either incident reproduction, which are the parts this Set actually owns.
  MEASURED AT REVIEW 2026-09-09: that grep returns NOTHING, so the flag does not exist and the expected branch is the absent one. `p8ni63` is `- Status: graduated`, handed to plan `3i0aaz` (`dirtybase-01`, `- Status: to-review`, `pending/`), whose E-04 adds the flag; so unless `3i0aaz` executes first, record ABSENT. Re-run the grep yourself rather than trusting this line.
  DO BOTH HOSTS EXPLICITLY. The runner suites are asymmetric, so four green child suites can still leave an agy-side regression. If a host cannot be demonstrated, say so plainly rather than inferring from the other. The asymmetry is the durable point; the counts are not: re-measured at review 2026-09-09 they are `tests/test_oc_runipd.py` 178 collected versus `tests/test_agy_runipd_cli.py` 60, not the 148/45 this plan was authored with, so measure your own rather than treating either pair as a criterion.
  - Depends on: none
  - Expected outcome: both incidents are survived on both hosts with no paid turns, no orphaned lanes, and no hook bypass; the startup gate's presence is DETERMINED and either exercised or recorded absent.
  - Execution state: performed

### Task group 2: record what the Set closed and did not

- [x] E-02 RECORD WHAT THE SET CLOSED AND WHAT IT DID NOT, because this Set deliberately leaves several named things open and a reader six months from now must not have to infer which. THE ARTIFACT IS A WALKTHROUGH under `.aw/records/walkthroughs/`. Do NOT invent a new record type and do NOT leave the artifact's type to the executor's judgement.
  THE FILENAME MUST NOT REUSE THIS PLAN'S id6, and the earlier instruction here to write `...-05-3v7wo6-<slug>-walkthrough.md` was WRONG: it would have put THIS PLAN's identity in the walkthrough's own identity slot, which DECISIONS.md D140 prohibits and `check.id6-identity-slot` reports as an ERROR (reproduced at review: a walkthrough named with `3v7wo6` in the slot beside this plan yields `filename identity-slot id6 3v7wo6 is another file's identity`). MINT A FRESH id6 for the walkthrough, name it `.aw/records/walkthroughs/<YYYYMMDD>-integpath-05-<new-id6>-<slug>.walkthrough.md` (the canonical facet form, not the legacy `-walkthrough.md` suffix), and express the link to this plan with the typed front-matter field `- Target-Id: 3v7wo6`, exactly as the three conforming walkthroughs in that directory already do. Note `aw check`'s name rule does NOT catch a legacy-suffix walkthrough with a foreign slot id6, so this is on you, not the linter, for the suffix half; the identity-slot half IS caught and will fail `aw check`.
  STATE THE RESIDUALS EXPLICITLY, each already named by a child: content-based narrowing of the dirty-overlap false-positive rate (declined by the maintainer 2026-09-05 as low-value relative to the ladder); path-category allowlists (REJECTED, not deferred, because they reason about who probably wrote a file rather than whether it can conflict, which is the fail-open inference `d07nz2` prohibits); `h1ksy6`, which fixes the same function but WIDENS its input set and must be reconciled with the ladder rather than stacked on it; and `a8eufb`, which would let the runner tell its own dirt from a co-worker's and is NECESSARY BUT NOT SUFFICIENT here because trailers mark commits while the motivating incident was 130+ uncommitted files.
  RECORD WHY `76gsmv` PASSED THE HOOK AS AN ANSWERED QUESTION, NOT AN OPEN ONE. Child 01 RESOLVED it on 2026-09-07 (its OQ-01, `Status: resolved`) and this record must not re-open it: the cause is the finalize journal's LIFETIME, not anything about git. `_clear_finalize_journal` deletes the journal on successful completion (`ipd_lifecycle.py:2649`) and on every rollback path, so it exists only between finalize and its consumption, and `76gsmv` merged 22 minutes before its three siblings and still had one. The backlog item's rename explanation is conclusively ruled out: all four merges are identical in diff shape (`R061`, `R063`, `R061`, `R060`). Verify against child 01's F-12/F-13 rather than restating this from here.
  NAME THE SIBLING SETS this one does NOT cover, so the boundary is legible: `integearn` covers a lane whose integration was never ATTEMPTED because the earned-integration gate refused, which is a different failure from the four here; `scopeattr` (`hyx1dg`) and `depreview` (`yf9fj9`) came from the same recovery sessions but are unrelated mechanisms. Do NOT cite `phawyy` as live work: it was RETRACTED and parked 2026-09-07 as false-premised (both blocked paths already persist the reason), so listing it as a sibling concern would propagate a withdrawn claim.
  TWO OF THE FOUR CITATIONS ABOVE HAVE ALREADY MOVED, MEASURED AT REVIEW 2026-09-09, and this is why the re-read rule below is not a formality. `32ij2j` and `xtklpd` are BOTH `- Status: superseded` under `.aw/records/plans/superseded/`, replaced by `daexj1` (`integearn-03`) and `ys1dor` (`integearn-04`), both `- Status: reviewed` under `pending/`; cite the SUCCESSORS for the live boundary and the superseded pair only as history. `hyx1dg` and `yf9fj9` are BACKLOG items, not plans (`hyx1dg` graduated, at `.aw/records/backlog/graduated/20260906-scopeattr-01-hyx1dg-...`; `yf9fj9` done, at `.aw/records/backlog/done/20260906-depreview-01-yf9fj9-...`), so do not describe either as a plan. Re-read each cited artifact's CURRENT status yourself before writing the boundary section rather than copying these; more may have moved since review.
  ALSO RECORD THE ROLLUP DEFECT THIS CHILD'S EXISTENCE IS EVIDENCE OF: that an orchestrator carrying real verification work has it discharged unperformed by the rollup, measured on `84j8d7`, and that the general fix (option (c) of `cczotj` OQ-04, separate backlog against `77tr3o` R-5) is still owed. This child is the per-Set workaround, not that fix.
  - Depends on: E-01
  - Expected outcome: a walkthrough at the named path listing every residual with its reason and every sibling Set with its boundary, with `76gsmv` recorded as ANSWERED, `phawyy` recorded as RETRACTED, and the rollup defect recorded as still open; no residual is left as an unstated assumption.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A `Kind: child` plan gets the ENFORCED `pre-transition` E/V checkpoint, and `retire_orchestrator` REFUSES to retire a child. That asymmetry with the orchestrator rollup is the entire reason this plan exists as a child rather than as two items on `cczotj`.
- Walkthroughs live at `.aw/records/walkthroughs/`. The CANONICAL name is the uniform facet form `YYYYMMDD-<setid>-NN-<id6>-<slug>.walkthrough.md`; the bare `-walkthrough.md` suffix AGENTS.md mentions is the LEGACY form, still read but not what a new file should use (`.aw/records/walkthroughs/README.md`). The artifact type is fixed by convention, not chosen by the executor.
- A WALKTHROUGH CARRIES ITS OWN id6, NEVER ITS SUBJECT PLAN'S. The identity slot is that file's own identity and must not hold another artifact's id6 (DECISIONS.md D140, enforced by `check.id6-identity-slot` in `check_engine.py:101` and `doctor.py:787`). The link to the documented plan is the typed `- Target-Id: <plan-id6>` field; all three conforming walkthroughs in the directory use it (`...hey7r7-execution.walkthrough.md`, `...5gdzyz-...`, `...zpbx7o-...`).
- WALKTHROUGHS ARE OPTIONAL IN GENERAL, but not here: E-02 makes one a required deliverable of this child, which is the exception the README's "write one only when it adds material value" allows for.
- `aw` HAS NO WALKTHROUGH-CREATING VERB (`aw walkthrough` is an invalid choice; only `aw rename walkthroughs` and `aw index`/`aw find` operate on them), so the file is written by hand and the naming rules above are the executor's responsibility, not a tool's.
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- This is a SHARED CHECKOUT. Run `aw runs` before starting, and never revert, stage, or clean another party's uncommitted work. THIS EXTENDS TO LANE BRANCHES: 29 `aw/lane/*` branches exist here, five of them `_attempt*` clusters (`03ie04`, `mm6wuz` x2, `nna8yz`, `xdr83v`) that `nuanaw` and `ys1dor` treat as live evidence. Never delete one to make an assertion pass.
- BOTH INCIDENT REPRODUCTIONS ARE SYNTHETIC BY DESIGN. Children 03 (E-07) and 04 (E-07) each reconstruct these shapes in a throwaway repository because the original lanes are historical, so this child verifies the same way. Any assertion about lane branches belongs to that throwaway repository.
- `--allow-dirty-base` DOES NOT EXIST at review HEAD (`grep -rn "allow-dirty-base\|allow_dirty_base" agent_workflows/` returns nothing), so the `p8ni63` branch of E-01 is expected to record ABSENT. The flag is owed by `3i0aaz` (`dirtybase-01`, `to-review`) E-04.
- THE BARE RUN CANNOT SEE THE SLOW SUITES. `addopts` carries `-m 'not slow'` and both declaration suites are `pytest.mark.slow`, so a bare `N passed` is not evidence about the cli declaration surface that children 03 and 04 touch. Use `make test-all` (or `-m ''`) for those two files.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | rollup vs verification | An orchestrator's E/V items are skipped by the rollup by design, so verification parked on a parent is marked complete unperformed. This child is the structural fix for this Set. | `ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']`; spec `77tr3o` R-5; `84j8d7` in `executed/` with E-01 `pending` and V-01 `pending`, retired by `run-20260906T222606Z-2987341` (`52c2872a`) |
| F-2 | HIGH | evidence sufficiency | Four green child suites cannot establish the Set's claim, because the prevented failure is an interaction across all four mechanisms. | `cczotj` gate section ("THE CLAIM THIS SET MAKES ..."); the seven-of-34 loss in `run-20260905T050043Z-639569` |
| F-3 | MEDIUM | host asymmetry | The two runner suites are unequal, so a green oc suite does not imply agy health. | measured 2026-09-07: `tests/test_oc_runipd.py` 148 collected vs `tests/test_agy_runipd_cli.py` 45 |
| F-4 | MEDIUM | baseline honesty | The suite is NOT green at HEAD, so the criterion is an EMPTY after-minus-before failure set, never a green run. The specific failure this plan inherited from `cczotj` is WRONG at review HEAD, which matters because a named-wrong baseline is worse than an unnamed one: an executor could excuse its own regression as the expected one. | `cczotj` gate section, BASELINE HONESTY; corrected by F-6 below |
| F-6 | MEDIUM | baseline honesty, measured | MEASURED 2026-09-09: `tests/test_orchestrator_retirement.py` is fully GREEN (`112 passed`), so the failure `cczotj` named no longer exists. The one bare-run failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, and it is ENVIRONMENTAL, not a code defect: it enumerates files containing the reporting-contract prose and trips on 189 files in the gitignored, untracked local `opencode-recovery/` dump. Confirmed causal by moving that directory aside, whereupon the file gives `53 passed`. It will therefore differ per machine, which is exactly why the executor must measure its OWN baseline and compare NODE IDS. | `python3 -m pytest` at review HEAD: `1 failed, 5919 passed, 3 skipped, 2 xfailed`; `git check-ignore -v opencode-recovery` -> `.gitignore:49`; `python3 -m pytest tests/test_orchestrator_retirement.py` -> `112 passed` |
| F-5 | LOW | dependency shape | All four implementing children must be `executed` before this child can verify anything, and the runner re-checks dependencies at dispatch, so declaring all four is correct rather than redundant. MEASURED 2026-09-09: 01 (`29wvmj`) and 02 (`6sb3yu`) ARE `executed`; 03 (`51vw4y`) and 04 (`rl67b0`) are `reviewed` and not yet approved, so this child is currently `dependency-blocked` by construction, which is the intended behavior and not a defect. | `- Item-Dependencies:` above; AGENTS.md (dependencies re-checked at dispatch); the four plans' `- Status:` lines |
| F-7 | HIGH | walkthrough identity | The walkthrough filename E-02 originally mandated put THIS PLAN's id6 in the walkthrough's own identity slot, which DECISIONS.md D140 prohibits and `check.id6-identity-slot` reports as an error, so following the plan literally produced a record that fails `aw check`. It also specified the LEGACY `-walkthrough.md` suffix rather than the canonical `.walkthrough.md` facet. | reproduced at review: a walkthrough named `...-05-3v7wo6-...` beside this plan yields `filename identity-slot id6 3v7wo6 is another file's identity`; `check_engine.py:101`; DECISIONS.md:2465; `.aw/records/walkthroughs/README.md:5` |
| F-8 | HIGH | reproduction hygiene | V-01's `git branch --list 'aw/lane/<id6>*'` assertion, read literally against `mm6wuz` in this checkout, fails on pre-existing history: `aw/lane/mm6wuz`, `_attempt2` and `_attempt3` all exist here among 29 lane branches. The only ways to satisfy it as written are to run it in the synthetic repository (correct) or to delete another party's preserved branches (forbidden). | `git branch --list 'aw/lane/mm6wuz*'` returns three branches; children 03/04 E-07 both reconstruct synthetically; `nuanaw` cites those clusters as evidence |
| F-9 | MEDIUM | evidence completeness | The validation demanded only the BARE suite, which deselects the two `slow` declaration suites; children 03 and 04 add runner flags and a cli leaf, so the bare run cannot see the surface most likely to regress. Child 04's own gate already requires the `-m ''` run and names the pre-existing five-leaf failure. | `pyproject.toml` `addopts` `-m 'not slow'`; child 04 E-07's slow-suite paragraph |

## Proposed changes (ordered, validatable)

1. After children 01 through 04 are `executed`, reproduce incident one (deferral then integration, no paid turn, no bypass) on both hosts, in a throwaway repository, and paste the evidence.
2. Reproduce incident two (resume integrates the existing lane, no `_attempt2` branch) on both hosts, asserting on the SYNTHETIC id6 inside that throwaway repository and never on `mm6wuz` here.
3. Run `grep -rn "allow-dirty-base\|allow_dirty_base" agent_workflows/` to determine whether `p8ni63` has landed; exercise the gate if so, record its absence plainly if not.
4. Measure your OWN before-baseline, run the bare suite after, and show the AFTER-minus-BEFORE failure set empty by node id; run the two `slow` declaration suites separately under `-m ''`.
5. Mint a FRESH id6 and write the walkthrough at `...-integpath-05-<new-id6>-<slug>.walkthrough.md` with `- Target-Id: 3v7wo6`, covering every residual, every sibling boundary read at execution time, and the still-open rollup defect.

## Deferred / out of scope (with reason)

- The startup dirty-base gate (`p8ni63`): prevention rather than recovery, not a child of this Set. Verified only if it happens to have landed, which at review it has not. CORRECTION measured 2026-09-09: the item is no longer OPEN as this plan said, it is `graduated` to plan `3i0aaz` (`dirtybase-01`, `to-review`), whose E-04 adds `--allow-dirty-base`. Still out of scope either way.
- The general rollup fix (option (c) of `cczotj` OQ-04): owed as separate backlog against `77tr3o` R-5. This child is a per-Set workaround, not the durable fix.
- Whether `84j8d7` needs a corrective IPD for its unperformed E-01/V-01: a maintainer decision, recorded in E-02's walkthrough rather than acted on here.
- `h1ksy6` (widens `dirty_tree_overlap`'s input set): must be reconciled with the ladder, not stacked on it; recorded as a residual, not implemented.

## Scope check

- Over-scope: none. This child authors no product code.
- Under-scope: it does NOT re-test each child's own mechanism (each child owns its unit coverage) and it does NOT close any backlog item. The three items the Set graduated from are `rnl3b7` (already `done`, closed by child 01), `5wdoze` (`graduated`, carried by children 02 and 03) and `yocdq4` (`graduated`, carried by child 04); this child closes none of them, and the word "respectively" earlier misdescribed a three-items-to-four-children mapping.
- Scope-Paths justification: `.aw/records/walkthroughs/` holds E-02's one deliverable; the plan file itself is named exactly so the lifecycle's own edits to this plan are declared rather than showing as an out-of-scope path. No product file is declared, because none is touched.

## Required tests / validation

Both incident reproductions on BOTH hosts, with pasted terminal output rather than summary. Plus the bare `python3 -m pytest` summary line, judged on the DELTA from a self-measured baseline, comparing NODE IDS rather than counts.

MEASURE YOUR OWN BEFORE-BASELINE AND DO NOT INHERIT THIS PLAN'S. At review HEAD the bare run was `1 failed, 5919 passed, 3 skipped, 2 xfailed`, the single failure being the environmental `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` (F-6), and `tests/test_orchestrator_retirement.py` was GREEN at `112 passed`, contradicting the failure this plan inherited from `cczotj`. Both figures are machine- and time-dependent, so the ONLY criterion is that your AFTER failure set minus your OWN BEFORE set is empty.

ALSO RUN THE SLOW SUITES, which a bare run CANNOT SEE, because `addopts` carries `-m 'not slow'` and both `tests/test_cli_conformance_matrix.py` and `tests/test_command_surface_declarations.py` are `pytest.mark.slow`. Children 03 and 04 add runner flags and a cli leaf, so those are exactly the suites that would catch an undeclared leaf they missed. Run `make test-all` (or `-m ''`) for them and paste that result SEPARATELY from the bare summary. Child 04's own gate records a KNOWN pre-existing slow failure (`test_zero_undeclared_parser_leaves`, five undeclared `oc profile *` leaves): re-measure it, and treat only GROWTH of that set as a regression.

VALIDATE IN THE REAL CHECKOUT, not only in a worktree: `tests/test_run_viewer.py` reads the gitignored `.aw/records/runs/` and fails in a bare worktree while passing here, so a green run elsewhere proves nothing.

## Spec / documentation sync

N/A for specs: this child changes no behavior and no contract. The walkthrough E-02 produces IS the documentation deliverable. Write no em or en dashes in that walkthrough, which is user-facing prose.

## Open questions

### OQ-01: Should this child also assert the startup dirty-base gate once `p8ni63` lands?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as authored. E-01 already handles both branches: exercise the gate if `--allow-dirty-base` exists, record its absence plainly if not. No further decision is needed, and the Set's completion criteria deliberately do not depend on it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste BOTH incidents reproduced and survived, for BOTH hosts. Incident one: a lane refused on dirty overlap, DEFERRED, then INTEGRATED after the dirt cleared, with the merge commit on main and NO agent turn spent. Incident two: an item with a verified lane resumed, showing the FIRST lane integrated and `git branch --list 'aw/lane/<id6>*'` containing NO `_attempt2`; state the SYNTHETIC id6 you asserted on and paste the path of the throwaway repository, because running that check against `mm6wuz` in this checkout is a FAILED validation (three such branches pre-exist here and are another party's preserved work). For both, paste evidence that NO `--no-verify` was used anywhere. Paste the exact output of `grep -rn "allow-dirty-base\|allow_dirty_base" agent_workflows/` to establish whether `p8ni63` had landed and, if so, paste the startup gate refusing a dirty base and honoring its override; empty output means ABSENT, which is the expected result and completes this item without it, since it is not a child of this Set. If a host could not be demonstrated, SAY SO PLAINLY; an inferred agy result is a FAILED validation.
    Paste the BARE `python3 -m pytest` summary line (the `N passed` line) TWICE, once for your own BEFORE baseline and once AFTER, and show the AFTER-minus-BEFORE failure set EMPTY by NODE ID. Paste the slow-suite run (`make test-all` or `-m ''`) SEPARATELY for `tests/test_cli_conformance_matrix.py` and `tests/test_command_surface_declarations.py`, with the undeclared-parser-leaf set no larger than your measured baseline's. A single pasted summary line, or a claim of green without a self-measured baseline, is a FAILED validation.
  - Observed evidence: PASS. Both measured incidents reproduced END TO END and survived on BOTH hosts, 45 assertions, 0 failures, executed at HEAD `36129255`. The startup dirty-base gate is PRESENT at this HEAD (contradicting this plan's review-time prediction of ABSENT, see D1 in the decisions register) and was therefore EXERCISED rather than recorded absent.

    THE HARNESS DRIVES EACH HOST'S OWN ADAPTER, not the shared functions the children's tests bind. Children 03/04 `MeasuredIncidentsAreSurvivedTests` calls `integrate_lane_branch` directly with a STUBBED suite; this drives `oc_runipd.retry_deferred_integrations` / `agy_runipd.retry_deferred_integrations` (incident one) and `oc_runipd._integrate_stranded_lanes` / `agy_runipd._integrate_stranded_lanes` (incident two), in throwaway repositories carrying a REAL passing test so the gate's own `run_suite_check` runs an ACTUAL suite. That difference was load-bearing: with no test file present pytest exits 5 and the gate fails CLOSED (measured on the first attempt: `integration_failed_combined_red ... suite FAILED with exit 5`), which would have proven only that the gate fails closed. Harness at `.aw/state/tmp/3v7wo6/verify_whole_set.py` (gitignored scratch; this child authors no product code).

    SYNTHETIC ids ASSERTED ON: `aa0001` (incident one) and `bb0002` (incident two), each in its own throwaway repository under `/tmp` (paths printed per case below). The branch assertion was NOT run against `mm6wuz` in this checkout: `git branch --list 'aw/lane/mm6wuz*'` here returns `aw/lane/mm6wuz`, `aw/lane/mm6wuz_attempt2`, `aw/lane/mm6wuz_attempt3`, another party's preserved work in a shared checkout. No lane branch was deleted.

    ```
    $ python3 .aw/state/tmp/3v7wo6/verify_whole_set.py
    ================================================================================================
    integpath child 05 (3v7wo6) E-01: WHOLE-SET VERIFICATION, both incidents, BOTH hosts
    ================================================================================================

    ------------------------------------------------------------------------------------------------
    HOST: oc (agent_workflows.oc_runipd)
    ------------------------------------------------------------------------------------------------

      INCIDENT ONE on host 'oc': dirty overlap -> DEFER -> integrate when dirt clears
        throwaway repository: /tmp/tmpqmhlvsw0/repo
        synthetic id6: aa0001   lane branch: aw/lane/aa0001
        dirt in main: 'M src/shared.txt'
        attempt 1 records: [{'id6': 'aa0001', 'outcome': 'deferred', 'detail': 'integration DEFERRED (attempt 1 of 11): main holds un-owned dirty paths overlapping this change, which is transient by nature, so the lane is preserved and integration is re-attempted through the full revalidate gate once other work advances'}]
        [PASS] oc/incident-1: attempt 1 DEFERS rather than going terminal
        [PASS] oc/incident-1: item status is 'integration-deferred'
        [PASS] oc/incident-1: that status is NOT terminal (a re-attempt remains possible)
        [PASS] oc/incident-1: the verified lane branch is PRESERVED after the refusal
        [PASS] oc/incident-1: main is UNTOUCHED (nothing integrated over the contaminated base)
        (the co-worker's dirt clears; NO agent turn is spent)
      + IPD aa0001 integrated to main on a deferred re-attempt (fast-forward integrated to main)
        attempt 2 records: [{'id6': 'aa0001', 'outcome': 'integrated', 'detail': 'fast-forward integrated to main'}]
        [PASS] oc/incident-1: attempt 2 INTEGRATES once the dirt clears
        [PASS] oc/incident-1: the item reaches 'executed'
        [PASS] oc/incident-1: the lane's WORK is on main (not lost)
        [PASS] oc/incident-1: the finalized plan is on main in executed/
        [PASS] oc/incident-1: NO lane was orphaned into an _attempt branch
        [PASS] oc/incident-1: NO additional agent turn was spent (attempt records still 1)
        [PASS] oc/incident-1: no commit records a --no-verify bypass

      INCIDENT TWO on host 'oc': resume integrates the FIRST lane, allocates no second
        throwaway repository: /tmp/tmpyh9y1f_m/repo
        synthetic id6: bb0002   lane branch: aw/lane/bb0002
        pre-fix probe: allocate_worktree -> aw/lane/bb0002_attempt2 (displaced aw/lane/bb0002)
        [PASS] oc/incident-2: the PRE-FIX path really does allocate an _attempt2 lane
        [PASS] oc/incident-2: and it displaces the FIRST, verified lane
      integrating already-verified lane aw/lane/bb0002 for IPD bb0002 (no agent turn; runs the suite in /tmp/tmpyh9y1f_m/repo)
      + IPD bb0002 integrated to main from its existing lane aw/lane/bb0002 with NO agent turn (fast-forward integrated to main)
        resume stranded-lane pass records: [{'id6': 'bb0002', 'branch': 'aw/lane/bb0002', 'outcome': 'integrated', 'detail': 'fast-forward integrated to main'}]
        [PASS] oc/incident-2: the resume INTEGRATES the existing lane
        [PASS] oc/incident-2: the item reaches 'executed' with no turn dispatched
        [PASS] oc/incident-2: the FIRST lane's verified work is on main
        git branch --list 'aw/lane/bb0002*' -> '+ aw/lane/bb0002'
        [PASS] oc/incident-2: git branch --list 'aw/lane/bb0002*' shows NO _attempt2
        [PASS] oc/incident-2: NO agent turn was spent recovering it
        [PASS] oc/incident-2: no commit records a --no-verify bypass

    ------------------------------------------------------------------------------------------------
    HOST: agy (agent_workflows.agy_runipd)
    ------------------------------------------------------------------------------------------------

      INCIDENT ONE on host 'agy': dirty overlap -> DEFER -> integrate when dirt clears
        throwaway repository: /tmp/tmpn0tv1xhx/repo
        synthetic id6: aa0001   lane branch: aw/lane/aa0001
        dirt in main: 'M src/shared.txt'
        attempt 1 records: [{'id6': 'aa0001', 'outcome': 'deferred', 'detail': 'integration DEFERRED (attempt 1 of 11): main holds un-owned dirty paths overlapping this change, which is transient by nature, so the lane is preserved and integration is re-attempted through the full revalidate gate once other work advances'}]
        [PASS] agy/incident-1: attempt 1 DEFERS rather than going terminal
        [PASS] agy/incident-1: item status is 'integration-deferred'
        [PASS] agy/incident-1: that status is NOT terminal (a re-attempt remains possible)
        [PASS] agy/incident-1: the verified lane branch is PRESERVED after the refusal
        [PASS] agy/incident-1: main is UNTOUCHED (nothing integrated over the contaminated base)
        (the co-worker's dirt clears; NO agent turn is spent)
      + IPD aa0001 integrated to main on a deferred re-attempt (fast-forward integrated to main)
        attempt 2 records: [{'id6': 'aa0001', 'outcome': 'integrated', 'detail': 'fast-forward integrated to main'}]
        [PASS] agy/incident-1: attempt 2 INTEGRATES once the dirt clears
        [PASS] agy/incident-1: the item reaches 'executed'
        [PASS] agy/incident-1: the lane's WORK is on main (not lost)
        [PASS] agy/incident-1: the finalized plan is on main in executed/
        [PASS] agy/incident-1: NO lane was orphaned into an _attempt branch
        [PASS] agy/incident-1: NO additional agent turn was spent (attempt records still 1)
        [PASS] agy/incident-1: no commit records a --no-verify bypass

      INCIDENT TWO on host 'agy': resume integrates the FIRST lane, allocates no second
        throwaway repository: /tmp/tmpu5z7s6sj/repo
        synthetic id6: bb0002   lane branch: aw/lane/bb0002
        pre-fix probe: allocate_worktree -> aw/lane/bb0002_attempt2 (displaced aw/lane/bb0002)
        [PASS] agy/incident-2: the PRE-FIX path really does allocate an _attempt2 lane
        [PASS] agy/incident-2: and it displaces the FIRST, verified lane
      integrating already-verified lane aw/lane/bb0002 for IPD bb0002 (no agent turn; runs the suite in /tmp/tmpu5z7s6sj/repo)
      + IPD bb0002 integrated to main from its existing lane aw/lane/bb0002 with NO agent turn (fast-forward integrated to main)
        resume stranded-lane pass records: [{'id6': 'bb0002', 'branch': 'aw/lane/bb0002', 'outcome': 'integrated', 'detail': 'fast-forward integrated to main'}]
        [PASS] agy/incident-2: the resume INTEGRATES the existing lane
        [PASS] agy/incident-2: the item reaches 'executed' with no turn dispatched
        [PASS] agy/incident-2: the FIRST lane's verified work is on main
        git branch --list 'aw/lane/bb0002*' -> '+ aw/lane/bb0002'
        [PASS] agy/incident-2: git branch --list 'aw/lane/bb0002*' shows NO _attempt2
        [PASS] agy/incident-2: NO agent turn was spent recovering it
        [PASS] agy/incident-2: no commit records a --no-verify bypass

      STARTUP DIRTY-BASE GATE: present at HEAD, so it is EXERCISED rather than recorded absent
        git status --porcelain --untracked-files=no -> 'M src/shared.txt'
        evaluate_clean_base(shared_tree=True).clean=False refuses=True
        verdict without consent: refuse
        [PASS] startup-gate: a dirty SHARED base is REFUSED without consent
        verdict with --allow-dirty-base: consented
        [PASS] startup-gate: --allow-dirty-base turns the refusal into recorded CONSENT
        [PASS] startup-gate: consent explicitly does NOT waive the integration-time refusal
        clean tree porcelain -> ''; clean=True
        [PASS] startup-gate: a clean base proceeds (the gate does not over-refuse)
        isolated-path verdict on the SAME dirt: warn
        [PASS] startup-gate: the ISOLATED path REPORTS (warn) rather than refusing, per d7qoxv

    ================================================================================================
    NOTE: oc/incident-1 merge subject: lifecycle(aa0001): finalize -> executed
    NOTE: agy/incident-1 merge subject: lifecycle(aa0001): finalize -> executed
    RESULT: ALL ASSERTIONS PASSED on both hosts for both incidents, plus the startup gate.
    ```

    BOTH HOSTS WERE DEMONSTRATED. Nothing is inferred from the other host: each of the four cases above ran against its own module (`agent_workflows.oc_runipd` and `agent_workflows.agy_runipd`, printed in the host banners).

    NO `--no-verify` ANYWHERE. Asserted per case on the actual resulting history (`git log --format=%s%n%b -3` contains no `no-verify`), and the runner's integration path uses `git merge --ff-only` with a controlled `--no-ff` fallback, neither of which passes it.

    THE STARTUP GATE HAS LANDED, so the ABSENT branch this plan predicted is the wrong one. The plan's own grep, re-run verbatim at HEAD `36129255`:
    ```
    $ grep -rn "allow-dirty-base\|allow_dirty_base" agent_workflows/
    agent_workflows/agy_runipd.py:3352:            allow_dirty_base=bool(
    agent_workflows/agy_runipd.py:3353:                state.get("options", {}).get("allow_dirty_base", False)
    agent_workflows/oc_runipd.py:6562:            allow_dirty_base=bool(
    agent_workflows/oc_runipd.py:6563:                state.get("options", {}).get("allow_dirty_base", False)
    agent_workflows/runner_shared.py:5107:#: `--allow-dirty-base` JOINED with dirtybase Order 01 (`3i0aaz`), which added the dirty-base refusal
    agent_workflows/runner_shared.py:5232:        flag="--allow-dirty-base",
    agent_workflows/runner_shared.py:5233:        dest="allow_dirty_base",
    agent_workflows/runner_shared.py:5702:#: signal value. Consent means the OPERATOR passed `--allow-dirty-base` over a refusal that still
    agent_workflows/runner_shared.py:5739:    allow_dirty_base: bool = False,
    agent_workflows/runner_shared.py:5746:    path REPORTS). This adds exactly one thing: `--allow-dirty-base` turns a REFUSAL into a recorded
    agent_workflows/runner_shared.py:5756:    `--allow-dirty-base` exists to override a REFUSAL; reporting `consented` where nothing was refused
    agent_workflows/runner_shared.py:5780:    if allow_dirty_base:
    agent_workflows/runner_shared.py:5785:                "--allow-dirty-base: proceeding over "
    ```
    The owing plan is now terminal: `3i0aaz` (`dirtybase-01`) is `- Status: executed` at `.aw/records/plans/executed/20260907-dirtybase-01-3i0aaz-guard-the-ungated-dirty-base-cases-nna8yz-leaves-open-untrac.ipd.md`. Its refusal, its override, its non-over-refusal, and the isolated-path `warn` split are the four `startup-gate` assertions above.

    ALL FOUR IMPLEMENTING CHILDREN ARE `executed` ON DISK, so this child was dispatchable rather than `dependency-blocked` (F-5 predicted 03/04 would still be `reviewed`):
    ```
    $ for f in .aw/records/plans/executed/20260906-integpath-0*.ipd.md; do printf "%s  %s\n" "$(grep -m1 '^- Id:' "$f" | cut -d' ' -f3)" "$(grep -m1 '^- Status:' "$f" | cut -d' ' -f3)"; done
    29wvmj  executed
    6sb3yu  executed
    51vw4y  executed
    rl67b0  executed
    ```
    (The id6 and status are printed on ONE line deliberately. Quoting each child's raw `- Status:` line here would embed a bare `- Status: executed` in this plan's text, which `executed_transition_gate` reads as THIS plan gaining a terminal status: it strips indentation and matches the whole line, so a quoted line inside a fenced block is indistinguishable from a real one. Measured 2026-09-18: it refused this very commit. Filed as backlog `vnzm27`. The evidence is identical; only the format avoids tripping a gate that must NOT be bypassed.)

    THE BARE SUITE, AND THE BASELINE CORRECTION THAT MATTERS. A bare run INSIDE this runner turn reports 32 failures, and 31 of them are caused by the RUNNER'S OWN ENVIRONMENT, not by the tree (decision D2; filed as backlog `1uq1cu`). The driver exports `AW_EXECUTION_ROLE=worker`, and `tests/test_worker_role_refusal.py:225` asserts that variable is not `worker`; tests that spawn a driver subprocess inherit the marking and `driver_begin` refuses inside the fixture. Both measurements below therefore unset that ONE variable, so BEFORE and AFTER are like-for-like, and the worker-marked reading is reported too rather than hidden.
    ```
    $ python3 -m pytest                                   # worker-marked, as the runner launched me
    32 failed, 7875 passed, 3 skipped, 2 xfailed in 251.21s (0:04:11)

    $ env -u AW_EXECUTION_ROLE python3 -m pytest          # BEFORE baseline (like-for-like)
    1 failed, 7906 passed, 3 skipped, 2 xfailed in 300.74s (0:05:00)

    $ env -u AW_EXECUTION_ROLE python3 -m pytest          # AFTER
    1 failed, 7906 passed, 3 skipped, 2 xfailed in 233.43s (0:03:53)
    ```
    AFTER-MINUS-BEFORE FAILURE SET, BY NODE ID: EMPTY. Both runs fail exactly one node, the same one:
    ```
    BEFORE: FAILED tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130
    AFTER:  FAILED tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130
    ```
    That one is a load-dependent flake, not a code defect, and it is a `subprocess.TimeoutExpired` under `-n auto` parallelism. Proven by running it alone:
    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest "tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130" -o addopts="-q -p no:randomly"
    1 passed in 0.75s
    ```
    This child authors no product code, so an empty delta is expected rather than impressive; it is pasted because the plan requires the measurement, and because measuring it is what surfaced `1uq1cu`.

    THE TWO SLOW DECLARATION SUITES, RUN SEPARATELY under `-m ''` because `addopts` carries `-m 'not slow'` and a bare run deselects them:
    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_cli_conformance_matrix.py tests/test_command_surface_declarations.py -m ""
    FAILED tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_undeclared_parser_leaves
    FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_every_declared_leaf_gets_a_full_scenario_row_set
    FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_no_undeclared_parser_leaves
    3 failed, 22 passed in 376.34s (0:06:16)
    ```
    THE UNDECLARED-LEAF SET DID NOT GROW. All three failures name the SAME five pre-existing entries child 04's gate already records, and this child adds no cli leaf:
    ```
    E       AssertionError: 5 != 0 : Found undeclared parser leaves: {'oc profile list', 'oc profile show', 'oc profile add', 'oc profile default', 'oc profile remove'}
    E       - ['oc profile add',
    E       -  'oc profile default',
    E       -  'oc profile list',
    E       -  'oc profile remove',
    E       -  'oc profile show'] : undeclared leaves present
    ```
    VALIDATED IN THE REAL CHECKOUT rather than only in a bare worktree: this lane is a full checkout whose `.aw/records/runs/` resolves, and `tests/test_run_viewer.py` is inside the green portion of both bare runs above.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the walkthrough's path and its residuals section verbatim. Confirm by quotation that it names all four residuals (content-based narrowing as DECLINED, path-category allowlists as REJECTED, `h1ksy6` as needing reconciliation, `a8eufb` as necessary-but-not-sufficient), records `76gsmv` as ANSWERED with the journal-lifetime cause, records `phawyy` as RETRACTED, and records the rollup defect as still open with `84j8d7` named. Paste the CURRENT status line of every sibling artifact you cite, read at execution time rather than copied from this plan, since several moved after authoring. A walkthrough that restates the rename explanation for `76gsmv` is a FAILED validation.
    ALSO PASTE the walkthrough's `- Target-Id: 3v7wo6` line and a clean `aw check --agent` for the identity-slot rule (`aw check --agent 2>&1 | grep id6-identity-slot` returning nothing). A walkthrough whose filename identity slot holds `3v7wo6` violates DECISIONS.md D140 and is a FAILED validation however good its content, so verify the name before the prose.
  - Observed evidence: PASS. The walkthrough is at:

    `.aw/records/walkthroughs/20260918-integpath-05-u8tiox-lane-to-main-integration-whole-set-verification-and-residuals.walkthrough.md`

    THE NAME WAS VERIFIED BEFORE THE PROSE, as this item demands. The identity slot holds `u8tiox`, a FRESHLY MINTED id6, not `3v7wo6`. Minted by collecting every id6 in `.aw/` (1262 known) and calling `artifact_core.generate_id6` against that set; `grep -rn "u8tiox" .aw/` returned nothing before the file was written. The canonical `.walkthrough.md` facet is used, not the legacy `-walkthrough.md` suffix. Its front matter:
    ```
    $ head -8 .aw/records/walkthroughs/20260918-integpath-05-u8tiox-lane-to-main-integration-whole-set-verification-and-residuals.walkthrough.md
    # Walkthrough: `integpath` whole-Set verification and residuals

    - Date: 2026-09-18
    - Kind: whole-Set verification and residuals record
    - Id: u8tiox
    - Target-Id: 3v7wo6
    - Author: opencode its_direct/pt3-claude-opus-5-1m-us
    - Verified at: HEAD `36129255`
    ```
    THE IDENTITY-SLOT RULE IS CLEAN, and so is every other rule against this file:
    ```
    $ aw check --agent 2>&1 | grep id6-identity-slot
    (no output)

    # parsed from the same aw.agent/v1 record, since `aw check` emits one JSON line:
    id6-identity-slot findings: 0
    findings on MY walkthrough: 0
    total repository findings: 385   (386 before this file was corrected; see below)
    ```
    ONE FINDING WAS FOUND AND FIXED HERE RATHER THAN SHIPPED. The first draft declared `- Set: integpath`, and `aw check` reported `check.setid-collision` (severity error, invariant I-09): `setid integpath conflicts with .aw/records/plans/pending/20260907-integpath-05-3v7wo6-...ipd.md (different type)`. The cause is real and is not this file's fault: `check_engine.py:894-916` treats a setid as owned by ONE record type, and `_iter_type_files` (`:522`) skips retired files, so a plan in `executed/` is invisible to the rule. A walkthrough declaring its Set is therefore CLEAN once its plan finalizes and DIRTY while the plan sits in `pending/`, which is why the existing walkthroughs that DO carry `- Set:` (for example `20260831-locksafe-01-5gdzyz-...`) do not trip it. The field was omitted with the reason recorded in the file, and the defect filed as backlog `sovauj` rather than left as a silent workaround.

    ALL FOUR RESIDUALS ARE NAMED WITH THEIR REASONS, quoted verbatim from the file's `## Residuals: what this Set deliberately did NOT close` section:
    ```
    1. CONTENT-BASED NARROWING of the dirty-overlap false-positive rate, meaning skipping the refusal
       when main's dirty version of a path is byte-identical to what the merge would produce. DECLINED by
       the maintainer on 2026-09-05 as low-value relative to the ladder. Still declined; no owner, and
       that is intentional rather than an oversight.

    2. PATH-CATEGORY ALLOWLISTS, of the "docs are safe" or "review records are harmless" kind. REJECTED,
       not deferred, and the distinction matters: they reason about who probably wrote a file rather than
       whether it can conflict, which is the fail-open inference `d07nz2` prohibits. If the false
       positive rate is ever narrowed, narrow on CONTENT, never on category. A future reader who mistakes
       this for a deferral will reintroduce a rejected design.

    3. `h1ksy6`, which fixes the same function the ladder guards but WIDENS its input set, making refusal
       MORE reachable. It must be RECONCILED with the ladder rather than stacked on it. MOVED SINCE
       REVIEW: it is now `- Status: graduated` (2026-09-08) to plan `fujm0y` (`mergedirty-01`), which is
       `- Status: approved` in `pending/`. So the reconciliation now has an owner and is live work rather
       than an unowned note.

    4. `a8eufb`, which would let the runner tell its own dirt from a co-worker's. NECESSARY BUT NOT
       SUFFICIENT here, by construction: trailers mark COMMITS, while the motivating incident's dirt was
       130+ UNCOMMITTED working-tree files carrying no trailer at all. MOVED SINCE REVIEW: it is now
       `- Status: graduated` (2026-09-08) to plan `wao266` (`runtrailwire-01`, `- Status: approved`),
       narrowed to step (1) only.
    ```
    `76gsmv` IS RECORDED AS ANSWERED WITH THE JOURNAL-LIFETIME CAUSE, and the rename explanation is NOT restated. The walkthrough's section is titled "`76gsmv` is an ANSWERED question, not an open one" and gives the journal's lifetime as the cause, verified against child 01's F-12/F-13 rather than copied: `_clear_finalize_journal` is called on the success path at `ipd_lifecycle.py:3988` (read at HEAD, confirming the deletion-on-completion claim), and the four merges' diff shapes were RE-MEASURED here rather than quoted:
    ```
    $ for c in 7e157380 0d80fef4 6608c877 eaf19dd0; do printf "%s " "$c"; git diff --name-status -M "$c^1" "$c" | grep -o "^R[0-9]*" | head -1; done
    7e157380 R061
    0d80fef4 R063
    6608c877 R061
    eaf19dd0 R060
    ```
    Four identical rename shapes with two different hook outcomes cannot be explained by the shape, so the rename explanation is conclusively ruled out, exactly as child 01's F-13 found.

    `phawyy` IS RECORDED AS RETRACTED, not as a live sibling concern: `- Status: parked` at `.aw/records/backlog/parked/20260906-depreview-01-phawyy-dependency-blocked-reason-not-persisted.backlog.md`.

    THE ROLLUP DEFECT IS RECORDED AS STILL OPEN WITH `84j8d7` NAMED, and it was re-verified at this HEAD rather than inherited:
    ```
    $ grep -n "Execution state\|Result:" .aw/records/plans/executed/20260906-orchretire-00-84j8d7-runner-owned-orchestrator-retirement-adopt-spec-77tr3o.ipd.md
    43:  - Execution state: pending
    170:  - Result: pending
    $ grep -n '^- Status:' .aw/records/plans/executed/20260906-orchretire-00-84j8d7-...ipd.md | head -1 | cut -d' ' -f3
    executed
    ```
    So an orchestrator carrying real verification work still sits in `executed/` with its E-01 unperformed and its V-01 unverified. The general fix (option (c) of `cczotj` OQ-04, separate backlog against spec `77tr3o` R-5) is recorded as still owed, and this child as the per-Set workaround.

    EVERY CITED SIBLING'S CURRENT STATUS, read at execution time rather than copied from this plan. Five had moved since review, which is why the plan required this re-read:
    ```
    76gsmv  - Status: executed    .aw/records/plans/executed/20260904-revsweep-01-76gsmv-...ipd.md
    84j8d7  - Status: executed    .aw/records/plans/executed/20260906-orchretire-00-84j8d7-...ipd.md
    3i0aaz  - Status: executed    .aw/records/plans/executed/20260907-dirtybase-01-3i0aaz-...ipd.md   (plan said to-review)
    daexj1  - Status: approved    .aw/records/plans/pending/20260908-integearn-03-daexj1-...ipd.md    (plan said reviewed)
    ys1dor  - Status: approved    .aw/records/plans/pending/20260908-integearn-04-ys1dor-...ipd.md    (plan said reviewed)
    9lyg5h  - Status: approved    .aw/records/plans/pending/20260908-integearn-05-9lyg5h-...ipd.md    (not named by this plan)
    32ij2j  - Status: superseded  .aw/records/plans/superseded/20260906-integearn-01-32ij2j-...ipd.md
    xtklpd  - Status: superseded  .aw/records/plans/superseded/20260906-integearn-02-xtklpd-...ipd.md
    h1ksy6  - Status: graduated   .aw/records/backlog/graduated/20260829-mergedirty-01-h1ksy6-...backlog.md  (plan implied unowned)
    fujm0y  - Status: approved    .aw/records/plans/pending/20260907-mergedirty-01-fujm0y-...ipd.md
    a8eufb  - Status: graduated   .aw/records/backlog/graduated/20260830-scopeattrib-01-a8eufb-...backlog.md (plan implied unowned)
    wao266  - Status: approved    .aw/records/plans/pending/20260908-runtrailwire-01-wao266-...ipd.md
    p8ni63  - Status: graduated   .aw/records/backlog/graduated/20260905-integdefer-01-p8ni63-...backlog.md
    phawyy  - Status: parked      .aw/records/backlog/parked/20260906-depreview-01-phawyy-...backlog.md
    hyx1dg  - Status: graduated   .aw/records/backlog/graduated/20260906-scopeattr-01-hyx1dg-...backlog.md   (BACKLOG, not a plan)
    yf9fj9  - Status: done        .aw/records/backlog/done/20260906-depreview-01-yf9fj9-...backlog.md         (BACKLOG, not a plan)
    ```
    The walkthrough describes `hyx1dg` and `yf9fj9` as backlog items rather than plans, and cites `daexj1`/`ys1dor`/`9lyg5h` for the live `integearn` boundary with `32ij2j`/`xtklpd` named only as superseded history.

    NO EM OR EN DASHES in the walkthrough, which is user-facing prose (`grep -n "—\|–"` returns nothing), and `aw sanitize --agent` reports nothing against it.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). This child is dispatchable only after children 01 through 04 are `executed` on disk; the runner re-checks `- Item-Dependencies:` at dispatch, so an unmet edge marks this item `dependency-blocked` and continues rather than failing the run.

THIS CHILD IS THE SET'S EVIDENCE, AND THE E/V CHECKPOINT ON IT IS ENFORCED. That is the whole point of its existence: the same two items on the orchestrator would have been discharged by the rollup unperformed. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and BOTH `V-*` items carry concrete pasted evidence.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. If an incident cannot be reproduced, that is a FINDING to report, not a validation to soften.

DO NOT WEAKEN A REFUSAL TO MAKE A REPRODUCTION SUCCEED. Every refusal on this path exists because integrating over a contaminated base can clobber or half-finish real work. If a reproduction only succeeds once a refusal is relaxed, the Set has failed its claim and that is the honest report.

AND DO NOT DELETE A LANE BRANCH TO MAKE AN ASSERTION PASS. This is the same rule aimed at the one shortcut this child's own evidence invites: `aw/lane/mm6wuz`, `_attempt2` and `_attempt3` exist in this checkout as historical evidence other work depends on, so incident two is asserted inside the throwaway repository on its own synthetic id6. Removing preserved lanes here would fabricate a pass and destroy another party's work in a shared checkout.

THE WALKTHROUGH'S NAME IS PART OF THE DELIVERABLE. Mint a fresh id6 for it, use the canonical `.walkthrough.md` facet, and link this plan with `- Target-Id: 3v7wo6`. Putting `3v7wo6` in the walkthrough's identity slot violates DECISIONS.md D140 and fails `aw check`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT: run `aw runs` before starting.

Closes no backlog item. `5wdoze` on this plan's `- From-Backlog:` records provenance only; child `51vw4y` closes it.

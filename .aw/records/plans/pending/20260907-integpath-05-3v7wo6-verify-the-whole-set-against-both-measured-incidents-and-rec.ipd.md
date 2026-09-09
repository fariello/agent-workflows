# IPD: Verify the whole Set against both measured incidents and record the residuals

- Date: 2026-09-07
- Kind: child
- Concern: The `integpath` Set's central claim is that verified work stops getting lost on the lane-to-main path. Four green child suites do NOT establish it: each child tests its own mechanism, while the failure the Set exists to prevent is an INTERACTION (a refusal that is terminal, times a recovery route the hook blocks, times a resume that orphans the lane). So the whole-Set verification is real execution work that somebody must perform.
  IT CANNOT LIVE ON THE ORCHESTRATOR, WHICH IS WHY THIS CHILD EXISTS. The runner-owned rollup deliberately OMITS the `pre-transition` E/V checkpoint for an orchestrator (`ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']`, spec `77tr3o` R-5 shape (b)) on the premise that an orchestrator's items are performed by NOBODY. Work parked on a parent is therefore marked complete having never been performed OR verified. MEASURED, not predicted: orchestrator `84j8d7` sits in `executed/` today carrying `Execution state: pending` on its E-01 and `Result: pending` on its V-01, rollup-retired by run `run-20260906T222606Z-2987341` (commit `52c2872a`), despite carrying an explicit forceful warning against exactly that. A warning addressed to a human does not constrain a code path (`k1nity`: informing an agent is necessary and not sufficient).
  THIS SHAPE MAKES IT UNSKIPPABLE. A `Kind: child` plan gets the enforced E/V checkpoint and `retire_orchestrator` REFUSES to retire a child, so the rollup cannot discharge this verification. Maintainer ruling 2026-09-07, option (b) of orchestrator `cczotj` OQ-04.
- Scope: Perform the whole-Set verification (both measured incidents, both hosts) and write the durable residuals record. Authors NO product code: every implementation belongs to children 01 through 04. This child is the Set's evidence, so its only deliverables are pasted observed evidence and one walkthrough artifact.
- Scope-Paths: .aw/records/walkthroughs/, .aw/records/plans/pending/20260907-integpath-05-3v7wo6-verify-the-whole-set-against-both-measured-incidents-and-rec.ipd.md
- Item-Dependencies: executed:29wvmj, executed:6sb3yu, executed:51vw4y, executed:rl67b0
- Status: reviewed
- Readiness: go-pending-approval
- Set: integpath
- Order: 5
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 3v7wo6
- From-Backlog: 5wdoze
- Blocks-Release: next

## Workflow history
- 2026-09-09 reviewed (aw set): /plan-review round 1 (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 all FIXED, no open questions. Reviewed by RUNNING the plan's own instructions rather than re-reading them, which produced both HIGH findings. PR-001: the walkthrough filename E-02 mandated put THIS plan's id6 in the walkthrough's own identity slot, violating DECISIONS.md D140 and failing check.id6-identity-slot (reproduced in a scratch repo); E-02 now mints a fresh id6, uses the canonical .walkthrough.md facet and links via Target-Id: 3v7wo6. PR-002: V-01's no-_attempt2 assertion fails on pre-existing history here (aw/lane/mm6wuz, _attempt2, _attempt3 all exist among 29 lane branches) and the only literal way to pass it was deleting a co-worker's preserved lanes; both incident reproductions are now explicitly synthetic, asserted on the synthetic id6 in a throwaway repo, with a do-not-delete-a-lane gate paragraph. PR-003: the inherited baseline failure was wrong (test_orchestrator_retirement is GREEN at 112 passed; the one bare-run failure is the environmental test_reporting_contract case caused by the gitignored opencode-recovery dump, proven causal by moving it aside for 53 passed). PR-004: added the -m '' slow-suite run the bare suite deselects, which children 03/04 already require. PR-005..PR-008: corrected stale citations (32ij2j/xtklpd superseded by daexj1/ys1dor, hyx1dg/yf9fj9 are backlog not plans, p8ni63 graduated to 3i0aaz), named the exact allow-dirty-base grep (returns nothing), re-measured 178/60 collection counts, narrowed Scope-Paths and fixed the 'respectively' closure claim. Lint conforming at author and review-finalize; typed review record written with four D-rows, all reversible.
- 2026-09-07 to-review (aw set): status set to to-review

- 2026-09-07 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created to carry orchestrator `cczotj`'s E-01/E-02, demoted here by maintainer ruling on that plan's OQ-04 (option (b)) so the whole-Set verification sits where the E/V checkpoint is ENFORCED rather than where the rollup omits it. The two E-items and their evidence requirements are carried over in substance from `cczotj` rather than rewritten, so nothing the review had already hardened is lost.

## Goal

Establish, with pasted evidence on both hosts, that the two measured incidents are survived end to end, and leave a durable record of exactly what this Set closed and what it deliberately did not.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This child authors NO product code. Its execution work is whole-Set verification and the durable record; children 01 through 04 carry every change.

### Task group 1: verify the Set's central claim

- [ ] E-01 VERIFY THE WHOLE SET against the two MEASURED INCIDENTS, on BOTH hosts, after all four implementing children have executed. This is the Set's central claim and it must be falsifiable rather than asserted from four green child suites.
  REPRODUCE INCIDENT ONE (`run-20260905T050043Z-639569`): a lane finalizes, finds an overlapping dirty path in main, and the dirt clears while other work is still running. Assert the item DEFERS and later INTEGRATES with no agent turn spent, and that a `--no-verify` was NOT required at any point.
  REPRODUCE INCIDENT TWO (`mm6wuz`, 2026-09-06): an item holding a verified lane is resumed. Assert the FIRST lane is integrated rather than a second being allocated, and that `git branch --list 'aw/lane/<id6>*'` shows no `_attempt2`.
  RUN THAT BRANCH CHECK INSIDE THE SYNTHETIC REPOSITORY, AGAINST THE SYNTHETIC ITEM'S OWN id6, AND NEVER AGAINST `mm6wuz` IN THIS CHECKOUT. Both children reconstruct these incidents synthetically in a throwaway repository because the original lanes are historical, and the historical lanes are STILL PRESENT here: measured at review 2026-09-09, `git branch --list 'aw/lane/mm6wuz*'` returns `aw/lane/mm6wuz`, `aw/lane/mm6wuz_attempt2` and `aw/lane/mm6wuz_attempt3`, three of the 29 `aw/lane/*` branches this checkout carries. So running the assertion here would report FAILURE for pre-existing history no matter how well the fix works, and DELETING those branches to make it pass is forbidden: they are another party's preserved work in a SHARED CHECKOUT, and `nuanaw`/`ys1dor` treat exactly those attempt clusters as live evidence. State the synthetic id6 you asserted on.
  THE STARTUP GATE (`p8ni63`) IS CONDITIONAL AND IS NOT THIS SET'S TO DELIVER. It is NOT a child of this Set, so FIRST determine whether it has landed: run `grep -rn "allow-dirty-base\|allow_dirty_base" agent_workflows/` (the exact check, so the result is reproducible). If it HAS landed, assert it refuses a dirty base and honors its override. If it has NOT, record that plainly and MOVE ON; its absence must NOT be reported as this Set's failure, and this item is complete without it. Do not treat its absence as a reason to weaken either incident reproduction, which are the parts this Set actually owns.
  MEASURED AT REVIEW 2026-09-09: that grep returns NOTHING, so the flag does not exist and the expected branch is the absent one. `p8ni63` is `- Status: graduated`, handed to plan `3i0aaz` (`dirtybase-01`, `- Status: to-review`, `pending/`), whose E-04 adds the flag; so unless `3i0aaz` executes first, record ABSENT. Re-run the grep yourself rather than trusting this line.
  DO BOTH HOSTS EXPLICITLY. The runner suites are asymmetric, so four green child suites can still leave an agy-side regression. If a host cannot be demonstrated, say so plainly rather than inferring from the other. The asymmetry is the durable point; the counts are not: re-measured at review 2026-09-09 they are `tests/test_oc_runipd.py` 178 collected versus `tests/test_agy_runipd_cli.py` 60, not the 148/45 this plan was authored with, so measure your own rather than treating either pair as a criterion.
  - Depends on: none
  - Expected outcome: both incidents are survived on both hosts with no paid turns, no orphaned lanes, and no hook bypass; the startup gate's presence is DETERMINED and either exercised or recorded absent.
  - Execution state: pending

### Task group 2: record what the Set closed and did not

- [ ] E-02 RECORD WHAT THE SET CLOSED AND WHAT IT DID NOT, because this Set deliberately leaves several named things open and a reader six months from now must not have to infer which. THE ARTIFACT IS A WALKTHROUGH under `.aw/records/walkthroughs/`. Do NOT invent a new record type and do NOT leave the artifact's type to the executor's judgement.
  THE FILENAME MUST NOT REUSE THIS PLAN'S id6, and the earlier instruction here to write `...-05-3v7wo6-<slug>-walkthrough.md` was WRONG: it would have put THIS PLAN's identity in the walkthrough's own identity slot, which DECISIONS.md D140 prohibits and `check.id6-identity-slot` reports as an ERROR (reproduced at review: a walkthrough named with `3v7wo6` in the slot beside this plan yields `filename identity-slot id6 3v7wo6 is another file's identity`). MINT A FRESH id6 for the walkthrough, name it `.aw/records/walkthroughs/<YYYYMMDD>-integpath-05-<new-id6>-<slug>.walkthrough.md` (the canonical facet form, not the legacy `-walkthrough.md` suffix), and express the link to this plan with the typed front-matter field `- Target-Id: 3v7wo6`, exactly as the three conforming walkthroughs in that directory already do. Note `aw check`'s name rule does NOT catch a legacy-suffix walkthrough with a foreign slot id6, so this is on you, not the linter, for the suffix half; the identity-slot half IS caught and will fail `aw check`.
  STATE THE RESIDUALS EXPLICITLY, each already named by a child: content-based narrowing of the dirty-overlap false-positive rate (declined by the maintainer 2026-09-05 as low-value relative to the ladder); path-category allowlists (REJECTED, not deferred, because they reason about who probably wrote a file rather than whether it can conflict, which is the fail-open inference `d07nz2` prohibits); `h1ksy6`, which fixes the same function but WIDENS its input set and must be reconciled with the ladder rather than stacked on it; and `a8eufb`, which would let the runner tell its own dirt from a co-worker's and is NECESSARY BUT NOT SUFFICIENT here because trailers mark commits while the motivating incident was 130+ uncommitted files.
  RECORD WHY `76gsmv` PASSED THE HOOK AS AN ANSWERED QUESTION, NOT AN OPEN ONE. Child 01 RESOLVED it on 2026-09-07 (its OQ-01, `Status: resolved`) and this record must not re-open it: the cause is the finalize journal's LIFETIME, not anything about git. `_clear_finalize_journal` deletes the journal on successful completion (`ipd_lifecycle.py:2649`) and on every rollback path, so it exists only between finalize and its consumption, and `76gsmv` merged 22 minutes before its three siblings and still had one. The backlog item's rename explanation is conclusively ruled out: all four merges are identical in diff shape (`R061`, `R063`, `R061`, `R060`). Verify against child 01's F-12/F-13 rather than restating this from here.
  NAME THE SIBLING SETS this one does NOT cover, so the boundary is legible: `integearn` covers a lane whose integration was never ATTEMPTED because the earned-integration gate refused, which is a different failure from the four here; `scopeattr` (`hyx1dg`) and `depreview` (`yf9fj9`) came from the same recovery sessions but are unrelated mechanisms. Do NOT cite `phawyy` as live work: it was RETRACTED and parked 2026-09-07 as false-premised (both blocked paths already persist the reason), so listing it as a sibling concern would propagate a withdrawn claim.
  TWO OF THE FOUR CITATIONS ABOVE HAVE ALREADY MOVED, MEASURED AT REVIEW 2026-09-09, and this is why the re-read rule below is not a formality. `32ij2j` and `xtklpd` are BOTH `- Status: superseded` under `.aw/records/plans/superseded/`, replaced by `daexj1` (`integearn-03`) and `ys1dor` (`integearn-04`), both `- Status: reviewed` under `pending/`; cite the SUCCESSORS for the live boundary and the superseded pair only as history. `hyx1dg` and `yf9fj9` are BACKLOG items, not plans (`hyx1dg` graduated, at `.aw/records/backlog/graduated/20260906-scopeattr-01-hyx1dg-...`; `yf9fj9` done, at `.aw/records/backlog/done/20260906-depreview-01-yf9fj9-...`), so do not describe either as a plan. Re-read each cited artifact's CURRENT status yourself before writing the boundary section rather than copying these; more may have moved since review.
  ALSO RECORD THE ROLLUP DEFECT THIS CHILD'S EXISTENCE IS EVIDENCE OF: that an orchestrator carrying real verification work has it discharged unperformed by the rollup, measured on `84j8d7`, and that the general fix (option (c) of `cczotj` OQ-04, separate backlog against `77tr3o` R-5) is still owed. This child is the per-Set workaround, not that fix.
  - Depends on: E-01
  - Expected outcome: a walkthrough at the named path listing every residual with its reason and every sibling Set with its boundary, with `76gsmv` recorded as ANSWERED, `phawyy` recorded as RETRACTED, and the rollup defect recorded as still open; no residual is left as an unstated assumption.
  - Execution state: pending

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

- [ ] V-01 validates E-01
  - Required evidence: paste BOTH incidents reproduced and survived, for BOTH hosts. Incident one: a lane refused on dirty overlap, DEFERRED, then INTEGRATED after the dirt cleared, with the merge commit on main and NO agent turn spent. Incident two: an item with a verified lane resumed, showing the FIRST lane integrated and `git branch --list 'aw/lane/<id6>*'` containing NO `_attempt2`; state the SYNTHETIC id6 you asserted on and paste the path of the throwaway repository, because running that check against `mm6wuz` in this checkout is a FAILED validation (three such branches pre-exist here and are another party's preserved work). For both, paste evidence that NO `--no-verify` was used anywhere. Paste the exact output of `grep -rn "allow-dirty-base\|allow_dirty_base" agent_workflows/` to establish whether `p8ni63` had landed and, if so, paste the startup gate refusing a dirty base and honoring its override; empty output means ABSENT, which is the expected result and completes this item without it, since it is not a child of this Set. If a host could not be demonstrated, SAY SO PLAINLY; an inferred agy result is a FAILED validation.
    Paste the BARE `python3 -m pytest` summary line (the `N passed` line) TWICE, once for your own BEFORE baseline and once AFTER, and show the AFTER-minus-BEFORE failure set EMPTY by NODE ID. Paste the slow-suite run (`make test-all` or `-m ''`) SEPARATELY for `tests/test_cli_conformance_matrix.py` and `tests/test_command_surface_declarations.py`, with the undeclared-parser-leaf set no larger than your measured baseline's. A single pasted summary line, or a claim of green without a self-measured baseline, is a FAILED validation.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the walkthrough's path and its residuals section verbatim. Confirm by quotation that it names all four residuals (content-based narrowing as DECLINED, path-category allowlists as REJECTED, `h1ksy6` as needing reconciliation, `a8eufb` as necessary-but-not-sufficient), records `76gsmv` as ANSWERED with the journal-lifetime cause, records `phawyy` as RETRACTED, and records the rollup defect as still open with `84j8d7` named. Paste the CURRENT status line of every sibling artifact you cite, read at execution time rather than copied from this plan, since several moved after authoring. A walkthrough that restates the rename explanation for `76gsmv` is a FAILED validation.
    ALSO PASTE the walkthrough's `- Target-Id: 3v7wo6` line and a clean `aw check --agent` for the identity-slot rule (`aw check --agent 2>&1 | grep id6-identity-slot` returning nothing). A walkthrough whose filename identity slot holds `3v7wo6` violates DECISIONS.md D140 and is a FAILED validation however good its content, so verify the name before the prose.
  - Observed evidence:
  - Result: pending

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

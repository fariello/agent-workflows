# IPD: Retire the redundant status-tolerance enumeration in artifact_audit and pin the catch-all statuses with a derived fence

- Date: 2026-09-30
- Kind: child
- Concern: `artifact_audit._status_disagrees` carries a 23-entry hand-maintained status enumeration that a measured sweep shows is already redundant with the derivation `run_status_is_nonterminal`, and the eight catch-all statuses backlog `qpgs4t` was filed about are now tolerated by an unplanned hand-fix with NO test pinning either the tolerance or its must-keep-flagging counterexample.
- Scope: Replace the enumerated in-flight/terminal-failure arm of `agent_workflows.artifact_audit._status_disagrees` with the existing derivation, proven behavior-preserving over every status either runner can write; restore a scope fence over the eight statuses named by `qpgs4t` plus the `executed/`-counterexample that must keep flagging; and correct a docstring that claims a cross-driver test pin which does not exist.
- Scope-Paths: agent_workflows/artifact_audit.py, tests/test_artifact_audit.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: qpgs4t
- Set: runviewdisc
- Order: 3
- Highest E allocated: 04
- Author: OpenCode lane qpgs4t
- Id: p5yaqw

## Workflow history

- 2026-09-30 draft (OpenCode lane qpgs4t): created.
- 2026-09-30 to-review (OpenCode lane qpgs4t): authored from backlog `qpgs4t`. The item's premise was re-measured at HEAD `928be376` and found STALE: all eight statuses it lists are already tolerated. The plan was rewritten around what is actually still wrong (no test fence, a redundant enumeration, and a false docstring claim) rather than around the item's original ask.

## Goal

Backlog `qpgs4t` asked for a per-status measured argument before admitting each of eight terminal-failure run statuses into the `_status_disagrees` tolerance arm. Re-measurement at HEAD shows all eight are ALREADY tolerated, so that ask is obsolete; what remains is that the tolerance arrived unplanned, is pinned by no test, and rests on a hand-maintained enumeration the codebase can now DERIVE. This plan converts the enumeration to the derivation (proven behavior-preserving on all 384 status/declared pairs that can actually occur), restores the scope fence the test trim deleted, and removes a docstring claim that is false.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the current behavior before changing it

- [ ] E-01 Add characterization tests to `tests/test_artifact_audit.py` that pin, against the CURRENT code and before any production edit, both arms of the `qpgs4t` question for all eight statuses it names (`failed`, `failed-safely`, `partial`, `not-attempted`, `merge-conflict`, `integration-blocked`, `merge-needs-human`, `cancelled`): (a) a plan UNMOVED in `pending/` reading `- Status: approved` must NOT be flagged (`has_discrepancy` False), and (b) the counterexample, a plan in `executed/` reading `- Status: executed`, must KEEP being flagged on both axes. Drive the real entry point `artifact_audit.audit_artifact` against a temporary git repo, not the private helper, so the test asserts operator-visible outcomes. This is the fence the test trim in commit `19313eed` deleted and it must pass BEFORE E-02 runs.
  - Depends on: none
  - Expected outcome: new tests pass at HEAD with no production change, demonstrating they characterize existing behavior rather than a hoped-for one; `python3 -m pytest tests/test_artifact_audit.py` green with the new cases counted.
  - Execution state: pending

- [ ] E-02 Add an equivalence test asserting that for EVERY status in `runner_shared.TERMINAL_STATES` unioned with the enumeration's own 23 literals and the extra aliases (`complete`, `executed`, `substantially-complete`, `queued`, `running`, `dependency-blocked`, `blocked`), crossed against every plausible declared value, `_status_disagrees` returns what the derived predicate returns. The test must FAIL if a future edit makes the two diverge on any status a driver can write. Exclude `timed-out` explicitly and in the test's own comment say why (see F-05).
  - Depends on: E-01
  - Expected outcome: the equivalence test passes at HEAD, independently confirming the enumeration and the derivation already agree, so E-03 is a refactor and not a behavior change.
  - Execution state: pending

### Task group 2: retire the enumeration in favor of the derivation

- [ ] E-03 In `agent_workflows.artifact_audit._status_disagrees`, replace the two literal status tuples (the 16-entry canonical tuple and the 7-entry raw-`recorded` tuple) with the single derived condition `run_status_is_nonterminal(recorded) and canonical_terminal_status(recorded) not in runner_shared.SUCCESS_STATES`, leaving the three earlier arms (`executed`/`complete`, `retired`, `reviewed`) and the accepted pre-terminal declared values BYTE-IDENTICAL. Do not admit `executed` to the accepted values. Keep the guard against success statuses: without it, `approved` (which IS in `TERMINAL_STATES` and maps to `pending`) would newly be tolerated, which is the one divergence measured in F-04.
  - Depends on: E-02
  - Expected outcome: the enumeration is gone, `_status_disagrees` reads its tolerance off the same derivation `run_status_is_nonterminal` already exposes, and the E-01 and E-02 tests still pass unchanged, proving the refactor preserved behavior.
  - Execution state: pending

- [ ] E-04 Correct the two stale claims in the surrounding documentation, changing no behavior: (a) the docstring of `run_status_is_nonterminal` asserts `tests/test_artifact_audit.py` pins it against BOTH host drivers' `TERMINAL_STATES`, which is false at HEAD (zero occurrences of `TERMINAL_STATES` in that file), so either make the claim true by citing the E-02 test or delete the sentence; and (b) rewrite the `_status_disagrees` docstring so its tolerance band is described as DERIVED rather than as a list of statuses, removing the now-absent enumeration from the prose so the comment cannot rot away from the code again.
  - Depends on: E-03
  - Expected outcome: no docstring in the module claims a test pin that does not exist, and the tolerance prose names the derivation instead of restating a list.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE DERIVED-NOT-ENUMERATED PATTERN IS ALREADY THIS MODULE'S ESTABLISHED CONVENTION, and this plan applies it rather than inventing it. `artifact_audit.run_status_is_nonterminal` was deliberately rewritten from an enumeration to a derivation by IPD `zexed1` (E-03, review PR-201); its docstring argues the enumerated form "fails" because a hand-written list leaves dominant false-alarm shapes unfixed. `_status_disagrees` is the same module's remaining enumeration and the same argument applies to it.
- Test-outcome discipline: `AGENTS.md` forbids code-pinning tests (no `inspect`, no `ast`, no source regex, no symbol censuses). Every test this plan adds therefore CALLS `audit_artifact` or `_status_disagrees` and asserts returned values, never that a literal still appears in the source.
- Suite invocation: run `python3 -m pytest` BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `tests/test_artifact_audit.py` builds its own temporary git repos and must not read the live gitignored `.aw/records/runs/` tree; follow the existing fixture style in that module.

## Findings

| # | Severity | Location | Finding | Evidence |
|---|---|---|---|---|
| F-01 | BLOCKER-FOR-THE-ITEM-AS-WRITTEN | `artifact_audit._status_disagrees` | THE BACKLOG ITEM'S PREMISE IS STALE AND ITS LITERAL ASK MUST NOT BE PERFORMED. All eight statuses `qpgs4t` lists as flagging are ALREADY tolerated at HEAD. The item asks for a measured argument before ADMITTING each one; they are already admitted, so executing the item as written would be a no-op. The plan is therefore scoped to what remains wrong: no test fence, a redundant enumeration, and a false docstring claim. | Probed `audit_artifact` at HEAD `928be376` against a temp repo with a plan at `- Status: approved` in `pending/`: all nine of `failed`, `failed-safely`, `partial`, `not-attempted`, `merge-conflict`, `integration-blocked`, `merge-needs-human`, `cancelled`, `interrupted` returned `location_mismatch=False status_mismatch=True=False` i.e. `has_discrepancy=False`, `difference_class=unchanged` |
| F-02 | HIGH | commit `05e77dfc` | THE TOLERANCE ARRIVED AS AN UNPLANNED HAND-FIX, which is why no per-status argument exists for it. `05e77dfc` ("fix(run_viewer): align non-executed audit status and suppress refusals on short", 2026-09-27) widened the arm from `vdabn5`'s single added value to 16 canonical statuses, and in the same edit DELETED the long docstring paragraph that recorded WHY the seven siblings were excluded. Its commit message body is empty and it cites no plan. So the codebase now does what `qpgs4t` asked for without the measured argument `qpgs4t` demanded. | `git log -S '"failed",' -- agent_workflows/artifact_audit.py` returns exactly `05e77dfc`; `git show 05e77dfc` shows `- ONE VALUE WAS ADDED, NOT THE SEVEN SIBLINGS` being removed and the 16-entry tuple added; `git log -1 --format=%B 05e77dfc` has no body |
| F-03 | HIGH | `tests/test_run_viewer.py` | THE SCOPE FENCE THE ITEM RELIES ON NO LONGER EXISTS, so nothing pins either direction today. `qpgs4t` says `test_the_seven_sibling_catch_all_statuses_are_deliberately_unchanged` "asserts all eight keep flagging, so whoever picks this up must update that test deliberately rather than loosening the arm by accident". That test was deleted by the suite trim, three days BEFORE `05e77dfc` widened the arm, so the widening tripped no fence. Neither the tolerance nor its must-keep-flagging counterexample is pinned at HEAD, which is what E-01 restores. | `grep -rn 'seven_sibling\|catch_all' tests/` returns nothing; `git log -S` on the test name returns `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24), which removed 1312 lines from `tests/test_artifact_audit.py` |
| F-04 | HIGH | `artifact_audit._status_disagrees` vs `run_status_is_nonterminal` | THE ENUMERATION IS ALREADY REDUNDANT WITH THE DERIVATION, WHICH IS WHAT MAKES E-03 SAFE, AND THE ONE GUARD IT NEEDS IS MEASURED. Swept all statuses either runner can write crossed against all plausible declared values: the naive derivation diverges on only 11 of 384 pairs, and adding the `not in SUCCESS_STATES` guard reduces that to 6, ALL of them `timed-out`. So the refined derivation in E-03 is exactly behavior-preserving on every status that can actually occur. WITHOUT the guard, `approved` diverges (it is in `TERMINAL_STATES` and `expected_dir_for_status('approved')=='pending'`, so it would be newly tolerated); that is why E-03 specifies the guard rather than the bare derivation. | Ran both candidate predicates over `set(TERMINAL_STATES)` plus the enumeration literals plus `complete`/`executed`/`substantially-complete`/`timed-out` (24 statuses) crossed with 12 declared values: naive `divergences=11` (5 `approved` rows, 6 `timed-out`); refined `divergences=6` (`timed-out` only); `SUCCESS_STATES == ['approved','executed','reviewed']` |
| F-05 | MED | `timed-out` | THE SOLE RESIDUAL DIVERGENCE IS A DEAD STRING, so it is not a behavior change anyone can observe. `timed-out` is in no status set and is written by neither runner; `vdabn5` F-10 already recorded that it "is not a status either runner writes". It is absent from the entire Python source. Under the derivation it would become tolerated, which is why E-02 excludes it explicitly and says so rather than leaving a silent difference. | `'timed-out' in runner_shared.TERMINAL_STATES` is False; `canonical_terminal_status('timed-out')=='timed-out'`; `grep -rn '"timed-out"' agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py agent_workflows/runner_shared.py` returns nothing; repo-wide `grep` finds it only in prose inside executed IPDs |
| F-06 | MED | `run_status_is_nonterminal` docstring | A DOCSTRING CLAIMS A TEST PIN THAT DOES NOT EXIST. It states `tests/test_artifact_audit.py` "pins this against BOTH host drivers' `TERMINAL_STATES`, in the style of `runner_shutdown.KNOWN_ITEM_STATUSES`, so a driver adding a status cannot drift silently". That file contains zero occurrences of `TERMINAL_STATES`; the pin was among the 1312 lines the trim removed. A reader trusting it would believe drift is caught when it is not. E-02 makes the claim true and E-04 reconciles the prose. | `grep -c 'TERMINAL_STATES' tests/test_artifact_audit.py` returns `0`; `grep -rn 'KNOWN_ITEM_STATUSES' tests/` returns nothing |
| F-07 | MED | `substantially-complete` | A SEPARATE LATENT ASYMMETRY IS OUT OF SCOPE AND IS RECORDED SO IT IS NOT SWEPT IN. `substantially-complete` canonicalizes to `fail-gate`, not to `complete` as `vdabn5` F-4 measured, so an item at that status whose plan legitimately reached `executed/` reading `- Status: executed` IS still flagged, while a `complete` item in the same shape is not. That may be correct (it is not in `SUCCESS_STATES`) or may be a real gap, but deciding needs its own measured argument about whether that status ever accompanies a legitimate finalize. This plan preserves the behavior exactly and does not adjudicate it. | `canonical_terminal_status('substantially-complete')=='fail-gate'`; `_status_disagrees('substantially-complete','executed')` is True while `_status_disagrees('complete','executed')` is False; `_RUN_SUCCESS_STATUSES == frozenset({'executed'})` |
| F-08 | CONFIRMED-NOT-BLOCKED | backlog `1f9m2j`, `rnl3b7` | THE ITEM'S CARVE-OUT FOR `integration-blocked` IS OBSOLETE AND DOES NOT GATE THIS PLAN. `qpgs4t` excludes `integration-blocked`/`merge-needs-human` as "ALREADY OWNED by backlog `1f9m2j`, which is BLOCKED on `rnl3b7`". Both have since moved: `rnl3b7` is in `done/` and `1f9m2j` is in `graduated/`. This plan changes no behavior for either status (F-04), so it neither duplicates nor conflicts with that work; it only PINS what HEAD already does. | `.aw/records/backlog/done/20260905-integdefer-01-rnl3b7-executed-gate-not-merge-aware.backlog.md` and `.aw/records/backlog/graduated/20260905-runviewdisc-01-1f9m2j-run-viewer-stale-record-mislabel.backlog.md` exist; both statuses measured `has_discrepancy=False` unmoved and True moved, identical to their six siblings |
| F-09 | LOW | published `--json`/`--agent` records | THE REFACTOR CANNOT BREAK THE AGENT PROTOCOL, because it touches no field. `ArtifactAudit` is `asdict()`ed into published records and `zexed1` established that removing `missing_entirely`/`location_mismatch`/`status_mismatch` would require an `aw.agent/v2` bump. E-03 changes only which VALUE `status_mismatch` takes for statuses where F-04 measured no change at all, so no field is added, removed, or renamed. | `ArtifactAudit.has_discrepancy` comment in `artifact_audit.py` records the stability rule; F-04 sweep shows zero value changes for every writable status |
| F-10 | LOW | suite baseline | BASELINE MEASURED IN THIS LANE, so the executor compares node ids against a real number rather than a stale one. Unlike `vdabn5`, which inherited two wrong baselines (its F-13), this lane's tree is clean and green. | `python3 -m pytest` bare in this worktree at HEAD `928be376`: `3291 passed, 2 skipped, 3 warnings in 196.85s`, plus `NOTE: 207 tests were deselected`; `tests/test_artifact_audit.py tests/test_run_viewer.py` together `59 passed` |

## Proposed changes (ordered, validatable)

1. E-01 restores the deleted scope fence FIRST, pinning both directions for all eight `qpgs4t` statuses through the public `audit_artifact` entry point, so the characterization exists before anything is refactored.
2. E-02 adds the cross-driver equivalence pin that F-06 shows the docstring already promises, proving the enumeration and the derivation agree today and failing loudly if they ever diverge.
3. E-03 deletes the two literal tuples and reads the tolerance off `run_status_is_nonterminal`, guarded by `SUCCESS_STATES` for the measured `approved` case, leaving the other three arms and the accepted declared values untouched.
4. E-04 reconciles the prose with reality: the false test-pin claim and the enumeration-shaped description both go.

The order matters and is not cosmetic: E-01 and E-02 must be GREEN AT HEAD before E-03 edits anything, because a test written after a refactor characterizes the refactor rather than the behavior it was supposed to preserve.

## Deferred / out of scope (with reason)

- THE `substantially-complete` ASYMMETRY (F-07). Left exactly as HEAD behaves. Deciding whether that status should join the success arm needs its own measured argument about whether it ever accompanies a legitimate finalize, which is the same standard `qpgs4t` itself demanded per status.
  - Carrier: 64a03w
- `timed-out` (F-05). Not tolerated today, tolerated under the derivation, and unobservable either way because nothing writes it. Explicitly excluded from E-02's equivalence assertion with the reason stated in the test, rather than silently absorbed.
  - Carrier-Declined: NOTHING IS OWED, because the divergence is unobservable by construction rather than merely unlikely. F-05 measures `timed-out` as absent from `TERMINAL_STATES`, absent from every status set, and absent from the entire Python source, so no run record can ever carry it; `vdabn5` F-10 independently recorded that neither runner writes it. An item asking someone to decide the tolerance of a status nothing produces would be work with no observable outcome. E-02 pins the exclusion explicitly and states the reason in the test, so a future reader finds the argument rather than a silent gap, and if a driver ever starts writing the status that same test is what fails.
- BACKDATING A PER-STATUS ARGUMENT FOR THE EIGHT STATUSES. `qpgs4t` wanted one argument per status before admission; admission already happened in `05e77dfc` (F-02). This plan does not manufacture retrospective justifications it did not measure. What it does instead is PIN the behavior in both directions so the next change is deliberate, which is the outcome the item's scope fence existed to produce.
  - Carrier-Declined: THE OBLIGATION IS DISCHARGED BY THIS PLAN, not deferred by it. OQ-01 resolves the substantive question from repository evidence: the tolerance is correct on a STATUS-INDEPENDENT argument (the accepted declared values are all pre-terminal and exclude `executed`, so a tolerated failure status suppresses the row only when the plan did not move, while the moved-plan case keeps flagging via `expected_dir_for_status`), which is precisely why a separate per-status measurement is not owed for each of the eight. What `qpgs4t` actually wanted protected was deliberateness, and E-01 restores that as an executable fence. Writing retrospective per-status justifications for an admission that already shipped would fabricate reasoning nobody performed.
- THE ITEM'S "consider a direction-aware classifier" SUGGESTION. `difference_class`/`classify_difference` already exists (IPD `zexed1`) and already runs beside these booleans; `qpgs4t` predates knowing that. Re-homing the tolerance into the classifier is a much larger change touching published record semantics (F-09).
  - Carrier-Declined: THE SUGGESTION IS ALREADY SATISFIED, so there is nothing outstanding to carry. The item asks whether "a direction-aware classifier would be" better than the ad-hoc list and names `classify_difference`/`difference_class` (IPD `zexed1`) as the likely home. That machinery SHIPPED and already runs on every audit: F-01 measures the eight tolerated rows returning `difference_class=unchanged`, and `ArtifactAudit.is_alarming` already gates the red styling on the class rather than on the booleans. So the direction-awareness the item wanted exists; this plan additionally removes the enumeration it objected to (E-03). Moving the remaining pre-terminal tolerance INTO the classifier would change which rows published `--json`/`--agent` consumers receive, which F-09 shows is an `aw.agent/v2` question and a maintainer's call, not an unowned task.
- `run_viewer.py` ITSELF. The five `Issue` predicate copies consume this module's output and need no edit; not in `Scope-Paths`.
  - Carrier-Declined: This row records a SCOPE FENCE on this plan rather than a deferred defect, so nothing is owed and there is no future work to carry. The copies consume `audit_artifact`'s output unchanged, so E-03 reaches every surface with no predicate edit; `vdabn5` F-5 measured the same five copies and reached the same conclusion, and unifying them is separately owned by plan `r2i1b1` E-03.

## Scope check

- Over-scope: none. `agent_workflows/artifact_audit.py` is in scope ONLY for the one tolerance arm inside `_status_disagrees` and the two docstrings named in E-04. Do NOT touch `canonical_terminal_status`, `expected_dir_for_status`, `_TERMINAL_EXPECTED_DIR`, `_RUN_SUCCESS_STATUSES`, `allowed_lifecycle_pairs`, `classify_difference`, the `ArtifactAudit` fields, or any `run_viewer.py` issue-predicate copy.
- Under-scope: stated rather than left as `none`. (a) `substantially-complete` remains asymmetric with `complete` (F-07). (b) `timed-out` remains untolerated (F-05). (c) The backlog item's own body still asserts the eight statuses flag, which is false at HEAD; note it when closing the item rather than rewriting the item's history. (d) The tolerance still lives in `_status_disagrees` rather than in the `difference_class` machinery the item floated as the better long-term home.

## Required tests / validation

`python3 -m pytest` BARE in the executing worktree. Do not add `-n0`, a second `-q`, or `-p no:randomly`. Compare failing NODE IDS, not totals.

Baseline measured IN THIS LANE at HEAD `928be376` (F-10): `3291 passed, 2 skipped, 3 warnings in 196.85s`, with `NOTE: 207 tests were deselected by -m/-k`. Any post-change failure must be a node id absent from that green run.

Both new test groups must be shown GREEN AT HEAD BEFORE the E-03 edit, and green again after, and the executor must paste BOTH runs. A single post-refactor green run does not distinguish "behavior preserved" from "test written to match whatever the new code does", which is the specific failure this sequencing prevents.

## Spec / documentation sync

N/A with reason: no `.spec.md` governs `_status_disagrees`, and none is edited (`Scope-Paths` declares no spec file). The contract this touches is the `aw.agent/v1` record shape in `docs/cli-agent-protocol.md`, and F-09 establishes that no field is added, removed, or renamed, so that document needs no change. The only documentation edits are the two in-module docstrings in E-04.

## Open questions

### OQ-01: Should the eight statuses' tolerance be preserved at all, given it arrived unplanned?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, preserve it. The tolerance is correct on the same reasoning `vdabn5` used for `interrupted` and recorded in its own docstring: the accepted declared values are all PRE-TERMINAL and do not include `executed`, so tolerating a failure status suppresses the row EXACTLY when the plan has not moved, while the moved-plan case keeps flagging on both axes independently via `expected_dir_for_status`. That argument is status-independent, which is why it extends to all eight without a separate measurement per status, and F-04's sweep confirms the derivation reproduces HEAD exactly. Reverting to the pre-`05e77dfc` narrow arm would re-introduce the false alarms `qpgs4t` was filed to remove. The plan preserves behavior and adds the missing pin.

### OQ-02: Should `substantially-complete` be fixed in the same pass?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED, no, deferred to its own item (F-07). It is a genuinely different question: the eight statuses are about a plan that did NOT move, while `substantially-complete` is about a plan that DID reach `executed/`, so tolerating it would admit `executed` to the accepted declared values, which every prior plan in this area explicitly forbids as suppressing the one row most needing an operator's eyes. `vdabn5` F-4 already deferred it once, and its measurement is now stale (it canonicalizes to `fail-gate`, not `complete`), so a fix would need fresh measurement this plan has not done.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `python3 -m pytest tests/test_artifact_audit.py` output showing the new cases GREEN AT HEAD BEFORE any edit to `artifact_audit.py`, together with `git diff --stat agent_workflows/artifact_audit.py` proving that file is UNCHANGED at that moment. Then, for each of the eight statuses, paste the asserted pair: unmoved-in-`pending/`-at-`approved` gives `has_discrepancy=False`, and in-`executed/`-at-`executed` gives `location_mismatch=True status_mismatch=True`. Finally, demonstrate the fence bites by temporarily narrowing the tolerance arm to `interrupted` only and pasting the resulting FAILING node ids (then revert); a fence that cannot fail is not a fence.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the equivalence test passing at HEAD, and paste the enumerated list of statuses it actually swept (it must include every member of `runner_shared.TERMINAL_STATES`, so paste that set too and show the test covers it) with the total pair count asserted. Show `timed-out` is excluded and that the exclusion is justified in the test's own comment. Then prove the test detects drift: add a fabricated status to the derivation's tolerated set (or remove one from the enumeration), paste the FAILING node id, and revert.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff agent_workflows/artifact_audit.py` showing BOTH literal tuples removed and the derived condition in their place, with the three earlier arms and the accepted pre-terminal declared values textually unchanged. Paste a full bare `python3 -m pytest` run and compare against the `3291 passed, 2 skipped` baseline by node id. Paste the E-01 and E-02 tests passing UNMODIFIED after the refactor (show they were not edited: `git diff tests/test_artifact_audit.py` between the pre-refactor and post-refactor commits must be empty for those cases). Prove the `SUCCESS_STATES` guard is load-bearing by removing it, pasting the resulting failure that shows `approved` becoming tolerated, and reverting.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `grep -n 'TERMINAL_STATES' tests/test_artifact_audit.py` returning a real match from E-02 (making the `run_status_is_nonterminal` docstring claim TRUE), or paste the diff deleting that sentence if the other route was taken. Paste the new `_status_disagrees` docstring showing it describes the tolerance as derived and no longer enumerates statuses, and confirm by `grep` that the removed status literals appear nowhere in the module's prose. Confirm no behavior changed in this item with a final bare `python3 -m pytest` matching V-03's counts.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution; do not self-approve, and do not hand-write a `- Readiness:` field (it is an output of `/plan-review`).

Execution contract: commit only the two paths in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, `git add .`, `git commit -a`, or `--no-verify`; do not push; do not create a tag or release. Paste ACTUAL runner output for every validation item rather than asserting success.

Sequencing is part of the contract, not a suggestion: E-01 and E-02 must be committed and green BEFORE E-03 touches `artifact_audit.py`, so the characterization tests provably predate the refactor they protect. An executor who writes the tests after the refactor has validated nothing and must start over.

Post-gate lifecycle: after every `V-*` is verified with pasted evidence and `aw ipd lint --phase pre-transition` reports conforming, move this plan to `.aw/records/plans/executed/` through the tooled transition (`aw ipd set executed`), never by hand-editing terminal state. Note in the backlog item's closing that its premise was stale (F-01) so the next reader is not misled.

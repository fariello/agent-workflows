# IPD: Restore the anti-widening guard that keeps a release gate off the re-derivation allow-list

- Date: 2026-09-30
- Kind: child
- Concern: THE SAFETY PROPERTY BACKLOG ITEM `mgz3f1` RELIES ON DOES NOT EXIST, AND THE ITEM COULD NOT HAVE KNOWN IT. The item's central reassurance is that the re-derivation allow-list cannot be widened to admit a release gate because "`tests/test_records_only_lane_rederive.py` fails if the allow-list is widened to include it, deliberately." MEASURED AT AUTHORING HEAD `a579db9f`: that file does not exist. Commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) deleted it entirely, 679 lines and 25 test functions, two days after the item was filed on 2026-09-22. `rg REDERIVABLE_FRONT_MATTER_KEYS tests/` returns ZERO hits, as do `classify_records_only_front_matter_conflict`, `rederive_front_matter` and `REDERIVE_SHAPE`, so the entire carve-out ships with no test caller of any kind. I DEMONSTRATED THE CONSEQUENCE RATHER THAN ARGUING IT (F-03): I edited `REDERIVABLE_FRONT_MATTER_KEYS` to `frozenset(("Work-Kind", "Priority", "Blocks-Release"))`, ran the full bare suite, and got `3284 passed, 2 skipped in 198.48s` with nothing objecting. The exact widening that spec `25kzda` Section 2.1a calls "strictly worse than the conflict it resolves" is now a silent one-token edit. THIS INVERTS THE ITEM'S PREMISE, so this plan does NOT decide the item's options (a)/(b)/(c): it restores the guard those options all presuppose, which is prerequisite to deciding them and is not itself the maintainer's judgement call.
- Scope: Restore behavioral test coverage for the records-only front-matter re-derivation mechanism (`agent_workflows/runner_shared.py`), reinstating in particular the two named controls the deleted file existed for (the ANTI-REVERT control and the ALLOW-LIST control), and correct the one stale in-repo citation that still points at the deleted path. Out of scope: deciding backlog `mgz3f1`'s options (a)/(b)/(c), any edit to `REDERIVABLE_FRONT_MATTER_KEYS` itself, and any change to classifier, writer or integration behavior.
- Scope-Paths: tests/test_records_only_lane_rederive.py, agent_workflows/runner_shared.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: medium
- From-Backlog: mgz3f1
- Set: rederiveguard
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 9mi8eg

## Workflow history

- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `mgz3f1` during a non-interactive authoring turn. Measurement at HEAD `a579db9f` found the item's cited guard test deleted by `19313eed`, so the plan's subject is the missing guard rather than the item's stated options; recorded as F-01 through F-08 with the widening demonstration at F-03.

## Goal

Restore the deleted behavioral guard so that admitting `- Blocks-Release:` (or `- Status:`, `- Readiness:`, `- Approval:`, `- Item-Dependencies:`) to the re-derivation allow-list fails the test suite loudly instead of passing silently, and so that the mechanism spec `25kzda` Section 2.1a governs has test callers at all. This restores the safety property backlog item `mgz3f1` assumes is already in force; it deliberately does NOT resolve that item's options (a)/(b)/(c), which remain a maintainer decision.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: restore the two named controls

- [ ] E-01 Recreate `tests/test_records_only_lane_rederive.py` with the PURE-CLASSIFIER arms of the deleted file, recovered from `git show 19313eed^:tests/test_records_only_lane_rederive.py` and re-verified against the CURRENT signatures of `runner_shared.classify_records_only_front_matter_conflict`, `classify_records_only_conflict_set`, `format_records_only_conflict_refusal_reason` and `rederive_front_matter` rather than pasted blind. Cover at minimum: the allow-list is exactly the two measured keys; a real conflict of this shape classifies as a match; a code path, a `- Status:`-versus-`- Status:` disagreement, a body-prose rewrite, a non-transitioned target and a value disagreement on an allow-listed key each classify `not-this-shape`; and an unmeasured record type plus a missing merge stage each return `unknown` rather than an assumed verdict.
  - Depends on: none
  - Expected outcome: The file exists and its classifier arms pass against unmodified source. `python3 -m pytest tests/test_records_only_lane_rederive.py -o addopts=""` reports all collected tests passing, and `rg -c 'REDERIVABLE_FRONT_MATTER_KEYS' tests/test_records_only_lane_rederive.py` is non-zero where it was zero before.
  - Execution state: pending

- [ ] E-02 Restore the ALLOW-LIST CONTROL: the writer `rederive_front_matter` refuses every gate or attestation key even when handed a verdict that positively classifies it. Parametrize over at least `Status`, `Readiness`, `Approval` and `Blocks-Release`, constructing a `RecordsOnlyConflictVerdict` whose `added_keys` carries the dangerous key and asserting `DriverError` naming that key. This is the arm that speaks directly to backlog `mgz3f1`: `Blocks-Release` must be refused BY THE WRITER regardless of what any classifier or injected allow-list says.
  - Depends on: E-01
  - Expected outcome: Four (or more) parametrized cases pass, each asserting a raised `DriverError` whose message names the refused key. Deleting the writer's allow-list check makes them fail.
  - Execution state: pending

- [ ] E-03 Restore the ANTI-REVERT CONTROL over the mechanism, using REAL GIT (a temporary repository with an actual conflicting merge, as the deleted file did) rather than a hand-built fixture asserting the author's belief about git: for a conflict whose target sits in a terminal lifecycle directory, the re-derived text must carry the TARGET's terminal `- Status:` and must not carry the incoming branch's non-terminal one. Include the deleted file's companion demonstration that widening the allow-list to `Status` still refuses in BOTH independent places (the classifier's value-clash rule on the realistic shape, and the writer's own allow-list on the statusless shape that evades it), since a future reader deleting one layer while believing the other was the only one is exactly the regression this pins.
  - Depends on: E-01
  - Expected outcome: The anti-revert assertions pass, and the two-layer widening demonstration passes, against unmodified source. No plan in a terminal directory can acquire a non-terminal status through this mechanism.
  - Execution state: pending

- [ ] E-04 Add the RED-side demonstration that the restored guard actually bites, which is the property whose absence this plan exists to fix: with the suite restored, temporarily set `REDERIVABLE_FRONT_MATTER_KEYS` to include `Blocks-Release`, confirm the restored file FAILS, then revert the source edit and confirm it passes. Record both runs as pasted output in V-04. Do NOT leave any source edit behind, and do NOT encode the widening into a committed test double that mutates the shipped constant.
  - Depends on: E-02, E-03
  - Expected outcome: A pasted RED run showing at least one failure under the widened constant, a pasted GREEN run after reverting, and `git diff --stat agent_workflows/runner_shared.py` clean of any allow-list change at the end.
  - Execution state: pending

### Task group 2: correct the stale citation

- [ ] E-05 Correct the stale in-source citation at `runner_shared.REDERIVABLE_FRONT_MATTER_KEYS`'s docstring comment, which states that `tests/test_records_only_lane_rederive.py` "fails if `- Status:`, `- Readiness:`, `- Approval:`, `- Blocks-Release:` or `- Item-Dependencies:` is ever admitted". Once E-01..E-04 land the claim is true again for the keys actually covered; verify the restored file covers every key the comment names and either cover the remainder or narrow the comment to what is genuinely pinned. Do not overstate: the comment must name only properties the restored tests really enforce.
  - Depends on: E-04
  - Expected outcome: The comment's enumerated keys and the restored file's parametrized cases agree exactly, verifiable by reading both. No claim remains that no test enforces.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE SUITE IS RUN BARE. `AGENTS.md` requires `python3 -m pytest` with no added flags, because `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; adding `-q` compounds into `-qq` and suppresses the `N passed` line this plan must paste. Where per-test counts from a narrowed run are genuinely needed, clear defaults explicitly with `-o addopts=""` rather than fighting individual flags.
- TESTS MUST EXERCISE BEHAVIOR, NEVER CODE STRUCTURE (`AGENTS.md`, GUIDING_PRINCIPLES P16). This plan is directly exposed to that rule because it restores a DELETED test file, and the honest check is that the deleted file complies: `git show 19313eed^:tests/test_records_only_lane_rederive.py | rg 'import inspect|import ast|getsource|read_text\(\)'` returns NOTHING, so it read no production source and pinned no source text. It called the real functions, drove real `git` subprocesses, and asserted real verdicts and raised errors. Restoring it therefore does not reintroduce a code-pinning test.
- CITE BY SYMBOL, NOT BY BARE LINE OFFSET (spec `ipd-structure-and-linting` Section 10.2, advisory `IPD-C801`), which is why every citation in this plan names `runner_shared.<symbol>` or quotes content.
- THE INTEGRATION SEAM IS SHARED BY BOTH HOSTS. `classify_records_only_front_matter_conflict`, `classify_records_only_conflict_set`, `format_records_only_conflict_refusal_reason`, `rederive_front_matter` and `integrate_lane_branch` all live in `agent_workflows/runner_shared.py`, so a single restored test file reaches `oc_runipd` and `agy_runipd` with no per-host edit. The deleted file pinned exactly this in `test_the_seam_is_shared_by_both_runners`.
- AN ALLOW-LIST IS THE SAFETY PROPERTY, REPEATEDLY AND EXPLICITLY. Both `runner_shared`'s section header ("THE ALLOW-LIST IS AN ALLOW-LIST AND MUST NEVER BECOME A DENY-LIST") and spec `25kzda` Section 2.1a ("THE ALLOW-LIST IS AN ALLOW-LIST, NEVER A DENY-LIST") state it, and both enumerate the same dangerous absentees for the same reason.

## Findings

| Id | Finding | Evidence (measured at HEAD `a579db9f`) |
|---|---|---|
| F-01 | The guard test backlog `mgz3f1` relies on DOES NOT EXIST. | `git ls-files --error-unmatch tests/test_records_only_lane_rederive.py` -> `error: pathspec ... did not match any file(s) known to git`. |
| F-02 | It was deleted by the suite trim, two days AFTER the item was filed. | `git show --stat 19313eed -- tests/test_records_only_lane_rederive.py` -> `1 file changed, 679 deletions(-)`, commit `19313eed` "test: trim test suite from 9,136 to under 2,000 tests", dated 2026-09-24; item `mgz3f1` is dated 2026-09-22. The item was CORRECT WHEN WRITTEN. |
| F-03 | THE WIDENING THE ITEM CALLS IMPOSSIBLE IS NOW SILENT. Demonstrated, not reasoned. | Set `REDERIVABLE_FRONT_MATTER_KEYS = frozenset(("Work-Kind", "Priority", "Blocks-Release"))`, ran bare `python3 -m pytest`: `3284 passed, 2 skipped, 3 warnings in 198.48s`. Zero failures. Source then reverted (`git checkout --`, tree clean, constant back to the shipped two keys). |
| F-04 | The carve-out has NO test caller at all, not merely a weakened one. | `rg 'REDERIVABLE_FRONT_MATTER_KEYS\|classify_records_only_front_matter_conflict\|rederive_front_matter\|REDERIVE_SHAPE' tests/` returns zero matches. The only in-tree `rederive` hits are `test_installer.py`'s unrelated `test_second_install_rederives_identical_hashes` and one `test_runner_shared.py` line asserting `merge-rederived` is a success kind, which tests the deferral ladder's vocabulary and not this mechanism. |
| F-05 | The deleted file is BEHAVIORAL and so is legitimate to restore under P16. | It contains no `inspect`, no `ast`, no `getsource` and no source `read_text()`. Its own docstring states "REAL GIT, NOT MOCKS, for every end-to-end case", and it drove real `subprocess` git. 25 `def test_` functions. |
| F-06 | The two controls are NAMED in the deleted file as its reason for existing, so restoring them is restoring a stated contract rather than inventing coverage. | Its module docstring: "THE TWO CONTROLS ARE THE POINT OF THIS FILE, and they are why one would not suffice", enumerating the ANTI-REVERT control and the ALLOW-LIST control. `Blocks-Release` appears in its `test_the_writer_refuses_every_gate_or_attestation_key_even_if_classified` parametrization. |
| F-07 | A stale citation in shipped source still asserts the guard exists. | `runner_shared.REDERIVABLE_FRONT_MATTER_KEYS`'s comment: "`tests/test_records_only_lane_rederive.py` fails if `- Status:`, `- Readiness:`, `- Approval:`, `- Blocks-Release:` or `- Item-Dependencies:` is ever admitted, so a widening is refused rather than merely discouraged." Per F-01 and F-03 that is false in both halves. Executed plan `kl18sz` also names the path in its `- Scope-Paths:` and its pasted evidence, but that is a terminal record and MUST NOT be edited (`AGENTS.md`). |
| F-08 | No other artifact claims this restoration, so the scope does not collide. | `rg -l test_records_only_lane_rederive .aw/records/` matches only item `mgz3f1` and executed plan `kl18sz`. The three sibling restore-coverage items name different files: `ikxtkj` names five docs-cited tests (`test_flag_surface_uniformity`, `test_release_readiness`, `test_security_hardening`, `test_wtiso_taxonomy_freeze`, `test_wtiso_characterization`), `gzmr54` names `tests/test_docs.py` classes, and `f15tne` names `tests/test_turn_bounds.py`. |
| F-09 | The item's stated options are NOT settled by this plan, and one of them has been partly overtaken by a later amendment. | Spec `25kzda` gained Section 2.1b on 2026-09-27 (after the item was filed on 2026-09-22), which sends a `git-merge-conflict` on an EXECUTE lane back to the agent to resolve in its own lane, bounded by `--retry-budget`. It is implemented (`runner_shared` `merge_conflict_sendback` / `MERGE_CONFLICT_RETRY_COUNT_KEY`, tested by `tests/test_merge_conflict_sendback.py`), and `integrate_lane_branch`'s own comment states a re-derivation failure "falls straight through to the refusal below, which is then sent back to the agent in `execute_item_core` if retry budget remains (spec 25kzda 2.1b)". So an `lc4unl`-shaped lane no longer necessarily strands on a human. This REDUCES the operator toil the item weighs but does not decide (a)/(b)/(c), and it is recorded here so the maintainer weighs the options against current behavior rather than the 2026-09-22 behavior. |

## Proposed changes (ordered, validatable)

1. Recreate `tests/test_records_only_lane_rederive.py`, recovering the deleted content from `19313eed^` and re-verifying every call against current symbol signatures. Classifier arms first (E-01), so the file collects and passes before the controls are layered on.
2. Restore the ALLOW-LIST control over the writer (E-02), parametrized across `Status`, `Readiness`, `Approval` and `Blocks-Release`. This is the arm backlog `mgz3f1` depends on.
3. Restore the ANTI-REVERT control with real git (E-03), including the two-layer demonstration that widening to `Status` is refused by classifier and writer independently.
4. Prove the restored guard bites (E-04) by a RED/GREEN pair around a temporary widening of the shipped constant, reverting the source edit afterwards.
5. Reconcile the stale source comment with what is actually pinned (E-05), narrowing rather than overstating.

No change to `REDERIVABLE_FRONT_MATTER_KEYS`, to the classifier, to the writer, to `integrate_lane_branch`, or to spec `25kzda`. This plan adds coverage and corrects one comment; it alters no behavior.

## Deferred / out of scope (with reason)

- BACKLOG `mgz3f1`'s OPTIONS (a), (b) AND (c) ARE NOT DECIDED HERE. The item itself says "the decision between (a), (b) and (c) is a maintainer's, since it trades operator toil against automated writes to a gate field", and `AGENTS.md` reserves exactly that class (risk appetite, public contracts) for the human. This plan restores the guard all three options presuppose; whichever is later chosen, a widening must fail loudly first. The item therefore remains open on its decision after this plan executes.
  - Carrier: mgz3f1
- WIDENING THE ALLOW-LIST IS NOT ATTEMPTED, deliberately. Both the source header and spec `25kzda` Section 2.1a state an integration able to write a gate field automatically would be strictly worse than the conflict it resolves; option (c) in the item is explicitly forbidden by E-04's all-or-nothing rule in `kl18sz`. Nothing here relaxes that.
  - Carrier-Declined: This row records a PROHIBITION on this plan, not deferred work, so nothing is owed and there is nothing to carry. The prohibition is what the plan enforces rather than something it postpones: V-04 requires the temporary widening to be reverted and proven gone. Whether the allow-list should ever widen is the live decision on item `mgz3f1`, carried by the row above; recorded here so a reviewer does not read the silence as agreement that widening is acceptable.
- THE BROADER SUITE-TRIM COVERAGE LOSS IS NOT SWEPT. Commit `19313eed` deleted far more than this one file; items `ikxtkj`, `gzmr54` and `f15tne` already carry other parts (F-08). This plan restores only the file its own backlog item depends on, so it does not silently absorb three other items' scope.
  - Carrier-Declined: Nothing is owed BY THIS PLAN, and the outstanding work already has three durable homes that F-08 measures as naming different files: `ikxtkj` (five docs-cited tests), `gzmr54` (`tests/test_docs.py` classes) and `f15tne` (`tests/test_turn_bounds.py`). Pointing a `- Carrier:` at any one of them would misattribute this file's restoration to an item that does not name it. Whether the trim's remaining losses need a single sweeping carrier is a separate judgement this plan does not prejudge.
- EXECUTED PLAN `kl18sz` IS NOT EDITED even though it cites the deleted path (F-07), because `AGENTS.md` forbids changing what an executed plan records. A `## Workflow history` line pointing at this plan would be permissible but is not required, and is left out to keep this plan's scope to its two declared paths.
  - Carrier-Declined: Nothing is owed: the stale citation that ships in SOURCE is fixed inside this plan by E-05, and the copy inside the executed plan is a terminal record that `AGENTS.md` forbids rewriting, so there is no future work to carry. The optional history-note route remains available to a maintainer at any time and needs no tracked item to stay available.

## Scope check

- Over-scope: none. Both declared paths are necessary: `tests/test_records_only_lane_rederive.py` is the restoration itself, and `agent_workflows/runner_shared.py` is touched ONLY for the stale comment at `REDERIVABLE_FRONT_MATTER_KEYS` (E-05) plus the temporary, reverted widening used as a RED demonstration (E-04). No spec file is in scope, so no spec amendment is declared.
- Under-scope: The restored file may not reach 25 test functions if a recovered arm no longer matches a current signature; E-01 requires re-verification rather than blind paste, so an arm that no longer applies is to be dropped WITH ITS REASON stated in that E-item's evidence rather than silently omitted. The two named controls (E-02, E-03) are not eligible for that treatment and must land.

## Required tests / validation

- `python3 -m pytest tests/test_records_only_lane_rederive.py -o addopts=""` for per-test counts on the restored file (defaults cleared explicitly, per the conventions note).
- Bare `python3 -m pytest` for the full suite, to show the restoration breaks nothing. The pasted evidence must include the `N passed` summary line.
- The RED/GREEN pair of E-04/V-04, which is the only evidence that actually proves the guard bites rather than merely exists.
- `git status --short` and `git diff --stat agent_workflows/runner_shared.py` at the end, to prove no experimental widening was left behind.

## Spec / documentation sync

N/A for spec text, with reason: spec `25kzda` Section 2.1a already states the required property in full ("The keys eligible for re-derivation MUST therefore be enumerated, and widening the enumeration is a deliberate, visible change"). The defect is that the property is UNENFORCED, not that it is unstated or misstated, so the spec needs no amendment and none is declared in `- Scope-Paths:`. The only documentation-shaped change is the stale in-source comment corrected by E-05 (F-07). No file under `docs/` cites the deleted path, so item `ikxtkj`'s docs-citation scope is untouched.

## Open questions

### OQ-01: Should the restored file also pin that a re-derivation failure falls through to the Section 2.1b agent send-back?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, resolved from repository evidence at authoring rather than deferred. That fall-through is already covered by `tests/test_merge_conflict_sendback.py`, which exercises the conflict send-back end to end (`DriverConflictSendbackTests` cases a through e, including the zero-budget and unresolved-lane arms) and reads `merge_conflict_sendback` off the attempt record. Adding a second caller here would duplicate that file's subject and blur this one's, which is the allow-list and anti-revert controls. Recorded as F-09 because it changes how a maintainer should weigh the item's options, but it is not this plan's coverage to add.

### OQ-02: Should this plan set backlog `mgz3f1` to `graduated` given that it deliberately leaves the item's own decision open?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NOT THIS PLAN'S ACT. The authoring contract for this turn states the runner sets `graduated` upon verification and that the authoring turn must not change the item's status, so no status write happens here either way. The substantive point for a reviewer is recorded in the Deferred section: this plan carries the item's PREREQUISITE, not its decision, so the maintainer still owes a ruling on (a)/(b)/(c) afterwards. Flagged rather than silently implied, since a reader seeing the item graduate could otherwise assume the decision was made.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the full output of `python3 -m pytest tests/test_records_only_lane_rederive.py -o addopts=""` showing every collected test passing and the explicit count. Paste `rg -c 'REDERIVABLE_FRONT_MATTER_KEYS' tests/test_records_only_lane_rederive.py` showing a non-zero count. Additionally paste, for each classifier arm, the asserted verdict constant, so a reviewer can confirm `unknown` is asserted where `unknown` is meant and `not-this-shape` where that is meant (the three-valued distinction the source calls load-bearing). If any recovered arm was dropped, name it and state why it no longer applies.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the parametrized test ids and results for the writer-refusal cases, showing `Blocks-Release` among them PASSING. Then paste a NEGATIVE control proving the arm is non-vacuous: temporarily remove or bypass the writer's allow-list check in `rederive_front_matter`, show the `Blocks-Release` case FAILING, restore the source, and show it passing again with `git diff --stat agent_workflows/runner_shared.py` empty.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the anti-revert test output, plus the assertion text showing the target's terminal `- Status:` is required present and the incoming non-terminal one required absent. Paste evidence that REAL git produced the conflict (the fixture's git invocation and its conflicted-path list, not a hand-written merge stage). Paste the two-layer widening demonstration's output, showing the classifier arm asserting `not-this-shape` with a reason naming a DIFFERENT value, and the writer arm raising `DriverError` naming `Status`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: THE LOAD-BEARING ONE. Paste, in order: (1) the exact edit widening `REDERIVABLE_FRONT_MATTER_KEYS` to include `Blocks-Release` (a `git diff` of that one line); (2) the RED run output showing at least one FAILING test with its name; (3) the revert; (4) the GREEN run output; (5) `git diff --stat agent_workflows/runner_shared.py` and `git status --short` proving the widening is gone and no stray file remains. A restored guard that cannot be shown failing under the widening does not close this item, since silent passage under widening is the precise defect measured at F-03.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the before and after text of the `REDERIVABLE_FRONT_MATTER_KEYS` comment, and for EACH key the comment names (`Status`, `Readiness`, `Approval`, `Blocks-Release`, `Item-Dependencies`) cite the restored test function or parametrized case that enforces it. If any named key is not enforced, show that the comment was narrowed to drop it rather than left overstating. Then paste a bare `python3 -m pytest` run including its `N passed` summary line, demonstrating the whole suite is green with the restoration in place, and compare the count against the 3284-passed baseline recorded at F-03.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution; it writes no `- Readiness:` field, since that is `/plan-review`'s output and never an author's to assert.

EXECUTION CONTRACT. Commit only the two declared `- Scope-Paths:` and only through `aw commit <plan> -- <paths>`, never `git add -A` and never with `--no-verify`; do not push; do not create a tag or release. The full suite must be run BARE (`python3 -m pytest`) and its actual output pasted, never summarized or claimed. E-04 and V-02 both require a TEMPORARY source edit as a negative control: each must be reverted in the same pass and the revert proven with `git diff --stat`, because leaving a widened allow-list or a bypassed writer check in the tree would ship exactly the hazard this plan exists to prevent. This is a shared checkout, so stage nothing another party modified and verify the staged set with `git diff --cached --name-only` before committing.

POST-GATE LIFECYCLE MOVE. After every `V-*` carries pasted evidence and a non-pending `Result`, run `aw ipd lint --phase pre-transition` and require it conforming, then transition the plan to `executed` through the tooled lifecycle (`aw ipd set`), which moves the file to `.aw/records/plans/executed/`. Do not hand-edit the status line or hand-move the file. Backlog item `mgz3f1` is NOT closed `done` by this plan: it retains its own undecided question (a)/(b)/(c) per the Deferred section, and this plan is its graduation carrier only.

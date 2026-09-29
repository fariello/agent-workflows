# IPD: State the deferral passthrough's real reachability and stop the rescore docstring citing a comment that no longer exists

- Date: 2026-09-29
- Kind: child
- Concern: `runner_shared.reconcile_disposition`'s deferral passthrough (`if item.get("status") == INTEGRATION_DEFERRED_STATUS`) is DEAD on `execute_item_core`'s first score, because `execute_item_core` writes `item["status"] = "running"` at dispatch, and it is ALSO dead on the post-re-ask rescore, because `record_integration_refusal` (the only writer of `merge-retry`) runs LATER in the same body than the rescore does. `rescore_is_an_improvement`'s docstring nonetheless directs a reader to "the comment above `reconcile_disposition`'s deferral passthrough, `oc_runipd.py:6120-6132`", and that comment NO LONGER EXISTS: commit `6b94a4d9` deleted the host copy when it collapsed the function into `runner_shared`, and `oc_runipd.py` is now 5296 lines, so the cited range is past end of file. So the one reachable caller is documented by a dangling pointer, and two live comments overstate what the branch does.
- Scope: Correct the two comments that misdescribe the deferral passthrough (the dangling `oc_runipd.py:6120-6132` citation in `rescore_is_an_improvement`, and `reconcile_disposition`'s docstring rung list plus the `runrecon-02` comment that calls the branch a fall-through the exit-code fallback shares), state the passthrough's REAL reachable caller by symbol, and add a behavioral test pinning both the branch's surviving contract and its unreachability from `execute_item_core`'s two scoring points. KEEPS THE BRANCH: it is live via `reattempt_deferred_integrations` -> `resume --retry-incomplete`, so deleting it would be a behavior change, and this plan proves that rather than assuming it. EXCLUDES deleting or reordering any branch of `reconcile_disposition`, EXCLUDES touching `rescore_is_an_improvement`'s refusal list or `RESCORE_DISPOSITION_RANK`, and EXCLUDES the three other stale `oc_runipd.py:<line>` citations the same file carries (a separate class, filed not fixed).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_deferral_passthrough_reachability.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: ddzc4h
- Set: defpass
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: gyam7x

## Workflow history

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `ddzc4h`. GATE NOTE: the item carries NO `- Blocks-Release:`, so this plan inherits none; `- Work-Kind: chore` and `- Priority: low` are INHERITED from the item and are correct, because no user-perceptible behavior changes (the code edits are comments; the only new executable code is a test). THE ITEM'S CENTRAL CLAIM VERIFIES, AND ITS SCOPE WAS TOO NARROW IN ONE DIRECTION AND TOO BROAD IN ANOTHER. VERIFIED: `execute_item_core` writes `item["status"] = "running"` before dispatch (`runner_shared.py:30868`), and the first score at `runner_shared.py:31657` therefore cannot see `merge-retry`, so the passthrough is dead on the first score exactly as the item says. TOO NARROW: the item asks only whether the passthrough has "ANY reachable caller in `execute_item_core`", and the answer is that it has a reachable caller OUTSIDE it - `reattempt_deferred_integrations` sets `merge-retry` through `record_integration_refusal` (`runner_shared.py:10173`), the run ends, and `resume --retry-incomplete` requeues a `merge-retry` item (`oc_runipd.run_queue`'s status set names both `integration-deferred` and `merge-retry`), after which a LATER turn's `reconcile_disposition` can legitimately see a deferral the item still carries. So the branch is NOT dead code and MUST NOT be deleted; the defect is purely descriptive. TOO BROAD, CORRECTED HERE: the item's hypothesis that "the deferral is only ever set downstream by `record_integration_refusal`" is CONFIRMED (that is the sole `item["status"] = decision.status` write of `merge-retry`, and `deferred_integration_items` selects on it), which is what makes the item's suspicion about the comment correct. A THIRD DEFECT NOT IN THE ITEM was found by following the citation and is in scope because it is the same sentence: the cited comment was DELETED by `6b94a4d9` and the line range is past EOF, so the docstring points a reader at nothing. NOTHING HERE IS OBSOLETE: grepping the 137 pending plans for `reconcile_disposition` / `rescore_is_an_improvement` returns four files and none touches these comments (`vbhat9` deliberately excludes `runner_shared.py`, `entv1d` cites the function in a finding only, `oi0sv9` cites the `StopAtCheckpoint` call site, `wqk5s2`/`oi0sv9` neither reads nor writes the passthrough).

## Goal

Make the deferral passthrough's documentation say what is true: name its one REACHABLE route (a deferral that outlives its run and is requeued by `resume --retry-incomplete`), drop the claim that it is reachable as a first-score fall-through, and replace the dangling `oc_runipd.py:6120-6132` pointer with a live symbol citation. Lock the result with a behavioral test that both exercises the branch through its real route and proves it cannot fire at either of `execute_item_core`'s two scoring points. No runtime behavior changes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Re-measure the three claims at execution HEAD

- [ ] E-01 RE-MEASURE, at execution HEAD rather than trusting this plan's authoring numbers, all four facts the later items depend on, because `runner_shared.py` is the repository's highest-churn file and every line number below will have moved. Confirm: (a) `execute_item_core` still writes `item["status"] = "running"` before its dispatch (locate by the content string `item["status"] = "running"`, expected inside `execute_item_core`'s body and BEFORE the `spawn_executor` call); (b) the first `reconcile_disposition` call in `execute_item_core` is still positioned AFTER that write (locate by the `disposition, outcome = reconcile_disposition(` call); (c) the post-re-ask rescore call (locate by `rescored, rescored_outcome = reconcile_disposition(`) still precedes every `record_integration_refusal(` call in the same function body, which is what makes the rescore unable to see a deferral either; and (d) `oc_runipd.py` still has FEWER than 6120 lines, so the cited range is genuinely past EOF. Record the measured line numbers for use in evidence, but write none of them into a comment as a bare offset. If ANY of (a) through (d) has drifted, STOP and report which: (c) in particular is the fact that decides whether E-03's wording is correct.
  - Depends on: none
  - Expected outcome: the four facts re-confirmed at execution HEAD with their measured locations recorded, or an explicit report naming which one drifted and stopping before E-02.
  - Execution state: pending

- [ ] E-02 PROVE the passthrough's REACHABLE route exists before documenting it, so E-03 states a measured fact and not a plausible story. Establish by reading code that all three links hold: (i) `record_integration_refusal` is the ONLY writer of `INTEGRATION_DEFERRED_STATUS` onto `item["status"]` (locate by `item["status"] = decision.status`; confirm no other assignment of that constant to an item status exists in `agent_workflows/`); (ii) `reattempt_deferred_integrations` calls it for an item whose lane refused integration; and (iii) each host's `run_queue` `--retry-incomplete` status set contains BOTH `"merge-retry"` and the pre-rename `"integration-deferred"`, so a deferral that outlived its run is requeued rather than stranded. Also record the one fact that makes the branch matter: `merge-retry` is NOT in `TERMINAL_STATES` on either host, so without the explicit branch the exit-code fallback would relabel it to a TERMINAL status and destroy the deferral.
  - Depends on: E-01
  - Expected outcome: the writer-to-requeue chain confirmed link by link with each link cited by symbol, plus a recorded check that `merge-retry` is absent from both hosts' `TERMINAL_STATES`.
  - Execution state: pending

### Task group 2: Correct the three misleading comments

- [ ] E-03 REPLACE the dangling citation in `runner_shared.rescore_is_an_improvement`'s docstring. Locate the sentence by its content string `for why). By` (in the paragraph beginning `THREE STATUSES ARE NEVER REPLACEABLE IN EITHER DIRECTION`), which currently directs the reader to `the comment above :func:`reconcile_disposition`'s deferral passthrough, `oc_runipd.py:6120-6132``. Cite the LIVE location by symbol instead (the passthrough inside `runner_shared.reconcile_disposition`), with NO bare line offset. ALSO CORRECT THE CLAIM THAT SENTENCE MAKES, which E-01(c) measures: the docstring asserts `merge-retry` "is NOT in `DEFECT_REASK_SKIPPED_STATUSES`, so a re-ask can fire on a deferred item and reach the rescore", and while the membership half is TRUE the conclusion is NOT, because the only writer of that status runs later in `execute_item_core` than the rescore does. Restate it as what it is: defence in depth, for the same reason the paragraph's next two sentences already give for `interrupted` and `unknown_outcome`. DO NOT change the `never_replaceable` tuple, the rank table, or any behavior; this is docstring text only, and the entry stays.
  - Depends on: E-02
  - Expected outcome: `rescore_is_an_improvement`'s docstring cites a location that exists, no longer claims the deferral is a live pre-rescore value, and keeps `merge-retry` in the refusal tuple with its retention justified as defence in depth; no executable line of the function changes.
  - Execution state: pending

- [ ] E-04 CORRECT the two comments in `reconcile_disposition` itself that describe the passthrough as a fall-through of the ordinary scoring path. First, the `runrecon-02` comment above the outcome read (locate by the content string `declines to answer still falls through to the deferral passthrough and the exit-code fallback`): it lumps the passthrough together with the exit-code fallback as things reached when the precedence helper declines, which is true only in the LATER-TURN case and misleads a reader into thinking a first score can land there. Second, the function's own docstring rung list (locate by the content string `4. Integration deferred status fallback.`): the word `fallback` is what makes rung 4 read like a sibling of rung 5. In BOTH, name the ONE route E-02 established (a prior turn's deferral, re-scored on a later turn after `--retry-incomplete` requeued the item) and say plainly that `execute_item_core`'s own two scoring points cannot reach it. Keep both edits to comment and docstring text; change no branch, no ordering, and no return value.
  - Depends on: E-02
  - Expected outcome: both comments describe the passthrough by its real route and explicitly exclude the two `execute_item_core` scoring points, with the branch, its position after the outcome block, and its return value untouched.
  - Execution state: pending

### Task group 3: Lock it behaviorally

- [ ] E-05 ADD `tests/test_deferral_passthrough_reachability.py` pinning the passthrough's surviving CONTRACT and its unreachability as OUTCOMES, never as code structure. Three behavioral assertions, each driving real code and asserting on real returns: (1) THE CONTRACT: call `reconcile_disposition` on an item whose `status` is `INTEGRATION_DEFERRED_STATUS` with exit code 0 AND with a nonzero exit code, and assert it returns `merge-retry` BOTH times, which is what keeps a later turn from destroying a deferral the exit-code fallback would otherwise relabel; assert the returned status is absent from `TERMINAL_STATES` in the same test, so the test states WHY it matters. (2) THE NEGATIVE CONTROL that proves assertion (1) is not vacuous: the same call on an item whose `status` is `"running"` (the value `execute_item_core` actually holds at its first score) must NOT return `merge-retry`, and must return the exit-code fallback instead. (3) THE UNREACHABILITY, measured by OBSERVATION rather than by reading source: drive `execute_item_core` through the established harness in `tests/test_defect_report.py::RescoreAfterAReaskTests` (reuse its fixture shape; a launcher stub, a stubbed `integration_is_earned` that refuses, and `self_finalize`), wrap `reconcile_disposition` in a recorder that captures `item["status"]` AS PASSED at every call, and assert that NO captured value is `merge-retry` across both the first score and the post-re-ask rescore. The test MUST NOT use `inspect`, `ast`, regex over source, or any substring search of production code, MUST NOT count call sites, and MUST NOT assert any comment text survives. Name in its module docstring that assertion (3) is the one that would go red if a future change made the status reachable there, which is a legitimate signal to re-read E-03/E-04's wording rather than to loosen the test.
  - Depends on: E-01
  - Expected outcome: a new test file whose three assertions pass, whose negative control fails if the passthrough is deleted, and which reads no production source text.
  - Execution state: pending

- [ ] E-06 PROVE the new test can FAIL, because a reachability test that passes trivially is worse than none. In a THROWAWAY copy of the tree OUTSIDE this worktree (never committed), delete the two-line deferral passthrough from `reconcile_disposition` and record that E-05's assertion (1) goes RED; then restore it. ALSO record that assertions (2) and (3) still PASS with the branch deleted, which is the honest statement of what each assertion covers: only (1) guards the branch's existence, while (2) and (3) describe the surrounding reachability. Then run the full suite BARE on the real tree and paste the summary line.
  - Depends on: E-05
  - Expected outcome: pasted red output for assertion (1) against a branch-deleted scratch copy, a recorded note that (2) and (3) are insensitive to that deletion, and a pasted bare full-suite summary on the real tree.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This plan's subject matter IS an expired offset, so every citation it writes obeys the rule it is enforcing.
- TESTS ASSERT OUTCOMES, NOT CODE STRUCTURE (`GUIDING_PRINCIPLES` P16, restated in `AGENTS.md`): no `inspect`, no `ast`, no regex over production source, no caller-count or symbol-census assertions, and no assertion that a comment or docstring string survives. This constrains E-05 sharply, since the natural way to test "this branch is unreachable" is to read the source, and that is exactly what is forbidden; E-05 therefore observes real calls instead.
- `reconcile_disposition` is a SINGLE SHARED DEFINITION, and both hosts expose the same object: `tests/test_recovone_single_definition.py::TestSingleDefinitionIdentity::test_identity_pins` asserts `assertIs` between each host attribute and `runner_shared`'s. So one edit in `runner_shared.py` reaches both hosts and neither host file needs to appear in `Scope-Paths`.
- The status vocabulary is DUAL: `l2mzxn` renamed `integration-deferred` to `merge-retry`, and both spellings remain readable because the requeue set is matched against statuses read from DURABLE run directories written before the rename. Any prose this plan writes must use the constant (`INTEGRATION_DEFERRED_STATUS`) or both spellings, never the legacy one alone.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE ITEM'S CORE CLAIM IS TRUE. `execute_item_core` sets `item["status"] = "running"` before dispatch and saves state; its first `reconcile_disposition` call comes several hundred lines later in the same body. So at the first score `item["status"]` is `"running"`, never `merge-retry`, and the passthrough cannot fire. | `runner_shared.py:30868` (`item["status"] = "running"`, immediately followed by `save_state`); first score at `runner_shared.py:31657`. |
| F-02 | THE RESCORE CANNOT SEE A DEFERRAL EITHER, AND FOR A STRONGER REASON THAN THE ITEM GIVES. The item notes `merge-retry` is not in `DEFECT_REASK_SKIPPED_STATUSES` (confirmed: the frozenset holds 12 statuses and `merge-retry` is not among them), and infers a re-ask could therefore reach the rescore carrying one. But ORDER forbids it: the rescore (locate by `rescored, rescored_outcome = reconcile_disposition(`) precedes every `record_integration_refusal(` call in this body, the nearest being the review arm's (locate by `review_decision = record_integration_refusal(`) and the execute arm's later still. Between the `"running"` write and the rescore, the only assignments to `item["status"]` are `fail-lane`, `fail-begin`, `interrupted`, and the scored `disposition` itself. | `runner_shared.DEFECT_REASK_SKIPPED_STATUSES`; the `rescored, rescored_outcome = reconcile_disposition(` call versus the three `record_integration_refusal(` call sites in `runner_shared.execute_item_core` and `runner_shared.reattempt_deferred_integrations`. Probed: `INTEGRATION_DEFERRED_STATUS in DEFECT_REASK_SKIPPED_STATUSES` -> `False`. |
| F-03 | THE BRANCH IS NEVERTHELESS LIVE, so it must NOT be deleted, and this is the correction to the item's framing. `record_integration_refusal` writes `item["status"] = decision.status` (which is `merge-retry` when the ladder defers), the run can END with the item still deferred, and each host's `--retry-incomplete` requeue set explicitly names both `"integration-deferred"` and `"merge-retry"` with an in-tree comment saying a deferral "can outlive its run". A later turn's `reconcile_disposition` can then legitimately observe the status. | `runner_shared.py:10173`; `oc_runipd.run_queue`'s requeue status set (comment `integpath-03 (`51vw4y`): a DEFERRED integration can outlive its run`); twin in `agy_runipd`. |
| F-04 | WITHOUT THE BRANCH THE DEFERRAL WOULD BE DESTROYED, which is why F-03 matters rather than being a curiosity. `merge-retry` is deliberately absent from `TERMINAL_STATES` on both hosts, so `outcome_precedence_disposition` returns None for it and control would reach the exit-code fallback, relabelling it `fail-verify` (exit 0) or `fail-gate` (nonzero) - both TERMINAL, so the item would never be re-attempted. | Probed: `merge-retry` in shared / oc / agy `TERMINAL_STATES` -> `False, False, False`; `outcome_precedence_disposition(None, {"disposition": "merge-retry"})` -> `None`; `fail-verify` and `fail-gate` both in `TERMINAL_STATES` -> `True`. |
| F-05 | THE CITED COMMENT NO LONGER EXISTS, which the item does not mention and which is the most concrete defect here. `rescore_is_an_improvement`'s docstring cites `oc_runipd.py:6120-6132`; `oc_runipd.py` is 5296 lines. The comment was real when cited: it was added by `11013cb1` as `integpath-03 (`51vw4y`) E-01: PASS THE NON-TERMINAL DEFERRAL THROUGH, EXPLICITLY` / `THIS IS THE SILENT-DOWNGRADE TRAP`, and `6b94a4d9` deleted the host copy when it replaced the body with `reconcile_disposition = runner_shared.reconcile_disposition`. The prose it pointed at did NOT survive the move: `grep -n 'SILENT-DOWNGRADE' agent_workflows/*.py` matches nothing on this tree. | `wc -l agent_workflows/oc_runipd.py` -> `5296`; `git log -S 'SILENT-DOWNGRADE TRAP'` -> `6b94a4d9`, `11013cb1`; `git show 6b94a4d9 -- agent_workflows/oc_runipd.py` shows the block deleted and replaced by the one-line rebind. |
| F-06 | THE SURVIVING COMMENTS UNDERSTATE AND OVERSTATE IN DIFFERENT PLACES, so both need the same correction. `reconcile_disposition`'s docstring calls rung 4 `Integration deferred status fallback.`, and the `runrecon-02` comment says whatever the precedence helper "declines to answer still falls through to the deferral passthrough and the exit-code fallback below". Both frame the passthrough as a sibling of the exit-code fallback on the ordinary path, which F-01/F-02 refute for every `execute_item_core` score. | `runner_shared.py:29573` (docstring rung 4); `:29688` (the `falls through to the deferral passthrough` comment). |
| F-07 | EXISTING COVERAGE PINS THE CONTRACT BUT NOT THE REACHABILITY, which is the gap E-05 fills. `tests/test_runner_shared.py` drives `reconcile_disposition` on a `merge-retry` item for both hosts and asserts the passthrough returns it (exit code 0 only, no nonzero case, no negative control), and `tests/test_defect_report.py::RescoreAfterAReaskTests::test_deferral_behavior` pins the rescore's refusal using a SCRIPTED `reconcile_disposition` that RETURNS `merge-retry` - a stub, so it proves nothing about whether production can produce that value there. Nothing asserts the status is unreachable at either scoring point. | `tests/test_runner_shared.py::test_deferred_item_dependency_cascade_and_reconcile` (comment `Reconcile disposition passes deferral through`); `tests/test_defect_report.py::test_deferral_behavior`'s `def scripted(...)` returning `R.INTEGRATION_DEFERRED_STATUS`. |
| F-08 | THREE MORE STALE `oc_runipd.py:<line>` CITATIONS SURVIVE IN THE SAME FILE, found by scanning rather than assumed. `runner_shared.py` carries five such citations; besides F-05's, the two in the comments beginning `The pre-``pgq326`` dispatch branch` and `THE THREE FACTS, measured at execution inside` name host line ranges past EOF, and the ones in `SET_RETIREMENT_DONE_STATUS`'s comment and in `queue_artifact_path`'s docstring name host offsets that land on unrelated lines. They are the same defect class but a different sentence each, with no shared fix, so they are FILED and not swept here. | `grep -n 'oc_runipd\.py:[0-9]' agent_workflows/runner_shared.py` -> 5 matches; the four non-F-05 matches checked individually against `wc -l agent_workflows/oc_runipd.py` and against the content actually at each cited offset. |

## Proposed changes (ordered, validatable)

1. Re-measure F-01 through F-05 at execution HEAD and confirm the ordering fact F-02 rests on (E-01).
2. Confirm the writer-to-requeue chain that makes the branch live, and the `TERMINAL_STATES` absence that makes it necessary (E-02).
3. Repoint `rescore_is_an_improvement`'s dangling citation at a live symbol and downgrade its reachability claim to defence in depth (E-03).
4. Correct `reconcile_disposition`'s own docstring rung and the `runrecon-02` fall-through comment to name the real route (E-04).
5. Add the behavioral test: contract on both exit codes, negative control on `running`, and observed unreachability across both scoring points (E-05).
6. Prove assertion (1) can fail against a branch-deleted scratch copy, record what (2) and (3) do and do not cover, and run the bare suite (E-06).

## Deferred / out of scope (with reason)

- DELETING THE PASSTHROUGH IS REFUSED, not deferred. F-03 and F-04 together show the branch is reachable through `resume --retry-incomplete` and that its absence would convert a non-terminal deferral into a terminal status, destroying the lane's re-attempt. The item's phrasing ("whether the passthrough has ANY reachable caller") invites deletion; the measured answer is no.
- THE OTHER FOUR STALE `oc_runipd.py:<line>` CITATIONS (F-08) are left alone. Each needs its own re-measurement of what the cited code now says and where it moved, and bundling them here would put four unrelated prose edits behind one review. Recommend a single follow-up backlog item covering all four, plus the question of whether a mechanical check should refuse a `<file>:<line>` citation past EOF in tracked source (which would also catch the `agy_runipd.py` offsets in the same `THE THREE FACTS, measured at execution inside` comment).
- NO CHANGE TO `DEFECT_REASK_SKIPPED_STATUSES`. Adding `merge-retry` to it would make the docstring's claim true by construction and would also be a real behavior change (it would suppress a defect re-ask for a deferred item), which is out of this plan's descriptive fence and would need its own justification.
- NO CHANGE TO `rescore_is_an_improvement`'s refusal tuple or rank table. The entry stays for the same defence-in-depth reason the paragraph already gives for its two neighbours.

## Scope check

- Over-scope: none. `agent_workflows/runner_shared.py` receives comment and docstring edits only; the sole new executable code is a test file. The three other stale citations in the same file are deliberately untouched (F-08).
- Under-scope: the four remaining stale citations (F-08) and any mechanical guard against a past-EOF citation are not fixed here; both are recommended as a follow-up backlog item in Deferred. Neither host driver file is edited, which is correct rather than a gap: the function is a single shared definition and both hosts rebind the same object (Step 0).

## Required tests / validation

- `python3 -m pytest tests/test_deferral_passthrough_reachability.py` for the new file, plus a run with `-o addopts=""` when per-test counts are needed.
- `python3 -m pytest tests/test_runner_shared.py tests/test_defect_report.py tests/test_recovone_single_definition.py` for the three files whose existing assertions touch `reconcile_disposition`, the rescore, and the single-definition identity.
- `python3 -m pytest` BARE for the full suite (the configured `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; do not add flags).
- The falsification run in E-06 against a throwaway branch-deleted copy outside this worktree.

## Spec / documentation sync

N/A with reason. No `.spec.md` governs `reconcile_disposition`'s comment text, and no `- Scope-Paths:` entry is a spec file, so neither runner will announce a declared spec edit for this plan. The two specs that do govern nearby behavior are unchanged BY DESIGN and were checked rather than assumed: `c4gd2h` R22 (never record a disposition the runner did not observe) is untouched because no branch, ordering, or return value changes, and `25kzda` says nothing about the deferral passthrough's documentation. The documentation being corrected lives INSIDE the changed file, which is where this repository keeps it.

## Open questions

### OQ-01: Should a mechanical check refuse a `<file>:<line>` citation that points past end of file in tracked source?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: DEFERRED to the follow-up backlog item in Deferred, not resolved here. The repository already forbids a bare line offset as a citation (spec `ipd-structure-and-linting` Section 10.2, advisory `IPD-C801`) but enforces it only for IPD prose, while F-05 and F-08 are offsets in PYTHON COMMENTS, which nothing checks. A guard is plausible and cheap for the past-EOF case specifically (a citation naming a line beyond the file's length is wrong with no judgement call), but the far more common failure is an offset that still resolves to the WRONG line, which no mechanical check can catch. Deciding the bound belongs with the four-citation sweep, where the sample is large enough to say whether the cheap half is worth having; deciding it here would put a new repo-wide check behind a two-comment fix.

### OQ-02: Is `--retry-incomplete` the ONLY route by which a `merge-retry` item reaches `reconcile_disposition` again?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as "it is the only route that reaches a NEW TURN's score, and one other route reaches the status without a score". The requeue set in each host's `run_queue` is what converts a surviving deferral back to `queued` for a fresh turn. The in-run ladder (`reattempt_deferred_integrations`) re-attempts the INTEGRATION with no agent turn and therefore never calls `reconcile_disposition` at all, and `resolve_exhausted_deferrals` rewrites the status to `fail-merge` directly. This distinction is exactly what E-04 must state, which is why it is answered in the plan rather than left for the executor: the branch's route is "a later turn after a requeue", not "the ladder".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the command output establishing each of E-01's four facts at execution HEAD: the `grep -n 'item\["status"\] = "running"' agent_workflows/runner_shared.py` hit with its line number, the line numbers of the first-score and rescore `reconcile_disposition` calls, the line numbers of every `record_integration_refusal(` call in `execute_item_core`, and `wc -l agent_workflows/oc_runipd.py`. State in one line whether the rescore precedes every `record_integration_refusal` call (F-02's ordering fact) and whether `oc_runipd.py` is still shorter than 6120 lines. If any fact drifted from this plan's authoring numbers, the pasted output must show the NEW value and the report must say so explicitly rather than silently adopting it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `grep -n` output showing every assignment of `INTEGRATION_DEFERRED_STATUS` (or `decision.status`) to an item status across `agent_workflows/`, demonstrating `record_integration_refusal` is the sole writer; paste the `--retry-incomplete` status set from ONE host showing both `"integration-deferred"` and `"merge-retry"` present; and paste the executed probe `python3 -c` output for `merge-retry` membership in `runner_shared`, `oc_runipd`, and `agy_runipd` `TERMINAL_STATES` (all three must print False) plus `outcome_precedence_disposition(None, {"disposition": "merge-retry"})` printing `None`. A missing link means E-03/E-04's wording is unsupported: stop and report rather than documenting an unproven route.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the FULL edited paragraph of `rescore_is_an_improvement`'s docstring. Confirm by inspection, stating each as a separate line: (a) it contains no `oc_runipd.py:` substring and no bare line offset; (b) it cites the passthrough by symbol; (c) it no longer asserts a re-ask can reach the rescore carrying a deferral, and instead labels the entry defence in depth; and (d) `merge-retry` is STILL in the `never_replaceable` tuple. Paste `git diff --stat` for the file proving only comment/docstring lines changed in this item, and paste `python3 -m pytest tests/test_defect_report.py` output showing the rescore tests still pass, since they assert the behavior this docstring describes.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste both edited comment blocks in full (the `reconcile_disposition` docstring rung list and the `runrecon-02` fall-through comment). Confirm on separate lines that each names the later-turn-after-requeue route, that each explicitly says `execute_item_core`'s own scoring points cannot reach the branch, and that neither describes rung 4 as a `fallback` sibling of rung 5. Paste `git diff` for `reconcile_disposition`'s body showing the executable lines are IDENTICAL (the `if item.get("status") == INTEGRATION_DEFERRED_STATUS:` branch, its position after the `outcome_precedence_disposition` block, and the return tuple all unchanged).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_deferral_passthrough_reachability.py -o addopts=""` output showing every test passing with its node ids visible. Paste the new file's assertion for the observed-status recorder, showing it asserts on values CAPTURED FROM REAL CALLS and not on source text. Confirm on one line each that the file imports none of `inspect`/`ast`, performs no regex or substring search over any `agent_workflows/*.py` content, asserts no call counts as a correctness proxy, and asserts no comment text survives. Also confirm the nonzero-exit case and the `running` negative control are both present, since assertion (1) alone would pass against a broken implementation that returned `merge-retry` unconditionally.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the RED output from running the new test file against the throwaway branch-deleted copy, showing assertion (1) failing and naming the observed wrong status (expected `fail-verify` or `fail-gate` in place of `merge-retry`). Paste the same run's result for assertions (2) and (3), which must PASS, and state in one line that this is the honest scope of each assertion rather than a defect in the test. Then paste the BARE `python3 -m pytest` summary line from the real tree (the `N passed` line; do not add `-q`, which would suppress it). State the scratch location was outside this worktree and was not committed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THE EXECUTION CONTRACT. Commit only the two paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push. Run the suite BARE as `python3 -m pytest` and paste ACTUAL output for every test claim; do not claim a pass that was not run. Other agents and humans may be working concurrently in this checkout, so verify the staged set with `git diff --cached --name-only` before committing and unstage anything that is not yours with `git restore --staged <path>`; `runner_shared.py` is a high-traffic file and a co-worker's edit to it must not enter this commit.

WHAT AN EXECUTOR MUST NOT DO. Do not delete or reorder any branch of `reconcile_disposition`: F-03 and F-04 establish the passthrough is live through `resume --retry-incomplete` and that its removal would convert a non-terminal deferral into a terminal status. Do not add `merge-retry` to `DEFECT_REASK_SKIPPED_STATUSES` to make the old docstring claim true; that is a behavior change outside this fence. Do not touch the other four stale `oc_runipd.py:<line>` citations (F-08). Do not satisfy E-05 with a source-reading test: the reachability assertion must observe real calls, per `GUIDING_PRINCIPLES` P16. Do not change backlog `ddzc4h`'s `- Status:` by hand; the runner sets `graduated` on verification.

POST-GATE LIFECYCLE. After every `E-*` is performed and every `V-*` carries pasted, non-empty observed evidence, run `aw ipd lint --phase pre-transition` and finalize through the tooled path so the plan moves to `.aw/records/plans/executed/` with a scope-reconciled, path-scoped commit. Do not hand-edit terminal state. If E-01 reports drift that invalidates F-02's ordering claim, STOP before E-03: the wording of both comment fixes depends on it, and documenting an unproven route would reproduce the exact defect this plan exists to correct.

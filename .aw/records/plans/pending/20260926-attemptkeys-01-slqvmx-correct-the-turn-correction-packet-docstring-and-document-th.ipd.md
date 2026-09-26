# IPD: Correct the turn_correction_packet docstring and document the prior-attempt allowlist's driver-only contract

- Date: 2026-09-26
- Kind: child
- Concern: THE PRIOR-ATTEMPT ALLOWLIST SILENTLY DROPS EVERY KEY NOT ON IT, AND ONE DOCSTRING TELLS THE NEXT AUTHOR THE OPPOSITE. `lane_containment.prior_attempt_summary` returns, for an ISOLATED turn (the default for an execute item), only the keys in `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` (25 keys). Measured with `rg -o 'attempt(_record)?\["([a-z_]+)"\]\s*='` over `agent_workflows/`: at HEAD `61ef21d8`, 80 distinct keys were assigned onto attempt records that way, of which 63 were not allowlisted; RE-MEASURED AT REVIEW (HEAD `027e2f69`) the figures are 85 and 68, the five new keys being `accounting_error`, `session_reconciliation_error` (both from `zrvtm2`, now executed) and `review_shared_commit`/`review_shared_commit_refused`/`review_shared_committed_paths`. The pattern misses dict-literal writes, so these counts are INDICATIVE, NOT EXACT, and they DRIFT with ordinary merges: treat the magnitude ("most attempt keys are driver-only") as the durable fact and re-derive the numbers at execution rather than trusting either pair. That drop is CORRECT for containment (spec `7ckptx` R1.1: path-bearing keys such as `prompt`, `worktree`, `verify_log` must not leak), but nothing at the allowlist says so, and `runner_shared.turn_correction_packet`'s docstring states falsely that the packet "is recorded on the ATTEMPT under the allowlisted `turn_correction` key, so it reaches the next turn's prompt through that one channel". Measured: `"turn_correction" in _PRIOR_ATTEMPT_SAFE_KEYS` is `False`, and `prior_attempt_summary({"turn_correction": {...}, "session_id": "s", "exit_code": 0, "finalize_refused": "r"}, Path("/tmp"))` returns `{'exit_code': 0, 'finalize_refused': 'r'}`. The packet actually arrives through `runner_shared.build_correction_notice`, whose docstring and `build_prompt`'s comment state this correctly. A SECOND CONDITION THE CONTRACT MUST NAME (added at review, PR-002): the projection is reached ONLY on a RECOVERY turn -- `build_prompt` computes `prior = item.get("attempts", [])[-1] if recovery and item.get("attempts") else None`, and `prior_attempt_summary(None, lane_root)` returns `None` -- so on a FIRST turn NO attempt key reaches the agent at all, allowlisted or not. An author who reads only "add your key to the allowlist" will still find their fact absent from the first turn's prompt, which is the same silent trap one step further on.
- Scope: IN: (a) correct `turn_correction_packet`'s "WHICH CONSTRUCTION PATH CARRIES IT" paragraph to name `build_correction_notice` as the delivery channel and state that `turn_correction` is deliberately NOT allowlisted; (b) replace the three-line comment above `_PRIOR_ATTEMPT_SAFE_KEYS` with a documented contract (a new attempt key is DRIVER-ONLY unless added here; delivering a fact to the agent must go through an explicit prompt notice or an allowlist entry; adding an entry requires that the value can never carry a filesystem path), with a short `_PRIOR_ATTEMPT_DRIVER_ONLY_EXAMPLES` comment block naming representative driver-only keys and why; (c) one sentence in `prior_attempt_summary`'s docstring pointing at that contract; (d) ONE behavioral test. OUT: any change to the projection's behavior or to the allowlist's members (spec `7ckptx` R1.1 fail-closed); a key-enumerator or any source-scanning test (maintainer ruling 2026-09-26); a denylist (the backlog's option (b), which inverts the fail-closed direction).
- Scope-Paths: agent_workflows/lane_containment.py, agent_workflows/runner_shared.py, tests/test_prior_attempt_projection.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: ytrz7u
- Set: attemptkeys
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: slqvmx

## Workflow history
- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 all FIXED, none deferred, no open question raised. Reviewed at HEAD `027e2f69`; `aw ipd lint --phase author` conformed before revision. All three authored findings reproduced exactly (E-01 run verbatim: `False False True` and `{'exit_code': 0, 'finalize_refused': 'r'}`), spec `7ckptx` R1.1/R1.3 and the maintainer ruling on backlog `ytrz7u` both verified, and the design (document, change no behavior) is right. Added two gaps: F-5, the drafted contract documented only the allowlist gate while `build_prompt` populates `prior` ONLY on a recovery turn and reads only `attempts[-1]`, so an author adding a key would still get silence on a first turn (split out as E-05, with E-06 gaining a first-turn assertion and V-06 a matching control); and F-6, E-02's replacement span began one sentence too late, leaving the dangling "the plan's E-04" reference to executed plan `xipfy1` in shipped code. Corrected three stale authored facts: the key census drifted 80/63 -> 85/68 (five keys from merged work, now re-derived by E-01 rather than cited), `zrvtm2` is EXECUTED not pending, and F-3 undercounted its own supporting evidence (four correct descriptions, not two). Verified the V-06 sabotage actually changes the projection output before requiring it. PR-007 records that my own first revision tripped the IPD-Z602 density advisory on E-03, so E-03 was split into E-03/E-04/E-05 (contract, example block, second gate) with the test item becoming E-06; re-linted conforming. Findings recorded in `.aw/records/reviews/20260926-attemptkeys-01-slqvmx-correct-the-turn-correction-packet-docstring-and-document-th.review.md`.

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog ytrz7u on the maintainer's batch-graduation instruction and the 2026-09-26 ruling (no source-scanning tests; fix the false docstring and document the driver-only contract, behavior unchanged). Allowlist membership and the projection's output were re-measured at HEAD 61ef21d8.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Stop the prior-attempt projection from being a silent trap: correct the one docstring that claims `turn_correction` rides the allowlist, and write the allowlist's contract where the next author adding an attempt key will read it, with the projection's behavior unchanged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE at the executing HEAD and paste: `python3 -c "from agent_workflows import lane_containment as L; from pathlib import Path; print('turn_correction' in L._PRIOR_ATTEMPT_SAFE_KEYS, 'session_id' in L._PRIOR_ATTEMPT_SAFE_KEYS, 'finalize_refused' in L._PRIOR_ATTEMPT_SAFE_KEYS); print(L.prior_attempt_summary({'turn_correction': {'x': 1}, 'session_id': 's', 'exit_code': 0, 'finalize_refused': 'r'}, Path('/tmp')))"`, and `rg -n "allowlisted .turn_correction" agent_workflows`. ALSO re-derive the indicative key census at THIS HEAD (`rg -o 'attempt(_record)?\["([a-z_]+)"\]\s*=' agent_workflows/ -r '$2' --no-filename | sort -u | wc -l`, and the count of those not in the allowlist) and paste both numbers; they were 80/63 at `61ef21d8` and 85/68 at review HEAD `027e2f69`, so they WILL have moved again -- record what you measure and do NOT treat either earlier pair as the bar (the property is "most attempt keys are driver-only", not any particular number). If `turn_correction` IS now allowlisted (for example because a concurrent plan added it), the docstring may be true: STOP E-02 and report, and do E-03 through E-06 only.
  - Depends on: none
  - Expected outcome: `False False True`; `{'exit_code': 0, 'finalize_refused': 'r'}`; one `rg` hit in `runner_shared.turn_correction_packet`; a re-derived census whose not-allowlisted count is a large majority of the total.
  - Execution state: pending

### Task group 2: documentation

- [ ] E-02 CORRECT `runner_shared.turn_correction_packet`'s docstring paragraph "WHICH CONSTRUCTION PATH CARRIES IT". Replace the sentences from "It is the EXISTING recovery-prompt channel" through "through that one channel." with, in substance: the packet is recorded on the attempt under `turn_correction` for the RECORD, and it reaches the next turn through `build_correction_notice`, which `build_prompt` renders as its own notice; `turn_correction` is deliberately NOT in `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS`, so the `Prior attempt:` line does not carry it on an isolated turn (the first shape tried, measured inert by `xipfy1`). ALSO FIX THE PARAGRAPH'S OPENING CLAUSE (added at review, PR-003), which the original replacement span did not reach: it reads "stated because the plan's E-04 demands the path be NAMED rather than described", where "the plan" is `xipfy1` (now EXECUTED, at `.aw/records/plans/executed/20260908-retrywire-01-xipfy1-...ipd.md`). A bare "the plan" in shipped code reads as the CURRENT plan and sends a future reader to the wrong document, so either name `xipfy1` explicitly or drop the justification clause; do not leave the dangling deictic. Keep the `run_packet.build_step_packet` sentence and the "WHAT IS OMITTED" paragraph unchanged. Change no code.
  - Depends on: E-01
  - Expected outcome: `rg -n "allowlisted .turn_correction" agent_workflows` returns nothing; the paragraph names `build_correction_notice`; `rg -n "the plan's E-04" agent_workflows` returns nothing.
  - Execution state: pending

- [ ] E-03 DOCUMENT THE CONTRACT at `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS`. Replace the existing `#:` comment with a block stating four points. (1) WHAT IT GUARANTEES: an isolated turn sees only these keys, because every other attempt key may carry an absolute driver-side path (spec `7ckptx` R1.1), and dropping is fail-closed. (2) THE CONTRACT FOR A NEW KEY: any key written onto an attempt record is DRIVER-ONLY by default and will NOT reach an isolated agent. (3) HOW TO DELIVER A FACT TO THE AGENT: either render an explicit prompt notice (the supported route, for example `runner_shared.build_correction_notice` for `turn_correction`) or add the key here, and only if its value can never carry a filesystem path. (4) WHY THE FAILURE IS SILENT: a unit test asserting on the attempt dict still passes, so the author must check the rendered prompt of an ISOLATED turn (as `tests/test_finalize_sendback.py` does for `finalize_refused`). Do NOT change the tuple's members or the function body. The driver-only example list and the second gate are E-04 and E-05.
  - Depends on: E-01
  - Expected outcome: `git diff agent_workflows/lane_containment.py` shows only comment lines added at the allowlist; the tuple and `prior_attempt_summary`'s `return` lines are byte-identical.
  - Execution state: pending

- [ ] E-04 ADD THE DRIVER-ONLY EXAMPLE BLOCK. Add a `# _PRIOR_ATTEMPT_DRIVER_ONLY_EXAMPLES` comment block beneath the E-03 contract (comments only, no new symbol, nothing reads it) listing representative driver-only keys with a one-phrase reason each, each verified present in the tree at execution: `prompt`/`worktree`/`verify_log`/`lane_plan_path` (absolute paths), `session_id` (host session handle, driver bookkeeping), `turn_correction` (delivered by its own notice), `suite_baseline` (driver-side gate state). All seven were re-verified present at review HEAD `027e2f69`. Do NOT list `cost` or `tokens`: they ARE allowlisted, so naming them as driver-only would state the opposite of the truth.
  - Depends on: E-03
  - Expected outcome: the block names seven keys, each confirmed by `rg` to be assigned onto an attempt record at the executing HEAD, and none of them allowlisted.
  - Execution state: pending

- [ ] E-05 DOCUMENT THE SECOND GATE, which the allowlist does not control (added at review, PR-002). State in the same block that membership is NECESSARY BUT NOT SUFFICIENT: `runner_shared.build_prompt` populates `prior` only when `recovery` is true (`prior = item.get("attempts", [])[-1] if recovery and item.get("attempts") else None`, and `prior_attempt_summary(None, lane_root)` returns `None`), so a FIRST turn carries NO prior-attempt key at all whether or not it is allowlisted, and only `attempts[-1]` is ever read. Say plainly that a fact needed on a first turn must be rendered as its own notice, because an author who adds a key here and expects it on turn one has walked into the same silent trap one step further on. Add one sentence to `prior_attempt_summary`'s docstring pointing at the whole block.
  - Depends on: E-03
  - Expected outcome: the block states both gates; `prior_attempt_summary`'s docstring points at it; `git diff` still shows only comment and docstring lines.
  - Execution state: pending

### Task group 3: prove behavior is as documented

- [ ] E-06 ADD `tests/test_prior_attempt_projection.py` with ONE behavioral test class (no `inspect.getsource`/`read_text` of package source, maintainer ruling 2026-09-26): calling `lane_containment.prior_attempt_summary` with a `lane_root` (isolated) on an attempt dict carrying `turn_correction`, `session_id`, `prompt` (an absolute path string), `exit_code`, and `finalize_refused` returns a dict WITHOUT `turn_correction`, `session_id`, or `prompt` and WITH `exit_code` and `finalize_refused` unchanged; the same dict with `lane_root=None` (non-isolated, spec `7ckptx` R1.3) is returned unchanged including all five keys; and `None` input returns `None`. ADD ONE MORE ASSERTION for the second gate the contract now documents (review PR-002): render an isolated FIRST-turn prompt via `runner_shared.build_prompt(..., recovery=False, lane_root=<lane>)` on an item that already carries an attempt with an allowlisted key (`finalize_refused`), and assert the prompt line reads `Prior attempt: none` -- i.e. allowlist membership alone does NOT put a fact in a first turn's prompt. This is the assertion that makes the documented contract testable rather than merely stated, and it complements `tests/test_finalize_sendback.py`, which covers the RECOVERY direction. Name each test so its failure message explains the contract (e.g. `test_isolated_projection_drops_driver_only_keys_and_keeps_allowlisted_ones`, `test_a_FIRST_turn_carries_no_prior_attempt_even_for_an_allowlisted_key`).
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: passes before and after (behavior is unchanged by design); it pins the documented contract so a future allowlist or projection change that leaks `session_id`/`turn_correction`, drops an allowlisted key, or starts populating `prior` on a first turn, goes red.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec `7ckptx` R1.1/R1.3: an isolated turn's prompt names nothing outside the lane; a non-isolated turn gets the record unchanged. `prior_attempt_summary` implements both, and its docstring says path-valued keys are "DROPPED, not rewritten". Both requirement ids verified present in the approved spec at review.
- `runner_shared.build_correction_notice` and the comment in `build_prompt` ("retrywire (`xipfy1`) E-04 ... MEASURABLY INERT") already describe the correct delivery channel; only `turn_correction_packet`'s docstring disagrees. Re-measured at review: FOUR descriptive references exist and all four are correct, so the wrong one is genuinely isolated (see F-3).
- The projection has exactly ONE caller, `runner_shared.build_prompt`, and it is reached only on a RECOVERY turn, reading `attempts[-1]`. That second gate is as load-bearing as the allowlist for anyone trying to deliver a fact to an agent (F-5).
- `tests/test_finalize_sendback.py` already asserts `finalize_refused` membership and that it survives the projection; this plan adds the complementary drop-side assertion rather than duplicating those.
- Tests are behavioral only (maintainer ruling 2026-09-26); run BARE `python3 -m pytest`, narrowed runs with `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Authored at HEAD `61ef21d8`; every row RE-VERIFIED at review HEAD `027e2f69` on 2026-09-26, with the two corrections noted in-row.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MEDIUM | `runner_shared.turn_correction_packet` docstring | Claims `turn_correction` is allowlisted and reaches the prompt via `Prior attempt:`. It is not and does not. CONFIRMED at review, unchanged. | `'turn_correction' in L._PRIOR_ATTEMPT_SAFE_KEYS` -> `False`; projection output omits it; one `rg` hit for "allowlisted `turn_correction`" |
| F-2 | LOW | `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` | No stated contract for new keys; most written keys are silently driver-only. COUNTS CORRECTED at review: 85 assigned / 68 not allowlisted at `027e2f69`, against the authored 80/63 at `61ef21d8`. The delta is five keys landed by merged work (`accounting_error`, `session_reconciliation_error`, `review_shared_commit`, `review_shared_commit_refused`, `review_shared_committed_paths`), which is itself evidence the census DRIFTS and must be re-derived rather than cited. | re-derived at review with the same `rg` pattern; delta attributed by `comm` against the `61ef21d8` key set |
| F-3 | INFO | delivery | The correct channel exists and is documented elsewhere. CORRECTED at review: it is FOUR other places, not two -- `build_correction_notice`'s docstring, `build_prompt`'s comment, the `finalback` section header comment ("THE FEEDBACK CHANNEL IS ALREADY BUILT"), and `build_prompt`'s inline note at the projection call. The one wrong description is genuinely isolated, which strengthens the case that this is a docstring fix and not a design question. | `rg -n 'prior_attempt_summary' agent_workflows/` -> 6 hits, 4 descriptive and all correct |
| F-4 | INFO | overlap | CORRECTED at review: `zrvtm2` is NOT pending, it is EXECUTED (`.aw/records/plans/executed/20260925-intrmeta-01-zrvtm2-...ipd.md`, `- Status: executed`) and its keys are already in the tree. Its substance holds: `cost`/`tokens` ARE allowlisted, `session_id` is NOT, and neither is `accounting_error` or `session_reconciliation_error`. No ordering dependency either way, since this plan changes no behavior. | `find .aw/records/plans -name '*zrvtm2*'` -> `executed/`; membership re-measured for all four keys |
| F-5 | MEDIUM (ADDED at review) | `runner_shared.build_prompt`, the `prior` computation | **ALLOWLIST MEMBERSHIP IS NECESSARY BUT NOT SUFFICIENT, AND THE PLANNED CONTRACT OMITTED THE SECOND GATE.** `prior` is populated only on a RECOVERY turn (`... if recovery and item.get("attempts") else None`), and `prior_attempt_summary(None, lane_root)` returns `None`, so a FIRST turn carries no prior-attempt key at all however the allowlist reads; it also reads only `attempts[-1]`. An author following a contract that says only "add your key to the allowlist" would still find the fact absent from turn one. | measured: the guarded expression in `build_prompt`; `prior_attempt_summary(None, Path('/tmp'))` -> `None` |
| F-6 | LOW (ADDED at review) | `runner_shared.turn_correction_packet` docstring, opening clause | **A DANGLING "the plan" DEICTIC SURVIVES THE PLANNED EDIT.** The paragraph opens "stated because the plan's E-04 demands the path be NAMED rather than described", where "the plan" is `xipfy1` (executed 2026-09-08). E-02's replacement span begins at the NEXT sentence, so the stale reference would remain in shipped code, reading to a future maintainer as the current plan. | `rg -n "the plan's E-04" agent_workflows` -> 1 hit, above E-02's quoted start anchor; `xipfy1` E-04 located in `executed/` |

## Proposed changes (ordered, validatable)

1. E-01 re-measures membership and the projection.
2. E-02 corrects the false docstring.
3. E-03 documents the contract beside the allowlist; E-04 adds the driver-only example list; E-05 documents the recovery-only second gate.
4. E-06 adds the behavioral tests of the documented contract, including the first-turn gate.

## Deferred / out of scope (with reason)

- A test that enumerates attempt keys and fails when one is neither allowlisted nor marked driver-only (backlog option (a)).
  - Carrier-Declined: maintainer ruling 2026-09-26, no source-scanning tests.
- Replacing the allowlist with a denylist (backlog option (b)).
  - Carrier-Declined: inverts the fail-closed containment direction spec `7ckptx` R1.1 requires; a new path-bearing key would leak by default.
- Adding any key (e.g. `session_id`) to the allowlist.
  - Carrier-Declined: no current consumer needs it in an isolated prompt; behavior is deliberately unchanged here.

## Scope check

- Over-scope: none.
- Under-scope: none.
- Scope-Paths justification: `lane_containment.py` (comment and docstring), `runner_shared.py` (one docstring), new test file.

## Required tests / validation

- `tests/test_prior_attempt_projection.py` (new), one behavioral class; passes before and after, since behavior is unchanged.
- `tests/test_finalize_sendback.py` stays green.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- N/A for specs: spec `7ckptx` R1.1/R1.3 already require exactly the behavior documented here; no `.spec.md` is in `- Scope-Paths:`.
- No user-facing docs change (internal docstrings and comments only).

## Open questions

### OQ-01: Add a key-enumerator test (backlog option (a))?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: No. Maintainer ruling 2026-09-26 (recorded on backlog `ytrz7u`'s history): no source-scanning tests; fix the false docstring and document the driver-only keys next to the allowlist, behavior unchanged.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `python3 -c` output, the `rg` hit, and the re-derived census pair (total distinct assigned keys / not-allowlisted) measured at the executing HEAD. State the pair you measured rather than repeating 80/63 or 85/68.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the docstring diff and `rg -n "allowlisted .turn_correction" agent_workflows` returning nothing (exit 1). ALSO paste `rg -n "the plan's E-04" agent_workflows` returning nothing, which is the F-6 fix.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `lane_containment.py` diff for the contract block, showing only `#` comment lines added; paste the E-01 `python3 -c` command re-run with identical output (behavior unchanged, tuple members untouched). Quote the four numbered points so the contract is verifiably complete rather than merely rewritten.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the example block, and for EACH of the seven named keys paste the `rg` hit proving it is assigned onto an attempt record at the executing HEAD plus a membership check showing it is NOT allowlisted. Also paste the membership check for `cost` and `tokens` showing they ARE allowlisted, which is the negative proving the block does not misclassify them.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: quote the sentence(s) stating the RECOVERY-ONLY gate and the `attempts[-1]` limit (F-5), and paste the `build_prompt` line they describe so the documentation is checked against the code rather than against memory. Paste `prior_attempt_summary(None, Path('/tmp'))` returning `None`. Paste the one added `prior_attempt_summary` docstring sentence.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_prior_attempt_projection.py tests/test_finalize_sendback.py -o addopts="" -q` passing with counts; then, to show the new test is not vacuous, temporarily add `"session_id"` to `_PRIOR_ATTEMPT_SAFE_KEYS` and paste the new test FAILING, then restore and paste it passing. (Verified at review that this sabotage does change the projection's output: with it, `prior_attempt_summary` returns `{'exit_code': 0, 'finalize_refused': 'r', 'session_id': 's'}` instead of `{'exit_code': 0, 'finalize_refused': 'r'}`, so the control is real and not decorative.) SEPARATELY show the first-turn assertion is not vacuous: temporarily drop `and item.get("attempts")`'s `recovery` guard in `build_prompt` (or otherwise force `prior` to populate on a first turn) and paste `test_a_FIRST_turn_carries_no_prior_attempt_even_for_an_allowlisted_key` FAILING, then restore and paste it passing. Paste the bare `python3 -m pytest` summary BEFORE and AFTER and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Documentation and one test file, no behavior change: a false docstring in `turn_correction_packet` is corrected (plus a dangling "the plan" reference beside it), the prior-attempt allowlist gains a written contract saying new attempt keys are driver-only unless deliberately added and that allowlist membership alone still does not reach a FIRST turn, and behavioral tests pin that driver-only keys are dropped for an isolated turn, that allowlisted keys survive, and that a first turn carries no prior attempt at all. Per the maintainer's 2026-09-26 ruling there is no key-enumerator or source-scanning test.

WHAT THE REVIEW ADDED. The plan's three authored findings all reproduced exactly, and its design (document, do not change behavior) is right. Two gaps were added as F-5 and F-6: the contract as drafted documented only the allowlist gate and would have left an author still trapped one step further on, since the projection is reached only on a recovery turn; and E-02's replacement span started one sentence too late, leaving a stale cross-plan reference in shipped code. Two authored findings carried stale numbers and one a stale status (`zrvtm2` is executed, not pending), corrected in place with the drift explained rather than silently re-stated.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the three paths in `- Scope-Paths:`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-04 must show the new test going red under a deliberate allowlist leak.

Commit ONLY paths in `- Scope-Paths:` through `aw commit slqvmx -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `ytrz7u` `done` with `--evidence` citing the executed plan.

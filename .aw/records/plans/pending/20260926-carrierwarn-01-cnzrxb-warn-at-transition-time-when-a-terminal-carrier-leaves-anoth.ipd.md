# IPD: Verify a finished carrier with an agent instead of failing on it, and fail only on abandoned carriers

- Date: 2026-09-26
- Kind: child
- Concern: A pending plan can hand deferred work to another plan or backlog item (`- Carrier: <id6>`). When that carrier FINISHES, `check.ipd-uncarried-obligation` calls the handed-off work unowned and reports an ERROR, both in CI (`aw check plans`, fail-closed, which turned main red twice on 2026-09-26: 8ud1is -> 0yrtne, a6xbso -> 8apjpp, both times the carrier HAD done the work) and at a plan's own pre-transition finalize gate. Nothing re-checks the OTHER plans that named a carrier at the moment it finishes, and the runner's retry instructions do not tell the agent how to resolve this case. The checker cannot tell 'finished and did it' from 'finished without doing it', so a judgement is needed, and the maintainer ruled that an agent makes it.
- Scope: IN: split the terminal verdict into FINISHED (executed, done) vs ABANDONED (superseded, not-executed, parked); in `aw check` a FINISHED carrier becomes a non-failing 'needs verification' finding while ABANDONED stays an error; a reverse lookup of pending plans that name a given carrier; in a run, after a plan finalizes, the driver gives the SAME agent (same lane, same session) a verification turn for each affected row with instructions to record `Carrier-Evidence` if the work was done or otherwise fix the row (re-point to a live owner, or do the work) and justify any out-of-lane edit; a 'no'/unresolved answer is sent back through the existing correction budget; the finalize-refusal retry path recognizes a FINISHED-carrier refusal as retryable with the same instructions; outcome tests; one CHANGELOG line. OUT: auto-editing other plans without an agent; aw attention surfacing.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/ipd_lint.py, agent_workflows/runner_shared.py, tests/test_carrier_reverse_lookup.py, tests/test_carrier_finished_verification.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: zi2uzu
- Set: carrierwarn
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: cnzrxb

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REDESIGNED per maintainer ruling 2026-09-26 (asked via question tool): a carrier that FINISHED is not an automatic error; an agent verifies it in the run (yes = record proof, no = fix it or send back), CI does not fail on a finished carrier but still fails on an abandoned one. Replaces the warn-only design.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog zi2uzu: warn at finalize, rollup and backlog done/parked when another pending plan names the transitioning artifact as a Carrier.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A carrier that FINISHED no longer turns CI red or strands a plan. Instead an agent checks whether the finished carrier actually did the handed-off work: if yes it records the proof (`Carrier-Evidence`), if not it fixes the row (hands it to a live owner or does the work) with a justified out-of-lane edit, and only an unresolved 'no' fails. A carrier that was ABANDONED (superseded, not-executed, parked) still fails, because then the work truly has no owner.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Tell finished from abandoned

- [ ] E-01 In `check_engine`, split `_CARRIER_TERMINAL_STATUSES` (~:5730, currently executed/superseded/not-executed/done/parked) into `_CARRIER_FINISHED_STATUSES = {"executed", "done"}` and `_CARRIER_ABANDONED_STATUSES = {"superseded", "not-executed", "parked"}`. Make `_resolve_carrier` (~:5904) return a new verdict `"finished"` when every owner is finished (and none live), `"terminal"` (renamed in the detail text to abandoned) when any owner is abandoned and none live or finished. Thread it through `evaluate_carrier_obligation` so a `finished` carrier yields a `CloseVerdict` with severity `warn` and code `check.ipd-carrier-finished-unverified` whose detail says: `carrier <id6> finished (<status>); an agent must confirm it did this work and record Carrier-Evidence, or re-point the row`. Register the new rule in the rule table (~:553, beside `check.ipd-uncarried-obligation`) at warning severity so `aw check plans` does NOT exit nonzero on it. `ipd_lint._merge_durable_carrier` (~:2129) surfaces it as an ADVISORY, not an error, so a plan's own finalize is not refused for it.
  - Depends on: none
  - Expected outcome: `aw check plans` exits 0 on a tree whose only carrier problem is a FINISHED carrier, and still exits 1 on an ABANDONED one.
  - Execution state: pending

- [ ] E-02 Add `check_engine.find_obligations_carried_by(repo_root, id6, *, include_untracked=False) -> List[CarriedObligation]` (`plan_path, plan_id6, locator, line_no, row_text`). Iterate pending plans the way `check_durable_carrier` (~:6126) does; substring pre-filter on `id6` before parsing; obligations from `_deferred_section_obligations` + `_question_obligations`; keep rows whose `parse_carrier_ids` good tokens include `id6` and that carry no `Carrier-Evidence`/`Carrier-Declined`. Never raises (return `[]`). Reuse only the existing parsers.
  - Depends on: none
  - Expected outcome: one pure reverse lookup; measured cost recorded in E-07 (authoring measured a 3 ms pre-filter over ~65 pending plans).
  - Execution state: pending

### Task group 2: Verify with an agent in the run

- [ ] E-03 In `runner_shared.execute_item_core` (~:27096), after a SUCCESSFUL finalize of plan B on both finalize call sites (`_call_driver_finalize` returns at ~:29069 and ~:29294), call `find_obligations_carried_by(<lane or repo>, B)`. If rows exist and the run has a live session for this item, dispatch ONE follow-up turn to the same agent in the same lane using a new builder `build_carrier_verification_prompt(b_id6, rows)` that says, in plain words: 'Plan <B> just finished. These pending plans named it as the owner of work they deferred: <plan, row, text>. For each: if <B> did this work, add `- Carrier-Evidence: <path of executed B>` under the row; if it did not, re-point `- Carrier:` to a live backlog item or plan (file one with `aw backlog new` if needed) or do the work. These edits are outside your plan's scope: commit them with `aw commit --no-plan -m <why>` naming each path, and state the reason. Report yes/no per row.' Before integration, re-run `find_obligations_carried_by` on the lane: resolved rows = continue; any row still unresolved = record a refusal code `carrier-verification-unresolved` on the item and send it back through `finalize_retry_decision` (~:6181) and the existing budget (`frozen_retry_budget` ~:6142); exhausted = item stays non-integrated and is reported, lane preserved.
  - Depends on: E-01, E-02
  - Expected outcome: finishing a carrier in a run leaves no other plan pointing at it unresolved, or the run says exactly which row it could not resolve.
  - Execution state: pending

- [ ] E-04 Make the finalize-refusal classifier recognize the FINISHED-carrier case for the plan being finalized itself (its OWN deferred row names a carrier that finished earlier): add the new rule code to the retryable set used by `finalize_refusal_is_retryable` (~:6056, `RETRYABLE_FINALIZE_FINDING_TEXTS` ~:6019) ONLY IF E-01 leaves any path where it still refuses; otherwise document in Findings that E-01 removed the refusal. In both cases the recovery prompt (the `Prior attempt:` channel, ~:5993) must carry the same instructions as E-03 for that row.
  - Depends on: E-01
  - Expected outcome: a plan never gets stuck on a finished carrier in its own Deferred section.
  - Execution state: pending

### Task group 3: Outcome tests

- [ ] E-05 `tests/test_carrier_reverse_lookup.py` (scratch git repo, `tests/support.ready_plan_text` fixtures): (a) plan A defers to executed plan B -> `aw check plans` exit 0 with a `check.ipd-carrier-finished-unverified` warning naming A's row; (b) plan A defers to superseded plan B -> exit 1 with `check.ipd-uncarried-obligation`; (c) the same row with `- Carrier-Evidence:` -> no finding; (d) `find_obligations_carried_by(repo, B)` returns A's row, and `[]` for an id6 nobody names.
  - Depends on: E-01, E-02
  - Expected outcome: four outcome tests.
  - Execution state: pending

- [ ] E-06 `tests/test_carrier_finished_verification.py`: drive `execute_item_core` with an injected host runner double (no real model; the suite forbids real spawns) on a scratch repo where pending plan A defers to plan B: (a) the double answers the verification turn by adding `Carrier-Evidence` -> B integrates, A's row resolved, no refusal; (b) the double changes nothing -> item B carries refusal `carrier-verification-unresolved` and, with budget 0, is not integrated and the lane is preserved; (c) no plan names B -> no verification turn is dispatched (the double's call count is unchanged).
  - Depends on: E-03
  - Expected outcome: three outcome tests of what the run does, not of prompt wording.
  - Execution state: pending

### Task group 4: Record and verify

- [ ] E-07 Add one `- Changed:` line under `## 2.0.0 (pending)` in `CHANGELOG.md`, plain words, no em or en dashes: when a plan or backlog item that other plans handed work to is finished, a run now asks the agent to confirm the work was done and records the proof, and `aw check plans` no longer fails on a finished owner (it still fails when the owner was abandoned). Then run the bare suite, `python3 -m agent_workflows check plans --agent`, `aw sanitize --agent`, and time `find_obligations_carried_by` warm on this repository.
  - Depends on: E-05, E-06
  - Expected outcome: 0 failed; timing recorded.
  - Execution state: pending

## Project conventions discovered (Step 0)

- One evaluator, many surfaces: `evaluate_durable_carrier` serves both `aw check` and `aw ipd lint --phase pre-transition`; `_resolve_carrier`, `_deferred_section_obligations`, `_question_obligations`, `parse_carrier_ids` are the only carrier parsers; reuse them.
- The runner already has a bounded send-back loop for refused finalizes (`finalize_retry_decision`, `handle_finalize_refusal` ~:6249, `frozen_retry_budget`) and a recovery-prompt channel (`Prior attempt:`); reuse them, do not add a second budget.
- The suite refuses real model spawns (`_assert_probe_spawn_is_permitted` precedent); tests inject runner doubles.
- Out-of-lane edits are allowed when justified (AGENTS.md execution contract; finalize `--scope-reason`).
- Tests: outcome only (maintainer standing rule).

## Findings

| # | Location | Finding |
| --- | --- | --- |
| F-1 | backlog `zi2uzu` claim that aw check reports a clean tree in the window | FALSE: `check_durable_carrier` sweeps all pending plans on every `aw check plans`, fail-closed in CI; that is what turned main red on 2026-09-26 (fixed by hand in b20b7a74 and e0581df0). |
| F-2 | `_resolve_carrier` (~:5904) | Treats executed/done the same as superseded/not-executed/parked. The two real incidents were both FINISHED carriers that had done the work; the rule cannot distinguish that from a finished carrier that dropped it, which is why an agent must judge (maintainer ruling 2026-09-26). |
| F-3 | runner finalize path | After plan B finalizes, nothing looks at plans that named B; the only detection is the next `aw check plans` (CI) or the other plan's own pre-transition lint. |
| F-4 | design history | The first version of this plan only printed a warning at the transition. Rejected by the maintainer: warnings in unattended runs and in CI are not read, so they fix nothing. |

## Proposed changes (ordered, validatable)

1. E-01 finished vs abandoned verdicts; finished is non-failing in `aw check`.
2. E-02 reverse lookup.
3. E-03 agent verification turn after finalize in runs; E-04 retry path for a plan's own row.
4. E-05, E-06 outcome tests; E-07 CHANGELOG, suite, timing.

## Deferred / out of scope (with reason)

- Surfacing unverified finished carriers in `aw attention`.
  - Carrier-Declined: the run resolves them at finish and `aw check plans` still reports them; a third surface adds nothing.
- Resolving finished carriers outside a run (a human running `aw ipd finalize` by hand).
  - Carrier-Declined: `aw check plans` reports the row as needing verification and the human is the verifier; no agent is present to ask.

## Scope check

- Over-scope: none; the rule split, the lookup, and the run turn are one concern (who confirms handed-off work was done).
- Under-scope: none known.

## Required tests / validation

Outcome tests only (maintainer standing rule): `tests/test_carrier_reverse_lookup.py` (what `aw check plans` reports and its exit code for finished, abandoned, and evidenced carriers) and `tests/test_carrier_finished_verification.py` (what a run does: integrates, sends back, or dispatches nothing), with an injected runner double and no real model. Run the suite BARE: `python3 -m pytest`.

## Spec / documentation sync

No `.spec.md` is amended. The durable-carrier contract (plan `rnkqrc`) changes in one respect: a FINISHED carrier is now a non-failing finding pending agent verification. That is recorded in this plan and the CHANGELOG; if a spec states the old rule, the executor must list it here and add it to Scope-Paths before editing it.

## Open questions

### OQ-01: Should a finished carrier fail CI, or wait for an agent?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED 2026-09-26 BY THE MAINTAINER when asked directly: verify with an agent in the run; CI does not fail on a finished carrier (it reports it) but still fails on an abandoned one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m agent_workflows check plans --agent` on the E-05 (a) and (b) scratch trees, showing exit 0 with the new warning for (a) and exit 1 with `check.ipd-uncarried-obligation` for (b).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -c "from pathlib import Path; from agent_workflows import check_engine as ce; print(ce.find_obligations_carried_by(Path('.'), '<id6 some pending plan here names as Carrier>')); print(ce.find_obligations_carried_by(Path('.'), 'zzzzzz'))"` showing that plan's row, then `[]`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste E-06 tests (a) and (b) passing (node ids), and the item's recorded refusal record from test (b) showing code `carrier-verification-unresolved`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste either the Findings line stating E-01 removed the self-refusal plus `aw ipd lint <scratch plan whose own row names a finished carrier> --phase pre-transition` reporting advisory, not error; or the retryable-classifier change and a test showing the recovery prompt carries the row instructions.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_carrier_reverse_lookup.py -o addopts="" -v` showing 4 passed.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_carrier_finished_verification.py -o addopts="" -v` showing 3 passed.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `git diff CHANGELOG.md`, `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` printing nothing, the final summary line of a BARE `python3 -m pytest` with 0 failed, `python3 -m agent_workflows check plans --agent` exit 0, `aw sanitize --agent` exit 0, and three warm timings of the reverse lookup.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern, who confirms that handed-off work was done when its owner finishes: the checker distinguishes finished from abandoned, and the run asks the agent.

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: (1) `aw check plans` stops failing when a named owner FINISHED and still fails when it was ABANDONED; (2) a run spends one extra agent turn after finishing a plan that other plans named as an owner, and that turn may edit those other plans with a stated reason; (3) an unresolved answer sends the item back under the existing retry budget.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the files in `- Scope-Paths:`. If the work requires another file, make the edit and JUSTIFY it at finalize (`--scope-reason`).

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a test passed that was not run. Run the suite BARE (`python3 -m pytest`), no `-n0`, no extra `-q`, no `-p no:randomly`.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit cnzrxb -- <paths>`; never `git add -A`, never `-a`, never push. The runner owns finalize in a lane. Backlog `zi2uzu` carries no `- Blocks-Release:`; after execution set it `done` with `--evidence` citing the executed plan.

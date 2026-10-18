# IPD: Let runner turns ask the maintainer and take answers while the run is live (spec 6kwd2e)

- Date: 2026-10-17
- Kind: orchestrator
- Concern: Spec `6kwd2e` (approved 2026-09-12, amended 2026-10-17 with R9 and R10) designs how a runner turn hands the maintainer a question and how the answer comes back while the run is still live, from a second terminal or a chat app; none of it is implemented. Measured 2026-10-17: the worker's question tool is denied, deferred questions are unread prose, no runner writes a question file, there is no answer command, and no notification exists (findings `xjsc9k`; reports `kdg4uz`, `cpcn9k`, `49sv63`, `js5p5k`).
- Scope: Orchestration only: sequence the eleven children below and confirm each reaches `executed`. No code, test or record of its own.
- Scope-Paths: .aw/records/plans/pending/20261017-qchan-00-wpv9r7-let-runner-turns-ask-the-maintainer-and-take-answers-while-t.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: b85cde20cc6e36c802f6da7579ba305f415cf0e130917abec4213e846fe312cd
- Coverage-Checked: 2026-10-17 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: feature
- Priority: high
- From-Spec: 6kwd2e
- Set: qchan
- Order: 0
- Highest E allocated: 11
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: wpv9r7

## Workflow history
- 2026-10-18 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5.5-1m-us variant=high profile=opus): RETIRED as the orchestrator rollup step of a runner Set completion, not executed by an agent: every child of Set qchan reached executed, so the runner (run run-20261018T201524Z-4077155) retired this Order-0 plan as bookkeeping. Its own E-*/V-* items were NOT performed; the runner superseded them by enforcing the ordering, the isolation and the per-child merge gate. Justifying children: 0jooqz, epsti7, mtmqlm, j0ufrj, 8u071n, y1vjzp, 4kkcex, jshwxb, txl556, qrup8m, mrlblc, uqp95y.
- 2026-10-18 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): design input: until this Set lands, `Attended: required` plans run by opening an INTERACTIVE agent session (`aw work begin`, and the runners pause at a terminal) - DECISIONS D176, backlog rfofos. When runner turns can ask questions, attended plans should be able to run as ordinary turns through this channel, with the interactive hand-off kept as the fallback; keep the two consistent.
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003
- 2026-10-17 coverage pass (aw oc run): fingerprint b85cde20cc6e, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-17 coverage fail (aw oc run): fingerprint f631d4a35384, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-17 to-review (aw set): authored review-ready: orchestrates spec 6kwd2e (amended 2026-10-17) across 11 children; coverage pass

- 2026-10-17 coverage pass (aw oc run): fingerprint 38eba791cd10, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-17 coverage fail (aw oc run): fingerprint ebd9fd2d83ab, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Implement spec `6kwd2e` in full, including its 2026-10-17 amendment, as eleven independently executable children: a worker can hand the human a question, the item parks without stopping the queue, the human is told and can answer from a terminal or Telegram while the run is live, and the parked item resumes in its own session.

## Detailed Implementation Checklist (TODO)


> Its own E-*/V-* items were NOT performed; the runner superseded them by enforcing the ordering, the isolation and the per-child merge gate.

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Children

- [ ] E-01 CONFIRM 0jooqz REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans 0jooqz` shows it under `executed/`.
  - Execution state: pending

- [ ] E-02 CONFIRM epsti7 REACHED executed
  - Depends on: E-01
  - Expected outcome: `aw find plans epsti7` shows it under `executed/`.
  - Execution state: pending

- [ ] E-03 CONFIRM mtmqlm REACHED executed
  - Depends on: E-02
  - Expected outcome: `aw find plans mtmqlm` shows it under `executed/`.
  - Execution state: pending

- [ ] E-04 CONFIRM j0ufrj REACHED executed
  - Depends on: E-03
  - Expected outcome: `aw find plans j0ufrj` shows it under `executed/`.
  - Execution state: pending

- [ ] E-05 CONFIRM 8u071n REACHED executed
  - Depends on: E-03
  - Expected outcome: `aw find plans 8u071n` shows it under `executed/`.
  - Execution state: pending

- [ ] E-06 CONFIRM y1vjzp REACHED executed
  - Depends on: E-03
  - Expected outcome: `aw find plans y1vjzp` shows it under `executed/`.
  - Execution state: pending

- [ ] E-07 CONFIRM 4kkcex REACHED executed
  - Depends on: E-03
  - Expected outcome: `aw find plans 4kkcex` shows it under `executed/`.
  - Execution state: pending

- [ ] E-08 CONFIRM jshwxb REACHED executed
  - Depends on: E-04, E-07
  - Expected outcome: `aw find plans jshwxb` shows it under `executed/`.
  - Execution state: pending

- [ ] E-09 CONFIRM txl556 REACHED executed
  - Depends on: E-04
  - Expected outcome: `aw find plans txl556` shows it under `executed/`.
  - Execution state: pending

- [ ] E-10 CONFIRM qrup8m REACHED executed
  - Depends on: E-09
  - Expected outcome: `aw find plans qrup8m` shows it under `executed/`.
  - Execution state: pending

- [ ] E-11 CONFIRM mrlblc REACHED executed
  - Depends on: E-10
  - Expected outcome: `aw find plans mrlblc` shows it under `executed/`.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `0jooqz` | `20261017-qchan-01-0jooqz-carry-emergent-questions-in-the-worker-outcome-file-with-dri.ipd.md` | `questions[]` outcome field, validator, driver-computed fingerprint, execute and review prompts (R2, R4.1a). | none |
| 02 | `epsti7` | `20261017-qchan-02-epsti7-park-a-questioning-item-non-terminally-and-keep-the-queue-mo.ipd.md` | Non-terminal `awaiting-human` status; park with preserved lane; dependents wait; drain exits 3, not fail (R3, R6.1, R7.3). | `executed:0jooqz` |
| 03 | `mtmqlm` | `20261017-qchan-03-mtmqlm-write-a-per-run-question-and-answer-inbox-through-one-shared.ipd.md` | `question_inbox`: `questions/` and `answers/` files, the one shared answer writer, `open-questions.md` at park time (R9.1, R9.2, R4a.1). | `executed:epsti7` |
| 04 | `j0ufrj` | `20261017-qchan-04-j0ufrj-consume-answers-at-dispatch-checkpoints-and-resume-the-parke.ipd.md` | Consume answers at every checkpoint, answered items first, same-session resume with fresh-turn fallback, staleness (R9.3, R9.4, R5.5, R5.6). | `executed:mtmqlm` |
| 05 | `8u071n` | `20261017-qchan-05-8u071n-add-aw-runs-answer-to-answer-a-live-or-finished-run-s-questi.ipd.md` | `aw runs answer` (interactive, flags, `--agent`) and `aw runs questions` for live runner runs (R9.5, R4a.2). | `executed:mtmqlm` |
| 06 | `y1vjzp` | `20261017-qchan-06-y1vjzp-make-parked-questions-visible-mid-run-in-the-statusline-a-be.ipd.md` | Statusline count and answer hint, one bell, `aw attention` label and count (R4a.3-R4a.6, R9.6). | `executed:mtmqlm` |
| 07 | `4kkcex` | `20261017-qchan-07-4kkcex-sweep-pre-existing-open-questions-before-dispatch.ipd.md` | Pre-flight sweep of existing open questions, bounded free-text prompt, answers written into the artifact, unattended route to the inbox (R1). | `executed:mtmqlm` |
| 08 | `jshwxb` | `20261017-qchan-08-jshwxb-deduplicate-and-order-questions-ask-at-the-drain-bound-round.ipd.md` | Fingerprint dedup and ordering, one answer for a group, drain-time ask with bounded rounds, `answers.md`, runaway bound (R4, R4b, R5.1-R5.3a). | `executed:j0ufrj`, `executed:4kkcex` |
| 09 | `txl556` | `20261017-qchan-09-txl556-add-the-notification-channel-core-with-user-level-config-san.ipd.md` | Notification core: channel interface, user-level config and policy, sanitized terse output, registry, once-per-park, webhook and command channels (R10.1-R10.4, R10.7, R10.8b). | `executed:j0ufrj` |
| 10 | `qrup8m` | `20261017-qchan-10-qrup8m-add-a-standard-library-two-way-telegram-channel.ipd.md` | Standard-library two-way Telegram channel and its single per-bot receiver (R10.5, R10.6, R10.8a). | `executed:txl556` |
| 11 | `mrlblc` | `20261017-qchan-11-mrlblc-add-aw-notify-setup-test-status-and-listen.ipd.md` | `aw notify` setup, test, status, listen and disable, docs and per-OS hand-test checklist (R10.9, R10.6). | `executed:qrup8m` |

Order 01 has no prerequisite. Orders 05, 06 and 07 depend only on 03 and can run in any order after it; 09 depends on 04; 10 on 09; 11 on 10. The runner orders by dependency depth and isolates each child in its own worktree, so children touching the same files is not a hazard.

## Completion criteria (the whole Set is done only when)

- A worker can return `questions[]` and the driver validates and fingerprints it. Owner: `0jooqz`.
- A questioning item parks non-terminally, keeps its lane, holds its dependents and lets the rest of the queue finish; a parked-only drain exits 3. Owner: `epsti7`.
- Every parked question has a file in `questions/`, and every answer goes through the one shared writer. Owner: `mtmqlm`.
- An answer written while the run is live is consumed at the next checkpoint and the item resumes in its own session. Owner: `j0ufrj`.
- `aw runs answer` answers a live run's question. Owner: `8u071n`.
- The statusline, bell and `aw attention` show waiting questions. Owner: `y1vjzp`.
- Existing open questions are swept before dispatch and answers land in the artifact. Owner: `4kkcex`.
- Duplicate questions are asked once, the drain asks and re-dispatches within bounds, and runaway escalation stops dispatch. Owner: `jshwxb`.
- A parked question triggers one sanitized, terse-by-default off-machine notification through a webhook or command hook. Owner: `txl556`.
- A Telegram button press or threaded reply from the paired user answers a live run's question. Owner: `qrup8m`.
- `aw notify setup telegram` pairs and tests a bot, and the per-OS hand-test checklist is documented. Owner: `mrlblc`.

## Cross-IPD validation

- Every acceptance criterion A1-A55 of spec `6kwd2e` is asserted by a test in exactly the child whose requirements it maps to (A1-A2, A14, A16, A18, A27-A28, A40-A41 in `4kkcex`; A3-A5, A7-A8, A13, A32, A39 in `epsti7`; A6, A12, A43-A44 in `j0ufrj`; A9-A10, A17, A20-A26, A33-A35 in `jshwxb`; A10a-A10b, A19, A29-A31 in `0jooqz` (A30, the missing-input versus question carrier separation, in its E-05); A10c, A45 in `8u071n`; A10d-A10h, A46 in `y1vjzp`; A11, A42 in `mtmqlm` (its E-04); A15 (host parity) is asserted on both hosts by `epsti7`, `j0ufrj`, `4kkcex` and `jshwxb`, each of whose test modules runs every case against `aw oc run` and `aw agy run`; A36-A37 in `j0ufrj`; A38 in `epsti7`; A47 in `4kkcex`; A48-A49, A53, A55 in `txl556`; A50-A52 in `qrup8m`; A54 in `mrlblc`). Each child's V-items require the test output of its own module and of the routine gate. `mrlblc` has the greatest dependency depth (7) and so dispatches last in a runner queue and in table order, but no child is guaranteed to run after every other child's merge (Orders 05, 06 and 08 are shallower and may finish later under parallel lanes); post-merge revalidation is the runner's merge-and-revalidate gate on each child, not work of this plan.

## Deferred / out of scope (with reason)

- Signal as a channel: deferred by spec `6kwd2e` R10.10; carried by parked backlog `szjsgj`.
  - Carrier-Declined: not shipped by decision (spec `6kwd2e` R10.10); a possible later channel is recorded as parked backlog `szjsgj`, which is a maybe, not committed work
- An in-run hotkey that opens a prompt inside the streaming terminal: excluded by R9.6 (it would sit beside the SIGINT menu, the most wedge-prone code in the runners).
  - Carrier-Declined: excluded by spec `6kwd2e` as a design decision, not deferred work
- An installed background OS service for receiving answers: excluded by R10.6.
  - Carrier-Declined: excluded by spec `6kwd2e` as a design decision, not deferred work

## Scope check

- Over-scope: none.
- Under-scope: none. Every requirement R1-R10 maps to a child in the table above.

## Required tests / validation

This plan runs no tests. Each child runs its own module and the routine gate, and the runner revalidates after each merge (see Cross-IPD validation).

## Open questions

None.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `aw find plans 0jooqz` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw find plans epsti7` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `aw find plans mtmqlm` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `aw find plans j0ufrj` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `aw find plans 8u071n` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `aw find plans y1vjzp` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted `aw find plans 4kkcex` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: pasted `aw find plans jshwxb` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: pasted `aw find plans txl556` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: pasted `aw find plans qrup8m` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: pasted `aw find plans mrlblc` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) of this plan and each child. EXECUTION CONTRACT: all open questions are resolved. This plan performs no work of its own; each child carries its own scope fence, test evidence and path-scoped `aw commit`. Under `aw oc run` / `aw agy run` the runner retires this plan once every child is `executed`. When executing by hand, run the children in table order, then confirm each and run `aw ipd lint --phase pre-transition` and `aw ipd finalize` on this plan. Never push.

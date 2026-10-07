# IPD: Fix first: send agent-caused run failures back to the agent instead of failing the item or the run

- Date: 2026-10-07
- Kind: orchestrator
- Concern: Unattended `aw oc run` / `aw agy run` runs stop on failures an agent fixes in one turn when told what went wrong, and the maintainer loses hours to it ("99% of the time the intervention is telling an agent to investigate and fix"). Measured 2026-10-07 at HEAD `03ddbcb83`: the turn retry can never fire (`runner_shared.TURN_RETRYABLE_DISPOSITIONS` admits only `failed-safely`, which nothing reaching `handle_turn_failure_retry` carries); a crash, stall, spawn failure, hook refusal or red merged suite fails the item with no fix-it turn; spec `25kzda` 4.1/5.5/5.7 promises run aborts the code never performs; out-of-scope edits are auto-justified by the runner; and an agent's "the gate or tool must change" has no durable channel.
- Scope: Orchestrate eight children that together make the runner FIX FIRST: every agent-caused failure gets a bounded fix-it turn naming what failed; the agent may propose a gate, tool or approach change and that proposal lands durably while the item stops `needs-human`; only runner-state failures and human gates stop an item without a fix-it turn; only a corrupt ledger aborts the run. This plan holds ORCHESTRATION ONLY: every deliverable belongs to a child. EXCLUDES, in every child: push detection (Set `denypush`, `l4vw9o`), global fix-it caps across kinds (backlog `38hwvk`), and changing the per-kind retry budget default.
- Scope-Paths: .aw/records/plans/pending/20261007-fixfirst-00-lxb1ew-fix-first-send-agent-caused-run-failures-back-to-the-agent-i.ipd.md
- Item-Dependencies: none
- Status: draft
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 0
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: lxb1ew

## Workflow history

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

When an unattended run hits a failure the agent caused, the agent is told what went wrong and fixes it, instead of the run stopping and waiting for a human to say "investigate and fix". A human is needed only when a gate, tool or approach genuinely has to change, and then the agent's proposal is waiting for them as a tracked record.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: sequence the children

- [ ] E-01 CONFIRM tb6lw3 REACHED executed
  - Depends on: none
  - Expected outcome: `tb6lw3` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 01 rewrites spec `25kzda`'s failure policy first, so every code child is reviewed and executed against the contract it implements rather than against the never-retry list it removes.

- [ ] E-02 CONFIRM tha7a6 REACHED executed
  - Depends on: E-01
  - Expected outcome: `tha7a6` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 02 builds the proposal channel and the `needs-human` stop. It precedes the message (Order 03) because the message must tell the agent how to propose.

- [ ] E-03 CONFIRM mcbph5 REACHED executed
  - Depends on: E-02
  - Expected outcome: `mcbph5` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 03 builds the one shared fix-it message every later child sends.

- [ ] E-04 CONFIRM ytas91 REACHED executed
  - Depends on: E-03
  - Expected outcome: `ytas91` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 04 makes crashed, stalled and unstarted turns retryable and resumes the turn's own session. It replaces plan `p47qfu`.

- [ ] E-05 CONFIRM w9nvq4 REACHED executed
  - Depends on: E-03
  - Expected outcome: `w9nvq4` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 05 makes hook refusals and a red merged suite retryable.

- [ ] E-06 CONFIRM psgyzw REACHED executed
  - Depends on: E-03
  - Expected outcome: `psgyzw` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 06 stops the runner writing scope reasons for the agent and adds the `- Scope-Exceeded:` record.

- [ ] E-07 CONFIRM 62sdwr REACHED executed
  - Depends on: E-03
  - Expected outcome: `62sdwr` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 07 adds detection of untooled status changes and hook-skipping commits.

- [ ] E-08 CONFIRM iksylm REACHED executed
  - Depends on: E-04, E-05, E-06, E-07
  - Expected outcome: `iksylm` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 08 proves the whole Set end to end and owns every Set-level criterion below.

## Child IPDs, sequence, and dependencies

| Order | Id | What it does | Depends on |
|---|---|---|---|
| 01 | `tb6lw3` | Rewrite spec `25kzda` 4.1, 5.5, 5.7 (and the `run_evidence` transcription the spec pins) as fix first; only a corrupt ledger aborts a run | none |
| 02 | `tha7a6` | Outcome-file `proposal` field; runner files a plan or backlog item onto main through a coordinator worktree; item stops `needs-human`, run continues | `executed:tb6lw3` |
| 03 | `mcbph5` | One shared fix-it message: what failed, fix the cause not the gate, when a small gate/tool fix is acceptable, how to propose | `executed:tha7a6` |
| 04 | `ytas91` | Fix-it turns for nonzero exit / no outcome file, stall or turn limit, spawn failure; resume the turn's own session; supersedes `p47qfu` | `executed:mcbph5` |
| 05 | `w9nvq4` | Fix-it turns for a hook refusal of the finalize commit, a hook refusal of an integration commit, and a red combined suite after merge | `executed:mcbph5` |
| 06 | `psgyzw` | Out-of-scope edits sent back as revert-or-justify; the agent writes the reason; kept ones recorded as `- Scope-Exceeded:` | `executed:mcbph5` |
| 07 | `62sdwr` | Detect untooled plan status changes / moves and `--no-verify`-style commits in the lane; send them back for correction | `executed:mcbph5` |
| 08 | `iksylm` | One scripted run per failure kind proving fix first end to end; owns the Set-level checks | `executed:ytas91`, `executed:w9nvq4`, `executed:psgyzw`, `executed:62sdwr` |

Orders 04 to 07 are mutually independent once 03 has executed. They all edit `agent_workflows/runner_shared.py`, which is not a hazard: the runner gives each its own worktree and merges through the revalidate gate.

## Completion criteria (the whole Set is done only when)

1. Every failure class the amended spec calls agent-caused gets a fix-it turn naming what failed, within the existing per-kind `--retry-budget`. [Owner: iksylm E-01]
2. A fix-it turn's message says to fix the cause, not the gate, and tells the agent how to propose a gate, tool or approach change. [Owner: iksylm E-02]
3. A proposal lands on main as a plan or backlog item even when the lane does not merge, and the item stops `needs-human` while independent items continue. [Owner: iksylm E-03]
4. No run aborts except on a corrupt ledger. [Owner: iksylm E-04]
5. The spec text, the `run_evidence` transcription and the shipped behavior agree. [Owner: iksylm E-05]
6. The bare suite is green apart from failures reproduced at the Set's baseline. [Owner: iksylm E-06]

## Cross-IPD validation

- The spec (Order 01) is the contract every code child cites. Each code child's V-items quote the amended spec row it implements. [Owner: each code child's own V-items; cross-checked by iksylm E-05]
- The message (Order 03) is the ONLY fix-it text: Orders 04 to 07 call `build_fix_it_notice` rather than writing their own. [Owner: iksylm E-02]
- The proposal path (Order 02) is the only way an item reaches `needs-human` from a fix-it turn. [Owner: iksylm E-03]

## Deferred / out of scope (with reason)

- Push detection. Measured: nothing detects a push today, and Set `denypush` (`l4vw9o`) owns the enforcement question. Order 01 rewrites the spec response to "record and continue" so that work lands against the right contract.
  - Carrier: oq05nc
- Global fix-it caps per artifact, per Set and per run. Maintainer request 2026-10-07, low priority, not release-blocking.
  - Carrier: 38hwvk
- Mid-run human questions (spec `6kwd2e` R2 to R5, approved, unbuilt). Order 02's `needs-human` stop is narrower: it records a proposal and stops one item; it does not pause a run for an answer.
  - Carrier-Declined: spec `6kwd2e` is itself the durable carrier of that work; this Set does not change it.

## Scope check

- Over-scope: none. This plan contributes no code, test or record of its own.
- Under-scope: push detection and global caps are deferred above with carriers.

## Required tests / validation

This plan runs no tests. `iksylm` (Order 08) performs the whole-Set measurement, including the bare suite.

## Open questions

### OQ-01: Should the proposal record land on main directly, or only travel with the lane?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Resolved 2026-10-07 in session. The maintainer asked whether the lane could be used but only the record merged. That is what Order 02 does: the record is committed in a coordinator worktree cut from main (the `perform_coordinator_backlog_close` pattern) and fast-forwarded under the integration lock, so main moves atomically or not at all and the lane's other changes do not come with it. See `tha7a6` F-02.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw find plans tb6lw3` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw find plans tha7a6` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw find plans mcbph5` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw find plans ytas91` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `aw find plans w9nvq4` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `aw find plans psgyzw` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `aw find plans 62sdwr` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `aw find plans iksylm` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval of each child before execution. The runner retires this orchestrator once every child is `executed`. Backlog `coivul` is set `graduated` when the Set is authored and closes through the normal backlog close once every carrier has executed.

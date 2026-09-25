# IPD: Agent comms broker Set: payload-blind nudge broker, discovery registry, agent acks

- Date: 2026-09-24
- Kind: orchestrator
- Concern: The comms convention shipped broker-free (executed plan `ssmov3`; spec `20260715-1722-01-agent-comms-convention`, implemented) and deferred its three follow-ups, which `ssmov3` calls "IPDs 2, 3, and 4": the payload-blind broker (backlog `ifeyjv`), agent-side ack writing plus status aggregation (backlog `0gd5w6`), and discovery/registry (backlog `lbhmi3`). This Set sequences them as three small, opt-in children.
- Scope: Orchestration only. Child 01 `nomhl1` (broker, OpenCode HTTP API nudge, loopback-only), child 02 `ex539u` (filesystem target registry, depends on 01), child 03 `ozcfjr` (agent acks and status, depends on 01). This plan authors no code and no docs; each child owns its own spec amendment.
- Scope-Paths: .aw/records/plans/pending/20260924-commsbroker-00-u8tabj-agent-comms-broker-set-payload-blind-nudge-broker-discovery.ipd.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: low
- From-Backlog: ifeyjv
- Set: commsbroker
- Order: 0
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: u8tabj

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog ifeyjv, lbhmi3, 0gd5w6; re-measured that OpenCode 1.18.32 still exposes the `/tui/show-toast`, `/tui/append-prompt` and `/session/{sessionID}/prompt_async` routes the broker design relies on.

## Goal

Deliver the three deferred comms follow-ups in dependency order, each opt-in, so the broker-free convention keeps working unchanged when none of them is used.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator carries orchestration only; every piece of work lives in a child.

### Task group 1: children

- [ ] E-01 CONFIRM nomhl1 REACHED executed
  - Child 01, the payload-blind broker.
  - Depends on: none
  - Expected outcome: `nomhl1` is in `.aw/records/plans/executed/` with `- Status: executed`, or it stopped at its E-01 spike and the Set is re-planned.
  - Execution state: pending
- [ ] E-02 CONFIRM ex539u REACHED executed
  - Child 02, the target registry.
  - Depends on: E-01
  - Expected outcome: `ex539u` is in `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending
- [ ] E-03 CONFIRM ozcfjr REACHED executed
  - Child 03, agent acks and per-message status.
  - Depends on: E-01
  - Expected outcome: `ozcfjr` is in `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | What it does | Depends on |
|---|---|---|---|
| 01 | `nomhl1` | `agent_workflows/comms_broker.py`: header-only scan, `Not-Before`, one constant nudge via `POST /tui/show-toast` + `/tui/append-prompt` (attended) or `/session/{sessionID}/prompt_async` (headless), loopback-only, broker acks only. E-01 is a spike with a stop condition. From-Backlog `ifeyjv`. | none |
| 02 | `ex539u` | Filesystem registry `untracked/registry/<agent>.json`, verified by `GET /global/health` and `GET /path`; mDNS deferred. From-Backlog `lbhmi3`. | executed:nomhl1 |
| 03 | `ozcfjr` | `agent_workflows/comms_acks.py`: agent-only ack writer, per-message status with derived `unread`, README paragraph, spec ack-path fix. From-Backlog `0gd5w6`. | executed:nomhl1 |

Children 02 and 03 are independent of each other and both edit the same spec file; the runner's per-item worktrees and merge gate handle that.

## Completion criteria (the whole Set is done only when)

- All three children are executed, and none was re-scoped away from being opt-in.
- The comms spec's Deferred list no longer names the broker, filesystem discovery or agent ack writing, and still names mDNS, cross-box delivery and `Depends-On`.

## Cross-IPD validation

- `grep -rn "comms_broker\|comms_acks" agent_workflows/ --include=*.py` shows no importer outside the two new modules, which proves nothing is auto-started or installed.
- The backlog items `ifeyjv`, `lbhmi3`, `0gd5w6` are closed by their own children's executors, not by this plan.

## Deferred / out of scope (with reason)

- mDNS discovery and cross-box delivery.
  - Carrier-Declined: Deferred in child 02 with reasons (non-stdlib client, binds 0.0.0.0); no obligation outstanding.
- OpenCode server auth support.
  - Carrier-Declined: Maintainer decision recorded as child 01 OQ-01 with a no-for-v1 default.

## Scope check

- Over-scope: none; this plan edits only itself.
- Under-scope: if child 01 stops at its spike, children 02 and 03 must be re-read before running, since both assume its module exists.

## Required tests / validation

Each child runs its own targeted tests and the bare `python3 -m pytest`; this plan checks only the children's lifecycle state.

## Open questions

### OQ-01: Should the Set proceed with child 03 if child 01 stops at its spike?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default: no. Child 03's writer stands alone, but its status view reads broker acks and its `Item-Dependencies: executed:nomhl1` blocks it at dispatch; lifting that is a maintainer call.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls .aw/records/plans/executed/ | grep nomhl1` and `grep -n "^- Status:" <that file>` showing `executed`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `ls .aw/records/plans/executed/ | grep ex539u` and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `ls .aw/records/plans/executed/ | grep ozcfjr` and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval, as does each child. It carries no work of its own, so when every child is executed the runner retires it; executed by hand, the executor fills the three V items from the children's records and finalizes with `aw ipd finalize`. Nothing is pushed.

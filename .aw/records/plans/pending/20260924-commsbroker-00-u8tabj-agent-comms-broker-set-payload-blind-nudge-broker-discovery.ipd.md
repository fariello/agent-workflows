# IPD: Agent comms broker Set: payload-blind nudge broker, discovery registry, agent acks

- Date: 2026-09-24
- Kind: orchestrator
- Concern: The comms convention shipped broker-free (executed plan `ssmov3`; spec `20260715-1722-01-agent-comms-convention`, implemented) and deferred its three follow-ups, which `ssmov3` calls "IPDs 2, 3, and 4". READ THE MAPPING FROM THIS TABLE AND NOT FROM POSITION, because this Set's Orders are deliberately NOT in `ssmov3`'s numbering: `ssmov3` IPD 2 (payload-blind broker, backlog `ifeyjv`) is Order 01 `nomhl1`; `ssmov3` IPD 4 (discovery/registry, backlog `lbhmi3`) is Order 02 `ex539u`; `ssmov3` IPD 3 (agent-side ack writing plus status aggregation, backlog `0gd5w6`) is Order 03 `ozcfjr`. Discovery is sequenced before acks because it is the smaller change to the module child 01 creates, and neither depends on the other. This Set sequences them as three small, opt-in children.
- Scope: Orchestration only. Child 01 `nomhl1` (broker, OpenCode HTTP API nudge, loopback-only), child 02 `ex539u` (filesystem target registry, depends on 01), child 03 `ozcfjr` (agent acks and status, depends on 01). This plan authors no code and no docs; each child owns its own spec amendment.
- Scope-Paths: .aw/records/plans/pending/20260924-commsbroker-00-u8tabj-agent-comms-broker-set-payload-blind-nudge-broker-discovery.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: low
- From-Backlog: ifeyjv
- Set: commsbroker
- Order: 0
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: u8tabj

## Workflow history

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (uncarriered OQ, `check.ipd-uncarried-obligation` at `error`), PR-002 (cross-IPD opt-in grep false-positives on its own Set), PR-003 (backlog closure asserted a route no child carries), PR-004 (a completion criterion no child owns; recorded as OQ-02), PR-005 (gate carried almost no execution contract) all FIXED. Findings recorded in `.aw/records/reviews/20260924-commsbroker-00-u8tabj-agent-comms-broker-set-payload-blind-nudge-broker-discovery.review.md`. Readiness go-pending-approval.
- 2026-09-25 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 all FIXED; review record written

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
  - Expected outcome: `nomhl1` is in `.aw/records/plans/executed/` with `- Status: executed`. THE SPIKE BRANCH IS NOT AN ALTERNATIVE OUTCOME OF THIS ITEM: if child 01 stops at its own E-01 spike, it does not reach `executed`, so this item stays UNTICKED, the Set does not complete, this orchestrator stays in `pending/` (the runner retires an orchestrator only when every child reads `executed` on disk, `runner_shared.evaluate_set_retirement`), and the Set is re-planned. Do not tick this item on a STOP report.
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

Children 02 and 03 are independent of each other, and each declares `- Item-Dependencies: executed:nomhl1`, which the parent's E-02 and E-03 `Depends on: E-01` edges mirror.

SPEC-FILE OVERLAP, AND WHAT ACTUALLY HANDLES IT. All three children declare `.aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md` in `- Scope-Paths:`, and all three edit its Deferred list. Each execute item runs in its own isolated worktree whose changes return through the merge-and-revalidate gate (the `isolate_worktree` option, default on, opt out with `--no-isolate-worktree`), and the queue is sorted with dependency depth first (`runner_shared.queue_sort_key`, `runner_shared.dependency_depth`), so child 01 always lands before 02 or 03 begin. What that leaves is a real, bounded hazard between 02 and 03 ALONE: neither depends on the other, both delete a different line from the same Deferred list, and a merge of the second onto the first can conflict on that hunk. Two things make it survivable rather than a design flaw: `ipd_lifecycle.land_worktree_commit` REFUSES rather than clobbers, so the failure mode is a refused merge naming the item, not a silently lost spec edit; and the fix is mechanical (re-run the refused child, whose worktree is then cut from a tree already containing the other's edit). An executor who sees that refusal should re-run the refused item, NOT hand-resolve the spec by hand.

DO NOT declare a `03 depends on 02` edge to avoid it. That would assert a dependency that does not exist (child 03 touches `comms_acks.py`, not the registry), and it would make child 03 unreachable if child 02 is ever retired.

## Completion criteria (the whole Set is done only when)

READ THE OWNER COLUMN. Each criterion below names the child `V-*` that actually demands evidence for it, because this orchestrator's own V-01..V-03 check lifecycle state ONLY, and on the runner path they are marked complete without inspection (see the gate). A criterion whose owner is "none" is a RECORDED GAP, not a silent assumption.

| Criterion | Owned by |
|---|---|
| All three children are in `.aw/records/plans/executed/` with `- Status: executed`. | this plan's V-01..V-03 |
| The broker is opt-in: nothing imports, installs, or auto-starts `comms_broker`, and no pre-commit hook or console entry point references it. | `nomhl1` V-05, extended by the Cross-IPD validation below |
| Agent acks are OPTIONAL: the README paragraph says MAY, and `comms_acks` is reachable only as an explicit module invocation. | `ozcfjr` V-03, V-04 |
| The comms spec's Deferred list no longer names the broker, filesystem discovery, or agent ack writing. | `nomhl1` V-07, `ex539u` V-06, `ozcfjr` V-06, each for its OWN bullet |
| The spec's Deferred list STILL names mDNS, cross-instance reachability, `Depends-On`, and cross-box comms AFTER all three edits have merged. | none; see OQ-02 |

## Cross-IPD validation

- THE OPT-IN PROOF, and the naive form of it reports a FALSE POSITIVE. Do NOT use `grep -rn "comms_broker\|comms_acks" agent_workflows/ --include=*.py` and read a non-empty result as a defect: child 03's E-04 adds the line `python3 -m agent_workflows.comms_acks ack <msg-id> read --by <proj.agent>` to `engine._COMMS_README_TEMPLATE`, so `engine.py` MATCHES that grep by design and is not an importer. The check that means what this criterion wants is an IMPORT check plus an AUTO-START check, and both must be re-derived at execution rather than trusted from here:
  - `grep -rnE "^\s*(from|import)\s+.*comms_(broker|acks)" agent_workflows/ --include=*.py` must return NOTHING. Any hit is a real importer.
  - `grep -rn "comms_broker\|comms_acks" pyproject.toml agent_workflows/command_surface.py` must return nothing, which is what actually rules out a console entry point and a declared CLI leaf.
  - `grep -rn "comms_broker\|comms_acks" agent_workflows/engine.py` may legitimately return ONLY the README-template paragraph child 03 declares. Any other hit in `engine.py` (a hook `entry:`, a created file, an installed artifact) is an auto-start and a defect.
- THE THREE BACKLOG ITEMS ARE NOT CLOSED BY THIS SET, AND NOTHING IN IT CLOSES THEM. Stated plainly because the earlier wording ("closed by their own children's executors") asserted a route no child carries: no child plan contains a `aw backlog set` instruction, and `aw ipd finalize` performs no backlog write (`ipd_lifecycle` calls nothing in `backlog`). Closing them is a FOLLOW-UP after the Set completes, in the shape plan `wj5b53` already uses for a closure whose citation does not exist until its plan is terminal:

  ```sh
  aw backlog set done ifeyjv --evidence .aw/records/plans/executed/<nomhl1's filename> --message "graduated into commsbroker; broker shipped"
  aw backlog set done lbhmi3 --evidence .aw/records/plans/executed/<ex539u's filename> --message "graduated into commsbroker; registry shipped"
  aw backlog set done 0gd5w6 --evidence .aw/records/plans/executed/<ozcfjr's filename> --message "graduated into commsbroker; agent acks shipped"
  ```

  MEASURED at review, and re-derive it rather than trusting the number: none of the three carries `- Blocks-Release:`, so `check_engine.evaluate_blocking_close` returns `legitimate=True` by the DE-GATED path for all three and a bare close would not fail closed either. The `--evidence` citation is supplied anyway, because it is the route that stays correct if a gate is ever added.

## Deferred / out of scope (with reason)

- mDNS discovery and cross-box delivery.
  - Carrier-Declined: Deferred in child 02 with reasons (non-stdlib client, binds 0.0.0.0); no obligation outstanding.
- OpenCode server auth support.
  - Carrier-Declined: Maintainer decision recorded as child 01 OQ-01 with a no-for-v1 default.

## Scope check

- Over-scope: none; this plan edits only itself. `- Scope-Paths:` is deliberately this file alone and NOT the union of the children's paths: the finalize scope gate reconciles declared against ACTUAL per item, so a parent declaring paths it never edits would need a `--scope-ack` for every one of them.
- Under-scope: if child 01 stops at its spike, children 02 and 03 must be re-read before running, since both assume its module exists. Note the runner does not need that warning to stay safe: both declare `- Item-Dependencies: executed:nomhl1`, which is re-checked AT DISPATCH, so each is marked `dependency-blocked` and skipped rather than run against a module that does not exist. The warning is for a HUMAN or agent running the Set by hand.

## Required tests / validation

Each child runs its own targeted tests and the bare `python3 -m pytest`; this plan runs no test of its own and checks only the children's lifecycle state.

## Open questions

### OQ-01: Should the Set proceed with child 03 if child 01 stops at its spike?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default: no, and it needs no action to hold. Child 03's ack WRITER stands alone (its own F-4 says the dependency is on the broker ack LAYER, which only the status aggregation reads), but `- Item-Dependencies: executed:nomhl1` is re-checked at dispatch, so child 03 is marked `dependency-blocked` automatically if child 01 never reaches `executed`. Lifting that edge is a maintainer call about scope, not something an executor may decide mid-run.
- Carrier-Declined: The default holds with NO action (the dependency edge enforces it), so there is no outstanding work to hand to a carrier; a maintainer choosing the other answer would edit child 03's edge, which is a new decision rather than a deferred one.

### OQ-02: Does the Set need a final spec-reconciliation step, given no single child can check the residual Deferred list?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Recommendation: NO, accept the per-child checks. All three children delete a different bullet from the same Deferred list and children 02 and 03 have no order between them, so no child is structurally LAST and none can assert the final list. What is actually covered: `ex539u` V-06 demands "mDNS still deferred", so mDNS is checked by a child; `Depends-On` and cross-box comms live in a FOURTH bullet that no child touches at all, so nothing deletes them and there is nothing for a check to catch. The residual risk is narrow: a HAND-RESOLVED merge conflict on that hunk could drop a line, which is exactly why the spec-overlap note above forbids hand-resolving and directs a re-run instead. If the maintainer wants belt-and-braces, the right shape is a new Order 04 child that diffs the final spec, NOT an item parked on this parent, because a parent's items are performed by nobody on the runner path.
- Carrier-Declined: A recorded gap with a stated recommendation and a named remedy shape; no work is outstanding unless the maintainer chooses the Order 04 route, which is a new authoring decision rather than a deferred obligation.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls .aw/records/plans/executed/ | grep nomhl1` and `grep -n "^- Status:" <that file>` showing `executed`. Both halves are required: the DIRECTORY is what `runner_shared.edge_satisfied` reads for an `executed:` edge, and the `- Status:` line is what a reader sees, so a mismatch between them is itself a finding. If child 01 stopped at its E-01 spike, paste the STOP report instead and record this item `blocked`, not `verified`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `ls .aw/records/plans/executed/ | grep ex539u` and its `- Status: executed` line, same two-part rule as V-01.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `ls .aw/records/plans/executed/ | grep ozcfjr` and its `- Status: executed` line, same two-part rule as V-01.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution, AND SO DOES EACH CHILD SEPARATELY. Approving this orchestrator approves the SEQUENCING, not the three children's content: all three read `- Status: to-review` and none has been reviewed, so the Set cannot execute end to end on this approval alone.

OPEN QUESTIONS: OQ-01 and OQ-02 are both `Blocking: no` and both carry a recorded recommendation with a named remedy shape. Neither blocks execution, and an executor must NOT re-decide either mid-run: OQ-01's default is already enforced mechanically by child 03's dependency edge, and OQ-02's alternative is a new Order 04 child, which is an authoring act and not an executor's.

WHAT A HUMAN IS ACTUALLY APPROVING, SINCE IT IS NOT VISIBLE FROM THIS FILE. Child 01's E-01 is a SPIKE that starts a real `opencode serve --pure` on a free port and makes live HTTP requests to it. That is a local loopback process the executor starts and disposes, never a human's running instance, and child 01's own gate says so; it is named here because this parent is where a human decides whether the Set runs at all, and "this plan authors no code" could otherwise read as "this Set launches no process".

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS: this plan's `- Scope-Paths:` is its OWN file alone, which is the honest declaration for a plan whose every item is a child confirmation. It is a DECLARATION and not a stop order: an out-of-scope edit that is genuinely required must be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and a declared path left unmodified needs a `--scope-ack`. Do not halt over a scope question. DO halt for a genuinely unsafe condition: an unresolvable concurrent-edit conflict (which on this Set means the 02/03 spec-hunk conflict described above, whose correct response is to re-run the refused item, not to hand-resolve the spec), or a prerequisite whose symbols are absent.

SPEC EDITS THIS SET DECLARES: all three children declare `.aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md`, so both runners will ANNOUNCE three declared spec edits before the run and reconcile them at the end. That is expected, not a defect. An UNDECLARED spec edit from any child is a defect.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*` above. A `V-*` may not be marked complete from the matching `E-*` checkmark, from memory, or from a child's own self-report. Never claim a test pass that was not run.

COMMIT DISCIPLINE: commit only the paths this plan declares, path-scoped, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, and never push. This is a shared checkout, so run `git diff --cached --name-only` before each commit and unstage anything that is not yours with `git restore --staged <path>`.

LIFECYCLE TRANSITION, AND IT IS CONDITIONAL, WHICH IS THE ONE THING NOT TO GET WRONG HERE. This plan is `- Kind: orchestrator`, so on the RUNNER path it is RETIRED without an agent turn once all three children read `executed` on disk (`runner_shared.dispatch_orchestrator_item` -> `ipd_lifecycle.retire_orchestrator`, gated on `runner_shared.evaluate_set_retirement`), and that path deliberately SKIPS the pre-transition E/V checkpoint (`ipd_lifecycle.ROLLUP_OMITTED_GATES`). Do NOT run `aw ipd finalize` on this file under a runner, and do NOT hand-roll a `git mv` to `executed/` on any path. If this Set is executed BY HAND instead, the executor owns the transition and must genuinely perform V-01 through V-03 with pasted evidence before `aw ipd lint --phase pre-transition` conforms and `aw ipd finalize` moves the file.

BECAUSE RETIREMENT SKIPS THE CHECKPOINT, V-01 THROUGH V-03 CAN BE MARKED COMPLETE HAVING NEVER BEEN INSPECTED. That is tolerable here for a specific reason and not as a general allowance: each of the three restates the exact fact retirement itself gates on (every child `executed` on disk), so the skipped inspection asserts nothing the gate did not already check. The ORCHESTRATOR COVERAGE GATE additionally probes, before any agent turn, whether this parent carries work no child covers, and refuses unattended when it does. The one Set-level criterion NO child owns is recorded openly as OQ-02 rather than parked here as an item, precisely because an item on this parent would be performed by nobody.

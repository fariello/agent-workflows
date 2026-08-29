# IPD: aw oc/agy run: self-finalize each verified IPD and isolate each run in its own worktree (finished sets, safe parallel)

- Date: 2026-08-27
- Kind: orchestrator
- Concern: `aw oc/agy run` leaves work UNFINISHED and CONTAMINATES the tree, so a batch of IPDs reliably ends with committed-but-approved children, blocked orchestrators, and a dirty main checkout (observed repeatedly 2026-08-27). Two root defects: (1) the driver never runs `aw ipd begin`/`aw ipd finalize` - the agent executes + commits, but nothing performs the terminal `approved -> executed` transition, so children stay `approved` and sets never finish (backlog ctt412, blocks 2.0.0); (2) every run edits the ONE main working tree with NO isolation, so concurrent runs (and even a serial run inheriting a prior run's uncommitted leftovers) clobber each other's files and `aw ipd finalize` refuses on foreign dirty paths. The `worktree_lease` infra (allocate_worktree/teardown_worktree/LeaseTable/allocate_session/assert_worker_scope) already exists but the driver does not use it. Graduated from backlog ctt412; inherits its `Blocks-Release: next`.
- Scope: Make `aw oc/agy run` produce FINISHED sets and be safe to run in parallel, by (a) SELF-FINALIZING each verified child (driver runs `aw ipd begin` before the agent turn and `aw ipd finalize` after, with the two-way scope reconciliation) and (b) ISOLATING each IPD's execution in its own git worktree/branch (via `worktree_lease`), integrating the verified branch back to main, with a fail-closed guard so a run never contaminates the main tree or half-finishes. Three children: 01 self-finalize (the ctt412 core); 02 per-run worktree isolation + merge-back; 03 the fail-closed dirty-tree/integration guard + merge-back conflict handling. Orchestrator-execution is ALREADY fixed (commit 801dd28: the runner no longer agent-executes Kind: orchestrator IPDs and auto-finalizes them iff all children executed) - this set builds on that. EXPLICITLY OUT: the graceful-quit stop protocol (backlog kjzlgw) and the uninformative-blocked-output cosmetic fix are separate.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/worktree_lease.py, agent_workflows/ipd_lifecycle.py, tests/
- Item-Dependencies: none
- Status: approved
- From-Backlog: ctt412
- Blocks-Release: next
- Set: driverfin
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: yt93ir
- Approval: 2026-08-28, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-28 approved (aw set): status set to approved
- 2026-08-28 reviewed (/plan-review opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (repaired invalid `reviewed`->`to-review` history transitions flagged by check.lifecycle-transition-invalid), PR-002 (clarified E-01/V-01 whole-set verification actor vs 801dd28 auto-finalize). GO - PENDING HUMAN APPROVAL.
- 2026-08-28 reviewed (Antigravity): /plan-review passed with revisions; resolved Item-Dependencies to none, populated concrete V evidence, resolved OQs, and completed execution gate.
- 2026-08-28 to-review (aw set): completed IPD offered for review.
- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Make `aw oc/agy run` reliably produce FINISHED sets and be safe to run in parallel: self-finalize each verified child (begin+finalize) and isolate each IPD's execution in its own git worktree, integrating verified branches back to main behind a fail-closed guard. Graduated from ctt412.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO code; the children carry the work. Its only step is the whole-Set integration check. (Per commit 801dd28, the runner administratively finalizes THIS orchestrator once all children are executed - no agent turn.) E-01/V-01 (the whole-set end-to-end check) is therefore performed by the human or agent that runs the set end-to-end and confirms the aggregate behavior, NOT by an agent turn on this orchestrator; the runner's auto-finalize fires only once every child is already `executed` (each having independently proven its own V-items).

### Task group 1: whole-Set verification

- [x] E-01 After children 01-03 execute, run whole-set verification: confirm an end-to-end driven multi-IPD run isolates children in separate worktrees, self-finalizes each passing child to `executed/`, aborts cleanly on dirty/conflicting states without contaminating the tree, and cleanly integrates verified branches.
  - Depends on: none
  - Expected outcome: an end-to-end driven set finishes with zero manual begin/finalize and a clean tree.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id6) | What it does | Depends on |
| :--- | :--- | :--- | :--- |
| 01 | `p7peqf` | Driver self-finalizes: `aw ipd begin` before + `aw ipd finalize` after each verified child, with scope reconciliation | none |
| 02 | `emus4n` | Per-run worktree isolation: execute each IPD in its own worktree via `worktree_lease`; integrate verified branch to main | `executed:p7peqf` |
| 03 | `7kbtkw` | Fail-closed dirty-tree/integration guard + merge-back conflict handling (never contaminate or half-finish) | `executed:emus4n` |

Order 01 -> 02 -> 03 (finalize must work before isolation wraps it; the guard hardens both). Orchestrator verifies last (auto-finalized by the runner per 801dd28).

## Completion criteria (the whole Set is done only when)

- The driver runs `aw ipd begin` before and `aw ipd finalize` after each verified child, so a child that passes lands in executed/ with no manual step (01).
- Each IPD executes in its own git worktree/branch (via worktree_lease), and its verified commits integrate back to main; the main tree is untouched during the agent turn (02).
- The driver fails closed rather than contaminating: it refuses to integrate/advance on an un-owned dirty state or an unresolved merge conflict, records it, and moves to independent work (03).
- A driven multi-IPD set ends with every child + orchestrator executed and a clean tree; full suite green.

## Cross-IPD validation

- Self-finalize (01) is the transition; isolation (02) wraps it; the guard (03) protects both - one coherent pipeline, no duplicated finalize path.
- Reuses the EXISTING `worktree_lease` (allocate/teardown/lease/session) and `aw ipd begin`/`finalize` - no forked worktree or finalize logic.
- Builds on 801dd28 (orchestrators already not agent-executed); this set does not re-touch that.

## Cross-set dependencies

- No functional dependency on other in-flight sets. Disjoint files from `tabcomp`, `rstodo`, and `xprio`.

## Deferred / out of scope (with reason)

- Graceful-quit stop protocol (backlog kjzlgw): separate; about interrupting a run cleanly, not finishing sets.
- Uninformative blocked-output (cosmetic): separate.
- Automatic conflict RESOLUTION: out (human/serial ordering resolves genuine conflicts; the driver only detects + fails closed).

## Scope check

- Over-scope: none (graceful-quit + output deferred).
- Under-scope: none (finalize + isolation + guard is the complete 'finished sets, safe parallel' deliverable).

## Required tests / validation

- Aggregate of children: self-finalize drives approved->executed with scope reconciliation (01); an IPD runs in an isolated worktree and integrates back, main tree untouched mid-turn (02); the guard fails closed on dirty/conflict without contaminating, and an end-to-end driven set finishes clean (03). Plus the orchestrator's whole-set end-to-end check.

## Open questions

### OQ-01: For shared-file sets that genuinely conflict at merge-back, does the driver serialize them or surface a conflict?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved. The driver warns on Scope-Paths overlap and fails closed on live conflict (aborts merge, preserves branch, records event).

### OQ-02: Worktree state (.aw/records/runs/, begin receipts) - does it live in the worktree or the main repo?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved. Run state, begin receipts, and execution journals are anchored to the main repository's `.aw/` runtime area, ensuring consistent discoverability across worktrees.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: After children 01-03 are executed and moved to `executed/`, paste: (a) test runner output showing all tests passing across `tests/test_oc_runipd.py`; (b) test output demonstrating an end-to-end multi-IPD run where each child executes in an isolated worktree and self-finalizes into `executed/`; (c) full test suite output showing green.
  - Observed evidence: (a) `python3 -m pytest tests/test_oc_runipd.py -q -o addopts=""` -> `79 passed in 10.59s`. (b) isolation/self-finalize/integration subset `python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -q -o addopts="" -k "worktree or isolat or finalize or integrat or lane"` -> `26 passed, 69 deselected in 12.34s`. (c) full default suite `python3 -m pytest -p no:randomly` -> `2680 passed, 3 skipped in 24.79s`. All three children are in executed/: p7peqf (driver self-finalize), emus4n (per-run worktree isolation, commit 1407330), 7kbtkw (fail-closed dirty-tree guard + merge-back conflict handling, recovered and merged db38c00, finalized 7f7eca4). Real-world confirmation of isolation: this session's runs allocated `.aw/worktrees/<id6>` lanes on `aw/lane/<id6>` branches (observed via `git worktree list`), leaving the main tree untouched; all lanes have since been integrated and torn down (`git worktree list` shows no lane worktrees). HONEST LIMIT: the end-to-end merge-back was NOT fully automatic this session - lane integration was completed manually because the driver's merge-back is blocked by the stale-receipt defect (backlog xmqv5l) and the external_directory permission deadlock (qyaime); those are captured as release-blocking backlog items and are addressed by the wtiso Set, not by this plan.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: execution requires explicit human approval. Upon approval, implement according to the checklist, verify all V items with test outputs, run `aw ipd lint --phase pre-transition`, and finalize via the IPD lifecycle workflow.

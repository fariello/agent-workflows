# IPD: Worktree isolation + driver-owned control plane: adopt research x03wgn

- Date: 2026-08-28
- Kind: orchestrator
- Concern: Worktree isolation (emus4n) shipped, but the runner leaves per-machine control state (`.aw/state`, `.aw/records/runs`) in-repo and cwd-relative, and its prompt forces the in-lane agent to touch main-repo paths. This produces three live failures, all diagnosed this session and captured as backlog: qyaime (external_directory permission prompt deadlocks a non-interactive --auto turn forever), xmqv5l (begin freezes a whole-file plan_content_digest so a normal self-execution goes stale and finalize/merge-back refuses), dh0uno (inner aw resolves state relative to the worktree, forking a second receipt/run tree the driver cannot see and teardown destroys). Research x03wgn (.aw/records/research/20260828-wtiso-00-x03wgn) establishes these are one architecture problem and prescribes a driver-owned control plane vs lane-owned product data plane, out-of-repo machine state keyed by git-common-dir, driver-performed lifecycle (so a FORGETFUL agent that runs no aw tools still completes safely), a layered permission-deadlock defense, and real candidate-merge integration. This orchestrator sequences the 7-child migration adopting x03wgn.
- Scope: ORCHESTRATOR - authors NO product code. Its own execution work is (E-01) whole-Set verification only. The children carry all implementation. This plan owns: the child table + dependency chain, the shared anti-greenwash execution contract every child inherits, the Set completion criteria, and the cross-IPD no-drift checks. It cites research x03wgn as the binding design and each child names the exact x03wgn section(s) it implements.
- Scope-Paths: .aw/records/plans/pending/20260828-wtiso-00-bl9q3d-worktree-isolation-driver-owned-control-plane-adopt-research.ipd.md
- Item-Dependencies: none
- From-Backlog: qyaime
- Status: to-review
- Set: wtiso
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: bl9q3d

## Workflow history
- 2026-08-29 to-review (aw set): status set to to-review

- 2026-08-28 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Adopt research x03wgn across a 7-child, dependency-ordered migration that (1) stops the live permission-deadlock and silent-loss failures, (2) moves lifecycle authority into the driver so a forgetful agent cannot cause a false or lost result, (3) unifies path resolution and (4) relocates machine-state out of the repo, then (5) adds real candidate-merge integration + crash recovery, with (6) an optional OS-sandbox hard mode. Every child is authored to be green-wash-proof: acceptance is a pasted command result or a driver/verifier observation of real git+filesystem state, never an agent's prose claim.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: whole-Set verification (orchestrator authors no code)

- [ ] E-01 After ALL children (wtiso-01..07) are in `executed/`, run the whole-Set verification: confirm every child's V-items were satisfied with pasted evidence, confirm the acceptance criteria in x03wgn Section (implementation acceptance criteria) hold against the real repo, and confirm no cross-IPD drift (see Cross-IPD validation). Author no product code here.
  - Depends on: none
  - Expected outcome: a single verification record demonstrating each acceptance criterion holds, with pasted command evidence; any failing criterion blocks the Set (orchestrator stays not-executed).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## The shared anti-greenwash execution contract (every child inherits this verbatim)

This contract is the Set's defining property. Each child IPD MUST embed it in its own Approval-and-execution gate; this orchestrator is the source of truth, and cross-IPD validation V-02 checks each child carries it.

1. **Prose is never evidence.** No E-item is complete on an assertion. Each E-item names ONE observable action; each paired V-item names FALSIFIABLE evidence: an exact command to run plus the specific string/exit-code/file-state that must appear. "Tests pass", "done", "verified", "should work" are forbidden as evidence.
2. **Paste real output (HARD MUST).** Every V-item's Observed evidence MUST be the ACTUAL pasted stdout/stderr + exit code of the named command, run in this repo at execution time. Fabricated, summarized, remembered, or "expected" output is a validation failure and a GP2 honesty violation. A V-item whose command was not run stays `Result: pending`.
3. **Adversarial acceptance is mandatory.** Because this Set is ABOUT untrustworthy agents, each child MUST include at least one adversarial test proving the guard fires: a test that a wrong/forgetful/lying behavior is DETECTED and BLOCKED (e.g. a fabricated outcome.json does not mark success; a stale/forked receipt is refused; an unanswerable permission prompt is killed, not awaited). Green-path-only tests are insufficient and are an UNDER-SCOPE finding.
4. **Determinism over model judgment.** Where a check can be a pure function + unit test (path resolution, receipt validity, scope reconciliation, retention classification), it MUST be, and the hook/driver/verifier MUST call the SAME predicate library so rules cannot drift.
5. **Scope fence.** Touch ONLY the child's declared Scope-Paths. Do not edit sibling children, this orchestrator, or product code outside scope. If the work seems to need more, STOP and report - do not silently broaden.
6. **Path-scoped commits, never push.** `git commit -m msg -- <paths>`; never `git add -A`/bare/`-a`; never push; never `--no-verify`.
7. **Lifecycle move is a POST-gate step.** Verify every V-item with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed. (NOTE: until wtiso-03 lands, finalize may hit xmqv5l; if so, record substantially-complete honestly rather than forcing.)
8. **Cite the research.** Each child's Findings section MUST cite the exact x03wgn section(s) it implements (research doc 20260828-wtiso-00-x03wgn) so a reviewer can check fidelity to the approved design.


## Child IPDs, sequence, and dependencies

Each child depends on the prior via `Item-Dependencies: executed:<id6>` (strict linear chain; the research mandates writer-model-correct-before-relocation ordering). From-Backlog links tie the failures to the fixing phase.

| Order | Id | Phase / what it does | Depends on | From-Backlog | x03wgn section |
|---|---|---|---|---|---|
| 00 | bl9q3d | Orchestrator (this) | - | qyaime | 1, 8 |
| 01 | 8zgybk | Phase 0: freeze state taxonomy + characterization & adversarial tests | - | - | 2, 7, 8 (Phase 0) |
| 02 | qcqhj7 | Phase 1: stop deadlock + silent loss (in-lane paths, deny external/question, watchdogs, minimal input manifest, AW_MISSING_INPUT, clean-base, teardown preservation) | executed:8zgybk | qyaime | 6, 8 (Phase 1) |
| 03 | rchpms | Phase 2: driver-owned lifecycle authority (driver-created receipts, worker-role verbs refuse, OBSERVED from git+process, five-way output classifier + harvest) | executed:qcqhj7 | xmqv5l | 2, 5, 8 (Phase 2) |
| 04 | 7p9n2v | Phase 3: one typed ExecutionContext/PathResolver keyed by git-common-dir checkout-id; AST guard | executed:rchpms | dh0uno | 3, 8 (Phase 3) |
| 05 | 58ha43 | Phase 4: relocate machine-state out-of-repo (XDG state dir), aw migrate-runtime-state, remove receipt copies | executed:7p9n2v | dh0uno | 3, 8 (Phase 4) |
| 06 | 2c122z | Phase 5: real candidate-merge integration + full crash recovery (integration lock, expected-tip recheck, publication projection, aw recover/doctor, cross-platform locks, process-tree kill) | executed:58ha43 | - | 5, 7, 8 (Phase 5) |
| 07 | 1o4eif | Phase 6: optional OS-sandbox hard mode (host capability contract, read-only git-common-dir, driver-owned git mutation, read-only discovery phase) | executed:2c122z | - | 4, 8 (Phase 6) |

## Completion criteria (the whole Set is done only when)

Each criterion is an x03wgn "implementation acceptance criterion" and must be shown with pasted evidence in E-01's verification record:

- Two concurrent lanes + every inner read-only `aw` resolve the SAME checkout identity but DISTINCT lane roots (test output).
- A lane that uses NO custom tools still completes safely and yields an accurate driver report (adversarial test).
- A task needing an approved untracked input gets a digest-verified lane copy and NEVER needs live original-checkout access.
- A request for a missing original-checkout file is denied, classified, materialized-if-safe, resumed with NO interactive prompt.
- A permission ask cannot leave a headless root OR child session waiting indefinitely (killed + recorded).
- A lane cannot silently create authoritative receipts/reports/decisions/locks/journals/integration records.
- Killing the worker at any point preserves and classifies all work (crash-injection tests).
- Integration tests run on the EXACT merged candidate; target movement forces rebuild.
- Recovery explains every retained worktree/branch/lock/receipt/transaction/candidate WITHOUT a model.
- Removing a lane is always preceded by a durable event proving its content was integrated, abandoned, or preserved.

## Cross-IPD validation

- No-drift: hook, `aw lane status`, driver, finalize, and integration all call ONE pure gate/predicate library (grep shows a single import site set; no duplicated rule logic).
- Every child embeds the shared anti-greenwash contract verbatim (checked in V-02).
- The Item-Dependencies chain is strictly linear 01->02->...->07 and `aw ipd dependencies`/lint report it consistently.
- No child re-forks a second path resolver (after Phase 3, an AST guard forbids raw `.aw/state`/`.aw/records/runs` construction outside the resolver + bounded migration code).

## Deferred / out of scope (with reason)

- Actual implementation of any phase: owned by the respective child, not here.
- Phase 6 (OS sandbox) is optional/hardening; the Set's core value is delivered by 01-06. 06->07 dependency stands but 07 may be deferred/parked without blocking the release-gating fixes (qyaime/xmqv5l/dh0uno are resolved by 02-05).

## Scope check

- Over-scope: none (orchestrator authors no code).
- Under-scope: none (child table + contract + completion criteria + cross-IPD checks are the complete orchestrator deliverable).

## Required tests / validation

- E-01 verification runs the acceptance-criteria checks above and pastes their output.
- Validation command (whole-Set, after all children executed): `python3 -m pytest -p no:randomly -q` (full suite green) plus the specific adversarial tests each child added (enumerated in E-01's record). Paste ACTUAL output.

## Open questions

### OQ-01: Is Phase 6 (OS-sandbox hard mode) in-scope for the release this Set gates, or a follow-up?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: Follow-up-eligible. The release blockers (qyaime/xmqv5l/dh0uno) are fully resolved by children 02-05; Phase 6 is defense-in-depth for a malicious (not merely forgetful) same-user worker, which x03wgn explicitly scopes as an optional profile. 07 keeps its dependency on 06 but may be parked without blocking the Set's release-gating value.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: A whole-Set verification record (path cited) with THREE parts, each pasted from real execution: (1) for EACH completion criterion above, the ACTUAL output of the command/test proving it holds against the real repo, plus a `python3 -m pytest -p no:randomly -q` full-suite result; (2) the anti-greenwash-property check - grep/inspection showing each child wtiso-01..07 embeds the shared anti-greenwash execution contract AND that hook/`aw lane status`/driver/finalize/integration import ONE shared predicate library (no duplicated rule logic); (3) the AST/static guard (added by Phase 3) rejecting raw `.aw/state`/`.aw/records/runs` construction outside the resolver, shown BOTH passing on the clean tree AND failing on a planted violation. Any part without pasted passing evidence leaves this pending and the orchestrator not-executed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: one architecture (adopt x03wgn); children are strictly-ordered phases of that single migration, each independently executable/verifiable but dependency-chained.

Execution contract (orchestrator):

1. Open questions: OQ-01 resolved; execution requires explicit human approval of the Set.
2. This orchestrator authors NO product code. Its only E-item (E-01) is whole-Set verification AFTER all children are executed. Do NOT finalize this orchestrator until wtiso-01..07 (or 01..06 with 07 explicitly parked) are in executed/.
3. Honesty rule (HARD MUST): E-01's verification record pastes ACTUAL command output for every acceptance criterion; never claim a criterion holds without running its check.
4. Commit ONLY this plan file, path-scoped; never push.
5. Lifecycle move on completion: verify V-01+V-02 with pasted evidence, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize` this orchestrator. An orchestrator finalizes only after its children are terminal.

The shared anti-greenwash execution contract (above) is the authority every child copies into its own gate; do not weaken it per child.

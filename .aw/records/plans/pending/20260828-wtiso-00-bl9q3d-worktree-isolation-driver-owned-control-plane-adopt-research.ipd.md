# IPD: Worktree isolation + driver-owned control plane: adopt research x03wgn

- Date: 2026-08-28
- Kind: orchestrator
- Concern: Worktree isolation (emus4n) shipped, but the runner leaves per-machine control state (`.aw/state`, `.aw/records/runs`) in-repo and cwd-relative, and its prompt forces the in-lane agent to touch main-repo paths. This produces three live failures, all diagnosed this session and captured as backlog: qyaime (external_directory permission prompt deadlocks a non-interactive --auto turn forever), xmqv5l (begin freezes a whole-file plan_content_digest so a normal self-execution goes stale and finalize/merge-back refuses), dh0uno (inner aw resolves state relative to the worktree, forking a second receipt/run tree the driver cannot see and teardown destroys). Research x03wgn (.aw/records/research/20260828-wtiso-00-x03wgn) establishes these are one architecture problem and prescribes a driver-owned control plane vs lane-owned product data plane, out-of-repo machine state keyed by git-common-dir, driver-performed lifecycle (so a FORGETFUL agent that runs no aw tools still completes safely), a layered permission-deadlock defense, and real candidate-merge integration. This orchestrator sequences the 7-child migration adopting x03wgn.
- Scope: ORCHESTRATOR - authors NO product code. Its own execution work is (E-01) whole-Set verification only. The children carry all implementation. This plan owns: the child table + dependency chain, the shared anti-greenwash execution contract every child inherits, the Set completion criteria, and the cross-IPD no-drift checks. It cites research x03wgn as the binding design and each child names the exact x03wgn section(s) it implements.
- Scope-Paths: .aw/records/plans/pending/20260828-wtiso-00-bl9q3d-worktree-isolation-driver-owned-control-plane-adopt-research.ipd.md, .aw/records/walkthroughs/
- Item-Dependencies: none
- From-Backlog: qyaime
- Blocks-Release: next
- Status: approved
- Set: wtiso
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: bl9q3d
- Approval: 2026-08-29, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 /plan-review (OpenCode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. Fixed a dangling `V-02` referenced three times (including in the gate's own "verify V-01+V-02") when only V-01 exists - the contract check is V-01 part (2), so an executor could have blocked on a nonexistent item or skipped the check. Restored the 5 x03wgn acceptance criteria the completion list had silently dropped (tracked-but-uncommitted refusal, verified local artifact manifest, SECRETS-never-in-Git, protected-ref/git-common-dir mutation blocking, default/hardened external-write denial), numbered all 15, and attributed each to its owning child. Reconciled the E-01-vs-OQ-01 contradiction over whether wtiso-07 must be executed, and made criteria 9/10 explicitly PARTIALLY VERIFIED when Phase 6 is parked instead of silently unverified. Fixed real exit-blocking release-gate drift: this plan carried `From-Backlog: qyaime` with NO `Blocks-Release`, firing `check.from-backlog-gate-mismatch` (verified live: 5 findings before, 4 after) - added `Blocks-Release: next` and cross-referenced the 4 sibling children that still mismatch and must fix it in their own files. Added `.aw/records/walkthroughs/` to Scope-Paths, since E-01 required writing a verification record with no legal path inside its own scope fence. Named the ONE shared predicate library concretely (`agent_workflows/lane_status.py` from rchpms) with a real grep command, as the no-drift check was unverifiable as written. Hardened the gate (named full-suite command, scope fence, no `--no-verify`/tag/release) and added V-01 part (4) requiring a zero-finding release-gate check.
- 2026-08-29 reviewed (aw set): status set to reviewed
- 2026-08-29 to-review (aw set): status set to to-review

- 2026-08-28 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Adopt research x03wgn across a 7-child, dependency-ordered migration that (1) stops the live permission-deadlock and silent-loss failures, (2) moves lifecycle authority into the driver so a forgetful agent cannot cause a false or lost result, (3) unifies path resolution and (4) relocates machine-state out of the repo, then (5) adds real candidate-merge integration + crash recovery, with (6) an optional OS-sandbox hard mode. Every child is authored to be green-wash-proof: acceptance is a pasted command result or a driver/verifier observation of real git+filesystem state, never an agent's prose claim.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: whole-Set verification (orchestrator authors no code)

- [ ] E-01 Once children wtiso-01..06 are ALL in `executed/` AND wtiso-07 is either `executed/` or explicitly parked per OQ-01, run the whole-Set verification: confirm every child's V-items were satisfied with pasted evidence, confirm EACH of the 15 numbered completion criteria below holds against the real repo (recording criteria 9 and 10 as PARTIALLY VERIFIED if 07 is parked), and confirm no cross-IPD drift (see Cross-IPD validation, including a re-run of the release-gate checker). Write the verification record to `.aw/records/walkthroughs/` (see Scope-Paths). Author no product code here.
  - Depends on: none
  - Expected outcome: a single verification record at the declared `.aw/records/walkthroughs/` path demonstrating each of the 15 criteria with pasted command evidence (criteria 9/10 partially, with the parked child cited, if 07 is parked); any unconditional criterion that fails blocks the Set (orchestrator stays not-executed).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## The shared anti-greenwash execution contract (every child inherits this verbatim)

This contract is the Set's defining property. Each child IPD MUST embed it in its own Approval-and-execution gate; this orchestrator is the source of truth, and V-01 part (2) checks each child carries it.

1. **Prose is never evidence.** No E-item is complete on an assertion. Each E-item names ONE observable action; each paired V-item names FALSIFIABLE evidence: an exact command to run plus the specific string/exit-code/file-state that must appear. "Tests pass", "done", "verified", "should work" are forbidden as evidence.
2. **Paste real output (HARD MUST).** Every V-item's Observed evidence MUST be the ACTUAL pasted stdout/stderr + exit code of the named command, run in this repo at execution time. Fabricated, summarized, remembered, or "expected" output is a validation failure and a GP2 honesty violation. A V-item whose command was not run stays `Result: pending`.
3. **Adversarial acceptance is mandatory.** Because this Set is ABOUT untrustworthy agents, each child MUST include at least one adversarial test proving the guard fires: a test that a wrong/forgetful/lying behavior is DETECTED and BLOCKED (e.g. a fabricated outcome.json does not mark success; a stale/forked receipt is refused; an unanswerable permission prompt is killed, not awaited). Green-path-only tests are insufficient and are an UNDER-SCOPE finding.
4. **Determinism over model judgment.** Where a check can be a pure function + unit test (path resolution, receipt validity, scope reconciliation, retention classification), it MUST be, and the hook/driver/verifier MUST call the SAME predicate library so rules cannot drift.
5. **Scope fence.** Touch ONLY the child's declared Scope-Paths. Do not edit sibling children, this orchestrator, or product code outside scope. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt). Do NOT edit a sibling plan or this orchestrator, and do NOT reimplement a rule another plan owns.
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

This list is the COMPLETE x03wgn "Implementation acceptance criteria" set (research Section 9, 15 criteria) - it is reproduced in full deliberately, because a partial copy would let the Set "pass" while an approved criterion went unverified. Each must be shown with pasted evidence in E-01's verification record. `owner` names the child that implements it, so a parked child makes its criteria explicitly unverified rather than silently dropped (see the Phase-6 conditionality note below).

1. Two concurrent lanes + every inner read-only `aw` resolve the SAME checkout identity but DISTINCT lane roots (test output). [owner: 7p9n2v]
2. A lane that uses NO custom tools still completes safely and yields an accurate driver report (adversarial test). [owner: rchpms]
3. A task needing an approved untracked input gets a digest-verified lane copy and NEVER needs live original-checkout access. [owner: qcqhj7]
4. A request for a missing original-checkout file is denied, classified, materialized-if-safe, resumed with NO interactive prompt. [owner: qcqhj7]
5. Tracked-but-uncommitted main content can never be silently omitted: default mode REFUSES it before launch, and any future snapshot mode records it separately from the agent delta. [owner: qcqhj7 clean-base gate]
6. Tracked product changes and sanitized durable AW records survive through Git, while useful nontracked outputs survive through a VERIFIED local artifact manifest. [owner: rchpms five-way classifier + verified harvest; 2c122z publication projection]
7. Secrets never enter Git or ordinary reports/artifact bundles; unknown ignored files PREVENT teardown. [owner: rchpms secret-local class + unknown-blocks-teardown]
8. A lane cannot silently create authoritative receipts/reports/decisions/locks/journals/integration records. [owner: rchpms worker-role refusal]
9. Unexpected mutations to protected refs, Git configuration/hooks, or other worktree administration BLOCK integration; hardened workers cannot write the Git common directory. [owner: 2c122z integration block; hardened-worker half is 1o4eif E-04/E-09 - PHASE-6 CONDITIONAL]
10. In default mode, accidental external writes are denied or detected; in hardened mode, the OS denies them. [owner: qcqhj7 default-mode deny/detect; OS-denial half is 1o4eif E-05/E-08 - PHASE-6 CONDITIONAL]
11. A permission ask cannot leave a headless root OR child session waiting indefinitely (killed + recorded). [owner: qcqhj7 watchdogs]
12. Killing the worker at any point preserves and classifies all work (crash-injection tests). [owner: 2c122z]
13. Integration tests run on the EXACT merged candidate; target movement forces rebuild. [owner: 2c122z]
14. Recovery explains every retained worktree/branch/lock/receipt/transaction/candidate WITHOUT a model. [owner: 2c122z aw recover/doctor --lanes]
15. Removing a lane is always preceded by a durable event proving its content was integrated, abandoned, or preserved. [owner: rchpms teardown gate + 2c122z durable events]

PHASE-6 CONDITIONALITY (reconciles E-01 with OQ-01): criteria 9 and 10 each have a hardened-mode half owned by `1o4eif` (Phase 6), which OQ-01 permits parking. If 07 is parked, E-01 MUST record criteria 9 and 10 as PARTIALLY VERIFIED - default-mode half demonstrated, hardened-mode half explicitly deferred with the parked child cited - and MUST NOT mark them satisfied. All other 13 criteria are unconditional and must be fully demonstrated regardless.

## Cross-IPD validation

- No-drift: hook, `aw lane status`, driver, finalize, and integration all call ONE pure gate/predicate library, which is `agent_workflows/lane_status.py` as introduced by child `rchpms` (Phase 2). Verification is concrete: `grep -rn "import lane_status\|from agent_workflows.lane_status" agent_workflows/` shows the driver/finalize/integration/`aw lane status` call sites resolving to that ONE module, and no second copy of a classification/receipt/scope rule exists elsewhere. If a later child needs a predicate the module lacks, it EXTENDS `lane_status.py`; it does not fork a parallel rule implementation.
- Every child embeds the shared anti-greenwash contract verbatim (checked in V-01 part (2)).
- The Item-Dependencies chain is strictly linear 01->02->...->07 and `aw ipd dependencies`/lint report it consistently. (Verified at review time: `8zgybk` none -> `qcqhj7` -> `rchpms` -> `7p9n2v` -> `58ha43` -> `2c122z` -> `1o4eif`.)
- No child re-forks a second path resolver (after Phase 3, an AST guard forbids raw `.aw/state`/`.aw/records/runs` construction outside the resolver + bounded migration code).
- RELEASE-GATE CONSISTENCY (added at review; currently FAILING for 4 children): every plan carrying `- From-Backlog: <id6>` MUST also carry a `- Blocks-Release:` value MATCHING that backlog item's, or the deterministic `check.from-backlog-gate-mismatch` rule fires and is EXIT-BLOCKING (`check_engine.check_release_gate_consistency`). All three source items (qyaime, xmqv5l, dh0uno) carry `Blocks-Release: next` (the `planned` 2.0.0 release f33nrj), so each From-Backlog plan needs `- Blocks-Release: next`. At review time this orchestrator was FIXED, but FOUR children still mismatch and MUST each be corrected in their OWN file (scope fence: this orchestrator may not edit them): `qcqhj7` (qyaime), `rchpms` (xmqv5l), `7p9n2v` (dh0uno), `58ha43` (dh0uno) - set with `aw ipd set <status> <id6> --blocks-release next`. E-01 MUST re-run the checker and show ZERO `check.from-backlog-gate-mismatch` findings before the Set is complete; a nonzero count blocks the Set. Rationale: without this, the release blockers these plans inherit could be closed while 2.0.0 silently lost its gate.

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
  - Required evidence: A whole-Set verification record at a cited `.aw/records/walkthroughs/<...>-walkthrough.md` path with FOUR parts, each pasted from real execution: (1) for EACH of the 15 NUMBERED completion criteria above, the ACTUAL output of the command/test proving it holds against the real repo, naming the criterion number and its owning child, plus a `python3 -m pytest -p no:randomly -q` full-suite result - and if wtiso-07 is parked, criteria 9 and 10 are recorded as PARTIALLY VERIFIED (default-mode half pasted, hardened-mode half deferred citing the parked child), never as satisfied; (2) the anti-greenwash-property check - grep/inspection showing each child wtiso-01..07 embeds the shared anti-greenwash execution contract AND that `grep -rn "import lane_status\|from agent_workflows.lane_status" agent_workflows/` proves hook/`aw lane status`/driver/finalize/integration resolve to the ONE `agent_workflows/lane_status.py` predicate library with no duplicated rule logic; (3) the AST/static guard (added by Phase 3) rejecting raw `.aw/state`/`.aw/records/runs` construction outside the resolver, shown BOTH passing on the clean tree AND failing on a planted violation (paste both runs); (4) the release-gate check - pasted output of the `check.from-backlog-gate-mismatch` rule showing ZERO findings across all wtiso plans (i.e. every `From-Backlog` plan carries a matching `Blocks-Release`), e.g. via `aw attention --check` or `python3 -c "from pathlib import Path; from agent_workflows import check_engine as ce; print(ce.check_release_gate_consistency(Path('.')))"`. Any part without pasted passing evidence leaves this pending and the orchestrator not-executed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: one architecture (adopt x03wgn); children are strictly-ordered phases of that single migration, each independently executable/verifiable but dependency-chained.

Execution contract (orchestrator):

1. Open questions: OQ-01 resolved; execution requires explicit human approval of the Set.
2. This orchestrator authors NO product code. Its only E-item (E-01) is whole-Set verification AFTER the children are terminal. Do NOT finalize this orchestrator until wtiso-01..06 are in executed/ and 07 is executed/ or explicitly parked per OQ-01.
3. Honesty rule (HARD MUST): E-01's verification record pastes the ACTUAL stdout/stderr + exit code of every check, run in this repo at execution time, for all 15 numbered criteria plus the full-suite run `python3 -m pytest -p no:randomly -q`. Never claim a criterion holds without running its check; a criterion whose check was not run stays unsatisfied and the orchestrator stays not-executed. Fabricated, summarized, remembered, or "expected" output is a validation failure and a GP2 honesty violation.
4. Scope fence: touch ONLY this plan file and the E-01 verification record under `.aw/records/walkthroughs/` (the declared Scope-Paths). Do NOT edit sibling children (including to fix their `Blocks-Release`; that is each child's own file), the research report, or any product code. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt). Do NOT edit a sibling plan or this orchestrator, and do NOT reimplement a rule another plan owns.
5. Commit ONLY the files in Scope-Paths, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push; never `--no-verify`; never create a git tag, GitHub Release, or registry upload.
6. Lifecycle move on completion: verify V-01 (ALL FOUR parts) with pasted evidence, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize` this orchestrator. An orchestrator finalizes only after its children are terminal. (This orchestrator has exactly ONE E-item and therefore exactly ONE V-item; there is no V-02. The anti-greenwash-property, AST-guard, and release-gate checks are V-01 parts (2), (3), and (4), not separate V-items.)

The shared anti-greenwash execution contract (above) is the authority every child copies into its own gate; do not weaken it per child.

# IPD: the runner-owned orchestrator retirement transition

- Date: 2026-09-06
- Kind: child
- Concern: `finalize_orchestrator` (`oc_runipd.py:773-796`) has NEVER once succeeded. Measured across all 102 durable run records: `orchestrator-finalized` fired 0 times, `orchestrator-deferred` fired 28 times across 15 distinct orchestrators. It was born broken: the gated terminal transition landed `99760832` (2026-08-24) and `finalize_orchestrator` was written `801dd28a` (2026-08-27), three days later, against a gate that already refused it. Two gates block it and both are structural, not incidental. FIRST, it shells to `aw ipd set executed`, which requires a `begin` receipt; an orchestrator is never agent-executed so nothing ever calls `aw ipd begin` for it and no receipt can exist. SECOND, with a receipt present (verified by writing one, then deleting it) the `pre-transition` checkpoint refuses on six `IPD-S404` findings because `check_checkpoint` (`ipd_lint.py:694-725`) requires every `E-*` performed and every `V-*` evidenced UNCONDITIONALLY, and `grep -c orchestrator agent_workflows/ipd_lint.py` is 0 so the linter has no orchestrator concept at all. That is the contradiction: the honesty gate demands evidence for items that, under `aw run`, are by design performed by nobody.
- Scope: Make a runner-owned retirement transition that actually works, resolving spec `77tr3o` R-5 (the E/V pre-transition requirement) and R-6 (the receipt requirement) EXPLICITLY rather than by bypass, and writing an honest terminal history entry per R-4. THE R-5 SHAPE IS DECIDED, not left to the executor: the maintainer chose a SEPARATE runner-owned rollup transition and ruled `ipd_lint.py` out of bounds, so this plan adds a transition and does NOT teach the honesty checker any exception. Consumes child 01's predicate; it performs the transition and does NOT decide eligibility itself. It does NOT touch either runner's dispatch branch (child 03), does NOT relax any gate for CHILD plans, and adds NO path by which an ordinary plan can reach `executed` without evidence.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/runner_shared.py, tests/test_orchestrator_retirement.py
- Item-Dependencies: executed:5942n7
- Status: approved
- Readiness: go-pending-approval
- Set: orchretire
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ueg5cf
- Approval: 2026-09-06, recorded via aw ipd set: status set to approved
- From-Backlog: kxkc04
- From-Spec: 77tr3o

## Workflow history
- 2026-09-06 approved (aw set): status set to approved
- 2026-09-06 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review complete: PR-201..PR-204 fixed, Readiness go-pending-approval

- 2026-09-06 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-201..PR-204 all FIXED, no deferrals, no open questions. This is the Set's highest-risk plan because it deliberately OPENS a lifecycle gate, and the review was conducted on that basis: every claim re-verified plus a hunt for ways the opened gate could reach an ordinary plan. Three HIGH findings, all from reading `ipd_lifecycle.py` rather than the plan's account of it. PR-201: the worker-role refusal is NOT inheritable, because `worker_role_active` is called in the CLI wrappers `run_begin` (`:2223`) and `run_finalize` (`:2403`) and NOT inside `finalize()` (exactly two call sites in the module), so a new transition function starts with NO role guard and a managed worker could create lifecycle authority through it; added E-06/V-06 to close it. PR-202: E-01's "every other gate" named five gates while `finalize` performs at least nine, omitting the exclusive finalize LOCK (`:303`), the two-phase transaction JOURNAL (`:130-143`), EARLY CRASH RECOVERY (`:1744-1760`) and the idempotent pre-commit rollback (`:1632`), so a drift test built to the short list would pass while the rollup silently ran lockless and journal-less inside a live runner in a shared checkout. PR-203: gating the route on `Kind: orchestrator` alone makes it retire whatever it is pointed at, and `action_for` returns `orchestrate` from `reviewed` onward, so the transition must require child 01's eligibility verdict itself. PR-204 (MED): the receipt also carries `base_head`, the baseline the whole scope delta is computed from (`:1355-1364`), so "no receipt" silently means "no scope reconciliation" and that consequence must be stated and asserted rather than discovered. Self-review disclosure in the review record.
- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored complete from approved spec 77tr3o. Both blocking gates reproduced verbatim at HEAD 844d195c before authoring; the probe receipt written to expose the second gate was deleted.
- 2026-09-06 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give the runner a terminal transition it can actually perform on an Order-0 orchestrator whose Set is
complete, which states truthfully that the plan was RETIRED as a rollup step rather than executed, and
which cannot be reused to sneak an ordinary plan past its evidence gate.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: resolve the two gates

- [ ] E-01 Add the SEPARATE runner-owned rollup transition (spec R-5, shape (b), decided by the maintainer 2026-09-06). It MUST NOT route through the `pre-transition` E/V checkpoint, and it MUST still perform every other gate the main path performs (E-02 owns the FULL enumeration, which is longer than the list here: status legality, the plan move, the fail-loud plans-index refresh, the path-scoped lifecycle commit, post-transition lint, AND the finalize lock, transaction journal, and crash recovery). It MUST refuse for anything that is not `Kind: orchestrator`, so the route cannot be aimed at an ordinary plan at all.

  GATE ON ELIGIBILITY, NOT ONLY ON KIND. `Kind: orchestrator` alone is NOT sufficient authority to retire: the route MUST also require child 01's predicate to return eligible, in the transition itself rather than trusting its caller. Reason, and it is concrete: `action_for` returns `orchestrate` for a `reviewed` orchestrator, so a Kind-only route is a function that retires any orchestrator anyone points it at, and the ONLY thing standing between that and a false retirement is a caller remembering to ask. Defense in depth is cheap here and the failure it prevents is the one this Set must never cause.

  Add a comment naming spec `77tr3o` R-5 and OQ-1, stating that `ipd_lint.py` was deliberately left untouched and why, so a later reader does not "simplify" this into the linter exemption that was rejected.
  - Depends on: none
  - Expected outcome: retiring an eligible orchestrator produces none of the six `IPD-S404` findings; pointing the same route at a `Kind: child` plan is REFUSED regardless of that plan's state; and pointing it at a `Kind: orchestrator` plan whose Set is INELIGIBLE is also REFUSED.
  - Execution state: pending

- [ ] E-02 Pin the accepted cost of shape (b): TWO PATHS CAN DRIFT. Write a test that asserts the rollup transition performs the same gate set as the main finalize MINUS the E/V checkpoint, enumerated explicitly rather than by inspection, so a future change that adds a gate to one path and not the other FAILS. The maintainer accepted drift as the known risk of this shape; this E-item is what makes that risk detectable instead of latent.

  THE ENUMERATION IN E-01 IS INCOMPLETE, and completing it is part of this item. `finalize` performs MORE than the five gates E-01 lists, each verified in `ipd_lifecycle.py`: (1) a non-empty `--actor` and `--message` refusal (`:1730-1737`); (2) the EXCLUSIVE finalize LOCK (`acquire_finalize_lock`, `:303`), released in a `finally:`; (3) the two-phase transaction JOURNAL with phases `prepared -> mutating -> ready-to-commit -> committed -> complete` (`:130-143`, `_finalize_transaction` `:1869`); (4) EARLY CRASH RECOVERY that resumes or rolls back a prior interrupted transaction BEFORE the fresh precheck (`:1744-1760`), including the idempotent pre-commit rollback (`_rollback_precommit`, `:1632`); (5) the status-legality check, which for `pre-transition` means "not already terminal" (`ipd_schema.checkpoint_allows_status`, `:1066-1068`); (6) the plan move, (7) the fail-loud plans-index refresh that re-runs `--check` and RAISES if it did not converge (`:1500-1516`), (8) the path-scoped lifecycle commit over exactly `owned_paths`, and (9) post-transition lint. Enumerate the ones the rollup MUST share, and for each one the rollup deliberately does NOT share, say so explicitly with a reason. A drift test built from E-01's five-item list would pass while the rollup silently lacked a lock, a journal, and any crash recovery.

  CONCURRENCY IS NOT OPTIONAL HERE. The rollup runs inside a live runner that may be executing other items, and this repo is a shared checkout, so a rollup that mutates the plans tree and the git index WITHOUT taking the same lock the main path takes can interleave with a child's own finalize. Take the same lock or state precisely why it is safe not to; do not leave it unstated.
  - Depends on: E-01
  - Expected outcome: a test that names each shared gate INCLUDING the lock, the journal, the recovery path and the fail-loud index refresh, fails if the rollup path stops performing one, and would have caught a gate added to `finalize` alone.
  - Execution state: pending

- [ ] E-03 Resolve the receipt requirement (spec R-6) explicitly: either the rollup transition does not require a `begin` receipt, or the runner mints one as part of the rollup. Do NOT silently reuse the child-plan receipt path, which is what fails today. If a receipt is minted, it must be recognizable as a rollup receipt rather than an execution receipt, so it cannot be mistaken for evidence that an agent executed the orchestrator.

  NAME WHAT THE RECEIPT WAS CARRYING BEFORE YOU DROP IT. The receipt is not merely an authority token: `finalize_precheck` reads `base_head` FROM the receipt and refuses when it is missing or `unversioned` (`ipd_lifecycle.py:1355-1362`), because `base_head` is the baseline the whole SCOPE DELTA is computed against (`_changed_path_sources`, `:1170`), and it also reads the receipt's frozen `scope_paths` (`:1364`). So "the rollup does not require a receipt" necessarily also means "the rollup performs no scope reconciliation", and that consequence must be STATED and JUSTIFIED, not discovered later. The justification available to you is that a rollup makes no code edits at all, so its only changed paths are the lifecycle artifacts the transaction itself owns; if you rely on that, ASSERT it (the rollup must verify it changed nothing outside its own `owned_paths`) rather than merely assuming it.
  - Depends on: E-01
  - Expected outcome: the "no begin receipt for <id6>" refusal no longer blocks a legitimate rollup; no receipt is left behind claiming an execution that did not happen; and the scope-delta consequence of the chosen shape is stated explicitly, with the rollup asserting it touched nothing beyond its own lifecycle paths.
  - Execution state: pending

- [ ] E-06 Refuse the rollup in the WORKER role, mirroring `run_begin`/`run_finalize`. The existing refusal is NOT inherited by construction: `worker_role_active` is checked in the CLI wrappers `run_begin` (`ipd_lifecycle.py:2223`) and `run_finalize` (`:2403`), NOT inside `finalize()` itself, and it is checked exactly twice in the module (verified). So a new transition function that does not call those wrappers has NO role guard at all, and a managed worker could create lifecycle authority through it. That is `wtiso-03` E-05's invariant and the same class of hole as the `aw set executed` bypass this plan is careful not to build on. Refuse FIRST, before any selector resolution, gate, or mutation, so a refused invocation has no side effect, and reuse `_refuse_worker_role_verb` rather than writing a second refusal message.
  - Depends on: E-01
  - Expected outcome: the rollup invoked with the worker-role environment set performs NO transition, commit, or plan move and returns the deterministic `AW-LIFECYCLE-ROLE-001` refusal; the coordinator-role path is unaffected.
  - Execution state: pending

### Task group 2: the honest record

- [ ] E-04 Write the terminal history entry per spec R-4: it MUST record that the orchestrator was RETIRED as a rollup step of a runner Set completion, name the run id, and name the children whose execution justified it. It MUST NOT claim the orchestrator's own `E-*`/`V-*` items were performed. Note the existing message string (`"Orchestrator rollup: all children of set X executed (aw oc run, no agent turn)"`) has never actually been written to a plan, so there is no precedent to preserve and the wording is free; it must satisfy the attribution lint, which means keeping the actor string parenthesis-free (`driver_actor`'s documented constraint at `oc_runipd.py:799-810`; today's `--actor "aw oc run (orchestrator rollup)"` contains parentheses and would misparse).
  - Depends on: E-02, E-03
  - Expected outcome: a retired orchestrator's history line names the rollup, the run, and the children, and passes the attribution lint.
  - Execution state: pending

- [ ] E-05 Extend `tests/test_orchestrator_retirement.py` (created by child 01) with transition-level tests: a complete Set retires and lands in `executed/` with the honest history line; a CHILD plan with unperformed E-items is still refused; a human `aw ipd finalize` on an orchestrator outside the rollup path still faces the E/V requirement; and the terminal entry passes the attribution lint. Include a test that the retirement refuses when child 01's predicate says ineligible, so the two halves cannot drift apart.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: tests that fail if the exemption widens to ordinary plans, which is the regression that matters most.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Run the suite BARE (`python3 -m pytest`); configured `addopts` already parallelize and quieten it.
- `finalize` CONSUMES the receipt on success (`ipd_lifecycle.py:2114`), which is why `nna8yz` has no receipt today: its agent finalized in-lane and consumed it. Any minted rollup receipt must not resurrect that confusion.
- The attribution lint parses `- <date> <status> (<actor>): <msg>` and misparses a parenthesized actor; `driver_actor` renders the model as `model=<model>` for exactly this reason.
- `aw set executed` delegates to the gated finalize but checks `worker_role_active` ZERO times (`status_set.py`), unlike `aw ipd finalize`. That is a separate defect (spec Section 4) and must not be "fixed" incidentally here, but do not build the rollup on top of it either.

## Findings

| # | Sev | Where | Finding | Evidence |
|---|-----|-------|---------|----------|
| F-1 | BLOCKER | all runs | The rollup has never worked. 0 `orchestrator-finalized` vs 28 `orchestrator-deferred` across 102 runs. | `grep -rh ... .aw/records/runs/*/events.jsonl \| wc -l` |
| F-2 | BLOCKER | `ipd_lint.py:694-725` | `pre-transition` requires every E performed and V evidenced unconditionally; the linter has no orchestrator concept (`grep -c orchestrator` = 0). | reproduced: six `IPD-S404` findings on `rh5tt6` with a receipt present |
| F-3 | BLOCKER | `oc_runipd.py:773-796` | The rollup requires a `begin` receipt that cannot exist for a plan that is never agent-executed. | reproduced: "no begin receipt for rh5tt6" |
| F-4 | MED | `oc_runipd.py:785` | The rollup actor string `"aw oc run (orchestrator rollup)"` contains parentheses, which the attribution lint's actor capture misparses. | `driver_actor` docstring at `:799-810` documents the constraint |
| F-5 | LOW | timeline | The gate (`99760832`, 2026-08-24) predates the rollup (`801dd28a`, 2026-08-27), so this was never a regression; it never worked. | `git merge-base --is-ancestor 801dd28a 99760832` false |
| F-6 | HIGH | `ipd_lifecycle.py:2223`, `:2403` | The worker-role refusal is NOT inheritable. `worker_role_active` is called in the CLI wrappers `run_begin`/`run_finalize`, NOT inside `finalize()`, and appears exactly twice in the module. A new transition function therefore has NO role guard, so a managed worker could create lifecycle authority through it: the `wtiso-03` E-05 invariant, and the same class of hole as the `aw set executed` bypass this plan avoids building on. E-06 closes it. | source read; `grep -n worker_role_active` yields `:72` (def), `:2223`, `:2403` only |
| F-7 | HIGH | `ipd_lifecycle.py` | E-01's "every other gate" list named five gates; `finalize` performs at least nine, including the exclusive LOCK (`:303`), the two-phase JOURNAL (`:130-143`), EARLY CRASH RECOVERY that resumes or rolls back before the fresh precheck (`:1744-1760`), the idempotent pre-commit rollback (`:1632`), and the actor/message refusals (`:1730-1737`). A drift test written against the five-item list would pass while the rollup silently lacked a lock, a journal and any recovery, inside a live runner sharing this checkout. | source read at review time |
| F-8 | MED | `ipd_lifecycle.py:1355-1364` | The receipt carries more than authority: `finalize_precheck` takes `base_head` from it (refusing a missing or `unversioned` value) and that is the baseline the entire scope delta is computed against, plus the frozen `scope_paths`. So "no receipt" necessarily means "no scope reconciliation", a consequence R-6's two options do not mention and which must be stated and justified rather than discovered. | source read |
| F-9 | MED | E-01 pre-revision | Gating the route on `Kind: orchestrator` alone makes it a function that retires any orchestrator it is pointed at, with only caller discipline preventing a premature retirement. `action_for` returns `orchestrate` from `reviewed` onward, so the window exists before approval. The transition must require child 01's eligibility verdict itself. | `oc_runipd.py:2450-2463`; verified by calling `action_for` |

## Proposed changes (ordered, validatable)

1. E-01 add the rollup transition (shape (b), with its reason recorded), gated on `Kind: orchestrator` AND child 01's eligibility verdict.
2. E-02 enumerate and pin the FULL shared-gate set (lock, journal, recovery, index refresh included), with a reason for each deliberate omission.
3. E-03 resolve the receipt requirement without reusing the child path, stating the scope-delta consequence.
4. E-06 refuse the rollup in the worker role (not inherited from the CLI wrappers).
5. E-04 write the honest, lint-passing terminal entry.
6. E-05 tests, including the exemption-must-not-widen case.

## Deferred / out of scope (with reason)

- Deciding eligibility: child 01 owns the predicate; this plan consumes it.
- Wiring dispatch and removing the terminal-status write: child 03.
- The `aw set executed` worker-role bypass reopening `i452hf`: spec Section 4, separately filed.
- Retiring the four stuck orchestrators: a consequence, not the mechanism.

## Scope check

- Over-scope: none. `ipd_lint.py` was REMOVED from `Scope-Paths` when the maintainer resolved OQ-01 to shape (b); it is now explicitly out of bounds rather than conditionally in, so V-01 requires an empty diff for it as positive evidence that the rejected shape was not taken.
- Under-scope: nothing here is reachable from a real run until child 03 wires the dispatch sites.

## Required tests / validation

`python3 -m pytest` bare. Baseline measured in the executing worktree at execution time and pasted; compare failing NODE IDS, not totals (a lane worktree legitimately reports lane-environment failures: 35 measured on `xdr83v`'s lane).

## Spec / documentation sync

Implements spec `77tr3o` R-4, R-5, R-6. The `ipd-spec` documentation of the `pre-transition` checkpoint needs NO change, which is a direct consequence of the maintainer's shape-(b) ruling: the checkpoint's rule is untouched and exempts nothing, so there is no special case to document. The new rollup transition itself must be documented where the lifecycle verbs are described, stating plainly that it is runner-owned, orchestrator-only, and skips the E/V checkpoint because under `aw run` those items are performed by nobody.

## Open questions

### OQ-01: linter exemption (a) or a separate rollup transition (b)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED 2026-09-06 by the MAINTAINER, asked directly rather than deferred to execution: shape (b), a SEPARATE runner-owned rollup transition, and `ipd_lint.py` is out of bounds. His reasoning for rejecting (a): a safety check that learns one narrow exception is how it quietly stops protecting anything, because a later reader sees the exception and widens it. He accepted the known cost of (b) explicitly, that two transition paths can drift, which is why E-02 exists to make that drift detectable rather than latent. Recorded here in full because the rejected option and its reason are what a future reader needs; the decision is no longer the executor's to make.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a successful retirement of a synthetic complete Set showing NO `IPD-S404` findings. Paste `git diff --stat agent_workflows/ipd_lint.py` showing it is EMPTY, proving the rejected shape (a) was not taken. Paste the rollup route REFUSING a `Kind: child` plan, and separately paste a CHILD plan still being refused by the normal `finalize` with the same `IPD-S404` findings it produces today. Additionally paste the route REFUSING a `Kind: orchestrator` plan whose Set is INELIGIBLE per child 01's predicate, proving the transition gates on eligibility itself and not merely on Kind (a Kind-only route retires whatever it is pointed at, and `action_for` yields `orchestrate` as early as `reviewed`). All five are required: the first shows the gate opened where intended, the rest show it did not open anywhere else.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the drift test and its passing output, showing it enumerates the shared gates by name and that the enumeration INCLUDES the finalize lock, the transaction journal, the crash-recovery path, and the fail-loud index refresh, not just the five gates E-01 originally listed. For each gate the rollup deliberately does NOT share, paste the recorded reason. Then paste a SABOTAGE: remove one gate (e.g. the plans-index refresh) from the rollup path only, and show the test FAILS naming that gate. A drift test that only passes proves nothing about the drift it exists to catch.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a retirement succeeding with no pre-existing `begin` receipt. If a rollup receipt is minted, paste it and show it is distinguishable from an execution receipt; if none is minted, show `.aw/state/ipd-lifecycle/` contains no new file for the retired id6. Then address the scope-delta consequence directly: state whether the rollup performs a scope reconciliation, and if it does not, paste evidence that it changed NOTHING outside its own lifecycle `owned_paths` (the property that makes dropping the receipt-derived `base_head` safe). An answer that only shows the receipt refusal is gone does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the retired orchestrator's terminal history line, showing it names the rollup, the run id, and the justifying children, and does NOT claim its own E/V items were performed. Paste `aw ipd lint` output for the retired plan showing the attribution lint passes (this is where a parenthesized actor would fail).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the bare suite summary with the new tests passing. Then paste a SABOTAGE showing the exemption cannot widen: modify the exemption predicate to also accept `Kind: child` and show the "child still refused" test FAILS. A test that only passes proves nothing about the boundary it is supposed to defend.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the rollup invoked with the worker-role environment active, showing the `AW-LIFECYCLE-ROLE-001` refusal and that NO transition occurred: the plan is still in `pending/`, its `Status:` is unchanged, and no commit was created. Then paste a SABOTAGE: remove the role check and show the worker-role test FAILS. Note why a test is required rather than an assertion by inspection: the existing guard lives in the CLI wrappers (`ipd_lifecycle.py:2223`, `:2403`) and not in `finalize()`, so a new transition inherits NOTHING and only a test can show the guard is actually on this path.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Stay inside `Scope-Paths`; both runners' dispatch branches are OUT of bounds (child
03 owns them). Do not expand scope casually; if the work genuinely requires a file outside the fence,
make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`aw ipd finalize` refuses
without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path).

THIS PLAN DELIBERATELY OPENS A GATE, which makes it the most dangerous item in the Set and sets the bar
for its own evidence. You MUST NOT add any path by which an ordinary plan reaches `executed` without
evidence, and V-01/V-02/V-05/V-06 exist to prove you did not. Three specific ways this could go wrong,
all found in review and none hypothetical: (1) gating on `Kind` alone yields a function that retires any
orchestrator it is handed, so require child 01's eligibility verdict IN the transition; (2) the
worker-role refusal is NOT inherited, because it lives in the CLI wrappers (`ipd_lifecycle.py:2223`,
`:2403`) and not in `finalize()`, so a new function starts with no role guard at all; (3) `finalize`
performs at least nine gates, not the five originally listed, so a rollup built to the short list
silently lacks the exclusive lock, the transaction journal and crash recovery while running inside a live
runner in a shared checkout. Add the gate you are opening ONE place and prove the boundary everywhere
else.

Do not weaken the CHILD-plan gates, do not touch `EXECUTION_SUCCESS_STATES` or `TERMINAL_STATES`, and do
not incidentally "fix" the `aw set executed` worker-role bypass. `agent_workflows/ipd_lint.py` IS OUT OF
BOUNDS: OQ-01 is RESOLVED by the maintainer to shape (b), so do NOT teach the honesty checker any
exception, and do not "simplify" the separate transition into one. If you come to believe shape (a) is
better, STOP and raise it rather than substituting your judgement for the maintainer's; he rejected it
for a stated reason.

PASTE ACTUAL OUTPUT for every `V-*`, including every sabotage; a claim of success without pasted output
is a contract violation. Include the empty `ipd_lint.py` diff V-01 requires as positive evidence. Commit
path-scoped only (`git commit -m msg -- <path>`); never `git add -A`/bare/`-a`; never push; never tag or
release; and because others may be working in this checkout, verify `git diff --cached --name-only`
before each commit and unstage anything that is not yours. All open questions are resolved; no maintainer
decision is outstanding.

POST-GATE LIFECYCLE. Do not claim done or move this plan until every `V-*` is verified with concrete
pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed
by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.

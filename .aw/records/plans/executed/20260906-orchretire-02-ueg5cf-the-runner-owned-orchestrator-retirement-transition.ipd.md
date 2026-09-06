# IPD: the runner-owned orchestrator retirement transition

- Date: 2026-09-06
- Kind: child
- Concern: `finalize_orchestrator` (`oc_runipd.py:773-796`) has NEVER once succeeded. Measured across all 102 durable run records: `orchestrator-finalized` fired 0 times, `orchestrator-deferred` fired 28 times across 15 distinct orchestrators. It was born broken: the gated terminal transition landed `99760832` (2026-08-24) and `finalize_orchestrator` was written `801dd28a` (2026-08-27), three days later, against a gate that already refused it. Two gates block it and both are structural, not incidental. FIRST, it shells to `aw ipd set executed`, which requires a `begin` receipt; an orchestrator is never agent-executed so nothing ever calls `aw ipd begin` for it and no receipt can exist. SECOND, with a receipt present (verified by writing one, then deleting it) the `pre-transition` checkpoint refuses on six `IPD-S404` findings because `check_checkpoint` (`ipd_lint.py:694-725`) requires every `E-*` performed and every `V-*` evidenced UNCONDITIONALLY, and `grep -c orchestrator agent_workflows/ipd_lint.py` is 0 so the linter has no orchestrator concept at all. That is the contradiction: the honesty gate demands evidence for items that, under `aw run`, are by design performed by nobody.
- Scope: Make a runner-owned retirement transition that actually works, resolving spec `77tr3o` R-5 (the E/V pre-transition requirement) and R-6 (the receipt requirement) EXPLICITLY rather than by bypass, and writing an honest terminal history entry per R-4. THE R-5 SHAPE IS DECIDED, not left to the executor: the maintainer chose a SEPARATE runner-owned rollup transition and ruled `ipd_lint.py` out of bounds, so this plan adds a transition and does NOT teach the honesty checker any exception. Consumes child 01's predicate; it performs the transition and does NOT decide eligibility itself. It does NOT touch either runner's dispatch branch (child 03), does NOT relax any gate for CHILD plans, and adds NO path by which an ordinary plan can reach `executed` without evidence.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/runner_shared.py, tests/test_orchestrator_retirement.py
- Item-Dependencies: executed:5942n7
- Status: executed
- Readiness: go-pending-approval
- Set: orchretire
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ueg5cf
- From-Backlog: kxkc04
- From-Spec: 77tr3o

## Workflow history
- 2026-09-06 executed (aw oc run): aw oc run self-finalize: ueg5cf verified (set orchretire, attempt 1). [Scope reconciliation - in-scope-unmodified agent_workflows/runner_shared.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
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

- [x] E-01 Add the SEPARATE runner-owned rollup transition (spec R-5, shape (b), decided by the maintainer 2026-09-06). It MUST NOT route through the `pre-transition` E/V checkpoint, and it MUST still perform every other gate the main path performs (E-02 owns the FULL enumeration, which is longer than the list here: status legality, the plan move, the fail-loud plans-index refresh, the path-scoped lifecycle commit, post-transition lint, AND the finalize lock, transaction journal, and crash recovery). It MUST refuse for anything that is not `Kind: orchestrator`, so the route cannot be aimed at an ordinary plan at all.

  GATE ON ELIGIBILITY, NOT ONLY ON KIND. `Kind: orchestrator` alone is NOT sufficient authority to retire: the route MUST also require child 01's predicate to return eligible, in the transition itself rather than trusting its caller. Reason, and it is concrete: `action_for` returns `orchestrate` for a `reviewed` orchestrator, so a Kind-only route is a function that retires any orchestrator anyone points it at, and the ONLY thing standing between that and a false retirement is a caller remembering to ask. Defense in depth is cheap here and the failure it prevents is the one this Set must never cause.

  Add a comment naming spec `77tr3o` R-5 and OQ-1, stating that `ipd_lint.py` was deliberately left untouched and why, so a later reader does not "simplify" this into the linter exemption that was rejected.
  - Depends on: none
  - Expected outcome: retiring an eligible orchestrator produces none of the six `IPD-S404` findings; pointing the same route at a `Kind: child` plan is REFUSED regardless of that plan's state; and pointing it at a `Kind: orchestrator` plan whose Set is INELIGIBLE is also REFUSED.
  - Execution state: performed

- [x] E-02 Pin the accepted cost of shape (b): TWO PATHS CAN DRIFT. Write a test that asserts the rollup transition performs the same gate set as the main finalize MINUS the E/V checkpoint, enumerated explicitly rather than by inspection, so a future change that adds a gate to one path and not the other FAILS. The maintainer accepted drift as the known risk of this shape; this E-item is what makes that risk detectable instead of latent.

  THE ENUMERATION IN E-01 IS INCOMPLETE, and completing it is part of this item. `finalize` performs MORE than the five gates E-01 lists, each verified in `ipd_lifecycle.py`: (1) a non-empty `--actor` and `--message` refusal (`:1730-1737`); (2) the EXCLUSIVE finalize LOCK (`acquire_finalize_lock`, `:303`), released in a `finally:`; (3) the two-phase transaction JOURNAL with phases `prepared -> mutating -> ready-to-commit -> committed -> complete` (`:130-143`, `_finalize_transaction` `:1869`); (4) EARLY CRASH RECOVERY that resumes or rolls back a prior interrupted transaction BEFORE the fresh precheck (`:1744-1760`), including the idempotent pre-commit rollback (`_rollback_precommit`, `:1632`); (5) the status-legality check, which for `pre-transition` means "not already terminal" (`ipd_schema.checkpoint_allows_status`, `:1066-1068`); (6) the plan move, (7) the fail-loud plans-index refresh that re-runs `--check` and RAISES if it did not converge (`:1500-1516`), (8) the path-scoped lifecycle commit over exactly `owned_paths`, and (9) post-transition lint. Enumerate the ones the rollup MUST share, and for each one the rollup deliberately does NOT share, say so explicitly with a reason. A drift test built from E-01's five-item list would pass while the rollup silently lacked a lock, a journal, and any crash recovery.

  CONCURRENCY IS NOT OPTIONAL HERE. The rollup runs inside a live runner that may be executing other items, and this repo is a shared checkout, so a rollup that mutates the plans tree and the git index WITHOUT taking the same lock the main path takes can interleave with a child's own finalize. Take the same lock or state precisely why it is safe not to; do not leave it unstated.
  - Depends on: E-01
  - Expected outcome: a test that names each shared gate INCLUDING the lock, the journal, the recovery path and the fail-loud index refresh, fails if the rollup path stops performing one, and would have caught a gate added to `finalize` alone.
  - Execution state: performed

- [x] E-03 Resolve the receipt requirement (spec R-6) explicitly: either the rollup transition does not require a `begin` receipt, or the runner mints one as part of the rollup. Do NOT silently reuse the child-plan receipt path, which is what fails today. If a receipt is minted, it must be recognizable as a rollup receipt rather than an execution receipt, so it cannot be mistaken for evidence that an agent executed the orchestrator.

  NAME WHAT THE RECEIPT WAS CARRYING BEFORE YOU DROP IT. The receipt is not merely an authority token: `finalize_precheck` reads `base_head` FROM the receipt and refuses when it is missing or `unversioned` (`ipd_lifecycle.py:1355-1362`), because `base_head` is the baseline the whole SCOPE DELTA is computed against (`_changed_path_sources`, `:1170`), and it also reads the receipt's frozen `scope_paths` (`:1364`). So "the rollup does not require a receipt" necessarily also means "the rollup performs no scope reconciliation", and that consequence must be STATED and JUSTIFIED, not discovered later. The justification available to you is that a rollup makes no code edits at all, so its only changed paths are the lifecycle artifacts the transaction itself owns; if you rely on that, ASSERT it (the rollup must verify it changed nothing outside its own `owned_paths`) rather than merely assuming it.
  - Depends on: E-01
  - Expected outcome: the "no begin receipt for <id6>" refusal no longer blocks a legitimate rollup; no receipt is left behind claiming an execution that did not happen; and the scope-delta consequence of the chosen shape is stated explicitly, with the rollup asserting it touched nothing beyond its own lifecycle paths.
  - Execution state: performed

- [x] E-06 Refuse the rollup in the WORKER role, mirroring `run_begin`/`run_finalize`. The existing refusal is NOT inherited by construction: `worker_role_active` is checked in the CLI wrappers `run_begin` (`ipd_lifecycle.py:2223`) and `run_finalize` (`:2403`), NOT inside `finalize()` itself, and it is checked exactly twice in the module (verified). So a new transition function that does not call those wrappers has NO role guard at all, and a managed worker could create lifecycle authority through it. That is `wtiso-03` E-05's invariant and the same class of hole as the `aw set executed` bypass this plan is careful not to build on. Refuse FIRST, before any selector resolution, gate, or mutation, so a refused invocation has no side effect, and reuse `_refuse_worker_role_verb` rather than writing a second refusal message.
  - Depends on: E-01
  - Expected outcome: the rollup invoked with the worker-role environment set performs NO transition, commit, or plan move and returns the deterministic `AW-LIFECYCLE-ROLE-001` refusal; the coordinator-role path is unaffected.
  - Execution state: performed

### Task group 2: the honest record

- [x] E-04 Write the terminal history entry per spec R-4: it MUST record that the orchestrator was RETIRED as a rollup step of a runner Set completion, name the run id, and name the children whose execution justified it. It MUST NOT claim the orchestrator's own `E-*`/`V-*` items were performed. Note the existing message string (`"Orchestrator rollup: all children of set X executed (aw oc run, no agent turn)"`) has never actually been written to a plan, so there is no precedent to preserve and the wording is free; it must satisfy the attribution lint, which means keeping the actor string parenthesis-free (`driver_actor`'s documented constraint at `oc_runipd.py:799-810`; today's `--actor "aw oc run (orchestrator rollup)"` contains parentheses and would misparse).
  - Depends on: E-02, E-03
  - Expected outcome: a retired orchestrator's history line names the rollup, the run, and the children, and passes the attribution lint.
  - Execution state: performed

- [x] E-05 Extend `tests/test_orchestrator_retirement.py` (created by child 01) with transition-level tests: a complete Set retires and lands in `executed/` with the honest history line; a CHILD plan with unperformed E-items is still refused; a human `aw ipd finalize` on an orchestrator outside the rollup path still faces the E/V requirement; and the terminal entry passes the attribution lint. Include a test that the retirement refuses when child 01's predicate says ineligible, so the two halves cannot drift apart.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: tests that fail if the exemption widens to ordinary plans, which is the regression that matters most.
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: paste a successful retirement of a synthetic complete Set showing NO `IPD-S404` findings. Paste `git diff --stat agent_workflows/ipd_lint.py` showing it is EMPTY, proving the rejected shape (a) was not taken. Paste the rollup route REFUSING a `Kind: child` plan, and separately paste a CHILD plan still being refused by the normal `finalize` with the same `IPD-S404` findings it produces today. Additionally paste the route REFUSING a `Kind: orchestrator` plan whose Set is INELIGIBLE per child 01's predicate, proving the transition gates on eligibility itself and not merely on Kind (a Kind-only route retires whatever it is pointed at, and `action_for` yields `orchestrate` as early as `reviewed`). All five are required: the first shows the gate opened where intended, the rest show it did not open anywhere else.
  - Observed evidence: all five required elements, measured against throwaway git repos. The probe script is
    preserved at `.aw/state/lane-submissions/.../evidence/v01_probe.py` and its full output at
    `evidence/v01_output.txt`.

    (1/5) AN ELIGIBLE SET RETIRES, with NO `IPD-S404` findings:

    ```text
    exit_code = 0   (0 = EXIT_OK)
    commit    = 538915956555153fee7009824863a6411664d5f2
    message   = finalized orc000 -> executed at 538915956555 (actor aw oc run model=probe).
    findings  = ()
    IPD-S404 findings = []   <- MUST be []
    landed in executed/ = True   still in pending/ = False
    Status line = ['- Status: executed', ...]
    ```

    (2/5) THE ROLLUP ROUTE REFUSES A `Kind: child` PLAN, with the Set otherwise ELIGIBLE so nothing
    else can be what refused:

    ```text
    target Kind = ['- Kind: child']
    Set eligible? True  <- everything else IS valid
    exit_code = 1   (1 = EXIT_FINDINGS, refused)
    findings  = ('not-an-orchestrator',)
    message   = REFUSED: aaa111 is not an orchestrator (Kind='child', Order='1'). The rollup
                retirement exists ONLY for an Order-0 plan whose E-*/V-* items the runner supersedes;
                an ordinary plan must earn `executed` through `aw ipd finalize`, with its evidence.
    ```

    (3/5) A CHILD PLAN IS STILL REFUSED BY THE NORMAL `finalize`, with the same findings as today:

    ```text
    begin exit = 0 (begin receipt written for aaa111 at base 9e33bf32bca8)
    finalize exit_code = 1
    message = pre-transition gate did NOT conform (error); plan left unmoved.
      IPD-S404 E-01: not 'performed' at pre-transition
      IPD-S404 V-01: not 'pass' at pre-transition
      IPD-S404 V-01: empty Observed evidence at pre-transition
    child left unmoved = True
    ```

    (4/5) AN ORCHESTRATOR IS STILL REFUSED BY THE NORMAL `finalize`, i.e. the HUMAN-facing gate is
    unchanged. A receipt was minted first, so what refuses is the E/V CHECKPOINT and not the receipt
    gate, reproducing spec Section 2.3 exactly:

    ```text
    begin exit = 0  (a receipt EXISTS)
    finalize exit_code = 1
    message = pre-transition gate did NOT conform (error); plan left unmoved.
      IPD-S404 E-01: not 'performed' at pre-transition
      IPD-S404 V-01: not 'pass' at pre-transition
      IPD-S404 V-01: empty Observed evidence at pre-transition
    orchestrator left unmoved = True
    ```

    (5/5) AN ORCHESTRATOR WHOSE SET IS INELIGIBLE IS REFUSED, both refusal causes, proving the
    transition gates on ELIGIBILITY and not merely on Kind:

    ```text
    -- unfinished child
       target ['- Kind: orchestrator']  <- IS an orchestrator
       predicate: eligible=False reason='unfinished-children'
       exit_code = 1  findings = ('set-ineligible',)
       message   = REFUSED: Set 'inel' is not retirement-eligible (unfinished-children): Set 'inel'
                   has 1 child(ren) that are not 'executed': bbb222 (approved)
       orchestrator unmoved = True
    -- unauthored child row `03+`
       target ['- Kind: orchestrator']  <- IS an orchestrator
       predicate: eligible=False reason='unauthored-child-rows'
       exit_code = 1  findings = ('set-ineligible',)
       message   = REFUSED: Set 'inel' is not retirement-eligible (unauthored-child-rows): ... the
                   orchestrator's child table declares row(s) '03+' that resolve to no plan, so the
                   child set is not fully authored
       orchestrator unmoved = True
    ```

    THE REJECTED SHAPE (a) WAS NOT TAKEN. `agent_workflows/ipd_lint.py` is byte-unchanged:

    ```text
    $ git diff --stat agent_workflows/ipd_lint.py
    $ git diff HEAD --stat -- agent_workflows/ipd_lint.py
    (no output from either = EMPTY diff, staged and unstaged)
    $ grep -ci orchestrator agent_workflows/ipd_lint.py
    0
    ```

    The honesty checker therefore still has NO orchestrator concept, which is the whole point of the
    maintainer's OQ-1 ruling. `TheRejectedShapeWasNotTaken` pins all three facts as tests, so this
    cannot rot: the zero `orchestrator` count, the unconditional `pre-transition` E/V requirement
    applied directly to an orchestrator document, and `ipd_lint` staying out of this plan's
    `Scope-Paths`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the drift test and its passing output, showing it enumerates the shared gates by name and that the enumeration INCLUDES the finalize lock, the transaction journal, the crash-recovery path, and the fail-loud index refresh, not just the five gates E-01 originally listed. For each gate the rollup deliberately does NOT share, paste the recorded reason. Then paste a SABOTAGE: remove one gate (e.g. the plans-index refresh) from the rollup path only, and show the test FAILS naming that gate. A drift test that only passes proves nothing about the drift it exists to catch.
  - Observed evidence: THE ENUMERATION IS TEN GATES, not the five E-01 originally listed, and the four
    E-01 omitted (the lock, the journal, crash recovery, the fail-loud index refresh) are all present:

    ```text
    $ python3 -c "from agent_workflows import ipd_lifecycle as LC; print(LC.ROLLUP_SHARED_GATES)"
    ('worker-role-refusal', 'actor-and-message-required', 'early-crash-recovery',
     'exclusive-finalize-lock', 'transaction-journal', 'status-legality', 'plan-move',
     'plans-index-refresh-fail-loud', 'path-scoped-lifecycle-commit', 'post-transition-lint')
    ```

    The drift test class `GateParityBetweenTheTwoPaths` restates the required set INDEPENDENTLY in
    `_REQUIRED_SHARED` (with the `ipd_lifecycle` evidence for each), so the assertion compares two
    separately-authored lists rather than a list against itself, and
    `test_the_lock_journal_recovery_and_index_refresh_are_all_named` singles out precisely the four an
    abbreviated list omits:

    ```text
    $ python3 -m pytest tests/test_orchestrator_retirement.py -o addopts="" -q -k GateParity
    .......                                                                  [100%]
    7 passed, 78 deselected in 0.12s
    ```

    THE DELIBERATELY OMITTED GATES, each with its recorded reason (`ROLLUP_OMITTED_GATES`, printed in
    full in `evidence/v03_v04_output.txt`; abbreviated here):

    - `pre-transition-ev-checkpoint`: "THE ONE DELIBERATE DIFFERENCE, and the entire reason this
      transition exists ... Under `aw run` an orchestrator's items are performed by NOBODY ... so the
      requirement is unsatisfiable by construction rather than unsatisfied by neglect. Spec `77tr3o`
      R-5, resolved by the maintainer to shape (b) ... the E/V requirement is untouched for CHILD
      plans, which this route refuses outright."
    - `begin-receipt-requirement`: "An orchestrator has no `begin` receipt BY CONSTRUCTION ... The
      rollup does not require one and MINTS NONE, so no artifact is left behind claiming an execution
      that did not happen."
    - `scope-delta-reconciliation`: "A CONSEQUENCE of omitting the receipt, stated rather than
      discovered ... No receipt therefore means no scope reconciliation ... The rollup does not merely
      ASSUME that - `_assert_rollup_touched_only_owned_paths` VERIFIES it before committing."

    `test_the_only_omitted_gates_are_the_ev_checkpoint_and_its_consequences` asserts the omitted set
    is EXACTLY those three, so a fourth gate cannot quietly join them, and
    `test_every_omitted_gate_carries_a_REASON` refuses an empty or token justification.

    HOW THE DRIFT RISK IS ACTUALLY REDUCED, beyond naming. Every gate that CAN be shared as code IS
    (`_early_recovery_result`, `acquire_finalize_lock`/`release_finalize_lock`,
    `_finalize_transaction`, and through it `_refresh_plans_index_fail_loud`,
    `status_set.apply_status_change`, the path-scoped commit and `_complete_after_commit`), so those
    gates are not on the drift surface at all; `_early_recovery_result` was EXTRACTED from `finalize`
    in this change for exactly that reason. `test_the_gates_that_CAN_be_shared_as_code_ARE` pins the
    shared call sites and `test_the_rollup_does_NOT_reimplement_the_move_commit_or_index_refresh`
    refuses a private copy.

    SABOTAGE 2/5, THE ONE THIS ITEM DEMANDS, and deliberately a BEHAVIOR removal rather than a
    declaration edit: excise the EXCLUSIVE FINALIZE LOCK from `retire_orchestrator` only. Full log at
    `evidence/v02_sabotage2.txt`.

    ```text
    SABOTAGE applied: retire_orchestrator no longer acquires/releases the finalize lock

    --- the BEHAVIORAL test (a live lock must block the rollup) ---
        res = self.retire(orch, "locked", apply=True)
    >   self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN, res.message)
    E   AssertionError: 0 != 2 : finalized orc000 -> executed at a7b7e2f92801 (actor aw oc run model=test).
    FAILED TheSharedGatesActuallyFireOnTheRollupPath::test_a_LIVE_finalize_lock_blocks_the_rollup
    1 failed, 82 deselected in 0.30s

    --- the SOURCE-parity test ---
    E   AssertionError: False is not true : retire_orchestrator no longer calls acquire_finalize_lock;
        the rollup must REUSE that code, not re-implement it, or the two transition paths can drift
    FAILED GateParityBetweenTheTwoPaths::test_the_gates_that_CAN_be_shared_as_code_ARE
    1 failed, 82 deselected in 0.14s

    restored: md5 424b9e41eacc76e42bd6c2b13f05b371
    ```

    Note WHAT the sabotage revealed, which is the substance rather than the red test: the lockless
    rollup COMPLETED (`exit_code = 0`, a real commit), i.e. it genuinely would have run without the
    exclusive lock inside a live runner in this shared checkout. That is the latent failure E-02
    exists to make detectable.

    SABOTAGE 1/5, the plans-index refresh removed from the DECLARATION, showing the parity test names
    the specific gate (`evidence/v02_sabotage1.txt`):

    ```text
    SABOTAGE applied: plans-index-refresh-fail-loud removed from ROLLUP_SHARED_GATES
    E   AssertionError: Lists differ: ['plans-index-refresh-fail-loud'] != []
    E   + [] : the rollup path dropped a gate the main path performs:
        plans-index-refresh-fail-loud (_refresh_plans_index_fail_loud raises)
    FAILED GateParityBetweenTheTwoPaths::test_the_lock_journal_recovery_and_index_refresh_are_all_named
    FAILED GateParityBetweenTheTwoPaths::test_every_required_gate_is_declared_shared
    2 failed, 5 passed, 69 deselected in 0.20s
    ```

    BEYOND the declaration, each shared gate is also exercised at RUNTIME on the rollup path by
    `TheSharedGatesActuallyFireOnTheRollupPath`: a live lock blocks it; the journal progresses through
    all five phases and is cleared; an injected pre-commit fault ROLLS BACK (plan restored to
    `pending/`, HEAD unchanged); a stale pre-commit journal is recovered and a retry then succeeds; a
    failing index refresh fails the whole transaction with HEAD unchanged; post-transition lint still
    gates it (yielding `COMMITTED-INCOMPLETE`); and an empty actor is refused.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste a retirement succeeding with no pre-existing `begin` receipt. If a rollup receipt is minted, paste it and show it is distinguishable from an execution receipt; if none is minted, show `.aw/state/ipd-lifecycle/` contains no new file for the retired id6. Then address the scope-delta consequence directly: state whether the rollup performs a scope reconciliation, and if it does not, paste evidence that it changed NOTHING outside its own lifecycle `owned_paths` (the property that makes dropping the receipt-derived `base_head` safe). An answer that only shows the receipt refusal is gone does NOT satisfy this item.
  - Observed evidence: THE CHOSEN SHAPE, stated plainly first: the rollup DOES NOT REQUIRE a receipt and
    MINTS NONE. Minting one was rejected because any receipt for an orchestrator would be a durable
    artifact asserting a `pre-execution` gate an agent passed, which nobody did; a "rollup-flavored"
    receipt would still be one more object a future reader could mistake for execution evidence, and
    R-6's own words are that the receipt must not be mistakable. Full output at
    `evidence/v03_v04_output.txt`, probe preserved at `evidence/v03_v04_probe.py`.

    A RETIREMENT SUCCEEDS WITH NO RECEIPT, and leaves none:

    ```text
    receipt BEFORE = /tmp/.../.aw/state/ipd-lifecycle/orc000.receipt.json  exists=False
    exit_code = 0   message = finalized orc000 -> executed at d181ba8a5c1b (actor aw oc run model=probe).
    'no begin receipt' in message = False   <- MUST be False
    receipt AFTER exists = False   <- MUST be False: no false execution evidence
    contents of /tmp/.../.aw/state/ipd-lifecycle = <no receipt dir at all>
    ```

    The receipt DIRECTORY was never even created, which is the strongest form of "no new file for the
    retired id6". Pinned by `NoReceiptIsRequiredAndNoneIsLeftBehind`.

    THE SCOPE-DELTA CONSEQUENCE, addressed directly rather than left implicit. The rollup performs NO
    SCOPE RECONCILIATION. That is not an oversight but a NECESSARY consequence of dropping the
    receipt: `finalize_precheck` reads `base_head` FROM the receipt (`ipd_lifecycle.py:1355-1364`) and
    refuses a missing or `unversioned` value, and `base_head` is the baseline the entire delta is
    diffed against (`_changed_path_sources`), along with the receipt's frozen `scope_paths`. No
    receipt therefore means no baseline, hence no delta. This is recorded in code, not only here, as
    `ROLLUP_OMITTED_GATES['scope-delta-reconciliation']`, and
    `test_the_scope_delta_consequence_is_RECORDED_not_merely_true` asserts that record mentions
    `base_head` and "no scope reconciliation" so it cannot be silently dropped.

    WHAT MAKES THAT SAFE, VERIFIED RATHER THAN ASSUMED. A rollup makes no code edits, so its only
    changed paths are the lifecycle artifacts the transaction owns. The COMPLETE path set of a real
    rollup's lifecycle commit:

    ```text
      the lifecycle commit's COMPLETE path set (4 paths):
        .aw/records/plans/INDEX.json
        .aw/records/plans/INDEX.md
        .aw/records/plans/executed/20260906-owned-00-orc000-synthetic.ipd.md
        .aw/records/plans/pending/20260906-owned-00-orc000-synthetic.ipd.md
      every path is a lifecycle artifact this transaction owns: True
    ```

    That is exactly `owned_paths` (the plan's origin, its destination, and the two index files) and
    nothing else. `test_a_clean_rollup_changes_nothing_outside_its_owned_lifecycle_paths` asserts the
    set EXACTLY (`changed - expected == {INDEX.json, INDEX.md}`) rather than by a `.aw/records/plans/`
    prefix, so committing some other plans-tree file would fail.

    The one part of "a rollup edits nothing" that COULD be false is someone having uncommitted changes
    to the very plan the rollup rewrites, and with no `base_head` there is no delta to catch it. So
    `_assert_rollup_touched_only_owned_paths` CHECKS it and refuses:

    ```text
       exit_code = 1  findings = ('unowned-edit-to-plan',)
       message   = REFUSED: the orchestrator's own plan file ...20260906-dirty-00-orc000-synthetic.ipd.md
                   has UNCOMMITTED changes (M ...). A rollup makes no code edits, so it performs no
                   scope reconciliation (it has no begin receipt and therefore no base_head to diff
                   against); committing a dirty plan file would sweep someone else's in-flight edit
                   into a lifecycle commit and attribute it to the runner. Land or set that edit aside
                   and re-run.
       the co-worker's edit SURVIVED = True
       HEAD unchanged = True
    ```

    A CO-WORKER'S UNRELATED WORK IS LEFT ALONE, which is the other half of behaving correctly in a
    shared checkout: `test_the_lifecycle_commit_is_path_scoped_to_owned_paths_only` puts an untracked
    file beside the plan and asserts it is neither committed NOR staged (`?? someone_elses.py`
    afterwards), so the rollup cannot silently capture its provenance either.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the retired orchestrator's terminal history line, showing it names the rollup, the run id, and the justifying children, and does NOT claim its own E/V items were performed. Paste `aw ipd lint` output for the retired plan showing the attribution lint passes (this is where a parenthesized actor would fail).
  - Observed evidence: THE TERMINAL HISTORY LINE, verbatim from a real retirement (full output at
    `evidence/v03_v04_output.txt`):

    ```text
    - 2026-09-06 executed (aw oc run model=probe variant=v1): RETIRED as the orchestrator rollup step
      of a runner Set completion, not executed by an agent: every child of Set hist reached executed,
      so the runner (run run-20260906T162533Z-1552446) retired this Order-0 plan as bookkeeping. Its
      own E-*/V-* items were NOT performed; the runner superseded them by enforcing the ordering, the
      isolation and the per-child merge gate. Justifying children: aaa111, bbb222.
    ```

    (One physical line in the file; wrapped here for readability.) Every R-4 fact checked
    mechanically:

    ```text
      says RETIRED                                  = True
      says rollup                                   = True
      names the run id                              = True
      names child aaa111                            = True
      names child bbb222                            = True
      says its own items were NOT performed         = True
    ```

    IT DOES NOT CLAIM THE ITEMS WERE PERFORMED, and that is asserted in two ways rather than one. The
    line states positively that they were NOT performed, and the plan's own rows are untouched, so
    nothing was back-filled to manufacture evidence:

    ```text
      - [ ] E-01 TODO one observable action.
        - Execution state: pending
      - [ ] V-01 validates E-01
        - Result: pending
    ```

    THE ATTRIBUTION LINT PASSES on the retired plan:

    ```text
      disposition = conforming
      diagnostics = []
      IPD-S406 (attribution) findings = []   <- MUST be []
    ```

    F-4 REPRODUCED AND CLOSED. Today's actor string is `"aw oc run (orchestrator rollup)"`
    (`oc_runipd.py:785`), and `ipd_lint._HISTORY_ATTRIB_RE` captures the actor with `\(([^)]*)\)`, so
    a parenthesized actor misparses. Rather than merely avoiding the string, the transition REFUSES it
    BEFORE mutating anything, because the alternative failure mode is worse: the attribution check
    runs post-commit, so it would leave the transaction `committed-incomplete` for a human to resolve.

    ```text
      actor    = 'aw oc run (orchestrator rollup)'   (today's string, oc_runipd.py:785)
      exit_code = 2
      message   = actor 'aw oc run (orchestrator rollup)' contains a parenthesis. The terminal history
                  line is '- <date> <status> (<actor>): <msg>' and the attribution lint captures the
                  actor with '\(([^)]*)\)', so a parenthesized actor misparses and post-transition lint
                  would fail AFTER the commit. Render qualifiers as key=value (see
                  oc_runipd.driver_actor).
      plan unmoved = True   HEAD unchanged = True
    ```

    The accepted actor above (`aw oc run model=probe variant=v1`) is exactly the parenthesis-free
    `key=value` shape `driver_actor` already produces, so child 03 can wire the existing actor
    function without a second convention. `TheHonestTerminalRecord` pins all of it, including that a
    missing run id degrades honestly to "an unrecorded run" rather than fabricating one.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the bare suite summary with the new tests passing. Then paste a SABOTAGE showing the exemption cannot widen: modify the exemption predicate to also accept `Kind: child` and show the "child still refused" test FAILS. A test that only passes proves nothing about the boundary it is supposed to defend.
  - Observed evidence: BASELINE measured in THIS lane worktree at HEAD `b877b34b` BEFORE any edit, bare
    `python3 -m pytest`:

    ```text
    32 failed, 5386 passed, 3 skipped, 2 xfailed in 123.55s (0:02:03)
    ```

    AFTER this plan's changes, bare `python3 -m pytest`:

    ```text
    31 failed, 5431 passed, 3 skipped, 2 xfailed in 117.03s (0:01:57)
    ```

    Compared by failing NODE IDS, never totals, as this plan's Required tests section demands:

    ```text
    baseline=32  final=31
    --- NEW failures (final MINUS baseline) ---
    --- (empty above = ZERO regressions) ---
    --- disappeared (baseline MINUS final) ---
    tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130
    ```

    ZERO new failures. Passed rose 5386 -> 5431, i.e. +45, exactly the new tests. The 31 remaining are
    the pre-existing lane-environment artifacts (`test_run_viewer`, `test_oc_runipd` worktree cases,
    and so on) present in the baseline.

    THE ONE DISAPPEARED FAILURE IS FLAKY, not fixed by this plan, and I checked rather than assumed:

    ```text
      run 1: 1 passed in 0.57s
      run 2: 1 passed in 0.52s
      run 3: 1 passed in 0.53s
      run 4: 1 passed in 0.55s
      files this plan changed: agent_workflows/ipd_lifecycle.py, tests/test_orchestrator_retirement.py
      'runner_backlog_close' or 'sigint' appearing in this plan's diff: 0
    ```

    It is a SIGINT-timing test, it passes in isolation, and this plan's diff does not mention it or its
    subject. Recorded rather than claimed as an improvement.

    The new module alone:

    ```text
    $ python3 -m pytest tests/test_orchestrator_retirement.py -o addopts="" -q
    ........................................................................ [ 84%]
    .............                                                            [100%]
    85 passed in 2.89s
    ```

    THE SABOTAGE, and a correction to this item's own premise. The item asks for the "child still
    refused" test to fail when the exemption widens. It does, but measuring it revealed that the
    obvious version of that test is WEAKER than it looks, so a stronger one was added. With
    `is_orchestrator` widened to accept `Kind: child`, pointing the route at a child of the SAME Set is
    still refused for a DIFFERENT reason (`set-ineligible`), because an unexecuted child makes its own
    Set ineligible. That containment is real but ACCIDENTAL. The shape that actually works is to name
    an ELIGIBLE Set as `setid` while pointing `plan_path` at an approved, evidence-free child of a
    DIFFERENT Set, since `setid` and `plan_path` are separate inputs and nothing correlates them except
    the Kind gate. Measured directly:

    ```text
    SABOTAGE: Kind gate widened
    victim before: ['- Status: approved', '  - Execution state: pending', '  - Result: pending']
    exit_code = 0 | findings = ()
    message   = finalized vvv999 -> executed at a4e30f98c3d8 (actor aw oc run model=attacker).
    VICTIM REACHED executed/ WITHOUT EVIDENCE = True
      its Status: ['- Status: executed']
      its E-01 : ['  - Execution state: pending']
    ```

    So the widening is a REAL bypass, not a theoretical one: an ordinary plan reached `executed` with
    `Execution state: pending` intact. `test_a_child_of_ANOTHER_set_cannot_ride_an_eligible_sets_verdict`
    was written for exactly that shape and FAILS on the sabotage, alongside three others
    (`evidence/v05_sabotage3_widen_exemption.txt`):

    ```text
    SABOTAGE applied: `Kind: child` now ALSO accepted by the rollup route

    --- THE DECISIVE TEST: only the Kind gate stands in the way of this shape ---
        res = self.retire(victim, "clean", apply=True)
    >   self.assertEqual(res.exit_code, LC.EXIT_FINDINGS, res.message)
    E   AssertionError: 0 != 1 : finalized vvv999 -> executed at 784280542a7b (actor aw oc run model=test).
    FAILED TheGateDoesNotOpenForOrdinaryPlans::test_a_child_of_ANOTHER_set_cannot_ride_an_eligible_sets_verdict
    1 failed, 84 deselected in 0.31s

    --- the whole module: every widening-detector fires ---
    FAILED TheGateDoesNotOpenForOrdinaryPlans::test_a_child_plan_is_refused_by_the_rollup_route
    FAILED TheGateDoesNotOpenForOrdinaryPlans::test_an_APPROVED_PENDING_child_with_unperformed_items_is_refused
    FAILED TheGateDoesNotOpenForOrdinaryPlans::test_a_child_plan_in_an_ELIGIBLE_set_is_STILL_refused
    FAILED TheGateDoesNotOpenForOrdinaryPlans::test_a_child_of_ANOTHER_set_cannot_ride_an_eligible_sets_verdict
    4 failed, 81 passed in 3.26s

    restored: md5 424b9e41eacc76e42bd6c2b13f05b371
    ```

    A SECOND SABOTAGE covers the eligibility half (`evidence/v01_sabotage4_trust_caller_eligibility.txt`),
    since F-9's failure is a route that trusts its caller. Removing the in-transition eligibility gate
    (computing and recording the verdict but not acting on it) fails three tests:

    ```text
    SABOTAGE applied: the eligibility verdict is recorded but not enforced
    FAILED TheGateDoesNotOpenForOrdinaryPlans::test_a_supplied_ineligible_verdict_is_VALIDATED_not_trusted
    FAILED TheGateDoesNotOpenForOrdinaryPlans::test_an_orchestrator_whose_set_is_INELIGIBLE_is_refused
    FAILED TheGateDoesNotOpenForOrdinaryPlans::test_an_orchestrator_with_unauthored_child_rows_is_refused
    3 failed, 82 passed in 3.60s
    ```

    `TheHumanFacingGateIsUNCHANGED` additionally pins that the ordinary `aw ipd finalize` still refuses
    both an orchestrator and an unevidenced child (see V-01, items 3 and 4), so the boundary is
    asserted from both sides.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the rollup invoked with the worker-role environment active, showing the `AW-LIFECYCLE-ROLE-001` refusal and that NO transition occurred: the plan is still in `pending/`, its `Status:` is unchanged, and no commit was created. Then paste a SABOTAGE: remove the role check and show the worker-role test FAILS. Note why a test is required rather than an assertion by inspection: the existing guard lives in the CLI wrappers (`ipd_lifecycle.py:2223`, `:2403`) and not in `finalize()`, so a new transition inherits NOTHING and only a test can show the guard is actually on this path.
  - Observed evidence: THE ROLLUP INVOKED WITH THE WORKER-ROLE ENVIRONMENT ACTIVE, refused with no side
    effect at all (full log at `evidence/v06_sabotage5_remove_worker_role_guard.txt`):

    ```text
    WORKER-role exit_code = 2 (2 = EXIT_CANNOT_RUN) | findings = ('worker-role',)
    message = AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes; a worker-role
              process must not run them (refused: orchestrator rollup retirement). The runner performs
              this transition from the coordinator role; a worker-role process must not.
    plan still in pending/ = True
    HEAD unchanged = True
    worktree clean = ''
    ```

    All four required negatives hold: the plan is still in `pending/`, HEAD did not move (no commit),
    the worktree is byte-clean (so the `Status:` line was never rewritten), and the message carries the
    canonical `AW-LIFECYCLE-ROLE-001` token, reused from `LIFECYCLE_ROLE_ERROR` rather than reworded.

    THE GUARD REALLY WOULD HAVE BEEN MISSING, which is what makes this item substantive rather than
    ceremonial. F-6: `worker_role_active` is called in the CLI wrappers `run_begin`
    (`ipd_lifecycle.py:2223`) and `run_finalize` (`:2403`), NOT inside `finalize()`, and exactly twice
    in the module. A new transition function inherits NOTHING. With the guard removed, a worker-role
    process COMPLETES the transition:

    ```text
    guard REMOVED
    WORKER-role exit_code = 0 | commit = 8ab6d6619c0076f154cde17e099270bf8f8c9b63
    message = finalized orc000 -> executed at 8ab6d6619c00 (actor aw oc run model=worker).
    plan moved to executed/ BY A WORKER = True
    ```

    That is precisely the forked lifecycle authority `wtiso-03` E-05 exists to prevent, so the guard is
    load-bearing and an inspection-only claim would have been worthless.

    THE SABOTAGE, red tests:

    ```text
    SABOTAGE applied: retire_orchestrator no longer refuses the WORKER role
    >   self.assertIn(LC.ROLLUP_REFUSED_WORKER_ROLE, res.findings)
    E   AssertionError: 'worker-role' not found in ()
    FAILED TheWorkerRoleIsRefused::test_it_reuses_the_ONE_canonical_refusal_message
    FAILED TheWorkerRoleIsRefused::test_a_worker_role_rollup_performs_NO_transition
    FAILED TheWorkerRoleIsRefused::test_the_refusal_is_the_FIRST_gate_so_it_cannot_leak_through_another
    3 failed, 1 passed, 81 deselected in 0.44s

    restored: md5 424b9e41eacc76e42bd6c2b13f05b371
    ```

    IT IS THE FIRST GATE, asserted without pinning a line number:
    `test_the_refusal_is_the_FIRST_gate_so_it_cannot_leak_through_another` calls the rollup with a
    worker env AND an empty actor AND a non-orchestrator target, and requires the ROLE reason to win
    over the others. And `test_the_coordinator_role_is_UNAFFECTED` shows the guard does not break the
    path it protects (both an absent marking and `coordinator` proceed).

    ONE IMPLEMENTATION NOTE the plan asked about. E-06 says to reuse `_refuse_worker_role_verb`; that
    helper PRINTS to stderr and returns a bare `EXIT_CANNOT_RUN` int, which is the right shape for a
    CLI wrapper but not for a function whose contract is to return a `FinalizeResult` carrying typed
    findings. So the canonical MESSAGE constant `LIFECYCLE_ROLE_ERROR` is reused (the thing that could
    drift) while the return is a `FinalizeResult` with `findings=('worker-role',)`, matching this
    transition's typed-refusal vocabulary. `test_it_reuses_the_ONE_canonical_refusal_message` pins the
    reuse of both `LIFECYCLE_ROLE_ERROR` and `worker_role_active` so a second hand-written wording
    cannot appear. Recorded as DECISION 3-ueg5cf-D1.

    A TESTABILITY DETAIL worth stating, because it nearly produced a vacuous pass: `retire_orchestrator`
    takes an `env` parameter defaulting to `os.environ` (mirroring `worker_role_active`'s own pure
    design). This matters because the suite itself may run INSIDE a managed lane; this very plan was
    executed with `AW_EXECUTION_ROLE=worker` set, so a test reading `os.environ` implicitly would have
    refused for the wrong reason and every retirement test would have passed vacuously. The shared
    fixture therefore passes `env={}` explicitly and the worker tests pass the marking explicitly.
  - Result: pass

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

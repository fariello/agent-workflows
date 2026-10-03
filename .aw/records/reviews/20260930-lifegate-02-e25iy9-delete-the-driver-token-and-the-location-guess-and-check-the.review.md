# Review findings: plan e25iy9

- Subject-Id: e25iy9
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file in `pending/` was committed and byte-identical to the
lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author --agent`
reported `clean` (exit 0, zero findings) BEFORE semantic review, and reports `clean` again after revision.
The plan is `- Kind: child`, so the `IPD-S407` orchestrator child-row check does not apply.

THE PLAN'S ARCHITECTURE IS RIGHT AND ITS SIX AUTHORING FACTS ALL REPRODUCE. Fact 1: both `finalize` and
`retire_orchestrator` contain `if lane_worktree_active(repo_root):` followed by `verify_driver_attestation`,
returning `ROLLUP_REFUSED_NO_DRIVER_ATTESTATION`, and `lane_worktree_active` really does test a path under
`checkout_control_root(repo_root) / "worktrees"` or an `aw/lane/*` branch, which is the proxy P15 forbids.
Fact 2: `ipd_lifecycle.begin` really contains NO role or location check; the only one is
`_refuse_worker_role_verb("begin")` in `run_begin`. Fact 3: `finalize`'s own comment records that it is the
choke point for the CLI, the rollup, and `status_set._delegate_plan_executed_to_finalize`. Fact 4: both
hosts set `child_env[_gch.RUN_ID_ENV] = str(state["run_id"])` for isolated AND non-isolated turns, so the
transport exists and reaches the worker, exactly as claimed; E-05's environment fence is the right response
and is the single most important instruction in the plan. Fact 5: the token surface is as enumerated,
including `get_run_attestation` lazily MINTING for any existing run directory (F-7 is correct that it is a
writer disguised as a getter) and `_call_driver_finalize` inspecting the callee signature for the
`attestation` keyword. Fact 6: the four spec passages exist as quoted and `llbr2b` is still `to-review`,
so D8's in-place condition holds. The deletion is well scoped, the ordering argument for the worker label
running first is sound and correctly grounded in the one honest mistake actually observed, and the plan
correctly refuses to reuse `ROLLUP_REFUSED_NO_DRIVER_ATTESTATION` for a mechanism that no longer exists.

BUT THE PLAN WOULD HAVE STRANDED A SHIPPED FLAG, AND THE REPOSITORY ALREADY KNOWS WHY. That is PR-001.
`--no-self-finalize` is a shipped run option whose help text reads "the agent must move the plan itself",
and under it `runner_shared.execute_item_core` skips `driver_begin` and `driver_finalize` entirely (both
sit inside `if self_finalize and not is_review and not is_production:`). Worktree isolation is INDEPENDENT
of that flag: `isolation_for_action` reads `isolate_execute` / `isolate_worktree` and never consults
`self_finalize`, so the turn still gets a lane, and both hosts still set
`child_env[EXECUTION_ROLE_ENV] = ROLE_WORKER` whenever `work_dir` is truthy. So under
`--no-self-finalize` the lane agent is labelled a WORKER while being the only party that can transition the
plan. Today that half-works by accident: `finalize` already refuses it at the CLI handler and inside
`finalize`, but `begin` has NO core gate (fact 2), so E-02 would add a refusal to a path that currently
works and leave the plan beginnable by nobody.

This is not a hypothetical the review invented. `ipd_lifecycle.runner_owns_lifecycle_notice` is
DELIBERATELY conditional on `options.self_finalize` and its docstring states the exact failure mode: an
unconditional claim would tell "the one agent that MUST transition its own plan not to, leaving the plan in
`pending/` transitioned by nobody: strictly worse than the wasted turn this fixes". The plan advertises
that rule correctly and then enforces the unconditional version of it. New E-10 owns the fix and must run
BEFORE E-02, since it constrains what E-02 may do.

The fix shape matters and the plan must not take the easy one. Granting a worker the run-id exception when
`self_finalize` is false would contradict D2 twice ("the worker label runs FIRST" and "that agent never
receives a run id") and would void E-05's fence, because a worker would then legitimately carry a run id
and the fence could no longer be stated as an invariant. Narrowing the LABEL instead keeps D2 intact: the
label means "the driver owns your transition", which is false under `--no-self-finalize`, so not setting it
there makes the label HONEST rather than weaker. E-10 states both shapes, names (a) as strongly preferred,
and forbids the third option of exempting `begin` from the holder check, which would reopen the hole this
plan exists to close.

THREE DELETION-COMPLETENESS GAPS, each measured rather than inferred. PR-003: the plan names one test file
to delete and one to write, but THREE `fake_driver_finalize` doubles in two OTHER files declare
`attestation=None`. This is only a problem because E-06 also deletes `_call_driver_finalize`'s signature
probe, and that probe is precisely what tolerates a mismatched double today, so the two halves of one item
interact to produce a failure neither half predicts. PR-004: `ROLLUP_SHARED_GATES` cannot be updated alone,
because `tests/test_orchestrator_retirement.py` asserts `set(ROLLUP_OMITTED_GATES)` EXACTLY and its
`_REQUIRED_SHARED` table hard-codes the evidence string "run_begin/run_finalize check worker_role_active",
which E-02 makes stale by moving that check into the core functions. The plan correctly identified the
tuple as a drift detector (F-11) and then did not declare the test that reads it. PR-002: the plan says
reusing `retire_orchestrator`'s existing `run_id` means "no new parameter is needed there", which is true
but understates the cost, since that parameter is consumed by
`rollup_history_message(setid=..., run_id=..., children=...)` where its contract is provenance written into
the plan's permanent terminal history. Unifying two meanings is defensible here (the rollup's caller IS the
holder) but must be stated, or a later caller passing a provenance id that is not the holder grants itself
the exception as a side effect.

PR-005 is small but real: `aw ipd begin`'s own CLI description promises "Mutates no tracked file; the
receipt is never committed", and E-07 instructs the override to write a `## Workflow history` line, which
is a tracked edit. The plan should choose where that record lives rather than discovering the conflict in
execution. I also required the digest measurement rather than an assumption: `frozen_region_digest`
deliberately EXCLUDES `## Workflow history` (that exclusion is why a correct execution no longer goes
stale) while `plan_content_digest` covers the whole file, so which digest a history line moves is a
question with a measurable answer and no need for a guess.

WHAT I DID NOT FLAG, recorded so the next reviewer does not re-litigate it. The plan's `- Scope-Paths:`
declares `status_set.py` while saying an edit there may prove unnecessary; that is correct practice, not
over-scope, because the finalize reconciliation records a declared-but-unmodified path through
`--scope-ack`. The plan's refusal to declare `platform_lock.py` or `run_viewer.py` is also right: it
consumes Order 01's predicate and adds no liveness logic, so an edit to either genuinely means the
predicate was insufficient. Both existing open questions are addressed and non-blocking, and OQ-01's
reasoning is sound: the dangerous half (defaulting the exception from the environment) is fenced by E-05
regardless of which transport is chosen, so the transport is a real preference rather than a hidden risk.
I left both as the author wrote them. Separately, `tests/support.py` cites
`tests/test_worker_role_refusal.py`, which does not exist at this HEAD; that is pre-existing comment drift
in a file this plan does not touch, so it is noted here and not fixed.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A (correctness) / C (operability) / D (anti-regression) | `oc_runipd.py` `--no-self-finalize` help "the agent must move the plan itself"; `runner_shared.execute_item_core` `if self_finalize and not is_review and not is_production:` guarding `driver_begin`/`driver_finalize`; `runner_shared.isolation_for_action` reading only `isolate_*`; `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn` setting `child_env[EXECUTION_ROLE_ENV] = ROLE_WORKER` whenever `work_dir`; `ipd_lifecycle.runner_owns_lifecycle_notice` docstring "leaving the plan in `pending/` transitioned by nobody: strictly worse than the wasted turn this fixes" | **E-02 WOULD STRAND EVERY `--no-self-finalize` RUN, MAKING THE PLAN BEGINNABLE BY NOBODY.** Under that shipped flag the runner performs neither begin nor finalize, yet isolation is independent of it so the lane agent is still labelled `worker`. `finalize` already refuses that agent, but `begin` has no core gate today, so E-02 ADDS a refusal to the one path that still works for the one agent contractually obliged to transition its own plan. The repository already encodes this exact hazard as the reason `runner_owns_lifecycle_notice` is conditional; the plan quotes that mechanism approvingly and then enforces the unconditional form. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-10 (and V-10) added, depending only on E-01 so it precedes E-02, and E-02 is now constrained by it. E-10 states the measurement, requires one of exactly two shapes with shape (a) (do not label the turn `worker` when `self_finalize` is false) named strongly preferred, records that shape (b) contradicts D2's ordering and voids E-05's fence, and FORBIDS resolving it by exempting `begin` from the holder check. V-10 demands a driven `--no-self-finalize` turn that can begin and finalize, the DEFAULT-case control proving the label still refuses, and a mutation proving the V-item is not satisfiable by a no-op. New F-13 records it; E-06's expected outcome now admits the one documented host change. |
| PR-002 | MEDIUM | IN-SCOPE | A / F (honest documentation) | `ipd_lifecycle.retire_orchestrator`'s `run_id` parameter consumed by `rollup_history_message(setid=setid, run_id=run_id, children=justifying)`; `rollup_history_message` docstring "the RUN ID that retired it (so the durable run record can be found)" | **E-05'S "NO NEW PARAMETER IS NEEDED THERE" OVERLOADS ONE PARAMETER WITH TWO MEANINGS WITHOUT SAYING SO.** `retire_orchestrator`'s `run_id` is currently PROVENANCE, written into the plan's permanent terminal history. Making it also the holder exception is defensible because the rollup's only caller is the holding run, but unstated it becomes a latent hazard: a later caller passing a provenance id that is not the holder would grant itself the exception as a side effect of writing history. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now names the existing consumer and its contract, requires EITHER an explicit comment that the two meanings are deliberately unified with the reason they cannot diverge, OR a separately-named parameter, and forbids silent overloading. V-05 requires the choice stated and the comment or signature pasted. New F-14 records it. |
| PR-003 | MEDIUM | UNDER-SCOPE | D (anti-regression) / E (testing) | `tests/test_contention_wait.py` `def fake_driver_finalize(r, p, id6, actor, msg, attestation=None)`; `tests/test_finalize_sendback.py` same shape at two sites; `runner_shared._call_driver_finalize`'s `inspect.signature` probe for the `attestation` keyword | **THE DELETION LEAVES THREE STALE TEST DOUBLES IN TWO UNDECLARED FILES, AND E-06 REMOVES THE VERY MACHINERY THAT TOLERATES THEM.** The plan declares one test file for deletion and one for creation, but three `fake_driver_finalize` doubles elsewhere declare the deleted `attestation` keyword. The two halves of E-06 interact: removing the signature probe (correctly, as dead compatibility machinery) is exactly what makes a mismatched double fail, so the item as authored would break two suites it never names. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `tests/test_contention_wait.py` and `tests/test_finalize_sendback.py` added to `- Scope-Paths:`. E-06 now names all three sites, explains WHY the probe's deletion is what makes them fail, and requires each diff pasted. V-06 requires both files' passing output. New F-15 records it; the scope check states the reason each path was added. |
| PR-004 | MEDIUM | UNDER-SCOPE | D (anti-regression) | `tests/test_orchestrator_retirement.py::test_gate_parity_declarations_and_reasons` asserting `set(LC.ROLLUP_OMITTED_GATES) == {"pre-transition-ev-checkpoint", "begin-receipt-requirement", "scope-delta-reconciliation"}` exactly, and `_REQUIRED_SHARED["worker-role-refusal"] = "run_begin/run_finalize check worker_role_active"` | **E-04 UPDATES THE DRIFT DETECTOR WITHOUT UPDATING THE TEST THAT READS IT.** The plan correctly identifies `ROLLUP_SHARED_GATES` as a drift detector (F-11) but does not declare `tests/test_orchestrator_retirement.py`, which asserts the omitted-gate key set EXACTLY and hard-codes an evidence string that E-02 falsifies by moving the worker-label check into the core functions. Left alone, the detector would keep passing against a stale contract, which is precisely the silent drift F-11 exists to prevent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `tests/test_orchestrator_retirement.py` added to `- Scope-Paths:`. E-04 now requires the new holder refusal added to `ROLLUP_SHARED_GATES` AND to `_REQUIRED_SHARED`, the stale `worker-role-refusal` evidence string corrected, the exact omitted-set assertion respected, and the 120-character minimum on any touched reason preserved. V-04 requires the test diff and its passing output. New F-16 records it. |
| PR-005 | LOW | IN-SCOPE | A / F | `aw ipd begin` CLI description "Mutates no tracked file; the receipt is never committed"; `ipd_lifecycle.frozen_region_digest` docstring recording that `## Workflow history` is excluded because covering it "made the receipt go stale on every CORRECT execution" | **E-07 WRITES A TRACKED HISTORY LINE FROM A VERB THAT PROMISES IT MUTATES NO TRACKED FILE.** `begin`'s whole design is that it writes only a gitignored receipt. An override history line written from `begin` breaks that documented promise, and the plan does not say which of the two plan digests the write moves, so an executor could invalidate the begin receipt with the very override meant to unblock the work. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now requires choosing between recording the `begin` override in the gitignored receipt (preferred, with the durable record written at `finalize` where a tracked write is already normal) or correcting the now-false help text in the same change, and requires the MEASURED before/after of both `plan_content_digest` and `frozen_region_digest` rather than an assumption. V-07 demands the choice and the measurement. New F-17 records it. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-02 adds a core refusal to `begin`, which strands `--no-self-finalize`. What shape fixes it? | Add E-10 ahead of E-02, requiring the runner NOT to label the turn `worker` when `self_finalize` is false (shape (a) preferred), with shape (b) permitted only if reconciled with D2 explicitly. | (a) Grant a worker the run-id exception under the flag: REJECTED as the primary shape, it contradicts D2 twice (label first; the worker never receives a run id) and makes E-05's fence unstateable, since a worker would then legitimately carry a run id. (b) Exempt `begin` from the holder check: REJECTED, it reopens fact 2's hole this plan exists to close. (c) Deprecate or refuse `--no-self-finalize`: REJECTED as a scope change this plan has no mandate for; the flag is shipped and documented. (d) Leave it and let execution discover it: REJECTED, the stranded state is a plan transitionable by nobody, which is the failure `runner_owns_lifecycle_notice` already names as worse than the problem it fixes. | `runner_shared.execute_item_core`'s `if self_finalize ...` guard around both driver calls; `isolation_for_action` not reading `self_finalize`; both hosts' unconditional `ROLE_WORKER` on `work_dir`; `runner_owns_lifecycle_notice`'s docstring stating the transitioned-by-nobody failure; backlog `dvonrn` D2's ordering. | yes |
| D-2 | Is unifying `retire_orchestrator`'s provenance `run_id` with the holder exception acceptable? | Permitted, but it must be stated at the site with the reason the two cannot diverge; a separate parameter is equally acceptable. | Forbidding reuse outright: REJECTED, the values genuinely coincide (the rollup's only caller is the holding run) and a second parameter carrying the same value at every call site is duplication wearing a name. Leaving the plan's "no new parameter is needed" unqualified: REJECTED, it hides a semantic merge in a sentence about convenience, and the hazard (a provenance id that is not the holder) is invisible to a later reader. | `rollup_history_message`'s stated contract for `run_id` as the provenance written into permanent history; the rollup call site passing `state["run_id"]`, which is the holding run. | yes |
| D-3 | The three stale `fake_driver_finalize` doubles: widen scope, or let execution find them? | Widen `- Scope-Paths:` and name all three in E-06. | Letting the executor discover them: REJECTED, the scope fence is a declaration and an undeclared edit costs a `--scope-reason` round trip at finalize for something measurable now. Keeping the signature probe to tolerate them: REJECTED, the plan is right that it is dead compatibility machinery once the keyword is gone, and keeping it would preserve a parameter that no longer exists. | The three doubles' signatures; `_call_driver_finalize`'s probe existing only for that keyword; the plan's own E-06 instruction to delete the probe. | yes |
| D-4 | Should the two existing open questions (OQ-01 transport, OQ-02 UNDETERMINABLE refusing) be reopened, re-answered, or left? | Left exactly as authored, both non-blocking. | Reopening OQ-01: REJECTED, its reasoning is correct that the dangerous property (defaulting from the environment) is fenced by E-05 under either transport, so the choice is a genuine preference with no hidden risk. Reopening OQ-02: REJECTED, it implements a recorded maintainer ruling from D3 verbatim and the plan states the honest cost (UNDETERMINABLE can refuse when nothing is working) plus the recorded escape hatch; a reviewer substituting a preference for a maintainer ruling would be the error. | Backlog `dvonrn` D3 "Lock file unreadable ... REFUSE (maintainer ruling)"; E-05's fence being transport-independent; the 2026-09-10 ruling (plan `qhy3i3` OQ-01) that a non-blocking question does not force `no-go`. | yes |
| D-5 | Verdict and readiness, given one BLOCKER and four others all now fixed and no blocking open questions. | `APPROVE WITH REVISIONS APPLIED` / `go-pending-approval`. | `REJECT - NEEDS REPLAN`: REJECTED, the design is sound and PR-001 was repairable by adding one item and constraining another, which is bounded editing rather than rethinking; the Set's sequencing, the one-predicate design and the deletion scope all stand. `REVIEWED - OPEN QUESTIONS`: REJECTED, both OQs are non-blocking and deliberately left resolved-in-place by their authors. Bare `NO-GO`: REJECTED, the workflow reserves it for genuine not-ready conditions and a reviewed clean plan awaiting sign-off is `GO - PENDING HUMAN APPROVAL`. | Workflow readiness vocabulary; zero findings left OPEN or DEFERRED at or above the default `HIGH` gate threshold, so no escalation to a `Blocking: yes` question is owed; `aw ipd lint` clean at `author` and `review-finalize`. | yes |

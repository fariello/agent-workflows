# Spec: Lifecycle automation policy: one configurable per-(type, transition) permission surface

- Date: 2026-09-20
- Status: to-review
- Id: llbr2b
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- From-Backlog: rxya25
- Priority: high
- Work-Kind: feature
- Scope: One configurable, argument-overridable policy deciding how far automation may advance an artifact along the lifecycle, consulted by a single shared predicate. Specification only; authorizes no code change.
- Constrained-by: `.aw/records/specs/implemented/20260815-0151-01-honest-human-approval-attestation.spec.md`
  (`implemented`), which OWNS the human-attestation model, `attention_contract.SPEC_TRANSITIONS`,
  `attention_contract.TRANSITION_AUTHORITY` and the `APPROVAL_FLOOR`. This spec EXTENDS that table
  and does not redefine it; every statement below about who may perform a spec transition is a
  statement about that table's contents.
- Constrained-by: `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` and
  `.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md`, which own the PLAN lifecycle's own status
  vocabulary (`draft` -> `to-review` -> `reviewed` -> `approved`/`auto-approved` -> terminal). This
  spec adds no status and renames none.
- Constrained-by: `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`
  (`25kzda`, `approved`) Sections 2.5, 2.5a and 2.5b, which own the runner's selection gates
  (mixed-type, draft admission, orchestrator coverage). Those gates decide WHAT ENTERS A QUEUE; this
  spec decides WHETHER A TRANSITION MAY BE WRITTEN. Section 4.4 states why they are different
  questions and must not be merged.
- Constrained-by: `.aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md`
  (`approved`) R-4/R-5/R-6, which own orchestrator rollup retirement, INCLUDING its deliberate
  omission of the pre-transition `E-*`/`V-*` checkpoint. Section 3.6 brings that transition inside the
  policy's INVENTORY without weakening or re-deciding R-5.

## Workflow history
- 2026-09-20 to-review (aw set): Authored by plan u06zo2 from backlog rxya25. Inventories 6 automated lifecycle-advance surfaces at HEAD 2c316ef0 with citations plus the exhaustiveness searches; classifies 10 candidate conditions as POLICY or INVARIANT; answers all five of the item's design questions, THREE from attested maintainer rulings (OQ-01 default permissive 2026-09-08, OQ-02 both directions 2026-09-08, OQ-04 distinguishability 2026-09-10) and TWO from the plan's reviewed recommendation and explicitly marked UNATTESTED in section 5.6 (OQ-03 pair key, OQ-05 retirement scope). Specifies one predicate with a three-way verdict whose single-authority requirement covers the transition CALL as well as the decision, extends auto-approved and TRANSITION_AUTHORITY by name, and authorizes no code change. NOT approved: approving it is the act that attests the two open answers and is the maintainer's --by-human.

- 2026-09-20 created (aw specs): One configurable, argument-overridable policy deciding how far automation may advance an artifact along the lifecycle, consulted by a single shared predicate. Specification only; authorizes no code change.

## 0. What this spec authorizes, and what it does not

THIS SPEC AUTHORIZES NO CODE CHANGE. It is a design contract produced by plan `u06zo2` from backlog
item `rxya25`, and nothing in it licenses an implementation. A later executor reading this document
has no permission to build from it: implementation is a follow-on Set, graduated from this spec once a
human has approved it, and that Set's plans are where scope, sequencing and tests are decided.

The sentence above is load-bearing rather than ceremonial. Section 3 documents behavior that exists
today and Sections 4 through 7 describe behavior that does not, and the two are easy to conflate when
skimming. Every requirement in Sections 4 through 8 is a statement about what an implementation MUST
do WHEN it is built, not a claim that it does.

WHY THE SPEC CAME FIRST. The backlog item carries five design questions, and one of them (what the
default is) the item itself notes "would immediately break `--full-auto` unless it ships with a
permissive default for the transitions it already performs". A plan that implemented a policy engine
would have had to answer all five by fiat, which is exactly the hardcoding this item exists to end: it
would have added a sixth hardcoded opinion beside the five it is meant to consolidate.

## 1. The problem

How far automation may advance an artifact along the pipeline

    backlog -> backlog-review -> graduate to IPD -> to-review -> reviewed -> approved -> executed

is decided today by hardcoding, DIFFERENTLY in each verb, rather than by one configurable policy a
maintainer can set and an argument can override. The maintainer recorded that requirement on
2026-08-31 while resolving `97df1z` (fullauto-01) OQ-02, and filed it separately because it spans
every lifecycle verb.

The consequence is not that any single decision is wrong. Each site's decision is individually
defensible, and Section 3's inventory shows several of them are unusually careful. The consequence is
that there is no place to ASK the question, no place to CHANGE the answer, and no way to tell whether
two sites answering the same question answer it the same way. Section 3.8 records three measured
divergences of exactly that kind.

The maintainer's worked example, retained because it is the question the policy must be able to
answer: is it acceptable to advance an artifact carrying an unanswered OPEN QUESTION that the "try
harder before refusing" rule (`DECISIONS.md` D148) could not resolve into a strong recommendation?
Today that is hardcoded per verb, differently in each.

## 2. Terms

* TRANSITION. An ordered pair of statuses for one artifact type, written `<type>:<old>-><new>`, e.g.
  `ipd:reviewed->auto-approved`. A transition is the unit the policy is keyed on (Section 5.1).
* AUTOMATED ACTOR. A process performing a transition with no human in the loop for THAT transition: a
  driver, a hook, a checker, a scheduled job. An agent turn driven by a human's instruction is
  automated for this purpose, because the human authorized the TASK and not the individual write.
* ADVANCE. A transition toward a terminal state. FORWARD is the pipeline direction; REVERSAL moves
  backward (`approved -> to-review`); RETIREMENT ends an artifact's life without completing it
  (`superseded`, `not-executed`, `parked`, `deferred`); TERMINAL WRITE reaches a completion state
  (`executed`, `implemented`, `done`).
* POLICY-CLOSED. A transition a maintainer has chosen to forbid to automation. Loosenable by an
  override, which is RECORDED (Section 6.3).
* CONTRACT-CLOSED. A transition no policy setting and no override may open, because opening it would
  make a record assert something false. Section 6.4 enumerates these and they are a CLOSED set.
* INVARIANT (as opposed to POLICY). A condition that is never negotiable, so it is not on the policy
  surface at all (Section 4).

## 3. Inventory: what automation actually decides today

Every row was READ from the code at HEAD `2c316ef0`, and each cites the file and symbol it was read
from. THE INVENTORY IS INTENDED TO BE EXHAUSTIVE over automated lifecycle-status writes in this
package, and Section 3.9 states how that was checked and where the check's limits are.

EXHAUSTIVENESS IS A SAFETY PROPERTY HERE, NOT A DOCUMENTATION NICETY. Section 5.2 resolves the default
to PERMISSIVE, so an unlisted transition is a PERMITTED one. That inverts the usual cost of a missing
row: normally a missing row means a gate is not applied; here it means no gate exists.

### 3.1 The `--full-auto` clear, at TWO sites per host

| Fact | Value |
|---|---|
| Transition | `ipd:reviewed->auto-approved` |
| Read from | `runner_shared.initialize_run` (`runner_shared.py:13196-13202`) - the QUEUE-BUILD site; `runner_shared.execute_item` (`runner_shared.py:15235-15271`) - the POST-REVIEW site |
| Performed by | `oc_runipd.set_plan_approved` (`oc_runipd.py:875`) / `agy_runipd.set_plan_approved` (`agy_runipd.py:972`), each shelling out to `aw set auto-approved <id6> --actor <FULL_AUTO_ACTOR>` |
| Condition checked | `plan_readiness.is_plan_review_approved(plan_path)`, plus `options.full_auto` |
| On failure | Queue-build site: `except Exception: pass`, leaving the status `reviewed` (the item then needs input). Post-review site: prints `! Failed to auto-approve IPD <id6>` and proceeds |
| Automated actor may perform it | YES, and this is the ONLY transition `--full-auto` performs |

TWO SITES, NOT ONE, and the second does more than set a status: it also rewrites the queue item's
`action` to `execute` and its `status` to `queued` (`runner_shared.py:15243-15247`), which is what
converts a review turn into an execution turn within one run. A policy that governed only the status
write would leave that re-dispatch ungoverned.

WHAT IT DELIBERATELY DOES NOT DO, which is the honest-attestation precedent this spec extends: it does
NOT claim human `approved`. The target status is the sibling `auto-approved` tier, the actor is an
automated string, and the message reads "auto-approved by --full-auto: review readiness cleared (not
human approval)" (`oc_runipd.py:870-873`). `set_plan_approved`'s own docstring names backlog `rxya25`
and says its behavior is "hardcoded-but-honest until that lands" (`oc_runipd.py:892-896`). This spec
is that landing.

### 3.2 `aw ipd begin`: the pre-execution authority gate

| Fact | Value |
|---|---|
| Transition | Not a status change. It writes the EXECUTION-AUTHORITY receipt that `finalize` later consumes, so it gates `ipd:*->executed` one step removed |
| Read from | `ipd_lifecycle.begin` (`ipd_lifecycle.py:1220`); driver entry `runner_shared.driver_begin` (`runner_shared.py:11817`), wrapped per host at `oc_runipd.py:1036` and `agy_runipd.py:1053` |
| Conditions checked, in order | (1) non-empty `--actor`; (2) plan exists and carries a valid `- Id:` id6; (3) `pre-execution` lint disposition is `conforming`; (4) base HEAD is versioned and unambiguous; (5) requirements + `Scope-Paths` freeze; (6) baseline clean WITHIN the frozen `Scope-Paths` |
| On failure | REFUSE, writing no receipt ("fail-closed: no receipt = no execution authority"). The driver marks the item `blocked` (`runner_shared.py:14227-14232`) |
| Automated actor may perform it | YES. The driver calls it with `driver_actor(state)` (`runner_shared.py:14221`), e.g. `aw oc run model=<model>` |

NOTE the `isolated` parameter selects WHICH baseline condition (6) measures, and does not skip it
(`ipd_lifecycle.py:1244-1257`). A worker-role process is refused outright at the CLI wrapper
(`ipd_lifecycle.run_begin`), which Section 4.2 classifies as an invariant.

### 3.3 `aw ipd finalize`: the terminal transition

| Fact | Value |
|---|---|
| Transition | `ipd:<pre-terminal>->executed` |
| Read from | `ipd_lifecycle.finalize` (`ipd_lifecycle.py:3358`) and `ipd_lifecycle.finalize_precheck` (`:1885`); driver entry `oc_runipd.driver_finalize` (`oc_runipd.py:1346`), `agy_runipd.driver_finalize` (`agy_runipd.py:1081`) |
| Conditions checked | a matching begin receipt EXISTS; the receipt is CURRENT against the plan digest, with exactly one accepted mismatch class (an ADDITIVE `Scope-Paths` widening whose every other frozen category is byte-identical, `:1919-1963`); a usable `base_head`; `pre-transition` lint conforming (every `E-*` performed, every `V-*` evidenced); two-way scope reconciliation (out-of-scope changed paths need `--scope-reason`, declared-but-unmodified paths need `--scope-ack`, `:3437-3460`) |
| On failure | REFUSE, leaving the plan unmoved. The driver records the item NOT executed and preserves its lane (`runner_shared.py:15211-15230`) |
| Automated actor may perform it | YES. The driver computes the reconciliation programmatically and passes the same gated surface (`oc_runipd.py:1355-1378`) |

### 3.4 Automated backlog closing

| Fact | Value |
|---|---|
| Transition | `backlog:<open\|blocked\|graduated>->done` |
| Read from | `oc_runipd.process_backlog_close` (`oc_runipd.py:1861`), called from `runner_shared.execute_item` (`:15208`) and `runner_shared.py:4360-4367`; decided by `oc_runipd.evaluate_backlog_close` (`oc_runipd.py:1471`); the RELEASE-GATE half by `check_engine.evaluate_blocking_close` (`check_engine.py:2539`) |
| Conditions checked | the item resolves and is not already `done`; at least one artifact carries `From-Backlog: <id6>`; if any carrier is an IPD, EVERY IPD carrier is terminal `executed`; the run EARNED it (the deciding carrier is one this run produced, not one it found finished); and then the release-gate predicate's HANDOFF / SATISFIED / DE-GATED test |
| On failure | Records `backlog-item-left-open` WITH THE REASON and proceeds. Every lookup is wrapped to fail closed: "a missing item, an unreadable tree, or a raising helper yields `close=False` plus a recorded reason" (`oc_runipd.py:1484-1487`) |
| Automated actor may perform it | YES, via the GATED `aw backlog set <id6> --status done` spelling, chosen deliberately over the positional one, which "cannot even accept `--evidence`" (`oc_runipd.py:1718-1725`) |

### 3.5 The backlog release-gate close predicate

| Fact | Value |
|---|---|
| Transition | `backlog:*->done` (gated), `backlog:*->parked` (warned), `backlog:*->graduated` (explicitly legitimate), priority demotion of a blocker (warned) |
| Read from | `check_engine.evaluate_blocking_close` (`check_engine.py:2539`) |
| Condition checked | for `->done` on an item carrying `- Blocks-Release:`, one of HANDOFF (a `From-Backlog` plan or spec carrying the SAME `Blocks-Release`), SATISFIED (a resolvable `--evidence` citation), or DE-GATED (the post-mutation item carries no gate) |
| On failure | `->done`: REFUSE, severity `error`, naming the three fixes. `->parked` and a priority demotion: WARN and allow |
| Automated actor may perform it | YES, and this is the SHARED-PREDICATE PRECEDENT this spec's Section 7 requires the policy to copy: one predicate backs the setter, the `aw check` rules and the opt-in pre-commit hook, so they provably cannot diverge |

### 3.6 Orchestrator rollup retirement: an automated TERMINAL write with no agent turn

| Fact | Value |
|---|---|
| Transition | `ipd:<pre-terminal>->executed` on an Order-0 orchestrator |
| Read from | LIVE PATH: `runner_shared.dispatch_orchestrator_item` (`:9800`) -> `ipd_lifecycle.retire_orchestrator` (`ipd_lifecycle.py:3107`), decided by `runner_shared.evaluate_set_retirement` (`:8037`). Called from `oc_runipd.py:6758` and `agy_runipd.py:3520` |
| Conditions checked | `Kind: orchestrator` (a `Kind: child` plan is refused outright); the Set has an orchestrator on disk; the Set has >= 1 child; EVERY child's on-disk `Status:` is exactly `executed`; the child table parsed and declares no row resolving to nothing; then the 12 gates in `ipd_lifecycle.ROLLUP_SHARED_GATES` (`:2938`) |
| Deliberately OMITTED | the `pre-transition` `E-*`/`V-*` checkpoint, per `ROLLUP_OMITTED_GATES` (`:2989`) and spec `77tr3o` R-5, on the premise that an orchestrator's own items are performed by nobody |
| On failure | REFUSE. The dispatcher rewrites the outcome to TERMINATE with reason `finalize-refused` rather than RECONSIDER, because a structural refusal retried each iteration would spin (`runner_shared.py:9875-9886`) |
| Automated actor may perform it | YES, with NO agent turn and NO human, using `driver_actor(state)` |

THIS IS THE ITEM'S OWN CANDIDATE CONDITION HAPPENING TODAY. The item asks "whether an automated actor
may write a terminal state at all"; this transition is an automated actor writing a terminal state,
already, in production. It is the strongest single piece of evidence for Section 5.5's answer that
retirement and terminal writes are IN SCOPE for the policy.

NOTE A STALE SIBLING. `oc_runipd.finalize_orchestrator` (`oc_runipd.py:976`) is an `aw ipd set
executed` route with the actor `aw oc run step=orchestrator-rollup`. Its own docstring records that it
has ZERO callers (AST-verified) and is retained only because
`tests/test_lane_tool_identity.py:585-609` asserts it as a documented `oc`-only asymmetry. The policy
must govern it if it is ever wired up, so it is listed; it is not a live advance today. The plan that
produced this spec cited it as live (`oc_runipd.py:836-859`) and that citation is now stale in both
line number and liveness.

### 3.7 The spec status setter, on TWO forked surfaces

| Fact | Value |
|---|---|
| Transition | Every pair in `attention_contract.SPEC_TRANSITIONS` (`:437`), i.e. `spec:draft->to-review`, `->reviewed`, `->approved`, `->implementing`, `->implemented`, plus `deferred`/`parked`/`superseded` |
| Read from | TWO surfaces, reached by different CLI spellings: `specs.run_set` (`specs.py:498`) for `aw specs set <path> --status <enum>`, and `status_set.validate_transition_allowed` (`status_set.py:493`) for the positional `aw specs set <status> <selector>` |
| Conditions checked | transition legality against `SPEC_TRANSITIONS`; the `TRANSITION_AUTHORITY` requirement kinds for the target - `by_human` (`->approved`), `evidence` resolvable (`->implemented`), `review_record` (`->reviewed`); and for `->approved` the shared `plan_readiness.approval_refusals` predicate |
| On failure | REFUSE, exit 1, file unchanged |
| Automated actor may perform it | PARTIALLY, and this is the sharpest per-transition split in the inventory. `->to-review`, `->implementing`, `->deferred`, `->parked` and `->superseded` are open to an automated actor. `->approved` REFUSES without `--by-human`. `->implemented` REFUSES without a resolvable evidence citation. `->reviewed` REFUSES without a conforming review record |

WHY BOTH SURFACES ARE LISTED RATHER THAN ONE. They are a FORK, not a wrapper: the code at each site
says so explicitly, because "a gate installed in only one of them is bypassed by choosing the other
spelling" (`specs.py:563-568`, `status_set.py:541-547`). The mitigation already in place is that both
call the SAME shared predicates rather than carrying two copies of the logic. That is the pattern
Section 7.3 requires the policy to follow, and this row is the reason the requirement has to cover the
transition-performing call and not only the decision.

NOTE THIS SETTER IS ALSO WHERE THE `draft` -> `to-review` PROMOTION WOULD HAPPEN if the runner's draft
admission gate ever performed one; Section 4.4 records that it currently does not.

### 3.8 Three measured divergences the policy must not inherit

| # | Divergence | Evidence |
|---|---|---|
| D-1 | THE SHARED-PREDICATE PRECEDENT IS HALF-ADOPTED. The DECISION is shared (`plan_readiness.is_plan_review_approved`, one definition, with `agy_runipd.py:134-141` recording that a near-copy once meant "a fix to one driver left `aw agy run --full-auto` broken"), but the ACTION is DUPLICATED: `set_plan_approved` is defined twice, once per host, the agy copy's own docstring conceding it is "Kept byte-for-byte equivalent to the oc twin" by convention rather than by construction | `oc_runipd.py:875`; `agy_runipd.py:972`, `:980-982`, `:965-971` |
| D-2 | THERE ARE THREE `FULL_AUTO_ACTOR` CONSTANTS AND THE THIRD DISAGREES WITH BOTH OTHERS. `oc_runipd.py:869` is `"aw oc run --full-auto"`, `agy_runipd.py:966` is `"aw agy run --full-auto"`, and `runner_shared.py:13503` is `"aw-driver/full-auto"` with a DIFFERENT message ("Auto-approved via --full-auto (review passed all gates)", which also asserts more than the host copies do). The shared pair has no reader: both hosts import `runner_shared` but define their own, and the only two tests that assert an actor reaches the argv assert the HOST constants (`tests/test_oc_runipd.py:1428`, `tests/test_agy_runipd_cli.py:1121`) | grep for `FULL_AUTO_ACTOR` across `agent_workflows/` and `tests/` |
| D-3 | THE CONDITION VOCABULARY IS ALREADY SHARED FOR APPROVAL AND NOT FOR THE REST. `plan_readiness.approval_refusals` (`:496`) is genuinely THE one predicate for reaching a ready-to-execute status, consumed by both setter surfaces because "a gate installed in one of them is simply bypassed by choosing the other". No equivalent exists for `->executed`, `->done`, or a retirement | `plan_readiness.py:503-508`; `status_set.py:590`, `specs.py:588` |

D-2 IS REPORTED AS A DEFECT AND NOT FIXED HERE, because this spec changes no code. A third constant
that no code reads, whose value and message both differ from the two that are read, is a trap for
whoever next consolidates these hosts: adopting it would silently change every recorded actor string
and would make the message claim the review "passed all gates" rather than that readiness cleared.

### 3.9 How exhaustiveness was checked, and what the check does not cover

Three searches, each run at HEAD `2c316ef0`:

1. EVERY NESTED LIFECYCLE-SETTING CLI INVOCATION in the two drivers and the shared runner, by finding
   every `pinned_module_argv(` construction and every console-script fallback:
   `grep -rn 'pinned_module_argv(\|"aw",$' agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
   agent_workflows/runner_shared.py`. EIGHT sites, minus the two definitions of the helper itself:
   `oc_runipd.py:901` and `:933` (`aw set auto-approved`, 3.1), `:993` (`aw ipd set executed`, the
   callerless 3.6 sibling), `:1363` (`aw ipd finalize`, 3.3), `:1740` (`aw backlog set --status done`,
   3.4); `agy_runipd.py:984` and `:1013` (3.1), `:1096` (3.3); `runner_shared.py:11854` (`aw ipd
   begin`, 3.2). Every one is inventoried above.
2. EVERY AUTOMATED ACTOR STRING: `grep -rn "FULL_AUTO_ACTOR = \|def driver_actor\|step=orchestrator-rollup\|orchestrator rollup" agent_workflows/*.py`. It returned the three `FULL_AUTO_ACTOR`
   constants (D-2), the three `driver_actor` definitions (one shared at `runner_shared.py:12280`, one
   thin wrapper per host), the callerless rollup actor at `oc_runipd.py:1002`, and the rollup HISTORY
   MESSAGE builder at `ipd_lifecycle.py:3067`, which is the live path's attribution.
3. EVERY CALLER OF THE SINGLE STATUS-WRITE PRIMITIVE: `grep -rn "apply_status_change"
   agent_workflows/*.py`. Exactly one non-comment call outside `status_set` itself, at
   `ipd_lifecycle.py:3778`, inside the rollup retirement's coordinator worktree (3.6). Everything else
   reaches it through the CLI, which search 1 covers.

THREE LIMITS, STATED SO THE INVENTORY IS NOT TRUSTED FURTHER THAN IT HOLDS.

* IT COVERS THIS PACKAGE. A hook script, a CI job, or an agent running `aw set` from a workflow
  performs a transition this inventory does not name. Section 7.3's single-authority requirement is
  what makes those reach the policy anyway: they go through the CLI, and the CLI consults the
  predicate.
* IT IS A SNAPSHOT. A transition added after HEAD `2c316ef0` is not here. Section 5.2 requires the
  implementation to CARRY this inventory as data and Section 8's acceptance criterion 4 requires a
  test that fails when a new automated advance appears without a row, which is what converts a
  snapshot into a maintained invariant.
* IT NAMES STATUS WRITES, not every decision that leads to one. The runner's selection gates (spec
  `25kzda` 2.5/2.5a/2.5b) decide which items enter a queue, and Section 4.4 explains why those are a
  different question.

## 4. Condition vocabulary: which conditions are POLICY and which are INVARIANT

The backlog item lists six candidate conditions. Each is classified below as POLICY (a maintainer might
reasonably set it either way) or INVARIANT (never negotiable, therefore NOT on the policy surface).

GETTING THIS SPLIT RIGHT IS WHAT STOPS THE POLICY BECOMING A SWITCH THAT DISABLES A CORRECTNESS GATE.
A condition on the policy surface is, by construction, one a maintainer can turn off.

### 4.1 The classification

| # | Condition | Enforced today at | Class | Why |
|---|---|---|---|---|
| C-1 | Unresolved BLOCKING open question | `plan_readiness.has_unresolved_blocking_question` via `approval_refusals` (`plan_readiness.py:592-596`); `ipd_lint` checkpoint code `IPD-Q501` (`ipd_lint.py:76`) | POLICY | It is ALREADY overridable, by `--allow-open-questions`, and the override is already recorded in the artifact's actor string (`status_set.py:672-676`). A condition the shipped code lets a human wave is a policy condition by demonstration. This is also the maintainer's worked example, so it MUST be settable |
| C-2 | Unresolved NON-BLOCKING open question | Not a refusal anywhere; the maintainer ruled 2026-09-10 that it is not a not-ready condition | POLICY | Currently permissive everywhere. A maintainer might reasonably want a stricter posture for a release branch, which is precisely the CI tightening case of Section 6.2 |
| C-3 | An unfixed review finding at or above `review_findings_gate.block_at` | `check.review-finding-unescalated` (`check_engine.py:208`, `:3795`); `review_findings.subject_gating_blocks` via `approval_refusals` (`plan_readiness.py:517-527`); threshold from `config.findings_gate_threshold` (`config.py:1130`) | POLICY, with an invariant floor | The THRESHOLD is already configurable and already has a fail-closed default of `high` (`config.py:1103`), so the policy inherits a decided shape rather than inventing one. THE FLOOR: `approval_refusals` gives this refusal NO override at all today (`plan_readiness.py:527-532`), and the policy must not add one. So the threshold is policy; "a finding at or above the effective threshold refuses" is invariant |
| C-4 | A stale `aw ipd begin` receipt | `ipd_lifecycle.finalize_precheck` (`:1919-1963`) | INVARIANT | A stale receipt means the frozen contract the execution was authorized against is not the contract now written down, so the scope delta finalize computes is meaningless. This is not a risk appetite question; it is a correctness precondition for the computation. Note the ONE accepted mismatch class (an additive `Scope-Paths` widening with every other frozen category byte-identical) is already specified and is not an override |
| C-5 | Out-of-scope changed paths needing `--scope-reason` | `ipd_lifecycle.finalize` (`:3437-3460`), `_compute_scope_reconciliation` on the driver side (`oc_runipd.py:1355`) | INVARIANT that the DEMAND is made; POLICY whether an automated actor may ANSWER it | The demand for a reason is not negotiable: a silent out-of-scope edit is the thing the gate exists to surface. But TODAY the driver answers it programmatically and unattended, which is a real automation decision presently hardcoded. That half belongs on the policy surface |
| C-6 | A `Blocks-Release` gate on the artifact | `check_engine.evaluate_blocking_close` (`:2539`), three surfaces | INVARIANT for `->done`; POLICY for the warned transitions | The `->done` branch fails closed and offers three explicit fixes, one of which (`--blocks-release -`) already de-gates deliberately. An override that let automation close a gated item WITHOUT one of the three fixes would make the release-blocker set unreliable, which is the one property the field exists to provide. The `->parked` and priority-demotion branches already only WARN, and whether they should refuse is a genuine policy question |
| C-7 | Whether an automated actor may write a TERMINAL state at all | Nowhere as a single question; answered per site (3.3, 3.4, 3.6) | POLICY | This is the item's sharpest question and it is a policy one: automation writes terminal states today (3.6), a maintainer might reasonably forbid it, and both postures are coherent. Section 6.4 keeps the two transitions that must never be automated out of reach regardless |
| C-8 | The worker/coordinator ROLE of the process | `ipd_lifecycle.worker_role_active` in `run_begin`/`run_finalize` and in `retire_orchestrator` (`ipd_lifecycle.py:3180-3186`) | INVARIANT | A worker-role process must not create lifecycle authority. This is a containment property (spec `7ckptx`), not a lifecycle-advance judgement, and a policy that could relax it would let a lane grant itself authority its container denies |
| C-9 | The ACTOR being non-empty and parenthesis-free | `attention_contract.actor_refusal`, backstopped in `status_set.apply_status_change` (`:658-662`) | INVARIANT | An unattributed record is not a record. Nothing is gained by making this settable |
| C-10 | Nested tool identity | `assert_child_tool_identity` (`oc_runipd.py:725`), run-fatal | INVARIANT | If the tooling performing a transition is not the tooling that gated it, every gate in this document is void. Explicitly run-fatal today rather than item-local, and that is correct |

C-7 through C-10 are ADDITIONS to the item's six, found while reading the code. C-1 through C-6 are the
item's own list, each checked against the code rather than adopted wholesale.

### 4.2 The exclusion sentence

THE POLICY SURFACE CONSISTS OF THE CONDITIONS CLASSIFIED POLICY IN SECTION 4.1 AND NOTHING ELSE. An
INVARIANT is not a policy key, has no default, accepts no override, and MUST NOT be expressible in the
configuration file or on the command line; an implementation that admits one has widened the policy
beyond this spec and is nonconforming.

That is stated as a prohibition on the SURFACE rather than on the values, deliberately: a key whose
only legal value is "enforced" is still a key, and the next person to touch it will wonder why it
cannot be set to anything else and may add the missing value.

### 4.3 The invariant/policy split is not the same as the closed/open split

Section 6.4's CONTRACT-CLOSED transitions and Section 4.1's INVARIANT conditions are different axes and
must not be collapsed. An invariant is a CONDITION that is always checked; a contract-closed transition
is a TRANSITION automation may never perform. `ipd:*->approved` is contract-closed (no automated actor
may write human `approved`) while the conditions governing it are a mix of both classes.

### 4.4 What the policy does NOT govern: queue admission

Spec `25kzda` Sections 2.5, 2.5a and 2.5b own three gates that look adjacent and are not: the
mixed-type confirmation, the complete-draft admission (`--allow-drafts`, which promotes `draft` to
`to-review`), and the orchestrator coverage probe. They decide WHETHER AN ITEM ENTERS A QUEUE.

THE DRAFT ADMISSION GATE IS THE ONE THAT MOST LOOKS LIKE A COUNTEREXAMPLE, so it is named explicitly.
Its flag help says it promotes drafts "to 'to-review'" (`runner_shared.py:6068`), which reads like a
`draft->to-review` status write. It is not one: `enforce_draft_admission_gate` returns a FILTERED
`queue_ids` list and writes no status (`runner_shared.py:7434-7524`), and its verdict's `WAIVES` tuple
is exactly `("draft-admission",)` so it cannot become a general override seam
(`run_selection_policy.py:940-945`). If an implementation ever makes that promotion a real status
write, THAT write is a transition and this policy governs it; the admission decision itself is not.

The line is: `25kzda` decides what a run will ATTEMPT; this spec decides what a write may ASSERT.
Merging them would put a queue-shaping flag in reach of a lifecycle gate.

## 5. The five design questions, answered

Each answer names the open question it came from. NO ANSWER HERE IS THIS SPEC'S OWN AUTHORITY: two were
resolved by the maintainer on 2026-09-08 and are transcribed; one was resolved by the maintainer on
2026-09-10; two carry the plan's reviewed RECOMMENDATION and are flagged as unattested (Section 5.6).

### 5.1 Question 1: is the policy keyed per-TRANSITION, per-ARTIFACT-TYPE, or both?

FROM OQ-03 (status `open`, owner maintainer; the recommendation, not an attested ruling).

ANSWER: BOTH, keyed on the `(artifact-type, transition)` PAIR, written `<type>:<old>-><new>`.

REASONING, from OQ-03. The item's own argument is that "a backlog item graduating is not the same risk
as a plan finalizing", and the pair key is the only key shape that expresses it. The repository already
thinks in both axes: `attention_contract.TRANSITION_AUTHORITY` (`:486`) is keyed per TRANSITION while
`ipd_schema`, `backlog` and the spec setter carry separate per-TYPE vocabularies, so a single-axis
policy would have to flatten one of two axes that already exist.

THE COST IS COMBINATORIAL SURFACE, and it bites harder because of 5.2's permissive default: every
unlisted pair is PERMITTED, so a sparse table is a broad allowance.

WHAT AN UNLISTED KEY MEANS, stated explicitly because OQ-03 requires it not be left implicit: an
unlisted `(type, transition)` pair is PERMITTED to automation, subject to every invariant in Section
4.1 and to the contract-closed set in Section 6.4. It is not an error, and it is not refused.

### 5.2 Question 3: what is the default?

FROM OQ-01, RESOLVED BY THE MAINTAINER 2026-09-08 (recorded in commit `0f0eb2b4`, verified in review
as maintainer-authored). Transcribed, not re-decided.

ANSWER: A PERMISSIVE DEFAULT MATCHING TODAY'S BEHAVIOR, with fail-closed available PER TRANSITION.

THE POSTURE IS ALLOW-UNLESS-FORBIDDEN, AND THAT IS A DELIBERATE INVERSION OF THIS REPOSITORY'S POSTURE
EVERYWHERE ELSE, which is refuse-unless-allowed. The maintainer chose it over the reviewed
recommendation of fail-closed-plus-a-grandfather-list. It is recorded as deliberate here so that a
later reader does not read it as an oversight and "correct" it, breaking whatever automation has come
to rely on it by then.

WHY IT IS DEFENSIBLE, transcribed from OQ-01 so the choice is not recorded as arbitrary:

1. NOTHING CAN BREAK on the day the policy lands, which was the entire hazard the grandfather list
   existed to avoid. A list that must be maintained accurately is itself a failure mode.
2. THE SHIPPED AUTOMATION IS ALREADY CAREFUL IN THE WAY THAT MATTERS. `--full-auto` performs exactly
   one advance, `reviewed -> auto-approved`, and deliberately does not claim human `approved`. So the
   distinction the policy most needs to protect is already preserved by the one thing the default
   permits.
3. A PERMISSIVE DEFAULT IS NOT AN UNBOUNDED ONE. Fail-closed remains available per transition, so the
   transitions that must never be automated can each be closed individually and explicitly, which is
   arguably clearer than a blanket refusal plus an exception list.

THE COST DID NOT DISAPPEAR, IT MOVED, and a reviewer should weigh it: Section 6.5's fail-closed-from-
the-start list is the inverse of the grandfather list and carries the same maintenance burden.

RECONCILED AGAINST THE SHIPPED `--full-auto`, as OQ-01 and V-03 require. Measured in Section 3.1, the
transitions `--full-auto` performs today are: `ipd:reviewed->auto-approved` (at both the queue-build
and post-review sites), plus the queue re-dispatch to `action: execute` that accompanies the second.
Under this default all three remain permitted on the day the policy lands, so `--full-auto` is
unchanged by the policy's arrival. That is the whole purpose of the default, and it is the one
behavioral claim in this spec that an implementation must test directly (Section 8, criterion 2).

### 5.3 Question 2: may an argument override TIGHTEN, or only LOOSEN?

FROM OQ-02, RESOLVED BY THE MAINTAINER 2026-09-08 (same commit `0f0eb2b4`). Transcribed.

ANSWER: BOTH DIRECTIONS ARE ALLOWED, AND ONLY THE LOOSENING ONES ARE RECORDED.

WHY THE ASYMMETRY IS THE POINT. Because 5.2 resolved to a permissive default, TIGHTENING is the
direction that ADDS safety and LOOSENING is the direction that REMOVES it. The recording rule follows
the RISK rather than the mechanism: a tightening override needs no justification because being stricter
is never the hazardous choice, while a loosening override is written into the artifact so a relaxation
is auditable rather than silent.

THE CI CASE IS WHY BOTH DIRECTIONS ARE NEEDED, and it is concrete: a job may want to refuse ANY
automated advance while building a release, which is stricter than the repository policy. Without
tightening, that job would have to reimplement the check, and a second copy of the rule is exactly the
divergence Section 7's single-predicate requirement exists to prevent.

HOW A LOOSENING OVERRIDE IS RECORDED: by the existing mechanism, not a new one. `--allow-open-questions`
is folded into the recorded ACTOR string (`status_set.py:672-676`), so the override is visible in the
artifact's own history and is machine-greppable. A loosening policy override MUST be recorded the same
way. Note a run log would be the wrong home: `.aw/records/runs/` is gitignored and per-machine, so a
record there is not a record.

### 5.4 Question 4: must a policy-permitted automated advance always remain DISTINGUISHABLE?

FROM OQ-04, RESOLVED BY THE MAINTAINER 2026-09-10 via `/askme`. This is the maintainer's ruling, not
this spec's assertion.

ANSWER: YES. A machine's advance remains distinguishable from a human's in EVERY transition, and no
policy setting relaxes it. A loosening override does not reach this requirement.

THIS IS A CURRENTLY-ENFORCED REQUIREMENT AND NOT A CLAIM ABOUT THE FUTURE. The maintainer chose the
strongest option AND rejected absolutist framing: rules here are enforced until evidence shows they
need changing, and recording inflexibility in prose is counterproductive because a prior declaration of
inflexibility gets cited back and has to be policed. So this section states what is enforced and why,
and does not assert that the rule can never change. There is deliberately NO exception mechanism; that
option was offered and declined.

THREE MECHANISMS ALREADY IMPLEMENT IT, so the ruling records existing behavior:

1. `auto-approved` is a SEPARATE status from `approved`, a sibling in `READY_TO_EXECUTE`, documented as
   "an automated clear, NOT human approval" (`ipd_schema.py:265-267`).
2. The schema REFUSES the human `Approval:` field unless the status is exactly `approved`, and REQUIRES
   it when it is (`ipd_schema.py:400-411`).
3. Each host records an automated ACTOR string rather than `--by-human`: `FULL_AUTO_ACTOR` at
   `oc_runipd.py:869` and `agy_runipd.py:966`, and `driver_actor` at `runner_shared.py:12280` for the
   begin/finalize/rollup paths.

### 5.5 Question 5: does the policy govern retirement and reversal?

FROM OQ-05 (status `open`, owner maintainer; the recommendation, not an attested ruling).

ANSWER: YES, IN SCOPE, with the two halves distinguished because they differ in risk.

* RETIREMENT and TERMINAL WRITES (`superseded`, `not-executed`, `parked`, `deferred`, and `executed` /
  `implemented` / `done`) END an artifact's life. These are IN SCOPE and are the ones ALREADY HAPPENING
  automatically: Section 3.6 is an automated terminal write with no agent turn, and Section 3.4 is an
  automated `->done`. Leaving them outside the policy under a permissive default would mean they are
  governed by NOTHING, which is strictly worse than today, where each site at least refuses on its own
  terms.
* REVERSAL (`approved -> to-review`, `reviewed -> draft`, and their spec equivalents in
  `attention_contract.SPEC_TRANSITIONS`) moves an artifact BACKWARD. It is IN SCOPE but is generally
  SAFE, because it REMOVES rather than grants permission. The default for a reversal pair should be
  permissive, and the reason is worth stating: an automation that can undo its own premature advance is
  safer than one that cannot.

SPECIFYING RETIREMENT SEMANTICS IN FULL IS NOT DONE HERE. This section decides SCOPE. If the
implementing Set finds the retirement half needs detail beyond the policy key, that detail may warrant
its own spec section or its own spec.

### 5.6 Attestation status of these five answers

| Question | Source | Attested by the maintainer? |
|---|---|---|
| 3 (default) | OQ-01, commit `0f0eb2b4` | YES, 2026-09-08 |
| 2 (override direction) | OQ-02, commit `0f0eb2b4` | YES, 2026-09-08 |
| 4 (distinguishability) | OQ-04, `/askme` | YES, 2026-09-10 |
| 1 (key shape) | OQ-03, `open` | NO. This is the plan's reviewed recommendation |
| 5 (retirement/reversal scope) | OQ-05, `open` | NO. This is the plan's reviewed recommendation |

THIS TABLE IS WHY THE SPEC IS AT `to-review` AND NOT AT `approved`. Two of the five answers are
proposals. Approving this spec is the act that attests them, and it is the maintainer's
(`--by-human`); nothing in this document may be read as that attestation having happened.

## 6. The policy surface

### 6.1 Where the policy lives

`.aw/config/project.json`, following the `review_findings_gate` precedent EXACTLY (`config.py:1085-1147`)
rather than inventing a mechanism:

* A top-level key, read directly rather than through the XDG user config, which drops unknown keys.
* Deliberately NOT registered in `CONFIG_SCHEMA`: `project_schema.parse_portable_policy` preserves
  unknown keys in `unknown_fields` and writes them back on serialization, so the key round-trips
  safely. The `dependency_schema_cutover` marker is likewise absent from the schema.
* A reader that NEVER RAISES: a missing file, unparseable JSON, or a missing key yields the default.
* A value outside the vocabulary lands on the DEFAULT rather than being honored, so a typo cannot
  silently change the posture.

That last property inverts for this key relative to `review_findings_gate`, and the difference must be
deliberate: `review_findings_gate`'s default is fail-CLOSED at `high`, so a typo lands on the safe
side. This policy's default is PERMISSIVE (5.2), so a typo in a fail-closed entry would land on the
PERMISSIVE side, which is the unsafe direction. THEREFORE: a malformed entry for a `(type, transition)`
pair MUST be reported as a configuration error rather than silently defaulted. This is the one place
where the `review_findings_gate` precedent must be followed in shape and not in behavior, and the
reason is that the two keys' defaults point opposite ways.

### 6.2 The override

A loosening or tightening override arrives as a command-line argument on the verb performing the
transition. Both directions are legal (5.3). A TIGHTENING override is not recorded. A LOOSENING
override IS recorded, in the ACTOR string, by the `--allow-open-questions` mechanism
(`status_set.py:672-676`), and is recorded ONLY where it could have had an effect, so an
inconsequential flag does not litter history with a false claim (that restriction is already in the
shipped code and must be kept).

### 6.3 POLICY-closed versus CONTRACT-closed

This distinction is OQ-02's explicit requirement and did not exist in the question as authored. Under a
permissive default the per-transition closures are the only real protection, so if a loosening flag
could open them they would be decorative.

* A POLICY-CLOSED transition is closed by a maintainer's choice. A loosening override MAY open it, and
  the override is recorded.
* A CONTRACT-CLOSED transition is closed because opening it would make a record assert something
  false. NO policy setting and NO override opens it. An implementation MUST refuse the attempt rather
  than warn.

### 6.4 The contract-closed set

This is a CLOSED enumeration. Adding to it is an amendment to this spec.

| Transition | Why no override may open it |
|---|---|
| `ipd:reviewed->approved` (human `approved`) | `approved` REQUIRES the human `Approval:` field (`ipd_schema.py:400-405`) and `->approved` carries `by_human: True` in `TRANSITION_AUTHORITY`. An automated actor writing it asserts a human approved something no human approved. The honest automated route already exists and is `auto-approved` |
| `spec:reviewed->approved` | The anti-self-approval FLOOR. `aw specs set` refuses without `--by-human` on BOTH surfaces (`specs.py:525-540`, `status_set.py:523-540`), and the floor's own text says a plain set without it "stops and refuses" |
| `spec:implementing->implemented` | An agent may not set `implemented`; it requires a resolvable evidence citation (`specs.py:543-549`), and the repository instructions state the prohibition directly |

NOTE WHAT IS NOT IN THIS SET, because the omissions are deliberate and each is a judgement a reviewer
may dispute. `ipd:*->executed` is NOT contract-closed: automation performs it today through the gated
`finalize` (3.3) and through the rollup retirement (3.6), and both are attributed honestly. Neither is
`backlog:*->done` (3.4). Those are POLICY questions (C-7), so a maintainer may close them and a
recorded override may reopen them.

### 6.5 Fail-closed from the start

OQ-01's third explicit requirement: because an unlisted pair is PERMITTED, the policy must ship with an
EXPLICIT, NAMED list of transitions that are fail-closed from day one. Omission is the dangerous
direction.

The shipped default SHOULD close, at minimum, every pair in the contract-closed set of 6.4. Listing
them there AND closing them here is not redundant: 6.4 says no override opens them, 6.5 says the
default posture for them is closed, and an implementation that only did the former would ship a
permitted-by-default transition that merely could not be overridden further open.

BEYOND THAT MINIMUM, THE SET IS THE IMPLEMENTING SET'S TO PROPOSE AND THE MAINTAINER'S TO SETTLE,
against Section 3's inventory as the baseline. This spec does not enumerate it, because choosing which
of today's permitted automated advances to close is a risk-appetite decision, and 5.2's whole point is
that nothing breaks on the day the policy lands.

## 7. The single predicate

### 7.1 Signature

One predicate, consulted by every surface that performs a lifecycle transition.

INPUTS:

* `artifact_type` - the canonical type token (`ipd`, `spec`, `backlog`, ...), from
  `status_set.detect_artifact_type` / `run_selection_policy.SPEC_TYPE_BY_RESOLVER_TYPE`, never a new
  vocabulary.
* `current_status` and `target_status` - the transition, together forming the 5.1 pair key.
* `condition_state` - the artifact's own answers to the Section 4.1 POLICY conditions, supplied by the
  caller rather than read here, so the predicate stays pure and cheap (7.4).
* `resolved_policy` - the policy as read from configuration, resolved to a value for this pair.
* `override` - the loosening or tightening argument, or none.
* `actor` - the automated actor string that would be recorded, because a PERMIT-WITH-ATTESTATION
  verdict has to name what the attestation will say.

OUTPUT: exactly one of three verdicts.

* PERMIT - the transition may proceed with its ordinary attribution.
* REFUSE, WITH A REASON - and the reason must be specific enough to act on. A refusal that does not
  name its cause is the failure mode this whole area exists to remove, which is why
  `plan_readiness._blocking_question_ids` exists to quote the actual `OQ-NN` ids
  (`plan_readiness.py:602-618`). It must also say WHICH kind of closure refused: POLICY-closed (an
  override could open it, and which one) or CONTRACT-closed (nothing can).
* PERMIT-WITH-ATTESTATION - permitted, and the record MUST carry the automated provenance: the
  `auto-approved`-style sibling status where one exists, the automated actor string, and the loosening
  override folded into the actor when one was used. This verdict is how Section 5.4's
  distinguishability requirement is delivered mechanically rather than by the caller remembering.

### 7.2 It must never raise

Every shipped gate in this area fails in a chosen direction rather than by exception:
`approval_refusals` returns no refusals on an unreadable path because "a crashing gate is a disabled
gate, and one that refuses everything is worse than none" (`plan_readiness.py:533-536`);
`evaluate_backlog_close` wraps every lookup to fail closed (`oc_runipd.py:1484-1487`).

THE TWO DIRECTIONS ARE OPPOSITE, AND THAT IS NOT AN INCONSISTENCY TO TIDY: a gate whose absence
withholds nothing fails open, while a gate whose absence would let a release blocker close fails
closed. This predicate MUST NOT RAISE, and it MUST state per verdict path which direction it fails in
and why. An implementation that picks one direction globally will be wrong at one end.

### 7.3 Single authority: it covers the DECISION *and* the TRANSITION CALL

The precedent is `check_engine.evaluate_blocking_close` (`check_engine.py:2539`), which backs the
backlog setter, the `aw check` rules AND the opt-in pre-commit hook, so those three provably cannot
diverge.

THE REQUIREMENT COVERS BOTH HALVES, AND THIS IS THE ANSWER TO AN AMBIGUITY THAT WOULD OTHERWISE LICENSE
A MEASURED DRIFT. "Follow the shared-predicate pattern" is ambiguous about whether it means the PERMIT
DECISION only or also the TRANSITION-PERFORMING call, and Section 3.8's D-1 shows the repository is
currently half-adopted: the decision is shared, the action is duplicated per host, and D-2 shows that
duplication has ALREADY produced a third divergent constant nobody reads.

So: ONE definition of the permit decision, AND ONE definition of the call that performs a
policy-governed transition, including the actor string and message it records. A second copy of the
performer is a second copy of the attestation, and the attestation is what Section 5.4 requires to stay
honest.

### 7.4 Import discipline

The predicate must be STDLIB-CHEAP and DRIVER-AGNOSTIC: it must not import a runner. Both host drivers
will consume it, and `runner_shared`'s own module contract already states that shared code may not
import a runner and must take host-varying data as a PARAMETER (the `HostLabels` descriptor, and
`driver_begin`'s injected `env_builder`/`argv_builder`, are the shipped shape). `plan_readiness`
carries the same constraint, and the anti-divergence guard in `tests/test_runner_item_dependencies.py`
polices that class of coupling.

The practical consequence: `condition_state` is a PARAMETER (7.1) rather than something the predicate
reads, so the predicate is a deterministic function of its inputs and every branch is testable without
a TTY, a host, or a live run. `run_selection_policy` is the model here; its module docstring states
exactly this property.

## 8. Extending the shipped vocabularies

THE POLICY EXTENDS TWO EXISTING TABLES AND FORKS NEITHER.

### 8.1 `ipd_schema.READY_TO_EXECUTE` and the `auto-approved` tier

`auto-approved` is a SHIPPED sibling ready-to-execute tier (`ipd_schema.py:267`:
`READY_TO_EXECUTE: FrozenSet[str] = frozenset(("approved", "auto-approved"))`), documented at
`:265-266` as recording "an automated clear, NOT human approval", with `APPROVAL_STATUSES` at `:264`
holding `approved` alone so the human `Approval:` field cannot attach to the automated tier
(`:400-411`). `.aw/records/plans/README.md` records D65's rule that it is set only by an automated
checker, never by an executor fast-tracking its own work.

THE POLICY MUST NOT REDEFINE THIS. It is the MODEL for how a policy-permitted advance is recorded: a
distinct status token where the pipeline has one, so the distinction survives in the artifact rather
than only in a log. Where a pipeline stage has NO automated sibling token, the automated actor string
carries the distinction (Section 8.3).

### 8.2 `attention_contract.TRANSITION_AUTHORITY`

`TRANSITION_AUTHORITY` (`attention_contract.py:486`) is ALREADY a per-transition table of who may
perform which transition, introduced by the implemented spec
`20260815-0151-01-honest-human-approval-attestation.spec.md`. It carries `who`, `by_human`,
`human_token`, `evidence`, `review_record` and `requires_gate` per entry, and it is consumed by BOTH
spec-setting surfaces (`specs.py:524`, `status_set.py:523`).

THE POLICY EXTENDS THIS TABLE RATHER THAN ADDING A PARALLEL ONE. Two observations make that the right
move rather than a preference:

1. It is keyed on `->{status}` today, i.e. per TRANSITION with the type implied (specs). Section 5.1's
   pair key is a generalization of exactly this key, so the policy is the same table widened by one
   axis, not a new concept.
2. It already distinguishes REQUIREMENT KINDS (`by_human`, `evidence`, `review_record`), which is the
   same shape a policy needs for "what must be true for this actor to perform this transition".

A PARALLEL TABLE WOULD BE THE DIVERGENCE THIS SPEC EXISTS TO END. Two tables answering "who may perform
this transition" is D-1 and D-2 again, one layer up.

### 8.3 How a policy-permitted automated advance is recorded

Three mechanisms, all shipped, composed rather than replaced:

1. THE TARGET STATUS, where an automated sibling exists (`auto-approved`). Preferred, because it is
   visible to every reader of the artifact's front matter without parsing history.
2. THE ACTOR STRING in the workflow-history record, always. `FULL_AUTO_ACTOR` for a `--full-auto`
   clear; `driver_actor(state)` (e.g. `aw oc run model=<model>`) for begin, finalize and the rollup
   retirement. The actor is validated non-empty and parenthesis-free by
   `attention_contract.actor_refusal`, backstopped in `status_set.apply_status_change` (`:658-662`).
3. THE LOOSENING OVERRIDE, folded into that same actor string, following `--allow-open-questions`
   (`status_set.py:672-676`).

WHAT MUST NOT HAPPEN, as Section 5.4's ruling requires: no policy setting and no override may cause an
automated advance to be recorded in a way indistinguishable from a human's. Concretely, an automated
actor must not pass `--by-human`, must not write the `Approval:` field, and must not record a bare
human-looking actor string.

## 9. Acceptance criteria for the implementing Set

An implementation conforms when all of the following hold. These are criteria, not a plan: sequencing,
file layout and test placement belong to the implementing Set.

1. ONE PREDICATE exists with Section 7.1's inputs and three-way output, it never raises, it imports no
   runner, and every surface in Section 3's inventory consults it. No surface reimplements the
   decision, and no surface has a second copy of the transition-performing call (7.3).
2. `--full-auto`'s BEHAVIOR IS UNCHANGED by the policy's arrival under the default configuration,
   tested directly against the three transitions named in 5.2, on BOTH hosts. This is the criterion
   that makes the permissive default a measured claim rather than an intention.
3. The policy is keyed on the `(artifact-type, transition)` pair, an unlisted pair is permitted, and
   that is asserted by a test rather than left to the reader (5.1).
4. THE INVENTORY IS CARRIED AS DATA AND POLICED. A test fails when a new automated lifecycle advance
   is added without a corresponding row, in the shape `ipd_lifecycle.ROLLUP_SHARED_GATES` /
   `ROLLUP_OMITTED_GATES` already use: an explicit enumeration a test can compare against, not a set
   derived by inspection. Without this, Section 3 is a snapshot that rots (3.9).
5. Every INVARIANT in Section 4.1 is absent from the configuration surface and from the CLI (4.2).
6. Every CONTRACT-CLOSED transition in 6.4 refuses every override, and the refusal SAYS it is
   contract-closed rather than policy-closed (6.3).
7. A LOOSENING override is recorded in the artifact's actor string; a TIGHTENING override is not
   (5.3, 6.2).
8. An automated advance is distinguishable from a human's at every transition: no `--by-human` from an
   automated actor, no `Approval:` field outside status `approved`, and an automated actor string on
   every automated transition (5.4, 8.3).
9. A MALFORMED policy entry is reported as a configuration error rather than silently defaulted, and
   the divergence from `review_findings_gate`'s tolerant reader is documented at the reader (6.1).
10. `TRANSITION_AUTHORITY` is EXTENDED, not paralleled (8.2), and `auto-approved` is reused, not
    redefined (8.1).
11. THE MIGRATION SEQUENCING IS THE IMPLEMENTING SET'S DECISION, recorded with its reasoning:
    either every verb at once, or the `--full-auto` path first and the rest behind it. This spec
    deliberately does not choose, because the trade (blast radius versus a period of two live
    mechanisms) depends on how the work is actually staged.

## 10. Deliberately out of scope

* IMPLEMENTING THE POLICY ENGINE. See Section 0.
* CHANGING ANY VERB'S CURRENT BEHAVIOR, including `--full-auto`. Nothing regresses while the design is
  settled.
* FIXING THE THREE DIVERGENCES IN 3.8. They are REPORTED. D-2 in particular (a third, divergent
  `FULL_AUTO_ACTOR` with a different message, read by nothing) is a live trap and should be filed and
  fixed on its own, not folded into a policy rollout.
* THE `auto-approved` VOCABULARY ITSELF. Shipped and enforced; extended here, not redefined.
* SPECIFYING RETIREMENT SEMANTICS IN FULL. Section 5.5 decides scope only.
* THE CONFIG SCHEMA. `.aw/config/project.json` is `config_version 2`; this spec names where the policy
  lives and follows the unregistered-key precedent, and edits no schema.
* THE RUNNER'S QUEUE-ADMISSION GATES. Owned by spec `25kzda`; see 4.4 for why they are a different
  question.

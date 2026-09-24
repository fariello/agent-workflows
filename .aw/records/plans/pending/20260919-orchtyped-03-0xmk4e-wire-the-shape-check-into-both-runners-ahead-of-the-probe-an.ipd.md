# IPD: Wire the shape check into both runners ahead of the probe and report every finding before refusing

- Date: 2026-09-19
- Kind: child
- Concern: Review-time repair (child 02) is agent-performed and self-assessed, so it bounds and logs the repair without making it independent. Spec `r07vma` R8 puts a deterministic re-check in the run, which is what provides that independence: the run re-validates rather than trusting the review's verdict. It must also fix an operator-experience failure the maintainer named explicitly: a gate that reports one violation, gets fixed, then reports the next is the worst possible shape, so the run must collect EVERY finding across EVERY queued orchestrator and report them together before exiting.
  THE ORDERING IS LOAD-BEARING AND IS NOT AN OPTIMISATION. The shape check is free and deterministic; the probe spends a model call and has an availability failure mode (`could-not-ask` proceeds with a warning and a recorded hole). Running the shape check FIRST means the tidy violation costs nothing, and R9 plus criterion 11 require that a shape refusal spends zero model calls. Running the probe first would pay for a verdict on a plan the cheap check already refuses.
  THE PROBE MUST SURVIVE THIS CHANGE, and that is a governing-spec requirement rather than a preference. `25kzda` 2.5b (approved) states the coverage check is SEMANTIC, that "A syntactic rule MUST NOT be added in its place", and gives the measured reason: the dangerous violation is stated in PROSE and matches no checklist syntax. Spec `r07vma`'s own SR-001 records that its draft proposed retiring the probe and was wrong. Measured at HEAD `21eff5d8`: seven probe functions in `runner_shared` spanning 476 source lines (an AST span, re-verified at review; 442 non-blank), plus `tests/test_orchestrator_probe.py` at 1265 lines.
- Scope: The runner-side consumer of child 01's shared function, on BOTH hosts. IN: a pre-queue shape check over the queued orchestrators, sited so it runs before any agent turn, lane worktree or session; collecting all findings across all queued orchestrators and reporting them together before refusing (R8); ordering it AHEAD of the existing probe so a shape refusal spends no model call (R9, criteria 9 and 11); and making the two refusals distinguishable by rule id (criterion 10). OUT: the grammar and function (child 01); the review consumer (child 02); migrating any orchestrator (child 04); the merged proof (child 05); and any edit to the probe's seven functions or its test file, which criterion 9 pins as intact.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_orchestrator_shape_gate.py, tests/test_runner_refork_guard.py
- Item-Dependencies: executed:dpdyed
- Status: approved
- Readiness: go-pending-approval
- Set: orchtyped
- Order: 3
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 0xmk4e
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved
- From-Spec: r07vma
- Blocks-Release: next
- Work-Kind: bug
- Priority: high

## Workflow history
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-19 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-301..PR-306 all FIXED, none deferred, none open. Readiness go-pending-approval. Record: .aw/records/reviews/20260919-orchtyped-03-0xmk4e-wire-the-shape-check-into-both-runners-ahead-of-the-probe-an.review.md. SELF-REVIEW, so its value rests on EXECUTING claims: I read initialize_run_core's call order line by line, resolved every named symbol through both host modules, CONSTRUCTED the refork-guard row the plan asked for and ran its predicate, computed probe-cache digests across a simulated migration, and ran the three adjacent suites. WHAT HELD: every structural claim is accurate (probe gate called from initialize_run_core not run_queue; the three pre-queue gates raise before run_dir at 11853/11881/11907 vs 11917; the collect-then-partition batch shape is exactly as described; queued_orchestrator_targets scopes to the queue and skips an unreadable plan; F-4's one-sided-row and F-5's spawn-seam observations are quoted correctly). THREE HIGHS, each an instruction that cannot be followed as written. PR-304: E-01 required re-exporting the gate to both hosts and V-01 demanded oc.<sym> is agy.<sym>, but NO pre-queue gate is a host attribute (hasattr FALSE on both hosts for the probe gate, mixed-type gate, draft-admission gate and queued_orchestrator_targets), so that read raises AttributeError and the natural way to make it pass is to add the host symbol the same item forbids; the hosts share via CALLING initialize_run_core and the shipped identity pattern is getattr(module, name, getattr(module.runner_shared, name)) plus assertIs. PR-305: E-04's refork-guard row DIRECTLY CONTRADICTS E-01 - I constructed the Owned row and ran the identity half, which reports MISSING on both hosts for a runner_shared-only symbol with the remedy string 're-export <owner>.<symbol>', which is why the existing pre-queue gates carry no row; withdrawn and replaced with object identity plus a both-hosts BEHAVIOURAL refusal following BothHostsActuallyRefuse. PR-301: OQ-01 was framed as taste (invariant tidiness vs aw runs readability) while a DECIDING fact existed - --prepare-only takes an early return at 12103 BETWEEN run_dir creation and the probe, so a gate sited beside the probe is SILENTLY SKIPPED under the one flag an operator uses to check a queue before committing; the probe's own skip rests on a no-model-turn contract that does not transfer to a free check, and is ANNOUNCED precisely to prevent the false 'these orchestrators are cleared' reading; resolved to EARLY. Also PR-303 (E-05's evidence would have been VACUOUS: _assert_probe_spawn_is_permitted raises under pytest regardless of ordering and its docstring disclaims production-path semantics, so absence-of-spawn passes identically with the gate sited after the probe; now count invocations of an injected double via probe_orchestrator's counter, plus must-fail-first), PR-302 (ruled OUT a plausible worry: a cached probe PASS cannot survive the migration, since probe_cache_digest covers E-item action text and the rewrite moves it, verified with two digests; so add no invalidation) and PR-306 (baseline recorded plus the three adjacent suites at 142 passed). Nothing was weakened: the probe is untouched, and the E-04 replacement strengthens the coexistence proof by adding a behavioural both-hosts refusal. Validation: author and review-finalize lint conform; carrier CLEAN at pre-transition; the three adjacent suites 142 passed; bare suite 1 failed / 7305 passed with the single failure being the corpus-pinned reaskscore case proven pre-existing during child 01's review; aw check all reports 0 findings against this plan.

- 2026-09-19 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from approved spec `r07vma` as Order 03 of Set `orchtyped`. Measured at HEAD `21eff5d8`: `enforce_orchestrator_probe_gate` is called from `initialize_run_core` and already collects all outcomes then partitions them into `blocking` and `unavailable`, so R8's batch shape is the house pattern rather than a new one; `queued_orchestrator_targets` already enumerates the queue's orchestrators and already skips an unreadable plan rather than refusing. This child extends both rather than duplicating either.

## Goal

Make a run refuse a non-conforming orchestrator deterministically, before it spends anything, having reported every finding across every queued orchestrator in one pass; and leave the semantic probe running behind that check so the prose case is still caught.

READ THE SCOPE PRECISELY: this child adds a CONSUMER and a gate ordering. It adds no rule (child 01 owns that) and removes no control. If its diff touches the probe's seven functions or `tests/test_orchestrator_probe.py`, it has violated criterion 9 and the reviewer should refuse it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the gate, on both hosts, from one object

- [x] E-01 ADD THE PRE-QUEUE SHAPE GATE IN `runner_shared`, calling child 01's function over the queued orchestrators. Reuse `queued_orchestrator_targets` for the enumeration rather than writing a second queue walk: it already selects `kind == "orchestrator"` from `state["queue"]`, already resolves each plan path, and already SKIPS an unreadable plan rather than refusing (a plan the runner cannot read is a different refusal the existing preflight owns).
  DO NOT ADD A HOST RE-EXPORT, AND DO NOT EXPECT ONE: the plan's original "re-export it to both hosts so there is ONE object" was based on a false premise, corrected at review (PR-304). Measured: NO pre-queue gate is a host attribute. `hasattr(oc_runipd, "enforce_orchestrator_probe_gate")` is FALSE, and so is the agy side, and the same holds for `enforce_mixed_type_gate`, `enforce_draft_admission_gate` and `queued_orchestrator_targets`. Both hosts reach these by CALLING `runner_shared.initialize_run_core` (`oc_runipd.py:3360`, `agy_runipd.py:2137`), which is the seam that makes them shared; adding a re-export would be a NEW host-surface symbol this Set does not need and would contradict the plan's own no-new-host-symbol rule.
  THE SHIPPED IDENTITY PATTERN IS A `getattr` FALLBACK THROUGH `module.runner_shared`, not a direct attribute. `tests/test_orchestrator_probe.py::BothHostsShareOneDefinition` resolves each symbol as `getattr(module, name, getattr(module.runner_shared, name))` and asserts `assertIs` against the `runner_shared` object; verified at review that this returns True for both hosts on `enforce_orchestrator_probe_gate` while a direct `hasattr` is False. Follow that pattern.
  NO SYMBOL MAY BE ADDED TO `oc_runipd` FOR AGY TO IMPORT. `agy_runipd` already imports dozens of names from `oc_runipd` and zero flow the other way; a shared symbol goes in `runner_shared`. E-04 pins this with the refork guard.
  - Depends on: none
  - Expected outcome: one gate function in `runner_shared`, reached by both hosts through `initialize_run_core`; each host resolves it to the SAME object under the shipped `getattr(module, name, getattr(module.runner_shared, name))` pattern; NO new host attribute is added; and the oc-to-agy import count is not increased.
  - Execution state: performed

- [x] E-02 SITE IT BEFORE ANY AGENT TURN, LANE WORKTREE, OR SESSION, and ORDER IT AHEAD OF THE PROBE. `enforce_orchestrator_probe_gate` is called from `initialize_run_core` after the run directory exists, and that siting is a PRICED EXCEPTION recorded in its own docstring: the probe needs somewhere durable to log its model call and its refusal must be readable in `aw runs`. The shape check has NO such need, because it spends nothing and produces no model call to log.
  SITE IT EARLY, WITH THE THREE PRE-QUEUE GATES. OQ-01 IS RESOLVED AT REVIEW AND IS NO LONGER YOURS TO CHOOSE (PR-301); read its rationale before writing code. Place it beside `enforce_draft_admission_gate`, `enforce_dependency_preflight` and `enforce_mixed_type_gate`, all of which raise BEFORE `run_dir` is created, and record the reason in a code comment.
  THE REASON IS `--prepare-only`, NOT INVARIANT TIDINESS, which is what makes this a decision rather than a preference. Measured at review, `initialize_run_core` runs the three pre-queue gates (`:11853`, `:11881`, `:11907`), creates `run_dir` (`:11917`), then takes an EARLY RETURN for `--prepare-only` (`:12103`), and only then calls the probe (`:12122`). A gate sited "beside the probe" is therefore DOWNSTREAM of that early return and is SKIPPED under `--prepare-only`. The probe's own skip there is correct for a reason that does NOT transfer, stated in its comment: the flag's contract is to build and display the queue "WITHOUT launching OpenCode", so spending a model turn would break it. The shape check spends no model turn, so skipping it buys nothing and denies the operator the one thing `--prepare-only` exists for, namely learning the queue is not runnable BEFORE committing to a run. Note also that the probe's skip is deliberately ANNOUNCED so "an operator inspecting a queue must not conclude the orchestrators in it were cleared"; a silently skipped shape check would create that same false impression with nothing announcing it.
  THE ACCEPTED COST, stated rather than discovered: an early refusal is read from the process output, NOT from `aw runs`, because no run directory exists yet. Criterion 11 is then trivially evidenced, since there is no run to probe. Do NOT move the gate behind the early return to gain durable readability; if that is wanted later, keep the check early and ALSO record it.
  - Depends on: E-01
  - Expected outcome: a non-conforming orchestrator refuses the run with no agent turn, no lane worktree, no session AND no run directory; the siting is justified in a comment naming both the no-durable-write invariant and the `--prepare-only` reason; and `aw oc run --prepare-only` over a non-conforming queue REFUSES rather than printing a queue.
  - Execution state: performed

### Task group 2: the report, the coexistence, and the pins

- [x] E-03 COLLECT EVERY FINDING ACROSS EVERY QUEUED ORCHESTRATOR AND REPORT THEM TOGETHER BEFORE REFUSING (R8). Follow the existing structure rather than inventing one: `enforce_orchestrator_probe_gate` already loops its targets, appends to `outcomes`, then partitions into `blocking` and `unavailable`. Generalise that shape across CHECK KINDS so a run can report shape findings and probe findings in one place, and do not stop at the first violation.
  THE MAINTAINER'S STATED REQUIREMENT, quoted because it is the acceptance bar: a cycle of "fix this, retry, now that is wrong, retry" is the worst possible operator experience, so a run must complete all checks and report on all of them before exiting.
  - Depends on: E-01
  - Expected outcome: a queue with three non-conforming orchestrators reports all three, with all their per-row findings, then exits once.
  - Execution state: performed

- [x] E-04 PIN THAT THE PROBE STILL RUNS AND THAT THE TWO REFUSALS ARE TELLABLE APART (criteria 9 and 10). Add a test that an orchestrator whose ROWS all conform but which carries an obligation in a BARE INDENTED continuation line is STILL refused, by the probe, after this change. PROVE THIS WITH A BARE INDENTED CONTINUATION LINE AND NOT WITH `## Completion criteria` (corrected at review, PR-005): that SECTION IS NOT IN THE PROBE'S PAYLOAD AT ALL. Verified in-process at review by calling `runner_shared.orchestrator_probe_excerpt` on a fixture whose `## Completion criteria` said "SOMEONE MUST MIGRATE THE DATABASE BEFORE ANY CHILD RUNS": the rendered excerpt contains only the checklist item action text and the child-table row cells, and the string is absent. `probe_cache_payload` returns exactly the two keys `e_items` and `child_table_rows`, so no prose section outside a checklist item ever reaches the model (pre-existing limit, tracked as backlog `rmcqw8`, pinned by `tests/test_orchestrator_probe.py::TheExcerptHasAKnownLIMIT`). A `- Key: value` continuation line is ALSO invisible, because `e_item_action_blocks` stops at the first line matching `ipd_lint._SUBFIELD_RE`. So the ONLY shape that demonstrates criterion 9 is a BARE indented continuation line under a conforming row; anything else reports a pass the mechanism did not earn, and this item FAILS if the evidence uses one. Add a test that the shape refusal and the probe refusal name DIFFERENT rule ids, so an operator reading a refused run knows which control fired and therefore which remedy applies.
  ALSO ASSERT THE PROBE IS UNTOUCHED: `tests/test_orchestrator_probe.py` byte-unchanged in this child's diff, and the seven probe functions present.
  DO NOT ADD A REFORK-GUARD ROW FOR THE GATE, AND UNDERSTAND WHY, because the plan originally required one and that requirement CONTRADICTS E-01 (PR-305). The guard's identity half (`test_every_runner_attribute_is_the_owning_modules_object`) resolves `getattr(_MODULES[runner], row.local)` and records a violation when it is MISSING, with the remedy "re-export `<owner>.<symbol>`". Verified at review by constructing the row in-process: for a `runner_shared`-only gate it reports MISSING on BOTH hosts, so the row FAILS unless a host re-export is added, which is exactly the new host-surface symbol E-01 forbids. The existing pre-queue gates carry no refork row for the same reason. So the refork guard is the WRONG pin for this symbol, and `tests/test_runner_refork_guard.py` is consequently expected to be reconciled UNCHANGED with a `--scope-ack`.
  PIN THE SHARING THE WAY THE PROBE DOES INSTEAD: object identity through the shipped `getattr(module, name, getattr(module.runner_shared, name))` pattern (`BothHostsShareOneDefinition`), plus a both-hosts behavioural test that drives the real `initialize_run` over one fixture on each host, which is what `BothHostsActuallyRefuse` exists for and is the `pgq326` lesson (agy DECIDED an orchestrator action while having no dispatch branch that read it). That pair is a stronger guarantee than a guard row would have been.
  - Depends on: E-02, E-03
  - Expected outcome: the prose-only case still refuses via the probe; the two rule ids differ; the probe's test file is absent from this child's diff; and the sharing is pinned by object identity plus a both-hosts behavioural refusal, with NO refork-guard row added and that file reconciled unchanged.
  - Execution state: performed

- [x] E-05 PROVE A SHAPE REFUSAL SPENDS ZERO MODEL CALLS (criterion 11), which is the whole point of the ordering. Assert it by OBSERVATION rather than by reading the code path: inject a probe double and assert it was never called.
  MAKE THE ASSERTION NON-VACUOUS, WHICH TAKES CARE (PR-303). Do NOT rest it on the real spawn not happening: `_assert_probe_spawn_is_permitted` RAISES on any real spawn whenever pytest is running, so "no tokens were spent" is already true suite-wide and says NOTHING about this gate's ordering. The claim that matters is that `ask_orchestrator_probe` was never REACHED. Count invocations of an injected double and assert ZERO. `probe_orchestrator` already accepts `asker`, `runner` and a `counter` list, and appends the target's id6 to `counter` per attempt, so an empty `counter` after a refused run is the direct observation. A test that merely completes without a `DriverError` about a real spawn has proven nothing.
  - Depends on: E-02
  - Expected outcome: a run refused by the shape check shows ZERO invocations of the injected probe double (an empty `counter`), and the test would FAIL if the gate were sited after the probe.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `enforce_orchestrator_probe_gate` IS CALLED FROM `initialize_run_core`, not from `run_queue`. The queue is BUILT and then gated; `run_queue` is the dispatch loop where `queue_sort_key` orders by `dependency_depth` first. So a pre-queue gate refuses regardless of an item's dependencies or position, and a `DriverError` there means the dispatch loop never starts.
- THE BATCH-REPORT SHAPE ALREADY EXISTS in that gate: loop targets, append `outcomes`, partition into `blocking` and `unavailable`. E-03 generalises it across check kinds rather than rebuilding it.
- `queued_orchestrator_targets` SCOPES TO THE QUEUE ON PURPOSE (its docstring: "Never the whole corpus"), because `aw oc run all` would otherwise make the cost a function of the tree. It also SKIPS an unreadable plan rather than refusing, leaving that to the existing preflight. E-01 reuses it.
- THE THREE EXISTING PRE-QUEUE GATES RAISE BEFORE THE RUN DIRECTORY EXISTS (`enforce_draft_admission_gate` `:11853`, `enforce_dependency_preflight` `:11881`, `enforce_mixed_type_gate` `:11907`; `run_dir` is created at `:11917`), and the probe's post-directory siting at `:12122` is documented as a deliberate PRICED EXCEPTION because it must log a model call. The shape check has no such need.
- `--prepare-only` TAKES AN EARLY RETURN AT `:12103`, BETWEEN THE RUN DIRECTORY AND THE PROBE, and this is the fact that DECIDES E-02's siting (PR-301). A gate placed beside the probe is skipped under that flag; a gate placed with the three pre-queue gates is not. The probe's skip there is correct on a reason that does not transfer (spending a model turn would break the flag's no-launch contract), and it is ANNOUNCED so "an operator inspecting a queue must not conclude the orchestrators in it were cleared".
- MIGRATION MOVES THE PROBE CACHE KEY, so no stale pass survives child 04's rewrite (verified at review): `probe_cache_digest` covers E-item action text, and rewriting a prose row into `CONFIRM <id6> REACHED <status>` changes the digest. Do not add cache invalidation for that; it is already by construction.
- BOTH HOSTS REACH `initialize_run_core` THROUGH ONE SEAM (`oc_runipd.py:3360`, `agy_runipd.py:2137`), so a gate added inside it gates both by construction, and E-01's object-identity requirement is about the RE-EXPORTED symbol rather than about reaching the call.
- NO SYMBOL FLOWS FROM `oc_runipd` TO `agy_runipd` WITHOUT COST: agy already imports dozens of names from oc and none flow back. Shared symbols belong in `runner_shared`, and `tests/test_runner_refork_guard.py` is the pin.
- NO PRE-QUEUE GATE IS A HOST ATTRIBUTE, which corrects E-01's original re-export instruction (PR-304). Measured at review: `hasattr` is FALSE on both hosts for `enforce_orchestrator_probe_gate`, `enforce_mixed_type_gate`, `enforce_draft_admission_gate` and `queued_orchestrator_targets`. The hosts share them by CALLING `initialize_run_core` (`oc_runipd.py:3360`, `agy_runipd.py:2137`). The shipped identity assertion is therefore `getattr(module, name, getattr(module.runner_shared, name))` plus `assertIs`, as `BothHostsShareOneDefinition` does, and NOT a direct attribute read.
- THE REFORK GUARD'S AGGREGATE TEST DOES NOT FAIL A ONE-SIDED ROW (measured previously in this repository: 4 of 46 shipped rows are legitimately one-sided and pass). MORE IMPORTANTLY ITS IDENTITY HALF REQUIRES A HOST ATTRIBUTE and reports MISSING with the remedy "re-export" when there is none, so it is the WRONG pin for a `runner_shared`-only gate (PR-305, verified by constructing the row in-process). Use object identity plus a both-hosts behavioural refusal instead, as the probe does.
- SUITE BARE: `python3 -m pytest`; compare failing NODE IDS, not totals.

## Findings

| Id | Severity | Location (symbol / content anchor) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `runner_shared.enforce_orchestrator_probe_gate`; `25kzda` 2.5b | The probe must survive: an approved spec forbids substituting a syntactic rule for the semantic check, and `r07vma`'s SR-001 records that its own draft proposed exactly that and was wrong. This child therefore ADDS a gate and touches no probe function. | the spec text; 476 lines across seven functions measured |
| F-2 | HIGH | `initialize_run_core`; the three pre-queue gates | Siting is a real choice with an invariant attached: the pre-queue gates raise before any durable write, while the probe's later siting is a documented priced exception for logging a model call. The shape check has no logging need, so the earlier position is available and cleaner. | the gate's docstring; the three sibling gates' placement |
| F-3 | HIGH | `enforce_orchestrator_probe_gate`'s outcomes/partition structure | R8's batch reporting is the house pattern already, so it must be generalised rather than reimplemented; a second reporting path would diverge. | source read |
| F-4 | MEDIUM | `tests/test_runner_refork_guard.py::test_every_runner_attribute_is_the_owning_modules_object` | **REWRITTEN AT REVIEW (PR-305).** The original finding (the aggregate test passes a one-sided row, so mutation-check it) is TRUE but led to a self-contradictory instruction. The guard's identity half requires the symbol be a HOST ATTRIBUTE and reports MISSING otherwise, with the remedy "re-export". Verified by constructing the row in-process: a `runner_shared`-only gate reports MISSING on both hosts, so the row fails unless a host re-export is added, which E-01 forbids. The existing pre-queue gates carry no row for the same reason. The refork guard is the WRONG pin here; identity-plus-behaviour is the right one. | the identity half's body; the constructed row's result; the four-of-46 one-sided measurement still holds and is why a row would also be weak |
| F-5 | MEDIUM | `ask_orchestrator_probe`'s spawn seam; `probe_orchestrator`'s `counter` | Criterion 11 is provable by injection, but the assertion must count INVOCATIONS rather than observe the absence of a real spawn (see F-9, which corrects how): `probe_orchestrator` accepts `asker`/`runner`/`counter` and appends per attempt, so an empty `counter` after a refused run is the direct observation. | the docstring; `probe_orchestrator:8135,8179-8180` |
| F-6 | LOW | `queued_orchestrator_targets` | It skips an unreadable plan rather than refusing, so the shape gate inherits that behaviour and must not silently convert a skip into a pass. An unreadable plan is the existing preflight's refusal. | the docstring |
| F-7 | HIGH | `initialize_run_core` `:12103` (the `--prepare-only` early return) | **Added at review (PR-301).** The siting question had a DECIDING FACT the plan did not surface, which is why it read as a taste call. `--prepare-only` returns at `:12103`, between `run_dir` creation and the probe, so a gate sited beside the probe is SKIPPED under that flag while one sited with the three pre-queue gates is not. The probe's skip is justified on a reason that does not transfer (a model turn would break the flag's no-launch contract) and is ANNOUNCED for exactly the misreading a silent skip would cause. OQ-01 resolved to EARLY on this basis. | the call order measured at review; the probe's own skip comment |
| F-8 | MEDIUM | `probe_cache_digest`; child 04's migration | **Added at review (PR-302).** Worth recording because the opposite is a plausible worry: a cached probe PASS cannot survive the migration, because the digest covers E-item action text and rewriting a prose row into the typed form changes it. Verified in-process. So this child needs no cache-invalidation work, and an executor should not add any. | two digests computed over a pre- and post-migration fixture |
| F-9 | MEDIUM | `ask_orchestrator_probe`; `_assert_probe_spawn_is_permitted` | **Added at review (PR-303).** E-05's evidence needs care to be non-vacuous. The real spawn RAISES under pytest by construction, so "no tokens were spent" is already guaranteed suite-wide and asserting it proves nothing about the ORDERING. The claim that matters is that `ask_orchestrator_probe` was never REACHED, so the assertion must count invocations of an injected asker/runner double and show ZERO, not merely observe that no spawn occurred. | the guard's docstring ("NOT A PRODUCTION CODE PATH GUARD"); `probe_orchestrator`'s `asker`/`runner`/`counter` parameters |

## Proposed changes (ordered, validatable)

1. E-01 adds one gate in `runner_shared`, re-exported to both hosts, reusing the existing queue enumeration.
2. E-02 sites it before any agent turn and ahead of the probe, with the siting choice justified.
3. E-03 generalises the existing collect-then-partition structure across check kinds.
4. E-04 pins the probe's survival, the distinguishable rule ids, and the refork guard with a mutation check.
5. E-05 proves a shape refusal spends zero model calls, by injection.

## Deferred / out of scope (with reason)

- THE GRAMMAR AND THE SHARED FUNCTION: child 01 (`dpdyed`). This child calls it.
  - Carrier-Declined: Owned by a named sibling in this Set.
- THE REVIEW CONSUMER AND ITS REPAIR LOOP: child 02 (`r3xk1f`). Independent consumer, separately reviewable.
  - Carrier-Declined: Owned by a named sibling in this Set.
- MIGRATING THE EXISTING ORCHESTRATORS: child 04 (`68uhp0`). This child will make every live orchestrator refuse once it lands, which is EXPECTED and is why child 04 depends on it; that ordering is deliberate so the migration is verified against the same gate a run applies.
  - Carrier-Declined: Owned by a named sibling in this Set.
- RETIRING, WEAKENING, OR REORDERING THE PROBE BEHIND THE SHAPE CHECK: forbidden by `25kzda` 2.5b and pinned by criterion 9. Ordering the shape check first is not weakening the probe; deleting or gating it would be.
  - Carrier-Declined: An explicit non-goal the governing spec forbids.
- TYPING THE ORCHESTRATOR'S PROSE SECTIONS so the probe becomes unnecessary: out of scope and out of this Set. Spec Section 3a limit 1 records the residue as an honest limit.
  - Carrier: rmcqw8

## Scope check

- Over-scope: `tests/test_runner_refork_guard.py` is declared but is now EXPECTED TO BE RECONCILED UNCHANGED with a `--scope-ack` (PR-305): E-04's refork row was withdrawn as self-contradictory, since the guard's identity half demands a host attribute the gate deliberately does not have. Leaving the path declared is harmless and honest; adding a row to justify the declaration is not, and would force the host re-export E-01 forbids.
- Under-scope: if E-02's siting decision places the gate somewhere this plan does not declare (for example a host-level entry point rather than `initialize_run_core`'s shared path), that path must be DECLARED before editing. The siting is deliberately left as a recorded decision rather than prescribed, so the executor should expect to amend `- Scope-Paths:` and say so.

## Required tests / validation

`python3 -m pytest` BARE, in an isolated worktree, baseline measured there, compared by failing NODE ID.

BASELINE MEASURED AT REVIEW on this lane at HEAD `8d603020`: `1 failed, 7305 passed, 3 skipped, 2 xfailed`. The single failure is `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`, it is PINNED TO THE LIVE MUTABLE PLAN CORPUS, and it is NOT THIS PLAN'S: it names three `reaskscore` plans another party is editing concurrently in this shared checkout. It was PROVEN pre-existing during child 01's review by stashing every edit and re-running the single node, which still failed. Do not touch those plans and do not report it as a regression. Re-measure your own before-baseline; the criterion is AFTER minus BEFORE being EMPTY.

RUN THE THREE ADJACENT SUITES EXPLICITLY, since this child edits the module they guard: `python3 -m pytest tests/test_orchestrator_probe.py tests/test_orchestrator_probe_cache.py tests/test_runner_refork_guard.py -o addopts=""`. Measured together at review: `142 passed` for the three files, so any failure there is yours.

EXPECT THE LIVE CORPUS TO REFUSE once this lands, and do NOT fix it here: measured at HEAD `21eff5d8`, ZERO live orchestrator rows conform (the denominator was re-measured at review as 38 rows across 12 orchestrators, not the spec's dated 32; re-derive it rather than quoting either), so every pending orchestrator will refuse until child 04 migrates them. Tests must therefore use FIXTURES rather than the repository's own plans, and an executor who finds themselves editing a real orchestrator to make a test pass has taken child 04's work and should stop.

Beyond the suite: the object-identity check across both hosts; a three-violation queue reporting all findings in one pass; the prose-only case still refused by the probe; both rule ids side by side; the refork-guard mutation check; and zero probe invocations on a shape refusal.

## Spec / documentation sync

N/A with reason: spec `r07vma` R8/R9 and criteria 9 through 11 are implemented as written, and `25kzda` 2.5b is respected rather than amended (the probe keeps its mechanism and its position relative to the agent turn; only a cheaper check is added ahead of it). No `.spec.md` path is declared. If an executor concludes the ordering requires amending 2.5b, that is a finding to report rather than an edit to make, because 2.5b is approved and its prohibition is what this child is built around.

## Open questions

### OQ-01: Should the shape gate refuse before the run directory exists, or beside the probe so its refusal is readable in `aw runs`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW FROM REPOSITORY EVIDENCE as **EARLY, with the three sibling pre-queue gates** (PR-301). The authored rationale reached the same PROPOSED DIRECTION, but it framed the trade as invariant-tidiness versus operator-readability, which is a matter of taste and is why it was left open. There is a DECIDING FACT the plan did not surface, and it is not a matter of taste.
  THE DECIDING FACT IS `--prepare-only`. Measured in `initialize_run_core` at review, the call order is: the three pre-queue gates (`:11853`, `:11881`, `:11907`), then `run_dir` is created (`:11917`), then an EARLY RETURN for `--prepare-only` (`:12103`), and only then the probe (`:12122`). So a gate placed "beside the probe" sits DOWNSTREAM of that early return and is SKIPPED under `--prepare-only`, while a gate placed with the three pre-queue gates runs regardless.
  WHY THAT DECIDES IT RATHER THAN MERELY INFORMING IT. The probe's own skip under `--prepare-only` is CORRECT and is justified in its comment on a reason that does not transfer: "That flag's documented contract is 'create and display the durable queue WITHOUT launching OpenCode', so spending a model turn under it would break the one promise it makes." The shape check spends NO model turn, so skipping it buys nothing and costs the operator the one thing `--prepare-only` is for: being told, before committing to a run, that the queue is not runnable. Worse, the probe's skip is ANNOUNCED precisely so "an operator inspecting a queue must not conclude the orchestrators in it were cleared"; a silently-skipped shape check would recreate exactly that false impression with no announcement behind it.
  THE COST IS ACCEPTED AND STATED: an early refusal is read from the process output rather than from `aw runs`, because no run directory exists to record it. That is the right trade for this control, since a shape violation is fixed by editing a plan, not by inspecting run state, and criterion 11's "zero model calls" becomes trivially provable because there is no run to probe. If durable readability is later wanted, the honest change is to keep the check early and ALSO record it, not to move it behind the early return.
- Carrier-Declined: RESOLVED AT REVIEW, so nothing outlives this plan (PR-301, superseding the earlier self-closing note). The siting is now decided from repository evidence rather than deferred to execution, E-02 carries the decision and the `--prepare-only` reason, and V-02 requires the `--prepare-only` behaviour be demonstrated. There is no future act for a carrier to own.


## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste object-identity output resolving the gate symbol from BOTH hosts to the same `runner_shared` object USING THE SHIPPED PATTERN `getattr(module, name, getattr(module.runner_shared, name))` and `assertIs`, as `tests/test_orchestrator_probe.py::BothHostsShareOneDefinition` does. A bare `oc.<sym> is agy.<sym>` FAILS this item as unsatisfiable (PR-304): no pre-queue gate is a host attribute today, verified at review, so a direct attribute read raises `AttributeError` rather than proving identity, and adding one to make it pass would introduce the host-surface symbol this plan forbids.
  Paste the AST-measured oc-to-agy import count before and after, showing it did not increase. Paste the call showing `queued_orchestrator_targets` is reused rather than a second queue walk added.
  - Observed evidence: PASS.
    Object identity resolution across both hosts using the shipped getattr fallback pattern:
    ```
    oc: getattr fallback is rs.enforce_orchestrator_shape_gate -> True
    oc: direct hasattr -> False
    agy: getattr fallback is rs.enforce_orchestrator_shape_gate -> True
    agy: direct hasattr -> False
    ```
    AST-measured oc-to-agy import count before and after:
    ```
    oc-to-agy import count: 4 ['record_item_spec_edits', 'classify_recovery_disposition', 'build_verify_and_continue_notice', 'route_recovery_turn']
    ```
    Reuse of `queued_orchestrator_targets` inside `enforce_orchestrator_shape_gate`:
    ```python
    targets = queued_orchestrator_targets(state, repo=Path(repo))
    ```
    AST call scan in `enforce_orchestrator_shape_gate`:
    ```
    calls in enforce_orchestrator_shape_gate: ['queued_orchestrator_targets', 'sum', 'len', 'DriverError', 'tuple', 'Path', 'len']
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the code comment recording the siting and WHY, naming both the no-durable-write invariant and the `--prepare-only` reason (PR-301). Paste proof a refused run left NO agent turn, NO lane worktree, NO session and NO run directory; since the gate raises before `run_dir` is created, the strongest form is showing `state_root(repo)` gained no new run directory at all, which also evidences criterion 11 by there being no run to probe.
  AND DEMONSTRATE THE `--prepare-only` CASE EXPLICITLY, which is the behaviour that decided the siting: run a non-conforming queue under `--prepare-only` and show it REFUSES rather than printing a queue. A shape check that `--prepare-only` skips has been sited behind the early return at `:12103` and FAILS this item, because it would leave an operator inspecting a queue with the false impression the orchestrators in it were fine, which is the exact misreading the probe's own announced skip exists to prevent.
  - Observed evidence: PASS.
    Code comment in `initialize_run_core` (`agent_workflows/runner_shared.py`):
    ```python
    # orchtyped-03 (`0xmk4e`) E-01/E-02: THE PRE-QUEUE ORCHESTRATOR SHAPE GATE, sited HERE ahead
    # of run directory creation, sessions, worktrees, and ahead of the semantic coverage probe.
    #
    # SITED EARLY, WITH THE THREE PRE-QUEUE GATES (draft admission, dependency preflight, and
    # mixed-type gate, each called above), and that siting is a DECISION (OQ-01 / PR-301) resting
    # on repository facts rather than invariant-tidiness taste:
    #
    # 1. NO DURABLE WRITE: raising before `run_dir` is created ensures no run directory, events.jsonl,
    #    state.json, or prompt logs are created on a shape refusal.
    # 2. `--prepare-only` INTEGRATION: `--prepare-only` returns early between run directory creation
    #    and the probe gate. Siting this deterministic, free check before the run directory ensures
    #    `--prepare-only` evaluates orchestrator shape conformance and refuses invalid queues rather
    #    than printing a non-runnable queue.
    # 3. ZERO MODEL CALLS: because this gate sits ahead of the probe gate, non-conforming queues
    #    refuse without ever invoking the model coverage probe (criterion 11).
    enforce_orchestrator_shape_gate({"queue": queue}, repo=repo)
    ```
    Proof `state_root(repo)` gained no run directory on refusal:
    ```
    Durable run directories created in state_root: []
    ```
    Demonstration of `--prepare-only` refusal over non-conforming queue:
    ```
    $ aw oc run start bad001 --repo /tmp/repo-1 --prepare-only
    agent_workflows.runner_shared.DriverError: orchestrator checklist shape check failed (IPD-S407): 1 finding across 1 queued orchestrator.
      [bad001] (20260924-fixbad-00-bad001.ipd.md):
        - E-01 is not a typed child-tracking row (not-a-typed-child-tracking-row): the row does not match the typed grammar exactly (it must carry no prose before or after the three fields; free prose belongs on the continuation lines). Write it as `- [ ] E-NN CONFIRM <child-id6> REACHED <status>`. WHY: an Order-0 orchestrator is retired PROGRAMMATICALLY, with the pre-transition E-*/V-* checkpoint deliberately skipped, so a step parked on a parent is performed by NOBODY and is marked complete having never run. DELETING the item is NOT an acceptable fix: the checklist is what makes a Set execute completely and in order when it is run BY HAND, so deleting it causes the lost work this rule prevents. FIX: two remedies are legitimate and this rule does not prescribe either: MOVE the step into a child plan whose `- Item-Dependencies:` put it in the right order, OR REMOVE it because a child already covers it (which is removal for redundancy, not deletion to silence this rule). Row as written: '- [ ] E-01 Establish the characterization baseline before any child runs'
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the output of a queue containing THREE non-conforming orchestrators, showing every finding for all three reported together before a single exit. Confirm no early return exists by showing the collect-then-partition structure in the diff. A run that reported one violation and exited FAILS this item regardless of the exit code.
  - Observed evidence: PASS.
    Output of a queue containing three non-conforming orchestrators:
    ```
    orchestrator checklist shape check failed (IPD-S407): 3 findings across 3 queued orchestrators.
      [bad001] (20260924-fixbad-00-bad001.ipd.md):
        - E-01 is not a typed child-tracking row (not-a-typed-child-tracking-row): the row does not match the typed grammar exactly (it must carry no prose before or after the three fields; free prose belongs on the continuation lines). Write it as `- [ ] E-NN CONFIRM <child-id6> REACHED <status>`. WHY: an Order-0 orchestrator is retired PROGRAMMATICALLY, with the pre-transition E-*/V-* checkpoint deliberately skipped, so a step parked on a parent is performed by NOBODY and is marked complete having never run. DELETING the item is NOT an acceptable fix: the checklist is what makes a Set execute completely and in order when it is run BY HAND, so deleting it causes the lost work this rule prevents. FIX: two remedies are legitimate and this rule does not prescribe either: MOVE the step into a child plan whose `- Item-Dependencies:` put it in the right order, OR REMOVE it because a child already covers it (which is removal for redundancy, not deletion to silence this rule). Row as written: '- [ ] E-01 Establish the characterization baseline before any child runs'
      [bad002] (20260924-fixbad2-00-bad002.ipd.md):
        - E-01 is not a typed child-tracking row (child-id6-is-not-a-row-of-this-orchestrators-child-table): 'unk999' is not a row of this orchestrator's own child table (it declares chd001). Write it as `- [ ] E-NN CONFIRM <child-id6> REACHED <status>`. WHY: an Order-0 orchestrator is retired PROGRAMMATICALLY, with the pre-transition E-*/V-* checkpoint deliberately skipped, so a step parked on a parent is performed by NOBODY and is marked complete having never run. DELETING the item is NOT an acceptable fix: the checklist is what makes a Set execute completely and in order when it is run BY HAND, so deleting it causes the lost work this rule prevents. FIX: two remedies are legitimate and this rule does not prescribe either: MOVE the step into a child plan whose `- Item-Dependencies:` put it in the right order, OR REMOVE it because a child already covers it (which is removal for redundancy, not deletion to silence this rule). Row as written: '- [ ] E-01 CONFIRM unk999 REACHED executed'
      [bad003] (20260924-fixbad3-00-bad003.ipd.md):
        - E-01 is not a typed child-tracking row (missing-the-depends-on-edge): the row supplies no `- Depends on:` edge, which is the third typed field (write `- Depends on: none` when it has no predecessor). Write it as `- [ ] E-NN CONFIRM <child-id6> REACHED <status>`. WHY: an Order-0 orchestrator is retired PROGRAMMATICALLY, with the pre-transition E-*/V-* checkpoint deliberately skipped, so a step parked on a parent is performed by NOBODY and is marked complete having never run. DELETING the item is NOT an acceptable fix: the checklist is what makes a Set execute completely and in order when it is run BY HAND, so deleting it causes the lost work this rule prevents. FIX: two remedies are legitimate and this rule does not prescribe either: MOVE the step into a child plan whose `- Item-Dependencies:` put it in the right order, OR REMOVE it because a child already covers it (which is removal for redundancy, not deletion to silence this rule). Row as written: '- [ ] E-01 CONFIRM chd001 REACHED executed'
    ```
    Collect-then-partition loop structure in `enforce_orchestrator_shape_gate`:
    ```python
    targets = queued_orchestrator_targets(state, repo=Path(repo))
    outcomes: list[tuple[ProbeTarget, _lint.OrchestratorRowResult]] = []
    for target in targets:
        res = _lint.orchestrator_row_conformance(target.text)
        outcomes.append((target, res))

    blocking = [(target, res) for target, res in outcomes if not res.conforming]
    if not blocking:
        return tuple(outcomes)
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste a fixture orchestrator whose ROWS all conform but which carries an obligation in a BARE INDENTED continuation line, and show it is STILL refused by the probe after this change. State explicitly that the obligation is written as a bare indented line rather than as a `- Key: value` subfield or in a prose section, and say why (PR-005): neither of those reaches the probe's payload, so a fixture using one proves nothing. Paste the shape refusal and the probe refusal side by side, showing DIFFERENT rule ids. Paste `git status`/`git diff --stat` proving `tests/test_orchestrator_probe.py` is byte-unchanged and the seven probe functions are intact. DO NOT PASTE A REFORK-GUARD MUTATION CHECK; that requirement was withdrawn at review as self-contradictory (PR-305). Instead paste (a) the object-identity resolution from both hosts under the shipped `getattr(module, name, getattr(module.runner_shared, name))` pattern, and (b) a both-hosts BEHAVIOURAL test driving the real `initialize_run` over the same non-conforming fixture and refusing on each, following `BothHostsActuallyRefuse`. Confirm `tests/test_runner_refork_guard.py` is reconciled UNCHANGED with a `--scope-ack`.
  - Observed evidence: PASS.
    Fixture orchestrator with typed rows and bare indented continuation line obligation:
    ```markdown
    - [ ] E-01 CONFIRM chd001 REACHED executed
      Establish the characterization baseline before any child runs and produce the inventory report.
      - Depends on: none
      - Expected outcome: chd001 reads `- Status: executed` on disk.
      - Execution state: pending
    ```
    The obligation is written as a bare indented line immediately after the E-item header because `e_item_action_blocks` collects bare continuation lines into the probe payload while excluding `- Key: value` subfields (`ipd_lint._SUBFIELD_RE`) and prose outside checklist items.

    Shape check verdict: passes (`conforming: True`).
    Probe payload excerpt:
    ```
    ### Checklist item action text

    - E-01 CONFIRM chd001 REACHED executed Establish the characterization baseline before any child runs and produce the inventory report.

    ### Child IPDs table (row cells, in document order)

    | Order | Id | Status | Plan | Depends on |
    | 01 | chd001 | pending | .aw/records/plans/pending/20260924-fixprose-01-chd001.ipd.md | none |
    ```
    Probe refusal:
    ```
    the orchestrator coverage probe reports that prs001 carries work no child covers. The runner retires an orchestrator once its children are `executed` and SKIPS the pre-transition E/V checkpoint, so that work would be reported complete having never been performed or verified. ADD A CHILD for the uncovered work...
    ```
    Rule IDs side by side:
    - Shape check rule ID: `IPD-S407`
    - Probe check rule ID: `orchestrator-uncovered-work`

    Git diff stat proving `tests/test_orchestrator_probe.py` and `tests/test_runner_refork_guard.py` are byte-unchanged:
    ```
    $ git diff --stat tests/test_orchestrator_probe.py tests/test_runner_refork_guard.py
    (empty output: files are byte-unchanged)
    ```
    Seven probe functions intact in `agent_workflows/runner_shared.py`:
    `render_probe_prompt`, `orchestrator_probe_excerpt`, `classify_probe_reply`, `probe_reply_text`, `probe_argv`, `ask_orchestrator_probe`, `probe_orchestrator`.

    Both-hosts behavioural test (`tests/test_orchestrator_shape_gate.py::TheProbeSurvivesAndRefusalsAreDistinct::test_both_hosts_behaviourally_refuse_non_conforming_orchestrators`):
    Passed on both `oc` and `agy` hosts.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the test that injects a probe double and asserts ZERO invocations on a run the shape check refused, showing the injection and not only the assertion. Use the invocation count (an empty `counter`, or an asker double that records calls), NOT the absence of a real spawn (PR-303): `_assert_probe_spawn_is_permitted` raises on any real spawn under pytest, so absence-of-spawn is guaranteed suite-wide and evidences nothing about ordering.
  AND SHOW THE TEST CAN FAIL, which is what distinguishes it from a tautology: move the gate after the probe call (or call the probe first) in a scratch edit, show the assertion FAILS, then revert and show it passes. Paste both.
  - Observed evidence: PASS.
    Test method `test_shape_refusal_spends_zero_probe_invocations` in `tests/test_orchestrator_shape_gate.py`:
    ```python
    counter: list[str] = []

    def probe_double(*args, **kwargs):
        counter.append("called")
        return rs.PROBE_ANSWER_EXECUTIONS, "double"

    with unittest.mock.patch.object(rs, "ask_orchestrator_probe", probe_double):
        args = oc_runipd.build_parser().parse_args(["start", "bad001", "--repo", str(repo)])
        with self.assertRaises(rs.DriverError):
            oc_runipd.initialize_run(args)

    self.assertEqual(counter, [], "Probe double must not be invoked on shape refusal")
    ```
    Pass output when shape gate is correctly sited before the probe:
    ```
    tests/test_orchestrator_shape_gate.py::TheShapeRefusalSpendsZeroModelCalls::test_shape_refusal_spends_zero_probe_invocations PASSED [100%]
    ```
    Must-fail-first demonstration (scratch edit temporarily removing pre-queue gate so probe runs first):
    ```
    FAILED tests/test_orchestrator_shape_gate.py::TheShapeRefusalSpendsZeroModelCalls::test_shape_refusal_spends_zero_probe_invocations
    AssertionError: Lists differ: ['called'] != []
    First list contains 1 additional elements.
    First extra element 0:
    'called'
    - ['called']
    + [] : Probe double must not be invoked on shape refusal
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Size note: 5 E-leaves in 2 groups. The gate and its siting are one concern; the report, the coexistence pins and the zero-cost proof are the surfaces that prove it behaves.
- Cohesion rationale: E-01 and E-02 are one gate and its position, inseparable because the position is what makes it cost nothing. E-03 through E-05 are the three properties the spec's criteria demand of that gate (batch reporting, coexistence with the probe, zero model calls), and each is meaningless without the gate existing. Splitting the pins into their own child would leave a gate whose required properties are unproven.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. When reporting tests passed, paste the ACTUAL runner output. This is a SHARED CHECKOUT: other agents are editing this tree concurrently, so never revert or commit a file you did not change. In particular do NOT edit any real orchestrator to make a test pass; that is child 04's work and doing it here hides the migration's cost.

Post-gate lifecycle: requires `/plan-review` then explicit human approval (`aw ipd set approved 0xmk4e --by-human --message ...`). Do NOT hand-write a `- Readiness:` field. Its `- Item-Dependencies:` refuse dispatch until `dpdyed` is executed. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

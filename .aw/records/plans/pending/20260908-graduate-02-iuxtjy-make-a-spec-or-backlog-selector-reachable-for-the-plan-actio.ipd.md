# IPD: Make a spec or backlog selector reachable for the plan action now that spec discovery exists

- Date: 2026-09-08
- Kind: child
- Concern: Spec `25kzda` (`- Status: approved`) describes the graduation path as SHIPPED BEHAVIOR that is not. Its §1.3 lists "Author an IPD from an approved spec" and "Graduate an open backlog item into an IPD" as dispositions of `aw <host> run`, and §2.1 registers `--action plan` whose legality rules say it is legal "only for an `approved` spec or `open` backlog item". Neither works: `ACTION_IMPLEMENTED` is `frozenset({'review'})` (measured), so `--action plan` refuses, and no selector expansion or queue builder consults a spec or backlog tree.
  THE GAP IS MUCH NARROWER THAN BACKLOG `6h7y2y` STATES, AND THAT NARROWING IS THIS PLAN'S MAIN FINDING. The item says "NO selector reaches a spec or a backlog item however it is spelled" because `runner_shared.discover_plans` walks only the two plans trees. That is now FALSE for specs: `runner_shared.discover_specs` EXISTS, is documented as "the SPEC sibling of `discover_plans`", reads identity through `check_engine._ITEM_ID_RE`, status through `selectors.read_front_matter_status`, and enumerates through `check_engine._iter_spec_records` so it adds NO new path literal (guarded by an AST test rejecting a new `"records/specs"` literal in that module). Measured, it finds 9 specs including `25kzda` at `status='approved'`. Executed plan `5slbpi` E-05 shipped it: "Let needs-review discovery reach the SPECS tree".
  WHAT ACTUALLY SURVIVES: `discover_specs` has exactly ONE consumer, the review sweep (`runner_shared.py:1107`, inside the `sweep` helper that dispatches on `spec_type`). It is not wired into selector expansion or the queue builder, so a spec cannot be the SUBJECT of a `plan` action. And there is no backlog equivalent at all: no `discover_backlog` exists.
  THE ITEM'S OTHER PREMISE IS ALSO OVERTAKEN. Its reproduction (`aw oc run start --action plan 25kzda` yielding "'25kzda' is a backlog item ..., not an IPD plan") no longer describes the failure mode: `--action plan` now FAILS CLOSED before that, with a named refusal that starts no run ("`--action plan` is not implemented yet ... No run was started. To review instead, run: aw oc review <selector>"). That landed at `a3bb14bf` on 2026-09-05, ONE DAY BEFORE the item was filed. So the operator-facing hazard is already gone; only the capability is missing.
- Scope: Make a spec or backlog selector resolvable for the `plan` action, CONSUMING the existing `discover_specs` rather than adding a second enumeration, and wire child 01's pre-graduation view into that path so the guard is reached rather than merely available. EXCLUDES re-implementing the `--action plan` fail-closed refusal, which already works; excludes the pre-graduation view itself (child 01 `jxxec8`); excludes per-requirement spec tracking (`f1sw71`); excludes the spec-review workflow and the `to-review -> reviewed` attestation, owned by spec `6m4kow` and its three executed plans.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_graduation_dispatch.py, tests/test_runner_shared.py
- Item-Dependencies: executed:jxxec8
- Status: to-review
- Set: graduate
- Order: 2
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: iuxtjy
- From-Backlog: 6h7y2y

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `6h7y2y` Half 1, NARROWED, and this is the child that CLOSES the item. It carries no `- Blocks-Release:` so none is inherited or invented. `- Item-Dependencies: executed:jxxec8` is declared because the item's sequencing note is explicit and gives its reason: "A working `--action plan` with no duplicate check is a machine for generating redundant plans faster than a human can."
  TWO OF THE ITEM'S THREE PREMISES ARE OVERTAKEN BY SHIPPED WORK, measured rather than assumed, and both narrowings are recorded in the item file. FIRST, `--action plan` already fails closed with a named refusal that starts no run, landed at `a3bb14bf` the day BEFORE the item was written; the item's reproduction therefore no longer describes the failure and must not be re-fixed. SECOND, `discover_specs` already exists and finds 9 specs including `25kzda`, shipped by executed plan `5slbpi` E-05, so "no selector reaches a spec however it is spelled" is false for specs. What survives is that `discover_specs` has ONE consumer (the review sweep) and no backlog equivalent exists.
  THE ASYMMETRY BETWEEN SPECS AND BACKLOG IS THE BIGGEST THING THE ITEM DOES NOT SAY, and it decides this plan's shape: specs have a careful, guarded enumeration to consume, while backlog items have none, so those two halves are NOT the same size. E-02 and E-03 are separated for exactly that reason, and OQ-01 escalates whether the backlog half belongs here at all or in a follow-on.
  I ALSO READ `discover_specs`' OWN DOCUMENTED LIMITS rather than assuming it is a drop-in: it deliberately SKIPS a spec with no `- Id:` (because such a spec "cannot be named by a selector, cannot carry a review record ... and cannot be attested"), and it finds only 9 of 28 specs for that reason, which its docstring records so "a reader who sees 8 discovered against 27 spec files will otherwise assume a bug". So consuming it inherits a documented, deliberate coverage gap that this plan must state rather than silently pass on to an operator who names an unfound spec.

## Goal

Let a spec or backlog item actually be the subject of a plan action, reusing the discovery that already exists, with the duplicate guard reached on the way.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm the ground before building on it

- [ ] E-01 RE-MEASURE WHAT ALREADY EXISTS AND RECORD IT, before writing anything. Both drivers and `runner_shared` are edited by live runs, and this plan's whole shape rests on two shipped facts that must still hold at execution time.
  CONFIRM `--action plan` STILL FAILS CLOSED: `ACTION_IMPLEMENTED` must still exclude `plan` and `enforce_requested_action('plan', ...)` must still raise a refusal that starts no run. If another Set has since implemented it, STOP and report rather than building a second path.
  CONFIRM `discover_specs` STILL EXISTS AND STILL HAS ONE CONSUMER, and record its measured coverage (9 of 28 specs at authoring, for the documented `- Id:` reason). If its consumer count has grown, read the new consumer before adding a third.
  CONFIRM CHILD 01 (`jxxec8`) IS EXECUTED and read its view's actual interface, since E-04 calls it. Do not guess its signature from this plan.
  - Depends on: none
  - Expected outcome: all three facts re-measured and pasted; any divergence from this plan's assumptions reported rather than worked around; `discover_specs`' coverage number recorded at execution time.
  - Execution state: pending

### Task group 2: reach a spec, then decide about backlog

- [ ] E-02 MAKE A SPEC SELECTOR RESOLVE FOR THE `plan` ACTION BY CONSUMING `discover_specs`. This is the surviving half of the item's Half 1 and it is small precisely because the enumeration exists.
  DO NOT ADD A SECOND SPEC ENUMERATION. `discover_specs` reads identity, status and the tree through shared authorities and adds no path literal, guarded by an AST test that rejects a new `"records/specs"` string constant in `runner_shared.py`. A parallel walk would make the review sweep and the plan action disagree about which specs exist, which is the exact class of defect the sweep's own docstring says it was built to remove ("so the sweep and the dispatch table agree BY CONSTRUCTION").
  INHERIT AND SURFACE ITS COVERAGE GAP. `discover_specs` deliberately skips a spec with no `- Id:`, so an operator naming such a spec gets "not found" for a file that plainly exists. That is correct behavior with a confusing message. Make the refusal SAY why (a spec without an `- Id:` cannot be named by a selector), rather than letting a documented deliberate skip look like a bug.
  DO NOT RE-IMPLEMENT THE FAIL-CLOSED REFUSAL. It already works (E-01 confirms). Extend `ACTION_IMPLEMENTED` only for what this plan actually delivers, and leave the refusal in place for the rest. A Set that made an unimplemented path silently proceed would be worse than the gap it closed.
  - Depends on: E-01
  - Expected outcome: a spec selector resolves for the `plan` action through `discover_specs` alone; the no-`- Id:` skip produces a refusal that explains itself; `ACTION_IMPLEMENTED` widens only for what is delivered; the AST no-new-path-literal guard still passes.
  - Execution state: pending

- [ ] E-03 DECIDE THE BACKLOG HALF EXPLICITLY, and implement it only if OQ-01 resolves that it belongs here. There is NO `discover_backlog`, so unlike the spec half this one means building an enumeration, which is a materially larger change than consuming one.
  IF YOU BUILD IT, FOLLOW `discover_specs` EXACTLY. Its design is the template and its choices are deliberate: enumerate through the existing shared iterator so no new path literal is added, read identity and status through the shared authorities rather than fresh regexes, and skip an item that cannot be named or attested rather than admitting it. `aw backlog` already owns the tree, so an enumeration must not become a second authority over it.
  IF YOU DO NOT BUILD IT, LEAVE THE REFUSAL INTACT for backlog selectors and say so in the refusal text. A half-implemented `plan` action that accepts a spec and silently ignores a backlog item would be worse than one that refuses both, because the operator cannot tell which happened.
  - Depends on: E-02
  - Expected outcome: OQ-01 answered and recorded; either a `discover_backlog` built to `discover_specs`' template with no new path literal, or an explicit refusal for backlog selectors that names the gap; never a silent partial.
  - Execution state: pending

### Task group 3: reach the guard, and both hosts

- [ ] E-04 CALL CHILD 01'S PRE-GRADUATION VIEW ON THIS PATH, so the guard is REACHED rather than merely available. This is the item's sequencing requirement made real: the guard exists after child 01, but until something calls it during graduation it helps only whoever remembers to run it.
  SHOW, DO NOT BLOCK. Child 01's view is advisory and read-only by design, because the already-implemented case is not mechanically answerable (backlog `f1sw71`) and a refusal would therefore rest on a heuristic and would flag the 17 legitimate multi-plan clusters. Report the cluster before the plan action proceeds; do not refuse on it.
  PUT IT WHERE IT IS SEEN BEFORE WORK STARTS, not after. A cluster report printed after an agent has authored a tenth plan has cost exactly what it was meant to save. The natural seam is the same pre-flight region where the other fail-closed gates already run before the run directory exists.
  DO NOT DUPLICATE THE VIEW'S LOGIC. Call it. If its interface does not fit this call site, report that rather than reimplementing a second cluster reader.
  - Depends on: E-03
  - Expected outcome: the pre-graduation cluster report is emitted before the plan action proceeds, by CALLING child 01's view; it informs and does not refuse; no cluster logic is duplicated.
  - Execution state: pending

- [ ] E-05 LAND IT ON BOTH HOSTS THROUGH ONE IMPLEMENTATION. `enforce_requested_action` exists in BOTH drivers with near-identical bodies (measured: `oc_runipd` derives via `action_for`, `agy_runipd` via `determine_action`, and their refusal texts differ only in the host name), so a one-sided change would leave the two disagreeing about what `plan` means.
  SITE SHARED LOGIC IN `runner_shared.py`, NEVER IN `oc_runipd` FOR AGY TO IMPORT. `agy_runipd` already imports 47 names from `oc_runipd` and zero flow back; adding to that list would deepen the layering defect backlog `cnwy8g` owns, whose graduated plans are re-homing exactly those names.
  RESPECT THE MEASURED HOST ASYMMETRY. `--full-auto` DEFAULTS TO TRUE on the agy host and false on oc, which is why `enforce_requested_action`'s docstring calls the legality check "THE SAFETY CONTENT OF `--action`, NOT PLUMBING": on agy a mis-derived action can execute a plan the operator asked to merely review. Any widening of `ACTION_IMPLEMENTED` must be checked against that default, not only against oc's.
  - Depends on: E-04
  - Expected outcome: one implementation for the new dispatch, sited in `runner_shared`; both hosts behave identically for a spec selector; the agy `--full-auto` default checked explicitly; the oc-to-agy import count not increased from 47.
  - Execution state: pending

- [ ] E-06 TEST THE REFUSALS AS CAREFULLY AS THE SUCCESS PATH, from fixtures. The failure modes here are worse than the gap.
  THE REQUIRED CASES: a spec at `approved` resolves and the cluster report is emitted; a spec with NO `- Id:` refuses with a message explaining why; a spec at a status the legality table forbids refuses; a backlog selector either resolves or refuses per E-03's decision, never silently no-ops; an action still in `ACTION_IMPLEMENTED`'s complement still fails closed and starts NO run; and the cluster report appears BEFORE any durable state is created.
  ASSERT THE NO-DURABLE-STATE PROPERTY ON THE FILESYSTEM, not on a return code. The existing fail-closed gates are sited before the run directory exists specifically so a refusal leaves nothing to reconcile; a new gate that creates a run directory then refuses would break that property silently.
  DO NOT READ THE LIVE SPEC TREE. It has 28 specs of which 9 are discoverable, and both numbers move; build fixtures. Child 01's live-corpus assertion is deliberate and different, because it asserts a no-false-positive property that only the real corpus can show.
  - Depends on: E-05
  - Expected outcome: six cases per host from fixtures; the no-durable-state property asserted on the filesystem; no test reads the live spec tree.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `discover_specs` EXISTS AND IS CAREFULLY BUILT, and is the thing to consume. It enumerates through `check_engine._iter_spec_records` (no new path literal, asserted by an AST test), reads `- Id:` through `check_engine._ITEM_ID_RE` and status through `selectors.read_front_matter_status` (which returns None for a multi-word status, so a legacy free-form line yields no status rather than a mis-parse), and SKIPS a spec with no `- Id:` deliberately. Measured: 9 of 28 specs discoverable, a gap its own docstring records so a reader does not assume a bug.
- THE SWEEP AND THE DISPATCH TABLE ARE DESIGNED TO AGREE BY CONSTRUCTION. `runner_shared`'s review sweep asks the SAME `run_selection_policy.needs_review` for both types precisely so they cannot disagree, and its comment says an unknown type "sweeps NOTHING rather than guessing a tree", keeping the function from becoming "the place a new type is quietly admitted without amending the dispatch table it must agree with". Adding a type means amending both together.
- `--action` LEGALITY IS SAFETY, NOT PLUMBING. `enforce_requested_action`'s docstring says so, with the measured reason: `determine_action` returns `execute` for both `approved` and `reviewed`, `--full-auto` DEFAULTS TO TRUE on agy, so a mis-derived action can execute a plan the operator asked to review. Spec `25kzda` §2.6 forbids exactly that.
- THE FAIL-CLOSED GATES RUN BEFORE THE RUN DIRECTORY EXISTS, so a refusal leaves no session and no durable state to reconcile. A new gate must preserve that.
- THE IMPORT DIRECTION IS ONE-WAY: `agy_runipd` imports 47 names from `oc_runipd`, zero flow back. Shared symbols go in `runner_shared`.
- THE ALREADY-IMPLEMENTED CASE IS NOT MECHANICALLY ANSWERABLE (backlog `f1sw71`), which is why child 01's view informs rather than refuses and why E-04 must not turn it into a gate.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses).

## Findings

| Id | Severity | Location (measured at HEAD `a2e0438a`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | PARTLY OBSOLETE | `oc_runipd.ACTION_IMPLEMENTED`; commit `a3bb14bf` | THE ITEM'S REPRODUCTION NO LONGER DESCRIBES THE FAILURE: `--action plan` FAILS CLOSED with a named refusal that starts no run, landed 2026-09-05, ONE DAY BEFORE the item was filed. Do not re-fix it. | `ACTION_IMPLEMENTED` is `frozenset({'review'})`; `enforce_requested_action('plan', ...)` raises "not implemented yet ... No run was started"; `git log -S` |
| F-2 | PARTLY OBSOLETE | `runner_shared.discover_specs`; executed plan `5slbpi` E-05 | THE ITEM'S "NO SELECTOR REACHES A SPEC" CLAIM IS FALSE FOR SPECS. `discover_specs` exists, is the documented spec sibling of `discover_plans`, and finds 9 specs including `25kzda` at `approved`. | called it |
| F-3 | MED | `runner_shared.py:1107` | WHAT SURVIVES: `discover_specs` has exactly ONE consumer, the review sweep. Nothing wires it into selector expansion or the queue builder, so a spec cannot be the subject of a `plan` action. | read its only call site |
| F-4 | MED | `runner_shared` | THE TWO HALVES ARE NOT THE SAME SIZE: there is no `discover_backlog` at all, so the backlog half means BUILDING an enumeration while the spec half means CONSUMING one. The item treats them as one job. | grepped for a backlog discovery function; none |
| F-5 | MED | `discover_specs` docstring | It deliberately SKIPS a spec with no `- Id:` and finds only 9 of 28, a gap its docstring records explicitly so a reader "will otherwise assume a bug". Consuming it inherits that gap, so the refusal must explain itself. | docstring read; count measured |
| F-6 | MED | `enforce_requested_action` in both drivers | `--action` legality is SAFETY: `--full-auto` defaults TRUE on agy, so a mis-derived action can execute a plan the operator asked to review, which spec `25kzda` §2.6 forbids. Any widening must be checked against agy's default. | docstrings read in both drivers |
| F-7 | MED | `runner_shared` review sweep comment | The sweep and the dispatch table are designed to agree BY CONSTRUCTION, and an unknown type "sweeps NOTHING rather than guessing a tree" so the function does not become "the place a new type is quietly admitted without amending the dispatch table". Adding a type means amending both. | comment read |
| F-8 | MED | spec `25kzda` §1.3, §2.1 | The spec describes graduation as shipped behavior it is not, which is the discrepancy this plan narrows. If this plan delivers a subset, the spec still overstates and the honest response is to record the gap, not amend the spec to match. | spec text |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the three shipped facts this plan rests on and reports any divergence.
2. E-02 makes a spec selector resolve for `plan` by consuming `discover_specs`, surfacing its documented coverage gap in the refusal.
3. E-03 decides the backlog half explicitly and either builds an enumeration to the same template or refuses with a named gap.
4. E-04 calls child 01's view on this path so the guard is reached, informing rather than blocking, before durable state exists.
5. E-05 lands it on both hosts through one shared implementation, checking agy's `--full-auto` default.
6. E-06 tests six cases per host from fixtures, asserting the no-durable-state property on the filesystem.

## Deferred / out of scope (with reason)

- RE-IMPLEMENTING THE `--action plan` FAIL-CLOSED REFUSAL. F-1: it already works and landed the day before the item was filed. Re-doing it would be work an existing commit already declares.
- ADDING A SECOND SPEC ENUMERATION. F-2 and F-7: `discover_specs` exists, is guarded against a new path literal, and the sweep is designed to agree with the dispatch table by construction.
- THE PRE-GRADUATION VIEW ITSELF. Child 01 (`jxxec8`), declared as this plan's `executed:` dependency. This plan CALLS it.
- PER-REQUIREMENT SPEC TRACKING AND THE ALREADY-IMPLEMENTED VERDICT. Backlog `f1sw71` (open). It is also why E-04 informs rather than refuses.
- THE SPEC-REVIEW WORKFLOW AND THE `to-review -> reviewed` ATTESTATION. Spec `6m4kow` (`to-review`) and its three executed plans (`eyh1fu`, `5slbpi`, `wpomxa`) own that. Re-deciding it here would collide with settled work.
- THE BACKLOG HALF, IF OQ-01 RESOLVES AGAINST IT. F-4: it means building an enumeration rather than consuming one, which is a different size of change. If deferred, E-03 requires an explicit refusal naming the gap rather than a silent no-op, and the item must be set `graduated` rather than `done`.
- WIDENING `ACTION_IMPLEMENTED` BEYOND WHAT IS DELIVERED. F-6: the legality check is safety content, and agy's `--full-auto` default makes an over-wide table actively dangerous.

## Scope check

- Over-scope: `oc_runipd.py` and `agy_runipd.py` are in scope ONLY to route through the shared dispatch and to widen `ACTION_IMPLEMENTED` for what is delivered. Do NOT change `determine_action`, `action_for`, or any other legality rule. Do NOT add a symbol to `oc_runipd` for agy to import.
- Under-scope: stated rather than left as `none`. After this plan, specs with no `- Id:` remain unreachable by selector (a deliberate inherited gap, F-5), the backlog half may remain unimplemented (OQ-01), and the already-implemented case remains undetectable (`f1sw71`), so spec `25kzda` §1.3 may still overstate the shipped behavior. Each is named with its owner.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. Fixtures for every case; do NOT read the live spec tree, whose discoverable count (9 of 28) moves as specs gain ids. `tests/test_runner_shared.py` holds the cross-host wrapper and call-site-count pins, so if the wiring changes a counted site, reflect it rather than working around it. Run `aw check all` before and after, since this plan touches selector resolution that other surfaces share.

## Spec / documentation sync

Spec `25kzda` (`- Status: approved`) §1.3 and §2.1 DESCRIBE THIS CAPABILITY AS SHIPPED, so this plan moves the code TOWARD the approved contract and is a COMPLIANCE fix rather than an amendment. That is the justification to record, and no spec file is declared in `- Scope-Paths:`.
TWO THINGS TO DETERMINE AND REPORT, and the first is the one that must not be got wrong. FIRST, §2.1's legality table for `plan` may require MORE than this plan delivers (both a spec and a backlog item, at specific statuses). If this plan implements a SUBSET, the spec still overstates the shipped behavior, and the honest response is to RECORD THE REMAINING GAP in this plan and leave the fail-closed refusal covering it. Do NOT amend the spec to match a partial implementation: that would convert a known gap into a silently narrowed contract. SECOND, if delivering this requires a per-type dispatch table, spec `25kzda` §2.6 governs per-type legality and F-7 warns that the sweep and the dispatch table must be amended TOGETHER; check whether the table is specified in the spec or only in code, and if in the spec, declare the file before execution since the runners announce declared spec edits before a run starts and the finalize scope gate reconciles declared against actual.
Do NOT edit §4.2's finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Does the backlog half belong in this plan or a follow-on?

- Blocking: no
- Status: open
- Owner: this plan's executor for the sizing, the maintainer for the scope call
- Resolution or deferral rationale: NOT blocking, because E-03 requires an explicit decision and, if deferred, an explicit refusal naming the gap, so the plan terminates correctly either way and never ships a silent partial. The measured asymmetry is the whole question (F-4): the spec half CONSUMES an existing, carefully guarded enumeration, while the backlog half means BUILDING one to the same template, including its no-new-path-literal guard and its skip rules. That is a materially larger change in a plan already touching both drivers. Recommend delivering the spec half here and filing the backlog half as a follow-on carrying the same provenance, in which case backlog `6h7y2y` is set `graduated` rather than `done`. If the maintainer wants both, this plan grows by roughly one E-item and its risk concentrates in a new enumeration over a tree `aw backlog` already owns.

### OQ-02: Should a spec with no `- Id:` be reported as unreachable, or should the plan action mint one?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-02 already requires the refusal to EXPLAIN itself, which is sufficient and safe. Recommend REPORTING and not minting. Minting an id6 into a spec as a side effect of naming it in a run would be a durable records write performed by a dispatch path, which is exactly the kind of silent mutation the `aw specs` verbs exist to own; `aw rename specs <legacy> --to-id6` already exists for that conversion and is the operator's route. Measured, 19 of 28 specs lack a discoverable id6, so this case is common rather than exotic, which makes a clear message valuable and a silent mutation dangerous.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste all three re-measurements: `ACTION_IMPLEMENTED`'s value and the `plan` refusal text; `discover_specs`' existence, its consumer count, and its discoverable-spec count AT YOUR HEAD; and child `jxxec8`'s `- Status:` line with its view's actual interface. State any divergence from this plan's assumptions and what you did about it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a spec selector resolving for the `plan` action, showing the resolved spec and its status. Paste the code showing `discover_specs` was CALLED (not a similar walk), and paste the AST no-new-path-literal guard PASSING. Paste the refusal for a spec with no `- Id:`, showing the message EXPLAINS why rather than saying only "not found". Paste `ACTION_IMPLEMENTED` before and after, showing it widened only for what is delivered.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: state OQ-01's answer and the sizing that decided it. If BUILT: paste `discover_backlog` and its AST no-new-path-literal guard, and show it reads identity and status through the shared authorities. If DEFERRED: paste the ACTUAL refusal for a backlog selector, showing it names the gap, and confirm it does not silently no-op. Either way, paste the follow-on item id if one was filed.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the ACTUAL output of a `plan` action on a source that already has plans, showing the cluster report appearing BEFORE the action proceeds. Paste proof it INFORMS rather than refuses (the action continues). Paste a filesystem assertion that no run directory existed at the moment the report was emitted. Paste the call into child 01's view and a grep proving no cluster logic was duplicated.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste a `python3 -c` showing any new shared symbol resolves to the SAME object from `oc_runipd`, `agy_runipd` and `runner_shared`. Paste both hosts resolving the same spec selector identically. Paste the agy `--full-auto` default check explicitly, showing a widened `ACTION_IMPLEMENTED` cannot execute a plan the operator asked to merely graduate. Paste the AST-measured oc-to-agy import count before and after, showing it did not increase from 47.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste all six cases per host with actual runner output: approved spec resolves plus cluster report; no-`- Id:` spec refuses with an explanation; forbidden-status spec refuses; backlog selector per E-03; an unimplemented action still fails closed AND started no run; and the cluster report preceding any durable state. For the two refusal cases, assert on the FILESYSTEM that no run directory was created. Paste proof no test reads the live spec tree.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the five paths in `- Scope-Paths:`. Do NOT re-implement the `--action plan` refusal (F-1). Do NOT add a second spec enumeration (F-2, F-7). Do NOT widen `ACTION_IMPLEMENTED` beyond what is delivered (F-6). Do NOT turn child 01's advisory view into a gate. Do NOT duplicate its cluster logic. Do NOT mint an id6 into a spec as a side effect (OQ-02). Do NOT change `determine_action`, `action_for`, or any other legality rule. Do NOT add a symbol to `oc_runipd` for `agy_runipd` to import. Do NOT amend spec `25kzda` to match a partial implementation, and never its §4.2 finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. `oc_runipd.py` and `agy_runipd.py` are the highest-contention files in this repository and are being edited by live runs; measured, their line numbers moved roughly 70 and 95 lines in a single day. Find `discover_specs`, `discover_plans`, `enforce_requested_action`, `ACTION_IMPLEMENTED`, `ACTION_CHOICES`, `expand_selectors`, `describe_unresolved_plan_selector`, and the review sweep helper by name.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index and several pending Sets are editing these same two drivers. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved iuxtjy --by-human --message ...`) before execution, and child 01 (`jxxec8`) must read `executed` first, which the declared `- Item-Dependencies: executed:jxxec8` enforces. That order is the backlog item's own instruction, not an implementation detail. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, close backlog `6h7y2y`, which both children of this Set carry as `- From-Backlog:`; it closes HERE because the graduation path it describes becomes reachable here. BUT if OQ-01 defers the backlog half, set the item `graduated` rather than `done` and file the follow-on, so the unimplemented half is not silently dropped.

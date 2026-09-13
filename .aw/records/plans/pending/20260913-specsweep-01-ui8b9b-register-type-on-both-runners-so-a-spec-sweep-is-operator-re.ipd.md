# IPD: Register --type on both runners so a spec sweep is operator-reachable

- Date: 2026-09-13
- Kind: child
- Concern: CROSS-TYPE NEEDS-REVIEW DISCOVERY IS BUILT AND UNREACHABLE, so spec `6m4kow` R-15 is satisfied at the function boundary and by nothing an operator can type. MEASURED at HEAD `9697856e`: `runner_shared.sweep_review_candidates_for_type(repo, "spec")` returns exactly the four specs now at `to-review` (`6m4kow`, `2lcqno`, `6kwd2e`, `w15vzb`), and `grep '"--type"'` returns ZERO in both `oc_runipd.py` and `agy_runipd.py`, so `aw oc run reviews --type spec` is an unrecognized-argument error. The gap is deliberate and documented at the function's own definition ("An OPERATOR typing `--type spec` still cannot, because the flag does not exist yet. Reporting the latter as working would be the false claim this comment exists to prevent") and executed plan `uyeko5` excluded the flag by name.
  WHY THIS PLAN EXISTS RATHER THAN A NOTE IN THE SPEC: the maintainer ruled on 2026-09-13, during `6m4kow`'s spec review, that a release gate belongs on a PLAN and not on the spec, and that the spec's `- Blocks-Release:` is cleared once the plan carrying it is filed. This plan is that carrier. It inherits `- Blocks-Release: next` from `6m4kow`.
- Scope: Register `--type` on both host runners' `run` and `resume` parsers and thread it to the ALREADY-SHIPPED type-scoped sweep, so a spec awaiting review is reachable from the command line. IN: the flag on both hosts, its default (IPDs only, per spec `25kzda` 2.4a property 1), threading it to `sweep_review_candidates_for_type`, freezing it into run state per the resume rule, and the mixed-type gate becoming reachable for the first time. OUT: what a runner DOES with a selected spec once queued, which is the per-type dispatch table and is NOT this plan (see Deferred); multi-type SELECTION semantics beyond passing the operator's value through; any change to the sweep predicate or the dispatch table, both already correct.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_run_flag_surface.py, .aw/records/specs/20260904-6m4kow-01-6m4kow-cross-type-review.spec.md
- Item-Dependencies: none
- Status: to-review
- Set: specsweep
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: ui8b9b
- Priority: medium
- Work-Kind: feature
- Blocks-Release: next
- From-Spec: 6m4kow

## Workflow history

- 2026-09-13 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored during `/spec-review` of spec `6m4kow` to CARRY that spec's release gate, per the maintainer's ruling that a gate belongs on a plan rather than on a spec and that plans are preferred to backlog items. Every claim below was measured at HEAD `9697856e` rather than inherited from the spec: the sweep returning the four `to-review` specs, the zero `--type` registrations on both hosts, the flag's exclusion by executed plan `uyeko5`, the `DECLARED_BUT_NOT_OWNED_HERE` row that currently names it, and the fact that queueing a spec would reach plan-shaped code. THE SCOPE WAS CUT DOWN DURING AUTHORING, and the reason is the most important thing here: registering the flag is small, but making a selected spec actually RUN is the whole per-type dispatch table, so this plan delivers REACHABILITY and refuses to pretend it delivers execution. OQ-01 is BLOCKING and asks the maintainer to confirm that boundary is the one they want.
- 2026-09-13 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Let an operator type `aw oc run reviews --type spec` and have it select the specs awaiting review, closing the one requirement of spec `6m4kow` that is built but unreachable, without pretending the runner can yet EXECUTE a spec-review turn.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: register the flag and thread it

- [ ] E-01 REGISTER `--type` ON BOTH HOSTS' `run` AND `resume` PARSERS, through the SHARED flag table rather than twice. `runner_shared.py` already holds the run-flag surface for exactly this reason (executed plan `uyeko5` put it there so "the flags are wired ONCE into the shared shape rather than twice into two diverging parsers"), and that plan's own history records `--full-auto` having meant opt-in on one host and opt-out on the other because a gate was wired to one runner only. Accept the canonical type names the dispatch table already keys on (`run_selection_policy._TYPE_ACTIONS` registers `ipd`, `spec`, `backlog`, and the prompt/always-skip types are handled separately); REFUSE an unknown value with a message listing the accepted set, rather than silently sweeping nothing.
  THE DEFAULT IS NORMATIVE AND MUST NOT BE WIDENED: spec `25kzda` 2.4a property 1 fixes it as IPDs only with no `--type`, and `sweep_review_candidates_for_type` deliberately takes the type with NO default precisely so a later caller cannot widen the default sweep by omission. Registering the flag must not change what a bare `aw oc run reviews` selects.
  - Depends on: none
  - Expected outcome: `--type` parses on both hosts and both subcommands, appears in `--help`, and a bare invocation's selection is byte-identical to before.
  - Execution state: pending

- [ ] E-02 THREAD THE OPERATOR'S VALUE TO THE ALREADY-SHIPPED SWEEP, changing no policy. Both hosts' `expand_selectors` currently call `runner_shared.sweep_review_candidates(manifest, repo=repo)` for the `reviews`/`review`/`to-review` selectors (`oc_runipd.py:2276`, `agy_runipd.py:1569`); route them through `sweep_review_candidates_for_type(repo, <type>, manifest=manifest)`, which for `ipd` delegates to the existing function VERBATIM (same manifest walk, same Set ordering, same memoized decision) so no existing invocation's behavior moves. Do NOT reimplement membership: `run_selection_policy.needs_review` is the one predicate and it is already type-aware by signature.
  KEEP THE EMPTY-RESULT CONTRACT. An empty `reviews` is a SUCCESS that exits 0 (spec 2.4a property 3, carried by `EmptyStatusSelection`), and that must hold for `--type spec` too: a repository with no spec awaiting review is the healthy state, not an error.
  - Depends on: E-01
  - Expected outcome: `aw oc run reviews --type spec --dry-run` (or the nearest non-mutating spelling) selects the specs at `to-review`; `--type ipd` and a bare invocation select what they select today; an empty result exits 0.
  - Execution state: pending

- [ ] E-03 FREEZE THE VALUE INTO RUN STATE AND DECIDE `resume`'s BEHAVIOR EXPLICITLY. Spec `25kzda` freezes selection-affecting options into run state so a resume cannot silently re-scope a run, and `uyeko5` implemented that for the flags it owned while recording an honest divergence: only `--retry-budget` is refused on resume, because the shipped `--full-auto` resume handler OVERWRITES rather than refuses. Do NOT inherit that divergence by accident. Freeze `--type` at `run`, and on `resume` either refuse it or ignore it in favour of the frozen value, whichever the spec's rule requires; state WHICH in the plan record and pin it with a test. A resume that silently re-scopes the queue is the failure this item exists to prevent.
  - Depends on: E-02
  - Expected outcome: the frozen value is present in run state, and a `resume` passing a DIFFERENT `--type` behaves as the pinned rule says rather than re-scoping the queue.
  - Execution state: pending

### Task group 2: the gate this makes reachable, and the honest limit

- [ ] E-04 THE MIXED-TYPE GATE BECOMES LIVE FOR THE FIRST TIME, AND THAT IS A SAFETY CHANGE, NOT A SIDE EFFECT. `enforce_mixed_type_gate` is reached on every run today and correctly does not apply, because no invocation can produce a mixed selection; `uyeko5` proved the gate WIRED and CORRECT on a constructed classification while stating plainly that no live invocation could trigger it, and pinned that limit with `test_no_live_invocation_can_yet_produce_a_mixed_selection`. THAT TEST WILL NOW FAIL BY DESIGN, and it must be INVERTED rather than deleted: rewrite it to assert the gate is reachable and fires, keeping the invariant it actually defended. Then demonstrate the gate on a REAL invocation, refusing unattended without `--allow-mixed` and proceeding with it, which is evidence nobody has been able to produce before.
  - Depends on: E-02
  - Expected outcome: a real multi-type invocation is refused with the spec's `[RUN-MIXED-TYPES]` text and proceeds under `--allow-mixed`; the superseded limit test asserts reachability instead of unreachability.
  - Execution state: pending

- [ ] E-05 AMEND SPEC `6m4kow` AND CLEAR ITS RELEASE GATE, which is the record-keeping this plan exists to make honest. Record in that spec that R-15's operator surface is delivered here, update its Section 0 status table row and its Section 6 honest limit (both of which currently say an operator cannot reach the sweep), and clear its `- Blocks-Release:` with `aw specs set ... --blocks-release -` now that THIS plan carries the gate. DO NOT hand-edit the spec's `- Status:` or its `## Workflow history`: both are tool-owned, a `status_untooled_gate` hook exists for that bypass, and this plan's own author is not the spec's approver. Use `aw specs note` for the amendment record.
  THE ORDERING IS NOT OPTIONAL: the gate moves to this plan when this plan is FILED (it already carries `- Blocks-Release: next`), and the spec's field is cleared as part of THIS item, so at no point is the gate carried by neither artifact.
  - Depends on: E-04
  - Expected outcome: `6m4kow` no longer carries `- Blocks-Release:`, this plan does, `aw check` reports no dangling or mismatched gate, and the spec's status/history were written only by the setters.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE FLAG SURFACE IS SHARED ON PURPOSE. `runner_shared.py` holds the run-flag table because `uyeko5`'s sequencing rationale was to wire flags ONCE rather than twice into two diverging parsers. Its own history records the measured cost of the alternative: `--full-auto` defaulted opt-in on one host and opt-out on the other, at three sites each.
- `--type` IS ALREADY DECLARED-BUT-NOT-OWNED, so there is a registry to update rather than a blank field. `uyeko5` put `--type` in `DECLARED_BUT_NOT_OWNED_HERE` with a named reason and owner, and `test_every_flag_the_spec_declares_is_accounted_for` fails on `declared - owned - excluded`. Taking ownership means moving the row, not adding a second one.
- THE SWEEP AND THE DISPATCH TABLE AGREE BY CONSTRUCTION, and must keep doing so. `sweep_review_candidates_for_type` asks the SAME `run_selection_policy.needs_review` for a spec that it does for a plan, which is the property `6m4kow` R-16 requires. Any new membership test here would recreate the divergence `6ypimw` deleted (two verbatim `_needs_review` closures, one of which tested `status == "to-review"` while the table routed `draft` to review as well).
- A SPEC WITH NO `- Id:` IS DELIBERATELY SKIPPED by `discover_specs`, and that skip is measured safe rather than assumed: 19 of 32 spec files carry no id6, every one a grandfathered pre-cutover legacy name, and all sit at statuses the predicate answers False for. Do not "fix" the skip.
- AN EMPTY STATUS SWEEP IS A SUCCESS. `EmptyStatusSelection` exists so `reviews` exits 0 on an empty result while a misspelled id6 still exits 2. A `--type spec` sweep must inherit that, not raise.
- THE SPEC'S OWN STATUS AND HISTORY ARE TOOL-OWNED (`aw specs set` / `aw specs note`), enforced by a hook, and `- Readiness:` is never written onto a spec at all.

## Findings

| ID | Severity | Evidence | Finding |
|---|---|---|---|
| F-1 | HIGH | `sweep_review_candidates_for_type(repo, "spec")` -> `['6m4kow', '2lcqno', '6kwd2e', 'w15vzb']`; `grep -c '"--type"'` -> 0 in both `oc_runipd.py` and `agy_runipd.py` | THE CAPABILITY IS COMPLETE AND UNREACHABLE. The sweep resolves real specs; no operator input can supply the type. This is the entire gap between `6m4kow` R-15 as built and R-15 as usable. |
| F-2 | HIGH | `run_selection_policy._SPEC_ACTIONS`: `to-review` -> review, `approved` -> plan, `implementing` absent, `implemented`/`deferred`/`parked`/`superseded` -> skip | SELECTING A SPEC IS NOT RUNNING ONE, and the dispatch table proves the second half is much bigger. A selected spec at `approved` routes to `plan` (author IPDs from it) and at `implementing` has no row at all because it dispatches children. None of that exists. This is why E-02 stops at selection and why OQ-01 is blocking. |
| F-3 | HIGH | `oc_runipd.py:2959` writes `"configured_file": plan["file"]`; `resolve_plan_path` resolves against the plans tree; `build_dynamic_manifest` compiles only discovered PLANS | THE QUEUE ENTRY IS PLAN-SHAPED, so a queued spec would reach code that assumes a plan. A queue item carries plan fields and its path is resolved as a plan. Registering the flag makes SELECTION correct; anything past selection needs the manifest to admit a non-plan artifact, which this plan does not do. An executor must not assume `--type spec` yields a working review turn. |
| F-4 | MEDIUM | `uyeko5` `test_no_live_invocation_can_yet_produce_a_mixed_selection`, pinned deliberately "so registering `--type` later fails here rather than silently outgrowing it" | A TEST WILL FAIL BY DESIGN, AND THE PREVIOUS AUTHOR ARRANGED THAT ON PURPOSE. It must be INVERTED (assert reachability, keep the defended invariant), never deleted. A failing pin is the handoff signal working, not breakage. |
| F-5 | MEDIUM | `uyeko5`'s recorded divergence: only `--retry-budget` is refused on resume, because the shipped `--full-auto` resume handler overwrites the frozen option | THE RESUME RULE IS ALREADY INCONSISTENT IN THE SHIPPED CODE, so E-03 must decide `--type`'s behavior explicitly rather than copying a neighbour. Copying `--full-auto` would let a resume re-scope the queue silently. |
| F-6 | LOW | `aw find specs --status` returns all 32 specs for `to-review`, `implemented`, and an invalid `bogusvalue` alike, at exit 0; root cause `cli._find_type_records`'s "All other types" branch never consults `explicit_flags.status` | A NEIGHBOURING DISCOVERY SURFACE IS BROKEN AND UNTRACKED. It affects seven record types, `5slbpi` avoided it deliberately rather than fixing it, and no backlog item covers it. Out of scope here (this plan must not depend on it, and does not), but recorded because anyone touching spec discovery will meet it. |

## Proposed changes (ordered, validatable)

1. Register `--type` once in the shared flag surface, on both hosts and both subcommands, refusing an unknown value (E-01).
2. Route both hosts' review sweep through the type-scoped entry point, preserving the IPD default and the empty-is-success contract (E-02).
3. Freeze the value into run state and pin an explicit `resume` rule (E-03).
4. Invert the unreachability pin and demonstrate the mixed-type gate on a real invocation (E-04).
5. Amend spec `6m4kow` and move its release gate onto this plan (E-05).

## Deferred / out of scope (with reason)

- WHAT A RUNNER DOES WITH A SELECTED SPEC. The per-type dispatch table (spec `25kzda` Section 3) is the work, not a flag: it needs the manifest to admit a non-plan artifact, a queue entry that is not plan-shaped (F-3), and a per-status action for `approved` (author IPDs) and `implementing` (dispatch children) that does not exist. Excluded so this plan delivers a provable, bounded thing. OQ-01 asks the maintainer to confirm that is the boundary they want before execution.
- MULTI-TYPE SELECTION SEMANTICS beyond passing the operator's value through and letting the shipped gate judge it. `25kzda` 2.2/2.3 owns them.
- FIXING `aw find specs --status` (F-6). Seven record types, a `cli.py` change, and no dependency from this plan.
- ANY CHANGE TO `needs_review` OR THE DISPATCH TABLE. Both are already correct for specs; touching them would recreate the divergence `6ypimw` removed.

## Scope check

- Over-scope: none. The spec file is in `Scope-Paths` because E-05 amends it, which is what makes the amendment visible to the runner's declared-spec-edit announcement and the finalize scope gate.
- Under-scope: DELIBERATE AND NAMED. This plan makes a spec sweep SELECTABLE, not EXECUTABLE (F-2, F-3). A reader who expects `aw oc run reviews --type spec` to review specs end to end after this plan will be wrong, and E-02's validation must state the limit rather than imply the capability.

## Required tests / validation

Run the suite BARE (`python3 -m pytest`) and paste the actual summary line; the configured `addopts` already supply quiet, parallel, fast-subset behavior.

- The flag surface contract suite (`tests/test_run_flag_surface.py`), which asserts the two HOSTS agree and which owns the `DECLARED_BUT_NOT_OWNED_HERE` accounting E-01 changes.
- A test that a bare `reviews` selection is UNCHANGED, which is the regression that matters most: the normative default must not widen.
- A test that `--type spec` selects the specs at `to-review` and that an empty result exits 0.
- The inverted mixed-type reachability test (E-04), plus the real-invocation refusal and `--allow-mixed` proceed.
- The `resume` rule pinned either way (E-03).
- `aw check` no-worse-than-baseline with both counts pasted, and `aw sanitize --agent` clean.

## Spec / documentation sync

Spec `6m4kow` is AMENDED by E-05: its Section 0 status table row for R-15, its Section 6 honest limit, and its `- Blocks-Release:` field. The spec file is declared in `Scope-Paths` for that reason. The amendment's reason is recorded in the spec's own text and history, not only here. No other spec changes: `25kzda` still owns the flag's grammar and the dispatch table, and this plan implements a subset of what that spec declares rather than amending it.

## Open questions

### OQ-01: Is REACHABLE-BUT-NOT-EXECUTABLE the right boundary for closing R-15 and the release gate?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: ASKED AND ANSWERED BY THE MAINTAINER, 2026-09-13. THE QUESTION was whether `aw oc run reviews --type spec` SELECTING the specs is enough to consider `6m4kow` R-15 delivered and 2.0.0 unblocked, or whether the gate should stay until a spec-review turn actually RUNS. It needed a human because the facts were settled and measured (F-2, F-3) while the judgement was one of scope and release risk, and the two readings differ in size by roughly an order of magnitude.
  THE RULING: **selection now, AND the execution half is filed as its own release blocker too.** So this plan proceeds exactly as scoped, and it does NOT reduce 2.0.0's blocker count: plan `mng63x` (`specdispatch` Order 01) carries the execution half with its own `- Blocks-Release: next`. Nothing is lost by clearing the gate from the spec, because two plans now carry between them what the spec carried alone.
  THE MAINTAINER ADDED A SECOND INSTRUCTION, recorded here because it constrains the sibling rather than this plan: **HOW execution is implemented needs DISCUSSION, and that fact must be captured loudly.** `mng63x` is therefore filed as a DESIGN-FIRST blocker whose own blocking question is the design itself; it must not be executed as though the approach were settled. See that plan's OQ-01.
  CONSEQUENCE FOR THIS PLAN: unchanged scope, and V-02's obligation to state the executability limit plainly is now doubly load-bearing, since the limit is what the sibling blocker exists to close.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `--help` from BOTH hosts and BOTH subcommands showing `--type`; paste the refusal for an unknown value with its listed accepted set; paste the flag-surface suite passing, including the accounting assertion that fails on `declared - owned - excluded`, proving the row was MOVED rather than duplicated. Then paste a bare `aw oc run reviews` selection before and after the change and show it IDENTICAL, because the normative default not widening is the load-bearing half of this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the selection for `--type spec` (expect the specs at `to-review`, re-derived at execution rather than compared against this plan's four ids, since the population moves), for `--type ipd`, and for a bare invocation, on BOTH hosts. Paste an empty `--type spec` case exiting 0. Paste a grep showing no second membership test was added and that both hosts reach the SAME shared function. THEN STATE PLAINLY, as a limitation and not a success, that a selected spec cannot yet be EXECUTED (F-2, F-3): a validation that omits this reads as a shipped capability.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the frozen value in run state, and paste a `resume` passing a DIFFERENT `--type` showing the pinned behavior (refusal or frozen-value-wins), plus the test that pins it. State which rule was chosen and why, citing the spec line, since `uyeko5` recorded a shipped divergence here and copying a neighbour silently would reproduce it.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the mixed-type gate REFUSING a real invocation with the `[RUN-MIXED-TYPES]` text and PROCEEDING under `--allow-mixed`, with `gate_applied=True`. A verdict carrying `gate_applied=False` does NOT satisfy this item: that is the single-type short circuit and is what a still-unreachable gate would also return. Paste the inverted limit test and show it asserts reachability while keeping the invariant it defended; a DELETED test does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `6m4kow`'s front matter showing no `- Blocks-Release:`, this plan's showing it present, and `aw check` reporting no dangling or mismatched gate. Paste the spec's amended Section 0 row and Section 6 limit. Paste a `git diff` proving the spec's `- Status:` line is byte-unchanged and that its history was written by `aw specs note` rather than by hand. Confirm the gate was carried by this plan BEFORE the spec's field was cleared, so it was never carried by neither.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files this plan changed, path-scoped, never `git add -A`, never push. Paste ACTUAL runner output for every test claim; run the suite bare. This plan AMENDS A SPEC, so that spec file is declared in `Scope-Paths` and the amendment's reason is recorded in the spec's own text, not only here. DO NOT hand-write another role's attestation: this plan's `- Readiness:` is `/plan-review`'s output and is deliberately absent, its `- Approval:` is the human's, and the amended spec's `- Status:` belongs to `aw specs set`.

BLOCKING QUESTION FIRST: OQ-01 asks whether reachable-but-not-executable is the right boundary for clearing a release gate. It is `- Blocking: yes` and unresolved, so this plan is not executable until the maintainer answers. If the answer is that execution is required, SUPERSEDE this plan with a Set rather than widening it.

Post-gate lifecycle: on completion, run `aw ipd lint --phase pre-transition`, verify every `V-*` with pasted evidence, then move this file to `.aw/records/plans/executed/` with a path-scoped lifecycle commit.

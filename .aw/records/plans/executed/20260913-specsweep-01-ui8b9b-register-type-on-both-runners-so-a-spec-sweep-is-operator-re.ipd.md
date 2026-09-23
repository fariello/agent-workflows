# IPD: Register --type on both runners so a spec sweep is operator-reachable

- Date: 2026-09-13
- Kind: child
- Concern: CROSS-TYPE NEEDS-REVIEW DISCOVERY IS BUILT AND UNREACHABLE, so spec `6m4kow` R-15 is satisfied at the function boundary and by nothing an operator can type. MEASURED at HEAD `9697856e`: `runner_shared.sweep_review_candidates_for_type(repo, "spec")` returned exactly the four specs then at `to-review` (`6m4kow`, `2lcqno`, `6kwd2e`, `w15vzb`), and `grep '"--type"'` returns ZERO in both `oc_runipd.py` and `agy_runipd.py`, so `aw oc run reviews --type spec` is an unrecognized-argument error. THE POPULATION FIGURE IS ALREADY STALE, corrected at review and left visible rather than quietly rewritten: at HEAD `2674c250` that same call returns `[]`, because the spec-review round that authored this plan advanced all four specs to `approved`, and no spec sits at `to-review` anywhere in the repository. THE UNREACHABILITY CLAIM, which is this plan's whole reason to exist, was RE-VERIFIED and is unchanged: zero `--type` registrations on either host. What the staleness changes is the VALIDATION, not the premise (see F-7 and E-02). The gap is deliberate and documented at the function's own definition ("An OPERATOR typing `--type spec` still cannot, because the flag does not exist yet. Reporting the latter as working would be the false claim this comment exists to prevent") and executed plan `uyeko5` excluded the flag by name.
  WHY THIS PLAN EXISTS RATHER THAN A NOTE IN THE SPEC: the maintainer ruled on 2026-09-13, during `6m4kow`'s spec review, that a release gate belongs on a PLAN and not on the spec, and that the spec's `- Blocks-Release:` is cleared once the plan carrying it is filed. This plan is that carrier. It inherits `- Blocks-Release: next` from `6m4kow`.
- Scope: Register `--type` on both host runners' `run` and `resume` parsers and thread it to the ALREADY-SHIPPED type-scoped sweep, so a spec awaiting review is reachable from the command line. IN: the flag on both hosts, its default (IPDs only, per spec `25kzda` 2.4a property 1), threading it to `sweep_review_candidates_for_type`, freezing it into run state per the resume rule, and the mixed-type gate becoming reachable for the first time. OUT: what a runner DOES with a selected spec once queued, which is the per-type dispatch table and is NOT this plan (see Deferred); multi-type SELECTION semantics beyond passing the operator's value through; any change to the sweep predicate or the dispatch table, both already correct.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_run_flag_surface.py, .aw/records/specs/20260904-6m4kow-01-6m4kow-cross-type-review.spec.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
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
- 2026-09-23 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: ui8b9b verified (set specsweep, attempt 1). [Scope reconciliation - out-of-scope tests/test_rununify_build_parser.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_rununify_initialize_run.py: changed by the plan's approved execution (auto-reconciled by aw oc run)]
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-13 reviewed (opencode (its_direct/pt3-claude-opus-5-1m-us)): /plan-review ROUND 1: APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. PR-701..PR-704, all FIXED, no open questions. The premise re-verified and holds: zero --type registrations on either host, so the capability is built and unreachable. Four corrections, each measured at HEAD 2674c250: F-7 the headline population went stale within hours (the sweep now returns [] because the same spec-review round that authored this plan advanced all four specs to approved, and NO spec is at to-review repo-wide), so E-02's positive case must use a fixture and must not be manufactured by moving a real spec's status; F-8 the gate paragraph asserted OQ-01 was 'Blocking: yes and unresolved' while its fields read Blocking: no / resolved, so the plan refused itself while the linter and a runner would dispatch it; F-9 half of E-05 is already done (6m4kow carries no Blocks-Release and its history records the clearing in b16e1108), so its evidence as written was unobtainable and the item is re-aimed at the two genuinely stale assertions; F-10 E-01 named a 'run' subparser that does not exist (both hosts expose start/resume). No product code changed.

- 2026-09-13 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored during `/spec-review` of spec `6m4kow` to CARRY that spec's release gate, per the maintainer's ruling that a gate belongs on a plan rather than on a spec and that plans are preferred to backlog items. Every claim below was measured at HEAD `9697856e` rather than inherited from the spec: the sweep returning the four `to-review` specs, the zero `--type` registrations on both hosts, the flag's exclusion by executed plan `uyeko5`, the `DECLARED_BUT_NOT_OWNED_HERE` row that currently names it, and the fact that queueing a spec would reach plan-shaped code. THE SCOPE WAS CUT DOWN DURING AUTHORING, and the reason is the most important thing here: registering the flag is small, but making a selected spec actually RUN is the whole per-type dispatch table, so this plan delivers REACHABILITY and refuses to pretend it delivers execution. OQ-01 is BLOCKING and asks the maintainer to confirm that boundary is the one they want.
- 2026-09-13 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Let an operator type `aw oc run reviews --type spec` and have it select the specs awaiting review, closing the one requirement of spec `6m4kow` that is built but unreachable, without pretending the runner can yet EXECUTE a spec-review turn.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: register the flag and thread it

- [x] E-01 REGISTER `--type` ON BOTH HOSTS' `start` AND `resume` PARSERS, through the SHARED flag table rather than twice. `runner_shared.py` already holds the run-flag surface for exactly this reason (executed plan `uyeko5` put it there so "the flags are wired ONCE into the shared shape rather than twice into two diverging parsers"), and that plan's own history records `--full-auto` having meant opt-in on one host and opt-out on the other because a gate was wired to one runner only. Accept the canonical type names the dispatch table already keys on (`run_selection_policy._TYPE_ACTIONS` registers `ipd`, `spec`, `backlog`, and the prompt/always-skip types are handled separately); REFUSE an unknown value with a message listing the accepted set, rather than silently sweeping nothing.
  THE DEFAULT IS NORMATIVE AND MUST NOT BE WIDENED: spec `25kzda` 2.4a property 1 fixes it as IPDs only with no `--type`, and `sweep_review_candidates_for_type` deliberately takes the type with NO default precisely so a later caller cannot widen the default sweep by omission. Registering the flag must not change what a bare `aw oc run reviews` selects.
  THE SUBCOMMAND NAME WAS CORRECTED AT REVIEW (PR-704, F-10). This item originally said "`run` AND `resume`", and there is NO `run` subparser on either host: both expose exactly `['report', 'resume', 'start', 'status', 'stop']`. The operator-facing spelling `aw oc run reviews` reaches the `start` parser through the CLI wrapper, which is why the plan's command-line prose is right while its parser instruction was wrong. The shipped pin test already keys on the correct pair (`for sub in ("start", "resume")`, `tests/test_run_flag_surface.py:464`), so an executor registering on a `run` parser would satisfy neither the flag nor the test.
  - Depends on: none
  - Expected outcome: `--type` parses on both hosts' `start` and `resume` subparsers, appears in `--help`, and a bare invocation's selection is byte-identical to before.
  - Execution state: performed

- [x] E-02 THREAD THE OPERATOR'S VALUE TO THE ALREADY-SHIPPED SWEEP, changing no policy. Both hosts' `expand_selectors` currently call `runner_shared.sweep_review_candidates(manifest, repo=repo)` for the `reviews`/`review`/`to-review` selectors (`oc_runipd.py:2276`, `agy_runipd.py:1569`); route them through `sweep_review_candidates_for_type(repo, <type>, manifest=manifest)`, which for `ipd` delegates to the existing function VERBATIM (same manifest walk, same Set ordering, same memoized decision) so no existing invocation's behavior moves. Do NOT reimplement membership: `run_selection_policy.needs_review` is the one predicate and it is already type-aware by signature.
  KEEP THE EMPTY-RESULT CONTRACT. An empty `reviews` is a SUCCESS that exits 0 (spec 2.4a property 3, carried by `EmptyStatusSelection`), and that must hold for `--type spec` too: a repository with no spec awaiting review is the healthy state, not an error.
  THE LIVE POPULATION IS NOW ZERO, SO THE ACCEPTANCE TEST MUST USE A FIXTURE (PR-701, F-7). MEASURED AT REVIEW at HEAD `2674c250`: `sweep_review_candidates_for_type(repo, "spec")` returns `[]`, NOT the four specs the Concern and F-1 claim. All four (`6m4kow`, `2lcqno`, `6kwd2e`, `w15vzb`) were advanced `to-review` -> `approved` by the same spec-review round that authored this plan, and `needs_review('spec','approved')` is False, so they are correctly no longer swept. Verified further that ZERO specs sit at `to-review` anywhere in the repository (`grep -l '^- Status: to-review' .aw/records/specs/*.spec.md` returns nothing; the 14 discovered id6-carrying specs are 11 `approved`, 1 `superseded`, 1 `draft`, 1 `implementing`). CONSEQUENCE: the positive half of this item cannot be demonstrated against the live tree at all. Build a FIXTURE spec at `to-review` and assert the sweep returns it; do NOT advance a real spec's status to create a population, which would be a tooled lifecycle change made to satisfy a test. Note the empty-result contract is now the case the LIVE tree exercises, which makes that half easy and the positive half fixture-only.
  - Depends on: E-01
  - Expected outcome: with a FIXTURE spec at `to-review`, `aw oc run reviews --type spec` (dry-run or nearest non-mutating spelling) selects it; `--type ipd` and a bare invocation select what they select today; an empty result exits 0, which is what the live tree returns.
  - Execution state: performed

- [x] E-03 FREEZE THE VALUE INTO RUN STATE AND DECIDE `resume`'s BEHAVIOR EXPLICITLY. Spec `25kzda` freezes selection-affecting options into run state so a resume cannot silently re-scope a run, and `uyeko5` implemented that for the flags it owned while recording an honest divergence: only `--retry-budget` is refused on resume, because the shipped `--full-auto` resume handler OVERWRITES rather than refuses. Do NOT inherit that divergence by accident. Freeze `--type` at `run`, and on `resume` either refuse it or ignore it in favour of the frozen value, whichever the spec's rule requires; state WHICH in the plan record and pin it with a test. A resume that silently re-scopes the queue is the failure this item exists to prevent.
  - Depends on: E-02
  - Expected outcome: the frozen value is present in run state, and a `resume` passing a DIFFERENT `--type` behaves as the pinned rule says rather than re-scoping the queue.
  - Execution state: performed

### Task group 2: the gate this makes reachable, and the honest limit

- [x] E-04 THE MIXED-TYPE GATE BECOMES LIVE FOR THE FIRST TIME, AND THAT IS A SAFETY CHANGE, NOT A SIDE EFFECT. `enforce_mixed_type_gate` is reached on every run today and correctly does not apply, because no invocation can produce a mixed selection; `uyeko5` proved the gate WIRED and CORRECT on a constructed classification while stating plainly that no live invocation could trigger it, and pinned that limit with `test_no_live_invocation_can_yet_produce_a_mixed_selection`. THAT TEST WILL NOW FAIL BY DESIGN, and it must be INVERTED rather than deleted: rewrite it to assert the gate is reachable and fires, keeping the invariant it actually defended. Then demonstrate the gate on a REAL invocation, refusing unattended without `--allow-mixed` and proceeding with it, which is evidence nobody has been able to produce before.
  - Depends on: E-02
  - Expected outcome: a real multi-type invocation is refused with the spec's `[RUN-MIXED-TYPES]` text and proceeds under `--allow-mixed`; the superseded limit test asserts reachability instead of unreachability.
  - Execution state: performed

- [x] E-05 AMEND SPEC `6m4kow` AND CLEAR ITS RELEASE GATE, which is the record-keeping this plan exists to make honest. Record in that spec that R-15's operator surface is delivered here, update its Section 0 status table row and its Section 6 honest limit (both of which currently say an operator cannot reach the sweep), and clear its `- Blocks-Release:` with `aw specs set ... --blocks-release -` now that THIS plan carries the gate. DO NOT hand-edit the spec's `- Status:` or its `## Workflow history`: both are tool-owned, a `status_untooled_gate` hook exists for that bypass, and this plan's own author is not the spec's approver. Use `aw specs note` for the amendment record.
  THE ORDERING IS NOT OPTIONAL: the gate moves to this plan when this plan is FILED (it already carries `- Blocks-Release: next`), and the spec's field is cleared as part of THIS item, so at no point is the gate carried by neither artifact.
  THE GATE IS ALREADY CLEARED, SO HALF THIS ITEM IS A NO-OP AND MUST NOT BE RE-PERFORMED (PR-703, F-9). MEASURED AT REVIEW: `6m4kow`'s front matter carries NO `- Blocks-Release:` line at all, and its own workflow history records "this spec's gate is cleared in this same call" as part of commit `b16e1108`, the same spec-review round that filed this plan. So the clearing happened at authoring time, not at execution time, and the ordering worry this item raises was already discharged by the filing order the history describes. `aw check` was verified CLEAN on these gates at review (zero diagnostics mentioning `ui8b9b`, `mng63x` or `6m4kow`, and zero `blocks-release`/`from-spec` rule hits). DO NOT run `aw specs set ... --blocks-release -` again: the field is absent, and a setter call against an absent field is at best a no-op and at worst writes a spurious history line onto an approved spec this plan's author is not the approver of.
  WHAT REMAINS GENUINELY UNDONE, and it is the part worth doing: the spec's Section 0 status row for R-15 still reads "IMPLEMENTED AT THE FUNCTION BOUNDARY, NOT OPERATOR-REACHABLE" with the evidence "`--type` is registered on NEITHER host" (`:40`), and Section 6's honest limit says the same. Those become FALSE when E-01 lands and are this item's real deliverable. NOTE THAT ROW ALSO CARRIES A NOW-STALE MEASUREMENT of its own: it says the sweep "returns the four `to-review` specs", which F-7 measures as `[]` today. Correct that too rather than leaving a second stale claim behind, and phrase the replacement so it does not rot again (describe the PREDICATE, not a frozen population).
  - Depends on: E-04
  - Expected outcome: `6m4kow`'s Section 0 R-15 row and Section 6 limit describe an operator-reachable sweep, its stale four-spec population claim is replaced by a non-rotting phrasing, the gate remains absent from the spec and present on this plan, `aw check` still reports no dangling or mismatched gate, and the spec's `- Status:`/history were not hand-edited.
  - Execution state: performed

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
| F-1 | HIGH | `grep -c '"--type"'` -> 0 in both `oc_runipd.py` and `agy_runipd.py`, RE-VERIFIED at review; the sweep function exists and is type-scoped by signature | THE CAPABILITY IS COMPLETE AND UNREACHABLE. The sweep resolves specs by asking the shipped predicate; no operator input can supply the type. This is the entire gap between `6m4kow` R-15 as built and R-15 as usable. THE POPULATION HALF OF THIS ROW IS STALE AND IS CORRECTED BY F-7: at authoring the sweep returned `['6m4kow','2lcqno','6kwd2e','w15vzb']`, and at review it returns `[]`, because the same spec-review round that authored this plan advanced all four to `approved`. The UNREACHABILITY claim (the point of this row) is unchanged and was re-verified; only the illustrative population moved. Do not cite the four ids at execution time: re-derive, and expect an empty live result. |
| F-2 | HIGH | `run_selection_policy._SPEC_ACTIONS`: `to-review` -> review, `approved` -> plan, `implementing` absent, `implemented`/`deferred`/`parked`/`superseded` -> skip | SELECTING A SPEC IS NOT RUNNING ONE, and the dispatch table proves the second half is much bigger. A selected spec at `approved` routes to `plan` (author IPDs from it) and at `implementing` has no row at all because it dispatches children. None of that exists. This is why E-02 stops at selection and why OQ-01 is blocking. |
| F-3 | HIGH | `oc_runipd.py:2959` writes `"configured_file": plan["file"]`; `resolve_plan_path` resolves against the plans tree; `build_dynamic_manifest` compiles only discovered PLANS | THE QUEUE ENTRY IS PLAN-SHAPED, so a queued spec would reach code that assumes a plan. A queue item carries plan fields and its path is resolved as a plan. Registering the flag makes SELECTION correct; anything past selection needs the manifest to admit a non-plan artifact, which this plan does not do. An executor must not assume `--type spec` yields a working review turn. |
| F-4 | MEDIUM | `uyeko5` `test_no_live_invocation_can_yet_produce_a_mixed_selection`, pinned deliberately "so registering `--type` later fails here rather than silently outgrowing it" | A TEST WILL FAIL BY DESIGN, AND THE PREVIOUS AUTHOR ARRANGED THAT ON PURPOSE. It must be INVERTED (assert reachability, keep the defended invariant), never deleted. A failing pin is the handoff signal working, not breakage. |
| F-5 | MEDIUM | `uyeko5`'s recorded divergence: only `--retry-budget` is refused on resume, because the shipped `--full-auto` resume handler overwrites the frozen option | THE RESUME RULE IS ALREADY INCONSISTENT IN THE SHIPPED CODE, so E-03 must decide `--type`'s behavior explicitly rather than copying a neighbour. Copying `--full-auto` would let a resume re-scope the queue silently. |
| F-6 | LOW | `aw find specs --status` returns all 32 specs for `to-review`, `implemented`, and an invalid `bogusvalue` alike, at exit 0; root cause `cli._find_type_records`'s "All other types" branch never consults `explicit_flags.status` | A NEIGHBOURING DISCOVERY SURFACE IS BROKEN AND UNTRACKED. It affects seven record types, `5slbpi` avoided it deliberately rather than fixing it, and no backlog item covers it. Out of scope here (this plan must not depend on it, and does not), but recorded because anyone touching spec discovery will meet it. RE-VERIFIED AT REVIEW and still broken: `--status to-review` and `--status bogusvalue` both return 33 lines at exit 0, and the `to-review` output visibly lists `approved` specs. The count moved 32 -> 33, which is itself a reminder not to trust a frozen population figure (see F-7). |
| F-7 | HIGH | measured at review at HEAD `2674c250`: `sweep_review_candidates_for_type(repo, "spec")` -> `[]`; all four named specs now `- Status: approved`; `needs_review('spec','approved')` False; zero specs at `to-review` repo-wide; 14 discovered specs are 11 `approved` + 1 `superseded` + 1 `draft` + 1 `implementing` | THE PLAN'S HEADLINE MEASUREMENT WENT STALE WITHIN HOURS AND ITS ACCEPTANCE TEST IS NOW UNOBTAINABLE FROM THE LIVE TREE. The Concern, Goal and F-1 all rest on the sweep returning `6m4kow`, `2lcqno`, `6kwd2e`, `w15vzb`; the same spec-review round that authored this plan advanced all four `to-review` -> `approved`, so the sweep correctly returns nothing and NO spec anywhere is at `to-review`. The capability claim (built but unreachable) is UNAFFECTED and still true, which is why this is a validation defect rather than a premise collapse. But E-02's positive case must now use a FIXTURE spec, and it must NOT be created by advancing a real spec's status to manufacture a population. Note the live tree now exercises the empty-result contract by default, which inverts which half of E-02 is easy. | measured at review by calling the shipped function, reading all four specs' front matter, evaluating the predicate at `approved`, and grepping the whole specs tree for `to-review` |
| F-8 | HIGH | the gate paragraph said OQ-01 "is `- Blocking: yes` and unresolved"; OQ-01's fields read `- Blocking: no` / `- Status: resolved` with the maintainer's 2026-09-13 ruling recorded in full; `aw ipd lint --phase author` reports conforming | THE PLAN CONTRADICTED ITSELF ABOUT WHETHER IT MAY BE EXECUTED, AND THE TWO READERS DISAGREE. A human executor reading the gate would stop; the linter and a runner read the FIELDS, find no blocking-open question, and would dispatch it. That is worse than either answer alone, because the outcome depends on which reader acts. The fields are right and the prose was stale, so the prose was corrected. The conditional instruction to supersede this plan with a Set is likewise void, since it was contingent on an answer that was not given. | verified at review by comparing the gate paragraph against OQ-01's own fields and against the linter's disposition |
| F-9 | MEDIUM | `6m4kow` front matter has NO `- Blocks-Release:` line; its history records "this spec's gate is cleared in this same call" (commit `b16e1108`); `aw check` clean on all three artifacts; `mng63x` present in `pending/` carrying the gate | HALF OF E-05 IS ALREADY DONE, SO ITS EVIDENCE AS WRITTEN CANNOT BE PRODUCED BY EXECUTING IT. The gate was cleared from the spec at AUTHORING time by the same spec-review round that filed this plan, not at execution time. So `aw specs set ... --blocks-release -` would act on an absent field, and the ordering worry E-05 raises was already discharged. What genuinely remains is the spec's Section 0 R-15 row (`:40`) and Section 6 limit, which still assert `--type` is registered on neither host and which E-01 falsifies. That row ALSO carries its own stale claim that the sweep "returns the four `to-review` specs", which F-7 measures as `[]`, so it needs two corrections and a non-rotting phrasing. | verified at review by reading `6m4kow`'s front matter and history, running `aw check --agent` and filtering its diagnostics, and locating the sibling plan |
| F-10 | MEDIUM | both hosts' subparsers are exactly `['report', 'resume', 'start', 'status', 'stop']`; the shipped pin test iterates `("start", "resume")` (`tests/test_run_flag_surface.py:464`) | E-01 NAMED A SUBCOMMAND THAT DOES NOT EXIST. It said to register on the `run` and `resume` parsers; there is no `run` subparser on either host. The operator spelling `aw oc run reviews` reaches `start` through the CLI wrapper, which is why the plan's command-line prose is right while its parser instruction is wrong. An executor following it literally would register nothing the pin test can see. | measured at review by walking both hosts' `build_parser()` for their `_SubParsersAction` choices |

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
- Under-scope, ADDED AT REVIEW: E-02 now needs a FIXTURE spec at `to-review` (F-7), which means a test file gains a fixture rather than reading the live tree. `tests/test_run_flag_surface.py` is already declared and already builds a real multi-type path set including a spec (`multi_type_paths`, `:329-333`), so the fixture machinery exists there and no new `Scope-Paths` entry is required. Reuse it rather than writing a second spec-fixture helper.
- SCOPE NOTE ON THE DECLARED SPEC FILE, verified at review: `.aw/records/specs/...6m4kow...spec.md` stays declared and IS still modified by E-05, because the Section 0 row and Section 6 limit remain genuinely stale even though the gate half is already done (F-9). So no `--scope-ack` is expected for it. If an executor finds nothing left to change there, that is a signal to re-read F-9 rather than to acknowledge an unmodified path. CONFIRMED AT EXECUTION: every one of the five declared paths was modified, so NO `--scope-ack` was needed for any of them.
- OUT-OF-SCOPE PATHS CHANGED AT EXECUTION (two), declared here rather than left for the finalize gate to discover. `aw check` reports the expected `check.scope-drift` naming exactly these, and each is a SHIPPED PINNED-COUNT TEST that measures the operator-visible flag surface and therefore FAILS BY DESIGN when a flag is added. Re-basing a pin is what its own failure message instructs ("If this change is intended, update EXPECTED_OPTION_STRINGS in the SAME change and say why"):
  - `tests/test_rununify_build_parser.py`: `LIVE_PARTITION` shared count 56 -> 57, `POLICY_FLAG_ROWS` 14 -> 15, `LIVE_STRINGS_FROM_POLICY_TABLE` 23 -> 24, and `--type` added to all FOUR `start`/`resume` rows of `EXPECTED_OPTION_STRINGS`. Every number rose by exactly ONE and the HOST-SPECIFIC counts did not move, which is the property those pins exist to police: the flag reached both hosts because one shared table declares it.
  - `tests/test_rununify_initialize_run.py`: `SHARED_OPTION_KEYS` gained `types` and `LIVE_OPTION_KEY_UNION` 36 -> 37, again through the one shared `freeze_run_policy_flags` expansion with the thirteen host-specific keys unmoved.
  NEITHER file's ASSERTIONS were weakened; only the measured constants were re-based, with the measurement history appended beside each in the comment style those tables already use. The plan could not have declared these at authoring time without knowing which pinned counts a new flag would move, which is the kind of path the two-way reconciliation exists to surface rather than to forbid.

## Required tests / validation

Run the suite BARE (`python3 -m pytest`) and paste the actual summary line; the configured `addopts` already supply quiet, parallel, fast-subset behavior.

- The flag surface contract suite (`tests/test_run_flag_surface.py`), which asserts the two HOSTS agree and which owns the `DECLARED_BUT_NOT_OWNED_HERE` accounting E-01 changes.
- A test that a bare `reviews` selection is UNCHANGED, which is the regression that matters most: the normative default must not widen.
- A test that `--type spec` selects a FIXTURE spec at `to-review`, and that an empty result exits 0. CORRECTED AT REVIEW (F-7): the live tree has ZERO specs at `to-review`, so a live-tree assertion cannot demonstrate the positive case and would pass vacuously against unchanged code. The fixture must be created by the test, never by advancing a real spec's status.
- A test that `--type spec` against the LIVE tree exits 0 with an empty selection, which is now the real-repository state and is the cheap direct regression for the empty-is-success contract.
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

- [x] V-01 validates E-01
  - Required evidence: paste `--help` from BOTH hosts and BOTH subcommands (`start` and `resume`, per F-10; there is no `run` subparser) showing `--type`; paste the refusal for an unknown value with its listed accepted set; paste the flag-surface suite passing, including the accounting assertion that fails on `declared - owned - excluded`, proving the row was MOVED rather than duplicated. Then paste a bare `aw oc run reviews` selection before and after the change and show it IDENTICAL, because the normative default not widening is the load-bearing half of this item.
  - Observed evidence: `--type` REGISTERED on BOTH hosts and BOTH subcommands (per F-10 there is no `run` subparser; `start` is the one the operator spelling reaches). Walked each built parser:
```
oc_runipd start:  --type ['--type'] choices=['ipd','spec','backlog','prompt','research','release','walkthrough'] default=None
oc_runipd resume: --type ['--type'] choices=['ipd','spec','backlog','prompt','research','release','walkthrough'] default=None
agy_runipd start: --type ['--type'] choices=['ipd','spec','backlog','prompt','research','release','walkthrough'] default=None
agy_runipd resume:--type ['--type'] choices=['ipd','spec','backlog','prompt','research','release','walkthrough'] default=None
```
    IN `--help`, rendered from the shared table (`python3 -m agent_workflows.oc_runipd start --help`):
```
  --type TYPE           Scope a needs-review sweep to one or more artifact
                        TYPES, repeatable (--type ipd --type spec selects the
                        union). Omitted, the sweep selects IPDs ONLY, which is
                        normative: a type never joins `reviews` implicitly.
```
    UNKNOWN VALUE REFUSED, listing the accepted set (argparse `choices`, so it refuses at parse time before any durable state):
```
$ python3 -m agent_workflows.oc_runipd start reviews --type bogus --repo .
runipd start: error: argument --type: invalid choice: 'bogus' (choose from 'ipd', 'spec', 'backlog', 'prompt', 'research', 'release', 'walkthrough')
```
    THE ROW WAS MOVED, NOT DUPLICATED, which is what the accounting assertion measures (`declared - owned - excluded` must be empty):
```
--type owned: True        (in runner_shared.RUN_POLICY_FLAGS_BY_FLAG)
--type still excluded: False  (removed from tests DECLARED_BUT_NOT_OWNED_HERE)
rows: 15  unique flags: 15  unique dests: 15   (no collision; nothing collapsed)
```
    THE BARE DEFAULT IS UNCHANGED, which is the load-bearing half. Measured on the LIVE tree, both hosts:
```
oc  legacy=[] typed_ipd=[] default=[]  ALL EQUAL: True
agy legacy=[] typed_ipd=[] default=[]  ALL EQUAL: True
$ python3 -m agent_workflows.oc_runipd  start reviews --repo . --prepare-only ; echo $?   -> 0
$ python3 -m agent_workflows.agy_runipd start reviews --repo . --prepare-only ; echo $?   -> 0
```
    `legacy` is `sweep_review_candidates`, the pre-change function, unchanged and still shipped. NOTE the live tree has ZERO plans at `to-review`, so the live comparison is `[] == [] == []` and is NOT sufficient on its own; the non-vacuous proof is `TypeScopedReviewSweepTests::test_a_bare_reviews_selection_is_byte_identical_to_the_ipd_only_sweep`, which builds a fixture holding two plans AND a `to-review` spec and asserts the bare sweep returns the plan only and equals both `--type ipd` and `sweep_review_candidates`.
    THE FLAG-SURFACE SUITE PASSES, including the accounting gate:
```
$ python3 -m pytest tests/test_run_flag_surface.py
70 passed in 4.69s     (before the new class was added)
$ python3 -m pytest tests/test_run_flag_surface.py tests/test_rununify_build_parser.py tests/test_rununify_initialize_run.py
167 passed in 7.15s
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the selection for `--type spec` against a FIXTURE spec at `to-review`, for `--type ipd`, and for a bare invocation, on BOTH hosts. Paste an empty `--type spec` case exiting 0. Paste a grep showing no second membership test was added and that both hosts reach the SAME shared function. THEN STATE PLAINLY, as a limitation and not a success, that a selected spec cannot yet be EXECUTED (F-2, F-3): a validation that omits this reads as a shipped capability.
  - DO NOT EXPECT THE LIVE TREE TO YIELD A POSITIVE CASE (F-7). The plan's four ids are stale and the live sweep returns `[]`; re-derive the population at execution and expect it EMPTY. If a live `--type spec` run returns anything, say so and explain it, because that means a spec was moved to `to-review` between this review and execution. A positive case demonstrated ONLY against the live tree, or a fixture created by advancing a real spec's status, does not satisfy this item.
  - Observed evidence: BOTH hosts route the review sweep through the type-scoped entry point, and they reach the SAME function object:
```
same fn object: True   (oc_runipd.runner_shared.sweep_review_candidates_for_types is agy's)
def needs_review in package: 1   (no second membership test was added)
```
    POSITIVE CASE, against a FIXTURE spec at `to-review` as F-7 requires, on both hosts (`TypeScopedReviewSweepTests::test_type_spec_selects_a_FIXTURE_spec_awaiting_review_on_both_hosts`): the fixture holds `spc001` at `to-review`, `spc002` at `approved`, and `pln001` at `to-review`; `--type spec` returns EXACTLY `['spc001']` on oc and agy. The `approved` spec is excluded because the dispatch table routes it to `plan`, which is membership being the table's rather than a status-string test.
    THE FIXTURE IS NOT OPTIONAL AND WAS NOT MANUFACTURED FROM A REAL SPEC. Re-derived the live population at execution per F-7's instruction and it had moved a THIRD time: `sweep_review_candidates_for_type(repo, "spec")` returns `['z7nbn1']` at HEAD `a7e27f4a`, where the plan's Concern says four ids and F-7 measured `[]`. Recorded in the decisions register. No real spec's status was touched.
    LIVE-TREE CONFIRMATION that the wiring reaches the real repository (this is the demonstration, NOT the durable assertion):
```
$ python3 -m agent_workflows.oc_runipd start reviews --repo . --prepare-only --type spec
runipd: --type spec: this selection was RESOLVED but cannot be RUN. Selected:
  20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md
```
    `--type ipd` AND THE BARE INVOCATION are byte-identical to before, on both hosts; see V-01's paste.
    EMPTY IS A SUCCESS THAT EXITS 0 (spec 2.4a property 3), asserted both at the seam and as a real exit code in `test_an_empty_type_scoped_sweep_is_a_SUCCESS_that_exits_zero`: `EmptyStatusSelection` is raised, `main` returns 0, and no run directory is created. The live tree exercises this half by default for PLANS too (zero plans at `to-review`, both hosts exit 0).
    THE LIMIT, STATED PLAINLY AND AS A LIMITATION RATHER THAN A SUCCESS (F-2, F-3): A SELECTED SPEC CANNOT BE EXECUTED. This plan delivers REACHABILITY only. A `--type spec` run selects the specs and is then REFUSED at queue build by `refuse_unrunnable_selected_types`, because a run queue entry is plan-shaped: the manifest is compiled from the plans trees, the queue builder reads `manifest["plans"][id6]`, and `resolve_plan_path` fails OPEN on a non-plan path (measured in superseded plan `mng63x`'s review), so queueing a spec would hand it to plan-shaped code SILENTLY rather than loudly. DECISION 12-ui8b9b-D4 records why refusing beats crashing and beats synthesizing a plan-shaped entry. The refusal NAMES what it selected, so the capability is usable even though the runner cannot act on it. Per-type dispatch is owned by spec `z7nbn1`, which carries its own `- Blocks-Release: next`. A reader must NOT read this item as "the runner can review a spec".
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the frozen value in run state, and paste a `resume` passing a DIFFERENT `--type` showing the pinned behavior (refusal or frozen-value-wins), plus the test that pins it. State which rule was chosen and why, citing the spec line, since `uyeko5` recorded a shipped divergence here and copying a neighbour silently would reproduce it.
  - Observed evidence: THE RULE CHOSEN IS **REFUSE**, and the reason is recorded in full as DECISION 12-ui8b9b-D2 rather than copied from a neighbour (F-5's warning). Spec `25kzda` `:129` says `--resume` is "mutually exclusive with a new selector and with flags that would change the frozen queue or policy"; `--type` IS the selection, and the queue is already frozen, so an ACCEPTED `--type` on resume could not re-scope the queue - it could only write a frozen option CONTRADICTING the queue the run holds. That is strictly worse than refusing, and unlike `--full-auto` there is no `:129`-versus-`:131` tension to inherit, because `:129` names this exact case. Implemented as `resume_rule=RESUME_REFUSE`, the table's second refusing row after `--retry-budget`.
    THE FROZEN VALUE, read back from real `state.json` on both hosts (a bare run freezes the EFFECTIVE default, never `null`):
```
oc  state["options"]["types"] == ["ipd"]
agy state["options"]["types"] == ["ipd"]
```
    A RESUME PASSING A DIFFERENT `--type` IS REFUSED, before any state is loaded or written:
```
$ ... resume <run-id> --repo <repo> --type spec
runipd: --type cannot be changed on --resume: spec 25kzda 2.1 freezes it at queue build
        ('the frozen value cannot change on resume'). Resume the run without it, or start a new run
resume exit code: 2
```
    AN OMITTED `--type` ON RESUME CHANGES NOTHING (the other half, without which the refusal would be satisfiable by an unusable flag): `apply_run_policy_flags_on_resume` returns False and the frozen `["ipd"]` survives, because the resume parser declares `default=None` so silence is distinguishable from an explicit value.
    PINNED BY `TypeScopedReviewSweepTests::test_resume_REFUSES_a_different_type_rather_than_re_scoping_the_queue` (both halves, both hosts) and `test_the_effective_type_set_is_FROZEN_into_run_state`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the mixed-type gate REFUSING a real invocation with the `[RUN-MIXED-TYPES]` text and PROCEEDING under `--allow-mixed`, with `gate_applied=True`. A verdict carrying `gate_applied=False` does NOT satisfy this item: that is the single-type short circuit and is what a still-unreachable gate would also return. Paste the inverted limit test and show it asserts reachability while keeping the invariant it defended; a DELETED test does not satisfy this item.
  - Observed evidence: THE GATE FIRES ON A REAL INVOCATION, which is evidence nobody could produce before this plan. `test_the_mixed_type_gate_REFUSES_a_real_invocation_and_proceeds_with_allow_mixed` drives `initialize_run` on BOTH hosts with `reviews --type ipd --type spec --unattended` against a fixture holding a `to-review` plan and a `to-review` spec: the run raises carrying `[RUN-MIXED-TYPES]` and `No work started.`, and NO run directory is created. Adding `--allow-mixed` SATISFIES that gate (its refusal is gone) and the run then reaches the unrunnable-type refusal, which is itself the proof the mixed gate was satisfied rather than skipped.
    `gate_applied=True` ON THE REAL PATH SET, which is the assertion the item demands and which `gate_applied=False` (the single-type short circuit) cannot satisfy. `test_the_gate_reports_gate_applied_TRUE_on_the_real_multi_type_path_set` builds the path set through the SAME `resolve_selected_artifact_paths` the runner uses and asserts: 2 of 2 artifacts resolved, the PLAN subset holds exactly 1, and the verdict carries `proceed=True`, `gate_applied=True`, `record.response_or_flag == "--allow-mixed"`.
    THAT SEAM IS WHERE THIS COULD HAVE GONE WRONG SILENTLY, so it is called out: the gate is now handed the FULL typed path set (`selection.all_paths`), not the plan subset. Passing the plan subset would have filtered the spec out before the gate could see it, keeping the old limit permanently true by construction while every registration test still passed.
    THE SUPERSEDED PINS WERE INVERTED, NOT DELETED (F-4), and there were TWO of them rather than the one the plan names - see DECISION 12-ui8b9b-D6:
      * `test_no_live_invocation_can_yet_produce_a_mixed_selection` -> `test_a_live_invocation_CAN_now_produce_a_mixed_selection`. Its `assertNotIn("--type", ...)` became `assertIn` on both hosts and both subcommands, it now drives the gate to a real `[RUN-MIXED-TYPES]` refusal, and its DISCOVERY half is deliberately UNCHANGED: `discover_plans` must still return IPDs only, because `--type spec` reaches specs through `discover_specs` and a spec appearing in plan discovery would mean the normative default was widened by the back door.
      * `test_the_combined_path_is_proven_correct_and_NOT_proven_fired` (NOT named by the plan, found at execution) carried the same stale `assertNotIn`. Its flag assertion was inverted while the invariant it actually defends was kept: a `--allow-drafts` run that is NOT mixed must not reach the combined mixed-plus-draft entry point. Its claim is now narrower and still true.
    Both were deliberate handoff signals from `uyeko5` ("so registering `--type` later fails here rather than silently outgrowing it") and both failed by design before being inverted. NEITHER was deleted.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `6m4kow`'s front matter showing no `- Blocks-Release:`, this plan's showing it present, and `aw check` reporting no dangling or mismatched gate. Paste the spec's amended Section 0 row and Section 6 limit. Paste a `git diff` proving the spec's `- Status:` line is byte-unchanged and that its history was written by `aw specs note` rather than by hand.
  - THE GATE-CLEARING HALF IS ALREADY TRUE AND MUST BE REPORTED AS SUCH, NOT RE-PERFORMED (F-9). Verified at review that `6m4kow` carries no `- Blocks-Release:` line and that its own history records the clearing in commit `b16e1108`, the authoring round. So the front-matter evidence above is a CONFIRMATION of an existing state, and the item's original demand to "confirm the gate was carried by this plan BEFORE the spec's field was cleared" is satisfied by that history rather than by anything execution does. State it that way. Do NOT run `--blocks-release -` against the absent field; if you did, say so and show what it wrote, because a setter call on an approved spec this plan's author did not approve is a change worth surfacing.
  - THE REAL DELIVERABLE IS THE TWO STALE ASSERTIONS. Paste the BEFORE and AFTER of the Section 0 R-15 row (`:40`), showing it no longer says `--type` is registered on neither host AND no longer claims the sweep "returns the four `to-review` specs" (which F-7 measures as `[]`). Show the replacement describes the predicate rather than a frozen population, so it cannot rot the same way twice.
  - Observed evidence: THE GATE-CLEARING HALF WAS ALREADY TRUE AND WAS NOT RE-PERFORMED (F-9). Verified `6m4kow` carries NO `- Blocks-Release:` front-matter line (the 7 textual matches in the file are all PROSE about where the gate went), and its own history records the clearing in commit `b16e1108`, the authoring round. `aw specs set ... --blocks-release -` was NOT run: the field is absent, and a setter call against an absent field on an approved spec this plan's author did not approve would write a spurious history record. This plan still carries `- Blocks-Release: next` (line 20), so the gate was never carried by neither artifact.
    THE REAL DELIVERABLE, the two stale assertions. Section 0's R-15 row, BEFORE:
```
| R-15 | IMPLEMENTED AT THE FUNCTION BOUNDARY, NOT OPERATOR-REACHABLE | `runner_shared.sweep_review_candidates_for_type(repo, "spec")` returns the four `to-review` specs; but `--type` is registered on NEITHER host, so no operator invocation can reach it |
```
    AFTER:
```
| R-15 | IMPLEMENTED AND OPERATOR-REACHABLE | `aw <host> run reviews --type spec` selects the specs the shipped predicate answers `needs_review` True for; `--type` is registered on BOTH hosts' `start` and `resume` parsers from the shared `RUN_POLICY_FLAGS` table and threaded to `sweep_review_candidates_for_type` (`ui8b9b`, `tests/test_run_flag_surface.py::TypeScopedReviewSweepTests`) |
```
    BOTH stale claims are gone: the "registered on NEITHER host" evidence AND the four-spec POPULATION. The replacement describes the PREDICATE and cites its tests, so it cannot rot the same way; the prose beneath it records that the population measured four, then `[]`, then one (`z7nbn1`) on three different days, and that a reader wanting today's answer runs the command. Section 6's honest limit is rewritten the same way: R-15's operator surface ships, and the REMAINING limit is restated as "you can ask and the runner refuses" with the plan-shaped-queue reason and `z7nbn1` named. Section 0's gate table now names spec `z7nbn1` instead of plan `mng63x`, and Section 7's non-goal no longer assigns `--type`'s registration to `uyeko5`.
    A THIRD STALENESS WAS FOUND AND FIXED, beyond the two the item names: F-9 asserts `mng63x` is "present in `pending/` carrying the gate", and it is NOT - it was SUPERSEDED on 2026-09-18 by spec `z7nbn1` (per that spec's OQ-03) and sits in `.aw/records/plans/superseded/` with the gate carried forward to the spec. Leaving the spec pointing at a retired plan would have been a fourth stale claim. Recorded in the decisions register.
    NO TOOL-OWNED FIELD WAS HAND-EDITED. `git diff` over the spec shows ZERO changed lines matching `^[-+]- (Status|Id|Date|Blocks-Release|Approval)`, so `- Status: approved` is byte-unchanged, and the amendment record was appended by `aw specs note` (its own confirmation: "appended a history record to ...").
    `aw check` REPORTS NO DANGLING OR MISMATCHED GATE: zero `check.blocks-release-*`, `check.from-spec-dangling` or `check.from-backlog-gate-mismatch` diagnostics naming `ui8b9b`, `6m4kow` or `z7nbn1`. Baseline 54 findings, after 55; the ONE added finding is `check.scope-drift` on this plan, naming the two shipped pin files below, and it is reconciled by finalize's `--scope-reason` rather than being a gate failure.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files this plan changed, path-scoped, never `git add -A`, never push. Paste ACTUAL runner output for every test claim; run the suite bare. This plan AMENDS A SPEC, so that spec file is declared in `Scope-Paths` and the amendment's reason is recorded in the spec's own text, not only here. DO NOT hand-write another role's attestation: this plan's `- Readiness:` is `/plan-review`'s output and is deliberately absent, its `- Approval:` is the human's, and the amended spec's `- Status:` belongs to `aw specs set`.

OQ-01 IS ANSWERED AND NOTHING HERE IS GATED. CORRECTED AT REVIEW (PR-702, F-8): this paragraph previously read "OQ-01 asks whether reachable-but-not-executable is the right boundary for clearing a release gate. It is `- Blocking: yes` and unresolved, so this plan is not executable until the maintainer answers." That contradicted OQ-01's own fields, which read `- Blocking: no` and `- Status: resolved` and carry the maintainer's 2026-09-13 ruling in full. The plan therefore refused itself: an executor reading the gate would stop, while the linter (which reads the FIELDS) reports conforming and a runner would dispatch it. Two artifacts disagreeing about whether a plan may start is worse than either answer alone.
THE RULING, restated here because that is what this paragraph is for: SELECTION SHIPS NOW, and the execution half is filed as its own release blocker (`mng63x`, verified at review to exist in `pending/` carrying `- Blocks-Release: next`). So this plan proceeds exactly as scoped and does not reduce 2.0.0's blocker count. The instruction to "SUPERSEDE this plan with a Set rather than widening it" is also void, since it was conditional on an answer requiring execution, which was not the answer given.

Post-gate lifecycle: on completion, run `aw ipd lint --phase pre-transition`, verify every `V-*` with pasted evidence, then move this file to `.aw/records/plans/executed/` with a path-scoped lifecycle commit.

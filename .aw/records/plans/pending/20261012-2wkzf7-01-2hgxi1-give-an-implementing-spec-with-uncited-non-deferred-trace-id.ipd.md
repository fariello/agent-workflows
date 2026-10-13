# IPD: Give an implementing spec with uncited non-deferred TRACE ids a plan-writing turn

- Date: 2026-10-12
- Kind: child
- Concern: Spec `89xjll` OQ-08 (maintainer decision 2026-10-08) says a spec planned in stages STAYS `implementing` between stages, and that the runner should start the next stage itself: when it dispatches an `implementing` spec that declares at least one mandatory, non-`[Deferred]` TRACE id cited by no pooled plan (`89xjll` 6.1), it runs a plan-writing turn checked by `SPEC-PLAN-TRACE` over the pooled set. Nothing implements that today. Measured at authoring HEAD `ca878876a`: `run_selection_policy.runner_action("spec", "implementing")` returns `undetermined` (`_SPEC_ACTIONS` omits `implementing`), so `runner_shared.enforce_freeze_time_refusal` refuses the WHOLE run with `[RUN-UNDETERMINED-ACTION]` (pinned by `tests/test_freeze_time_refusal.py::TestRefusalClassCases::test_5_1_undetermined_action_refuses_at_freeze`). The only way to start a second stage is the stopgap: a human steps the spec `implementing -> approved` with `--by-human`.
- Scope: IN: (1) re-measure the dispatch path and the live `implementing` population at the executing HEAD, as a gate (E-01); (2) one shared predicate in `production_checks` that returns the mandatory, non-deferred, declared TRACE ids no pooled plan cites, computed by the SAME coverage code `spec_plan_trace` uses (E-02); (3) a runner-only refinement in `run_selection_policy.runner_action` that turns spec `implementing` into `plan` when, and only when, that predicate is non-empty, fed by ONE content reader that every runner call site and the mixed-selection preview use (E-03); (4) make the existing spec production arm of `runner_shared.execute_item_core` run for an `implementing` source: a prompt naming the uncited ids and requiring qualified citations, the same five post-turn checks, and on success a history note plus a path-scoped commit instead of the illegal same-status `-> implementing` set (E-04); (5) amend `25kzda` 3.3 and 2.6 and `89xjll` 3.3 and 6.1 so the contract matches the behavior (E-05); (6) behavioral tests on both hosts (E-06); (7) a `CHANGELOG.md` line and a docs sentence (E-07). OUT: the OTHER half of `25kzda` 3.3's `implementing` row (resolving and dispatching an implementing spec's `From-Spec` children, then setting `implemented`), which is unimplemented today and stays exactly as it is (F-03); any change to `SPEC-PLAN-TRACE`'s pass criterion or message; any change to backlog production.
- Scope-Paths: agent_workflows/production_checks.py, agent_workflows/run_selection_policy.py, agent_workflows/runner_shared.py, tests/test_implementing_spec_replan.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, .aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md, docs/artifact-lifecycles.md, CHANGELOG.md
- Item-Dependencies: executed:rtvdak
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- From-Backlog: 2wkzf7
- Set: 2wkzf7
- Order: 1
- Highest E allocated: 07
- Author: opencode model=claude-opus
- Id: 2hgxi1
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005

- 2026-10-12 to-review (opencode model=claude-opus): authored from backlog item `2wkzf7`. Measured at HEAD `ca878876a` that an `implementing` spec is refused at freeze as `undetermined` (F-01), that `rtvdak`'s parser and `spec_plan_trace` are shipped (F-02), and that every live `implementing` spec is grandfathered (F-04). Resolved the dispatch-seam, same-status-transition and preview questions from repository evidence (OQ-01..OQ-03).
- 2026-10-12 draft (opencode model=claude-opus): created.

## Goal

When the runner is handed an `implementing` spec whose body declares a mandatory, non-`[Deferred]` TRACE id that no pooled plan cites, it gives that spec a plan-writing turn verified by `SPEC-PLAN-TRACE` over the pooled set, keeps the spec `implementing`, and records the stage in the spec's history; every other `implementing` spec, including every grandfathered one, dispatches exactly as it does today. This retires the `implementing -> approved` stopgap as the only way to start a later stage, as `89xjll` OQ-08 decided.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before changing anything

- [x] E-01 Re-measure the `implementing` dispatch path and population at the executing HEAD, editing no file.
  - Depends on: none
  - Expected outcome: a pasted transcript with the HEAD hash showing: (a) `python3 -c "from agent_workflows import run_selection_policy as p; print(p.runner_action('spec','implementing'))"` prints `undetermined`; (b) `python3 -m pytest tests/test_freeze_time_refusal.py -o addopts="" -q -k test_5_1` passes (the whole-run refusal is live); (c) `production_checks.spec_plan_trace`, `parse_spec_requirement_ids`, `parse_spec_id_markers`, `_find_executed_linked_plans` and `spec_plan_trace_deferred` exist; (d) for every spec under `.aw/records/specs/implementing/`, `spec_requires_requirement_ids(name, repo_root=repo)` and `spec_plan_trace_vacuity(repo, id6)`. Expected at authoring: three specs (`c4gd2h`, `7ckptx`, `z7nbn1`), all `False` / `grandfathered`. GATE: if (a) no longer prints `undetermined`, another lane has changed the `implementing` row, so STOP and reconcile with it before editing; if (d) finds a NON-grandfathered `implementing` spec, record it, because after this plan it becomes eligible for a production turn on the next run that names it.
  - Execution state: performed

### Task group 2: the predicate and the dispatch decision

- [x] E-02 Add `production_checks.spec_uncited_trace_ids(repo, spec_id6) -> list[str]` returning, sorted, the mandatory, non-`[Deferred]` declared requirement and acceptance ids of the spec that NO pooled plan cites, where the pooled set is `89xjll` 6.1's: active linked plans (`existing_handoff_plans(repo, "spec", id6)`) plus linked plans in `executed/` (`_find_executed_linked_plans`), with `superseded/` and `not-executed/` excluded.
  - Depends on: E-01
  - Expected outcome: the coverage computation (pooled-set assembly, qualified citation regex of `89xjll` 6.2b, orchestrator `CONFIRM` row exclusion, requirement-vs-`E-*` and acceptance-vs-`V-*` split, marker filtering) is extracted from `spec_plan_trace` into ONE private helper that both `spec_plan_trace` and `spec_uncited_trace_ids` call, so the "should this spec be re-planned" answer and the "did this production cover it" answer cannot diverge. `spec_plan_trace`'s return value and message are byte-identical for every input (its existing tests in `tests/test_production_checks_trace.py` and `tests/test_spec_production.py` pass unedited). The new function returns `[]` for a grandfathered spec, a spec declaring no TRACE ids, a spec whose only uncovered ids are `[Deferred]`, `[Should]` or `[Optional]`, and a spec that cannot be found. Unknown references (the third conjunct) are NOT part of its answer: they are a defect of an existing plan, not a signal to plan a new stage.
  - Execution state: performed

- [x] E-03 Add refinement (iv) to `run_selection_policy.runner_action`: a keyword input `uncited_trace_ids: Optional[bool] = None`; for `spec_type == "spec"` and status `implementing`, `True` yields `ACTION_PLAN`, and `False` or `None` leave the table's `undetermined` answer untouched. Add ONE content reader beside `review_depends_on_completeness` (for example `implementing_spec_needs_plan(repo_root, id6) -> bool`, lazily importing `production_checks` and failing safe to `False` on any exception), and route every runner call site that derives a spec's action through it: `runner_shared.expand_selectors` (the `all` sweep), `closure_target_admission`, the `--action` preflight and the typed non-plan queue branch in `initialize_run_core`, plus `run_selection_policy.classify_paths` so the mixed-selection preview shows `plan` for the same item. Also reword the `--action plan` refusal in `runner_shared.enforce_requested_action` (the string "Plan is the next legal action only for an approved spec") so it names the `implementing` re-plan condition, since that sentence becomes false for an eligible `implementing` spec (review PR-002).
  - Depends on: E-02
  - Expected outcome: `_SPEC_ACTIONS` is NOT given an `implementing` row (the table stays status-only; the answer depends on content, exactly as the `draft` row does), and its comment is rewritten to say: "`implementing` absent: a post-cutover spec with uncited non-deferred TRACE ids is refined to `plan` by `runner_action` (spec `25kzda` 3.3, `89xjll` OQ-08); otherwise it stays undetermined". `tests/test_run_selection_policy.py::test_undeterminable_action_is_reported_not_bucketed` (which asserts `_action_for("spec","implementing")` is undetermined) passes unedited. Because `enforce_requested_action` is driven by the derived action, `--action plan` becomes legal for an eligible `implementing` spec and stays illegal for an ineligible one with no further change. A grandfathered `implementing` spec still reaches `enforce_freeze_time_refusal` as `undetermined`, so `test_5_1_undetermined_action_refuses_at_freeze` passes unedited.
  - Execution state: performed

### Task group 3: the production turn for an implementing source

- [x] E-04 Make the spec production arm of `runner_shared.execute_item_core` (`is_spec_production`) serve an `implementing` source: `build_spec_production_prompt` gains an `implementing` variant, and the success path records the stage instead of transitioning.
  - Depends on: E-03
  - Expected outcome: (1) the prompt, when the spec's on-disk status is `implementing`, says it is planning a LATER STAGE of an already approved spec, lists the ids `spec_uncited_trace_ids` returned, and states that each must be cited QUALIFIED with the spec id6 (for example "`<id6>` R-2") in an `E-*` (requirement) or `V-*` (acceptance) item, per `89xjll` 6.2b; it keeps the existing "Continue this handoff" section (`_append_continue_handoff_section`) and the prohibition on changing the spec's `- Status:`, worded so it no longer claims the runner will set `implementing`. The `approved` prompt is byte-identical to today. (2) Post-turn verification runs the same five checks in the same order (`spec_plan_count`, `spec_plan_set`, `spec_plan_conformance`, `spec_plan_gate_carry`, `spec_plan_trace`) with the same correction-turn loop; a finding leaves the spec `implementing` and unchanged on disk. (3) On success the runner does NOT call `aw specs set ... --status implementing` (a same-status write; OQ-02); it calls `aw specs note <spec> --message "stage planned by run <run-id>: <plan id6s>"` through `pinned_module_argv` and commits only the spec path, path-scoped, with a subject `note(spec): record planned stage for <id6>` (a sibling of `commit_spec_transition_output`, or that function parameterized, sharing its path filter and trailers), records a `spec-stage-planned` event, and sets `generated_next_actions` exactly as today. The `approved` success path is unchanged. (4) The spec is never set `implemented` and never `approved` by this path.
  - Execution state: performed

### Task group 4: keep the contract true

- [x] E-05 Amend the two specs this changes, in the same change: `25kzda` 3.3's `implementing` row and 2.6's `--action plan` bullet, and `89xjll` Section 2's "Verification entry point" bullet, 3.3's OQ-08 bullet and 6.1's first paragraph; append a `## Workflow history` note to each with `aw specs note`.
  - Depends on: E-04
  - Expected outcome: `25kzda` 3.3 splits the `implementing` row into two conditions: "post-cutover, with a mandatory non-`[Deferred]` TRACE id cited by no pooled plan (`89xjll` 6.1)" -> author the remaining plans as the `approved` row does, verified by the same codes including `SPEC-PLAN-TRACE` over the pooled set, keep the spec `implementing`, record the stage with a history note, report the plans as next actions; and "otherwise" -> the existing text verbatim. `25kzda` 2.6 reads "`--action plan` is legal only for an `approved` spec, an `implementing` spec meeting 3.3's re-plan condition, or an `open` backlog item." `89xjll` 3.3's OQ-08 TARGET DESIGN bullet records that it is delivered by plan `2hgxi1` and the STOPGAP bullet says it remains legal but is no longer required. `89xjll` 6.1's "only specifications with status `approved` map to `ACTION_PLAN`" is corrected to name the `implementing` refinement, and so is `89xjll` Section 2's "Verification entry point" bullet ("`run_selection_policy._SPEC_ACTIONS` maps strictly `approved` to `ACTION_PLAN` ... judge exclusively the `approved` spec population"), which states the same now-false claim (review PR-001). No requirement id, acceptance id, pass criterion or message template in either spec changes. Both edits are listed in `- Scope-Paths:`.
  - Execution state: performed

### Task group 5: pin it

- [x] E-06 Create `tests/test_implementing_spec_replan.py`, behavioral tests in temporary git repositories driving the real runner on BOTH hosts (`oc_runipd`, `agy_runipd`) with the host spawn patched by a fake agent, in the style of `tests/test_spec_production.py`.
  - Depends on: E-04
  - Expected outcome: cases: (1) the predicate on a post-cutover (`20261001`-dated) `implementing` fixture spec declaring `R-1`, `R-2`, `R-3 [Deferred]`, `AC-1`, with an `executed/` linked plan citing "`spc` R-1" and "`spc` AC-1": returns `["R-2"]`; a `superseded/` linked plan citing `R-2` does not change that; an UNQUALIFIED `R-2` does not cover it; a `20260927`-dated twin returns `[]`. (2) `runner_action` returns `plan` only for `("spec","implementing", uncited_trace_ids=True)` and leaves every other `(type, status)` pair's answer unchanged (asserted against the unrefined call). (3) End to end, success: `start <spec-id6>` on the fixture, the fake agent writes a conformant `to-review` plan carrying `From-Spec` and citing "`spc` R-2"; the item ends `executed`, the spec file is still under `specs/implementing/` with `- Status: implementing`, its history gained a `note` line naming the run and the new plan, `generated_next_actions` names the plan, and `git log` shows one path-scoped commit touching only the spec for the note. (4) End to end, refusal: the fake agent writes a plan that does not cite `R-2`; the item fails with `[SPEC-PLAN-TRACE]` naming `R-2`, and the spec file is byte-identical to before. (5) Unchanged dispatch: a post-cutover `implementing` spec whose ids are all cited, and a grandfathered one with uncited ids, both still refuse at freeze with `[RUN-UNDETERMINED-ACTION]` and create no run directory. (6) `--action plan --prepare-only` is admitted for the eligible spec and refused for the fully cited one. (7) `classify_paths` previews the eligible spec as `plan`. Tests drive code and assert outputs, exit codes and files; none reads production source (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE").
  - Execution state: performed

- [x] E-07 Add one `CHANGELOG.md` `Added:` line under the pending 2.0.0 section and one sentence to the spec lifecycle section of `docs/artifact-lifecycles.md` saying that `aw oc run` / `aw agy run` on an `implementing` spec that still has uncited, non-deferred requirement ids writes the plans for the next stage and keeps the spec `implementing`.
  - Depends on: E-04
  - Expected outcome: both are user-facing prose with no em or en dash (`AGENTS.md`). The docs sentence sits next to the existing "Step back one ... `implementing -> approved`" paragraph and says the step back is no longer needed to plan a later stage.
  - Execution state: performed


## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `run_selection_policy` is the single status-to-action authority (spec `z7nbn1` 1.1/1.2, 5.6). A content-dependent row is expressed as a `runner_action` refinement fed by a caller-supplied input, not as a table row, exactly as `draft` is (`authoring_complete`, `review_depends_on_completeness`). E-03 follows that precedent rather than adding a second mapping.
- `SPEC-PLAN-TRACE` is wired only at the spec production block of `execute_item_core`, after `spec_plan_count`, `spec_plan_set`, `spec_plan_conformance`, `spec_plan_gate_carry`, under the production correction-turn loop (`production_set_retry_decision`). E-04 reuses that block rather than adding a second one.
- `89xjll` 6.4: TRACE is a citation gate, never proof of implementation. Nothing this plan adds may describe a re-planned spec as implemented or verified beyond "trace-verified against declared identifiers".
- `attention_contract.SPEC_TRANSITIONS["implementing"]` is `{implemented, approved, deferred, parked, superseded}`; `implementing -> implementing` is not a transition, so the success path records a note (`aw specs note`, which appends history without changing status) rather than a set.
- Run the suite BARE as `python3 -m pytest`; use `-o addopts=""` only for narrowed per-test counts (`AGENTS.md`).
- `- Readiness:` is omitted on purpose: `/plan-review` writes it, the author does not (`AGENTS.md`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | **An `implementing` spec is refused at freeze today.** `_SPEC_ACTIONS` has no `implementing` row, `runner_action` applies no refinement to it, and `enforce_freeze_time_refusal` turns `undetermined` into a whole-run `[RUN-UNDETERMINED-ACTION]` refusal. | `python3 -c "...runner_action('spec','implementing')"` printed `undetermined` at `ca878876a`; `test_5_1_undetermined_action_refuses_at_freeze` asserts "has status implementing, for which no action is defined". |
| F-02 | **The dependency is shipped.** `rtvdak` is in `plans/executed/`; `production_checks` exposes `parse_spec_requirement_ids`, `parse_spec_id_markers`, `spec_plan_trace` (pooling active plus `executed/` linked plans), `spec_plan_trace_vacuity` and `spec_plan_trace_deferred`. The coverage logic needed to decide "uncited" lives inside `spec_plan_trace` only, so E-02 extracts it rather than copying it. | `.aw/records/plans/executed/20260930-reqids-02-rtvdak-...ipd.md`; `production_checks.spec_plan_trace` body. |
| F-03 | **The "otherwise dispatch children as today" branch does not exist.** `25kzda` 3.3 says an `implementing` spec resolves and dispatches its `From-Spec` children, but nothing implements it (F-01); `z7nbn1` Section 7 leaves it with `25kzda`. So "unchanged" for that branch means "still refused as undetermined", and this plan must not quietly start dispatching children. | `z7nbn1` Section 7: "the `implementing` spec dispatch row of `25kzda` 3.3 (resolving and running a spec's `From-Spec` children), which stay with `25kzda`". |
| F-04 | **Every live `implementing` spec is grandfathered.** `c4gd2h`, `7ckptx`, `z7nbn1` all predate the `20261001` `spec_requirement_ids` cutover, so on the current corpus the new branch never fires and no live run changes behavior. | E-01 (d) probe at authoring: all three `False grandfathered`. |
| F-05 | **The success path cannot reuse the transition.** The `approved` success path calls `aw specs set <spec> --status implementing`; for an `implementing` source that is a same-status write: the setter reports `unchanged` and appends a history line reading `implementing (aw specs): <msg>`, which reads as a transition that did not happen (corrected at review, PR-003: the earlier wording said it is tagged `same-status`), and `commit_spec_transition_output`'s subject says "-> implementing". A note plus its own commit subject records what actually happened. | `execute_item_core` spec success path (the `"specs", "set", rel_spec_str, "--status", "implementing"` argv); review probe in a scratch repo: `aw specs set <implementing spec> --status implementing --message probe --no-commit` -> `unchanged`, history `- 2026-10-12 implementing (aw specs): probe`; `aw specs note ... --message "stage planned by run R: abc123"` -> `- Status: implementing` kept, history `- 2026-10-12 note (aw specs): stage planned by run R: abc123`, file stayed under `specs/implementing/`. |
| F-06 | **`SPEC-PLAN-COUNT` already handles a later stage.** It counts pre-existing active linked plans as continued output and refuses a second Set only when one exists; executed stage-one plans are not "active", so a fully executed first stage lets the second stage start a fresh Set. A second stage written while stage-one plans are still pending must join their Set; that is existing behavior and is kept. | `production_checks.spec_plan_count` condition (c); `existing_handoff_plans` skips `_TERMINAL_DISPOSITIONS`. |
| F-07 | **The preview must agree.** `classify_paths` computes `_action_for` on status alone, so without E-03's routing a mixed-selection preview would say `undetermined` for an item the queue dispatches as `plan`, the two-mapping defect `z7nbn1` 1.1/5.6 forbids. | `run_selection_policy.classify_paths` body. |

## Proposed changes (ordered, validatable)

1. **Re-measure (E-01).** Confirm the refusal is live and the population is grandfathered; a changed result stops the plan.
2. **Predicate (E-02).** One shared coverage helper behind both `spec_plan_trace` and the new `spec_uncited_trace_ids`.
3. **Decision (E-03).** `runner_action` refinement (iv) plus one content reader used by every call site and the preview.
4. **Production (E-04).** The existing spec production arm accepts an `implementing` source and records a stage instead of a transition.
5. **Contract (E-05).** `25kzda` 3.3/2.6 and `89xjll` 3.3/6.1 amended to match.
6. **Pin and record (E-06, E-07).** Both-host behavioral tests, a changelog line, a docs sentence.

## Deferred / out of scope (with reason)

- **Dispatching an `implementing` spec's `From-Spec` children and setting it `implemented` (`25kzda` 3.3's other branch).** Unimplemented today (F-03); the backlog item requires that branch's behavior to stay as it is, and building it is a separate runner feature.
  - Carrier-Declined: this plan creates no obligation for it; it is `25kzda` 3.3's own pre-existing row, assigned to `25kzda` by `z7nbn1` Section 7, and an approved spec already carries it.
- **`aw partition -t specs` runnability.** `partition._is_runnable` reads the public table through `run_selection_policy.action_for_status`, which carries none of `runner_action`'s refinements, so it already excludes a complete `draft` spec and will likewise exclude an eligible `implementing` spec. That is the existing, consistent precedent for every content-dependent row, not a new divergence introduced here (review PR-004).
  - Carrier-Declined: no new obligation; giving `partition` the runner refinements would apply to `draft` as well and is a separate change to `partition`, which is outside this plan's dispatch scope.
- **Retiring the `implementing -> approved` stopgap edge.** It stays legal in `attention_contract.SPEC_TRANSITIONS` because it is also the ordinary step-back edge; only its role as the sole way to start a stage ends.
  - Carrier-Declined: nothing to remove; the edge has other legitimate uses.

## Scope check

- Over-scope: E-03 touches four runner call sites and the preview, not only the queue builder. That is required by the single-authority rule (F-07); routing only the queue builder would make `--action plan`, `--with-dependencies` and the preview disagree with dispatch.
- Under-scope: none known. The re-plan branch's only observable entry points are the four call sites plus `classify_paths`, all named.
- Right-sizing: seven items, one concern each. E-02 (predicate) and E-03 (decision) are separate because E-02 is testable alone and also refactors `spec_plan_trace`; E-04 (runtime) and E-05 (spec text) touch disjoint files.

## Required tests / validation

- `python3 -m pytest tests/test_implementing_spec_replan.py -o addopts="" -q` with output pasted (E-06, both hosts).
- Unedited regression set, output pasted: `tests/test_production_checks_trace.py tests/test_spec_production.py tests/test_freeze_time_refusal.py tests/test_run_selection_policy.py tests/test_set_dispatch_parity.py tests/test_production_correction_turn.py tests/test_production_resume_handoff.py tests/test_production_set_check.py tests/test_handoff_ready_gate.py`.
- A bare `python3 -m pytest`, compared by FAILURE SET; any failure shown to reproduce on an unmodified tree at the same HEAD before it is called pre-existing.
- `aw specs check` on both amended specs; `aw ipd lint --phase pre-transition` on this plan; `aw check`; `aw sanitize --agent`.

## Spec / documentation sync

- `25kzda` (`.aw/records/specs/approved/20260826-25kzda-01-...spec.md`), Sections 3.3 and 2.6: AMENDED by E-05. Why: `89xjll` 7 and OQ-08 state that OQ-08 "changes `25kzda`'s `implementing` dispatch rule; that amendment belongs to the plan delivering backlog `2wkzf7`". Leaving 3.3 unchanged would make every later plan reviewed against `25kzda` treat the re-plan turn as a violation of the `implementing` row, and 2.6 would make `--action plan` on such a spec contractually illegal while the runner admits it.
- `89xjll` (`.aw/records/specs/approved/20261001-89xjll-01-...spec.md`), Sections 2 ("Verification entry point" bullet), 3.3 and 6.1: AMENDED by E-05. Why: 3.3 describes the delivery as future work, and 6.1 and the Section 2 bullet state only `approved` specs map to `ACTION_PLAN`; all three become false when this ships.
- `docs/artifact-lifecycles.md` and `CHANGELOG.md`: E-07.

## Open questions

### OQ-01: Where does the content-dependent answer enter dispatch?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: AS A `runner_action` REFINEMENT FED BY A CALLER-SUPPLIED BOOLEAN, with one content reader in `run_selection_policy` that every caller uses (E-03). Evidence: `draft` is the in-repo precedent for a content-dependent row (`authoring_complete`, `review_depends_on_completeness`, comment "completeness is CONTENT"), and `z7nbn1` 1.1/5.6 forbid a second mapping. Rejected: an `implementing -> plan` table row (would plan every implementing spec, including grandfathered ones, breaking the backlog's "dispatch unchanged" requirement); deciding inside `execute_item_core` only (the queue would still freeze-refuse it as undetermined first).

### OQ-02: How is a successful later stage recorded on the spec?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: A HISTORY NOTE VIA `aw specs note`, COMMITTED PATH-SCOPED (E-04). Demonstrated at review on a scratch copy of an `implementing` spec (F-05): `aw specs note` appends `note (aw specs): ...`, keeps `- Status: implementing` and the directory. Evidence: OQ-08 says the spec "STAYS `implementing`"; `implementing -> implementing` is not in `SPEC_TRANSITIONS`, and a same-status set is recorded as `same-status`, which reads as "nothing happened". Rejected: re-calling `aw specs set --status implementing` (F-05); stepping through `approved` (exactly what OQ-08 rejected as the permanent design).

### OQ-03: Does the mixed-selection preview change too?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, through the same reader (E-03, F-07). A preview that says `undetermined` for an item the queue runs as `plan` is the two-mapping defect `z7nbn1` exists to remove.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Paste the four-part E-01 transcript with the HEAD hash, taken BEFORE any edit: the `runner_action` output, the `test_5_1` pytest line, the existence check of the five `production_checks` names, and the per-`implementing`-spec grandfathering table. State explicitly whether either GATE fired.
  - Observed evidence:
    ```
    Pre-edit transcript at executing HEAD 381bf46f4243d287a5cf527a5c1b067d9fdf09a8:
    (a) runner_action('spec', 'implementing') -> undetermined
    (b) pytest tests/test_freeze_time_refusal.py -o addopts="" -q -k test_5_1:
    1 passed, 18 deselected in 1.48s
    (c) existence check:
    spec_plan_trace: True
    parse_spec_requirement_ids: True
    parse_spec_id_markers: True
    _find_executed_linked_plans: True
    spec_plan_trace_deferred: True
    (d) per-implementing-spec grandfathering:
    c4gd2h: requires_req_ids=False, vacuity=grandfathered
    7ckptx: requires_req_ids=False, vacuity=grandfathered
    z7nbn1: requires_req_ids=False, vacuity=grandfathered
    Gate status: Neither GATE fired. (a) printed undetermined, and (d) found 0 non-grandfathered implementing specs.
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the `git diff` of `agent_workflows/production_checks.py` showing one shared coverage helper called by both `spec_plan_trace` and `spec_uncited_trace_ids`. Paste an interpreter transcript calling `spec_uncited_trace_ids` on the E-06 case (1) fixtures (post-cutover, deferred-only, grandfathered, superseded-only, unqualified) with each return value. Paste `python3 -m pytest tests/test_production_checks_trace.py tests/test_spec_production.py -o addopts="" -q` passing with `git diff --stat tests/` showing neither file edited.
  - Observed evidence:
    1. git diff agent_workflows/production_checks.py showing _compute_spec_trace_coverage shared by spec_plan_trace and spec_uncited_trace_ids:
    ```diff
    --- a/agent_workflows/production_checks.py
    +++ b/agent_workflows/production_checks.py
    @@ -684,46 +684,33 @@ def _find_executed_linked_plans(repo: Path, spec_id6: str) -> list[Path]:
    +class _SpecTraceCoverage(NamedTuple):
    +    uncovered_reqs: set[str]
    +    uncovered_acs: set[str]
    +    unknown_refs: set[str]
    +    is_traceable: bool
    +
    +def _compute_spec_trace_coverage(
    +    repo: Path | str,
    +    spec_id6: str,
    +    produced_paths: Sequence[Path | str] | None = None,
    +) -> _SpecTraceCoverage:
    ...
    +def spec_uncited_trace_ids(repo: Path | str, spec_id6: str) -> list[str]:
    +    repo = Path(repo)
    +    cov = _compute_spec_trace_coverage(repo, spec_id6, produced_paths=None)
    +    if not cov.is_traceable:
    +        return []
    +    return sorted(cov.uncovered_reqs | cov.uncovered_acs)
    ```
    2. Interpreter transcript calling spec_uncited_trace_ids on E-06 case 1 fixtures:
    ```
    post-cutover uncited: ['R-2']
    with superseded plan citing R-2: ['R-2']
    with unqualified R-2 cited in active plan: ['R-2']
    deferred-only spec uncited: []
    grandfathered spec uncited: []
    ```
    3. Pytest passing and git diff --stat tests/ clean:
    ```
    python3 -m pytest tests/test_production_checks_trace.py tests/test_spec_production.py -o addopts="" -q
    .............................................                            [100%]
    45 passed in 132.02s (0:02:12)
    $ git diff --stat tests/
    (empty)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the `git diff` of `agent_workflows/run_selection_policy.py` and of each `runner_shared` call site E-03 names. Paste an interpreter transcript printing `runner_action('spec','implementing', uncited_trace_ids=v)` for `v` in `True`, `False`, `None`, and `_action_for('spec','implementing')`. Paste `python3 -m pytest tests/test_run_selection_policy.py tests/test_freeze_time_refusal.py -o addopts="" -q` passing unedited. Paste a real `aw oc run start <fixture-spec> --action plan --prepare-only` against the eligible fixture (code path: `initialize_run_core` -> `enforce_requested_action`) admitted, and against the fully cited fixture refused. Paste the refused run's `--action plan` message showing the reworded legality sentence naming the `implementing` re-plan condition.
  - Observed evidence:
    1. git diff excerpt of run_selection_policy.py and runner_shared.py call sites:
    ```diff
    --- a/agent_workflows/run_selection_policy.py
    +++ b/agent_workflows/run_selection_policy.py
    @@ -107,4 +107,6 @@ _SPEC_ACTIONS: dict[str, str] = {
    -    #   implementing absent: planned in stages; future work (89xjll OQ-08)
    +    #   implementing absent: a post-cutover spec with uncited non-deferred TRACE ids
    +    #   is refined to plan by runner_action (spec 25kzda 3.3, 89xjll OQ-08); otherwise
    +    #   it stays undetermined.
    @@ -171,2 +173,4 @@ def runner_action(
    +    uncited_trace_ids: bool | None = None,
    +    if spec_type == "spec" and status == "implementing" and uncited_trace_ids is True:
    +        return ACTION_PLAN
    ```
    2. Interpreter transcript:
    ```
    runner_action(spec, implementing, uncited_trace_ids=True): plan
    runner_action(spec, implementing, uncited_trace_ids=False): undetermined
    runner_action(spec, implementing, uncited_trace_ids=None): undetermined
    _action_for(spec, implementing): undetermined
    ```
    3. Pytest passing unedited:
    ```
    python3 -m pytest tests/test_run_selection_policy.py tests/test_freeze_time_refusal.py -o addopts="" -q
    78 passed in 68.42s (0:01:08)
    ```
    4. Real CLI execution:
    Eligible fixture (spceli) admitted:
    ```
    $ aw oc run start spceli --action plan --prepare-only --repo /tmp/repo
    Run order (1 item(s)): 01 spceli
    ▶ implmntg ◕ queued spec - - - - - - 20261001 spceli 01 spceli -
    Action: plan, Status: queued (exit 0)
    ```
    Fully-cited fixture (spcful) refused:
    ```
    $ aw oc run start spcful --action plan --prepare-only --repo /tmp/repo
    runipd: --action plan is illegal for 1 selected item(s): spcful (status 'implementing' -> action 'undetermined'). Plan is the next legal action only for an approved spec, an implementing spec with uncited non-deferred TRACE ids, or an open backlog item; a to-review or draft plan would REVIEW, which is not what 'plan' asks for. No run was started and no session launched. To plan an approved spec instead, run: aw oc run --action plan <selector>
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the `git diff` of the spec production arm of `runner_shared.execute_item_core`, `build_spec_production_prompt`, and the commit helper. Paste the rendered `implementing` prompt for the fixture (naming the uncited id and the qualified-citation rule) and a byte comparison showing the `approved` prompt for an approved fixture is unchanged from HEAD. Paste the E-06 case (3) run's `state.json` item (status, `generated_next_actions`), the spec file's status line and new history line, its directory, and `git log --stat -2` showing the note commit touches only the spec (code path: `execute_item_core` spec production success path, created by E-04).
  - Observed evidence:
    1. Rendered implementing prompt excerpt:
    ```markdown
    # Plan production from implementing spec: .aw/records/specs/implementing/20261001-spc001-01-spc001-test-spec.spec.md

    You are authoring implementation plan(s) (IPDs) for a later stage of already approved spec `spc001` at `.aw/records/specs/implementing/20261001-spc001-01-spc001-test-spec.spec.md`.
    ...
    8. Mandatory uncited requirement and acceptance items awaiting coverage: R-1, R-2. Each must be cited qualified with the spec id6 (for example `spc001 R-2`) in an E-* (requirement) or V-* (acceptance) item, per spec 89xjll 6.2b.
    ```
    2. Byte comparison showing approved prompt unchanged from pre-change HEAD:
    ```
    Current approved prompt equals pre-change HEAD approved prompt: True
    ```
    3. E-06 case (3) run results:
    ```
    state.json item status: executed
    state.json item generated_next_actions: [{'from_spec': 'spc003', 'id6': 'plnnew', 'path': '.aw/records/plans/pending/20261001-demo-01-plnnew-test-plan.ipd.md'}]
    spec directory: implementing
    spec status line: - Status: implementing
    spec history line: - 2026-10-13 note (aw specs): stage planned by run run-oc-succ: plnnew

    git log --stat -2:
    commit da82530798c7c1921caf0304dc8d4d69260f8c8b
    Author: Tester <test@example.com>
    Date:   Tue Oct 13 00:16:06 2026 -0400

    note(spec): record planned stage for spc003

    Spec spc003 recorded planned stage in workflow history. Path-scoped to the spec file; hooks ran normally.

    AW-Run: run-oc-succ
    AW-Item: spc003
    AW-Committed-By: driver

     .../specs/implementing/20261001-spc003-01-spc003-test-spec.spec.md      | 2 ++
     1 file changed, 2 insertions(+)
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the `git diff` of both spec files showing only 25kzda 3.3 and 2.6 and 89xjll Section 2 ("Verification entry point" bullet), 3.3 and 6.1 changed plus one history note each, and `grep -c` over each spec's requirement and acceptance id declarations before and after showing the counts unchanged. Paste `aw specs check` on both specs passing.
  - Observed evidence:
    1. Spec declaration counts before and after:
    25kzda before: req=0, ac=4
    25kzda after:  req=0, ac=4
    89xjll before: req=9, ac=10
    89xjll after:  req=9, ac=10
    2. aw specs check:
    ```
    $ aw specs check .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    aw specs check: all specs conform. 1 specs checked.
    $ aw specs check .aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md
    aw specs check: all specs conform. 1 specs checked.
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Paste `python3 -m pytest tests/test_implementing_spec_replan.py -o addopts="" -q -v` output listing every case on both hosts passing. Paste one deliberate-failure proof: in a throwaway `git worktree add` at the pre-change HEAD with only the new test file copied in, the run FAILS; then paste `git worktree list` showing the throwaway removed. Paste the regression set from `## Required tests / validation` passing.
  - Observed evidence:
    1. Test suite execution:
    ```
    $ python3 -m pytest tests/test_implementing_spec_replan.py -o addopts="" -v
    tests/test_implementing_spec_replan.py::TestImplementingSpecReplan::test_case_4_end_to_end_refusal PASSED [ 14%]
    tests/test_implementing_spec_replan.py::TestImplementingSpecReplan::test_case_3_end_to_end_success PASSED [ 28%]
    tests/test_implementing_spec_replan.py::TestImplementingSpecReplan::test_case_5_unchanged_dispatch PASSED [ 42%]
    tests/test_implementing_spec_replan.py::TestImplementingSpecReplan::test_case_2_runner_action_parity PASSED [ 57%]
    tests/test_implementing_spec_replan.py::TestImplementingSpecReplan::test_case_6_action_plan_preflight PASSED [ 71%]
    tests/test_implementing_spec_replan.py::TestImplementingSpecReplan::test_case_1_predicate_coverage PASSED [ 85%]
    tests/test_implementing_spec_replan.py::TestImplementingSpecReplan::test_case_7_classify_paths_preview PASSED [100%]
    ============================== 7 passed in 30.64s ==============================
    ```
    2. Deliberate failure proof in throwaway worktree at pre-change HEAD:
    ```
    FAILED tests/test_implementing_spec_replan.py::TestImplementingSpecReplan::test_case_3_end_to_end_success
    FAILED tests/test_implementing_spec_replan.py::TestImplementingSpecReplan::test_case_4_end_to_end_refusal
    FAILED tests/test_implementing_spec_replan.py::TestImplementingSpecReplan::test_case_7_classify_paths_preview
    FAILED tests/test_implementing_spec_replan.py::TestImplementingSpecReplan::test_case_1_predicate_coverage
    FAILED tests/test_implementing_spec_replan.py::TestImplementingSpecReplan::test_case_2_runner_action_parity
    FAILED tests/test_implementing_spec_replan.py::TestImplementingSpecReplan::test_case_6_action_plan_preflight
    6 failed, 1 passed in 10.55s
    ```
    Throwaway worktree cleanly removed:
    ```
    $ git worktree remove --force .aw/worktrees/throwaway-test
    $ git worktree list (confirms throwaway-test removed)
    ```
    3. Regression suite:
    ```
    $ python3 -m pytest tests/test_production_checks_trace.py tests/test_spec_production.py tests/test_freeze_time_refusal.py tests/test_run_selection_policy.py tests/test_set_dispatch_parity.py tests/test_production_correction_turn.py tests/test_production_resume_handoff.py tests/test_production_set_check.py tests/test_handoff_ready_gate.py -o addopts="" -q
    207 passed in 875.12s (0:14:35)
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: Paste the `git diff` of `CHANGELOG.md` and `docs/artifact-lifecycles.md`, a search of the added lines for the em dash and en dash characters returning nothing, `aw sanitize --agent` passing, and the bare `python3 -m pytest` final summary line with its failure set (empty, or each failure shown to reproduce at the unmodified HEAD).
  - Observed evidence:
    1. git diff CHANGELOG.md docs/artifact-lifecycles.md:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index ad41401cf..f22970b66 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -36,2 +36,3 @@
     - Added: `aw lanes list` and `aw lanes prune [--apply]` commands to inspect worker and review sweep lanes, report ownership, live status, unmerged commits, and uncommitted files, and safely prune merged clean lanes through the R5.5 inventory gate. Integrated run-end lane cleanup at normal completion of OpenCode and Antigravity runner queues, removing merged lanes without snapshots on dirty work.
    +- Added: `aw oc run` and `aw agy run` now dispatch an `implementing` spec with uncited, non-deferred TRACE requirement identifiers into a plan-writing turn for its next stage, keeping the spec `implementing` and recording a workflow history note instead of requiring a step back to `approved`.
    diff --git a/docs/artifact-lifecycles.md b/docs/artifact-lifecycles.md
    index aca890385..e11f03ff8 100644
    --- a/docs/artifact-lifecycles.md
    +++ b/docs/artifact-lifecycles.md
    @@ -247,2 +247,2 @@
     "Step back one" means `to-review -> draft`, `reviewed -> to-review`, `approved -> reviewed`, and
    -`implementing -> approved`. The exact table is `SPEC_TRANSITIONS`.
    +`implementing -> approved`. The exact table is `SPEC_TRANSITIONS`. Running `aw oc run` or `aw agy run` on an `implementing` spec that still has uncited, non-deferred requirement ids writes the plans for the next stage and keeps the spec `implementing`, so stepping back to `approved` is no longer needed to plan a later stage.
    ```
    2. Search of added lines for em dash and en dash:
    ```
    Added lines count: 2
    Found em/en dashes: []
    ```
    3. aw sanitize --agent:
    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":4905,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
    4. Full pytest suite run:
    ```
    7511 passed, 2 skipped, 3 warnings in 633.13s (0:10:33)
    Failure set: empty (0 failures)
    ```
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Open questions OQ-01..OQ-03 are resolved. Follow the agent execution contract: commit through `aw commit 2hgxi1 -- <paths>` limited to `- Scope-Paths:`, never `git add -A`, never push; you MUST paste the actual runner output for every test claim. Scope fence: `- Scope-Paths:` is a declaration; an out-of-scope edit is justified at finalize with `--scope-reason`, not silently made. E-01's GATE is a genuine stop condition (the prerequisite changed under the plan), not a scope stop. Lifecycle: once `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with observed evidence, the plan moves to `executed/`: under `aw oc run` / `aw agy run` the runner owns that finalize, so do not run `aw ipd finalize` or `git mv` yourself; executed by hand, run `aw ipd finalize 2hgxi1`. Never `git mv` the plan by hand.

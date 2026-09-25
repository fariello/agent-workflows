# IPD: Remove the never-built --follow-generated run flag because nothing generates an IPD mid-run

- Date: 2026-09-24
- Kind: child
- Concern: `--follow-generated` (spec `25kzda` 2.1) is registered, appears in `--help`, and REFUSES (`runner_shared.RUN_POLICY_FLAGS` row `flag="--follow-generated"`, `implemented=False`). Backlog `ceauac` asks whether the behavior is wanted and how a generated IPD would be detected. MEASURED: nothing in the runner can generate an IPD during a run, nothing reads back what a turn created, and the queue cannot admit one. The flag follows a thing that does not exist, and its refusal names an owner (`backlog x8diyb`) that is already `done`, so an operator who hits it is pointed at a closed item.
- Scope: REMOVE `--follow-generated` from the shared flag table (both hosts register from it), update the docstrings that name it, add a regression test proving both host parsers reject it, amend spec `25kzda` so every mention states the report-only behavior plainly and records why same-run following is not offered, correct the stale `x8diyb` owner sentence in spec `z7nbn1` 3.4, and add a CHANGELOG line. EXCLUDES building any production action (`--action plan` stays refused; spec `z7nbn1` owns it), any generated-artifact reporting (no producer exists), and any change to `refuse_unimplemented_run_flags` as a mechanism (it stays, with no current row).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_runner_shared.py, .aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md, .aw/records/specs/to-review/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: medium
- Set: followgen
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: hzdq8y
- From-Backlog: ceauac

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog ceauac; re-measured that no run outcome across 481 recorded turns ever created a plan outside its frozen manifest, that `files_changed`/`recommended_next_action` are never parsed back, and that `--action plan` is refused, so the plan removes the flag rather than designing detection.

## Goal

Stop advertising a run flag whose subject cannot occur. Remove `--follow-generated` from the CLI and from spec `25kzda`, keep the spec's report-only rule for generated IPDs (so a future production action inherits the safe default), and record why same-run following is not offered.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Regression test first

- [ ] E-01 Add a test class `FollowGeneratedRemovedTests` to `tests/test_runner_shared.py` asserting (a) `"--follow-generated" not in runner_shared.RUN_POLICY_FLAGS_BY_FLAG` and `"follow_generated" not in runner_shared.RUN_POLICY_FLAGS_BY_DEST`; (b) `oc_runipd.build_parser().parse_args(["start", "abc123", "--follow-generated"])` and the same on `agy_runipd.build_parser()` raise `SystemExit` with code 2 (argparse unknown argument); (c) the spec `25kzda` file contains no `--follow-generated` token. Run it against the unmodified tree and confirm it FAILS.
  - Depends on: none
  - Expected outcome: the new test exists and fails on the current tree because the flag is still registered and the spec still names it.
  - Execution state: pending

### Task group 2: Remove the flag

- [ ] E-02 In `agent_workflows/runner_shared.py`, delete the `RunPolicyFlag(flag="--follow-generated", ...)` row from `RUN_POLICY_FLAGS`. Update the `refuse_unimplemented_run_flags` docstring (it says "This is the honest end state for `--follow-generated` and `--with-dependencies`") to say the mechanism is retained for any future registered-but-unbuilt flag and that no row currently uses it. Do not delete the function or its call in `initialize_run_core`.
  - Depends on: E-01
  - Expected outcome: `rg -n "follow.generated" agent_workflows` returns no hit; both host parsers reject the flag; the E-01 parts (a) and (b) pass.
  - Execution state: pending

- [ ] E-03 Confirm old run state stays resumable: `apply_run_policy_flags_on_resume` and `freeze_run_policy_flags` iterate `RUN_POLICY_FLAGS` only, so a stale `options["follow_generated"]: false` key in a pre-removal `state.json` is inert. Prove it with a one-off probe under `/tmp/opencode/g2/probe-followgen/` that loads a state dict carrying `follow_generated: False`, calls `runner_shared.apply_run_policy_flags_on_resume(state, argparse.Namespace())`, and shows it returns `False` without raising. No code change unless the probe fails; if it fails, STOP and report.
  - Depends on: E-02
  - Expected outcome: probe prints `changed=False` and no traceback.
  - Execution state: pending

### Task group 3: Spec and docs

- [ ] E-04 Amend spec `25kzda` (`.aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`): remove `[--follow-generated]` from the 2.1 synopsis; drop it from the `--full-auto` "does not imply" list; replace the 2.1 bullet "`--follow-generated` adds newly generated IPDs ..." with a bullet stating generated IPDs are ALWAYS reported as generated next actions and never join the frozen run, with the reason (the frozen queue is what resume reads, and no producer exists; see this plan `hzdq8y`); reword the "generated child is recorded but excluded because `--follow-generated` was not selected" endpoint, the two dispatch-table cells "Do not run the generated IPD(s) unless `--follow-generated` is present", DAG rule 10, the "Generated child" consent-table row, and the worked `spec09` example, so each says report-only without naming the flag. Append a `## Workflow history` line recording the amendment and its cause.
  - Depends on: E-02
  - Expected outcome: `rg -n "follow-generated" <spec>` returns nothing; `rg -n "generated next action" <spec>` still returns the report-only rule; E-01 part (c) passes.
  - Execution state: pending

- [ ] E-05 In spec `z7nbn1` section 3.4, replace "the repository has an unimplemented flag reserving the question (`--follow-generated`, measured `implemented=False`, owner backlog `x8diyb`)" with a sentence stating the flag was removed by plan `hzdq8y` because no producer existed, and that a plan building production actions may reintroduce an opt-in if the maintainer wants one. Do NOT edit the OQ-01 Resolution text (a recorded maintainer ruling). Add one CHANGELOG bullet under the pending 2.0.0 entry: "Removed the `--follow-generated` run flag. It was never implemented and always refused. Plans created during a run are reported as next actions, as before."
  - Depends on: E-04
  - Expected outcome: `rg -n "x8diyb" <z7nbn1 spec>` shows only the untouched OQ-01 ruling; `rg -n "follow-generated" CHANGELOG.md` shows the new bullet.
  - Execution state: pending

### Task group 4: Full suite

- [ ] E-06 Run the bare suite `python3 -m pytest` with no extra flags.
  - Depends on: E-05
  - Expected outcome: the summary line reports 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Both hosts register spec 2.1 flags from one table, `runner_shared.RUN_POLICY_FLAGS`, via `register_run_policy_flags`, so one row deletion removes the flag from `aw oc run` and `aw agy run` together.
- `RunPolicyFlag.implemented=False` means registered-and-refusing; `refuse_unimplemented_run_flags` raises `RunFlagRefusal` naming `row.owner`.
- Specs are living contracts; a plan that changes described behavior amends the spec and declares it in `- Scope-Paths:` (AGENTS.md "A PLAN MAY AMEND A SPEC").
- Commit through `aw commit hzdq8y -- <paths>`; CHANGELOG prose has no em/en dashes.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Re-measured at HEAD `cfc7f5c1`:

1. NO PRODUCER. `run_selection_policy.ACTION_PLAN` is the only action that would author an IPD (spec rows "`approved`: author conformant IPDs", "`open`: graduate"). It is registered and refused: `runner_shared` docstring near `ACTION_IMPLEMENTED`: "that action is registered and REFUSED (`ACTION_IMPLEMENTED` excludes it)". `refuse_unrunnable_selected_types` refuses any non-`ipd` selection, so a spec or backlog item cannot even be queued.
2. NO DETECTION INPUT. `files_changed` and `recommended_next_action` appear only in the outcome schema text inside the turn prompt (`runner_shared` prompt builder, `"files_changed": [],`). `rg '\.get\("files_changed|\.get\("recommended_next_action'` over `agent_workflows/` returns nothing: they are written by agents and never read. `collect_earned_paths` reads the git diff, but only to decide closes.
3. NO QUEUE GROWTH. The queue is built once in `initialize_run_core` (`queue.append(` inside `for position, id6 in enumerate(queue_ids, start=1)`); spec `25kzda` DAG rule 11 "The queue never incorporates unrelated files discovered after freezing", and spec `z7nbn1` OQ-01 records why: "the frozen `state['queue']` is what `resume` reads".
4. NO OCCURRENCE IN PRACTICE. Probe `/tmp/opencode/g2/probe-followgen/p.py` over the main checkout's `.aw/records/runs/*/outcomes/*.json`: 481 outcomes, 446 listing a `plans/pending/*.ipd.md` path, 181 naming a plan other than the item's own, and exactly 1 naming a plan absent from its run's frozen manifest (`uvwqvz` in run `run-20260924T050407Z-3108751`, item `68uhp0`). That plan was ADDED by commit `df792b59` on 2026-09-23, before the run; the turn's summary says it migrated existing orchestrator checklists. So zero turns generated a new IPD.
5. STALE OWNER. The row's `owner="backlog x8diyb (rundepflags-01)"` names an item filed under `.aw/records/backlog/done/`; the refusal message points operators at closed work.
6. RESUME IS SAFE. 161 of 261 recorded `state.json` files carry `follow_generated` in `options`; `apply_run_policy_flags_on_resume` and `freeze_run_policy_flags` iterate the table, not the stored keys, so a leftover key is ignored (confirmed in E-03).

## Proposed changes (ordered, validatable)

1. Failing regression test (E-01).
2. Delete the table row and fix the docstring (E-02); prove old state resumes (E-03).
3. Amend spec `25kzda` to report-only wording with the reason (E-04); fix `z7nbn1` 3.4 and CHANGELOG (E-05).
4. Bare suite (E-06).

## Deferred / out of scope (with reason)

- Building a production action that authors IPDs mid-run (`--action plan`) and reporting what it created.
  - Carrier: z7nbn1
- Re-introducing a same-run opt-in once a producer exists. Nothing to design until then; the maintainer can ask for it in the plan that builds production actions.
  - Carrier-Declined: no producer exists to follow; spec `z7nbn1` OQ-01 already fixes the default as report-only, and E-05 leaves a pointer in its 3.4.

## Scope check

- Over-scope: none. The `z7nbn1` edit is one sentence that names this flag and its dead owner.
- Under-scope: backlog `ceauac` itself is not transitioned here; the graduating workflow sets it `graduated`.

## Required tests / validation

- New `FollowGeneratedRemovedTests` fails before E-02/E-04 and passes after.
- Resume probe shows a stale key is inert.
- `rg` checks for zero `follow.generated` hits in `agent_workflows/` and spec `25kzda`.
- Bare `python3 -m pytest` passes.

## Spec / documentation sync

- Spec `25kzda` (approved) is AMENDED in E-04. WHY: it describes a flag whose subject cannot arise; leaving it makes every plan reviewed against 2.1 inherit a phantom obligation, and it is what made backlog `ceauac` exist. The report-only rule for generated IPDs is KEPT, so no contract weakens.
- Spec `z7nbn1` (to-review) section 3.4 is corrected in E-05; its OQ-01 ruling text is untouched.
- CHANGELOG gains one bullet (E-05).

## Open questions

### OQ-01: Remove the flag, or design detection of generated IPDs?

- Blocking: yes
- Status: resolved
- Owner: none
- Resolution or deferral rationale: REMOVE. Findings 1 to 4: the only producer (`--action plan`) is refused, the outcome fields that could carry a detection are never parsed, the queue is frozen by design, and 0 of 481 recorded turns generated an IPD. Detection would be "invent the missing half", the shape superseded plan `kaygwo` E-07 already drew NEEDS REPLAN for.

### OQ-02: Does removal sit with the maintainer's z7nbn1 OQ-01 ruling?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: That ruling (2026-09-16) says `--follow-generated` "becomes the opt-in mechanism for the same-run behavior" once implemented, with report-only as the default. DEFAULT: proceed with removal. The default behavior is identical, and the plan that builds production actions can re-add an opt-in if one is wanted. If the maintainer prefers to keep the reserved flag, drop E-04/E-05's removal wording and instead re-point the row's `owner` to `spec z7nbn1`, which fixes Finding 5 alone.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_runner_shared.py -k FollowGeneratedRemoved` run on the tree BEFORE E-02, showing it FAILING (expected: at least one `failed`, with an assertion naming `--follow-generated`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "follow.generated" agent_workflows` (expected: no output, exit 1) and the same pytest command as V-01 after E-02, showing parts (a) and (b) pass.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the probe command and its output (expected: `changed=False`, no traceback).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `rg -n "follow-generated" .aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` (expected: no output) and `rg -n "generated next action" <same path>` (expected: the new report-only bullet), plus the V-01 pytest command now fully passing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `rg -n "x8diyb|hzdq8y" .aw/records/specs/to-review/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md` (expected: `hzdq8y` in 3.4, `x8diyb` only in the OQ-01 ruling) and `rg -n "follow-generated" CHANGELOG.md` (expected: one bullet).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the final summary line of bare `python3 -m pytest` (expected: `N passed`, 0 failed).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after `Status: approved`. Commit through `aw commit hzdq8y -- <Scope-Paths>`, never push. After every V item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `executed/` through the lifecycle transition.

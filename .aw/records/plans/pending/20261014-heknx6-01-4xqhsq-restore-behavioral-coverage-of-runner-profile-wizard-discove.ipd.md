# IPD: Restore behavioral coverage of runner_profile_wizard discovery-failure reporting and manual-entry flows

- Date: 2026-10-14
- Kind: child
- Concern: `runner_profile_wizard` guarantees (module docstring behavior 1) that a failed model discovery is reported with its NAMED reason and falls through to EXACT MANUAL ENTRY rather than refusing or green-washing, and that manual entry is always reachable, schema-validated, and bounded; the behavioral tests for these flows were deleted with `tests/test_runner_profile_wizard.py` in `19313eed`, and the only surviving coverage (`tests/test_cli.py` `test_wizard_failure_is_reported_not_raised`) mocks `run_session` away entirely, so a regression in either flow would now go undetected.
- Scope: Add one new behavioral test module driving `runner_profile_wizard._report_catalog`, `select_model`, `ask_model_manual` and `run_wizard` through a scripted injected `WizardIO` (no TTY, no OpenCode, no user config), asserting on emitted lines, returned models, `WizardResult` fields and store write counts; then update the stale "no live guard currently asserts these five behaviors" remark in the module docstring to name the new module for behavior 1 and manual entry.
- Scope-Paths: tests/test_runner_profile_wizard_discovery.py, agent_workflows/runner_profile_wizard.py, .aw/records/plans/pending/20261014-heknx6-01-4xqhsq-restore-behavioral-coverage-of-runner-profile-wizard-discove.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: heknx6
- Set: heknx6
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: 4xqhsq

## Workflow history
- 2026-10-15 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed (review record 20261014-heknx6-01-4xqhsq)
- 2026-10-14 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored from backlog heknx6; review-ready.

## Goal

Restore, as behavioral tests only (P16), coverage that the runner-profile wizard (a) names the reason discovery failed on screen for every named failure reason and still lets the user finish a profile by typing an exact model id, and (b) offers manual entry from a live catalog, validates it through the schema, and gives up after a bounded number of attempts without writing anything. Lost with `tests/test_runner_profile_wizard.py` (`ev7t1w` site S-25, disposition RETIRE-UNGUARDED).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: discovery-failure tests

- [ ] E-01 Create `tests/test_runner_profile_wizard_discovery.py` with local helpers re-implemented from `19313eed7^:tests/test_runner_profile_wizard.py` `_Script` (scripted `ask` popping answers and raising `EOFError` when exhausted; `emit` recording lines) and `_Store` (injected `load`/`save` counting writes), and a `unittest.TestCase` whose `setUp` calls `support.declare_execution_role(self)`. Add `test_every_failure_reason_is_named_on_screen`: for each of `oc_models.CATALOG_MISSING_BINARY`, `CATALOG_TIMED_OUT`, `CATALOG_NONZERO_EXIT`, `CATALOG_UNPARSEABLE`, `CATALOG_NO_MODELS` (as `subTest`), build `oc_models.ModelCatalog(source=CATALOG_SOURCE_NONE, reason=R, detail=f"detail-{i}")` (the detail MUST NOT contain the reason string, or a mutation dropping `catalog.reason` would still pass via the detail), call `runner_profile_wizard._report_catalog`, and assert the emitted text contains `R` and `detail-{i}` and an instruction to enter an exact provider/model id (`"exact provider/model"`), and does NOT contain `"Found "` (no green-wash). Add `test_config_fallback_still_names_the_cli_failure`: a `CATALOG_SOURCE_CONFIG` catalog with two models and `reason=CATALOG_TIMED_OUT` emits that reason AND the model count. Add `test_dead_catalog_falls_through_to_manual_entry_and_saves`: drive `run_wizard(io)` with a `CATALOG_SOURCE_NONE` catalog and the script `["gem", "example/private-model", "", "", "", "", ""]` (name, manual model, variant default, no agent, save default yes, default-profile and default-runner answers: with an empty store both default questions are asked, so all seven answers are consumed), and assert the script is exhausted, `result.saved is True`, `result.profile.model == "example/private-model"`, the store recorded exactly one write, the emitted text names the failure reason, and no numbered model line (`"  [1] "`) was emitted before the manual-entry prompt (record `ask` and `emit` calls in one ordered event list so "before" is checkable; the variant menu legitimately emits `"  [1] "` afterwards).
  - Depends on: none
  - Expected outcome: the module exists and all three tests pass against current code.
  - Execution state: pending

### Task group 2: manual-entry tests

- [ ] E-02 In the same module add a `ManualEntryTests` class: `test_m_reaches_manual_entry_from_a_live_catalog` (a `CATALOG_SOURCE_CLI` catalog with one model; script `["m", "example/unlisted"]`; `select_model` returns `"example/unlisted"`, proving a private model absent from the catalog is reachable); `test_invalid_ids_are_refused_then_a_valid_one_accepted` (dead catalog; script `["", "not a model", "example/ok"]`; `select_model` returns `"example/ok"` and the emitted text contains the "required" message and a schema refusal line for `not a model`); `test_manual_entry_is_bounded` (dead catalog; script `["bad"] * (MAX_ATTEMPTS + 2)`; `select_model` raises `WizardCancelled`, and the number of recorded prompts equals `MAX_ATTEMPTS`); and `test_exhausted_manual_entry_writes_nothing` (`run_wizard` with a dead catalog and a name followed by `MAX_ATTEMPTS` invalid ids returns `saved is False`, `cancelled is True`, `reason == "cancelled"`, and the store recorded zero writes).
  - Depends on: E-01
  - Expected outcome: the four manual-entry tests pass against current code.
  - Execution state: pending

### Task group 3: stale remark

- [ ] E-03 In `agent_workflows/runner_profile_wizard.py`, edit the module-docstring sentence "each had a named falsifier in `tests/test_runner_profile_wizard.py` (deleted in `19313eed`; no live guard currently asserts these five behaviors)" so it states that behavior 1 and the manual-entry path are asserted by `tests/test_runner_profile_wizard_discovery.py` while behaviors 2-5 remain without a live guard. Docstring-only change; no behavior change.
  - Depends on: E-02
  - Expected outcome: the docstring names the new live module and no longer claims all five behaviors are unguarded.
  - Execution state: pending

## Project conventions discovered (Step 0)

- P16 (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): drive the code and assert outputs; never read source via `inspect`/`ast`/regex. The deleted module imported `ast` for source pins elsewhere; the new module must not.
- `runner_profile_wizard.WizardIO` is dependency-injected on purpose (module docstring "DEPENDENCY-INJECTED ON PURPOSE"): `ask`, `emit`, `discover`, `load`, `save` are all injectable, so no TTY, subprocess or user config is needed.
- Suite runs bare as `python3 -m pytest` (`-n auto`); tests must be xdist-safe and call `support.declare_execution_role(self)` (`tests/support.py` `declare_execution_role`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- Executed plan `ev7t1w` (`.aw/records/plans/executed/20261011-iosmvn-03-ev7t1w-retire-or-repoint-the-dangling-test-citations-in-the-non-run.ipd.md`) row S-25: `runner_profile_wizard.py` / module docstring / `tests/test_runner_profile_wizard.py` / `19313eed` / RETIRE-UNGUARDED; "`tests/test_cli.py` only tests error handling in the setup flow".
- `19313eed7^:tests/test_runner_profile_wizard.py` held `test_the_dead_catalog_report_names_the_reason_it_failed` and `ManualEntryTests.test_manual_entry_gives_up_after_a_bounded_number_of_attempts`, both scripted-IO behavioral tests; they are the model for E-01/E-02.
- Verified at review by a scripted-IO probe against current code: the E-01 end-to-end script consumes all seven answers and saves once with `model == "example/private-model"`; `select_model` on a dead catalog with `["bad"] * 7` raises `WizardCancelled` after exactly 5 prompts; `run_wizard` with a name plus 5 invalid ids returns `saved=False, cancelled=True, reason="cancelled"` with zero writes; `["", "not a model", "example/ok"]` returns `example/ok` and emits `A model identifier is required` and `invalid model 'not a model'`; `["m", "example/unlisted"]` on a live catalog returns `example/unlisted`.
- `runner_profile_wizard.select_model` returns `ask_model_manual(io)` immediately when `not catalog.available`, and on input `m` otherwise; `ask_model_manual` validates via `runner_profiles.validate_model` and raises `WizardCancelled("too many invalid model identifiers")` after `MAX_ATTEMPTS`.
- `runner_profile_wizard._report_catalog` has three branches keyed on `catalog.source` (`CATALOG_SOURCE_CLI`, `CATALOG_SOURCE_CONFIG`, otherwise), each emitting different text; E-01 covers the two degraded branches.
- `rg -l runner_profile_wizard tests/` returns only `tests/test_cli.py`, whose single use patches `run_session` with a `RuntimeError` side effect.

## Proposed changes (ordered, validatable)

1. E-01: new module, discovery-failure reporting and fall-through-to-manual end to end.
2. E-02: manual-entry reachability, validation, and bounded termination with zero writes.
3. E-03: docstring-only update in `runner_profile_wizard`.

## Deferred / out of scope (with reason)

- Restoring the rest of the deleted module (paging/filtering, variant, preview, save-outcome, default questions, byte-identical config, credential-leak tests): not part of backlog `heknx6`, which names only discovery-failure and manual-entry flows.
  - Carrier-Declined: outside this backlog item's named property; no defect is known in those areas.
- Restoring `oc_models.discover_models` failure-classification tests (`CatalogDiagnosticTests`): those test `oc_models`, not the wizard's interactive flow.
  - Carrier-Declined: different module and property from the one this item names.
- Any behavior change to the wizard: this is coverage restoration.
  - Carrier-Declined: deliberate non-goal, not an outstanding obligation.

## Scope check

- Over-scope: none. The only production edit is a docstring sentence that would otherwise become partly false.
- Under-scope: none. Both named flows (discovery failure, manual entry) are covered, including the end-to-end save through `run_wizard`.

## Required tests / validation

- `python3 -m pytest tests/test_runner_profile_wizard_discovery.py` passes (V-01, V-02).
- Mutation check: temporarily make `_report_catalog`'s final branch omit `catalog.reason` (keep the detail), confirm `test_every_failure_reason_is_named_on_screen` FAILS, then revert with `git checkout -- agent_workflows/runner_profile_wizard.py` BEFORE E-03 edits that file (V-01).
- Mutation check: temporarily make `ask_model_manual` loop `MAX_ATTEMPTS + 1` times, confirm `test_manual_entry_is_bounded` FAILS, then revert with `git checkout -- agent_workflows/runner_profile_wizard.py` BEFORE E-03 (V-02).
- Full bare suite `python3 -m pytest` with no new failures (V-03).

## Spec / documentation sync

N/A: no spec or user-facing documentation describes these tests; the only text change is the module docstring in E-03.

## Open questions

### OQ-01: New module or re-create `tests/test_runner_profile_wizard.py`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: a new purpose-named module `tests/test_runner_profile_wizard_discovery.py`. Re-creating the deleted name would imply all five behaviors are guarded again, which the docstring would then misstate; sibling restoration plans (`55kl2u`, `yfo6z6`) likewise use purpose-named modules.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -v tests/test_runner_profile_wizard_discovery.py` showing the three E-01 tests PASSED; pasted output of the temporary `_report_catalog` mutation run showing `test_every_failure_reason_is_named_on_screen` FAILED (with all five subTests reporting the missing reason), followed by an empty `git diff --stat agent_workflows/runner_profile_wizard.py` proving the mutation was reverted; plus `grep -nE "inspect|import ast|read_text" tests/test_runner_profile_wizard_discovery.py` returning no match.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted `-v` pytest output showing the four `ManualEntryTests` PASSED; pasted output of the temporary `ask_model_manual` bound mutation showing `test_manual_entry_is_bounded` FAILED, followed by an empty `git diff --stat agent_workflows/runner_profile_wizard.py` proving it was reverted.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff agent_workflows/runner_profile_wizard.py` showing only docstring lines changed and naming `tests/test_runner_profile_wizard_discovery.py`; AND the pasted summary line of a bare `python3 -m pytest` run with no new failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`aw ipd set approved 4xqhsq --by-human`); OQ-01 is resolved and no question blocks. Begin with `aw ipd begin 4xqhsq`.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. STOP only for a genuinely unsafe condition: a concurrent edit to `agent_workflows/runner_profile_wizard.py` that cannot be safely combined, or a cited symbol (`_report_catalog`, `select_model`, `ask_model_manual`, `run_wizard`, `MAX_ATTEMPTS`) that no longer exists.

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never claim a result you did not run. Both mutations are temporary and MUST be reverted before E-03; no mutation may be committed.

Commits: commit only the Scope-Paths files you changed through `aw commit 4xqhsq -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize; when executed by hand, run `aw ipd finalize 4xqhsq` only after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`.

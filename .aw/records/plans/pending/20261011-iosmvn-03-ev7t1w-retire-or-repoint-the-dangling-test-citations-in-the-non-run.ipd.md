# IPD: Retire or repoint the dangling test citations in the non-runner shipped modules

- Date: 2026-10-11
- Kind: child
- Concern: Seventeen non-runner modules under `agent_workflows/` carry 27 comment/docstring citations of test files that commit `19313eed` deleted, that do not exist at HEAD, that no sibling plan owns, and whose surrounding prose (3 lines either side) does not already name `19313eed`. Several are load-bearing claims that a property is guarded (`check_engine.check_spec_review_attestation` names an "anti-duplication guard ... enforces its absence"; `plan_readiness.approval_refusals` names "an explicit anti-fork guard test"; `plans` names its "repo drift-guard test"). Measured at authoring HEAD `8538be828` with the Set measurement command over the 17 files in Scope-Paths: `UNRETIRED 27`.
- Scope: IN: comment and docstring prose at the 27 sites in Findings, each dispositioned REPOINT, RETIRE-PIN or RETIRE-UNGUARDED (definitions in sibling `9rthek` Project conventions), preserving each comment's design reason. Three sites (S-02, S-03, S-07) already describe their test in the past tense without naming the commit; they are brought to the same form by naming `19313eed`. OUT: any executable change; restoring any test; `tools/lost_guard_census.py` (its two hits are classifier fixtures that read deleted blobs via `git show 19313eed^:...`/`80db6750c^:...`, which is correct usage and not a citation, see F-01); the `ipd_lifecycle._run_record_committed_paths` incident narrative naming `tests/test_orchestrator_probe_cache.py` as a path a past plan declared (F-02: accurate history, not a guard claim); filing backlog (Order 04 `ellenm`).
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/artifact_naming.py, agent_workflows/artifact_types.py, agent_workflows/attention.py, agent_workflows/check_engine.py, agent_workflows/cli.py, agent_workflows/ipd_lifecycle.py, agent_workflows/lane_containment.py, agent_workflows/plan_readiness.py, agent_workflows/plans.py, agent_workflows/prompts.py, agent_workflows/pwatch.py, agent_workflows/render_stream.py, agent_workflows/run_cli.py, agent_workflows/runner_profile_wizard.py, agent_workflows/selectors.py, agent_workflows/work_cmd.py, .aw/records/plans/pending/20261011-iosmvn-03-ev7t1w-retire-or-repoint-the-dangling-test-citations-in-the-non-run.ipd.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: iosmvn
- Set: iosmvn
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ev7t1w

## Workflow history

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog `iosmvn`; 27 sites measured at HEAD `8538be828`.

## Goal

Make every residual `19313eed` dangling test citation in the non-runner shipped modules truthful, so a reader of `check_engine`, `plan_readiness`, `selectors` and the rest is never told that a nonexistent test guards a property.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Measure

- [ ] E-01 Re-measure at execution HEAD: run the Set measurement command over the 17 source files in Scope-Paths and record the hit list, `UNRETIRED N`, and `git rev-parse --short HEAD`. Match sites by enclosing symbol and cited path; disposition any delta by the same rules.
  - Depends on: none
  - Expected outcome: recorded list equals Findings S-01..S-27, or each delta carries a disposition.
  - Execution state: pending

- [ ] E-02 For each site, decide REPOINT / RETIRE-PIN / RETIRE-UNGUARDED and record a `Site | Disposition | Evidence` table appended to Findings, with evidence of the kinds the Set conventions require. For S-08 (`test_no_hardcoded_reviews_path_in_check_engine`) and S-10 (occurrence-counting test), RETIRE-PIN is expected because the deleted tests read `check_engine` source; confirm from `git show 19313eed^:<path>`.
  - Depends on: E-01
  - Expected outcome: 27 (plus deltas) dispositioned rows, each with evidence.
  - Execution state: pending

### Task group 2: Edit

- [ ] E-03 Apply the dispositions as comment/docstring edits, keeping each design reason and, for both RETIRE forms, naming `19313eed` within three lines of the citation in the established wording ("deleted in `19313eed`; no live guard currently asserts this"). Where a docstring sentence would otherwise read as live enforcement ("there is an explicit anti-fork guard test at ..."), rewrite the tense, not just append a note.
  - Depends on: E-02
  - Expected outcome: measurement over the 17 files prints `UNRETIRED 0`.
  - Execution state: pending

- [ ] E-04 Prove prose-only and regression-free: run the AST-equivalence command against the E-01 HEAD over the 17 source files, and the bare suite `python3 -m pytest`.
  - Depends on: E-03
  - Expected outcome: `AST-DIFFER []`; suite summary with no failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- SET MEASUREMENT COMMAND and AST-EQUIVALENCE COMMAND: verbatim as recorded in sibling plan `yuhl6o` (Order 01) Project conventions; this plan passes its 17 source files as arguments.
- Disposition definitions: as in sibling plan `9rthek` Project conventions.
- `tests/test_docs_test_citations.py` `HISTORICAL_EXEMPTIONS` is the precedent that a past-tense mention of a retired test is acceptable prose; the measurement requires the commit to be named so the form is uniform and machine-checkable.
- Run the suite bare: `python3 -m pytest`. Cite code by symbol.

## Findings

Measured at HEAD `8538be828`.

| Site | File | Enclosing symbol | Cited path |
|---|---|---|---|
| S-01 | `artifact_core.py` | `global_id6s` | `tests/test_id6_global_mint.py` |
| S-02 | `artifact_core.py` | module (`SCAN_ROOTS`) | `tests/test_artifact_core.py::ScanRootClassificationInvariantTests` |
| S-03 | `artifact_naming.py` | module docstring | `tests/test_naming_authority_single_source.py` |
| S-04 | `artifact_types.py` | module docstring | `tests/test_awcmdsurf_vocab_and_parsers.py` |
| S-05 | `attention.py` | module (prefix-parse note) | `tests/test_naming_authority_single_source.py` |
| S-06 | `check_engine.py` | `check_scope_drift` | `tests/test_ci_check_parity.py` |
| S-07 | `check_engine.py` | `check_release_gate_consistency` | `tests/test_bug_gate_check.py` |
| S-08 | `check_engine.py` | `check_spec_review_attestation` | `tests/test_review_findings.py::test_no_hardcoded_reviews_path_in_check_engine` |
| S-09 | `check_engine.py` | `evaluate_durable_carrier` | `tests/test_durable_capture.py` |
| S-10 | `check_engine.py` | `check_ipd_lint_reach` | `tests/test_review_decisions.py` |
| S-11 | `check_engine.py` | `check_ipd_lint_reach` | `tests/test_durable_capture.py` |
| S-12 | `cli.py` | `_build_parser` | `tests/test_run_dispatch.py` |
| S-13 | `cli.py` | `_build_parser` | `tests/test_work_kind.py::test_the_cli_choices_match_the_shared_vocab` |
| S-14 | `ipd_lifecycle.py` | `runner_owns_lifecycle_notice` | `tests/test_reporting_contract.py::DriverPromptTests::test_prompts_are_pure_ascii` |
| S-15 | `lane_containment.py` | module (`MISSING_INPUT_VERDICT_*`) | `tests/test_missing_input_repair.py` |
| S-16 | `lane_containment.py` | `evaluate_clean_base` | `tests/test_dirty_base_gate.py::test_the_tracked_scope_is_IDENTICAL_on_both_paths` |
| S-17 | `plan_readiness.py` | `approval_refusals` | `tests/test_review_findings_gate.py` |
| S-18 | `plan_readiness.py` | `recheck_conditions` | `tests/test_review_findings_gate.py` |
| S-19 | `plans.py` | module docstring | `tests/test_plan_status.py` |
| S-20 | `prompts.py` | `build_prompt_name` | `tests/test_naming_authority_single_source.py` |
| S-21 | `pwatch.py` | `main` | `tests/test_pwatch.py` |
| S-22 | `render_stream.py` | module (import rule) | `tests/test_refusal_surfacing.py` |
| S-23 | `render_stream.py` | `format_activity_cell` | `tests/test_render_stream.py` |
| S-24 | `run_cli.py` | `_emit_error` | `tests/test_run_cli_ledger_message.py` |
| S-25 | `runner_profile_wizard.py` | module docstring | `tests/test_runner_profile_wizard.py` |
| S-26 | `selectors.py` | module (precedence order) | `tests/test_selector_zero_open.py::PrecedenceForcesFrontMatterReadsTests` |
| S-27 | `work_cmd.py` | `run_commit` | `tests/test_work_primitives.py` |

| ID | Excluded hit | Reason |
|---|---|---|
| F-01 | `tools/lost_guard_census.py` `print_classifier`: `git_show(repo_root, "80db6750c^:tests/test_orchestrator_probe_cache.py")` and `mixed_example = "tests/test_dependency_verb.py"` | The census reads deleted blobs by design; these are inputs, not claims. Rewriting them would break the tool. |
| F-02 | `agent_workflows/ipd_lifecycle.py` `_run_record_committed_paths` docstring: "declaring its plan file, ``agent_workflows/runner_shared.py`` and ``tests/test_orchestrator_probe_cache.py``" | A dated incident narrative naming a path a past plan declared; true as history, asserts no guard. |

## Proposed changes (ordered, validatable)

1. E-01 re-measure. 2. E-02 disposition table. 3. E-03 prose edits. 4. E-04 AST-equivalence and bare suite.

## Deferred / out of scope (with reason)

- Filing backlog for RETIRE-UNGUARDED properties.
  - Carrier: ellenm
- F-01 and F-02 hits.
  - Carrier-Declined: not dangling claims (see Findings F-01, F-02); editing them would be wrong.
- An advisory check rule that flags new dangling source citations.
  - Carrier: j7daih

## Scope check

- Over-scope: none; prose only in 17 files, proven by E-04.
- Under-scope: none; all 27 measured sites have rows and an E-item; the two excluded hits are dispositioned in Findings.

## Required tests / validation

- Measurement over the 17 files -> `UNRETIRED 0`.
- AST-equivalence -> `AST-DIFFER []`.
- Bare `python3 -m pytest` with no failures.

## Spec / documentation sync

N/A: comment and docstring prose only; no `.spec.md` is touched.

## Open questions

### OQ-01: Are S-02, S-03 and S-07 already correct and therefore out of scope?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: They read in the past tense, but S-02 still says "see `tests/test_artifact_core.py::ScanRootClassificationInvariantTests`" as an instruction, and none names the commit. Bringing them to the uniform form costs three one-line edits and lets the Set's measurement reach zero without a special-case list.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted measurement output with `UNRETIRED N` and HEAD sha, deltas listed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the appended disposition table, one row per site, with pasted evidence for every REPOINT and RETIRE-UNGUARDED row and the `git show` excerpt for S-08 and S-10.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted post-edit measurement ending `UNRETIRED 0` and `git diff --stat` over the 17 files.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `AST-DIFFER []` and the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Commit through `aw commit ev7t1w -- <paths>` limited to the declared Scope-Paths; never push. Move to `executed/` only via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` is `pass` with pasted evidence.

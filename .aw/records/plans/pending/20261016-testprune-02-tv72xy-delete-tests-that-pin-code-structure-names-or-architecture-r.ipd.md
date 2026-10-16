# IPD: Delete tests that pin code structure, names or architecture rather than behavior

- Date: 2026-10-16
- Kind: child
- Concern: Prompt `4ul37x` categories 1 to 3 (code-structure pins, name and shape pins, architecture and change freezes) and `GUIDING_PRINCIPLES.md` P16 ("No production source inspection", "No count or census pins", "No text, banner, or docstring pins", "No architectural placement pins"). Research `offdhr` listed 53 files matching a heuristic scan and warned that "the word-based patterns over-match". Re-run and read while authoring this plan (main `6ea45c974`): the baseline's own pattern set now matches 56 files and 222 lines, and about 200 of those lines are FALSE POSITIVES, chiefly tests that build a throwaway repo containing an `agent_workflows/demo.py` fixture (`tests/test_ipd_lifecycle_cli.py`, `tests/test_commit_scope_reason.py`, `tests/test_finalize_disregarded_record.py`, `tests/test_lifecycle_holder_gate.py`, `tests/test_merge_gate_spec_anchors.py`, `tests/test_spec_citation_anchors.py`, `tests/test_check_engine_source_test_citation.py`) and docstrings that merely say "no inspect.getsource". The real pins are a different, smaller population found by wider patterns the baseline did not use (host-module identity `assertIs`, `hasattr` on production modules, `__doc__`, `len(<CONST>) ==`, `sys.modules` fences). Prior pass `ad9213cc6` already removed `tests/test_no_code_structure_pins.py` and several pins, so the residue is scattered single assertions inside otherwise behavioral tests rather than whole files.
- Scope: Using `qqrgv3`'s `tests/tools/pinscan.py` output (re-run at execution), classify every candidate by reading (true pin or false positive, with category); for each true pin choose DELETE (assertion or whole test), CONVERT (replace with a behavioral assertion that exercises the same contract), or KEEP (documented contract, or architecture freeze with a written compelling reason); execute in subsystem batches; record every deleted node id with category and one-line reason in the `qqrgv3` decision-table research record. Tests citing a backlog id6, plan id6 or incident lose only the pin assertion and keep their behavioral body; whole-test deletion applies only to tests whose sole assertions are pins. No production behavior change (at most a citing comment in `agent_workflows/worktree_lease.py`, only if a cited test is renamed).
- Scope-Paths: tests/, .aw/records/research/, agent_workflows/worktree_lease.py
- Item-Dependencies: executed:qqrgv3
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: high
- Set: testprune
- Order: 2
- Highest E allocated: 09
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: tv72xy
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): status set to reviewed
- 2026-10-16 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
- 2026-10-16 to-review (aw set): authored from prompt 4ul37x (Set testprune) with baseline research offdhr/7ry5kv

- 2026-10-16 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

No retained test fails because working code was moved, renamed, re-exported, reformatted, or had a docstring edited, while every documented contract (CLI verbs and flags, `aw.agent/v1` fields, exit codes, front-matter fields, filename grammar, documented Python API) and every stated security boundary stays tested by behavior, with each deletion recorded by node id and reason.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: classify

- [ ] E-01 Re-run `python3 -m tests.tools.pinscan` (from `qqrgv3`) on the execution base and also the baseline's original pattern set, so the 53-file population named by research `offdhr` is covered. Read EVERY hit and write a classification table into the `qqrgv3` decision-table research record (`file | test | line pattern | verdict (true-pin / false-positive) | category (structure / name-shape / arch-freeze) | action (delete / convert / keep) | reason`). The authoring-time pre-classification in Findings F-3 to F-9 is the starting point, not the result: confirm or correct each row, and add any row the re-run finds that did not exist at authoring.
  - Depends on: none
  - Expected outcome: every pinscan hit has exactly one row; counts per verdict, category and action are stated.
  - Execution state: pending

### Task group 2: delete and convert, in subsystem batches (one commit each)

- [ ] E-02 Runner host-identity and placement pins (`tests/test_runner_shared.py`, `tests/test_agy_runipd_cli.py`, `tests/test_oc_runipd.py`, `tests/test_records_only_lane_rederive.py`, `tests/test_terminal_status_vocabulary.py`, `tests/test_reaskscore_composed.py`, `tests/test_forkresid_shared_shells.py`, `tests/test_orchestrator_retirement.py`, `tests/test_orchestrator_shape_gate.py`, `tests/test_hostdedup_third_host.py`, `tests/test_runwire_verifier_authority.py`, `tests/test_runner_fallback_bindings.py`, `tests/test_attention.py` lane-probe `hasattr`). Remove `assertIs(<host>.X, runner_shared.X)` identity, `hasattr`/`not hasattr` on host modules, `__module__ ==`, and "exactly one definition site" assertions. Where the identity guarded a real cross-host behavior (backlog `s4jctz`/`h0zk2g` permissive `_read_id`; `DriverError` catchability across hosts; equal `SUCCESS_STATES` bar), keep or add the behavioral half that drives BOTH hosts with the same input and asserts the same output (the `BOTH` / `_MODULES` loop pattern already in `tests/test_runner_shared.py` `DriverErrorUnificationTests`). Tests left with no assertion are deleted.
  - Depends on: E-01
  - Expected outcome: no `assertIs` between host-module attributes and no `hasattr` on `oc_runipd`/`agy_runipd`/`runner_shared` remain in these files; each touched id6-citing test keeps a behavioral assertion; affected modules pass.
  - Execution state: pending
- [ ] E-03 Removed-symbol and private-name pins outside the runners: `tests/test_attention.py` and `tests/test_term.py` (`hasattr(att, "_STATUS_COLOR_256")`, `_CLASS_COLOR_256`), `tests/test_descriptive_refusal_hoist.py::test_public_hoisted_helper_exists` (`not hasattr(..., "_refuse_unsafe_descriptive")`), `tests/test_check_engine_metadata_region.py` (`hasattr(ce, "_read_item_id")` etc.), `tests/test_ipd_lint.py::test_the_dash_rule_code_is_gone_rather_than_merely_silent` (`hasattr(L, "C_DASH")`), `tests/test_host_capability_extension.py` (`hasattr(hsp, "CAP_DENY_PUSH")`, `hasattr(hsp, "_probe_egress_filtering")`), `tests/test_releases_cli.py` (`hasattr(releases, "run_check")`), `tests/test_turn_bounds.py` (`MAX_TURN_DEADLINE`), `tests/test_run_analytics_statistics.py` (`cache_write_per_mtok`), `tests/test_project_context.py` (`DURABLE_PRIVATE`). Rule: delete only the `hasattr` line when the same test already asserts the behavior (for example `tests/test_releases_cli.py` already asserts `releases check` exits 2, `tests/test_project_context.py` already asserts `normalize_durability_state("durable-private")`, `tests/test_run_analytics_statistics.py` already asserts `rate_for("cache_write")` raises, and `tests/test_ipd_lint.py`'s table already proves the dash rule never fires), and delete the whole test when the `hasattr` is its only assertion.
  - Depends on: E-01
  - Expected outcome: no `hasattr` on a production module or class remains in these files except where E-01 recorded KEEP with a contract reason; affected modules pass.
  - Execution state: pending
- [ ] E-09 Convert `tests/test_agy_run.py::test_re_exports_and_interface_parity` (six `hasattr` lines on `tools/antigravity_execute_ipd.py`) into a behavioral test that invokes the documented compat entry point (`tools/README.md` "backwards-compatible wrapper that delegates directly to `tools/agy_run.py`") with `--help` and asserts exit 0 and the delegated parser's usage line, since a working wrapper is the contract.
  - Depends on: E-01
  - Expected outcome: the converted test passes and contains no `hasattr`.
  - Execution state: pending
- [ ] E-04 Docstring and prose pins: `tests/test_oc_runipd.py::test_the_docstring_states_that_a_bucket_is_not_a_readiness` (`plan_bucket.__doc__`), `tests/test_host_sandbox_profile.py::test_module_publishes_its_guarantees` (`hsp.__doc__`), `tests/test_completion_stale_notice.py::test_test_completion_docstring_updated` (a test module's docstring). Delete each; before deleting the `plan_bucket` one, confirm that a behavioral test exercises `oc_runipd.edge_satisfied` with a `reviewed`/`approved` external target (the defect the docstring records), and add one if none exists. README/AGENTS/docs prose tests (`tests/test_completion_stale_notice.py::test_readme_tab_completion_section`, `tests/test_agents_block_target_neutral.py`, `tests/test_spec_review_attestation.py`, `tests/test_run_analytics_privacy_docs.py`, `tests/test_authoring_coverage_guidance.py`) read published documentation or workflow bodies, which P16's "one narrow exception" ("the text or file itself is the artifact under test") permits: E-01 records them KEEP or hands them to `83nnyn` for consolidation, and this item does not delete them.
  - Depends on: E-01
  - Expected outcome: no assertion on a production `__doc__` remains; the `edge_satisfied` review-target behavior is covered by a named test.
  - Execution state: pending
- [ ] E-05 Count, census and vocabulary-size pins: `len(<CONST>) == N` where the set's MEMBERS are not otherwise asserted (`tests/test_runwire_verifier_authority.py::test_set_level_checks` vocabulary sizes; `tests/test_fix_it_global_caps.py` `len(FIX_IT_COUNT_KEYS) == 13`; `tests/test_finalize_stale_plan_path.py` `len(VERIFY_ABSENCE_CODES) == 4`; `tests/test_ipd_exec_finding_codes.py`; `tests/test_run_selection_policy.py` `len(SPEC_TYPE_ORDER) == 7`; `tests/test_run_analytics.py` `len(ABSENT_PROVENANCE) == 3`; `tests/test_attention_contract.py` `len(RULE_IDS) >= 12`). Rule: a size pin on a spec-enumerated closed vocabulary is a documented contract only if it is asserted as the exact member set against the spec; convert a bare `len` to a member-set equality where the spec enumerates the members (cite the spec section in the test), and delete it where it duplicates a sibling member-set assertion or no spec enumerates it. `tests/test_fix_it_global_caps.py` keeps its behavioral `fix_it_turns_spent(item) == len(keys)` sum, which is the property.
  - Depends on: E-01
  - Expected outcome: no bare `len(<module>.<CONST>) == <int>` remains without a member-set assertion or a cited spec enumeration.
  - Execution state: pending
- [ ] E-06 Vacuous guards on helpers: `tests/test_history_order.py` wraps assertions in `if hasattr(il, "_plan_status_event_groups"):` five times, so they silently pass if the helper is renamed. Remove the conditional wrapper and the private-helper assertions inside it; the same tests already assert the public outcome (`check_lifecycle_transitions` drift list) which is the contract. Apply the same rule to any other `if hasattr(<production module>, ...)` guard E-01 finds.
  - Depends on: E-01
  - Expected outcome: no `if hasattr(<production module>` guard remains; `tests/test_history_order.py` passes and still asserts the drift result in every fixture.
  - Execution state: pending

### Task group 3: architecture freezes, decide and convert

- [ ] E-07 Decide each architecture freeze with a written reason recorded in the research table. KEEP, as behavior (they run a fresh interpreter and observe what loads, which is an outcome): `tests/test_worktree_lease_stdlib_only.py` (reason recorded in its docstring: a measured 2.10x import regression and a latent import cycle with `runner_shared`; cited three times from `agent_workflows/worktree_lease.py` and by backlog `rdl9lh`). This keep is NOT on the "stdlib-only" ground the OQ-01 ruling rejects: what it asserts is that importing `worktree_lease` loads no FIRST-PARTY `agent_workflows` module (a measured import-cost and cycle defect), not that it avoids third-party dependencies; record the reason in those words. Do not rename the file (three source citations and `check.source-test-citation-dangling`); and `tests/test_egress_policy.py::test_policy_has_no_allow_all_or_negation_switch` as a security boundary (the egress allowlist must not gain an allow-all), CONVERTED: replace its three `not hasattr(policy, ...)` lines with `EgressPolicy(allow_all=True)` / `EgressPolicy(negation=True)` raising `TypeError` (verified at review: both raise `TypeError` today), and keep the existing wildcard `ValueError` refusal. DELETE as change freezes, per the maintainer's OQ-01 ruling: the three stdlib-only import tests `tests/test_ipd_lint.py::test_lint_module_is_stdlib_only`, `tests/test_ipd_schema.py::test_module_is_stdlib_only`, `tests/test_ipd_authoring.py::test_authoring_module_is_stdlib_only`, UNLESS E-01 finds a documented packaging promise (a cited spec, decision, or install path that runs the module before dependencies are installed), in which case convert to a test that runs that promise and record the citation; the one-word "stdlib-only" in a module docstring (for example `ipd_lint`'s header) is a description, not such a promise (`DECISIONS.md` D138, maintainer ruling). Also `tests/test_hostdedup_third_host.py::test_pin_measured_turn_execution_limits` (its docstring says it fails if "execute_item or run_queue is unified into runner_shared", which forbids a refactor), `tests/test_orchestrator_shape_gate.py::test_no_new_host_attribute_is_added`, the "(a) ONE TRANSLATION / (b) NO PRIVATE HOST COPY / (c) VOCABULARY UNCHANGED" arms of `tests/test_runwire_verifier_authority.py::test_set_level_checks` (its (d)/(e) `sys.modules` ledger-fence arms are deleted too, per OQ-02, unless E-01 finds a spec or backlog citation stating the fence), `tests/test_ipd_lint.py::test_enforcement_lives_in_the_checkpoint_layer_not_in_metadata` (pins which internal function enforces; the composed `lint_text` table already pins the three-valued phase behavior).
  - Depends on: E-02, E-03, E-04, E-05, E-06, E-09
  - Expected outcome: every arch-freeze row in the research table reads KEEP with a reason naming a security boundary or a measured defect, or DELETE/CONVERT; no keep row reads "prevents refactoring" or "stdlib-only"; the three stdlib-only import tests are deleted (or converted with a cited packaging promise).
  - Execution state: pending

### Task group 4: record and prove

- [ ] E-08 Append every deleted node id (and every deleted assertion, as `node id (assertion)`) with category and reason to the "Recorded deletions" table of the `qqrgv3` research record, update its summary counts, run `aw research index`. Then run the changed modules, bare `python3 -m pytest` (core tier), the full tier `python3 -m pytest tests/ -m ''`, the hguae9 core per-module coverage script (no core module may drop to 0), and `python3 -m tests.tools.percov_analyze --compare` between the `qqrgv3` baseline directory and a fresh post-change run, listing every line or arc that lost all coverage. Any lost line or arc is either justified in the table (reached only by a deleted pin, for example code executed only by `inspect.getsource`) or covered by a new behavioral assertion added in this child; a deletion is reverted only if neither is possible. Before deleting a whole test FILE (F-10 expects none), run `git grep -n <file>` over `agent_workflows/`, `tools/` and `.aw/records/specs/` and update or keep per Step 0; cited test FUNCTION names (`git grep -n <test_name>` over the same paths plus `.aw/records/backlog/`) are checked the same way and a citing backlog item that is already `done` is a historical record, not a reason to keep.
  - Depends on: E-07
  - Expected outcome: zero unexplained lost lines or arcs; core and full tiers pass; the research "Recorded deletions" row count equals the number of removed `def test_` functions plus removed assertions, both derived from `git diff <base>..HEAD -- tests/` at execution (`git diff --stat` counts lines, not tests).
  - Execution state: pending

## Project conventions discovered (Step 0)

- P16 forbids production-source reads, census pins, docstring pins and placement pins, and permits reading a file only when that file is the artifact under test (`GUIDING_PRINCIPLES.md` "The one narrow exception"); it also forbids weakening an assertion so it passes ("Never weaken an assertion so it passes everywhere").
- `check_engine.check_source_test_citations` (rule `check.source-test-citation-dangling`) scans `agent_workflows` and `tools` comments for cited test files, and `check_engine.check_spec_test_citations` scans specs; deleting a whole test FILE that is cited breaks `aw check`. Measured at authoring: `tests/test_worktree_lease_stdlib_only.py`, `tests/test_records_only_lane_rederive.py`, `tests/test_reaskscore_composed.py`, `tests/test_forkresid_shared_shells.py` are cited from source, and `tests/test_runner_shared.py`, `tests/test_agy_runipd_cli.py`, `tests/test_oc_runipd.py`, `tests/test_orchestrator_retirement.py`, `tests/test_term.py`, `tests/test_attention_contract.py` from specs. This plan deletes assertions and test functions, not those files; if a file empties, update the citing comment in the same commit or keep the file.
- Prior pass `ad9213cc6` deleted pins and left explanatory comments (`tests/test_runner_shared.py` "A SOURCE-TEXT PIN WAS DELETED HERE, NOT REPLACED") recording the mutation that proved the behavioral sibling sufficient; follow that convention for any deletion that removes the only assertion in a block.
- `.agents/` legacy layout is still supported (`DECISIONS.md`), so a test asserting legacy-layout behavior is not obsolete by name.

## Findings

Authoring-time read of the candidates (pre-classification for E-01; counts are test functions unless stated).

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | Baseline pattern set: 56 files, 222 lines on the authoring tree; widened union: 88 files | `rg -l` with the `offdhr` patterns; union with identity, `hasattr`, `__doc__`, `len(CONST)`, `sys.modules`, docs-read patterns |
| F-2 | About 200 of 222 baseline lines are false positives: fixture repos writing `agent_workflows/demo.py` (about 120 lines in 12 files), docstrings declaring P16 compliance, the word "census" in prose or in the behavioral `tests/tools`-style scanners (`tests/test_lost_guard_census.py`, `tests/test_runner_fork_scan_constants.py` drive scanners over `tmp_path` fixtures), and `tests/test_local_leaks.py::test_module_source_is_self_clean` / `tests/test_leak_sanitizer.py::test_engine_source_is_self_clean` which run the sanitizer over its own source (the file IS the artifact under test; KEEP, leak-sanitizer rules are keep-regardless) | reading each hit |
| F-3 | Host identity pins: 14 test functions in 7 files (`assertIs(<host>.X, runner_shared.X)`, `__module__ ==`) | regex join by enclosing `def test_`; e.g. `tests/test_runner_shared.py::CrossHostSuccessBar...::test_cross_host_success_bar_constants_and_tokens`, `tests/test_records_only_lane_rederive.py::test_the_seam_is_shared_by_both_runners` |
| F-4 | `hasattr`/`not hasattr` on production objects: 29 negative lines in 17 files, 20 positive lines; about 35 are pins, the rest are attribute checks on argparse namespaces or result objects (`tests/test_oc_runipd.py::test_verify_with_cli_and_resume` checks a parsed CLI flag: documented flag contract, KEEP; `tests/test_suppress_narrowing.py` checks a returned handle) | `rg -n '(assertFalse\(|assert not |assertTrue\(|assert )\s*hasattr\('` |
| F-5 | Production `__doc__` assertions: 3 tests | `tests/test_oc_runipd.py`, `tests/test_host_sandbox_profile.py`, `tests/test_completion_stale_notice.py` |
| F-6 | Bare vocabulary-size pins: 11 lines in 10 files | `rg -n 'len\([a-zA-Z_]+\.[A-Z_]{3,}\)\s*(==|,)'` |
| F-7 | Vacuous `if hasattr(il, "_plan_status_event_groups")` guards: 5 in `tests/test_history_order.py`; the helper exists today (`ipd_lifecycle._plan_status_event_groups`), so they run now but would silently skip on rename | file read |
| F-8 | Architecture freezes: about 8 tests (`tests/test_hostdedup_third_host.py`, `tests/test_orchestrator_shape_gate.py`, `tests/test_runwire_verifier_authority.py`, `tests/test_ipd_lint.py` layering test, 3 stdlib-only import tests, `tests/test_worktree_lease_stdlib_only.py`, `tests/test_egress_policy.py` no-allow-all) | file reads |
| F-9 | Docs/prose readers: 6 files read README/AGENTS/docs or workflow bodies; P16's narrow exception covers them | `rg` over `.md").read_text` |
| F-10 | Estimate: about 55 to 70 true pins total; about 15 to 20 whole test functions deleted, about 35 to 45 assertions deleted inside retained tests, about 5 converted, about 6 kept with reason; no whole file deleted | sum of F-3 to F-8 after excluding F-2 |

## Proposed changes (ordered, validatable)

E-01 classify -> E-02..E-06 and E-09 subsystem batches (runner identity; removed-symbol names; docstrings; counts; vacuous guards; compat-wrapper conversion) -> E-07 architecture-freeze decisions -> E-08 record and prove.

## Deferred / out of scope (with reason)

- Consolidating duplicate, marginal or combinatorial tests, including docs/prose tests flagged in E-04.
  - Carrier: 83nnyn (Set `testprune` Order 03).
- Tautology and mock-only tests (prompt category 4).
  - Carrier: 83nnyn, which owns marginal and duplicate tests measured by `qqrgv3`'s unique line and arc data.
- Mutation spot-check of the deleted tests.
  - Carrier: vgus66 (Set `testprune` Order 05), which samples at least 20 deletions from this plan's recorded table and every deletion that cites a defect id.

## Scope check

- Over-scope: none.
- Under-scope: none; categories 1 to 3 are fully owned here, others are carried above.

## Required tests / validation

Per V-items: each batch's changed modules with `-o addopts="" -n 6`; bare `python3 -m pytest`; `python3 -m pytest tests/ -m ''`; `percov_analyze --compare`; `aw check` for citation rules.

## Spec / documentation sync

No spec governs which tests exist. Tests deleted here are cited by no spec by node id (specs cite test FILES, which are kept, F-conventions). If E-05 converts a size pin to a member-set equality citing a spec section, the spec is read, not edited.

## Open questions

### OQ-01: Are "module is stdlib-only" import tests a contract or a freeze?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED by the maintainer 2026-10-16: "That's a very old misinterpretation. We're keeping dependencies small, not zero." So "module is stdlib-only" import tests are a refactoring freeze, not a contract: DELETE them (category: architecture freeze), unless one guards a documented packaging promise such as a module that must import before dependencies are installed, in which case convert it to a behavior test that runs that promise. Previous text: `DECISIONS.md` D138 says "stdlib-only" statements "are descriptions of that tool, not a repo-wide ban", which reads as a freeze; but `ipd_lint` documents itself as "stdlib-only and Python 3.9" and the IPD tooling may be copied into target repos. (The pre-ruling default "KEEP the three tests pending maintainer ruling" is superseded by the ruling and no longer applies; E-07 carries the DELETE.)

### OQ-02: Is the run ledger import fence in `tests/test_runwire_verifier_authority.py` (d)/(e) a boundary?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from evidence for execution-time confirmation: the arms assert, in a clean subprocess, that importing the drivers does not load `run_engine`/`run_recovery`. No spec or decision found at authoring names that as a boundary, so it is a change freeze; E-07 deletes it unless E-01 finds a spec or backlog citation stating the fence, in which case it is kept with that citation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted pinscan summary on the execution base and pasted per-verdict, per-category and per-action counts from the research table, with the row count equal to the hit count.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted `rg` for host-module `assertIs`/`hasattr` in the batch files returning only KEEP rows, and pasted pytest output for the batch modules.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `rg` for `hasattr(<production module>` in the batch files returning only KEEP rows, and pytest output for the batch modules.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `rg -n '__doc__' tests` showing no production docstring assertion, the node id of the `edge_satisfied` review-target behavioral test and its passing output.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted `rg` for bare `len(<module>.<CONST>) ==` with each remaining hit paired to a member-set assertion or cited spec section, and pytest output for the batch modules.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted `rg -n 'if hasattr\('` over `tests/` showing no production-module guard, and `tests/test_history_order.py` pytest output.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: the pasted arch-freeze rows from the research table with their reasons; `git grep -n "def test_lint_module_is_stdlib_only\|def test_module_is_stdlib_only\|def test_authoring_module_is_stdlib_only" tests` returning nothing (or each converted with its cited promise); pytest output for `tests/test_egress_policy.py` showing the converted `TypeError` test passing and `git grep -n "hasattr" tests/test_egress_policy.py` returning nothing.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: pasted research "Recorded deletions" row count next to the count of removed test functions from `git diff`, pasted bare `python3 -m pytest` and `python3 -m pytest tests/ -m ''` summary lines, pasted core per-module coverage output with no zero module, pasted `percov_analyze --compare` lost-line and lost-arc list each with its justification, and pasted `aw check --agent` (or `python3 -m agent_workflows check all --agent`) showing no `check.source-test-citation-dangling` diagnostic and no spec test-citation diagnostic.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: pasted pytest output for the converted `tests/test_agy_run.py` test (code path: `tools/antigravity_execute_ipd.py` delegating to `tools/agy_run.py`), and `rg -n hasattr` on that test returning nothing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after review and human approval (all open questions resolved) and after `qqrgv3` is executed (Item-Dependencies), in an isolated worktree (`aw work begin tv72xy`, or the runner's lane). Scope fence: `- Scope-Paths:` is a declaration; an out-of-scope edit is allowed when needed and justified at finalize (`--scope-reason`), and a declared but unmodified path is acknowledged (`--scope-ack`; `agent_workflows/worktree_lease.py` is declared only in case a citing comment must follow a test rename, and is otherwise left untouched, since this plan changes no production behavior). Commit each subsystem batch separately via `aw commit tv72xy -- <paths>` (never `git add -A`); never push or tag. Never weaken an assertion to make a test pass; a deletion is either recorded with its reason or reverted. Respect `hguae9`'s `core` marker: a `core` test may lose a pin assertion but not its behavioral assertions, and the core per-module coverage must not open a gap. You MUST paste the ACTUAL runner output in each V-item; never claim a pass you did not run. Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize and the move to `executed/`; executed by hand, finish with `aw ipd lint --phase pre-transition` conforming and then `aw ipd finalize tv72xy` (never a hand `git mv`), and publish with `aw integration-lock -- git merge --ff-only <branch>`.

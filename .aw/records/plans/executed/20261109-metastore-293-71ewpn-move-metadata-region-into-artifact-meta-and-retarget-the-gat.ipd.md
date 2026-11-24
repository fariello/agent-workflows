# IPD: Move metadata_region into artifact_meta and retarget the gate and readiness callers

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` C5 allows exactly one metadata reader (`artifact_meta`), and `k6jd6l` E-11 deletes `selectors.metadata_region`, the function that bounds a record's metadata region (everything before the first `##` heading). Part 14 of the round-3 split of `k6jd6l` (Order 43, research `nj8zdp` guidance): this part gives `artifact_meta` the region function and moves the production callers outside `selectors` onto it. Measured at `f83159217`: `hooks/executed_transition_gate._has_executed_status` and `_plan_id_of` (2), `orchestrator_readiness.resolve_all_set_memberships` (1), `artifact_meta._set_bullet` (1), `check_engine._metadata_region` (1), `runner_shared._split_metadata_region` (1), `status_set.read_artifact_record` (1), `releases.parse_graduated_to` (1).
- Scope: The non-`selectors` callers of `selectors.metadata_region` from `k6jd6l` E-11. Each call changes from `selectors.metadata_region(text)` to `artifact_meta.metadata_region(text)` ONLY; the `^-` regex literals applied to the region stay, because Orders 247 (`akhrp5`, `orchestrator_readiness._BATCH_META_RE`), 249 (`n2cvf0`, the literal in `executed_transition_gate._plan_id_of`) and 45 (`e8420v`, `check_engine`, `runner_shared`, `status_set`, `releases`) delete them after `k6jd6l`. EXCLUDES the `selectors` internal uses and the deletion (Order 294).
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/hooks/executed_transition_gate.py, agent_workflows/orchestrator_readiness.py, agent_workflows/check_engine.py, agent_workflows/runner_shared.py, agent_workflows/status_set.py, agent_workflows/releases.py, .aw/records/plans/pending/20261109-metastore-293-71ewpn-move-metadata-region-into-artifact-meta-and-retarget-the-gat.ipd.md
- Scope-Exceeded: agent_workflows/selectors.py (E-01 requires selectors.metadata_region become a one-line delegate to artifact_meta.metadata_region)
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:csobg7, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:t4gl15
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: standard
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 293
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 71ewpn

This plan conforms to the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md`.

## Workflow history
- 2026-11-24 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5.5-1m-us variant=high profile=opus): aw oc run self-finalize: 71ewpn verified (set metastore, attempt 1). [Scope reconciliation - out-of-scope agent_workflows/selectors.py: E-01 requires selectors.metadata_region become a one-line delegate to artifact_meta.metadata_region; in-scope-unmodified agent_workflows/hooks/executed_transition_gate.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified agent_workflows/orchestrator_readiness.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-11-16 approved (aw set): status set to approved
- 2026-11-14 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 FIXED

- 2026-11-14 /plan-review (antigravity/gemini-3.8-flash): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed; review record .aw/records/reviews/20261109-metastore-293-71ewpn-move-metadata-region-into-artifact-meta-and-retarget-the-gat.review.md
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from k6jd6l (round 3, research nj8zdp guidance).

## Goal

Only `selectors` itself still calls `selectors.metadata_region`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Carried from `k6jd6l` E-11: "Delete the text readers of the record and selector modules: ... `metadata_region` (their remaining callers, including `hooks/executed_transition_gate`, use `artifact_meta.read`, `read_text` or `read_at`)". A caller that only needs the region text keeps applying its own (later-deleted) literal to `artifact_meta.metadata_region`, so no unit here is also edited by Orders 247 or 249. Ensure the baseline directory exists (`mkdir -p .aw/state/9o83cr`) and save the before-list of `tests/test_executed_transition_gate.py`, `tests/test_orchestrator_readiness.py`, `tests/test_check_engine_status_meta.py`, `tests/test_graduation_forward_links.py` and `tests/test_artifact_meta_legacy.py` to `.aw/state/9o83cr/E-11a-before.txt`.

PIN RULE (carried from `9o83cr`): before an edit that deletes or retargets, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > <before-file>`); after it, run the same command into the matching after-file. A retargeted test keeps every input case, so the after-list may rename a test but not drop a case; the evidence pastes both lists and maps each removed name to its successor.

### Task group 1: one or two callers per item

- [x] E-01 Ensure directory `.aw/state/9o83cr` exists (`mkdir -p .aw/state/9o83cr`) and record baseline outcomes to `.aw/state/9o83cr/E-11a-before.txt`. Move `selectors.metadata_region` (and `selectors._metadata_region_complete` if only it uses it) into `artifact_meta` as a public `artifact_meta.metadata_region` with unchanged behavior; for now `selectors.metadata_region` is a one-line call to it; change `artifact_meta._set_bullet` to call the local function.
  - Depends on: none
  - Expected outcome: `artifact_meta.metadata_region` exists; `artifact_meta` does not call `_sel.metadata_region`.
  - Execution state: performed

- [x] E-02 In `agent_workflows/hooks/executed_transition_gate.py` (`_has_executed_status`, `_plan_id_of`) and `orchestrator_readiness.resolve_all_set_memberships`, call `artifact_meta.metadata_region`.
  - Depends on: E-01
  - Expected outcome: neither module calls `selectors.metadata_region`.
  - Execution state: performed
  - Note: already satisfied before this run: `_has_executed_status`, `_plan_id_of` and `resolve_all_set_memberships` read through `artifact_meta.read_text`/`artifact_meta.query` (earlier metastore plans), so no edit was needed; `rg` confirms no `metadata_region` call in either module.

- [x] E-03 In `check_engine._metadata_region` and `runner_shared._split_metadata_region`, call `artifact_meta.metadata_region`.
  - Depends on: E-02
  - Expected outcome: neither module calls `selectors.metadata_region`.
  - Execution state: performed

- [x] E-04 In `status_set.read_artifact_record` and `releases.parse_graduated_to`, call `artifact_meta.metadata_region`.
  - Depends on: E-03
  - Expected outcome: neither module calls `selectors.metadata_region`.
  - Execution state: performed

- [x] E-05 Save the after-list; run `rg -n "selectors\.metadata_region|_sel\.metadata_region" agent_workflows tools`; commit through `aw commit 71ewpn -- <paths>`.
  - Depends on: E-04
  - Expected outcome: only `selectors` calls `selectors.metadata_region`; no pinned case is dropped.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `agent_workflows/releases.py::_in_metadata_region` also called `agent_workflows/selectors.py::metadata_region`; Order 284 (`zs7a45`) deleted it.
- The `agent_workflows/artifact_meta.py` interface (names from `tve77h`, `ffceq0`, `xexn45`): `read(id6) -> State`, `history(id6)`, `read_at(id6, rev)`, `read_text(text, *, record_type=None) -> State`, `append(id6, events, *, expect_seq)` with `dry_run`, the phase-B legacy writer (`append_legacy`, `render_legacy`), and the legacy loader (`load_legacy_artifact`).
- Cite code by SYMBOL (`path::Symbol`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `f83159217` with `rg -n "metadata_region\(" agent_workflows | grep -v selectors.py`: see the Concern. Order 280's F-25 re-derives the list after phase B.
Context baseline measured at HEAD `56c6460f0`: 65 passed in 4.44s across the five PIN test modules (`tests/test_executed_transition_gate.py`: 12, `tests/test_orchestrator_readiness.py`: 24, `tests/test_check_engine_status_meta.py`: 5, `tests/test_graduation_forward_links.py`: 9, `tests/test_artifact_meta_legacy.py`: 15).

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    E01["E-01: Baseline capture & move metadata_region into artifact_meta"] --> E02["E-02: Retarget executed_transition_gate & orchestrator_readiness"]
    E02 --> E03["E-03: Retarget check_engine & runner_shared"]
    E03 --> E04["E-04: Retarget status_set & releases"]
    E04 --> E05["E-05: Verification & committed artifact state"]
```

1. Move the function into `artifact_meta` (E-01).
2. Retarget the gate and readiness callers (E-02).
3. Retarget `check_engine` and `runner_shared` (E-03).
4. Retarget `status_set` and `releases` (E-04).
5. Verify and commit (E-05).

## Deferred / out of scope (with reason)

- `selectors` internal uses and deleting `selectors.metadata_region`.
  - Carrier: 8ysz6b
- The literals applied to the region in these modules.
  - Carrier: e8420v

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 5 E-items, 7 work Scope-Paths.

## Required tests / validation

The five PIN modules above: `tests/test_executed_transition_gate.py` (12 tests), `tests/test_orchestrator_readiness.py` (24 tests), `tests/test_check_engine_status_meta.py` (5 tests), `tests/test_graduation_forward_links.py` (9 tests), and `tests/test_artifact_meta_legacy.py` (15 tests). Baseline context measured at HEAD `56c6460f0`: 65 passed in 4.44s.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.3 and section 7 step 7. CONTRIBUTES to `4sd62s` AC-1 (owned by `9o83cr`).

## Open questions

### OQ-01: Is a public `artifact_meta.metadata_region` allowed by C5?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes: it keeps the region bound inside `artifact_meta`, and the callers that use it are exactly the regex-literal sites that later plans delete; once those run, its only callers are inside `artifact_meta` and the cutover (`cxxmyv`) may make it private. Recommendation strength: medium. RESOLVED 2026-11-11 by the user via /askme: public now, private later (the function is public in artifact_meta so every caller uses the one copy; the cutover may make it private once no outside caller remains). No reason was given.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `rg -n "def metadata_region|_sel\.metadata_region" agent_workflows/artifact_meta.py` showing only the definition.
  - Observed evidence:
    ```
    $ rg -n "def metadata_region|_sel\.metadata_region" agent_workflows/artifact_meta.py
    6593:def metadata_region(text: str) -> str:
    ```
    `artifact_meta._set_bullet` now calls `region = metadata_region(text)` (local); `selectors.metadata_region` is a one-line delegate `return _meta.metadata_region(text)`. `selectors._metadata_region_complete` stays in `selectors` because `selectors._read_header` also uses it (not only `metadata_region`). Commit d44e23542.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `rg -n "metadata_region" agent_workflows/hooks/executed_transition_gate.py agent_workflows/orchestrator_readiness.py` showing only `artifact_meta` calls, and the before/after per-test lines of `tests/test_executed_transition_gate.py` and `tests/test_orchestrator_readiness.py`.
  - Observed evidence:
    ```
    $ rg -n "metadata_region" agent_workflows/hooks/executed_transition_gate.py agent_workflows/orchestrator_readiness.py
    (no output, rc=1)
    ```
    Neither module calls any `metadata_region`; earlier metastore plans already moved `_has_executed_status`, `_plan_id_of` (`artifact_meta.read_text`) and `resolve_all_set_memberships` (`artifact_meta.query`) off it, so no `selectors.metadata_region` call remains.
    Before (.aw/state/9o83cr/E-11a-before.txt):
    ```
    PASSED tests/test_executed_transition_gate.py::ExecutedGateEndToEndTests::test_commit_adding_fenced_executed_to_approved_plan_passes_gate
    PASSED tests/test_executed_transition_gate.py::ExecutedGateEndToEndTests::test_false_accept_during_merge_with_preamble_fenced_id_is_refused
    PASSED tests/test_executed_transition_gate.py::ExecutedGateEndToEndTests::test_genuine_raw_transition_into_executed_is_still_refused
    PASSED tests/test_executed_transition_gate.py::ExecutedGateEndToEndTests::test_misattribution_refusal_with_preamble_fenced_id_names_real_id
    PASSED tests/test_executed_transition_gate.py::ExecutedStatusUnitTests::test_case_a_approved_with_fenced_executed_returns_false
    PASSED tests/test_executed_transition_gate.py::ExecutedStatusUnitTests::test_case_b_metadata_executed_returns_true
    PASSED tests/test_executed_transition_gate.py::ExecutedStatusUnitTests::test_case_c_metadata_done_returns_true
    PASSED tests/test_executed_transition_gate.py::ExecutedStatusUnitTests::test_case_d_metadata_executed_with_oq_open_below_returns_true
    PASSED tests/test_executed_transition_gate.py::ExecutedStatusUnitTests::test_case_e_headingless_approved_with_fenced_executed_returns_false
    PASSED tests/test_executed_transition_gate.py::ExecutedStatusUnitTests::test_case_f_vnzm27_pinned_shape_fenced_grep_transcript_returns_false
    PASSED tests/test_executed_transition_gate.py::ExecutedStatusUnitTests::test_plan_id_of_headingless_record_with_fenced_id_above_metadata
    PASSED tests/test_executed_transition_gate.py::ExecutedStatusUnitTests::test_plan_id_of_preamble_versus_body_fenced_quote
    PASSED tests/test_orchestrator_readiness.py::TestConsumerParityAndModelFreeLinters::test_lint_and_check_never_call_model
    PASSED tests/test_orchestrator_readiness.py::TestConsumerParityAndModelFreeLinters::test_parity_across_lint_check_and_coverage
    PASSED tests/test_orchestrator_readiness.py::TestIpdCoverageCommand::test_ipd_coverage_agent_bare_repo_no_args
    PASSED tests/test_orchestrator_readiness.py::TestIpdCoverageCommand::test_ipd_coverage_second_invocation_caching
    PASSED tests/test_orchestrator_readiness.py::TestIpdM112LintCases::test_m112_fail_without_findings_section
    PASSED tests/test_orchestrator_readiness.py::TestIpdM112LintCases::test_m112_missing_fingerprint
    PASSED tests/test_orchestrator_readiness.py::TestIpdM112LintCases::test_m112_no_matching_history_line
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_1_child_open_ended
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_1_child_table_unusable
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_1_child_unauthored
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_2_child_fails_lint
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_2_child_status_draft
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_2_child_status_terminal
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_2_executed_child_under_executed_dir_is_ready
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_3_checklist_row_nonconforming
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_4_could_not_ask
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_4_coverage_fail_with_two_quotes
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_4_coverage_record_absent
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_4_coverage_record_stale
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_ready_orchestrator
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessRefusalStylingAndFormatting::test_child_lint_question_extraction_and_fallback
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessRefusalStylingAndFormatting::test_render_human_byte_identical_default_and_to_review
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessRefusalStylingAndFormatting::test_render_human_target_status_approved
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessRefusalStylingAndFormatting::test_term_styling_lifecycle_and_plain_escapes
    ```
    After (.aw/state/9o83cr/E-11a-after.txt): identical, 36 lines, no removed or renamed case:
    ```
    PASSED tests/test_executed_transition_gate.py::ExecutedGateEndToEndTests::test_commit_adding_fenced_executed_to_approved_plan_passes_gate
    PASSED tests/test_executed_transition_gate.py::ExecutedGateEndToEndTests::test_false_accept_during_merge_with_preamble_fenced_id_is_refused
    PASSED tests/test_executed_transition_gate.py::ExecutedGateEndToEndTests::test_genuine_raw_transition_into_executed_is_still_refused
    PASSED tests/test_executed_transition_gate.py::ExecutedGateEndToEndTests::test_misattribution_refusal_with_preamble_fenced_id_names_real_id
    PASSED tests/test_executed_transition_gate.py::ExecutedStatusUnitTests::test_case_a_approved_with_fenced_executed_returns_false
    PASSED tests/test_executed_transition_gate.py::ExecutedStatusUnitTests::test_case_b_metadata_executed_returns_true
    PASSED tests/test_executed_transition_gate.py::ExecutedStatusUnitTests::test_case_c_metadata_done_returns_true
    PASSED tests/test_executed_transition_gate.py::ExecutedStatusUnitTests::test_case_d_metadata_executed_with_oq_open_below_returns_true
    PASSED tests/test_executed_transition_gate.py::ExecutedStatusUnitTests::test_case_e_headingless_approved_with_fenced_executed_returns_false
    PASSED tests/test_executed_transition_gate.py::ExecutedStatusUnitTests::test_case_f_vnzm27_pinned_shape_fenced_grep_transcript_returns_false
    PASSED tests/test_executed_transition_gate.py::ExecutedStatusUnitTests::test_plan_id_of_headingless_record_with_fenced_id_above_metadata
    PASSED tests/test_executed_transition_gate.py::ExecutedStatusUnitTests::test_plan_id_of_preamble_versus_body_fenced_quote
    PASSED tests/test_orchestrator_readiness.py::TestConsumerParityAndModelFreeLinters::test_lint_and_check_never_call_model
    PASSED tests/test_orchestrator_readiness.py::TestConsumerParityAndModelFreeLinters::test_parity_across_lint_check_and_coverage
    PASSED tests/test_orchestrator_readiness.py::TestIpdCoverageCommand::test_ipd_coverage_agent_bare_repo_no_args
    PASSED tests/test_orchestrator_readiness.py::TestIpdCoverageCommand::test_ipd_coverage_second_invocation_caching
    PASSED tests/test_orchestrator_readiness.py::TestIpdM112LintCases::test_m112_fail_without_findings_section
    PASSED tests/test_orchestrator_readiness.py::TestIpdM112LintCases::test_m112_missing_fingerprint
    PASSED tests/test_orchestrator_readiness.py::TestIpdM112LintCases::test_m112_no_matching_history_line
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_1_child_open_ended
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_1_child_table_unusable
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_1_child_unauthored
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_2_child_fails_lint
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_2_child_status_draft
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_2_child_status_terminal
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_2_executed_child_under_executed_dir_is_ready
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_3_checklist_row_nonconforming
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_4_could_not_ask
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_4_coverage_fail_with_two_quotes
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_4_coverage_record_absent
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_4_coverage_record_stale
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_ready_orchestrator
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessRefusalStylingAndFormatting::test_child_lint_question_extraction_and_fallback
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessRefusalStylingAndFormatting::test_render_human_byte_identical_default_and_to_review
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessRefusalStylingAndFormatting::test_render_human_target_status_approved
    PASSED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessRefusalStylingAndFormatting::test_term_styling_lifecycle_and_plain_escapes
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `rg -n "_sel\.metadata_region" agent_workflows/check_engine.py agent_workflows/runner_shared.py` printing nothing and the before/after per-test lines of `tests/test_check_engine_status_meta.py`.
  - Observed evidence:
    ```
    $ rg -n "_sel\.metadata_region" agent_workflows/check_engine.py agent_workflows/runner_shared.py
    (no output, rc=1)
    ```
    Before (.aw/state/9o83cr/E-11a-before.txt):
    ```
    PASSED tests/test_check_engine_status_meta.py::CheckEngineStatusMetaTests::test_check_status_untooled_fenced_quote_in_body_no_drift
    PASSED tests/test_check_engine_status_meta.py::CheckEngineStatusMetaTests::test_is_retired_real_status_executed_signal
    PASSED tests/test_check_engine_status_meta.py::CheckEngineStatusMetaTests::test_status_meta_front_matter_approved_with_fenced_quote
    PASSED tests/test_check_engine_status_meta.py::CheckEngineStatusMetaTests::test_status_meta_headingless_first_bullet_approved
    PASSED tests/test_check_engine_status_meta.py::CheckEngineStatusMetaTests::test_status_meta_no_front_matter_fenced_quote_is_none
    ```
    After (.aw/state/9o83cr/E-11a-after.txt): identical, 5 lines, no removed or renamed case:
    ```
    PASSED tests/test_check_engine_status_meta.py::CheckEngineStatusMetaTests::test_check_status_untooled_fenced_quote_in_body_no_drift
    PASSED tests/test_check_engine_status_meta.py::CheckEngineStatusMetaTests::test_is_retired_real_status_executed_signal
    PASSED tests/test_check_engine_status_meta.py::CheckEngineStatusMetaTests::test_status_meta_front_matter_approved_with_fenced_quote
    PASSED tests/test_check_engine_status_meta.py::CheckEngineStatusMetaTests::test_status_meta_headingless_first_bullet_approved
    PASSED tests/test_check_engine_status_meta.py::CheckEngineStatusMetaTests::test_status_meta_no_front_matter_fenced_quote_is_none
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `rg -n "_sel\.metadata_region" agent_workflows/status_set.py agent_workflows/releases.py` printing nothing and the before/after per-test lines of `tests/test_graduation_forward_links.py`.
  - Observed evidence:
    ```
    $ rg -n "_sel\.metadata_region" agent_workflows/status_set.py agent_workflows/releases.py
    (no output, rc=1)
    ```
    Before (.aw/state/9o83cr/E-11a-before.txt):
    ```
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_1_forward_only
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_2_reverse_only
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_3_agreement_both_directions
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_4_disagreement_visible
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_5_sweep_identity
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_6_no_source_at_all
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_7_agent_evidence_value
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_8_spec_source
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_parse_graduated_to_ignores_body_and_code_fence
    ```
    After (.aw/state/9o83cr/E-11a-after.txt): identical, 9 lines, no removed or renamed case:
    ```
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_1_forward_only
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_2_reverse_only
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_3_agreement_both_directions
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_4_disagreement_visible
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_5_sweep_identity
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_6_no_source_at_all
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_7_agent_evidence_value
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_case_8_spec_source
    PASSED tests/test_graduation_forward_links.py::GraduationForwardLinksTests::test_parse_graduated_to_ignores_body_and_code_fence
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `rg` output listing no file but `agent_workflows/selectors.py`, `diff .aw/state/9o83cr/E-11a-before.txt .aw/state/9o83cr/E-11a-after.txt` with no FAILED or ERROR line, and `git show --stat` of the `aw commit 71ewpn` commit.
  - Observed evidence:
    ```
    $ rg -n "selectors\.metadata_region|_sel\.metadata_region" agent_workflows tools
    (no output, rc=1)
    $ rg -n "metadata_region\(" agent_workflows/selectors.py   (selectors internal unqualified uses remain, Order 294)
    445, 462, 528, 540, 553, 559, 613 (def, delegate), 617, 1089, 1307
    $ diff .aw/state/9o83cr/E-11a-before.txt .aw/state/9o83cr/E-11a-after.txt && echo IDENTICAL
    IDENTICAL
    $ wc -l .aw/state/9o83cr/E-11a-*.txt
       76 .aw/state/9o83cr/E-11a-after.txt
       76 .aw/state/9o83cr/E-11a-before.txt
    $ git show --stat d44e23542
    commit d44e23542a092c8d288c1613f80a2c196af8a1c0
        work(71ewpn): move metadata_region into artifact_meta and retarget check_engine, runner_shared, status_set, releases (E-01..E-04)
     agent_workflows/artifact_meta.py | 70 ++++++++++++++++++++++++----------------
     agent_workflows/check_engine.py  | 10 +++---
     agent_workflows/releases.py      |  4 ++-
     agent_workflows/runner_shared.py |  6 ++--
     agent_workflows/selectors.py     | 30 +++--------------
     agent_workflows/status_set.py    |  2 +-
     6 files changed, 58 insertions(+), 64 deletions(-)
    $ aw suite   (core tier)
    2889 passed, 1 skipped, 11 warnings in 113.40s (0:01:53)
    ```
    `agent_workflows/selectors.py` is outside Scope-Paths; it was edited because E-01 requires `selectors.metadata_region` become a one-line delegate (scope reason recorded at commit).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Safety stop: if prerequisite metastore symbols from `1ajqaa`, `59aiyh`, `csobg7`, `dcerjg`, `ffceq0`, `g5hpbb`, or `t4gl15` are absent, or if an unresolvable concurrent-edit conflict arises on any Scope-Paths file, STOP and report. Pin-first where an item deletes or retargets. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Honesty rule: paste the ACTUAL runner output; never claim a result you did not run. Commits: only through `aw commit 71ewpn -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 71ewpn` itself after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.

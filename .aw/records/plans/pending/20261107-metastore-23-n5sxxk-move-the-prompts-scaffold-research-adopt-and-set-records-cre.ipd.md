# IPD: Move the prompts, scaffold, research, adopt and set_records create, note and setter writers onto artifact_meta

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` section 7 step 4 requires every metadata writer to write through `artifact_meta` in phase B. The prompts, plan-scaffold, research, adopt and set_records writers still build metadata text by hand (measured raw writes with `rg -c "atomic_write\(|write_text\(|git_mv\("`: `ipd_authoring` 5, `research_cmd` 5, `set_records` 6, `prompts` 1, `artifact_adopt` 1). This is a part of `xexn45`, split 2026-11-07.
- Scope: Move `prompts.run_new` with `render_metadata_comment`, `ipd_authoring.run_scaffold`, `research_cmd.run_new`/`run_new_comparison`, `artifact_adopt.apply_adoption`, `set_records.write_walkthrough` onto `artifact_meta.create` (`xexn45` E-02 subset B) and `research_cmd.run_set_outcome`/`run_set_priority`, `ipd_authoring.run_sync`, `set_records.close_on_answer`/`promote_question_to_backlog` onto `artifact_meta.append` (`xexn45` E-05 subset B). Depends on `g6tw94` because `close_on_answer` calls `backlog._reattach_history`, which `g6tw94` moves. EXCLUDES: specs, backlog, releases (`g6tw94`), `--summary` (`6e93gt`), `set_records.write_local_projections` (a generated projection file, not metadata).
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/prompts.py, agent_workflows/ipd_authoring.py, agent_workflows/research_cmd.py, agent_workflows/artifact_adopt.py, agent_workflows/set_records.py, .aw/records/plans/pending/20261107-metastore-23-n5sxxk-move-the-prompts-scaffold-research-adopt-and-set-records-cre.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827, executed:g6tw94
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 23
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: n5sxxk

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from xexn45 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).
- 2026-11-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The prompts, scaffold, research, adopt and set_records create, note and field-setter paths write through `artifact_meta`, each keeping a named, tested behavior.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the named existing test modules GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/n5sxxk/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/n5sxxk/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions D-1 to D-6 below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: prompts, scaffold, research, adopt and set_records writers

- [ ] E-01 Move the remaining creating commands onto `artifact_meta.create`, pinned first (`xexn45` E-02, subset B of its writer list; subset A is `g6tw94` E-01): `prompts.run_new` with `render_metadata_comment`, `ipd_authoring.run_scaffold`, `research_cmd.run_new`/`run_new_comparison`, `artifact_adopt.apply_adoption` and `set_records.write_walkthrough`. Each passes its fields and its created-history message as events; the body text stays the command's own rendering. Behaviors kept: preview prints the exact bytes `--apply` writes (`tests/test_prompts_new.py::test_dry_run_prints_intended_path_and_writes_nothing`, `tests/test_ipd_authoring.py::test_dry_run_writes_nothing`); conformant output (`tests/test_ipd_authoring.py::test_apply_writes_conforming_child`); the UTC history date (`tests/test_scaffold_history_clock.py`); descriptive refusals before any write (`tests/test_research_descriptive_safety.py`, `tests/test_descriptive_refusal_hoist.py`); walkthrough id6 and `Target-Id` (`tests/test_walkthrough_id6.py::test_write_walkthrough_mints_own_id6`); adoption safety (`tests/test_artifact_adopt.py::test_fail_severity_leak_refuses_before_any_write`, `test_destination_write_failure_leaves_the_original`); the prompt comment stays the single first line with the body byte-identical (`tests/test_prompts_set_surface.py::test_comment_write_with_body_byte_identity`); and research creation (`tests/test_research_cmd_create.py`).
  - Depends on: none
  - Expected outcome: every named module passes before and after with equal PASSED sets; `rg -n "Workflow history" agent_workflows/ipd_authoring.py agent_workflows/set_records.py agent_workflows/research_cmd.py agent_workflows/artifact_adopt.py` shows no remaining text-building of the history section in a create path.
  - Execution state: pending

- [ ] E-02 Move the remaining note and field-setter writers onto `artifact_meta.append`, pinned first (`xexn45` E-05, subset B of its writer list; subset A is `g6tw94` E-02): `research_cmd.run_set_outcome`/`run_set_priority`, `ipd_authoring.run_sync` (the `Highest E allocated` watermark set), and `set_records.close_on_answer`/`promote_question_to_backlog`. Behaviors kept: unknown backlog bullets kept in order (`tests/test_backlog.py::test_close_on_answer_preserves_custom_field_and_handed_off_blocks_release`, `test_backlog_set_metadata_preservation_both_spellings_agree`); watermark (`tests/test_ipd_authoring.py::test_sync_assigns_from_watermark_and_advances`, `test_sync_backfills_missing_id_and_leaves_present_id`); research setters (`tests/test_research_cmd_create.py::test_run_set_outcome_apply_writes`, `tests/test_research_priority.py`); slug slice (`tests/test_slug_slice_trailing_hyphen.py`).
  - Depends on: none
  - Expected outcome: every named module passes before and after with equal PASSED sets; `rg -n "f\"- \{(date|today|hdate)\} " agent_workflows/research_cmd.py agent_workflows/set_records.py` shows no hand-built history line outside `artifact_meta`.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `history`, `query`, `resolve`, `read_at`, `append(id6, events, *, expect_seq)`, `create(...)`, `validate_new_events(type, events, *, records_root, migration_import=False)`, `repair`. Order 02's `append`/`create` are log-format and "switched on at the cutover"; this plan adds the phase-B branch (`write_legacy`) that Order 13 removes.
- Atomic replacement is `artifact_core.atomic_write(path, text, *, prefix)`; the lock is `platform_lock.held`; UTC history days come from `artifact_core.utc_history_date` (spec `2vev8j` 4.4).
- Today's history-insertion rules differ (F-04): `status_set._prepend_workflow_history_entry` and `backlog.run_note` insert DIRECTLY under the heading; `specs._append_history` normalizes to exactly one blank line then the record; `plan_readiness._prepend_history_entry` keeps an existing blank line and inserts after it; `coverage_record.write` inserts directly under the heading.
- The newest-history reader is `attention_contract.newest_history_record` over `attention_contract.history_block`, which drops blank lines; so the blank-line difference changes no reader result.
- Descriptive refusals: `attention_contract.refuse_unsafe_descriptive` with `MAX_DESCRIPTIVE_LEN` 300 and `MAX_PROSE_DESCRIPTIVE_LEN` 4300; `specs._refuse_unsafe_descriptive(..., prose=True)` is the spec `--summary` path.
- Recognized plan bullets are `ipd_schema.META_RECOGNIZED`; an unrecognized bullet is lint error `IPD-M103` (`ipd_lint.C_META_UNKNOWN`). Backlog keeps unknown bullets in order (`backlog._render_item`, rendrop 2yqt0a).
- The prompt mirror is the single `aw-prompt` comment (`prompts.render_metadata_comment`, `inject_metadata_id6`, `update_metadata_status`); nothing visible may precede the prompt body (spec `20260808-1958-01-prompt-purity-lint` R1/P4).
- Finalize scope evidence is `evidence["scope_reconciliation"]` with `reasons` and `widened_paths` (`ipd_lifecycle._finalize_transaction`, `runner_shared.compute_scope_reconciliation`).
- Rollup retirement is `ipd_lifecycle.retire_orchestrator` -> `_finalize_transaction` with `evidence["transition"] == "orchestrator-rollup"`.
- The rename ledger is `record_history.record_rename`, written by `artifact_rename` and `plans_refs`; the sidecar is gitignored (`.aw/.gitignore` `records/history.jsonl`).
- Core tier: `pyproject.toml` marker `core`; modules set `pytestmark = pytest.mark.core`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by a line number alone (advisory `IPD-C801`).

## Findings

| Id | Evidence (measured 2026-11-07 at `ac76110f4`) | Finding |
|---|---|---|
| F-01 | Raw writes in this family attributed to the enclosing `def` (`rg -n "atomic_write\(|write_text\("` then the nearest preceding `def`): `prompts.run_new`, `ipd_authoring.run_scaffold`, `run_sync`, `backfill_plan_ids`, `_atomic_write` (2), `set_records.write_walkthrough`, `close_on_answer`, `promote_question_to_backlog`, `write_local_projections` (3) | `backfill_plan_ids`, `_atomic_write` and `write_local_projections` are not named writers; `xexn45` E-14 records them in F-09 with a reason. |
| F-02 | Hidden units of E-01: 7 writer functions, 5 files, 9 pinned modules (`test_prompts_new` 22, `test_prompts_set_surface` 6, `test_ipd_authoring` 31, `test_scaffold_history_clock` 8, `test_research_descriptive_safety` 24, `test_descriptive_refusal_hoist` 3, `test_walkthrough_id6` 4, `test_artifact_adopt` 39, `test_research_cmd_create` 20 tests): about 21 units | Within the 25-unit limit. `research_cmd.run_new_comparison` has no direct test caller; it shares the create path that `test_research_cmd_create` drives. |
| F-03 | Hidden units of E-02: 5 writer functions, 3 files, 5 pinned modules (`test_backlog` 47, `test_ipd_authoring` 31, `test_research_cmd_create` 20, `test_research_priority` 11, `test_slug_slice_trailing_hyphen` 2 tests): about 13 units | Within the limit. |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-1 (blank line under the history heading). KEPT per file: the legacy writer inserts the new line after an existing blank line when one is present and directly under the heading otherwise; it never adds or removes a blank line. This keeps every existing file's shape (F-04) and matches `attention_contract.history_block`, which ignores blank lines. CHANGED: `specs._append_history`'s normalization of a missing blank line (19 specs) no longer adds one, and `specs._append_history` and `status_set._prepend_workflow_history_entry` create a missing section differently today (specs at end of file, plans before the first `##`); the legacy writer uses the `status_set` rule for every type except prompts, which keep end-of-file (pinned by `2xwb9b` E-02). Named tests: `tests/test_specs_verbs.py::test_note_appends_one_record_only` (asserts the record count, not the blank line), `tests/test_history_order.py::test_fixture_a_newest_first`, and a new `tests/test_artifact_meta_legacy_writer.py` case per insertion rule (with blank line, without, section absent) that compares full file bytes. Any existing test that pins the OLD specs normalization fails the E-05 pin diff; it is then listed here by name with its changed assertion, as the PIN-FIRST RULE allows, and in no other case.
- D-2 (new bullet position). KEPT: in place when present; otherwise after `- Status:`, else after `- Id:`, else end of block; never in the body (a88210). The few writers with a different anchor (`coverage_record` after `- Readiness:`, `runner_shared.mark_plan_attended` at block end, `perform_coordinator_proposal_file` after `- Priority:`) change position only; no reader depends on bullet order (`ipd_schema.parse_metadata_block` is order-free). Named tests: `tests/test_coverage_record.py`, `tests/test_run_proposal_channel.py`.

## Proposed changes (ordered, validatable)

1. Move the create commands (E-01).
2. Move the note and field setters (E-02).

## Deferred / out of scope (with reason)

- The final merge-independence test, the AC-21 obligations test, the raw-write audit (F-09), the `docs/cli-output-contract.md` and `CHANGELOG.md` lines, and the full-suite gates of the writer move.
  - Carrier: xexn45

## Scope check

- Over-scope: none.
- Under-scope: none. `artifact_meta.py` is declared for the prompt comment field mapping; acknowledge it at finalize if unmodified.

## Required tests / validation

No new module. Pinned before and after (equal outcome lists): the nine modules of V-01 and the five of V-02.

## Spec / documentation sync

None. Implements `4sd62s` section 7 step 4 for this module family; no documented behavior changes.

## Open questions

None open. Every question this work raised was resolved in `xexn45` before the split; the decisions above carry the answers.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `diff` of `.aw/state/n5sxxk/E-01-before.txt` and `-after.txt` (must print nothing; both files are the PIN-FIRST rule's sorted outcome lists) and both summary lines of `python3 -m pytest -o addopts="" -q -rA tests/test_prompts_new.py tests/test_prompts_set_surface.py tests/test_ipd_authoring.py tests/test_scaffold_history_clock.py tests/test_research_descriptive_safety.py tests/test_descriptive_refusal_hoist.py tests/test_walkthrough_id6.py tests/test_artifact_adopt.py tests/test_research_cmd_create.py`, plus the `rg -n "Workflow history"` output of E-01 showing no create-path text building.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `diff` of `.aw/state/n5sxxk/E-02-before.txt` and `-after.txt` (must print nothing; both files are the PIN-FIRST rule's sorted outcome lists) and both summary lines of `python3 -m pytest -o addopts="" -q -rA tests/test_backlog.py tests/test_ipd_authoring.py tests/test_research_cmd_create.py tests/test_research_priority.py tests/test_slug_slice_trailing_hyphen.py`, plus the E-02 `rg` output showing no hand-built history line in the two modules.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit n5sxxk -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize n5sxxk` itself.

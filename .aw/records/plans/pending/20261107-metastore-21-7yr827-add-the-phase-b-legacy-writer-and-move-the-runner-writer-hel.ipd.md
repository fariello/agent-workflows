# IPD: Add the phase-B legacy writer and move the runner writer helpers onto it

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` section 7 step 4 requires every metadata writer to write through `artifact_meta` in phase B, while `artifact_meta` still writes today's bullets and history lines (C1, C10a). Every other writer move of plan `xexn45` needs ONE named legacy renderer to target first, and the four runner writer helpers that `t4gl15` handed to `xexn45` need the same renderer over in-memory text. This plan is the first part of `xexn45`, split 2026-11-07 because `xexn45` as one plan hid several hundred units of work in single items.
- Scope: Extract the phase-B legacy renderer that `2xwb9b` built inside `artifact_meta.append_legacy` into one named function, `artifact_meta.write_legacy`, extend it to `create`, the `aw-prompt` comment forms and the note, transition, review and coverage events, and add its text mode `artifact_meta.render_legacy_text` (xexn45 E-01). Move the write halves of the runner helpers `runner_shared.mark_plan_attended`, `rederive_front_matter`, `perform_coordinator_proposal_file` and `review_sequence.restore_pre_s7_plan` onto it (xexn45 E-11). Also capture the `.aw/state/xexn45/` baselines that `xexn45` E-14 compares against, because every later part depends on this one and so this is the first writer edit of the whole move. EXCLUDES: every other writer (parts `g6tw94`, `n5sxxk`, `6e93gt`, `bsl45u`, `8q27jt`) and the finishing work (`xexn45`).
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/runner_shared.py, agent_workflows/review_sequence.py, tests/test_artifact_meta_legacy_writer.py, .aw/records/plans/pending/20261107-metastore-21-7yr827-add-the-phase-b-legacy-writer-and-move-the-runner-writer-hel.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 21
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7yr827

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from xexn45 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).
- 2026-11-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`artifact_meta` gains ONE phase-B legacy renderer (`write_legacy`, with the string form `render_legacy_text`) that every later writer move calls, and the runner writer helpers already use it, so each later part only replaces hand-built text with events.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the named existing test modules GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/7yr827/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/7yr827/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions D-1 to D-6 below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: the phase-B legacy writer and the runner writer helpers

- [ ] E-01 Before any edit, save `aw check --agent` output to `.aw/state/xexn45/check-before.jsonl` and the bare `python3 -m pytest` summary line to `.aw/state/xexn45/core-before.txt`. Add `artifact_meta.write_legacy(path, events, *, record_type, dry_run=False)` and route the phase-B branch of `artifact_meta.create` and `artifact_meta.append` through it. `2xwb9b` E-03 to E-05 already built the legacy branch of `append` (its renderer, `LegacyRender`, `WritePreview`, the `_storage_format` per-target dispatch, the path-keyed target and the move-then-write order); `write_legacy` EXTRACTS that renderer into the one named function and extends it to `create`, the `aw-prompt` comment forms and the event types this plan adds, so there is still exactly ONE legacy renderer. It must not be a second implementation beside `2xwb9b`'s, and `tests/test_artifact_meta_legacy_write.py` and `tests/test_status_set_meta_writer.py` (both `2xwb9b`) must pass unchanged after the extraction. It takes events already accepted by `validate_new_events` and the replay rules (tve77h E-03, E-06), and renders them into the file: `set` and `unset` edit the bullet in the metadata block before the first `##` (in place when present; a new bullet goes after `- Status:`, else after `- Id:`, else at the end of the block, never into the body: the a88210 rule of `artifact_rename._update_frontmatter_metadata`); a prompt edits keys INSIDE its single `aw-prompt` comment and never adds a bullet (`prompts.inject_metadata_id6` rule, ubac5n); `note`, `transition`, `review` and `coverage` events with a `message` PREPEND one `- <YYYY-MM-DD> <label> (<tool>): <message>` line directly under `## Workflow history`, keeping the blank line under the heading exactly when one was there (D-1), and create the section before the first `##` after the metadata when absent; field names map back from registry names to legacy names (`plan_role` -> `Kind`, `work_kind` -> `Work-Kind`); `item_dependencies` renders through its `raw` declarations. It writes with `artifact_core.atomic_write`, holds `platform_lock.held(<state>/locks/meta-<key>.lock)` (the `2xwb9b` key, so an id-less legacy record locks by path) like the log path, keeps `2xwb9b`'s source-digest freshness check, and on refusal or `dry_run` writes nothing. Test module `tests/test_artifact_meta_legacy_writer.py`, including a round trip: for 40 tracked records copied to `tmp_path` (8 each of plans, specs, backlog items, releases and prompts, chosen by sorted path; when a type has fewer than 8 tracked records, all of them, and the count is reported), a `set` of an existing field to its own value, then `read()`, returns the same State and leaves the file byte-identical.
  - Depends on: none
  - Expected outcome: `write_legacy` edits exactly the bullet, comment key or history line an event names; a refused event (for example `set readiness`) changes no byte; the 40-record round trip is byte-identical; `2xwb9b`'s two test modules pass unchanged.
  - Execution state: pending

- [ ] E-02 Move the WRITE halves of the runner helpers (carried here by `t4gl15`): `runner_shared.mark_plan_attended` (`attended: required` plus its history line), `rederive_front_matter` (the `REDERIVABLE_FRONT_MATTER_KEYS` = `Work-Kind`, `Priority` set plus the lane's history bullet, applied to TARGET text), `perform_coordinator_proposal_file` (scaffold-then-set `Blocks-Release` on a created plan, and the fallback stub's created line) and `review_sequence.restore_pre_s7_plan` (restore `status` and `readiness` and drop review history lines added since the pre-pass snapshot). The two pure text-to-text helpers gain a `write_legacy` text mode (`artifact_meta.render_legacy_text(text, events)`, the same renderer over a string) because their callers operate on merge-stage or snapshot text that is not a file (OQ-04). `record_oq_answer` edits an open-question BODY block (`- Status:` and the rationale line inside `### OQ-..`), which N3 keeps as body text, so it is recorded as NOT a metadata writer and does not move. Behaviors kept: `tests/test_run_proposal_channel.py::test_needs_attended_proposal_marks_plan_and_files_no_stub`, `test_attended_field_value_is_linted`, `tests/test_records_only_lane_rederive.py` (24 tests, including `test_the_anti_revert_control_holds_on_the_shipped_allow_list`), `tests/test_review_sequence_runner.py::test_ac07_readiness_written_before_s7_reverted_and_reasked`, `tests/test_history_date_clock_residual.py::test_proposal_fallback_record_records_utc_date`, `tests/test_question_preflight.py::test_record_oq_answer_appends_to_existing_rationale`.
  - Depends on: E-01
  - Expected outcome: the named modules pass before and after with equal PASSED sets; `restore_pre_s7_plan` through the renderer emits no `set readiness` event (it restores the pre-pass VALUE as a legacy-text edit only, see D-5).
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
| F-01 | `rg -n "^def (append_legacy|append|create|validate_new_events)\(" agent_workflows/artifact_meta.py`: `validate_new_events`, `append_legacy`, `append`, `create` exist; `rg -n "def (write_legacy|render_legacy_text)" agent_workflows/artifact_meta.py`: no match | `write_legacy` and `render_legacy_text` are new; the renderer to extract lives in `append_legacy`, dispatched by `_storage_format`. |
| F-02 | Hidden units of E-01: one extraction (`append_legacy` renderer), one `create` branch, three prompt comment forms (`prompts.render_metadata_comment`, `inject_metadata_id6`, `update_metadata_status`), four event kinds with a `message` (note, transition, review, coverage), two pinned `2xwb9b` modules (`tests/test_artifact_meta_legacy_write.py` 27 tests, `tests/test_status_set_meta_writer.py` 8 tests, counted with `rg -c "^\s*def test_"`), one new module with seven named cases plus a five-type round trip, two baseline files: about 19 units | Within the 25-unit limit. |
| F-03 | Hidden units of E-02: four helpers (`rg -c "^def (mark_plan_attended|rederive_front_matter|perform_coordinator_proposal_file)\(" agent_workflows/runner_shared.py` = 3, `restore_pre_s7_plan` in `review_sequence` = 1), `render_legacy_text`, `record_oq_answer` confirmed body-only, three files, six pinned modules (`test_run_proposal_channel` 18, `test_records_only_lane_rederive` 24, `test_review_sequence_runner` 10, `test_history_date_clock_residual` 2, `test_question_preflight` 15, `test_attended_session` 10 tests): about 15 units | Within the limit. `mark_plan_attended` and `restore_pre_s7_plan` have no direct test caller (`rg -l` over `tests/` finds none); they are exercised through the runner tests named in E-02. |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-1 (blank line under the history heading). KEPT per file: the legacy writer inserts the new line after an existing blank line when one is present and directly under the heading otherwise; it never adds or removes a blank line. This keeps every existing file's shape (F-04) and matches `attention_contract.history_block`, which ignores blank lines. CHANGED: `specs._append_history`'s normalization of a missing blank line (19 specs) no longer adds one, and `specs._append_history` and `status_set._prepend_workflow_history_entry` create a missing section differently today (specs at end of file, plans before the first `##`); the legacy writer uses the `status_set` rule for every type except prompts, which keep end-of-file (pinned by `2xwb9b` E-02). Named tests: `tests/test_specs_verbs.py::test_note_appends_one_record_only` (asserts the record count, not the blank line), `tests/test_history_order.py::test_fixture_a_newest_first`, and a new `tests/test_artifact_meta_legacy_writer.py` case per insertion rule (with blank line, without, section absent) that compares full file bytes. Any existing test that pins the OLD specs normalization fails the E-05 pin diff; it is then listed here by name with its changed assertion, as the PIN-FIRST RULE allows, and in no other case.
- D-2 (new bullet position). KEPT: in place when present; otherwise after `- Status:`, else after `- Id:`, else end of block; never in the body (a88210). The few writers with a different anchor (`coverage_record` after `- Readiness:`, `runner_shared.mark_plan_attended` at block end, `perform_coordinator_proposal_file` after `- Priority:`) change position only; no reader depends on bullet order (`ipd_schema.parse_metadata_block` is order-free). Named tests: `tests/test_coverage_record.py`, `tests/test_run_proposal_channel.py`.
- D-5 (`restore_pre_s7_plan`). KEPT as a TEXT restore of the pre-pass value of `- Status:` and `- Readiness:` through `render_legacy_text`; it emits no `set readiness` event, because it reverts an unauthorized write rather than making one. After the cutover the equivalent is a log-level refusal of the S7-premature event, owned by the runner review path (`cxxmyv`).

## Proposed changes (ordered, validatable)

1. Capture the baselines, then extract and extend the legacy renderer (E-01).
2. Move the runner writer helpers onto it, adding the text mode (E-02).

## Deferred / out of scope (with reason)

- The final merge-independence test, the AC-21 obligations test, the raw-write audit (F-09), the `docs/cli-output-contract.md` and `CHANGELOG.md` lines, and the full-suite gates of the writer move.
  - Carrier: xexn45
- Every other writer move of `xexn45`: specs, backlog and releases (`g6tw94`); prompts, scaffold, research, adopt and set_records (`n5sxxk`); `--summary` and `aw describe` (`6e93gt`); renames and archive moves (`bsl45u`); recheck, coverage, finalize scope and retirement (`8q27jt`).
  - Carrier: xexn45

## Scope check

- Over-scope: none.
- Under-scope: none. The baselines of E-01 are written under `.aw/state/xexn45/` on purpose, because `xexn45` E-14 reads them after every part has run.

## Required tests / validation

New core test module: `tests/test_artifact_meta_legacy_writer.py` (`tmp_path` fixtures, never reads source). Pinned before and after (equal outcome lists): `tests/test_artifact_meta_legacy_write.py`, `tests/test_status_set_meta_writer.py`, `tests/test_run_proposal_channel.py`, `tests/test_records_only_lane_rederive.py`, `tests/test_review_sequence_runner.py`, `tests/test_history_date_clock_residual.py`, `tests/test_question_preflight.py`, `tests/test_attended_session.py`.

Contributes to `4sd62s` AC-34 (path writes stay moves; `validate_new_events` runs on every event this plan writes) and AC-15 (a refused `set readiness` writes no byte); owners are named in `xexn45`.

## Spec / documentation sync

None. This part implements `4sd62s` section 7 step 4 (the legacy writer) and changes no documented behavior.

## Open questions

### OQ-04: Do the pure text-to-text runner helpers write through a file path?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. `rederive_front_matter` returns TEXT for a merge-stage resolution (its docstring: "it returns TEXT and performs no IO"), and `restore_pre_s7_plan` compares two in-memory snapshots. So `artifact_meta.render_legacy_text(text, events)` exposes the same renderer over a string, validated by the same `validate_new_events`; the caller still writes the file it already writes. Order 13 replaces both with log appends. Recommendation strength: medium.
- Note: carried unchanged from `xexn45` with its id, so the item text that cites it still resolves.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_legacy_writer.py` with every test PASSED, including named tests for: an in-place bullet edit, a new bullet placed after `- Status:` and never below the first `##`, a prompt key written inside its comment with the body byte-identical, a history line prepended with and without a blank line under the heading (D-1), a refused `set readiness` leaving the file byte-identical (quote the `sha256sum` before/after), and the 40-record round trip reporting `40 byte-identical`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `diff` of `.aw/state/7yr827/E-02-before.txt` and `-after.txt` (must print nothing; both files are the PIN-FIRST rule's sorted outcome lists) and both summary lines of `python3 -m pytest -o addopts="" -q -rA tests/test_run_proposal_channel.py tests/test_records_only_lane_rederive.py tests/test_review_sequence_runner.py tests/test_history_date_clock_residual.py tests/test_question_preflight.py tests/test_attended_session.py`, and quote the PASSED line of `tests/test_review_sequence_runner.py::test_ac07_readiness_written_before_s7_reverted_and_reasked`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. This part runs first among the `xexn45` parts; every other part depends on it.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit 7yr827 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 7yr827` itself.

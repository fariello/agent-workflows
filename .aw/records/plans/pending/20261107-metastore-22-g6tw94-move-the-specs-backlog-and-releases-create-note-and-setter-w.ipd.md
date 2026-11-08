# IPD: Move the specs, backlog and releases create, note and setter writers onto artifact_meta

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` section 7 step 4 requires every metadata writer to write through `artifact_meta` in phase B. The specs, backlog and releases modules still build their `- Field:` bullets and `## Workflow history` lines by hand (measured: `specs` 14 bullet literals and 8 history references, `backlog` 29 and 18, `releases` 11 and 4). This is a part of `xexn45`, split 2026-11-07 because its create and note items each spanned seven modules and 17 or 9 test modules.
- Scope: Move `specs.run_new`, `backlog.run_new`, `releases.create_release`/`plan_release` onto `artifact_meta.create` (`xexn45` E-02 subset A) and `specs.run_note`, `specs.run_migrate`, `backlog.run_note`, `backlog._reattach_history`, `releases.set_item_dependencies_line`, `set_graduated_to_line` onto `artifact_meta.append` (`xexn45` E-05 subset A), through the legacy writer of `7yr827`. EXCLUDES: the prompts, scaffold, research, adopt and set_records writers (`n5sxxk`), `--summary` (`6e93gt`).
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/specs.py, agent_workflows/backlog.py, agent_workflows/releases.py, .aw/records/plans/pending/20261107-metastore-22-g6tw94-move-the-specs-backlog-and-releases-create-note-and-setter-w.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 22
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: g6tw94

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from xexn45 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).
- 2026-11-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The specs, backlog and releases create, note and field-setter paths write through `artifact_meta`, each keeping a named, tested behavior, so no module of this family builds metadata text by hand.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the named existing test modules GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/g6tw94/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/g6tw94/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions D-1 to D-6 below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: specs, backlog and releases writers

- [ ] E-01 Move the creating commands of the specs, backlog and releases family onto `artifact_meta.create`, pinned first (`xexn45` E-02, subset A of its writer list; subset B is `n5sxxk` E-01): `specs.run_new`, `backlog.run_new`, `releases.create_release`/`plan_release`. Each passes its fields and its created-history message as events; the body text stays the command's own rendering. Behaviors kept: preview prints the exact bytes `--apply` writes (`tests/test_releases.py::test_plan_release_previews_exactly_what_create_writes`); conformant output (`tests/test_backlog.py::test_new_creates_conformant_item_that_checks_clean`, `tests/test_spec_id6_filenames.py::test_new_preview_then_apply_conformant`, `tests/test_releases_cli.py::test_apply_creates_a_record_that_check_releases_passes`); the UTC history date (`tests/test_history_date_clock.py`); descriptive refusals before any write (`tests/test_specs_releases_descriptive_safety.py`, `tests/test_backlog_descriptive_safety.py`, `tests/test_descriptive_refusal_hoist.py`); and the sidecar is written only after the durable write (`tests/test_history_write_order.py`).
  - Depends on: none
  - Expected outcome: every named module passes before and after with equal PASSED sets; `rg -n "Workflow history" agent_workflows/specs.py agent_workflows/backlog.py agent_workflows/releases.py` shows no remaining text-building of the history section in a create path.
  - Execution state: pending

- [ ] E-02 Move the note and field-setter writers of the specs, backlog and releases family onto `artifact_meta.append`, pinned first (`xexn45` E-05, subset A of its writer list; subset B is `n5sxxk` E-02): `specs.run_note`, `specs.run_migrate`, `backlog.run_note`, `backlog._reattach_history` (used by `set_records.close_on_answer`, which `n5sxxk` moves), `releases.set_item_dependencies_line` and `set_graduated_to_line` (called by the `status_set` engine; Order 06 keeps the call site). Behaviors kept: one record per note, identical note deduplicated (`tests/test_specs_verbs.py::test_note_appends_one_record_only`, `test_note_deduplicates_identical_call`; `tests/test_backlog.py::test_note_records_history_without_changing_status_or_moving_the_file`, `test_a_second_note_preserves_the_first`); migrate folds prose into one history record (`tests/test_specs_verbs.py::test_migrate_free_form_to_bare_enum`, `test_migrate_to_deferred_with_gate`, `test_migrate_folds_implemented_line`); unknown backlog bullets kept in order through `_reattach_history` (`tests/test_backlog.py`, whose close-on-answer tests `n5sxxk` also pins); graduation lines (`tests/test_graduation_forward_links.py`); history bounding (`tests/test_history_block_bounding.py::test_e2_writer_round_trip_wrapped_and_quoted`); newest-first order (`tests/test_history_order.py`, the D-1 named test); note date containment (`tests/test_specs_date_containment.py`, which drives `specs.run_note`; named in `xexn45`'s pinned-module list but in no `xexn45` V-item, so pinned here).
  - Depends on: none
  - Expected outcome: every named module passes before and after with equal PASSED sets; `rg -n "f\"- \{(date|today|hdate)\} " agent_workflows/specs.py agent_workflows/backlog.py` shows no hand-built history line outside `artifact_meta`.
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
| F-01 | `rg -n "f\"- \{(date|today|hdate)\} " agent_workflows/specs.py agent_workflows/backlog.py`, attributed to the enclosing `def`: `specs.run_migrate`, `specs.run_note`, `specs._render_new_spec`, `backlog._render_item` (2), `backlog.run_note`, `backlog._reattach_history` | Seven hand-built history-line sites, all in this part. `_render_new_spec` and `_render_item` are the create renderers that E-01 replaces. |
| F-02 | Hidden units of E-01: 4 writer functions, 3 files, 9 pinned modules (`test_releases` 21, `test_releases_cli` 37, `test_backlog` 47, `test_spec_id6_filenames` 21, `test_history_date_clock` 5, `test_specs_releases_descriptive_safety` 19, `test_backlog_descriptive_safety` 19, `test_descriptive_refusal_hoist` 3, `test_history_write_order` 8 tests, counted with `rg -c "^\s*def test_"`): about 16 units | Within the 25-unit limit. |
| F-03 | Hidden units of E-02: 6 writer functions, 3 files, 6 pinned modules (`test_specs_verbs` 20, `test_backlog` 47, `test_graduation_forward_links` 9, `test_history_block_bounding` 9, `test_history_order` 7, `test_specs_date_containment` 15 tests): about 15 units | Within the limit. |
| F-04 | `tests/test_descriptive_refusal_hoist.py` exercises `specs`, `backlog`, `releases` and `research_cmd` (`rg -o` over the module: 8, 8, 7 and 4 references) | It is pinned in both this part and `n5sxxk`; a re-run is harmless and each part sees its own family green. |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-1 (blank line under the history heading). KEPT per file: the legacy writer inserts the new line after an existing blank line when one is present and directly under the heading otherwise; it never adds or removes a blank line. This keeps every existing file's shape (F-04) and matches `attention_contract.history_block`, which ignores blank lines. CHANGED: `specs._append_history`'s normalization of a missing blank line (19 specs) no longer adds one, and `specs._append_history` and `status_set._prepend_workflow_history_entry` create a missing section differently today (specs at end of file, plans before the first `##`); the legacy writer uses the `status_set` rule for every type except prompts, which keep end-of-file (pinned by `2xwb9b` E-02). Named tests: `tests/test_specs_verbs.py::test_note_appends_one_record_only` (asserts the record count, not the blank line), `tests/test_history_order.py::test_fixture_a_newest_first`, and a new `tests/test_artifact_meta_legacy_writer.py` case per insertion rule (with blank line, without, section absent) that compares full file bytes. Any existing test that pins the OLD specs normalization fails this plan's E-02 pin diff; it is then listed here by name with its changed assertion, as the PIN-FIRST RULE allows, and in no other case.
- D-2 (new bullet position). KEPT: in place when present; otherwise after `- Status:`, else after `- Id:`, else end of block; never in the body (a88210). The few writers with a different anchor (`coverage_record` after `- Readiness:`, `runner_shared.mark_plan_attended` at block end, `perform_coordinator_proposal_file` after `- Priority:`) change position only; no reader depends on bullet order (`ipd_schema.parse_metadata_block` is order-free). Named tests: `tests/test_coverage_record.py`, `tests/test_run_proposal_channel.py`.

## Proposed changes (ordered, validatable)

1. Move the create commands (E-01).
2. Move the note and field setters (E-02).

## Deferred / out of scope (with reason)

- The final merge-independence test, the AC-21 obligations test, the raw-write audit (F-09), the `docs/cli-output-contract.md` and `CHANGELOG.md` lines, and the full-suite gates of the writer move.
  - Carrier: xexn45
- The other writer families of `xexn45` (subset B of E-02 and E-05).
  - Carrier: n5sxxk

## Scope check

- Over-scope: none.
- Under-scope: none. `artifact_meta.py` is declared in case a field mapping must be added; leave it unmodified and acknowledge it at finalize when none is needed.

## Required tests / validation

No new module. Pinned before and after (equal outcome lists): the nine modules of V-01 and the six of V-02.

## Spec / documentation sync

None. Implements `4sd62s` section 7 step 4 for this module family; no documented behavior changes.

## Open questions

None open. Every question this work raised was resolved in `xexn45` before the split; the decisions above carry the answers.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `diff` of `.aw/state/g6tw94/E-01-before.txt` and `-after.txt` (must print nothing; both files are the PIN-FIRST rule's sorted outcome lists) and both summary lines of `python3 -m pytest -o addopts="" -q -rA tests/test_releases.py tests/test_releases_cli.py tests/test_backlog.py tests/test_spec_id6_filenames.py tests/test_history_date_clock.py tests/test_specs_releases_descriptive_safety.py tests/test_backlog_descriptive_safety.py tests/test_descriptive_refusal_hoist.py tests/test_history_write_order.py`, plus the `rg -n "Workflow history"` output of E-01 showing no create-path text building.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `diff` of `.aw/state/g6tw94/E-02-before.txt` and `-after.txt` (must print nothing; both files are the PIN-FIRST rule's sorted outcome lists) and both summary lines of `python3 -m pytest -o addopts="" -q -rA tests/test_specs_verbs.py tests/test_backlog.py tests/test_graduation_forward_links.py tests/test_history_block_bounding.py tests/test_history_order.py tests/test_specs_date_containment.py`, plus the E-02 `rg` output showing no hand-built history line in the two modules.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit g6tw94 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize g6tw94` itself.

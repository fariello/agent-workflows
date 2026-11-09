# IPD: Move the attestation, finalize scope and retirement writers onto artifact_meta

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` 4.4 and 4.2c require the readiness re-check to write one gate `review` event, the coverage record one `op: coverage` event, and finalize to write `scope_result`, `out_of_scope_paths` and `widened_paths` in the executed append, and section 7 step 4 requires the retirement writers to go through `artifact_meta`. Measured: 41 tracked plans carry `- Scope-Exceeded:`, 39 carry `- Coverage:`, 61 history lines contain `readiness re-check` (`xexn45` F-05, F-06). This is a part of `xexn45`, split 2026-11-07.
- Scope: Move the retirement writers `ipd_lifecycle.retire_orchestrator` and `status_set`'s child-retirement history (`xexn45` E-10) onto `artifact_meta.append`, as the FINISHING PART of the attestation, finalize-scope and retirement family. Round-3 split 2026-11-09 per research `nj8zdp`: the readiness re-check and coverage writers (E-01, E-02) now live in `d4w53g` (Order 130), the repository-root path rule with its `4sd62s` 4.2 amendment in `9qhtrc` (131), and the finalize scope fields in `1dvb08` (132). EXCLUDES: the `status_set` engine (`2xwb9b`), the `finalize` event payload (`nq1src`).
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/status_set.py, agent_workflows/artifact_meta.py, .aw/records/plans/pending/20261107-metastore-26-8q27jt-move-the-attestation-finalize-scope-and-retirement-writers-o.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827, executed:d4w53g, executed:9qhtrc, executed:1dvb08
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 26
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8q27jt

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): round-3 split per research nj8zdp; items E-01, E-02, E-03 (split into path rule and finalize fields) moved to d4w53g, 9qhtrc, 1dvb08.
- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from xexn45 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).
- 2026-11-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The orchestrator retirement writers write through `artifact_meta`; with its three parts, readiness and coverage can only be written by their owning events and the finalize scope result is a logged field.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the named existing test modules GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/8q27jt/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/8q27jt/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions D-1 to D-6 below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: retirement

- [ ] E-04 Move the retirement writers onto `artifact_meta.append`: `ipd_lifecycle.retire_orchestrator`'s history record (`rollup_history_message`) becomes the `message` of the transition event that `status_set.apply_status_change` writes (Order 06), with `_insert_rollup_checklist_statement` kept as a BODY edit (it writes into the checklist section, not metadata); `status_set`'s child-retirement history line on the orchestrator (`same-status (<actor>): child <id6> retired <status>`) becomes one `note` event appended to the orchestrator through `artifact_meta.append`; the `RETIRED <date>: <reason>` banner of a hand retirement stays body text that `artifact_audit._has_retired_banner` reads. Behaviors kept: `tests/test_orchestrator_retirement.py` (44 tests, including `test_honest_terminal_record_history_entry_and_actor`, `test_an_eligible_set_retires_and_lands_in_executed`), `tests/test_orchestrator_child_retired.py::test_retirement_appends_orchestrator_history_and_commits_both`, `test_skip_conditions_no_set_dirty_whole_set`, `tests/test_lifecycle_holder_gate.py::test_entry_05_retire_orchestrator_in_process`.
  - Depends on: none
  - Expected outcome: the named modules pass before and after with equal PASSED sets.
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
| F-01 | Hidden units of E-01 (`plan_readiness.recheck_readiness`): 12 named units by `IPD-Z603` | Over the round-3 guidance; moved to `d4w53g` and split into the event move and the verdict rule. |
| F-02 | Hidden units of E-02 (`coverage_record.write`): 8 named units | Moved to `d4w53g` so the two attestation writers share one obligations test module. |
| F-03 | Hidden units of E-03: 11 named units by `IPD-Z603` (`_finalize_transaction`, the deletion of `_insert_scope_exceeded_metadata`, `validate_new_events`, the spec amendment, 5 pinned modules, 1 new module) | Over the guidance; split into the path-root rule with the spec amendment (`9qhtrc`) and the finalize scope fields (`1dvb08`). |
| F-04 | Hidden units of E-04: `retire_orchestrator`, `_insert_rollup_checklist_statement` kept as body, `status_set` child-retirement line, 2 files, 3 pinned modules (`test_orchestrator_retirement` 44, `test_orchestrator_child_retired` 8, `test_lifecycle_holder_gate` 14 tests): 7 named units | Kept here. |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-2 (new bullet position). KEPT: in place when present; otherwise after `- Status:`, else after `- Id:`, else end of block; never in the body (a88210). No reader depends on bullet order (`ipd_schema.parse_metadata_block` is order-free).

## Proposed changes (ordered, validatable)

1. Readiness re-check and coverage writers (`d4w53g`).
2. The repository-root path rule and the spec amendment (`9qhtrc`).
3. Finalize scope fields (`1dvb08`).
4. Retirement writers (E-04).

## Deferred / out of scope (with reason)

- E-01 (readiness re-check as one gate `review` event, with the readiness refusal case that creates `tests/test_writers_obligations.py`) and E-02 (coverage as one `op: coverage` event, with its refusal case): Moved to d4w53g (round-3 split 2026-11-09 per research nj8zdp guidance)
  - Carrier: d4w53g
- E-03 path-root subset (the OQ-03 rule in `artifact_meta.validate_new_events`, the `tests/test_artifact_meta_registry.py` D-6 change, the OQ-03 cases that create `tests/test_writers_scope_fields.py`, and the `4sd62s` 4.2 amendment): Moved to 9qhtrc (round-3 split 2026-11-09 per research nj8zdp guidance)
  - Carrier: 9qhtrc
- E-03 finalize subset (the three scope fields in the executed append of `ipd_lifecycle._finalize_transaction`, the phase-B `- Scope-Exceeded:` rendering, the deletion of `_insert_scope_exceeded_metadata`, the finalize and rollup cases): Moved to 1dvb08 (round-3 split 2026-11-09 per research nj8zdp guidance)
  - Carrier: 1dvb08
- The final merge-independence test, the AC-21 obligations test, the raw-write audit (F-09), the `docs/cli-output-contract.md` and `CHANGELOG.md` lines, and the full-suite gates of the writer move.
  - Carrier: xexn45
- The `finalize` event payload that later replaces the interim scope fields.
  - Carrier: nq1src

## Scope check

- Over-scope: none.
- Under-scope: none. `agent_workflows/artifact_meta.py` is declared in case the `note` event to the orchestrator needs a mapping; acknowledge it at finalize when unmodified. Plan size after the split: 1 E-item.

## Required tests / validation

No new module here (`tests/test_writers_obligations.py` is created by `d4w53g`, `tests/test_writers_scope_fields.py` by `9qhtrc`). Pinned before and after (equal outcome lists): the three modules of V-04.

With its parts, contributes to `4sd62s` AC-15, AC-14a (1)-(2) and AC-39 (4) (owners named in `xexn45`).

## Spec / documentation sync

None here: the `4sd62s` 4.2 path-root amendment moved with the E-03 path-root subset to `9qhtrc`.

## Open questions

None open. OQ-03 (finalize path root) moved with the item it decides to `9qhtrc` and `1dvb08`, under the same id.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-04 validates E-04
  - Required evidence: paste the `diff` of `.aw/state/8q27jt/E-04-before.txt` and `.aw/state/8q27jt/E-04-after.txt` (must print nothing), and from `-after.txt` the PASSED lines of `tests/test_orchestrator_retirement.py::test_honest_terminal_record_history_entry_and_actor`, `test_an_eligible_set_retires_and_lands_in_executed`, `tests/test_orchestrator_child_retired.py::test_retirement_appends_orchestrator_history_and_commits_both`, `test_skip_conditions_no_set_dirty_whole_set` and `tests/test_lifecycle_holder_gate.py::test_entry_05_retire_orchestrator_in_process`, plus the per-module PASSED counts (equal before and after) of the three modules.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit 8q27jt -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 8q27jt` itself.

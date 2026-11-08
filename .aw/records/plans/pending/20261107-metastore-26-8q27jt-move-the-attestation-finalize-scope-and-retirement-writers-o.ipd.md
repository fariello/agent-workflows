# IPD: Move the attestation, finalize scope and retirement writers onto artifact_meta

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` 4.4 and 4.2c require the readiness re-check to write one gate `review` event, the coverage record one `op: coverage` event, and finalize to write `scope_result`, `out_of_scope_paths` and `widened_paths` in the executed append, and section 7 step 4 requires the retirement writers to go through `artifact_meta`. Measured: 41 tracked plans carry `- Scope-Exceeded:`, 39 carry `- Coverage:`, 61 history lines contain `readiness re-check` (`xexn45` F-05, F-06). This is a part of `xexn45`, split 2026-11-07.
- Scope: Move `plan_readiness.recheck_readiness` (`xexn45` E-07), `coverage_record.write` (E-08), finalize scope fields in `ipd_lifecycle._finalize_transaction` with the deletion of `_insert_scope_exceeded_metadata` and the OQ-03 path-root rule in `artifact_meta.validate_new_events` plus its spec amendment (E-09), and the retirement writers `ipd_lifecycle.retire_orchestrator` and `status_set`'s child-retirement history (E-10). Creates `tests/test_writers_obligations.py` with the readiness and coverage refusal cases, which `xexn45` E-13 extends. EXCLUDES: the `status_set` engine (`2xwb9b`), the `finalize` event payload (`nq1src`).
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/plan_readiness.py, agent_workflows/readiness_recheck.py, agent_workflows/coverage_record.py, agent_workflows/ipd_lifecycle.py, agent_workflows/status_set.py, tests/test_writers_scope_fields.py, tests/test_writers_obligations.py, tests/test_artifact_meta_registry.py, .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md, .aw/records/plans/pending/20261107-metastore-26-8q27jt-move-the-attestation-finalize-scope-and-retirement-writers-o.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827
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

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from xexn45 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).
- 2026-11-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The attestation, finalize-scope and retirement writers write through `artifact_meta`, so readiness and coverage can only be written by their owning events and the finalize scope result is a logged field.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the named existing test modules GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/8q27jt/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/8q27jt/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions D-1 to D-6 below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: attestations

- [ ] E-01 Move `plan_readiness.recheck_readiness` (`aw ipd recheck-readiness`) onto `artifact_meta.append` as ONE gate `review` event (4.4, 4.1a K2): `review_kind: gate`, `readiness: go-pending-approval` (still pinned to `plan_readiness.RECHECK_TARGET_READINESS`, never caller input), no new verdict: `plan_readiness.newest_verdict` returns a POLARITY and the raw newest review record, not a verdict string, so the event's `verdict` is the verdict token that `plan_readiness.classify_verdict` reads from that raw record (a member of `plan_readiness.VERDICTS`, as K2 requires of a `gate` event), and when no token can be read the recheck refuses exactly as it does today, so `aw ipd recheck-readiness` never mints a verdict, and `message` = the existing `plan_readiness.format_recheck_history_entry` text. The legacy writer renders it as today: the `- Readiness:` line replaced and one `readiness re-check` history line prepended. `readiness_recheck._run_stale_findings` and its call to `review_findings.append_round_resolving_stale` stay text edits of the REVIEW FILE body (N3), not metadata. Behaviors kept: `tests/test_plan_readiness_recheck.py` (40 tests, including `test_the_only_permitted_write_is_no_go_to_go_pending_approval`, `test_apply_writes_exactly_the_readiness_line_and_one_history_record`, `test_the_recheck_CLEARS_once_the_stale_finding_is_closed`), `tests/test_review_record_classifier.py`, `tests/test_read_verb_zero_match_refusal.py`.
  - Depends on: none
  - Expected outcome: the named modules pass before and after with equal PASSED sets; an extra test in `tests/test_writers_obligations.py` shows that a hand-built `set readiness=go` through `artifact_meta.append` is refused with no byte written, while the recheck path writes `go-pending-approval`.
  - Execution state: pending

- [ ] E-02 Move `coverage_record.write` onto `artifact_meta.append` as ONE `op: coverage` event carrying `coverage` and `coverage_fingerprint` (4.4); `coverage_checked` is written only as the legacy bullet that the legacy writer derives from the event's `at` day and `actor.model` (`<YYYY-MM-DD> by <model>`, its migrated-value format), so the post-cutover log never carries it. The `## Coverage findings` body section stays body text written by `coverage_record` (N3). The history line keeps the shape `- <day> coverage <verdict> (<tool>): fingerprint <12>, model <m>`, which `IPD-M112` reads in phase B. Behaviors kept: `tests/test_coverage_record.py` (`test_write_and_read_fail`, `test_write_pass_removes_findings_and_lints_conforming`, `test_checklist_edit_makes_is_current_false`), `tests/test_coverage_not_written.py`, `tests/test_history_date_clock_residual.py::test_coverage_record_write_records_utc_date`, `tests/test_orchestrator_readiness.py`, `tests/test_gradcover_end_to_end.py`.
  - Depends on: none
  - Expected outcome: the named modules pass before and after with equal PASSED sets; a `set coverage=pass` outside an `op: coverage` event is refused with no byte written (`tests/test_writers_obligations.py`).
  - Execution state: pending

### Task group 2: finalize and retirement

- [ ] E-03 Move finalize's scope fields onto the executed append (the 4sd62s interim rule, 4.2 op list, 4.2c, 4.4): in `ipd_lifecycle._finalize_transaction`, the transition to `executed` from `status_set.apply_status_change` (Order 06) and, in the SAME `artifact_meta.append` call, a `set` of `scope_result` (`within` when no path was out of scope or widened, `widened` when only widened paths exist, `exceeded` when any out-of-scope path was accepted), `out_of_scope_paths` and `widened_paths` (each a list of `{path, reason}` from `evidence["scope_reconciliation"]`). Paths stay REPOSITORY-relative, the form `Scope-Paths` and `compute_scope_reconciliation` use, because a finalize path is a code path and not a records path (OQ-03). In phase B the legacy writer renders ONLY what today's file shows: the existing `- Scope-Exceeded: <path> (<reason>); ...` bullet with today's sanitizing from `_format_scope_exceeded_value` (sorted, `;()` removed, newlines folded, 200-character cap), and nothing for `within`/`widened` (D-3). `_insert_scope_exceeded_metadata` is deleted in favor of that renderer. In `artifact_meta.validate_new_events`, apply the records-root containment rule to `path` only and the repository-root rule to `out_of_scope_paths` and `widened_paths` (OQ-03), and amend spec `4sd62s` 4.2 to say so. If `tve77h`'s `tests/test_artifact_meta_registry.py` pins records-root containment for those two keys, its assertion changes here under decision D-6. Rollup retirement (`retire_orchestrator`) writes none of the three fields. Behaviors kept: `tests/test_scope_exceeded.py` (cases a to e), `tests/test_finalize_refusal_findings.py`, `tests/test_finalize_sendback.py`, `tests/test_ipd_lifecycle_cli.py::test_widening_finalizes_when_each_added_path_carries_a_reason`. New test module `tests/test_writers_scope_fields.py` asserts through `artifact_meta.read` that `scope_result`, both lists and their reasons are present after a fixture finalize (`exceeded`, `widened`, `within` cases), that a rollup retirement leaves all three absent, that a separate later `set scope_result` is refused, and that an `agent_workflows/...` out-of-scope path is stored while a `../x` path is refused (OQ-03).
  - Depends on: none
  - Expected outcome: `tests/test_scope_exceeded.py` passes unchanged; the three new cases report `exceeded`, `widened` and `within` with the expected path lists; rollup leaves them absent; the out-of-append `set` is refused.
  - Execution state: pending

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
| F-01 | Hidden units of E-01: 1 writer (`plan_readiness.recheck_readiness`), 2 files, 3 pinned modules (`test_plan_readiness_recheck` 40, `test_review_record_classifier` 13, `test_read_verb_zero_match_refusal` 11 tests), 1 new refusal case: about 7 units | Within the limit. |
| F-02 | Hidden units of E-02: 1 writer (`coverage_record.write`), 1 file, 5 pinned modules (`test_coverage_record` 7, `test_coverage_not_written` 8, `test_history_date_clock_residual` 2, `test_orchestrator_readiness` 24, `test_gradcover_end_to_end` 5 tests), 1 new refusal case: about 8 units | Within the limit. |
| F-03 | Hidden units of E-03: `_finalize_transaction`, the deletion of `_insert_scope_exceeded_metadata` (one call site: `rg -c "_insert_scope_exceeded_metadata\(" agent_workflows` = 2 including the def), `validate_new_events`, the spec amendment, `tests/test_artifact_meta_registry.py` (21 tests), 4 pinned modules (`test_scope_exceeded` 7, `test_finalize_refusal_findings` 4, `test_finalize_sendback` 62, `test_ipd_lifecycle_cli` 73 tests), 1 new module with six cases: about 15 units | Within the limit. |
| F-04 | Hidden units of E-04: `retire_orchestrator`, `_insert_rollup_checklist_statement` kept as body, `status_set` child-retirement line, 2 files, 3 pinned modules (`test_orchestrator_retirement` 44, `test_orchestrator_child_retired` 8, `test_lifecycle_holder_gate` 14 tests): about 8 units | Within the limit. |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-3 (scope fields in phase B). The logged values `within` and `widened` have no legacy bullet; the legacy file shows only `- Scope-Exceeded:` for `exceeded`, exactly as today. So in phase B the cache returns `scope_result` only from a just-written append (fixture tests) and the legacy loader reads it back from `- Scope-Exceeded:` as `exceeded`; `within` and `widened` become durable only at the cutover. This is the honest phase-B form of AC-39 (4); Order 13 re-demonstrates it on logs.
- D-6 (finalize path root, OQ-03). CHANGED: `out_of_scope_paths` and `widened_paths` are validated against the repository root, not the records root; `path` is unchanged. Named test: the OQ-03 case in `tests/test_writers_scope_fields.py`, and any `tests/test_artifact_meta_registry.py` assertion that pinned the records-root rule for those two keys.

## Proposed changes (ordered, validatable)

1. Readiness re-check as one gate `review` event (E-01).
2. Coverage as one `op: coverage` event (E-02).
3. Finalize scope fields and the path-root rule (E-03).
4. Retirement writers (E-04).

## Deferred / out of scope (with reason)

- The final merge-independence test, the AC-21 obligations test, the raw-write audit (F-09), the `docs/cli-output-contract.md` and `CHANGELOG.md` lines, and the full-suite gates of the writer move.
  - Carrier: xexn45
- The `finalize` event payload that later replaces the interim scope fields.
  - Carrier: nq1src

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

New core test modules: `tests/test_writers_scope_fields.py` and `tests/test_writers_obligations.py` (readiness and coverage refusal cases; `xexn45` E-13 adds the AC-21 and AC-6 cases). Pinned before and after (equal outcome lists): the modules of V-01 to V-04.

Contributes to `4sd62s` AC-15, AC-14a (1)-(2) and AC-39 (4) (owners named in `xexn45`).

## Spec / documentation sync

One spec amendment, carried with E-03: spec `4sd62s` 4.2 states that `out_of_scope_paths` and `widened_paths` are repository-relative (relative, no `..`, not absolute, inside the repository root), while `path` stays records-root-relative. Why: finalize paths are code paths (`xexn45` F-05: 35 of 64 measured entries name `agent_workflows/` or `tests/`) that have no records-root form, so the current wording would refuse every out-of-scope code path that finalize records today (OQ-03 below).

## Open questions

### OQ-03: Are finalize's `out_of_scope_paths` and `widened_paths` records-root-relative?

- Blocking: no
- Status: resolved
- Owner: plan-review (round 1, decision D-2)
- Resolution or deferral rationale: No; they are repository-relative, exactly as `Scope-Paths` and `runner_shared.compute_scope_reconciliation` produce them. F-05 measures 35 of 64 entries as code paths (`agent_workflows/...`, `tests/...`) that have no records-root form. The 4.2 PATH HISTORY rule ("relative to the resolved records root") governs the artifact's own `path` field; 4.2 lists `out_of_scope_paths` and `widened_paths` only as payload values "checked by the path rules", which this plan reads as: relative, no `..`, no absolute path, sanitizer-scanned. Re-checked at review: `tve77h` E-03 (c) as written DOES require "every `path`, `out_of_scope_paths` and `widened_paths` value" to "resolve inside the resolved records root", and spec 4.2 says these two keys "are checked by the path rules (PATH HISTORY below)", whose root is the records root. So the two approved texts and this plan disagree, and 35 of 64 measured finalize paths (F-05) would be refused. Because `artifact_meta.py` is in this plan's Scope-Paths, E-09 resolves it in the writer: `validate_new_events` applies the records-root containment rule to `path` only, and applies "relative, no `..`, not absolute, sanitizer-scanned, inside the REPOSITORY root" to `out_of_scope_paths` and `widened_paths`; a `tests/test_writers_scope_fields.py` case finalizes with an `agent_workflows/...` out-of-scope path and one `../x` path and asserts the first is stored and the second refused. The spec text is amended in the same change (the 4.2 sentence naming the path rules gets "repository-relative for `out_of_scope_paths` and `widened_paths`"), so `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` is in Scope-Paths and the spec-sync section says why. Recommendation strength: strong. Owner of the decision: plan-review round 1 (D-2).
- Note: carried unchanged from `xexn45` with its id, so the item text that cites it still resolves.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `diff` of `.aw/state/8q27jt/E-01-before.txt` and `-after.txt` (must print nothing; both files are the PIN-FIRST rule's sorted outcome lists) and both summary lines of `python3 -m pytest -o addopts="" -q -rA tests/test_plan_readiness_recheck.py tests/test_review_record_classifier.py tests/test_read_verb_zero_match_refusal.py`, and `python3 -m pytest -o addopts="" -v tests/test_writers_obligations.py -k readiness` PASSED, with the test asserting the refused `set readiness=go` leaves the file sha256 unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `diff` of `.aw/state/8q27jt/E-02-before.txt` and `-after.txt` (must print nothing; both files are the PIN-FIRST rule's sorted outcome lists) and both summary lines of `python3 -m pytest -o addopts="" -q -rA tests/test_coverage_record.py tests/test_coverage_not_written.py tests/test_history_date_clock_residual.py tests/test_orchestrator_readiness.py tests/test_gradcover_end_to_end.py`, and `python3 -m pytest -o addopts="" -v tests/test_writers_obligations.py -k coverage` PASSED.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_scope_exceeded.py tests/test_writers_scope_fields.py tests/test_finalize_refusal_findings.py tests/test_finalize_sendback.py tests/test_ipd_lifecycle_cli.py` all PASSED, with `tests/test_scope_exceeded.py` unchanged (`git diff --stat tests/test_scope_exceeded.py` empty); quote the `tests/test_writers_scope_fields.py` assertions for `scope_result == "exceeded"` with its `out_of_scope_paths`, `"widened"` with its `widened_paths`, `"within"` with both lists empty, the rollup case with all three absent, and the refused out-of-append `set scope_result`; plus `rg -n "_insert_scope_exceeded_metadata" agent_workflows` returning no match.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the `diff` of `.aw/state/8q27jt/E-04-before.txt` and `-after.txt` (must print nothing; both files are the PIN-FIRST rule's sorted outcome lists) and both summary lines of `python3 -m pytest -o addopts="" -q -rA tests/test_orchestrator_retirement.py tests/test_orchestrator_child_retired.py tests/test_lifecycle_holder_gate.py`.
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

# IPD: Move the rename, regroup and archive field writers onto artifact_meta

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` section 7 step 4 requires the rename, regroup and archive verbs to write their metadata edits through `artifact_meta` in phase B, while the file move itself stays a git move until the cutover (section 7: path-bearing events start at the cutover commit). Measured: `artifact_rename` holds 11 hand-built bullet literals; `plans_refs` 4. This is a part of `xexn45`, split 2026-11-07.
- Scope: FINISHING PART of the rename, regroup and archive field-writer move (`xexn45` E-06). Round-3 split 2026-11-09 per research `nj8zdp`: the moves now live in `1hfmpb` (Order 127, `artifact_rename`, which also captures the family baseline), `fnu6kw` (128, `plans_refs`, and the pure-move check of `plans_archive.apply_shard_moves`) and `9gy5jk` (129, `research_refs` and `research_archive`). This plan keeps the family close-out (E-02): the four modules that exercise all three writer modules at once, compared against the baseline `1hfmpb` captured, and the D-4 ledger check. EXCLUDES: `rename` and path events (`cxxmyv`).
- Scope-Paths: .aw/records/plans/pending/20261107-metastore-25-bsl45u-move-the-rename-regroup-and-archive-field-writers-onto-artif.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827, executed:1hfmpb, executed:fnu6kw, executed:9gy5jk
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 25
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: bsl45u

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): round-3 split per research nj8zdp; items E-01 (split by writer module) moved to 1hfmpb, fnu6kw, 9gy5jk.
- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from xexn45 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).
- 2026-11-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

After its three parts run, the rename, regroup and shelf-move verbs edit metadata only through `artifact_meta`, and the cross-module rename tests and the rename ledger behave exactly as before the first part.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the named existing test modules GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/bsl45u/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/bsl45u/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions D-1 to D-6 below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: family close-out

- [ ] E-02 Close out the rename family: run the PIN-FIRST command over `tests/test_rename_ledger.py`, `tests/test_rename_group_machine_output.py`, `tests/test_mutation_result_facts.py` and `tests/test_artifact_refs_rewrite.py` into `.aw/state/bsl45u/family-after.txt` and `diff` it against `.aw/state/bsl45u/family-before.txt` (captured by `1hfmpb` E-01 before any rename writer changed). These four modules drive `artifact_rename`, `plans_refs` and `research_refs` together (machine output, mutation facts, citation rewrite), so they are checked once, after all three parts. Also confirm D-4: `tests/test_rename_ledger.py::test_applied_plan_rename_appends_one_record` still passes, so `record_history.record_rename` is unchanged.
  - Depends on: none
  - Expected outcome: the `diff` prints nothing; the ledger test passes.
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

| Id | Evidence (measured 2026-11-07 at `ac76110f4`; split counts 2026-11-09 at `3d0ddb845`) | Finding |
|---|---|---|
| F-01 | Hidden units of the original E-01: 7 writer functions, 4 edited files, 13 pinned modules: about 24 units, and 21 named units by `IPD-Z603` | Over the round-3 guidance of 8; split by writer module into `1hfmpb`, `fnu6kw` and `9gy5jk`. |
| F-02 | `artifact_rename` raw writes attributed to the enclosing `def`: `_update_frontmatter_metadata` (2), `_update_or_inject_set_metadata` (1); `plans_refs.apply_renames` (1) | `1hfmpb` and `fnu6kw`. |
| F-03 | `rg -o '"(rename|group|research)", "(plans|specs|backlog|prompts|mv|set-assign)"'` and the imports of the four shared modules: `test_mutation_result_facts` imports `artifact_rename`, `plans_refs` and `research_refs`; `test_artifact_refs_rewrite` drives `rename plans` and `rename specs`; `test_rename_group_machine_output` drives rename, group and research `mv`; `test_rename_ledger` drives `rename plans` and `group` | These modules span all three parts, so they are baselined before the first and compared after the last (E-02). |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-2 (new bullet position). KEPT: in place when present; otherwise after `- Status:`, else after `- Id:`, else end of block; never in the body (a88210). The few writers with a different anchor (`coverage_record` after `- Readiness:`, `runner_shared.mark_plan_attended` at block end, `perform_coordinator_proposal_file` after `- Priority:`) change position only; no reader depends on bullet order (`ipd_schema.parse_metadata_block` is order-free). Named tests: `tests/test_coverage_record.py`, `tests/test_run_proposal_channel.py`.
- D-4 (rename ledger). KEPT until the cutover: `record_history.record_rename` still writes the gitignored sidecar; no `rename` event exists in phase B.

## Proposed changes (ordered, validatable)

1. The moves, in three parts: `artifact_rename` with the baseline (`1hfmpb`), `plans_refs` (`fnu6kw`), research shelf (`9gy5jk`).
2. The family close-out (E-02).

## Deferred / out of scope (with reason)

- E-01 `artifact_rename` subset (`artifact_rename._update_frontmatter_metadata`, `_update_or_inject_set_metadata`; pins `tests/test_artifact_rename.py`, `tests/test_artifact_group.py`, `tests/test_spec_id6_filenames.py`) and the family baseline: Moved to 1hfmpb (round-3 split 2026-11-09 per research nj8zdp guidance)
  - Carrier: 1hfmpb
- E-01 `plans_refs` subset (`plans_refs._set_metadata`, `apply_renames`, the batch-refusal-before-write rule; pins `tests/test_plans_group_order_preservation.py`, `tests/test_plans_order_grammar.py`) and the `plans_archive.apply_shard_moves` pure-move check (`tests/test_plans_archive.py`): Moved to fnu6kw (round-3 split 2026-11-09 per research nj8zdp guidance)
  - Carrier: fnu6kw
- E-01 research subset (`research_refs.run_mv`, `run_set_assign`, the status edit in `research_archive.apply_moves`; pins `tests/test_research_rename_frontmatter.py`, `tests/test_research_set_assign_date_containment.py`, `tests/test_research_archive.py`): Moved to 9gy5jk (round-3 split 2026-11-09 per research nj8zdp guidance)
  - Carrier: 9gy5jk
- The final merge-independence test, the AC-21 obligations test, the raw-write audit (F-09), the `docs/cli-output-contract.md` and `CHANGELOG.md` lines, and the full-suite gates of the writer move.
  - Carrier: xexn45
- `rename` and path-bearing events, retiring the sidecar writer and the rename ledger.
  - Carrier: cxxmyv

## Scope check

- Over-scope: none.
- Under-scope: none. Each of the 13 originally pinned modules is pinned in exactly one plan: nine in the three parts and four (the cross-module ones) here. Plan size after the split: 1 E-item, no code path.

## Required tests / validation

No new module and no code edit. Compared against the `1hfmpb` baseline: the four modules of V-02.

Contributes to `4sd62s` AC-34 and AC-40 case 3 (owners named in `xexn45`).

## Spec / documentation sync

None. Implements `4sd62s` section 7 step 4 for the rename family; no documented behavior changes.

## Open questions

None open. Every question this work raised was resolved in `xexn45` before the split; the decisions above carry the answers.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-02 validates E-02
  - Required evidence: paste the empty `diff .aw/state/bsl45u/family-before.txt .aw/state/bsl45u/family-after.txt`, the per-module PASSED counts from `family-after.txt` for each of `tests/test_rename_ledger.py`, `tests/test_rename_group_machine_output.py`, `tests/test_mutation_result_facts.py` and `tests/test_artifact_refs_rewrite.py`, and the PASSED line of `tests/test_rename_ledger.py::test_applied_plan_rename_appends_one_record`.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit bsl45u -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize bsl45u` itself.

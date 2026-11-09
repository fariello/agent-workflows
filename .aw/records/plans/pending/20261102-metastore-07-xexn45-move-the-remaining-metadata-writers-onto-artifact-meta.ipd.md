# IPD: Move the remaining metadata writers onto artifact_meta

- Date: 2026-11-02
- Kind: child
- Concern: Spec `4sd62s` section 7 step 4 requires every metadata WRITER to change to write through `artifact_meta` in phase B, while `artifact_meta` still writes today's bullets and history lines, so that the cutover (Order 13) switches one writer and not dozens (C1, C10a). Order 06 (`2xwb9b`) moves the `status_set` engine. Every other writer still edits metadata text by hand. Measured 2026-11-02 at `0cbfcc706`: 12 writer modules in this plan's scope hold 99 hand-formatted `- Field: value` literals and 47 `## Workflow history` references (`specs` 14/8, `backlog` 29/18, `releases` 11/4, `ipd_authoring` 11/1, `artifact_rename` 11/0, `plans_refs` 4/0, `plan_readiness` 1/10, `coverage_record` 3/5, `set_records` 1/1, `review_sequence` 3/1, `runner_shared` writer helpers, `ipd_lifecycle` finalize), plus `prompts` comment writers. These modules use four different history-insertion rules (F-04), and three of them write the gitignored rename ledger (`record_history.record_rename`). Finalize writes `- Scope-Exceeded:` through `ipd_lifecycle._insert_scope_exceeded_metadata` (41 tracked plans carry it), which 4.2c and 4.4 replace with `scope_result`, `out_of_scope_paths` and `widened_paths` written in the executed append. No creating command can write `short_description` yet (AC-36 case 1). Section 7 and 3c require each phase-B plan to name each moved writer's behavior and the test that checks it, because a behavior that no test exercises can change unnoticed.
- Scope: Phase B step 4, part 2 of 2 (`4sd62s` section 7), FINISHING PART. Split 2026-11-07 per the maintainer step-complexity rule into six writer parts (`7yr827` Order 21, `g6tw94` 22, `n5sxxk` 23, `6e93gt` 24, `bsl45u` 25, `8q27jt` 26), which round 3 (2026-11-09, research `nj8zdp`) split further into Orders 120 to 136; and round 3 moved the merge-independence test (E-12) to `b4y4ee` (Order 133). This plan keeps the integration work that needs all of them: the AC-21 obligations and AC-6 phase-B diff test (E-13), the raw-write audit F-09 in two halves (E-14, E-15), the `docs/cli-output-contract.md` reconciliation and `CHANGELOG.md` line (E-16), and the full gates and commit (E-17). It still OWNS AC-21. EXCLUDES: every writer move (the parts above); the `status_set` engine itself (`2xwb9b`); readers (`ffceq0`, `t4gl15`); deleting old parsers (`9o83cr`); the log format, `rename` and path events and sidecar retirement, which start at the cutover (`cxxmyv`).
- Scope-Paths: tests/test_writers_obligations.py, docs/cli-output-contract.md, CHANGELOG.md, .aw/records/plans/pending/20261102-metastore-07-xexn45-move-the-remaining-metadata-writers-onto-artifact-meta.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827, executed:g6tw94, executed:n5sxxk, executed:6e93gt, executed:bsl45u, executed:8q27jt, executed:b4y4ee
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 7
- Highest E allocated: 17
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: xexn45
- Review-Depth: complex

## Workflow history
- 2026-11-09 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): round-3 split per research nj8zdp; items E-12 moved to b4y4ee; E-14 (the finish, 12 named units) redistributed in place into new items E-14 to E-17 (no obligation moved out); the six 2026-11-07 parts were themselves re-split into Orders 120 to 136.
- 2026-11-07 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): split per maintainer step-complexity rule; items E-01, E-11 moved to 7yr827; E-02 (subset A), E-05 (subset A) moved to g6tw94; E-02 (subset B), E-05 (subset B) moved to n5sxxk; E-03, E-04 moved to 6e93gt; E-06 moved to bsl45u; E-07, E-08, E-09, E-10 moved to 8q27jt.
- 2026-11-07 to-review (aw set): demoted approved -> to-review: APPROVAL WITHDRAWN: maintainer direction 2026-11-07: paused before re-review; the metastore plans MUST build the tools that migrate ANY repo from ANY prior format (.agents layout, id-less/untitled records, no sidecar), not only this repository. Re-review against the amended spec 4sd62s before re-approval.
- 2026-11-07 approved (aw set): status set to approved
- 2026-11-06 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 FIXED
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 FIXED; review record .aw/records/reviews/20261102-metastore-07-xexn45-move-the-remaining-metadata-writers-onto-artifact-meta.review.md
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every metadata write outside the `status_set` engine goes through `artifact_meta`, which validates it with the Order 02 rules and renders it, in phase B, into today's bullets and history lines through one legacy writer. The writer parts listed in `- Scope:` perform the moves and `b4y4ee` proves merge independence; this plan proves the AC-21 obligations and the AC-6 phase-B diff, audits the raw writes that remain, reconciles the documentation, and runs the full gates once every part is executed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the named existing test modules GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/xexn45/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/xexn45/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions D-1 to D-6 below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: obligations, audit and finish (after every part is executed)

- [ ] E-13 Add to `tests/test_writers_obligations.py` (created by `d4w53g`) the AC-21 (4.4a) and AC-6 phase-B cases: (a) AC-21 rows: run and paste `tests/test_find_filters.py` (`wja06w`), the zero-match `aw find` exit code 2 (`zyj8io`, via `tests/test_cli_find.py`), `tests/test_graduation_forward_links.py` (`pw2ln3`: declarations alone, origin links alone, both), `tests/test_readiness_absence_invariant.py` (`l56tyz`) and the AC-15 tests of Order 06 (`fhinri`); a reference to this plan's commit closes the `63zo2f` row (its `Carrier: 4sd62s` deferral: "the setters change to use `artifact_meta`"); the `me227c` and `6tjye0` rows point at AC-1 (`9o83cr`) and AC-20 (`dcerjg`); (b) AC-6 phase-B form: a fixture `aw backlog set <id6> done` and a fixture finalize each produce a `git diff` whose metadata hunk is exactly the `- Status:` line, any owned unset, the scope bullet and ONE new history line (the phase-B form of "exactly one `transition`"); (c) the attestation refusals named in the original E-07 and E-08 are already in the module (since round 3: `d4w53g` E-02 and E-03); this item adds only (a) and (b).
  - Depends on: none
  - Expected outcome: every listed module passes; the two `git diff` hunks contain exactly the listed lines.
  - Execution state: pending

- [ ] E-14 Audit the remaining raw writes, half A of F-09: run `rg -n "atomic_write\(|write_text\(" agent_workflows/specs.py agent_workflows/backlog.py agent_workflows/releases.py agent_workflows/prompts.py agent_workflows/ipd_authoring.py` and record in `## Findings` (table F-09) every hit with its enclosing `def` and its reason (body text per N3, a generated index file, a non-record file, or a call into `artifact_meta`). A hit inside a writer that a part moved is a defect of that part: record it and stop rather than editing here.
  - Depends on: none
  - Expected outcome: F-09 has one row per hit in the five modules of half A, each with its enclosing `def` and reason.
  - Execution state: pending

- [ ] E-15 Audit the remaining raw writes, half B of F-09: run `rg -n "atomic_write\(|write_text\(" agent_workflows/artifact_rename.py agent_workflows/plans_refs.py agent_workflows/plan_readiness.py agent_workflows/set_records.py agent_workflows/coverage_record.py` and record in `## Findings` (table F-09) every hit with its enclosing `def` and its reason (body text per N3, a generated index file, a non-record file, or a call into `artifact_meta`). A hit inside a writer that a part moved is a defect of that part: record it and stop rather than editing here.
  - Depends on: E-14
  - Expected outcome: F-09 has one row per hit in the five modules of half B, each with its enclosing `def` and reason.
  - Execution state: pending

- [ ] E-16 Reconcile `docs/cli-output-contract.md` with the two new `--summary` options of `aw ipd scaffold` and `aw prompts new` (added by `py2vu9`) beside the `aw describe` leaf (added by `h06gs7`), and add one `CHANGELOG.md` `2.0.0 (pending)` line naming `--summary` at creation and `aw describe`.
  - Depends on: none
  - Expected outcome: the contract lists both options and the leaf; the changelog has one new line.
  - Execution state: pending

- [ ] E-17 Run the gates once every part is executed and commit: re-run every module named in the V-items of each part listed in `- Item-Dependencies:` (one PIN-FIRST outcome list per part, under `.aw/state/xexn45/`); the bare core gate `python3 -m pytest` (within its 30 s budget); `make test-all`; `aw check --agent`, comparing its `(location, rule)` pairs with `.aw/state/xexn45/check-before.jsonl` (captured by `7yr827` E-01 before the first writer edit; no added pair); `aw ipd lint --all` on this repository (no new diagnostic); `aw sanitize --agent`; then commit through `aw commit xexn45 -- <each changed path>` (one commit per task group is allowed, each through `aw commit`). Never push.
  - Depends on: E-13, E-14, E-15, E-16
  - Expected outcome: all runs pass; no added `(location, rule)` pair; every commit is path-scoped.
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

## Findings

| Id | Evidence (measured 2026-11-02 at `0cbfcc706`) | Finding |
|---|---|---|
| F-01 | Per-module counts of hand-formatted bullet literals (`f"- Field: {` or `"- Field: "`) and `Workflow history` references: `specs` 14/8, `backlog` 29/18, `releases` 11/4, `ipd_authoring` 11/1, `artifact_rename` 11/0, `plans_refs` 4/0, `plan_readiness` 1/10, `coverage_record` 3/5, `set_records` 1/1, `review_sequence` 3/1; `prompts` writes only inside its comment (`render_metadata_comment`, `inject_metadata_id6`, `update_metadata_status`) | Each module builds metadata text itself; the move replaces those sites with events. |
| F-02 | Raw write calls (`atomic_write`, `write_text`, `git_mv`): `set_records` 6, `artifact_rename` 5, `ipd_authoring` 4, `specs` 3, `backlog` 2, `releases` 2, `plans_refs` 2, `prompts` 1, `plan_readiness` 1, `coverage_record` 1; `readiness_recheck` 0 (it calls `plan_readiness.recheck_readiness`) | The writer surface of this plan. E-14 re-measures what remains. |
| F-03 | Writers the spec's step-4 list does not name but that write metadata: `research_cmd.run_new`/`run_set_outcome`/`run_set_priority`, `research_refs.run_mv`/`run_set_assign`, `research_archive.apply_moves` (`_rewrite_status_in_text`), `plans_archive.apply_shard_moves`, `artifact_adopt.apply_adoption`; the runner writers `mark_plan_attended`, `rederive_front_matter`, `perform_coordinator_proposal_file`, `restore_pre_s7_plan` (handed here by `t4gl15` Deferred) | 4.8 lists them as tooled writers ("the research shelf moves", `aw archive plans`, `aw adopt --summary`); no other child owns their write side, so this plan carries them. |
| F-04 | Blank line directly under `## Workflow history`: plans 1,430 none / 250 one; specs 19 / 29; backlog 1,133 / 0; walkthroughs 0 / 1. Four insertion rules exist (Step 0) | The writers disagree today; D-1 decides the kept behavior. |
| F-05 | 41 tracked plans carry `- Scope-Exceeded:`; their entries name 29 `.aw/records/` paths and 35 code paths; `_format_scope_exceeded_value` sorts, strips `;()`, folds newlines and caps a reason at 200 characters | Finalize paths are repository-relative and include code paths (OQ-03); the legacy render must keep today's sanitizing. |
| F-06 | 39 plans carry `- Coverage:` (`coverage_record.write`); 61 plan history lines contain `readiness re-check`; 3 plans carry `- Attended:` | Volume of the attestation and runner-field writers. |
| F-07 | `aw prompts new --help` and `aw ipd scaffold --help` show no `--summary`; `aw adopt --help` does; no `aw describe` or walkthrough-creating verb exists (`aw walkthroughs` is an invalid choice) | AC-36 case 1 needs two new options and a setter (E-03, E-04). |
| F-08 | Tests that call private writer helpers directly: `tests/test_plans_order_grammar.py` (`plans_refs._set_metadata`, 3 tests), `tests/test_spec_id6_filenames.py` (`artifact_rename._update_frontmatter_metadata`), `tests/test_prompts_set_surface.py` (`prompts.render_metadata_comment`), `tests/test_records_only_lane_rederive.py` (`runner_shared.rederive_front_matter`) | These functions keep their signatures as thin adapters over `artifact_meta`, so the pins stay valid without editing assertions; Order 11 (`9o83cr`) may delete the adapters. |
| F-09 | (filled by E-14 and E-15) remaining raw writes with reasons | Audit record for AC-1 (owned by `9o83cr`). |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-1 (blank line under the history heading). KEPT per file: the legacy writer inserts the new line after an existing blank line when one is present and directly under the heading otherwise; it never adds or removes a blank line. This keeps every existing file's shape (F-04) and matches `attention_contract.history_block`, which ignores blank lines. CHANGED: `specs._append_history`'s normalization of a missing blank line (19 specs) no longer adds one, and `specs._append_history` and `status_set._prepend_workflow_history_entry` create a missing section differently today (specs at end of file, plans before the first `##`); the legacy writer uses the `status_set` rule for every type except prompts, which keep end-of-file (pinned by `2xwb9b` E-02). Named tests: `tests/test_specs_verbs.py::test_note_appends_one_record_only` (asserts the record count, not the blank line), `tests/test_history_order.py::test_fixture_a_newest_first`, and a new `tests/test_artifact_meta_legacy_writer.py` case per insertion rule (with blank line, without, section absent) that compares full file bytes. Any existing test that pins the OLD specs normalization fails the E-05 pin diff; it is then listed here by name with its changed assertion, as the PIN-FIRST RULE allows, and in no other case.
- D-2 (new bullet position). KEPT: in place when present; otherwise after `- Status:`, else after `- Id:`, else end of block; never in the body (a88210). The few writers with a different anchor (`coverage_record` after `- Readiness:`, `runner_shared.mark_plan_attended` at block end, `perform_coordinator_proposal_file` after `- Priority:`) change position only; no reader depends on bullet order (`ipd_schema.parse_metadata_block` is order-free). Named tests: `tests/test_coverage_record.py`, `tests/test_run_proposal_channel.py`.
- D-3 (scope fields in phase B). The logged values `within` and `widened` have no legacy bullet; the legacy file shows only `- Scope-Exceeded:` for `exceeded`, exactly as today. So in phase B the cache returns `scope_result` only from a just-written append (fixture tests) and the legacy loader reads it back from `- Scope-Exceeded:` as `exceeded`; `within` and `widened` become durable only at the cutover. This is the honest phase-B form of AC-39 (4); Order 13 re-demonstrates it on logs.
- D-4 (rename ledger). KEPT until the cutover: `record_history.record_rename` still writes the gitignored sidecar; no `rename` event exists in phase B.
- D-6 (finalize path root, OQ-03). CHANGED: `out_of_scope_paths` and `widened_paths` are validated against the repository root, not the records root; `path` is unchanged. Named test: the OQ-03 case in `tests/test_writers_scope_fields.py`, and any `tests/test_artifact_meta_registry.py` assertion that pinned the records-root rule for those two keys.
- D-5 (`restore_pre_s7_plan`). KEPT as a TEXT restore of the pre-pass value of `- Status:` and `- Readiness:` through `render_legacy_text`; it emits no `set readiness` event, because it reverts an unauthorized write rather than making one. After the cutover the equivalent is a log-level refusal of the S7-premature event, owned by the runner review path (`cxxmyv`).

## Proposed changes (ordered, validatable)

1. The writer moves, in the parts listed in `- Scope:`.
2. The merge-independence test (`b4y4ee`).
3. The obligations test (E-13).
4. The raw-write audit in two halves (E-14, E-15).
5. The documentation reconciliation (E-16).
6. The gates and commit (E-17).

## Deferred / out of scope (with reason)

- E-12 (the merge-independence test `tests/test_writers_merge_independence.py`, AC-3 phase-B form): Moved to b4y4ee (round-3 split 2026-11-09 per research nj8zdp guidance)
  - Carrier: b4y4ee
- E-01 (the phase-B legacy writer, and the `.aw/state/xexn45/` baselines) and E-11 (runner writer helpers), with OQ-04: Moved to 7yr827 (split 2026-11-07 per maintainer step-complexity rule).
  - Carrier: 7yr827
- E-02 subset A (`specs.run_new`, `backlog.run_new`, `releases.create_release`/`plan_release`) and E-05 subset A (`specs.run_note`, `specs.run_migrate`, `backlog.run_note`, `backlog._reattach_history`, `releases.set_item_dependencies_line`, `set_graduated_to_line`): Moved to g6tw94 (split 2026-11-07 per maintainer step-complexity rule).
  - Carrier: g6tw94
- E-02 subset B (`prompts.run_new` with `render_metadata_comment`, `ipd_authoring.run_scaffold`, `research_cmd.run_new`/`run_new_comparison`, `artifact_adopt.apply_adoption`, `set_records.write_walkthrough`) and E-05 subset B (`research_cmd.run_set_outcome`/`run_set_priority`, `ipd_authoring.run_sync`, `set_records.close_on_answer`/`promote_question_to_backlog`): Moved to n5sxxk (split 2026-11-07 per maintainer step-complexity rule).
  - Carrier: n5sxxk
- E-03 (`--summary` at creation) and E-04 (`aw describe`), with OQ-02: Moved to 6e93gt (split 2026-11-07 per maintainer step-complexity rule).
  - Carrier: 6e93gt
- E-06 (rename, regroup and archive field writers): Moved to bsl45u (split 2026-11-07 per maintainer step-complexity rule).
  - Carrier: bsl45u
- E-07 (readiness re-check), E-08 (coverage record), E-09 (finalize scope fields and the `4sd62s` 4.2 path-root amendment), E-10 (retirement writers), with OQ-03: Moved to 8q27jt (split 2026-11-07 per maintainer step-complexity rule).
  - Carrier: 8q27jt
- The `status_set` setter engine, including the `approval` and `readiness` attestation writes on transition and the `->reviewed` gate predicate.
  - Carrier: 2xwb9b
- Reader moves (`selectors`, `check_engine`, `attention`, `ipd_lint`, including `IPD-M112` reading the last `coverage` event and the display of `short_description`).
  - Carrier: ffceq0
- Reader moves of the runner, hooks and git-content gates through `read_at`.
  - Carrier: t4gl15
- A tooled command that records a NEW review round as one subject event (AC-14 writer form, handed here by `dcerjg`), and the `plan-review` and `spec-review` workflow text that tells agents to run it instead of writing `- Readiness:` (4.4 "The implementing plan names that command"). No `aw` verb writes review records today (`aw reviews` is read-only; `review_findings.write_review` has no CLI caller), so the command must be NEW, and its text changes the managed workflow bodies, which may land only in the cutover commit (C10a). This plan names the command `aw reviews record <subject-id6> --round <n> --verdict <v> [--readiness <r>] [--review-depth <t>] --file <review.md>` and leaves its build to the documents child, which already rewrites those workflow bodies.
  - Carrier: 90iqr1
- `rename` and path-bearing events, retiring the sidecar writer and the rename ledger (AC-31, AC-34 post-cutover form), and switching `write_legacy` off.
  - Carrier: cxxmyv
- Deleting the thin adapters kept for F-08 and every remaining legacy parser, plus the AC-1 test.
  - Carrier: 9o83cr
- A walkthrough-creating command (4.2 SHORT DESCRIPTION: "the plan names the tooled command"). Named here as `aw walkthrough new --set <set> --order <nn> --target <id6> --slug <slug> [--summary ...]` over the existing `set_records.write_walkthrough`; its CLI is needed only after the cutover, when a hand-written walkthrough has no log, so it lands with the documents that describe it.
  - Carrier: 90iqr1
- The `finalize` event payload that later replaces the interim scope fields.
  - Carrier: nq1src

## Scope check

- Over-scope: none.
- Under-scope: none. Every writer move lives in exactly one part (see Deferred), and the merge test in `b4y4ee`. Round 3 redistributed the original E-14 in place into E-14 to E-17 without moving any obligation out: the ten-module audit is E-14 plus E-15 (five modules each, together the original list), the documentation and changelog are E-16, and the gates and commit are E-17. Plan size after the split: 5 E-items in 1 task group.

## Required tests / validation

No new test module is created here: `tests/test_writers_obligations.py` is created by `d4w53g` and extended here; `tests/test_writers_merge_independence.py` is created by `b4y4ee`; `tests/test_artifact_meta_legacy_writer.py`, `tests/test_writers_create_summary.py` and `tests/test_writers_scope_fields.py` are created by `7yr827`, `fekdwv` and `9qhtrc`. All use `tmp_path` fixtures and real git repositories where git is involved; none reads source code.

Existing modules pinned before and after each move now live in the V-items of the parts; E-17 re-runs every one of them once all parts are executed. `tests/test_specs_date_containment.py`, listed in this plan's original module list but in no original V-item, is pinned by `g6tw94` E-02.

Acceptance criteria of `4sd62s` that this plan OWNS:

| AC | Proven by | Note |
|---|---|---|
| AC-21 | E-13 | every 4.4a row with its pasted evidence; the `63zo2f` row is closed by this plan's commit |

CONTRIBUTES to (owned or finally shown elsewhere):

| AC | Proven by | Owner / final demonstration |
|---|---|---|
| AC-3 | `b4y4ee` E-01 (phase-B form: different artifacts merge without conflict through the moved writers) | `cxxmyv` re-demonstrates on logs |
| AC-6 | E-13 (b) (phase-B form: status line plus one history line, and the finalize scope bullet) | `cxxmyv` shows the `transition` event diff |
| AC-34 | `7yr827` E-01 and the `bsl45u` parts (`1hfmpb`, `fnu6kw`, `9gy5jk`) keep path writes as moves only; the path rules are enforced by `validate_new_events` on every event this plan writes | `cxxmyv` (path-bearing events start at the cutover); `tve77h` owns the projection |
| AC-36 case 1 | `fekdwv`, `bir7xm`, `py2vu9`, `h06gs7`; cross-checked by `6e93gt` E-03 | `cxxmyv` re-demonstrates the full criterion |
| AC-39 (4) | `1dvb08` E-01, E-02 (writer side; phase-B rendering per D-3) | `tve77h` owns the projection; `cxxmyv` re-demonstrates on logs |
| AC-15 | `d4w53g` E-02, E-03 (writer-side refusal of `set readiness` and `set coverage`) | `2xwb9b` |
| AC-14a (1)-(2) | `d4w53g` E-01, E-02 (the recheck writes only a `gate` event with `readiness`) | `2xwb9b`, `dcerjg` |
| AC-40 case 3 | `ernmom` E-03 and `1hfmpb` E-02 (a prompt edit rewrites only its comment key) | `dcerjg`, `cxxmyv` |
| AC-1b | E-17 (core and thorough tier lines at this merge) | `cxxmyv` |

Commands: the pin-first runs of each part's E-items, E-17's bare core gate, `make test-all`, `aw check`, `aw ipd lint --all`, `aw sanitize --agent`.

## Spec / documentation sync

No spec amendment here: the `4sd62s` 4.2 path-root amendment for `out_of_scope_paths` and `widened_paths` moved with E-09 to `8q27jt` and in round 3 to `9qhtrc` (OQ-03). Otherwise the work of this plan and its parts implements `4sd62s` section 7 step 4 (second half), 4.2 SHORT DESCRIPTION, 4.4, 4.4a (AC-21) and 4.8. `docs/cli-output-contract.md` gains the `aw describe` leaf in `h06gs7`; E-16 here reconciles it with the two `--summary` options and adds one `CHANGELOG.md` line, because they are user-visible in phase B. Workflow bodies (`plan-review`, `spec-review`) are NOT changed here (C10a; carried by `90iqr1`).

## Open questions

### OQ-01: Split this plan into 07a and 07b?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The plan fits the limits (14 E-items, 5 task groups), but its pinned-module list is the longest of the Set. If review judges a group too large for one pass, split at the natural seam, each half one green merge under C10a: 07a = Task groups 1 to 3 (E-01 to E-06: the legacy writer, creating commands, `--summary`, `aw describe`, notes, field setters, renames; owns AC-36 case 1 contribution) and 07b = Task groups 4 and 5 (E-07 to E-14: recheck, coverage, finalize scope fields, retirement, runner helpers, merge test, AC-21 obligations), with 07b depending on `executed:<07a id6>`, and Orders 08 and 09 depending on 07b. AC-21 stays with 07b. Recommendation strength: medium (keep as one plan unless an executor reports a group exceeded one focused pass). Resolved: keep as one plan; `/plan-review` of this plan may apply the split at the stated seam. Superseded 2026-11-07: the plan was split into six parts by writer family under the maintainer step-complexity rule (see Workflow history and Deferred), not at the 07a/07b seam.

Questions OQ-02, OQ-03 and OQ-04 moved with the items they decide, under the same ids: OQ-02 to `6e93gt`, OQ-03 to `8q27jt`, OQ-04 to `7yr827`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.
- [ ] V-13 validates E-13
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_writers_obligations.py tests/test_find_filters.py tests/test_cli_find.py tests/test_graduation_forward_links.py tests/test_readiness_absence_invariant.py` with the per-module PASSED counts and, by name, the new AC-21 and AC-6 cases of `tests/test_writers_obligations.py`; the AC-21 row table with one evidence reference per 4.4a row (the `63zo2f` row citing this plan commit hash); and the two fixture `git diff -U0` metadata hunks (backlog `done`, finalize) showing exactly the lines listed in E-13 (b).
  - Observed evidence:
  - Result: pending
- [ ] V-14 validates E-14
  - Required evidence: paste the E-14 `rg` command and its full output, and the F-09 rows for half A, one per hit, each with its enclosing `def` and reason; for each of `agent_workflows/specs.py`, `agent_workflows/backlog.py`, `agent_workflows/releases.py`, `agent_workflows/prompts.py`, `agent_workflows/ipd_authoring.py`, state its hit count.
  - Observed evidence:
  - Result: pending
- [ ] V-15 validates E-15
  - Required evidence: paste the E-15 `rg` command and its full output, and the F-09 rows for half B, one per hit, each with its enclosing `def` and reason; for each of `agent_workflows/artifact_rename.py`, `agent_workflows/plans_refs.py`, `agent_workflows/plan_readiness.py`, `agent_workflows/set_records.py`, `agent_workflows/coverage_record.py`, state its hit count.
  - Observed evidence:
  - Result: pending
- [ ] V-16 validates E-16
  - Required evidence: paste `git diff docs/cli-output-contract.md CHANGELOG.md` showing the `aw ipd scaffold --summary` and `aw prompts new --summary` entries, the `aw describe` leaf, and the one new changelog line.
  - Observed evidence:
  - Result: pending
- [ ] V-17 validates E-17
  - Required evidence: paste: per part listed in `- Item-Dependencies:`, the part id6 with the PASSED count of its re-run outcome list and the `diff` against that part's own after-list (empty); the `(location, rule)` comparison with `.aw/state/xexn45/check-before.jsonl` showing no added pair; the `aw ipd lint --all` summary with no new diagnostic; the `aw sanitize --agent` result record; the `aw commit` output listing the committed paths; and, beside those, the bare `python3 -m pytest` summary line with its wall time and the `make test-all` summary line.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed: `tve77h`, `2xwb9b`, the six parts `7yr827` (Order 21), `g6tw94` (22), `n5sxxk` (23), `6e93gt` (24), `bsl45u` (25), `8q27jt` (26), each of which waits for its own round-3 parts, and `b4y4ee` (133). All open questions are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where D-1 to D-6 name it.

Honesty rule: run the named modules, `python3 -m pytest` (core gate) and `make test-all`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit xexn45 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize xexn45` itself.

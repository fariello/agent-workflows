# Review findings: plan 2cv6rz

- Subject-Id: 2cv6rz
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `e29e38eb1` in a runner review-sweep lane worktree (non-interactive). The plan was committed and unmodified (last plan commit `51731d591`), so no pre-review snapshot was taken. `aw ipd lint --phase author` was clean before revisions, and `aw ipd lint --phase review-finalize` is clean after them. Reviewed against backlog `fbxkvo`, `agent_workflows/engine.py` (`resolve_target_layout`, `_records_member_destination`, `create_setup_artifacts`, `_merge_tree`, `_ensure_untracked_gitignore`, `_lane_bases`, `migrate_local_lanes_to_untracked`, `UNTRACKED_PATTERNS`, `ensure_untracked_gitignore`), `agent_workflows/layout_migration.py` (`_raw_move`, `_ensure_gitignore`, `commit_paths`, `_is_removable_leftover`, `_handle_leftovers`, `execute_migration`, `resume_migration`, `rollback_migration`, `apply_embedded_stage_one`, `rollback_embedded_stage_one`), `agent_workflows/layout_inventory.py` (`DEFAULT_ROOTS`, `classify_item`), `agent_workflows/cli.py` (`normalize-lanes`, the `--to-aw` install path), executed plan `njfyjt`, and spec `20260715-1722-01-agent-comms-convention`.

`AW-TIER: standard`
`AW-REVIEW: DONE`

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Scope | Gate `_lane_bases` and `migrate_local_lanes_to_untracked` | Gate only the nested `.gitignore` call for `.agents/` bases; `_lane_bases` unchanged | PR-001 |
| E-02 | Three steps gating `_lane_bases` and using `elif not is_canonical_aw` | Leave `_lane_bases`; `.agents/`-scoped skip branch; docstring of one function | PR-001, PR-002 |
| Proposed changes item 2, mermaid nodes K and L | `_lane_bases skips .agents/...` | Rename still runs; only nested `.gitignore` is skipped | Consistency with revised E-02 |
| OQ-02 resolution | Gate in both functions | Gate in one function, with the review rationale | Consistency with revised E-02 |
| E-01 step 6 | Embedded path persistence unstated; crash window unstated | Saves `tx_data`; residual crash window accepted; resume limitation stated | PR-003, PR-006 |
| E-01 step 7 | Rollback pruning "without touching `.aw/state`" | Prune strictly below `<records_root>/<lane>/untracked/`; order after `move_journal` reversal | PR-004 |
| E-03 | No embedded-path test, no local-lane test, no canonical `local/` test, `-k` names unstated | Adds three tests and a naming rule | PR-005, PR-007 |
| E-03 collision test | No ignore rule for the pre-populated destination | Root `.gitignore` `**/*untracked*/` | PR-008 |
| V-01, V-02 | Old E-02 wording | Names new tests and the unchanged `_lane_bases` | Bijection with revised E-items |
| Spec / documentation sync | "existing specifications" | Cites spec `20260715-1722-01-agent-comms-convention` "Gitignore:" paragraph | Verifiable citation |

#### Issues

None.

### Step T

1. Yes: `migrate_local_lanes_to_untracked` runs on every `aw install` and on `aw normalize-lanes`, and the relocation runs inside the shared `MigrationManager` used by `--to-aw`, `aw migrate-layout`, and the m0001 embedded stage.
2. No.
3. No: 4 E-items in 4 task groups, 5 Scope-Paths.
4. Yes: no `.spec.md` path in Scope-Paths.
5. Medium: the change moves user files that git cannot restore (gitignored lane content), so a wrong move or a wrong rollback is not recoverable from history.

Tier: standard.

### Step R1

- Checked: every symbol named in the plan exists with the claimed behavior. `resolve_target_layout` returns `aw` when the system dir exists or neither tree exists. `_lane_bases` unconditionally includes `.agents/{prompts,comms}`. `migrate_local_lanes_to_untracked` takes the `else:` branch for any base whose repo-relative path does not start with `.aw/records/`. `commit_paths` offers only journaled tracked moves, removed leftovers, id backfill, `.aw/.gitignore`, and portable config. `_is_removable_leftover` preserves any path containing `untracked` or `/local/`.
- `_lane_bases` gating conflicts with executed plan `njfyjt`, which made the `local/`-to-`untracked/` rename cover both layouts on purpose (PR-001).
- `else:` is also reached by external companion or home records roots, where `rel` is an absolute path (PR-002).
- `resume_migration` from `staged`, `verified`, `switched`, or `retained` never reaches `_handle_leftovers` (PR-006).

### Step R2

- Checked: E/V bijection 4/4; Scope-Paths cover every edited file; `Item-Dependencies: none` is correct for Order 1 of a one-child Set; each V-item demands pasted diff and runner output.
- The embedded stage-one wiring and rollback in E-01 had no test (PR-005).
- New tests had no naming rule, so the `-k` selector in E-04 and V-03 could miss them (PR-007).
- The collision fixture placed a destination file under `.aw/records/` with no ignore rule, so inventory would see it under the `partial-aw` root and the test would not exercise the helper's collision branch (PR-008).

### Step R3

- Checked: the change moves gitignored user content and never stages it. `_raw_move` is a filesystem move that preserves symlinks; the plan forbids `git mv` and `git add`, keeps `commit_paths` free of the new journal key, and walks with `followlinks=False`. No secrets, network, or trust-boundary code. Rollback restores only journaled moves and only when the source slot is empty, so it cannot overwrite a file the user created after migration.
- Crash between a move and the transaction save leaves an unjournaled file in the destination lane; it is not lost (PR-003).

### Step R4

- Checked: A data model: one new transaction key, `untracked_lane_relocations`, beside `move_journal`. C reuses `_raw_move`, `_records_root_for_backend`, and existing pruning. D invariants: non-clobber, no staging, `local/` untouched, legacy nested `.gitignore` preserved, each mapped to a test. E tests drive `execute_migration`, `rollback_migration`, the embedded pair, `migrate_local_lanes_to_untracked`, and `cli.main(["install", ...])` (P16 compliant). F smallest design: un-pruning the inventory walk is correctly declined (collision errors and grammar renames). Spec sync: spec `20260715-1722-01-agent-comms-convention` already reserves nested `.gitignore` files for the legacy layout, so no amendment is needed.
- Rollback pruning scope was vague (PR-004).

### Step S5

- Checked: no question needs a human. OQ-01 and OQ-02 are resolved from repository evidence; the PR-001 narrowing is supported by executed plan `njfyjt` and by the gitignore coverage analysis.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | D invariant (regression) | `engine._lane_bases` docstring "Every comms/prompts base across BOTH layouts"; executed plan `njfyjt` Concern "It receives only the ACTIVE layout's `dirs` ... structurally cannot rename the legacy `.agents/{prompts,comms}/local`"; `engine.UNTRACKED_PATTERNS` `**/*untracked*/` | Gating `_lane_bases` on `legacy` stops renaming `.agents/{prompts,comms}/local/` on canonical repos. After `--to-aw` moves the tracked `.agents/prompts/.gitignore` away, a stranded `local/` lane is ignored by no rule and its private content shows as committable; the rename to `untracked/` is what puts it under the root untracked-safety pattern. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now leaves `_lane_bases` unchanged and skips only `_ensure_untracked_gitignore` for `.agents/` bases on canonical repos; E-03 adds a canonical `local/` rename test. |
| PR-002 | MEDIUM | IN-SCOPE | C compatibility | `engine.migrate_local_lanes_to_untracked` `except ValueError: rel = str(base)...`; `engine._records_member_destination` returns `project_records_dir(...)` for companion/home | `elif not is_canonical_aw:` would also silently drop nested `.gitignore` creation for an external companion or home records root, whose absolute `rel` reaches the same `else:` branch. That behavior change was unstated and untested. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 step 2 scopes the skip to `rel == ".agents"` or `rel.startswith(".agents/")` and states that other bases keep current behavior. |
| PR-003 | MEDIUM | UNDER-SCOPE | A crash safety | `layout_migration.apply_embedded_stage_one` saves `self._save_transaction(tx_data)` with `ls` nested; E-01 step 6 | E-01 did not say how the embedded path persists the journal, and did not state the crash window between a move and the save. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 step 6 requires saving the caller's `tx_data` and records the residual window as accepted (file lands in its intended gitignored destination). |
| PR-004 | LOW | IN-SCOPE | G executability | E-01 step 7 "empty parent directories inside `.aw/` or the external records root, without touching `.aw/state`" | The rollback pruning boundary and its order relative to the `move_journal` reversal were vague. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 step 7 runs after the `move_journal` loop and prunes strictly below `<records_root>/<lane>/untracked/`. |
| PR-005 | MEDIUM | UNDER-SCOPE | E testing | E-01 step 6 and 7 wire `apply_embedded_stage_one` and `rollback_embedded_stage_one`; E-03 tested only `execute_migration`; `tests/test_m0001_layout_stage.py::test_stage1_embedded_apply_backfill_false_and_snapshot_rollback` is the existing harness | Half of the E-01 wiring had no test. The `local/` preservation claim in the expected outcome also had no positive test in the new fixture. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 adds an embedded apply-and-rollback parity test and a local-lane non-regression test; V-01 names both. |
| PR-006 | LOW | IN-SCOPE | R1 reachability | `layout_migration.resume_migration` branches for `staged`, `verified`, `switched`, `retained` complete without `_handle_leftovers` | Relocation is skipped on those resume paths; the plan did not say so. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 step 6 states the limitation as out of scope and notes that E-02 still prevents the nested `.gitignore` there. |
| PR-007 | LOW | IN-SCOPE | E testing | E-04 and V-03 `-k "untracked or migrate_local_lanes or LeftoverDisposition or InstallMigrationResidueSweep"` | New tests had no naming rule, so the targeted selector could silently skip them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 requires `untracked` in new `test_layout_migration.py` names and `migrate_local_lanes` in new `test_engine_restored_behavior.py` names. |
| PR-008 | LOW | IN-SCOPE | E testing | `layout_inventory.DEFAULT_ROOTS` `("partial-aw", ".aw")`; `layout_inventory._walk` prunes only gitignored dirs | The collision fixture's pre-populated `.aw/records/prompts/untracked/same.md` was not gitignored, so inventory would classify it and the test would not reach the helper's collision branch as a real canonical tree would. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 collision test adds a root `.gitignore` `**/*untracked*/`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Where to gate legacy lanes on a canonical repo? | Only the nested `.gitignore` call in `migrate_local_lanes_to_untracked`, for `.agents/` bases | Gate `_lane_bases` too (rejected: undoes `njfyjt` both-layout rename and strands an unignored `local/` lane) | Executed plan `njfyjt`; `engine.UNTRACKED_PATTERNS`; `engine._lane_bases` docstring | yes |
| D-2 | Behavior for external companion or home records roots | Unchanged | Skip nested `.gitignore` for every non-`.aw/records/` base on canonical repos | `engine._records_member_destination`; backlog `fbxkvo` scope names only `.agents/` | yes |
| D-3 | Review tier | standard | simple | Step T answers 1 yes, 5 medium | yes |

# Review findings: ipd qpvem9

- Subject-Id: qpvem9
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran non-interactively in an isolated review-sweep lane worktree (run `run-20261124T195117Z-1319864`, HEAD `4603a0bc1`). The target plan `.aw/records/plans/pending/20261121-ujxi56-01-qpvem9-skip-legacy-agents-docs-readme-md-in-layout-migration-and-ve.ipd.md` was committed and unmodified (last commit `9e5b60d4f`), so no pre-review snapshot commit was made. `aw ipd lint --phase author --agent` returned `clean` with zero findings before and after edits.

The review read backlog `ujxi56`, `agent_workflows/layout_inventory.py` (`classify_item`, `_AGENTS_RECORD_SUBDIRS`, `_RECORDS_SUBPATH_REWRITES`, `_flatten_records_subpath`, `build_migration_map`), `agent_workflows/layout_migration.py` (`execute_migration`, `_handle_leftovers`, `_is_removable_leftover`, `commit_paths`, `project_stage_one_to_scratch`, `_summarize_planned_groups`, `rollback_migration`), `agent_workflows/cli.py::_install_leftover_disposition`, and `agent_workflows/engine.py::collect_scaffold_members`. Scratch probes ran under `/tmp/opencode/qpvem9/`. They applied the plan's two `E-01` edits in memory only and wrote nothing into the repository. Measured:

- **The bug reproduces, and the fix removes it end to end.** The probe built the E-03 fixture (tracked `.agents/{workflows,docs}` plus `workflow-artifacts/assess-bugs/...`) and ran `cli.main(["install", repo, "--to-aw", "--yes"])`.
  - Unpatched: `.aw/records/docs` exists, `attention.scan` is `valid False` with one `attention.uninventoried-tree` at `.aw/records/docs`, and `attention --check` exits 1. `workflow-artifacts` already lands untracked and ignored under `.aw/workflow-artifacts/` (`.aw/.gitignore:78:/workflow-artifacts/`), because `0hdqbw` is executed.
  - Patched: `.aw/records/docs` is absent, `.agents/docs` is pruned, `valid True` with no violations, and `attention --check` exits 0. Wall time was 1.37 s.
- **Every leftover mode behaves as the plan says.** Patched `execute_migration`:
  - `remove` with a clean tracked README: removed and backed up.
  - `remove` with a locally modified or an untracked README: preserved in place.
  - `defer` and `keep`: preserved.
  - Every case ends `valid True` with no `.aw/records/docs`. Unpatched, every case is `valid False`.
  - `commit_paths()` includes `.agents/docs/README.md` after `remove`.
  - `project_stage_one_to_scratch` creates no `scratch/.aw/records/docs` (unpatched, it does).
- **The collision guard is necessary.** When `.agents/README.md`, `.agents/docs/README.md`, and `.agents/records/docs/README.md` coexist with distinct bytes, the classification change alone makes `build_migration_map` return `valid False` with `destination-collision`. Adding the `!= "regenerate"` guard makes it valid. The `agents:docs` and `agents:records/docs` DIRECTORY entries still map to `records/docs` as `migrate`, but those entries are never moved (PR-005).
- **The fix does not cover every file under `.agents/docs/`.** A tracked `.agents/docs/notes.md` beside the README still produces `.aw/records/docs/notes.md` and `valid False`, even with the fix applied (PR-004).
- **Dependency `0hdqbw` is already executed** (`.aw/records/plans/executed/`, code commit `f4792a7e4`), but the plan calls it approved and pending (PR-003).
- **The repository gates the plan requires are red at HEAD for unrelated reasons.**
  - `tests/test_runner_resume_clears_stop.py`: `3 failed, 10 passed`. This is backlog `rryabb`, with pending plan `z6wodh`.
  - `aw check all --agent`: exit 1, 12 errors. None is at a Scope-Path. This plan appears only as an `info` finding (`check.lifecycle-transition-unvalidated`).
  - `tests/test_cli.py` is module-marked slow, so under the default `addopts` it is entirely deselected.
- **The four layout test modules collect 114 tests** under `-o addopts=""`.

`AW-TIER: standard`
`AW-REVIEW: DONE`

### Step T

1. No: no spec, CLI flag, output format, or config key changes. Migration output for one legacy file changes, toward the existing `20260817-2124-01` layout.
2. No: `layout_inventory.py` is not a listed guard module, although its output decides which legacy files `remove` may delete.
3. No: 4 E-items in 3 task groups, one production module.
4. Yes: `- Scope-Paths:` names all four touched files.
5. Yes, partly: under `remove` the migration now deletes a tracked `.agents/docs/README.md`. The deletion is limited to unmodified HEAD content and is backed up first.

Tier: standard.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Goal | Did not mention the intermediate path; implied all of `.agents/docs/` is fixed | Names `.agents/records/docs/README.md` and says other files under `.agents/docs/` stay unfixed | PR-004 |
| E-02 item 1 | "zero file items map to `records/docs/...`" (ambiguous) | Pins `kind == "file"`, and explains why the directory entries still map there harmlessly | PR-005 |
| E-04 | Gated on `make test-all` and `aw check all` passing; targeted run lacked `-o addopts=""` | Records a check baseline before editing; slow tests included; no new Scope-Path diagnostics; `make test-all` explicitly not gated, with the `rryabb` reason | PR-001, PR-002 |
| Project conventions | Called `0hdqbw` approved; said full installs "exceed" 2 s | `0hdqbw` executed (`f4792a7e4`); the install is near 2 s (1.37 s measured) | PR-003, PR-007 |
| F-03, Deferred row 1, OQ-01, Approval gate | Cited `0hdqbw` as approved and in `pending/` | Executed at review HEAD; the dependency is satisfied | PR-003 |
| Deferred row 2 | Silent on the user-file consequence | Records the measured residual defect and recommends a separate backlog item | PR-004 |
| Ordered changes 4, Required tests, V-04 | Listed `make test-all` and an `-o`-less targeted run | Matches the revised E-04, adds the lifecycle lint as a separate gate | PR-001, PR-002, PR-006 |
| POST-GATE LIFECYCLE | Finalize without `aw ipd begin` | Runner owns begin and finalize; a manual run does begin, then work and evidence commits, then finalize | PR-006 |

#### Issues

- None remaining. Lint is clean, and the plan contains no em or en dashes.

### Step R1

- Checked: every cited symbol exists at HEAD. These are `classify_item`, `_AGENTS_RECORD_SUBDIRS` (contains `"docs"`), `_RECORDS_SUBPATH_REWRITES` (five prefixes), `_flatten_records_subpath`, `build_migration_map` (the `if not preserve_in_place:` collision guard), `MigrationManager._handle_leftovers`, `_is_removable_leftover`, `commit_paths`, `project_stage_one_to_scratch`, `engine.collect_scaffold_members` (emits `docs/README.md` only for `layout != "aw"`), `engine.ARTIFACTS_DIR`, `engine.ensure_plans_readmes`, and the sibling test `tests/test_cli.py::Order15CliTests::test_install_legacy_repo_to_aw_flag`. Spec `20260817-2124-01` exists (`implemented/`).
- Found: the `0hdqbw` status and path are stale (PR-003), and the slow-threshold claim was stated as fact without a measurement (PR-007).

### Step R2

- Checked: the E/V bijection is 4/4. `Highest E allocated: 04` is unchanged. The dependency graph E-01 -> E-02, E-03 -> E-04 is acyclic. `From-Backlog`, `Work-Kind: bug`, and `Blocks-Release: next` match backlog `ujxi56`. Each of the backlog's three acceptance criteria maps to E-03.
- Found:
  - E-04's expected outcome cannot be reached, because two of its gates fail at HEAD for unrelated reasons (PR-001).
  - Its targeted command silently ran zero `tests/test_cli.py` tests (PR-002).
  - E-02's zero-items assertion was ambiguous about directory entries (PR-005).
  - The lifecycle finalize lacked `aw ipd begin` (PR-006).

### Step R3

- Checked: the only new destructive effect is deleting `.agents/docs/README.md` under `remove`. Probes confirmed that only a tracked copy unmodified against HEAD is removed, that it is backed up to a tarball first, and that modified, untracked, `defer`, and `keep` copies stay in place. No new subprocess, network, or untrusted-input surface. Rollback is unaffected, because `regenerate` items never enter `move_journal`. No security finding.

### Step R4

- Checked (simplicity): the fix is one classification branch plus one guard condition, and it reuses the existing `.agents/README.md` `regenerate` pattern. OQ-02's rejection of the alternatives rests on code evidence.
- Checked (tests): E-02 and E-03 drive real functions and the CLI and assert on disk state, exit codes, and attention output. No source-reading assertions, so P16 holds. The new end-to-end test is slow-marked and allowlisted, keeping it out of the core-tier budget.
- Found: the Goal overstated coverage of `.agents/docs/`. Any user file there still breaks the attention view (PR-004). That residual is out of the backlog's stated scope, so it is documented rather than expanded into this plan.

### Step S5

- Checked: no question needs a human to unblock this plan. OQ-01 and OQ-02 stay resolved. Where user files under `.agents/docs/` should migrate is a human decision. It belongs to a new backlog item, not to this plan, and the plan now says so.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | MEDIUM | IN-SCOPE | V reachability | `tests/test_runner_resume_clears_stop.py`: `3 failed, 10 passed` (`rryabb`, plan `z6wodh` pending); `aw check all --agent` exit 1 with 12 errors, none at a Scope-Path | E-04 required `make test-all` and `aw check all` to succeed. Both fail at HEAD for unrelated reasons, so the plan could never be completed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 records a pre-edit check baseline and requires no new error or warning at a Scope-Path; `make test-all` is explicitly not gated, with the reason given. |
| PR-002 | MEDIUM | IN-SCOPE | G executability | `tests/test_cli.py` sets `pytestmark = pytest.mark.slow`; default `addopts` deselects `slow` | The targeted run without `-o addopts=""` deselected all of `tests/test_cli.py`, including the sibling `--to-aw` install tests the plan relies on. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04, Required tests, and V-04 use `-o addopts=""` and require `0 failed`. |
| PR-003 | LOW | IN-SCOPE | R1 references | `.aw/records/plans/executed/20261121-2biutm-01-0hdqbw-...ipd.md` (`Status: executed`); `git log` names `f4792a7e4` | The plan cited `0hdqbw` as approved and in `pending/`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Conventions, F-03, Deferred, OQ-01, and the gate state that the dependency is executed and satisfied. |
| PR-004 | MEDIUM | IN-SCOPE | Completeness of the stated goal | Patched probe with a tracked `.agents/docs/notes.md`: `.aw/records/docs` exists, `attention.uninventoried-tree` remains | A user file under `.agents/docs/` still breaks `aw attention` after this fix. The Goal implied otherwise. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Goal and Deferred row 2 state the measured residual and recommend a separate backlog item; scope is unchanged per backlog `ujxi56`. |
| PR-005 | LOW | IN-SCOPE | V precision | Patched `build_migration_map`: `agents:docs` and `agents:records/docs` directory entries map to `records/docs` (`migrate`) | "zero file items map to `records/docs/...`" could be read as zero items of any kind, an assertion that would fail. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 pins `kind == "file"` and explains the harmless directory entries. |
| PR-006 | LOW | IN-SCOPE | Lifecycle | `aw ipd finalize --help` validates a matching `aw ipd begin` receipt | The post-gate clause ran finalize without begin. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Runner-owned, or begin, then commits, then finalize by hand. |
| PR-007 | LOW | IN-SCOPE | Reference accuracy | Probe: E-03 fixture install plus attention took 1.37 s wall serially | The plan asserted full installs "exceed" 2 s. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reworded to "near" the threshold with the measurement; keeping the test slow-marked and allowlisted is still correct. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should E-04 treat repository gates that are red for unrelated reasons? | Baseline-and-compare for `aw check all`; do not gate on `make test-all` | Require both to pass (rejected: unreachable at HEAD); drop the checks (rejected: loses regression signal) | PR-001 measurements | yes |
| D-2 | Should this plan also fix user files under `.agents/docs/`? | No: document the residual and recommend a separate backlog item | Widen scope to route or skip all `.agents/docs/*` files (rejected: user-data placement is a human decision, and backlog `ujxi56` scopes only the README) | PR-004 probe; backlog `ujxi56` acceptance criteria | yes |
| D-3 | Review tier | standard | simple (rejected: Step T question 5 is partly yes, since `remove` now deletes a tracked file) | Step T answers | yes |

### Plans reviewed and not reviewed

- ELIGIBLE: qpvem9 (reviewed; APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 FIXED)
- NOT REVIEWED: (none)

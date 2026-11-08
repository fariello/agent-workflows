# IPD: Move the check_engine, hook and setter git-content readers onto read_at

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` 4.4 requires every reader of a HEAD, staged or branch revision to call `artifact_meta.read_at` instead of parsing git content, and C5a requires every gate and hook to read metadata through the cache. Measured 2026-11-07 at `ac76110f4`: `check_engine._blob_text` (`git show <ref>:<path>`, `:0:<path>`) has 12 call sites in 6 functions across `check_engine`, `hooks/ipd_dependency_statement_gate` and `status_set`, and `check_engine._status_meta` has 35 call sites in 13 functions; `hooks/executed_transition_gate` reads blobs with its own `_blob_at`; `plan_readiness.review_staleness_index` uses `git cat-file --batch`; `ipd_lifecycle._release_own_plan_edit_before_landing` uses `git show <landed>:<path>`. Part 1 of the split of `t4gl15` (Order 09), whose single plan hid several hundred units of work.
- Scope: (a) The part of `t4gl15` E-01 that re-runs the 4.4 search, restricted to the gate, hook, setter and lifecycle files, plus both baselines that must precede every code edit of the `t4gl15` split. (b) `t4gl15` E-02: the `check_engine` git-content readers. (c) `t4gl15` E-03: the four hooks. (d) `t4gl15` E-04 whole: `status_set._prepare_status_change`, `plan_readiness.review_staleness_index`, `ipd_lifecycle._release_own_plan_edit_before_landing` and the five `runner_shared` git-content readers. (e) The residual-audit rows of `t4gl15` E-15 for this plan's hook, readiness and lifecycle modules. EXCLUDES: every other runner read (Order 34 `y97k46`), the record, review and orchestration modules (Orders 35 `jd7874` and 36 `2zpw22`), the new `meta/*.jsonl` append hook, the cache-parity and offline tests and the repo-wide finish (`t4gl15`).
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/hooks/executed_transition_gate.py, agent_workflows/hooks/ipd_dependency_statement_gate.py, agent_workflows/hooks/status_untooled_gate.py, agent_workflows/hooks/backlog_blocking_close_gate.py, agent_workflows/status_set.py, agent_workflows/plan_readiness.py, agent_workflows/ipd_lifecycle.py, agent_workflows/runner_shared.py, agent_workflows/artifact_meta.py, tests/test_readers_read_at_gates.py, .aw/records/plans/pending/20261107-metastore-33-h58z9n-move-the-check-engine-hook-and-setter-git-content-readers-on.ipd.md
- Item-Dependencies: executed:ffceq0, executed:g5hpbb, executed:tve77h, executed:xexn45
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 33
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: h58z9n

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from t4gl15 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).

## Goal

Every gate, hook, setter and runner merge path that reads metadata out of a git revision (HEAD, the index, a commit, a merge stage) reads it through `artifact_meta.read_at`, with each moved reader's verdict pinned by a behavioral test before and after the move.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

The pin-first rule of `ffceq0` applies to every move here (carried from `t4gl15`): BEFORE the edit, a behavioral test in the named module pins the reader's current observable behavior (the ledger in `## Findings`) and runs green on the unmodified code; AFTER the edit, the same test runs unchanged. A test that must change is a behavior change and must be one of `t4gl15`'s decisions D-1 to D-4 (copied below). For every existing module named as a baseline, save the per-test outcome list under the gitignored `.aw/state/t4gl15/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/t4gl15/<E>-before.txt`) before the move and the same command into `<E>-after.txt` after it, where `<E>` is the ORIGINAL `t4gl15` item id named in each item below; `diff` of the two prints nothing except lines a named decision explains. Run a new module's `-k` selection as its own command, never combined with baseline module paths, because `-k` filters every path on the command line. Every saved baseline goes under `.aw/state/t4gl15/`, never `/tmp`. New test modules set `pytestmark = pytest.mark.core` unless they need real `git` subprocesses across many commits, in which case they are marked `slow` and run in `make test-all`; none reads production source.

### Task group 1: search and baselines

- [ ] E-01 (carried from `t4gl15` E-01, gate-file subset) Re-run the 4.4 search for git-content readers and record the result as table F-03 in this plan, for the hits in THIS SUBSET of files only: `agent_workflows/check_engine.py`, `agent_workflows/hooks/executed_transition_gate.py`, `agent_workflows/hooks/ipd_dependency_statement_gate.py`, `agent_workflows/plan_readiness.py`, `agent_workflows/ipd_lifecycle.py` and `agent_workflows/artifact_meta.py` (44 hits in 26 functions at `ac76110f4`; `status_set.py` has no direct hit, because it reads through `check_engine._blob_text`). Command: `rg -n -e '"show"' -e 'cat-file' -e '"ls-files", "-s"' -e '"--cached"' -e '":0:"' -e 'rev-parse' <those six files>`, classifying each hit as metadata reader (moves to `read_at`), path-only reader (no change), or not a metadata read (for example `artifact_meta.read_at` itself, and `ipd_lifecycle` commit-existence and committer-date probes). Any metadata reader not in the 4.4 list is added to E-02 or E-04. The `runner_shared`/`oc_runipd`/`agy_runipd` rows are written by Order 34 (`y97k46`); the rows of the other 31 files by Order 35 (`jd7874`). Before any code edit of the `t4gl15` split (this plan is the first part; every other part depends on it), also save the sorted rule-id counts of `aw check all --agent` to `.aw/state/t4gl15/check-before.txt` and paste those counts into this plan as table F-10, so that the last part (`t4gl15` E-15) can compare against them even when this plan ran in an isolated lane worktree whose gitignored `.aw/state/` is not carried back.
  - Depends on: none
  - Expected outcome: F-03 lists every hit in the six files with its class; the metadata-reader set equals the gate-file subset of F-02 or names the additions; `check-before.txt` is saved and F-10 holds its rule-id counts.
  - Execution state: pending

### Task group 2: read_at gates, hooks and setter

- [ ] E-02 (carried from `t4gl15` E-02) Pin, then move, the `check_engine` git-content readers onto `artifact_meta.read_at`: `_blob_text` and `_status_meta` stop being called by `check_status_untooled`, `check_status_untooled_range`, `check_staged_illegal_backlog_transition`, `_lane_carrier_is_executed`, `_staged_backlog_done_items` and `check_release_gate_consistency`, which call `read_at(id6, ":0:")`, `read_at(id6, "HEAD")` or `read_at(id6, <commit>)` and compare the returned `State`s. The phase-B rule shapes stay (4.4 rewrites them only after the cutover): "status changed with no matching tool-authored history line" compares `read_at` states and their `history` rows; a renamed or moved record is resolved INSIDE each revision, so a staged rename compares the HEAD record at its old path with the staged record at its new path. Pin in `tests/test_readers_read_at_gates.py` (real `git init` fixtures: an untooled status flip refused, a tooled one accepted, a staged rename into `executed/`, an illegal backlog transition, a release-blocking `done` with and without a handoff), and run `tests/test_check_engine_status_meta.py`, `tests/test_check_engine_release_gate.py`, `tests/test_precommit_scope_gate_severity.py` and `tests/test_backlog_close_gate_prose.py` green before and after.
  - Depends on: E-01
  - Expected outcome: every listed test passes before and after; `check_engine` no longer calls `_blob_text` (shown by `rg -n "_blob_text\(" agent_workflows`, which lists only its definition until Order 11 deletes it).
  - Execution state: pending

- [ ] E-03 (carried from `t4gl15` E-03) Move the four hooks onto `read_at`: `executed_transition_gate` (`_blob_at`, `_has_executed_status`, `_plan_id_of`, `_staged_plan_executed_transitions` call `read_at` for `HEAD` and `:0:`; "an executed transition" stays "the staged status is terminal and the HEAD status is not"); `ipd_dependency_statement_gate._staged_ipd_overlay` (staged status and Item-Dependencies from `read_at(id6, ":0:")`); `status_untooled_gate` and `backlog_blocking_close_gate` keep delegating to the moved `check_engine` rules. Pin in `tests/test_readers_read_at_gates.py` through the real CLI entry points (`aw ipd-executed-gate`, `aw ipd-status-untooled-gate`, `aw backlog-blocking-close-gate`, `aw ipd-dependency-statement-gate`) on staged fixture repositories, and run `tests/test_executed_transition_gate.py`, `tests/test_executed_transition_gate_e2e.py` and `tests/test_ipd_dependency_statement_gate.py` green before and after.
  - Depends on: E-02
  - Expected outcome: each hook refuses and accepts the same fixtures before and after with the same exit codes; no hook module contains a `^-` metadata regex or a `git show` of a record.
  - Execution state: pending

- [ ] E-04 (carried from `t4gl15` E-04) Move the remaining 4.4 git-content readers onto `read_at`: `status_set._prepare_status_change` (HEAD status), `plan_readiness.review_staleness_index` (plan status at the latest `plan-review:` commit through `read_at(id6, <commit>)`; the batched `git cat-file --batch` body read stays for the frozen-region digest, which is body prose, N3), `ipd_lifecycle._release_own_plan_edit_before_landing` (the byte comparison of a landed blob is not a metadata read and stays; any status or id read uses `read_at`), and the five `runner_shared` functions (`backlog_item_paths_for_commit`, `check_review_lane_artifacts`, `read_merge_stage`, `classify_conflict_set_for_rederivation`, `integrate_lane_branch` conflict description). For a merge stage blob (`:<stage>:<path>`), `read_at` accepts the stage revision spelling, or the function passes the blob text to `artifact_meta.read_text` (added by `ffceq0`) when no revision name exists. Pin with `tests/test_review_staleness_advisory.py`, `tests/test_ipd_lifecycle_cli.py`, `tests/test_records_only_lane_rederive.py`, `tests/test_runner_backlog_close_behavior.py`, `tests/test_merge_conflict_sendback.py` and `tests/test_status_set.py -k untooled` (5 tests at review; `-k head` selects none) before and after, plus a new `tests/test_readers_read_at_gates.py` case that drives `aw ipd set` on a plan whose working-tree status differs from HEAD and asserts the HEAD status the setter reports is unchanged by the move. (Measured units at `ac76110f4`: 8 functions, 6 baseline modules, 1 new case.)
  - Depends on: E-02
  - Expected outcome: all listed modules pass before and after; F-03's metadata-reader set has no remaining direct git-blob regex read.
  - Execution state: pending

### Task group 3: residual audit and finish

- [ ] E-05 (carried from `t4gl15` E-15, this plan's module subset) Run `rg -n "re\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?[\"'](\(\?m\))?\^-" <files>` and `rg -n "Workflow history" <files>` over `agent_workflows/hooks/executed_transition_gate.py`, `agent_workflows/hooks/status_untooled_gate.py`, `agent_workflows/plan_readiness.py` and `agent_workflows/ipd_lifecycle.py` (31 hits in 17 functions measured at `ac76110f4`; the `check_engine` and `status_set` rows belong to `ffceq0`'s residual table F-12, because both modules are in `ffceq0`'s scope, and `runner_shared` rows to Order 34 `y97k46`), and write table F-04 in this plan listing every remaining hit with its owner: writer (Orders 06/07, named), body-prose bullet kept by N3 (named pattern), a working-tree reader owned by `ffceq0` (named), or a parser that Order 11 deletes. A reader hit with no such owner is a defect of this plan and is moved before finishing. Run every module named in E-02 to E-04 again, the bare core gate `python3 -m pytest` and `aw sanitize --agent`; commit through `aw commit h58z9n -- <each changed path>`, never `git add -A`, a bare `git add` or `git commit -a`. Never push.
  - Depends on: E-03, E-04
  - Expected outcome: F-04 has no unowned reader hit; all runs pass; every commit is path-scoped to Scope-Paths (or justified at finalize).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Interface names from Order 02 (`tve77h`), used exactly: `artifact_meta.read(id6) -> State`, `artifact_meta.history(id6)`, `artifact_meta.query(...)`, `artifact_meta.resolve(path_or_id6)`, and `artifact_meta.read_at(id6, rev)`, which runs git in the repository that owns the resolved records root, resolves the record's path inside that revision (`git ls-files -s` for the index, `git rev-parse <rev>:<path>` for a commit), caches by blob sha in `rev_log_states`/`rev_mirrors`, feeds a miss to the same loader (the legacy loader for a bullet blob in phase B), fails closed on a validation error, and returns distinct results for an absent record, an invalid revision and an unversioned placement. From Order 08 (`ffceq0`): `artifact_meta.read_text(text, *, record_type=None) -> State` and decision D-1 (canonical normalized status for multi-word plans).
- Today's git-content helpers: `check_engine._blob_text(repo_root, ref, path)` (`git show <ref>:<path>`, `:0:<path>` for the index) and `check_engine._status_meta(text)`; `hooks.executed_transition_gate._blob_at`.
- The hooks are thin: `hooks.status_untooled_gate.check` delegates to `check_engine.check_status_untooled`, and `hooks.backlog_blocking_close_gate.check` filters `check_engine.check_release_gate_consistency`; both are dispatched by `cli` (`ipd-status-untooled-gate`, `backlog-blocking-close-gate`, `ipd-executed-gate`, `ipd-dependency-statement-gate`) and installed as optional pre-commit hooks from the `engine` template.
- Core tier: `pytestmark = pytest.mark.core`; tests needing many real git commits use the `slow` marker and run in `make test-all`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-07 at `ac76110f4` (the split measurement); F-02 is copied from `t4gl15` (measured 2026-11-02 at `0cbfcc706`).

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -n "_blob_text\(\|_status_meta\(" agent_workflows` prints 39 lines: the two definitions, 12 `_blob_text` calls (in `check_status_untooled`, `check_status_untooled_range`, `check_staged_illegal_backlog_transition` 8, `_lane_carrier_is_executed`, `check_release_gate_consistency`, `hooks.ipd_dependency_statement_gate._staged_ipd_overlay`, `status_set._prepare_status_change`) and `_status_meta` calls in 13 functions | E-02 moves 6 `check_engine` callers; E-03 and E-04 move the other two. |
| F-02 | (from `t4gl15`) git-content metadata readers moved by this plan: `check_engine._blob_text` callers `check_status_untooled`, `check_status_untooled_range`, `check_staged_illegal_backlog_transition`, `_lane_carrier_is_executed`, `check_release_gate_consistency` (via `_staged_backlog_done_items`); `hooks.executed_transition_gate._blob_at`; `hooks.ipd_dependency_statement_gate._staged_ipd_overlay`; `status_set._prepare_status_change`; `plan_readiness.review_staleness_index` (`git cat-file --batch`); `ipd_lifecycle._release_own_plan_edit_before_landing` (`git show <landed>:<path>`); `runner_shared.backlog_item_paths_for_commit` (`git show <sha>:<path>` then `backlog.parse_item`), `check_review_lane_artifacts` (`git show <branch>:<path>`), `read_merge_stage`, `classify_conflict_set_for_rederivation` (`git cat-file -p`), `integrate_lane_branch` (`git cat-file -p <tree>:<path>` then `check_engine._metadata_status`) | All 15 functions of the 4.4 list. |
| F-03 | (written by E-01) the re-run 4.4 search over this plan's six files, each hit classified, and the merge-stage path chosen (OQ-02 of `t4gl15`). Measured at the split: 44 hits (`check_engine` 11, `hooks/executed_transition_gate` 8, `hooks/ipd_dependency_statement_gate` 2, `plan_readiness` 2, `ipd_lifecycle` 17, `artifact_meta` 4) | 4.4 says the list is a minimum. |
| F-04 | (written by E-05) residual `^-` regex and `Workflow history` hits in this plan's four modules, with owners. Measured at the split: `hooks/executed_transition_gate` 2 hits, `hooks/status_untooled_gate` 3, `plan_readiness` 16, `ipd_lifecycle` 10 | Input to `t4gl15` E-15 and Order 11. |
| F-10 | (written by E-01) rule-id counts of `aw check all --agent` before any edit of the `t4gl15` split | Baseline for `t4gl15` E-15. |

READER LEDGER (this plan's rows, copied from `t4gl15`):

| Reader | Prior behavior | Pinning test | After |
|---|---|---|---|
| `check_engine.check_status_untooled` and `_range` | HEAD vs staged `- Status:` via `_blob_text` + `_status_meta`; refuse with no matching history line | E-02 fixtures; `tests/test_check_engine_status_meta.py`, `tests/test_precommit_scope_gate_severity.py` | same verdicts via `read_at` states and their history |
| `check_engine.check_staged_illegal_backlog_transition`, `_staged_backlog_done_items`, `check_release_gate_consistency`, `_lane_carrier_is_executed` | staged/HEAD backlog and carrier status via git blobs | E-02 fixtures; `tests/test_check_engine_release_gate.py`, `tests/test_backlog_close_gate_prose.py` | same via `read_at` |
| `hooks.executed_transition_gate` | case-insensitive region `status: executed\|done`, `- Id:` outside fences, finalize evidence | `tests/test_executed_transition_gate.py`, `tests/test_executed_transition_gate_e2e.py` | same via `read_at`; D-2 for case |
| `hooks.ipd_dependency_statement_gate` | staged `- Status:` and `Item-Dependencies` overlay | `tests/test_ipd_dependency_statement_gate.py` | same via `read_at(":0:")` |
| `status_set._prepare_status_change` HEAD read | HEAD `- Status:` of the plan path | `tests/test_status_set.py` | `read_at(id6, "HEAD")` |
| `plan_readiness.review_staleness_index` | status at latest `plan-review:` commit plus frozen-region body digest | `tests/test_review_staleness_advisory.py` | status via `read_at`; body digest unchanged (N3) |
| `runner_shared` git readers | backlog id from commit blob, review-lane plan checks, merge-stage keys, conflict status | `tests/test_runner_backlog_close_behavior.py`, `tests/test_records_only_lane_rederive.py`, `tests/test_merge_conflict_sendback.py` | `read_at` or `read_text` |
| `ipd_lifecycle._release_own_plan_edit_before_landing` | byte equality of landed blob vs mirrored bytes | `tests/test_ipd_lifecycle_cli.py` | unchanged (not a metadata read); recorded in F-03 |

DECISIONS (copied from `t4gl15`; authoritative text stays there): D-1 multi-word status (plan records return the canonical normalized status); D-2 the executed-transition hook's case-insensitive match is preserved because the cached status is canonical lower-case.

## Proposed changes (ordered, validatable)

1. Re-run the 4.4 search over this plan's files and save the split-wide `aw check` baseline (E-01).
2. Pin then move the `check_engine` git readers, the four hooks, and the setter, staleness, lifecycle and runner merge-path git readers onto `read_at` (E-02 to E-04).
3. Residual audit for this plan's modules, gates, commit (E-05).

## Deferred / out of scope (with reason)

- The 4.4 search rows for `runner_shared`/`oc_runipd`/`agy_runipd`, the runner selection and execution reads, the own-log finalize scope, and the runner residual rows.
  - Carrier: y97k46
- The 4.4 search rows for the other 31 files, and the plans, research and prompts module reads.
  - Carrier: jd7874
- The review, orchestration, production-check and work module reads.
  - Carrier: 2zpw22
- The `meta/*.jsonl` append hook, the gate cache-parity and offline tests, the repo-wide residual audit and the `CHANGELOG.md` line.
  - Carrier: t4gl15

## Scope check

- Over-scope: none. `artifact_meta.py` changes only if `read_at` must accept a merge-stage revision spelling (E-04), recorded in the finalize scope reconciliation if used. `hooks/status_untooled_gate.py` and `hooks/backlog_blocking_close_gate.py` change only if their delegation needs an argument change; otherwise they are acknowledged unmodified at finalize.
- Under-scope: none known; E-01 and E-05 exist to find what the measurement missed. Size: 5 E-items, 12 Scope-Paths; the largest item (E-01) classifies 44 hits in 26 functions, and the largest move (E-04) edits 8 functions.

## Required tests / validation

New test module: `tests/test_readers_read_at_gates.py` (core unless real multi-commit git fixtures exceed the core budget, then `slow` with the reason in the module docstring). It builds `tmp_path` fixture repositories with real `git init`, calls real functions or the `aw` CLI hook leaves, asserts on exit codes and outputs, and never reads production source. CONTRIBUTES to `4sd62s` AC-16 and AC-33 (gate-level `read_at` use after a rename). Commands: every module named in E-02 to E-04, the bare core gate `python3 -m pytest`, `aw sanitize --agent`.

## Spec / documentation sync

No spec change. Implements the gate, hook, setter and merge-path part of `4sd62s` 4.4 and C5a. CONTRIBUTES to AC-3 and AC-17 (merge-path readers through `read_at`; owned by `xexn45` and `tve77h`).

## Open questions

### OQ-01: Where do the split-wide baselines live?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `.aw/state/` is gitignored, so a baseline saved inside an isolated lane worktree does not reach a later plan. E-01 therefore also pastes the `aw check all --agent` rule-id counts into this plan (F-10), which is tracked; `t4gl15` E-15 compares against F-10. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the exact `rg` command of E-01 with its full output line count, and the F-03 table written into this plan with one row per hit and a class column (metadata reader / path-only / not a metadata read); every metadata-reader row names the E-item (E-02, E-03 or E-04) that moves it; `ls -l .aw/state/t4gl15/check-before.txt`; and the F-10 table.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff --stat agent_workflows/check_engine.py` empty before the move, then `python3 -m pytest -o addopts="" -v tests/test_readers_read_at_gates.py -k check_engine` all PASSED (untooled flip refused, tooled flip accepted, staged rename into `executed/`, illegal backlog transition, release-blocking done with and without handoff) and `diff .aw/state/t4gl15/E-02-before.txt .aw/state/t4gl15/E-02-after.txt` (outcome lists of `tests/test_check_engine_status_meta.py tests/test_check_engine_release_gate.py tests/test_precommit_scope_gate_severity.py tests/test_backlog_close_gate_prose.py`) printing nothing; paste `rg -n "_blob_text\(" agent_workflows` showing only the definition.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_readers_read_at_gates.py -k hook` all PASSED, each test driving the real `aw ipd-executed-gate`, `aw ipd-status-untooled-gate`, `aw backlog-blocking-close-gate` or `aw ipd-dependency-statement-gate` leaf on a staged fixture and asserting the exit code; `diff .aw/state/t4gl15/E-03-before.txt .aw/state/t4gl15/E-03-after.txt` (outcome lists of `tests/test_executed_transition_gate.py tests/test_executed_transition_gate_e2e.py tests/test_ipd_dependency_statement_gate.py`) printing nothing; and `rg -n "\^-|\"show\"" agent_workflows/hooks/` showing no metadata regex or record `git show`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `diff .aw/state/t4gl15/E-04-before.txt .aw/state/t4gl15/E-04-after.txt` (outcome lists of `tests/test_review_staleness_advisory.py tests/test_ipd_lifecycle_cli.py tests/test_records_only_lane_rederive.py tests/test_runner_backlog_close_behavior.py tests/test_merge_conflict_sendback.py`) printing nothing, the same diff for `tests/test_status_set.py -k untooled` showing 5 or more selected tests, the new HEAD-status setter case PASSED, and the F-03 row recording which merge-stage path (`read_at` stage spelling or `read_text`) was used.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the two `rg` commands of E-05 and the F-04 table (every remaining hit with its owner, none unowned); the bare `python3 -m pytest` summary line and wall time; the `aw sanitize --agent` result with zero `fail`; and every `aw commit h58z9n` output listing only Scope-Paths (or paths justified at finalize).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `ffceq0`, `g5hpbb`, `tve77h` and `xexn45` are executed. OQ-01 is resolved and not blocking.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every reader move is pin-first.

Honesty rule: run the named modules and `python3 -m pytest` (core gate), and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit h58z9n -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.

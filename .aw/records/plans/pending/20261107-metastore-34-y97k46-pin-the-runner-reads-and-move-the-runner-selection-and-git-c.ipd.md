# IPD: Pin the runner reads and move the runner selection and execution reads onto artifact_meta

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` C5a requires every runner to read metadata through the cache. `runner_shared` holds one plan record for both hosts (`runner_shared.PlanRecord`, built by `runner_shared.parse_plan_file`), and the queue is built from it by per-file regex reads. Measured 2026-11-07 at `ac76110f4`: `runner_shared` has 68 metadata reader or regex sites in 26 functions (`_SET_RE`, `_ORDER_RE`, `_KIND_RE`, `read_front_matter_*`, `backlog.parse_item`, `ipd_schema.read_readiness`, `^-` regexes), and `oc_runipd` and `agy_runipd` re-export 10 of those names. Part 2 of the split of `t4gl15` (Order 09): this part pins the runner's metadata behavior and moves both the plan-selection reads (the queue-building path) and the execution-path reads, in two task groups, and adds the 4.4 own-log finalize scope rule.
- Scope: (a) The `runner_shared`/`oc_runipd`/`agy_runipd` rows of the 4.4 search of `t4gl15` E-01. (b) `t4gl15` E-06 whole (pin the runner reads). (c) `t4gl15` E-07 whole, split into its plan-selection subset (E-03) and its execution-path subset (E-04), each named site by site. (d) `t4gl15` E-08 whole (own-log finalize scope, E-05). (e) The `runner_shared`/`oc_runipd`/`agy_runipd` rows of `t4gl15` E-15's residual audit (E-06). EXCLUDES: the five `runner_shared` git-content readers (Order 33, `h58z9n`); every writer (Orders 06/07), including `record_oq_answer`, `perform_coordinator_proposal_file`, `mark_plan_attended`, `set_plan_approved`, the `_fail_incomplete` status rewrite and the WRITE half of `rederive_front_matter`; deleting parsers (Order 11).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/ipd_lifecycle.py, tests/test_readers_runner.py, tests/test_front_matter_loose_whitespace.py, .aw/records/plans/pending/20261107-metastore-34-y97k46-pin-the-runner-reads-and-move-the-runner-selection-and-git-c.ipd.md
- Item-Dependencies: executed:ffceq0, executed:g5hpbb, executed:h58z9n, executed:tve77h, executed:xexn45
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 34
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: y97k46

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from t4gl15 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).

## Goal

The runner builds its queue (plan discovery, selectors, dependency edges, disposition and freeze checks) and executes items (item execution, review sequence, production-set retries, backlog resolution) from `artifact_meta.read`/`query` instead of per-file regexes, on both hosts, with the observable behavior pinned before the move and unchanged after it except the named D-1 status normalization; a finalized plan's own metadata log is in its scope; and every remaining runner regex hit has a named owner.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

The pin-first rule of `ffceq0` applies to every move here (carried from `t4gl15`): BEFORE the edit, a behavioral test in the named module pins the reader's current observable behavior and runs green on the unmodified code; AFTER the edit, the same test runs unchanged. A test that must change is a behavior change and must be one of decisions D-1 to D-4 (copied below from `t4gl15`). For every existing module named as a baseline, save the per-test outcome list under the gitignored `.aw/state/t4gl15/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/t4gl15/<E>-before.txt`) before the move and the same command into `<E>-after.txt` after it, where `<E>` is the ORIGINAL `t4gl15` item id named below; `diff` of the two prints nothing except lines a named decision explains. Run a new module's `-k` selection as its own command. Every saved baseline goes under `.aw/state/t4gl15/`, never `/tmp`. A count measured at authoring (for example F-05's 1,719 records) is context, never the bar. New test modules set `pytestmark = pytest.mark.core` unless they need real `git` subprocesses across many commits (then `slow`); none reads production source.

### Task group 1: search rows and pin

- [ ] E-01 (carried from `t4gl15` E-01, runner-file subset) Re-run the 4.4 search over `agent_workflows/runner_shared.py`, `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` (`rg -n -e '"show"' -e 'cat-file' -e '"ls-files", "-s"' -e '"--cached"' -e '":0:"' -e 'rev-parse' <those files>`; 53 hits in 38 functions at `ac76110f4`) and record the result as table F-03 in this plan. Classify the 9 hits in the 6 functions that read a blob (`backlog_item_paths_for_commit`, `check_review_lane_artifacts`, `read_merge_stage`, `classify_conflict_set_for_rederivation`, `integrate_lane_branch`, `describe_recorded_commits`) one row each: the first five are the metadata readers that Order 33 (`h58z9n`) E-04 moved, and `describe_recorded_commits` (`git cat-file -e <sha>^{commit}`) is an existence probe, not a metadata read. Classify the remaining 44 hits (`rev-parse` and `--cached` only, in 32 functions, whose output is a commit id, a path or a ref and cannot carry record metadata) in ONE bulk row of class path-only that lists every function name. Any metadata reader the search finds that is not in the 4.4 list is reported as a defect of `h58z9n` and moved here before E-03.
  - Depends on: none
  - Expected outcome: F-03 has 6 single rows plus one bulk row naming 32 functions; no unclassified hit.
  - Execution state: pending

- [ ] E-02 (carried from `t4gl15` E-06) Pin the runner's metadata behavior in `tests/test_readers_runner.py`: `runner_shared.parse_plan_file` on both hosts (`oc_runipd.parse_plan_file`, `agy_runipd` re-export) for id, status (single token, loose whitespace, multi-word falls back to the directory bucket), kind, Set, Order, Item-Dependencies, From-Backlog, Attended; `discover_plans`, `discover_specs`, `edge_satisfied` for `executed:`, `exists:` and `state:` edges, `resolve_backlog_item`, `backlog_item_paths_for_id`, `read_set_membership`, `expand_selectors` (id6, Set, status selectors), `plan_bucket`, `reconcile_disposition`, `enforce_freeze_time_refusal`, and the readiness read used before auto-approval (`plan_readiness.is_plan_review_approved`, 4.4a row `l56tyz`: a missing readiness is refused). Run `tests/test_front_matter_loose_whitespace.py`, `tests/test_runner_shared.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, `tests/test_typed_queue_entries.py`, `tests/test_run_selection_policy.py`, `tests/test_spec_review_dispatch.py`, `tests/test_readiness_absence_invariant.py`, `tests/test_attended_session.py` and `tests/test_freeze_time_refusal.py` green as the baseline (`.aw/state/t4gl15/E-06-before.txt`). (Measured units: 13 pinned functions and 10 baseline modules.)
  - Depends on: none
  - Expected outcome: the new module passes on the unmodified code; the ten baseline summary lines are recorded.
  - Execution state: pending

### Task group 2: move the selection reads

- [ ] E-03 (carried from `t4gl15` E-07, plan-selection subset) Move these runner reads onto `artifact_meta.read`/`query`/`history`: `parse_plan_file` builds `PlanRecord` from `artifact_meta.read(id6)` resolved by path; `discover_plans`/`discover_specs` use one `query()` (the `read_front_matter_status` call in `discover_specs` is replaced); `expand_dependency_closure` and `edge_satisfied` read target status and dependencies from the cache; `reconcile_disposition` (its `^-` status regex and two `_read_status` calls), `enforce_freeze_time_refusal` (two `_read_status` calls), `plan_bucket`, `expand_selectors`, `read_set_membership` and `plan_audit_target` read through the moved `parse_plan_file` or the cache; `_read_set`, `_read_order`, `_read_kind`, `_read_item_dependencies` and `_read_from_backlog` lose their callers in this list (their `_SET_RE`, `_ORDER_RE` and `_KIND_RE` uses in the execution path move in E-04, and the definitions stay until Order 11 deletes them). Plan text read for prompts and bodies still reads the file (N3). `oc_runipd`/`agy_runipd` keep their `_read_id` re-exports (`tools/ipdrunner/runagy.py` consumes `agy_runipd._read_id`) bound to the moved selector function, and keep their `_SET_RE`/`_ORDER_RE`/`_KIND_RE` re-export names. `parse_plan_file` keeps today's loose `-  `/`-\t` tolerance (D-4) by taking `id` and `status` from the loose values that `ffceq0`'s `artifact_meta.read_text` returns when the strict cached value is absent; the fallbacks for a missing Set, Order or id6 (filename, then a path hash) are unchanged. (Measured units: 19 functions or re-export bindings.)
  - Depends on: E-02
  - Expected outcome: E-02 and its ten baseline modules pass unchanged except the assertions D-1 names; a `python3 -c` snippet that prints `sorted((r.id6, r.status, r.setid, r.order, r.kind, tuple(r.dependencies)) for r in runner_shared.discover_plans(Path(".").resolve()).values())` for this checkout, saved to `.aw/state/t4gl15/discover-before.txt` before the edit, prints the same list after the move except the status values D-1 names (measured at review: one record, `vfa1tl`, changes from `EXECUTED` to `executed`; F-05's count is context) (`aw oc run` has no dry-run mode, measured with `aw oc run start --help`).
  - Execution state: pending

### Task group 3: move the execution reads and own-log scope

- [ ] E-04 (carried from `t4gl15` E-07, execution-path subset) Move these runner reads onto `artifact_meta.read`/`query`/`history`: `execute_item_core` (4 `_SET_RE`, 3 `backlog.parse_item`, 1 `^-` regex and 1 `ipd_schema.read_readiness` site), `initialize_run_core` (its `parse_plan_file`/`discover_plans` consumers, verified to use the moved functions), `run_review_sequence` and `_promote_reviewed_plan` (one `read_readiness` each), `handle_review_orchestrator_readiness`, `production_set_findings_are_retryable` (3 `_SET_RE`), `production_set_retry_attempts` and `production_set_retry_key_already_spent` (1 `_SET_RE` each), `resolve_backlog_item`, `backlog_item_paths_for_id` and `populate_manifest_backlog` (1 `backlog.parse_item` each), `declared_spec_paths` (the `- Scope-Paths:` regex) and `enforce_no_active_runner_conflict` (the `- Id:` regex). Plan text read for prompts and bodies (lint, review sequence, scope reconciliation of body sections) still reads the file (N3). `runner_shared._front_matter_bullets` and `_split_metadata_region` keep their roles only inside the records-only conflict classifier and `rederive_front_matter` (merge-stage text) until `artifact_meta.read_text` serves them; their remaining uses are listed in F-04. Record `.aw/state/t4gl15/E-07x-before.txt` (the ten E-02 baseline modules plus `tests/test_readers_runner.py`) before this edit and `E-07x-after.txt` after it. (Measured units: 24 sites in 13 functions.)
  - Depends on: E-03
  - Expected outcome: the two outcome lists are equal except lines D-1 names; `rg -n "_SET_RE|parse_item\(|read_readiness\(" agent_workflows/runner_shared.py` lists none of the 13 functions.
  - Execution state: pending

- [ ] E-05 (carried from `t4gl15` E-08) Treat a finalized plan's own `meta/<id6>.jsonl` as a path the plan owns (4.4 bullet on `runner_shared._body_change_is_history_insert_only`): `compute_scope_reconciliation`, `_body_change_is_history_insert_only` and the finalize scope check in `ipd_lifecycle` accept a change to `.aw/records/meta/<own id6>.jsonl` without a Scope-Paths entry and still flag another artifact's log. Test in `tests/test_readers_runner.py` with a finalize-scope fixture that changes its own log and another plan's log.
  - Depends on: E-04
  - Expected outcome: the own-log change is in scope, the other plan's log is reported out of scope.
  - Execution state: pending

### Task group 4: runner residual audit and finish

- [ ] E-06 (carried from `t4gl15` E-15, runner subset) Run `rg -n "re\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/runner_shared.py agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` and `rg -n "Workflow history" <the same files>` (40 hits in 21 functions at `ac76110f4`, before this plan) and write table F-04 in this plan listing every remaining hit with its owner: writer (Orders 06/07, named: `record_oq_answer`, `perform_coordinator_proposal_file`, `mark_plan_attended`, `set_plan_approved`, `_fail_incomplete`, `rederive_front_matter`, `resolve_history_append_conflict`, `_write_fallback_record`, `process_backlog_close`, `commit_review_lane_output`), body-prose bullet kept by N3 (named pattern), or a parser that Order 11 deletes (the module-level `_SET_RE`, `_ORDER_RE`, `_KIND_RE`, `_HISTORY_BULLET_RE`, `_FRONT_MATTER_BULLET_RE` definitions). A reader hit with no such owner is a defect of this plan and is moved before finishing. Run `tests/test_readers_runner.py`, the ten E-02 baseline modules and the bare core gate `python3 -m pytest`; commit through `aw commit y97k46 -- <each changed path>`, never `git add -A`, a bare `git add` or `git commit -a`. Never push.
  - Depends on: E-04, E-05
  - Expected outcome: F-04 has no unowned reader hit; all runs pass; every commit is path-scoped to Scope-Paths (or justified at finalize).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Interface names from Order 02 (`tve77h`): `artifact_meta.read(id6) -> State`, `artifact_meta.history(id6)`, `artifact_meta.query(...)` (type, status, Set, order, `depends_on`, `latest_gate_review_of`, `path` filters, and an `incomplete` list), `artifact_meta.resolve(path_or_id6)`. From Order 08 (`ffceq0`): `artifact_meta.read_text(text, *, record_type=None) -> State` and decision D-1.
- One runner plan record serves both hosts: `runner_shared.PlanRecord` (`id6`, `setid`, `status`, `order`, `path`, `rel_path`, `dependencies`, `kind`, `dependency_error`, `from_backlog`) built by `runner_shared.parse_plan_file`; `oc_runipd` re-exports `selectors.read_front_matter_id as _read_id`, and `tools/ipdrunner/runagy.py` consumes `agy_runipd._read_id`.
- `runner_shared._front_matter_bullets` and `_split_metadata_region` feed the records-only conflict classifier (`classify_records_only_front_matter_conflict`) and `rederive_front_matter` (plan `kl18sz`).
- Cite code by SYMBOL (`module.function`), never a bare line number (advisory `IPD-C801`).

## Findings

Measured 2026-11-07 at `ac76110f4`; F-05 and F-06 copied from `t4gl15` (2026-11-02 at `0cbfcc706`).

| Id | Evidence | Finding |
|---|---|---|
| F-01 | Reader sites per `runner_shared` function, measured with an AST pass over `rg` hits of `_SET_RE\|_ORDER_RE\|_KIND_RE\|read_front_matter_\w+\(\|parse_item\(\|_read_set\(\|_read_order\(\|_read_item_dependencies\(\|_read_from_backlog\(\|read_readiness\(\|_metadata_status\(` plus the `^-` regex pattern: 68 sites in 26 functions; module-level definitions 18; `execute_item_core` 9; writers `record_oq_answer` 6 and `perform_coordinator_proposal_file` 6 (Orders 06/07) | E-03 moves the selection functions; E-04 the execution functions. |
| F-02 | Execution-function reader sites: `execute_item_core` 9, `production_set_findings_are_retryable` 3, `production_set_retry_attempts` 1, `production_set_retry_key_already_spent` 1, `run_review_sequence` 1, `_promote_reviewed_plan` 1, `resolve_backlog_item` 1, `backlog_item_paths_for_id` 1, `populate_manifest_backlog` 1, `declared_spec_paths` 1, `enforce_no_active_runner_conflict` 1 | 21 direct sites for E-04; `initialize_run_core` and `handle_review_orchestrator_readiness` read through the moved functions. |
| F-03 | (written by E-01) the runner-file 4.4 rows | 4.4 says the list is a minimum. |
| F-04 | (written by E-06) residual `^-` regex and `Workflow history` hits in the three runner files with owners. Measured at the split: `runner_shared` 38 hits in 19 functions (module level 10), `oc_runipd` 2 | Input to `t4gl15` E-15 and Order 11. |
| F-05 | `runner_shared.discover_plans(repo)` returns 1,719 records on this checkout (at `0cbfcc706`) | Baseline context for E-03's parity check. |
| F-06 | `aw oc run` sub-commands are `start, resume, status, report, stop, integrate, audit`; none has a dry-run option | E-03 compares `discover_plans` output instead of a queue preview. |

READER LEDGER (this plan's rows, copied from `t4gl15`):

| Reader | Prior behavior | Pinning test | After |
|---|---|---|---|
| `runner_shared.parse_plan_file` (both hosts) | loose `^-\s*` id/status/kind/Set/Order; multi-word status falls back to the directory bucket (`pending`) | `tests/test_front_matter_loose_whitespace.py`, E-02 | D-1, D-4 |
| `runner_shared.discover_plans`, `discover_specs`, `edge_satisfied`, `expand_selectors`, `resolve_backlog_item` | per-file regex reads | E-02 module, `tests/test_runner_shared.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, `tests/test_typed_queue_entries.py`, `tests/test_run_selection_policy.py`, `tests/test_spec_review_dispatch.py` | cached fields; same `discover_plans` list (F-05) |
| `plan_readiness.is_plan_review_approved` | structured readiness believed only with review provenance in history; missing readiness refused (4.4a `l56tyz`) | `tests/test_readiness_absence_invariant.py` | same rule over cached readiness and `history` (pinned here; not moved by this plan) |

DECISIONS (copied from `t4gl15`, whose text is authoritative):

- D-1 (multi-word status): PLAN records return the canonical normalized status (`plans.normalize_status` of the first token); every other type keeps its raw single-token status. `runner_shared.parse_plan_file` today returns the directory bucket for a multi-word value and now returns the normalized first-token value. The one test assertion that changes is the fixture in `tests/test_front_matter_loose_whitespace.py::test_single_token_status_contract_survives`, whose multi-word `EXECUTED (approved by maintainer)` in `pending/` now yields `executed` instead of `pending`; that test is updated and listed in Scope-Paths. Measured at review: `discover_plans` differs on one record only (`vfa1tl`, `EXECUTED` to `executed`).
- D-4 (loose whitespace in the runner): KEPT; the runner takes `id` and `status` from `read_text`'s loose values when the strict value is absent (E-03), so `tests/test_front_matter_loose_whitespace.py::test_parse_plan_file_tolerates_loose_leading_whitespace` passes unchanged.

## Proposed changes (ordered, validatable)

1. Record the runner-file 4.4 rows (E-01).
2. Pin the runner reads (E-02).
3. Move the plan-selection reads (E-03).
4. Move the execution-path reads; own-log finalize scope (E-04, E-05).
5. Runner residual audit, commit (E-06).

## Deferred / out of scope (with reason)

- The five `runner_shared` git-content readers (moved onto `read_at`).
  - Carrier: h58z9n
- The runner writers named in E-06.
  - Carrier: xexn45
- Deleting the module-level runner parsers.
  - Carrier: 9o83cr

## Scope check

- Over-scope: none. `tests/test_front_matter_loose_whitespace.py` changes only in the D-1 assertion; `ipd_lifecycle.py` changes only for the E-05 finalize scope check.
- Under-scope: none known. Size: 6 E-items in 4 task groups, 7 Scope-Paths; per-item units: E-01 53 hits classified as 6 rows plus 1 bulk row, E-02 23, E-03 19, E-04 24, E-05 3 functions, E-06 40 hits classified (edits only unowned reader hits).

## Required tests / validation

New test module: `tests/test_readers_runner.py` (core). It builds `tmp_path` fixture repositories, calls real functions, asserts on returned values and never reads production source. CONTRIBUTES to `4sd62s` AC-21 row `l56tyz` (pasted `tests/test_readiness_absence_invariant.py`; AC-21 is owned by `xexn45`). Commands: the ten E-02 baseline modules, `tests/test_readers_runner.py`, the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change. Implements the runner part of `4sd62s` C5a and section 7 step 5, and the 4.4 finalize own-log rule.

## Open questions

### OQ-01: How is the runner move split?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Into two task groups of this plan, at the seam `t4gl15` OQ-03 named (E-03: `parse_plan_file`, `discover_*`, `edge_satisfied` and the other queue-building reads; E-04: `execute_item_core`/`initialize_run_core`/review-sequence reads), not into two plans: each item is under the 25-unit bound and both share one pinning module and one baseline. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the exact `rg` command of E-01 with its output line count and the F-03 table (6 single rows, one bulk row naming every function), with no unclassified hit.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff --stat agent_workflows/runner_shared.py agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` empty, `python3 -m pytest -o addopts="" -v tests/test_readers_runner.py` all PASSED on the unmodified code (including the `l56tyz` missing-readiness refusal), `wc -l` of the ten baseline modules' outcome list `.aw/state/t4gl15/E-06-before.txt`, and `wc -l .aw/state/t4gl15/discover-before.txt`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `diff .aw/state/t4gl15/E-06-before.txt .aw/state/t4gl15/E-07-after.txt` printing nothing or only lines D-1 names, `git diff tests/` showing only D-1 assertions, `diff .aw/state/t4gl15/discover-before.txt <(python3 -c '<the E-03 snippet>')` printing only the D-1 status lines (each named).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `diff .aw/state/t4gl15/E-07x-before.txt .aw/state/t4gl15/E-07x-after.txt` printing nothing or only lines D-1 names, `git diff tests/` showing only D-1 assertions, and `rg -n "_SET_RE|parse_item\(|read_readiness\(" agent_workflows/runner_shared.py` with each remaining hit's enclosing function named and none of the 13 functions present.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_readers_runner.py -k own_log` PASSED, asserting that a finalize-scope fixture changing `.aw/records/meta/<own id6>.jsonl` is in scope while a change to another plan's log is reported out of scope.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the two `rg` commands of E-03 and the F-04 table (every remaining hit with its owner, none unowned); the bare `python3 -m pytest` summary line and wall time; and every `aw commit y97k46` output listing only Scope-Paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `ffceq0`, `g5hpbb`, `h58z9n`, `tve77h` and `xexn45` are executed. OQ-01 is resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every reader move is pin-first, and a test edited after a move must be one that D-1 to D-4 name.

Honesty rule: run the named modules and `python3 -m pytest` (core gate), and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit y97k46 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.

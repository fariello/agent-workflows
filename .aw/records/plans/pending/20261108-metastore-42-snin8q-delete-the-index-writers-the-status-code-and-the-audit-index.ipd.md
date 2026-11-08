# IPD: Delete the INDEX writers, the STATUS code and the audit index cache

- Date: 2026-11-08
- Kind: child
- Concern: Spec `4sd62s` 4.5 says the SQLite cache REPLACES the `INDEX.{json,md}` files, `plans/STATUS.md` and `artifact_audit._INDEX_CACHE`. Once Order 41 (`q6epwc`) has removed every caller of the INDEX write path, the writers themselves, the dead STATUS renderer and the in-process audit cache are still in the package. Measured 2026-11-07 at `ac76110f4`: `rg -n "build_index_(json|md)|emit_index_(write|check)_result|DEFAULT_INDEX_LIMIT|_set_last_touched" agent_workflows` prints 50 lines in 7 files; 11 test modules import one of those symbols or `run_index`; `rg -n "render_status_index|write_index" agent_workflows` prints 6 lines; `rg -n "_INDEX_CACHE" agent_workflows tests` prints 29 lines (10 in `artifact_audit`, 19 in three test modules). Part 2 of the split of `9o83cr` (Order 11).
- Scope: `9o83cr` E-03 (INDEX writers), E-06 (STATUS code) and E-07 (`_INDEX_CACHE`), carried verbatim with their original ids, plus a baseline item E-01 and a finishing item E-17 that are new to this part. EXCLUDES: the aliases, regeneration calls and stale-index rules (Order 41, `q6epwc`); value writers, adapters and parsers (Orders 43 to 46); the AC-1 test, audit and documents (`9o83cr`); on-disk INDEX files and skip names (`cxxmyv`).
- Scope-Paths: agent_workflows/plans_index.py, agent_workflows/research_index.py, agent_workflows/prompts_index.py, agent_workflows/artifact_core.py, agent_workflows/record_producers.py, agent_workflows/plans_archive.py, agent_workflows/research_archive.py, agent_workflows/ipd_lifecycle.py, agent_workflows/plans.py, agent_workflows/cli.py, agent_workflows/artifact_audit.py, tests/test_plans_index.py, tests/test_research_index.py, tests/test_prompts_index.py, tests/test_index_write_agent_records.py, tests/test_index_check_agent_records.py, tests/test_drift_rule_registration.py, tests/test_model_vocab.py, tests/test_research_priority.py, tests/test_research_unsafe_field.py, tests/test_research_set_assign_date_containment.py, tests/test_plans_board.py, tests/test_support_section.py, tests/test_artifact_audit_cache_eviction.py, tests/test_artifact_audit_index_cache.py, tests/test_artifact_audit_identity_staleness.py, .aw/records/plans/pending/20261108-metastore-42-snin8q-delete-the-index-writers-the-status-code-and-the-audit-index.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:q6epwc, executed:t4gl15
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 42
- Highest E allocated: 17
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: snin8q

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 9o83cr per maintainer step-complexity rule (no single E/V item hides hundreds of steps).

## Goal

No INDEX writer, STATUS renderer or audit index cache remains in the package: `aw find` and the content drift rules keep working from `scan_*`/`query`/`check_drift`, and `artifact_audit.build_index` answers from the metadata cache on every call.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Item ids E-03, E-06 and E-07 are the ids these items had in `9o83cr`; they are kept so cross-references in sibling plans still point at the right item. E-01 and E-17 are new to this part: E-01 is this part's own baseline (a subset of `9o83cr` E-01), because `.aw/state/` does not travel between lane worktrees; "the E-01 baseline" in the carried text means this plan's E-01.

PIN RULE for every deletion or retarget (carried from `9o83cr`): before the edit, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/snin8q/<E>-before.txt`); after it, run the same command into `<E>-after.txt`. A retargeted test keeps every input case, so the after-list may rename a test but not drop a case; the evidence pastes both lists and maps each removed name to its successor. A test whose only subject is a deleted INDEX byte or the removed LRU is deleted, and the evidence names it.

### Task group 1: baseline and deletions

- [ ] E-01 Record this part's baseline before any edit, under the gitignored `.aw/state/snin8q/before/`: the stdout and exit code of `aw check plans --all --agent`, `aw check research --all --agent`, `aw check prompts --all --agent` (rule-id multisets, `jq -r '.diagnostics[].rule' | sort | uniq -c`), `aw find plans --agent`, `aw ipd board` (as `board.txt`), and the bare core gate summary line of `python3 -m pytest`.
  - Depends on: none
  - Expected outcome: the saved outputs and a core gate summary exist under `.aw/state/snin8q/before/`.
  - Execution state: pending

- [ ] E-03 Delete the INDEX writers and their result helpers: `build_index_json`, `build_index_md`, `_set_last_touched` and the write path of `run_index` in `plans_index`, `research_index` and `prompts_index`; `DEFAULT_INDEX_LIMIT`; `artifact_core.emit_index_write_result` and `emit_index_check_result`; the `plans_index` and `research_index` (and any prompts) entries in `record_producers`. Keep `scan_*`, `query`, `run_find` and the non-INDEX drift classes of each `check_drift` (F-04), which `check_engine.check_content` still reaches. Delete or retarget the tests that assert INDEX bytes (`tests/test_plans_index.py`, `tests/test_research_index.py`, `tests/test_prompts_index.py`, `tests/test_index_write_agent_records.py`, `tests/test_index_check_agent_records.py`), keeping every assertion about `aw find` results and non-INDEX drift findings. `prompts_index` has no `run_find` (it has `scan_prompts` and `check_drift`); keep those. Measured at `ac76110f4` and added at the split: the two direct writers outside the index modules, `plans_archive._refresh_index` and the post-move refresh in `research_archive` (each writes `INDEX_JSON`/`INDEX_MD` with `build_index_json`/`build_index_md`), are deleted here too, and the `DEFAULT_INDEX_LIMIT` reference in `ipd_lifecycle._refresh_plans_index_fail_loud` goes with that function in Order 41; the other test modules that call a deleted symbol (`tests/test_drift_rule_registration.py`, `tests/test_model_vocab.py`, `tests/test_research_priority.py`, `tests/test_research_unsafe_field.py`, `tests/test_research_set_assign_date_containment.py`) are retargeted to `check_drift` or `aw find`. Measured units: 14 definitions in 4 production files, 2 archive writers, 2 `record_producers` entries, 10 test modules: about 28.
  - Depends on: E-01
  - Expected outcome: `rg -n "build_index_(json|md)|emit_index_(write|check)_result|DEFAULT_INDEX_LIMIT" agent_workflows` prints nothing; `aw check plans --all --agent`, `aw check research --all --agent` and `aw check prompts --all --agent` report the same non-INDEX rule multiset as the E-01 baseline.
  - Execution state: pending

- [ ] E-06 Delete the STATUS code: `plans.render_status_index` and the unreachable `write_index` branch of `cli._run_plans` (no parser defines `--write-index`, F-02). Retarget `tests/test_plans_board.py` and `tests/test_support_section.py` from `render_status_index` to the observable `aw ipd board` output. Measured units: 1 function, 1 branch, 2 test modules: 4.
  - Depends on: E-01
  - Expected outcome: `rg -n "render_status_index|write_index" agent_workflows` prints only `run_cli.write_index` (the run ledger, unrelated); `aw ipd board` output is byte-identical to the E-01 baseline.
  - Execution state: pending

- [ ] E-07 Delete `artifact_audit._INDEX_CACHE` and `_INDEX_CACHE_MAX` (4.5: the cache replaces it): `artifact_audit.build_index` answers from `artifact_meta.query`/`resolve` on every call. Delete `tests/test_artifact_audit_cache_eviction.py` (it tests the removed LRU) and retarget the freshness assertions of `tests/test_artifact_audit_index_cache.py` and `tests/test_artifact_audit_identity_staleness.py` to the behavior: a record added, deleted or moved after a first `build_index` call is reflected by the second call. Measured units: 10 lines in `artifact_audit`, 3 test modules (19 lines): about 6 edits.
  - Depends on: E-01
  - Expected outcome: `rg -n "_INDEX_CACHE" agent_workflows tests` prints nothing; the retargeted tests pass.
  - Execution state: pending

### Task group 2: finish

- [ ] E-17 Finish: run every test module named in E-03, E-06 and E-07, the bare core gate `python3 -m pytest`, `aw check plans --all --agent`, `aw check research --all --agent` and `aw check prompts --all --agent` (rule multisets equal the E-01 baselines; any difference traced to a record changed in between), `aw ipd lint` on this plan, and `aw sanitize --agent`; commit through `aw commit snin8q -- <paths>` with only Scope-Paths files, never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-03, E-06, E-07
  - Expected outcome: all runs pass; every commit's `git show --stat` lists only Scope-Paths files (or paths justified at finalize).
  - Execution state: pending

## Project conventions discovered (Step 0)

- `check_engine.check_content` calls `plans_index.check_drift` and `research_index.check_drift` (and, after Order 41, `prompts_index.check_drift`), which host non-INDEX rules (F-04), so those functions survive with their INDEX classes removed.
- `artifact_core.emit_index_check_result` and `emit_index_write_result` are called only from the three `run_index` functions; `artifact_core.emit_index_missing_dir_refusal` is a separate refusal helper and stays if any caller remains (check at execution).
- `run_cli.write_index` writes the run ledger projection and is unrelated to INDEX manifests.
- Test data comes from ONE builder, `tests/record_builder.py` (`59aiyh`); core tests carry `pytestmark = pytest.mark.core`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-07 at `ac76110f4`. F-02, F-04 and F-10 are copied from `9o83cr`.

| Id | Evidence | Finding |
|---|---|---|
| F-02 | Writers: `plans_index.run_index` (`json_path.write_text`, `md_path.write_text`), `research_index.run_index`, `prompts_index.run_index`, `artifact_core.emit_index_write_result`. `plans.render_status_index` is reached only from `cli._run_plans` `if getattr(args, "write_index", False)`, and no parser defines `--write-index`. | E-03, E-06. |
| F-04 | Non-INDEX drift rules inside `check_drift` (see `q6epwc` F-04). | Kept by E-03. |
| F-10 | `artifact_audit._INDEX_CACHE: OrderedDict` with `_INDEX_CACHE_MAX = 8` inside `artifact_audit.build_index`; tests `tests/test_artifact_audit_index_cache.py` (6 lines), `tests/test_artifact_audit_cache_eviction.py` (7), `tests/test_artifact_audit_identity_staleness.py` (6). | E-07. |
| F-23 | `rg -c "build_index_(json|md)|emit_index_(write|check)_result|DEFAULT_INDEX_LIMIT|_set_last_touched" agent_workflows`: `plans_index` 14, `research_index` 15, `prompts_index` 14, `artifact_core` 2, `plans_archive` 2, `research_archive` 2, `ipd_lifecycle` 1. Test modules naming one of them or `run_index`: 11 (listed in E-03; `tests/test_orchestrator_retirement.py` names only `_refresh_plans_index_fail_loud`, owned by Order 41). | The archive writers were not in the original E-03 list; added here so no writer survives. |

## Proposed changes (ordered, validatable)

1. Baseline (E-01).
2. Delete the INDEX writers (E-03), the STATUS code (E-06) and the audit cache (E-07); E-06 and E-07 are independent of E-03.
3. Validate and commit (E-17).

## Deferred / out of scope (with reason)

- Aliases, regeneration calls and stale-index rules.
  - Carrier: q6epwc
- The residual inventory, the AC-1 test and audit, and the INDEX documents.
  - Carrier: 9o83cr
- Deleting the on-disk INDEX files and `plans/STATUS.md`, and the skip-name entries that protect scans from them.
  - Carrier: cxxmyv

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 5 E-items, 27 Scope-Paths entries (11 production modules, 15 test modules, this plan); the largest item (E-03) hides about 28 units.

## Required tests / validation

Retargeted modules: those named in E-03, E-06 and E-07. Commands: `python3 -m pytest` (core gate), `aw check <type> --all --agent`, `aw ipd board`, `aw sanitize --agent`. CONTRIBUTES to AC-9 (owned by `9o83cr`; final proof `cxxmyv`).

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.5 and section 7 step 7.

## Open questions

### OQ-01: Should `plans_index`, `research_index` and `prompts_index` be renamed once they write no index?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Carried from `9o83cr` OQ-02. No. They still host `aw find` backends (`run_find`, `query`) and the F-04 content rules; renaming is churn the spec does not ask for and would widen this plan's diff across 17 importing modules. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls -l .aw/state/snin8q/before/` showing each saved output with its exit code, the three `aw check <type> --all` rule multisets, and the core gate `N passed` summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the empty output of `rg -n "build_index_(json|md)|emit_index_(write|check)_result|DEFAULT_INDEX_LIMIT" agent_workflows`; paste `aw check plans --all --agent`, `aw check research --all --agent` and `aw check prompts --all --agent` rule-id multisets (`jq -r '.diagnostics[].rule' | sort | uniq -c`) beside the E-01 baselines, equal; and the summary lines of `python3 -m pytest -o addopts="" tests/test_plans_index.py tests/test_research_index.py tests/test_prompts_index.py tests/test_index_check_agent_records.py tests/test_drift_rule_registration.py tests/test_model_vocab.py tests/test_research_priority.py tests/test_research_unsafe_field.py tests/test_research_set_assign_date_containment.py` (or the note that a module was deleted, with the `git diff --stat` line), with the PIN-rule before/after lists and each removed test name mapped to its successor or named as an INDEX-byte-only test.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `rg -n "render_status_index|write_index" agent_workflows` showing only `run_cli.write_index`; `diff <(aw ipd board) .aw/state/snin8q/before/board.txt` empty (board saved in E-01); and the summary lines of `python3 -m pytest -o addopts="" tests/test_plans_board.py tests/test_support_section.py` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the empty output of `rg -n "_INDEX_CACHE" agent_workflows tests`, the `git diff --stat` line deleting `tests/test_artifact_audit_cache_eviction.py`, and `python3 -m pytest -o addopts="" -v tests/test_artifact_audit_index_cache.py tests/test_artifact_audit_identity_staleness.py` with the add, delete and move freshness cases PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-17 validates E-17
  - Required evidence: paste the bare `python3 -m pytest` summary line, the three `aw check <type> --all --agent` rule multiset diffs against E-01 (empty, or each difference traced), `aw sanitize --agent` with zero `fail`, and `git show --stat` of every `aw commit snin8q` commit listing only Scope-Paths files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: 27 Scope-Paths entries against a guide of about 12, because the INDEX writers are imported by 15 test modules. The production change is one concern (no code can write an INDEX file, a STATUS file or an in-process index cache) and each test module only loses or retargets the assertions on a deleted symbol, under the PIN rule. Splitting the writers from their tests would leave a commit whose tests import deleted symbols, which fails the core gate (C10a). Every E-item stays at about 25 units (E-03 about 28).

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Every deletion is pin-first (PIN RULE above). Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`). Honesty rule: paste the ACTUAL summary lines; never claim a result you did not run. Commits: only through `aw commit snin8q -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.

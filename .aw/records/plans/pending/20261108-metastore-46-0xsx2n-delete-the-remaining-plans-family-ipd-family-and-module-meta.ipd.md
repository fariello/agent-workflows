# IPD: Delete the remaining plans-family, ipd-family and module metadata regular expressions

- Date: 2026-11-08
- Kind: child
- Concern: Spec `4sd62s` 4.3 requires deleting every `^-` metadata regular expression outside `artifact_meta`, and AC-1 audits for them. Measured 2026-11-07 at `ac76110f4` (see `e8420v` F-26 for the census method): after Orders 43 to 45, 106 literals remain in 30 modules other than `check_engine`, `runner_shared`, `status_set` and `releases`. Of these, 24 are the patterns of readers that Order 43 (`k6jd6l`) deletes (`backlog` 10, `specs` 9, `selectors` 5) and should already be gone; the other 82 are spread over 27 modules with one to eight literals each. Part 6 of the split of `9o83cr` (Order 11).
- Scope: `9o83cr` E-12, its site list SPLIT across two plans by module: this plan takes every module not covered by Order 45 (`e8420v`), as four items by module family (E-21 to E-24), plus a baseline item E-01 and a finishing item E-17. The site lists of `e8420v` and this plan together equal the original E-12 list. EXCLUDES: `check_engine`, `runner_shared`, `status_set`, `releases` (Order 45); body-prose bullets (N3) and `comms` (N4); the legacy loader inside `artifact_meta`.
- Scope-Paths: agent_workflows/plans_index.py, agent_workflows/plans_refs.py, agent_workflows/plans_archive.py, agent_workflows/artifact_rename.py, agent_workflows/artifact_refs.py, agent_workflows/artifact_adopt.py, agent_workflows/artifact_audit.py, agent_workflows/ipd_lint.py, agent_workflows/ipd_lifecycle.py, agent_workflows/ipd_schema.py, agent_workflows/ipd_authoring.py, agent_workflows/plan_readiness.py, agent_workflows/readiness_recheck.py, agent_workflows/coverage_record.py, agent_workflows/orchestrator_readiness.py, agent_workflows/attention.py, agent_workflows/attention_contract.py, agent_workflows/review_sequence.py, agent_workflows/review_findings.py, agent_workflows/research_index.py, agent_workflows/production_checks.py, agent_workflows/work_cmd.py, agent_workflows/set_records.py, agent_workflows/hooks/executed_transition_gate.py, agent_workflows/cli.py, agent_workflows/run_viewer.py, agent_workflows/git_commit_helper.py, agent_workflows/backlog.py, agent_workflows/specs.py, agent_workflows/selectors.py, tests/test_review_findings_gate.py, tests/test_artifact_audit.py, tests/test_coverage_record.py, tests/test_plans_archive.py, .aw/records/plans/pending/20261108-metastore-46-0xsx2n-delete-the-remaining-plans-family-ipd-family-and-module-meta.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:k6jd6l, executed:t4gl15
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 46
- Highest E allocated: 24
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 0xsx2n

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 9o83cr per maintainer step-complexity rule (no single E/V item hides hundreds of steps).

## Goal

No module outside `artifact_meta` (other than the four Order 45 covers) holds a `^-` metadata regular expression: every surviving `^-` literal is body prose (N3), a non-metadata grammar, or a listed exclusion.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

The original `9o83cr` E-12 text is quoted in full in `e8420v` (Order 45). This plan carries it for the modules named in its Scope, including the named E-12 sites `review_findings._META_RE` (the round and finding grammar stays, N3), `plans_index._META_RE` and `plans_index._meta`, `plan_readiness._STATUS_RE` and `artifact_audit._STATUS_LINE_RE`, and "every other `^-` metadata regex literal in F-20" for these modules. Each site is deleted by reading the value through `artifact_meta.read`, `read_text` or `read_at` at its caller; a literal that matches body prose (N3) or a non-metadata grammar is classed and kept, not deleted. Update code comments in the touched modules that cite a deleted symbol. E-21 to E-24 are new ids for the four module-family subsets; E-01 and E-17 are new.

PIN RULE for every deletion or retarget (carried from `9o83cr`): before the edit, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/0xsx2n/<E>-before.txt`); after it, run the same command into `<E>-after.txt`. A retargeted test keeps every input case.

### Task group 1: baseline

- [ ] E-01 Before any edit: save the rule-id multisets of `aw check all --agent` and `aw check all --all --agent`, `aw find plans --agent`, `aw attention --format json` and the bare core gate summary line to `.aw/state/0xsx2n/before/`; re-run `rg -n "re\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?[\"'](\(\?m\))?\^-"` over each Scope-Paths module and write F-27: one row per hit, classed `delete (E-21..E-24)`, `body prose (N3)`, `non-metadata` or `already gone`.
  - Depends on: none
  - Expected outcome: the baselines exist and F-27 has a class on every row.
  - Execution state: pending

### Task group 2: deletions by module family

- [ ] E-21 (`9o83cr` E-12, subset plans and artifact family) Sites at the split (24 literals): `plans_index` (6 module-level, including `_META_RE` and the `_meta` reader), `plans_refs` (5: `_ID_RE`, `_DATE_RE`, `_SET_LINE_RE`, `_ORDER_LINE_RE`, and the `order_lines` literal in `_set_metadata` if Order 43 left it), `plans_archive` (5: `_ID_RE`, and the inline literals in `_plan_date`, `_resolve_plan_date`, `_plan_status`, `sweep_candidates`), `artifact_rename` (5: `_SET_LINE_RE`, `_ORDER_LINE_RE`, `_ID_LINE_RE`, `_STATUS_LINE_RE`, `_DATE_LINE_RE`), `artifact_refs` (1, in `classify_citing_plans_for_rewrite`), `artifact_adopt` (1, `_BULLET_ID_RE`), `artifact_audit` (1, `_STATUS_LINE_RE`). Update `tests/test_artifact_audit.py` and `tests/test_plans_archive.py` where a test names a deleted pattern.
  - Depends on: E-01
  - Expected outcome: no F-27 `delete (E-21)` row survives the re-run search; `aw find plans --agent` matches E-01.
  - Execution state: pending

- [ ] E-22 (`9o83cr` E-12, subset ipd and readiness family) Sites at the split (25 literals): `ipd_lint` (4: `_HISTORY_LINE_RE`, `_CITATION_PLAN_DATE_RE`, and the `m_stat`/`m_prio` literals in `run_lint`), `ipd_lifecycle` (4, in `_insert_scope_exceeded_metadata`, a WRITER that moves to `artifact_meta.append`), `ipd_schema` (3: the literal in `plan_requires_attended`, `_META_LINE_RE`, `_READINESS_LINE_RE`), `ipd_authoring` (2: `_ID_LINE_RE`, `_WATERMARK_RE`), `plan_readiness` (6: `_READINESS_FIELD_PRESENT_RE`, `_READINESS_LINE_SUB_RE`, `_STATUS_RE`, the two `id6_match` literals in `approval_refusals` and `recheck_conditions`; `_OQ_FIELD_RE` is body prose, N3, and stays), `readiness_recheck` (1, in `_run_stale_findings`), `coverage_record` (4: `_COVERAGE_LINE_RE`, `_STATUS_LINE_RE`, `_READINESS_LINE_RE`, `_ID_LINE_RE`), `orchestrator_readiness` (1, `_BATCH_META_RE`). `ipd_schema`'s E/V checklist and section grammar stays (N3). Update `tests/test_coverage_record.py` where a test names a deleted pattern.
  - Depends on: E-01
  - Expected outcome: no F-27 `delete (E-22)` row survives the re-run search; `tests/test_ipd_lint*.py`, `tests/test_coverage_record.py` and `tests/test_orchestrator_readiness.py` pass.
  - Execution state: pending

- [ ] E-23 (`9o83cr` E-12, subset attention, review and research) Sites at the split (17 literals): `attention` (8: `_ITEM_DEPS_RE` and the literals in `_plans_id`, `_release_record` (2), `_spec_record`, `_plans_record` (2); `_OQ_STATUS_RE` is an open-question row, body prose, N3, and stays), `attention_contract` (4: `GATE_KIND_RE`, `GATE_REF_RE`, `GATE_SUMMARY_RE`, `HISTORY_RECORD_RE`), `review_sequence` (2, in `restore_pre_s7_plan`, a WRITER that moves to `artifact_meta.append`), `review_findings` (1, `_META_RE`; the round and finding grammar stays, N3), `research_index` (2: `_META_ID_RE` and the literal in `_backlog_is_done`). Update `tests/test_review_findings_gate.py` where a test names a deleted pattern.
  - Depends on: E-01
  - Expected outcome: no F-27 `delete (E-23)` row survives the re-run search; `aw attention --format json` matches E-01; `tests/test_review_findings_gate.py`, `tests/test_attention*.py` and `tests/test_research_index.py` pass.
  - Execution state: pending

- [ ] E-24 (`9o83cr` E-12, subset remaining modules) Sites at the split: `production_checks` (5: `_PLAN_ID_RE`, `_ITEM_DEPS_RE`, `_SCOPE_PATHS_RE`, `_ITEM_FROM_BACKLOG_RE`, `_SET_RE`), `work_cmd` (3, in `_plan_id6`, `_plan_status`, `_warn_if_begin_skipped`), `set_records` (1, in `write_walkthrough`), `hooks/executed_transition_gate` (1, in `_plan_id_of`), `cli` (2, in `_run_search`), and any of the 24 `backlog`, `specs` and `selectors` literals that Order 43 left (expected none: `backlog` `_ID_RE`, `_STATUS_RE`, `_SET_RE`, `_PRIORITY_RE`, `_WORK_KIND_RE`, `_KIND_RE`, `_SUMMARY_RE`, `_BLOCKS_RELEASE_RE`, `_CLOSE_EVIDENCE_RE`, `_TOP_KEY_RE`; `specs` `_BLOCKS_RELEASE_RE`, `_SPEC_ID_RE`, `_PRIORITY_RE`, `_WORK_KIND_RE`, `_SCOPE_RE`, `_SUMMARY_RE`, `_TOP_KEY_RE`, the literal in `run_migrate`, `_SPEC_ID_BULLET_RE`; `selectors` `_ID_RE`, `_FRONT_MATTER_ID_RE`, `_FRONT_MATTER_STATUS_RE`, `_FRONT_MATTER_BLOCKS_RELEASE_RE`, `_YAML_FENCE_CLOSE_RE`). Classed `non-metadata` unless E-01 shows otherwise: `run_viewer.load_run_summary` (3: run-report `Created:`/`Updated:`/`Selectors:` lines, not artifact metadata), `git_commit_helper._DIVIDER_RE` (`^---`, a commit-message divider), and the `_YAML_FENCE_CLOSE_RE` fences in `selectors` and `cli` (a fence, not a field; it goes only if its YAML reader is gone). Measured units: 12 metadata sites plus up to 24 leftovers expected to be zero, and 6 `non-metadata` rows to class: about 18.
  - Depends on: E-01
  - Expected outcome: no F-27 `delete (E-24)` row survives the re-run search; every `non-metadata` row is named in F-27 for the `9o83cr` E-14 exclusion file.
  - Execution state: pending

### Task group 3: finish

- [ ] E-17 Finish: run every test module named in E-21 to E-24, the bare core gate `python3 -m pytest`, `aw check all --agent` and `aw check all --all --agent` (rule multisets equal E-01), `aw find plans --agent` and `aw attention --format json` (equal E-01), `aw ipd lint` on this plan and `aw sanitize --agent`; commit through `aw commit 0xsx2n -- <paths>` with only Scope-Paths files, one commit per item allowed, never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-21, E-22, E-23, E-24
  - Expected outcome: all runs pass; every commit's `git show --stat` lists only Scope-Paths files (or paths justified at finalize).
  - Execution state: pending

## Project conventions discovered (Step 0)

- N3 keeps Markdown body bullets (open-question rows such as `plan_readiness._OQ_FIELD_RE` and `attention._OQ_STATUS_RE`, E/V checklist fields, review rounds and findings) outside `artifact_meta`; their patterns are `body prose` and stay, and `9o83cr` E-14 lists them in its exclusion file.
- A literal inside a function that REWRITES a bullet (`ipd_lifecycle._insert_scope_exceeded_metadata`, `review_sequence.restore_pre_s7_plan`) is a writer; its replacement is an `artifact_meta.append` event, not a read.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-27 | Site census at `ac76110f4` (method in `e8420v` F-26): 106 literals in 30 modules outside Order 45's four. Families: plans and artifact 24; ipd and readiness 27 (2 of them body prose); attention, review and research 18 (1 body prose); remaining modules 37 (24 expected gone with Order 43, 6 non-metadata). Re-derived by E-01. | Four items, each at or under about 25 delete sites. |

## Proposed changes (ordered, validatable)

1. Baseline and F-27 (E-01).
2. Delete the four module-family subsets (E-21 to E-24); they are independent.
3. Validate and commit (E-17).

## Deferred / out of scope (with reason)

- `check_engine`, `runner_shared`, `status_set` and `releases` literals and parsers.
  - Carrier: e8420v
- The residual inventory F-20, the AC-1 test and the AC-1 audit with its exclusion file.
  - Carrier: 9o83cr

## Scope check

- Over-scope: none.
- Under-scope: none known; E-01 re-derives the site list. Size: 6 E-items; 35 Scope-Paths entries (30 modules holding one to ten literals each, 4 test modules, this plan).

## Required tests / validation

Named test modules of each touched module (at least `tests/test_review_findings_gate.py`, `tests/test_artifact_audit.py`, `tests/test_coverage_record.py`, `tests/test_plans_archive.py`, `tests/test_ipd_lint*.py`). Commands: `python3 -m pytest` (core gate), `aw check all --agent`, `aw check all --all --agent`, `aw find plans --agent`, `aw attention --format json`, `aw sanitize --agent`. CONTRIBUTES to AC-1 (owned by `9o83cr`).

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.3 and section 7 step 7.

## Open questions

### OQ-01: Are run-report and commit-message bullets metadata?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. `run_viewer.load_run_summary` parses a run report's `Created:`/`Updated:`/`Selectors:` lines and `git_commit_helper._DIVIDER_RE` parses a commit-message divider; neither is artifact metadata in the sense of spec 4.3 section 1, so both are classed `non-metadata` and listed in the `9o83cr` E-14 exclusion file, which is where AC-1 allows explicit exclusions. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls -l .aw/state/0xsx2n/before/`, the `rg` command with its hit count, and F-27 as written with a class on every row.
  - Observed evidence:
  - Result: pending

- [ ] V-21 validates E-21
  - Required evidence: paste the re-run `rg` over the E-21 modules showing no `delete (E-21)` row, the summary lines of `python3 -m pytest -o addopts="" tests/test_artifact_audit.py tests/test_plans_archive.py tests/test_plans_index.py tests/test_artifact_rename.py` passing, and `diff` of `aw find plans --agent` against E-01, empty.
  - Observed evidence:
  - Result: pending

- [ ] V-22 validates E-22
  - Required evidence: paste the re-run `rg` over the E-22 modules showing only `body prose` rows, and the summary lines of `python3 -m pytest -o addopts="" tests/test_ipd_lint*.py tests/test_coverage_record.py tests/test_orchestrator_readiness.py tests/test_ipd_schema.py tests/test_ipd_authoring.py` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-23 validates E-23
  - Required evidence: paste the re-run `rg` over the E-23 modules showing only `body prose` rows, the summary lines of `python3 -m pytest -o addopts="" tests/test_review_findings_gate.py tests/test_review_sequence.py tests/test_attention*.py tests/test_research_index.py` passing, and `diff` of `aw attention --format json` against E-01, empty.
  - Observed evidence:
  - Result: pending

- [ ] V-24 validates E-24
  - Required evidence: paste the re-run `rg` over the E-24 modules showing only `non-metadata` rows, each named in F-27, and the summary lines of the touched modules' tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-17 validates E-17
  - Required evidence: paste the bare `python3 -m pytest` summary line, the two `aw check all` rule multiset diffs and the `aw find`/`aw attention` diffs against E-01 (empty, or each difference traced), `aw sanitize --agent` with zero `fail`, and `git show --stat` of every `aw commit 0xsx2n` commit listing only Scope-Paths files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: 35 Scope-Paths entries against a guide of about 12. The step bound holds (each item at or under about 25 sites). The residual literals are spread thinly (one to eight per module over 30 modules), so any partition by module either keeps many paths per plan or needs more Order numbers than this split was allotted; the four items are independent and each is verified separately, so a run that stops after any item leaves a consistent, green tree.

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Every deletion is pin-first (PIN RULE above). Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Honesty rule: paste the ACTUAL summary lines; never claim a result you did not run. Commits: only through `aw commit 0xsx2n -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.

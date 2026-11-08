# IPD: Delete the check_engine, runner, setter and release metadata parsers and regular expressions

- Date: 2026-11-08
- Kind: child
- Concern: Spec `4sd62s` 4.3 requires deleting every metadata parser and `^-` metadata regular expression outside `artifact_meta`, and AC-1 audits for them. Measured 2026-11-07 at `ac76110f4`: `rg -n "re\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows` prints 211 literals in 36 files; excluding `artifact_meta.py`, the E/V and open-question checklist fields (N3), and the 18 literals that Order 43 deletes with their writers and readers, 168 remain in 34 files. Four files hold 62 of them: `check_engine` 30, `runner_shared` 16, `status_set` 10 and `releases` 6; `check_engine` also defines the named parsers `_blob_text`, `_status_meta` and `_metadata_status` (51 references, 50 of them in modules a phase-B reader plan already moves). Part 5 of the split of `9o83cr` (Order 11).
- Scope: `9o83cr` E-12, its site list SPLIT across two plans by module: this plan takes the `check_engine`, `runner_shared` (with the `oc_runipd`/`agy_runipd` re-exports), `status_set` and `releases` sites and the `tools/gate_drop_audit.py` retarget, as three items (E-12, E-19, E-20); Order 46 (`0xsx2n`) takes every other module. Plus a baseline item E-01 and a finishing item E-17. EXCLUDES: the readers and writers of Order 43; body-prose bullets (N3: open-question rows, E/V checklist fields), `comms` (N4); the legacy loader inside `artifact_meta`.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/status_set.py, agent_workflows/releases.py, agent_workflows/hooks/ipd_dependency_statement_gate.py, agent_workflows/prompts.py, tools/gate_drop_audit.py, tests/test_check_engine_status_meta.py, tests/test_gate_drop_audit.py, tests/test_runner_shared.py, tests/test_status_set.py, tests/test_releases.py, .aw/records/plans/pending/20261108-metastore-45-e8420v-delete-the-check-engine-runner-setter-and-release-metadata-p.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:k6jd6l, executed:t4gl15
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 45
- Highest E allocated: 20
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: e8420v

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 9o83cr per maintainer step-complexity rule (no single E/V item hides hundreds of steps).

## Goal

`check_engine`, `runner_shared`, `status_set` and `releases` contain no metadata parser and no `^-` metadata regular expression: each rule, runner step and setter reads metadata through `artifact_meta`, and every rule finding is unchanged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

The original `9o83cr` E-12 text is: "Delete the remaining parsers and regular expressions classed `delete` in F-20, at least: `check_engine._blob_text`, `_status_meta` and `_metadata_status`; `runner_shared._front_matter_bullets` and its re-exports in `oc_runipd`/`agy_runipd`; `review_findings._META_RE` (the round and finding grammar stays, N3); `plans_index._META_RE` and `plans_index._meta`; `status_set._STATUS_RE` and its `finditer` loop; `releases._STATUS_RE`; `plan_readiness._STATUS_RE`; `artifact_audit._STATUS_LINE_RE`; and every other `^-` metadata regex literal in F-20. Update code comments in the touched modules that cite a deleted symbol. Retarget `tools/gate_drop_audit.py` (`check_engine._status_meta`, `backlog.parse_item`) to `artifact_meta.read`/`read_at`, keeping `tests/test_gate_drop_audit.py` green." This plan carries it for the modules named in its Scope; each item below names its exact site subset (measured at `ac76110f4`, re-derived by E-01). E-12 keeps the `9o83cr` id for the `check_engine` subset; E-19 and E-20 are the runner and setter/release subsets; E-01 and E-17 are new. Each site is deleted by reading the value through `artifact_meta.read`, `read_text` or `read_at` at its caller; a literal that matches body prose (N3) is NOT a metadata parser and is classed `body prose`, not deleted.

PIN RULE for every deletion or retarget (carried from `9o83cr`): before the edit, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/e8420v/<E>-before.txt`); after it, run the same command into `<E>-after.txt`. A retargeted test keeps every input case.

### Task group 1: baseline

- [ ] E-01 Before any edit: save the rule-id multisets of `aw check all --agent` and `aw check all --all --agent` and the bare core gate summary line to `.aw/state/e8420v/before/`; re-run `rg -n "re\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/check_engine.py agent_workflows/runner_shared.py agent_workflows/status_set.py agent_workflows/releases.py` and `rg -n "_blob_text|_status_meta\b|_metadata_status\b|_front_matter_bullets" agent_workflows tools tests`, and write F-26: one row per hit, classed `delete (E-12|E-19|E-20)`, `body prose (N3)` or `already gone`.
  - Depends on: none
  - Expected outcome: the baselines exist and F-26 has a class on every row.
  - Execution state: pending

### Task group 2: deletions by module

- [ ] E-12 (`9o83cr` E-12, subset `check_engine`) Delete `check_engine._blob_text`, `_status_meta` and `_metadata_status` and every `^-` metadata regex literal in `check_engine`. Sites at the split (30 literals): the named patterns `_ID_LINE_RE`, `_SET_LINE_RE`, `_IDENT_ID_BULLET_RE`, `_IDENT_SET_BULLET_RE`, `_STATUS_META_RE`, `_ITEM_ID_RE`, `_ITEM_PRIORITY_RE`, `_ITEM_WORK_KIND_RE`, `_META_BLOCKS_RELEASE_RE`, `_META_CLOSE_EVIDENCE_RE`, `_META_FROM_BACKLOG_RE`, `_ITEM_FROM_SPEC_RE` (defined twice), `_PLAN_STATUS_RE`, `_ITEM_DEPENDENCIES_RE`, `_DATE_LINE_RE`, `_REVIEW_SUBJECT_TYPE_RE`, `_FROM_SPEC_LINE_RE`, `_SCOPE_PATHS_LINE_RE`, `_CARRIER_DATE_RE`; the inline literals in `_artifact_compact_date`, `evaluate_handoff_ready`, `check_spec_review_attestation`, `find_obligations_carried_by`, `check_ipd_lint_reach` and `check_orchestrator_not_review_ready` (three). Classed `body prose` (kept, N3) unless E-01 shows otherwise: `_TARGET_BULLET_RE` (Concern/Scope/Scope-Paths prose targets), the `parse_spec_acceptance_criteria` table-rule literal (`^-+$`, a Markdown table divider). Also retarget the `_status_meta`/`_blob_text` callers in `hooks/ipd_dependency_statement_gate.py` (2) and `status_set` (2), and `_metadata_status` in `runner_shared` (1) and `prompts` (if still present). Update `tests/test_check_engine_status_meta.py`. Most of the 50 references of the three named parsers sit in `check_engine` functions that Orders 29 to 33 already move; at the split about 25 edit sites remain (28 literals plus 5 external callers minus the `body prose` rows).
  - Depends on: E-01
  - Expected outcome: no F-26 `delete (E-12)` row survives the re-run search; `aw check all --agent` and `aw check all --all --agent` rule multisets equal the E-01 baselines.
  - Execution state: pending

- [ ] E-19 (`9o83cr` E-12, subset runner) Delete `runner_shared._front_matter_bullets` and its re-exports in `oc_runipd`/`agy_runipd`, and every `^-` metadata regex literal in `runner_shared`. Sites at the split (16 literals): the named `_SET_RE`, `_ORDER_RE`, `_KIND_RE`, `_HISTORY_BULLET_RE` (defined twice), `_FRONT_MATTER_BULLET_RE`; inline literals in `declared_spec_paths`, `enforce_no_active_runner_conflict`, `run_review_sequence` (the `- Status:` rewrite to `to-review`, a WRITE that must go through `artifact_meta.append`), `reconcile_disposition`, `execute_item_core`, `perform_coordinator_proposal_file` (three). Classed `body prose` (kept, N3) unless E-01 shows otherwise: the two `record_oq_answer` literals (open-question row `- Status: open` and its bullet scan). Update `tests/test_runner_shared.py`. Measured units: 14 delete sites, 5 `_front_matter_bullets` references, 2 re-exports: about 21.
  - Depends on: E-01
  - Expected outcome: no F-26 `delete (E-19)` row survives the re-run search; `python3 -m pytest -o addopts="" tests/test_runner_shared.py` passes.
  - Execution state: pending

- [ ] E-20 (`9o83cr` E-12, subset setter and release) Delete `status_set._STATUS_RE` and its `finditer` loop and `releases._STATUS_RE`, and every other `^-` metadata regex literal in `status_set` and `releases`. Sites at the split: `status_set` (10) `_ID_RE`, `_STATUS_RE`, `_SET_RE`, `_GATE_KIND_RE`, `_GATE_REF_RE`, `_GATE_SUMMARY_RE`, the three inline searches in `_format_status_transition_line` and the `finditer` loop in `plan_priority_work_kind_problems`; `releases` (6) `_ID_RE`, `_STATUS_RE`, `_VERSION_RE`, `_SUMMARY_RE`, `_ITEM_FROM_BACKLOG_RE`, `_ITEM_GRADUATED_TO_RE` (the `releases` line-writer patterns go with the writers in Order 43). Retarget `tools/gate_drop_audit.py` (`check_engine._status_meta`, `backlog.parse_item`) to `artifact_meta.read`/`read_at`, keeping `tests/test_gate_drop_audit.py` green. Update `tests/test_status_set.py` and `tests/test_releases.py` only where a test names a deleted pattern. Measured units: 16 literals and their 23 internal uses (each a one-line swap), 2 `tools` call sites: about 25.
  - Depends on: E-01
  - Expected outcome: no F-26 `delete (E-20)` row survives the re-run search; `rg -n "_status_meta|parse_item\(" tools/` prints nothing; `tests/test_gate_drop_audit.py`, `tests/test_status_set.py` and `tests/test_releases.py` pass.
  - Execution state: pending

### Task group 3: finish

- [ ] E-17 Finish: update code comments in the touched modules that cite a deleted symbol; run every test module named in E-12, E-19 and E-20, the `tests/test_check_engine*.py` modules, the bare core gate `python3 -m pytest`, `aw check all --agent` and `aw check all --all --agent` (rule multisets equal E-01), `aw ipd lint` on this plan and `aw sanitize --agent`; commit through `aw commit e8420v -- <paths>` with only Scope-Paths files, one commit per item allowed, never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-12, E-19, E-20
  - Expected outcome: all runs pass; every commit's `git show --stat` lists only Scope-Paths files (or paths justified at finalize).
  - Execution state: pending

## Project conventions discovered (Step 0)

- `check_engine._status_meta` and `_blob_text` read a git blob's text and its status bullet; their callers reach `artifact_meta.read_at(id6, rev)` or `read_text(blob_text)` after phase B.
- `runner_shared.run_review_sequence` rewrites a plan's `- Status:` line with `re.sub`; that is a WRITE and moves to `artifact_meta.append` (a `set` event of `status`), not to a reader.
- N3 keeps Markdown body bullets (open-question rows, E/V checklist fields, prose targets) out of `artifact_meta`; their patterns are `body prose` and stay.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-26 | `^-` literal census at `ac76110f4`: 211 in 36 files; minus `artifact_meta.py` (16), minus E/V and open-question field literals, minus the 18 literals Order 43 deletes with their writers and readers: 168 in 34 files. This plan: `check_engine` 30, `runner_shared` 16, `status_set` 10, `releases` 6 (62). Order 46: the other 106 in 30 files. Named parsers: `_blob_text` 18, `_status_meta` 23, `_metadata_status` 5, `_front_matter_bullets` 5 references. Re-derived by E-01. | Split by module so no item exceeds about 25 sites. |

## Proposed changes (ordered, validatable)

1. Baseline and F-26 (E-01).
2. Delete the `check_engine` (E-12), runner (E-19) and setter/release (E-20) sites; the three are independent.
3. Validate and commit (E-17).

## Deferred / out of scope (with reason)

- The remaining modules' regex literals (`9o83cr` E-12 for every module not named here).
  - Carrier: 0xsx2n
- The residual inventory F-20, the AC-1 test and audit.
  - Carrier: 9o83cr

## Scope check

- Over-scope: none.
- Under-scope: none known; E-01 re-derives the site list. Size: 5 E-items, 15 Scope-Paths entries; the largest item hides about 25 units.

## Required tests / validation

Named test modules of each touched module (at least `tests/test_runner_shared.py`, `tests/test_status_set*.py`, `tests/test_check_engine*.py`, `tests/test_gate_drop_audit.py`, `tests/test_releases.py`). Commands: `python3 -m pytest` (core gate), `aw check all --agent`, `aw check all --all --agent`, `aw sanitize --agent`. CONTRIBUTES to AC-1 (owned by `9o83cr`).

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.3 and section 7 step 7.

## Open questions

### OQ-01: Is the split of `9o83cr` E-12 by module safe?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes. Each literal is private to its module (none of the 62 sites here is imported elsewhere except `_status_meta`, `_blob_text`, `_metadata_status` and `_front_matter_bullets`, whose external callers this plan retargets), so the two parts can merge in either order and each leaves `main` green. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls -l .aw/state/e8420v/before/`, the two `rg` commands with their hit counts, and F-26 as written with a class on every row.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: paste the re-run `rg` over `agent_workflows/check_engine.py` showing only rows classed `body prose`, `rg -n "_blob_text|_status_meta\b|_metadata_status\b" agent_workflows tools` printing nothing, the summary lines of `python3 -m pytest -o addopts="" tests/test_check_engine*.py` passing, and the `aw check all --agent` and `aw check all --all --agent` rule multiset diffs against E-01, empty.
  - Observed evidence:
  - Result: pending

- [ ] V-19 validates E-19
  - Required evidence: paste the re-run `rg` over `agent_workflows/runner_shared.py` showing only rows classed `body prose`, `rg -n "_front_matter_bullets" agent_workflows tests` printing nothing, and `python3 -m pytest -o addopts="" -v tests/test_runner_shared.py` with every test PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-20 validates E-20
  - Required evidence: paste the re-run `rg` over `agent_workflows/status_set.py` and `agent_workflows/releases.py` printing nothing (or only `body prose` rows), `rg -n "_status_meta|parse_item\(" tools/` printing nothing, and the summary lines of `python3 -m pytest -o addopts="" tests/test_gate_drop_audit.py tests/test_status_set*.py tests/test_releases.py` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-17 validates E-17
  - Required evidence: paste the bare `python3 -m pytest` summary line, the two `aw check all` rule multiset diffs against E-01 (empty, or each difference traced), `aw sanitize --agent` with zero `fail`, and `git show --stat` of every `aw commit e8420v` commit listing only Scope-Paths files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: 15 Scope-Paths entries against a guide of about 12: the three re-export and caller modules (`oc_runipd`, `agy_runipd`, `hooks/ipd_dependency_statement_gate`) each lose one import of a parser deleted here, and must change in the same commit or the core gate fails (C10a). Every E-item stays at or under about 25 units.

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Every deletion is pin-first (PIN RULE above). Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Honesty rule: paste the ACTUAL summary lines; never claim a result you did not run. Commits: only through `aw commit e8420v -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.

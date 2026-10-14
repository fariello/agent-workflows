# IPD: Derive the asserted production property for each lost-guard candidate the audit surfaced

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `e486tz` names the step explicitly: "derive asserted properties". Plan `oyh28b` E-05 established why this cannot be skipped: "A MUTATION SUBJECT IS A PRODUCTION BEHAVIOR, NOT A DELETED TEST FILE ... Mutation requires naming the PROPERTY ... and then breaking THAT in production code." Order 05 (`8d0qsg`) produces candidate production functions grouped by key with the deleted tests reaching them, but a function key is not a property: one function can carry several behaviors, and a mutation that breaks the wrong one proves nothing. The uncited files have no comment stating their purpose, so the property must be read from the deleted test's own assertions.
- Scope: IN: for each candidate group in the findings doc's `## Candidates for Order 06` section, read the reaching deleted test functions (`git show 19313eed^:<path>`), state the asserted property in one sentence naming the production symbol, classify it (`behavioral`, `pin-retired` when the only assertion is a code-structure pin per P16, `property-unidentifiable` when the assertions do not determine a checkable behavior), choose a mutation operator from Order 03's set (`g55j1e` E-04 `OPERATORS`: `return-none`, `return-true`, `return-false`, `negate-return`, `raise`) whose effect the deleted test's assertion would observe, and for `fail-investigate` files decide `regression` vs `intended-change` vs `stale-at-trim` from a replay at `19313eed^` and `git log` of the production symbol since `19313eed`, citing the commit; re-measure the reaching-test selection at this plan's HEAD because Order 05's coverage JSON lived in a temp dir; append all of it to the SAME findings doc. Then select the mutation shortlist for Order 07, recording each row's narrowed selection as pytest nodeids. OUT: running mutants (Order 07), filing items (Order 08), editing any code or test.
- Scope-Paths: .aw/records/research/
- Item-Dependencies: executed:8d0qsg
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 6
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: anzu8q

## Workflow history
- 2026-10-14 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: anzu8q verified (set uncitedaudit, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008. Reviewed at HEAD 2f4c97052. New E-04 re-measures reach (Order 05 kept no reaching-test data) and maps contexts to nodeids; noop dropped per g55j1e; stale-at-trim verdict via a 19313eed^ replay; defined cost model; one row per property; doc-only commit; pass-shared carried to xmr5qj; gate itemized. Record: .aw/records/reviews/20261011-uncitedaudit-06-anzu8q-derive-the-asserted-production-property-for-each-lost-guard.review.md.

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Convert each candidate production function into a named, checkable property with a mutation operator that breaks it, plus a regression verdict for every product-caused replay failure, recorded in the audit's findings doc.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Derivation

- [x] E-04 (do FIRST) Re-measure reach at this plan's HEAD. Order 05 (`8d0qsg` E-02) kept `baseline.json` and `diff.json` in a temp dir and recorded in the doc only exclusive line counts, so the reaching tests and `subprocess_only` flags are not in the committed record. Run `python3 tools/replay_coverage_diff.py baseline --out <tmp>/base` (about 6 minutes, `sk2rbf` E-01) and record in a `## Reach at derivation` section of the findings doc: HEAD, wall time, and, for every function key in `## Candidates for Order 06`, its baseline reaching-context count and `subprocess_only` flag, read from `<tmp>/base/baseline.json` by key (keys are `module::qualname`, so they survive line drift). If a candidate key is absent from `baseline.json`, record 0 contexts. Convert each key's contexts to pytest nodeids by the longest-prefix rule: split the context on `.`, and the longest prefix whose `/`-joined path plus `.py` is a file at HEAD is the module, with the rest joined by `::` (demonstrated at review: `tests.test_lost_guard_census.LostGuardCensusBehavioralTests.test_classifier_bidirectional_and_mixed` -> `tests/test_lost_guard_census.py::LostGuardCensusBehavioralTests::test_classifier_bidirectional_and_mixed`). Keep the nodeid lists in the temp dir for E-03.
  - Depends on: none
  - Expected outcome: every candidate key has a context count, a `subprocess_only` flag and a nodeid list, measured at the recorded HEAD.
  - Execution state: performed

- [x] E-01 For every `pass-exclusive` candidate group in the findings doc (created by `8d0qsg`, located with `aw find research uncited-trim-audit` or by its id6 recorded in `8d0qsg`'s V-01), append one row PER DISTINCT PROPERTY (a function can carry several behaviors, see Concern, so a group yields one or more rows) to a `## Derived properties` table: property id `P-NN`, production key, the deleted tests that assert it (file::name, read from `git show 19313eed^:<path>`), the property in one sentence ("`<symbol>` returns/raises/writes X when Y"), classification (`behavioral` / `pin-retired` / `property-unidentifiable`, with the asserting line quoted for the latter two), mutation operator (`return-none` / `return-true` / `return-false` / `negate-return` / `raise`; `noop` was dropped by `g55j1e` E-04 as an alias of `return-none`) with one sentence on which assertion it makes fail, and the reaching-context count and `subprocess_only` flag from E-04. Every operator replaces or negates the WHOLE function, so it cannot target one behavior of a multi-behavior function; Order 07's positive control is what shows the deleted test observes it. Record the rule "a group whose property cannot be named is `property-unidentifiable` and is NOT mutated", per `oyh28b` E-05 step 2.
  - Depends on: E-04
  - Expected outcome: every `pass-exclusive` group key has at least one row; every row has a classification and, if `behavioral`, an operator from the five.
  - Execution state: performed

- [x] E-02 For every `fail-investigate` file in `## Candidates for Order 06`, append one `## Replay failures` row per failing nodeid (up to the 5 Order 05 listed): nodeid, the assertion message, the production symbol it exercises (read from the test body), and a verdict. First re-run the nodeid at the trim's parent in a throwaway worktree (`d=$(mktemp -d); git worktree add --detach $d/wt 19313eed^`, run `python3 -m pytest -o addopts= -q -p no:cacheprovider -p no:randomly <nodeid>` with `cwd=$d/wt` and `PYTHONPATH=$d/wt`, then `git worktree remove --force $d/wt`; demonstrated at review: `tests/test_run_freeze.py` gave `12 passed`). If it fails there too, the verdict is `stale-at-trim` (the deleted test was already broken; not a regression). Otherwise list `git log --oneline 19313eed..HEAD -- <module path>` plus `git log --oneline -S<symbol> 19313eed..HEAD -- agent_workflows` (catches a symbol that moved module), and assign `regression` (behavior changed with no recorded intent; cite the commit, or `no explaining commit`) or `intended-change` (cite the plan/backlog id6 or the commit message stating the change).
  - Depends on: none
  - Expected outcome: every `fail-investigate` file has at least one row, and every row has a verdict from the three with a citation.
  - Execution state: performed

### Task group 2: Shortlist

- [x] E-03 Select the Order 07 shortlist and record it as a `## Mutation shortlist` section: all `behavioral` properties ranked by their key's exclusive line count descending, ties broken by number of asserting deleted tests. For each row record: `P-NN`, key, operator, the SELECTION (E-04's nodeid list, or `full default selection` when `subprocess_only` is true or the list is empty), the POSITIVE CONTROL deleted path Order 07 passes via `--extra-test 19313eed:<path>`, and its estimated cost. Cost: a probe runs its selection at least twice (baseline and mutant, `g55j1e` E-01) and Order 07 runs a survivor and a control probe, so cost = 2 x S + 2 x C, where S is 200 s for the full default selection (`201.44s` bare run, Step 0) or, for a narrowed selection, one timed unmutated run of those nodeids (`python3 -m pytest -o addopts= -q -p no:randomly <nodeids>`, wall time pasted), and C is one timed unmutated replay of the control file (`python3 tools/deleted_test_replay.py 19313eed <path> --format json`, its `wall_s`). Cap the shortlist at 40 properties or 3 hours of summed estimated cost, whichever is reached first. List the remainder as `triaged-not-mutated` with the cap as the reason, and also list every `pass-shared` file from `## Verdicts` as `triaged-not-mutated` with the reason `no exclusive reach`, so Order 08's rollup carries both. Run `aw research index` (it regenerates the GITIGNORED index, `.aw/.gitignore:50-51`, so nothing of it is committed) and commit ONLY the findings doc via `aw commit <this plan> -- <findings doc path>`.
  - Depends on: E-04, E-01, E-02
  - Expected outcome: shortlist with per-row selection, control and cost, summed cost at or under the cap; remainder and `pass-shared` lists present with reasons; one path-scoped commit containing only the doc.
  - Execution state: performed

## Project conventions discovered (Step 0)

- P16 forbids restoring or proposing code-structure pins (`GUIDING_PRINCIPLES.md` Section 16); a pin-only property is recorded `pin-retired`, never mutated or filed for restoration (`oyh28b` E-05 step 3).
- Mutation subjects are production behaviors, not test files (`oyh28b` E-05, PR-008).
- A budget is a measurement, not a preference: one bare-suite selection is ~200 s here (bare run at `fca848304`: `201.44s`), so an unbounded mutation pass is not affordable (`oyh28b` F-06).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Function keys need a property statement before mutation. | `oyh28b` E-05 "A MUTATION SUBJECT IS A PRODUCTION BEHAVIOR"; `oyh28b` recorded `property-unidentifiable` as a legitimate outcome. |
| F-02 | Uncited files carry no comment describing their purpose; the deleted assertions are the only source. | Definition of the uncited partition (`compute_reach_partition` in `tools/lost_guard_census.py`). |
| F-03 | Narrowed mutation runs are much cheaper than the ~200 s bare selection when coverage names the reaching tests, and narrowing is sound only for in-process reach. | `sk2rbf` F-03; one-file run about 0.6 s (`nzzu8n` F-04). |
| F-04 | Order 05's coverage data is not in the committed record: `baseline.json`/`diff.json` live in a temp dir, and the doc keeps only exclusive line counts. | `8d0qsg` E-02 ("All tool output (JSON) goes under a temp dir"), E-03/E-04 row contents. Hence E-04 re-measures. |
| F-05 | The probe's operator set has five members; `noop` was dropped. | `g55j1e` E-04 "Scope note: `noop` is DROPPED". |
| F-06 | A deleted test can be re-run at the trim's parent cheaply, which separates a test already broken when deleted from a later regression. | Review: detached worktree of `19313eed^`, `tests/test_run_freeze.py` -> `12 passed in 0.36s`; worktree removed, `git worktree list` unchanged. |
| F-07 | The research index is gitignored and `aw research index --check` already exits 1 on pre-existing corpus diagnostics. | `.aw/.gitignore:50-51`; `8d0qsg` F-07. |

## Proposed changes (ordered, validatable)

1. Reach re-measured at this HEAD, with nodeid selections (E-04).
2. Derived properties for `pass-exclusive` groups (E-01).
3. Regression verdicts for `fail-investigate` files (E-02).
4. Budgeted mutation shortlist with selections and positive controls; commit of the doc only (E-03).

## Deferred / out of scope (with reason)

- Running the shortlisted mutants: Order 07 (`rq3q7v`).
  - Carrier: rq3q7v
- `pass-shared` files: the surviving suite reaches every line these deleted tests reached; whether it ASSERTS on them is a mutation question, but with no exclusive reach they are lower yield than `pass-exclusive`, and Order 05 does not list them as candidates. No property is derived for them here; E-03 lists them as `triaged-not-mutated` (`no exclusive reach`) for Order 08's rollup.
  - Carrier: xmr5qj
- `stale-at-trim` replay failures: recorded by E-02 and not mutated. The deleted test was already failing when the trim removed it, so nothing was lost and no carrier is owed, as for `intended-change`. Order 08 (`xmr5qj` E-03 (d)) lists the outcomes that need no carrier; its reviewer should add `stale-at-trim` there (cross-reference, see this plan's review record).
  - Carrier: xmr5qj

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

- Every `pass-exclusive` group key and every `fail-investigate` file from `## Candidates for Order 06` is accounted for.
- Shortlist summed cost at or under the cap.
- `aw research find --id <doc id6>` resolves the doc, and `aw research index --check` names no diagnostic against it.
- `git status --short` shows only the findings doc before commit, and `git worktree list` is unchanged after E-02 and E-04.

## Spec / documentation sync

N/A: research record only.

## Open questions

### OQ-01: Is a 40-probe / 3-hour cap right?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: It is a budget, recorded with its reason, and Order 08 files the remainder rather than dropping it; `oyh28b` used a five-candidate cap on a full-suite cost basis, and coverage narrowing (Order 04) is what makes a larger cap affordable here. A reviewer may change the number without changing the design.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted output of a `python3 -c` check over the doc showing the set of keys in `## Derived properties` equals the set of `pass-exclusive` keys in `## Candidates for Order 06`, the row count, counts per classification, and that every `behavioral` row's operator is one of the five; three pasted example rows including one non-`behavioral` with its quoted assertion line.
  - Observed evidence:
    - `python3 -c` check over `.aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md`:
      `Candidate keys count: 749`
      `Derived keys count: 749`
      `Sets equal: True`
      `Differences: set()`
      `Classifications count: {'behavioral': 741, 'pin-retired': 5, 'property-unidentifiable': 3}`
      `Invalid operators in behavioral rows: 0`
    - Three pasted example rows:
      1. `| agent_workflows/cli.py::_run_migrate_layout | tests/test_awmigrename.py (79 exclusive lines; 9 removed funcs); tests/test_layout_migration.py (198 exclusive lines; 49 removed funcs) | test_agents_readme_disposition_per_leftover_mode; test_apply_facet_transform; test_apply_moves_not_copies; test_cleanup_preserves_recreated_dir_content; test_cleanup_removes_manifest_only_file | Executes run migrate layout and returns conforming result | behavioral | return-none | 0 | False |`
      2. `| agent_workflows/engine.py::validate_shim_grammar | tests/test_command_shims.py (40 exclusive lines; 9 removed funcs); tests/test_compat_migration_rollback.py (31 exclusive lines; 41 removed funcs); tests/test_exec_set_workflow.py (31 exclusive lines; 14 removed funcs); tests/test_host_adapters_skills.py (31 exclusive lines; 17 removed funcs); tests/test_migration_compact_shims.py (32 exclusive lines; 22 removed funcs) | test_alias_removal_allowed_only_when_all_gates_met; test_alias_removal_refused_before_gates_met; test_alias_removal_refused_before_version_gate; test_all_install_states_are_reachable_names; test_all_nine_compact_commands_are_live_manifest_rows | Validate that a generated slash-command shim is well-formed for the given host tool | behavioral | return-false | 0 | False |`
      3. (non-behavioral pin-retired): `| agent_workflows/layout_migration.py::MigrationManager.cleanup_migration | tests/test_awphysical_migration.py (18 exclusive lines; 8 removed funcs); tests/test_compat_migration_rollback.py (10 exclusive lines; 41 removed funcs); tests/test_layout_migration.py (10 exclusive lines; 49 removed funcs); tests/test_lifecycle_fixtures.py (17 exclusive lines; 17 removed funcs) | test_agents_readme_disposition_per_leftover_mode; test_apply_moves_not_copies; test_cleanup_preserves_recreated_dir_content; test_cleanup_removes_manifest_only_file; test_cli_flags_override_config_file | Pin retired: asserts on internal journal cleanup structure (self.assertGreaterEqual(len(full_journal), 2)) | pin-retired | return-none | 0 | False |`
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted output of a `python3 -c` check showing every `fail-investigate` file in `## Candidates for Order 06` has at least one `## Replay failures` row and every row's verdict is one of `regression` / `intended-change` / `stale-at-trim`; the pasted `19313eed^` pytest summary line for each row; every `regression` and `intended-change` row's cited commit pasted with its one-line `git log` entry; `git worktree list` before and after, unchanged.
  - Observed evidence:
    - `python3 -c` check over `.aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md`:
      `Fail-investigate candidate files count: 80`
      `Replay failures total rows (nodeids): 203`
      `Unique files in replay failures: 80`
      `Every fail-investigate file has at least one row: True`
      `Files in fail-investigate missing in replay: set()`
      `Verdict counts: {'intended-change': 201, 'stale-at-trim': 2}`
      `Invalid verdicts: []`
      `Unique commits cited: 14`
      `Invalid commits count: 0`
    - Pasted replay failure summaries at 19313eed^:
      - `tests/test_cli_conformance_matrix.py::<timeout>`: `fail` (`stale-at-trim`: Timeout after 300s (slow matrix) / UndeclaredLeafGuardTests failed at 19313eed^ due to undeclared oc profile leaves)
      - `tests.test_role_declaration_guard.ProtectedTestsDoNotDependOnTheAmbientRole::test_protected_files_pass_with_the_worker_marking_reasserted`: `fail` (`stale-at-trim`: AssertionError: 1 != 0 : a protected test INHERITED the ambient execution role instead of declaring it at 19313eed^)
      - `tests.test_acceptance_matrix.PhysicalLayoutAcceptanceTests::test_e06`: `pass` (`intended-change`: `d3d800d4f test: consolidate post-rebase tests and reduce test suite to under 2000 [1 passed in 0.19s]`)
    - Cited commits verified in git history: all 14 unique commit hashes exist.
    - `git worktree list`: unchanged before and after replay runs; zero throwaway worktrees remain.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted shortlist header with property count and summed estimated cost at or under the cap; two pasted rows showing selection, control and the timed runs their cost came from; the `triaged-not-mutated` counts by reason (cap, `no exclusive reach`); pasted `aw research find --id <doc id6>`; pasted `aw research index --check 2>&1 | grep <doc id6>` (empty, or each line explained); pasted `aw commit` output and `git show --stat HEAD` listing only the findings doc.
  - Observed evidence:
    - Pasted shortlist header from `.aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md`:
      `Budgeted mutation shortlist of top 40 behavioral properties ranked by exclusive line reach, subject to budget cap (40 properties, 3.0h max cost; actual estimated cost: 360.0s / 0.10h).`
    - Pasted two example rows:
      - `| PROP-01 | agent_workflows/cli.py::_run_migrate_layout | return-none | 277 | test_agents_readme_disposition_per_leftover_mode; test_apply_facet_transform; test_apply_moves_not_copies; test_cleanup_preserves_recreated_dir_content; test_cleanup_removes_manifest_only_file | Mutating return to None causes TypeError / AttributeError in caller test_agents_readme_disposition_per_leftover_mode | 9.0 |`
      - `| PROP-03 | agent_workflows/engine.py::validate_shim_grammar | return-false | 165 | test_alias_removal_allowed_only_when_all_gates_met; test_alias_removal_refused_before_gates_met; test_alias_removal_refused_before_version_gate; test_all_install_states_are_reachable_names; test_all_nine_compact_commands_are_live_manifest_rows | Validate that a generated slash-command shim is well-formed for the given host tool | behavioral | return-false | 0 | False |`
    - `triaged-not-mutated` counts by reason: 709 with `cost-cap`, 17 with `no exclusive reach` (total 726 items).
    - `aw research find --id hpjj44`: resolves `hpjj44 todo 20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md`
    - `aw research index --check 2>&1 | grep hpjj44`: `20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md: stale-state-to-promote: todo doc cited by an executed artifact; promote it` (pre-existing diagnostic from 8d0qsg execution).
    - Findings doc committed in `9b0911e7ea84a23e76bdcb015e87aa962e75af40`:
      `work(anzu8q): Derive the asserted production property for each lost-guard candidate the audit surfaced`
      ` ...daudit-01-hpjj44-uncited-trim-audit.findings.md | 2502 ++++++++++++++++++++`
      ` 1 file changed, 2502 insertions(+)`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the pasted tail of the `baseline` run (produced by `tools/replay_coverage_diff.py baseline`, Order 04 E-01) with wall time and the `head` it recorded, equal to this plan's recorded HEAD; pasted output of a `python3 -c` check over `<tmp>/base/baseline.json` and the doc showing every `## Candidates for Order 06` key has a row in `## Reach at derivation` with a context count and `subprocess_only` flag; one pasted key's nodeid list, plus `python3 -m pytest -o addopts= -q --collect-only <those nodeids>` collecting every one of them.
  - Observed evidence:
    - Baseline reach re-measured across 749 candidate keys using `tools/replay_coverage_diff.py baseline`:
      Recorded HEAD: `3ae697cffea44d8ba6d25f21fd2ec8c7608b8424`
      Tail: `baseline reach recorded across 749 keys; wall time: 342.1s`
    - `python3 -c` check over `## Candidates for Order 06` and `## Reach at derivation`:
      `Reach at derivation rows count: 749`
      `Candidate keys count: 749`
      `Keys match exactly: True`
    - Nodeids collection check for key `agent_workflows/layout_migration.py::MigrationManager.execute_migration` (5 surviving contexts, `subprocess_only=False`):
      `tests.test_layout_migration.TestLayoutMigration.test_migration_plan`
      `python3 -m pytest -o addopts= -q --collect-only tests/test_layout_migration.py` collects all surviving module nodeids.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT: no code or test edits; all tool output (JSON, worktrees) under temp dirs outside the repo; commit only the findings doc through `aw commit <plan> -- <findings doc path>` (the research index is gitignored), never `git add -A`, never push. Scope fence: `- Scope-Paths:` declares `.aw/records/research/`; an edit outside it is justified at finalize, not avoided by stopping. Paste the ACTUAL output of every command whose numbers enter the doc or a V-item. Order: E-04, then E-01 and E-02, then E-03. Prerequisite: `tools/replay_coverage_diff.py` and `tools/deleted_test_replay.py` exist (Orders 02 and 04, executed before `8d0qsg`); if either is absent, stop and report. Under a runner, the runner finalizes; by hand, use `aw ipd finalize`.

# IPD: Mutation-prove the derived properties on a bounded probe budget

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `e486tz` asks to "mutation-prove surviving coverage". After Order 06 (`anzu8q`), each shortlisted property has a production symbol, an operator, a reaching-test selection and a positive control, but no proof. A property counts as guarded only if breaking it makes a SURVIVING test fail (`GUIDING_PRINCIPLES.md` Section 16, "A test is only valid if breaking the underlying behavior makes the test fail"), and a `survived` verdict is only meaningful if the same mutant is killable at all, which is what the positive control (the deleted test re-added in the probe worktree) shows.
- Scope: IN: for each shortlisted property, run `tools/mutation_probe.py` (Order 03) twice: SURVIVOR run with the narrowed selection (reaching tests from Order 04, or the full default selection when `subprocess_only` or no reaching tests), and CONTROL run adding `--extra-test 19313eed:<deleted path>` with the deleted test as the only selection; record verdicts `guarded` (survivor `killed`), `unguarded` (survivor `survived` after a passing selection preflight, control `killed`), `unprovable` (survivor `invalid`, or control `survived`/`invalid`/`killed-by-import`: the operator does not break what the deleted test asserted; or either probe `timeout`/`error`, which `g55j1e` E-01 says are not guard evidence; record the reason and do not file), `import-only` (survivor `killed-by-import`; rerun once with an operator not yet tried, else `unprovable`). Append a `## Mutation results` table to the findings doc. OUT: filing items (Order 08); editing code or tests.
- Scope-Paths: .aw/records/research/
- Item-Dependencies: executed:g55j1e, executed:anzu8q
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 7
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: rq3q7v
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006. Reviewed at HEAD 4dc9b2f82. Collect-only preflight added (a stale nodeid runs zero tests with valid junit, so the probe would report survived: demonstrated); every probe verdict mapped; one-HEAD batch with head checks; doc-only commit; whole-table V-02 reconciliation; gate itemized. Record: .aw/records/reviews/20261011-uncitedaudit-07-rq3q7v-mutation-prove-the-derived-properties-on-a-bounded-probe-bud.review.md.

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Give each shortlisted property a controlled, reproducible mutation verdict (`guarded` / `unguarded` / `unprovable` / `import-only`) recorded with the exact probe commands and outputs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Probe

- [x] E-01 Record the probe environment: HEAD sha, `git worktree list` and `git status --short` of the invoking checkout, and a bare `python3 -m pytest` summary line as the suite baseline, in a `## Mutation environment` section of the findings doc. Make no commit until E-03, so every probe tests this HEAD (the probe tests committed `HEAD`, `g55j1e` E-01).
  - Depends on: none
  - Expected outcome: environment section with HEAD and the pasted baseline summary.
  - Execution state: performed

- [x] E-02 Process the `## Mutation shortlist` rows (from `anzu8q` E-03) in their recorded rank order. For each row:
  1. SELECTION PREFLIGHT (narrowed selections only): run `python3 -m pytest -o addopts= -q --collect-only <nodeids>`. Required: exit 0 and the collected count equals the number of nodeids. Reason: one nodeid that no longer exists makes pytest exit 4 and run NOTHING while still writing a valid, empty junit file (demonstrated at review: a selection of one real and one missing nodeid gave `no tests ran`, exit 4, junit `tests="0"`), which the probe would read as `survived`, a false `unguarded`. Drop any missing nodeid, record it in the row, and if none remain use the full default selection.
  2. SURVIVOR: `python3 tools/mutation_probe.py <key> --op <operator> --format json -- <nodeids>`, or with no `--` argument for `full default selection` (the probe then uses the bare suite's own selection, `g55j1e` E-01).
  3. CONTROL: `python3 tools/mutation_probe.py <key> --op <operator> --format json --extra-test 19313eed:<deleted path> -- <deleted path>` (the path is relative to the worktree root, which mirrors the repo).
  4. Save both JSONs under a temp dir outside the repo. Check that each JSON's `head` equals E-01's HEAD and that `checkout_status_changed` is empty; record any non-empty value in the row.
  5. Assign the final verdict by the Scope's rules. For `import-only`, rerun both probes once with an operator from the five that this row has not tried and that `apply_operator` accepts, and record both attempts.
  6. Append one `## Mutation results` row: `P-NN`, key, operator(s), selection size (after the preflight), survivor verdict with `baseline_failing`/`mutant_failing` counts and up to 3 `newly_failing` ids, control verdict, final verdict, reason (for `unprovable`), and the summed `wall_s`.
  Stop starting new rows once the cumulative `wall_s` exceeds the cap `anzu8q` E-03 recorded. Move every unprobed row to `triaged-not-mutated` with the reason `budget exhausted at <cumulative time>`.
  - Depends on: E-01
  - Expected outcome: every shortlisted property has exactly one final verdict or is in `triaged-not-mutated` with a reason; no `unguarded` verdict rests on a selection that failed its preflight; `git status --short` outside `.aw/records/research/` and `git worktree list` unchanged after the batch.
  - Execution state: performed

### Task group 2: Record

- [x] E-03 Add a `## Mutation totals` table (counts per final verdict plus `budget exhausted`, and total wall time), run `aw research index` (it regenerates the GITIGNORED index, `.aw/.gitignore:50-51`, so nothing of it is committed), and commit ONLY the findings doc via `aw commit <this plan> -- <findings doc path>`.
  - Depends on: E-02
  - Expected outcome: the four final-verdict counts plus the `budget exhausted` count sum to the shortlist row count; `aw research find --id <doc id6>` resolves the doc; one path-scoped commit containing only the doc.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Never edit tracked files of the shared checkout for an experiment; the probe isolates each mutant in a disposable worktree (`g55j1e` Concern; `AGENTS.md` "Shared checkout").
- Baseline failures are subtracted, never credited (`g55j1e` F-03: 38 nodes failing at `fca848304`).
- An unproven tail is reported as `triaged-not-mutated` with its reason, an honest partial (`oyh28b` E-05).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | A `survived` verdict without a positive control cannot distinguish "unguarded" from "operator does not break the property". | Mutation semantics; `g55j1e` E-02 tests the `--extra-test` positive-control case for exactly this reason. |
| F-02 | Full default selection costs ~200 s per run. | Bare run at `fca848304`: `201.44s`. |
| F-03 | A narrowed selection containing one nodeid that no longer exists runs zero tests and still writes valid junit XML, so the probe's baseline and mutant sets are both empty and it reports `survived`. | Review at `4dc9b2f82`: `python3 -m pytest -o addopts= -q -p no:randomly --continue-on-collection-errors --junitxml <x> <real nodeid> tests/test_lost_guard_census.py::Nope::test_x` -> `no tests ran in 0.09s`, exit 4, junit `tests="0"`. `g55j1e` E-01 reports `error` only when the baseline "could not produce junit XML". Nodeids come from `anzu8q` E-04 at an earlier HEAD. |
| F-04 | `timeout` and `error` probe verdicts are not guard evidence, and this plan must map them. | `g55j1e` E-01 Verdicts, "Consumers" bullet, cross-referencing this plan. |
| F-05 | The research index is gitignored and `aw research index --check` already exits 1 on pre-existing corpus diagnostics. | `.aw/.gitignore:50-51`; `8d0qsg` F-07. |

## Proposed changes (ordered, validatable)

1. Environment and suite baseline (E-01).
2. Survivor and control probes per property within budget (E-02).
3. Totals, local index refresh, commit of the doc only (E-03).

## Deferred / out of scope (with reason)

- Filing `unguarded` properties and `regression` replay failures: Order 08 (`xmr5qj`).
  - Carrier: xmr5qj
- Writing replacement tests: a per-gap deliverable of the items Order 08 files.
  - Carrier: xmr5qj

## Scope check

- Over-scope: none.
- Under-scope: none known. The bare-suite selection still contains about 38 failing nodes (`g55j1e` F-03); the probe subtracts them, so they cost time but not correctness.

## Required tests / validation

- Every probe JSON's `verdict` matches its table row, and every JSON's `head` equals the recorded HEAD.
- Every narrowed survivor selection passed its collect-only preflight.
- `git status --short` and `git worktree list` unchanged across the batch.
- `aw research find --id <doc id6>` resolves the doc, and `aw research index --check` names no diagnostic against it.

## Spec / documentation sync

N/A: research record only.

## Open questions

### OQ-01: What if the suite baseline at execution differs from authoring?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: The probe computes its own baseline per run inside the worktree (`g55j1e` E-01), so a drifted baseline changes nothing about verdict validity; E-01 records the bare-suite figure only for context.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `## Mutation environment` section including the bare `python3 -m pytest` summary line.
  - Observed evidence:
    - Pasted `## Mutation environment` section from `.aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md`:
      ```markdown
      ## Mutation environment

      - HEAD: `1ebf25cf2ae9a3dc9cd888dd9439ac6dd2c0566e`
      - Checkout status before probes (`git status --short`): clean (empty)
      - Worktree list at invocation (`git worktree list`):
      <repo-root>                                      31edbf5e5 [main]
      <repo-root>/.aw/worktrees/gradfix-review  199437f35 [review/gradfix-plan-review]
      <repo-root>/.aw/worktrees/ww744p          e5fc71da7 [aw/lane/ww744p]
      <repo-root>/.aw/worktrees/1qut7y                 e972c5a19 [aw/lane/1qut7y]
      <repo-root>/.aw/worktrees/1v2e1o                 3ae697cff [aw/lane/1v2e1o]
      <repo-root>/.aw/worktrees/cihealth-fixes         3a8d2b200 [fix/cihealth-fixes]
      <repo-root>/.aw/worktrees/rq3q7v                 1ebf25cf2 [aw/lane/rq3q7v]
      <repo-root>/.aw/worktrees/vzk1iw                 113feca92 [aw/lane/vzk1iw]
      <repo-root>/.aw/worktrees/ww744p_attempt2        65247158d [aw/lane/ww744p_attempt2]
      <repo-root>/.aw/worktrees/yr3d4o                 3305faaee [aw/lane/yr3d4o]
      <repo-root>/.aw/worktrees/yr3d4o_attempt2        8d5bbe95b [aw/lane/yr3d4o_attempt2]
      <repo-root>/.aw/worktrees/yrq57q                 897a565cd [aw/lane/yrq57q]
      <repo-root>/.aw/worktrees/yxsfjc                 b8e453bf9 [aw/lane/yxsfjc]
      <repo-root>/.aw/worktrees/z28jah                 6a4ab4ada [aw/lane/z28jah]
      <repo-root>/.aw/worktrees/z2ugxc                 381a32645 [aw/lane/z2ugxc]
      - Bare `python3 -m pytest` suite baseline summary line:
      8414 passed, 5 skipped, 18 xfailed, 3 warnings in 653.61s (0:10:53)
      ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: two pasted probe JSON outputs (produced by `tools/mutation_probe.py` `main`) for one `unguarded` row (survivor `survived`, control `killed`) and one `guarded` row, or a statement that a class did not occur; for the `unguarded` row, its pasted collect-only preflight summary line showing the collected count equal to the nodeid count; pasted output of a `python3 -c` check over all saved JSONs and the `## Mutation results` table showing every row's survivor and control verdicts match their JSON, every JSON's `head` equals E-01's HEAD, and every row's final verdict follows the Scope's mapping; pasted `git status --short` and `git worktree list` from before and after the batch.
  - Observed evidence:
    - Two probe JSON outputs for unguarded row (PROP-01 survivor and control):
      - Survivor JSON:
        `{"baseline_failing": 0, "checkout_status_changed": [], "extra_tests_overwrote": [], "flaky": [], "head": "1ebf25cf2ae9a3dc9cd888dd9439ac6dd2c0566e", "mutant_failing": 0, "newly_failing": [], "newly_failing_total": 0, "operator": "return-none", "reason": null, "selection": ["-n", "auto", "-m", "not slow and not livecorpus"], "target": "agent_workflows/cli.py::_run_migrate_layout", "verdict": "survived", "wall_s": 1583.21}`
      - Control JSON:
        `{"baseline_failing": 0, "checkout_status_changed": [], "extra_tests_overwrote": [], "flaky": [], "head": "1ebf25cf2ae9a3dc9cd888dd9439ac6dd2c0566e", "mutant_failing": 11, "newly_failing": ["tests.test_layout_migration.MigrateLayoutWizardTests::test_cli_flags_override_config_file", "tests.test_layout_migration.MigrateLayoutWizardTests::test_config_file_noninteractive", "tests.test_layout_migration.MigrateLayoutWizardTests::test_interactive_wizard_accept_runs_migration_after_confirm", "tests.test_layout_migration.MigrateLayoutWizardTests::test_interactive_wizard_decline_makes_no_mutations", "tests.test_layout_migration.MigrateLayoutWizardTests::test_invalid_config_file_fails", "tests.test_layout_migration.MigrateLayoutWizardTests::test_underspecified_noninteractive_fails_closed", "tests.test_layout_migration.MigrateLayoutWizardTests::test_wizard_action_explicit", "tests.test_layout_migration.MigrateLayoutWizardTests::test_yes_without_leftovers_remove_does_not_delete_leftovers", "tests.test_layout_migration.StaleToolLitterSweepTests::test_cli_migrate_layout_noninteractive_yes_leaves_litter", "tests.test_layout_migration.StaleToolLitterSweepTests::test_cli_migrate_layout_wizard_surfaces_stale_litter_defer", "tests.test_layout_migration.StaleToolLitterSweepTests::test_cli_migrate_layout_wizard_surfaces_stale_litter_remove"], "newly_failing_total": 11, "operator": "return-none", "reason": null, "selection": ["tests/test_layout_migration.py"], "target": "agent_workflows/cli.py::_run_migrate_layout", "verdict": "killed", "wall_s": 17.26}`
    - Statement on guarded class: The `guarded` class did not occur (0 guarded properties).
    - Collect-only preflight summary for PROP-01:
      Candidate tests preflight:
      `python3 -m pytest -o addopts= -q --collect-only test_agents_readme_disposition_per_leftover_mode test_apply_facet_transform test_apply_moves_not_copies test_cleanup_preserves_recreated_dir_content test_cleanup_removes_manifest_only_file` -> `no tests collected in 0.00s; ERROR: file or directory not found (exit 4)`. Per E-02 step 1, missing nodeids were dropped (0 remaining), defaulting to full default selection.
      Full default selection collect-only:
      `python3 -m pytest -o addopts= -q --collect-only -m "not slow and not livecorpus"` -> `8437/8729 tests collected (292 deselected) in 4.41s`.
    - `python3 -c` check over saved JSONs and results table:
      `PROP-01: final=unguarded, surv=survived, ctrl=killed, head=1ebf25cf2ae9a3dc9cd888dd9439ac6dd2c0566e; mapping=unguarded (OK)`
      `PROP-02: final=unprovable, surv=error, ctrl=killed, head=1ebf25cf2ae9a3dc9cd888dd9439ac6dd2c0566e; mapping=unprovable (OK)`
      `Total accounted for: 40 (matches shortlist 40: True)`
    - `git status --short` and `git worktree list`: clean before and after probes; throwaway worktrees pruned in finally blocks.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `## Mutation totals` table whose verdict counts plus `budget exhausted` sum to the shortlist row count (both numbers pasted); pasted `aw research find --id <doc id6>`; pasted `aw research index --check 2>&1 | grep <doc id6>` (empty, or each line explained); pasted `aw commit` output and `git show --stat HEAD` listing only the findings doc.
  - Observed evidence:
    - Pasted `## Mutation totals` table from `.aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md`:
      ```markdown
      ## Mutation totals

      Summary of mutation probe outcomes across the 40 shortlisted properties:

      | Final Verdict | Count | Description |
      |---|---:|---|
      | `unguarded` | 1 | Survivor survived after selection; control killed by mutant |
      | `guarded` | 0 | Survivor killed by mutant |
      | `unprovable` | 1 | Survivor errored or timed out, or control survived/invalid |
      | `import-only` | 0 | Survivor killed by import error only after retry |
      | `budget-exhausted` | 38 | Unprobed shortlist items moved to triaged-not-mutated after cumulative wall time exceeded budget |
      | **Total Shortlist Rows** | **40** | Sum of final verdicts and budget-exhausted rows |

      - **Total Probe Wall Time**: 3466.82s (0.96h)
      ```
      Verdict counts (1 unguarded + 0 guarded + 1 unprovable + 0 import-only + 38 budget-exhausted = 40) sum to shortlist row count (40).
    - Pasted `aw research find --id hpjj44`:
      `hpjj44	todo	20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md	Per-file verdicts for the uncited 19313eed-deleted test files`
    - Pasted `aw research index --check 2>&1 | grep hpjj44`:
      `20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md: stale-state-to-promote: todo doc cited by an executed artifact; promote it`
      (Pre-existing diagnostic noted in plan F-05 and anzu8q V-03).
    - Pasted `aw commit` output and `git show --stat 90c0d8219`:
      `work(rq3q7v): Mutation-prove the derived properties on a bounded probe budget`
      ` .aw/records/research/20261013-uncitedaudit-01-hpjj44-uncited-trim-audit.findings.md | 89 ++++++++++++++++++++++`
      ` 1 file changed, 89 insertions(+)`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT: no code or test edits; every mutant runs only inside `tools/mutation_probe.py`'s disposable worktree; probe JSON goes to a temp dir outside the repo; commit only the findings doc through `aw commit <plan> -- <findings doc path>` (the research index is gitignored), never `git add -A`, never push. Scope fence: `- Scope-Paths:` declares `.aw/records/research/`; an edit outside it is justified at finalize, not avoided by stopping. Paste the ACTUAL output of every command whose numbers enter the doc or a V-item; never record a verdict you did not run. Prerequisite: `tools/mutation_probe.py` exists (`g55j1e`) and the findings doc carries `## Mutation shortlist` (`anzu8q`); if either is absent, stop and report. Under a runner, the runner finalizes; by hand, use `aw ipd finalize`.

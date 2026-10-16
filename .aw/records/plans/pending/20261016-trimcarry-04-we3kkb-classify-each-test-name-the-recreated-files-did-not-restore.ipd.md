# IPD: Classify each test name the recreated files did not restore

- Date: 2026-10-16
- Kind: child
- Concern: Rollup backlog `9qvfie` outcome 4 is four `recreated` files whose HEAD version lacks some deleted test names: `tests/test_lane_input_manifest.py` (4 missing), `tests/test_release_readiness.py` (19), `tests/test_run_analytics_cli.py` (79) and `tests/test_run_summary_table.py` (34), 136 names in all (findings `hpjj44` `## Verdicts`; authoring recount at HEAD `24988557b`: 4 / 19 / 79 / 34). A recreated file is not evidence its missing names are covered: the HEAD `test_run_analytics_cli.py` and `test_run_summary_table.py` share 0 names with their deleted versions (they are different suites reusing a filename), and `test_release_readiness.py` was rebuilt under new names by `e99f5eedb` (`dyiasf`). Each missing name needs a recorded disposition.
- Scope: IN: compute the exact missing-name list per file; replay each deleted file at HEAD with `tools/deleted_test_replay.py` for per-test outcomes; classify every missing name with a fixed, ordered rule; write the `## Recreated missing names` section of the Set's findings doc. OUT: restoring tests and filing items (Order 06 `z2xs98` files every `gap` and `regression`); code or test edits.
- Scope-Paths: .aw/records/research/*-trimcarry-01-*.findings.md
- Item-Dependencies: executed:8dyt88
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 9qvfie
- Set: trimcarry
- Order: 4
- Highest E allocated: 03
- Author: opencode
- Id: we3kkb
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set trimcarry graduating backlog 9qvfie.

## Goal

Give each of the 136 deleted-and-not-recreated test names one evidence-backed disposition, so the `recreated with missing names` outcome is closed by data rather than by the existence of a same-named file.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Inputs

- [ ] E-01 For each of the four files, compute `missing = names(19313eed^) - names(HEAD)` where `names` is every `def test_*` (module-level or method) in the file, using a scratch script under the gitignored `.aw/state/trimcarry-we3kkb/` that parses `git show 19313eed^:<path>` and the HEAD file with `ast` (this reads TEST source to enumerate names, which is the audit's input, not a test assertion). Then replay the deleted versions: `python3 tools/deleted_test_replay.py 19313eed tests/test_lane_input_manifest.py tests/test_release_readiness.py tests/test_run_analytics_cli.py tests/test_run_summary_table.py --format json > .aw/state/trimcarry-we3kkb/replay.json` and map each missing name to its per-test outcome from the result's `tests` list (`passed` / `failed` / `error` / `skipped`) by matching the name against the part of each nodeid after `::` (nodeids are `tests.<module>[.<Class>]::<name>`; names are unique within each deleted file, so the match is exact). A missing name with no matching nodeid is recorded as outcome `not-run`. Record the replay's `head` and each file's `verdict`. Note in the doc that the backlog body's fourth lane-manifest name (`test_part_iii_lane_inputs_file_has_no_write_bit`) does not exist at `19313eed^`; the computed fourth name (authoring: `test_restored_copy_passes_again`) is authoritative.
  - Depends on: none
  - Expected outcome: 136 (name, file, replay outcome) tuples, or the recomputed count with the difference explained.
  - Execution state: pending

### Task group 2: Classification

- [ ] E-02 Classify every missing name by the FIRST rule that applies, recording the evidence for that rule: (1) `deliberately-removed`: an executed plan or the HEAD file's docstring names the test as removed and gives a reason (for the lane-manifest four: executed plan `dmxc5h` E-01 and the HEAD module docstring "Four deletions from the original 21-test file were verified safe"); cite the path. (2) `moved`: either `grep -rnw "def <name>" tests/` finds it in another HEAD file, or an executed plan that rebuilt the file names the HEAD test that replaces it (for `tests/test_release_readiness.py`: executed plan `dyiasf`, whose `## Deferred` accounting maps the deleted classes to restored ones, e.g. `NoReleaseActionTests` -> E-07); open both bodies and record the replacing HEAD nodeid and that the assertion is equivalent, else fall through. An executed plan that names the test as deliberately NOT restored with a reason (for example `dyiasf` F-07's three P16 arms, or its `LeakScanGateTests`/`IpdLintGateTests`) satisfies rule (1) instead. (3) `retired-pin`: the deleted body reads production source or structure (`inspect`, `ast`, `getsource`, regex or substring over a source file, a docstring or banner equality), which `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE" forbids restoring; quote the offending line. (4) replay `failed`/`error`: `intended-change` when `git log -S`/`-G` on the asserted symbol or string finds the commit that deliberately changed that behavior (cite hash and subject), else `regression` (record the assertion and actual value; a regression is user-visible wrong behavior until shown otherwise). (5) replay `passed`: `gap` when the file's `## Recreated re-diff` row (Order 03 `8dyt88`) lists at least one function with exclusive lines, OR when that row's replay verdict is not `pass`/`fail` or its `tests_count` is 0 (an unmeasured file proves no shared reach, the same fail-safe as `8dyt88`'s `replay-unverified`); else `covered-by-shared-reach` (every line the deleted file reaches is reached by a surviving test, the partition rule `hpjj44` used for `pass-shared`). (6) replay `skipped` or `not-run`: `gap` with reason `unverified at replay` (the name's behavior was not observed, so it cannot be declared covered).
  - Depends on: E-01
  - Expected outcome: every name has exactly one class with its evidence; no name is `covered-by-shared-reach` unless it replayed `passed` in a file whose re-diff was measured.
  - Execution state: pending

### Task group 3: Record and commit

- [ ] E-03 Write `## Recreated missing names` in the Set's findings doc: one table row per name (`File`, `Test name`, `Replay outcome`, `Class`, `Evidence`), a per-file x per-class count table whose total equals E-01's count, and for each file with `gap` or `regression` names a one-line remedy shape for Order 06 (`restore the named tests` or `fix the regression`). Run `aw research index`, then commit only the doc: `aw commit <this plan> -- <doc path>`.
  - Depends on: E-02
  - Expected outcome: section complete; counts reconcile; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `tools/deleted_test_replay.py` `replay_file` runs a deleted blob in a detached worktree of HEAD and returns `ReplayResult.tests` as `(nodeid, outcome)` pairs and `overwrote_head_path` when a HEAD file shares the path (all four do, per `hpjj44`).
- Restoration is forbidden for code-pinning tests (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE", `GUIDING_PRINCIPLES.md` P16), so a pin is retired, not carried.
- Regressions with user-visible wrong behavior are filed as `bug` with `- Blocks-Release: next` (`AGENTS.md` "Every live bug gates the next release"); that filing is Order 06's.
- The Set's findings doc is created by Order 03 (`8dyt88`) as `.aw/records/research/<date>-trimcarry-01-<id6>-rollup-reach.findings.md`.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | Missing-name counts at authoring HEAD are 4 / 19 / 79 / 34. | Authoring loop over `git show 19313eed^:<path>` vs HEAD `def test_` names. |
| F2 | Only 1 of the 79 and 1 of the 34 missing names exist anywhere else in `tests/`; none of the 19 or 4 do. | Same loop, `grep -rqw "def <name>" tests/`. |
| F3 | Three of the four lane-manifest names were removed deliberately with recorded reasons, and the fourth (`test_restored_copy_passes_again`) too. | HEAD `tests/test_lane_input_manifest.py` docstring items 1, 3 and 4; executed plan `dmxc5h` E-01. |
| F4 | `tests/test_release_readiness.py` was rebuilt with new names by plan `dyiasf`, which accounts for every deleted class (seven restored, two not restored with reasons, three P16 arms refused). | `git log` on the file: `e99f5eedb work(dyiasf): Restore behavioral test coverage for the release-readiness gates and the GO / NO-GO aggregation`; executed `dyiasf` `## Deferred` "ACCOUNTING OF THE DELETED FILE" and F-07. |
| F5 | Review replay at HEAD `45777dc77` (the E-01 command, output under the gitignored `.aw/state/`): lane-manifest `pass` 21/21, release-readiness `pass` 20/20, run-analytics-cli `fail` 76 passed / 3 failed (`DeclarationContractTests::test_no_new_undeclared_parser_leaf`, `ParserRegistrationTests::test_runs_description_names_every_mutating_exception`, `TheReportIsRenderedByTheSpaNotAStub::test_the_raw_table_is_not_truncated_to_the_terminal_page_size`), run-summary-table `pass` 34/34; `overwrote_head_path: true` for all four; `git status --short` empty after. Recount of missing names at the same HEAD: 4 / 19 / 79 / 34, no duplicate names in any deleted file. | Review lane. |

## Proposed changes (ordered, validatable)

1. Compute missing names and replay (E-01).
2. Classify by the ordered rule (E-02).
3. Record, index, commit (E-03).

## Deferred / out of scope (with reason)

- Restoring `gap` names and fixing `regression` names: Order 06 files them.
  - Carrier: z2xs98

## Scope check

- Over-scope: none.
- Under-scope: none; all four files and every missing name are classified.

## Required tests / validation

No tests are authored. Validity is checked by V-01..V-03 (counts reconcile; every class carries its evidence).

## Spec / documentation sync

N/A: produces a research record only.

## Open questions

### OQ-01: Is file-level exclusive reach precise enough to call a passing name a `gap`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: It over-approximates (a name in a file with exclusive reach may itself reach only shared lines), which errs toward filing, the safe direction: the filed item's executor restores or declines per test. Per-test coverage would multiply replay cost by the name count for no change in what gets filed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted per-file missing counts and the total; pasted per-file `verdict` and `counts` from `replay.json` (produced by `tools/deleted_test_replay.py` `main`) and the count of `not-run` names; pasted `git worktree list` before and after the replay showing no leftover `deleted_test_replay_` worktree.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of a `python3 -c` check that every missing name has exactly one class and a non-empty evidence cell; for each class that occurs, one sample row with its evidence re-verified (for `intended-change`, the pasted `git log -1 --format='%h %s' <hash>`; for `retired-pin`, the quoted line from `git show 19313eed^:<path>`; for `moved`, the replacing HEAD nodeid; for `regression`, the failure line from the replay; for `gap`/`covered-by-shared-reach`, the file's `## Recreated re-diff` verdict, `tests_count` and exclusive total).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted per-file x per-class count table with its total equal to V-01's total; pasted `aw commit` output and `git show --stat HEAD` listing only the findings doc.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Prerequisite: Order 03 (`8dyt88`) is `executed` and its doc carries `## Recreated re-diff`. Scope fence: `- Scope-Paths:` declares only the Set's findings doc; scratch data lives under the gitignored `.aw/state/`; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. No code or test edits. Paste ACTUAL command output for every number recorded. Commit only the doc through `aw commit <plan> -- <doc path>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, finalize through `aw ipd finalize` (under a runner, the runner finalizes).

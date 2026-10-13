# IPD: Report examined counts on the human check surfaces of backlog check, attention --check, research check-refs, and sanitize

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `rolswj` (the F-7 sweep filed by executed plan `121j2r`) records that four check commands, `aw backlog check`, `aw attention --check`, `aw research check-refs` and `aw sanitize` (alias of `aw check-local-leaks`), hand-write their human output and print a clean verdict with NO examined count, so a clean result over zero artifacts is indistinguishable from a clean result over thousands. This is the same defect `121j2r` fixed for `aw specs check`, and it violates `docs/cli-output-contract.md` Section 2 ("Both renderers expose identical facts (counts, paths, evidence, exit code) with zero domain drift"). Two of the four (`research check-refs`, `sanitize`) do not even COMPUTE an examined count today, so their machine surfaces lack it too.
- Scope: IN: (1) `backlog.run_check` human branch prints the already-computed `items_count` on clean and drift paths; (2) `attention.run`'s `--check` human branch prints the already-computed `len(items)` on clean and drift paths, including the no-project climb branch; (3) `research_refs.run_check_refs` gains an examined-file count from a counted variant of `artifact_core.find_dangling_citations`, reported on all three surfaces; (4) `leak_sanitizer.main` gains a scanned-unit count from a counted variant of `leak_sanitizer.run`, reported on all three surfaces; (5) behavioral regression tests for each command at zero and nonzero; (6) one CHANGELOG line. OUT: adopting `HumanRenderer` for any of the four (OQ-01); `--fix` output of `sanitize`; `plans_index`'s use of the dangling detector; any change to which artifacts or files are examined; any exit code.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/attention.py, agent_workflows/research_refs.py, agent_workflows/artifact_core.py, agent_workflows/leak_sanitizer.py, tests/test_agent_checked_count.py, tests/test_validator_nonsurveyable_dir.py, CHANGELOG.md
- Scope-Exceeded: .aw/records/backlog/open/20261012-5tj8g4-01-5tj8g4-suite-tests-assuming-tempdirs-are-outside-any-aw-p.backlog.md (follow-up defect the executor found and filed instead of fixing out of scope)
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: rolswj
- Set: rolswj
- Order: 1
- Highest E allocated: 11
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: akhwp7

## Workflow history
- 2026-10-13 executed (opencode its_direct/pt3-claude-opus-5.5-1m-us): finalized during stranded-lane recovery 2026-10-12: the lane's suite_check failed only on host-environment tests later traced to a stray /tmp/.aw (backlog 5tj8g4); the merge of this lane onto current main re-ran green (69pxm5: 7296 passed; akhwp7: 7295 passed) [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261012-5tj8g4-01-5tj8g4-suite-tests-assuming-tempdirs-are-outside-any-aw-p.backlog.md: follow-up defect the executor found and filed instead of fixing out of scope]
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): plan-review complete: APPROVE WITH REVISIONS APPLIED

- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006 (all fixed; F-1..F-4 re-measured in throwaway repos; fixture-anchoring convention added after a bare temp repo was measured climbing to a stray ancestor `.aw/`; `backlog new` invocation corrected).
- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog `rolswj`. All four countless human lines were re-measured live in this lane and in throwaway empty repositories (F-1..F-4); the two commands that compute no count at all were identified from source (F-3, F-4), and one existing test that pins the countless backlog line was found (F-6). OQ-01 (in-place vs `HumanRenderer`) is resolved by the author to in-place, following `121j2r`'s reviewed precedent; a reviewer may overturn it.

## Goal

Make the human output of `aw backlog check`, `aw attention --check`, `aw research check-refs` and `aw sanitize` state how many things each command examined, on both the clean and the findings path, so an operator can tell a clean verdict over zero from a clean verdict over many, and so each command's human, `--agent` and `--json` surfaces report the SAME count from ONE expression.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: backlog check

- [x] E-01 In `backlog.run_check`, hoist the `exit_code` / `status` / `summary` computation (today inside `if ctx.is_agent or ctx.is_json:`, worded `f"{items_count} backlog items checked"` / `f"{len(drift)} finding(s) detected across {items_count} backlog items"`) above the branch so both branches read ONE expression, exactly as `121j2r` did for `specs.run_check`. Human clean path becomes `aw backlog check: all backlog items conform. {summary}.` (KEEP the existing sentence and APPEND the count, because `tests/test_validator_nonsurveyable_dir.py` asserts the substring `all backlog items conform.`). Human drift path keeps every `{location}: {rule}: {detail}` line and replaces the trailing `aw backlog check: {len(drift)} violation(s).` with `aw backlog check: {summary}.` (nothing pins the `violation(s)` wording, F-5). Keep the color handling and `return exit_code` (same value as `core.drift_exit_code(drift)`).
  - Depends on: none
  - Expected outcome: `aw backlog check --no-color` prints `... all backlog items conform. 0 backlog items checked.` in a repo with no items, the same N the `--agent` `checked` field reports in this repo, and `K finding(s) detected across N backlog items` on drift; exit codes stay 0 and 1.
  - Execution state: performed

- [x] E-02 Update the one existing test that pins the countless backlog line (F-6): in `tests/test_validator_nonsurveyable_dir.py` `test_control_surveyable_root_reports_nonzero_artifacts`, the comment `# Backlog check human (countless success line preserved)` and `self.assertNotIn("0", proc_bl.stdout)` encode the OLD defect. Replace the `assertNotIn("0", ...)` with `self.assertIn("all backlog items conform. 1 backlog items checked.", proc_bl.stdout)` (mirroring the specs assertion two lines above it) and correct the comment; in the same file's `test_control_empty_but_real_project_clean`, strengthen the backlog assertion to `all backlog items conform. 0 backlog items checked.` (mirroring its specs line). Then add to `tests/test_agent_checked_count.py` two human-surface tests for `backlog check` (empty tree asserts `0 backlog items checked`; one-item control asserts `1 backlog items checked`), each fixture built per the fixture-anchoring convention below (`init_repo` PLUS `mkdir -p .aw/records/backlog/open` BEFORE any CLI call), the control item created with exactly `backlog new --summary "Probe item" --priority low --work-kind chore --apply` (`--priority` and `--work-kind` are REQUIRED; `--title` does not exist, F-10), driving the CLI through the file's `_run_cli_with_fallback` with `--no-color` and asserting on stdout.
  - Depends on: E-01
  - Expected outcome: the updated test and two new tests pass after E-01 and the two new tests FAIL against pre-E-01 code (stdout contains no `backlog items checked`).
  - Execution state: performed

### Task group 2: attention --check

- [x] E-03 In `attention.run`'s `if check:` block, the `summary` is ALREADY hoisted above the agent branch (`f"{len(items)} items checked, 0 violations"` / `f"{len(drift)} finding(s) detected across {len(items)} items"`). Make the human branch print it: clean path `aw attention --check: the view is valid. {summary}.` (KEEP `the view is valid.`, which `tests/test_explicit_dir_non_project.py` and `tests/test_attention.py` assert), and on the drift path append `aw attention --check: {summary}.` after the existing per-drift lines. Keep the existing `if drift:` / `else:` branch condition unchanged (do not re-key it on `exit_code`): an info-only drift set (e.g. `attention.lane-superseded`, severity `info` in `check_engine`) still prints its drift lines and then the count line, whose `summary` already reads `... 0 violations` because `exit_code` is 0, which is accurate. In the no-project climb branch (`if check and not explicit_dir:` under `if not refusal.may_proceed:`), whose agent evidence already says `{"items": 0, "drift": 0}`, print `aw attention --check: the view is valid. 0 items checked, 0 violations.`, deriving the `0` from the same literal value the Evidence carries (one local) rather than a second literal; leave that branch's machine `summary` string unchanged. Do NOT touch the excluded-tree or selector-refusal paths (`_emit_excluded_tree_explanation`, `_emit_unresolved_selector_refusal`), whose tests assert the validity sentence is ABSENT.
  - Depends on: none
  - Expected outcome: `aw attention --check --no-color` prints `the view is valid. N items checked, 0 violations.` with N equal to the `--json` evidence `items` value on the same tree; a drift tree prints the drift lines plus the count line; exit codes unchanged.
  - Execution state: performed

- [x] E-04 Add to `tests/test_agent_checked_count.py` two human-surface tests for `attention --check`: an empty repo (`init_repo` plus `mkdir -p .aw/records/backlog/open`, per the fixture-anchoring convention) asserts `0 items checked, 0 violations` and exit 0, and the same fixture plus one item created with `backlog new --summary "Probe item" --priority low --work-kind chore --apply` asserts `1 items checked, 0 violations` (measured at review on exactly this fixture: `--json` summary `1 items checked, 0 violations`, evidence `{'items': 1, 'drift': 0}`, F-9). In the nonzero test also run `attention --check --json` on the same tree and assert its `evidence[0]["value"]["items"]` equals the integer parsed from the human line, so the test pins cross-surface parity rather than a constant alone. Assert on subprocess stdout only.
  - Depends on: E-03
  - Expected outcome: two new tests pass after E-03 and fail against pre-E-03 code.
  - Execution state: performed

### Task group 3: research check-refs

- [x] E-05 Add `artifact_core.find_dangling_citations_counted(...)` taking the same arguments as `artifact_core.find_dangling_citations` and returning `(danglers, files_examined)`, where `files_examined` counts each file from `iter_scan_files` that was NOT skipped by `exclude_root` and was successfully read. Re-express `find_dangling_citations` as `find_dangling_citations_counted(...)[0]` so there is ONE scan loop (precedent: `leak_sanitizer.scan_working_tree` is `scan_working_tree_counted(...)[0]`). Add the matching `research_refs.find_dangling_citations_counted(repo_root, research_root=None)` wrapper beside `research_refs.find_dangling_citations`. The existing callers of the uncounted functions, `plans_index` (calls `_core.find_dangling_citations`) and `research_index` (calls `RF.find_dangling_citations`, i.e. `research_refs.find_dangling_citations`), are untouched and must behave identically.
  - Depends on: none
  - Expected outcome: both functions exist; the uncounted function returns exactly what it returned before (proved by the unchanged existing suite, including `tests/test_read_class_callers_refuse.py`'s `dng999` case).
  - Execution state: performed

- [x] E-06 In `research_refs.run_check_refs`, call the counted wrapper once, and compute ONE `summary` above the agent branch: `f"no dangling citations across {n} files"` when clean (keeps the `no dangling citations` substring) and `f"detected {len(danglers)} dangling citation(s) across {n} files"` otherwise. Pass it to `CommandResult`, add `"checked": n` to `data` (so the `--agent` record gains `checked`, via `result_types.CommandResult.to_agent_record`'s existing `"checked" in self.data` test) and `"checked": n` to the `research-refs` Evidence value beside `dangling_count`. Human clean path prints `{summary}`; human drift path keeps every `{file}:{line}: dangling id6 ...` line and appends `research check-refs: {summary}`. Exit codes unchanged (0/1/2).
  - Depends on: E-05
  - Expected outcome: human, `--agent` (`checked`) and `--json` (`data.checked`) report the same integer on one tree; a zero-scan-root repo reports `0 files`.
  - Execution state: performed

- [x] E-07 Add to `tests/test_agent_checked_count.py` tests for `research check-refs`: an empty repo (`init_repo` plus `mkdir -p .aw/records/plans`, per the fixture-anchoring convention, so the scan root exists but holds no file), human stdout contains `across 0 files` and exit 0, and `--agent` record has `checked == 0`; a repo with one markdown file under `.aw/records/plans/` citing `RSCH-zzz999` exits 1, its human stdout names `zzz999` AND contains `across 1 files`, and `--agent` `checked == 1`.
  - Depends on: E-06
  - Expected outcome: new tests pass after E-06 and fail against pre-E-06 code.
  - Execution state: performed

### Task group 4: sanitize (check-local-leaks)

- [x] E-08 Make each `leak_sanitizer` scan mode report how many units it examined, without changing the public `leak_sanitizer.run` signature or return shape (tests and `local_leaks` re-export call `run(...)` and unpack two values). Add `leak_sanitizer.run_counted(...)` with `run`'s parameters returning `(fails, warns, examined, unit)`, where working tree uses the existing `scan_working_tree_counted` (unit `files`), staged counts staged blobs actually scanned (unit `staged files`), history counts `commit ` header lines seen (unit `commits`), and wheel counts entries read (unit `wheel entries`); add `_counted` siblings for staged/history/wheel the same way `scan_working_tree_counted` is shaped, with the existing functions becoming `[0]` of them. Re-express `run` as `run_counted(...)[:2]` so there is one dispatch.
  - Depends on: none
  - Expected outcome: `run_counted` exists; `run` returns identical `(fails, warns)` to before (proved by the unchanged `tests/test_leak_sanitizer.py` and `tests/test_local_leaks.py`).
  - Execution state: performed

- [x] E-09 In `leak_sanitizer.main`'s scan path (not `--fix`), call `run_counted` and compute ONE `summary` above the machine branch: clean `f"No local leaks found. {examined} {unit} checked."` (keeps the `No local leaks found.` substring `tests/test_local_leaks.py` asserts), findings `f"{len(fails)} local leak(s) detected across {examined} {unit}"`. Use it as the `CommandResult.summary`, add `"checked": examined` to `data` and to the `leak-scan` Evidence value. Human clean path prints `summary` to stderr where it prints today; human fail path keeps the `Local-leak(s) found:` block and per-finding lines and adds one `{summary}.` line before the remediation paragraph. Stream choice and exit codes (0/1/2) unchanged.
  - Depends on: E-08
  - Expected outcome: `aw sanitize` in this repo prints `No local leaks found. N files checked.` with N equal to the `--agent` `checked` value; the pre-commit hook (`.pre-commit-config.yaml` `local-leaks`) still exits 0 on a clean tree.
  - Execution state: performed

- [x] E-10 Add to `tests/test_agent_checked_count.py` tests for `check-local-leaks`, isolating user hints the way `tests/test_leak_sanitizer_machine_flags.py` does (XDG override) so the maintainer's machine cannot change the result. Set `XDG_CONFIG_HOME` in `os.environ` for the test's duration (setUp/addCleanup or `unittest.mock.patch.dict`), NOT via a `run_cli(env=...)` argument, because `_run_cli_with_fallback` accepts no `env` and its `AW_UNFIXED_TREE` branch copies `os.environ`, so only an `os.environ` override reaches both branches. Pass the repo as the positional `dir` argument (`check-local-leaks <repo> --no-color`), which `leak_sanitizer.main` honors with no project climb, so a bare `init_repo` fixture is correct here: a git repo with one committed harmless file prints `1 files checked` on the human surface (STDERR, where `leak_sanitizer.main` writes its human verdict) at exit 0 and reports `checked == 1` on `--agent` (stdout); the same repo with a second committed file containing `"/home/" + "someuser" + "/x"` exits 1 and its stderr names the rule `home-path` and contains `across 2 files`.
  - Depends on: E-09
  - Expected outcome: new tests pass after E-09 and fail against pre-E-09 code.
  - Execution state: performed

### Task group 5: user-facing record and suite

- [x] E-11 Add ONE `- Fixed:` line under `## 2.0.0 (pending)` in `CHANGELOG.md`, in user-facing register with NO em or en dash: `aw backlog check`, `aw attention --check`, `aw research check-refs` and `aw sanitize` now report how many items or files they examined, so a clean result over nothing is distinguishable from a clean result over many. Run `python3 -m pytest` BARE before the first source edit and after the last, recording each summary line and FAILED set.
  - Depends on: E-02, E-04, E-07, E-10
  - Expected outcome: one CHANGELOG line; two bare-suite summary lines with identical (expected empty) FAILED sets, with the passed count higher by the number of tests added.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Count wording convention: `"<N> <plural-noun> checked"` clean, `"<M> finding(s) detected across <N> <plural-noun>"` dirty, already used by `specs.run_check`, `backlog.run_check` and `attention.run`'s `--check` block. Grammar is not singularized (`1 specs checked` ships today in `specs check` and is asserted by `tests/test_validator_nonsurveyable_dir.py`); keep that convention rather than inventing pluralization.
- Precedent and pattern: executed plan `121j2r` (`.aw/records/plans/executed/20260929-uwerb5-01-121j2r-report-the-examined-count-on-the-human-specs-check-surface-s.ipd.md`) fixed `specs check` by hoisting `summary` above the branch, appending the count to the existing clean sentence, and pinning it in `tests/test_agent_checked_count.py` via `_run_cli_with_fallback`. This plan applies the same pattern four times.
- Counted-variant precedent: `leak_sanitizer.scan_working_tree_counted` returns `(findings, count)` and `scan_working_tree` is its `[0]`; `doctor.probe_sanitizer` consumes the counted form. E-05 and E-08 follow that shape so there is one scan loop per mode.
- `result_types.CommandResult.to_agent_record` emits `checked` whenever `"checked" in self.data` (zero survives, `kifrou`), so adding `data["checked"]` is all the agent surface needs.
- FIXTURE-ANCHORING CONVENTION (F-9, measured at review): `backlog check`, `attention --check` and `research check-refs` resolve their root with `project_context.resolve_verb_repo_root`, which CLIMBS (`find_project_root`) to the nearest ancestor holding `.aw/{system,records,config}` or a legacy `.agents/` marker. A bare `init_repo` temp directory is NOT a project, so on a machine with any such ancestor (this review host has a stray `/tmp/.aw/records` and `~/.aw/config`) the command surveys THAT ancestor and the "empty" count is not zero. Every zero/nonzero fixture for these three commands MUST therefore create `.aw/records/<tree>` inside the temp repo BEFORE the first CLI call (as the existing `test_backlog_check_agent_emits_checked_zero_on_empty_tree` already does), and every throwaway-repo V-evidence run must do the same. `check-local-leaks` takes a positional `dir` and does not climb.
- Test contract (AGENTS.md, GUIDING_PRINCIPLES P16): assert subprocess/CLI outputs and exit codes; never read production source with `inspect`/`ast`/regex.
- Run the suite BARE as `python3 -m pytest`; do not add `-n0`, another `-q`, or `-p no:randomly`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Where | Finding |
|---|---|---|
| F-1 | `backlog.run_check` human branch | Measured in this lane 2026-10-12: `aw backlog check --no-color` prints exactly `aw backlog check: all backlog items conform.` at exit 0 while `--agent` reports `"checked":948`; in an empty repo `--agent` reports `"checked":0` and the human line is identical. The drift path prints `aw backlog check: 6 violation(s).` with no examined count. The count (`items_count`) and the `summary` wording already exist but only inside the machine branch. |
| F-2 | `attention.run` `--check` block | Measured: `aw attention --check --no-color` prints `aw attention --check: the view is valid.` while `--json` reports summary `2472 items checked, 0 violations` and evidence `{'items': 2472, 'drift': 0}`; an empty repo prints the identical human line while `--json` says `0 items checked, 0 violations`. The drift path prints only per-drift lines. The `summary` is already hoisted above the branch, so this is pure plumbing. A second hand-written `the view is valid.` sits in the no-project climb branch. |
| F-3 | `research_refs.run_check_refs`, `artifact_core.find_dangling_citations` | NO EXAMINED COUNT EXISTS ON ANY SURFACE. The detector returns only `List[Dangler]`; `--agent` in an empty repo prints `"findings":0` with no `checked`, and the human prints `no dangling citations`. The only meaningful examined unit is files read by the scan loop (`iter_scan_files` minus `exclude_root` minus unreadable). `plans_index` also calls `_core.find_dangling_citations` and `research_index` calls `research_refs.find_dangling_citations` (review addition), so both uncounted functions must keep their exact behavior. |
| F-4 | `leak_sanitizer.main` / `leak_sanitizer.run` | NO EXAMINED COUNT ON ANY SURFACE: `run` returns `(fails, warns)`; `--agent` in an empty repo prints `"findings":0` with no `checked`; human prints `No local leaks found.` to stderr. Only the working-tree mode has a counted sibling (`scan_working_tree_counted`, used by `doctor.probe_sanitizer`). The unit legitimately differs per mode (files, staged files, commits, wheel entries), so the unit must travel with the count. `run` is called with two-value unpacking in `tests/test_leak_sanitizer.py` and `tests/test_local_leaks.py` and re-exported by `local_leaks`, so its signature is a compatibility surface. |
| F-5 | strings pinned by tests | Measured with `rg`: `all backlog items conform.` is asserted in `tests/test_validator_nonsurveyable_dir.py`; `the view is valid` in `tests/test_explicit_dir_non_project.py` and `tests/test_attention.py` (presence) and in `tests/test_attention_excluded_tree_selector.py` / `tests/test_attention.py` (ABSENCE, on excluded-tree and refusal paths this plan does not touch); `No local leaks found.` in `tests/test_local_leaks.py`; `dng999` presence in `tests/test_read_class_callers_refuse.py`. `violation(s).` and `no dangling citations` are asserted by no test. Every pinned substring is preserved by appending, never replacing. |
| F-6 | `tests/test_validator_nonsurveyable_dir.py` `test_control_surveyable_root_reports_nonzero_artifacts` | This test PINS THE DEFECT: its comment reads `# Backlog check human (countless success line preserved)` and it asserts `self.assertNotIn("0", proc_bl.stdout)`. With one item the new line `1 backlog items checked` happens to contain no `0`, so it would still pass, but only by accident (ten items would break it) and the comment would then be false. E-02 replaces it with a positive count assertion mirroring the specs assertion beside it. |
| F-7 | `tests/conformance_matrix.py` | As measured by `121j2r` F-10, this module collects zero tests and is imported by no test module; it lists `research check-refs` among its leaves. Keeping the in-place shape (OQ-01) leaves `semantic_facts_from_human`'s input shape unchanged for these leaves anyway. |
| F-9 | `project_context.find_project_root` climb vs bare temp fixtures | Measured at review 2026-10-12: in a bare `git init` directory under `/tmp/opencode/`, `aw attention --check --json` reported `12 items checked, 0 violations` (it climbed to a stray `/tmp/.aw/records`), and `aw backlog new ... --apply` WROTE its item to `/tmp/.agents/backlog/open/` rather than the temp repo. With `.aw/records/backlog/open` created first, the same commands reported `0 items checked, 0 violations` / `checked:0`, and after one `backlog new` `1 items checked, 0 violations` / `checked:1`. Hence the fixture-anchoring convention. |
| F-10 | `aw backlog new` CLI | Measured: `--title` is rejected (`unrecognized arguments`); `--summary` alone is refused with `--priority and --work-kind required`. The working form is `backlog new --summary <s> --priority low --work-kind chore --apply`. |
| F-8 | pending plan `19fch9` | Also declares `agent_workflows/backlog.py`, but edits the `run_set` adapter, not `run_check`. Recorded for reviewers; ordering and worktree isolation are the runner's job, so no dependency edge is declared. |

## Proposed changes (ordered, validatable)

1. E-01, E-02: `backlog check` human count on both paths; fix the defect-pinning test; add human tests.
2. E-03, E-04: `attention --check` human count on both paths and the no-project branch; add human tests.
3. E-05, E-06, E-07: counted dangling-citation scan; `research check-refs` count on all three surfaces; tests.
4. E-08, E-09, E-10: counted leak scan per mode; `sanitize` count on all three surfaces; tests.
5. E-11: CHANGELOG line and bare-suite before/after comparison.

## Deferred / out of scope (with reason)

- Full `HumanRenderer` adoption for the four commands (OQ-01). It rewrites every line of four outputs, widens regression risk, and is not needed to close the missing-fact defect.
  - Carrier-Declined: A STYLING MIGRATION, NOT AN OBLIGATION. The defect this item names (a missing count) is closed in full by the in-place edits, and `121j2r`'s reviewed OQ-01 made the same call for `specs check`. No contract requires the renderer layout for these commands; filing an item for it would create work no evidence demands.
- `sanitize --fix` output. It reports rewritten files by name already, which is its examined set; it is not a check verdict.
  - Carrier-Declined: NOT PART OF THE DEFECT. `--fix` lists each rewritten path, so its output is never a bare countless verdict, and nothing remains to carry.
- `plans_index`'s dangling-citation surface. It uses the uncounted detector inside `aw index plans --check`, a different command not named by this item.
  - Carrier-Declined: OUT OF THE ITEM'S SUBJECT. The item names four commands; `aw index plans --check` reports through `emit_index_check_result`, a separate surface whose count behavior was not measured as defective here, so filing work for it would assert a defect nobody observed.

## Scope check

- Over-scope: `agent_workflows/artifact_core.py` is not one of the four commands' modules, but `research check-refs` has no count without a counted detector (F-3), and putting the loop there keeps one scan loop. `tests/test_validator_nonsurveyable_dir.py` is edited only because it pins the defect (F-6). Adding `checked` to the `research check-refs` and `sanitize` machine surfaces goes beyond "human surfaces", but without it the human surface would report a fact the machine surfaces lack, which is the Section 2 drift in the other direction.
- Under-scope: none known. The four commands named by the item are all covered on both paths.

## Required tests / validation

- `python3 -m pytest tests/test_agent_checked_count.py tests/test_validator_nonsurveyable_dir.py` bare, plus each new test shown FAILING against pre-change code (stash or revert the source edit, re-run, paste failures).
- For each command, a three-surface comparison (human, `--agent`, `--json`) on one unchanged tree showing one integer, and a zero case in a throwaway empty repository, pasted verbatim.
- Exit-code parity on a clean and a dirty tree for each command.
- `python3 -m pytest` bare before and after, FAILED sets compared by name.
- `aw ipd lint --phase pre-transition` conforming before any terminal transition.

## Spec / documentation sync

No `.spec.md` governs how these four commands phrase their human output, so no spec path is declared and none is amended (`121j2r` searched the specs tree for the same question and found none; the specs mentioning `backlog check`/`attention --check` describe validation rules, not output wording). `docs/cli-output-contract.md` Sections 2 and 11.1 already require the behavior and need no edit. The only documentation written is the E-11 CHANGELOG line. If the executor finds a doc sentence quoting a countless line as correct, correct it and declare the file with `--scope-reason`.

## Open questions

### OQ-01: four in-place edits, or a unified `HumanRenderer` adoption?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED TO IN-PLACE EDITS. The backlog item offers both. In-place is the smallest change that closes the measured defect, preserves every test-pinned substring (F-5), and matches the shape `121j2r`'s reviewer chose for `specs check`, so all five check commands stay consistent with each other. `HumanRenderer` adoption would restyle four outputs, newly emit the `AW <command>` banner that `tests/conformance_matrix.py`'s `semantic_facts_from_human` keys on (latent today, F-7), and break the absence/presence assertions listed in F-5. A reviewer or maintainer who prefers the renderer migration should overturn this before approval, since it changes the E-items and V-evidence materially.
- Carrier-Declined: DECIDED HERE; the unchosen alternative is a styling choice with no residual obligation (see the matching Deferred entry).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the `backlog.run_check` diff; ACTUAL stdout and exit status of `aw backlog check --no-color` in (a) this repo, with `aw backlog check --agent`'s `checked` on the same tree showing the same integer (re-derive it, do not assume 948), (b) a throwaway repo with an empty `.aw/records/backlog/open/` showing `0 backlog items checked` and exit 0, (c) a throwaway repo with one malformed item showing the drift lines plus `finding(s) detected across 1 backlog items` and exit 1. Quote the single hoisted `summary` expression both branches read. Observations come from `backlog.run_check` via the CLI.
  - Observed evidence:
    `backlog.run_check` now computes `exit_code`/`status`/`summary` ONCE above `if ctx.is_agent or ctx.is_json:`:
      summary = (f"{items_count} backlog items checked" if exit_code == 0
                 else f"{len(drift)} finding(s) detected across {items_count} backlog items")
    Human clean: `msg = f"aw backlog check: all backlog items conform. {summary}."`; drift: `sys.stdout.write(f"aw backlog check: {summary}.\n")`; `return exit_code`.
    (a) this repo: `aw backlog check: all backlog items conform. 976 backlog items checked.` exit=0; `--agent`: `{"cmd":"backlog check","outcome":"clean","exit":0,...,"checked":976,...}`.
    (b) /dev/shm throwaway with empty `.aw/records/backlog/open/`: `aw backlog check: all backlog items conform. 0 backlog items checked.` exit=0.
    (c) one malformed item: five `...: backlog.id-invalid|priority-invalid|kind-invalid|set-missing|summary-missing: ...` lines then `aw backlog check: 5 finding(s) detected across 1 backlog items.` exit=1.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the diff of `tests/test_validator_nonsurveyable_dir.py` showing `assertNotIn("0", proc_bl.stdout)` replaced by a positive count assertion, the comment corrected, and the empty-project backlog assertion strengthened to `0 backlog items checked.`; the two new tests' fixture code showing `.aw/records/backlog/open` created before the first CLI call; names and source of the two new backlog tests; bare `python3 -m pytest tests/test_agent_checked_count.py tests/test_validator_nonsurveyable_dir.py` summary line; and the FAILURE output of the two new tests against pre-E-01 `backlog.py`.
  - Observed evidence:
    `tests/test_validator_nonsurveyable_dir.py`: comment now `# Backlog check human (nonzero examined count reported, rolswj/akhwp7)`; `self.assertNotIn("0", proc_bl.stdout)` replaced by `self.assertIn("all backlog items conform. 1 backlog items checked.", proc_bl.stdout)`; `test_control_empty_but_real_project_clean` now asserts `all backlog items conform. 0 backlog items checked.`.
    New tests in `tests/test_agent_checked_count.py::HumanCheckedCountTests`: `test_backlog_check_human_emits_checked_zero_on_empty_tree`, `test_backlog_check_human_emits_checked_nonzero_control`; fixture `_anchored_repo(td, "backlog/open")` = `init_repo` + `mkdir -p .aw/records/<tree>` before any CLI call; item via `_new_backlog_item` (`backlog new --summary "Probe item" --priority low --work-kind chore --apply`).
    Focused run (`python3 -m pytest -o addopts="" -q -p no:cacheprovider tests/test_agent_checked_count.py tests/test_validator_nonsurveyable_dir.py`): `5 failed, 21 passed in 33.21s`; the 5 failures (`test_specs_check_bare_no_project_refusal_human/agent`, `test_backlog_check_bare_no_project_refusal_human/agent`, `test_precondition_outside_is_not_project`) are in the PRE-CHANGE baseline FAILED set, caused by a stray `/tmp/.aw` on this host (`AssertionError: PosixPath('/tmp') is not None : outside_cwd must not be under an AW project`); every edited/new test passes.
    Against pre-change code (`AW_UNFIXED_TREE` = `git archive 09cf2ec24 agent_workflows`):
      E AssertionError: 'all backlog items conform. 0 backlog items checked.' not found in 'aw backlog check: all backlog items conform.\n'
      E AssertionError: 'all backlog items conform. 1 backlog items checked.' not found in 'aw backlog check: all backlog items conform.\n'
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the `attention.run` diff; ACTUAL stdout and exit status of `aw attention --check --no-color` in this repo with the `--json` `evidence[0].value.items` from the same tree showing the same integer; in an empty throwaway repo anchored per the fixture-anchoring convention (`0 items checked, 0 violations`); in a tree with at least one drift record (drift lines plus count line, exit 1; an anchored repo plus a status-less `.aw/records/plans/pending/x.md` produced `attention.missing-status` at review); and bare `aw attention --check` run from a directory for which `project_context.find_project_root()` returns `None` (paste that call's output from the same cwd FIRST; a temp dir under `/tmp` may climb to a stray `/tmp/.aw`, F-9, so choose e.g. a fresh dir under `/dev/shm`) showing the no-project branch line with `0 items checked`. Confirm in writing the excluded-tree and refusal paths were not edited. Observations come from `attention.run` via the CLI.
  - Observed evidence:
    `attention.run`: drift path appends `sys.stdout.write(f"aw attention --check: {summary}.\n")` after per-drift lines; clean path `f"aw attention --check: the view is valid. {summary}.\n"`; `if drift:`/`else:` unchanged. No-project branch: local `no_project_items = 0` feeds BOTH the Evidence value `{"items": no_project_items, "drift": 0}` and the human line `the view is valid. {no_project_items} items checked, 0 violations.`; machine summary unchanged. `_emit_excluded_tree_explanation` / `_emit_unresolved_selector_refusal` were not edited (diff touches only the two blocks above).
    This repo: `aw attention --check: 6 finding(s) detected across 2605 items.` exit=1 (live lane-stranded drift); `--json`: `6 finding(s) detected across 2605 items {'items': 2605, 'drift': 6}`.
    Anchored empty /dev/shm repo: `aw attention --check: the view is valid. 0 items checked, 0 violations.` exit=0; `--json`: `0 items checked, 0 violations {'items': 0, 'drift': 0}`.
    Drift tree (status-less `.aw/records/plans/pending/x.md`): `.aw/records/plans/pending/x.md: attention.missing-status: no plan Status` then `aw attention --check: 1 finding(s) detected across 1 items.` exit=1.
    No project: in a fresh `/dev/shm/.../np`, `find_project_root(Path.cwd())` printed `None`; `aw attention --check --no-color` printed `aw attention --check: the view is valid. 0 items checked, 0 violations.` exit=0.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: names and source of the two new attention tests, the bare focused-run summary line, and their FAILURE output against pre-E-03 `attention.py`.
  - Observed evidence:
    New tests: `test_attention_check_human_emits_checked_zero_on_empty_tree` (asserts `the view is valid. 0 items checked, 0 violations.`, exit 0) and `test_attention_check_human_count_matches_json_evidence` (one backlog item; asserts `1 items checked, 0 violations`, parses the integer with `re.search(r"(\d+) items checked", ...)` and asserts it equals `--json` `evidence[0]["value"]["items"]`).
    Passing in the post-change bare full run (`39 failed, 7182 passed`, neither test in the FAILED set). Against pre-change code:
      E AssertionError: 'the view is valid. 0 items checked, 0 violations.' not found in 'aw attention --check: the view is valid.\n'
      E AssertionError: 'the view is valid. 1 items checked, 0 violations.' not found in 'aw attention --check: the view is valid.\n'
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the `artifact_core.py` and `research_refs.py` diff showing ONE scan loop with the uncounted function as `[0]` of the counted one; bare run of `tests/test_read_class_callers_refuse.py` and `tests/test_research_index.py` summary lines showing them still passing.
  - Observed evidence:
    `artifact_core.find_dangling_citations_counted(...)` holds the ONLY scan loop, incrementing `files_examined` after the `exclude_root` skip and successful `read_text`, returning `danglers, files_examined`; `find_dangling_citations(...)` is now `return find_dangling_citations_counted(...)[0]`. `research_refs.find_dangling_citations_counted(repo_root, research_root=None)` delegates to it with the same resolver/matcher/exclude as the unchanged `research_refs.find_dangling_citations`.
    `tests/test_read_class_callers_refuse.py` and `tests/test_research_index.py`: in the focused run, the only failures in these files were `test_check_miscategorized_bare_outside_project`, `test_read_verbs_refuse_bare_outside_project[cmd_prefix0]`, `[cmd_prefix2]`, all three in the pre-change baseline FAILED set (stray `/tmp/.aw`); `comm -23` of focused FAILED vs baseline FAILED printed nothing. Bare full suite before/after FAILED sets identical.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the `run_check_refs` diff quoting the single `summary` expression; human, `--agent` and `--json` output of `aw research check-refs` on one unchanged tree (this repo) showing the same integer (human `across N files`, agent `checked`, json `data.checked`); an empty throwaway repo anchored per the fixture-anchoring convention showing `no dangling citations across 0 files`, exit 0, and agent `"checked":0`; exit 1 unchanged on the dangling tree. Observations come from `research_refs.run_check_refs` via the CLI.
  - Observed evidence:
    `research_refs.run_check_refs` computes above the agent branch:
      summary = (f"no dangling citations across {files_examined} files" if not danglers
                 else f"detected {len(danglers)} dangling citation(s) across {files_examined} files")
    `data["checked"] = files_examined`, Evidence value `{"dangling_count": len(danglers), "checked": files_examined}`; human clean prints `summary`, drift appends `research check-refs: {summary}`.
    This repo: human `research check-refs: detected 275 dangling citation(s) across 2528 files` exit=1; `--agent` `"checked":2528,"findings":275`; `--json` `data.checked` = `2528`, evidence `{'dangling_count': 275, 'checked': 2528}`.
    Anchored empty /dev/shm repo: `no dangling citations across 0 files` exit=0; `--agent` `{"cmd":"research check-refs","outcome":"clean","exit":0,...,"checked":0,"findings":0,...}`.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: names and source of the new research tests, the bare focused-run summary line, and their FAILURE output against pre-E-06 code.
  - Observed evidence:
    New tests: `test_research_check_refs_reports_zero_files_on_empty_tree` (anchored `plans` tree; human `no dangling citations across 0 files`, exit 0; agent `checked == 0`) and `test_research_check_refs_reports_files_on_dangling_tree` (`.aw/records/plans/note.md` citing `RSCH-zzz999`; exit 1, stdout names `zzz999` and contains `across 1 files`; agent `checked == 1`). Both pass in the post-change bare run. Against pre-change code:
      E AssertionError: 'no dangling citations across 0 files' not found in 'no dangling citations\n'
      E AssertionError: 'across 1 files' not found in "/tmp/tmpz0sggf93/.aw/records/plans/note.md:1: dangling id6 'zzz999': See RSCH-zzz999 for details.\n"
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: the `leak_sanitizer.py` diff showing `run_counted`, the `_counted` siblings, and `run` re-expressed over `run_counted`; bare `python3 -m pytest tests/test_leak_sanitizer.py tests/test_local_leaks.py tests/test_leak_sanitizer_machine_flags.py` summary line showing all still pass.
  - Observed evidence:
    `leak_sanitizer.py` adds `scan_staged_counted` (counts staged blobs scanned), `scan_history_counted` (counts `commit ` header lines), `scan_wheel_counted` (counts entries read); `scan_staged`/`scan_history`/`scan_wheel` are now `[0]` of them (as `scan_working_tree` already was). `run_counted(...)` holds the one dispatch and returns `(fails, warns, examined, unit)` with unit `wheel entries`/`commits`/`staged files`/`files`; `run(...)` unpacks `run_counted` and returns `fails, warns` (signature unchanged).
    `tests/test_leak_sanitizer.py tests/test_local_leaks.py tests/test_leak_sanitizer_machine_flags.py`: none of their tests appears in the focused-run FAILED list (all 15 focused failures are baseline `/tmp/.aw` cases in other files) nor in the post-change full-run FAILED set.
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: the `leak_sanitizer.main` diff quoting the single `summary` expression; human (stderr), `--agent` and `--json` output of `aw sanitize` on this repo showing one integer; `aw sanitize --staged` and `aw sanitize --history --max-commits 3` human lines showing their units (`staged files`, `commits`); a throwaway repo with one committed harmless file showing `1 files checked` at exit 0 and with a planted home-path leak showing the findings block plus `across N files` at exit 1. Observations come from `leak_sanitizer.main` via the CLI.
  - Observed evidence:
    `leak_sanitizer.main` computes above the machine branch:
      summary = (f"No local leaks found. {examined} {unit} checked." if not fails
                 else f"{len(fails)} local leak(s) detected across {examined} {unit}")
    `data["checked"]` and the `leak-scan` Evidence value carry `examined`; human clean `print(summary, file=sys.stderr)`; fail path prints `{summary}.` before the remediation paragraph.
    This repo: stderr `No local leaks found. 4791 files checked.` exit=0; `--agent` `"checked":4791,"findings":0`; `--json` `No local leaks found. 4791 files checked. {'fails': 0, 'warns': 0, 'checked': 4791}`.
    `aw sanitize --staged`: `No local leaks found. 0 staged files checked.` exit=0. `aw sanitize --history --max-commits 3`: `No local leaks found. 3 commits checked.` exit=0.
    Throwaway (XDG_CONFIG_HOME isolated): one harmless committed file `No local leaks found. 1 files checked.` exit=0; with a planted home path: `Local-leak(s) found:` / `  l.txt:1: home-path: path <home>/someuser/x` / `1 local leak(s) detected across 2 files.` then the remediation paragraph, exit=1. The `local-leaks` pre-commit hook will be exercised by `aw commit` below.
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: names and source of the new sanitize tests (showing the XDG isolation), the bare focused-run summary line, and their FAILURE output against pre-E-09 code.
  - Observed evidence:
    New tests: `test_sanitize_reports_files_checked_on_clean_repo` and `test_sanitize_reports_files_checked_on_leaking_repo`, each wrapped in `mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(Path(td) / "cfg")})` and passing the repo as positional `dir`; assert stderr `No local leaks found. 1 files checked.` + agent `checked == 1`, and exit 1 + stderr `home-path` + `across 2 files`. Both pass post-change. Against pre-change code:
      E AssertionError: 'No local leaks found. 1 files checked.' not found in 'No local leaks found.\n'
      E AssertionError: 'across 2 files' not found in "Local-leak(s) found:\n  leak.txt:1: home-path: path <home>/someuser/x\n\nRemove or abstract these ...
  - Result: pass

- [x] V-11 validates E-11
  - Required evidence: the CHANGELOG line, confirmed under `## 2.0.0 (pending)` with no em or en dash; the bare `python3 -m pytest` summary line and FAILED set from BEFORE the first source edit and AFTER the last, with an explicit statement whether the FAILED sets are identical; confirmation no flag was added to the bare invocation.
  - Observed evidence:
    CHANGELOG line added under `## 2.0.0 (pending)`: "- Fixed: `aw backlog check`, `aw attention --check`, `aw research check-refs` and `aw sanitize` now report how many items or files they examined, so a clean result over nothing is distinguishable from a clean result over many." (grep for U+2013/U+2014 on it: none).
    BEFORE (bare `python3 -m pytest`, prior to any source edit): `39 failed, 7174 passed, 2 skipped, 3 warnings in 394.44s (0:06:34)`.
    AFTER (bare `python3 -m pytest`): `39 failed, 7182 passed, 2 skipped, 3 warnings in 333.02s (0:05:33)`.
    FAILED sets compared by name (`comm` both directions): IDENTICAL, no new and none fixed; passed +8 = the 8 new tests. The 39 pre-existing failures are environmental (stray `/tmp/.aw` / `/tmp/.agents` ancestor on this host making `/tmp` a project). No flag was added to either bare invocation.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan has been through `/plan-review` and requires explicit human approval before execution. OQ-01 is resolved; no open question remains. Execute task groups in order; groups 1 through 4 are independent of one another, group 5 runs last but its BEFORE suite baseline must be captured before the first source edit.

Execution contract: commit only the paths in `- Scope-Paths:` through `aw commit akhwp7 -- <paths>`; never `git add -A`, `-a`, or `--no-verify`; never push, tag, or release. Paste actual runner output for every test claim. Other agents may share this checkout: verify the staged set with `git diff --cached --name-only` before committing and unstage anything not yours path by path with `git restore --staged <path>`.

Keep every test-pinned substring (F-5) by APPENDING the count, never replacing the sentence. Do not change `leak_sanitizer.run`'s signature or `artifact_core.find_dangling_citations`'s return value. If a needed edit falls outside `- Scope-Paths:`, make it and justify it with `--scope-reason`.

Post-gate lifecycle: do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence with `Result: pass`. In a runner lane the runner owns finalize; outside one, the executor completes the transition with `aw ipd finalize akhwp7` (never a hand `git mv`). The "fails against pre-change code" demonstrations in V-02/V-04/V-07/V-10 may use the test file's `AW_UNFIXED_TREE` hook (a pristine checkout of the base commit on `PYTHONPATH`) instead of stashing. Backlog `rolswj` carries no `- Blocks-Release:`; it reaches `done` once this plan is `executed`.

# IPD: Report examined counts on the human check surfaces of backlog check, attention --check, research check-refs, and sanitize

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `rolswj` (the F-7 sweep filed by executed plan `121j2r`) records that four check commands, `aw backlog check`, `aw attention --check`, `aw research check-refs` and `aw sanitize` (alias of `aw check-local-leaks`), hand-write their human output and print a clean verdict with NO examined count, so a clean result over zero artifacts is indistinguishable from a clean result over thousands. This is the same defect `121j2r` fixed for `aw specs check`, and it violates `docs/cli-output-contract.md` Section 2 ("Both renderers expose identical facts (counts, paths, evidence, exit code) with zero domain drift"). Two of the four (`research check-refs`, `sanitize`) do not even COMPUTE an examined count today, so their machine surfaces lack it too.
- Scope: IN: (1) `backlog.run_check` human branch prints the already-computed `items_count` on clean and drift paths; (2) `attention.run`'s `--check` human branch prints the already-computed `len(items)` on clean and drift paths, including the no-project climb branch; (3) `research_refs.run_check_refs` gains an examined-file count from a counted variant of `artifact_core.find_dangling_citations`, reported on all three surfaces; (4) `leak_sanitizer.main` gains a scanned-unit count from a counted variant of `leak_sanitizer.run`, reported on all three surfaces; (5) behavioral regression tests for each command at zero and nonzero; (6) one CHANGELOG line. OUT: adopting `HumanRenderer` for any of the four (OQ-01); `--fix` output of `sanitize`; `plans_index`'s use of the dangling detector; any change to which artifacts or files are examined; any exit code.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/attention.py, agent_workflows/research_refs.py, agent_workflows/artifact_core.py, agent_workflows/leak_sanitizer.py, tests/test_agent_checked_count.py, tests/test_validator_nonsurveyable_dir.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: medium
- From-Backlog: rolswj
- Set: rolswj
- Order: 1
- Highest E allocated: 11
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: akhwp7

## Workflow history

- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog `rolswj`. All four countless human lines were re-measured live in this lane and in throwaway empty repositories (F-1..F-4); the two commands that compute no count at all were identified from source (F-3, F-4), and one existing test that pins the countless backlog line was found (F-6). OQ-01 (in-place vs `HumanRenderer`) is resolved by the author to in-place, following `121j2r`'s reviewed precedent; a reviewer may overturn it.

## Goal

Make the human output of `aw backlog check`, `aw attention --check`, `aw research check-refs` and `aw sanitize` state how many things each command examined, on both the clean and the findings path, so an operator can tell a clean verdict over zero from a clean verdict over many, and so each command's human, `--agent` and `--json` surfaces report the SAME count from ONE expression.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: backlog check

- [ ] E-01 In `backlog.run_check`, hoist the `exit_code` / `status` / `summary` computation (today inside `if ctx.is_agent or ctx.is_json:`, worded `f"{items_count} backlog items checked"` / `f"{len(drift)} finding(s) detected across {items_count} backlog items"`) above the branch so both branches read ONE expression, exactly as `121j2r` did for `specs.run_check`. Human clean path becomes `aw backlog check: all backlog items conform. {summary}.` (KEEP the existing sentence and APPEND the count, because `tests/test_validator_nonsurveyable_dir.py` asserts the substring `all backlog items conform.`). Human drift path keeps every `{location}: {rule}: {detail}` line and replaces the trailing `aw backlog check: {len(drift)} violation(s).` with `aw backlog check: {summary}.` (nothing pins the `violation(s)` wording, F-5). Keep the color handling and `return exit_code` (same value as `core.drift_exit_code(drift)`).
  - Depends on: none
  - Expected outcome: `aw backlog check --no-color` prints `... all backlog items conform. 0 backlog items checked.` in a repo with no items, the same N the `--agent` `checked` field reports in this repo, and `K finding(s) detected across N backlog items` on drift; exit codes stay 0 and 1.
  - Execution state: pending

- [ ] E-02 Update the one existing test that pins the countless backlog line (F-6): in `tests/test_validator_nonsurveyable_dir.py` `test_control_surveyable_root_reports_nonzero_artifacts`, the comment `# Backlog check human (countless success line preserved)` and `self.assertNotIn("0", proc_bl.stdout)` encode the OLD defect. Replace the `assertNotIn("0", ...)` with `self.assertIn("all backlog items conform. 1 backlog items checked.", proc_bl.stdout)` (mirroring the specs assertion two lines above it) and correct the comment. Then add to `tests/test_agent_checked_count.py` two human-surface tests for `backlog check` (empty tree asserts `0 backlog items checked`; one-item control created with `aw backlog new ... --apply` asserts `1 backlog items checked`), driving the CLI through the file's `_run_cli_with_fallback` with `--no-color` and asserting on stdout.
  - Depends on: E-01
  - Expected outcome: the updated test and two new tests pass after E-01 and the two new tests FAIL against pre-E-01 code (stdout contains no `backlog items checked`).
  - Execution state: pending

### Task group 2: attention --check

- [ ] E-03 In `attention.run`'s `if check:` block, the `summary` is ALREADY hoisted above the agent branch (`f"{len(items)} items checked, 0 violations"` / `f"{len(drift)} finding(s) detected across {len(items)} items"`). Make the human branch print it: clean path `aw attention --check: the view is valid. {summary}.` (KEEP `the view is valid.`, which `tests/test_explicit_dir_non_project.py` and `tests/test_attention.py` assert), and on the drift path append `aw attention --check: {summary}.` after the existing per-drift lines. In the no-project climb branch (`if check and not explicit_dir:` under `if not refusal.may_proceed:`), whose agent evidence already says `{"items": 0, "drift": 0}`, print `aw attention --check: the view is valid. 0 items checked, 0 violations.`, deriving the `0` from the same literal value the Evidence carries (one local) rather than a second literal; leave that branch's machine `summary` string unchanged. Do NOT touch the excluded-tree or selector-refusal paths (`_emit_excluded_tree_explanation`, `_emit_unresolved_selector_refusal`), whose tests assert the validity sentence is ABSENT.
  - Depends on: none
  - Expected outcome: `aw attention --check --no-color` prints `the view is valid. N items checked, 0 violations.` with N equal to the `--json` evidence `items` value on the same tree; a drift tree prints the drift lines plus the count line; exit codes unchanged.
  - Execution state: pending

- [ ] E-04 Add to `tests/test_agent_checked_count.py` two human-surface tests for `attention --check`: an empty initialized repo asserts `0 items checked` and exit 0, and a repo with one backlog item created via `aw backlog new ... --apply` asserts `1 items checked` (or, if `aw attention` counts that item differently, the integer the same tree's `--json` `evidence[0].value.items` reports, read from a second subprocess in the same test, never hardcoded from a guess). Assert on subprocess stdout only.
  - Depends on: E-03
  - Expected outcome: two new tests pass after E-03 and fail against pre-E-03 code.
  - Execution state: pending

### Task group 3: research check-refs

- [ ] E-05 Add `artifact_core.find_dangling_citations_counted(...)` taking the same arguments as `artifact_core.find_dangling_citations` and returning `(danglers, files_examined)`, where `files_examined` counts each file from `iter_scan_files` that was NOT skipped by `exclude_root` and was successfully read. Re-express `find_dangling_citations` as `find_dangling_citations_counted(...)[0]` so there is ONE scan loop (precedent: `leak_sanitizer.scan_working_tree` is `scan_working_tree_counted(...)[0]`). Add the matching `research_refs.find_dangling_citations_counted(repo_root, research_root=None)` wrapper beside `research_refs.find_dangling_citations`. `plans_index`'s existing caller of the uncounted function is untouched and must behave identically.
  - Depends on: none
  - Expected outcome: both functions exist; the uncounted function returns exactly what it returned before (proved by the unchanged existing suite, including `tests/test_read_class_callers_refuse.py`'s `dng999` case).
  - Execution state: pending

- [ ] E-06 In `research_refs.run_check_refs`, call the counted wrapper once, and compute ONE `summary` above the agent branch: `f"no dangling citations across {n} files"` when clean (keeps the `no dangling citations` substring) and `f"detected {len(danglers)} dangling citation(s) across {n} files"` otherwise. Pass it to `CommandResult`, add `"checked": n` to `data` (so the `--agent` record gains `checked`, via `result_types.CommandResult.to_agent_record`'s existing `"checked" in self.data` test) and `"checked": n` to the `research-refs` Evidence value beside `dangling_count`. Human clean path prints `{summary}`; human drift path keeps every `{file}:{line}: dangling id6 ...` line and appends `research check-refs: {summary}`. Exit codes unchanged (0/1/2).
  - Depends on: E-05
  - Expected outcome: human, `--agent` (`checked`) and `--json` (`data.checked`) report the same integer on one tree; a zero-scan-root repo reports `0 files`.
  - Execution state: pending

- [ ] E-07 Add to `tests/test_agent_checked_count.py` tests for `research check-refs`: empty initialized repo, human stdout contains `across 0 files` and exit 0, and `--agent` record has `checked == 0`; a repo with one tracked markdown file under `.aw/records/plans/` citing `RSCH-zzz999` exits 1, its human stdout names `zzz999` AND contains `across 1 files`, and `--agent` `checked == 1`.
  - Depends on: E-06
  - Expected outcome: new tests pass after E-06 and fail against pre-E-06 code.
  - Execution state: pending

### Task group 4: sanitize (check-local-leaks)

- [ ] E-08 Make each `leak_sanitizer` scan mode report how many units it examined, without changing the public `leak_sanitizer.run` signature or return shape (tests and `local_leaks` re-export call `run(...)` and unpack two values). Add `leak_sanitizer.run_counted(...)` with `run`'s parameters returning `(fails, warns, examined, unit)`, where working tree uses the existing `scan_working_tree_counted` (unit `files`), staged counts staged blobs actually scanned (unit `staged files`), history counts `commit ` header lines seen (unit `commits`), and wheel counts entries read (unit `wheel entries`); add `_counted` siblings for staged/history/wheel the same way `scan_working_tree_counted` is shaped, with the existing functions becoming `[0]` of them. Re-express `run` as `run_counted(...)[:2]` so there is one dispatch.
  - Depends on: none
  - Expected outcome: `run_counted` exists; `run` returns identical `(fails, warns)` to before (proved by the unchanged `tests/test_leak_sanitizer.py` and `tests/test_local_leaks.py`).
  - Execution state: pending

- [ ] E-09 In `leak_sanitizer.main`'s scan path (not `--fix`), call `run_counted` and compute ONE `summary` above the machine branch: clean `f"No local leaks found. {examined} {unit} checked."` (keeps the `No local leaks found.` substring `tests/test_local_leaks.py` asserts), findings `f"{len(fails)} local leak(s) detected across {examined} {unit}"`. Use it as the `CommandResult.summary`, add `"checked": examined` to `data` and to the `leak-scan` Evidence value. Human clean path prints `summary` to stderr where it prints today; human fail path keeps the `Local-leak(s) found:` block and per-finding lines and adds one `{summary}.` line before the remediation paragraph. Stream choice and exit codes (0/1/2) unchanged.
  - Depends on: E-08
  - Expected outcome: `aw sanitize` in this repo prints `No local leaks found. N files checked.` with N equal to the `--agent` `checked` value; the pre-commit hook (`.pre-commit-config.yaml` `local-leaks`) still exits 0 on a clean tree.
  - Execution state: pending

- [ ] E-10 Add to `tests/test_agent_checked_count.py` tests for `check-local-leaks`, isolating user hints the way `tests/test_leak_sanitizer_machine_flags.py` does (XDG override) so the maintainer's machine cannot change the result: a git repo with one committed harmless file prints `1 files checked` on the human surface at exit 0 and reports `checked == 1` on `--agent`; the same repo with a second committed file containing `"/home/" + "someuser" + "/x"` exits 1, names the rule `home-path`, and reports `across 2 files`.
  - Depends on: E-09
  - Expected outcome: new tests pass after E-09 and fail against pre-E-09 code.
  - Execution state: pending

### Task group 5: user-facing record and suite

- [ ] E-11 Add ONE `- Fixed:` line under `## 2.0.0 (pending)` in `CHANGELOG.md`, in user-facing register with NO em or en dash: `aw backlog check`, `aw attention --check`, `aw research check-refs` and `aw sanitize` now report how many items or files they examined, so a clean result over nothing is distinguishable from a clean result over many. Run `python3 -m pytest` BARE before the first source edit and after the last, recording each summary line and FAILED set.
  - Depends on: E-02, E-04, E-07, E-10
  - Expected outcome: one CHANGELOG line; two bare-suite summary lines with identical (expected empty) FAILED sets, with the passed count higher by the number of tests added.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Count wording convention: `"<N> <plural-noun> checked"` clean, `"<M> finding(s) detected across <N> <plural-noun>"` dirty, already used by `specs.run_check`, `backlog.run_check` and `attention.run`'s `--check` block. Grammar is not singularized (`1 specs checked` ships today in `specs check` and is asserted by `tests/test_validator_nonsurveyable_dir.py`); keep that convention rather than inventing pluralization.
- Precedent and pattern: executed plan `121j2r` (`.aw/records/plans/executed/20260929-uwerb5-01-121j2r-report-the-examined-count-on-the-human-specs-check-surface-s.ipd.md`) fixed `specs check` by hoisting `summary` above the branch, appending the count to the existing clean sentence, and pinning it in `tests/test_agent_checked_count.py` via `_run_cli_with_fallback`. This plan applies the same pattern four times.
- Counted-variant precedent: `leak_sanitizer.scan_working_tree_counted` returns `(findings, count)` and `scan_working_tree` is its `[0]`; `doctor.probe_sanitizer` consumes the counted form. E-05 and E-08 follow that shape so there is one scan loop per mode.
- `result_types.CommandResult.to_agent_record` emits `checked` whenever `"checked" in self.data` (zero survives, `kifrou`), so adding `data["checked"]` is all the agent surface needs.
- Test contract (AGENTS.md, GUIDING_PRINCIPLES P16): assert subprocess/CLI outputs and exit codes; never read production source with `inspect`/`ast`/regex.
- Run the suite BARE as `python3 -m pytest`; do not add `-n0`, another `-q`, or `-p no:randomly`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Where | Finding |
|---|---|---|
| F-1 | `backlog.run_check` human branch | Measured in this lane 2026-10-12: `aw backlog check --no-color` prints exactly `aw backlog check: all backlog items conform.` at exit 0 while `--agent` reports `"checked":948`; in an empty repo `--agent` reports `"checked":0` and the human line is identical. The drift path prints `aw backlog check: 6 violation(s).` with no examined count. The count (`items_count`) and the `summary` wording already exist but only inside the machine branch. |
| F-2 | `attention.run` `--check` block | Measured: `aw attention --check --no-color` prints `aw attention --check: the view is valid.` while `--json` reports summary `2472 items checked, 0 violations` and evidence `{'items': 2472, 'drift': 0}`; an empty repo prints the identical human line while `--json` says `0 items checked, 0 violations`. The drift path prints only per-drift lines. The `summary` is already hoisted above the branch, so this is pure plumbing. A second hand-written `the view is valid.` sits in the no-project climb branch. |
| F-3 | `research_refs.run_check_refs`, `artifact_core.find_dangling_citations` | NO EXAMINED COUNT EXISTS ON ANY SURFACE. The detector returns only `List[Dangler]`; `--agent` in an empty repo prints `"findings":0` with no `checked`, and the human prints `no dangling citations`. The only meaningful examined unit is files read by the scan loop (`iter_scan_files` minus `exclude_root` minus unreadable). `plans_index` also calls `_core.find_dangling_citations`, so the uncounted function must keep its exact behavior. |
| F-4 | `leak_sanitizer.main` / `leak_sanitizer.run` | NO EXAMINED COUNT ON ANY SURFACE: `run` returns `(fails, warns)`; `--agent` in an empty repo prints `"findings":0` with no `checked`; human prints `No local leaks found.` to stderr. Only the working-tree mode has a counted sibling (`scan_working_tree_counted`, used by `doctor.probe_sanitizer`). The unit legitimately differs per mode (files, staged files, commits, wheel entries), so the unit must travel with the count. `run` is called with two-value unpacking in `tests/test_leak_sanitizer.py` and `tests/test_local_leaks.py` and re-exported by `local_leaks`, so its signature is a compatibility surface. |
| F-5 | strings pinned by tests | Measured with `rg`: `all backlog items conform.` is asserted in `tests/test_validator_nonsurveyable_dir.py`; `the view is valid` in `tests/test_explicit_dir_non_project.py` and `tests/test_attention.py` (presence) and in `tests/test_attention_excluded_tree_selector.py` / `tests/test_attention.py` (ABSENCE, on excluded-tree and refusal paths this plan does not touch); `No local leaks found.` in `tests/test_local_leaks.py`; `dng999` presence in `tests/test_read_class_callers_refuse.py`. `violation(s).` and `no dangling citations` are asserted by no test. Every pinned substring is preserved by appending, never replacing. |
| F-6 | `tests/test_validator_nonsurveyable_dir.py` `test_control_surveyable_root_reports_nonzero_artifacts` | This test PINS THE DEFECT: its comment reads `# Backlog check human (countless success line preserved)` and it asserts `self.assertNotIn("0", proc_bl.stdout)`. With one item the new line `1 backlog items checked` happens to contain no `0`, so it would still pass, but only by accident (ten items would break it) and the comment would then be false. E-02 replaces it with a positive count assertion mirroring the specs assertion beside it. |
| F-7 | `tests/conformance_matrix.py` | As measured by `121j2r` F-10, this module collects zero tests and is imported by no test module; it lists `research check-refs` among its leaves. Keeping the in-place shape (OQ-01) leaves `semantic_facts_from_human`'s input shape unchanged for these leaves anyway. |
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

- [ ] V-01 validates E-01
  - Required evidence: the `backlog.run_check` diff; ACTUAL stdout and exit status of `aw backlog check --no-color` in (a) this repo, with `aw backlog check --agent`'s `checked` on the same tree showing the same integer (re-derive it, do not assume 948), (b) a throwaway repo with an empty `.aw/records/backlog/open/` showing `0 backlog items checked` and exit 0, (c) a throwaway repo with one malformed item showing the drift lines plus `finding(s) detected across 1 backlog items` and exit 1. Quote the single hoisted `summary` expression both branches read. Observations come from `backlog.run_check` via the CLI.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the diff of `tests/test_validator_nonsurveyable_dir.py` showing `assertNotIn("0", proc_bl.stdout)` replaced by a positive count assertion and the comment corrected; names and source of the two new backlog tests; bare `python3 -m pytest tests/test_agent_checked_count.py tests/test_validator_nonsurveyable_dir.py` summary line; and the FAILURE output of the two new tests against pre-E-01 `backlog.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the `attention.run` diff; ACTUAL stdout and exit status of `aw attention --check --no-color` in this repo with the `--json` `evidence[0].value.items` from the same tree showing the same integer; in an empty throwaway repo (`0 items checked, 0 violations`); in a tree with at least one drift record (drift lines plus count line, exit 1); and bare `aw attention --check` run outside any project showing the no-project branch line with `0 items checked`. Confirm in writing the excluded-tree and refusal paths were not edited. Observations come from `attention.run` via the CLI.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: names and source of the two new attention tests, the bare focused-run summary line, and their FAILURE output against pre-E-03 `attention.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the `artifact_core.py` and `research_refs.py` diff showing ONE scan loop with the uncounted function as `[0]` of the counted one; bare run of `tests/test_read_class_callers_refuse.py` and `tests/test_research_index.py` summary lines showing them still passing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the `run_check_refs` diff quoting the single `summary` expression; human, `--agent` and `--json` output of `aw research check-refs` on one unchanged tree (this repo) showing the same integer (human `across N files`, agent `checked`, json `data.checked`); an empty throwaway repo showing `no dangling citations across 0 files`, exit 0, and agent `"checked":0`; exit 1 unchanged on the dangling tree. Observations come from `research_refs.run_check_refs` via the CLI.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: names and source of the new research tests, the bare focused-run summary line, and their FAILURE output against pre-E-06 code.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: the `leak_sanitizer.py` diff showing `run_counted`, the `_counted` siblings, and `run` re-expressed over `run_counted`; bare `python3 -m pytest tests/test_leak_sanitizer.py tests/test_local_leaks.py tests/test_leak_sanitizer_machine_flags.py` summary line showing all still pass.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: the `leak_sanitizer.main` diff quoting the single `summary` expression; human (stderr), `--agent` and `--json` output of `aw sanitize` on this repo showing one integer; `aw sanitize --staged` and `aw sanitize --history --max-commits 3` human lines showing their units (`staged files`, `commits`); a throwaway repo with one committed harmless file showing `1 files checked` at exit 0 and with a planted home-path leak showing the findings block plus `across N files` at exit 1. Observations come from `leak_sanitizer.main` via the CLI.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: names and source of the new sanitize tests (showing the XDG isolation), the bare focused-run summary line, and their FAILURE output against pre-E-09 code.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: the CHANGELOG line, confirmed under `## 2.0.0 (pending)` with no em or en dash; the bare `python3 -m pytest` summary line and FAILED set from BEFORE the first source edit and AFTER the last, with an explicit statement whether the FAILED sets are identical; confirmation no flag was added to the bare invocation.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` and explicit human approval before execution. Execute task groups in order; groups 1 through 4 are independent of one another, group 5 runs last but its BEFORE suite baseline must be captured before the first source edit.

Execution contract: commit only the paths in `- Scope-Paths:` through `aw commit akhwp7 -- <paths>`; never `git add -A`, `-a`, or `--no-verify`; never push, tag, or release. Paste actual runner output for every test claim. Other agents may share this checkout: verify the staged set with `git diff --cached --name-only` before committing and unstage anything not yours path by path with `git restore --staged <path>`.

Keep every test-pinned substring (F-5) by APPENDING the count, never replacing the sentence. Do not change `leak_sanitizer.run`'s signature or `artifact_core.find_dangling_citations`'s return value. If a needed edit falls outside `- Scope-Paths:`, make it and justify it with `--scope-reason`.

Post-gate lifecycle: do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence with `Result: pass`. In a runner lane the runner owns finalize. Backlog `rolswj` carries no `- Blocks-Release:`; it reaches `done` once this plan is `executed`.

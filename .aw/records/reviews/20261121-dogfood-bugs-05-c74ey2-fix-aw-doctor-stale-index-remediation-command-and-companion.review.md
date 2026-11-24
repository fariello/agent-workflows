# Review findings: ipd c74ey2

- Subject-Id: c74ey2
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: opencode/claude-opus-5.5
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `34792ea0bcce89b5d82dbf628e0ada14c0e1ea77` in an isolated runner review-sweep lane worktree. The target plan `.aw/records/plans/pending/20261121-dogfood-bugs-05-c74ey2-fix-aw-doctor-stale-index-remediation-command-and-companion.ipd.md` was committed and clean at turn start (last changed in `a165d7aca` and `e571f1081`), so no pre-review snapshot commit was needed. It is Order 5 of Set `dogfood-bugs` (orchestrator `p2zmjs`), graduated from backlog `gqpgvm`, and carries `- Blocks-Release: next`. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings).

The central result: both defects the plan was written to fix are already gone on HEAD, removed by work that executed after the plan was authored on 2026-11-21. The plan was rewritten as a regression lock (tests that fail if either symptom returns), with a production change only if a new test fails. The plan's filename slug still says "stale-index"; renaming is a lifecycle act outside this review, so only the title and Short-Description were updated.

AW-TIER: standard

### Step T

1. No: as revised, the plan adds tests only. No CLI option, output format, schema, or spec changes. (As written, it changed `doctor` remediation text, a minor user-visible string.)
2. No: `agent_workflows/doctor.py` guards no private data, commit, worktree, merge, or sandbox path.
3. No: three E-items in one new test module plus one conditional production file.
4. Yes: `- Scope-Paths:` is present. Review replaced `tests/test_doctor_stale_index_companion.py` with `tests/test_doctor_companion_paths.py`.
5. Low: the revised plan changes no production code unless a test fails, and a test-only change is trivially reverted.

`AW-TIER: standard`

### Step R1

- Checked: `agent_workflows/doctor.py` (`_infer_artifact_type` 1297, `_normalize_rel_path` 1359, `build_remediation` 1394, call sites 577 and 626, `_categorize_drift` grouping 1891-1916, allowlist comments 763 and 766); `agent_workflows/artifact_core.py::repo_relative_posix` 553 and its records-root mapping 657-673; `agent_workflows/project_context.py::project_records_dir` 1406; `agent_workflows/check_engine.py::_finding_rel_path` 1161; `tests/test_companion_doctor_and_carriers.py` (helpers 53-130, companion README location assertion at 570-611); `tests/test_record_residual_helpers.py` 100-130; `tests/test_drift_rule_registration.py` 115-145; `tests/test_agy_runipd_cli.py:23` (imports a helper from a sibling test module). Git history: `972cff4cf` (`f1yjlx`), `a5707f414` (`w819as`), `419e01d67` (`6qh68x`), `5acca6ce5` (`kfnfji`), `493367069` (`pbdtss`), plan creation `6efa5700e`.
- Found F1: E-02 edits the `stale-index` branch of `doctor.build_remediation`, but `f1yjlx` (executed, code commit `972cff4cf`, 2026-11-23) deleted that branch, including `cmd = f"aw index {art_type}" if art_type else "aw index"` and `summary_fix="aw index"`. `rg -n "stale-index|aw index" agent_workflows/doctor.py` at HEAD prints only the two allowlist comments. A probe of `doctor.build_remediation(core.Drift(".aw/records/plans/INDEX.json", "check.stale-index-missing", "x"), Path("."))` at HEAD returned `command=None`, `summary_fix='inspect artifact frontmatter and schema conformity.'`. E-02 had nothing to edit.
- Found F2: E-01's premise (Step 0: `repo_relative_posix` "cannot relativize a path outside `repo_root`") is false. `artifact_core.py:657-673`, added by `5acca6ce5` on 2026-10-16, maps an absolute path inside `project_records_dir(repo_root)` to `.aw/records/<rel>`. A probe on a real companion install (built with `_install_companion_repo`) printed `normalize: plans/INDEX.json -> .aw/records/plans/INDEX.json | type: plans` and `categorize dir: .aw/records/plans`, and the same for `research`. The real cause of the `- .` grouping was that the deleted `check.stale-index-*` emitters (`plans_index.py`, `prompts_index.py`, `research_index.py`) set the drift location to the bare constant `INDEX.json` / `INDEX.md`, and `_categorize_drift` then fell back to `repo_root.rglob(fname)`, found nothing in the target, and returned `.`. A probe with a bare `INDEX.json` location still returns directory `.`, which is why case (e) and the declined deferral guard against a bare-filename emitter returning.
- Found F3: Step 0's conventions described code that no longer exists, and its metastore note said the rules "will eventually" be removed when `w819as`, `6qh68x`, and `f1yjlx` had already removed them. Fixed: Step 0 now records the measured state with commits and line numbers.

### Step R2

- Checked: the E/V bijection (E-01..E-03 to V-01..V-03, `Highest E allocated: 03`), `Depends on` order, Scope-Paths completeness, V-item evidence specificity, and consistency of the Goal, diagram, Proposed changes, and Required tests.
- Found F4: V-01 and V-02 demanded `git diff -- agent_workflows/doctor.py` showing changes that, after F1 and F2, must not be made; an honest executor could not satisfy them. Fixed: V-01 and V-02 demand per-case `PASSED` lines and the asserting source lines; V-03 demands `git diff --stat` and, only if `doctor.py` changed, the failing run before the fix.
- Found F5: Required tests used the glob `tests/test_doctor*.py`, which would also match the new module, and passed no `-o addopts=""`, so `-q` defaults hid per-test lines. The new test file name embedded the deleted rule name. Fixed: a precise `-v` command for the new module, a named list for neighbours, and the file `tests/test_doctor_companion_paths.py`.

### Step R3

- Checked (short form): the revised plan adds test code that builds temp-directory repositories and drives `aw doctor` in-process. It adds no subprocess with user input, no network call, and no credential handling. Cases (f) and (g) assert that no output contains the absolute companion path, which strengthens the leak guarantee.
- No security finding.

### Step R4

- Checked: correctness of each test case against HEAD (all seven scenarios were run by hand at `34792ea0b` through scratch probes and produced the expected outcomes: no INDEX, `stale-index`, or bare `aw index` text in human or `--agent` output; plan finding location `.aw/records/plans/pending/20261121-zzprobe-01-q9q9q9-probe.ipd.md`; research finding `.aw/records/research/badname.md`; no absolute companion path); test cost (each companion install runs `aw install` in-process, comparable to the existing `tests/test_companion_doctor_and_carriers.py` cases); release gate (`- Blocks-Release: next` and `- From-Backlog: gqpgvm` are kept, so executing this plan hands off `gqpgvm`'s gate).
- Found F6: the title, Short-Description, Concern, Goal, and diagram all described fixing deleted code. Fixed: each now states that both symptoms are already fixed on HEAD and that the plan locks them in.
- Found F7: orchestrator `p2zmjs` describes this child's outcome as `doctor.py` code changes (E-05 expected outcome, child table row 05, success criterion at line 98). That file is outside this plan's Scope-Paths. Deferred to `p2zmjs` with a `Carrier:` line.

### Proofreading

Checked the plan against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
| --- | --- | --- | --- |
| Title, Short-Description | Fix stale-index remediation and companion paths | Lock in the fixes with regression tests | F6 |
| Concern, Scope, Scope-Paths | Code edits to three `doctor.py` functions; test file `test_doctor_stale_index_companion.py` | Symptoms already fixed; regression tests in `test_doctor_companion_paths.py`; `doctor.py` conditional | F1, F2, F5 |
| Goal and diagram | Diagram of a mapping to add and a branch to edit | Two numbered outcomes, a definition of companion install, and a diagram of the existing mapping and the deleted emitters | F2, F6; requirement 12 |
| E-01..E-03 | Edit `_normalize_rel_path`, edit the deleted branch, add tests | Function-level tests (a)-(d), end-to-end tests (e)-(g), conditional fix | F1, F2 |
| Step 0 | False claims about current code | Measured state with commits, lines, and the real root cause | F2, F3 |
| Findings DF-05 | Area named the functions | Notes the fixing commits | F6 |
| Proposed changes, Scope check, Required tests, Spec sync | Code-change list; "none" claims; glob command | Test-first list; accurate scope; precise commands; spec `4sd62s` 4.5 note | F4, F5, F7 |
| Deferred | One carrier | Added a declined bare-filename search and the `p2zmjs` wording carrier | F2, F7 |
| V-01..V-03 | Demanded diffs that must not exist | Per-case `PASSED` lines, asserting source lines, conditional diff evidence | F4 |
| Approval gate | Bare cohesion line | Cohesion reason | Followability |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
| --- | --- | --- | --- | --- | --- |

### Step S5

- Checked: the plan has no open questions. The judgement calls this review made are recorded in Decisions D1-D3 and are reversible. Whether to execute this plan as a regression lock or retire it to `superseded/` is a choice the human makes at approval (D1); nothing needs an answer before approval.

### Pass 2

- Re-read the revised plan end to end. The seven cases are named identically in E-01, E-02, E-03, and V-01..V-03; the Goal, diagram, Step 0, and Proposed changes agree that no production change is expected. `aw ipd lint --phase review-finalize --agent` returned `clean` (exit 0; info only: `IPD-Z602`, `IPD-Z603`, `IPD-C801`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | HIGH | IN-SCOPE | R1 / Stale target | `972cff4cf` (`f1yjlx`) deleted the `stale-index` branch of `doctor.build_remediation`; `rg -n "stale-index\|aw index" agent_workflows/doctor.py` prints only lines 763 and 766 | E-02 edits code that no longer exists. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-02 replaced with end-to-end regression tests. |
| F2 | HIGH | IN-SCOPE | R1 / False premise | `agent_workflows/artifact_core.py:657-673` (`5acca6ce5`); probe output `.aw/records/plans/INDEX.json`, dir `.aw/records/plans` | `_normalize_rel_path` already maps companion paths; the `- .` grouping came from bare-filename locations in the deleted emitters. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-01 replaced with function-level regression tests; root cause recorded in Step 0. |
| F3 | MEDIUM | IN-SCOPE | R1 / Accuracy | plan Step 0 bullets 1, 2, 4 | Step 0 described deleted code and future work that had already executed. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Step 0 rewritten from measurements. |
| F4 | MEDIUM | IN-SCOPE | R2 / Evidence | plan V-01, V-02 demanded `git diff -- agent_workflows/doctor.py` | V-items demanded diffs the revised plan must not produce. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | V-items demand per-case results and conditional diff evidence. |
| F5 | LOW | IN-SCOPE | R2 / Commands | plan Required tests glob `tests/test_doctor*.py`; no `-o addopts=""` | The test command was imprecise and hid per-test lines; the file name used a deleted rule name. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Precise commands; file `tests/test_doctor_companion_paths.py`. |
| F6 | LOW | IN-SCOPE | R4 / Accuracy | plan title, Short-Description, Concern, Goal, diagram | The framing described fixing deleted code. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Framing states the regression-lock purpose. |
| F7 | LOW | OUT-OF-SCOPE | R4 / Cross-plan consistency | `p2zmjs` E-05 expected outcome, child table row 05, line 98 | The orchestrator describes this child as `doctor.py` code changes. | C:Low;U:Low;S:Low;F:Low;Overall:Low | DEFERRED | Carrier `p2zmjs` recorded in the plan's Deferred section. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D1 | Retire the plan as superseded, or keep it? | Keep it as a regression lock | Retire to `superseded/` (by `f1yjlx`, `w819as`, `6qh68x`) and close `gqpgvm` with `--evidence` | No test pins either symptom today, and a bare-filename emitter would bring `- .` back silently; keeping the plan also hands off `gqpgvm`'s release gate by the normal path. The human may still retire it at approval. | yes |
| D2 | Change `_categorize_drift` to search the companion root for bare filenames? | No; `Carrier-Declined` | Add the search | No live emitter passes a bare filename for a companion record (probes at HEAD) | yes |
| D3 | Where do the tests get a companion install? | Import `_install_companion_repo`, `_patched_env`, `_run_aw_inproc` from `tests/test_companion_doctor_and_carriers.py` | Copy the helpers | Sibling-module helper imports are an existing convention (`tests/test_agy_runipd_cli.py:23`) | yes |

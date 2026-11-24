# Review findings: ipd p0hq1k

- Subject-Id: p0hq1k
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: opencode/claude-opus-5.5
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at local HEAD `341d7137a` (the `osq7nu` lane integration) in an isolated runner review-sweep lane worktree. The target plan `.aw/records/plans/pending/20261121-dogfood-bugs-04-p0hq1k-resolve-companion-records-paths-in-check-scope-path-target-s.ipd.md` was committed and clean at turn start, so no pre-review snapshot commit was needed. It is Order 4 of Set `dogfood-bugs`, graduated from backlog `dv9ses` (`Work-Kind: bug`, `Status: graduated`), and carries `- Blocks-Release: next`. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings).

The central result: the diagnosis is correct and the defect reproduces at HEAD, but the planned fix was incomplete. The declared-move check in the same function compares only repo-relative paths, so in companion mode a plan declaring a move pair would still be reported (F1). The plan also named a test module that does not test this code, so its validation could not show a regression (F2).

AW-TIER: standard

### Step T

- Checked: the five tier questions in `steps/t-tier.md`.

1. No: no flag, reason code, or spec text changes. One CHANGELOG bullet is added at review.
2. Yes, narrowly: `check.scope-path-target-stale` feeds `aw check` exit codes and the runner's dispatch refusal, but the change only removes false positives and absolute paths.
3. No: four E-items after review, four work Scope-Paths.
4. Yes: `- Scope-Paths:` is present; review added `CHANGELOG.md`.
5. Low: one predicate in `check_engine.py`, covered by 25 existing tests plus the new module.

`AW-TIER: standard`

### Step R1

- Checked: `agent_workflows/check_engine.py::stale_record_scope_paths` (10336-10436: `target = repo_root / entry` at 10371, the basename fallback that calls `project_records_dir` at 10389-10401, the `dparot` `hit_rels` set at 10403-10410, and the `hit.as_posix()` fallbacks at 10422 and 10430); `check_scope_path_target_stale` (10439-10488); `agent_workflows/status_set.py::detect_artifact_type`; `agent_workflows/project_context.py::project_records_dir`; `agent_workflows/artifact_core.py::repo_relative_posix`; `agent_workflows/runner_shared.py::_logical_record_file_rel` and the dispatch refusal that calls `stale_record_scope_paths`; spec `25kzda` section 5 (declared-move rule); `docs/cli-output-contract.md` "Path Sanitization and Leak Posture".
- Reproduced with `tests/test_companion_doctor_and_carriers.py::_provision_lightweight_companion_repo`: an existing companion plan is `moved` with an absolute `resolved`; after a move it is `moved-terminal` with an absolute `resolved`; `aw check --dir <target> --agent` exits 1 and prints the temporary directory in its `next` field.
- Found F1: a plan declaring both `.aw/records/plans/pending/<file>` and `.aw/records/plans/executed/<file>` was reported twice as `moved-terminal` in companion mode. `hit_rels` is built with `relative_to(repo_root.resolve())` and drops every hit outside `repo_root`, so the `dparot` declared-pair exemption never matches. The original E-02 changed only the reported path. Fixed: E-02 adds `_logical_scope_rel` and uses it for `hit_rels` as well as both reported-path sites.
- Found F3: E-01 asked to pass "`records_dir` context when detecting artifact type". `detect_artifact_type` takes no such argument, and it already returns `plans` for the companion entry from the `.ipd.md` facet (measured). Fixed: E-01 step 3 says to leave that call unchanged.
- Found F4: the original E-02 fell back to repo-relative formatting and did not say what to do for a hit outside both roots, which is the case that leaked. Fixed: the third branch uses `_core.repo_relative_posix`, which returns a records segment or bare name and never an absolute path.
- Noted: `check.scope-path-target-stale` runs only in the full sweep; `aw check plans --agent` on the reproduction reported nothing. Recorded in the plan's conventions so the executor tests with `aw check`.

### Step R2

- Checked: the E/V bijection, `Depends on` edges, Scope-Paths, the right-sizing rule, test placement, and whether each V-item demands concrete evidence.
- Found F2: E-03 and V-03 named `tests/test_check_engine.py`, which contains no reference to `stale_record_scope_paths` or `check.scope-path-target-stale` (`grep -c` returned 0). The real coverage is `tests/test_scope_path_target_stale.py` (25 tests, `25 passed in 1.89s` under `-n 0`) and `tests/test_scope_paths_status_agnostic.py`. Case (d), "standard repository-backed behavior is unchanged", was vague. Fixed: E-03 relies on those modules for repository mode; V-03 runs them.
- Found F5: E-03 did not say how to build a companion-mode repository or call the check, and V-03 did not show that the new tests fail without the fix. Fixed: E-03 names `_provision_lightweight_companion_repo`, `_patched_env`, and `_run_aw_inproc`, lists cases (a) to (e) with exact assertions, and V-03 requires a run at the base commit in a throwaway worktree showing (a) to (d) failing. Provisioning measured 0.03s and one in-process `aw check` 0.2s, so no slow-allowlist entry is needed.
- Found F6: no CHANGELOG entry for a user-visible fix, unlike siblings `gftvh6`, `5q8whb`, and `d8b9rp`. Fixed: new E-04 and V-04 add one `- Fixed:` bullet; `CHANGELOG.md` added to Scope-Paths.

### Step R3

- Checked (short form): the change removes absolute paths from findings, which tightens leak containment. No new input is parsed, and no subprocess, network, or credential is involved. `aw sanitize --agent` at HEAD returned `clean` (7176 files checked).
- No security finding.

### Step R4

- Checked: the runner's dispatch refusal (`runner_shared.py`) reads `StaleScopePath.resolved` and gets the same relative paths without its own change. The orchestrator `p2zmjs` description of this child (child table row 04, E-04, and its V-03 cross-reference) still holds after the revisions.

### Step S5

- Checked: no open questions in the plan. The two judgement calls this review made are recorded as D1 and D2 and are reversible. No question needs a human answer before approval.

### Pass 2

- Re-read the revised plan end to end. E-01 to E-04 map one-to-one to V-01 to V-04, `Highest E allocated: 04`, and the flowchart shows the declared-move branch and the three rendering branches. `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings) after the edits.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | HIGH | IN-SCOPE | R1 / Correctness | `agent_workflows/check_engine.py:10403-10410`; probe: declared pair reported twice as `moved-terminal` | The declared-move check drops hits outside `repo_root`, so companion move pairs stay reported after the planned fix. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-02 renders `hit_rels` through `_logical_scope_rel`; E-03 case (c). |
| F2 | MEDIUM | IN-SCOPE | R2 / Validation target | `grep -c stale_record_scope_paths tests/test_check_engine.py` -> 0; `tests/test_scope_path_target_stale.py` 25 passed | Validation named a module that does not test this code and omitted the two that do. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | V-03 runs `test_scope_path_target_stale.py` and `test_scope_paths_status_agnostic.py`. |
| F3 | LOW | IN-SCOPE | R1 / Nonexistent parameter | `agent_workflows/status_set.py::detect_artifact_type(path, repo_root)`; probe returned `plans` | E-01 asked to pass `records_dir` to a function that takes none and needs none. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-01 step 3 leaves the call unchanged. |
| F4 | MEDIUM | IN-SCOPE | R1 / Leak fallback | `check_engine.py:10422,10430` `hit.as_posix()`; `artifact_core.py::repo_relative_posix` | The plan did not say how to render a hit outside both roots, the case that leaks. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-02 third branch uses `_core.repo_relative_posix`; E-03 case (e). |
| F5 | MEDIUM | IN-SCOPE | R2 / Test executability | `tests/test_companion_doctor_and_carriers.py::_provision_lightweight_companion_repo`, `_run_aw_inproc` | Test setup and exact assertions were unstated, and nothing showed the tests fail without the fix. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-03 names fixtures and cases (a) to (e); V-03 demands a failing run at the base commit. |
| F6 | LOW | IN-SCOPE | R2 / User docs | Siblings `gftvh6`, `5q8whb`, `d8b9rp` each add a `- Fixed:` bullet | A user-visible fix had no CHANGELOG entry. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | New E-04 and V-04; `CHANGELOG.md` in Scope-Paths. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D1 | Reuse `runner_shared._logical_record_file_rel` or add a local helper? | Local `_logical_scope_rel` in `check_engine.py` | Import from `runner_shared` | `check_engine` should not import the runner module; the helper is about ten lines and also needs the leak-free third branch the runner helper lacks | yes |
| D2 | Add a CHANGELOG bullet? | Yes, one `- Fixed:` bullet | No user-facing note | The fix changes `aw check` output users see; sibling plans in the same Set document theirs | yes |

### Proofreading

Checked the plan against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
| --- | --- | --- | --- |
| Front matter | `Highest E allocated: 03`; three Scope-Paths | `04`; `CHANGELOG.md` added | F6 |
| Scope | Existence and formatting only | Names the declared-move comparison and the CHANGELOG bullet | F1, F6 |
| Goal flowchart | Formatting only for hits under `records_dir` | Three rendering branches and the declared-move decision | F1, F4; requirement 12 |
| E-01 | `removeprefix`; pass `records_dir` to type detection | Numbered steps; slice; leave type detection unchanged | F3 |
| E-02 | Reformat reported path only | `_logical_scope_rel` used for `hit_rels` and both reported sites | F1, F4 |
| E-03 | Four loosely stated cases; wrong module | Fixtures, five exact cases, existing modules for repository mode | F2, F5 |
| New E-04, V-04 | none | One `- Fixed:` CHANGELOG bullet | F6 |
| Conventions, Findings | No reproduction; no output-contract citation | DF-03a reproduction; full-sweep-only note; contract citation | F1, F4 |
| Scope check, Spec sync, Required tests | "N/A"; wrong test module | Spec `25kzda` rationale; corrected test command | F2 |
| V-01 to V-03 | Generic diffs and test output | Named hunks, `PASSED` lines per case, failing run at base | F2, F5 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
| --- | --- | --- | --- | --- | --- |

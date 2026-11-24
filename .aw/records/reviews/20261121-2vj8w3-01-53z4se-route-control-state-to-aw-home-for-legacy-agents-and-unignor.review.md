# Review findings: plan 53z4se

- Subject-Id: 53z4se
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `9f976d7cf` in a runner review-sweep lane worktree (non-interactive). The plan was committed and unmodified (last plan commit `65355760f`), so no pre-review snapshot was taken. `aw ipd lint --phase author` was clean before revisions (0 findings) and after them (1 advisory `IPD-Z603` info, 0 errors, 0 warnings). Reviewed against backlog `2vj8w3`, `agent_workflows/ipd_lifecycle.py` (`clean_delta_control_root`, `checkout_control_root`, `clear_checkout_control_root_cache`, `control_state_dir`, `_git`), `agent_workflows/project_context.py` (`ProjectContextError`, `checkout_main_root`, `_is_project_marker`, `_stored_physical_classes`, `has_stored_records_placement`, `resolve_project_context` records-backend resolution), `agent_workflows/project_schema.py` (`RecordsBackend`, `PrecedenceLevel`), `agent_workflows/checkup.py` (`CHECKUP_STATE_REL`, `checkup_dir`, `read_checkup_record`, `run_checkup_cli`), `agent_workflows/work_cmd.py` (`_WORK_STATE_SUBDIR`, `_work_dir`), `agent_workflows/runner_shared.py` (`SUITE_BASELINE_SUBDIR`, `suite_baseline_checkout_path`, `runs_repo_root`), `agent_workflows/doctor.py` (`inspect_repo` checkup evidence), `conftest.py` (environment sandbox, core tier), the tests that write in-repo `.aw/state/`, and spec `25kzda`.

`AW-TIER: standard`
`AW-REVIEW: DONE`

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| E-01 step 1, git probe | `check-ignore` on `.aw/state/checkup/last.json` | `check-ignore` on `.aw/state/`, with the reason and the measured git result | PR-001 |
| E-01 step 1, new bullet | No caching | Bounded memo keyed by anchor, cleared by `clear_checkout_control_root_cache()` | PR-004 |
| E-01 step 2, Condition B | `rec_source != builtin_defaults`; enums with no module | `rec_source in (project_durable_config, machine_local_binding)`; import from `agent_workflows.project_schema`; reason | PR-002, PR-003 |
| Goal mermaid node F, note under diagram | "not builtin_defaults" | Names the two allowed sources; notes that `G` probes the directory | Consistency with PR-001, PR-002 |
| E-03 test 1 | `doctor.inspect_repo(repo)` "reads the saved record" | Asserts on the `checkup` evidence entry; adds `work` and `suite-baselines` routing asserts | PR-005 |
| E-03 test 5 | Three ignore variants | Adds the subtree-only `/.aw/state/checkup/` variant | PR-001 |
| E-03 test 6 | Tracked and unconfigured controls only | Adds a user-level `default_records_backend` control and cache clearing in setUp/tearDown | PR-002, PR-004 |
| E-03 expected outcome, E-04, Required tests | Five regression files | Adds `tests/test_resolve_plan_path_typed.py` and `tests/test_legacy_finalize.py` | PR-006 |
| Project conventions | No suite-baseline consequence; Condition B rationale used `!= builtin_defaults` | States the suite-baseline worktree move; rationale names the stored-placement predicate | PR-002, PR-006 |
| Proposed changes item 3, V-01 | Old test list | Names the two new test variants | Bijection with revised E-03 |
| Spec / documentation sync | "No separate specification" with no evidence | Cites spec `25kzda` and why it stays unamended | Verifiable citation |

#### Issues

None.

### Step T

1. Yes: `ipd_lifecycle.control_state_dir` is shared by `checkup.checkup_dir`, `work_cmd._work_dir`, and `runner_shared.suite_baseline_checkout_path`, so the change moves where three kinds of runtime state are written.
2. No.
3. No: 4 E-items in 4 task groups, 3 Scope-Paths.
4. Yes: no `.spec.md` path in Scope-Paths.
5. Medium: a wrong routing predicate either leaves state committable (the bug) or silently moves state for repositories that never asked for it, and the suite-baseline worktree location moves with it.

Tier: standard.

### Step R1

- Checked: every cited symbol exists with the claimed behavior. `control_state_dir` reroutes only when `clean_delta_control_root` is not `None`. `checkout_main_root` is pure and spawns no subprocess. `_is_project_marker` requires `system`/`records`/`config` for `.aw` and `workflows`/`plans`/`docs`/`prompts`/`comms`/`backlog` for `.agents`. `resolve_project_context` resolves `records_backend` through explicit flag, machine-local binding, durable config, preset, named profile, user global default, then built-in `home`. `checkup.run_checkup_cli` relativizes `Saved record:` with `clean_delta_control_root` only. `doctor.inspect_repo` reads `checkup.read_checkup_record` and appends an `Evidence(key="checkup")`.
- The ignore probe used a checkup-only path although the accessor serves three subtrees (PR-001).
- Condition B's `!= builtin_defaults` test also matches `global_defaults` and `named_global_profile` (PR-002).
- `RecordsBackend` and `PrecedenceLevel` are defined in `agent_workflows/project_schema.py`, not `project_context` (PR-003).

### Step R2

- Checked: E/V bijection 4/4; Scope-Paths cover every edited or created file; `Item-Dependencies: none` is correct for Order 1 of a one-child Set; each V-item demands pasted diff and runner output. The backlog `2vj8w3` acceptance criteria (no unignored state in a legacy repo; clean `git status --porcelain`) map to E-03 tests 1, 2, and 4.
- E-03 test 1 asserted that `doctor.inspect_repo` "reads the saved record" with no observable to check (PR-005).
- `tests/test_resolve_plan_path_typed.py` writes in-repo `.aw/state/suite-baselines/` fixtures and `tests/test_legacy_finalize.py` mixes `.agents/` and `.aw/` trees; neither was in the regression list (PR-006).

### Step R3

- Checked: the change only moves where gitignored-by-intent runtime state is written; it creates no files in the target checkout, deletes nothing, and edits no ignore files. `git check-ignore` runs through the shared `_git` wrapper with a fixed argument list. The `Saved record:` display stops printing an absolute machine path, which reduces local-path leakage. `--agent` `record_path` stays raw by design (declined in Deferred).
- No new security finding.

### Step R4

- Checked: A data model: no schema change. C reuses `clean_delta_control_root`, `checkout_main_root`, `_is_project_marker`, and `resolve_project_context`; leaves `clean_delta_control_root` and `checkout_control_root` unchanged for `worktree_lease` and `oc_runipd`. D invariants: tracked canonical repos and unconfigured fixtures keep `<repo>/.aw/state/`, each mapped to an E-03 test. E tests drive `cli.main(["checkup", ...])`, `checkup.perform_checkup`, and the accessors (P16 compliant). F smallest design: writing `.aw/.gitignore` during checkup is correctly declined because it would itself add `?? .aw/`. Performance: an uncached `git check-ignore` per call would run several times per command (PR-004). Spec sync: spec `25kzda` names the default in-repo path for the red-CI gate; the gate contract is unchanged, so no amendment is needed.
- Moving suite-baseline worktrees to AW_HOME for legacy and Condition-B repositories was unstated (PR-006).

### Step S5

- Checked: no question needs a human. The routing predicate, the probe path, and the provenance set are all resolved from repository evidence (`project_context._stored_physical_classes` precedent and a measured `git check-ignore` run).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | MEDIUM | IN-SCOPE | D invariant (correctness) | `work_cmd._work_dir` and `runner_shared.suite_baseline_checkout_path` both call `ipd_lifecycle.control_state_dir`; scratch repo with root `.gitignore` `/.aw/state/checkup/`: `check-ignore .aw/state/checkup/last.json` rc 0, `.aw/state/` rc 1, `.aw/state/work/x/l.json` rc 1 (git 2.43) | Probing `.aw/state/checkup/last.json` lets a checkup-only ignore rule mark the whole state tree as protected, so `work/` leases and suite-baseline worktrees would still land unignored in the checkout. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 probes `.aw/state/` (rc 0 for `.aw/state/` and `.aw/state/*` rules); E-03 test 5 adds the subtree-only variant. |
| PR-002 | MEDIUM | IN-SCOPE | C compatibility | `project_context.resolve_project_context` sets `GLOBAL_DEFAULTS` for `user_cfg_data["default_records_backend"]` and `NAMED_GLOBAL_PROFILE` for a profile; `project_context._stored_physical_classes` treats the backend as stored only for `project_durable_config` or `machine_local_binding` | `rec_source != builtin_defaults` would let one user-level default reroute every unconfigured `.aw/` repository and test fixture on the machine. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Condition B requires `project_durable_config` or `machine_local_binding`; E-03 test 6 adds a `default_records_backend` control that must not reroute. |
| PR-003 | LOW | IN-SCOPE | G executability | `agent_workflows/project_schema.py` `class RecordsBackend`, `class PrecedenceLevel(str, Enum)` | The plan used both enums without naming their module; the natural guess, `project_context`, re-exports them only incidentally. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 names `agent_workflows.project_schema` and a lazy import. |
| PR-004 | LOW | IN-SCOPE | Performance | `checkup.checkup_dir` reached by record path, lock path, read, write, and display; `ipd_lifecycle._CONTROL_ROOT_CACHE` precedent; `clear_checkout_control_root_cache` | An uncached `git check-ignore` subprocess would run on every `control_state_dir` call in a Condition-B repository. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 memoizes per anchor with a bounded dict cleared by `clear_checkout_control_root_cache()`; E-03 clears it in setUp/tearDown. |
| PR-005 | LOW | IN-SCOPE | E testing | `doctor.inspect_repo` calls `_chk.read_checkup_record(repo_root)` and appends `Evidence(key="checkup", value={"summary", "warning", "record"})` | "`doctor.inspect_repo(repo)` reads the saved record" named no observable, so the assertion could not be written as stated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 test 1 asserts the `checkup` evidence entry's `value["record"]` is not `None`, and adds `work`/`suite-baselines` routing asserts. |
| PR-006 | LOW | IN-SCOPE | C compatibility | `runner_shared.suite_baseline_checkout_path` returns `control_state_dir(...)` and creates a detached `git worktree` there; `tests/test_resolve_plan_path_typed.py` writes `.aw/state/suite-baselines/base1`; `tests/test_legacy_finalize.py` uses `.agents/` and `.aw/` trees | The suite-baseline worktree moves to AW_HOME for legacy and Condition-B repositories, and two affected test files were missing from the regression list. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Project conventions states the move and why it is intended; E-03, E-04, and Required tests add both test files. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Which path proves `.aw/state/` is ignored? | The `.aw/state/` directory itself | Per-parts probe (rejected: one accessor, one answer, and a partial rule still leaves sibling subtrees unignored) | Measured `git check-ignore` results in PR-001 | yes |
| D-2 | Which `records_backend` sources count as configured `home`? | `project_durable_config` and `machine_local_binding` | Anything but `builtin_defaults` (rejected: user-level defaults reroute every repository) | `project_context._stored_physical_classes` | yes |
| D-3 | Review tier | standard | simple | Step T answers 1 yes, 5 medium | yes |

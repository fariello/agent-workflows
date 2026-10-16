# Review findings: plan t1fri2

- Subject-Id: t1fri2
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `01cee44b9`. The plan was committed and byte-identical to the sealed lane input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean` before edits and `--phase review-finalize --agent` `clean` after. Child plan.

Verified:
- `work_cmd.run_work_begin` carries the `3d80673c1` guard (`except ValueError: plan_rel = str(plan_path)`); `git show 3d80673c1` matches F-01/F-02; `nwporz` (executed) lists `agent_workflows/work_cmd.py` under its scope reconciliation.
- `work_cmd._lease_path` -> `_work_dir` -> `ipd_lifecycle.control_state_dir`; only writer of the lease `plan_path` is `run_work_begin` (`"plan_path"` grep: `ipd_lifecycle` receipt and `runner_shared` readers are unrelated).
- Scratch probes under `/tmp` with temp HOME/AW_HOME: completely-clean-target and local-only both exit 0 with absolute `plan_path`; default install writes a relative path at `<repo>/.aw/state/work/<id6>/work-lease.json`.
- `aw commit` fallback `plan_rel = plan_path.name` exists in `work_cmd` as the plan states.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E coverage | plan Concern names `completely-clean-target` and `local-only`; `agent_workflows/project_schema.py` `Preset.LOCAL_ONLY` placements are all `HOME_UNTRACKED` | E-02 tested only `completely-clean-target` although the bug and the CHANGELOG line name both presets. | all Low | FIXED | E-02 and V-02 cover both presets; reproduction recorded for both. |
| PR-002 | MEDIUM | IN-SCOPE | E evidence honesty | `pathlib` on POSIX: `str(plan_path)` contains no backslash | The no-backslash assertion cannot fail on Linux with or without E-01, so it does not pin E-01; the plan implied the test locks the normalization. | all Low | FIXED | E-04 states the limit and scopes the mutation proof to the guard. |
| PR-003 | LOW | IN-SCOPE | G executability | `tests/test_clean_target_zero_delta_e2e.py` ipd scaffold step passes `--title`; probe lease paths | E-02/E-03 left the lease location to globbing and omitted the required scaffold flags; the measured paths are deterministic. | all Low | FIXED | Exact lease paths and scaffold/dependency commands named; E-03 also asserts no lease under AW_HOME. |
| PR-004 | LOW | IN-SCOPE | G right-sizing | plan E-04 bundled mutation proof with CHANGELOG | Two unrelated deliverables in one E-item, and the final regression gates sat only in V-04. | all Low | FIXED | Split into E-04 (mutation) and new E-05/V-05 (CHANGELOG, dash scan, narrowed and bare suites). |
| PR-005 | LOW | UNDER-SCOPE | D anti-regression | `tests/test_work_gate_severity.py` asserts `work begin` lease creation at `.aw/state/work/<id>/work-lease.json` | Existing `work begin` lease tests were not in the validation set; new module is outside `pyproject.toml` `testpaths`, so the bare gate does not run it. | all Low | FIXED | E-05 runs both modules plus the e2e explicitly and says why. |
| PR-006 | LOW | UNDER-SCOPE | G execution contract | gate section; OQ-01 `Owner: none` | No scope-fence declaration; resolved OQ had `Owner: none`. | all Low | FIXED | Added SCOPE FENCE paragraph; owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the plan add a Windows-path unit test so E-01 is pinned? | No; state the limit honestly. | Unit-test with a mocked `PureWindowsPath` (REJECTED: `run_work_begin` takes real `Path`s; it would pin structure, not behavior). | AGENTS.md TEST OUTCOMES rule; `work_cmd.run_work_begin`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.

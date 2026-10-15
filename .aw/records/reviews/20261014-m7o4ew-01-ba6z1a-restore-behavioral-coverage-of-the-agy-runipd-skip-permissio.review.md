# Review findings: plan ba6z1a

- Subject-Id: ba6z1a
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `9f4e0f477` in an isolated review lane. The plan was committed and unchanged (`b671b2a90`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified by driving the code:
- `agy_runipd.build_parser()`: no flag gives `True`, `--no-dangerously-skip-permissions` gives `False`, and both `--dangerous` and `--dangerously-skip-permissions` give `True`.
- `run_agy_turn` with `tests.test_turn_bounds._setup_launcher_run_dir`, `options["agy"] = sys.executable`, and a recording `Popen` fake made 5 Popen calls: 4 `git config --get ...` calls and 1 agy launch. The agy argv held the flag for absent and True options and omitted it for False.
- `runner_shared.probe_argv(host="agy")` carries the same `options.get("dangerously_skip_permissions", True)` fallback. The flag is present for `{}` and absent for `False`.
- `tests/test_runner_shared.VerificationPolarityTests.frozen_options("agy_runipd", ...)` drove the real `initialize_run` with `prepare_only` and an isolated `XDG_CONFIG_HOME`. It returned `True` with no flag and `False` with the opt-out, with no network or host binary.
- The deleted `TestAntigravitySkipPermissionsDefaultIsPinned` content matches the plan's description in `git show 19313eed^:tests/test_lane_permission_posture.py`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | D. Anti-regression (second consumer) | `runner_shared.probe_argv` agy branch `if options.get("dangerously_skip_permissions", True):` | The frozen option has a second launch site, the orchestrator coverage probe. A flip there would hang the unattended probe, and nothing guards it. The plan claimed no under-scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-05/V-05, a probe-argv test for the absent, True, and False cases. Non-vacuity now flips both fallbacks. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing (vacuity risk) | review probe: 5 `Popen` calls, 4 `git config --get`, 1 agy | E-02 did not say which recorded argv to inspect. A "contains" check across all calls, or on the wrong call, is fragile or vacuous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now selects the single argv whose `argv[0] == resolve_agy(sys.executable)` and asserts exactly one exists. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing (fixture, isolation, fallback) | `tests/test_runner_shared.py` `VerificationPolarityTests.frozen_options`; `runner_profiles.STORE_NAME` | E-03 pointed at an `orchestrator_retirement` Namespace-built fixture rather than the real parser. It lacked `XDG_CONFIG_HOME` isolation, so an ambient runner profile could change frozen options. It also allowed a Namespace fallback that recreates the vacuous test OQ-01 rejects. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now follows the demonstrated `frozen_options` flow (real parser, isolated config home, `load_state`), adds the opt-out `False` contrast, and drops the fallback because feasibility was demonstrated. |
| PR-004 | LOW | IN-SCOPE | G. Executability (ordering) | Required tests "Non-vacuity ... revert and show `git diff --stat` empty apart from the E-04 comment" | The non-vacuity revert of `agy_runipd.py` was not ordered relative to the E-04 comment edit, so a `git checkout` revert could discard E-04. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Non-vacuity is now performed BEFORE E-04, with the revert command named and a clean diff required. E-04 depends on E-02, E-03, and E-05. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked `aw ipd begin`, the paste-output honesty rule, never `-a`/`--no-verify`, a staged-set check, a scope fence, and runner-conditional finalize. It said "move the plan ... (`aw ipd finalize`)" unconditionally. The OQ owner was `none`, and the V-04 full-suite bar was absolute. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate. The OQ owner is now `plan author`, and the V-04 bar compares failures to base by name. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Guard `runner_shared.probe_argv` too, although the backlog names only `build_parser`? | Yes, as E-05 in the same new module | Leave it unguarded (a flip there hangs the unattended probe the same way) | `runner_shared.probe_argv` agy branch; backlog `m7o4ew` intent ("silent flip ... deadlock") | yes |
| D-2 | Keep the Namespace fallback in E-03? | Remove it | Keep it (vacuous `getattr`, rejected by OQ-01) | review demonstration via `VerificationPolarityTests.frozen_options` | yes |

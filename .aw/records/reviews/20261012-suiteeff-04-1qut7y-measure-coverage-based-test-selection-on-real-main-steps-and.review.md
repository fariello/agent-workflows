# Review findings: plan 1qut7y

- Subject-Id: 1qut7y
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `d3f283b0f` in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean, with one info-level `IPD-Z602` on E-03, before semantic review. `--phase review-finalize` was clean after revisions, with info-level `IPD-Z602` notes on the enumerated E-03 and E-06.

Re-verified:
- `agent_workflows/suite_cache.py` and `tests/test_suite_select.py` do not exist yet. Order 02 (`0o0wt2`) and Order 03 (`xvm6no`) are `reviewed`, not executed, and their reviewed text supplies `suite_key`, `run_full_suite`, `aw suite`, E-09's refusal, and `suite_slot`.
- `pyproject.toml`: `requires-python = ">=3.9"`; `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`. The `[dependency-groups] dev` comment says it "Mirrors the `test` extra; kept in sync with it". pytest-testmon 2.2.0 wheel metadata reads `Requires-Python: >=3.10`.
- 174 first-parent `main` commits since 2026-10-01 touch `agent_workflows` or `tests`.
- `runner_shared.py` 43,720 lines; 186 `agent_workflows/*.py` modules; `host_sandbox_profile` "the GIT COMMON DIRECTORY is READ-ONLY".
- `build_prompt` carries the FOREGROUND paragraph that Order 02 E-07 extends.
- Feasibility probes ran in a throwaway venv under `/tmp/opencode` with pytest 9.1.1, xdist 3.8.0, testmon 2.2.0 and coverage 7.16.2 on Python 3.14.6. The fixture was a 4-test repo under the ignored `.aw/state/pr4/` (deleted afterwards), with `addopts = -q -n 2 [--dist=worksteal]`. Results:
  - testmon builds its database under xdist.
  - After a one-function edit it ran 1 test where the full run failed 3.
  - The subprocess-only test and the data-file test were NOT selected.
  - Previously failing tests are re-run.
  - `.testmondata` appears untracked and not ignored at the rootdir; `TESTMON_DATAFILE` relocates it.
  - The default sysmon core warns "context data may be incomplete"; `COVERAGE_CORE=ctrace` removes the warning.
  - A database copied into a second clone reselected only the edited test.
  - `git clone --shared --no-checkout` added no file to the repo's git common dir.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / I2 | E-03 "a testmon database kept beside Order 02's cache"; probe: rootdir `.testmondata` untracked, not ignored; 0o0wt2 E-02 key hashes untracked non-ignored files | The plan did not fix where the database lives. Under the default, every `--select` run leaves an untracked file at the root. That file changes Order 02's key, so every later `aw suite` misses the cache, and it also dirties `git status`. A common-dir-only location is READ-ONLY to sandboxed workers. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now sets `TESTMON_DATAFILE` to ignored `.aw/state/suite-select/<digest>.testmondata`, seeded from and published to `<git-common-dir>/aw-suite-select/` with a fail-soft publish. E-06(d) asserts no `.testmondata` and an unchanged `suite_key`. OQ-02 added. |
| PR-002 | HIGH | IN-SCOPE | A. Correctness / install | `pyproject.toml` `requires-python = ">=3.9"`; testmon `Requires-Python: >=3.10` | An unmarked `pytest-testmon` in the `test` extra breaks `pip install '.[test]'` on the 3.9 CI leg. The `dev` group, which the comment says mirrors `test`, was omitted. | Low | FIXED | Both use `pytest-testmon>=2.2; python_version >= "3.10"`. The E-06 module skips when `testmon` is absent, and the docs state the 3.10 floor. Invariant I4. |
| PR-003 | HIGH | IN-SCOPE | E. Measurement validity | E-02 threshold "minimum recall == 1.0 over all 20 steps"; probe: subprocess and data-file tests missed | If the 20 steps carry no failures, recall 1.0 is vacuous, so the criterion could ADOPT a selector that has never been shown to fail a test. The plan also had no flake handling, so a flaky miss could DECLINE spuriously. | Low | FIXED | Added criterion (iii), a control step with a deliberate break that must be selected and fail. The failing-step count and a vacuity note are required. Each miss is re-run alone three times and classified as a genuine miss or a flake. Probed blind spots are named. |
| PR-004 | MEDIUM | IN-SCOPE | E. Like-for-like | E-01 "(a) `pytest --testmon` and (b) the full bare suite" | Neither the environment nor the flags were pinned. Without that, a measurement could compare `-n0` testmon against an xdist full run, or install testmon over the operator's venv. Python 3.14's sysmon core warns that context data may be incomplete. | Low | FIXED | Both sides now use the configured `addopts`, and none of the contract's forbidden flags may be added. A `/tmp` venv with `-e '.[test]'` and `COVERAGE_CORE=ctrace` is specified. Versions and the warning are recorded, and wall times on a loaded host are discarded rather than the whole run. |
| PR-005 | MEDIUM | IN-SCOPE | A. Correctness / scratch | E-01 "`git worktree add --detach`"; V-01 "`git worktree list` after cleanup" | A linked worktree registers in the shared git common dir and can be stranded. "21 most recent ... from October" was not a re-derivable selection. | Low | FIXED | The scratch checkout is now `git clone --shared --no-checkout`, probed to add nothing to the common dir. The population is re-derived by a stated `git log` command, with 174 commits counted at authoring as context. |
| PR-006 | MEDIUM | UNDER-SCOPE | G. Right-sizing | E-03 bundled command, pyproject, prompt and test file (lint `IPD-Z602`) | One item held four deliverables with independent test surfaces. | Low | FIXED | The work is split into E-03 (command and pyproject), new E-05 (prompt sentence in all three prompts, matching 0o0wt2 E-07) and new E-06 (tests), with ids from `aw ipd sync`. E-04 now depends on E-06. |
| PR-007 | MEDIUM | UNDER-SCOPE | C. Operability / ONE ENTRY POINT | z3cqvz cross-IPD "03 and 04 add behavior inside `aw suite`"; xvm6no E-02 slot wraps `run_full_suite` misses only | A selected run neither took Order 03's slot nor reused the worker bound, so seven drivers' `--select` runs would oversubscribe the CPU again. Order 03 was not a dependency, and flag interactions (`--no-cache`, `--agent`, narrowed args) and exit codes were undefined. | Low | FIXED | `run_selected_suite` reuses the worker bound and `suite_slot`. `Item-Dependencies` gains `executed:xvm6no`. Flag interactions and exit codes are defined. `command_surface.py` is added to Scope-Paths. |
| PR-008 | MEDIUM | UNDER-SCOPE | G. Verification | V-03/V-04 evidence; V-05/V-06 skeletons | The cache-untouched check sat on the docs item. No test was required to be shown capable of failing. The new V-items were TODO. | Low | FIXED | V-03 carries cache-dir, `git status` and pyproject evidence, with code path `run_selected_suite`. V-06 requires the cell (a) failure demonstration and the Order 02/03 tests. V-05 requires rendered prompts. V-04 requires an em/en dash grep and failing-id comparison. |
| PR-009 | LOW | IN-SCOPE | G. Contract | gate "Ready for `/plan-review`"; OQ-01 `Owner: none`; missing F-rows for review probes | The execution contract was incomplete (no begin, scope-ack on DECLINE, lifecycle ownership, prerequisite STOP, or runner-output honesty). OQ-01 had no owner, and the probe evidence was not in Findings. | Low | FIXED | Gate rewritten. OQ-01 owner set to `plan author`, with the criterion (iii) rationale. F-04 to F-08 added. Required tests list invariants I1 to I4. Spec sync notes `25kzda` is untouched. |
| PR-010 | MEDIUM | UNDER-SCOPE | Carrier rule | `aw check` `check.ipd-uncarried-obligation` (error) on both Deferred rows | Neither Deferred row named a carrier, so `aw check` failed on this plan. | Low | FIXED | Each row now carries `- Carrier-Declined:` with its reason: the first is rejected by design, and the second's decision belongs to the maintainer after E-02's measured recall. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where does the testmon database live? | Ignored `.aw/state/suite-select/` via `TESTMON_DATAFILE`, seeded from and published to the common dir | Default rootdir (poisons Order 02 key); common dir only (read-only in sandboxed lanes); add `.testmondata` to `.gitignore` (still per-lane cold start, and touches a path outside scope) | review probe; 0o0wt2 E-02; `host_sandbox_profile` | yes |
| D-2 | How to handle Python 3.9? | Environment marker `python_version >= "3.10"` plus test skip | Raise the repo floor (a release-level decision, not this plan's); omit from extras (breaks "optional `[test]` extra" scope) | testmon metadata; `pyproject.toml` | yes |
| D-3 | Add a control step criterion to the pre-stated threshold? | Yes, criterion (iii) | Leave recall-only (vacuous when no step fails) | probe showing misses exist; OQ-01 intent | yes |
| D-4 | Scratch checkout mechanism? | `git clone --shared --no-checkout` | `git worktree add --detach` (registers in the common dir) | review probe | yes |
| D-5 | Coverage core on 3.14? | `COVERAGE_CORE=ctrace`, recorded | default sysmon (warns that context data may be incomplete) | review probe | yes |
| D-6 | Should `--select` take a suite slot? | Yes, reuse `suite_slot` | No slot (recreates the oversubscription Order 03 fixes) | xvm6no E-02; z3cqvz ONE ENTRY POINT | yes |

# Review findings: plan ny8eh8

- Subject-Id: ny8eh8
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at `461fdf679`. The plan was committed and unchanged (`f965f374d`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize` clean after revisions.

Re-verified at review HEAD:
- `conftest.py:89` `@pytest.hookimpl(optionalhook=True)` on `pytest_xdist_auto_num_workers`; module docstring line 6 still says `one worker per CPU`.
- F-02 reproduced: `PYTEST_ADDOPTS="-n 2" python3 -m pytest -o addopts="" tests/test_xdist_auto_workers.py -k test_pytest_runs_without_xdist_plugin` -> `1 failed`.
- F-03 reproduced: `python3 -m unittest discover -s tests -t . -p test_xdist_auto_workers.py` -> `Ran 0 tests` / `NO TESTS RAN`, exit `5`.
- In-process mechanism demonstrated (F-05): `optionalhook=True -> check_pending OK; hasplugin xdist: False`; bare `@pytest.hookimpl` (in-memory copy) -> `PluginValidationError unknown hook 'pytest_xdist_auto_num_workers'`.
- Scrubbed subprocess under outer `PYTEST_ADDOPTS="-n 2 --dist=worksteal"` -> `1 passed, 7 deselected`, exit `0`.
- `tools/replay_coverage_diff.py:169` `cmd.extend(["-p", "no:xdist"])` (production serial argv).
- `unittest` discovery leaves `conftest` in `sys.modules`; importing it changed 14 env keys; `conftest.py:158` says `make test-serial` never loads it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Anti-regression / test isolation | `tests/test_xdist_auto_workers.py:15` `import conftest`; `conftest.py:166-235` env scrub/sandbox; `conftest.py:623` `_ensure_xdist_then_reexec()`; `conftest.py:158` "never loads this file" | Making the module discoverable under `unittest` (E-02's goal) runs conftest's import-time side effects in the `make test-serial` process: 14 env keys rewritten for every later test module, and, when `xdist` is missing, `pip install` plus `os.execv` into pytest. The plan did not address this, and the conftest comment claiming unittest never loads the file becomes false. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 adds a `setUpClass` loader: reuse `sys.modules["conftest"]` under pytest; otherwise skip if `xdist` is absent, snapshot `os.environ`, import, restore. E-01 corrects the line-158 comment. Added F-06 with probe evidence. V-01/V-02 demand it. |
| PR-002 | MEDIUM | IN-SCOPE | D. Fidelity to production path | `tools/replay_coverage_diff.py:169` `cmd.extend(["-p", "no:xdist"])`; plan E-02 argv | The helper added `-p no:xdist.looponfail`, so the regression test would exercise a different invocation than the real serial run it protects, and could mask a failure specific to `-p no:xdist` alone. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Argv now matches production (`-p no:xdist` only); Concern, Scope, F-04, and Proposed changes swept. |
| PR-003 | MEDIUM | IN-SCOPE | E. Robustness | plan E-02 helper; original `tests/test_xdist_auto_workers.py:126` relative path, no `cwd`/`timeout` | The subprocess used a relative test path with no `cwd` and no timeout; under `unittest` the conftest hang guard does not apply, so a hung child hangs `make test-serial`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Helper passes repo-root `cwd`, `timeout=120`, and the scrubbed `env`. Unused `env_overrides` parameter dropped (KISS). |
| PR-004 | MEDIUM | UNDER-SCOPE | E. Test sensitivity | plan E-03 sensitivity check covered only `optionalhook` | Nothing proved the new ambient-`PYTEST_ADDOPTS` test fails when the scrub is removed, so it could pass vacuously. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added sensitivity check B to E-03, Required tests, and V-03, plus a post-restore diff proving no residual mutation. |
| PR-005 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | plan E-02 Expected outcome, Required tests, V-02 "10 tests" | A fixed test count (an artifact of test organization) was the bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bar is now: all pass, unittest `Ran N` equals pytest `N passed`, N non-zero and re-derived at execution, no skips; test names are pointers. |
| PR-006 | LOW | IN-SCOPE | D. Behavior preservation | plan E-01, E-02 | Nothing stated that E-01 is documentation-only or that worker-count input/expected pairs stay unchanged during the re-homing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 is declared comment/docstring-only (V-01 checks it); E-02 keeps every existing assertion pair. |
| PR-007 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Gate lacked the paste-actual-output honesty rule, never-push, OQ status, a scope-fence declaration, and conditional finalize ownership (it read as executor-run `aw ipd finalize` with the runner as an alternative). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all elements; runner owns finalize under `aw oc run`/`aw agy run`, executor only when run by hand; sensitivity mutations must not be committed. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to stop the unittest import of `conftest` from leaking side effects? | Test-side loader: reuse pytest's module, else skip when `xdist` absent, snapshot/restore `os.environ` around import | Move the hook into a side-effect-free module (larger change to a high-traffic harness file); guard conftest's side effects behind a "running under pytest" check (changes harness behavior) | `conftest.py:166-235`, `:623`; review probe `env restored: True` | yes |
| D-2 | Pass `-p no:xdist.looponfail` in the subprocess test? | No; mirror production `-p no:xdist` | Disable both plugins (diverges from the protected path) | `tools/replay_coverage_diff.py:169` | yes |
| D-3 | Is the in-process `check_pending()` test a demonstrated mechanism? | Yes | Leave as an open spike | Review probe (F-05): passes with `optionalhook=True`, raises `PluginValidationError` with bare hookimpl | yes |
| D-4 | Is a spec amendment needed? | No | Amend a spec | No spec governs root `conftest.py`; files not shipped (`pyproject.toml` `[tool.hatch.build.targets.*]`) | yes |

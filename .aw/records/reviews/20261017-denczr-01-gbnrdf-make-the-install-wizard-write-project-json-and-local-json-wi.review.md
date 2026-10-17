# Review findings: plan gbnrdf

- Subject-Id: gbnrdf
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was byte-identical to the lane input and committed unchanged (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan, Set `denczr`, no dependants.

Verified:
- `install_wizard.persist_project_policy`: `json.dump(proj_schema.to_dict(), f, indent=2)` to `.tmp_project.json` then `os.replace`; `json.dump(local_schema.to_dict(), f, indent=2)` to `.tmp_local.json` then `os.replace`; then `_config.sync_cutovers_on_install(repo_path, aw_home=policy.aw_home)`.
- `config.sync_cutovers_on_install`: write only under `if modified:`, `json.dump(data, f, indent=2)` then `f.write("\n")`.
- `placement_switch` project writer already appends `"\n"`; its `_write_atomic_json` does not, but it is not on the reinstall path (out of scope, matches plan OUT list).
- `tests/test_reinstall_preserves_config.py::TestPersistProjectPolicyPreservation._init_repo` exists; class not slow-marked (only a later test at the `@pytest.mark.slow` decorator is). `tests/test_install_report_truth.py` is `pytestmark = pytest.mark.slow`.
- MEASURED: `python3 -m pytest -o addopts="" -q -p no:randomly tests/test_install_report_truth.py` -> `FAILED ...test_second_install_nochange_leaves_clean_status_and_no_false_lines`, `1 failed, 2 passed in 7.07s`.
- MEASURED (probe in `/tmp/opencode`): two `persist_project_policy` rounds, unmodified: `proj_equal False local_equal True`, round-1 project ends `}\n`, round-2 ends `}`; with a `"\n"` after each dump: `proj_equal True local_equal True`, both end `}\n`. The E-02 test therefore discriminates.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Executability (red-first proof) | old E-03 "revert E-01 temporarily without committing ... then restore E-01"; AGENTS.md shared-checkout rule | Proving the test catches the bug by temporarily reverting committed or applied work is fragile in a shared checkout (an interrupted turn leaves the fix reverted, and the "absent from the final diff" check is easy to get wrong). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reordered: E-02 writes and runs the test red first (`Depends on: none`), E-01 then depends on E-02; the revert step is removed; V-02 demands the red output; F6 records the probe proving the test discriminates. |
| PR-002 | LOW | IN-SCOPE | Validation (bar) | V-03 / Required tests "showing `3 passed`" | A collected test count is an artifact of test organization and is not a valid bar; the behavior is the named test passing with zero failures. Routine gate demanded no exit code. | all Low | FIXED | V-03 and Required tests now demand the named test PASSED and zero failed, plus `exit=`. |
| PR-003 | LOW | IN-SCOPE | Process (gate) | gate "move the plan to `executed/` through the tooled lifecycle"; `aw commit <plan>` placeholder | Gate did not name `aw ipd finalize` or the runner/executor split, and the commit command was a placeholder. V-03's staged-set list required the plan file unconditionally. | all Low | FIXED | Gate names `aw commit gbnrdf -- <paths>`, `aw ipd finalize`, no hand `git mv`, conditional ownership; V-03 allows the plan file only when that commit carries it. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to prove the new test catches the bug | Author it first and run it red, then fix | Temporary revert of E-01 (REJECTED: fragile in a shared checkout) | AGENTS.md shared-checkout rule; review probe F6 | yes |
| D-2 | Also fix `placement_switch._write_atomic_json` and `install_history` newline? | No, out of scope | Fix all JSON writers (REJECTED: not on the measured reinstall diff path; plan OUT list) | F2; `placement_switch` project writer already writes `"\n"` | yes |

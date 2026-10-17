# Review findings: plan vqr3xq

- Subject-Id: vqr3xq
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `c50b2ce2f`. The plan was already committed and unchanged, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` returned `clean` with 0 findings. This is a test-only child plan (Set `trimgap`, Order 17).

What was checked in the lane: scratch copies `tests/test_zzscr_*.py` from `19313eed^`, scratch `return <value>` edits in `agent_workflows/`, and a coverage JSON file. All of them were removed or reverted afterwards; `git diff agent_workflows/` is empty and `git status` is clean apart from the plan and this record.
- Unedited replay of the four files: `70 passed in 1.19s`. With the E-02 and E-04 edits: `65 passed` (19+9+20+17). Both `rg` checks are empty.
- Coverage JSON mapped to each key's function body: all 41 keys have an executed line.
- `return None` sweep over all 41 keys: 39 are killed. `SkillPackage.to_dict` and `HostAdapter.advertises_supported` survive.
- E-05 values reproduced exactly. With a scratch E-05 class there are `68 passed`, also under `-n 4` and in random order. All four `host_adapters` mutations are killed, in both polarities for `advertises_supported`.
- The V-01 to V-03 spot-check mutations (`path_is_worker_forbidden`, `derive_set_state`, `write_local_projections`, `verify_fresh`) are each killed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Validation (wrong mutation polarity) | V-05 "`HostAdapter.advertises_supported` return-`True`"; F-04 says the `False` mutation survives; `agent_workflows/host_adapters.py:667` `HostAdapter.advertises_supported` | V-05 asked for the `True` mutation to fail. The restored files already kill that one (`1 failed, 38 passed`). The mutation that only E-05 kills, `-> False` (`64 passed, 1 skipped` without E-05), was never demanded, so V-05 could pass without proving the gap F-04 identified was closed. | all Low | FIXED | V-05 now requires both polarities, with `-> False` named as the one only E-05 kills, and each failure must name its `ResidualKeyTests` test. Added F-05. |
| PR-002 | LOW | UNDER-SCOPE | E. Goal verification | Goal "an early-return mutation of any of the 41 keys turns a routine test red"; orchestrator `kn7xtw` invariant "killed by an early-return mutation. Owner: vqr3xq" | No V-item asked for the 41-key sweep that the Goal and the parent invariant rest on. Only seven spot checks were required. | all Low | FIXED | Required tests and V-05 now demand the full 41-key `return None` sweep, with every key KILLED. |
| PR-003 | LOW | IN-SCOPE | Validation (the command cannot produce the evidence) | Required tests "`--cov-report=term-missing`, showing each of the 41 keys executing" | `term-missing` lists missing lines for each module. It does not attribute lines to keys, so "each of the 41 keys executing" cannot be read from it. | all Low | FIXED | Added a per-key reach step: a JSON coverage report with each key's body lines checked against `executed_lines`. V-05 cites it. |
| PR-004 | LOW | IN-SCOPE | Live-artifact bar | E-01..E-04 and V-01..V-04 "19/9/20/17 PASSED" | Collected test counts were used as the pass bar. They are artifacts of how the tests are organized. | all Low | FIXED | The bar is now "every test passes, zero failed", with the counts kept as context. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | Approval gate paragraph; RESTORE RULE "STOP on it" | The gate lacked the honesty rule, the staged-set check, the rule for who runs finalize (runner or hand executor), and the scope-fence-as-declaration wording. The RESTORE RULE told the executor to STOP and gave no xfail disposition. That did not match the sibling `tf8fwt`. | all Low | FIXED | Rewrote the gate as a full execution contract using `aw commit vqr3xq` and `aw ipd finalize vqr3xq`. The RESTORE RULE now uses the Set's disposition rule (record, intended change or `bug` with `--blocks-release next`, then `xfail(strict=True)`). |
| PR-006 | LOW | IN-SCOPE | D. Honest documentation | `19313eed^:tests/test_host_adapters_skills.py:690` `test_reuses_engine_shim_generator_not_forked` docstring "asserts `host_adapters` is the same object" | Once E-04 removes the two `assertIs` lines, the kept test's docstring would describe an assertion that no longer exists. | all Low | FIXED | E-04 now rewords the docstring, and V-04's diff allows for that change. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep E-02's deletion of `test_help_advertises_only_real_commands`, which also checks real parser leaves? | Keep the deletion | Restore only the parser-leaf half (the `runs status/decisions/questions` leaves are a CLI-surface check that other tests own; this plan's keys do not need it, F-03) | AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE" rule (3); the 41 keys are all reached without it (F-05) | yes |
| D-2 | Mark all four files `core` whole? | Yes | Mark a subset (all 68 tests together run in about 1s) | F-03, F-05; `conftest.py` core tier with its 30s budget | yes |

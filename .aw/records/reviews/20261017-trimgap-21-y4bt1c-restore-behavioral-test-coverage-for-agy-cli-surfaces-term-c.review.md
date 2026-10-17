# Review findings: plan y4bt1c

- Subject-Id: y4bt1c
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `5ee9ed96b`. The plan was already committed and unchanged, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` returned `clean` with 0 findings. This is a test-only child plan (Set `trimgap`, Order 21).

What was checked in the lane: scratch copies `tests/test_zzscr_*.py` of all seven files from `19313eed^`, scratch early-return edits in `agent_workflows/`, and a coverage JSON file. All were removed or reverted afterwards; `git diff agent_workflows/` is empty and `git status` is clean apart from the plan and this record.
- Unedited replay: `81 passed`. With the E-01..E-05 edits and markers: `77 passed` (also with `-n 4`). `-m core` selects 66 tests, which run in `1.69s`, and all 19 keys reach an executed body line.
- 19-key sweep without E-05: only the two comms `-> True` mutations survive. With E-05, every mutation is killed.
- E-05 values reproduced exactly.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Evidence accuracy (F-04) | plan F-04; `19313eed^:tests/test_output_contract.py` `test_clean_result_exit_code_0` `assertFalse(res.has_findings)`; `19313eed^:tests/test_interrupt_tty_wedge.py` `test_the_ladder_still_requests_a_stop_in_the_unsafe_case` | F-04 says `has_findings -> True` survives. It does not: a restored test asserts `False` on a clean result (`1 failed`). F-04 also says a no-op `reset_signal_ladder` is invisible. In fact a restored test catches it in some orders and misses it in others: caught in file order and at random seeds 1, 3 and 5, missed at seeds 2 and 4 and when run alone. The second point matters more: the restored suite only catches a no-op reset by chance, which is why the E-05 reset test is needed. | all Low | FIXED | Added F-06 with the measured sweep. V-05 now also requires the residual reset test to fail when run alone. E-05 states why each test is kept. |
| PR-002 | MEDIUM | IN-SCOPE | Executability (lint hook) | `19313eed^:tests/test_agy_tools_graduation.py:25,29,33` (`importlib.util`, `Path`, `REPO_ROOT`); `19313eed^:tests/test_output_contract.py:23,31`; `.pre-commit-config.yaml` `ruff` | After the E-01 and E-02 deletions, these imports are unused and two classes (`CompatShimForwardingTests`, `AgyRunGraduatedTests`) and `OutputContractDocTests` are left empty. The `ruff` pre-commit hook would then reject the commit with an unused-import error. | all Low | FIXED | E-01 and E-02 now name each leftover to remove, and V-01 and V-02 require `ruff check` to be clean. The RESTORE RULE says to remove anything a deletion leaves unused. |
| PR-003 | MEDIUM | IN-SCOPE | Project rule: no code-pinning tests | `19313eed^:tests/test_term_components.py:97` `test_no_parallel_palette_defined` (`T.__dict__` COLOR-dict census, `hasattr(T, "STATUS_COLOR_256")`) | E-03 restores this test unchanged. It lists the module's dict names and asserts one symbol is absent. That is a symbol census, which `AGENTS.md` rule (2) forbids. It calls no Term method, so no key needs it. | all Low | FIXED | E-03 now deletes it. V-03 requires the diff and an empty `rg` check. Conventions updated. |
| PR-004 | LOW | UNDER-SCOPE | Goal verification | Goal "an early-return mutation of any of the 19 keys turns a routine test red" | No V-item asked for the full 19-key check that the Goal promises. Only eight spot checks were required. | all Low | FIXED | Required tests and V-05 now demand the full sweep and state which return value to use for each kind of key. |
| PR-005 | LOW | IN-SCOPE | Validation (the command cannot produce the evidence) | plan Required tests `--cov-report=term-missing` | `term-missing` does not attribute executed lines to individual keys. | all Low | FIXED | Added a per-key reach step that uses a JSON coverage report. |
| PR-006 | LOW | IN-SCOPE | Pass bar uses a live count | plan E-01..E-04, V-01..V-04 counts (14/4/38/18) | Collected test counts were used as the pass bar. | all Low | FIXED | The bar is now "every test passes, zero failed", with the counts kept as context. |
| PR-007 | LOW | IN-SCOPE | G. Execution contract | plan Approval gate; RESTORE RULE "STOP on it" | The gate lacked the honesty rule, the staged-set check, the rule for who runs finalize, and the scope-fence-as-declaration wording. The RESTORE RULE told the executor to STOP and gave no xfail disposition. This did not match the sibling plans `tf8fwt` and `vqr3xq`. | all Low | FIXED | Rewrote the gate as a full execution contract and used the Set's disposition rule. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep `PointerBlockTests.test_agents_block_has_check_inbox_clause` (it asserts substrings of `engine.agents_pointer_block()`)? | Keep it | Delete it as a prose check. Rejected: it calls a function and asserts on the text that function returns at runtime, which is the generated managed-block output that `aw` installs. It does not read a source or prose file. | `AGENTS.md` rule (4) "assert on real outputs" | yes |
| D-2 | Keep the E-05 `has_findings` test now that `-> True` is already killed? | Keep it | Drop it (it is only partly redundant). Rejected: it pins the `exit_code=2` and diagnostics-only cases, which no restored test asserts. | F-06 | yes |
| D-3 | Mark more `test_agy_tools_graduation.py` tests `core`? | No; keep exactly three | Mark the whole file (all of them are about 0.05s in-process). Rejected: the three named tests already reach all four agy keys, and this keeps the plan's scope. | F-06 durations and reach | yes |

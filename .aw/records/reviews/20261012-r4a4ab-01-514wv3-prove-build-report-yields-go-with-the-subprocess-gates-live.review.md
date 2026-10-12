# Review: Prove build_report yields GO with the subprocess gates live on a synthetic clean tree

- Subject-Id: 514wv3
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Verified at lane HEAD `03363cbc8`. The plan was committed and unchanged, so the snapshot was skipped.
`aw ipd lint --phase author` reported `clean` before review.

- `release_readiness.build_report` default `run_subprocess_gates=True` appends `gate_leak_scan` and
  `gate_ipd_lint`; both record `evidence={"returncode": proc.returncode}`; `failing_gates()` lists
  non-passing gate names. E-02/E-03 assertions are all reachable.
- `grep -n run_subprocess_gates tests/test_release_readiness.py` -> 339, 354, 370, 431, all `False`;
  `_build_synthetic_root` matches E-02's description.
- Review probe (same tree E-02 describes): `GO [] [('leak_scan', {'returncode': 0}), ('ipd_lint',
  {'returncode': 0})]`; adding the E-03 two-line plan -> `NO-GO ['ipd_lint']`, `returncode: 1`.
  Without `git init` -> `leak_scan` 2; without `pending/` -> `ipd_lint` 2.
- Live tree: `ipd lint --all` exit=0, `counts: conforming=117, ... error=0`; `15db4k` is in `executed/`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A. Evidence currency | `python3 -m agent_workflows ipd lint --all` at `03363cbc8` -> `exit=0`, `counts: conforming=117, quarantined=0, legacy/not evaluated=1324, error=0`; `.aw/records/plans/executed/20261011-4xtpvg-02-15db4k-...ipd.md` | Concern, Scope, F-01..F-03, Open questions and the gate all said the live tree IS red because of `15db4k`. It is now green and `15db4k` has executed. An executor could read E-01's green result as invalidating the premise. The coverage gap (F-04/F-06) is unaffected. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-01/F-02 relabelled HISTORICAL with the current measurement. F-03 restated as a principle. E-01 now says either exit code is acceptable and does not stop the plan. Concern, Scope, Open questions and the gate no longer assert the live tree is red. |
| PR-002 | LOW | IN-SCOPE | E. Testing / G. stop condition | `tests/test_release_readiness_child_pin.py::test_gates_do_not_execute_decoy_package_in_caller_repo_root` asserts `gate_leak_scan` and `gate_ipd_lint` return 0 on the same tree shape | The E-01 STOP ("a test already asserts GO with live subprocess gates") was ambiguous next to this existing test, which proves each gate individually but never `build_report`'s aggregate GO. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-06 defining the exact delta. E-01's expected outcome now says the child-pin test does not trigger the stop. F-04 records the review re-probe and that both tree preconditions are needed. |
| PR-003 | LOW | IN-SCOPE | E. Test cost | Review timing: probe 10.63 to 11.94s, child-pin test 9.25s, load average ~115 | F-05 claimed about 1.1s. Under load the cost is about 10x that, and E-03 spawns the gates twice. Keeping the tests unmarked still matches the unmarked child-pin precedent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 rewritten as load-sensitive with both measurements and the precedent. No `slow` marker added (D-1). |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | plan `## Approval and execution gate` | The gate lacked the scope-fence declaration, an explicit statement that no questions are open, conditional runner/executor finalize ownership, and the paste-actual-output rule. It also told the executor to finalize unconditionally. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Mark the new tests `slow`? | No | Mark `slow` (would deselect them from the default run, hiding the very coverage this plan adds) | `test_release_readiness_child_pin.py` spawns the same two gates unmarked; `pyproject.toml` `slow` is for heavy CLI/install integration | yes |
| D-2 | Does a now-green live tree invalidate the plan? | No | Retire as not-executed | The gap is coverage of `build_report` with live gates (F-06), independent of the live tree | yes |

# Review findings: plan g0u7f9

- Subject-Id: g0u7f9
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `66401aeb1` in an isolated review lane (`AW_EXECUTION_ROLE=worker` set); plan committed and unchanged, no snapshot needed.
`aw ipd lint --phase author --agent` clean before semantic review; `--phase review-finalize` clean after.

Re-verified:
- `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q` -> `10 failed, 15 passed`; collect-only count of `test_runagy` -> `0`.
- Symbols exist as cited: `runner_shared.attempt_log_path` (oc shape `-attempt-1-verify`), `_VERDICT_TABLE` `VERDICT_BLOCKED -> "fail-verify"`, `VERIFY_REFUSAL_CODE_UNEVIDENCED = "verifier-no-test-evidence"`, `SUITE_CHECK_ARGV`, `run_suite_check`, `edge_satisfied`, `dependency_status_detailed`; `tests.test_oc_runipd._CONFORMING_PLAN`; `tests/support.py` `load_module`.
- Scratch copy (gitignored `.aw/state/`, removed) with E-03 fixture changes only: `5 failed, 20 passed` module-wide; Lifecycle 4 failed (`two_turn`, `prepare_only`, `verification_blocked`, `concurrent_work`), identical with `AW_EXECUTION_ROLE` set and unset. Adding E-04 (a) and (b): those pass.
- E-04 (d) as written: Concurrent Work section bounded at next `## ` -> execute vs verifier `False`; bounded through `Never discard their work.` -> `True` (844 chars).
- E-05 design on a tempfile repo: execute-on-reviewed `(False, ['dep001'])`, execute-on-executed-dir `(True, [])`, review-on-reviewed `(True, [])`, executed-status-but-pending-dir `(False, ['dep005'])`.
- Prepare-only: exit 0, one `queued` item, `sessions/` directory exists (empty).
- Durations: slowest 4.65s (`test_stall_timeout_and_resume_recovery`).
- Siblings: `5s31xp` (reviewed) adds `tests/test_uncollected_test_modules.py` exempting `tools/ipdrunner/test_runagy.py` with a stale-exemption failure; `vzk1iw` (to-review) rewrites the same `_read_id` comments; backlog `3rj8wr` (open) duplicates `gte0pd`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Anti-regression | `5s31xp` E-02 seeds `EXEMPT` with `tools/ipdrunner/test_runagy.py` and asserts every exempt key still exists | Whichever of `5s31xp`/this plan lands second leaves a stale exemption that turns the bare suite red; the plan did not know about the guard. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New E-07/V-07 (conditional removal of that entry in the same commit), Scope-Paths extended, F-11 updated. |
| PR-002 | HIGH | IN-SCOPE | E. Testing | E-04 (d); measured section comparison `False` | "Section text extracted ... IDENTICAL" with a next-heading boundary fails: the execute prompt has un-headed run instructions after the block. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 (d) bounds the block through `Never discard their work.`; measured `True`. |
| PR-003 | MEDIUM | IN-SCOPE | D. Anti-regression | E-02 `sys.path.insert` of `tools/ipdrunner` | Once collected, a module-level `sys.path` insert leaks `tools/ipdrunner` onto every xdist worker's import path, making `runipd`/`runagy` importable suite-wide. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 uses `tests/support.load_module` on the shim path; V-02 checks no insert remains. |
| PR-004 | MEDIUM | IN-SCOPE | E. Testing | E-03 expected outcome; probe | `test_runagy_no_verify_skips_turn2` passes after E-03 only vacuously (asserts absence of a name no longer written); and E-03's "the ones E-04/E-05 own" misattributed (E-05 owns a Parser test). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 names the 4 remaining tests, the vacuity, and that E-04 (a) restores it; V-04 checks the current name. |
| PR-005 | MEDIUM | UNDER-SCOPE | A. Coordination | `vzk1iw` E-03 rewrites the same comments | E-06 quoted text that a sibling plan may have rewritten by execution time. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now edits by property, names `vzk1iw`; E-01/V-01 record sibling state; F-13 added. |
| PR-006 | MEDIUM | IN-SCOPE | E. Testing / baseline | Required tests "Bare ... passes" | No failing-test-name baseline; another party's failure would block a correct execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 records names; V-06 compares. |
| PR-007 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Missing `aw ipd begin`, scope-as-declaration with `--scope-reason`/`--scope-ack`, MUST-paste wording, staged-set check, conditional finalize ownership; "stop that item" lacked the continue-independent-work clause and a gate for a filed runner bug. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten. |
| PR-008 | LOW | UNDER-SCOPE | Traceability | backlog `3rj8wr` | Duplicate backlog item for this exact work is unlinked and would stay open. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-12 added; gate closes it with `--evidence` after execution. |
| PR-009 | LOW | IN-SCOPE | Clarity | E-04 (c); OQ owners; Step 0 role note | Prepare-only creates an empty `sessions/` dir (so "no session log" must mean no `*.jsonl`); OQ owners `none`; role-leak check left wholly to executor. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 (c) clarified; owners `plan author`; Step 0 records the review measurement. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to reconcile with `5s31xp`'s exemption? | Conditional E-07 here: remove the entry if the guard exists, else scope-ack | Add an `Item-Dependencies` edge on `5s31xp`; edit `5s31xp` | Guard's stale-exemption rule (`5s31xp` E-02); no ordering is needed if each side is conditional | yes |
| D-2 | Concurrent Work block boundary? | Through the terminal sentence `Never discard their work.` | Next `## ` heading; verbatim paragraph | Measured `True` vs `False`; all three `runner_shared` templates end with that sentence | yes |
| D-3 | How to import the shim once collected? | `support.load_module` on `tools/ipdrunner/runagy.py` | Keep `sys.path.insert` | Avoids suite-wide import-path pollution; helper already in `tests/support.py` | yes |

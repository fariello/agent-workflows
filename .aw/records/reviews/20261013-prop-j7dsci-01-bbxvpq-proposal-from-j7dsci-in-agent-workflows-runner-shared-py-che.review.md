# Review findings: plan bbxvpq

- Subject-Id: bbxvpq
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged at `0e8e95ac2`, so no snapshot was needed. `aw ipd lint` was clean at `author` before the edits and at `review-finalize` after them.

### Probes (git 2.43.0, temp repos, `diff.renames true` set repo-locally)

1. Deletion probe: after `git mv p/a.md e/a.md`, `git diff --name-only --diff-filter=D` printed nothing; with `--no-renames` it printed `p/a.md`. Confirms F-1.
2. Real gate, pending->executed (`executed_transition_gate.check`): retained source and removed source both exit 1 with no finalize journal, and both exit 0 with a matching journal. The defect does NOT change the outcome of this case.
3. Real gate, rename inside `executed/`, replaying `check_lane_hook_bypass`'s sequence: pre-fix the disposable index staged `A executed/<new>` and the gate exited 1; with `--no-renames` it staged `R100 <old> <new>` and the gate exited 0. This is the real defect.
4. `git show -M --name-status 0d15f3685` (the j7dsci work commit): `R099 .aw/records/plans/executed/20260101-instsafe-07-qrokie-... -> .aw/records/plans/executed/20260723-instsafe-07-qrokie-...`. The observed refusal was case 3.
5. `leak_sanitizer._staged_files`: renamed and modified file, `--diff-filter=ACM` with `diff.renames=true` printed nothing; with `diff.renames=false` or `--no-renames` it printed `b.txt`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / E. Test validity | `agent_workflows/hooks/executed_transition_gate.py:130` `_staged_plan_executed_transitions` (exemption needs same `- Id:` at the HEAD path); probes 2-4 | The plan said the defect refuses a TOOLED move pending->executed. It does not: the gate result there is the same with or without the retained source. The defect bites a rename INSIDE `executed/`, which is what qrokie was. E-01 as written ("tooled move ... or a non-plan rename such as `src/a.txt`") could not reproduce the refusal: the fixture's fake gate refuses any `executed/` path regardless, and a non-plan rename trips no gate. The fail-before-fix demand was unsatisfiable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern, title, Goal and F-3 corrected; F-3a added. E-01 now uses the real `ipd-executed-gate` hook (with `PYTHONPATH` to the repo) and a rename inside `executed/` under `diff.renames true`. Matches probe 3. |
| PR-002 | MEDIUM | UNDER-SCOPE | A. Correctness (audit) | `agent_workflows/leak_sanitizer.py:709` `_staged_files` `"--diff-filter=ACM"`; probe 5 | F-4 claimed only one `--diff-filter` call. There are two that select added/deleted paths. The staged leak scan (`local-leaks` pre-commit hook) silently skips a renamed-and-modified file under rename detection, which is a leak-scan gap. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-03/V-03 (one flag + outcome test). Scope-Paths extended. F-4 corrected; F-5 added. The audit moved to E-04/V-04. |
| PR-003 | LOW | IN-SCOPE | E. Verification checklist | old V-01 "showing the rename-caused refusal or retained source path" | The "or retained source path" alternative let V-01 pass without showing the gate refusal. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now requires the real-gate config line and the `moved into executed/` refusal text. |
| PR-004 | LOW | UNDER-SCOPE | G. Execution contract | old gate "Small, low-risk bug fix. Execute after review..." | The gate had no lifecycle-ownership clause (runner vs hand finalize) and no scope-fence declaration. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added an execution contract: OQ state, scope-fence declaration with justification and no stop, paste-actual-output rule, path-scoped commit, never push, and conditional finalize ownership. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Fold the `leak_sanitizer._staged_files` fix into this plan or file it separately? | Fold in as E-03 | A separate backlog item (it is the same root cause, a one-flag fix, and the plan's own E-03 audit already said "fix any") | Original E-03 text "fix any that select deletions"; probe 5 | yes |
| D-2 | What fixture reproduces the defect? | Real gate hook, rename inside `executed/`, `diff.renames true` repo-local | Fake staged gate (refuses any `executed/` path, so it is blind to the defect); a pending->executed move (unaffected, probe 2) | Probes 2 and 3; `test_executed_transition_gate_e2e.py` already runs the real hook with `PYTHONPATH` | yes |

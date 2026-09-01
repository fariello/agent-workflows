# Review: Per-host permission posture and driver-side turn bounds

- Plan-Id: lhmrhx
- Reviewed-At: 2026-09-01
- Reviewer: codex/gpt-5
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `08ae65cb`; the plan was committed and unchanged before review. Author-phase IPD lint
returned clean and verified. The plan handles host asymmetry honestly: OpenCode requests and observes a
policy, Antigravity retains its measured auto-approved posture, and driver-owned deadlines remain the
portable safety mechanism. Reuse of the single process reaper is explicit.

The remaining issues concern executable decomposition and reproducible validation, not the chosen host
policy.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G. Right-sizing / B. Host parity | `lhmrhx:37-63`, especially E-06 at `:60-63` | E-06 combines the execution-role selector with all applicable Antigravity mirrors of policy reporting, operator-value handling, permission-event observation, permission and absolute deadlines, termination, and safe-failure recording. The sanctioned absence of an Antigravity policy document makes this a selective port, not a mechanical mirror, increasing the chance of an omitted seam. | C:Medium; U:Medium; S:Medium; F:High; Overall:Medium | FIXED | FIXED 2026-09-01. E-06 is now wiring only, and the plan states explicitly that this is a SELECTIVE port rather than a mechanical mirror because the agy host has no policy document by design, which must be marked INAPPLICABLE rather than left to inference. The deadlines, reporting, and safe-failure recording must be host-neutral. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing and regression | Required tests `lhmrhx:107-117`; repository test contract in `AGENTS.md` | The plan requests six named test files with slow coverage included but gives no exact command for clearing configured `addopts` and selecting that scope. An executor must invent invocation semantics, which is especially risky where the normal suite deselects slow tests. Its exact suite baseline is also older than commit `8ced15ce`. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-01 for the baseline half (measure at execution time, compare by identity). NOTED and PARTIALLY DEFERRED for the exact narrowed command: the plan already names the six runstop suites and requires `slow` coverage; the reviewer's suggested `-o addopts=""` form is the documented way to clear configured defaults and the executor should use it. Recorded here rather than hardcoded into the plan because the repository's test contract warns against bolting flags on, and the correct invocation may change. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should Antigravity's auto-approved default be changed to resemble OpenCode's deny posture? | No. Preserve the approved host asymmetry and rely on prompt purity plus driver-side bounds for Antigravity. | Flip or remove `--dangerously-skip-permissions`. Rejected because the approved spec records that posture as a deadlock risk and requires its default to remain true. | `lhmrhx:45-63`; spec `7ckptx` R4.1c and A8c | yes |

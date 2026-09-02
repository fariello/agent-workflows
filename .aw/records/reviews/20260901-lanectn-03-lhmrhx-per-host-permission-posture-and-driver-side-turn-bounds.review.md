# Review: Per-host permission posture and driver-side turn bounds

- Plan-Id: lhmrhx
- Reviewed-At: 2026-09-01
- Reviewer: codex/gpt-5
- Verdict: REVIEWED

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
| PR-002 | MEDIUM | IN-SCOPE | E. Testing and regression | Required tests `lhmrhx:107-117`; repository test contract in `AGENTS.md` | The plan requests six named test files with slow coverage included but gives no exact command for clearing configured `addopts` and selecting that scope. An executor must invent invocation semantics, which is especially risky where the normal suite deselects slow tests. Its exact suite baseline is also older than commit `8ced15ce`. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-01, both halves, after a self-review agreed with GPT that a row cannot be `FIXED` while one half is explicitly deferred. Baseline half: replaced with measure-at-execution-time plus compare-by-failure-identity. Command half: the exact invocation is now WRITTEN INTO the plan rather than left to the executor or recorded only here - `python3 -m pytest -o addopts="" -q` over the six runstop suites, with an explanation that `-o addopts=""` clears the configured defaults wholesale (the repository's test contract forbids fighting them one at a time, and the default `-m 'not slow'` would deselect the very tests this Set depends on). VERIFIED before writing it in: `243 passed in 100.61s`, and that figure is recorded in the plan as a comparison point. The plan also states that this narrowed run does NOT substitute for the two whole-suite invocations. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should Antigravity's auto-approved default be changed to resemble OpenCode's deny posture? | No. Preserve the approved host asymmetry and rely on prompt purity plus driver-side bounds for Antigravity. | Flip or remove `--dangerously-skip-permissions`. Rejected because the approved spec records that posture as a deadlock risk and requires its default to remain true. | `lhmrhx:45-63`; spec `7ckptx` R4.1c and A8c | yes |

## Round 2

Disclosed self-review by the original author at HEAD `868106a4`. The finding below is fixed in the current plan and spec.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| SR-002 | HIGH | IN-SCOPE | C. Architecture / G. Plan executability | Plan `Scope-Paths` versus host-neutral instructions | Shared deadline and reporting behavior had no declared host-neutral module, making the remediation incompatible with the scope fence. | C:Medium; U:Low; S:Low; F:High; Overall:Medium | FIXED | Added spec R2.6/A5c and declared `agent_workflows/lane_containment.py`; Antigravity retains a thin selective adapter with its policy-document step explicitly inapplicable. |

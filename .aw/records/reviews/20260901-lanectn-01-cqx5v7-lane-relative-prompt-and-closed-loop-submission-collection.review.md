# Review: Lane-relative prompt and closed-loop submission collection

- Plan-Id: cqx5v7
- Reviewed-At: 2026-09-01
- Reviewer: codex/gpt-5
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `08ae65cb`; the plan was committed and unchanged before review. Author-phase IPD lint
returned clean and verified. The central sequencing choice is correct: prompt purification and collection
must land together because removing out-of-lane paths without harvesting lane-side output would turn an
obedient worker's success into an empty reconciliation result.

The OpenCode work is decomposed by property, and the collection requirements explicitly preserve source
files and require idempotency. The Antigravity half, however, is collapsed into one item that silently
contains the same four independent concerns.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G. Right-sizing / C. Clarity | `cqx5v7:37-59`, especially E-05 at `:56-59` | E-05 says to mirror E-01 through E-04 while also verifying host-specific seams. That single item covers prompt path projection, exception removal and missing-input wording, collection timing and copy semantics, register idempotency, and multiple test surfaces. It is not one focused pass and can be marked complete while one property remains absent. | C:Medium; U:Low; S:Medium; F:High; Overall:Medium | OPEN | Split Antigravity work into concern-aligned items matching E-01 through E-04, each with its own validation item, or extract shared helpers and limit the twin item to adapter wiring. Escalated as blocking OQ-02. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing and regression | Required tests `cqx5v7:101-113`; baseline commit `59e68d5a`; later test changes in `8ced15ce` | The plan carries an exact historical suite count as an expected execution result after the suite changed. The behavioral assertions remain useful, but the fixed pass count is stale evidence. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | OPEN | Measure the bare-suite baseline at execution time and attribute any delta by failing test identity. Keep the prompt-output, collection-idempotency, and sabotage checks unchanged. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should prompt purification and collection be split into separate plans to make this child smaller? | No. Keep them in one child and split only the host-specific execution items. | Separate plans for prompt and collection. Rejected because spec R2.1 and the orchestrator's Rule 1 require them to ship together to avoid invisible loss of successful output. | `cqx5v7:5-6,48-59`; orchestrator sequencing Rule 1 | yes |

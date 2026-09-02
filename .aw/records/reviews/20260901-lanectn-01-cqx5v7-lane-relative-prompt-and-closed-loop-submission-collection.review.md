# Review: Lane-relative prompt and closed-loop submission collection

- Plan-Id: cqx5v7
- Reviewed-At: 2026-09-01
- Reviewer: codex/gpt-5
- Verdict: REVIEWED

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
| PR-001 | HIGH | UNDER-SCOPE | G. Right-sizing / C. Clarity | `cqx5v7:37-59`, especially E-05 at `:56-59` | E-05 says to mirror E-01 through E-04 while also verifying host-specific seams. That single item covers prompt path projection, exception removal and missing-input wording, collection timing and copy semantics, register idempotency, and multiple test surfaces. It is not one focused pass and can be marked complete while one property remains absent. | C:Medium; U:Low; S:Medium; F:High; Overall:Medium | FIXED | FIXED 2026-09-01. E-05 is no longer a mirror: E-01 through E-04 must place their logic in host-neutral functions and E-05 is reduced to wiring plus event adaptation, with its outcome demanding AST or import-graph proof of NO duplicated logic. Also added E-06/V-06 (collection receipt) in response to child `xdr83v`'s PR-001, since this plan owns collection. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing and regression | Required tests `cqx5v7:101-113`; baseline commit `59e68d5a`; later test changes in `8ced15ce` | The plan carries an exact historical suite count as an expected execution result after the suite changed. The behavioral assertions remain useful, but the fixed pass count is stale evidence. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-01. Baseline block replaced with a measure-at-execution-time requirement and failure-identity comparison. The behavioral, idempotency, and sabotage assertions are unchanged. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should prompt purification and collection be split into separate plans to make this child smaller? | No. Keep them in one child and split only the host-specific execution items. | Separate plans for prompt and collection. Rejected because spec R2.1 and the orchestrator's Rule 1 require them to ship together to avoid invisible loss of successful output. | `cqx5v7:5-6,48-59`; orchestrator sequencing Rule 1 | yes |

## Round 2

Disclosed self-review by the original author at HEAD `868106a4`. It rechecked this plan after Round 1 remediation; both findings below are fixed in the current plan and spec.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| SR-002 | HIGH | IN-SCOPE | C. Architecture / G. Plan executability | Plan `Scope-Paths` versus host-neutral instructions | Shared behavior had no declared host-neutral module, making the remediation incompatible with the scope fence. | C:Medium; U:Low; S:Low; F:High; Overall:Medium | FIXED | Added spec R2.6/A5c and declared `agent_workflows/lane_containment.py`; driver work is limited to wiring and event adaptation. |
| SR-003 | MEDIUM | UNDER-SCOPE | G. Traceability | E-06 versus the then-current spec | The collection receipt added for retention had no normative requirement. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added spec R2.5 and A5b defining an attempt-keyed receipt, source digest, destination result, explicit failure, and absence-as-uncollected semantics. |

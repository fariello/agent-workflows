# Review: Retention: preserve a lane holding unclassifiable content

- Plan-Id: xdr83v
- Reviewed-At: 2026-09-01
- Reviewer: codex/gpt-5
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `08ae65cb`; the plan was committed and unchanged before review. Author-phase IPD lint
returned clean and verified. The fail-toward-preservation rule is correct and proportionate: an
inventory error retains recoverable data, while teardown is irreversible. Including ignored files and
recording refusal reasons closes the most important historical loss mode.

The plan does not yet identify authoritative evidence that a submission was collected, and its second
driver work is too compressed for the state distinctions involved.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A. Data integrity / G. Plan executability | E-01 and E-02 `xdr83v:35-41`; input manifest `nna8yz:35-45`; collection behavior `cqx5v7:48-54` | The sealed manifest records materialized inputs. It does not record whether a lane-side submission was copied successfully into the run directory or whether a run-wide append was committed idempotently. Therefore it cannot establish the plan's required “uncollected submission” classification. Guessing from path presence risks preserving every successful lane forever or deleting output whose harvest failed. | C:Medium; U:Medium; S:Medium; F:High; Overall:High | OPEN | Define an authoritative, attempt-keyed collection receipt or equivalent state transition, including source digest and destination result. Test collected, uncollected, interrupted, and repeated collection before teardown. Escalated as blocking OQ-02. |
| PR-002 | HIGH | UNDER-SCOPE | G. Right-sizing / B. Host parity | E-03 `xdr83v:43-46` compared with E-01 and E-02 `:35-41` | E-03 combines refusal-event semantics with mirroring the complete inventory and teardown guard into Antigravity. Inventory coverage, classification, fail-closed behavior, teardown refusal, and event identity are distinct properties with different failure modes. | C:Medium; U:Low; S:Medium; F:High; Overall:Medium | OPEN | Separate event recording from the Antigravity inventory and refusal wiring, or implement shared classification/refusal code with separately validated driver adapters. Escalated as blocking OQ-02. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing and regression | Required tests `xdr83v:84-92`; baseline commit `59e68d5a`; later test changes in `8ced15ce` | The fixed suite count is stale. This matters here because retention tests must distinguish intentional preservation from leaked cleanup state, and a raw count cannot attribute that distinction. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | OPEN | Measure the suite at execution time and require named assertions for each inventory class and collection state. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Can collection success be inferred from the sealed input manifest? | No. Require explicit collection evidence owned by the collection path. | Infer success from the existence or absence of lane and destination files. Rejected because collection copies rather than moves, retries are idempotent, and the lane intentionally retains its source, so file presence does not encode completion. | `nna8yz:35-45`; `cqx5v7:48-54`; spec `7ckptx` R2.2 and R5.5 | yes |

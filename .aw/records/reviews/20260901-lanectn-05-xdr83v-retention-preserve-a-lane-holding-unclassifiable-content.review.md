# Review: Retention: preserve a lane holding unclassifiable content

- Plan-Id: xdr83v
- Reviewed-At: 2026-09-01
- Reviewer: codex/gpt-5
- Verdict: REVIEWED

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
| PR-001 | HIGH | UNDER-SCOPE | A. Data integrity / G. Plan executability | E-01 and E-02 `xdr83v:35-41`; input manifest `nna8yz:35-45`; collection behavior `cqx5v7:48-54` | The sealed manifest records materialized inputs. It does not record whether a lane-side submission was copied successfully into the run directory or whether a run-wide append was committed idempotently. Therefore it cannot establish the plan's required “uncollected submission” classification. Guessing from path presence risks preserving every successful lane forever or deleting output whose harvest failed. | C:Medium; U:Medium; S:Medium; F:High; Overall:High | FIXED | FIXED 2026-09-01, and this was a genuine data-model error on my part. The sealed manifest records materialized INPUTS while collection is OUTPUT, so it cannot answer 'was this submission collected?'. Added E-06/V-06 to child `cqx5v7` (which owns collection) requiring an ATTEMPT-KEYED COLLECTION RECEIPT naming what was collected, its source digest, and the destination result, with absence of a receipt meaning NOT collected and a FAILED collection recorded as failed rather than omitted; V-06 tests collected, uncollected, interrupted, and repeated collection, and sabotage-checks the failure case. This plan now reads that receipt for collection state and the input manifest only for driver-written content, with the distinction stated explicitly. |
| PR-002 | HIGH | UNDER-SCOPE | G. Right-sizing / B. Host parity | E-03 `xdr83v:43-46` compared with E-01 and E-02 `:35-41` | E-03 combines refusal-event semantics with mirroring the complete inventory and teardown guard into Antigravity. Inventory coverage, classification, fail-closed behavior, teardown refusal, and event identity are distinct properties with different failure modes. | C:Medium; U:Low; S:Medium; F:High; Overall:Medium | FIXED | FIXED 2026-09-01. E-03 is now event detail plus thin wiring; classification and refusal must be host-neutral. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing and regression | Required tests `xdr83v:84-92`; baseline commit `59e68d5a`; later test changes in `8ced15ce` | The fixed suite count is stale. This matters here because retention tests must distinguish intentional preservation from leaked cleanup state, and a raw count cannot attribute that distinction. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-01. Baseline replaced with measure-at-execution-time; the per-inventory-class and per-collection-state named assertions are required by V-01 through V-03 and by the new receipt V-item. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Can collection success be inferred from the sealed input manifest? | No. Require explicit collection evidence owned by the collection path. | Infer success from the existence or absence of lane and destination files. Rejected because collection copies rather than moves, retries are idempotent, and the lane intentionally retains its source, so file presence does not encode completion. | `nna8yz:35-45`; `cqx5v7:48-54`; spec `7ckptx` R2.2 and R5.5 | yes |

## Round 2

Disclosed self-review by the original author at HEAD `868106a4`. It rechecked this plan after Round 1 remediation; both findings below are fixed in the current plan and spec.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| SR-002 | HIGH | IN-SCOPE | C. Architecture / G. Plan executability | Plan `Scope-Paths` versus host-neutral instructions | Shared inventory and refusal behavior had no declared host-neutral module, making the remediation incompatible with the scope fence. | C:Medium; U:Low; S:Low; F:High; Overall:Medium | FIXED | Added spec R2.6/A5c and declared `agent_workflows/lane_containment.py`; E-03 is limited to event detail and thin wiring. |
| SR-003 | MEDIUM | UNDER-SCOPE | G. Traceability | Collection receipt requirement consumed by this plan versus the then-current spec | Retention required authoritative collection state, but the newly added receipt had no normative requirement. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added spec R2.5/A5b; retention reads the collection receipt for output state and the sealed input manifest only for driver-written inputs. |

# Review: Worker lane containment: adopt spec 7ckptx

- Plan-Id: h0zljh
- Reviewed-At: 2026-09-01
- Reviewer: codex/gpt-5
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `08ae65cb`. The target plan and its six children were committed and unchanged before
review, so no pre-review snapshot was required. `aw ipd lint --phase author --agent` returned a clean,
verified result for every Set member. That proves the seven documents satisfy the structural IPD
contract; it does not prove that the dependency graph, right-sizing claims, or validation baselines are
semantically correct.

The orchestrator has strong whole-Set controls: it assigns all 36 requirements, makes the two normative
sequencing rules explicit, requires evidence for every child and acceptance criterion, and prevents an
agent from setting the spec to `implemented`. Its architecture does not need replacement. Execution is
nevertheless unsafe until the dependency graph and child decomposition are corrected.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | B. Sequencing / G. Plan executability | Orchestrator child table `:57-64`; `y5od1h:8,50-52,98`; `604wra:8,20,145` | The graph described as complete and acyclic is not the graph encoded by the child metadata. `y5od1h` consumes the denied-permission event produced by `lhmrhx` but declares only `nna8yz`. `604wra` says in prose that both `y5od1h` and `lhmrhx` must be complete while its `Item-Dependencies` names only `y5od1h`. A scheduler following metadata can start work before required seams exist. | C:Low; U:Low; S:Medium; F:High; Overall:Medium | OPEN | Correct the child metadata and recompute the displayed depth/order proof from the actual machine-readable edges. Escalated as blocking OQ-02. |
| PR-002 | HIGH | UNDER-SCOPE | G. Right-sizing | Orchestrator `:5-6,57-66`; `cqx5v7:56-59`; `nna8yz:54-57`; `lhmrhx:60-63`; `y5od1h:61-64`; `xdr83v:43-46` | The claim that the Set contains six small, independently executable children is not supported by the execution checklists. Five children compress most of the second driver's implementation into one final “mirror” item spanning multiple behaviors and test seams. Structural item counts therefore understate conceptual size and make partial completion likely. | C:Medium; U:Low; S:Medium; F:High; Overall:Medium | OPEN | Split mirror work by concern, or introduce shared behavior first and make host-specific items thin adapters. Recalculate the partition after revision. Escalated as blocking OQ-02. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing and regression | Orchestrator `:149-159`; child Required tests sections; Git range `59e68d5a..08ae65cb`, including test changes in `8ced15ce` | The exact `3996 passed` baseline was measured at `59e68d5a`, before later test changes. Treating that count as an execution-time expectation can misclassify an honest count change or conceal an attribution error. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | OPEN | Re-measure both required suites immediately before execution, preserve their distinct expected failure semantics, and compare failures by identity rather than relying on the historical pass count. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is the dependency defect a reason to replace the six-plan architecture? | No. Keep the architecture and repair the explicit edges and child decomposition before approval. | Replan the entire Set. Rejected because the requirement partition, normative sequencing rules, and whole-Set verification are coherent; the defects are bounded to execution metadata and item sizing. | Orchestrator `:39-66,79-108`; approved spec `7ckptx` Section 4 | yes |

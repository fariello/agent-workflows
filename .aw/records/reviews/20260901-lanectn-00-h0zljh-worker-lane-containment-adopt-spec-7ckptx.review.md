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
| PR-001 | HIGH | IN-SCOPE | B. Sequencing / G. Plan executability | Orchestrator child table `:57-64`; `y5od1h:8,50-52,98`; `604wra:8,20,145` | The graph described as complete and acyclic is not the graph encoded by the child metadata. `y5od1h` consumes the denied-permission event produced by `lhmrhx` but declares only `nna8yz`. `604wra` says in prose that both `y5od1h` and `lhmrhx` must be complete while its `Item-Dependencies` names only `y5od1h`. A scheduler following metadata can start work before required seams exist. | C:Low; U:Low; S:Medium; F:High; Overall:Medium | FIXED | FIXED 2026-09-01. Confirmed and it was my error: the prose required edges the metadata omitted, so a scheduler reading metadata could have started work early. Added `executed:lhmrhx` to BOTH `y5od1h` and `604wra` via `aw ipd dependencies set`. The orchestrator's partition proof is rewritten to state honestly that it originally checked ACYCLICITY ONLY and never checked metadata-vs-prose agreement, and now verifies BOTH properties; re-verified after correction: zero mismatches across all six children, depths 0/1/1/2/2/3. |
| PR-002 | HIGH | UNDER-SCOPE | G. Right-sizing | Orchestrator `:5-6,57-66`; `cqx5v7:56-59`; `nna8yz:54-57`; `lhmrhx:60-63`; `y5od1h:61-64`; `xdr83v:43-46` | The claim that the Set contains six small, independently executable children is not supported by the execution checklists. Five children compress most of the second driver's implementation into one final “mirror” item spanning multiple behaviors and test seams. Structural item counts therefore understate conceptual size and make partial completion likely. | C:Medium; U:Low; S:Medium; F:High; Overall:Medium | FIXED | FIXED 2026-09-01. Correct, and it is the same trap the maintainer warned about: I complied on E-item COUNT while compressing each second driver's whole implementation into one 'mirror' item. Restructured all five children per the reviewer's preferred remedy rather than by splitting: E-items now place logic in HOST-NEUTRAL functions both drivers call, and each driver item is reduced to wiring plus event-shape adaptation, with re-implementation named a STOP-and-report condition (CID-2). Precedent verified: the twins already share ten modules including `worktree_lease`, `ipd_lifecycle`, and `runner_stop`. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing and regression | Orchestrator `:149-159`; child Required tests sections; Git range `59e68d5a..08ae65cb`, including test changes in `8ced15ce` | The exact `3996 passed` baseline was measured at `59e68d5a`, before later test changes. Treating that count as an execution-time expectation can misclassify an honest count change or conceal an attribution error. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-01. Verified stale before execution: a co-worker's `8ced15ce` added two tests, moving the bare suite from 3996 to 3998. All seven plans now require measuring BOTH invocations at execution time and comparing failures BY TEST NODE IDENTITY rather than by total, with the two invocations' different expected outcomes stated separately. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is the dependency defect a reason to replace the six-plan architecture? | No. Keep the architecture and repair the explicit edges and child decomposition before approval. | Replan the entire Set. Rejected because the requirement partition, normative sequencing rules, and whole-Set verification are coherent; the defects are bounded to execution metadata and item sizing. | Orchestrator `:39-66,79-108`; approved spec `7ckptx` Section 4 | yes |

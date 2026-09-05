# Plan review findings: wpomxa

- Plan-Id: wpomxa
- Reviewed-At: 2026-09-04
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| F-1 | HIGH | IN-SCOPE | Correctness / evidence truthfulness | review_findings.py:805, :187, :640 | THE PLAN'S CENTRAL INDEPENDENCE CLAIM WAS FALSE. F-1, the history and the approval gate all asserted that plan_gating_blocks 'takes an id6 and NEVER reads the subject field', and that the executed:eyh1fu edge was therefore only a file-serialization convenience. It DOES read it: line 805 matches on doc.plan_id, where ReviewDocument.plan_id (:187) is populated from meta['plan-id'] (:640), which is exactly the parser field eyh1fu E-02 renames. An executor trusting the claim could have run this plan before eyh1fu and renamed around a line that was about to change. | complexity Low, usability Low, security Low, functionality Low; overall Low | FIXED | F-1 rewritten to state the real coupling with citations; the history's 'INDEPENDENCE IS MEASURED' sentence replaced with the correction; the approval gate now calls the edge LOAD-BEARING and instructs execution against post-eyh1fu code. The split itself remains justified on separation of CONCERNS, which is unaffected. |
| F-2 | LOW | IN-SCOPE | Traceability | wpomxa F-1 (as authored) | A typo in the original F-1 spelled the sibling plan 'eyhiffu', a nonexistent id6. | complexity Low, usability Low, security Low, functionality Low; overall Low | FIXED | Corrected to eyh1fu. |
| V-1 | LOW | IN-SCOPE | Verification (positive finding) | grep over agent_workflows/*.py at HEAD 9bb47658 | VERIFIED, no defect: the five plan_gating_blocks call sites are exactly as claimed (plan_readiness.py:509, agy_runipd.py:1834, oc_runipd.py:2847, check_engine.py:2070, ipd_set_plan.py:489), and plan_blocks_dependents genuinely has ZERO callers outside its own definition and tests. The threshold default and the four positional call sites (F-4) also check out, so E-01's characterization baseline is correctly identified as the only real guard against a silent semantic change. | n/a | FIXED | No change needed; recorded so the verification is auditable. |

## Round 2

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | HIGH | UNDER-SCOPE | E. Testing and verification / D. Anti-regression | tests/test_plan_readiness.py:736, :759; tests/test_review_findings_cascade.py:303 | THREE SITES NAME THE PREDICATE AS A STRING, WHICH A SYMBOL RENAME CANNOT FIND, and the plan named none of them. Two are mock.patch dotted paths ('agent_workflows.review_findings.plan_gating_blocks'); mock.patch resolves by getattr at call time, so an incomplete rename imports and type-checks cleanly and fails only when those tests RUN, with an AttributeError that looks unrelated to the rename. The third asserts the literal string appears in each runner's source text. The plan listed Scope-Paths for both test modules but its E-02 spoke only of 'call sites', so an executor using an editor's symbol rename would satisfy the letter of E-02 and still break the suite. | complexity Low, usability Low, security Low, functionality Medium; overall Medium | FIXED | E-02 now names all three sites explicitly, warns that mock.patch fails at runtime rather than import, and forbids relying on a symbol rename. Validation requirements and V-02 now demand each be pasted. |
| PR-002 | MEDIUM | UNDER-SCOPE | F. KISS / G. Plan executability | review_findings.py:739 | GatingBlock.plan_id6, the field these predicates POPULATE and an operator reads in a gate message, keeps the plan-only word after the rename, and the plan took no position on it. Silence here leaves the rename visibly half-done and invites an executor either to widen scope unbidden (every construction site plus attribute consumers) or to leave an inconsistency unmentioned. | complexity Low, usability Low, security Low, functionality Low; overall Low | FIXED | E-03 now requires a stated position, with the recorded default being to LEAVE it (renaming a returned record's public attribute is wider than the ruling) and, if changed, to treat it as a third rename with its own evidence. F-8 records the measurement; V-03 requires the statement. |
| PR-003 | LOW | IN-SCOPE | Verification (positive finding, no defect) | grep over agent_workflows/*.py at HEAD 9bb47658; review_findings.py:758-760, :841-843 | VERIFIED WITH NO DEFECT, recorded so the check is auditable: the five plan_gating_blocks call sites are exactly as the plan claims; plan_blocks_dependents genuinely has ZERO callers outside its definition and tests; the threshold default and the four positional call sites hold; the docstrings' two load-bearing claims exist where cited; and the round-1 F-1 correction about doc.plan_id (:805, :187, :640) is accurate. | n/a | FIXED | No change needed. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | Should GatingBlock.plan_id6 be renamed too, or left? | Left, with the position stated explicitly in E-03 and the measurement in F-8. | Rename it in this plan (rejected: a returned record's public attribute reaches every construction site and any attribute consumer, which is wider than the two function names the maintainer's ruling named). Say nothing (rejected: that is the silence PR-002 exists to remove). | review_findings.py:739; the maintainer's 2026-09-04 OQ-01 ruling names two FUNCTIONS only | yes |
| D-2 | Is the string-reference gap a finding on this plan, or an executor detail? | A finding (PR-001), fixed in place by naming all three sites in E-02 and requiring them in V-02. | Leave it to the executor (rejected: mock.patch fails at test RUNTIME, not import, so the failure mode is a green-looking rename that breaks later, which is exactly what a plan should pre-empt). | tests/test_plan_readiness.py:736, :759; tests/test_review_findings_cascade.py:303 | yes |

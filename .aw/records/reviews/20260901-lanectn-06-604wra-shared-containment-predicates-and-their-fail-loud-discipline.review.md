# Review: Shared containment predicates and their fail-loud discipline

- Plan-Id: 604wra
- Reviewed-At: 2026-09-01
- Reviewer: codex/gpt-5
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `08ae65cb`; the plan was committed and unchanged before review. Author-phase IPD lint
returned clean and verified. The single-definition and fail-loud goals are sound, as are the required
AST/import-graph checks and the instruction not to create product callers for predicates reserved to a
later phase.

The plan is not executable as written because it never names the predicates this Set owns, and its
machine-readable prerequisite omits one producer that its own prose requires.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G. Plan executability / C. Clarity | Scope and E-02 `604wra:5-6,35-42`; current predicate ownership in `agent_workflows/wtiso_gate.py:93-102,115-131,159-168` | The executor is told to implement predicates “this Set owns” after reading docstrings, but the plan names none and the current docstrings identify older owners rather than `lanectn` or a child id. The instruction cannot determine which bodies to implement, which to leave raising, or which old ownership labels have been superseded. | C:Medium; U:Low; S:Medium; F:High; Overall:Medium | OPEN | Enumerate each predicate by symbol, current owner label, new owning child or preserved future owner, required body behavior, intended callers, and test. Escalated as blocking OQ-02. |
| PR-002 | HIGH | IN-SCOPE | B. Sequencing | Metadata `604wra:8`; workflow history `:20`; execution gate `:145`; orchestrator child table `h0zljh:62-64` | `Item-Dependencies` names only `y5od1h`, while the plan's prose and orchestrator require both `y5od1h` and `lhmrhx`. A scheduler that reads metadata can start before permission and deadline rules exist, invalidating the consolidation audit. | C:Low; U:Low; S:Medium; F:High; Overall:Medium | OPEN | Add the missing `executed:lhmrhx` edge, or prove and encode an equivalent transitive edge after correcting `y5od1h`. Keep prose and metadata identical. Escalated as blocking OQ-02. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing and regression | Required tests `604wra:92-102`; baseline commit `59e68d5a`; later test changes in `8ced15ce` | The exact suite count is stale, and the plan's central “one definition” proof must report actual symbols and consumers rather than rely on a historical total. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | OPEN | Re-measure the suite at execution time and paste the AST/import-graph inventory showing every named predicate definition and consumer. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the executor infer this Set's predicate ownership from existing docstrings? | No. Require an explicit ownership table in the plan before execution. | Infer that every currently stubbed predicate belongs to this Set, or infer ownership from whichever child first needs a rule. Rejected because current docstrings deliberately assign other phases and E-03 requires unowned predicates to remain fail-loud. | `604wra:35-52`; `agent_workflows/wtiso_gate.py:93-168` | yes |

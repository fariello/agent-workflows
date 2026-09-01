# Review: Bounded missing-input repair without original-checkout access

- Plan-Id: y5od1h
- Reviewed-At: 2026-09-01
- Reviewer: codex/gpt-5
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `08ae65cb`; the plan was committed and unchanged before review. Author-phase IPD lint
returned clean and verified. The plan has the right core shape: workers emit a deterministic token and
continue, coordinator code classifies requests, the decision type cannot represent a live grant, and a
permitted repair creates a verified copy plus a new manifest revision and authorization.

Execution is blocked by a missing producer dependency, a project-generalization hole in secret
rejection, and an oversized twin-driver item.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | B. Sequencing / G. Plan executability | Metadata `y5od1h:8`; E-04 `:50-52`; deferred section `:98`; `lhmrhx:37-63` | E-04 routes a denied host-permission event through the missing-input classifier, but the plan depends only on `nna8yz`. The denied-event seam is owned by `lhmrhx`; without that dependency an executor may start before the event schema and observation path exist. | C:Low; U:Low; S:Medium; F:High; Overall:Medium | OPEN | Add `executed:lhmrhx` to `Item-Dependencies` and update the orchestrator's depth/order proof. Escalated as blocking OQ-02. |
| PR-002 | HIGH | UNDER-SCOPE | B. Security / A. Safe failure | E-03 `y5od1h:46-49`; spec `7ckptx:154-178`; current headings `.gitignore:25-39`; project-agnostic principle in `GUIDING_PRINCIPLES.md` | Secret rejection is derived from two headings in this repository's current ignore file, but the toolkit operates on managed target repositories whose ignore files may omit, rename, or restructure those headings. The plan defines no fail-closed result for absent or malformed sources. An empty derived vocabulary can therefore admit a secret-bearing tracked file. | C:Medium-High; U:Medium; S:High; F:High; Overall:High | OPEN | Obtain a maintainer-approved spec amendment defining a project-agnostic source and fail-closed behavior. Add missing/malformed-source tests before implementation. Escalated as blocking OQ-02. |
| PR-003 | HIGH | UNDER-SCOPE | G. Right-sizing / B. Host parity | E-06 `y5od1h:61-64` compared with E-01 through E-05 `:35-59` | E-06 combines refusal recording with the entire Antigravity token, pause, classification, repair/block, resume, manifest-revision, and authorization cycle. These are independently testable state transitions and cannot be validated reliably through one execution item. | C:Medium; U:Low; S:Medium; F:High; Overall:Medium | OPEN | Split Antigravity work by state transition or implement the cycle in shared host-neutral code and restrict each driver item to event adaptation. Escalated as blocking OQ-02. |
| PR-004 | MEDIUM | IN-SCOPE | E. Testing and regression | Required tests `y5od1h:108-118`; baseline commit `59e68d5a`; later test changes in `8ced15ce` | Historical exact pass counts are stale. Security and state-machine tests are specific, but the full-suite comparison must be refreshed at execution time. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | OPEN | Re-measure the baseline immediately before execution and identify any delta by test name and failure cause. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the reviewer select a secret-pattern fallback without changing the approved spec? | No. Escalate the contract gap and require an approved fail-closed rule before implementation. | Infer a built-in pattern list, treat every ignored path as secret, or accept an empty vocabulary. Rejected because each changes either functionality or security policy beyond the approved text, and accepting empty rules fails open. | Spec `7ckptx:154-178`; `y5od1h:46-49`; project-agnostic principle | yes |

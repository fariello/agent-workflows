# Review findings: plan aqun5z

- Subject-Id: aqun5z
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane after `7562cf9de` (the `xc8nae` review). The plan was committed and unchanged since `5901def55`, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean; `aw ipd coverage aqun5z` reported "ready for review" before and after revisions (attempt 1: the revision changed the fingerprint, which surfaced `IPD-S408` at `review-finalize`; re-running coverage recorded a fresh pass and the lint is clean; rows: 3 -> 3).

Re-verified: the three children exist in `pending/` with matching Order, id6 and filename; each child's `- Item-Dependencies:` names the cfgreloc plan OQ-01 cites (`xc8nae` `executed:xvlemm`, `fo08zx` `executed:xc8nae, executed:6u755v`, `y1e2m9` `executed:fo08zx, executed:ozr356`); `project_schema.Preset` has exactly four presets, so "every other preset" is the six pairs `xc8nae` enumerates; `y1e2m9` owns `make test-all` and `aw sanitize --agent`; `fo08zx` Deferred carries the companion-deletion and history-purge non-goals.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | D. Cross-plan consistency | `xc8nae` OQ-03, E-02 (kept `companion-unsupported`, review `7562cf9de`) | Completion criterion 1 required the planner to emit "not `companion-unsupported`" with owner `xc8nae`, contradicting `xc8nae`'s revised design, in which the blocker stays as an interim gate until `fo08zx` lifts it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Criterion 1 now says populated plan plus interim blocker (owner `xc8nae`); criterion 2 and the Order 02 row assign lifting it to `fo08zx`. |
| PR-002 | LOW | IN-SCOPE | D. Cross-IPD contract | `xc8nae` Scope field list | The cross-IPD field list omitted `companion_dir` and `direction="in-place"`, which Order 02 consumes. | Overall:Low | FIXED | Both added. |
| PR-003 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the resolved-questions statement, the paste-actual-output rule, the scope fence, the path-scoped `aw commit` and the conditional runner/by-hand finalize ownership. | Overall:Low | FIXED | Gate rewritten with every element. |
| PR-004 | LOW | IN-SCOPE | E. Evidence consistency | V-01 vs V-02/V-03 | V-01 offered an alternative command the siblings did not. | Overall:Low | FIXED | Uniform `ls .aw/records/plans/executed/` filtered by id6 plus the `- Status: executed` line. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Who owns removing `companion-unsupported`? | `fo08zx`, in the same change as executor support | `xc8nae` (unsafe interim, see its PR-001) | `xc8nae` OQ-03; `fo08zx` history cross-reference | yes |

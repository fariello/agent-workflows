# Assessment run report - documentation (whole project)

- Date / run ID: 20260704-180630
- Concern: documentation
- Scope: whole project (repo-level user-facing docs + workflow manifest + prompts/)
- IPD written: `.agents/plans/pending/2026-07-04-assess-documentation.md`
- Verdict: adequate for documentation (accurate and near-complete; one stale command example and one small orientation gap)

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| DOC-01 | Medium | Low | novice | `index.md` by-tool run guide still shows retired `/assess-security` / `/assess-performance src/server` command syntax; D31 collapsed these to `/assess <concern>`. A newcomer copying it types a nonexistent command. |
| DOC-02 | Low | Low | novice | `prompts/` is called a "reusable prompt library" but has no index explaining what the four files are, what is current vs. superseded, or how they relate to the shipped workflows. |

(The complete findings list is in `findings.csv`.)

## Proposed plan (summary)

1. Fix DOC-01: rewrite the OpenCode and Claude Code command examples in the "Running a workflow (by tool)" table to the parameterized `/assess security` / `/assess performance src/server` form (leave `/assess-all` alone).
2. Fix DOC-02: add `prompts/README.md` orienting the four prompt files (current vs. historical, relationship to the maintained `.agents/workflows/` framework).
3. Point README:216 and ARCHITECTURE:25-26 at the new `prompts/README.md`.

All three are Low Remediation Risk, docs-only, no behavior change.

## Deferred (with reason)

None. Both findings are Low Remediation Risk and are proposed for fixing.

## Out-of-repo / organizational notes (if any)

None.

## Next step

Review the IPD (optionally run the `plan-review` workflow on it) and approve before execution. This workflow does not execute the plan.

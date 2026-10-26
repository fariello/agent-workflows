# Check S6: Re-Review Decision

Decide whether the review's own edits or unresolved issues need another pass.

## Rules
1. A re-review pass is needed if:
   - `E-*` or `V-*` items were added or removed.
   - `- Scope-Paths:` or `- Item-Dependencies:` changed.
   - Edits made during review introduced new questions, findings, or structural ambiguities requiring another check.
2. In an interactive run, the agent decides the same thing and loops itself at most twice (spec Section 8.3). If the second pass still produces a re-review need, S7 must write `no-go` and add an open question `Blocking: yes` naming what still changed.
3. In a runner run, the runner reads the marker line below and automatically triggers another pass if needed (up to two passes).
4. Do NOT write any verdict output (`- Readiness:`, status change, or verdict-bearing history entry) in this step (MD-15). Verdicts are written in S7 only.
5. If recording a progress note in the plan's `## Workflow history`, record it ONLY as:
   `- <date> review progress (<agent/model>): <note>`
   NEVER use a `/plan-review` label, because `plan_readiness.is_review_history_entry` treats any line labeled `/plan-review` as a review record, which `newest_verdict` would misread as the newest verdict.

## Marker Requirement (Section 8.1)
End your reply with exactly one of these lines as the last non-empty line:

```text
AW-REVIEW: AGAIN
```
or
```text
AW-REVIEW: DONE
```

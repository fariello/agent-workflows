# Review findings: plan qp8fn1

- Subject-Id: qp8fn1
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T032734Z-4093657` at HEAD `07bc746c7`. The plan was
committed and byte-identical to the sealed lane input (rev-6), so no snapshot was needed. `- Kind: child`, so
`IPD-S407`/`IPD-S408` do not apply. `aw ipd lint --phase author --agent` was clean before review.

Re-measured rather than trusted: a temp repo driven through `python3 -m agent_workflows attention --agent` gave
`evidence: ["attention"]`, `findings: 0` with zero drops AND with two drops, while the board printed
"TODO: 2 files waiting in `.aw/inbox/`" (F-01/F-02). A clean `CommandResult` with one `severity="warning"` `Diagnostic`
gave `outcome: clean, findings: 1` (F-03). No pending plan's `- Scope-Paths:` declares `agent_workflows/result_types.py`,
and carrier `3ouico` exists and is `open` (F-04). `agent_schema.sanitize_evidence_item` returns `f"{key}:{val}"` for
`(int, float, bool)`, and `layout --agent` emits `["record_classes:11","logical_roots:4"]` (F-05/F-06). `--json`
does not reach the `if ctx.is_agent:` arm; it renders `render_json` at `schema_version: 4`, so the agent-only edit
cannot move the versioned payload. `Evidence.status` defaults to `verified`, as E-02 assumes. Siblings `nwcf8j` and
`r61br4` are `approved` and still pending, as F-08 states.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G executability / execution contract | plan `## Approval and execution gate` "Perform the terminal transition through the tooled path (`aw ipd finalize`)" | The gate told the executor to run `aw ipd finalize` unconditionally; under `aw oc run`/`aw agy run` the runner owns begin/finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The POST-GATE paragraph now says the runner owns the transition under the runners, and the executor runs `aw ipd finalize` only when executing by hand. |

# Review findings: plan itamry

- Subject-Id: itamry
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `fe2ee961c` in an isolated review lane. The plan was committed and byte-identical to the lane input,
so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean, and `aw ipd coverage itamry`
reported "ready for review".

Evidence:
- Children: `9sbfea` is pending (reviewed earlier in this sweep). `62pkkg` is pending `to-review` with
  `- Item-Dependencies: executed:9sbfea`. Its OQ-04 (composer reuse) is open and non-blocking, as the parent states.
- `aw check plans` reported `check.ipd-carrier-finished-unverified` on this plan for the `7stpjm` row.
  `7stpjm` is `done` via executed `lxcexr`. `3jez8u` is `done` via executed `0obt4k`, and
  `is_safe_descriptive('a\u202eb')` is now `False`, so the "bidi not matched" Deferred prose was stale.
- `0livgf` is `open` (never graduated). Runner precedent from `7stpjm`: "closed by aw agy run: IPD lxcexr executed
  (every IPD carrier is executed ...)", i.e. a runner moves a backlog item to `done` once its last carrier executes.

### IPD-S408 repair loop

- Attempt 1: after the revisions, `review-finalize` reported `IPD-S408`. The edited text no longer matched the stored
  coverage fingerprint `7d1b7115...`. Re-probed with `aw ipd coverage itamry --no-commit`: `pass`, new fingerprint
  `378987f1...`, plus a history `coverage pass` line. Lint was then clean. Child table rows: 2 -> 2 (unchanged).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | G. Carrier currency | `aw check plans` `check.ipd-carrier-finished-unverified`; executed `lxcexr`, `0obt4k` | Deferred carriers `7stpjm` and `3jez8u` have both finished, but the plan cited no evidence for them. The bidi row still claimed the predicate misses bidi controls. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `Carrier-Evidence` on both rows and corrected the prose. The finding clears. |
| PR-002 | MEDIUM | IN-SCOPE | G. Executability | `.aw/records/backlog/done/*7stpjm*` runner-close history line; `0livgf` `- Status: open` | E-02/V-02 required `0livgf` to be `graduated` (NOT `done`). A runner closes the item `done` on the last carrier's execution, so V-02 would fail on the normal runner path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Now accepts `done` (runner) or `graduated` (hand execution), reports `open` as a failure, and forbids writing the status. Completion criteria and Required tests aligned. |
| PR-003 | LOW | IN-SCOPE | E. Verification | Required tests; completion criteria | "Bare full suite green" ignores a non-green base. "Byte-identical to the pre-Set rows" contradicted the conditional bar in `9sbfea` E-04. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Now a failure-set-by-name comparison, and in-bound rows are byte-identical per `9sbfea` E-04. |
| PR-004 | MEDIUM | IN-SCOPE | G. Execution contract | Approval and execution gate | Missing paste-output rule, scope-fence declaration, and conditional lifecycle ownership (the runner retires an orchestrator, a hand execution finalizes). The Readiness sentence was stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all of these elements. |
| PR-005 | LOW | IN-SCOPE | G. Questions | OQ-01/OQ-02 `Owner: this plan` | The owner on the resolved questions was not a recorded decider. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What state should V-02 require of `0livgf` after both children execute? | `done` or `graduated`, named, never written by this plan | `graduated` only (fails on the runner path); `done` only (fails on a hand execution) | `7stpjm` runner-close history; AGENTS.md backlog `graduated` vs `done` semantics | yes |

# Review findings: plan gbizqt

- Subject-Id: gbizqt
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `5bc642bb7` in an isolated review lane. The plan was committed and unchanged (`ef5184d76`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified:
- The stale block in `run_analytics_cli._emit_query_agent` begins with "THE SUMMARY IS RENDERED WITHOUT THE FIELD PROJECTION, DELIBERATELY, TO PRESERVE PAGINATION." and ends above `parts.append(`. The neighbouring "THE SUMMARY CARRIES THE QUERY'S COUNTS, NOT THE STREAM'S" block exists as quoted.
- `agent_schema._PRESERVED_FIELDS = _MANDATORY_FIELDS | {"applied","total","emitted","omitted","next"}`. `6rcby1` is in `executed/`. `kkjrqr` and `3f4ayi` are done. `gygujf`, `mcdvx0` and `okiso1` are executed. Commit `a2f55c630` exists.
- `AgentRenderer.render_summary` re-adds `next` under the "IPD okiso1 E-03" comment.
- F-02 probe re-run: equality is True for `['cmd']`, `['total']`, `['outcome']`, `['a']` and `['next']`, and also for a record without `next`. Note that `OutputContext`/`OutputMode` live in `agent_workflows.result_types`.
- F-05: the outcome test exists as cited and drives `_emit_query_agent` with `fields=["cmd"]` and a `next`.
- `aw runs query overview --agent` is deterministic across two runs, but in this repo it emits a summary with no `next` (`analytics_root_exists: false`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Executability / ordering | plan E-02 "capture ... before E-01" while `E-02 Depends on: E-01`; "as the last act before commit" | E-02 asks for before-E-01 captures and a before-E-01 suite run, but it depends on E-01 and runs last. An executor following the dependency order cannot produce the baseline, which makes V-02 unsatisfiable or tempts a `git stash` reconstruction. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-03/V-03 to take the before-baseline on the unedited tree. E-01 now depends on E-03, E-02 compares against it, and the gate states the order. |
| PR-002 | LOW | UNDER-SCOPE | D. Anti-regression signal | `aw runs query overview --agent` stdout at review: summary `{"total":0,...,"complete":true}` with no `next` | The `overview` captures never exercise the `next`-under-projection path the comment talks about, so on their own they are weak evidence. The suite pin that does exercise it was buried in the bare run. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03/E-02 now run `tests/test_run_analytics_cli.py` before and after and compare the summaries. E-03 explains why `overview` alone is insufficient. |
| PR-003 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate`; `- Scope-Paths:` | The gate lacked the OQ status line, a scope-fence declaration, `aw ipd begin`, the hard-MUST honesty phrasing, and the conditional finalize ownership. Its "move this plan" wording did not name the tooled verb. Scope-Paths omitted the plan itself. The V-01 probe did not say where `OutputContext` imports from. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All of those elements are added, and the V-01 probe now names `agent_workflows.result_types`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Fix the baseline ordering by a new E-item or by reshuffling E-01/E-02 ids? | New E-03 performed first (ids are never renumbered) | Rewrite E-02 to depend on nothing (splits one item across two time points) | plan ids are append-only via `Highest E allocated` | yes |
| D-2 | Accept OQ-01's refinement (counts justify the summary's source, not omission of `ctx`)? | Yes, as authored | Adopt the backlog wording verbatim (would plant a false causal claim) | F-02 probe re-run; `_emit_query_agent` passes counts explicitly | yes |

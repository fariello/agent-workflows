# Review findings: plan u57rfv

- Subject-Id: u57rfv
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `5ce4a3f2e`. The plan was committed and unchanged, so no pre-review snapshot was needed.
`aw ipd lint --phase author --agent` was clean and `aw ipd coverage u57rfv` was ready before revision.

Re-measured at review:
- `gqyold` and `d0lg63` are both in `.aw/records/plans/executed/` with `- Status: executed`. Every V-item has `Result: pass`: gqyold V-01..V-07 and d0lg63 V-01..V-06.
- Scope-Paths are disjoint: gqyold has `tests/test_security_hardening.py, tests/test_host_runner_redaction.py, agent_workflows/security_hardening.py, docs/security.md`, and d0lg63 has `tests/test_packaging_distribution.py`. Both carry `From-Backlog: mflqqf`, and neither carries `Blocks-Release`.
- All four test files exist. `security_hardening.py:116` records the replaced `startswith("127.")` prefix test. `docs/security.md` no longer contains "without dedicated test coverage".
- Backlog `mflqqf` is `- Status: open`. Its 2026-10-06 history says "re-run graduation to complete the handoff". Carriers `go20fk`, `fe6aro` and `wc5c5e` exist in `backlog/open/`.
- `release_gate_work_kinds` is unset in `.aw/config/project.json`, so the default (`bug`) applies.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Evidence accuracy | plan E-02, criterion 1, V-02 "V-01..V-05"; d0lg63 has `- [x] V-06 validates E-06` (split at its review, PR-002) | The orchestrator demanded only V-01..V-05 from d0lg63, so a check could miss the full-suite delta that V-06 owns. | all Low | FIXED | Changed to V-01..V-06 in all three places. |
| PR-002 | LOW | IN-SCOPE | G. Ownership | criteria 4-8 "[Owner: gqyold and d0lg63]" | Single-child criteria named both children as owners, which blurs which record a reviewer should read. | all Low | FIXED | Criteria 4, 5 and 8 are now owned by gqyold, and criteria 6 and 7 by d0lg63. |
| PR-003 | LOW | IN-SCOPE | G. Lifecycle / provenance | Cross-IPD bullet and gate "stays `graduated` until both execute"; `mflqqf` `Status: open` | The plan claimed the item stays `graduated`, but the coverage demotion reopened it. The gate also left closure "the maintainer's call (OQ-02)", which contradicts OQ-02's resolution. | all Low | FIXED | Added a note on the item's current state. The gate now matches OQ-02 and calls re-graduation a backlog-tier act outside this Set. Attempt 1 phrased re-graduation as plan work, and the coverage gate flagged it (`IPD-S408`, "uncovered obligation: graduation must be re-run ..."). Attempt 2 reworded it as a state note, and coverage passed. |
| PR-004 | LOW | IN-SCOPE | G. Gate accuracy | gate "Each child requires its own approval; approving this orchestrator does not approve them" | Stale: both children are already executed. | all Low | FIXED | Restated: approval now authorizes only the two confirmation items. |

### Coverage repair log (`IPD-S408`)
- Attempt 1: `aw ipd coverage --no-commit u57rfv` reported `coverage-fail`: "uncovered obligation: graduation must be re-run once this plan is back at `to-review` or later." Changed: reworded the PR-003 note in both places as a state fact owned by the backlog tier.
- Attempt 2: `aw ipd coverage --no-commit u57rfv` reported "Orchestrator u57rfv is ready for review." `review-finalize` was clean.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is the `mflqqf` close the maintainer's call or resolved? | Resolved by OQ-02 (close `done` once both carriers are executed) | Leave the gate deferring to the maintainer | plan OQ-02 `Status: resolved`; carriers `go20fk`, `fe6aro`, `wc5c5e` exist | yes |
| D-2 | Should the orchestrator re-verify child work (re-run tests)? | No; it quotes child evidence | Re-run the suites | plan gate "Do not perform, re-run, or re-validate a child's work here"; AGENTS.md orchestrator rule | yes |

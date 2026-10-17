# Review findings: plan roi8f1

- Subject-Id: roi8f1
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `7f2d2fac3`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. Orchestrator (`- Kind: orchestrator`, first bullet).
`aw ipd lint --phase author --agent`: `clean`. `aw ipd coverage roi8f1`: "ready for review" before and
after edits (the post-edit run wrote a fresh `Coverage-Fingerprint` `3e5e83749028`); `IPD-S407` and
`IPD-S408` repair loops not needed (zero attempts; S408 surfaced only transiently on the stale
fingerprint and cleared on the re-check). `--phase review-finalize`: `clean`.

Verified at review:
- All five children exist in `pending/` with filenames, Orders and `Item-Dependencies` matching the
  `## Child IPDs` table exactly; `g00ljy` is `reviewed`, the other four `to-review`. The dependency graph
  is acyclic and each child depends on every child whose doc sections it reads.
- Concern figures: `b1mx2w` `## Rollup mutation totals` `10833.66s`; four keys
  (`orchestrate_isolation.execute_merge_and_revalidate...` 3307.22s, `ipd_lifecycle._run_record_committed_paths`
  2362.25s, `runner_shared.make_integration_validation_runner._runner` 1824.22s,
  `check_engine.evaluate_ipd_dependencies` 1801.71s) account for 85.8% of it ("most of it", correct).
- Completion criteria and cross-IPD validation owners point at items that exist in each child (e.g.
  `b83dpg` E-03 (a) 319 reconciliation and (c) `git log --stat ... -- agent_workflows tests`; `lictgf`/
  `f4pbs5`/`pr6lo9` V-02 selection and no-false-unguarded checks).
- The orchestrator's own checklist contains only CONFIRM items; no work exists only on the parent.
- Backlog `lrnh5f` is `graduated`, `Work-Kind: chore`, no `Blocks-Release`; nothing to inherit.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric G (goal vs. children's contracts) | `## Goal` "Every one of the 319 keys ends with a measured guard verdict"; `lictgf`/`f4pbs5` Goal "(only if the cap is hit) `budget-exhausted`"; `g00ljy` E-03 no-probe verdicts and `### Capacity warning` (review PR-001 of `g00ljy`, `P3` est. 8,103s at authoring) | The Goal promised a measured guard verdict for all 319 keys, but the children legitimately end keys with no-probe verdicts and, if a cap is hit, a residual `budget-exhausted`; Order 05 already carries those. The Set could execute fully and correctly while contradicting its own Goal. | all Low | FIXED | Goal restated as the set of verdicts the children actually produce, residual `budget-exhausted` carried by Order 05, with the Order 01 capacity warning as early visibility. |
| PR-002 | LOW | IN-SCOPE | Plan-review Step 4 (execution contract) | `## Approval and execution gate` | Gate lacked the paste-actual-output rule, path-scoped tooled commit, and the unmanaged-run finalize clause (it named only runner retirement). | all Low | FIXED | Added all three, conditional on runner vs. unmanaged execution. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the Set add a sixth child to absorb a possible `P3` overflow? | No; accept residual `budget-exhausted`, carried by Order 05, surfaced early by Order 01's capacity warning | Add a `P3b` probe child now (adds work whose need is unmeasured until Order 01 runs at HEAD) | `g00ljy` E-03 capacity-warning rule and review D-1 there; `b83dpg` E-01 groups `budget-exhausted` as `probe then restore` | yes |

# Review findings: plan qpmq2o

- Subject-Id: qpmq2o
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `f1dbef8a7`. The plan was byte-identical to the lane input and already committed at `fda207d3e` (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 25), test-only verify-first plan.

Verified at the lane HEAD:
- F-01: `git log -1 cbf70e39a` is `work(8bhcd3): Restore behavioral test coverage for run_analytics_telemetry` (2026-10-17 19:34); `git merge-base --is-ancestor cbf70e39a f3afece925` exits 1 (not an ancestor); it is an ancestor of HEAD. `wo21z5` findings doc carries `head: f3afece925...` and the `unguarded` rows for the four keys.
- All four functions exist in `agent_workflows/run_analytics_telemetry.py` (`_validate_label_list`, `_validate_number_map`, `_validate_tool_versions`, `node_pseudonym`); the three validators are reached from `validate_event`.
- `tests/test_run_analytics_telemetry.py` carries module-level `pytestmark = pytest.mark.core`.
- Re-ran all four probes: every one `verdict: killed`, `baseline_failing: 0` (recorded as plan F-04). F-02 and F-03 reproduce.
- `tools/mutation_probe.py` runs `git worktree add --detach <dir> HEAD`, so it probes committed HEAD only.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Executability (probe sees committed HEAD) | `tools/mutation_probe.py` `run_probe` "worktree add --detach ... HEAD" | E-02 said to re-run the probe after adding a test but not to commit first; an uncommitted test is invisible to the probe, so a re-probe would still read `survived`. | all Low | FIXED | E-02 commits via `aw commit qpmq2o` before re-probing; V-02 demands a `head:` at or after that commit. |
| PR-002 | MEDIUM | IN-SCOPE | Validation (evidence sufficiency) | V-01 old text "selection: containing -m core and its verdict: line" | V-01 did not demand `head:`, `baseline_failing: 0` or `newly_failing`, so a probe against a stale HEAD or with a red baseline could pass; no handling for `error`/`invalid` verdicts. | all Low | FIXED | E-01 records `<base>` and treats non-zero baseline or non killed/survived verdicts as not a result; V-01/V-02 demand those fields. |
| PR-003 | MEDIUM | IN-SCOPE | Validation (satisfiable bar) | `conftest.pytest_sessionfinish` budget block; sibling `f6el0l` review measured 34.68s | E-03 required the core tier "within its 30s budget", which the host already exceeds before this plan, making E-03 unsatisfiable for reasons outside scope. | all Low | FIXED | E-03/V-03 require exit 0 and no failures; a budget block is pasted verbatim and counts only if an added test is among the slowest. |
| PR-004 | MEDIUM | UNDER-SCOPE | Execution contract | old `## Approval and execution gate` | Gate lacked the paste-actual-output rule, scope-fence declaration wording with `--scope-ack`, and conditional finalize ownership; it implied a hand move to `executed/`. Production-diff check covered only the working tree. | all Low | FIXED | Gate rewritten as a full execution contract; diff check covers `<base>..HEAD` and working tree. |
| PR-005 | LOW | IN-SCOPE | Executability (placement) | `tests/test_run_analytics_telemetry.py` classes `NodeIdentityTests`, `EventSchemaTests` | E-02 did not name where a restored test belongs. | all Low | FIXED | E-02 names `NodeIdentityTests` for `node_pseudonym` and `EventSchemaTests` for the validators. |

`aw ipd lint --phase review-finalize --agent`: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does a pre-existing core-tier wall-time overrun fail this plan? | No, record it verbatim; it counts only if an added test is among the slowest | Keep the 30s bar (unsatisfiable on this host) | `conftest.pytest_sessionfinish`; sibling reviews `f6el0l`, `92tzo6` same rule | yes |
| D-2 | Keep the plan verification-first rather than restoring tests now? | Keep; conditional E-02 only | Restore redundant tests from `19313eed^` (duplicates `8bhcd3`) | plan OQ-01; F-04 re-probe killed all four | yes |

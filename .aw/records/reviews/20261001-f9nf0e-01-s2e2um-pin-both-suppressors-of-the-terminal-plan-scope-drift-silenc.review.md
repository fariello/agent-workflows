# Review: Pin both suppressors of the terminal-plan scope-drift silence

- Subject-Id: s2e2um
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so I skipped the pre-review snapshot. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

Checked by reading the code at lane HEAD:

- `_RETIRED_PATH_SEGMENTS` includes all three `plans.TERMINAL` members.
- `_iter_type_files` filters with `if not include_retired and is_retired(...)`.
- `check_scope_drift` iterates `_iter_type_files(..., "plans")` with the default `include_retired=False`.
- `_receipt_is_live` is module-level, takes `(repo_root, plan_path, receipt)`, and reads the plan's disposition from its path.
- `tests/support.scope_drift_repo` accepts `plan_dir`.
- `tests/test_check_scope_drift.py` states the bound that OQ-02 relies on, naming `xvp5vx` and `f9nf0e`.

I re-measured F-03, F-04 and F-05 with a probe built on `scope_drift_repo`, with an out-of-scope lane file added. The narrowed attribute was restored in a `finally` block.

| plan_dir | yielded | `_receipt_is_live` | stock findings | yielded with filter narrowed | findings with filter narrowed |
|---|---|---|---|---|---|
| pending | 1 | True | 1 | 1 | 1 |
| executed | 0 | False | 0 | 1 | 0 |
| executed/202609 | 0 | False | 0 | 1 | 0 |
| superseded | 0 | False | 0 | 1 | 0 |
| not-executed | 0 | False | 0 | 1 | 0 |

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | Evidence accuracy | `tests/test_run_finding_reachability.py` `test_unreachable_binding_refusal_fires_under_perturbation`; review run `1 failed, 4 passed` | E-02 cites this test as the precedent to copy, but the test is currently red. The plan does list it as pre-existing elsewhere. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now says to copy the test's restore shape, not its status. |
| PR-002 | LOW | IN-SCOPE | Validation feasibility (E) | plan Required tests: "twice with `-p randomly` seeds differing" | The command did not say how to vary the seed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Now names `--randomly-seed=<N>`. |
| PR-003 | LOW | IN-SCOPE | Execution contract (G) | plan gate "say so and stop, not to re-decide" | This told the executor to stop over a preference, which strands the turn. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The executor now records the view and reports it, and the planned work proceeds. The changed-prerequisite stops (F-04 contradicted, or E-01 inverted) are kept, annotated with the review's re-measurement. |
| PR-004 | LOW | IN-SCOPE | Execution contract (G) | plan "Post-gate lifecycle" | The section did not say whether the runner or the executor owns finalize, gave no scope-fence wording, and had a stale backlog claim. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten. |
| PR-005 | LOW | IN-SCOPE | Metadata | plan OQ-01, OQ-02 `- Owner: none` | Both questions were resolved by the plan author but recorded no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both set to `- Owner: plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Can OQ-01 (which direction to take) stay resolved without a maintainer ruling? | Keep direction (1) plus coverage | Refer it to the maintainer as the backlog item proposed | Review probe: a direct `_receipt_is_live` call returns False for all four terminal placements, so the item's "only (2) makes it testable" premise is false; F-06's cost was not re-timed | yes |
| D-2 | Is the narrowed-attribute perturbation permitted under P16? | Yes | Refuse it as code-pinning | It substitutes a value and asserts on behaviour; it reads no production source | yes |

# Review findings: plan yuhl6o

- Subject-Id: yuhl6o
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `1406157ff`. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and `--phase review-finalize` was clean after revisions.

Re-verified:
- The Set measurement command over `agent_workflows/runner_shared.py` prints the same 41 hits, `UNRETIRED 41`. The AST-equivalence command against `HEAD` prints `AST-DIFFER []`.
- `80db6750c` removed `signal.signal(` forbids from `tests/test_lane_allocation_idempotent.py` (2 hits at `80db6750c^`, 0 at `19313eed^`) (S-38). It also removed `test_neither_driver_tests_a_verdict_by_substring` (S-36) and both telemetry-symbol guards in `tests/test_runner_refork_guard.py` (S-12).
- These survive to `19313eed^`: the `ast.Name` `signal` guard in `test_runner_telemetry_integration.py` (S-02/S-19), `FrontMatterReaderBehaviorTests`, `InRunExecutedDependencyTests`, `_SHARED_NAMES`, `NothingRefusesOnTheBaseline`, `TheTwoMeasurementsAreComparable`, `TheExitCodeIsTheAuthorityAndNotTheList`, `TheExitCodeReflectsTheRealOutcome`, `test_stop_isolated_git_status`, and the `signal.signal(` forbids in `test_runner_stop*.py`.
- No `19313eed` appears near S-07/S-08 (`ABANDONED_STATUSES` comment and `manifest_entry_is_selectable` docstring), contrary to the Findings note. Backlog `mv18lz` is `graduated`.
- The S-16 paragraph already cites the live `tests/test_suite_baseline_direction.py` tests (`test_permissive_direction_is_reachable`, `test_forbidden_direction_is_absent`) correctly.
- Siblings `65d5zf`, `dtelfb`, `z2ugxc` are approved and edit `runner_shared.py`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Evidence / D. Honest documentation | `git show 80db6750c -- tests/test_lane_allocation_idempotent.py tests/test_runner_refork_guard.py` | Several guards these comments describe were removed in `80db6750c`, not `19313eed` (S-12, S-36, S-38 confirmed; more possible). The uniform "deleted in `19313eed`" wording would misdate them in shipped prose, and E-02's RETIRE-PIN evidence (`git show 19313eed^:`) cannot find a guard that is already gone. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Findings F-01. E-02 records `Removed-by` per site with `git log -S` evidence. E-03 names `80db6750c` where it applies, following `dtelfb`. V-02/V-03 demand the proof. |
| PR-002 | MEDIUM | IN-SCOPE | Evidence | `runner_shared.py` `ABANDONED_STATUSES` comment, `manifest_entry_is_selectable` docstring | The Findings note said S-07/S-08 "already mention the deletion further than 3 lines away"; neither does. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Note corrected. |
| PR-003 | MEDIUM | IN-SCOPE | E. Evidence sufficiency / D | E-03, V-03; S-02/S-19 "Keep the name qualified"; S-38..S-41 "It may not" | `UNRETIRED 0` proves only proximity, not truth. Several comments give INSTRUCTIONS justified by the removed guard, and a bare retirement note would leave the instruction reading as enforced. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 keeps the reason as history and states the constraint is no longer mechanically enforced. V-03 demands each passage quoted. |
| PR-004 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | E-02 "41 (plus deltas)" | The bar was the authoring count. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | One row per E-01 hit, re-derived; 41 kept as context, plus the review re-measurement. |
| PR-005 | LOW | UNDER-SCOPE | G. Execution contract | gate; OQ-01 `Owner: none` | The gate lacked the OQ status line, the scope fence, the MUST-paste rule, staged-set verification, the concurrent-edit stop naming the three sibling plans, runner/executor finalize ownership, and the no-`git mv` rule. E-04 had no pre-existing-failure rule, and OQ-01 had no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten; E-04/V-04 strengthened; owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Name `80db6750c` in rewritten prose where it removed the guard? | Yes, naming both commits so the Set measurement still sees `19313eed` | Uniform `19313eed` wording (misdates); change the shared measurement command (touches all three children) | `git show 80db6750c` excerpts; sibling `dtelfb` E-05; same decision recorded on `ev7t1w` round 1 D-1 | yes |
| D-2 | Pre-decide `Removed-by` for all 41 sites in the review? | No; list the confirmed ones and leave the per-site lookup to E-02 | Hard-code a table now (skips the execution-time check) | E-02 evidence rule | yes |

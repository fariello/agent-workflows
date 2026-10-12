# Review findings: plan d22iwu

- Subject-Id: d22iwu
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `d569d3dbc`. Plan committed and byte-identical to the lane input; no
pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; `--phase review-finalize`: `clean` after revision.
Not an orchestrator.

Re-measured every E-item at review. E-01: `tests/test_statusline_behavior.py` `test_box_renderer_invariants_across_swept_inputs`
iterates `generate_pairwise_covering_array(_STATUSLINE_SWEPT_DOMAINS)`; `test_box_renderer_invariants_exhaustive_sweep` carries
`@pytest.mark.slow` and `@pytest.mark.timeout(300)`. E-02: `conftest.py` defines `_DEFAULT_TEST_CPU_TIMEOUT = 60.0`,
`_DEFAULT_TEST_WALL_TIMEOUT = 240.0` and documents `ITIMER_PROF`; `python3 -m pytest tests/test_hang_guard_budget.py` ->
`9 passed in 4.82s`. E-03: `1 passed, 46 deselected in 0.23s`, call `0.04s`. E-04: bare `python3 -m pytest --durations=50`
-> `39 failed, 7180 passed, 2 skipped, 3 warnings in 203.09s`; `grep -n swept_inputs` over the saved output returned nothing
(absent from FAILED and from the slowest-50). Both cited executed plans exist and recommend closing `cqgr7f`; `8sr0or` and
`mu4k1g` are `done`; `cqgr7f` is `graduated` with `Blocks-Release: next`, which this plan inherits.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Evidence accuracy | review run: `Human surface for ('att',) expected exit 2, got 0` in `tests/test_no_project_exit_is_cannot_run.py`; `/tmp/.aw/records` exists; lane exports `AW_RUN_ID`/`AW_ITEM_ID6`/`AW_EXECUTION_ROLE` | F-04 attributed the unrelated failures to "running inside a nested lane worktree". Measured: the no-project failures come from `tmp_path` fixtures climbing (`project_context.find_project_root`) to a stray host `/tmp/.aw/records`; `tests/test_commit_run_trailers_env.py` fails on inherited lane env vars. A wrong cause misleads whoever files the follow-up. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 rewritten with the measured causes and review counts. |
| PR-002 | LOW | IN-SCOPE | Rubric G (live-artifact bar) | E-04, F-03 (`38 failed`) vs review (`39 failed`) | The unrelated FAILED count drifts between runs; E-04 did not state it is not a bar. | all Low | FIXED | E-04 states the count is live context and the only bar is the named nodeid's absence plus duration; V-04 demands the grep and the per-file FAILED count. |
| PR-003 | LOW | UNDER-SCOPE | Rubric G (execution contract) | Gate section | The gate lacked staged-set verification, the paste-actual-output rule, scope-as-declaration wording and conditional finalize ownership. It named an unconditional "lifecycle move" and left the `cqgr7f` close path unassigned. | all Low | FIXED | Gate rewritten: `aw commit d22iwu`, staged check, honesty rule, `--scope-reason`, runner-owned or `aw ipd finalize d22iwu`, close via `runner_shared.evaluate_backlog_close` or `aw backlog set done cqgr7f`. |
| PR-004 | LOW | IN-SCOPE | Evidence accuracy / ownership | `.aw/records/backlog/graduated/...cqgr7f...`; OQ-01 `Owner: none` | F-05 cited `cqgr7f` under `backlog/open/`; it is now `graduated`. OQ-01 recorded no owner for an author-made decision. | all Low | FIXED | F-05 path corrected; OQ-01 owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Close `cqgr7f` as a duplicate via a verification plan rather than new code? | Keep the author's resolution. | New code (rejected: no failing case; isolated call 0.04s, absent from slowest-50). | `mat9bt` / `6ye76g` Carrier-Declined recommendations; review measurements. | yes |
| D-2 | Should this plan file a backlog item for the 39 unrelated failures? | No; record the measured cause only. | File a bug now (rejected: the cause is a stray host `/tmp/.aw/records` and lane env, outside this plan's item). | review FAILED list and failure text. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.

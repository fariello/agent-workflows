# Review findings: plan wfm5iv

- Subject-Id: wfm5iv
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `e15d3e43`. The plan was byte-identical to the lane input and already committed at `5dba203fe` (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 29), new test module only.

Verified at the lane HEAD:
- The three keys exist: `runner_shared.spec_impacts_for_queue`, `runner_shared.expand_selectors`, `runner_shared.route_recovery_turn`; `oc_runipd.route_recovery_turn` is the one-line wrapper the plan says it is; `spec_impacts_for_queue` is re-exported by both drivers.
- `19313eed^` copies of `tests/test_resumedupe.py` and `tests/test_spec_visibility.py` contain every fixture and test the plan names (`git`, `out`, `fixture_repo`, `commit_in_lane`, `ZHR6MC_SUBJECT`, `ResumeRoutingBase`, `PLAN`, `_plan`, `TestSpecImpactsForQueue.QUEUES`, the two `TestDurableRecording` tests); no name collides between the two sources.
- The three mined tests run verbatim at HEAD: `3 passed in 1.01s`.
- `expand_selectors` re-probe: `killed`, `baseline_failing: 0`, `mutant_failing: 9` (F-02 reproduces).
- `tests/test_runner_shared_restored_behavior.py` does not exist; `tests/test_run_gates_restored_behavior.py` exists as the cited pattern.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Validation (satisfiable evidence) | `19313eed^:tests/test_resumedupe.py` `TestDurableRecording` "record[\"inspected_lane_id\"]", "record[\"inspected_branch\"]"; V-01 old pattern `inspect\|...` | V-01 demanded a substring grep for `inspect` return nothing, but E-02 copies a body asserting on `inspected_lane_id`/`inspected_branch`, so a faithful executor could not satisfy V-01. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 uses whole-word `grep -nwE` plus a separate `ast` import check; F-07 records the measured match. |
| PR-002 | MEDIUM | UNDER-SCOPE | Execution contract | old `## Approval and execution gate` "Move the plan to `.aw/records/plans/executed/` only after ..." | Gate implied a hand move to `executed/`; lacked the hard-MUST paste-actual-output rule, the production fence, and scope reconciliation via `--scope-reason`/`--scope-ack`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with `aw ipd finalize` and conditional runner/executor ownership. |
| PR-003 | MEDIUM | IN-SCOPE | Validation (satisfiable bar) | `conftest.pytest_sessionfinish` `session.exitstatus = 1`; plan F-05 bare core 105.48s; sibling `bli2ba` review 34.61s exit 1 | E-03/V-03 asked for "no failures" but gave no rule for the bare run's exit 1, which the pre-existing enforced budget overrun produces with every test green. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03/V-03 accept exit 1 only when it comes solely from the enforced budget block listing none of the new tests. |
| PR-004 | LOW | IN-SCOPE | Validation (evidence sufficiency) | old E-04/V-04 and Required tests; `<base>` never recorded | E-04/V-04 did not demand `baseline_failing: 0` or handle `error`/`invalid` verdicts; `<base>` for the production-diff check was never recorded, and the uncommitted tree was not checked. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 records `<base>`; E-04/V-04 require `baseline_failing: 0` and treat other verdicts as non-results; diff check covers `<base>..HEAD` and the working tree. |
| PR-005 | LOW | IN-SCOPE | Executability (commit hook) | `.pre-commit-config.yaml` ruff hook; `19313eed^` sources import `agy_runipd`, `Palette`, `format_spec_impact_announcement` | Copying fixtures together with their source import lines would leave unused imports and mis-grouped `import pytest`, which the mutating `ruff --fix` hook rewrites and rejects. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 specifies the import groups and the only modules to import. |

`aw ipd lint --phase review-finalize --agent`: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to keep V-01's no-source-reading check without rejecting the verbatim body? | Whole-word grep plus a separate `ast` import check | Rename record keys in the copied test (changes the assertion); drop the check | F-07; `AGENTS.md` TEST OUTCOMES rule | yes |
| D-2 | Does a pre-existing enforced core-budget overrun fail E-03? | No, unless a new test is among the listed slowest | Exit-0 bar (unsatisfiable on an enforcing host) | `conftest.pytest_sessionfinish`; `bli2ba` review D-1 | yes |
| D-3 | Keep E-04's full-core probe (about 6 to 7 minutes per key)? | Keep | Probe only the new file | plan OQ-02; the gap is defined over the full core selection | yes |

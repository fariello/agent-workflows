# Review findings: plan r495ec

- Subject-Id: r495ec
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `520f5006e`. The plan was byte-identical to the lane input and already committed at `5b61fbd28` (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 27), two decorator additions in one test file.

Verified at the lane HEAD:
- `record_history._endpoint_id6`, `append_rename`, `record_rename` exist; `record_rename` calls `_endpoint_id6(to_name)` to pick the key.
- `tests/test_rename_ledger.py` imports `pytest`; `@pytest.mark.core` is on `test_synthetic_key_only_via_case3_path` and `test_synthetic_key_deterministic_derivation` only; the two target tests are in `RecordRenameCaseTests` and call `RH.record_rename` then assert on `read_renames_for`.
- Backlog `hrz4cv` lists the three keys, operators and control files as the plan states.
- Re-probes (plan F-06), all `baseline_failing: 0`: `_endpoint_id6` return-none and `record_rename` raise SURVIVE `-m core tests/test_rename_ledger.py`; `append_rename` raise is killed by `test_synthetic_key_only_via_case3_path`; over only the two chosen tests, both mutants are killed by both tests. Whole-tier probes (about 7 min each) not re-run.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Executability (probe sees committed HEAD) | `tools/mutation_probe.py` `run_probe` "worktree add --detach ... HEAD"; plan old E-04 | E-04 re-probed right after the uncommitted decorator edits. The probe checks out committed HEAD, so it would report `survived` on correct work and V-04 could never pass (or an executor would misread it as a real gap). | all Low | FIXED | E-04 commits through `aw commit r495ec` first; V-04 demands `head:` equal to that commit. Same fix as sibling `di5puw` PR-001. |
| PR-002 | MEDIUM | IN-SCOPE | Validation (satisfiable bar) | old E-04 "within its 30s budget", "no budget breach"; sibling `di5puw` F-04 bare run 34.68s at `16d8abbb8` | The core tier already exceeds 30s on this host before this plan, so the bar was unsatisfiable for reasons outside scope. | all Low | FIXED | Exit 0 with no failures is the bar; a budget block is pasted verbatim and counts only if a marked test is among the slowest. |
| PR-003 | MEDIUM | IN-SCOPE | Validation (evidence sufficiency) | old E-01 "`mutant_failing` >= 1"; old V-01/V-04 | No `head:`, `baseline_failing: 0` or `<base>` demanded, no handling of `error` verdicts, and a count bar. A probe on a red baseline or stale HEAD could pass. | all Low | FIXED | E-01 records `<base>`, rejects non-zero baseline and non killed/survived verdicts; V-01/V-04 demand those fields; count replaced by a `newly_failing` property. |
| PR-004 | MEDIUM | UNDER-SCOPE | Execution contract | old `## Approval and execution gate` | Gate lacked the paste-actual-output rule, scope-fence declaration wording with `--scope-ack`, staged-set check, and conditional finalize ownership; it implied a hand move to `executed/`. Production diff checked only the working tree. | all Low | FIXED | Gate rewritten as a full execution contract; diff check covers `<base>..HEAD` and working tree. |

`aw ipd lint --phase review-finalize --agent`: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does a pre-existing core-tier wall-time overrun fail this plan? | No, record it verbatim; it counts only if a marked test is among the slowest | Keep the 30s bar (unsatisfiable on this host) | `conftest.pytest_sessionfinish`; sibling `di5puw` D-2 | yes |
| D-2 | Accept the authoring whole-tier probes (F-01, F-03) without re-running them at review? | Accept; file-level and per-test probes reproduced, and E-04 re-proves the outcome under `-m core` at execution | Re-run two 7-minute whole-tier probes | plan F-06; E-04 re-probe | yes |

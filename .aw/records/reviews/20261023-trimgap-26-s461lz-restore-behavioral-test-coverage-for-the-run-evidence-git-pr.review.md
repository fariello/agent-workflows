# Review findings: plan s461lz

- Subject-Id: s461lz
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `baeb8d0cc`. The plan was byte-identical to the lane input and already committed at `fa20a9d4f` (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 26), restores one deleted test module and adds one new one.

Verified at the lane HEAD:
- `run_evidence.get_git_head`, `_porcelain_paths`, `dirty_within`, `validate_evidence` exist; `ipd_lifecycle._baseline_ambiguity` imports and calls `dirty_within`, and `ipd_lifecycle` calls `get_git_head` for the receipt head.
- `19313eed^:tests/test_begin_dirty_gate_scope.py` is 319 lines with the six named classes; `test_driver_begin_accepts_the_isolated_declaration` asserts only on `inspect.signature(OC.driver_begin)`. Neither target file exists at HEAD. `runner_shared.begin_baseline_env` (re-exported by `oc_runipd`) and `oc_runipd.driver_begin(..., isolated=False)` exist. The four fixture helpers exist in `tests/test_ipd_lifecycle_cli.py`.
- Control probes with `--extra-test 19313eed:tests/test_begin_dirty_gate_scope.py`: all three `killed`, `baseline_failing: 0` (6/7/12), reproducing F-04 and showing the restored tests pass at HEAD.
- `validate_evidence` core probe: `killed`, `baseline_failing: 0`, 3 newly failing, reproducing F-02.
- F-06 direct-call values reproduce exactly (run inline in a system temp dir).
- Order 26 is shared with `di5puw`; `plans.py` only warns on duplicate Order in a Set, and the two plans touch disjoint files. Not raised.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Executability / checklist coverage | `tools/mutation_probe.py` `run_probe` "worktree add --detach ... HEAD"; old V-03..V-05 demanded core probes; old Required tests "runs after the E-01..E-05 commit" | V-03..V-05 required core-tier probe output, but no E-item committed the files or ran the probes. The probe sees only committed HEAD, so probes run on uncommitted tests would read `survived`; the bare gate and `validate_evidence` re-check also had no owning E-item. | all Low | FIXED | New E-06 owns the commit, the three helper probes, the `validate_evidence` re-check and the bare gate; new V-06 demands their evidence. V-03..V-05 now demand only the per-group `-v` results. |
| PR-002 | MEDIUM | IN-SCOPE | Validation (satisfiable bar) | old V-02 "`18 passed`", E-02 "carries 18 tests"; F-07 bare run 34.93s | Fixed test counts were the bar (an artifact of test organization), and the bare-gate bar ignored the pre-existing core-tier wall-time overrun. | all Low | FIXED | Bars are now "every test PASSED" and named-test absence; overrun reported verbatim and counted only if a test from either module is among the slowest. |
| PR-003 | MEDIUM | IN-SCOPE | Internal consistency | E-01 "a line naming the one dropped test"; V-02 `grep -c "inspect"` returning `0` | A natural provenance line ("pinned via inspect.signature") would make V-02's grep fail on correct work. | all Low | FIXED | E-01 gives example wording and forbids the word `inspect` in it. |
| PR-004 | MEDIUM | IN-SCOPE | Validation (evidence sufficiency) | old V-01 `git status --short` "added"; old probe evidence `verdict`/`newly_failing_total` only | No `<base>`, `head:` or `baseline_failing: 0` was demanded, so a probe on a stale HEAD or red baseline could pass; V-01's untracked-status check is unreachable after a commit. | all Low | FIXED | E-01 records `<base>`; E-06/V-06 demand `head:` after the commit and `baseline_failing: 0`, and reject `error` verdicts; V-01 uses collect-only and `-v`. |
| PR-005 | MEDIUM | UNDER-SCOPE | Execution contract | old `## Approval and execution gate` | Gate lacked the scope-fence declaration wording with `--scope-ack`, staged-set check, and conditional finalize ownership; it implied a hand move to `executed/`. Production diff checked only the working tree. | all Low | FIXED | Gate rewritten as a full execution contract; diff check covers `<base>..HEAD` and working tree. |

`aw ipd lint --phase review-finalize --agent`: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where should the commit-then-probe step live? | A new E-06 / V-06 pair | Fold into E-05 (bundles a second concern); keep probes in V-03..V-05 with no E-item (unreachable, no owner) | plan right-sizing rule; E/V bijection; sibling `di5puw` E-04 | yes |
| D-2 | Does a pre-existing core-tier wall-time overrun fail this plan? | No, record it verbatim; it counts only if a test from either module is among the slowest | Keep implicit bar (unsatisfiable on this host) | plan F-07; sibling `di5puw` D-2 | yes |
| D-3 | Accept the authoring whole-tier F-03 probes without re-running them? | Accept; E-06 re-proves the outcome under `-m core` at execution | Re-run three 4 to 5 minute whole-tier probes | plan F-08; E-06 | yes |

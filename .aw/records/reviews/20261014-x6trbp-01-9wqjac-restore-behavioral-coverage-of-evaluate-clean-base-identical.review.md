# Review findings: plan 9wqjac

- Subject-Id: 9wqjac
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`9642d450f`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize --agent` clean after revisions.

Re-verified at review HEAD:
- `lane_containment.evaluate_clean_base` (line ~3056) docstring carries "(deleted in `19313eed`; no live guard currently asserts this)"; `CleanBaseResult.refuses` is `not self.clean and self.shared_tree`.
- No test references `evaluate_clean_base` (`grep -rn` over `tests/` empty), confirming F-2.
- Probe: for `""`, `" M a.py\n"`, `"M  b.py\nR  c -> d\n"`, `"MM x.py\n D gone.py\n"` the `clean`/`dirty_paths` pair is equal on both paths; dirty inputs give `refuses` False isolated, True shared. `"?? u.txt\n"` gives `clean=False` (F-5 confirmed).
- `runner_shared.evaluate_clean_base_for_launch` runs `git status --porcelain --untracked-files=no` via `_run_git`, which ignores the return code and inherits `os.environ`.
- Deleted test at `19313eed7^:tests/test_dirty_base_gate.py:828` matches the plan's description.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E. Testing / isolation | `runner_shared._run_git` (inherits env, return code discarded by `evaluate_clean_base_for_launch`); `tests/support.clean_git_env` | E-02 did not require stripping `GIT_DIR`/`GIT_WORK_TREE`/etc. Under a git hook (pre-commit runs tests here) those can redirect `git status` to another repository, and a failed status reads as `clean=True`, so the test could silently pass against the wrong tree. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires the local git env vars removed around the calls and prefers `tests.support.init_repo`; V-02 demands the excerpt. |
| PR-002 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate told the executor to move the plan to `executed/` itself, with no scope-fence statement, honesty rule, or runner/hand finalize split. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Full execution contract written. |
| PR-003 | LOW | IN-SCOPE | Evidence | `lane_containment.py:1530` same phrase above `MISSING_INPUT_VERDICT_REFUSED` | E-03's `rg` check would still match the unrelated `test_missing_input_repair.py` comment, making its expected outcome ambiguous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 states that hit is out of scope and exactly one match remains. |
| PR-004 | LOW | UNDER-SCOPE | E. Testing | Required tests mutation step | The mutation check did not prove the source was restored. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Before/after `sha256sum` added to the mutation step and V-01. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Also fix the identical stale phrase about `test_missing_input_repair.py`? | No, leave it (different property, own backlog/S-site) | Fix it here | plan Deferred "other S-* sites"; `lane_containment.py:1530` | yes |
| D-2 | Fixture helper | Prefer `tests.support.init_repo` | Re-create the deleted `_init_repo` | `tests/support.py:281` | yes |

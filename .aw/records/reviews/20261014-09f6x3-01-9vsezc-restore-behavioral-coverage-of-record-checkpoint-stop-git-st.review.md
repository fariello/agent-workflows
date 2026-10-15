# Review findings: plan 9vsezc

- Subject-Id: 9vsezc
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `d8bfaca15` in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified by calling both host wrappers against real temp git repos built with `_init_clean_repo`:
- The dirty lane records `'?? dirty_file.txt'`, `level` 3, `stopped_deliberately` True, `item["stopped"]` is the returned record, and exactly one `events.jsonl` line carries the item id6.
- `item["worktree"]` and `attempts[-1]["worktree"]` both observe the lane. `work_dir` beats `item["worktree"]`.
- Fallback with a clean main gives `''`. Fallback with a dirty main gives `'?? main_dirty.txt'`.
- `mock.patch.object(<host>, "git_status", runner_shared.git_status)` reproduces the original defect: `<unobserved: git_status() missing 1 required keyword-only argument: 'run_checked'>`.
- `rg -n _record_checkpoint_stop tests/` returns nothing, which confirms F-2.
- yuhl6o S-33 lists `test_stop_isolated_git_status` as surviving to `19313eed^`, so `19313eed` is the correct deletion commit.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Test strength | E-02 fallback case "`git_state` does not contain `dirty_file.txt`"; review probe | With a clean main, the fallback case asserted only an absence. An `<unobserved: ...>` error string also satisfies it, so the case could not detect the defect class this plan exists for. Precedence between `work_dir` and `item["worktree"]` was also untested. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now uses a dirty main (`main_dirty.txt`) and a dirty lane, asserts a positive observation in all four cases (adding `work_dir` over `item["worktree"]`), and rejects an `<unobserved` prefix. Added F-5. |
| PR-002 | MEDIUM | IN-SCOPE | E. Verification safety | Required tests: "temporarily bind ... in a scratch copy ... revert" | The mutation check offered a production-source edit as one option, which risks committing a mutated file. Its suggested mutant (an arbitrary raise) also did not reproduce the actual defect. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Now an in-process patch to the unbound `runner_shared.git_status`, which reproduces the exact `'run_checked'` defect (demonstrated). V-01 demands the failure value and a clean `git diff --stat`. |
| PR-003 | MEDIUM | UNDER-SCOPE | G. Honest documentation | `runner_shared._record_checkpoint_stop` docstring "no live guard currently asserts this"; sibling `90yi49` E-04 | The plan deferred the docstring repoint even though its own tests make the sentence false the moment they land, and recorded no carrier for that deferral. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-04/V-04 (docstring-only repoint), added `agent_workflows/runner_shared.py` to Scope-Paths, and removed the deferral. Added F-6. |
| PR-004 | MEDIUM | IN-SCOPE | G. Lifecycle gate | `check.ipd-uncarried-obligation` on this plan at base | The Deferred rows named no carrier, so the plan would fail its own pre-transition gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The docstring row was removed (now E-04). The `_record_forced_stop` row has `Carrier-Declined` with its reason. The warning is cleared. |
| PR-005 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | Required tests "`python3 -m pytest` passes"; V-03 "`N passed` ... no new failures" | A fully green bare suite was the bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Now a base-commit comparison by failing test id. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract / 3.1(5) | Approval gate; OQ-01 `Owner: none` | The gate lacked the honesty rule, `aw ipd begin`, staged-set verification, a scope fence and runner-conditional finalize. OQ-01 named no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten and owner recorded. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Repoint the docstring in this plan or defer it? | In scope (E-04) | Defer with `Carrier-Declined` (leaves a sentence the plan itself makes false); file a backlog item (manufactures a chore for a one-line edit) | F-6; sibling `90yi49` E-04 precedent; backlog `09f6x3` | yes |
| D-2 | Which mutant proves falsifiability? | Patch each host's `git_status` to the unbound `runner_shared.git_status` | Arbitrary raising lambda (does not reproduce the recorded defect); source edit (risks commit) | review probe output (F-5) | yes |
| D-3 | Fallback assertion shape? | Dirty main, positive `main_dirty.txt` observation | Clean main with absence assertion (blind to `<unobserved`) | review probe (F-5) | yes |

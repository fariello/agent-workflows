# Review: Adopt the shared repo-relative POSIX renderer across the remaining callers

- Subject-Id: 61lsze
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `6515a6d95`, clean tree, target plan committed unchanged (snapshot skipped).
`aw ipd lint --phase author` conforming before revisions; `--phase review-finalize` conforming after.

Verified TRUE by probe: F-01 (out-of-root `_repo_relative` returns an absolute path); F-03 (the
`attention._rel_posix` callers named do not catch `ValueError`); F-05 (with an injected location,
`probe_artifacts(sym_root)` keeps a real-spelled and an out-of-root location ABSOLUTE); F-07 (the
`layout_inventory._repo_relative` callers `within_repo`, `_git_state`, `repo_relpath`); F-08 (the five
named suites, `63 passed`). Delegating `attention._rel_posix` changes nothing on this repository: a full
`attention.scan` with and without delegation returned identical items (2751) and identical drift, at
equal wall time (3.26s vs 3.30s).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A. Correctness (identity aliasing) | `ipd_lifecycle._finalize_transaction` (`wt_plan = coord.path / plan_rel`, `owned_paths = [plan_rel, dest_rel]`); `ipd_lifecycle._release_own_plan_edit_before_landing` (`plan_abs = repo_root / plan_rel`, `git checkout HEAD -- plan_rel`); probe: `selectors.resolve(root_a, "plans", <abs path in root_b>)` returns the root_b path; `repo_relative_posix(root_b/.aw/records/plans/pending/N, root_a)` gives `.aw/records/plans/pending/N` | The plan treats `_repo_relative` as display text, but `plan_rel` is an identity key for file writes, a `git checkout`, and the finalize commit. After E-01, an out-of-root plan under a records segment renders to the same text as an unrelated in-root plan with the same name, so finalize could silently overwrite, restore, or commit the WRONG file. Today the absolute fallback at least points at the right file. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added E-06/V-06: `run_begin`/`run_finalize` refuse (`EXIT_CANNOT_RUN`) an out-of-root plan path before any work, judged by a round-trip identity check that was demonstrated to accept in-root, symlinked-file, and symlinked-root cases; added a behavioral refusal test, F-10, a stop condition that E-01 must not land without E-06, and the Scope update. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness / CLI output contract | `ipd_lifecycle.receipt_dir` anchors on `checkout_control_root`; lane probe: receipt is under the main checkout's `.aw/state/ipd-lifecycle/`; `_repo_relative` gives an absolute path, plain delegation gives `61lsze.receipt.json` | `receipt_path` is outside `repo_root` in EVERY managed lane, not only in an edge case. Plain delegation would replace a leak with a bare, uninformative file name. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now renders `receipt_path` against `checkout_control_root(repo_root).parent`, giving `.aw/state/ipd-lifecycle/<id6>.receipt.json`; recorded as F-09; V-01 requires the linked-worktree observation. |
| PR-003 | MEDIUM | IN-SCOPE | D. Anti-regression (vacuous test) | Probe: a real `check.id6-collision` under both `real` and `sym` roots already renders repo-relative at HEAD | E-05 drove doctor parity "through `check_engine.check_collisions`" with a real `Drift`. Real rules emit the root-spelled path that HEAD's inline block already handles, so such a test cannot fail at HEAD and the V-05 revert demand could not be met. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 and V-03 now inject locations by patching `check_engine.check_collisions` with a stub returning a `Drift`; the reason is stated with the measured probe. |
| PR-004 | LOW | IN-SCOPE | G. Executability (validation breadth) | V-01 ran a `-k` subset of `tests/test_ipd_lifecycle_cli.py` | E-01 names `tests/test_ipd_lifecycle_cli.py` and `tests/test_orchestrator_retirement.py` as its constraint, but V-01 ran two tests from one of them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now runs both files in full. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | Original gate text; Scope-Paths | The plan file was missing from Scope-Paths, and nothing barred `--no-verify` or required scratch reverts to be restored before commit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Plan file added to Scope-Paths; gate states the scratch-restore rule, no `git stash`, no `--no-verify`, and the staged-set check. |
| PR-006 | LOW | OVER-SCOPE | C. Architecture (scope clarity) | `doctor._categorize_drift` has a third `is_relative_to(repo_root)` block (conflict-target text) | An executor sweeping `doctor.py` for the pattern might also "fix" this unnamed site. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now explicitly excludes it as not named by `rd6ei9`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to stop an out-of-root plan from aliasing an in-root `plan_rel`? | Refuse at the `run_begin`/`run_finalize` entry with a round-trip containment check. | (a) Keep the absolute fallback in `_repo_relative`: rejected, it is the leak `rd6ei9` targets and still breaks `git checkout -- <abs>`. (b) Guard inside `_repo_relative` (raise): rejected, many internal callers would need new handling. (c) Make `selectors.resolve` refuse out-of-root paths: rejected, wider blast radius than `rd6ei9`. | `ipd_lifecycle._finalize_transaction`; `_release_own_plan_edit_before_landing`; selectors probe | yes |
| D-2 | What should `receipt_path` be relative to? | The checkout that owns the receipt (`checkout_control_root(repo_root).parent`). | `repo_root` (bare name in lanes, uninformative); absolute (violates the leak posture). | `ipd_lifecycle.receipt_dir` docstring (backlog `dh0uno`); `docs/cli-output-contract.md` "Path Sanitization and Leak Posture" | yes |
| D-3 | Is E-06's new refusal a scope decision needing the maintainer? | No; recorded here. It only refuses an input that would otherwise corrupt the wrong file, and in-root behavior is unchanged. | Raise a blocking OQ: rejected as reversible and safety-only. | Plan Scope OUT clause (no change to normal in-root operation) | yes |

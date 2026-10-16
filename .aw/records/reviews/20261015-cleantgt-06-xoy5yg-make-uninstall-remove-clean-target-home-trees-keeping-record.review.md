# Review findings: plan xoy5yg

- Subject-Id: xoy5yg
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `82e484b00`. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author` was clean before the edits.

No cleantgt child is executed at this HEAD. The home layout this plan uninstalls exists only as the reviewed sibling plans describe it (`4gn1ka`, `qk0ew6`, `3m8aix`). The findings below therefore come from reading `engine.uninstall_repo`, `worktree_lease` and `runner_shared` against those plans, not from a scratch run. E-01 re-measures everything.

### Evidence verified

- `engine.uninstall_repo`:
  - its home `config/`+`state/` branch;
  - step 6 `manifest_rel = manifest_path.relative_to(repo_root).as_posix()`;
  - step 7's `.aw` prune.
- `plan_uninstall` composes `dest = repo_root / rel`.
- `plan_deep_cleanup`/`run_deep_cleanup` walk `repo_root / root` over `_DEEP_CLEANUP_ROOTS`.
- `DeepCleanupPlan.filtered` classifies with `root.startswith((".aw/records", ".agents"))`.
- `cli._run_uninstall` `has_footprint`.
- `cli._offer_commit_uninstall`'s `if not use_git or not changed: if changed: ... "Deletions are STAGED"`.
- `worktree_lease`:
  - `teardown_worktree`, `inspect_lane` and the `LaneState.reclaimable` docstring;
  - `lane_owned_by_other_live_process` (fail safe);
  - `_registered_worktrees`, keyed by branch, which drops detached entries.
- `runner_shared`:
  - `peer_drivers` (`PEER_LIVE`/`PEER_UNKNOWN`);
  - `remove_suite_baseline_checkout`, which deletes no branch.
- `--force` help: "Also remove files you have edited (drifted)".
- `3m8aix` E-08 test names `test_case_k`..`n`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A. Correctness | `engine.uninstall_repo` step 6 `manifest_path.relative_to(repo_root)`; `4gn1ka` E-03 routes `manifest.resolve_manifest_path` to the home system dir | Once the manifest lives at home, step 6 raises an uncaught `ValueError` on every clean-delta uninstall, after the owned files are already deleted. The plan never mentioned this step. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 branches the manifest-last step for an out-of-tree manifest. E-01 measures it, and V-05 demands exit 0 with no traceback. |
| PR-002 | HIGH | IN-SCOPE | A. Correctness / recovery | `_is_clean_delta_install` reads the stored home `config/`; F-05 (partial uninstall) | The mode predicate reads the very config the uninstall deletes. A mid-run re-evaluation, or a retry after a partial failure, sees "not clean-delta", so the leftover `system/`/`worktrees/` can never be cleaned. That is the exact F-05 failure the plan set out to fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now snapshots once before removal (`home_trees=` passed into `uninstall_repo`) and adds derived-id recovery. E-05 removes `config/` last, and `test_case_u` covers recovery. |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness | `LaneState.reclaimable` docstring "PROVABLY RECOVERED ... `commits_ahead` ... never returns to zero after a merge" | E-03 classified with `state == LANE_HOLDS_WORK`, so every already-merged lane would refuse uninstall without `--force`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Classification now uses `.reclaimable`; `test_case_q` adds a merged lane and E-08 adds mutation (c). |
| PR-004 | MEDIUM | UNDER-SCOPE | A. Correctness | `qk0ew6` E-06 suite baselines under `<project_dir>/state/suite-baselines/`; `_registered_worktrees` keyed by branch; `remove_suite_baseline_checkout` | A detached baseline checkout under home `state/` would be deleted by directory removal, leaving a registered-but-missing worktree in the target `.git`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The preflight scans all registered worktrees under `project_dir`; `detached` entries are removed through `remove_suite_baseline_checkout`. |
| PR-005 | MEDIUM | UNDER-SCOPE | A. Concurrency | `runner_shared.peer_drivers` | Only lanes were checked. A live driver between items, holding no lane, can allocate a lane or write home `state/` while the uninstall deletes it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 refuses on `PEER_LIVE`/`PEER_UNKNOWN`. Added OQ-03 (resolved) and `test_case_s`. |
| PR-006 | LOW | IN-SCOPE | B. Leak / F. UX | `cli._format_cleanup_root`; `DeepCleanupPlan.filtered` prefix test | Home roots would print absolute machine paths and be misfiled as "other scaffolding". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 renders paths `~`-relative and classifies by the plan-time `is_records` flag; `test_case_t` asserts no absolute prefix. |
| PR-007 | LOW | IN-SCOPE | F. Honest output | `cli._offer_commit_uninstall` prints "Deletions are STAGED" when `changed` is non-empty, even with `use_git=False` | Home-path removals appended to `changed_out` would print a false "staged" message. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04/E-05 never append home paths; V-04 and `test_case_o` assert the line is absent. |
| PR-008 | LOW | IN-SCOPE | E. Test organization | `3m8aix` E-08 adds `test_case_k`..`test_case_n` to the same file | Test names `m` and `n` collided. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Renamed to `o`..`u`. Lanes are created with `allocate_worktree`, which avoids needing an approved plan in home records. |
| PR-009 | LOW | IN-SCOPE | G. Traceability | `check.ipd-uncarried-obligation` on `3m8aix` for the identical `or061f` carrier (that plan's PR-009) | A spec id is not an accepted carrier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Carrier changed to `kvwwt0`. Also updated the gate (OQ statement, blocked-accessor rule) and the cohesion rationale. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should a partial uninstall be recovered when the stored policy is gone? | A snapshot before removal, plus derived-id recovery, with `config/` removed last | Re-derive from the preset (forbidden); leave leftovers to the user | U3 manifest-last precedent in `uninstall_repo`; `_derive_project_id` is what `persist_project_policy` records | yes |
| D-2 | Should uninstall refuse while a driver is live but holds no lane? | Yes, via `peer_drivers`, failing safe on UNKNOWN | Lanes only | `peer_drivers` three-valued contract; `lane_owned_by_other_live_process` fail-safe precedent | yes |
| D-3 | How should test lanes be created? | `worktree_lease.allocate_worktree` in-process | `aw work begin` (needs an approved plan resolvable from home records) | `work_cmd.run_work_begin` validates the plan before allocating | yes |

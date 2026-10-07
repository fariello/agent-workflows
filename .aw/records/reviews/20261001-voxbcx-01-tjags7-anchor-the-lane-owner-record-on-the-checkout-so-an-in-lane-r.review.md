# Review: Anchor the lane owner record on the checkout

- Subject-Id: tjags7
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `c8908e61b` in the sweep lane. The plan was committed and unchanged against its sealed lane input, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before and after the edits.

Re-measured on a scratch checkout (real `git worktree` via `allocate_worktree`, uid 1000):

- Asymmetry (F-1) still holds. The in-lane owner path is `repo/.aw/worktrees/lane1/.aw/worktrees/.owners/lane1.json` and does not exist; `receipt_dir(main) == receipt_dir(lane)` is True.
- No-migration property (F-3) still holds. Current path equals the anchored `checkout_control_root(r)/worktrees/.owners/lane1.json` for main=True, lane=False, nongit=True.
- Inversion (F-2) still holds, with a live child owner. From main: `safe=False`, `other_live=True`, `owner_live=True`. From the lane: `safe=True`, `other_live=False`, `owner_live=None`.
- E-03 premise. Absent record gives `(True, 'no owner record; unclaimed')`. Owners dir `chmod 0` gives `(True, 'no owner record; unclaimed')`, with `Path.exists()` returning False. Owners dir replaced by a file gives `(True, 'no owner record; unclaimed')`.
- E-03 classifier demonstrated on a scratch directory with an `os.stat` + parent-`S_ISDIR`/`os.access` classifier: no dir -> absent, empty dir -> absent, present -> present, `chmod 0` -> unreachable, dir-as-file -> unreachable.
- F-7 fixed independently. Plan `3mv7li` executed and `cjrjtu` is done; with one unmerged lane commit, `reclaimable` is False from both roots.
- `tests/test_lane_allocation_idempotent.py` is still absent. All seven named adjacent test files exist. `test_reintegrate_lane_ownership_ambiguity_and_error_refusals` is at `tests/test_runner_shared.py:4423`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | IN-SCOPE | Correctness / testing (A, E); HOW question undemonstrated | `agent_workflows/worktree_lease.py:779` `lane_is_safe_to_adopt` `if _owner_record_path(...).exists()`; measurements above | E-03 says "when the owners DIRECTORY itself cannot be reached or read" but names no mechanism. The existing `.exists()` test returns False for both a `chmod 0` directory and a directory replaced by a file, so an executor extending it would make no change. V-03 could then pass with a construction that never fires. `lane_owned_by_other_live_process` carries the same `.exists()` collapse and answers "not owned" for an unreachable store, and the plan did not address it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now specifies the `os.stat` classifier (only `FileNotFoundError` counts as absent; a missing parent dir is absent; a non-dir or inaccessible parent is unreachable) and applies it to `lane_owned_by_other_live_process` as well, failing safe to True. V-03 requires both constructions plus a pre-change baseline. E-04 (d) uses the file-replacement construction, which works for any uid, and skips `chmod` under root. |
| PR-302 | MEDIUM | IN-SCOPE | Evidence currency | `.aw/records/plans/executed/20261002-cjrjtu-01-3mv7li-...ipd.md` `- Status: executed`; backlog `cjrjtu` done | F-7, the Under-scope text and the execution gate described `cjrjtu` as live and told the executor to expect `reclaimable=True` in-lane. It is fixed. | all Low | FIXED | Added an update to F-7, rewrote the Under-scope and gate text (a wrong reading is now reported as a `3mv7li` regression), and added Carrier-Evidence. |
| PR-303 | LOW | IN-SCOPE | Executability | `OWNERS_SUBDIR = WORKTREES_SUBDIR + "/.owners"` | E-02 did not state the anchored path composition. A naive `checkout_control_root(r) / OWNERS_SUBDIR` would double the `.aw`. | all Low | FIXED | Spelled out `checkout_control_root(r)/worktrees/.owners/<lane>.json`, derived from `OWNERS_SUBDIR`. |
| PR-304 | LOW | IN-SCOPE | Test robustness | `ipd_lifecycle.checkout_control_root` memo (`_CONTROL_ROOT_CACHE`) | The fallback and the memo were not mentioned. | all Low | FIXED | E-02 now covers the import-failure fallback and when `clear_checkout_control_root_cache()` is needed. |
| PR-305 | LOW | IN-SCOPE | Validation commands | `pyproject.toml` addopts; V-04(1) | The addopts quote was stale (missing `not livecorpus`), the node id was elided with `...`, and V-04(1) needs per-case output. | all Low | FIXED | Corrected the addopts quote, switched to locate-by-name, and added `-o addopts=""` to V-04(1). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should "unreachable" be distinguished from "absent"? | `os.stat` classifier; only `FileNotFoundError` counts as absent; a missing owners dir counts as absent | `Path.exists()` (measured blind); try-`os.listdir` (fails on an absent dir, conflating it with unreachable) | scratch demonstration above; `allocate_worktree` first-allocation and empty-lane adoption need absent to stay adoptable | yes |
| D-2 | Should `lane_owned_by_other_live_process` also be fixed under E-03? | Yes, fail safe to True | Leave it (keeps the same class of inversion the plan exists to close) | its own docstring "Undeterminable liveness counts as owned (fail safe)"; plan Goal "a store that cannot be read is never reported as a store with nothing in it" | yes |

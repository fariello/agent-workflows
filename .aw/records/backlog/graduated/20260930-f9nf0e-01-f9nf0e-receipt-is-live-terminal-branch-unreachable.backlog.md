- Id: f9nf0e
- Status: graduated
- Graduated-To: f9nf0e
- Set: f9nf0e
- Priority: low
- Work-Kind: chore
- Summary: check_engine._receipt_is_live's terminal-plan branch is unreachable from its only caller: _iter_type_files filters a terminal plan out before its receipt is read

## Workflow history
- 2026-10-01 graduated (aw backlog): graduated by run run-20261001T221834Z-1991716: s2e2um
- 2026-09-30 created (aw backlog): Filed by /plan-review of plan qqg41f 2026-09-30 from a measured finding (F-09).

MEASURED 2026-09-30 while reviewing plan `qqg41f` (restoring check.scope-drift behavioral coverage).

`check_engine._receipt_is_live` rejects a receipt whose plan sits in a TERMINAL lifecycle directory (`plans.TERMINAL` = executed/superseded/not-executed). That branch cannot be reached from the function's ONLY caller in `agent_workflows/`, which is `check_engine.check_scope_drift`:

  * `check_scope_drift` iterates `_iter_type_files(repo_root, \"plans\")` with the default `include_retired=False`.
  * `_iter_type_files` skips any path for which `check_engine.is_retired` returns True.
  * `is_retired` returns True when ANY path segment is in `_RETIRED_PATH_SEGMENTS` = {archive, done, executed, not-executed, parked, shipped, superseded}, which is a strict SUPERSET of `plans.TERMINAL`.

So a terminal plan is never yielded to the loop, its receipt is never read, and `_receipt_is_live` is never called on it. PROOF: replacing `_receipt_is_live` with `lambda *_: True` (deleting the terminal rejection outright) leaves a terminal-plan arrangement with an out-of-scope lane change SILENT, and `_iter_type_files` returns `[]` for both a `executed/` and a `executed/YYYYMM/` sharded placement.

WHY THIS IS A chore AND NOT A bug: the OBSERVABLE contract is correct and unchanged. A terminal plan gets no drift advisory, which is exactly what the rule intends; the redundancy is in HOW that is achieved. Nothing a user can perceive differs, so per AGENTS.md's perceptibility test this is not a defect. It is filed because it is a latent trap rather than a live fault: the branch carries a substantial docstring explaining a decision nothing exercises, and a future change to `_iter_type_files`' retired filtering (or a second caller of `_receipt_is_live`) would silently change which mechanism is load-bearing.

CANDIDATE DIRECTIONS (none asserted): (1) leave the branch as intentional defense-in-depth and say so in its docstring, naming the outer filter as the actual suppressor today; (2) pass `include_retired=True` in `check_scope_drift` so liveness becomes the real gate and the branch is exercised; (3) remove the terminal branch and document that the retired-path filter owns the case. Direction (2) is the only one that makes the branch testable, and it changes which mechanism is authoritative, so it needs a maintainer decision rather than an agent's.

NOT FIXED BY PLAN `qqg41f`: that plan excludes changing the rule by construction, and its E-04 rows were corrected to assert the OBSERVABLE contract and to record the measured suppressor honestly rather than claiming to cover this branch.

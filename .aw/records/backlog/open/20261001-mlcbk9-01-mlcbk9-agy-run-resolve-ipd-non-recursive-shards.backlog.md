- Id: mlcbk9
- Status: open
- Blocks-Release: next
- Set: mlcbk9
- Priority: medium
- Work-Kind: bug
- Summary: Make agy_run.resolve_ipd recursive so sharded plans resolve

## Workflow history
- 2026-10-01 created (aw backlog): Make agy_run.resolve_ipd recursive so sharded plans resolve

`agy_run._candidate_plans` enumerates candidate plans with non-recursive `plans_base.glob("*.md")` over `.agents/plans/<state>` and `.aw/records/plans/<state>`, so a plan that has been moved into a monthly shard is invisible to `resolve_ipd`.

Measured in a temp repo at HEAD `e132c1f43`: with an executed plan at `.aw/records/plans/executed/202609/20260901-set-01-ab12cd-thing.ipd.md`, `resolve_ipd(root, "ab12cd", ("executed",))` raises `No IPD matching 'ab12cd' found in plan states: executed.` while the exact full path resolves (through the `direct.is_file()` early return, which never consults the glob).

This is DORMANT, not absent: measured at the same HEAD, all five plan disposition dirs in this repository have zero subdirectories, so nothing is broken yet. `plans_archive` creates `YYYYMM/` shards inside each terminal dir BY DESIGN (`_shard_target`), and its module docstring states that "the INDEX (Order 03) is recursive, so sharded plans stay visible" - a guarantee `_candidate_plans` does not share. The first `aw archive plans --apply` makes it live.

Why it is worse than a plain resolution error: `resolve_mode_and_target` calls `resolve_ipd` inside `try: ... except ScriptError: pass` on the positional auto-detection path, falling through to `return "prompt", target_str, ""`. So a valid id6 for a sharded plan is not reported missing, it is silently executed as an inline prompt.

Relationship to `8jl0rx`: that item fixes the same class of defect in the sibling `resolve_spec`, where the fix is to delegate to the existing canonical `specs._spec_files`. Plan `a6ootg` deliberately scopes `resolve_ipd` OUT (its F-06), because plans have no `_spec_files` equivalent to delegate to, so fixing this requires first choosing or creating the canonical plan-enumeration source (candidates exist: `plans_index`, `plans_archive` and `ipd_lint` all already walk plans recursively with `rglob`). Note the `specs._spec_files` docstring's warning applies here too: a recursive walk must also filter through `artifact_core.is_ignored_path`, because non-recursion masks the absence of an ignored-path filter.

# Review findings: plan m734rl

- Subject-Id: m734rl
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `7e9129224`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before review; `--phase
review-finalize`: `clean` after revision. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply.

Verified: `agy_run._candidate_plans` uses `plans_base.glob("*.md")` per state dir; `resolve_ipd`'s direct branch
checks `rel.parts[0] in states`; the ambiguity renderer is `p.relative_to(root)`; `plans_index.scan_plans` is
`rglob` + `plan_entry`, whose first line filters `_EXCLUDE_NAMES` and `is_ignored_path`; `plan_entry` takes
`ignored_dirs` keyword-only "to prevent redundant git subprocesses (F-6)"; `artifact_core._cached_ignored_dirs` is
`lru_cache`d on root plus `.gitignore`/`.git/info/exclude` mtimes OF THE ROOT PASSED; `specs._spec_files` docstring
records the recursion/filter coupling; `tools/test_agy_run.py` -> `44 passed in 0.37s`; backlog `mlcbk9` is
`bug`, `graduated`, `Blocks-Release: next`, matching the plan. No disposition subdirectory exists today.

Review probe (temp git repo under `/tmp/opencode/`, `AW_NO_REEXEC=1`, this lane's package): the E-03 filter
expression over `.aw/records/plans` returned only the two `executed/` plans (excluding `pending/README.md`,
`pending/untracked/`, and `pending/scratch/` ignored via `.git/info/exclude`, with `get_ignored_dirs` reporting
`pending/scratch`), and over `.agents/plans` returned the legacy plan. With `executed/...-ab12cd-other` and
`executed/202609/...-ab12cd-thing`, the CURRENT `resolve_ipd(root, "ab12cd", ("executed",))` silently returned
`...-other` and the positional mode returned `('ipd', '.aw/records/plans/executed/20260801-set-02-ab12cd-other.ipd.md', '')`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | D/E test expectations | E-02 (8) and its Expected outcome ("(8) PASS there"); review probe (plan F-09) | At base, an id6 duplicated across `executed/` and `executed/202609/` does NOT raise `is ambiguous`; the flat glob sees one and silently returns it. The plan predicted green, so an executor would hit a contradiction (or weaken the test). It is also a second silent-misresolution defect the fix closes. Sharing `ab12cd` between (1)/(2)/(7) and (8) would make those assertions ambiguous after the fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split (8) into (8a), red at base with its own id6 `dd44ee`, and (8b), green. Added a fixture rule of one id6 per assertion. Added an E-01 probe (6) and F-09. Updated the E-02, V-01, V-02 and V-05 expectations. |
| PR-002 | MEDIUM | IN-SCOPE | A correctness | `resolve_ipd` renderer `p.relative_to(root)`; E-04 ("if `root` is not already resolved") | Candidates become resolved paths, so with an unresolved `root` (relative or symlinked) the renderer raises an uncaught `ValueError` instead of the `is ambiguous` `ScriptError`. The plan left this conditional and vague. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires `relative_to(root.resolve())` unconditionally and names it as the only edit to the body. Scope check and V-04 are updated to match. |
| PR-003 | LOW | IN-SCOPE | C performance invariant | `plan_entry` docstring (F-6, ignored_dirs keyword-only); E-03 `plan_files(plans_dir)` | A `plan_files(plans_dir)` that always computes `get_ignored_dirs` would leave `scan_plans` needing a second call for `plan_entry`. That re-introduces a redundant git subprocess, a cost the code already documents avoiding (the cache hides it, but the plan should not rely on that). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Signature is now `plan_files(plans_dir, *, ignored_dirs=None)`, and `scan_plans` passes one set to both calls. |
| PR-004 | LOW | UNDER-SCOPE | E test reliability | `_cached_ignored_dirs` `lru_cache` keyed on exclude mtimes; E-02 (5b) | Writing `.git/info/exclude` after the first resolver call in a test could leave a stale cache entry. The plan did not fix the ordering. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 fixture rules now require writing the exclude file in `setUp` before any resolver call, and record why. |
| PR-005 | LOW | UNDER-SCOPE | G evidence ordering; contract | E-05 ("bare ... at the base commit and at the end", run after E-04); gate | The "before" bare-suite run was scheduled in E-05, which runs after the production edits, so it could not be a base. The gate also lacked staged-set verification and an OQ-resolution statement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now captures the base bare-suite run and its failing ids before any edit. E-05 compares against it. The gate gains both items. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Treat the duplicate-id6 case as a red-at-base defect test? | Yes, as (8a) with its own id6. | Keep it as a green "preserved semantics" check. Rejected: the probe shows it is false at base. | Review probe (F-09). | yes |
| D-2 | Render ambiguity relative to `root.resolve()` always? | Yes. | Resolve only when needed. Rejected: the condition is untestable and the unconditional form is equivalent when `root` is already resolved. | `resolve_ipd` renderer; `relative_posix` callers. | yes |
| D-3 | Should `plan_files` accept a precomputed `ignored_dirs`? | Yes, keyword-only and optional. | Always compute it internally. Rejected: that duplicates the git subprocess per `scan_plans`. | `plan_entry` docstring F-6. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.

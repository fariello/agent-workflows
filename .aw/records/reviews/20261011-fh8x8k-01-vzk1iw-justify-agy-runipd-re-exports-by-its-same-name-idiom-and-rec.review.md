# Review findings: plan vzk1iw

- Subject-Id: vzk1iw
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `2600a93e3` in an isolated review lane; plan committed and unchanged, no snapshot needed.
`aw ipd lint --phase author --agent` clean before semantic review; `--phase review-finalize` clean after.

Re-verified:
- `agy_runipd.py`: two `noqa: F401` (the `_read_id` import and `assert_child_tool_identity as assert_child_tool_identity`); last top-level import `from agent_workflows import agy_models`; `Heartbeat` comment "partial `__all__` that would understate the rest of the public surface".
- `oc_runipd.py` sentence "In contrast, `agy_runipd` has no `__all__` and retains a noqa F401 directive." present.
- 324 non-dunder attributes; `import *` yields 285.
- `tools/ipdrunner/runagy.py` copies `vars(agy_runipd)`; `tests/support.py` `load_module` exists and `tests/test_runner_shared.py` imports `from support import REPO_ROOT, load_module`.
- F-4 reproduced on a scratch copy under gitignored `tmp/`: after E-01/E-02 with the assignment directly after the `agy_models` import, `ruff --isolated --select F401,E402,RUF100` `All checks passed!` (base: 1 error, RUF100); `--select E4,E7,E9,F` `All checks passed!`; `pre-commit run ruff` and `ruff-format` `Passed` with the file byte-identical (`cmp`).
- `tools/ipdrunner/test_runagy.py`: `10 failed, 15 passed`; `-k test_read_deps_and_set` `1 passed`.
- `DECISIONS.md` last entry `D162`.
- `aw check all` before edits: `check.ipd-uncarried-obligation` ERROR (4 deferred rows, no carrier); after edits it does not fire.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Project rule (`check.ipd-uncarried-obligation`) | `## Deferred / out of scope` rows 1-4; `aw check all` ERROR | No deferral row named a carrier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rows 1-3 `Carrier-Declined` (decisions or no demand); row 4 `Carrier: g0u7f9`. |
| PR-002 | MEDIUM | IN-SCOPE | E. Evidence feasibility | V-01 (c) "hook-pinned `ruff 0.4.4` `ruff check` ... `All checks passed!`"; local bare `ruff check --isolated` reports 226 findings (205 `PLC0414`) | The demanded evidence named no reproducible invocation of the hook binary, and RUF100 is not in the default set so "clean under both versions" for RUF100 was unmeasurable on the hook. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Hook evidence is `pre-commit run ruff`/`ruff-format` plus a no-rewrite `git diff --stat`; local evidence is `--isolated --select F401,E402,RUF100`; F-3/F-4 corrected and bare local ruff declared not a bar. |
| PR-003 | MEDIUM | IN-SCOPE | C. Coordination | Pending `g0u7f9` Scope-Paths include both runner files and `tools/ipdrunner/test_runagy.py`; its F-13 / E-06 | A reviewed sibling relocates the shim test and rewrites the same comment blocks; this plan's E-03/E-04/V-04 cited only the current path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-8; E-03, E-04, V-03, V-04 and Required tests handle both landing orders and record which applied. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | Gate paragraph | Gate lacked approval/begin commands, scope-as-declaration wording, the MUST-paste rule, committing the plan file, and conditional finalize ownership; the backlog sentence was garbled. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten; genuine-unsafe STOP limited to an uncombinable concurrent edit or the hook removing the binding. |
| PR-005 | LOW | IN-SCOPE | E. Baseline | Required tests "pass count to rise by exactly the tests E-04 adds" | Pass count is a test-organization artifact and load-sensitive. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Compare FAILED node-id sets; count is context. |
| PR-006 | LOW | IN-SCOPE | Open questions | OQ-01 `- Owner: none` | A reviewer-or-author resolution should name its owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `Owner: plan author`. |
| PR-007 | LOW | IN-SCOPE | Executability | E-01 placement; E-04 cleanup | Comment block placement relative to the moved binding and `sys.path` side effect of loading the shim were unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 keeps the comment above the assignment and re-derives the last import; E-04 specifies `addCleanup(sys.modules.pop, ...)` and notes the repo-root `sys.path` insert is benign. `- From-Spec: none` added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to evidence the hook ruff verdict | `pre-commit run ruff`/`ruff-format` + no-rewrite diff | Invoke the cached binary by path (machine-local, leaks a home path) | `.pre-commit-config.yaml` `ruff-pre-commit` `rev: v0.4.4`; review run `Passed` | yes |
| D-2 | Ordering with sibling `g0u7f9` | Handle both orders in this plan, no `Item-Dependencies` edge | Add a dependency edge either way | `g0u7f9` E-01/E-06 already condition on this plan; neither is a prerequisite of the other | yes |
| D-3 | Accept the E-05 rule (binding form, no `__all__`) without asking | Keep as authored | Ask maintainer | `agy_runipd` `Heartbeat` comment already rejects a partial `__all__`; recorded in `DECISIONS.md`, editable later | yes |

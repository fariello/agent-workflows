# Review: Restore a behavioral stdlib-only guard for worktree_lease and correct its stale test citation

- Subject-Id: d8sc5n
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged (`252ea92e3`), so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before edits and `--phase review-finalize` was clean after them.

Re-verified at lane HEAD `ad815ed28`:

- `agent_workflows/worktree_lease.py` `inspect_lane` docstring still cites `tests/test_lane_allocation_idempotent.py::test_worktree_lease_stays_stdlib_only`; the file is absent.
- `git log --oneline -S stays_stdlib_only --all -- tests/` -> `80db6750c`, `7a6bc48ac`; `git merge-base --is-ancestor 80db6750c 19313eed7` rc 0. F-02 reproduces.
- `git show 80db6750c -- tests/test_lane_allocation_idempotent.py` shows `-        source = Path(WL.__file__).read_text(encoding="utf-8")`. F-03 reproduces.
- Module-level imports of `worktree_lease.py` are stdlib only; the single first-party import is function-local in `lane_merged_into_target`.
- In-process probe: baseline `['agent_workflows', 'agent_workflows._compat', 'agent_workflows.versioning']`, delta `[]`. F-07 reproduces.
- `pinned_env()` subprocess probe of `lane_merged_into_target(<tmpdir>, "definitely-no-such-branch-xyz")`: `FILE=<this worktree>/agent_workflows/worktree_lease.py`, `BEFORE=False`, `RET=False`, `AFTER=True`.
- 34 files under `tests/` import `runner_shared` at module level; importing `tests.test_lane_import_root` alone leaves `agent_workflows.runner_shared` in `sys.modules`.
- `python3 -m pytest --randomly-seed=2 tests/test_lane_import_root.py` -> `5 passed`, so the seed flag works without `-p randomly`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Testing feasibility (E) | plan E-03; `tests/test_lane_import_root.py` `from agent_workflows import runner_shared` (one of 34 such modules) | E-03 did not require a subprocess. In-process, the "absent before" assertion fails near-deterministically because other test modules already loaded `runner_shared` in the worker. F-08's reasoning applied to E-02 only. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and V-03 now mandate a `pinned_env()` subprocess and a tmp `repo_root`; shape demonstrated at review. |
| PR-002 | MEDIUM | UNDER-SCOPE | Anti-regression (D) | plan E-04, V-04; proposed change 4 "Mutation-prove both" | Only E-02 was mutation-tested. E-03, which exists to catch the wrong-way fix, was never shown to fail when the delegation is removed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04/V-04 add a second mutation (`return False` body) that must turn E-03 red with E-02 green, with restore and clean status. |
| PR-003 | MEDIUM | IN-SCOPE | Execution contract (G) | plan gate "Finalize with `aw ipd finalize`" | Unconditional finalize instruction conflicts with runner-owned transition; honesty rule not stated in the gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now assigns finalize to runner or hand executor conditionally, forbids hand `git mv`, and states the paste-actual-output rule. |
| PR-004 | LOW | IN-SCOPE | Evidence accuracy | plan Required tests "`-p randomly --randomly-seed=<n>` is already active" | The plugin is active; the flag phrasing implied `-p randomly` must be passed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reworded to `--randomly-seed=<n>`, verified on this tree. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Run E-03 in a subprocess or in-process with `sys.modules` manipulation? | Subprocess under `pinned_env()` | In-process with `sys.modules.pop` (mutates shared worker state, order-dependent) | Review probe output `BEFORE=False RET=False AFTER=True`; plan F-08 | yes |
| D-2 | Keep OQ-01 (no dependency edge on `tjags7`)? | Keep | Add an edge | AGENTS.md runner isolation paragraph; distinct sentences touched | yes |

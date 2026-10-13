# Review findings: plan n7xlhm

- Subject-Id: n7xlhm
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `0e7cf102e`. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and `--phase review-finalize` was clean after revisions; pre-transition shows no carrier findings.

Re-verified:
- `platform_lock.acquire`: non-blocking by default, raises `LockBusy` on contention, documented NOT re-entrant within a process.
- `runner_shared.runs_repo_root` and `attention._resolve_runs_repo_root` already resolve the primary checkout from a lane.
- `runner_shared.peer_drivers` exists; `runner_shared.initialize_run_core` is the shared run-start path both hosts call (`oc_runipd`, `agy_runipd`).
- `config.release_gate_work_kinds` warns and falls back on malformed values.
- `cli.py` `--source-anchors` (`dest="source_anchors"`) on `aw check`; `check_engine` has `check.spec-anchor-stale` and no registry of slow checks.
- `command_surface.COMMAND_INVENTORY` and `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves`; the CLI output-conformance CI job runs that test file.
- `doctor.run_doctor` returns aggregated Drift; `artifact_core.drift_exit_code` exempts only `info`.
- `.aw/state/` is gitignored (`.gitignore`, `.aw/.gitignore`). Remote is GitHub; `tests.yml` triggers on `main`/`master`.
- Backlog `5st6e5` is `graduated` with `Blocks-Release: next`; the plan inherits both.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | E. CI gate | `command_surface.COMMAND_INVENTORY`; `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` | Adding `aw checkup` without declaring the leaf would fail the CLI output-conformance CI job, the opposite of this Set's goal. `command_surface.py` was not in Scope-Paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 requires the declaration; Scope-Paths, Step 0, Required tests and V-06 updated. |
| PR-002 | HIGH | IN-SCOPE | D. Invariant (exit codes) | `doctor.run_doctor`; `artifact_core.drift_exit_code` | E-05 said the line "is a warning" in `aw doctor`; a `warning` Drift makes `aw doctor` exit 1, contradicting "exit codes unchanged". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now limits the doctor line to plain output or an `info` Drift; V-05 pastes exit codes before and after. |
| PR-003 | MEDIUM | IN-SCOPE | C. Canonical mechanisms | `runner_shared.runs_repo_root` | E-01 told the executor to derive the primary checkout from the git common dir, duplicating an existing resolver. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 reuses `runner_shared.runs_repo_root`; E-06 (g) tests it from a linked worktree. |
| PR-004 | MEDIUM | IN-SCOPE | E. Test feasibility | `platform_lock.acquire` docstring "NOT RE-ENTRANT" | E-06 (d) allowed "threads" racing the lock; the helper's in-process semantics make a two-thread race a different test than the cross-process one runs face. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 (d) requires two processes. |
| PR-005 | MEDIUM | IN-SCOPE | F. General-case | Scope (2), E-02 literals `tests.yml`, `main` | The toolkit installs into other repositories; hard-wiring this repo's workflow file and branch makes the checkup report a false UNKNOWN or wrong state elsewhere. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 adds `ci_checkup_workflow` and `ci_checkup_branch` keys (defaults `tests.yml`, `main`); E-02/E-04 use them; E-06 (h) tests they reach argv. |
| PR-006 | MEDIUM | IN-SCOPE | Evidence / G | F-05: no slow-check registry exists | "any other check registered as slow" names a registry that does not exist, leaving the executor to invent one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope and E-03 name a single tuple in `checkup.py`, today `check.spec-anchor-stale`, called in-process with a time bound. |
| PR-007 | MEDIUM | IN-SCOPE | C. Observability | E-04 events | Only the skip produced an event; a failed or performed checkup left no run record, and V-04 could not show `checkup-failed`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 emits exactly one of four events per run start; V-04 demands the skip and failed events. |
| PR-008 | LOW | IN-SCOPE | G. Right-sizing | E-06 bundled tests with README/CHANGELOG | Two deliverables in one item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Docs split into E-07/V-07; Proposed changes and Spec sync updated. |
| PR-009 | LOW | IN-SCOPE | B. Security / E | E-02, E-06 | The plan did not say the `gh` call is argv-only, that the record holds no paths or account names, or that tests never reach the network; V-02 demanded a real run with no fallback if `gh` is unauthenticated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01, E-02, E-06 state these; V-02 accepts a pasted UNKNOWN with reason. Also the record is treated as stale when its commit is no longer an ancestor (E-04). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Make workflow file and branch configurable? | Yes, two keys with this repo's values as defaults | Hard-wire (wrong in other installs); auto-discover from `.github/workflows` (guessing) | AGENTS.md fallback principle "General-case and configurable"; `release_gate_work_kinds` config precedent | yes |
| D-2 | How is the doctor line surfaced without changing exit codes? | Plain output or `info` Drift | `warning` Drift (exits 1) | `artifact_core.drift_exit_code` | yes |
| D-3 | What counts as "slow checks"? | One named tuple in `checkup.py`, today `check.spec-anchor-stale` | Build a registry in `check_engine` (unrequested abstraction) | F-05 | yes |

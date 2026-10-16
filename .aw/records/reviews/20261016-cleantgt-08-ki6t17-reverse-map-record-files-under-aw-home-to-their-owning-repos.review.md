# Review findings: plan ki6t17

- Subject-Id: ki6t17
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `4143d297c`. The plan was committed and byte-identical to the lane input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean`. The plan is a child, not an orchestrator.

Re-measured on a scratch clean-target install (gitignored `.aw/state/scratch-rev-ki6t17/`, `HOME`/`AW_HOME`/`XDG_CONFIG_HOME` isolated, `GIT_CEILING_DIRECTORIES` set):
- Fresh install leaves the target `git status --porcelain --ignored` empty; home `local.json` has `"common_dir": null` (F-06 holds).
- A scaffolded plan under `<h>/.aw/projects/t-623117/records/plans/pending/`: `artifact_core.repo_root_of`, `specs._repo_root_of`, `specs._spec_repo_root`, `status_set._repo_root_of`, `record_placement._find_repo_root` all return `<h>` (F-01 holds); `_identity_rename_hint` returns `''` (F-05 holds).
- `project_records_dir(target)` returns the home records root from both cwd=target and an unrelated cwd, while `project_records_dir(<h>)` returns `<h>/.aw/records` and `project_records_dir(<this repo>)` its in-tree records, so the E-03 verification rule distinguishes candidates correctly (OQ-02 holds).
- `project_context.find_project_root(target)` returns the target; `selectors.record_dirs(target, "plans")` returns the home plans dir (E-07 rename-hint fix is reachable).
- The two red modules (F-09): `9 failed, 16 passed`, exactly the 2 `5mnbaz` tests and 7 `a48b4m` setUp failures.
- All named symbols, Scope-Paths files, the spec, both executed dependencies (`kfnfji`, `fnnwj3`), and backlog `4uw2a6`, `miq4mi`, `a48b4m`, `5mnbaz` exist.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A (normal-path correctness) | `agent_workflows/orchestrator_readiness.py:736` `run_coverage` cwd climb `if (anc / ".aw").is_dir() or (anc / ".agents").is_dir()`; scratch target `<S>/h/src/t2`: `aw ipd coverage w91r2x` printed `no matching plans found`, climb probe `climb hits <S>/h`, `find_project_root()` gave the target | E-07 added `find_project_root` only as a fallback "when it finds none". In the default real layout (target under `$HOME`, `AW_HOME=$HOME/.aw`) the climb SUCCEEDS at `$HOME`, so the fallback never fires and coverage still fails. The authored F-04 used a `/tmp` target, which masked this. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-07 now calls `find_project_root(cwd)` FIRST, then the climb. Added F-10. E-01(c), E-02 item 10 (a second `$HOME/src/target` variant with the exact expected per-plan error), E-09(2c) and V-07 were updated. |
| PR-002 | MEDIUM | IN-SCOPE | G (evidence accuracy) | `ipd_lint._draft_ready_advisory(doc, text, checkpoint)` takes no path and does not climb; the `.git`-only climb is in `ipd_lint._review_stale_advisory` (`agent_workflows/ipd_lint.py:2355`) | The plan named the wrong function in the Concern and in E-06. An executor would find no climb in `_draft_ready_advisory`, and the real `.git` climb in `_review_stale_advisory` would be left unfixed. That climb can escape into an enclosing checkout (F-07). | all Low | FIXED | Concern and E-06 now name `_review_stale_advisory`. It returns `[]` for a home record because the target's git history has nothing to read. The site count was reconciled to six helper calls plus one guard, and V-06 updated. |
| PR-003 | MEDIUM | UNDER-SCOPE | C/F (user-perceptible performance) | 1574 `*.ipd.md`; `aw ipd lint --all --agent` 7.37s real; `_resolve_effective_aw_home()` about 0.14 ms/call with `AW_HOME` unset (reads user `config.json`), `_canonical_path` about 0.08 ms | Running the resolver unconditionally at five or more sites per plan would add roughly 1.5 to 2 s to a 7.4 s command that operators wait on. The plan had no fast path and no timing check. | all Low | FIXED | E-03 now has a string-only fast path: return `None` when the path has no `projects`...`records` components. E-09(6) and V-09 add a warm before/after timing with a 5% bar. Added F-11. |
| PR-004 | MEDIUM | IN-SCOPE | A (totality) | `project_context._check_path_security` raises `PathSecurityError(ProjectContextError)` on `..` | E-03's "total" list (`OSError`, `ValueError`, `RuntimeError`, JSON) omitted the exception that `_resolve_effective_aw_home` actually raises, so a resolver claimed to be total could crash every walker. | all Low | FIXED | Added `ProjectContextError` to the total list. |
| PR-005 | LOW | IN-SCOPE | E (baseline / live counts) | E-09(1) pinned the red set measured at authoring; E-09(5) compares against a baseline that no E-item captured | The pre-existing red set is a live artifact, and the bare-suite baseline was never recorded. | all Low | FIXED | E-01(f) and V-01(f) now capture both baselines and the timing. E-09(1) re-derives the red set by name and requires the tests to pass if `a48b4m` or `5mnbaz` is fixed by then. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should `run_coverage` prefer `find_project_root` over its own climb? | Yes, `find_project_root(cwd)` first, then the climb. | Keep the climb first with a fallback (REJECTED: measured to not fix the default layout). Make the climb skip AW_HOME (REJECTED: duplicates `find_project_root`'s ceilings and git-boundary rules). | F-10 scratch measurement; `project_context.find_project_root` docstring (git boundary, ceilings, `fnnwj3`). | yes |
| D-2 | What should `_review_stale_advisory` do for a home record? | Return `[]` (no advisory). | Resolve the owner and query its git history (REJECTED: home records are not in the target's git, so `review_staleness_index` has nothing to find). | `plan_readiness.review_staleness_index` docstring ("one git log call ... any git error or non-git environment yields an empty dict"). | yes |
| D-3 | Should the resolver have a no-I/O fast path? | Yes, a string check on the path parts before any AW_HOME resolution. | Cache AW_HOME resolution (REJECTED: env and config can change between calls in tests and long-lived processes). | F-11 timings; AGENTS.md "INEFFICIENCY A USER CAN NOTICE IS A DEFECT". | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.

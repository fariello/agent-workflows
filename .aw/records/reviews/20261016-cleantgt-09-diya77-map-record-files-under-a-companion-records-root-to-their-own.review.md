# Review findings: plan diya77

- Subject-Id: diya77
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `38d107d18`. The plan was committed and byte-identical to the sealed lane input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean` before edits and `--phase review-finalize --agent` reported `clean` after. Child plan, not an orchestrator. Dependency `ki6t17` is `approved` in `pending/` (not yet executed); `tests/test_record_owner_root.py` and `record_owner_root` do not exist yet, as expected.

Verified:
- `project_context.resolve_project_context` companion records root is `companion_dir or local-binding companion_dir or f"{repo_abs}.aw"` joined with `records` (project_context.py:1736-1742), so the sibling candidate is sound.
- `project_context.project_records_dir` returns the stored records class (project_context.py:1208).
- Probes under `/tmp` with isolated HOME/AW_HOME and `GIT_CEILING_DIRECTORIES`: a real `public-target-private-companion` install put plans under `<S>/t.aw/records`; see F-09..F-11 added to the plan for the new measurements.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Rubric D (anti-regression) | `agent_workflows/ipd_lint.py:2342` `_review_stale_advisory` runs `plan_readiness.review_staleness_index(repo_root, [path])` (git log in `repo_root`); `agent_workflows/status_set.py:1803` `_core.git_mv(repo_root, ...)` with `repo_root` from `specs._repo_root_of`; `ki6t17` E-05 guard returns `[]` for any non-`None` owner | Routing a companion record's owner to the TARGET breaks every git-bound consumer that today works only because the climb stops at the companion `.git`: measured, `review_staleness_index(<companion>)` finds the stale review while `review_staleness_index(<target>)` returns `{}`; `aw specs set` stages the rename in the companion today, while `git_mv(<target>, ...)` leaves an unstaged `D`/`??`. The plan claimed "no walker module is edited" and had no test pinning either. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added E-06/V-06 (owner root vs git root split at re-derived git-bound call sites, including `ki6t17`'s stale-advisory guard), E-02 tests 10 and 11 as anti-regression pins, F-10, scope paths for the four modules, spec amendment sentence, and V-05 re-measure lines. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric A (correctness) | `agent_workflows/cli.py:12208` `register_or_update_project(repo_path, str(aw_home), project_id=pid)`; `agent_workflows/project_registry.py:399` `records_backend: str = RecordsBackend.HOME.value` | E-03 candidate (3) filtered registry entries on `records_backend == companion`, but a real `aw project attach` records `home` (probe printed `home` while the resolved context printed `companion`), so the registry candidate could never fire; E-02 item 4 hand-built a `companion` entry and would have masked it. | all Low | FIXED | Candidate (3) no longer filters on the entry field (the candidate's own resolved backend is checked); item 4 uses a real `aw project attach` subprocess; F-11 added. |
| PR-003 | MEDIUM | UNDER-SCOPE | Rubric E (coverage) | `agent_workflows/specs.py:213` `_repo_root_of` climb stops at `.git`; probe `find` printed `<S>/t.aw/.aw/records/history.jsonl` | With a committed companion (the normal case) the stray sidecar lands at `t.aw/.aw/records/`, a second pre-fix outcome the plan neither recorded nor tested (item 9 ran only without companion git). | all Low | FIXED | F-09 added; E-01(d) re-measures it; item 9 runs before and after companion `git init` and asserts no `t.aw/.aw/records/history.jsonl`. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric G (executability) | `aw ipd scaffold --help`: `--title TITLE` is required | E-01(a)'s scaffold command omitted `--title` and would fail as written. | all Low | FIXED | `--title` added to the scaffold command. |
| PR-005 | LOW | IN-SCOPE | Rubric C (fast path) | plan E-03 fast path; `ki6t17` E-03 handles `<aw_home>/projects/<pid>/records` | AW_HOME's own top-level `records/` and declined `projects/...` paths would pass the companion fast path and pay registry I/O. | all Low | FIXED | Fast path also returns `None` for paths under `<aw_home>/projects/`. |
| PR-006 | LOW | UNDER-SCOPE | Rubric G (execution contract) | plan "Approval and execution gate" had no scope-fence declaration; E-05 named `tests/test_specs.py` (absent) | Missing scope-fence declaration; a test module that does not exist. | all Low | FIXED | Added SCOPE FENCE paragraph (`--scope-reason`/`--scope-ack`, no stop); targeted list uses `tests/test_specs_set_adapter.py`, `tests/test_specs_status_dirs.py`, `tests/test_status_set.py`; V-count updated to six. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should git-bound consumers of a companion record use the target or the companion git repository? | The companion git repository holding the record (owner root for config/records, git root for git ops). | Route everything to the target (REJECTED: measured regression F-10); drop companion records from the owner resolver (REJECTED: leaves F-01..F-05). | Probes in this lane (F-10); `plan_readiness.review_staleness_index` runs `git log` in `repo_root`; `artifact_core.git_mv` runs `git -C repo_root mv`. | yes |
| D-2 | Filter registry candidates on the entry's `records_backend`? | No; verify by the candidate's resolved backend. | Change `aw project attach` to record `companion` (REJECTED: attach semantics are out of scope per `ki6t17` OQ-01). | `cli._run_project_attach`; probe F-11. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.

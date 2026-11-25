# Review findings: ipd mmuv3v

- Subject-Id: mmuv3v
- Subject-Type: ipd
- Reviewed-At: 2026-11-25
- Reviewer: antigravity/Gemini 4 Neon (High)
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261125T045958Z-2935212`). The target plan `.aw/records/plans/pending/20261124-comphome-03-mmuv3v-fix-metadata-selectors-self-commit-routing-companion-locking.ipd.md` was committed and clean on entry, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit `0`, `0` findings). The review statically read `agent_workflows/status_set.py` (`match_selector`, `_prepare_status_change`, `apply_status_change`, `_delegate_plan_executed_to_finalize`, `_offer_self_commit`, `run_set_command`), `agent_workflows/git_commit_helper.py` (`_normalize`, `offer_commit`), `agent_workflows/commit_lock.py` (`_runtime_dir`, `lock_path`, `commit_isolated`, `writer_lock`), `agent_workflows/ipd_lifecycle.py` (`acquire_finalize_lock`, `_resolve_staged_companion_lane_plan`, `_run_record_committed_paths`, `retire_orchestrator`, `finalize`, `_finalize_transaction`), `agent_workflows/selectors.py` (`resolve`), `agent_workflows/artifact_meta.py` (`load_legacy_artifact`, `_git_target_root`, `write_legacy`), orchestrator `92ujfc`, and sibling plans `ywl7uc`, `7gverp`, `7eivm2`, `7hfx7r`, and `4vnd36`. It found five `HIGH` and two `MEDIUM` findings (`PR-001..PR-007`), all fixed in place in the plan. No product code or tests were modified.

### Proofreading

#### Changes
| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `E-01..E-05` | Single dense clauses per item; informal `mod.func` citations | Numbered sub-steps with canonical `agent_workflows/<mod>.py::<symbol>` citations | Technical Writing Standard Reqs 2, 4, 5, 9 and Check P Section 11.1 |
| `E-02` | "thread target repo allowlist/config context with `records_root = coord.path / 'records'` into `apply_status_change`" | Explicitly specifies adding optional `project_context` keyword parameter on `status_set.py::apply_status_change` and sorted canonical lock ordering | `apply_status_change` had no `project_context` parameter; deadlock-free ordering must be explicit |
| `## Proposed changes (ordered, validatable)` | Text list only, no diagram | Added self-commit/lock/finalize-routing Mermaid `flowchart TD` | Technical Writing Standard Req 12(a) and 12(b) |
| `## Approval and execution gate` | Two-sentence gate omitting honesty, fence, and lifecycle clauses | Full execution contract with scope-fence declaration, honesty rule, path-scoped commit, and conditional finalize ownership | Check R2 Rubric G and Check S7 |

#### Issues
| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | - | All material ambiguities were resolved from repository evidence and recorded in `### Decisions`. | - | - | - |

### Step T

1. Yes; the plan adds an optional `project_context` parameter on `status_set.py::apply_status_change`, extends `selectors.py::resolve` (`MATCH_PATH`) to records-relative paths, changes `git_commit_helper.py::offer_commit` / `commit_lock.py::commit_isolated` out-of-repo refusal behavior, and defines canonical multi-repo lock ordering consumed by Order 06 (`4vnd36`).
2. Yes; it directly modifies `agent_workflows/git_commit_helper.py` and `agent_workflows/commit_lock.py` (explicit Tier-question-2 commit/isolation modules) plus `ipd_lifecycle.py` coordinator worktree finalization.
3. Moderate; `5` E-items in `5` task groups across `6` production modules and `2` test files (`- Size assessment: standard`).
4. Yes; `- Scope-Paths:` lists all 6 production modules, 2 test files, and the plan file itself.
5. Yes; defects in multi-repo locking, isolated commits, coordinator-worktree finalization, or `artifact_meta` writers can deadlock, corrupt indexes, commit out-of-repo paths, or bypass companion lane isolation.

AW-TIER: complex

### Step R1

- Checked: every module and symbol cited in the plan against the workspace tree:
  - `agent_workflows/status_set.py`: `match_selector` (lines 597-600 check only `Path(tok)` and `repo_root / tok`), `_prepare_status_change` (lines 1640-1656 compute `rel` against `repo_root` with raw-path fallback; lines 1697-1720 ignore `repo_root` when `record_owner_root` is `None`), `apply_status_change` (lines 2121-2274 have no `project_context` parameter and pass raw external paths to `post_relocation_citation_rewrite` at lines 2248-2274), `_delegate_plan_executed_to_finalize` (line 2492 calls `finalize` directly without `_resolve_staged_companion_lane_plan`), `_offer_self_commit` (lines 2573-2592 inspect only `paths[0]` via `record_owner_root`), `run_set_command` (lines 4261-4289 run `git status --porcelain` with `cwd=repo_root` on `orch.path`).
  - `agent_workflows/git_commit_helper.py`: `_normalize` (line 1032 silently keeps out-of-repo absolute paths), `offer_commit` (line 1133 accepts them).
  - `agent_workflows/commit_lock.py`: `_runtime_dir`/`lock_path` (lines 69-78 derive from `finalize_lock_path(repo_root)`), `commit_isolated` (lines 369-373 compute `repo_root / r` and `wt / r`, triggering `shutil.SameFileError` on absolute out-of-repo paths), `writer_lock` (line 798).
  - `agent_workflows/ipd_lifecycle.py`: `acquire_finalize_lock` (line 719), `_resolve_staged_companion_lane_plan` (line 2556; called only in CLI wrapper at line 6892, not inside `finalize`), `_run_record_committed_paths` (line 2898 hardcodes `checkout_control_root(repo_root) / "records" / "runs"`), `retire_orchestrator` (line 5604 locks only `repo_root`), `finalize` (line 5914 locks only `repo_root`), `_finalize_transaction` (line 6249 passes `repo_root` to `agent_commit_identity`; lines 6299-6308 pass `coord.path` as `repo_root` to `read_artifact_record` and `apply_status_change`).
  - `agent_workflows/selectors.py`: `resolve` (`MATCH_PATH` lines 1013-1025 probe only `{Path(tok), repo_root / tok}`).
  - `agent_workflows/artifact_meta.py`: `load_legacy_artifact` (line 3588 passes `_proj_ctx.record_git_root(records_root) or records_root` instead of `scan_repo` to `_core.global_id6s`), `_git_target_root` (line 8494 ignores `repo_root`), `write_legacy` (line 8550 tries `record_git_root` before `_core.repo_root_of`).

### Step R2

- Checked: E/V bijection (`5/5`: `E-01..E-05` map 1:1 to `V-01..V-05`, `- Highest E allocated: 5`), internal dependency graph (`E-01 -> {E-02, E-03}`, `{E-02, E-03, E-04} -> E-05`), `- Item-Dependencies: executed:ywl7uc`, `- Scope-Paths:` completeness (`8` work paths + IPD), V-item evidence concreteness and reachability (every `V-*` demands pytest, mypy, or `aw sanitize` output, reachable by construction), and `## Approval and execution gate`.
- Found missing execution-contract clauses (`PR-005`) and missing existing regression test suites / exact `V-01` file names (`PR-006`), both fixed in place.

### Step R3

- Checked: out-of-repo path rejection in `git_commit_helper.py::offer_commit` and `commit_lock.py::commit_isolated` before staging or allocating a worktree (`PR-001`), path-traversal and symlink-escape containment in `selectors.py` records-relative `MATCH_PATH` resolution (`PR-004`), and preserving target-repo leak allowlist enforcement during companion coordinator-worktree finalization (`PR-002`).

### Step R4

- Checked: deadlock prevention via deterministic sorted canonical lock order across `repo_root` and `tx_git_root` with reverse-order `try/finally` release (`PR-002`), single source of truth (P8: shared records-relative path helper between `selectors.py::resolve` and `status_set.py::match_selector`; single `_resolve_staged_companion_lane_plan` chokepoint inside `ipd_lifecycle.py::finalize`), `coord.path` git-move routing via `_git_target_root` during coordinator-worktree finalization (`PR-002`, `PR-004`), unversioned `~/.aw/` graceful skip in self-commit, dirty-tree check, and same-status `HEAD` probe (`PR-001`, `PR-003`), P16 behavioral-only testing, and substantiated `## Spec / documentation sync` (`PR-006`).

### Step R5

- Checked through all eight personas:
  - **QA / QC:** caught missing `project_context` parameter on `apply_status_change` (`PR-002`), missing `git_root is None` guard on same-status `HEAD` probe (`PR-003`), and `shutil.SameFileError` root cause in `commit_isolated` (`PR-001`).
  - **Testing and regression:** added all 5 existing core regression suites (`test_commit_lock.py`, `test_git_commit_helper.py`, `test_selector_resolver_matrix.py`, `test_selector_type_containment.py`, `test_status_set.py`) to `## Required tests / validation` (`PR-006`).
  - **UI / UX:** ensured unversioned `~/.aw/` `aw set --commit` skips silently without confusing git errors or prompts, and dirty companion orchestrator `NextAction` uses the companion git root (`PR-001`, `PR-003`).
  - **Architect:** specified deterministic lexicographic lock ordering to prevent cross-repo deadlocks (`PR-002`) and unified records-relative path resolution across `selectors.py` and `status_set.py` (`PR-004`).
  - **Software engineer:** verified `artifact_meta.py::_git_target_root` interaction with `coord.path` coordinator worktrees so `git mv` stages inside the worktree while allowlist/log-format checks read `repo_root` (`PR-002`, `PR-004`).
  - **Power user:** ensured custom non-sibling `--dir` companions, mixed-repo batches, and `plans/pending/...` / `records/plans/pending/...` selectors all work reliably (`PR-001`, `PR-003`, `PR-004`).
  - **Novice:** ensured `aw set --commit` and `aw ipd set executed` work transparently without manual git workarounds or silent lane bypasses (`PR-001`, `PR-002`).
  - **Stakeholder:** verified all nine `/assess-bugs` metadata/selector/locking/finalize defects are cleanly closed for downstream Order 06 (`4vnd36`).

### Step R6

- Checked: `5` E-items in `5` task groups across `8` work `- Scope-Paths:` entries (`- Size assessment: standard`; `0` `IPD-Z603` advisories). Cleanly scoped to one architectural layer. No split warranted.

### Step R7

- Checked: orchestrator `92ujfc` and sibling plans `ywl7uc` (Order 01, prerequisite), `7gverp` (Order 02), `7eivm2` (Order 04), `7hfx7r` (Order 05), and `4vnd36` (Order 06, declares `executed:mmuv3v`). Zero production file overlap with parallel Orders 02, 04, and 05; Order 06 (`4vnd36`) builds cleanly on `mmuv3v`'s `ipd_lifecycle.py` changes. Updated `## Deferred / out of scope` to name all five sibling carriers consistently.

### Step S5

- Checked: `## Open questions` is `None`. All seven review findings (`PR-001..PR-007`) have `Overall:Low` remediation risk and were fixed in place. Three autonomous review decisions (`D-1..D-3`) are recorded below; all three are `Reversible: yes`. No human decision or blocking open question remains.

### Pass 2

- Re-read the complete revised plan end to end after applying all edits (`PR-001..PR-007`), transitioned `- Status:` to `reviewed` via `aw ipd set reviewed mmuv3v`, and ran `aw ipd lint --phase review-finalize --agent`.
- Verified `5/5` E/V bijection, unchanged E/V IDs and checkbox states, `- Status: reviewed`, `- Readiness: go-pending-approval`, `- Review-Depth: complex`, newest-first `## Workflow history` entries, matching Mermaid diagram terms, zero em or en dashes, and zero `error` or `warning` diagnostics.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R1 / R3 / R4 A | `.aw/records/plans/pending/20261124-comphome-03-mmuv3v-fix-metadata-selectors-self-commit-routing-companion-locking.ipd.md:35`; `agent_workflows/status_set.py::_offer_self_commit:2573`; `agent_workflows/git_commit_helper.py::_normalize:1032`, `offer_commit:1133`; `agent_workflows/commit_lock.py::commit_isolated:369` | `E-01` did not specify refusing out-of-repo absolute and `..` paths BEFORE staging/worktree allocation in `offer_commit` and `commit_isolated` (returning typed error outcomes with zero mutation), nor per-bucket repo-relative path conversion and clean silent return when all touched paths are unversioned `~/.aw/`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Detailed exact containment refusal and multi-root bucketing rules in `E-01` and `V-01`. Recommendation strength: very strong. |
| PR-002 | HIGH | IN-SCOPE | R1 / R4 A / R4 C | `.aw/records/plans/pending/20261124-comphome-03-mmuv3v-fix-metadata-selectors-self-commit-routing-companion-locking.ipd.md:42`; `agent_workflows/ipd_lifecycle.py::retire_orchestrator:5604`, `finalize:5914`, `_finalize_transaction:6249,6299,6307`; `agent_workflows/status_set.py::apply_status_change:2121` | `E-02` did not define the deterministic canonical lock order (deadlock risk on reverse acquisition) or partial-acquisition cleanup, and `status_set.py::apply_status_change` currently has no `project_context` or `records_root` parameter to receive target `repo_root` allowlist/config context while staging `git mv` inside `coord.path`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified lexicographically sorted canonical lock acquisition with reverse `try/finally` release, `_resolve_staged_companion_lane_plan` placement inside `finalize`, and optional `project_context` parameter on `apply_status_change` in `E-02` and `V-02`. Recommendation strength: very strong. |
| PR-003 | HIGH | IN-SCOPE | R1 / R4 A | `.aw/records/plans/pending/20261124-comphome-03-mmuv3v-fix-metadata-selectors-self-commit-routing-companion-locking.ipd.md:49`; `agent_workflows/status_set.py::_prepare_status_change:1640,1697`, `apply_status_change:2248`, `run_set_command:4261` | `E-03` did not specify skipping the same-status git `HEAD` probe when `record_git_root(rec.path)` is `None` (unversioned `~/.aw/`), computing `orch_rel` relative to `orch_git_root` for the dirty-tree check and `NextAction`, or falling back from `record_owner_root(rec.path)` to `repo_root` for custom-companion staleness. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Made all three exact guards explicit in `E-03` and `V-03`. Recommendation strength: strong. |
| PR-004 | HIGH | IN-SCOPE | R1 / R3 / R4 A | `.aw/records/plans/pending/20261124-comphome-03-mmuv3v-fix-metadata-selectors-self-commit-routing-companion-locking.ipd.md:56`; `agent_workflows/selectors.py::resolve:1013`; `agent_workflows/status_set.py::match_selector:597`; `agent_workflows/artifact_meta.py::load_legacy_artifact:3588`, `_git_target_root:8494`, `write_legacy:8550` | `E-04` did not specify sharing one records-relative path helper between `selectors.py::resolve` and `status_set.py::match_selector` with strict containment under `project_records_dir(repo_root).resolve()` (refusing `..` and symlink escapes), nor covering `home` local-git and coordinator-worktree `record_git_root` in `_git_target_root`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified the shared containment-checked helper in `selectors.py`, `_git_target_root` handling for companion/`home` local-git/coordinator worktrees, and `scan_repo` fallback in `load_legacy_artifact` across `E-04` and `V-04`. Recommendation strength: strong. |
| PR-005 | HIGH | UNDER-SCOPE | R2 / S7 | `.aw/records/plans/pending/20261124-comphome-03-mmuv3v-fix-metadata-selectors-self-commit-routing-companion-locking.ipd.md:147` | Execution gate omitted mandatory contract clauses: resolved open-question status, scope-fence declaration (`--scope-reason`/`--scope-ack`), hard-MUST honesty rule (paste actual output), ban on `git add -A`/`-a`/bare, and conditional runner/executor finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the complete execution contract to `## Approval and execution gate`. Recommendation strength: very strong. |
| PR-006 | MEDIUM | UNDER-SCOPE | R2 / R4 E / R7 | `.aw/records/plans/pending/20261124-comphome-03-mmuv3v-fix-metadata-selectors-self-commit-routing-companion-locking.ipd.md:94,104,110,122` | `## Required tests / validation` omitted existing core regression suites (`test_commit_lock.py`, `test_git_commit_helper.py`, `test_selector_resolver_matrix.py`, `test_selector_type_containment.py`, `test_status_set.py`), `V-01` omitted test file names, `## Deferred / out of scope` omitted four sibling carriers, and `## Spec / documentation sync` gave bare `N/A`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added all 5 existing regression suites to `## Required tests / validation` and `V-01..V-05`, listed all five sibling carriers in `## Deferred / out of scope`, and substantiated `## Spec / documentation sync`. Recommendation strength: strong. |
| PR-007 | MEDIUM | IN-SCOPE | Check P / Tech Writing Req 12 | `.aw/records/plans/pending/20261124-comphome-03-mmuv3v-fix-metadata-selectors-self-commit-routing-companion-locking.ipd.md:86` | Plan changes 6 related modules and specifies a branched self-commit/lock/finalize flow with no Mermaid diagram (Technical Writing Standard Req 12(a)/(b)), used single dense sentences per E-item, and mixed non-canonical code citations. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a Mermaid `flowchart TD` matching plan terms, converted `E-01..E-05` into numbered sub-steps, and standardized `path::Symbol` citations. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | What canonical lock order should `ipd_lifecycle.py` use when `tx_git_root != repo_root`? | Sort distinct resolved lock roots lexicographically (`sorted({repo_root.resolve(), tx_git_root.resolve()}, key=lambda p: p.as_posix())`), acquire in order, release in reverse order | Fixed `repo_root` then `tx_git_root` without canonical sorting (could invert if two paths cross-reference) | `agent_workflows/commit_lock.py:76-78`, `798`; `agent_workflows/ipd_lifecycle.py:5604`, `5914` | yes |
| D-2 | How should `_finalize_transaction` pass target-repo allowlist/config context into `apply_status_change` while mutating `coord.path`? | Add optional `project_context: Any = None` keyword parameter to `status_set.py::apply_status_change` and pass `repo_root=repo_root` with a context pointing `records` to `coord.path / "records"` (or `coord.path / ".aw" / "records"`) | Keep passing `coord.path` as `repo_root` (loses target allowlist and log-format metadata); add separate `allowlist_root` and `log_format_root` args (fragments context) | `agent_workflows/ipd_lifecycle.py:6299-6309`; `agent_workflows/status_set.py:2121-2240`; `agent_workflows/artifact_meta.py:8494-8505` | yes |
| D-3 | Should `selectors.py::resolve` and `status_set.py::match_selector` share one containment-checked records-relative path helper? | Yes; define in `selectors.py` and reuse from `status_set.py::match_selector` | Duplicate path checks in both modules (violates P8 and risks divergence on `..`/symlink escapes) | `agent_workflows/selectors.py:1013-1025`; `agent_workflows/status_set.py:597-600`; `GUIDING_PRINCIPLES.md` P8 | yes |

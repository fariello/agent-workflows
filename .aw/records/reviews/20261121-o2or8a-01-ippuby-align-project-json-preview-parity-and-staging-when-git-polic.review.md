# Review findings: ipd ippuby

- Subject-Id: ippuby
- Subject-Type: ipd
- Reviewed-At: 2026-11-21
- Reviewer: antigravity/gemini-4-neon-high
- Verdict: REJECT - NEEDS REPLAN

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261121T064614Z-2150223`). The target plan `.aw/records/plans/pending/20261119-o2or8a-01-ippuby-align-project-json-preview-parity-and-staging-when-git-polic.ipd.md` was committed and unchanged, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `2` non-blocking `IPD-C802` info advisories on template boilerplate). Inspection of backlog `o2or8a`, `git show 2c0a0fe21`, `agent_workflows/migrations/chain.py`, `agent_workflows/config.py`, `agent_workflows/engine.py`, `tests/test_installer_scaffold_preview_parity.py`, `tests/test_installer.py`, `CHANGELOG.md`, and live pytest runs surfaced one `BLOCKER` finding (`PR-001`, `REPLAN`) and one `HIGH` finding (`PR-002`, `FIXED`). All production and test deliverables (`E-01..E-04`) already landed on `main` in commit `2c0a0fe21` (2026-11-20), leaving only the optional `CHANGELOG.md` bullet (`E-05`) unlanded and rendering `V-01..V-03` diff demands unreachable on current `main`. Verdict: `REJECT - NEEDS REPLAN`; Readiness: `no-go`.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Approval and execution gate` | Single paragraph omitting resolved-OQ precondition, `--scope-reason`/`--scope-ack` variance rule, hard-MUST paste-actual-runner-output honesty rule, shared-checkout safety, explicit hand-`git mv` prohibition, and post-finalization separation for backlog `o2or8a` | Structured bulleted execution contract covering `no-go` replan notice, preconditions, `--scope-reason`/`--scope-ack` variance rule, honesty rule, shared-checkout safety, conditional runner/executor `aw ipd finalize ippuby` ownership, hand-`git mv` prohibition, and post-finalization backlog `o2or8a` closure | PR-002, `steps/r2-executability.md`, `steps/s7-finalize.md` |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| P-01 | `Concern`, `Scope`, `E-01..E-05`, `V-01..V-05` | `E-01..E-04` already landed on `main` in commit `2c0a0fe21` (2026-11-20); only the `CHANGELOG.md` bullet (`E-05`) is absent from `CHANGELOG.md` | Maintainer decision: retire `ippuby` (`not-executed`/`superseded`) and close backlog `o2or8a` citing commit `2c0a0fe21` (adding the `CHANGELOG.md` bullet directly if desired), OR replace `ippuby` with a 1-step `CHANGELOG.md`-only plan | Retire `ippuby` (`superseded`/`not-executed`), close backlog `o2or8a` citing commit `2c0a0fe21`, and add the single `CHANGELOG.md` bullet directly if wanted | very strong |

### Step T

1. Yes; targets `agent_workflows/migrations/chain.py`, `agent_workflows/config.py`, and `agent_workflows/engine.py` install preview and git-staging behavior relied on by `install-workflows.py` and `aw install`.
2. Yes; touches `agent_workflows/engine.py::stage_tracked_policy_files`, which controls which policy files enter the git index.
3. No; cohesive (`5` E-items across `2` task groups and `7` `- Scope-Paths:` files).
4. Yes; `- Scope-Paths:` explicitly lists all `7` files.
5. Yes; executing an already-landed plan (`2c0a0fe21`) against current `main` would fail `V-01..V-03` (empty diffs) or risk duplicating/churning already-verified installer code and tests.

AW-TIER: standard

### Step R1

- Checked: backlog `.aw/records/backlog/graduated/20261117-o2or8a-01-o2or8a-install-project-json-preview-and-staging.backlog.md`, commit `2c0a0fe21` (`git show --stat 2c0a0fe21` and diffs on `tests/test_installer_scaffold_preview_parity.py` and `tests/test_installer.py`), `agent_workflows/migrations/chain.py` (`build_metadata_schema_data`, `write_metadata_schema`), `agent_workflows/config.py` (`plan_cutovers_update`, `sync_cutovers_on_install`), `agent_workflows/engine.py` (`plan_project_json_update`, `show_install_diffs`, `install_into_repo`, `stage_tracked_policy_files`), `CHANGELOG.md`, and live pytest execution (`tests/test_installer_scaffold_preview_parity.py`: `11 passed in 2.94s`; `tests/test_installer.py -k "test_tool_scripts_are_executable_and_staged"`: `1 passed in 3.41s`).
- Found that commit `2c0a0fe21` (2026-11-20) already implemented every production and test item of `E-01..E-04` (`PR-001`); only the `CHANGELOG.md` entry (`E-05`) is absent.

### Step R2

- Checked: `E-*`/`V-*` bijection (`5/5`: `E-01..E-05` <-> `V-01..V-05`, `- Highest E allocated: 05`), `- Scope-Paths:`, `- Item-Dependencies: none`, runtime reachability of `V-01..V-05`, and `Approval and execution gate`.
- Found `V-01..V-03` diff demands are unreachable against current `main` because `2c0a0fe21` already committed those exact code changes (`PR-001`), and `Approval and execution gate` omitted required execution-contract clauses (`PR-002`, fixed in place).

### Step R3

- Checked: security and privacy lens (`steps/r3-security.md` full form). Verified in `2c0a0fe21` that `stage_tracked_policy_files` preserves `git check-ignore`, `GitPolicy.TARGET_GIT.value` filtering, and ignored/companion-preset protection (`test_ignored_and_companion_preset_project_json_not_staged`), and `plan_project_json_update` remains side-effect-free and bounded by `_is_safe_subpath` containment.

### Step R4

- Checked: correctness, anti-regression, and duplication risk (`PR-001`: executing `ippuby` as written would attempt to re-apply already-landed code and duplicate tests already present from `2c0a0fe21`), right-sizing, and `## Spec / documentation sync` (`CHANGELOG.md` bullet in `E-05` is the only unlanded item).

### Step S5

- Checked: `## Open questions` (`None.`). `PR-001` is marked `REPLAN` because retiring `ippuby` (and closing backlog `o2or8a` citing `2c0a0fe21`) versus re-scoping it to a 1-step `CHANGELOG.md`-only plan is a maintainer lifecycle decision. Per `agent_workflows/check_engine.py::_REVIEW_UNESCALATED_RULE` (line 10191), `replan` findings do not require an `IPD-Q501` blocking question in the plan; `- Readiness: no-go` and `Verdict: REJECT - NEEDS REPLAN` fail closed against approval and execution.

### Pass 2

- Re-checked the updated plan front matter (`- Status: reviewed`, `- Readiness: no-go`, `- Review-Depth: standard`), `## Workflow history`, and `Approval and execution gate`, plus verified `aw ipd lint --phase review-finalize --agent` returns `clean`.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | IN-SCOPE | R1 / R2 / R4 / Already implemented on `main` (`2c0a0fe21`) | .aw/records/plans/pending/20261119-o2or8a-01-ippuby-align-project-json-preview-parity-and-staging-when-git-polic.ipd.md:38-75,162-185; commit `2c0a0fe21`; agent_workflows/migrations/chain.py::build_metadata_schema_data:127; agent_workflows/config.py::plan_cutovers_update:1544; agent_workflows/engine.py::plan_project_json_update:4807; agent_workflows/engine.py::stage_tracked_policy_files:2867 | All production and test items (`E-01..E-04`) were already implemented on `main` by commit `2c0a0fe21` (2026-11-20), including `build_metadata_schema_data`, `plan_cutovers_update`, `plan_project_json_update`, `show_install_diffs(policy_members=...)`, `write_metadata_schema` ordered before `sync_cutovers_on_install`, `stage_tracked_policy_files` fallback via `project_context.resolve_project_context`, and all 5 behavioral regression tests in `tests/test_installer_scaffold_preview_parity.py` and `tests/test_installer.py`. Both cited failing tests already pass on unmodified `main` (`11 passed in 2.94s` and `1 passed in 3.41s`), rendering `V-01..V-03` diff demands unreachable. Only the single `CHANGELOG.md` bullet (`E-05`) is absent. | C:Low; U:Low; S:Low; F:High; Overall:High | REPLAN | Retire `ippuby` (`not-executed`/`superseded`) and close backlog `o2or8a` citing commit `2c0a0fe21` (optionally adding the single `CHANGELOG.md` `- Fixed:` bullet directly, or replanning `ippuby` as a 1-step `CHANGELOG.md`-only plan if a tracked IPD is desired for the changelog note). Recommendation strength: very strong. |
| PR-002 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261119-o2or8a-01-ippuby-align-project-json-preview-parity-and-staging-when-git-polic.ipd.md:187-192; .aw/system/workflows/plan-review/steps/r2-executability.md:57-60; .aw/system/workflows/plan-review/steps/s7-finalize.md:31-46 | `Approval and execution gate` omitted required execution-contract clauses (resolved-open-questions precondition, `--scope-reason`/`--scope-ack` scope-fence variance rule, hard-MUST paste-actual-runner-output honesty rule, shared-checkout safety rule, explicit hand-`git mv` prohibition, explicit both-branch conditional runner/executor `aw ipd finalize ippuby` ownership, and post-finalization separation for backlog `o2or8a` closure). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote `Approval and execution gate` in place with all required execution-contract clauses and `no-go` replan notice. Recommendation strength: very strong. |

### Decisions

None.

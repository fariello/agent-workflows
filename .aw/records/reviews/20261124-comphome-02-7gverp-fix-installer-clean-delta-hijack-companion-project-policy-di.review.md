# Review findings: ipd 7gverp

- Subject-Id: 7gverp
- Subject-Type: ipd
- Reviewed-At: 2026-11-25
- Reviewer: antigravity/Gemini 4 Neon (High)
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261125T045958Z-2935212`). The target plan `.aw/records/plans/pending/20261124-comphome-02-7gverp-fix-installer-clean-delta-hijack-companion-project-policy-di.ipd.md` was committed and clean on entry, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit `0`, `0` findings). The review statically read `agent_workflows/engine.py` (`_is_clean_delta_install`, `_clean_delta_home_trees`, `_system_member_destination`, `_records_member_destination`, `stage_tracked_policy_files`, `plan_project_json_update`, `show_install_diffs`, `_AW_GITIGNORE_TEMPLATE`, `collect_scaffold_members`, `migrate_local_lanes_to_untracked`, `install_into_repo`, `run`), `agent_workflows/install_wizard.py` (`get_preset_defaults`, `resolve_policy_noninteractive`, `collect_policy_interactive`, `persist_project_policy`), `agent_workflows/cli.py` (`_run_install`), `agent_workflows/project_context.py` (`_resolve_project_context_uncached`), `agent_workflows/project_schema.py` (`PRESET_PLACEMENTS`), `agent_workflows/placement_switch.py` (`plan_placement_switch` `config_retrack` and warnings), `agent_workflows/leak_sanitizer.py` (`resolve_allowlist_path`, `write_repo_allowlist`), `ARCHITECTURE.md`, `README.md`, spec `20260810-1447-01`, orchestrator `92ujfc`, sibling plans `ywl7uc`, `mmuv3v`, `7eivm2`, `7hfx7r`, and `4vnd36`, and existing test files (`tests/test_installer.py`, `tests/test_placement_switch_companion_plan.py`, `tests/test_placement_switch_companion_execute.py`, `tests/test_placement_switch_companion_cli.py`, `tests/test_clean_target_config_home.py`, `tests/test_project_layout.py`, `tests/test_reinstall_preserves_config.py`, `tests/test_leak_sanitizer.py`). It found four `HIGH` and three `MEDIUM` findings (`PR-001..PR-007`), all fixed in place in the plan. No product code or tests were modified.

### Proofreading

#### Changes
| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `E-01..E-05` | Single dense clauses per item; informal `mod.func` citations | Numbered sub-steps with canonical `agent_workflows/<mod>.py::<symbol>` citations | Technical Writing Standard Reqs 2, 4, 5, 9 and Check P Section 11.1 |
| `E-02`, `V-02` | Vague "reconcile `config_project` policy" omitting `OQ-01` ruling and affected modules/tests | Explicit `target-tracked`/`target-git` alignment across `install_wizard.py`, `project_schema.py`, `project_context.py`, `placement_switch.py`, and 4 pinning tests | Technical Writing Standard Reqs 5, 10; anti-regression |
| `E-03`, `V-03` | Unconditional default `<anchor>.aw` in `resolve_policy_noninteractive` | Scoped to first install (`existing_policy is None`) only, preserving `--relocate` refusal per spec `20260810-1447-01` | Correctness and spec compliance |
| `## Proposed changes (ordered, validatable)` | Text list only, no diagram | Added installer policy/recovery/`--diff` Mermaid `flowchart TD` | Technical Writing Standard Req 12(a) and 12(b) |
| `## Approval and execution gate` | Two-sentence gate omitting honesty, fence, and lifecycle clauses | Full execution contract plus `- Size assessment: exception` cohesion rationale | Check R2 Rubric G and Check S7 |

#### Issues
| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | - | All material ambiguities were resolved from repository evidence or `OQ-01` and recorded in `### Decisions`. | - | - | - |

### Step T

1. Yes; the plan changes the `public-target-private-companion` preset policy (`config_project` = `target-tracked`/`target-git` across `project_schema.py`, `install_wizard.py`, `project_context.py`, and `placement_switch.py`), first-install noninteractive default `companion_dir`, and `leak_sanitizer.py` allowlist placement.
2. Yes; it touches `agent_workflows/leak_sanitizer.py` (an explicit Tier-question-2 privacy/leak-guard module), `project_context.py` git policies, and `clean-delta` zero-footprint containment.
3. Yes; 5 E-items in 4 task groups spanning 7 production modules and 7 test files (`- Size assessment: exception`).
4. Yes; `- Scope-Paths:` lists all 7 production modules, 7 test files, and the plan file itself.
5. Yes; defects in `_clean_delta_home_trees` can hijack updates or strand `.aw/` on uninstall, and defects in `leak_sanitizer.py` or `install_wizard.py` can dirty `clean-delta` or public target repositories.

AW-TIER: complex

### Step R1

- Checked: every cited module, symbol, and existing test against the workspace tree:
  - `agent_workflows/engine.py`: `_is_clean_delta_install` (line 507), `_clean_delta_home_trees` (line 537, branch (b) lines 576-602 checks `("system", "state", "worktrees", "records")` without checking for in-tree `.aw/config/project.json`), `_system_member_destination` (line 2563), `_records_member_destination` (line 2626), `stage_tracked_policy_files` (line 2899), `show_install_diffs` (line 4903, hardcodes `plan.repo_root / rel` at line 4944), `_AW_GITIGNORE_TEMPLATE` (line 6477), `collect_scaffold_members` (line 7381), `migrate_local_lanes_to_untracked` (line 8345, unguarded `new.relative_to(repo_root)` at line 8361 and `else: _ensure_untracked_gitignore(base)` at line 8377), `install_into_repo` (line 8488, `clean` exclusions at lines 8508, 8535, 8548, 8556), `run()` `--diff` (lines 8804-8851, ignores `clean` and checks `(plan.repo_root / rel).exists()` at line 8841).
  - `agent_workflows/install_wizard.py`: `get_preset_defaults` (lines 201-224, `CONFIG_PROJECT` set to `COMPANION_TRACKED`/`COMPANION_GIT`), `resolve_policy_noninteractive` (lines 842-984, leaves `companion_dir=None` when `--companion-dir` omitted).
  - `agent_workflows/project_schema.py`: `PRESET_PLACEMENTS` (line 289, `CONFIG_PROJECT` set to `COMPANION_TRACKED`; module was omitted from `7gverp`).
  - `agent_workflows/project_context.py`: `_resolve_project_context_uncached` (lines 2460-2469, both `SYSTEM` and `CONFIG_PROJECT` return `GitPolicy.IGNORED` for `PUBLIC_TARGET_PRIVATE_COMPANION`).
  - `agent_workflows/placement_switch.py`: `plan_placement_switch` (lines 626-628 set `config_retrack = "untrack"` on attach and `"track"` on detach; line 1081 emits `warnings["config-becomes-untracked"] = 1`; module was omitted from `7gverp`).
  - `agent_workflows/cli.py`: `_run_install` (lines 9772-9783 refuse `--relocate` without `--companion-dir`; lines 9966-9988 init and attach companion when `policy.companion_dir` is set).
  - `agent_workflows/leak_sanitizer.py`: `resolve_allowlist_path` (line 181, hardcodes `repo_root / REPO_ALLOWLIST_REL`), `write_repo_allowlist` (line 414, already delegates to `resolve_allowlist_path`).
  - Existing tests pinning the old `public-target-private-companion` policy: `tests/test_installer.py:809`, `tests/test_placement_switch_companion_plan.py:188,217,233`, `tests/test_placement_switch_companion_execute.py:353`, `tests/test_placement_switch_companion_cli.py:199`; plus `tests/test_clean_target_config_home.py:1088` (`test_case_u_uninstall_recovers_partial`).

### Step R2

- Checked: E/V bijection (`5/5`: `E-01..E-05` map 1:1 to `V-01..V-05`, `- Highest E allocated: 5`), internal dependency graph (`E-01 -> E-02 -> E-03 -> E-05`, `E-04 -> E-05`), `- Item-Dependencies: executed:ywl7uc`, `- Scope-Paths:` completeness (extended with `project_schema.py`, `placement_switch.py`, and the 4 updated test files), V-item evidence concreteness and reachability (every `V-*` demands pytest, mypy, or `aw sanitize` output, reachable by construction), and `## Approval and execution gate`.
- Found missing execution-contract clauses (`PR-005`) and missing regression suites / test file assignments (`PR-006`), both fixed in place.

### Step R3

- Checked: `clean-delta` zero-footprint containment (`leak_sanitizer.py::resolve_allowlist_path` must skip the in-tree `.agents/` fallback when `project_config_dir` resolves outside `repo_root`, `PR-004`; `engine.py::run()` `--diff` must honor `clean-delta` exclusions, `PR-003`; `migrate_local_lanes_to_untracked` must not write stray nested `.gitignore` files into external repos, `PR-003`), explicit `--companion-dir` safeguard on `--relocate` (`PR-002`), and `target-git` policy for `.aw/config/project.json` without exposing `local.json` or `state/runtime/` (`PR-001`).

### Step R4

- Checked: anti-regression against `tests/test_clean_target_config_home.py::test_case_u_uninstall_recovers_partial` (`PR-003`), `cli.py:9772-9783` / spec `20260810-1447-01:143` `--relocate` refusal (`PR-002`), `tests/test_leak_sanitizer.py:1451` allowlist resolution table (`PR-004`), and all four existing tests pinning the overruled `public-target-private-companion` policy (`PR-001`). Checked `## Spec / documentation sync` against `ARCHITECTURE.md:91`, `README.md:138`, and spec `20260810-1447-01:143` (`PR-006`).

### Step R5

- Checked through all eight personas:
  - **QA / QC:** caught `placement_switch.py` actively untracking `.aw/config/project.json` on companion attach (`PR-001`), `--relocate` guard bypass if `<anchor>.aw` defaulted unconditionally (`PR-002`), and stray nested `.gitignore` creation in `migrate_local_lanes_to_untracked` (`PR-003`).
  - **Testing and regression:** identified all four existing tests that would break under `OQ-01` (`PR-001`) plus `test_case_u_uninstall_recovers_partial` (`PR-003`) and added all affected regression suites to `## Required tests / validation` (`PR-006`).
  - **UI / UX:** ensured `aw install --diff` matches `install_into_repo` with zero spurious diffs on companion/`home`/`clean-delta` installs (`PR-003`).
  - **Architect:** aligned all four policy authorities (`project_schema.py`, `install_wizard.py`, `project_context.py`, `placement_switch.py`) onto one consistent `config_project = target-tracked / target-git` contract (`PR-001`).
  - **Software engineer:** verified `cli.py:9978` `git init` exit-code check and `aw_home=policy.aw_home` forwarding (`PR-002`) and `leak_sanitizer.py` exception fallback (`PR-004`).
  - **Power user:** preserved `--relocate` explicit `--companion-dir` safety check and `clean-delta` zero-target-footprint guarantee (`PR-002`, `PR-004`).
  - **Novice:** ensured `aw install --preset public-target-private-companion --yes` works out of the box with a clean target `git status` and initialized `<repo>.aw` companion (`PR-001`, `PR-002`).
  - **Stakeholder:** verified all six `/assess-bugs` installer/allowlist defects and `OQ-01` are cleanly closed without breaking downstream Set `comphome` plans.

### Step R6

- Checked: `7gverp` has `5` E-items in `4` task groups (within the 5-item `IPD-Z603` guidance) and `14` work `Scope-Paths` after adding `project_schema.py`, `placement_switch.py`, and the 4 existing tests that pinned the overruled `OQ-01` policy. Evaluated splitting the `placement_switch.py` / test alignment into a separate child plan; rejected (`D-1`) because changing `config_project` to `target-git` in `install_wizard`/`project_context` without updating `project_schema`, `placement_switch`, and those 4 tests in the same merge breaks `pytest` immediately. Updated `- Size assessment: exception` with an explicit cohesion rationale.

### Step R7

- Checked: orchestrator `92ujfc` and sibling plans `ywl7uc` (Order 01, already reviewed), `mmuv3v` (Order 03), `7eivm2` (Order 04), `7hfx7r` (Order 05), and `4vnd36` (Order 06). `7gverp` declares `- Item-Dependencies: executed:ywl7uc`, so its edits to `project_context.py`, `placement_switch.py`, `test_home_isolation.py`, `test_companion_containment_and_storage.py`, and `test_placement_switch_companion_execute.py` serialize strictly after `ywl7uc`. Updated `## Deferred / out of scope` to name all five sibling carriers consistently.

### Step S5

- Checked: `## Open questions` contains only `OQ-01`, already `Status: resolved` and `Blocking: no` with `Owner: maintainer` (2026-11-24 `/askme` ruling). All seven review findings (`PR-001..PR-007`) have `Overall:Low` remediation risk and were fixed in place. Three autonomous review decisions (`D-1..D-3`) are recorded below; all three are `Reversible: yes`. No human decision or blocking open question remains.

### Pass 2

- Re-read the complete revised plan end to end after applying all edits (`PR-001..PR-007`), transitioned `- Status:` to `reviewed` via `aw ipd set reviewed 7gverp`, and ran `aw ipd lint --phase review-finalize --agent`.
- Verified `5/5` E/V bijection, unchanged E/V IDs and checkbox states, `- Status: reviewed`, `- Readiness: go-pending-approval`, `- Review-Depth: complex`, newest-first `## Workflow history` entries, matching Mermaid diagram terms, zero em or en dashes, and zero `error` or `warning` diagnostics.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R1 / R4 A / R4 D / S5 | `.aw/records/plans/pending/20261124-comphome-02-7gverp-fix-installer-clean-delta-hijack-companion-project-policy-di.ipd.md` `E-02`, `OQ-01`; `agent_workflows/project_schema.py::PRESET_PLACEMENTS:289`; `agent_workflows/project_context.py::_resolve_project_context_uncached:2460`; `agent_workflows/placement_switch.py::plan_placement_switch:626,1081`; `tests/test_installer.py:809`; `tests/test_placement_switch_companion_plan.py:188,217,233`; `tests/test_placement_switch_companion_execute.py:353`; `tests/test_placement_switch_companion_cli.py:199` | `E-02` did not encode resolved `OQ-01` (`config_project = target-tracked / target-git`), missed `project_schema.py` (`PRESET_PLACEMENTS`), missed `RootClass.SYSTEM` in `project_context.py:2460`, missed `placement_switch.py` actively setting `config_retrack = "untrack"` and `config-becomes-untracked` on companion attach, and omitted the 4 existing tests pinning the overruled policy. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote `E-02` and `V-02` to encode `OQ-01` across `install_wizard.py`, `project_schema.py`, `project_context.py` (`SYSTEM` + `CONFIG_PROJECT`), and `placement_switch.py`, and added the 2 missing modules and 4 pinning test files to `- Scope-Paths:`. Recommendation strength: very strong. |
| PR-002 | HIGH | IN-SCOPE | R1 / R4 D | `.aw/records/plans/pending/20261124-comphome-02-7gverp-fix-installer-clean-delta-hijack-companion-project-policy-di.ipd.md` `E-03`; `agent_workflows/cli.py::_run_install:9772-9783,9966-9988`; `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md:143` | Defaulting `companion_dir = <anchor>.aw` unconditionally in `install_wizard.py::resolve_policy_noninteractive` would bypass `cli.py:9772-9783`'s spec-mandated refusal requiring explicit `--companion-dir <path>` on `--relocate` switches into `public-target-private-companion`; `cli.py:9978-9987` also uses `check=False` on `git init` and omits `aw_home=policy.aw_home` when calling `storage.attach_companion`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scoped the `<anchor>.aw` default in `E-03` strictly to first install (`existing_policy is None`), added `--relocate` refusal verification to `V-03`, and required `git init` exit check + `aw_home=policy.aw_home` forwarding in `cli.py::_run_install`. Recommendation strength: very strong. |
| PR-003 | HIGH | IN-SCOPE | R1 / R4 A / R4 D | `.aw/records/plans/pending/20261124-comphome-02-7gverp-fix-installer-clean-delta-hijack-companion-project-policy-di.ipd.md` `E-01`; `agent_workflows/engine.py::_clean_delta_home_trees:589`, `migrate_local_lanes_to_untracked:8361,8377`, `show_install_diffs:4944`, `run:8824,8841`; `tests/test_clean_target_config_home.py::test_case_u_uninstall_recovers_partial:1088` | `E-01` left three execution traps: `_clean_delta_home_trees` branch (b) must check only `("system", "state", "worktrees")` while keeping `test_case_u_uninstall_recovers_partial` working; `migrate_local_lanes_to_untracked` line 8377 writes a stray nested `.gitignore` into external companion/`home` directories unless scoped to `.agents/`; and `run()` `--diff` also needs `clean = _is_clean_delta_install(plan.repo_root)` to drop shims/skills/in-target scaffolds and resolve scaffold existence via `_records_member_destination`/`_system_member_destination`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified all four sub-steps explicitly in `E-01` and `V-01`, including `test_case_u_uninstall_recovers_partial` verification. Recommendation strength: very strong. |
| PR-004 | HIGH | UNDER-SCOPE | R2 / S7 | `.aw/records/plans/pending/20261124-comphome-02-7gverp-fix-installer-clean-delta-hijack-companion-project-policy-di.ipd.md` `## Approval and execution gate` | Execution gate omitted mandatory contract clauses: resolved open-question status, scope-fence declaration (`--scope-reason`/`--scope-ack`), hard-MUST honesty rule (paste actual output), ban on `git add -A`/`-a`/bare, and conditional runner/executor finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the complete execution contract and updated `- Size assessment: exception` with cohesion rationale in `## Approval and execution gate`. Recommendation strength: very strong. |
| PR-005 | MEDIUM | IN-SCOPE | R3 / R4 D | `.aw/records/plans/pending/20261124-comphome-02-7gverp-fix-installer-clean-delta-hijack-companion-project-policy-di.ipd.md` `E-04`, `V-04`; `agent_workflows/leak_sanitizer.py::resolve_allowlist_path:181`; `tests/test_leak_sanitizer.py:1451` | In `clean-delta` mode, falling back to `<repo>/.agents/local-leaks-allowlist.toml` when `<AW_HOME>/projects/<pid>/config/local-leaks-allowlist.toml` does not yet exist would cause `aw sanitize --configure` to write into the target repo, violating `clean-delta` zero-footprint containment. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-04` and `V-04` to skip the in-tree `.agents/` fallback whenever `project_config_dir(repo_root)` resolves outside `repo_root`, while preserving `.aw/config/` -> `.agents/` precedence for in-tree repos. Recommendation strength: strong. |
| PR-006 | MEDIUM | UNDER-SCOPE | R2 / R4 E / R4 Spec Sync | `.aw/records/plans/pending/20261124-comphome-02-7gverp-fix-installer-clean-delta-hijack-companion-project-policy-di.ipd.md` `## Required tests / validation`, `## Spec / documentation sync`, `## Deferred / out of scope`, `V-01..V-05` | `## Required tests / validation` omitted affected regression suites (`test_installer.py`, `test_placement_switch_companion_*.py`, `test_project_layout.py`, `test_reinstall_preserves_config.py`, `test_clean_target_config_home.py`), `V-01..V-03` did not assign exact test files, `## Deferred / out of scope` omitted sibling carriers `mmuv3v`/`7eivm2`/`7hfx7r`/`4vnd36`, and `## Spec / documentation sync` remained conditional despite resolved `OQ-01`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Expanded `## Required tests / validation` and `V-01..V-05`, listed all five sibling carriers in `## Deferred / out of scope`, and substantiated `## Spec / documentation sync` against `ARCHITECTURE.md:91`, `README.md:138`, and spec `20260810-1447-01:143`. Recommendation strength: strong. |
| PR-007 | MEDIUM | IN-SCOPE | Check P / Tech Writing Req 12 | `.aw/records/plans/pending/20261124-comphome-02-7gverp-fix-installer-clean-delta-hijack-companion-project-policy-di.ipd.md` `## Proposed changes (ordered, validatable)`, `E-01..E-05` | Plan changes 7 related modules and specifies a branched install/recovery/policy flow with no Mermaid diagram (Technical Writing Standard Req 12(a)/(b)), packed multiple actions into run-on sentences, and used non-canonical code citations. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a Mermaid `flowchart TD` matching plan terms, converted `E-01..E-05` into numbered sub-steps, and standardized `path::Symbol` citations. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Keep `7gverp` as one Order-02 child (`- Size assessment: exception`, 14 work `Scope-Paths`) or split `placement_switch.py` and the 4 pinning tests into another child plan? | Keep in `7gverp` (`5` E-items, `4` task groups) with an explicit cohesion rationale | Split `placement_switch.py` and test updates into a separate child plan (leaves `pytest` red between merges) | Changing `public-target-private-companion` `config_project` to `target-git` requires atomic updates to `project_schema.py`, `placement_switch.py`, and the 4 pinning tests (`tests/test_installer.py:809`, `tests/test_placement_switch_companion_*.py`); `IPD-Z603` is advisory `info` only | yes |
| D-2 | Should `resolve_policy_noninteractive` default `companion_dir` to `<anchor>.aw` during `--relocate` switches or only on first install? | First install (`existing_policy is None`) only | Apply default on `--relocate` too (contradicts `cli.py:9772-9783` and spec `20260810-1447-01:143`) | `agent_workflows/cli.py:9772-9783`; `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md:143` | yes |
| D-3 | Should `leak_sanitizer.py::resolve_allowlist_path` fall back to `<repo>/.agents/local-leaks-allowlist.toml` in `clean-delta` mode? | No; return `project_config_dir(repo_root) / "local-leaks-allowlist.toml"` directly whenever `project_config_dir` resolves outside `repo_root` | Keep `.agents/` fallback unconditionally (would let `aw sanitize --configure` write inside a `clean-delta` target repo) | `agent_workflows/leak_sanitizer.py:181-197`, `443`; `clean-delta` zero-target-footprint invariant | yes |

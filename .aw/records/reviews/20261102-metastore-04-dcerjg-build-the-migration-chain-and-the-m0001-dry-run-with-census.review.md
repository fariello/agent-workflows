# Review findings: plan dcerjg

- Subject-Id: dcerjg
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `4f09df0c7` in a runner review-sweep lane worktree (non-interactive). The lane-input
copy (revision 7) is byte-identical to the tracked plan, which was committed and unmodified, so no
pre-review snapshot was needed. `aw ipd lint --phase author` was clean before the edits and
`--phase review-finalize` was clean after them.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| E-01, V-01, Scope-Paths | Add `metadata_schema` to `known_keys` "and the second parser beside it" | Add a `ProjectPolicySchema` field and the `install_wizard` fallback key set, carry the value through the reinstall rebuild, write atomically; `install_wizard.py` added to Scope-Paths | PR-001. |
| E-01, OQ-03, AC list | `require_current_schema` had no caller | Called from `artifact_meta`'s read-path refresh; AC-11 case 1 proven at the interface | PR-002. |
| E-10 | The plan spelled the staged-prompt mirror text itself | The mirror and banner are rendered by `artifact_meta`'s mirror writer (`tve77h`) | PR-003. |
| E-15, V-15 | Clone to `<tmpdir>`, copy a sidecar that a lane does not have, no statement of which package runs | Clone to the gitignored `tmp/dcerjg-clone`, a synthetic sidecar when none is present, the clone's own package, and code committed before the clone | PR-004. |
| E-04 | Worktree check by comparing `--git-dir`; `None` cases unstated | Absolute paths compared; `None` refuses or shows as unknown | PR-005. |
| E-07, V-07 | 34 entries as the bar | The bar is a re-derived property; the fixed rows are terminal-record facts | PR-006. |
| OQ-02, E-09, Scope check | Add a roadmap entry "if `tve77h` did not" | `tve77h` has seven types and no roadmap, so E-09 adds it | PR-007. |
| E-11, V-11 | Marker location and lifetime unstated | Resolved through `state_durable`, read-only in the hooks, deleted after commit or rollback | PR-008. |
| E-01, V-16, gate, E-16 | No `aw check` baseline, one commit after the clone proof, partial gate | Baseline saved before E-01, code committed before E-15, full gate | PR-009. |
| E-13 | Sanitizer threshold unstated against the imported bytes | `fail` refuses and `warn` is reported; `aw sanitize --agent` runs on the clone | PR-009. |
| F-13, F-17 | `run_rename_generic` named as the hard-coding site; no review measurements | `compute_target_name` named; review re-measurements added | R1 drift. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes: it adds the CLI commands `aw migrate metadata`, `aw migrate layout` and `aw install --migrate`, a `project.json` key, and changes to two commit hooks.
2. Yes: it changes `hooks/executed_transition_gate` and `hooks/backlog_blocking_close_gate`, adds a lock and worktree preflight, and rewrites the record corpus (on a clone only).
3. Yes: 16 E-items in 5 task groups touching about 15 modules.
4. Yes: 25 Scope-Paths, plus `install_wizard.py` added by this review.
5. Yes: the cutover it prepares is irreversible, and a bad hook bypass would admit unreviewed terminal edits.

AW-TIER: complex

### Step R1

- Checked, and present as claimed: `layout_migration.MigrationManager` and its `_acquire_lock`, `_save_transaction`, `_load_transaction`, `resume_migration` and `rollback_migration` methods; the shared `migration_transaction.json` path; `ipd_lifecycle.checkout_git_common_dir`; `platform_lock.probe_free`, which can return `None`; `runner_shared.lane_work_has_landed`, `integration_lock_path` and `integration_lock`; `artifact_core.mint_id6` and `REFERENCE_SCAN_ROOTS` (which already includes `tests`); `artifact_refs.plan_reference_rewrites_with_warnings`, whose `scan_roots` is a parameter; `artifact_naming._LEGACY_TIMESTAMP_RE`; `attention_contract.newest_history_record`; `command_surface.find_undeclared_leaves` and the `migrate-layout` declaration; the `install` and `setup` `-y` help texts; `hooks/*.check`; `runner_shared._assert_probe_spawn_is_permitted`; and CHANGELOG `2.0.0 (pending)`.
- `agent_workflows/migrations/` is absent and `aw migrate` does not exist, as F-01 says. There are 35 legacy-timestamp files outside comms, as F-02 says. `wvlk84` and `cwjnj0` exist, and `awphysical-01` would collide, as OQ-26 says. The six preserved `- Id:` files match F-04.
- F-13 named the wrong function: the hard-coded `set_id=mint_id6, order=1` is in `artifact_rename.compute_target_name`, which `run_rename_generic` calls. E-07 already names the right function. Corrected.
- `project_schema.parse_portable_policy` has no "second parser beside it" for `project.json`. The only other copy of the key set is the fallback `known_proj_keys` in `install_wizard`, and `ProjectPolicySchema.to_dict` re-serializes only named fields plus `unknown_fields` (PR-001).
- `tve77h` E-01 registers seven types and no `roadmap` (PR-007).

### Step R2

- Checked: the E/V bijection is 16/16, and every V item demands pasted test runs, diffs or clone output.
- Reachability: V-01's refusal was unreachable as authored because no caller existed (PR-002). V-15's clone demonstrations are reachable through E-15's own commands once the code is committed first and the clone runs its own package (PR-004).
- The 34-row bar was a live-artifact count (PR-006).
- `- Item-Dependencies: executed:tve77h` is sufficient. E-09 and E-13 use `tve77h`'s event model, loader and writer validation. `ya4ee4` depends on this plan, not the reverse.

### Step R3

- Checked: the two hook edits create a bypass of the executed-transition and release-close gates. The authored design binds the bypass to the exact staged tree id, which is sound. Review added a resolved location, read-only use, consumption after commit or rollback, and a test that a consumed marker no longer admits a commit (PR-008).
- The preflight's `None` cases now fail closed (PR-005).
- Leak scanning: `fail` refuses `--apply`, as 5.2 step 6 and AC-16 require (PR-009).
- No `--no-verify`. The clone is gitignored and is deleted afterwards.

### Step R4

- A: the journal, resume and rollback reuse `MigrationManager`, and the idempotence test is in E-13. The stamp write is atomic and keeps every other key (PR-001).
- C: mirror and banner text has one owner, `artifact_meta` (PR-003). There is no second journal or lock component.
- D: the reinstall regression on the stamp is now tested (PR-001), and `tests/test_install_config_trailing_newline.py` stays green.
- E: the plan has a test per AC case.
- F: `--yes` never runs a migration.
- Spec sync: no spec change, which is truthful. The user documents are `90iqr1`'s.

### Step R5

- Checked through the eight personas:
  - QA and regression: the stamp round-trip and the consumed-marker case were added.
  - Architect: one mirror writer and one read-path schema check.
  - Engineer: the clone procedure is now executable from a lane.
  - Power user: `aw migrate layout` is added and `aw migrate-layout` keeps working (OQ-06).
  - Novice: the refusal names the command to run.
  - Stakeholder: the irreversible run stays in `cxxmyv`, attended.

### Step R6

- Checked: 16 E-items in 5 groups. OQ-01 records a clean seam into `04a` and `04b`. Each E-item is one concern. No split is recommended (D-2).

### Step R7

- Checked the consumers of this plan:
  - `ya4ee4` E-07 fills the `describer` seam this plan defines, and its `--apply` rule matches E-12.
  - `cxxmyv` E-02 runs the dry run in the main checkout and owns AC-22 case 2. Its E-03 flips `CURRENT_METADATA_SCHEMA` and moves the legacy loader into `m0001`. Its E-04 removes the source-side sidecar lines.
  - `9o83cr` relies on this plan's step 5.
  - `t4gl15` changes the same two hook files, in their read path. Both plans run in phase B, after this plan, so they do not conflict; the runner isolates lanes in any case.
- The AC-11 CLI-level demonstration depends on Orders 08 and 09 moving readers onto `artifact_meta`, and is now stated as `cxxmyv`'s.

### Step S5

- Checked: OQ-01 to OQ-06 are resolved and non-blocking. OQ-02 was amended with the `tve77h` fact, and OQ-03 with the caller. No new human question.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R4 A / D | `install_wizard` rebuilds `ProjectPolicySchema(...)` from named fields plus `unknown_fields`; `known_proj_keys` fallback copy; plan E-01 "add `metadata_schema` to `known_keys`" | Moving the key out of `unknown_fields` without adding a schema field silently drops the stamp on the next `aw install`. A dropped stamp after the cutover makes every command refuse a migrated repository. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a schema field, the fallback key, the reinstall carry-through, an atomic write, and a reinstall test; `install_wizard.py` added to Scope-Paths. |
| PR-002 | MEDIUM | UNDER-SCOPE | R2 reachability / 5.3 | E-01 defines `require_current_schema`; no E-item calls it | The AC-11 refusal had no code path, so "every command refuses" could not be observed. | Low | FIXED | Called from `artifact_meta`'s read-path refresh; proven at the interface now; the CLI form is `cxxmyv`'s. |
| PR-003 | MEDIUM | IN-SCOPE | R4 C | E-10 spelled the `aw-managed-prompt` line; `tve77h` E-07/E-15 own mirror rendering | Two spellings of one mirror can drift, so a migrated prompt would fail `aw check meta`. | Low | FIXED | E-10 uses `artifact_meta`'s mirror writer. |
| PR-004 | MEDIUM | IN-SCOPE | R2 G | E-15 `<tmpdir>/copy`, "copy the gitignored `.aw/records/history.jsonl`"; F-17 shows no sidecar in a lane | Not executable from a runner lane: the clone was outside the workspace, the sidecar was absent, and uncommitted code would not be in a clone. | Low | FIXED | Clone under `tmp/`, a synthetic sidecar when none is present, the clone's own package, code committed first. |
| PR-005 | MEDIUM | IN-SCOPE | R3 fail-closed | `platform_lock.probe_free` "None is a real answer"; `lane_work_has_landed` returns None | The preflight could read "unknown" as "free". | Low | FIXED | `None` refuses (lock, common dir) or shows as unknown (lanes). |
| PR-006 | LOW | IN-SCOPE | R2 live-artifact convention | E-07 "the map has 34 entries" | A live count was used as the bar. | Low | FIXED | Re-derived property bar; counts kept as context. |
| PR-007 | LOW | IN-SCOPE | R1 | `tve77h` E-01 lists seven types | "If `tve77h` did not" left the roadmap entry conditional and unowned. | Low | FIXED | E-09 adds it; tested. |
| PR-008 | MEDIUM | UNDER-SCOPE | R3 gate bypass | E-11 marker | The marker's location and lifetime were unstated, so a stale marker could admit a later commit. | Low | FIXED | Resolved path, read-only in the hooks, consumed after commit or rollback, tested. |
| PR-009 | MEDIUM | UNDER-SCOPE | S7 contract / R2 | V-16 "before E-01" baseline; gate | No item captured the baseline; the commit order contradicted E-15; the gate was partial; the sanitizer threshold was unstated. | Low | FIXED | Baseline saved in E-01, two-commit order, full gate, `fail`/`warn` rule. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where does the schema refusal live? | One call in `artifact_meta`'s read-path refresh | A call in every command (scattered, violates C5); a CLI-wide preflight (refuses `aw migrate` itself) | spec 5.3, C5; `tve77h` E-13 | yes |
| D-2 | Split into 04a and 04b? | No | Split at the OQ-01 seam | Each E-item is one concern; 16 of 18 items | yes |
| D-3 | How does a lane run the clone proof without the sidecar? | A synthetic sidecar, recorded; the real line stays with `cxxmyv` E-02 | Block E-15 until it is run in the main checkout | `cxxmyv` E-02 owns AC-22 case 2 | yes |
| D-4 | Does a `warn` leak finding refuse `--apply`? | No: listed, not refused | Refuse on `warn` too | spec 5.2 step 6 and AC-16 name `fail`; `tve77h` E-03 (d) scans imported bytes | yes |

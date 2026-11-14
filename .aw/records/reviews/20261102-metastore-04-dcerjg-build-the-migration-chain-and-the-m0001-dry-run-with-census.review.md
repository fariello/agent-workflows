# Review findings: plan dcerjg

- Subject-Id: dcerjg
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
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

## Round 2

> Written to `.aw/system/workflows/technical-writing/technical-writing.md`. Every obligation, exact identifier, quotation, evidence record, and lifecycle status is preserved.

Re-reviewed at `HEAD` `0ea2db75d` in an isolated runner review-sweep worktree after the 2026-11-07 approval withdrawal (for amended spec `4sd62s` `C12`, `5.2a`, and `AC-42`) and the 2026-11-07 and 2026-11-09 plan splits (`g8na48`, `vxevph`, `1vfqdu`, `dky26u`, `ghhzb6`, `hpedmn`, and `o19353`). Pre-edit `git status --short` was clean (pre-review snapshot skipped unchanged); `aw ipd lint --phase author --agent` had 2 `info` findings (`IPD-C802` em dashes) before edits and 0 findings across all severities after edits.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter, Workflow history | Missing `executed:g8na48` dependency, `g8na48`/`g5hpbb`/`830wku`/`clors0` scope alignment, and technical-writing standard header | Added `executed:g8na48` to `- Item-Dependencies:`, updated `Concern` and `Scope` for `g8na48`, `g5hpbb` (`9vf2iv`, `6oi2nu`, `3g20ms`, `bv4kkj`), `830wku`, and `clors0`, and added the technical-writing header note | `PR-013`, `PR-014`, `PR-015`. |
| `Detailed Implementation Checklist` (`:40-55`), `Deferred` (`:126-144`) | Five split-part `Carrier:` bullets pasted inside a broken inline backtick span in the checklist | Replaced with a clean summary sentence and moved all seven split-part `Carrier:` entries (plus `g5hpbb` and `clors0`) into `## Deferred / out of scope (with reason)` | `PR-014`. |
| `E-12`, `V-12` | Census lacked `project_context.project_records_dir(repo)`, `"no sidecar (none expected)"`, and absent-template handling | Specified repository-agnostic `project_records_dir(repo)`, zero hard-coded `id6`/count constants, `"no sidecar (none expected)"` accounting (`4sd62s` `5.2a`), and clean skipping of absent template paths | `PR-014`. |
| `E-13`, `Scope check`, `V-13` | Omitted top-of-`run` `read_metadata_schema >= 2` guard, step-6 `write_metadata_schema(repo, 2)` stamp write, step-7 commit execution, and Phase-A-safe `artifact_meta.replay` + `SUPPORTED_TYPES` check | Wired top-of-`run` `read_metadata_schema >= 2` guard, direct `artifact_meta.replay` + mirror-parser verification (ensuring `"roadmap"` is in `SUPPORTED_TYPES`), journal-backed `write_metadata_schema(repo, 2)` before staging and `terminal_commit_marker`, and `commit=True` step-7 `offer_commit` + marker deletion | `PR-010`, `PR-012`. |
| `E-14`, `E-15`, `V-15` | Assumed `git clone` runs commit hooks without installing `.git/hooks/pre-commit`, named `"the backlog close gate"` informally, and missed `commit_lock.commit_isolated`'s detached `.aw-isocommit-*` worktree | Installed executable `.git/hooks/pre-commit` invoking `python3 -m agent_workflows ipd-executed-gate` and `python3 -m agent_workflows backlog-blocking-close-gate` in `E-14` and `E-15`, noted `ipd_lifecycle.checkout_control_root` marker lookup across `commit_isolated`, and sequenced `commit=False` inspection + `commit_staged` | `PR-011`. |
| `E-16`, `V-16`, `AC-11`, `OQ-01..OQ-04` | Assumed gitignored `.aw/state/dcerjg/check-before.jsonl` exists in an isolated lane, omitted `g8na48` on `AC-11`/`OQ-03`, used conditional tense for executed `tve77h` in `OQ-02`, and cited bare line numbers in `F-09`/`OQ-04` | Added deterministic regeneration of `.aw/state/dcerjg/check-before.jsonl` from `g8na48` `F-03`'s recorded `HEAD` SHA, credited `g8na48`, updated `OQ-02` for executed `tve77h`, and anchored `F-09`/`OQ-04` by `<!-- aw-prompt:` content | `PR-012`, `PR-013`, `PR-015`. |
| `Findings` (`F-18`), `Proposed changes`, `Validation-state rule` | No Round 2 re-measurements, no Requirement 12 Mermaid diagram, and two `IPD-C802` em dashes | Added `F-18` at `HEAD` `0ea2db75d`, added Mermaid `flowchart TD` diagram of `m0001_metadata_v2.run`, and replaced both em dashes with parentheses | `PR-015`. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes: wires `4sd62s` 5.2 steps 6 and 7 into `m0001_metadata_v2.run` (`aw migrate metadata --apply` and bare `aw migrate --apply`), stamps `metadata_schema: 2` in `project.json`, and exercises commit-gate hooks.
2. Yes: interacts with `hooks/executed_transition_gate.py`, `hooks/backlog_blocking_close_gate.py`, `commit_lock.commit_isolated`, `leak_sanitizer`, and the terminal commit marker on a full repository clone.
3. Yes: integrates 7 upstream split plans (`g8na48`, `vxevph`, `1vfqdu`, `dky26u`, `ghhzb6`, `hpedmn`, `o19353`) and runs a 10-module family gate plus a full-clone dry-run/apply/commit/second-apply proof.
4. Yes: 5 `Scope-Paths` directly, plus verification over 9 upstream migration modules and test suites.
5. Yes: final verification gate in Phase A before Order 13 (`cxxmyv`) executes the irreversible cutover commit.

AW-TIER: complex

### Step R1

- Verified live codebase state at `HEAD` `0ea2db75d`: `agent_workflows/migrations/` does not yet exist; `tve77h` is executed; `artifact_meta.REGISTRY` has 7 keys (`backlog`, `ipd`, `prompt`, `release`, `research`, `spec`, `walkthrough`), while `artifact_meta.SUPPORTED_TYPES` (`agent_workflows/artifact_meta.py:57`) is a separate module-level 7-tuple checked independently in `replay` (`:967`), `_load_sources` (`:2581`), and `read` (`:3235`) (`PR-012`).
- Verified `artifact_meta.check_freshness` (`agent_workflows/artifact_meta.py:3038`) walks `records_root` in `os.walk` order and calls Phase-B `load_legacy_artifact` (`:2923`) and `load_legacy_review` (`:2431`, `_parse_bullet_metadata`) on `.md` and `.review.md` files, whereas `artifact_meta.replay(id6, art_type, lines, records_root=scratch_records_root)` replays `meta/<id6>.jsonl` directly with zero Phase-B legacy `.md`/`.review.md` side effects (`PR-012`).
- Verified `git clone --no-hardlinks . tmp/...` succeeds from this linked worktree (`rc=0`), creates only `.git/hooks/*.sample` files, and `.pre-commit-config.yaml` omits opt-in `backlog-blocking-close-gate` (`PR-011`).
- Verified `aw commit --no-plan` (`work_cmd.py:959` -> `git_commit_helper.offer_commit` -> `commit_lock.commit_isolated` at `agent_workflows/commit_lock.py:351-415`) runs `git commit` inside a detached linked worktree `.aw-isocommit-*` where `<wt>/.aw/state/durable` is absent and `ipd_lifecycle.checkout_control_root(wt)` (`agent_workflows/ipd_lifecycle.py:447-463`) collapses back to the primary checkout's `.aw` (`PR-011`).
- Re-measured corpus counts at `HEAD` `0ea2db75d` (`F-18`): 35 legacy-timestamp records outside comms, 4,719 tracked `.md` files under `.aw/records`, 1,330 `.review.md` files, and no `.aw/records/history.jsonl` in this runner lane.

### Step R2

- Checked 1:1 `E-*`/`V-*` bijection (`E-12..E-16` <-> `V-12..V-16`, `- Highest E allocated: 16`).
- Found and closed three reachability gaps:
  1. `E-13` and `E-15` step (e) (`"metadata_schema is 2; nothing to do"`) were unreachable because no split part wired the top-of-`run` `chain.read_metadata_schema(repo) >= 2` guard, the step-6 `chain.write_metadata_schema(repo, 2)` stamp write, or the step-7 commit (`PR-010`).
  2. `V-15` demanded `"aw commit --no-plan output with both hooks passing"` on a fresh `git clone`, which runs zero hooks unless `.git/hooks/pre-commit` is installed (`PR-011`).
  3. `V-16` demanded comparing `aw check --agent` against gitignored `.aw/state/dcerjg/check-before.jsonl`, which is absent when `dcerjg` executes in an isolated lane separate from `g8na48`, and `- Item-Dependencies:` omitted `executed:g8na48` (`PR-013`).

### Step R3

- Checked gate-bypass and commit-isolation safety: `write_metadata_schema(repo, 2)` now runs before staging the migration's explicit path list and writing `o19353` E-01's `git write-tree` marker so the marker binds the exact staged tree including `project.json`, and `terminal_commit_marker` is deleted immediately after step-7 `offer_commit` succeeds and on `rollback` (`PR-010`).
- Installing `.git/hooks/pre-commit` in `E-14` and `E-15` proves both `ipd-executed-gate` and `backlog-blocking-close-gate` under real `commit_lock.commit_isolated` detached-worktree execution without `--no-verify` (`PR-011`).
- Safety invariant preserved: `--apply` never runs in this checkout, and `git status --porcelain | sha256sum` of this checkout is verified equal before and after `E-15`.

### Step R4

- Checked transactionality, idempotency, and `4sd62s` `C12` / `5.2a` repository-agnosticism:
  - `project.json` is backed up in `journal_dir / "backups"` before `write_metadata_schema(repo, 2)` so `rollback(repo)` restores pre-apply `project.json` (`PR-010`).
  - `m0001_verify.py` resolves `records_root` via `project_context.project_records_dir(repo)` with zero repository-specific `id6` or count constants, handles `"no sidecar (none expected)"` (`vxevph` E-04), and skips absent template paths cleanly (`PR-014`).
  - `commit=True` defaults `m0001_metadata_v2.run(..., apply=True)` to full `4sd62s` 5.2 step-0..step-7 completion while `commit=False` + `commit_staged` supports `E-15`'s staged-tree inspection (`D-5`, `PR-010`).

### Step R5

- Checked through the eight reviewer personas:
  - QA/QC and testing/regression caught that `git clone` installs no `.git/hooks/pre-commit` and that `commit_isolated` runs hooks inside `.aw-isocommit-*` where worktree-local `.aw/state/durable` is absent (`PR-011`).
  - Architect caught the unowned gap between `g8na48` (`write_metadata_schema`), `o19353` (`terminal_commit_marker`), and `clors0`/`cxxmyv` (`aw migrate metadata --apply` making one step-7 commit) (`PR-010`), plus `artifact_meta.SUPPORTED_TYPES` vs `REGISTRY` (`PR-012`).
  - Software engineer and power user caught the missing `executed:g8na48` dependency and cross-lane `.aw/state/dcerjg/check-before.jsonl` regeneration (`PR-013`).
  - Technical writer and novice caught the broken inline backtick span in `Detailed Implementation Checklist` (`:40-52`) and missing Requirement 12 flowchart (`PR-014`, `PR-015`).

### Step R6

- Checked plan sizing against `IPD-Z603`: 5 `E-*` items (`E-12`..`E-16`) in 1 task group and 4 work `Scope-Paths` (`m0001_verify.py`, `m0001_metadata_v2.py`, `tests/test_m0001_roundtrip.py`, `CHANGELOG.md`), well within the 5-item / 8-work-path ceiling (`aw ipd lint --phase author --agent` reports 0 findings). No further split is warranted.

### Step R7

- Checked cross-plan alignment across orchestrator `63ib9r` (`E-04`, `E-15`..`E-19`, `E-55`, `E-56`), upstream parts `tve77h` (executed), `g8na48` (reviewed), `vxevph` (reviewed), `1vfqdu`, `dky26u`, `ghhzb6`, `hpedmn`, and `o19353`, and downstream plans `odeo9z`/`830wku`/`ya4ee4` (Order 05), `9vf2iv`/`6oi2nu`/`3g20ms`/`bv4kkj`/`g5hpbb` (Order 14, `C12`/`5.2a`/`AC-42`), `ffceq0` (Order 08), `9o83cr` (Order 11), `clors0` (`E-19`), `5qyba0`, and `cxxmyv` (`E-02`, `E-10`).
- Confirmed `g8na48` (`E-01`, `F-03`), `o19353` (`E-01`), `1vfqdu` (`E-02`), `g5hpbb` (`E-07`), `clors0` (`E-19`), and `cxxmyv` (`E-10`) now join cleanly with `dcerjg` `E-12`..`E-16`.

### Step S5

- Checked `OQ-01`..`OQ-06` and all Round 2 findings (`PR-010`..`PR-015`): every open question is resolved and non-blocking, every Round 2 finding has Low Remediation Risk and is `FIXED` in place from repository and spec evidence (`D-5`..`D-8`), and zero human questions remain.

### Pass 2

- Re-read `.aw/records/plans/pending/20261102-metastore-04-dcerjg-build-the-migration-chain-and-the-m0001-dry-run-with-census.ipd.md` end-to-end and ran `aw ipd lint --phase author --agent`: `outcome: "clean"`, `exit: 0`, `findings: 0`.
- Verified `E-12..E-16` <-> `V-12..V-16` 1:1 bijection, `- Highest E allocated: 16`, valid Mermaid `flowchart TD` syntax, zero `TODO` placeholders, zero em/en dashes, zero bare line numbers, zero absolute paths, and zero `file://` URIs.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-010 | BLOCKER | UNDER-SCOPE | R2 / R4 / R7 | `.aw/records/plans/pending/20261102-metastore-04-dcerjg-build-the-migration-chain-and-the-m0001-dry-run-with-census.ipd.md:63,147`; `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:771-784`; `.aw/records/plans/pending/20261109-metastore-100-o19353-build-the-m0001-terminal-commit-marker-index-cleanup-step-an.ipd.md:37`; `.aw/records/plans/pending/20261108-metastore-48-clors0-build-the-dormant-log-format-gates-readers-event-overrides-c.ipd.md:39` | After the 2026-11-07 and 2026-11-09 splits, no part wired into `m0001_metadata_v2.run` (1) the top-of-`run` `chain.read_metadata_schema(repo) >= 2` guard returning `"metadata_schema is 2; nothing to do"` before preflight, (2) the journal-backed `chain.write_metadata_schema(repo, 2)` stamp write before staging and writing `o19353`'s `git write-tree` marker, or (3) `4sd62s` 5.2 step-7 commit execution (`offer_commit` + marker deletion), leaving `E-13`/`E-15`(e) unreachable and breaking `1vfqdu` `E-02`, `g5hpbb` `E-07`, `clors0` `E-19`, and `cxxmyv` `E-10` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Wired the top-of-`run` `read_metadata_schema >= 2` guard, journal-backed `write_metadata_schema(repo, 2)` before staging and `terminal_commit_marker`, and `commit=True` step-7 `offer_commit` + marker deletion (plus `commit=False` / `commit_staged`) into `E-13`, `Scope check`, and `V-13` (strength: very strong). |
| PR-011 | HIGH | IN-SCOPE | R1 / R3 / R7 | `.aw/records/plans/pending/20261102-metastore-04-dcerjg-build-the-migration-chain-and-the-m0001-dry-run-with-census.ipd.md:68,73,238`; `agent_workflows/commit_lock.py:351-415`; `.pre-commit-config.yaml:1-35`; `.aw/records/plans/pending/20261109-metastore-100-o19353-build-the-m0001-terminal-commit-marker-index-cleanup-step-an.ipd.md:37` | `git clone --no-hardlinks` installs only `.git/hooks/*.sample` and `backlog-blocking-close-gate` is absent from `.pre-commit-config.yaml`, so `aw commit --no-plan` in `E-15` and `tmp_path` fixtures in `E-14` run zero hooks unless `.git/hooks/pre-commit` is installed; moreover `commit_lock.commit_isolated` runs `.git/hooks/pre-commit` inside a detached `.aw-isocommit-*` linked worktree where `<wt>/.aw/state/durable` does not exist unless marker lookup falls back to `ipd_lifecycle.checkout_control_root(root) / "state" / "durable"` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required installing an executable `.git/hooks/pre-commit` invoking `python3 -m agent_workflows ipd-executed-gate` and `python3 -m agent_workflows backlog-blocking-close-gate` in `E-14` and `E-15` (and `V-15`), exercising `commit_isolated` and specifying the `checkout_control_root` marker-lookup fix (`--scope-reason`) if `o19353` omitted it (strength: very strong). |
| PR-012 | HIGH | IN-SCOPE | R1 / R7 | `.aw/records/plans/pending/20261102-metastore-04-dcerjg-build-the-migration-chain-and-the-m0001-dry-run-with-census.ipd.md:63,192`; `agent_workflows/artifact_meta.py:57,967,2431,2581,3038,3235`; `.aw/records/plans/pending/20261107-metastore-19-hpedmn-build-the-m0001-review-events-and-convert-research-records-w.ipd.md:38` | `E-13` did not specify calling `artifact_meta.replay` directly (avoiding Phase-B `check_freshness`'s `os.walk` `load_legacy_artifact` and `load_legacy_review` `_parse_bullet_metadata` scan on rewritten mirrors and templates) and missed that `artifact_meta.SUPPORTED_TYPES` (`:57`) is checked separately from `REGISTRY` in `replay` (`:967`), which rejects `"roadmap"` if `hpedmn` E-01 updated only `REGISTRY`; `OQ-02` also referred to executed `tve77h` in future tense | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified `artifact_meta.replay(id6, art_type, lines, records_root=scratch_records_root)` plus mirror-parser checks and `"roadmap"` membership in `SUPPORTED_TYPES` (`--scope-reason` if needed) in `E-13`, and updated `OQ-02` for executed `tve77h` (strength: very strong). |
| PR-013 | HIGH | UNDER-SCOPE | R1 / R2 / R7 | `.aw/records/plans/pending/20261102-metastore-04-dcerjg-build-the-migration-chain-and-the-m0001-dry-run-with-census.ipd.md:6,8,78,157,199,242`; `.aw/records/plans/pending/20261109-metastore-101-g8na48-build-the-migration-chain-the-metadata-schema-stamp-and-the.ipd.md:43,75,97` | Round-3 split `g8na48` (split from `vxevph` on 2026-11-09) was missing from `- Item-Dependencies:` and plan text, and `E-16`/`V-16` lacked cross-lane regeneration of gitignored `.aw/state/dcerjg/check-before.jsonl` from `g8na48` `F-03`'s recorded `HEAD` SHA when `dcerjg` runs in an isolated worktree | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `executed:g8na48` to `- Item-Dependencies:`, credited `g8na48` across `Concern`, `Scope`, `Deferred`, `E-14`, `Required tests / validation`, and `OQ-03`, and specified temporary-worktree regeneration of `.aw/state/dcerjg/check-before.jsonl` from `g8na48` `F-03` in `E-16` and `V-16` (strength: very strong). |
| PR-014 | MEDIUM | IN-SCOPE | Proofreading / R2 / R7 | `.aw/records/plans/pending/20261102-metastore-04-dcerjg-build-the-migration-chain-and-the-m0001-dry-run-with-census.ipd.md:24,40-52,58,126-144`; `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:83-85,786-805`; `.aw/records/plans/pending/20261107-metastore-14-g5hpbb-make-aw-migrate-metadata-migrate-any-repository-from-any-pri.ipd.md:36-48` | Five split-part `Carrier:` bullets were pasted inside a broken inline backtick span at lines 40-52 instead of `## Deferred / out of scope (with reason)`, `Scope`/`Deferred` omitted the `g5hpbb` (`C12`/`5.2a`/`AC-42`) and `830wku`/`clors0` carriers, and `E-12` lacked explicit `project_context.project_records_dir(repo)`, `"no sidecar (none expected)"`, and absent-template rules | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Repaired lines 40-52, moved all split-part `Carrier:` bullets into `Deferred` alongside `g5hpbb` and `clors0`, updated `Scope`, and specified `project_records_dir(repo)`, zero repo-specific constants, `"no sidecar (none expected)"`, and absent-template skipping in `E-12` and `V-12` (strength: strong). |
| PR-015 | LOW | IN-SCOPE | Proofreading | `.aw/records/plans/pending/20261102-metastore-04-dcerjg-build-the-migration-chain-and-the-m0001-dry-run-with-census.ipd.md:20,98,117-124,197,215` | Missing technical-writing header note and Requirement 12 Mermaid flowchart in `Proposed changes`, bare line-number citations (`"lines 14 to 15"`) in `F-09` and `OQ-04`, two `IPD-C802` em dashes in `Validation and cross-check`, and no Round 2 `HEAD` `0ea2db75d` re-measurement row | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added technical-writing header note, Mermaid `flowchart TD` diagram, `<!-- aw-prompt:` content anchors in `F-09`/`OQ-04`, `F-18` re-measurements at `0ea2db75d`, and parentheses replacing both em dashes (strength: strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-5 | Should `m0001_metadata_v2.run(..., apply=True)` execute `4sd62s` 5.2 step 7 by default (`commit: bool = True`) while exposing `commit=False` + `commit_staged` for staged-tree inspection? | Yes: default `commit=True` stamps `metadata_schema: 2`, stages the explicit path list (including in-tree `project.json`), writes `terminal_commit_marker`, commits via `git_commit_helper.offer_commit` (`RUNNER_AW_COMMIT`), and deletes the marker; `commit=False` leaves the staged index and marker intact for `E-15` step (c)/(d) inspection before `commit_staged` | Leave step-7 committing to manual callers only (breaks `aw migrate metadata --apply` in `1vfqdu` `E-02`, `g5hpbb` `E-07`, `clors0` `E-19`, and `cxxmyv` `E-10`); or omit `commit=False` (prevents `E-15` from running `aw sanitize --agent` and direct gate CLIs on the staged tree before commit) | `4sd62s` 5.2 steps 6-7, `1vfqdu` `E-02`, `g5hpbb` `E-07`, `clors0` `E-19`, `cxxmyv` `E-10`, and `dcerjg` `E-15`/`V-15` | yes |
| D-6 | When must `chain.write_metadata_schema(repo, 2)` run relative to `o19353` E-01's `terminal_commit_marker`? | Before staging the migration's explicit path list and computing `terminal_commit_marker`'s `git write-tree` id, with pre-apply `project.json` backed up in `journal_dir / "backups"` | Write `metadata_schema: 2` after the marker (either leaves `project.json` uncommitted or changes the staged index and invalidates `terminal_commit_marker`'s `git write-tree` match) | `4sd62s` 5.2 steps 4a, 6, and 7; `o19353` `E-01`; `commit_lock.commit_isolated` (`agent_workflows/commit_lock.py:383-415`) | yes |
| D-7 | How should `E-13` verify produced logs and mirrors before Phase B switches `artifact_meta._load_sources` away from legacy `.md`/`.review.md` loaders? | Replay each `meta/<id6>.jsonl` directly via `artifact_meta.replay(id6, art_type, lines, records_root=scratch_records_root)` (ensuring `"roadmap"` is in `SUPPORTED_TYPES`) and parse mirrors via `parse_artifact_mirror`, `parse_staged_prompt_mirror`, and `parse_review_mirror` | Call `artifact_meta.check_freshness` on the mixed scratch tree (walks in `os.walk` order and invokes Phase-B `load_legacy_artifact` and `load_legacy_review` `_parse_bullet_metadata` on templates, READMEs, and YAML-front-matter `.review.md` mirrors) | `agent_workflows/artifact_meta.py:57,967,2431,2923,3038` and `4sd62s` C9 / 5.2 step 6 | yes |
| D-8 | How should `E-16` / `V-16` compare `aw check --agent` against `.aw/state/dcerjg/check-before.jsonl` when `dcerjg` runs in an isolated worktree lane where `g8na48`'s gitignored `.aw/state/` is absent? | Regenerate `.aw/state/dcerjg/check-before.jsonl` from a temporary detached worktree under `tmp/` at the pre-edit `HEAD` SHA recorded in `g8na48` `F-03` (removing the temporary worktree immediately) | Require manual main-checkout state copying (violates lane isolation) or skip the baseline diff (weakens `V-16`) | `g8na48` `E-01` and `F-03` (`.aw/records/plans/pending/20261109-metastore-101-g8na48-build-the-migration-chain-the-metadata-schema-stamp-and-the.ipd.md:43,97`) | yes |

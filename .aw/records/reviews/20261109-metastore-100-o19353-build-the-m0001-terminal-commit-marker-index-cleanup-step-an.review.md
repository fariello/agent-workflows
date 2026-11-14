# Review findings: plan o19353

- Subject-Id: o19353
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `e8b9b9c11` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-100-o19353-build-the-m0001-terminal-commit-marker-index-cleanup-step-an.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `2` `IPD-C802` info advisories on line 92), the existing transition hook suites (`tests/test_executed_transition_gate.py` and `tests/test_executed_transition_gate_e2e.py`) passed (`19 passed in 3.85s`), and the release gate suite (`tests/test_check_engine_release_gate.py`) passed (`53 tests`). During revision, `o19353` was split in place from two under-specified items into four single-concern steps (`E-01`, `E-03`, `E-04`, and `E-02` paired 1:1 with `V-01`..`V-04`, advancing `- Highest E allocated:` from `02` to `04`), Pass 2 re-checked the complete revised plan against `4sd62s`, `vxevph`, `g8na48`, and `dcerjg`, and `aw ipd lint --phase review-finalize --agent` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern, Scope, Goal | Described marker and cleanup steps informally without specifying tree-id match semantics, project-context durable root resolution, or rollback cleanup | Specifies exact marker contract (`terminal_commit_marker.json` under `state_durable / "migrations" / "m0001"`, with payload `{"migration_id": "m0001", "tree_id": "<write_tree_sha>"}` and mirrored in `journal.json`), tree-id validation, and cleanup on commit and rollback | PR-001, PR-002. |
| Detailed Implementation Checklist (PIN-FIRST RULE, E-01..E-04) | Single `E-01` item bundling hook modifications, step 4a marker creation, and step 5 cleanup without `mkdir -p .aw/state/o19353` | Adds `mkdir -p .aw/state/o19353` and partitions the work into four right-sized steps (`E-01` hook marker acceptance in `executed_transition_gate.py` and `backlog_blocking_close_gate.py`, `E-03` step 5 cleanup in `m0001_metadata_v2.py`, `E-04` step 4a terminal marker write and cleanup in `m0001_metadata_v2.py`, and `E-02` test suite in `tests/test_m0001_gate_marker.py`), each within `<=8` units (`IPD-Z603`) | PR-001, PR-002, PR-004. |
| Project conventions discovered (Step 0) | Used unqualified `module.function` references and omitted hook signatures, git plumbing, and journal storage rules | Cites `path::Symbol` identifiers, documents hook `(int, List[str])` return signatures, `git write-tree` plumbing, `MigrationManager` journal directories, and `state_durable` resolution via `project_context.py` | Technical Writing Standard Requirement 7, PR-001, PR-006. |
| Findings (F-01..F-04) and Behavior decisions (D-1..D-4) | Omitted `## Behavior decisions` entirely and cited only `dcerjg` secondary findings | Adds `F-01`..`F-04` measured on `HEAD` and defines `D-1`..`D-4` covering marker tree-binding, marker lifecycle, step 5 cleanup scope/idempotence, and read-only hook safety | PR-001, PR-002, PR-004. |
| Proposed changes and Deferred / out of scope | Two-line list with no diagram and missing carrier entries | Four ordered steps with a Mermaid `flowchart TD` diagram and complete carrier attributions (`g8na48`, `vxevph`, `1vfqdu`, `dky26u`, `ghhzb6`, `hpedmn`, `dcerjg`, `9o83cr`, `cxxmyv`) | Technical Writing Standard Requirement 12(b), PR-005, PR-006. |
| Validation and cross-check (V-01..V-04) and Approval and execution gate | Two em dashes on line 92 (`IPD-C802`), bundled V-01 checking three files at once, V-02 lacking class-qualified pytest node IDs, and no unsafe-condition stop rule | Removes em dashes, pairs `V-01`..`V-04` 1:1 with `E-01`..`E-04`, specifies 14 exact class-qualified pytest node IDs in `V-02`, and adds a narrow unsafe-condition stop rule in `Approval and execution gate` | PR-003, PR-005, PR-006. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `o19353` adds positive migration marker acceptance to `agent_workflows/hooks/executed_transition_gate.py` and `agent_workflows/hooks/backlog_blocking_close_gate.py`, enabling the one-time metadata migration cutover commit to land without `--no-verify`.
2. Yes. Modifies repository pre-commit hooks to accept staged terminal plan transitions and release-blocking backlog closes, requiring strict tree-id matching (`git write-tree`), immediate deletion upon commit or rollback, and refusal of mismatched or stale markers.
3. Yes. Encompasses the pre-commit hook subsystem (`executed_transition_gate.py`, `backlog_blocking_close_gate.py`), migration engine (`m0001_metadata_v2.py`), and test infrastructure (`tests/test_m0001_gate_marker.py`).
4. Yes. Pre-commit hooks run on every developer and agent commit across the entire repository.
5. Yes. Step 5 permanently removes `plans/STATUS.md` and INDEX manifests, and removes gitignore lines from target repositories.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (Sections 4.5, 5.1, 5.2 steps 4a and 5, 5.2a, and AC-16); parent plan `dcerjg` (Order 04); prerequisite plans `tve77h` (Order 02), `g8na48` (Order 101), `vxevph` (Order 15), `1vfqdu` (Order 16), `dky26u` (Order 17), `ghhzb6` (Order 18), and `hpedmn` (Order 19); and production modules `agent_workflows/hooks/executed_transition_gate.py`, `agent_workflows/hooks/backlog_blocking_close_gate.py`, `agent_workflows/layout_migration.py`, `agent_workflows/project_context.py`, and `agent_workflows/project_schema.py`.
- Verified on `HEAD` (`e8b9b9c11`) that neither `executed_transition_gate.py` nor `backlog_blocking_close_gate.py` has migration marker acceptance (`PR-001`), that `STATUS.md` and 6 INDEX ignore lines exist in the target repository (`PR-001`), and that `vxevph` E-03 persists `"terminal_commit_marker"` in `journal.json` under `state_durable / "migrations" / "m0001"` (`PR-001`).

### Step R2

- Checked: `E-*`/`V-*` 1:1 bijection (`E-01` <-> `V-01`, `E-02` <-> `V-02`, `E-03` <-> `V-03`, `E-04` <-> `V-04`), `- Highest E allocated: 04`, acyclic dependency order (`E-01` and `E-03` independent; `E-04` depends on `E-01, E-03`; `E-02` depends on `E-01, E-03, E-04`), `- Scope-Paths:` completeness (`5` paths, every work path modified), PIN-FIRST directory creation (`mkdir -p .aw/state/o19353`), and test node IDs.
- Replaced vague prose test descriptions with 14 exact class-qualified pytest node IDs in `V-02` across four test classes (`TestExecutedTransitionGateMarker`, `TestBacklogBlockingCloseGateMarker`, `TestStep5Cleanup`, and `TestMarkerErrorHandling`) (`PR-003`).

### Step R3

- Checked: Path resolution security and hook isolation. Ensured that `executed_transition_gate.py` and `backlog_blocking_close_gate.py` resolve `state_durable` exclusively through `project_context.resolve_project_context(target_repo=str(repo_root))` checking `physical_classes["state_durable"]` and `logical_roots["state_durable"]`, avoiding hardcoded `.aw/state/` literals.
- Verified that the hooks execute only read operations (`git rev-parse`, `git write-tree`) and never write or alter git refs, index state, or working files (`D-4`). Confirmed that `--no-verify` is never permitted or suggested (`PR-001`, `PR-004`).

### Step R4

- Checked: Behavioral decisions and invariant preservation:
  1. `D-1`: Marker validation and tree-binding contract (`git write-tree` equality check; stderr warning on mismatch without crashing; fallback to standard enforcement).
  2. `D-2`: Marker lifecycle and cleanup (created only after staging complete path list in step 4a; unlinked immediately after commit in step 7 and inside `rollback`).
  3. `D-3`: Step 5 cleanup scope and idempotence (`plans/STATUS.md`, generated INDEX manifests, and gitignore lines removed cleanly and idempotently).
  4. `D-4`: Read-only hook safety (no working tree or index mutation).

### Step R5

- Checked: Architect (clean separation between hook acceptance and migration engine; robust durable state resolution via `project_context`), Security/Integrity Reviewer (fail-closed behavior on corrupted marker or unmerged index; exact tree SHA binding preventing piggybacked edits; immediate cleanup on commit/rollback), QA/QC Engineer (14 exact class-qualified test node IDs across four test classes in `tests/test_m0001_gate_marker.py`; PIN-FIRST regression coverage for both existing hooks), Software Engineer (defensive JSON loading; no crashes on missing directories; `m0001_metadata_v2.rollback` restoring deleted files byte-for-byte), and Modest Executor (four single-concern steps, each `<=8` units with zero `IPD-Z603` advisories).

### Step R6

- Checked: `4` `E-*` items across `5` `- Scope-Paths:` entries (`4` work paths plus the plan file; `- Size assessment: standard`), satisfying `nj8zdp` and `IPD-Z603` bounds (`<=5` E-items, `<=8` work Scope-Paths, `0` advisories).

### Step R7

- Checked: `- Item-Dependencies: executed:tve77h, executed:g8na48, executed:vxevph, executed:1vfqdu, executed:dky26u, executed:ghhzb6, executed:hpedmn` (`tve77h` verified executed; `g8na48`, `vxevph`, `1vfqdu`, `dky26u`, `ghhzb6`, `hpedmn` verified in `metastore`), parent `dcerjg` (Order 04), downstream phase C plan `9o83cr` (Order 11), and cutover plan `cxxmyv` (Order 13).

### Step S5

- Checked: zero open questions in the plan and four technical decisions surfaced during review (`D-1`..`D-4` in `### Decisions` below, all `Reversible: yes`).
- Resolved all four from repository code, `layout_migration.py`, `project_context.py`, and approved spec `4sd62s`. Zero questions belong to the human under the `askme` three-way sort.

### Pass 2

- Re-reviewed the complete revised plan per `steps/s6-rereview.md` rules 1 and 2 because `E-03`/`V-03` and `E-04`/`V-04` were partitioned from `E-01` (advancing `- Highest E allocated:` from `02` to `04`) and `E-01` was updated with defensive error handling.
- Verified `E-01..E-04` <-> `V-01..V-04` 1:1 bijection, `- Highest E allocated: 04`, acyclic dependency order (`E-01, E-03` -> `E-04` -> `E-02`), `- Scope-Paths:` (`5` files, every one modified), compliance with all 12 requirements of `.aw/system/workflows/technical-writing/technical-writing.md`, and `aw ipd lint --phase review-finalize --agent` (`outcome: clean`, `findings: 0`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | R1 / R3 / R4 / Scope, E-01, F-01, F-03, D-1, D-2 | `.aw/records/plans/pending/20261109-metastore-100-o19353-build-the-m0001-terminal-commit-marker-index-cleanup-step-an.ipd.md:37`, `agent_workflows/hooks/executed_transition_gate.py:347`, `agent_workflows/hooks/backlog_blocking_close_gate.py:40`, `agent_workflows/project_schema.py:808` | `o19353` E-01 left the marker location, filename, and payload format unspecified ("resolved from project_context.resolve_project_context(repo).logical_roots state_durable"). On `HEAD`, `ProjectContext.physical_classes` holds `state_durable` while `vxevph` E-03 defines `journal_dir = state_durable / "migrations" / "m0001"` with `journal.json` holding `"terminal_commit_marker"`. Ambiguity in marker location or schema would cause hook lookups to fail or raise KeyError on `logical_roots["state_durable"]`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Defined exact marker contract (`terminal_commit_marker.json` under `state_durable / "migrations" / "m0001"` with payload `{"migration_id": "m0001", "tree_id": "<write_tree_sha>"}` and mirrored in `journal.json`), specified robust `state_durable` resolution via `project_context.py` checking both `physical_classes` and `logical_roots`, and defined exact tree comparison logic (`D-1`, `D-2`). |
| PR-002 | HIGH | IN-SCOPE | R2 / R6 / E-01, E-03, E-04, D-1..D-4 | `.aw/records/plans/pending/20261109-metastore-100-o19353-build-the-m0001-terminal-commit-marker-index-cleanup-step-an.ipd.md:37`, `.aw/records/plans/pending/20261109-metastore-100-o19353-build-the-m0001-terminal-commit-marker-index-cleanup-step-an.ipd.md:63` | `o19353` bundled hook modifications across two separate hook modules, migration step 4a, and migration step 5 into a single `E-01` item, violating `IPD-Z603` single-concern right-sizing guidelines. Furthermore, `o19353` omitted a `## Behavior decisions` section defining marker validation/lifecycle contracts (`D-1`..`D-4`), and omitted `m0001_metadata_v2.rollback` cleanup of the marker. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Partitioned the work into four right-sized steps (`E-01` hook marker acceptance, `E-03` step 5 cleanup, `E-04` step 4a marker write and lifecycle, and `E-02` test suite), advanced `- Highest E allocated:` to `04`, added `V-03` and `V-04`, and documented `D-1`..`D-4`. |
| PR-003 | MEDIUM | IN-SCOPE | R2 / R4 / E-02, V-02 | `.aw/records/plans/pending/20261109-metastore-100-o19353-build-the-m0001-terminal-commit-marker-index-cleanup-step-an.ipd.md:44`, `.aw/records/plans/pending/20261109-metastore-100-o19353-build-the-m0001-terminal-commit-marker-index-cleanup-step-an.ipd.md:99` | `V-02` provided vague prose descriptions for test cases ("for each of the two hooks, one test per E-01 case... plus one step-5 test") without exact class-qualified pytest node IDs, omitted testing error handling when `git write-tree` fails on an unmerged index, and omitted testing step 5 cleanup idempotence when files or gitignore lines are already absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Defined explicit test classes and methods in `tests/test_m0001_gate_marker.py` (`TestExecutedTransitionGateMarker`, `TestBacklogBlockingCloseGateMarker`, `TestStep5Cleanup`, `TestMarkerErrorHandling`), specified 14 concrete class-qualified pytest node IDs in `V-02`, and verified error handling for unmerged index and corrupt marker payloads. |
| PR-004 | MEDIUM | IN-SCOPE | R3 / R4 / E-01, D-1, D-4 | `agent_workflows/hooks/executed_transition_gate.py:422`, `agent_workflows/hooks/backlog_blocking_close_gate.py:77` | `E-01` stated that a marker whose tree id mismatches is reported on stderr, but did not specify: (a) formatting stderr warnings so structured `--agent` and `--json` outputs are not corrupted; (b) handling corrupt/malformed marker JSON safely without crashing the hook; (c) ensuring `git write-tree` failure falls through to standard hook refusals; and (d) ensuring both hooks fail closed if the marker specifies an unrecognized `migration_id`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified defensive handling in both hooks: catch `(OSError, ValueError, subprocess.SubprocessError)` when reading marker or running `git write-tree`, emit warning to `sys.stderr` only when not in `--agent`/`--json` mode, verify `migration_id == "m0001"`, and fall through to standard gate logic on any mismatch or corruption (`D-1`, `D-4`). |
| PR-005 | LOW | IN-SCOPE | R7 / S7 / Deferred, Approval and execution gate | `.aw/records/plans/pending/20261109-metastore-100-o19353-build-the-m0001-terminal-commit-marker-index-cleanup-step-an.ipd.md:70`, `.aw/records/plans/pending/20261109-metastore-100-o19353-build-the-m0001-terminal-commit-marker-index-cleanup-step-an.ipd.md:108` | `Deferred / out of scope` omitted carrier attributions for `g8na48`, `vxevph`, `1vfqdu`, `dky26u`, `ghhzb6`, `hpedmn`, `9o83cr`, and `cxxmyv`, and `Approval and execution gate` omitted an explicit stop directive if prerequisite symbols from `vxevph` (`agent_workflows/migrations/m0001_metadata_v2.py`) are absent on `HEAD`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added complete carrier entries in `Deferred / out of scope` and added a narrow unsafe-condition stop rule in `Approval and execution gate` while keeping `- Scope-Paths:` declaration-only. |
| PR-006 | LOW | IN-SCOPE | Proofreading / Step 0, Proposed changes, Validation | `.aw/records/plans/pending/20261109-metastore-100-o19353-build-the-m0001-terminal-commit-marker-index-cleanup-step-an.ipd.md:53`, `.aw/records/plans/pending/20261109-metastore-100-o19353-build-the-m0001-terminal-commit-marker-index-cleanup-step-an.ipd.md:65`, `.aw/records/plans/pending/20261109-metastore-100-o19353-build-the-m0001-terminal-commit-marker-index-cleanup-step-an.ipd.md:92` | Line 92 carried two em dashes (`IPD-C802`), `Proposed changes` lacked the Mermaid diagram required by Technical Writing Standard Requirement 12(b), and `Step 0` cited code with unqualified `module.function` symbols instead of repo-relative `path::Symbol` identifiers. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced em dashes with parentheses, added a Mermaid `flowchart TD` dependency diagram in `Proposed changes`, and qualified code citations with repo-relative paths in `Step 0` and prose. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `executed_transition_gate.py` and `backlog_blocking_close_gate.py` locate, parse, and validate the migration positive marker? | Resolve `state_durable` via `project_context.resolve_project_context(target_repo=str(repo_root))`, check for `state_durable / "migrations" / "m0001" / "terminal_commit_marker.json"` (or `journal.json`), verify `migration_id == "m0001"`, and compare `tree_id` against current staged `git write-tree`. If matching, pass (`0, []`); if mismatched, emit warning to `sys.stderr` and fall through to standard gate logic; on corrupt JSON or missing marker, fall through silently. | Pass `--no-verify` (strictly forbidden by spec 5.2 step 4a and AC-16); hardcode `.aw/state/durable/migrations/m0001` (breaks external companion/home state roots and unconfigured test fixtures). | `agent_workflows/project_context.py:2006`, `4sd62s` Sections 5.1 and 5.2 step 4a | yes |
| D-2 | What is the exact lifecycle of the terminal-commit marker in `agent_workflows/migrations/m0001_metadata_v2.py`? | Write the marker in step 4a only after staging all converted files (`git add`) and capturing `git write-tree`. Unlink `terminal_commit_marker.json` and clear `journal.json["terminal_commit_marker"]` immediately after step 7 commit succeeds, AND inside `m0001_metadata_v2.rollback(repo)`. | Leave marker on disk indefinitely (allows stale marker to authorize subsequent illegitimate commits); delete marker during pre-commit hook (violates read-only hook requirement and breaks multi-hook validation). | `4sd62s` Section 5.2 step 4a and step 7, `.aw/records/plans/pending/20261107-metastore-15-vxevph-build-the-migration-chain-metadata-schema-stamp-m0001-prefli.ipd.md:56` | yes |
| D-3 | What files and configurations does step 5 clean up, and how is rollback handled? | Delete `plans/STATUS.md` under `records_root / "plans"`, delete all six `INDEX.json`/`INDEX.md` manifests under `plans/`, `research/`, `prompts/`, and remove the anchored `records/*/INDEX.*` ignore lines from the target repository's `.aw/.gitignore` (or `.agents/.gitignore`). Save pre-cleanup backups under `journal_dir / "backups"` so `rollback(repo)` restores them byte-for-byte; operate idempotently if files are already absent. | Retain `STATUS.md` and INDEX manifests (violates spec 5.2 step 5); edit toolkit source-code templates in `engine.py` or `placement_switch.py` (owned by Order 11 `9o83cr` and Order 13 `cxxmyv`). | `4sd62s` Section 5.2 step 5, `dcerjg` F-14 and Deferred | yes |
| D-4 | May `executed_transition_gate.py` or `backlog_blocking_close_gate.py` modify git refs, working tree files, or journal state when inspecting the marker? | No. The hooks are strictly read-only: `git write-tree` writes tree objects to the object database corresponding to the staged index without altering refs or working files. Hooks never touch or delete the marker. | Have the first hook unlink the marker (breaks the second hook when both hooks run in sequence). | `agent_workflows/hooks/executed_transition_gate.py:24`, `agent_workflows/typecheck_gate.py:312`, `4sd62s` Section 5.2 step 4a | yes |

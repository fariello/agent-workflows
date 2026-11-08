# IPD: Build the migration chain, metadata_schema stamp, m0001 preflight, migration journal and sidecar import

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` makes the cutover one scripted migration (5.1, 5.2), and none of it exists: `agent_workflows/migrations/` does not exist (`ls agent_workflows/migrations` fails), and `project_schema.parse_portable_policy` knows no `metadata_schema` key. Plan `dcerjg` owned this work in single items whose hidden work was too large for one agent turn, so it was split 2026-11-07 per the maintainer's step-complexity rule. This part is the foundation every other `m0001` part builds on.
- Scope: Add the numbered migration chain (`agent_workflows/migrations/__init__.py`, `chain.py`), the `metadata_schema` stamp in the resolved `project.json` and its round trip through `project_schema` and `install_wizard`, the `require_current_schema` hook in `artifact_meta`'s read path (`dcerjg` E-01); the step-1 preflight and `--force`/`--force-worktree` (`dcerjg` E-04); the migration journal on the `layout_migration.MigrationManager` components (`dcerjg` E-05); and the step-2 sidecar import and orphan export (`dcerjg` E-06); plus the tests for those four items (a subset of `dcerjg` E-14). Everything runs only on test fixtures. EXCLUDES: the `aw migrate` CLI group and the install prompt (`1vfqdu`); renames and citations (`dky26u`); conversion (`ghhzb6`, `hpedmn`); census, round trip, clone proof and changelog (`dcerjg`); descriptions (`odeo9z`, `ya4ee4`).
- Scope-Paths: agent_workflows/migrations/__init__.py, agent_workflows/migrations/chain.py, agent_workflows/migrations/m0001_metadata_v2.py, agent_workflows/migrations/m0001_preflight.py, agent_workflows/artifact_meta.py, agent_workflows/project_schema.py, agent_workflows/install_wizard.py, tests/test_migrations_chain.py, tests/test_m0001_preflight.py, tests/test_m0001_sidecar.py, .aw/records/plans/pending/20261107-metastore-15-vxevph-build-the-migration-chain-metadata-schema-stamp-m0001-prefli.ipd.md
- Item-Dependencies: executed:tve77h
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 15
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: vxevph

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from dcerjg per maintainer step-complexity rule (no single E/V item hides hundreds of steps).
- 2026-11-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The migration chain, the schema stamp, the preflight, the journal and the sidecar import exist and are proven on fixtures, so every later `m0001` part only adds steps to a journaled, preflighted run.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the migration chain and the stamp

- [ ] E-01 Before any edit, save `aw check --agent` output to `.aw/state/dcerjg/check-before.jsonl` (the V-16 baseline). Create `agent_workflows/migrations/__init__.py` and `agent_workflows/migrations/chain.py`: a `Migration` record (`number`, `name`, `target_schema`, `is_pending(repo) -> bool`, `run(repo, *, apply, force, force_worktree, describer=None)`), an ordered `MIGRATIONS` tuple holding `m0001` (`metadata-v2`, target 2), the constant `CURRENT_METADATA_SCHEMA = 1` (Order 13 flips it to 2 in the cutover commit), `read_metadata_schema(repo)` and `write_metadata_schema(repo, value)` against the `project_context.resolve_project_context` `config_project` path (never a hard-coded `.aw/config/project.json`), `repo_has_legacy_records(repo)` (any record with a `- Field:` bullet block before the first `##` or a `## Workflow history` section, READMEs excluded), and `require_current_schema(repo)` that raises with the exact text "run `aw migrate metadata`" when the stamp, or 1 when absent on a repository with legacy records, is below `CURRENT_METADATA_SCHEMA`. Call it from `artifact_meta`'s one cache-refresh entry point (the freshness check that every public read runs first, `tve77h` E-13), so every metadata-reading command reaches it through the one interface (5.3, C5) and no command needs its own call; `aw migrate`, `aw install`, `aw setup`, `aw doctor` and `aw --help` do not read metadata through `artifact_meta` and so never refuse. This is a one-line hook in `artifact_meta.py`, which is in Scope-Paths. Make `metadata_schema` a documented member of the portable policy: add it to `known_keys` in `project_schema.parse_portable_policy` AND to the fallback `known_proj_keys` set in `install_wizard` (the copy used when `parse_portable_policy` raises), add an optional `metadata_schema: Optional[int]` field to `project_schema.ProjectPolicySchema` that `to_dict` writes when set, and carry the parsed value through the `ProjectPolicySchema(...)` rebuild in `install_wizard`, so a reinstall never drops the stamp. Moving the key from `unknown_fields` to a field without these three edits would silently delete it on the next `aw install`, because `install_wizard` rebuilds `project.json` from named fields plus `unknown_fields`. `write_metadata_schema` writes the file atomically (temporary file plus `os.replace`, as `config.stamp_cutovers` and `install_wizard` do), keeps every other key and its value, and keeps the trailing newline (`tests/test_install_config_trailing_newline.py`). `parse_local_binding` is not changed: the stamp lives only in the portable `project.json`.
  - Depends on: none
  - Expected outcome: in a tmp repository, `write_metadata_schema(repo, 2)` adds `"metadata_schema": 2` to the resolved `project.json` and leaves `schema_version` and every other key unchanged; a following `aw install` into the same repository keeps `"metadata_schema": 2`; `require_current_schema` raises the named message when `CURRENT_METADATA_SCHEMA` is 2 and the stamp is absent on a legacy fixture, and returns silently under the shipped value 1, so no command in this repository refuses before the cutover; with `chain.CURRENT_METADATA_SCHEMA` monkeypatched to 2, `artifact_meta.read(<id6>)` on a legacy fixture raises naming `aw migrate metadata` (AC-11 case 1 at the interface; in phase A no CLI command reads through `artifact_meta` yet, so the CLI-level refusal is demonstrated by `cxxmyv` after Orders 08 and 09 have moved the readers).
  - Execution state: pending

### Task group 2: preflight, journal and sidecar

- [ ] E-02 Create `agent_workflows/migrations/m0001_preflight.py` implementing 5.2 step 1 in this order: (1) WORKTREE: refuse when the absolute `git rev-parse --path-format=absolute --git-dir` differs from `ipd_lifecycle.checkout_git_common_dir(repo)` (in this review lane they are `.git/worktrees/<name>` and `.git`), naming `--force-worktree`; `--force` never overrides it, and `None` from `checkout_git_common_dir` refuses as "cannot establish the common directory". (2) UNCOMMITTED: `git status --porcelain -- <records root>` non-empty. (3) LOCK: `platform_lock.probe_free(runner_shared.integration_lock_path(repo))` is False; `None` (unanswerable) is reported as its own condition and refuses like False, because `probe_free` documents that `None` is not proof the lock is free. (4) LANES: each linked worktree from `git worktree list --porcelain` whose branch changes a path under the plans tree and for which `runner_shared.lane_work_has_landed` is not True, listed by worktree, with `None` shown as "unknown" rather than dropped. Each condition refuses and is named; `--force` continues past (2) to (4) and the report names each overridden condition and its 5.2 consequence; refusals write nothing (no journal, no scratch). When the lock is free, the apply holds `runner_shared.integration_lock(repo, holder_label="aw migrate metadata")` for its whole duration.
  - Depends on: E-01
  - Expected outcome: every AC-27 case and AC-22 case (1) hold in tmp repositories; the tmp tree is byte-identical after each refusal.
  - Execution state: pending

- [ ] E-03 In `agent_workflows/migrations/m0001_metadata_v2.py`, build the migration journal on the `layout_migration.MigrationManager` components (reuse its writer lock, atomic journal save and load, and its resume and rollback model; do not write new ones) at a per-migration path under the resolved `state_durable` root (`migrations/m0001/journal.json`), never the shared `migration_transaction.json`. The journal records: the minted `id6` per legacy path (so every dry run and the apply mint the same value), the old-to-new rename map, per-step progress, the description-seam results, the orphan export path, and the terminal-exception marker (E-11). Dry run is the default; the scratch copy (records root plus the citation scan roots) lives under the same gitignored directory; `--apply` applies the verified scratch result to the checkout with per-file backups, and an interrupted apply resumes or rolls back from the journal, never restarts.
  - Depends on: E-02
  - Expected outcome: a fault injected between two applied files leaves a journal from which `aw migrate metadata --apply` resumes to the same final tree as an uninterrupted run, and a rollback restores the pre-apply bytes exactly; a dry run writes only under the gitignored journal directory.
  - Execution state: pending

- [ ] E-04 Implement step 2 (sidecar first) in `m0001_metadata_v2.py`: read `.aw/records/history.jsonl` before any other step; the sidecar is EXPECTED when the records tree has at least one spec or backlog item with an `id6`; the preflight line reports presence and record count; a missing expected sidecar refuses unless `--force` (the only non-step-1 refusal `--force` overrides). Classify each record by whether its `id6` resolves to a tracked record (filename `id6` or in-file `- Id:`): resolvable records are queued, in sidecar file order and unchanged, for `legacy` events with `source: sidecar` and `observed_day` from `date`; unresolvable ones are written to a gitignored `sidecar-orphans.jsonl` export beside the journal, counted per `id6` in the census, and get no log. Rename and group records stay `legacy`. On apply, move the sidecar file into the export directory and remove the `records/history.jsonl` line from the TARGET repository's `.aw/.gitignore`.
  - Depends on: E-03
  - Expected outcome: AC-30 case (1) and the `.aw/.gitignore` part of case (2) hold on a fixture; a lane-style worktree with `--force-worktree` and no sidecar refuses naming the sidecar.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add the test modules for E-01 to E-04, moved here from `dcerjg` E-14 (subset: the stamp-and-schema half of `tests/test_migrations_chain.py`, all of `tests/test_m0001_preflight.py`, and the sidecar cases, which `dcerjg` E-14 had placed in `tests/test_m0001_conversion.py` and which move to a new `tests/test_m0001_sidecar.py` so that each part owns its own module), all on `tmp_path` fixture repositories built with real `git init`, calling the real functions and asserting on outputs, exit codes and file bytes (no source reading): `tests/test_migrations_chain.py` (E-01, AC-11 case 1 at the interface with `CURRENT_METADATA_SCHEMA` patched to 2, and the project-schema test that a reinstall keeps the stamp, PR-001); `tests/test_m0001_preflight.py` (AC-27 cases 1 to 4, AC-22 case 1, journal resume and rollback); `tests/test_m0001_sidecar.py` (AC-30 case 1 and the `.aw/.gitignore` part of case 2). Mark each `core`; any module whose slowest test exceeds 2 s in `--durations=10` is marked `slow` instead and named in V-05.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: the three modules pass under `python3 -m pytest -o addopts="" -n auto <modules>`, and the bare core gate stays inside its 30 s budget.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Transactional migrations reuse `layout_migration.MigrationManager` (`_acquire_lock`, `_save_transaction`, `_load_transaction`, `resume_migration`, `rollback_migration`); spec 5.1 forbids new journal or lock components (carried from `dcerjg` Step 0).
- Path roots come from `project_context.resolve_project_context` (`config_project`, `state_durable`, `records`), never `<repo>/.aw/...` literals (spec 4.5, 5.1).
- Tests exercise code and assert on outputs (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); new modules set `pytestmark = pytest.mark.core` unless the `--durations=10` rule of `dcerjg` E-14 moves one to `slow`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by a line number alone (advisory `IPD-C801`).
- The integration lock is `runner_shared.integration_lock_path` and `runner_shared.integration_lock` (bounded, loud wait); a non-mutating probe is `platform_lock.probe_free`. Worktree identity is `ipd_lifecycle.checkout_git_common_dir`. Lane landing is `runner_shared.lane_work_has_landed` (True/False/None, None kept visible as unknown) (carried from `dcerjg` Step 0).

## Findings

| Id | Evidence (measured 2026-11-07 in this worktree) | Finding |
|---|---|---|
| F-01 | `ls agent_workflows/migrations`: "No such file or directory" | The chain, journal and preflight are unbuilt; the hidden work is counted as deliverables. |
| F-02 | `rg -n "known_keys\|known_proj_keys\|ProjectPolicySchema\(" agent_workflows/project_schema.py agent_workflows/install_wizard.py`: 8 hits (two `known_keys` sets in `project_schema`, the `install_wizard` fallback `known_proj_keys`, one `ProjectPolicySchema` class) | Stamp item (E-01, which also saves the `.aw/state/dcerjg/check-before.jsonl` baseline that `dcerjg` E-16 compares against, because this part runs first): files `chain.py`, `__init__.py`, `project_schema.py`, `install_wizard.py`, `artifact_meta.py` (one hook), 6 functions (`read_metadata_schema`, `write_metadata_schema`, `repo_has_legacy_records`, `require_current_schema`, `Migration`, `MIGRATIONS`), 3 schema edits: about 14 units. |
| F-03 | `rg -n "def (checkout_git_common_dir\|probe_free\|integration_lock_path\|integration_lock\|lane_work_has_landed)\b" agent_workflows`: all 5 exist | Preflight item (E-02): 4 conditions, 2 flags, 1 lock hold, 1 file: about 8 units. |
| F-04 | `rg -n "def (_acquire_lock\|_save_transaction\|_load_transaction\|resume_migration\|rollback_migration)" agent_workflows/layout_migration.py`: 5 | Journal item (E-03): reuse 5 components, 1 new path, 6 journal sections, dry-run scratch, backup apply: about 12 units. |
| F-05 | `ls .aw/records/history.jsonl`: absent in this worktree; `rg -c "records/history.jsonl" .aw/.gitignore`: 1 | Sidecar item (E-04): read, expected-ness rule, classify, orphan export, apply move, 1 ignore-line removal: about 6 units; a fixture sidecar is required. |
| F-06 | the original `dcerjg` E-14 named 7 test modules in one item | Split by the item they test: this part takes 2 of them plus a new `tests/test_m0001_sidecar.py` (the sidecar cases had been inside `test_m0001_conversion.py`). |

## Proposed changes (ordered, validatable)

1. E-01: baseline, chain, stamp, read-path hook.
2. E-02 to E-04: preflight, journal, sidecar.
3. E-05: tests.

## Deferred / out of scope (with reason)

- The `aw migrate` command group, bare `aw migrate`, and the install pending-migration prompt.
  - Carrier: 1vfqdu
- Every later `m0001` step, the census, the round trip, the clone proof, the changelog, and the `dcerjg` E-16 gates.
  - Carrier: dcerjg
- The description journal and model call.
  - Carrier: ya4ee4

## Scope check

- Over-scope: none. The `artifact_meta.py` edit is the one `require_current_schema` call in the read path.
- Under-scope: none for `dcerjg` E-01, E-04, E-05 and E-06 and their tests; AC-11 case 1 (interface form), AC-22 case 1, AC-27 cases 1 to 4 and AC-30 case 1 are proven here.

## Required tests / validation

New modules (all `core` unless E-05's duration rule moves one to `slow`): `tests/test_migrations_chain.py`, `tests/test_m0001_preflight.py`, `tests/test_m0001_sidecar.py`. Existing: `tests/test_install_config_trailing_newline.py`, `tests/test_layout_migration.py`. Gate: bare `python3 -m pytest`.

## Spec / documentation sync

No spec change; implements `4sd62s` 5.1 (chain, stamp) and 5.2 steps 1 and 2. The CHANGELOG line is written once by `dcerjg` E-16 for the whole family.

## Open questions

### OQ-03: How can `metadata_schema` and the AC-11 refusal ship in phase A without refusing this unmigrated repository?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Carried from `dcerjg` OQ-03 (resolved there): `require_current_schema` compares against `CURRENT_METADATA_SCHEMA`, which is 1 (the legacy format) and an absent stamp counts as 1, so nothing refuses before the cutover; Order 13 sets the constant to 2 in the cutover commit. Tests patch the constant to 2 to prove the behavior now.

- Note: carried unchanged from `dcerjg` with its id, so item text that cites it still resolves.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_migrations_chain.py -k "stamp or schema"` with every selected test PASSED, including a test asserting the resolved `project.json` gains `"metadata_schema": 2` with `schema_version` unchanged and a test asserting the exact refusal text "run `aw migrate metadata`" under a patched `CURRENT_METADATA_SCHEMA = 2`; the `git diff` hunks adding `metadata_schema` in `project_schema.py` and `install_wizard.py`; the PASSED test showing `aw install` into a stamped repository keeps `"metadata_schema": 2`; and the PASSED test showing `artifact_meta.read` on a legacy fixture with the constant monkeypatched to 2 raises naming `aw migrate metadata`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_preflight.py -k "preflight or worktree or sidecar_missing"` with one PASSED test per AC-27 case 1 (three conditions, refused and then forced, output naming the overridden condition), 2, 3, 4 and AC-22 case 1; each refusal test asserts a byte-identical tree.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_preflight.py -k "journal or resume or rollback"` all PASSED; and `ls -R` of the journal directory after one fixture dry run, showing files only under the gitignored `state/durable/migrations/m0001/` path.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_sidecar.py -k sidecar` all PASSED (status record, repeated inline line kept twice with distinct `source`, rename record kept as `legacy`, orphan `id6` in the export with no log, target `.aw/.gitignore` without the `records/history.jsonl` line). (The clone preflight line naming the sidecar record count moved to `dcerjg` V-15, because the clone proof runs after every part.)
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -n auto tests/test_migrations_chain.py tests/test_m0001_preflight.py tests/test_m0001_sidecar.py --durations=10` summary with 0 failed and the durations table, naming any module marked `slow`; and the bare `python3 -m pytest` summary line inside the 30 s budget.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. All open questions are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Safety: this plan NEVER runs `aw migrate metadata --apply` (or bare `aw migrate --apply`) in this checkout. Every apply is on a `tmp_path` fixture repository. If an apply would touch this checkout's records, stop and report: that is a genuinely unsafe condition, not a scope question.

Honesty rule: run the named test modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit vxevph -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize vxevph` itself.

# IPD: Migration must move-not-copy legacy artifacts (git mv/mv) with interactive leftover disposition

- Date: 2026-08-16
- Kind: child
- Concern: The shipped layout-migration tool (`aw migrate-layout apply` -> `MigrationManager.execute_migration`) COPIES every classified legacy artifact into `.aw/` (`layout_migration.py:478` `shutil.copy2`) and leaves the source in place ("copy-verify-switch-retain"). It only switches WRITE authority (records_backend -> repository, so `record_producers`/`storage` resolve `.aw/records/`), but the source is never moved and never untracked, and the READ tooling (`artifact_core.SCAN_ROOTS`, `aw attention`/`plans`/`backlog`) walks BOTH `.agents/*` and `.aw/records/*` on the filesystem. The result in EVERY migrated repo is two live, tracked, equally-scanned copies of every record: `aw attention` reports `valid: False` with a duplicate-id per pair. That is a duplicate installation, not a migration. There is also no handling of legacy material that was NOT classified/moved.
- Scope: `agent_workflows/layout_migration.py` `MigrationManager` (the copy phase in `execute_migration`, the `rollback_migration` reverse logic, the retention manifest semantics, and a new interactive leftover-disposition step) and its `migrate-layout` CLI surface in `agent_workflows/cli.py`; the awphysical migration tests in `tests/test_layout_migration.py`, `tests/test_acceptance_matrix.py`, and `tools/awphysical/test_awphysical_tools.py`. Does NOT change the inventory classifier dispositions, the resolver/packaging (xzuxet), or the workflow bodies.
- Status: reviewed
- Set: awphysical
- Order: 14
- Highest E allocated: 06
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: hnzr8v

## Workflow history

- 2026-08-16 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created after the Order-11 self-migration attempt (copy-based cutover, committed then rolled back) surfaced that the shipped migration tool copies-and-retains instead of moving, leaving every migrated repo in a duplicate-installation half-state (writers on `.aw/`, readers on both trees, `aw attention valid:False`). Maintainer ruling (chat): the migration should MOVE (git mv for tracked, mv for untracked); `aw attention` should keep walking legacy locations (near-zero cost, finds nothing post-move); and when migration finishes the tool should INTERACTIVELY ask what to do with anything not moved. Copy-then-delete is acceptable only if it buys rollback, but a move plus the transaction journal already gives reversibility.
- 2026-08-16 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS. Structural lint conforming at author + review-finalize. Findings applied in place: PR-001 (HIGH, UNDER-SCOPE) added E-06 - move breaks the pre-existing `resume_migration` re-run-from-scratch path (data-unsafe under move); now per-item-checkpointed, journal-driven resume/rollback so any crash resolves to fully-migrated or fully-legacy. PR-002 (MEDIUM) E-02 anchored to `inv_item.get("git_state")` (map item lacks it). PR-003 (MEDIUM) E-02 handles the `deduplicate_identical` collision (move first, remove twin, reversible) and verifies the DESTINATION hash post-move. PR-004 (MEDIUM) E-03/rollback reverses the incremental journal (move + dedup-remove) and is partial-state safe. E-05 test list extended to assert crash-recovery + dedupe. One OPEN question (OQ-01: formal spec revision vs. in-IPD reconciliation) - a human decision; NO-GO pending OQ-01 + human approval.

## Goal

Make `aw migrate-layout apply` a real MOVE, not a copy: each classified legacy artifact is relocated into `.aw/` (git-tracked items via `git mv` to preserve history and stage the rename; untracked items via a filesystem move), so no legacy twin remains and a migrated repo has exactly ONE logical records/system tree. Rollback reverses the moves. After moving all classified items, the tool interactively asks the operator what to do with any legacy material left behind (keep / remove / defer), with a non-interactive flag for CI. The read tooling (`aw attention`/`plans`/`backlog`) continues to scan legacy locations unchanged; post-move they are empty of records, so the duplicate-id half-state cannot arise.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Move instead of copy

- [ ] E-02 In `MigrationManager.execute_migration` (agent_workflows/layout_migration.py, the copy phase around :470-495), replace `shutil.copy2(src_p, dst_p)` with a MOVE that honors git tracking. The tracked/untracked signal is `inv_item.get("git_state")` from the JOINED inventory item (`inv_item = inv_item_map.get(item_id)` at :452), NOT the map item (map items carry `copy_method`, not `git_state`). When `git_state == "tracked"` and the repo is a git work tree, `git mv -- <src> <dst>` (creating dst parents first; on `git mv` failure fall back to `os.rename` + `git rm --cached <src>` + `git add <dst>` so the index still records the rename); when untracked, `shutil.move`/`os.rename` on the filesystem. Preserve the existing symlink handling and the host-adapter-in-place skip (never moved). Handle the existing `deduplicate_identical` collision case (build_migration_map may map two identical-hash sources to ONE destination): the FIRST is moved; a subsequent identical source cannot be moved onto the already-moved destination, so it is removed (tracked: `git rm`; untracked: unlink) as a de-duplicated twin, recorded as such. Because the source is gone after the move, the byte-identical verification MUST hash the DESTINATION (not the source) and still equal the inventory `sha256`, else fail the transaction. Record each performed relocation as `{source, destination, hash, was_tracked, action: move|dedup-remove}` in the transaction journal so rollback can reverse it.
  - Depends on: none
  - Expected outcome: after a real apply, each classified legacy path no longer exists at its old location and exists once under `.aw/`; tracked items show as a git rename (R) in `git status`; identical-hash duplicates collapse to one destination with the twin recorded; the transaction journal records reversible relocations.
  - Execution state: pending

- [ ] E-06 Make the move phase crash-recoverable and `resume_migration` move-aware (agent_workflows/layout_migration.py:657-717). Today the copy loop only checkpoints `staged` AFTER the whole loop, so a crash mid-loop leaves checkpoint `locked`, and `resume_migration` (:670-676) RE-RUNS `execute_migration` from the beginning. Under COPY that was roughly idempotent; under MOVE it is BROKEN and data-unsafe: already-moved sources are gone, so a fresh inventory no longer sees them and the partial move is neither completed nor reversed. Fix: persist each performed relocation to the transaction journal INCREMENTALLY (per item, before the next), and make the move phase idempotent on re-entry - for each planned item, if the destination already exists with the expected hash and the source is gone, treat it as already-moved and skip; otherwise perform the move. `resume_migration` from a mid-move interruption MUST continue the remaining moves using the ORIGINAL transaction's item list (not a fresh inventory that would miss moved sources), then proceed to switch/retain/complete. A crash at any point must be resolvable to either fully-migrated (resume) or fully-legacy (rollback), never a torn state.
  - Depends on: E-02
  - Expected outcome: killing the process mid-move then running `aw migrate-layout resume` completes the migration with every source moved exactly once; running `rollback` instead restores every source; no item is left half-moved or duplicated.
  - Execution state: pending

- [ ] E-03 Update `rollback_migration` (:744-756) to REVERSE the recorded relocations (from the incremental journal E-NEW writes), not merely delete staged `.aw/` copies. Iterate the journal (written incrementally by E-06) in REVERSE order; for each entry: an `action: move` relocates the destination back to the source (git mv back when `was_tracked`; filesystem move otherwise); an `action: dedup-remove` restores the removed twin FROM the surviving destination (copy the destination bytes back to the twin's source path, re-tracking if it was tracked) before that destination is itself moved back. Then revert the policy switch + remove the switch receipt/retention manifest, as today. Keep the host-adapter-in-place skip. Rollback MUST be safe from a PARTIAL (mid-move, resumed-or-not) state as well as a completed one, using only the journal. A rollback after a completed move-based apply MUST leave the repo byte-identical and rename-clean versus the pre-apply HEAD.
  - Depends on: E-02, E-06
  - Expected outcome: `aw migrate-layout rollback` after a full OR partial move-based apply returns the repo to the legacy-authoritative state with no `.aw/` records/system residue, every legacy source back in place (including de-duplicated twins), and `git status` clean of migration renames.
  - Execution state: pending

### Task group 2: Interactive leftover disposition

- [ ] E-04 Add a post-move leftover-disposition step to `execute_migration` (and expose it on the `migrate-layout` CLI): after all classified items are moved, scan the legacy roots for anything that remains (unclassified/leftover material under the inventoried legacy roots, excluding host-adapter-in-place and anything intentionally preserved) and INTERACTIVELY ask the operator per group what to do: keep (leave in place), remove (delete from disk/git), or defer (record in the retention manifest for a later `cleanup`). Provide a non-interactive path (`--yes` / an explicit `--leftovers keep|remove|defer` flag, default `defer`) so CI and scripted runs never block on a prompt and never delete without an explicit choice. Record the decision + affected paths in the transaction journal and the durable migration record.
  - Depends on: E-02
  - Expected outcome: after moving, the tool reports the leftover set and either prompts (interactive) or applies the flag (non-interactive); the chosen disposition is recorded; nothing is deleted without an explicit keep/remove/defer decision.
  - Execution state: pending

### Task group 3: Reconcile the migration contract and tests

- [ ] E-05 Reconcile the retention-manifest semantics and the controlling documentation to move-not-copy: the manifest now records the MOVES performed (for rollback) and the leftover disposition, not a set of retained copies to be cleaned later; align `cleanup_migration` (which previously deleted retained legacy copies) with the new model (its role narrows to acting on `defer`red leftovers, or is folded into the leftover step). Update the awphysical migration tests to assert MOVE semantics: `tests/test_layout_migration.py`, `tests/test_acceptance_matrix.py` (E-03/E-04/E-07), and `tools/awphysical/test_awphysical_tools.py` must assert the source is GONE post-move (not merely that the destination exists), that tracked items produce a git rename, that rollback restores the source, that a mid-move interruption is recoverable by BOTH resume (completes) and rollback (restores) to a non-torn state, that the identical-hash dedupe collapses to one destination, and that the leftover step records a disposition. Mutation-probe at least one assertion (e.g. reverting the move to a copy must make a "source no longer exists" assertion go RED).
  - Depends on: E-02, E-03, E-04, E-06
  - Expected outcome: the migration contract (code + manifest + docs) consistently describes a move; the test suite asserts move + crash-recovery + dedupe semantics and fails if the engine regresses to copy; full suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `execute_migration` is a copy-verify-switch-retain state machine with a transaction journal, lock, preflight hash re-check, and phase checkpoints (initialized -> locked -> staged -> verified -> switched -> retained -> completed). The copy is `shutil.copy2` at :478; the source is never removed by apply.
- The write-authority switch is real: `config.json` `records_backend=repository` -> `project_context.py:599` resolves `records_root` to `.aw/records`, and `record_producers.guard_write` rejects legacy `.agents/` writes.
- The read tooling is filesystem-based and dual-tree by design: `artifact_core.SCAN_ROOTS` lists both `.agents/*` and `.aw/records/*`; `attention.py` normalizes `.aw/records/ -> .agents/` for identity, so a retained twin surfaces as a duplicate-id. The maintainer's ruling keeps this dual scan (cheap; correct once legacy is empty post-move).
- Legacy retention was previously justified for rollback; a move plus the reversible transaction journal supplies the same rollback capability without a permanent twin.
- Host adapters (`.claude`, `.opencode`, `AGENTS.md`) are `host-adapter-in-place` and must NEVER be moved (spec S3.1/S9); the copy phase and rollback already skip them and must continue to.

## Findings

- The Order-11 self-migration executed cleanly as a transaction but produced a duplicate installation: 561-file `.aw/` copy committed, legacy `.agents/` retained + tracked, `aw attention valid:False` with 276 duplicate-ids. Root cause is `execute_migration` copying rather than moving. That cutover was rolled back (repo returned to HEAD 5c91499, legacy authoritative, attention valid) pending this fix.
- The bug is in the SHIPPED reusable tool (`aw migrate-layout` -> `MigrationManager`), so it affects every repo the tool migrates, not just the framework's own repo.
- `git mv` both moves on disk and stages the rename, preserving history (a plain `mv` of a tracked file leaves a delete+add). Untracked items have no index entry, so a filesystem move is correct.
- /plan-review finding (2026-08-16): the pre-existing `resume_migration` (:670-676) RE-RUNS `execute_migration` from scratch when a crash leaves the checkpoint at `locked` (the copy loop only checkpoints `staged` after completing). Under COPY this was ~idempotent; under MOVE it is data-unsafe (moved sources are gone, a fresh inventory misses them, the partial move is neither completed nor reversed). E-06 was added to make the move phase per-item-checkpointed and resume/rollback journal-driven so any crash resolves to fully-migrated or fully-legacy, never torn.
- /plan-review finding: `git_state` (tracked/untracked) lives on the INVENTORY item joined via `inv_item_map` in `execute_migration`, not on the map item; E-02 anchors to `inv_item.get("git_state")`. The `build_migration_map` `deduplicate_identical` collision (two identical-hash sources -> one destination) cannot be handled by moving twice; E-02 moves the first and removes the twin, recorded for reversal. Because the source is gone post-move, the byte-identical verification hashes the DESTINATION.

## Proposed changes (ordered, validatable)

1. Move classified items (git mv tracked / mv untracked) in the copy phase, recording reversible moves; keep the byte-identical post-move hash check and the host-adapter skip.
2. Reverse the moves in `rollback_migration`.
3. Add the interactive (with non-interactive flag) leftover-disposition step and record its decision.
4. Reconcile the retention manifest + `cleanup_migration` semantics and update the awphysical migration tests to assert move semantics (source gone, git rename, rollback restores), with a mutation probe.

## Deferred / out of scope (with reason)

- Re-running the real Order-11 self-migration with the corrected tool is Order 11's job (this IPD only fixes the tool the migration uses). It runs after this lands and is verified.
- The inventory classifier dispositions, the resolver/packaging reconciliation (xzuxet), and workflow bodies are unchanged.

## Scope check

- Over-scope: none; confined to the migration engine's copy/rollback/leftover behavior, its manifest/docs, and the migration tests.
- Under-scope: the move, the reverse-move rollback, the leftover step, the manifest/cleanup reconciliation, and the test updates are all included.

## Required tests / validation

- `python3 -m unittest tests.test_layout_migration tests.test_acceptance_matrix tools.awphysical.test_awphysical_tools`
- A disposable-clone real apply proving: sources gone post-move, tracked items are git renames, `aw attention` reports `valid: true` (no duplicate-ids), the full serial suite is green, and `aw sanitize --agent` is clean.
- `python3 -m unittest discover -s tests -t .` (full serial suite)
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`

## Spec / documentation sync

- Update the controlling spec 20260810-1447-01 language that describes "copy-verify-switch-retain" and "cutover never deletes legacy; cleanup is a later, separately confirmed operation" to the move-based contract with an interactive leftover step (retention/rollback is provided by the reversible move journal, not a permanent twin). Record the change and rationale in DECISIONS.
- Note the CLI change (leftover flag) in the `migrate-layout` help and any migration walkthrough.

## Open questions

### OQ-01: Does the controlling spec need a formal revision, or does this IPD reconcile the code to a maintainer ruling recorded here?

- Blocking: no
- Status: open
- Owner: human maintainer
- Resolution or deferral rationale: The maintainer ruled the move-not-copy + interactive-leftover contract in chat. This IPD implements it and updates the spec text + DECISIONS to match. If the maintainer wants a separate spec-editing pass (aw specs) before implementation, that gate is honored; otherwise the spec sync in this IPD is the record.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-02 validates E-02
  - Required evidence: On a disposable clone, run the real apply; paste `git status`/`git show --stat` proving classified tracked items are RENAMES and the legacy sources no longer exist on disk; paste the transaction journal move records. Mutation: reverting the move to `shutil.copy2` makes the "source no longer exists" assertion go RED, then GREEN when restored.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: After a move-based apply on a disposable clone, run `aw migrate-layout rollback`; paste evidence the repo is byte-identical + rename-clean versus pre-apply HEAD (legacy back in place, no `.aw/` records/system residue).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Paste a run showing the leftover set reported and (interactive) a prompt / (non-interactive `--leftovers`) the flag applied, with the decision recorded in the journal; a `remove` path deletes only the chosen leftovers and nothing else; the default without an explicit choice never deletes.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Paste the full serial suite + `tools.awphysical` result (all green) with the updated move-asserting tests; paste `aw attention --check` reporting valid after a real move-based apply on a disposable clone (no duplicate-ids); show the retention-manifest/docs/spec updates.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: On a disposable clone, inject a crash mid-move (fault-injection or a kill after N items), then run `aw migrate-layout resume` and show the migration completes with every source moved exactly once (no half-moved/duplicated item); separately, from the same mid-move state, run `rollback` and show every source restored. Paste the incremental journal proving per-item persistence. Mutation: making the move phase checkpoint only at the end (not per item) makes the resume-after-crash test go RED.
  - Observed evidence:
  - Result: pending



## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: One coherent correction of the migration engine's core relocation behavior (move instead of copy) plus its reverse (rollback), its leftover handling, and the tests/docs that describe the contract.

Execution requires human approval recorded as `Status: approved` + an attributed `- Approval:` line. The executor implements the E-items, pastes actual command output (including the mutation probe and a disposable-clone real apply), commits only the explicitly scoped paths, never pushes, runs `aw ipd lint --phase pre-transition --agent` and the full serial suite before any transition, and the orchestrator owns the terminal move to `executed/`. This IPD is a prerequisite for re-running the Order-11 self-migration correctly.

# IPD: Migrate existing on-disk research docs status intake -> todo and regenerate the index, with backward-compatible read

- Date: 2026-08-27
- Kind: child
- Concern: With the code token renamed to `todo` (child 01, backward-compat accepts legacy `intake`), the ~10 existing on-disk research docs still carry `status: intake` in frontmatter. They must be migrated to `status: todo` and the INDEX regenerated, so the corpus matches the new vocab and the board/index show `todo`.
- Scope: Migrate every on-disk research doc whose frontmatter `status:` is `intake` to `todo` (found ~10 via `grep -rl '^status: intake' .aw/records/research/`), preserving all other frontmatter, then regenerate `INDEX.json`/`INDEX.md` (`aw research index`). Use the naming/frontmatter tooling, not a blind sed, so it goes through the contract. Verify `aw research index --check` is clean and `aw attention` shows the migrated docs as READY `todo`. This depends on child 01 (the contract must ACCEPT `todo` first, and keep accepting `intake` during the window). Add a test that a doc created with legacy `intake` is migrated to `todo` and that `aw research index --check` passes post-migration.
- Scope-Paths: .aw/records/research/, tests/
- Status: approved
- Set: rstodo
- Order: 2
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: lpqy64
- Approval: 2026-08-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (aw set): plan-review APPROVE WITH REVISIONS APPLIED: PR-201 fixed false 'all READY' acceptance -> class-parity (verified 5 READY/5 PARKED via stale-reclass); PR-202 named the contract tool aw research promote --to todo (hot->hot in-place, auto-reindex); PR-203 concrete V-01 evidence incl before/after class table; PR-204 execution contract; PR-205 trimmed over-scoped code Scope-Paths (data migration); OQ-01 resolved (promote --apply gate).

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Migrate the ~10 existing on-disk research docs from `status: intake` to `status: todo` (through the contract, not a blind sed), regenerate the INDEX, and verify the board/index show `todo` and `aw research index --check` is clean.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: migrate + reindex

- [ ] E-01 Identify every research doc with frontmatter `status: intake` (`grep -rl '^status: intake' .aw/records/research/`; exactly 10 today) and rewrite each to `status: todo` preserving all other frontmatter, THROUGH the contract-aware tool - NOT a blind sed. The tool is `aw research promote <id6> --to todo` (dry-run default; `--apply` to write). For a HOT target (`todo` is a hot state), `promote` rewrites the frontmatter in place at the research root (its `_target_path` returns the root for hot statuses, so there is NO shard move) and auto-refreshes INDEX.json/INDEX.md via `apply_moves`. This requires child 01 first (`todo` must be a member of `research_contract.STATUSES` or `plan_transition` rejects `--to todo`). VALIDATE the same-path case in dry-run before applying (a hot->hot transition has src==dst; confirm the `git mv` step is a no-op and does not error). After applying to all 10, confirm `aw research index --check` is clean.
  - Depends on: none
  - Expected outcome: zero `^status: intake` docs remain; all 10 are `status: todo` with all other frontmatter intact; INDEX regenerated; `aw research index --check` clean.
  - Attention parity (NOT "all READY"): the migration is attention-class-PRESERVING. Verified today: of the 10 `intake` docs, ~5 classify `ready` (READY) and ~5 classify `parked` (the stale-reclass moves finished-but-unpromoted / run-prompt-set / cited-by-executed hot docs to PARKED - and `todo` is still a hot state, so that reclass still fires). After migration each doc MUST keep its SAME class as `todo` (the READY ones stay READY, the PARKED ones stay PARKED). Do NOT assert "board shows them all READY" - that contradicts the orchestrator's byte-identical-classification invariant.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Exactly 10 docs carry `^status: intake` (verified). Includes this session's sk94i0/40g511/3nlmug/ud28vy and older intake docs.
- The contract-aware status setter is `aw research promote <id6> --to <status>` (`research_archive.run_promote` -> `plan_transition` -> `apply_moves`): it validates `--to` against `STATUSES`, rewrites the frontmatter status preserving the rest (`_rewrite_status_in_text`), does a tracked `git mv` (a no-op for a hot->hot transition since `_target_path` returns the research root for hot statuses), and refreshes INDEX.json/INDEX.md. Dry-run by default; `--apply` writes. This is the right tool - no blind sed, no new helper.
- Depends on child 01: `plan_transition` rejects `--to todo` until `todo` is in `research_contract.STATUSES` (verified: today `aw research promote <id6> --to todo` errors "status must be one of ['active','archive','intake','reference']"). Child 01 also keeps accepting legacy `intake` during the window.
- Attention behavior: `attention.py` stale-reclasses finished-but-unpromoted HOT docs (run-prompt-set or cited-by-executed) from READY to PARKED. `todo` is still hot, so this reclass is unchanged; the migration is class-preserving, NOT "everything becomes READY".

## Findings

Mechanical data migration. Risks: (1) doing it OUTSIDE the contract (a blind sed could corrupt frontmatter or skip index refresh) - mitigated by using `aw research promote --to todo`; (2) asserting the WRONG acceptance criterion - the original "board shows them READY" is false (5 of the 10 are PARKED via stale-reclass), so the acceptance is CLASS PARITY, not all-READY; (3) the hot->hot `git mv` same-path case - validate in dry-run that it is a clean no-op before applying.

## Proposed changes (ordered, validatable)

1. Rewrite the 10 docs' `status: intake` -> `status: todo` via `aw research promote <id6> --to todo --apply` (preview all first, no `--apply`). INDEX is refreshed by the tool.
2. Confirm `aw research index --check` clean (belt-and-suspenders; the promote already reindexed).
3. `tests/`: a doc with legacy `intake` migrates to `todo` (frontmatter-only change, other fields intact); its attention class is unchanged by the migration; post-migration `index --check` passes.

## Deferred / out of scope (with reason)

- The code token rename + backward-compat read: child 01 (dependency).
- Dropping the `intake` compat alias: orchestrator OQ-01 (post-migration + one release).

## Scope check

- Over-scope: removed `agent_workflows/research_cmd.py` and `research_index.py` from Scope-Paths - this child is a pure DATA migration; those code files are child 01's. The only code touched here is `tests/` (the migration + parity test). INDEX regeneration is a generated-artifact write under `.aw/records/research/`, not a code change.
- Under-scope: none (all 10 on-disk docs + INDEX + the parity/compat test covered).

## Required tests / validation

- `grep -rl '^status: intake' .aw/records/research/` returns nothing after migration (was 10).
- Each migrated doc is `status: todo` with all other frontmatter intact (diff shows ONLY the status line changed).
- `aw research index --check` is clean.
- Attention CLASS PARITY (not "all READY"): capture each of the 10 docs' attention class BEFORE migration (today: ~5 `ready`, ~5 `parked`) and confirm each keeps the SAME class as `todo` AFTER migration. The count of READY vs PARKED research items is unchanged; only the native_status label flips `intake`->`todo`.

## Spec / documentation sync

- N/A (data migration; vocab docs updated in child 01).

## Open questions

### OQ-01: Migrate under a --dry-run/--apply gate (recommended) to preview the 10 rewrites?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED. `aw research promote <id6> --to todo` is dry-run by default and writes only with `--apply` - exactly the preview-then-apply pattern. Run each id6 without `--apply` first (or script the 10 in a loop, previewing all, then re-run with `--apply`), so the exact set is auditable before any write. No new flag or tool is needed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the ACTUAL output of: (1) `grep -rl '^status: intake' .aw/records/research/` returning nothing (was 10); (2) `grep -rl '^status: todo' .aw/records/research/ | wc -l` == 10; (3) a `git diff` sample on one migrated doc showing ONLY the `status:` line changed (all other frontmatter intact); (4) `aw research index --check` printing clean; (5) the BEFORE/AFTER attention-class table for the 10 docs (e.g. from `aw attention`), showing the same READY/PARKED split before and after - only the label flips `intake`->`todo` (NOT all-READY); (6) the new test run passing (migration + class-parity + `index --check`). Verified in a separate pass, not from the E-01 checkmark.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

### Execution contract

- Human approval required before execution. This is child 02 of Set `rstodo` (order 02); it DEPENDS on child 01 `p3o9je` (execute 01 first - `promote --to todo` fails until `todo` is in `STATUSES`).
- Resolved open questions: OQ-01 resolved (use `aw research promote --to todo`, dry-run by default; preview all 10 before `--apply`).
- Scope fence: touch ONLY `.aw/records/research/` (the 10 docs + regenerated INDEX) and `tests/`. This is a DATA migration; it makes NO code changes (those are child 01). Do NOT drop the `intake` compat alias here (orchestrator OQ-01: post-migration + one release).
- Data-safety: preview every `promote` (no `--apply`) first and inspect the exact 10-file set; apply only after the preview matches; the change to each doc must be the single `status:` line (verify with `git diff`). Do NOT hand-edit or sed frontmatter.
- Honesty (hard MUST): when reporting `index --check`, the suite, or any command as passing, paste the ACTUAL runner output. Never claim a validation passed that was not run. V-01 is verified from pasted output in a separate pass from the E-01 checkmark.
- Commit discipline: commit ONLY the files this child changed, path-scoped (`git commit -m <msg> -- <path> ...`); never `git add -A`/`-a`/bare add; never push; never create tags or releases. Note the migrated docs + INDEX are tracked records, so they ARE committed (unlike run-record scratch).
- Post-gate lifecycle move (NOT a checklist item; performed by the ipd-lifecycle gate after all E/V items complete and validated): append a `## Workflow history` line, set terminal `Status: executed`, and `git mv` from `pending/` to `.aw/records/plans/executed/` - coordinated with the orchestrator `dh5gnl` moving the whole Set together. Do not move until `aw ipd lint --phase pre-transition` conforms and V-01 is verified with pasted evidence; otherwise STOP and report.

# IPD: aw migrate-layout: optional rename-on-migrate to the .type.md grammar (ask-then-offer)

- Date: 2026-08-18
- Kind: child
- Concern: Backlog u9cicx (awnaming Set OQ-02, resolved ask-then-offer). The awnaming Set (spec 20260817-2147-01) shipped the uniform `.type.md` naming grammar for NEW files and renamed THIS repo's records, but `aw migrate-layout` (which moves ANOTHER repo's legacy `.agents/` records into `.aw/records/`) does NOT rename those legacy files. Because the record readers are front-matter-driven, a migrated repo's bare-`.md` records keep working (permanent dual-read), so renaming is an OPTIONAL nicety, not a correctness requirement. This adds an opt-in rename-on-migrate: gentle by default, ASK when interactive, `--rename-to-grammar` flag when non-interactive.
- Scope: The `aw migrate-layout` rename hook only. IN: an opt-in `--rename-to-grammar` CLI flag (default OFF) + a `rename_to_grammar` config key, an interactive ASK, and the rename transform that appends the correct `.<type>` facet to a migrated durable record's destination name (reusing the awnaming grammar map); tests. OUT: renaming by DEFAULT (rejected - too invasive on users' files); comms + research (documented exceptions, same as awnaming Order 02); the grammar/producers/validators (already shipped in awnaming Order 01); this repo's own files (already renamed in Order 02).
- Status: approved
- Approval: 2026-08-18, human ("approve. go.") after /plan-review (APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed).
- Set: awmigrename
- Order: 1
- Highest E allocated: 05
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 0qp7u8

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): from backlog u9cicx; grounded in layout_migration.py (_resolve_destination_path:254, _perform_move:290) + cli.py _run_migrate_layout:3574 (config/interactive flow).
- 2026-08-18 /plan-review (opencode Opus 4.8): APPROVE WITH REVISIONS APPLIED. Verified apply-flow (layout_migration.py:737 dst compute, 764 dedup, 773 journal, 1095/1108 rollback) + destination_root_class is high-level (aw_layout_inventory.py:691-727). Fixed: PR-001 (no per-item sub-type field; derive sub-type from destination_relpath, class resolution is two-level), PR-002 (apply facet BEFORE dedup dest_seen check), PR-003 (journal the faceted destination so rollback reverses correctly; hook at call site not inside _resolve_destination_path which rollback pruning reuses), PR-004 (destination_root_class only gates records-eligibility). All folded into E-03/E-04 + conventions.

## Goal

Let `aw migrate-layout` OPTIONALLY rename a migrated repo's legacy durable records to the uniform
`.type.md` grammar, without ever forcing it: OFF by default (a migrated repo's bare-`.md` files keep
working via the permanent front-matter dual-read); when the migration is INTERACTIVE, ASK the human
whether to also adopt the grammar; when NON-INTERACTIVE, honor an opt-in `--rename-to-grammar` flag
(or a `rename_to_grammar` config key). Comms and research remain naming exceptions, exactly as in the
awnaming Set.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: the rename decision (flag + config + interactive ask)

- [ ] E-01 Add the opt-in surface: a `--rename-to-grammar` flag (`action="store_true"`, default False) to the `migrate-layout` arg parser (agent_workflows/cli.py:1276 block) AND a `rename_to_grammar` config key parsed in `_run_migrate_layout` (cli.py:3574, alongside the existing `target_backend`/`leftovers`/`roots`/`confirm` keys). Default OFF.
  - Depends on: none
  - Expected outcome: `aw migrate-layout --help` lists `--rename-to-grammar`; a config file with `"rename_to_grammar": true` is parsed without error; neither set => rename disabled.
  - Execution state: pending
- [ ] E-02 Add the interactive ASK: when the migration runs interactively (a TTY, mirroring the existing confirm/leftovers prompts) and neither the flag nor the config key was given, present a self-contained P12 question - "Also rename migrated records to the uniform `.type.md` grammar? (default: no, leave existing names)" - and use the answer. When non-interactive and unset, default OFF (never rename silently).
  - Depends on: E-01
  - Expected outcome: an interactive run with no flag prompts once and honors the answer; a non-interactive run with no flag/key does NOT rename.
  - Execution state: pending

### Task group 2: the rename transform

- [ ] E-03 Implement the rename in the migration apply path, at the destination computed at layout_migration.py:737 (`dst_p = self._resolve_destination_path(mapping["destination_relpath"], target_backend)`): when rename-on-migrate is ON, append the correct `.<type>` facet to `dst_p`'s name. Class resolution is TWO-LEVEL: the mapping's `destination_root_class` gives the high-level class (only `records` items are eligible; `system`/`config`/`doc`/`host-adapter-in-place` are never faceted), and for a `records` item the SUB-TYPE is parsed from the `records/<subtype>/...` segment of `destination_relpath` (plans->`.ipd`, specs->`.spec`, walkthroughs->`.walkthrough`, roadmaps->`.roadmap`, backlog->`.backlog`, prompts + prompt-library->`.prompt`). Reuse `plans_refs.ARTIFACT_TYPE_FACETS`. CRITICAL ORDERING: compute the faceted `dst_p` BEFORE the `dest_seen`/dedup-twin check (line 764) and BEFORE journaling (`entry["destination"]`, line 773), so twins still dedup on the final name and rollback (which reverses via the journaled `destination`, line 1095/1108) restores correctly. The rename thus rides the SAME atomic `_perform_move` (no second pass, no history loss). Skip an already-faceted name (idempotent).
  - Depends on: E-01
  - Expected outcome: with rename ON, a legacy `.agents/.../plans/pending/20260101-0001-01-a.md` lands as `.aw/records/plans/pending/20260101-0001-01-a.ipd.md`; with rename OFF it lands bare; research + comms records are never faceted; the move journal records the faceted destination.
  - Execution state: pending
- [ ] E-04 Guard the exceptions + sub-type resolution: only `records`-class items are eligible; comms (routing-named) and research (`.<model>.<kind>.md`) sub-types are NEVER renamed even when the flag is on; a `records` sub-type with no durable facet, a non-`records` class, or a README/INDEX/STATUS basename is left bare. The comms/research exclusion is by SUB-TYPE (parsed from `destination_relpath`), mirroring awnaming Order 02.
  - Depends on: E-03
  - Expected outcome: with rename ON over a fixture containing plans + specs + comms + research + a README, only plans/specs get faceted; comms/research/README/non-records classes stay bare.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_awmigrename.py` covering: flag + config-key parsing (E-01); the non-interactive default-OFF (no rename) and flag-ON (rename) behaviors over a migration fixture (E-03); the exception guard for comms/research/README (E-04); idempotency (already-faceted names unchanged); a rename rides an atomic tracked move (the destination is git-added/renamed, not a copy). Run the FULL serial suite (`python3 -m pytest -p no:xdist`) and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04
  - Expected outcome: the new module passes; full serial suite green with no regressions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The migration is transactional and MOVES (no retained twin): `MigrationManager._perform_move` (layout_migration.py:290) uses `git mv` on the same work tree with a filesystem-move + `git rm --cached`/`git add` fallback; the rename must ride this same move to preserve history.
- The destination name is computed at the apply-flow call site (layout_migration.py:737) via `_resolve_destination_path` from the map item's `destination_relpath`; append the facet to that computed `dst_p` BEFORE the dedup-twin `dest_seen` check (764) and journaling (773), NOT inside `_resolve_destination_path` (which is also used for rollback empty-dir pruning at 1118).
- `MigrationItem`/mapping has NO record-sub-type field: `destination_root_class` is HIGH-LEVEL (`records`/`system`/`config`/`doc`/`host-adapter-in-place`, from aw_layout_inventory.py:691-727). The record SUB-TYPE (plans/specs/comms/...) must be parsed from the `records/<subtype>/` segment of `destination_relpath`.
- Rollback reverses a move via the JOURNALED `entry["destination"]` (layout_migration.py:1095/1108), so as long as the faceted name is journaled, reversal is correct; the `_resolve_destination_path` re-derivation at 1118 is only for empty-dir pruning.
- `_run_migrate_layout` (cli.py:3574) already parses a JSON `--config` with `target_backend`/`leftovers`/`roots`/`confirm` and supports both interactive and non-interactive flows; the new flag/key/ask slot into that shape.
- The awnaming Set already provides the grammar primitives: `plans_refs.ARTIFACT_TYPE_FACETS` + `clustered_name(artifact_type=)`, and the class->facet mapping used in Order 02 (plans->ipd, specs->spec, walkthroughs->walkthrough, roadmaps->roadmap, backlog->backlog, prompts/prompt-library->prompt).
- comms + research are documented naming EXCEPTIONS (awnaming Order 02 OQ-01 + spec 20260817-2147-01): comms are routing-named, research keeps `.<model>.<kind>.md`.
- Dual-read is permanent + free (readers are front-matter-driven), so leaving migrated files bare is fully correct; this feature is purely a convenience.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | The migration already moves atomically via git mv. | The facet rename must ride the SAME move (append at destination-name resolution), not a second rename pass, to preserve history + stay transactional. |
| F2 | Dual-read is free + permanent. | Default OFF is safe; a not-renamed migrated repo works forever. Renaming is convenience only. |
| F3 | Record class is already known in the migration map. | Facet selection is a class->facet lookup; comms/research are excluded by class, mirroring Order 02. |
| F4 | Forcing a rename rewrites users' historical filenames + external citations. | Never rename by default; require an explicit opt-in (flag/config) or an interactive yes (OQ-02 resolution). |

## Proposed changes (ordered, validatable)

1. Add the `--rename-to-grammar` flag + `rename_to_grammar` config key, default OFF (E-01).
2. Add the interactive ask; non-interactive-unset stays OFF (E-02).
3. Append the class-correct `.<type>` facet at destination resolution, riding the atomic move (E-03).
4. Exclude comms/research/non-durable classes; idempotent on already-faceted names (E-04).
5. Test module + full serial suite (E-05).

## Deferred / out of scope (with reason)

- Renaming by DEFAULT: rejected (OQ-02) - too invasive on users' historical filenames + citations.
- comms + research renaming: documented exceptions (awnaming), never faceted.
- The grammar/producers/validators + this repo's own files: already done (awnaming Orders 01/02).
- Rewriting citations INSIDE migrated files to the new names: out of scope - other repos cite by immutable Id, and a migrating user owns their own citation cleanup; this feature only renames files.

## Scope check

- Over-scope: none - strictly the migrate-layout rename hook + its opt-in surface + tests.
- Under-scope: none - flag + config + interactive ask + transform + exception guard + tests fully cover the u9cicx/OQ-02 behavior.

## Required tests / validation

`tests/test_awmigrename.py` (E-05) + the full serial suite; each V-item below pins one E to
falsifiable evidence over a migration fixture.

## Spec / documentation sync

Update the migrate-layout help text (the flag) and, if the migrate-layout behavior is documented in a
shipped workflow/README, note the opt-in rename. No spec change: spec 20260817-2147-01 already records
(OQ-2/OQ-02) that the migration rename is optional; this IPD implements that resolution. On completion,
move backlog u9cicx to done.

## Open questions

### OQ-01: When rename-on-migrate is ON, should the migration also rewrite intra-repo citations to the renamed files?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: NO (out of scope, recorded above). Plans/records cross-reference by immutable `- Id:`/`PLAN-xxxxxx`, so functional references survive a rename; filename citations are overwhelmingly historical prose. Rewriting a migrating user's citations is invasive and belongs to that user, not the migration tool. This feature renames FILES only; dual-read keeps any bare-name citation resolvable.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw migrate-layout --help` showing `--rename-to-grammar`, and a test asserting a config with `rename_to_grammar: true` parses and neither-set disables the rename.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste test output proving an interactive run with no flag prompts once and honors the answer, and a non-interactive run with no flag/key does not rename.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste test output over a migration fixture showing a plan lands as `.ipd.md` with rename ON and bare with rename OFF, and that the rename rode an atomic tracked move (git rename/add of the destination, not a copy).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste test output over a mixed fixture (plans + specs + comms + research + README) with rename ON showing only plans/specs faceted; comms/research/README stay bare; an already-faceted name is unchanged (idempotent).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the tail of the full serial suite (`python3 -m pytest -p no:xdist`) showing `tests/test_awmigrename.py` and the total pass count with no regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(opencode Opus 4.8) performs each E, verifies each V with pasted evidence, commits ONLY the files it
changed path-scoped (never `git add -A`), never pushes, and moves this plan to
`.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every
V-item is `pass`. On completion, move backlog u9cicx to done. Not a release blocker (post-awnaming
convenience).

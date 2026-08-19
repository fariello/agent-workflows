# IPD: rename local lanes to untracked with catch-all gitignore

- Date: 2026-08-18
- Kind: child
- Concern: awuntracked Order 01 (TODO item #39). The prompts and comms scaffolding create `local/` lanes whose SOLE purpose is to hold untracked, machine-local content (raw/sensitive prompt drafts; ephemeral comms routing). The name `local/` is ambiguous - it reads like "local config" and conceptually collides with several unrelated `local` uses in the tree - whereas `untracked/` states the intent plainly and matches the repo's own untracked-safety vocabulary. The lane is defined in a small set of engine.py constants/templates (PROMPTS_LOCAL_SUBDIR="local" engine.py:3756; the prompts gitignore template engine.py:3757-3763 with literal `local/` at :3762; COMMS_LOCAL_SUBDIRS engine.py:3769; the comms gitignore template engine.py:3815-3820 with literal `local/` at :3819; the comms README template engine.py:3822-3838 referencing `local/` at :3831/:3837; the scaffold mkdir engine.py:4337-4341; the uninstall guidance engine.py:2383; the AGENTS pointer engine.py:949), preserved across migration at layout_migration.py:429-438 (the `/local/` check at :438). A ready-made untracked convention already exists to reuse (UNTRACKED_SLUG="untracked" / UNTRACKED_PATTERNS engine.py:1206-1207, whose `**/*untracked*/` pattern already catch-alls any dir named `untracked`; `ensure_untracked_gitignore` engine.py:2407). Rename the prompts/comms `local/` lanes to `untracked/`, ensure the catch-all gitignore covers any `untracked/` dir, and migrate installed repos.
- Scope: IN: rename the prompts/comms `local/` lanes to `untracked/` across engine.py scaffolding + templates (the two constants + the two gitignore templates + the comms README template + the scaffold mkdir + the uninstall guidance + the AGENTS pointer), thread the rename through the migration-preservation path (layout_migration.py:429-438), ensure a catch-all `.gitignore` covers any `untracked/` dir (reuse UNTRACKED_SLUG/UNTRACKED_PATTERNS/ensure_untracked_gitignore), update the tests that assert `local/` (tests/test_setup_artifacts.py, tests/test_installer.py:1179, tests/test_comms.py:146, tests/test_layout_migration.py:747-884, tools/agy_run.py docstring + tools/test_agy_run.py), and ADD a migration that renames an existing repo's prompts/comms `local/` lane to `untracked/` preserving contents. OUT: any unrelated `local` name MUST NOT change - `.aw/config/local.json`, `local-leaks-allowlist.toml`, the `local-only` preset, and the `LOCAL_GIT`/`CONFIG_LOCAL` enums (project_schema.py:37/:59) are explicitly excluded.
- Status: executed
- Set: awuntracked
- Order: 1
- Highest E allocated: 03
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: c32roo

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from TODO item 39 (local/ -> untracked/).
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE. Verified all rename anchors still accurate (PROMPTS_LOCAL_SUBDIR:3756, COMMS_LOCAL_SUBDIRS:3769, mkdir 4337/4340, UNTRACKED_SLUG:1206, ensure_untracked_gitignore:2407, migration-preservation layout_migration.py:429-431); the do-not-touch fence for unrelated `local` names (local.json, local-only preset, LOCAL_GIT) is present. No findings.
- 2026-08-18 executed (opencode Opus 4.8): E-01..E-03 performed, V pass; local/->untracked/ lane rename + migration; full serial suite 1150 passed 1 skipped.

## Goal

Rename the prompts and comms `local/` lanes to `untracked/` (a clearer name for their machine-local,
never-committed purpose) with a catch-all `.gitignore` for any `untracked/` dir, and migrate existing
installed repos - without touching any unrelated `local` name.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: Do EXACTLY the steps below, in order. The rename is CONCENTRATED - it is driven by two
constants (`PROMPTS_LOCAL_SUBDIR`, `COMMS_LOCAL_SUBDIRS`) plus a handful of literal `local/` strings in
templates/guidance/pointer text. Change ONLY those. After each code step, run the matching V-item command
and paste its output. There is a HARD DO-NOT-TOUCH fence in E-01: those `local` names have a different
meaning and MUST be left byte-for-byte unchanged. When you finish a code step, run the tests named in that
step, then the FULL serial suite in E-02. Use 4-space indentation; keep the existing template comment style.

### Task group 1: rename lanes + catch-all gitignore

- [x] E-01 Rename the prompts/comms `local/` lanes to `untracked/` across the engine.py scaffolding, the migration-preservation path, and confirm the catch-all gitignore. Make these EXACT edits:

  1. `agent_workflows/engine.py:3756` - the prompts lane constant:
     ```python
     PROMPTS_LOCAL_SUBDIR = "untracked"
     ```
  2. `agent_workflows/engine.py:3757-3763` - the prompts nested-gitignore template. Change the literal `local/` on the last content line (:3762) to `untracked/` and update the prose to match:
     ```python
     _PROMPTS_GITIGNORE_TEMPLATE = """\
     # agent-workflows prompts staging: ignore the box-local, quarantine lane.
     # `untracked/` holds raw/sensitive/work-in-progress prompts (e.g. session-handoff drafts); it is
     # never committed. Promote a reviewed, scrubbed copy into a tracked lifecycle bucket (pending/, ...)
     # with `git mv`. The tracked buckets (siblings of this file) travel with the repo.
     untracked/
     """
     ```
  3. `agent_workflows/engine.py:3769` - the comms lane subdirs constant name stays but the PARENT dir name changes at the mkdir/template sites; the tuple itself is unchanged:
     ```python
     COMMS_LOCAL_SUBDIRS = ("inbox", "sent", "archive", "scheduled", "acks")
     ```
     (Leave this line as-is; it names the SUB-dirs, not the lane. The lane name is the literal `"local"` used at the mkdir in step 6 and in the templates in steps 4-5.)
  4. `agent_workflows/engine.py:3815-3820` - the comms nested-gitignore template. Change `local/` (:3819) to `untracked/` and the prose:
     ```python
     _COMMS_GITIGNORE_TEMPLATE = """\
     # agent-workflows inter-agent comms: ignore the box-local, ephemeral lane.
     # `untracked/` holds this machine's routing churn and scheduled messages; it is never committed.
     # `shared/` (a sibling of this file) is tracked deliberately and travels with the repo.
     untracked/
     """
     ```
  5. `agent_workflows/engine.py:3822-3838` - the comms README template. Change the two `local/` references (the layout bullet at :3831 and the privilege-level line at :3837) to `untracked/`:
     - `:3831`: `- `untracked/` (gitignored): this box only, ephemeral. `inbox/` incoming, ...`
     - `:3837`: `... The directory you write to IS the privilege level: `untracked/` = ephemeral/untracked, `shared/` =`
  6. `agent_workflows/engine.py:4337-4341` - the scaffold mkdir. The prompts lane uses the constant (already renamed in step 1); the comms lane uses a literal `"local"` that MUST become `"untracked"`:
     ```python
         (repo_root / dirs["prompts"] / PROMPTS_LOCAL_SUBDIR).mkdir(
             parents=True, exist_ok=True
         )
         for sub in COMMS_LOCAL_SUBDIRS:
             (repo_root / dirs["comms"] / "untracked" / sub).mkdir(parents=True, exist_ok=True)
     ```
     Also update the comment above it (engine.py:4335) from "gitignored `local/` quarantine lanes" to "gitignored `untracked/` quarantine lanes".
  7. `agent_workflows/engine.py:2383` - the uninstall/notice guidance. Change the lane paths:
     ```python
         print(
             "    - or use the gitignored untracked lanes: .agents/prompts/untracked/ and .agents/comms/untracked/."
         )
     ```
  8. `agent_workflows/engine.py:949` - the AGENTS pointer "check your inbox" clause. Change the two `local/inbox` references to `untracked/inbox`:
     ```python
             f"If `{comms_dir}/` exists, check `{comms_dir}/untracked/inbox/` (and `shared/inbox/`) at "
     ```
  9. `agent_workflows/layout_migration.py:429-438` - the migration-preservation guard. Update the docstring wording (`.agents/prompts/local/` -> `.agents/prompts/untracked/`, `.agents/comms/local/` -> `.agents/comms/untracked/`) AND the guard predicate at :438 so it preserves BOTH the legacy `local/` lane (still on disk in un-migrated repos until E-02's migration runs) AND the new `untracked/` lane. The `"untracked" in norm` clause already covers `untracked/`; keep the `/local/` clause too so a not-yet-migrated repo's lane is still preserved:
     ```python
             if (
                 "/local/" in f"/{norm}"
                 or norm.endswith("/local")
                 or "untracked" in norm
             ):
                 return False
     ```
  10. Catch-all gitignore: CONFIRM (do not add a new mechanism) that the existing UNTRACKED convention already ignores any dir named `untracked`. `UNTRACKED_PATTERNS` (engine.py:1206-1207) includes `**/*untracked*/`, which matches a nested `untracked/` dir anywhere; `ensure_untracked_gitignore` (engine.py:2407) writes these patterns into the target root `.gitignore`. No new pattern is required - the catch-all is inherited. (The per-lane NESTED `.gitignore` templates in steps 2 and 4 still emit `untracked/` for the lane's own dir.)

  HARD DO-NOT-TOUCH FENCE (these `local` names have a DIFFERENT meaning; leave them byte-for-byte unchanged):
  - `.aw/config/local.json` (machine-local config) and every reference to `config/local.json` / `config_local`.
  - `local-leaks-allowlist.toml` / `local-leaks-hints.json.example` and the `check-local-leaks` verb.
  - the `local-only` preset name (e.g. in `tools/awphysical/migration-scenarios.json`).
  - the `LOCAL_GIT` / `CONFIG_LOCAL` enums (`agent_workflows/project_schema.py:37`, `:59`) and their string values.
  - any "local time" / "local git" / "local binding" prose unrelated to the prompts/comms lane.
  - Depends on: none
  - Expected outcome: a fresh scaffold materializes `.aw/records/prompts/untracked/` and `.aw/records/comms/untracked/<sub>/` (no `local/`); the nested `.gitignore` files emit `untracked/`; the AGENTS pointer + uninstall guidance say `untracked/`; the migration guard preserves both `untracked/` and any residual `local/`; the unrelated `local` names are unchanged.
  - Execution state: performed

### Task group 2: tests + repo migration + full suite

- [x] E-02 Update the asserting tests to expect `untracked/`, ADD a migration that renames an existing repo's prompts/comms `local/` lane to `untracked/` preserving contents, and run the FULL serial suite. Concretely:

  1. `tests/test_setup_artifacts.py` (lines 78-110, 147, 257-283): replace every `local/` lane assertion with `untracked/`. The concrete edits:
     - `:81-83` prompts nested `.gitignore` contains `"local/"` -> `"untracked/"`.
     - `:85` `.aw/records/prompts/local` dir -> `.aw/records/prompts/untracked`.
     - `:86` `.aw/records/prompts/local/.gitkeep` -> `.aw/records/prompts/untracked/.gitkeep`.
     - `:88` `.aw/records/comms/local/inbox` -> `.aw/records/comms/untracked/inbox`.
     - `:104-105` `.aw/records/comms/local/inbox/.gitkeep` -> `.aw/records/comms/untracked/inbox/.gitkeep`.
     - `:108-110` comms nested `.gitignore` contains `"local/"` -> `"untracked/"`.
     - `:257-283` (the git-actually-ignores-content block) `local/` -> `untracked/` throughout: dir `.aw/records/prompts/untracked`, file `.aw/records/prompts/untracked/x.md`, the `check-ignore` path `.aw/records/prompts/untracked/x.md`, and the `local/` gitignore assertion at :265.
     - Update the explanatory comments (`# D94 ... local/`) to say `untracked/` so the intent stays legible.
  2. `tests/test_installer.py:1179`: `self.assertIn(".agents/prompts/local/", out)` -> `self.assertIn(".agents/prompts/untracked/", out)` (the `.assertIn("untracked", out)` at :1180 still holds).
  3. `tests/test_comms.py:146`: `self.assertIn(".agents/comms/local/inbox/", block)` -> `self.assertIn(".agents/comms/untracked/inbox/", block)`.
  4. `tests/test_layout_migration.py` (`LeftoverDispositionTests`, 744-885): this suite proves the migration guard PRESERVES the gitignored lane. Keep proving the same property for the RENAMED lane. Add `untracked/`-lane fixtures and assertions ALONGSIDE the existing `local/` ones (do NOT delete the `local/` coverage - a not-yet-migrated repo can still have a `local/` lane, and the guard must preserve both). Minimum: add a `.aw`/`.agents` `untracked/` lane fixture and assert `mgr._is_removable_leftover(".agents/prompts/untracked/notes.md")` is `False`.
  5. `tools/agy_run.py` (docstring examples at :99-100) and `tools/test_agy_run.py` (the `.agents/prompts/local/brief.md` / `.agents/prompts/local/task-brief.md` fixtures + assertions at :58-61, :118, :135, :169, :191, :214-215): update the lane path `local` -> `untracked`. These are prompt-BRIEF examples living in the prompts lane, so the rename applies.
  6. ADD the repo migration. Extend the migration so an existing installed repo's prompts/comms `local/` lane is RENAMED to `untracked/` with contents preserved. Implement it inside the layout-migration flow (the `MigrationManager` in `agent_workflows/layout_migration.py`, alongside `execute_migration` at :598) or the engine's `migrate_legacy_layout` (engine.py:2188) - whichever the existing lane-preservation path threads through - as an idempotent `git mv`-equivalent rename (`shutil.move` when un-tracked) that: (a) for prompts, moves `<records>/prompts/local/` -> `<records>/prompts/untracked/`; (b) for comms, moves `<records>/comms/local/` -> `<records>/comms/untracked/`; (c) is a no-op when the `local/` lane is absent or the `untracked/` lane already exists; (d) preserves ALL contents (files under the lane). Choose the SINGLE existing migration entry that already governs these lanes; do NOT add a second parallel migration mechanism.
  7. Run the FULL serial suite from the repo root and paste the tail:
     ```bash
     python3 -m pytest -p no:xdist
     ```
  - Depends on: E-01
  - Expected outcome: every updated test passes; the migration renames an existing `local/` lane to `untracked/` with contents intact and is idempotent; the full serial suite is green.
  - Execution state: performed

### Task group 3: focused migration test (optional)

- [x] E-03 (optional) Add a focused test `tests/test_untracked_lane_migration.py` with a `unittest.TestCase` subclass `UntrackedLaneMigrationTests` that: (a) builds a tmp repo fixture with a populated legacy `local/` lane under both prompts and comms (write a `notes.md` under `prompts/local/` and an `msg.json` under `comms/local/inbox/`); (b) runs the E-02 migration; (c) asserts the `untracked/` lane exists with the SAME file contents and the old `local/` lane is gone; (d) asserts a SECOND run is a no-op (idempotent). Then run the focused test and the full serial suite.
  ```bash
  python3 -m pytest tests/test_untracked_lane_migration.py -p no:xdist -q
  python3 -m pytest -p no:xdist
  ```
  - Depends on: E-02
  - Expected outcome: the focused test passes (rename + content-preservation + idempotency) and the full serial suite stays green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The prompts/comms local lanes are defined centrally in engine.py: `PROMPTS_LOCAL_SUBDIR = "local"` (engine.py:3756) and the comms lane literal `"local"` used at the scaffold mkdir (engine.py:4341); `COMMS_LOCAL_SUBDIRS` (engine.py:3769) names only the SUB-dirs, not the lane.
- Two NESTED `.gitignore` templates emit the lane's own ignore rule: prompts (engine.py:3757-3763, literal `local/` at :3762) and comms (engine.py:3815-3820, literal `local/` at :3819); the comms README template (engine.py:3822-3838) references `local/` at :3831/:3837. These are created deliverables and do NOT touch the target root `.gitignore`.
- The AGENTS pointer (engine.py:949) and the uninstall guidance (engine.py:2383) reference the lane paths in user-facing text.
- An untracked-safety convention already exists: `UNTRACKED_SLUG = "untracked"` / `UNTRACKED_PATTERNS = ("*.untracked.*", "*.untracked", "**/*untracked*/")` (engine.py:1206-1207), written into the target root `.gitignore` by `ensure_untracked_gitignore` (engine.py:2407). The `**/*untracked*/` pattern already CATCH-ALLS any dir named `untracked` anywhere - so renaming the lane to `untracked/` makes it ignored by the inherited convention; NO new pattern is needed.
- Migration preserves the lanes today (layout_migration.py:429-438); the guard at :438 keys on `/local/` and on `"untracked" in norm`, so it already preserves `untracked/` - the rename must keep BOTH clauses so an un-migrated repo's residual `local/` lane is still preserved.
- Several `local` names are UNRELATED and must be left alone: `.aw/config/local.json` / `config_local`, `local-leaks-allowlist.toml`, the `local-only` preset, and the `LOCAL_GIT`/`CONFIG_LOCAL` enums (project_schema.py:37/:59).
- Full serial suite command: `python3 -m pytest -p no:xdist` (run from the repo root).

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | The `local/` lane is driven by two constants + a small set of literal `local/` strings in templates/guidance/pointer. | The rename is CONCENTRATED, not scattered; low risk when the constant + literals are changed together. |
| F2 | An UNTRACKED convention already exists whose `**/*untracked*/` pattern catch-alls any `untracked/` dir. | The catch-all gitignore is INHERITED - no new mechanism; just rename the lane and confirm coverage. |
| F3 | Several tests hardcode `local/` (setup-artifacts, installer, comms, layout-migration, agy_run). | E-02 must update them in lockstep or the suite breaks; the layout-migration guard test must cover BOTH lane names during transition. |
| F4 | Other `local` names are unrelated (config/local.json, local-leaks-allowlist, local-only preset, LOCAL_GIT/CONFIG_LOCAL). | The rename must be scoped precisely to the prompts/comms lanes; the HARD FENCE in E-01 lists what NOT to touch. |
| F5 | The migration guard already preserves both `/local/` and `untracked`. | Installed repos keep their lane through migration; E-02 adds the actual rename so they CONVERGE on `untracked/`. |

## Proposed changes (ordered, validatable)

1. Rename the prompts/comms `local/` lanes to `untracked/` across the engine.py constant + two gitignore templates + comms README template + scaffold mkdir + uninstall guidance + AGENTS pointer, thread the rename through the migration guard (layout_migration.py:429-438), and confirm the inherited catch-all `untracked/` gitignore (E-01). 2. Update the asserting tests (setup-artifacts, installer, comms, layout-migration, agy_run), ADD an idempotent repo migration that renames an existing `local/` lane to `untracked/` preserving contents, and run the full serial suite (E-02). 3. (Optional) A focused migration test proving rename + content-preservation + idempotency (E-03).

## Deferred / out of scope (with reason)

- Renaming any unrelated `local` name (`.aw/config/local.json`, `local-leaks-allowlist.toml`, the `local-only` preset, `LOCAL_GIT`/`CONFIG_LOCAL` enums): explicitly EXCLUDED - different meaning (see the E-01 HARD FENCE).
- Broader `.gitignore` policy changes beyond the inherited catch-all `untracked/` rule: out of scope.
- Any change to the comms message format, ack enum, or privilege-level model: out of scope (only the lane DIR name changes).

## Scope check

- Over-scope: none - the rename is scoped strictly to the prompts/comms lanes; the HARD FENCE prevents collateral edits to unrelated `local` names.
- Under-scope: none - the constant, both gitignore templates, the comms README, the scaffold mkdir, the uninstall guidance, the AGENTS pointer, the migration guard, the catch-all confirmation, the asserting tests, and an idempotent repo migration are all covered.

## Required tests / validation

The updated `local/`->`untracked/` assertions in tests/test_setup_artifacts.py, tests/test_installer.py:1179, tests/test_comms.py:146, and tests/test_layout_migration.py (LeftoverDispositionTests) plus tools/test_agy_run.py (E-02); a migration proving an existing `local/` lane is renamed to `untracked/` with contents preserved and idempotently (E-02, and the focused E-03 test if taken); and the full serial suite `python3 -m pytest -p no:xdist`. Each V-item pins one E.

## Spec / documentation sync

Update the AGENTS pointer wording (engine.py:949) and the prompts/comms nested-`.gitignore` + comms README templates to say `untracked/` (done in E-01). If any tracked doc under `.aw/records/` or a top-level README references the `local/` prompt/comms lane by name, update that reference to `untracked/` in the same change; otherwise N/A. No spec transition here (the orchestrator advances any owning spec when the Set completes).

## Open questions

### OQ-01: should already-installed repos' `local/` lanes auto-migrate to `untracked/`, or be left in place?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Recommendation - AUTO-MIGRATE through the existing layout-migration path (E-02 step 6), renaming `<records>/prompts|comms/local/` -> `.../untracked/` with contents preserved and idempotently, so installed repos CONVERGE on the new name; surface a one-time notice. A maintainer may prefer leave-in-place with guidance (the migration guard already preserves a residual `local/` lane either way, so no data loss). Non-blocking for the fresh-scaffold rename in E-01.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a fresh scaffold's relevant tree showing `.aw/records/prompts/untracked/` and `.aw/records/comms/untracked/inbox/` exist and NO `local/` lane; paste the prompts + comms nested `.gitignore` contents showing `untracked/`; paste the AGENTS pointer clause (`engine.agents_pointer_block()`) showing `untracked/inbox/`; and paste a grep proving the unrelated names are unchanged, e.g.:
    ```bash
    python3 -c "from agent_workflows import engine; print(engine.PROMPTS_LOCAL_SUBDIR); print(engine._PROMPTS_GITIGNORE_TEMPLATE); print(engine._COMMS_GITIGNORE_TEMPLATE); print('untracked/inbox/' in engine.agents_pointer_block())"
    rg -n "local\.json|local-leaks-allowlist|local-only|LOCAL_GIT|CONFIG_LOCAL" agent_workflows/engine.py agent_workflows/project_schema.py
    ```
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the passing updated test modules and the tail of the full serial suite:
    ```bash
    python3 -m pytest tests/test_setup_artifacts.py tests/test_installer.py tests/test_comms.py tests/test_layout_migration.py tools/test_agy_run.py -p no:xdist -q
    python3 -m pytest -p no:xdist
    ```
    plus a snippet running the migration on a fixture with a populated `local/` lane and printing that the `untracked/` lane now holds the same file contents, the old `local/` lane is gone, and a second run is a no-op.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the focused migration test result (rename + content-preservation + idempotency) and the full serial suite tail:
    ```bash
    python3 -m pytest tests/test_untracked_lane_migration.py -p no:xdist -q
    python3 -m pytest -p no:xdist
    ```
    (If E-03 is not taken, mark this V `n/a` with a one-line rationale - E-02 already exercises the migration.)
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, with opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the files it changed
path-scoped (`git commit -m msg -- <path>`, never `git add -A`), never pushes, and the plan moves to
`.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item is
`pass`. Order 01 of awuntracked (self-contained; no dependent Orders).

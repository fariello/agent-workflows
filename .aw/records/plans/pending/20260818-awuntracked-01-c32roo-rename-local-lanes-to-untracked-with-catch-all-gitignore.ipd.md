# IPD: rename local lanes to untracked with catch-all gitignore

- Date: 2026-08-18
- Kind: child
- Concern: The prompts and comms scaffolding create `local/` lanes (engine.py: PROMPTS_LOCAL_SUBDIR="local" at :3756, COMMS_LOCAL_SUBDIRS at :3769, with gitignore/README templates and scaffold mkdir at :4337-4341) whose sole purpose is to hold untracked, machine-local content. The name `local/` is ambiguous and collides conceptually with other unrelated `local` uses; `untracked/` states the intent plainly. There is already an untracked-safety convention in the codebase (UNTRACKED_SLUG="untracked", UNTRACKED_PATTERNS at engine.py:1206-1207, `ensure_untracked_gitignore` at engine.py:2407) to reuse. Rename the prompts/comms `local/` lanes to `untracked/` and add a catch-all `.gitignore` for any directory named `untracked`. Addresses TODO item #39.
- Scope: IN: rename the prompts/comms `local/` lanes to `untracked/` across engine.py scaffolding, gitignore/README templates, scaffold mkdir, migration preservation (layout_migration.py:429-438), uninstall guidance (engine.py:2383), and the AGENTS pointer (engine.py:949); add a catch-all `.gitignore` for any `untracked/` dir reusing the existing UNTRACKED convention; update the asserting tests and add a migration that renames an existing repo's `local/` lane to `untracked/`. OUT: any unrelated `local` names MUST NOT change - `.aw/config/local.json`, `local-leaks-allowlist.toml`, the `local-only` preset, and the LOCAL_GIT/CONFIG_LOCAL enums are explicitly excluded.
- Status: draft
- Set: awuntracked
- Order: 1
- Highest E allocated: 02
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: c32roo

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): from TODO item #39; rename prompts/comms local/ lanes to untracked/ with a catch-all gitignore, plus a migration and test updates.

## Goal

Rename the prompts and comms `local/` lanes to `untracked/` (a clearer name for their machine-local,
never-committed purpose) with a catch-all `.gitignore` for any `untracked/` dir, and migrate existing
repos - without touching any unrelated `local` names.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: rename lanes + catch-all gitignore

- [ ] E-01 Rename the prompts/comms `local/` lanes to `untracked/` across engine.py scaffolding and templates: PROMPTS_LOCAL_SUBDIR (engine.py:3756), the prompts gitignore template (:3757-3763), COMMS_LOCAL_SUBDIRS (:3769), the comms gitignore/README templates (:3815-3820, :3831/:3837), scaffold mkdir (:4337-4341), uninstall guidance (:2383), the AGENTS pointer (:949), and the migration preservation path (layout_migration.py:429-438); add a catch-all `.gitignore` for any directory named `untracked` by reusing the existing UNTRACKED convention (UNTRACKED_SLUG/UNTRACKED_PATTERNS engine.py:1206-1207, `ensure_untracked_gitignore` engine.py:2407). Do NOT change unrelated `local` names (`.aw/config/local.json`, `local-leaks-allowlist.toml`, the `local-only` preset, LOCAL_GIT/CONFIG_LOCAL enums).
  - Depends on: none
  - Expected outcome: a fresh scaffold creates `untracked/` lanes (not `local/`) under prompts/comms, ignored by the catch-all gitignore; unrelated `local` names are unchanged.
  - Execution state: pending

### Task group 2: tests + repo migration

- [ ] E-02 Update the tests that assert `local/` (test_setup_artifacts.py, test_installer.py:1179, test_comms.py:146, test_layout_migration.py:747-884, tools/agy_run.py) to expect `untracked/`, add a migration that renames an existing repo's prompts/comms `local/` lane to `untracked/` (preserving contents), and run the full serial suite.
  - Depends on: E-01
  - Expected outcome: the updated tests pass, the migration renames an existing `local/` lane to `untracked/` with contents intact, and the full serial suite is green.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The prompts/comms local lanes are defined centrally in engine.py (PROMPTS_LOCAL_SUBDIR :3756, COMMS_LOCAL_SUBDIRS :3769) with paired gitignore/README templates and a scaffold mkdir (:4337-4341); the AGENTS pointer (:949) and uninstall guidance (:2383) reference them.
- An untracked-safety convention already exists: UNTRACKED_SLUG="untracked" / UNTRACKED_PATTERNS (engine.py:1206-1207) and `ensure_untracked_gitignore` (engine.py:2407) - reuse it for the catch-all rather than inventing a new one.
- Migration preserves the local lanes today (layout_migration.py:429-438); the rename must be threaded through that path.
- Several `local` names are UNRELATED to these lanes (`.aw/config/local.json`, `local-leaks-allowlist.toml`, `local-only` preset, LOCAL_GIT/CONFIG_LOCAL enums) and must be left alone.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | The `local/` lanes are defined in a few central engine.py constants/templates. | The rename is concentrated, not scattered; low risk if the constants are the single source. |
| F2 | An UNTRACKED convention already exists. | The catch-all gitignore reuses `ensure_untracked_gitignore`/UNTRACKED_PATTERNS - no new mechanism. |
| F3 | Multiple tests hardcode `local/`. | E-02 must update them in lockstep or the suite breaks. |
| F4 | Other `local` names are unrelated. | The rename must be scoped precisely to the prompts/comms lanes to avoid collateral damage. |

## Proposed changes (ordered, validatable)

1. Rename the prompts/comms `local/` lanes to `untracked/` across engine.py + migration + AGENTS pointer, and add the catch-all `untracked/` gitignore via the existing UNTRACKED convention (E-01). 2. Update the asserting tests, add a repo migration for existing `local/` lanes, and run the full suite (E-02).

## Deferred / out of scope (with reason)

- Renaming any unrelated `local` name (`.aw/config/local.json`, `local-leaks-allowlist.toml`, `local-only` preset, LOCAL_GIT/CONFIG_LOCAL enums): explicitly excluded - different meaning.
- Broader gitignore policy changes beyond the catch-all `untracked/` rule: out of scope.

## Scope check

- Over-scope: none - the rename is scoped strictly to the prompts/comms lanes.
- Under-scope: none - scaffolding, templates, migration, catch-all gitignore, tests, and a repo migration are all covered.

## Required tests / validation

The updated `local/`->`untracked/` assertions (E-02), a migration test proving an existing `local/` lane is renamed with contents preserved, and the full serial suite.

## Spec / documentation sync

Update the AGENTS pointer wording (engine.py:949) and any comms/prompts README templates to say `untracked/`; note the rename in the relevant docs if referenced. Otherwise N/A.

## Open questions

### OQ-01: should already-installed repos have their `local/` lane auto-migrated to `untracked/`, or left in place with a one-time notice?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Recommendation: auto-migrate through the existing layout-migration path (preserving contents) so installed repos converge, but surface a one-time notice; a maintainer may prefer leave-in-place with guidance. Non-blocking for the fresh-scaffold rename.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a fresh scaffold's tree showing `untracked/` lanes under prompts/comms (no `local/`), the catch-all `untracked/` gitignore, and a grep confirming the unrelated `local` names (local.json, local-leaks-allowlist.toml, local-only preset, LOCAL_GIT/CONFIG_LOCAL) are unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the passing updated tests, the migration run renaming an existing `local/` lane to `untracked/` with contents preserved, and the tail of the full serial suite.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The executor
(opencode Opus 4.8, or Gemini via `agy` with opencode owning verification and commits) performs each E,
verifies each V with pasted evidence, commits path-scoped, never pushes, and transitions the plan into
`executed/` only after `aw ipd lint --phase pre-transition` conforms and every V is `pass`.

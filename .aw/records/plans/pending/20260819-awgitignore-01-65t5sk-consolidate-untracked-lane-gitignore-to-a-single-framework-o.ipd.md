# IPD: consolidate untracked-lane gitignore to a single framework-owned .aw/.gitignore

- Date: 2026-08-19
- Kind: child
- Concern: The `untracked/` quarantine lanes are ignored by TWO nested per-lane files (`.aw/records/comms/.gitignore`, `.aw/records/prompts/.gitignore`), scattered + duplicated + needing `_ensure_untracked_gitignore` upkeep. The stated reason for nesting ("not a root .gitignore edit") conflated the USER's `repo/.gitignore` (which the framework must not touch) with `repo/.aw/.gitignore` (INSIDE the framework-owned `.aw/` tree - entirely ours, the whole point of the `.agents/`->`.aw/` rename). `.aw/` is framework-exclusive, so a single owned `.aw/.gitignore` is the clean design.
- Scope: `agent_workflows/engine.py` (replace the two nested-gitignore deliverables + `_ensure_untracked_gitignore` with a single `.aw/.gitignore` deliverable + writer); the comms-convention spec `20260715-1722-01` (rewrite the nested-gitignore prescription to the consolidated file); the affected tests; migrate THIS repo. Nothing has shipped since before the `.aw/` migration, so there is NO compatibility burden - do the right thing and rewrite the spec to match (do not preserve the nested design for users who do not exist).
- Status: approved
- Set: awgitignore
- Order: 1
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 65t5sk
- Approval: maintainer (human), 2026-08-19: approved this specific plan and said execute now.

## Workflow history

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created - `.aw/` is framework-owned (unlike the shared `.agents/`), so the two nested per-lane `.gitignore`s consolidate into one `.aw/.gitignore` (`records/*/untracked/`). Nothing shipped since pre-`.aw/`, so the comms spec is rewritten, not preserved.
- 2026-08-19 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): reviewed - verified `.aw/` is the exclusive framework namespace (spec 20260810-1447-01:19), the root-gitignore rule is about repo/.gitignore not repo/.aw/.gitignore, `.aw/.gitignore` with records/*/untracked/ ignores both lanes (git check-ignore), scaffold deliverable sites (engine.py:4321/4324), and nothing shipped since pre-.aw/. Verdict: GO - PENDING HUMAN APPROVAL. Awaiting explicit human approval.
- 2026-08-19 approved (maintainer, human): explicitly approved this plan and instructed execute now.

## Goal

Replace the two nested per-lane `.gitignore` files with ONE framework-owned `repo/.aw/.gitignore` (pattern `records/*/untracked/`) that ignores every records `untracked/` lane, since `.aw/` is exclusively ours. Retire the per-lane templates + the `_ensure_untracked_gitignore` upkeep, rewrite the comms-convention spec to describe the consolidated file, and migrate this repo. The legacy `.agents/` lanes keep their nested `.gitignore` (a `.agents/.gitignore` WOULD touch the shared `.agents/` namespace, and `.agents/` is pre-release litter anyway).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: the consolidated .aw/.gitignore

- [ ] E-01 In `agent_workflows/engine.py`, add a single `.aw/.gitignore` deliverable + template. Add `_AW_GITIGNORE_TEMPLATE` (a `#`-comment header explaining it ignores the box-local quarantine lanes + the line `records/*/untracked/`), a `AW_GITIGNORE_PATH = ".aw/.gitignore"` const, and in the scaffold file-list (engine.py:4321-4324) REPLACE the two `files.append((f"{dirs['prompts']}/.gitignore", ...))` / `({dirs['comms']}/.gitignore, ...)` deliverables with ONE `files.append((".aw/.gitignore", _AW_GITIGNORE_TEMPLATE))` - but ONLY when the resolved layout is the canonical `.aw/` one (a legacy `.agents/`-layout install keeps the nested per-lane files, since `.agents/` is shared). Guard on `dirs['comms'].startswith(".aw/")` (or the resolved-layout flag). Keep `_COMMS_GITIGNORE_TEMPLATE`/`_PROMPTS_GITIGNORE_TEMPLATE` ONLY for the legacy `.agents/` branch.
  - Depends on: none
  - Expected outcome: a fresh `.aw/`-layout install writes `repo/.aw/.gitignore` containing `records/*/untracked/` and NO `.aw/records/{comms,prompts}/.gitignore`; a legacy `.agents/` install still writes the nested files.
  - Execution state: pending

### Task group 2: migration writer + retire per-lane upkeep

- [ ] E-02 Rework `migrate_local_lanes_to_untracked` / `_ensure_untracked_gitignore` (awuntrackedfix Order 01) so the CANONICAL `.aw/` bases no longer get a per-lane `.gitignore`; instead ensure the single `repo/.aw/.gitignore` exists with `records/*/untracked/` (create it if absent; add the line if a `.aw/.gitignore` exists without it). LEGACY `.agents/` bases keep the per-lane `_ensure_untracked_gitignore` behavior. Also DELETE a now-redundant nested `.aw/records/{comms,prompts}/.gitignore` if present (superseded by the consolidated file) so a migrated repo does not carry both. The lane RENAME logic (local->untracked, recursive merge, both layouts) is unchanged.
  - Depends on: E-01
  - Expected outcome: running the migration on an `.aw/` repo yields a single `.aw/.gitignore` (with `records/*/untracked/`) and removes any stale nested `.aw/records/*/​.gitignore`; a `.agents/` lane keeps its nested file; idempotent.
  - Execution state: pending

### Task group 3: spec + tests + this repo

- [ ] E-03 Rewrite the nested-gitignore prescription in the comms-convention spec `.aw/records/specs/20260715-1722-01-agent-comms-convention.spec.md` (the `.gitignore  # nested; ignores local/` line ~28 and any prose) to describe the CONSOLIDATED design: the canonical `.aw/` layout ignores lanes via a single framework-owned `repo/.aw/.gitignore` (`records/*/untracked/`); nested per-lane `.gitignore` remains only for the legacy shared `.agents/` layout. Note in the spec's history that nothing had shipped, so this supersedes (not migrates) the earlier nested-only design. Keep the spec's `local/`->`untracked/` naming already reconciled by awuntracked-01.
  - Depends on: E-01
  - Expected outcome: the comms spec describes the single `.aw/.gitignore` for the owned layout; `aw specs check` conforms.
  - Execution state: pending

- [ ] E-04 (a) Migrate THIS repo: ensure `repo/.aw/.gitignore` exists with `records/*/untracked/`, delete the two now-redundant `.aw/records/{comms,prompts}/.gitignore`, and verify `git check-ignore` still ignores both `untracked/` lanes via the single file (the `.agents/` nested files stay). (b) Update the tests that assert the nested `.aw/records/*/​.gitignore` (test_setup_artifacts, test_comms, test_installer, test_untracked_lane_both_layouts, test_untracked_lane_migration) to the consolidated `.aw/.gitignore` expectation for the `.aw/` layout, keeping the legacy-`.agents/` nested assertions. Add a case asserting `records/*/untracked/` in `.aw/.gitignore` ignores a comms AND a prompts lane. (c) Build the wheel, pip-install into a throwaway repo, run `aw normalize-lanes` (+ a fresh `aw install`), and paste evidence that a single `.aw/.gitignore` is produced and ignores both lanes with no `tools` import error. Run the FULL serial suite and paste the tail.
  - Depends on: E-01,E-02,E-03
  - Expected outcome: this repo has ONE `.aw/.gitignore` (no nested `.aw/records/*/​.gitignore`); updated tests pass; installed-wheel evidence pasted; full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `.aw/` is the framework's EXCLUSIVE canonical namespace (migration spec `20260810-1447-01`:19); the `.agents/`->`.aw/` rename was done precisely because `.agents/` is shared with other tools and `.aw/` is not.
- The "installer does not touch the root .gitignore" rule (engine.py:4290, comms spec:28) is about the USER's `repo/.gitignore` (+ the `aw:untracked` managed block at engine.py:2408) - it does NOT apply to `repo/.aw/.gitignore`, which is inside the owned tree.
- Nested gitignores are scaffold deliverables (engine.py:4321/4324) + upkept by `_ensure_untracked_gitignore` (awuntrackedfix Order 01). Verified: `.aw/.gitignore` with `records/*/untracked/` correctly ignores `.aw/records/comms/untracked/...` and `.aw/records/prompts/untracked/...` (git check-ignore).
- Nothing has shipped since before the `.aw/` migration (last release v1.2.0 / v1.3.0-rc.1 both predate awphysical, Aug 10), so there is NO installed base or compatibility burden; the comms spec is rewritten, not preserved.

## Findings

The nested-per-lane `.gitignore` was justified by a rule that does not apply to the owned `.aw/` tree. Consolidating to one `repo/.aw/.gitignore` is simpler and correct. Legacy `.agents/` keeps nested files (shared namespace + litter).

## Proposed changes (ordered, validatable)

1. Single `.aw/.gitignore` deliverable/template for the `.aw/` layout.
2. Migration ensures the single file + removes stale nested ones (`.aw/` only); `.agents/` keeps nested.
3. Rewrite the comms spec.
4. Migrate this repo + update tests + installed-wheel proof.

## Deferred / out of scope (with reason)

- Removing the legacy `.agents/` tree entirely: backlog wxz7gg.
- Fixing `aw migrate-layout` being dead when installed: backlog revnjq (PR-003).

## Scope check

- Over-scope: none.
- Under-scope: does not consolidate the `.agents/` layout (deliberate - shared namespace + litter).

## Required tests / validation

Updated scaffold/comms/installer/lane tests assert the single `.aw/.gitignore` (`.aw/` layout) + nested for `.agents/`; `aw specs check` conforms; installed-wheel proof; full serial suite green.

## Spec / documentation sync

REQUIRED: rewrite the nested-gitignore prescription in comms-convention spec `20260715-1722-01` (E-03).

## Open questions

### OQ-01: scope of the consolidated pattern - `.aw/.gitignore` with `records/*/untracked/`

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Use `repo/.aw/.gitignore` (owned root, room for future lanes anywhere under `.aw/`) with an EXPLICIT `records/*/untracked/` pattern (not a blanket ignore), per the maintainer's steer toward the owned-root single file. No open decision.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a fresh `.aw/`-layout scaffold writes `repo/.aw/.gitignore` containing `records/*/untracked/` and NO `.aw/records/{comms,prompts}/.gitignore`; a legacy `.agents/` scaffold still writes the nested files. Shown by the updated scaffold tests.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the migration on an `.aw/` repo produces a single `.aw/.gitignore` (with the pattern) and removes any stale nested `.aw/records/*/​.gitignore`; a `.agents/` lane keeps its nested file; second run is a no-op. Shown by the new/updated lane tests.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the comms spec `20260715-1722-01` describes the single `.aw/.gitignore` design (quote the revised line); `aw specs check` exits 0.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: (i) THIS repo has one `.aw/.gitignore` (`records/*/untracked/`) and no `.aw/records/{comms,prompts}/.gitignore`; `git check-ignore` ignores both lanes via it; (ii) updated tests pass; (iii) INSTALLED-WHEEL proof - build, pip install, `aw normalize-lanes` + fresh `aw install` produce the single `.aw/.gitignore` ignoring both lanes, no `tools` error (pasted); (iv) full serial suite tail pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files changed by this plan, path-scoped, never push. The lane dirs are untracked; the `.aw/.gitignore` + spec + tests are the tracked changes. Run the full serial suite and paste the actual runner output as V evidence. On completion, lint `--phase pre-transition` while still approved, then flip Status to executed, add an executed workflow-history line, `git mv` to `.aw/records/plans/executed/`, and lint `--phase post-transition`. Do not mark executed until every V item is verified with concrete evidence.

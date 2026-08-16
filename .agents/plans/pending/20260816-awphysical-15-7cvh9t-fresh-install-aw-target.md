# IPD: Fresh install targets the physical .aw/ layout with legacy .agents auto-detect and offered migration

- Date: 2026-08-16
- Kind: child
- Concern: The installer writes the LEGACY layout into every target: `engine.WORKFLOWS_DIR = ".agents/workflows"` is the hardcoded install root, and shims/pointer/README paths derive from it. So `aw install` into a clean repo produces `.agents/workflows/`, never `.aw/`. The physical-.aw release requires a FRESH install to create ONLY the `.aw/` hierarchy (canonical system at `.aw/system/`, records/config/state per preset), while an existing `.agents/`-only repo running install/update must not break: it is detected and OFFERED migration, and declining keeps updating the legacy layout in place for the compatibility window with a deprecation notice (spec 20260810-1447-01 S11.3 + S13 acceptance criteria; end-state point #1).
- Scope: `agent_workflows/engine.py` install write paths (the workflow-bundle target, `WORKFLOWS_DIR` usage, `install_into_repo`/`install_all`/`collect_target_framework_files`/`prune_stale`, `migrate_legacy_layout`, the AGENTS pointer + shim + README ensurers as they reference the bundle root), `agent_workflows/_compat.py`/`project_context` for the resolved TARGET system root, the `install`/`update` CLI surface in `agent_workflows/cli.py`, and the installer tests (`tests/test_installer.py`, `tests/test_cli.py`). Does NOT change the migration engine (Order 14 hnzr8v owns move-not-copy), the resolver/packaging (xzuxet), or workflow bodies.
- Status: reviewed
- Set: awphysical
- Order: 15
- Highest E allocated: 04
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 7cvh9t

## Workflow history

- 2026-08-16 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created after verifying the fresh-install gap against the code (WORKFLOWS_DIR hardcoded to .agents/workflows) and the pending Set (no Order converts fresh installs to .aw/). Maintainer ruled the compatibility story: fresh install = .aw/ only; a legacy .agents/-only repo is auto-detected on install/update and OFFERED migration; declining keeps updating .agents/ in place for the compat window with a deprecation notice; readers support both. Traces to spec S11.3 install-target contract + S13 acceptance criteria.
- 2026-08-16 /plan-review (Gemini, via maintainer relay; findings evaluated on the merits by opencode Opus 4.8): REVIEWED - OPEN QUESTIONS (APPROVE verdict, but OQ-01 remains a human decision). Findings applied: PR-001 (MEDIUM, accepted + verified) - strengthened E-02 so GENERATED content reflects the resolved layout: `shim_body`'s `Read and execute @{workflow.body}` and `agents_pointer_prose`'s hardcoded `.agents/workflows/`/`.agents/docs/research/` must be rewritten to the `.aw/system/workflows/` bundle paths under an aw target (else shims/pointer reference a non-existent legacy path); E-04 now asserts shim+pointer paths. PR-003 (accepted) - E-02 rule made deterministic: `.aw/system` present is AUTHORITATIVE (no prompt) even with a stray legacy tree; E-04 tests it. PR-002 (partially accepted, CORRECTED) - installer-backup relocation deferred as an installer follow-up; Gemini's proposed `.aw/system/installer-backups/` is wrong per spec S6 (system is replaced on update), correct home is `.aw/state/` (classifier maps installer-backups -> durable_state). PR-004/OQ-01 - Gemini concurs with the keep-legacy non-interactive default; left OPEN for explicit maintainer confirmation. Status draft -> reviewed. NO-GO pending OQ-01 + human approval + Order 14 terminal.

## Goal

A fresh `aw install`/`aw setup` into a repository with no prior AW layout creates ONLY the physical `.aw/` hierarchy: the canonical workflow bundle at `.aw/system/workflows/` (with VERSION/manifest siblings at `.aw/system/`), and records/config/state at the resolved preset roots. It never creates a legacy `.agents/workflows/` tree in a fresh target. When install/update runs in a repository that already has a legacy `.agents/`-only layout, the tool detects it and offers to migrate to `.aw/` (delegating to the Order-14 migration tool); if the operator declines, it continues to update the legacy layout in place for the documented compatibility window, emitting the deprecation notice, and never creates a second divergent layout. Readers resolve either layout during the window.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Resolve the target install root instead of hardcoding legacy

- [ ] E-02 Introduce a resolved TARGET install-root concept so the installer no longer hardcodes `.agents/workflows`. Add a function (e.g. `resolve_target_layout(repo_root)`) that returns the layout the install/update should write for THIS target with a DETERMINISTIC rule: if `.aw/system` is present the layout is `aw` and it is AUTHORITATIVE (no migration prompt) even if a legacy `.agents/workflows` also exists (e.g. from an interrupted manual action; PR-003); a fresh repo (neither present) is `aw`; a repo with ONLY the legacy tree that has not opted to migrate is `legacy`. Thread the resolved bundle-root + records-root through `install_into_repo`/`install_all`/`collect_source_members` mapping/`collect_target_framework_files`/`prune_stale`, replacing bare `WORKFLOWS_DIR` uses with the resolved root. Keep `WORKFLOWS_DIR` as the LEGACY constant only. The prune/collect sets MUST be computed against the SAME resolved root so install and prune cannot diverge. CRUCIALLY, the GENERATED CONTENT must also reflect the resolved layout (PR-001): `shim_body` emits `Read and execute @{workflow.body}` where the manifest body paths are `.agents/workflows/...`, and `agents_pointer_prose` hardcodes `.agents/workflows/` + `.agents/docs/research/` etc.; under an `aw` target these must be rewritten to the resolved `.aw/system/workflows/` (and `.aw/records/...`) bundle paths, or a generated shim/pointer will reference a non-existent legacy path. Parameterize the shim `@`-body path and the pointer prose on the resolved layout (map the manifest body prefix to the resolved bundle root).
  - Depends on: none
  - Expected outcome: a fresh install writes `.aw/system/workflows/index.md` (+ the `.aw/` records/config/state per preset) and NO `.agents/workflows/`; an existing `.aw/` repo updates `.aw/` (and is treated as authoritative even if a stray legacy tree exists); an existing legacy-only repo (pre-migration) still updates `.agents/workflows/` when the user declines migration; generated shims (`Read and execute @...`) and the AGENTS.md pointer reference the RESOLVED bundle path, not a hardcoded legacy path.
  - Execution state: pending

### Task group 2: Legacy auto-detect and offered migration

- [ ] E-03 On `aw install`/`aw update`/`aw setup`, detect a legacy `.agents/`-only layout (legacy bundle present AND no `.aw/system`) and, interactively, OFFER to migrate to `.aw/` by delegating to the Order-14 `migrate-layout` tool (never a bespoke path). If accepted, run the migration (move) then complete the install against `.aw/`. If declined (or non-interactive without an opt-in flag), continue updating the legacy `.agents/` layout in place and emit a one-time DEPRECATION notice naming the compatibility-window removal release. Never create a second divergent layout (both `.agents/workflows/` and `.aw/system/workflows/` freshly written in the same run). Provide non-interactive flags (`--to-aw` / `--keep-legacy`) so CI is deterministic.
  - Depends on: E-02
  - Expected outcome: a legacy-only repo running install/update is detected, offered migration, and either migrated (ends `.aw/`-only) or kept legacy with a deprecation notice; a fresh repo is never prompted; no run produces both layouts.
  - Execution state: pending

### Task group 3: Lock it with tests

- [ ] E-04 Add/adjust falsifiable installer tests: a fresh install into a clean git repo creates `.aw/system/workflows/index.md` and NO `.agents/workflows/` (mutation: reverting the resolved root to the hardcoded legacy constant makes the "no `.agents/workflows/`" assertion RED); a fresh install's GENERATED shims (`.opencode/commands/*.md`, `.claude/commands/*.md`) and AGENTS.md pointer reference `.aw/system/workflows/` (NOT `.agents/workflows/`) (PR-001; falsifiable: assert the shim `@`-path + pointer text resolve to the aw bundle); a repo with BOTH `.aw/system` and a stray `.agents/workflows` is treated as `aw` and NOT prompted (PR-003); an `.aw/`-present repo updates `.aw/`; a legacy-only repo with `--keep-legacy` still updates `.agents/workflows/` (with legacy shim/pointer paths) and prints the deprecation notice; a legacy-only repo with `--to-aw` ends `.aw/`-only via the migration tool with the legacy sources moved (not duplicated). Update `tests/test_installer.py` + `tests/test_cli.py`; the existing `test_fresh_install` (which asserts `.agents/workflows/`) is updated to the new fresh-install target (or split: fresh->`.aw/`, legacy-keep->`.agents/`). Full suite green.
  - Depends on: E-02, E-03
  - Expected outcome: the installer's fresh-vs-legacy behavior is pinned by tests that fail if a fresh install writes legacy or if a legacy repo is silently dual-written.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `engine.WORKFLOWS_DIR = ".agents/workflows"` (:82) is the single hardcoded install target; `INDEX_FILE`, `collect_source_members` member prefix (`{WORKFLOWS_DIR}/rel`), `collect_target_framework_files`, `prune_stale`, and the shim/pointer/README ensurers all derive from it. The E-04 (xzuxet) fix deliberately ships VERSION to the LEGACY target during the compat window, so the installer already assumes legacy output.
- The resolver (`resolve_source_root`) already prefers `.aw/system` for the SOURCE; the packaged wheel ships the nested `.aw/system` bundle (xzuxet E-02). This IPD is about the TARGET write layout, the mirror of that.
- `is_source_checkout` and `project_context` already resolve `.aw/system`/`.aw/records` for a target that HAS `.aw/`; the gap is only the fresh-install WRITE path and the legacy auto-detect.
- The Order-14 migration tool (`aw migrate-layout`, hnzr8v) is the supported mover; the offered-migration path delegates to it rather than re-implementing a move.

## Findings

- No pending awphysical Order converts the fresh-install write path to `.aw/`; Order 11 migrates THIS repo, Order 12 is docs/release, xzuxet is source-resolver/packaging. Confirmed by grep over `.agents/plans/pending/`.
- Because readers already resolve both layouts, the risk is confined to the WRITE path + the auto-detect UX; there is no reader rework here.

## Proposed changes (ordered, validatable)

1. Resolve the target install root (aw vs legacy) and thread it through the install/prune paths, keeping WORKFLOWS_DIR as the legacy constant only.
2. Detect legacy-only repos on install/update and offer migration (delegating to migrate-layout); non-interactive flags `--to-aw`/`--keep-legacy`; deprecation notice on keep-legacy; never dual-write.
3. Tests pinning fresh->.aw/, aw-present->.aw/, legacy-keep->.agents/ + notice, legacy-to-aw->migrated, with a mutation probe.

## Deferred / out of scope (with reason)

- The move mechanics + interactive leftover disposition are Order 14 (hnzr8v); this IPD only DELEGATES to that tool for the offered migration.
- The guided migration WIZARD front-end is Order 16 (88bnw0).
- Removing legacy `.agents/` support entirely (end of the compatibility window) is a later, separately gated deprecation-removal step, not this IPD.
- Relocating the installer backup dir (`.agent-workflows-installer-backups/` at repo root) for `.aw/` targets (Gemini PR-002) is DEFERRED as an installer-behavior follow-up, not part of "fresh install writes .aw/". Note: Gemini proposed `.aw/system/installer-backups/`, but that is WRONG per spec S6 - `system/` is CLI-owned content REPLACED on update; mutable backup snapshots are `durable_state` (the classifier already maps `installer-backups -> durable_state`), so the correct home is under `.aw/state/`. Tracked as a backlog item, not a blocker here.

## Scope check

- Over-scope: none; confined to the installer target-layout write path, the legacy auto-detect/offer, and installer tests.
- Under-scope: the resolved target root, the fresh-vs-legacy branch, the offer-migration delegation, the non-interactive flags, the deprecation notice, and the pinning tests are all included.

## Required tests / validation

- `python3 -m unittest tests.test_installer tests.test_cli`
- A disposable-clone check: fresh `aw install` yields `.aw/` only (no `.agents/workflows/`); a legacy repo is offered migration and, per choice, ends `.aw/`-only or keeps legacy + notice.
- `python3 -m unittest discover -s tests -t .` (full serial suite)
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`

## Spec / documentation sync

- Trace to spec 20260810-1447-01 S11.3 install-target contract + S13 acceptance criteria (already recorded). Update the installer/setup CLI help and any getting-started/README text that says installs create `.agents/workflows/` to describe the `.aw/` fresh-install target + the legacy auto-detect/offer + deprecation window. Record in DECISIONS.

## Open questions

### OQ-01: Non-interactive default when a legacy-only repo runs `aw update` without --to-aw/--keep-legacy

- Blocking: no
- Status: open
- Owner: human maintainer
- Resolution or deferral rationale: In a genuinely non-interactive run on a legacy-only repo with neither flag, the safe default is KEEP-LEGACY + deprecation notice (never auto-migrate without consent, never block CI). Confirm this is the intended default, or specify that non-interactive update on a legacy repo should refuse until a flag is given.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-02 validates E-02
  - Required evidence: On a disposable clone, `aw install` into a CLEAN git repo; paste the tree proving `.aw/system/workflows/index.md` exists and `.agents/workflows/` does NOT. Mutation: reverting the resolved root to the hardcoded legacy constant makes the "no `.agents/workflows/`" assertion RED, then GREEN when restored.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: On a legacy-only fixture repo, show install/update DETECTS legacy and offers migration; with `--to-aw` it ends `.aw/`-only (legacy sources moved via the migration tool, not duplicated); with `--keep-legacy` it updates `.agents/workflows/` and prints the deprecation notice; a fresh repo is never prompted; no run writes BOTH layouts.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Paste the full serial suite + `tests.test_installer`/`tests.test_cli` result (all green) with the fresh-vs-legacy tests, including the mutation probe RED-then-GREEN.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: One coherent change to the installer's target-layout decision (fresh -> `.aw/`; legacy -> detect + offer migration) plus the tests that pin it.

Execution requires human approval recorded as `Status: approved` + an attributed `- Approval:` line, and depends on Order 14 (hnzr8v, the migration tool the offer delegates to) being terminal. The executor implements the E-items, pastes actual command output (including the mutation probe and a disposable-clone fresh install + legacy-repo offer), commits only the explicitly scoped paths, never pushes, runs `aw ipd lint --phase pre-transition --agent` and the full serial suite before any transition, and the orchestrator owns the terminal move to `executed/`.

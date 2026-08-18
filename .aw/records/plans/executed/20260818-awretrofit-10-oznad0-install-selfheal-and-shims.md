# IPD: Fix aw install: workflow-artifacts README git-add on a gitignored path + regenerate stale host shims

- Date: 2026-08-18
- Kind: child
- Concern: Discovered executing Order 09 (2026-08-18): `aw install .` on this repo is BROKEN and leaves stale host shims. (1) `ensure_workflow_artifacts_readme` (engine.py:4082) writes `workflow-artifacts/README.md` and the install `git add`s it, but `workflow-artifacts/` is gitignored -> the whole install FAILS ("The following paths are ignored... Use -f"). (2) 42 host shims (21 `.claude/commands/*` + 21 `.opencode/commands/*`) still say `Read and execute @.agents/workflows/...` - never regenerated after the migration; a fresh `aw install` would fix them but currently can't (it fails at (1)).
- Scope: (a) Make the installer tolerant when its `git add` target is gitignored - skip/soft-warn instead of failing the whole install (a gitignored `workflow-artifacts/` is a legitimate config, and the migration deliberately gitignores run scratch). (b) Regenerate the 42 stale `.claude`/`.opencode` command shims to `.aw/system/workflows/...`. This UNBLOCKS Order 09 (manifest regen via a now-working `aw install .`). OUT: the managed-sections manifest rekey itself (Order 09).
- Status: executed
- Set: awretrofit
- Order: 10
- Highest E allocated: 03
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: oznad0

## Workflow history

- 2026-08-18 authored (opencode Opus 4.8): created after Order 09 hit a broken `aw install .` (git-add of a gitignored path) + found 42 stale host shims. Unblocks Order 09.
- 2026-08-18 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. PR-001: `git_add_optional` (engine.py:1456) already does skip-when-ignored + is used by sibling ensurers; :4110 is the lone raw outlier, so E-01 is a one-line swap. GO - PENDING HUMAN APPROVAL.
- 2026-08-18 executed (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): human approved. Implemented E-01 (ensure_workflow_artifacts_readme -> git_add_optional, engine.py) + E-02 (regenerated 42 .claude/.opencode shims to @.aw/system/workflows via a now-completing `aw install .`) + E-03 (tests/test_awretrofit_install_selfheal.py + fixed test_plan_review_parity shim assertion) in commit 8ab840d. V-01..V-03 verified (install completes; shims 0 legacy; mutation RED->GREEN; full serial suite 1011 passed / 1 skipped; sanitize+attention clean). During execution the install auto-committed a broad sync (shims + a DUAL-keyed manifest); I soft-reset it, kept ONLY the shims + E-01 fix path-scoped, and reverted the manifest (aw install ACCUMULATES keys, does not prune - recorded as a finding on Order 09). pre-transition lint conforming; moved pending -> executed/. Order 09 unblocked (with the new purge-not-just-install caveat).

## Goal

Make `aw install`/update succeed on a repo that gitignores `workflow-artifacts/` (don't fail the whole
install trying to `git add` a gitignored deliverable), and bring the 42 stale `.claude`/`.opencode`
command shims onto the `.aw/system/workflows/` paths - so a self-install runs clean and Order 09 can
rekey the manifest.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: install tolerates a gitignored git-add target (the failure)

- [x] E-01 Fix `ensure_workflow_artifacts_readme` to stage via the EXISTING `git_add_optional` helper instead of the raw `git_run(plan.repo_root, ["add", "--", rel_path])` (engine.py:4110). **plan-review PR-001 (verified):** the fix is a one-line swap, NOT a new check-ignore path - `git_add_optional` (engine.py:1456) ALREADY does exactly the desired thing ("stage a path, tolerating the case where it is ignored by .gitignore... warn once and continue rather than aborting; any OTHER git failure is a real error and is raised"), and the sibling README ensurers (`ensure_plans/docs/prompts_readmes`, :4165/4217/4261) ALREADY use it - line 4110 is the lone outlier that used raw `git_run(add)` and therefore aborts on a gitignored `workflow-artifacts/`. Audit the other raw `git_run(add)` sites (engine.py:2105/2144/2226/2316/2441/3008) and confirm they add paths that are NOT gitignorable deliverables (`.gitignore` itself, native host-adapter files, backups) - they are intentionally raw; only 4110 hit the hazard. The README is still WRITTEN; it is just not staged when ignored. Do NOT `-f` force-add.
  - Depends on: none
  - Expected outcome: `aw install .` on this repo (which gitignores `workflow-artifacts/` + `.aw/workflow-artifacts/`) RUNS TO COMPLETION via `git_add_optional`'s skip-when-ignored; an ignored README is written-but-not-staged, not a fatal error.
  - Execution state: performed

### Task group 2: regenerate the stale host shims

- [x] E-02 Regenerate the 42 stale command shims (21 `.claude/commands/*` + 21 `.opencode/commands/*`) that still say `Read and execute @.agents/workflows/...` so they reference `@.aw/system/workflows/...`, via the installer's shim generation (now that E-01 lets `aw install .` complete) - NOT a hand-edit. Verify no shim still references `.agents/workflows/`.
  - Depends on: E-01
  - Expected outcome: `grep -rl "\.agents/workflows" .claude/commands .opencode/commands` -> empty; shims resolve the real installed bundle path.
  - Execution state: performed

### Task group 3: tests + verify

- [x] E-03 Add a regression test: `aw install`/`create_setup_artifacts`+ensurers on a repo that gitignores `workflow-artifacts/` completes without error and does not stage the ignored README (fails against the pre-fix code). Then run a clean `aw install .` on this repo and confirm it completes; commit ONLY the shim regeneration (`.claude/commands/*`, `.opencode/commands/*`) + the E-01 code + test, path-scoped (handle any other install side-effects explicitly, do not bundle an unexplained broad rewrite).
  - Depends on: E-01, E-02
  - Expected outcome: new test green (fail-before/pass-after); `aw install .` completes; shims regenerated; full serial suite >= 1009 passed / 1 skipped; sanitize + attention clean.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The `workflow-artifacts/` README template asserts "DO NOT gitignore this folder", but Order 07 (spec 20260817-2124-01) deliberately gitignores run scratch (`.aw/workflow-artifacts/` + repo-root `workflow-artifacts/`). So the installer must TOLERATE a gitignored target, not force it tracked - the design says run scratch is ephemeral/untracked.
- Command shims are GENERATED from the workflow manifest during install (never hand-maintained); regenerate via the installer.
- Firm rule: the installer must not `-f` force-add against the user's gitignore.
- `git_add_optional` (engine.py:1456) is the CANONICAL skip-when-ignored staging helper (it warns once + continues, raising only on non-ignore git failures); the fix is to route the one raw-add outlier (4110) through it, matching the sibling ensurers - not to invent new tolerance logic.

## Findings

| id | area | evidence | issue |
|---|---|---|---|
| INST01 | install failure | engine.py:4110 ensure_workflow_artifacts_readme uses raw `git_run(add)` on gitignored workflow-artifacts/README.md | `aw install .` aborts on a repo that gitignores workflow-artifacts/ |
| SHIM01 | stale host shims | 21 .claude/commands/* + 21 .opencode/commands/* say `@.agents/workflows/...` | never regenerated post-migration; shims point at a vanished path |
| PR-001 | plan-review (fix simplification) | `git_add_optional` already exists (engine.py:1456) + is used by the sibling README ensurers (:4165/4217/4261); 4110 is the lone raw-add outlier | E-01 is a one-line swap to `git_add_optional`, not a new check-ignore mechanism. FIXED in E-01. |

## Proposed changes (ordered, validatable)

1. E-01 make install `git add` tolerant of a gitignored target (skip + soft note, no `-f`).
2. E-02 regenerate the 42 stale shims via the (now-working) installer.
3. E-03 regression test + clean `aw install .` + path-scoped commit.

## Deferred / out of scope (with reason)

- managed-sections.json manifest rekey (Order 09 - this Order unblocks it).
- The broader workflow-artifacts-should-be-tracked-vs-ignored design question: settled by Order 07 (ignored); this Order just stops the installer from choking on it.

## Scope check

- Over-scope: none - both findings block/degrade a real `aw install` on a migrated repo.
- Under-scope: none - E-01 audits ALL installer git-add sites for the same gitignore hazard, not just the one that failed.

## Required tests / validation

- `aw install .` on this repo (gitignores workflow-artifacts/) COMPLETES; regression test fails against pre-fix.
- `grep -rl "\.agents/workflows" .claude/commands .opencode/commands` -> empty.
- Full serial suite >= 1009 passed / 1 skipped; `aw sanitize --agent` + `aw attention --check` clean.

## Spec / documentation sync

- None; installer behavior + generated shims only. No spec status change.

## Open questions

### OQ-01: Skip-when-ignored vs force-track the workflow-artifacts README?

- Blocking: no
- Status: resolved
- Owner: opencode Opus 4.8
- Resolution or deferral rationale: SKIP-when-ignored (write the file on disk, do not stage it, soft
  note). Order 07 settled that run scratch is gitignored; force-tracking (`-f`) would fight the
  framework's own gitignore and re-introduce the churn. The README-template's "DO NOT gitignore"
  wording is advisory for a TARGET repo that wants tracked run records; a repo that DOES ignore it
  must not have its install broken.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: `aw install .` on this repo (gitignores workflow-artifacts/) COMPLETES (exit 0, no "paths are ignored" abort); a regression test shows install/ensurers succeed on a gitignored-workflow-artifacts repo and the ignored README is written-but-not-staged; the test FAILS against the pre-fix code. Paste.
  - Observed evidence: Swapped the raw `git_run(add)` at engine.py:4110 for `git_add_optional`. `aw install .` RAN TO COMPLETION this turn (previously it aborted at ensure_workflow_artifacts_readme with "The following paths are ignored... Use -f"). `tests/test_awretrofit_install_selfheal.py`: `test_ensure_workflow_artifacts_readme_survives_gitignored_dir` (README written, NOT staged) + `test_git_add_optional_returns_false_on_ignored` pass. Mutation: reverting to raw `git add` -> the survives-gitignored test `1 failed`; restored -> 2 passed.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `grep -rl "\.agents/workflows" .claude/commands .opencode/commands` -> empty; a shim references `@.aw/system/workflows/...`. Paste a sample + the grep.
  - Observed evidence: `aw install .` regenerated all 42 shims (21 .claude + 21 .opencode). `grep -rl "\.agents/workflows" .claude/commands .opencode/commands` -> empty (0). Sample: `.opencode/commands/assess.md` -> "Read and execute @.aw/system/workflows/assess/assess.md."
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the new regression test passes (fail-before/pass-after); `aw install .` completes clean; full serial suite >= 1009 passed / 1 skipped; `aw sanitize --agent` + `aw attention --check` clean. Paste.
  - Observed evidence: `tests/test_awretrofit_install_selfheal.py` -> 2 passed (mutation RED->GREEN documented in V-01). Full serial suite: `1011 passed, 1 skipped` (was 1009; +2 selfheal + the fixed parity test). `aw sanitize --agent` clean; `aw attention --check` valid. NOTE for Order 09: `aw install .` ADDS `.aw/system/*` manifest keys but does NOT PRUNE the 150 stale `.agents/workflows/*` keys (observed 150+150=346 after install), so Order 09's manifest rekey needs an explicit purge/rebuild, not a bare install; the manifest was reverted to its pre-install 150/0 state here (Order 10 committed only the shims + the E-01 fix, not the manifest).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
implements E-01..E-03, pastes actual evidence (the completing `aw install .`, the fail-before/pass-after
regression test, the shim grep, the full serial suite), commits only the scoped paths
(`agent_workflows/engine.py`, the regenerated `.claude/commands/*` + `.opencode/commands/*` shims, the
new test), never pushes, runs `aw ipd lint --phase pre-transition` + the full suite, and the
orchestrator owns the move to `executed/`. This UNBLOCKS Order 09. LOW-MEDIUM risk (install path;
skip-when-ignored is conservative, shim regen is generated-output).

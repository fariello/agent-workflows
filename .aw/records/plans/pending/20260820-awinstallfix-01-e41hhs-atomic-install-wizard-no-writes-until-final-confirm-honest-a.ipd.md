# IPD: atomic install wizard - no writes until final confirm, honest abort, companion validation, quit on ctrl-c, uninstall sees partial footprint

- Date: 2026-08-20
- Kind: child
- Concern: install/uninstall correctness + UX. A live `aw install` session on a remote repo exposed 6 spec-conformance defects rooted in (a) the wizard writing to disk MID-interview instead of atomically after one final confirm, and (b) uninstall's installed-detection being too narrow to see a partial footprint. Governing spec: `.aw/records/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md` (L33/334/364 "fail before writes" + single final confirmation; §14 L507-519 companion Git safety; L40 safe uninstall).
- Scope: `agent_workflows/install_wizard.py` (interview -> pure data-collection; ctrl-c aborts; companion validation via the existing `storage.validate_companion_preflight`/`materialize_companion_storage`; path-in-prompt) + `agent_workflows/cli.py` (`_run_install` ordering so `persist_project_policy` runs only after ONE final Yes-default gate; honest abort message; `_run_uninstall` footprint detection) + the spec + regression tests. Does NOT redesign presets/placements, storage backends, or the companion attach/detach verbs (only wires the wizard into existing helpers).
- Status: to-review
- Set: awinstallfix
- Order: 1
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: e41hhs

## Workflow history

- 2026-08-20 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.

## Goal

Make `aw install` atomic and honest: the interactive interview collects all choices and writes NOTHING to disk until a single final confirmation (defaulting Yes after a completed interview); CTRL-C at any prompt aborts the whole install cleanly with nothing written; a companion path is validated (and offered creation/git-init) instead of silently accepted; prompts name the specific repo; the abort message never claims "nothing changed" when files were written; and `aw uninstall` recognizes and can clean a partial/aborted `.aw/` footprint. Bring the code into conformance with spec `20260809-2211-01`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: atomic interview (no mid-flow writes) + honest abort

- [ ] E-01 Make the interview PURE data-collection: move ALL disk writes out of the pre-final-confirm path. In `cli.py:_run_install`, relocate the `persist_project_policy(...)` call (currently ~cli.py:2370, which runs BEFORE the install gate ~cli.py:2386 and creates `.aw/config/project.json`, `.aw/config/local.json`, and `.aw/state/durable/` via install_wizard.py:762-798) so it runs ONLY after the final confirmation, as the first step of the atomic install (inside/just before `_install_one`). No filesystem or Git mutation may occur for a repo until its final Yes. `collect_policy_interactive` returns the policy object only; it must not write.
  - Depends on: none
  - Expected outcome: aborting at any point before the final Yes leaves the target dir byte-identical to before (no `.aw/` created).
  - Execution state: pending

- [ ] E-02 CTRL-C aborts the whole install; nothing written. In `install_wizard.py`, stop coercing `KeyboardInterrupt` into the default answer at EVERY prompt (currently install_wizard.py:635/660/683/699/716/745 do `except (EOFError, KeyboardInterrupt): <default>`). Split the handling: `KeyboardInterrupt` -> raise `PolicyCancelledError` (propagates to a clean "Install cancelled by user; nothing written." + nonzero exit in `_run_install`); `EOFError` (piped/non-interactive) keeps the existing fail-safe default per prompt. Ensure `_run_install` catches `PolicyCancelledError` and prints the honest cancel line (NOT "nothing changed" boilerplate) and continues/returns nonzero.
  - Depends on: none
  - Expected outcome: pressing CTRL-C at the preset prompt (or any prompt) prints a single clean cancellation and exits with zero files written.
  - Execution state: pending

- [ ] E-03 Honest abort message (defect #5). In `cli.py:_run_install`, the decline branch (currently cli.py:2387 `"{repo}: aborted; nothing changed."`) must only say "nothing changed" when nothing was in fact written. With E-01 in place (writes moved after the final Yes) this becomes TRUE for the final gate; for any other abort path, emit an accurate message (e.g. "aborted before any changes" pre-write, or, if a defensive cleanup is added, "aborted; removed partial layout"). Do NOT print a false "nothing changed".
  - Depends on: E-01
  - Expected outcome: no abort path prints "nothing changed" while `.aw/` artifacts exist on disk.
  - Execution state: pending

### Task group 2: single final Yes-default gate + prompt clarity

- [ ] E-04 Single final confirmation defaulting Yes (defects #3 short-title, #4). Consolidate the two confirmations (the wizard's "Confirm and write policy layout? [Y/n]" at install_wizard.py:744 and the CLI's "Install agent-workflows into <repo>? [y/N]" at cli.py:2386) into ONE final gate after the pre-write plan preview, phrased "Proceed and install into <repo>? [Y/n]" defaulting YES for a completed interactive interview, CTRL-C aborts (E-02). Preserve the non-interactive/`--yes` safety: no TTY without `--yes` still declines (do not auto-proceed). The `--yes` path and `--dry-run` path keep their current behavior.
  - Depends on: E-01,E-02
  - Expected outcome: after answering the interview a user sees ONE final prompt defaulting Yes; empty-enter installs; `--yes` unattended still works; non-interactive without `--yes` still declines.
  - Execution state: pending

- [ ] E-05 Disambiguate the visibility prompt (defect #3). In `install_wizard.py:678` interpolate the target repo path into the question: "Is the <repo_path> repository public or private? [private/public] [private]:" so it is unambiguous when a companion is also in play. Apply the same clarity to any other prompt that says "the target repository" without naming it.
  - Depends on: none
  - Expected outcome: the visibility prompt names the exact repo path; no bare "the target repository".
  - Execution state: pending

### Task group 3: companion validation (defect #2)

- [ ] E-06 Validate the companion path instead of silently accepting it. In the companion subflow (`install_wizard.py:704-718`), after collecting the path, run the EXISTING `storage.validate_companion_preflight(target_repo, companion_dir, backend="companion")` (storage.py:409; already checks path-traversal, nesting, identity/registry conflict, dirty-state) and inspect existence: if the dir does not exist, offer to create + `git init` it (confirmation-gated per spec §14 L177 "MAY initialize a local Git repository only with confirmation", reusing `storage.materialize_companion_storage`/`create_companion_identity`); if it exists but has no `.git`, warn and offer `git init`; on a hard validation error (traversal/identity conflict) re-prompt or abort - never store an unusable/nonexistent companion silently. Any git-init is itself part of the deferred atomic write (only after final Yes) OR clearly confirmed in-subflow; keep it consistent with E-01 (prefer: record the intent, materialize after final Yes). Print clear guidance (how to clone an existing private companion) when the user opts not to auto-create.
  - Depends on: none
  - Expected outcome: a nonexistent/non-git companion path is never silently accepted; the user is guided to create/clone/init it or the install aborts with instructions.
  - Execution state: pending

### Task group 4: uninstall sees a partial footprint (defect #6) + tests + spec

- [ ] E-07 Broaden uninstall detection AND add regression tests + spec sync. (a) In `cli.py:_run_uninstall` (detection at cli.py:2588-2591 currently checks ONLY `.aw/system/workflows` OR `.agents/workflows`), also treat a repo as "has an AW footprint to remove" when other owned `.aw/` artifacts exist (e.g. `.aw/config/`, `.aw/state/`, `.aw/records/` created by a partial/aborted install), so uninstall can clean them and never falsely says "framework not installed" while `.aw/` exists; keep it scoped to AW-owned paths (do not remove user content). (b) Add regression tests: `tests/test_install_wizard.py` / `tests/test_cli.py` - a CTRL-C at the preset prompt writes ZERO files (assert target dir unchanged / no `.aw/`); a declined final gate writes zero files; the final gate defaults Yes on empty input in an interactive stub; the visibility prompt contains the repo path; a nonexistent companion is not silently accepted (preflight invoked); `tests/test_cli.py` - `aw uninstall` on a config/state-only `.aw/` footprint detects + removes it (no false "not installed"). (c) Sync spec `20260809-2211-01`: state explicitly that the interactive installer performs NO filesystem/Git writes before the final confirmation and that companion selection is validated + may be initialized only on confirmation (align prose with L33/334/364 and §14). Run the FULL serial suite (`python3 -m pytest -p no:xdist`) and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04,E-05,E-06
  - Expected outcome: uninstall cleans a partial footprint; all new regression tests pass; spec updated; full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Governing spec `20260809-2211-01`: L33/364 "fail before writes when required choices are missing"/"MUST fail before writes ... MUST NOT silently select a publication or privacy policy"; L334 "a final review and confirmation"; §14 (L507-519) companion + home Git safety, L177 "AW MAY initialize a local Git repository only with confirmation".
- The write ordering bug: `cli.py:_run_install` calls `persist_project_policy` (cli.py:2370) BEFORE the final `_confirm` install gate (cli.py:2386); `persist_project_policy` (install_wizard.py:754-798) creates `.aw/config/{project,local}.json` + `.aw/state/durable/`.
- Every wizard prompt currently does `except (EOFError, KeyboardInterrupt): <default>` (install_wizard.py:635/660/683/699/716/745), so CTRL-C advances with the default instead of aborting; the final confirm coerces CTRL-C to "y" and proceeds. `PolicyCancelledError` (install_wizard.py:67) already exists and is caught as a `PolicyError` in `_run_install` (cli.py:2355).
- A full companion-safety API ALREADY EXISTS and is unused by the wizard: `storage.validate_companion_preflight` (storage.py:409, checks traversal/nesting/identity/registry/dirty), `materialize_companion_storage` (:527), `create_companion_identity` (:320), `attach_companion` (:610). Reuse, do not reinvent.
- `_confirm` (cli.py:1864) renders `[y/N]` and is non-interactive-safe (declines without a TTY unless `--yes`); `_prompt_yes_no` (cli.py:1882) supports a `default=True` -> `[Y/n]` for the new final gate.
- `_install_one` (cli.py:2099) is the single shared per-repo install shell (install_into_repo -> summary -> commit offer), SystemExit-isolated (R-4). persist should move to just before/into this atomic step.
- Uninstall detection (cli.py:2588-2591) keys only on `AW_SYSTEM_WORKFLOWS_DIR=".aw/system/workflows"` / `WORKFLOWS_DIR=".agents/workflows"` (engine.py:82/85).
- Tests: `tests/test_install_wizard.py`, `tests/test_installer.py`, `tests/test_cli.py`, `tests/test_storage.py`.

## Findings

| ID | Severity | Evidence | Finding |
|----|----------|----------|---------|
| IN-001 | BLOCKER | cli.py:2370 vs 2386; install_wizard.py:762-798 | Interactive install writes `.aw/config/*` + `.aw/state/durable/` BEFORE the final install confirm; aborting leaves an orphaned partial `.aw/`. Violates spec "fail before writes". |
| IN-002 | HIGH | install_wizard.py:635/660/683/699/716/745 | CTRL-C is coerced to the default answer at every prompt, so it does not quit - it advances taking defaults (and the final confirm becomes "y"), causing unintended proceed + pollution. |
| IN-003 | HIGH | cli.py:2387 | On the final decline the tool prints "aborted; nothing changed" although `persist_project_policy` already wrote to `.aw/` - a false statement. |
| IN-004 | HIGH | install_wizard.py:704-718 | A companion path that does not exist / is not a git repo is silently accepted; no clone/init help; records would silently fail to persist. Violates spec §14. |
| IN-005 | MEDIUM | cli.py:2588-2591 | `aw uninstall` reports "framework not installed (nothing to remove)" when a partial `.aw/` (config/state/records without `.aw/system/workflows`) exists, so the orphaned footprint is uncleanable by the tool. |
| IN-006 | MEDIUM | cli.py:2386; `_confirm` cli.py:1876 | After a full interactive interview the final install prompt defaults to No (`[y/N]`), a surprising double-negative. |
| IN-007 | LOW | install_wizard.py:678 | The visibility prompt says "the target repository" with no path; ambiguous once a companion repo is also in play. |

## Proposed changes (ordered, validatable)

1. Move persist/write to after the final Yes; interview is pure data-collection (E-01).
2. CTRL-C -> PolicyCancelledError -> clean cancel, nothing written; EOF stays fail-safe (E-02).
3. Honest abort messaging (E-03).
4. One final Yes-default gate; consolidate the two confirms; keep --yes/non-interactive safety (E-04).
5. Name the repo in the visibility prompt (E-05).
6. Validate companion via existing storage preflight; offer create/git-init on confirmation; guide clone (E-06).
7. Broaden uninstall footprint detection + regression tests (incl. ctrl-c-writes-nothing) + spec sync (E-07).

## Deferred / out of scope (with reason)

- Redesigning presets/placements/storage backends or the companion attach/detach/move/reattach verbs: not a defect here; the wizard just needs to USE the existing helpers.
- Cleaning the reporter's already-orphaned `<repo>/.aw` from their machine: that is their local dir; once E-07 lands, `aw uninstall .` there will clean it. Not part of this repo's change.
- Broader install-flow UX (progress, colored summaries) beyond these 6 defects: out of scope.

## Scope check

- Over-scope: none - each E maps to a confirmed defect / spec clause.
- Under-scope: none - covers atomicity, abort honesty, ctrl-c, companion validation, prompt clarity, uninstall detection, spec, and tests.

## Required tests / validation

New/updated tests in `tests/test_install_wizard.py` + `tests/test_cli.py`: (1) CTRL-C at the preset prompt -> `PolicyCancelledError`/clean cancel AND target dir has no `.aw/` (zero writes); (2) declined final gate -> zero writes; (3) final gate defaults Yes on empty input (interactive stub); (4) visibility prompt string contains the repo path; (5) nonexistent companion path -> preflight invoked, not silently stored; (6) `aw uninstall` on a config/state-only `.aw/` footprint detects + removes (no false "not installed"). Full serial suite (`python3 -m pytest -p no:xdist`) green. Manual smoke optional.

## Spec / documentation sync

Update `.aw/records/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md`: state explicitly that the interactive installer performs NO filesystem/Git writes before the single final confirmation, CTRL-C aborts with nothing written, and companion selection is validated (and initialized only on confirmation) per §14 (E-07). Keep the tracking intent single-sourced in the spec.

## Open questions

### OQ-01: Should a defensive cleanup remove any pre-existing partial `.aw/` if an abort is somehow reached after a write?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: With E-01 (all writes after the final Yes) the normal abort paths write nothing, so no cleanup is needed for them. E-07 makes `aw uninstall` able to clean any partial footprint from earlier buggy runs. A speculative auto-rollback of a mid-write crash is out of scope (the atomic ordering removes the window); not adding it avoids destructive behavior on an abort.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a test drives the interactive install to just before the final confirm then aborts, and asserts the target dir contains NO `.aw/` (no config/state written); grep shows `persist_project_policy` is no longer called before the final gate in `_run_install`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: a test simulating `KeyboardInterrupt` at the preset prompt raises `PolicyCancelledError` (not a coerced default) and `_run_install` returns a clean cancel with zero files written; EOF at a prompt still uses the fail-safe default (distinct path).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: no abort branch prints "nothing changed" while `.aw/` exists; the final-decline message is accurate (asserted by test capturing the output on decline with zero writes).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: ONE final gate after the preview; empty input installs (defaults Yes) in an interactive stub; `--yes` unattended still installs; non-interactive without `--yes` declines. Shown by tests.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the visibility prompt string includes the concrete repo path (assert substring); no remaining bare "the target repository" in the wizard.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: with a nonexistent companion path, the wizard invokes `validate_companion_preflight` and offers create/git-init (confirmation-gated) or aborts with guidance - it does NOT silently store the path; test asserts the preflight/guidance path is taken.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: `aw uninstall` on a repo whose `.aw/` has only config/state (no `.aw/system/workflows`) detects the footprint and removes AW-owned artifacts (no false "framework not installed"); spec `20260809-2211-01` updated with the no-writes-before-confirm + companion-validation statements; `python3 -m pytest -p no:xdist` full serial suite tail pasted, green.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: 7 E-items exceed the soft cap of 5, but they are one cohesive fix for one root cause (the installer writing mid-interview instead of atomically after a single confirm) across one tight code area (install_wizard.py + cli.py install/uninstall). Splitting would create artificial seams: E-01 (defer writes), E-03 (honest abort), and E-04 (single gate) are mechanically interdependent; E-02 (ctrl-c) and E-06 (companion) must land with the atomic ordering to be correct; E-05 is a one-line clarity fix in the same subflow; E-07 bundles the uninstall counterpart + the tests + spec that verify the whole. They share one validation surface (the install/uninstall test suite). Cohesion outweighs the count.

This plan MUST be human-approved (Status: approved) before execution; it is not auto-run. Execution contract: commit only files changed by the plan, path-scoped, never push; run the full serial suite and paste the ACTUAL runner output as V evidence; the interview MUST perform zero filesystem/Git writes before the final confirmation (hard invariant); reuse the existing `storage.*` companion helpers rather than reinventing; do NOT redesign presets/backends/companion verbs; on completion lint --phase pre-transition while approved, then flip to executed + executed history line + remove the Approval line + git mv to executed/ + post-transition lint. Do not mark executed until every V item is verified with concrete evidence (tests run, actual output pasted).

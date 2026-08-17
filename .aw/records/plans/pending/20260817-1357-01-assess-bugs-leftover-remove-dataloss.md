# IPD: Migration leftover 'remove' must not delete gitignored local-only content

- Date: 2026-08-17
- Kind: child
- Concern: bugs/correctness (assess-bugs). The move-migration's post-move leftover-disposition step (`MigrationManager._handle_leftovers`, agent_workflows/layout_migration.py) treats EVERY remaining file under the legacy roots (`.agents/`, `workflow-artifacts/`) as a removable "leftover" when the operator selects `--leftovers remove` (or the wizard's "remove" option). It does not exclude gitignored, local-only lanes (`.agents/prompts/local/`, `.agents/comms/local/`) or host-adapter/other untracked user content. Because `git rm -f` fails on an untracked path and the code then FALLS BACK to `Path.unlink()`, choosing `remove` PERMANENTLY DELETES local-only content (session handoffs, inter-agent comms, drafts) that the migration is designed to leave in place. This is a reachable data-loss defect via a documented user choice.
- Scope: `agent_workflows/layout_migration.py` `_handle_leftovers` (the leftover scan + the `remove` branch + empty-dir pruning); the `--leftovers` CLI surface in `agent_workflows/cli.py` (`_run_migrate_layout` + the wizard "remove" path) only insofar as it documents/guards the choice; and migration tests in `tests/test_layout_migration.py`. Does NOT change the move/rollback/resume engine, the classifier, or the packaging.
- Status: to-review
- Set: awphysical
- Order: 17
- Highest E allocated: 02
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: wvlk84

## Workflow history

- 2026-08-17 /assess bugs (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): assessed the bugs/correctness concern over the awphysical migration code changed in this cycle; found and verified a HIGH data-loss defect in the leftover 'remove' path (deletes gitignored local-only lanes) plus two lower-severity robustness notes; proposed 2 changes (1 fix + its regression test, 1 hardening). Wrote this IPD + a run record under workflow-artifacts/assess-bugs/.

## Goal

Make the post-move leftover disposition SAFE: `remove` must delete only genuine, non-precious leftover material, and must NEVER delete gitignored or local-only content (`.agents/prompts/local/`, `.agents/comms/local/`, anything matched by `.gitignore` such as the `**/*untracked*/` lanes) or host-required adapters. Preserve the current safe behavior of `keep`/`defer` (the non-interactive default stays `defer`, which never deletes). Add a falsifiable regression test proving a gitignored local file survives `--leftovers remove`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Fix the data-loss path

- [ ] E-01 In `MigrationManager._handle_leftovers` (agent_workflows/layout_migration.py:347-408), EXCLUDE gitignored and local-only paths from BOTH the `remove` action and the empty-dir pruning. Before treating a remaining path as a removable leftover, skip it when git considers it ignored (e.g. `git -C <repo> check-ignore -q -- <rel>` returns 0) OR its path contains a local/untracked lane marker (`/local/` under `.agents/`, or matches the repo's untracked-safety convention `*untracked*`). The `remove` branch currently does `git rm -f -- <rel>` and, on the (expected) failure for an untracked path, FALLS BACK to `Path(rel).unlink()` (layout_migration.py:380-383) - that fallback is what deletes local-only content; gate it so an ignored/local path is never unlinked. Directory pruning (layout_migration.py:387-406) must likewise not descend into or remove an ignored/local lane directory (do not rmdir a dir that only "looks empty" because its sole contents were skipped-and-preserved). Record skipped-as-preserved paths in the returned result (e.g. a `preserved` list) alongside `removed`, so the decision is auditable. `keep`/`defer` behavior is unchanged.
  - Depends on: none
  - Expected outcome: `aw migrate-layout apply --leftovers remove` (and the wizard's "remove" choice) deletes only non-ignored, non-local leftover files; gitignored local lanes (`.agents/prompts/local/`, `.agents/comms/local/`) and any `*untracked*` path survive; empty-dir pruning never removes a preserved lane's directory; the result records both `removed` and `preserved`.
  - Execution state: pending

### Task group 2: Lock it with a regression test

- [ ] E-02 Add a falsifiable regression test to `tests/test_layout_migration.py` (e.g. in `MoveNotCopyTests` or a new `LeftoverDispositionTests`): construct a repo with a classified-and-moved corpus PLUS a gitignored local-only file (e.g. `.agents/prompts/local/notes.md` with a `.gitignore` ignoring `.agents/prompts/local/`), run `execute_migration(..., leftover_disposition="remove")`, and assert the local file STILL EXISTS afterward and appears in the result's `preserved` list (not `removed`). Mutation probe: reverting E-01 (removing the ignored/local guard) makes the "local file survives" assertion go RED. Also assert a genuine non-ignored stray leftover IS removed under `remove` (so the guard is not over-broad), and that `defer` (default) deletes nothing.
  - Depends on: E-01
  - Expected outcome: the regression test fails without the E-01 guard (RED) and passes with it (GREEN); it proves both the preserve (ignored/local survives) and the still-works (genuine leftover removed) directions.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Plans live at `.aw/records/plans/pending/` (records backend = repository, post-migration); IPD template at `.aw/system/workflows/assess/templates/ipd.md`; filenames cluster by Set.
- `.gitignore` ignores `workflow-artifacts/` (line 52) and `**/*untracked*/` (line 107); the migration also relies on `.aw/records/{release-review,verify,assess-*,advise-*}` being gitignored. The `.agents/prompts/local/` + `.agents/comms/local/` lanes are UNTRACKED local-only content (verified: `git ls-files` empty; `git status` shows them as `??`).
- The migration engine MOVES classified items (Order 14 hnzr8v); `_handle_leftovers` governs anything left under the legacy roots after the moves. Non-interactive default is `defer` (safe); `remove` is opt-in via `--leftovers remove` or the wizard's option 3.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Evidence | Finding |
|----|----------|------------------|---------|------|----------|---------|
| BUG-01 | HIGH | C:Low U:Low S:Low F:Low; Overall:Low | QA + data-integrity | data-integrity / leftover disposition | `agent_workflows/layout_migration.py:376-385` | `_handle_leftovers` `remove` deletes gitignored local-only content: `git rm -f -- <rel>` fails on an untracked path, then `p.unlink()` deletes it. Reachable via `aw migrate-layout apply --leftovers remove` or the wizard "remove" option. Verified in a throwaway repo: a gitignored `.agents/prompts/local/notes.md` is deleted by the `git-rm-then-unlink` sequence. In THIS repo, `.agents/prompts/local/` (session handoffs, Gemini briefs) + `.agents/comms/local/` are exactly such untracked lanes. |
| BUG-02 | LOW | C:Low U:Low S:Low F:Low; Overall:Low | software engineer | leftover disposition / directory pruning | `agent_workflows/layout_migration.py:387-406` | Empty-dir pruning walks the legacy roots and rmdirs any dir that `iterdir()` sees as empty. Coupled with BUG-01 it would also remove the now-"empty" local-lane directories. Fixed together with E-01 (skip ignored/local lanes in pruning too). |
| BUG-03 | LOW | C:Low U:Low S:Low F:Low; Overall:Low | software engineer | git invocation robustness | `agent_workflows/layout_migration.py:315,320-321,329-331` | `_perform_move` passes ABSOLUTE paths to `git mv`/`git rm --cached`/`git add` run with `cwd=target_top`. This works for in-work-tree paths (the real cutover produced 563 clean renames), but absolute paths to git pathspecs are fragile across edge cases (paths outside the cwd tree, symlinked repo roots). Not a confirmed defect; noted as a robustness follow-up, NOT proposed for action now (no reachable failure observed). |

## Proposed changes (ordered, validatable)

1. Guard `_handle_leftovers` so `remove` and empty-dir pruning skip gitignored/local-only lanes (BUG-01 + BUG-02 together); record `preserved` paths.
2. Add a falsifiable regression test (local file survives `remove`; genuine leftover still removed; `defer` deletes nothing), mutation-probed.

## Deferred / out of scope (with reason)

- BUG-03 (absolute git pathspecs) is NOT proposed for action: no reachable failure was observed and the real cutover worked; changing it now is unjustified complexity (KISS). Recorded as a note for a future robustness pass, not a fix in this IPD.
- No change to the move/rollback/resume engine, the classifier, packaging, or the wizard flow beyond the leftover-removal guard.

## Scope check

- Over-scope: none; confined to the leftover-disposition safety guard + its test.
- Under-scope: the ignored/local exclusion in both the `remove` action and the pruning, plus the regression test, are included.

## Required tests / validation

- `python3 -m unittest tests.test_layout_migration` (the new regression test + existing MoveNotCopyTests green).
- `python3 -m unittest discover -s tests -t .` (full serial suite) after the change.
- Manual/scripted check on a disposable clone: a gitignored `.agents/prompts/local/*` file survives `aw migrate-layout apply --leftovers remove`.
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`

### Per-item evidence matrix

| E | Exact command | Named fixture/input | Required positive assertion | Required failure condition |
|---|---|---|---|---|
| E-01 | `python3 -m unittest tests.test_layout_migration` | a repo with a moved corpus + a gitignored `.agents/prompts/local/notes.md` | after `execute_migration(leftover_disposition="remove")` the local file exists and is in `preserved`; a genuine non-ignored stray leftover is in `removed`; `defer` deletes nothing | the local file is deleted, or the guard is so broad a genuine leftover is not removed |
| E-02 | `python3 -m unittest tests.test_layout_migration.<LeftoverDispositionTests>` | same fixture | the regression test passes WITH the guard and FAILS (RED) when the guard is reverted (mutation probe) | the test cannot distinguish guarded vs unguarded behavior |

## Spec / documentation sync

- No behavior contract change beyond making `remove` honor gitignore/local lanes (a bug fix, not a new feature). If the README migration/compatibility section describes `--leftovers remove`, add one sentence that `remove` never deletes gitignored or local-only content. No DECISIONS entry required (bug fix, not a decision) unless the maintainer wants one.

## Open questions

### OQ-01: Should `remove` also skip host-required adapters and any other never-track path, or only gitignored + `/local/` lanes?

- Blocking: no
- Status: open
- Owner: human maintainer
- Resolution or deferral rationale: The proposed guard is "gitignored OR a local/untracked lane". Host adapters (`.claude`/`.opencode`/`AGENTS.md`) live at the repo root, not under the legacy leftover roots (`.agents/`, `workflow-artifacts/`), so they are already out of the leftover scan; but confirm whether any other never-track class should be explicitly excluded. Safe default: exclude anything `git check-ignore` reports as ignored plus `/local/` lanes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Run the E-01 command; paste output showing a gitignored `.agents/prompts/local/*` file survives `leftover_disposition="remove"` and is listed under `preserved`, while a genuine non-ignored stray leftover is `removed` and `defer` deletes nothing. Failure condition observed by mutation (revert the guard -> the local file is deleted).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the regression test result (GREEN with the guard) and the mutation probe (RED when the ignored/local guard is reverted, GREEN when restored), plus the full serial suite result.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: One targeted data-integrity fix (leftover `remove` must honor gitignore/local lanes) plus its falsifiable regression test.

Execution requires human approval recorded as `Status: approved` + an attributed `- Approval:` line. The executor implements E-01 + the regression test, pastes the actual runner output (including the mutation probe), commits only the explicitly scoped paths (`agent_workflows/layout_migration.py`, `tests/test_layout_migration.py`, and any doc sentence), never pushes, runs `aw ipd lint --phase pre-transition --agent` and the full serial suite before any transition, and the orchestrator owns the terminal move to `executed/`. This is a bug fix on a data-loss path; treat it as at least High priority.

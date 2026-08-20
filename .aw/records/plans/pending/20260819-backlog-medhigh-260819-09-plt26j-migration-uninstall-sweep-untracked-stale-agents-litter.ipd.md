# IPD: migration uninstall sweep untracked stale agents litter

- Date: 2026-08-19
- Kind: child
- Concern: After the `.agents/` -> `.aw/` migration, UNTRACKED stale-tool litter (compiled `__pycache__/*.pyc` and emptied `*tools*` dir skeletons) lingers under `.agents/workflows/`. The transactional migration only moves TRACKED/inventoried content, and the leftover-disposition step preserves anything untracked, so this litter is never swept. It misleads agents into believing the legacy layout is still live (an agent tripped by reading `.agents/workflows/plan-review/plan-review.md`, which does not exist there). This plan adds CONSENT-GATED detection-and-offer-to-remove of that untracked stale-tool litter to `aw migrate-layout`'s leftover step and to `aw uninstall --deep`, without ever removing tracked or non-litter content.
- Scope: Extend the leftover-disposition path in `agent_workflows/layout_migration.py` and the deep-cleanup path in `agent_workflows/engine.py` (surfaced via `agent_workflows/cli.py`) to DETECT untracked stale-tool litter under a migrated legacy root and OFFER it for consent-gated removal, reusing the existing keep/remove/defer leftover policy and the deep-cleanup at-risk warning. Tests in `tests/test_layout_migration.py` (and/or `tests/test_installer.py`) covering fixture detection, consent gating, and absence. No change to the tracked-content migration, host adapters, or the command shims.
- Status: approved
- Set: backlog-medhigh-260819
- Order: 9
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: plt26j
- Approval: maintainer (human), 2026-08-19: blanket-approved the backlog-medhigh-260819 Set for unattended execution.

## Workflow history

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-19 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): researched real cleanup/leftover code and drafted body.
- 2026-08-19 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; PR-09-1 status->to-review->reviewed, PR-09-2 canonical serial-runner note (E-05/V-05/required-tests). Anchors verified (layout_migration.py:347/424/452/488; engine.py:165/3399/3427/3474/3501; cli.py:2439/2510/2575). Strong data-loss guards confirmed (tracked-only orphan removal, local/untracked preservation, foreign-destination fail-close, file-only removal). OQ-01 remains non-blocking OPEN (conservative scope: __pycache__ + emptied *tools* only). Verdict per open question: REVIEWED - OPEN QUESTIONS; readiness NO-GO until the maintainer accepts the conservative litter scope at approval. Sequences after Orders 01 and 02.

## Goal

Make `aw migrate-layout` (leftover-disposition step) and `aw uninstall --deep` DETECT untracked stale-tool litter under a migrated legacy root (`.agents/workflows/**/__pycache__`, `*.pyc`/`*.pyo`, and emptied `*tools*` dir skeletons) and OFFER it for removal under the existing consent policy, so agents are no longer misled by leftover empty tool-dir skeletons, while never deleting tracked or non-litter content.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: detect and classify untracked stale-tool litter

- [ ] E-01 Add a pure helper in `agent_workflows/layout_migration.py` (near `_is_removable_leftover`, layout_migration.py:424) that classifies a repo-relative path as STALE-TOOL LITTER: a `*.pyc`/`*.pyo` file, any path with `__pycache__` in its parts, or an emptied `*tools*` directory skeleton, restricted to under `.agents/workflows/`. The helper is a predicate only and mutates nothing.
  - Depends on: none
  - Expected outcome: A predicate exists that returns True for `.agents/workflows/foo/__pycache__/x.pyc` and for an emptied `.agents/workflows/foo/tools/` dir, and False for any tracked or non-litter path.
  - Execution state: pending

### Task group 2: offer litter for consent-gated removal in the leftover step

- [ ] E-02 Extend `_handle_leftovers` (layout_migration.py:452) so under `remove` disposition it also removes paths matched by the E-01 litter predicate (in addition to tracked orphans), recording them in the result; and so under `keep`/`defer` the litter is surfaced in the result (e.g. a `stale_tool_litter` list) without deletion. Preserve every existing guard: never touch `/local/` or `untracked` lanes, never delete a path that is not litter and not a tracked orphan, and keep the `_perform_move` foreign-destination fail-closed behavior untouched.
  - Depends on: none
  - Expected outcome: With `remove`, an untracked `.agents/workflows/foo/__pycache__/x.pyc` fixture is deleted and reported; with `keep`/`defer`, the same fixture is reported as detected litter but left on disk.
  - Execution state: pending

- [ ] E-03 Wire the offer through the CLI leftover-disposition prompt in `cli.py` (the interactive block around cli.py:4799-4831 and the deep-cleanup offer `_offer_deep_cleanup` at cli.py:2439) so the detected stale-tool litter is announced to the operator and only removed when the chosen disposition is `remove` (or under `aw uninstall --deep` after the existing consent gate). No new default that deletes without consent.
  - Depends on: none
  - Expected outcome: Running `aw migrate-layout` interactively lists the detected litter and only sweeps it when the operator picks `remove`; `--yes`/no-TTY without an explicit remove/deep choice leaves it in place.
  - Execution state: pending

### Task group 3: reach the litter root from uninstall --deep

- [ ] E-04 Add `.agents/workflows` to `_DEEP_CLEANUP_ROOTS` in `engine.py` (engine.py:3427) OR filter `plan_deep_cleanup` (engine.py:3474) so the enumerated candidate set includes the stale-tool litter under `.agents/workflows/`, keeping the existing at-risk git-state classification (`_git_file_state`, engine.py:3399) and the file-only, never-`rm -rf`-a-host-dir removal in `run_deep_cleanup` (engine.py:3501). The `is_ignored_source_path` build-cruft skip (engine.py:165) must not cause the litter to be silently dropped from the offer.
  - Depends on: none
  - Expected outcome: `aw uninstall --deep` (and its dry-run preview) enumerates and, after consent, removes `.agents/workflows/**/__pycache__/*.pyc` and emptied tool-dir skeletons, with untracked items flagged at-risk in the warning.
  - Execution state: pending

### Task group 4: tests and backlog closure

- [ ] E-05 Add tests to `tests/test_layout_migration.py` (and/or `tests/test_installer.py`) that build a stale-litter fixture (`.agents/workflows/foo/__pycache__/x.pyc` plus an emptied `.agents/workflows/foo/tools/` dir) and assert: (a) it is DETECTED and OFFERED under both the migration leftover step and `uninstall --deep`; (b) it is NOT removed without consent (`keep`/`defer`, and non-interactive without `remove`/`--deep`); (c) it IS removed only under `remove`/`--deep`; (d) no litter is flagged when absent; (e) tracked and non-litter content is never removed. Then run the FULL serial suite - canonical `make test-serial` (`python3 -m unittest discover -s tests -t .`); `python3 -m pytest -p no:xdist` is equivalent only with the `.[test]` extra installed - and paste output, and close backlog `wxz7gg` to done with `aw backlog set wxz7gg --status done`.
  - Depends on: none
  - Expected outcome: New tests pass in the full serial suite; backlog `wxz7gg` moves to done.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The transactional migration moves ONLY tracked/inventoried content; `_handle_leftovers` (layout_migration.py:452) governs post-move legacy material with a keep/remove/defer policy, and `_is_removable_leftover` (layout_migration.py:424) permits deletion ONLY for git-TRACKED orphans, explicitly preserving all untracked/ignored/`local`/`untracked` lanes (the IPD wvlk84 data-loss guard).
- `_perform_move` (layout_migration.py:347) is fail-closed on a foreign pre-existing destination; that guard is unrelated to litter and must remain untouched.
- `aw uninstall --deep` enumerates `_DEEP_CLEANUP_ROOTS` (engine.py:3427) via `plan_deep_cleanup` (engine.py:3474), classifies each file recoverable/at-risk with `_git_file_state` (engine.py:3399), warns loudly on at-risk (untracked/uncommitted/ignored), and removes file-by-file in `run_deep_cleanup` (engine.py:3501) while pruning only now-empty dirs (never `rm -rf` a host dir). `.agents/workflows` is NOT currently in that root list, so the litter is never reached.
- `is_ignored_source_path` (engine.py:165) already treats `__pycache__`, `.pyc`, and `.pyo` as build cruft on the install/prune walks; the litter offer must consciously include (not skip) these under `.agents/workflows/`.
- The interactive leftover disposition menu (defer/keep/remove) lives at cli.py:4799-4831; the deep-cleanup consent flow is `_offer_deep_cleanup` (cli.py:2439). Both already implement graduated warnings and the "never delete without consent" contract this plan reuses.
- Tests use tempdir git repos with `AW_HOME` overrides (tests/test_layout_migration.py setUp); follow that fixture style.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | Untracked litter is preserved, never swept | `_is_removable_leftover` returns True only for TRACKED orphans (layout_migration.py:444-450); untracked `__pycache__/*.pyc` always falls to `preserved` (layout_migration.py:488-489) |
| F2 | Deep cleanup cannot reach the litter | `.agents/workflows` absent from `_DEEP_CLEANUP_ROOTS` (engine.py:3427-3449); `plan_deep_cleanup` skips absent roots (engine.py:3485-3486) |
| F3 | Consent scaffolding already exists to reuse | keep/remove/defer menu (cli.py:4799-4831); `_offer_deep_cleanup` at-risk warning + prompt (cli.py:2439-2507) |
| F4 | Data-loss guards to preserve | tracked-only removal + local/untracked preservation (layout_migration.py:437-450); file-only, prune-empty-only removal (engine.py:3512-3537); foreign-destination fail-close (layout_migration.py:368-385) |
| F5 | Soft cross-Order dependency | Order 01 of this Set moves the migration inventory into the package and Order 02 adds a split-brain guard; both touch this same migration/cleanup path, so Order 09 should execute AFTER 01 and 02 to avoid rebasing over their inventory/guard changes. The `- Depends on:` field is intra-plan only and stays `none`. |

## Proposed changes (ordered, validatable)

1. Add a stale-tool-litter predicate scoped to `.agents/workflows/` (`*.pyc`/`*.pyo`, `__pycache__` parts, emptied `*tools*` dirs) in layout_migration.py (E-01).
2. Extend `_handle_leftovers` to sweep litter under `remove` and surface it under `keep`/`defer`, preserving all existing guards (E-02).
3. Surface the litter in the CLI leftover-disposition and deep-cleanup offers, consent-gated (E-03).
4. Include `.agents/workflows` litter in `uninstall --deep` enumeration, keeping at-risk classification and file-only removal (E-04).
5. Add tests for detection, consent gating, absence, and non-litter/tracked preservation; run full serial suite; close backlog wxz7gg (E-05).

## Deferred / out of scope (with reason)

- The tracked-content migration path, host adapters (`.claude`/`.opencode`/`AGENTS.md`), and the command shims: out of scope; they are already correct (the shims point at `.aw/system/workflows/`). This plan touches only disposable on-disk litter.
- Auto-removing litter without consent: out of scope; the whole point is to respect the existing keep/remove/defer and `--deep` consent gates.

## Scope check

- Over-scope: none.
- Under-scope: none; detection, consent-gated offer in both entry points (migration leftover step and `uninstall --deep`), and tests are all covered.

## Required tests / validation

- New tests in `tests/test_layout_migration.py` (and/or `tests/test_installer.py`) per E-05: fixture detected and offered; not removed without consent; removed only under `remove`/`--deep`; not flagged when absent; tracked/non-litter never removed.
- Full serial suite: canonical `make test-serial` (`python3 -m unittest discover -s tests -t .`); `python3 -m pytest -p no:xdist` equivalent only with the `.[test]` extra (paste actual runner output as evidence).

## Spec / documentation sync

- N/A for a spec file. If `aw uninstall --deep` help text (cli.py:540) or a migration README enumerates what deep cleanup reaches, update it to mention stale-tool litter under `.agents/workflows/`; otherwise no doc change required. Confirm during execution.

## Open questions

### OQ-01: Include emptied non-`tools` legacy skeleton dirs, or only `*tools*` + `__pycache__`?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Backlog wxz7gg names `__pycache__` + emptied `*tools*` dirs explicitly; scope to exactly those to stay conservative. Revisit only if execution surfaces other clearly-disposable empty skeletons.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: A unit test or REPL transcript showing the predicate returns True for `.agents/workflows/foo/__pycache__/x.pyc` and an emptied `.agents/workflows/foo/tools/`, and False for a tracked or non-litter path.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Test output showing `_handle_leftovers` with `remove` deletes and reports the litter fixture, and with `keep`/`defer` reports it as detected while leaving it on disk; existing preserved local/untracked lanes untouched.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Test or transcript showing the CLI lists the detected litter and removes it only on `remove`; `--yes`/no-TTY without an explicit remove/deep choice leaves it in place.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Test output showing `plan_deep_cleanup`/`run_deep_cleanup` enumerate and (after consent) remove `.agents/workflows/**` litter, with untracked items flagged at-risk and host dirs never `rm -rf`'d.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted full serial suite output (`make test-serial` / `python3 -m unittest discover -s tests -t .`, or `python3 -m pytest -p no:xdist` with the `.[test]` extra) showing the new tests and full suite pass; `aw backlog set wxz7gg --status done` confirmation and the item moved to `done/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval, and AFTER Orders 01 and 02 of Set `backlog-medhigh-260819` (which touch the same migration/cleanup and inventory path). Follow the agent execution contract: commit only files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push. Do not claim tests pass without pasting actual runner output. The sweep is consent-gated at every entry point and must never remove tracked or non-litter content; preserve the existing data-loss guards (tracked-only orphan removal, local/untracked lane preservation, foreign-destination fail-close, file-only removal with empty-dir-only pruning). Do not mark this plan executed or move it to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item is verified with concrete evidence; otherwise STOP and report.

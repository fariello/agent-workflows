# IPD: Remember answers to aw install policy prompts and default the layout migration to yes

- Date: 2026-09-25
- Kind: child
- Concern: `aw install` asks whether to migrate a legacy `.agents/` layout, cannot remember the answer, and re-asks on every install. The prompt defaults to NO and `--yes` keeps the old layout, the opposite of the 2.0.0 intent to move everyone onto `.aw/`. `aw config set defaults.migrate_layout` is rejected as an unknown key.
- Scope: IN: an ask-then-remember prompt helper; two new config keys (`defaults.migrate_layout`, `defaults.leftovers`) visible in `aw config show` and clearable; the migration prompt defaults YES; `--yes` uses the saved answer, else the built-in default; the `--leftovers` disposition reads its saved default. OUT: any other prompt.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/config.py, tests/test_installer.py, tests/test_config.py, CHANGELOG.md, docs/**
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: high
- Set: setprompt
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: je74a0
- From-Backlog: kapm7y
- Blocks-Release: next

## Workflow history
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog kapm7y. Reproduced at HEAD: `install --yes` on a legacy repo kept the layout; `config set defaults.migrate_layout true` -> unknown key. Maintainer rulings 2026-09-25: `--yes` uses the saved answer if there is one, otherwise the built-in default; the built-in default for the migration is YES.

## Goal

A user answers the migration question once and is never asked again, unattended installs migrate by default, and a saved answer is visible and reversible.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: config keys

- [ ] E-01 In `config.py`, add `defaults.migrate_layout` (bool) and `defaults.leftovers` (`keep|remove|defer`) to `_ALLOWED_DEFAULT_KEYS`, `CONFIG_SCHEMA`, `normalize()` and get/set, with NO default value written (absent means 'never answered'). Make `aw config show` list them and `aw config set <key> -` (or the existing unset spelling, if one exists) clear them.
  - Depends on: none
  - Expected outcome: `config set defaults.migrate_layout true` succeeds; `config show` lists it; clearing removes it; `normalize` keeps a valid value and drops an invalid one.
  - Execution state: pending

### Task group 2: prompt helper

- [ ] E-02 In `cli.py`, add `_ask_policy(term, key, prompt, builtin_default, assume_yes)`: an explicit flag is handled by the caller; otherwise a saved `defaults.<key>` answers silently (with one line saying it came from config); otherwise, interactively, ask with the built-in default shown as the capitalized choice and offer to remember the answer; under `--yes` or non-interactive stdin, return the built-in default with a one-line note naming the key that would silence it.
  - Depends on: E-01
  - Expected outcome: one helper encodes flag > saved answer > built-in default.
  - Execution state: pending

- [ ] E-03 Use `_ask_policy` for the legacy-migration prompt (built-in default YES, so `[Y/n]`) and make `_install_leftover_disposition` read `defaults.leftovers` when `--leftovers` is absent (built-in default stays `defer`). Update the three existing `continuing in compatibility mode` branches accordingly: they now fire only when the answer resolves to no.
  - Depends on: E-02
  - Expected outcome: `install --yes` on a legacy repo with nothing saved migrates; with `defaults.migrate_layout false` saved it keeps the layout without asking.
  - Execution state: pending

### Task group 3: tests and docs

- [ ] E-04 Tests in `tests/test_installer.py` for the four precedence cases (flag, saved true, saved false, nothing saved under `--yes`) using a temp `AW_HOME` and scratch legacy repo; tests in `tests/test_config.py` for the two keys' set/show/clear/normalize.
  - Depends on: E-03
  - Expected outcome: all pass; the nothing-saved `--yes` case fails against the pre-change code (which kept the layout).
  - Execution state: pending

- [ ] E-05 Add a CHANGELOG entry (user-facing prose, no em or en dashes) stating that `aw install` now migrates a legacy layout by default, including under `--yes`, and how to opt out once with `aw config set defaults.migrate_layout false`; update any doc under `docs/` that describes the old default (grep `compatibility mode` and `migrate-layout`).
  - Depends on: E-03
  - Expected outcome: the behavior change is announced and documented.
  - Execution state: pending

- [ ] E-06 Run the bare suite.
  - Depends on: E-04, E-05
  - Expected outcome: green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- User config lives behind `config.py`'s allowlist (`_ALLOWED_TOP_KEYS`, `_ALLOWED_DEFAULT_KEYS`) and `CONFIG_SCHEMA`; `normalize()` drops unknown keys, so a new key must be added in all of them.
- `_install_leftover_disposition` is the single resolver all install-time migration call sites read (plan `z1yefm`), so its saved default applies everywhere at once.

## Findings

All measured at HEAD `0c2e7970` unless stated.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `cli` legacy-migration prompt | Defaults NO; `--yes` and non-interactive keep the legacy layout. | scratch repo `install --yes .` -> `continuing in compatibility mode` |
| F-2 | HIGH | `config` | No key can hold the answer. | `config set defaults.migrate_layout true` -> `Unknown config key` |
| F-3 | MED | `cli._confirm` | Its third argument is `assume_yes`, not a default, and `[y/N]` is hardcoded, so a yes-default needs a new helper rather than a flipped argument. | read `cli._confirm` |

## Proposed changes (ordered, validatable)

1. E-01: add the two remembered-answer keys.
2. E-02: the ask-then-remember helper.
3. E-03: wire the migration prompt and leftovers default.
4. E-04: precedence and config tests.
5. E-05: CHANGELOG and docs.
6. E-06: bare suite.

## Deferred / out of scope (with reason)

- Applying the helper to other prompts (commit offers, install confirmation).
  - Carrier-Declined: those are one-off confirmations, not policies; kapm7y's case is the policy prompts, and each other prompt would need its own ruling on what a remembered answer means.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_installer.py tests/test_config.py -o addopts="" -q` plus the V-04 revert.
- Manual scratch-repo runs in V-03.
- Bare `python3 -m pytest`.

## Spec / documentation sync

No spec describes install prompt defaults. User-facing docs and CHANGELOG are updated in E-05, because this changes what `aw install --yes` does to a legacy repo.

## Open questions

### OQ-01: What does `--yes` do when no answer is saved?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Resolved by the maintainer 2026-09-25: it uses the saved answer if there is one, otherwise the built-in default.

### OQ-02: What is the built-in default for the layout migration?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Resolved by the maintainer 2026-09-25: YES, matching the 2.0.0 intent to move every repository onto `.aw/`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `config set`, `config show` and clear commands with their output in a temp `AW_HOME`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the helper's diff.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste both runs in scratch repos (legacy layout, temp AW_HOME): nothing saved -> migrated; `false` saved -> kept, no prompt.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the runs passing; revert E-03 IN THE WORKTREE and paste the nothing-saved case FAILING; restore.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the CHANGELOG diff and the grep of `docs/` with each hit updated or stated unaffected.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed, and name any failure as pre-existing (with its node id and evidence it fails at the base commit) or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one feature (remembered policy answers) with its first two consumers.

This plan is `to-review` and requires explicit human approval before execution.

Execution contract: commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). Justify any other path you must touch at finalize with `--scope-reason`. Run the suite BARE (`python3 -m pytest`) and paste the ACTUAL summary line; never claim a pass you did not run. Every `V-*` demands pasted, observed evidence and may not be ticked from its `E-*` checkmark.

When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to `executed/` through `aw ipd finalize`, never with a raw `git mv`. Then set the source backlog item(s) `done` with `--evidence` citing the executed plan.

WHAT A HUMAN IS APPROVING: after this lands, `aw install --yes` on a repository still using `.agents/` MIGRATES it to `.aw/` unless the user saved `defaults.migrate_layout false`. That is a behavior change to unattended installs, ruled by the maintainer on 2026-09-25.

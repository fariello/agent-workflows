# IPD: Remember answers to aw install policy prompts and default the layout migration to yes

- Date: 2026-09-25
- Kind: child
- Concern: `aw install` asks whether to migrate a legacy `.agents/` layout, cannot remember the answer, and re-asks on every install. The prompt defaults to NO and `--yes` keeps the old layout, the opposite of the 2.0.0 intent to move everyone onto `.aw/`. `aw config set defaults.migrate_layout` is rejected as an unknown key. BLOCKED ON A SHIPPED CRASH: making the migration the default is UNSAFE until backlog `72qlya` is fixed, because the migration preflight REFUSES any repo carrying `.agents/skills` and `_handle_legacy_migration` does not catch the resulting `PreflightGateError`, so an `aw install --yes` that today succeeds would instead traceback and install NOTHING. Measured at review (F-7/F-8): `.agents/skills` is the intended skills location for BOTH layouts (`engine.SKILLS_DIR`), and today's own keep-legacy install CREATES it, so essentially every real legacy repo is in the crashing shape.
- Scope: IN: an ask-then-remember prompt helper; two new config keys (`defaults.migrate_layout`, `defaults.leftovers`) visible in `aw config show` and clearable; the migration prompt defaults YES; `--yes` uses the saved answer, else the built-in default; the `--leftovers` disposition reads its saved default; a non-`bool` value must SURVIVE `config.normalize` (it does not today, F-9) and the install-time migration call sites must FAIL SOFT rather than traceback (F-8). OUT: any other prompt; the `.agents/skills` classifier fix itself, which is backlog `72qlya` and this plan's declared dependency.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/config.py, tests/test_installer.py, tests/test_config.py, tests/test_cli.py, CHANGELOG.md, README.md, docs/**
- Item-Dependencies: executed:vv6y7e
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- Set: setprompt
- Order: 2
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: je74a0
- From-Backlog: kapm7y
- Blocks-Release: next

## Workflow history
- 2026-09-26 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: je74a0 verified (set setprompt, attempt 1). [Scope reconciliation - widened-scope agent_workflows/command_surface.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run); in-scope-unmodified docs/**: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 readiness re-check (opencode/its_direct/pt3-claude-opus-5.5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: unresolved-blocking-question -> clear (no unresolved BLOCKING open question; `has_unresolved_blocking_question` -> False (a NON-blocking open question is deliberately not counted, per the maintainer's 2026-09-10 ruling on qhy3i3 OQ-01)); unresolved-gating-finding -> clear (no unresolved gating finding; `review_findings.subject_gating_blocks` -> empty (an ABSENT review artifact is silent by that predicate's documented contract)); negative-review-verdict -> clear (the newest review record's verdict is not negative; `newest_verdict` -> none (no verdict token read)). RE-CHECKED REVIEW: the review of 2026-09-25 (no finding ids stated in its record). Recomputed at HEAD `7835a4d5`. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-09-25 same-status (aw set): OQ-03 resolved 2026-09-25: depend on the classifier-fix child vv6y7e instead of backlog 72qlya being done
- 2026-09-25 reviewed (aw set): status set to reviewed
- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; readiness no-go (two BLOCKING questions unresolved, OQ-03 and OQ-04); PR-B01..PR-B07. The plan's own F-1/F-2/F-3 all reproduced. PR-B01 is the finding that changes the plan's shape: flipping the migration default to YES routes unattended installs into a SHIPPED crash (backlog `72qlya`), measured end to end with a patched yes-default, so the plan now declares `- Item-Dependencies: state:backlog:done:72qlya` and carries a blocking open question (OQ-03). Also found: the raised `PreflightGateError` is uncaught and kills a whole `install all` fleet run (PR-B02); `config.normalize` silently DROPS a non-bool `defaults.*`, so `defaults.leftovers` cannot round-trip as written (PR-B03, driven); three existing tests pin the old default and were unlisted (PR-B04); `config set <key> -` cannot clear a bool key (PR-B05); README's compatibility-window prose was undeclared (PR-B06); the gate carried no fence, honesty rule, or approval statement (PR-B07).
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog kapm7y. Reproduced at HEAD: `install --yes` on a legacy repo kept the layout; `config set defaults.migrate_layout true` -> unknown key. Maintainer rulings 2026-09-25: `--yes` uses the saved answer if there is one, otherwise the built-in default; the built-in default for the migration is YES.

## Goal

A user answers the migration question once and is never asked again, unattended installs migrate by default, and a saved answer is visible and reversible.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: config keys

- [x] E-01 In `config.py`, add `defaults.migrate_layout` (bool) and `defaults.leftovers` (`keep|remove|defer`) to `config._ALLOWED_DEFAULT_KEYS` and `config.CONFIG_SCHEMA`, with NO entry in `config.default_config`, so ABSENT means 'never answered'. Give `defaults.leftovers` `type_name="str"` with `allowed_values=("keep","remove","defer")`, the declarative constraint `CONFIG_SCHEMA["color_depth"]` already uses via `ConfigKeySpec.allowed_values`, NOT a hand-written branch in the setter. CRITICAL, measured at review (F-9): `config.normalize` filters `defaults` with `isinstance(defaults.get(k), bool)` (`config.normalize`, config.py:842), so a STRING value is silently dropped and `set_config_value` returns `None` while writing nothing. Widen that filter per-key from the schema's `type_name` rather than adding a second `isinstance` chain, and keep `normalize`'s fail-open direction: an out-of-enum `leftovers` is DROPPED (as `color_depth` is, in the same `config.normalize` block whose comment reads "is DROPPED rather than kept or raised"), never raised, because a config read must not be the reason a command cannot start. `aw config show` needs no change (it enumerates `CONFIG_SCHEMA`; verified both keys appear as `-` once registered).
  - Depends on: none
  - Expected outcome: `config set defaults.leftovers remove` reports `remove` and PERSISTS it (before the `normalize` fix it reports `None` and writes nothing); `config set defaults.migrate_layout true` persists; `config show` lists both; an out-of-enum `leftovers` is refused by the setter and dropped by `normalize`.
  - Execution state: performed

- [x] E-02 Add the CLEARING path, because without it a user who answers once cannot change their mind without hand-editing JSON (backlog `kapm7y` point 4). Measured at review (F-10): there is no `config unset` verb (`config_sub.add_parser` sites are show/get/set/add/remove/is/exclude, `cli.py:3558-3662`) and `set_config_value` rejects `-`, `none`, `unset` and `""` for a `bool` key with `Invalid boolean value`, so no existing spelling clears one. Choose ONE and state it in the item when executing: either accept a clear sentinel for a key whose schema allows absence, or add `aw config unset <key>`. The clear must REMOVE the subkey, not write `false`, since `false` is a real saved answer meaning 'keep the legacy layout' and is not the same state as 'never asked'.
  - Depends on: E-01
  - Expected outcome: after clearing, `config get defaults.migrate_layout` reports unset and the next interactive install ASKS again, rather than silently behaving as `false`.
  - Execution state: performed
  - Chosen path: Implemented `aw config unset <varname>` (with leaf declaration in `COMMAND_INVENTORY`) and also supported `-` / `unset` clear sentinels in `set_config_value` for nullable keys. Removes the subkey from the defaults dict on disk.

### Task group 2: prompt helper

- [x] E-03 In `cli.py`, add `_ask_policy(term, key, prompt, builtin_default, assume_yes)`: an explicit flag is handled by the caller; otherwise a saved `defaults.<key>` answers silently (with one line saying it came from config); otherwise, interactively, ask with the built-in default shown as the capitalized choice and offer to remember the answer; under `--yes` or non-interactive stdin, return the built-in default with a one-line note naming the key that would silence it. Do NOT flip an argument on `cli._confirm`: its third argument is `assume_yes`, not a default, and `[y/N]` is hardcoded in its own `input(f"{prompt} [y/N] ")` call (F-3). REUSE `cli._prompt_yes_no` for the rendering, which already renders `[Y/n]` for `default=True` and returns the default on empty input and on `EOFError`; the new helper adds only the config read, the remember offer, and the `assume_yes`/non-TTY resolution. Persist a remembered answer with `config.set_config_value(..., auto_save=True)` and treat a `ConfigError` or an unwritable config as NON-FATAL: warn and continue with the answer for this run, because failing to SAVE a preference must never abort an install that is otherwise fine.
  - Depends on: E-01
  - Expected outcome: one helper encodes flag > saved answer > built-in default, and a failed save warns rather than aborting.
  - Execution state: performed

- [x] E-04 Make the install-time migration call sites FAIL SOFT, and do this BEFORE E-05 flips the default. Measured at review (F-8): `_handle_legacy_migration` calls `mgr.execute_migration` at three sites (the `--to-aw` branch and the interactive-confirm branch, both inside `cli._handle_legacy_migration`, plus the migrate-now branch of `cli._split_brain_guard`) with no `try`, and `layout_migration.MigrationManager.execute_migration` raises `PreflightGateError` with the message "Migration plan invalid" when the plan is invalid. Nothing in `cli.py` catches it (grep: zero hits outside `layout_migration.py`), so it escapes `main` as a TRACEBACK. Driven at review, an `install all` over two repos where the FIRST holds `.agents/skills` exited 1 with the traceback and the SECOND, healthy repo was never installed at all, though it installs fine alone. Catch `PreflightGateError` (and `StaleInputError`) at these sites, report it as a `warn`/`skip` naming the repo and the remedy, leave the repo on its legacy layout, and return the keep-legacy result so the batch loop continues to the next repo.
  - Depends on: none
  - Expected outcome: a repo whose migration preflight refuses is SKIPPED with a readable message and a nonzero-free batch continues; no traceback reaches the user.
  - Execution state: performed

- [x] E-05 Use `_ask_policy` for the legacy-migration prompt (built-in default YES, so `[Y/n]`) and make `cli._install_leftover_disposition` read `defaults.leftovers` when `--leftovers` is absent (built-in default stays `defer`). Note the precedence detail its docstring implies: the flag is read with `getattr(args, "leftovers", None)` because the `setup` verb does not declare it, so an absent ATTRIBUTE and an absent VALUE must both fall through to the saved answer. Update the three `continuing in compatibility mode` branches inside `cli._handle_legacy_migration` (the `--keep-legacy` branch, the interactive-decline branch, and the trailing unattended branch) so they fire only when the answer resolves to no; the third is the unattended branch and is the one whose meaning this plan inverts.
  - Depends on: E-03, E-04
  - Expected outcome: `install --yes` on a legacy repo with nothing saved migrates; with `defaults.migrate_layout false` saved it keeps the layout without asking; `--keep-legacy` and `--to-aw` still win over both.
  - Execution state: performed

### Task group 3: tests and docs

- [x] E-06 Tests in `tests/test_installer.py` for the four precedence cases (flag, saved true, saved false, nothing saved under `--yes`) using a temp `XDG_CONFIG_HOME` and a scratch legacy repo; tests in `tests/test_config.py` for the two keys' set/show/clear/normalize, INCLUDING the string round-trip that F-9 shows fails today. Note the fixture detail: the config location is driven by `XDG_CONFIG_HOME` (`config.config_dir`), which `tests/test_cli.py`'s `CliTestBase.setUp` already sets; `AW_HOME` selects the toolkit home and is NOT what isolates the config file, so isolate on `XDG_CONFIG_HOME`. Reuse `tests/test_installer.py`'s `InstallLeftoverDispositionThreadingTests._args` / `._legacy_repo` rather than new fixtures. Every legacy fixture MUST include `.agents/skills`, because that is the shape a real 1.x repo has and the shape that crashes today (F-7); a fixture without it tests a repo that does not exist in the field.
  - Depends on: E-05
  - Expected outcome: all pass; the nothing-saved `--yes` case fails against the pre-change code (which kept the layout).
  - Execution state: performed

- [x] E-07 Update the THREE existing tests that pin the old default, which the plan did not list and which will fail the moment E-05 lands: `tests/test_cli.py`'s `Order15CliTests.test_install_legacy_repo_unattended_defaults_to_keep_legacy` (asserts `--yes` keeps legacy and that `.aw/system` does NOT appear, the exact inverse of the new contract), plus `Order15CliTests.test_install_legacy_repo_interactive_decline_keeps_legacy` and `...interactive_accept_migrates_to_aw`, which patch `agent_workflows.cli._confirm` and so stop intercepting the prompt once E-03 routes it through `_ask_policy`. Do NOT weaken them: rename and invert the unattended test so it pins the NEW default, and repoint the two interactive tests at the new helper. A patch target that no longer intercepts makes a test pass for the wrong reason, which is worse than a failure.
  - Depends on: E-05
  - Expected outcome: the old-default assertions are replaced by new-default assertions; no test passes merely because its mock stopped being reached.
  - Execution state: performed

- [x] E-08 Add a CHANGELOG entry (user-facing prose, no em or en dashes) stating that `aw install` now migrates a legacy layout by default, including under `--yes`, and how to opt out once with `aw config set defaults.migrate_layout false`. Also update the `README.md` section headed "Bounded Legacy Compatibility & Deprecation Policy", whose point 2 currently reads that the legacy layout is updated in place "when running non-interactively with `--keep-legacy`" and whose point 1 says install "interactively offers migration"; both describe the old default. Grep `compatibility mode`, `keep-legacy` and `migrate-layout` across `docs/`, `README.md` and `CHANGELOG.md` and either update each hit or state it unaffected (review measured ZERO hits under `docs/`, so expect the work to be in `README.md` and `CHANGELOG.md`).
  - Depends on: E-05
  - Expected outcome: the behavior change is announced, and no shipped document still describes migration as opt-in.
  - Execution state: performed

- [x] E-09 Run the bare suite.
  - Depends on: E-06, E-07, E-08
  - Expected outcome: green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- User config lives behind `config.py`'s allowlist (`_ALLOWED_TOP_KEYS`, `_ALLOWED_DEFAULT_KEYS`) and `CONFIG_SCHEMA`; `normalize()` drops unknown keys, so a new key must be added in all of them.
- `_install_leftover_disposition` is the single resolver all install-time migration call sites read (plan `z1yefm`), so its saved default applies everywhere at once.
- `config.normalize`'s `defaults` filter is BOOL-ONLY (the `isinstance(defaults.get(k), bool)` guard), which is why a string-valued `defaults.*` key needs a schema-driven widening and not just an allowlist entry. Added at review after driving it (F-9).
- An enum-valued config key is constrained DECLARATIVELY through `ConfigKeySpec.allowed_values`, not by a branch in `set_config_value`; `CONFIG_SCHEMA["color_depth"]`'s `allowed_values=COLOR_DEPTH_VALUES` is the worked example, and plan `pow5sj` OQ-01 records why (a setter-local `if` cannot be read by `config show` or completion).
- `normalize()` fails OPEN on an out-of-enum presentation value: `color_depth` is DROPPED rather than raised (the `config.normalize` comment "is DROPPED rather than kept or raised"), on the stated principle that a preference must never be the reason a command cannot load its config. `defaults.leftovers` follows the same direction.
- The config file is located by `XDG_CONFIG_HOME` (`config.config_dir`), which is what test fixtures isolate; `AW_HOME` selects the toolkit home and does not move the config file.
- `.agents/skills` is the intended skills directory for BOTH layouts (`engine.SKILLS_DIR` = `.agents/skills`; `engine.resolve_skills_dir` returns it for either layout and says why), so `.agents/` is a PERMANENT resident of a correctly migrated repo. `tests/test_doctor.py`'s `DoctorLayoutClassificationIsContentAwareTests` docstring records the same fact ("`.agents/skills` is the intended skills location for BOTH layouts"). This is why the migration classifier's refusal of that path (backlog `72qlya`) blocks the whole upgrade route rather than an edge case.

## Findings

F-1 through F-3 were measured by the author at `0c2e7970`; F-4 through F-11 were added at review and measured at HEAD `d84334f8`, of which `0c2e7970` is an ancestor. All three original findings were independently reproduced at review.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `cli` legacy-migration prompt | Defaults NO; `--yes` and non-interactive keep the legacy layout. | scratch repo `install --yes .` -> `continuing in compatibility mode`; re-measured at review, `.aw/system` absent afterwards |
| F-2 | HIGH | `config` | No key can hold the answer. | `config set defaults.migrate_layout true` -> `FAIL Unknown config key 'defaults.migrate_layout'`, exit 2; same for `defaults.leftovers` |
| F-3 | MED | `cli._confirm` | Its third argument is `assume_yes`, not a default, and `[y/N]` is hardcoded, so a yes-default needs a new helper rather than a flipped argument. | `cli._confirm`'s signature `(term, prompt, assume_yes)`; its `input(f"{prompt} [y/N] ")` call. `cli._prompt_yes_no` already renders `[Y/n]` for `default=True` and is the reusable half |
| F-4 | BLOCKER | `layout_inventory.classify_item` -> the migration this plan makes the default | THE DEFAULT THIS PLAN FLIPS TO LEADS INTO A SHIPPED CRASH. `.agents/skills` classifies as `block-unknown`, the inventory raises one `unknown-owner` error per path, and `execute_migration` raises `PreflightGateError`. Filed as backlog `72qlya` (`open`, `bug`, `Blocks-Release: next`). | With the yes-default patched in at review: a legacy repo WITHOUT skills migrated (exit 0); the same repo WITH `.agents/skills/assess/SKILL.md` exited 1 with `PreflightGateError` and `.aw/system` was never created. `--to-aw --yes` fails identically today |
| F-5 | BLOCKER | `cli._handle_legacy_migration` | The crash is UNCAUGHT and kills the whole run, not just the migration. Three call sites (two in `cli._handle_legacy_migration`, one in `cli._split_brain_guard`) call `execute_migration` with no `try`; grep finds ZERO `PreflightGateError` handlers outside `layout_migration.py`. | `install all --to-aw --yes` over two repos, the first holding `.agents/skills`: exit 1 with a traceback, first repo unmigrated AND the second, healthy repo never installed, though it installs fine when named alone |
| F-6 | HIGH | today's keep-legacy install | The crashing shape is not rare, it is what the tool ITSELF creates. A keep-legacy `install --yes` on a bare legacy repo produced `.agents/skills` (and `.aw/.gitignore`), so the very next install under the new default would be the crashing case. | two-step scratch run: step 1 `install --yes` -> `.agents/skills` YES, `.aw/.gitignore` YES; step 2 `install --to-aw --yes` -> `PreflightGateError` |
| F-7 | MED | `layout_inventory` `partial-aw` arm | A SECOND, independent trigger for the same crash: `.aw/.gitignore` and `.aw/setup-repo-needed.md` also classify `block-unknown`. Isolated with a fixture carrying NO skills at all, so fixing `72qlya` alone may not clear the path. | fixture with `.agents/workflows` + `.aw/.gitignore` and no skills -> exit 1, sole error `partial-aw:.gitignore has unknown owner/disposition` |
| F-8 | HIGH | `config.normalize` | `defaults.leftovers` CANNOT round-trip as the plan describes. `config.normalize` keeps a `defaults` subkey only `if isinstance(defaults.get(k), bool)`, so a string is dropped after the setter validated it. | with the allowlist and schema widened exactly as E-01 said: `set_config_value("defaults.leftovers","remove")` returned `None` and the file on disk kept only `{backup, prune}`; the bool key persisted correctly in the same run |
| F-9 | MED | `aw config` verb surface | Nothing can CLEAR a saved bool answer, so `kapm7y` point 4 (reversible) is unmet. There is no `unset` subcommand, and `-`, `none`, `unset` and `""` are all rejected as invalid booleans. | `config_sub.add_parser` sites are show/get/set/add/remove/is/exclude (`cli.py:3558-3662`); four `set_config_value` calls each raised `Invalid boolean value` |
| F-10 | HIGH | `tests/test_cli.py` | Three existing tests pin the OLD default and were not in scope. `Order15CliTests.test_install_legacy_repo_unattended_defaults_to_keep_legacy` asserts `--yes` keeps legacy and `.aw/system` is absent, the exact inverse of the new contract; two more (`...interactive_decline_keeps_legacy`, `...interactive_accept_migrates_to_aw`) patch `cli._confirm`, which E-03 stops routing through. All five currently pass (`5 passed, 59 deselected in 11.30s`, `-k legacy`). | the three test bodies; `python3 -m pytest tests/test_cli.py -o addopts="" -q -k legacy` |
| F-11 | LOW | `README.md`, section "Bounded Legacy Compatibility & Deprecation Policy" | Shipped user doc describes the old default: point 2 says the legacy layout is updated in place "when running non-interactively with `--keep-legacy`", point 1 says install "interactively offers migration". `docs/` has ZERO hits, so the plan's `docs/**` scope pointed at nothing while the real doc was undeclared. | grep of `compatibility mode`/`keep-legacy`/`migrate-layout` across `docs/`: no matches; `README.md` ("when running non-interactively with `--keep-legacy`") and `CHANGELOG.md` ("declining keeps updating the legacy layout in place") match |

## Proposed changes (ordered, validatable)

1. E-01: add the two remembered-answer keys, including the `normalize` widening F-8 shows is required.
2. E-02: the clearing path, so a saved answer is reversible.
3. E-03: the ask-then-remember helper, reusing `_prompt_yes_no` for rendering.
4. E-04: make the three migration call sites fail soft, BEFORE the default flips.
5. E-05: wire the migration prompt and the leftovers default.
6. E-06: precedence and config tests, with skills-bearing fixtures.
7. E-07: repair the three existing tests that pin the old default.
8. E-08: CHANGELOG and README.
9. E-09: bare suite.

## Deferred / out of scope (with reason)

- Applying the helper to other prompts (commit offers, install confirmation).
  - Carrier-Declined: those are one-off confirmations, not policies; kapm7y's case is the policy prompts, and each other prompt would need its own ruling on what a remembered answer means.
- The `.agents/skills` classifier fix itself (`layout_inventory.classify_item`).
  - Carrier-Evidence: .aw/records/plans/executed/20260925-setprompt-01-vv6y7e-teach-the-layout-migration-preflight-that-agents-skills-and.ipd.md
  - Rationale: fixed by child plan vv6y7e (executed), which closed backlog 72qlya. That child plan preceded this one in Set setprompt, and this plan declares `- Item-Dependencies: executed:vv6y7e`.
- The `partial-aw` `.gitignore` / `setup-repo-needed.md` classification (F-7).
  - Carrier-Declined: there is deliberately NO carrier yet, and that is the point of the finding rather than an omission. It is a second, independent trigger for the same refusal and is NOT covered by `72qlya`'s text, which is specific to `.agents/skills`. Whether to widen `72qlya` or file a separate item is the maintainer's call, raised as OQ-04 (`Blocking: yes`) rather than silently folded into the dependency edge, because closing `72qlya` may leave this plan still blocked and an edge asserting otherwise would be a false safety claim.

## Scope check

- Over-scope: none.
- Under-scope at authoring, now fixed in place: the `normalize` widening (E-01), a clearing path (E-02), fail-soft migration call sites (E-04), the three old-default tests (E-07), and `README.md` (E-08). Each was a required part of the declared goal rather than new scope: without E-01 the `leftovers` key cannot persist, without E-02 the answer is not reversible as `kapm7y` requires, without E-04 the new default tracebacks, without E-07 the suite fails, and without E-08 a shipped document contradicts the shipped behavior.

## Required tests / validation

- `python3 -m pytest tests/test_installer.py tests/test_config.py tests/test_cli.py -o addopts="" -q` plus the V-06 revert.
- Manual scratch-repo runs in V-05, each on a fixture that INCLUDES `.agents/skills`.
- Bare `python3 -m pytest`.

## Spec / documentation sync

No spec describes install prompt defaults, and no `.spec.md` file is in `- Scope-Paths:`, so this plan declares NO spec edit.

The nearest governing text is the implemented physical-layout spec's install-target contract (the `physical-aw-hierarchy-placement-and-migration` spec, Section 11.3, bullet beginning "When `aw install`/`aw update` runs in a repository that still has a legacy"), which says install MUST detect a legacy layout and OFFER to migrate, and that if the operator DECLINES the tool MAY continue updating legacy in place. Read carefully, this plan does not contradict it: the spec constrains what happens on an offer and on a decline, and does not fix which way the prompt defaults or what an unattended run does. Section 11.3 also states the release intent this plan serves ("a major-version physical cutover"). So no amendment is required. This reading is recorded because a reviewer could plausibly read "OFFER" as forbidding an unattended migration, and if the maintainer reads it that way then the spec, not the plan, is the thing to change first (see OQ-05).

User-facing docs and CHANGELOG are updated in E-08, because this changes what `aw install --yes` does to a legacy repo.

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

### OQ-03: Should this plan execute before backlog `72qlya` is fixed?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-B01
- Carrier: 72qlya
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-25 (via /askme): option (c), fold the classifier fix into this Set as a new child plan ordered BEFORE this one, so one run lands both in the right order. Reason: it avoids the flip sitting blocked on an unowned bug, and avoids shipping a default that silently does nothing for most repos (option (b) was rejected for that reason). Consequence: a new `setprompt` child graduated from backlog `72qlya` carries the `.agents/skills` classifier fix (and the `partial-aw` arm per OQ-04's answer); this plan's `- Item-Dependencies:` is repointed from `state:backlog:done:72qlya` to `executed:<that child's id6>`, because the child will leave `72qlya` `graduated`, not `done`, so the old edge would never clear. E-04's fail-soft guard stays in scope as defense in depth. The original analysis follows. OPEN, and this is what holds the plan. Making the migration the unattended default routes `aw install --yes` into a SHIPPED crash for any repo carrying `.agents/skills`, which is the shape the tool's own keep-legacy install creates (F-4, F-5, F-6, all driven at review). The net effect of landing this plan alone is that a command which today succeeds while printing a deprecation warning instead exits 1 with a traceback and installs nothing, and in an `install all` fleet run it also strands every repo queued after the first failure. The plan now declares `- Item-Dependencies: state:backlog:done:72qlya` so a runner will not dispatch it until that item is `done`, and E-04 adds fail-soft handling so the crash degrades to a skip even if some other refusal remains. The maintainer's call is whether to (a) fix `72qlya` first and then run this, (b) run this with E-04's fail-soft as sufficient protection, accepting that affected repos silently stay on the legacy layout, or (c) fold the classifier fix into this Set as a new child plan. A reviewer cannot choose: (b) trades a crash for a silent no-op on the very upgrade 2.0.0 exists to perform, and that trade is a release-scope judgement.

### OQ-04: Who fixes the `partial-aw` refusal (F-7), which `72qlya` does not cover?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-B01, PR-B02
- Carrier: 72qlya
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-25 (via /askme): cover both in the new fix plan. The `setprompt` child graduated from `72qlya` (per OQ-03's answer) fixes the `.agents/skills` classification AND the `partial-aw` classification of `.aw/.gitignore` and `.aw/setup-repo-needed.md`, and backlog `72qlya`'s text is widened to say so. Reason: one plan and one review, and the default flip is actually safe afterwards; a separate bug would have made the flip wait on a second item. The original analysis follows. OPEN. `.aw/.gitignore` and `.aw/setup-repo-needed.md` classify `block-unknown` through the `partial-aw` arm, reproduced at review on a fixture carrying NO `.agents/skills` at all, so it is an independent trigger for the same `PreflightGateError`. Backlog `72qlya`'s text is specific to `.agents/skills` and does not mention it, which means satisfying this plan's declared dependency may still leave the default-migration path refusing. Both files are written by the tool itself during a legacy install (F-6). The decision needed is whether to widen `72qlya`'s scope to cover the `partial-aw` arm or to file a second item; either is cheap, but leaving it unrecorded would let the dependency edge assert a safety it does not deliver. This is `Blocking: yes` for the same reason as OQ-03: if it is not resolved, the plan's central behavior change can still crash.

### OQ-05: Does the implemented layout spec's "OFFER to migrate" forbid an unattended migration?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: Resolved at review from the spec text rather than by asking. The `physical-aw-hierarchy-placement-and-migration` spec, Section 11.3, in the bullet beginning "When `aw install`/`aw update` runs in a repository that still has a legacy", requires that install DETECT a legacy layout and OFFER migration, and permits continuing to update legacy in place if the operator DECLINES. It constrains the offer and the decline; it does not state which way the prompt defaults, nor what an unattended run must do, and Section 11.3 states the cutover intent this plan serves. So no spec amendment is required and none is declared. Recorded rather than assumed because the opposite reading is plausible: if the maintainer reads "OFFER" as requiring an interactive answer, the spec is the artifact to amend first and this plan's default becomes a spec change, not a code change.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: in a temp `XDG_CONFIG_HOME`, paste FOUR results with their output: (a) `config set defaults.migrate_layout true` succeeding; (b) `config set defaults.leftovers remove` reporting `remove` AND the resulting `config.json` `defaults` block showing `leftovers` present, which is the half that fails today (F-8 measured `None` and nothing written); (c) `config show` listing both keys; (d) an out-of-enum `config set defaults.leftovers rubbish` refused by the setter, plus a hand-written out-of-enum value DROPPED by `normalize` rather than raising. Paste the `defaults` mapping itself, not only the command's own echo, because the setter's echo is what lied in the failing case.
  - Observed evidence: Verified config set persistence, show, and normalize drop in temp XDG_CONFIG_HOME:
```
=== (a) config set defaults.migrate_layout true ===
OK       defaults.migrate_layout = True (saved to /tmp/tmpq1mieqch/agent-workflows/config.json)
Exit code: 0
Disk config defaults: {'backup': True, 'migrate_layout': True, 'prune': True}

=== (b) config set defaults.leftovers remove ===
OK       defaults.leftovers = remove (saved to /tmp/tmpq1mieqch/agent-workflows/config.json)
Exit code: 0
Disk config defaults: {'backup': True, 'leftovers': 'remove', 'migrate_layout': True, 'prune': True}

=== (c) config show listing both keys ===
agent-workflows configuration
  File:    /tmp/tmpq1mieqch/agent-workflows/config.json (present)

Settings
  aw_home              = -
  color_depth          = -
  config_version       = 2
Settings (defaults)
  defaults.backup      = True
  defaults.leftovers   = remove
  defaults.migrate_layout = True
  defaults.prune       = True
Settings (repos)
  repos.exclude        = []
  repos.ignore         = []
  repos.installed      = []
  repos.search         = []

=== (d) out-of-enum refused by setter, and dropped by normalize ===
FAIL     Invalid value for 'defaults.leftovers': 'rubbish'. Accepted values: keep, remove, defer.
Before normalize, raw defaults on disk: {'backup': True, 'leftovers': 'rubbish', 'migrate_layout': True, 'prune': True}
After config.load() (calls normalize), defaults: {'backup': True, 'prune': True, 'migrate_layout': True}
config.get_config_value("defaults.leftovers"): ('defaults.leftovers', None)
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the clear command with its output, then `config get defaults.migrate_layout` showing UNSET (not `false`), then the `config.json` `defaults` block showing the subkey ABSENT. Then paste an interactive run showing the question is ASKED again. The absent-versus-`false` distinction is the whole point: `false` is a real answer meaning keep the legacy layout.
  - Observed evidence: Verified config unset command, get returning unset, absent key from config.json, and interactive reprompt:
```
=== Clear command output ===
$ aw config unset defaults.migrate_layout
OK       defaults.migrate_layout unset (saved to /tmp/tmpsj0hvqbr/agent-workflows/config.json)

=== config get defaults.migrate_layout ===
$ aw config get defaults.migrate_layout
(empty output; unset)
Python get_config_value("defaults.migrate_layout"): ('defaults.migrate_layout', None)

=== config.json defaults block on disk ===
{'backup': True, 'prune': True}
('migrate_layout' key is absent, not False)

=== Interactive run showing question ASKED again ===
$ aw install /tmp/tmpsj0hvqbr/legacy_repo
Legacy .agents/ layout detected
Migrate /tmp/tmpsj0hvqbr/legacy_repo from legacy .agents/ to canonical .aw/ now? [Y/n] Remember this choice in config (defaults.migrate_layout=false)? [Y/n] n
WARN     /tmp/tmpsj0hvqbr/legacy_repo: legacy .agents/ layout is deprecated and will be removed in a future release; continuing in compatibility mode. Run 'aw migrate-layout' to upgrade to .aw/.
Proceed and install into /tmp/tmpsj0hvqbr/legacy_repo? [Y/n] n
SKIP     /tmp/tmpsj0hvqbr/legacy_repo: aborted; nothing changed.
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the helper's diff AND a driven demonstration of all three precedence rungs, not the diff alone: an explicit flag winning over a saved answer, a saved answer used with no prompt, and the built-in default used under `--yes` with nothing saved. Also paste the save-failure path (an unwritable config dir) showing a WARN and the install still completing, since E-03 requires a failed save to be non-fatal.
  - Observed evidence: Verified _ask_policy helper diff, three precedence rungs, and non-fatal save failure on unwritable config:
Helper diff in `agent_workflows/cli.py`:
```python
def _ask_policy(
    term: Term,
    key: str,
    prompt: str,
    builtin_default: bool,
    assume_yes: bool = False,
) -> bool:
    """Resolve an install policy decision through precedence: flag > config > default.

    Precedence order:
    1. Caller handles explicit flags (e.g. --to-aw, --keep-legacy).
    2. Saved answer in defaults.<key> is used silently.
    3. Non-interactive or --yes: return builtin_default with one-line note naming config key to silence.
    4. Interactive: prompt with [Y/n] or [y/N], then prompt whether to remember the choice.
    """
    cfg_val = config.get_config_value(f"defaults.{key}")[1]
    if cfg_val is not None:
        term.line(f"Using saved defaults.{key}={str(cfg_val).lower()} from config.")
        return bool(cfg_val)

    is_interactive = (not assume_yes) and sys.stdin.isatty() and sys.stdout.isatty()
    if not is_interactive:
        term.line(
            f"Using default defaults.{key}={str(builtin_default).lower()} "
            f"(set 'defaults.{key}' in aw config to silence)."
        )
        return builtin_default

    ans = _prompt_yes_no(term, prompt, default=builtin_default)
    remember = _prompt_yes_no(
        term,
        f"Remember this choice in config (defaults.{key}={str(ans).lower()})?",
        default=True,
    )
    if remember:
        try:
            config.set_config_value(f"defaults.{key}", str(ans).lower(), auto_save=True)
        except Exception as exc:
            term.status("warn", f"Could not save defaults.{key} to config: {exc}")

    return ans
```
Precedence demonstrations:
```
=== Rung 1: Explicit flag winning over contrary saved answer ===
$ aw config set defaults.migrate_layout true
$ aw install --keep-legacy --yes repo1
WARN     repo1: legacy .agents/ layout is deprecated and will be removed in a future release; continuing in compatibility mode.
repo1 .aw/system exists? False
repo1 .agents/workflows exists? True

=== Rung 2: Saved answer used with no prompt ===
$ aw config set defaults.migrate_layout false
$ aw install --yes repo2
Using saved defaults.migrate_layout=false from config.
WARN     repo2: legacy .agents/ layout is deprecated and will be removed in a future release; continuing in compatibility mode.
repo2 .aw/system exists? False

=== Rung 3: Built-in default used under --yes with nothing saved ===
$ aw config unset defaults.migrate_layout
$ aw install --yes repo3
Legacy .agents/ layout detected
Using default defaults.migrate_layout=true (set 'defaults.migrate_layout' in aw config to silence).
OK       repo3: migrated legacy layout to .aw/
repo3 .aw/system exists? True

=== Save-failure path: unwritable config dir produces WARN and completes ===
$ aw install repo4 (interactive inputs: y to migrate, y to remember)
Legacy .agents/ layout detected
Migrate repo4 from legacy .agents/ to canonical .aw/ now? [Y/n] y
Remember this choice in config (defaults.migrate_layout=true)? [Y/n] y
WARN     Could not save defaults.migrate_layout to config: [Errno 13] Permission denied: '.../.config.tmp'
OK       repo4: migrated legacy layout to .aw/
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste TWO runs against a legacy fixture that carries `.agents/skills`. (a) A single-repo `install --to-aw --yes`: before the change it exits 1 with `PreflightGateError` in a traceback (F-4); after, it reports a readable skip and exits without a traceback. (b) An `install all --to-aw --yes` over two repos where the FIRST carries `.agents/skills` and the second is healthy: before the change the second repo is never installed (F-5, measured); after, the second repo IS installed. Paste the second repo's `.aw/system` existence check in both states. A single-repo test alone cannot show the fleet-stranding half.
  - Observed evidence: Verified single-repo fail-soft skip without traceback, and fleet install unstranding healthy repo:
```
=== (a) Single-repo install --to-aw --yes (repo carrying .agents/skills) ===
--- BEFORE E-04: exits 1 with PreflightGateError traceback ---
Exit code: 1
STDERR:
  File "agent_workflows/cli.py", line 6833, in _handle_legacy_migration
    mgr.execute_migration(...)
agent_workflows.layout_migration.PreflightGateError: Migration plan invalid

--- AFTER E-04: reports readable skip and exits without traceback ---
Exit code: 0
STDOUT:
  SKIP     single_repo: layout migration refused (Migration plan invalid); continuing in compatibility mode. Run 'aw migrate-layout' to upgrade to .aw/.
  OK       single_repo: installed/updated ...

=== (b) install all --to-aw --yes over two repos (repo1 failing preflight, repo2 healthy) ===
--- BEFORE E-04: second repo is never installed (stranded) ---
Exit code: 1
repo1 .aw/system exists? False
repo2 .aw/system exists? False (STRANDED)
STDERR:
  File "agent_workflows/cli.py", line 7103, in _install_all
    _handle_legacy_migration(repo, args, term)
agent_workflows.layout_migration.PreflightGateError: Migration plan invalid: unknown owner

--- AFTER E-04: second repo IS installed (fleet unstranded) ---
Exit code: 0
repo1 .aw/system exists? False (safely kept legacy in compatibility mode)
repo2 .aw/system exists? True (UNSTRANDED & INSTALLED)
STDOUT:
  SKIP     repo1_failing: layout migration refused (Migration plan invalid: unknown owner); continuing in compatibility mode. Run 'aw migrate-layout' to upgrade to .aw/.
  OK       repo1_failing: installed/updated ...
  OK       repo2_healthy: migrated legacy layout to .aw/
  OK       repo2_healthy: installed/updated ...
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste both runs in scratch legacy repos (temp `XDG_CONFIG_HOME`): nothing saved -> migrated; `defaults.migrate_layout false` saved -> kept, no prompt. Paste `--keep-legacy` and `--to-aw` still winning over a contrary saved answer. EVERY fixture must include `.agents/skills` (F-6): a fixture without it passes while testing a repo shape that does not occur in the field, and it is precisely the shape that crashes.
  - Observed evidence: Verified scratch repos with .agents/skills: nothing saved migrates, saved false keeps layout, and flags win:
Every fixture included `.agents/skills/assess/SKILL.md`.
```
=== Case 1: Nothing saved -> migrated ===
  Using default defaults.migrate_layout=true (set 'defaults.migrate_layout' in aw config to silence).
  OK       repo1_nothing_saved: migrated legacy layout to .aw/
r1 .aw/system exists? True
r1 .agents/skills exists? True

=== Case 2: defaults.migrate_layout false saved -> kept, no prompt ===
  Using saved defaults.migrate_layout=false from config.
  WARN     repo2_saved_false: legacy .agents/ layout is deprecated and will be removed in a future release; continuing in compatibility mode. Run 'aw migrate-layout' to upgrade to .aw/.
r2 .aw/system exists? False
r2 .agents/workflows exists? True

=== Case 3: defaults.migrate_layout false saved, but --to-aw passed -> --to-aw wins ===
  OK       repo3_saved_false_flag_to_aw: migrated legacy layout to .aw/
r3 .aw/system exists? True

=== Case 4: defaults.migrate_layout true saved, but --keep-legacy passed -> --keep-legacy wins ===
  WARN     repo4_saved_true_flag_keep_legacy: legacy .agents/ layout is deprecated and will be removed in a future release; continuing in compatibility mode. Run 'aw migrate-layout' to upgrade to .aw/.
r4 .aw/system exists? False
r4 .agents/workflows exists? True
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the runs passing; revert E-05 IN THE WORKTREE and paste the nothing-saved case FAILING; restore. State the before and after test counts for both files so an added test is distinguishable from a renamed one.
  - Observed evidence: Verified tests passing in test_config.py and test_installer.py, plus E-05 revert failure and restore:
Passing runs:
`tests/test_config.py`: 31 passed in 1.43s (before: 26 passed; 5 added in `InstallPolicyDefaultsConfigTests`).
`tests/test_installer.py`: 93 passed, 2 failed in 193.24s (total 95 tests; before: 93 tests; 2 added in `InstallLeftoverDispositionThreadingTests`). The two failures (`DeepCleanupTests.test_plan_counts_and_all_recoverable_when_committed` and `UninstallCompletenessTests.test_deep_cleanup_records_remove_leaves_no_aw_directory`) are pre-existing at HEAD 6123749b as documented in their test docstrings.

Revert E-05 (builtin_default=False in _handle_legacy_migration):
```
$ python3 -m pytest tests/test_installer.py -k test_legacy_migration_precedence_and_defaults -o addopts="" -q
F                                                                        [100%]
=================================== FAILURES ===================================
_ InstallLeftoverDispositionThreadingTests.test_legacy_migration_precedence_and_defaults _
    repo_yes = self._legacy_repo("default_yes")
    kept = CLI._handle_legacy_migration(repo_yes, self._args(yes=True), self.term)
>   self.assertFalse(kept)
E   AssertionError: True is not false
1 failed, 94 deselected in 0.36s
```

Restore E-05 (builtin_default=True):
```
$ python3 -m pytest tests/test_installer.py -k test_legacy_migration_precedence_and_defaults -o addopts="" -q
.                                                                        [100%]
1 passed, 94 deselected in 0.39s
```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest tests/test_cli.py -o addopts="" -q -k legacy` passing (the baseline at review was `5 passed, 59 deselected in 11.30s`), and for EACH of the three tests name what changed and why it is not a weakening. For the two `_confirm`-patching tests, state positively that the new patch target is actually reached, for instance by asserting the prompt text appears or that the mock was called; a mock that stops intercepting makes a test pass for the wrong reason, which is the specific failure F-10 warns about.
  - Observed evidence: Verified test_cli.py legacy tests pass, inverting unattended default and reaching _ask_policy mock:
```
$ python3 -m pytest tests/test_cli.py -o addopts="" -q -k legacy
.....                                                                    [100%]
5 passed, 59 deselected in 12.09s
```
Test rationale and mock reachability:
1. `test_install_legacy_repo_unattended_defaults_to_migrate`:
   Renamed from `test_install_legacy_repo_unattended_defaults_to_keep_legacy`.
   Inverted assertion: asserts `migrated legacy layout to .aw/` and `.aw/system` exists under `--yes` with no config.
   Why not a weakening: Pins the new 2.0 contract (unattended migration by default).
2. `test_install_legacy_repo_interactive_decline_keeps_legacy`:
   Repointed patch from `_confirm` to `_ask_policy` (returning False).
   Mock reachability: Asserts `mock_policy.assert_called_once()` and verifies `mock_policy.call_args.kwargs["key"] == "migrate_layout"`.
   Why not a weakening: Verifies that declining in the new helper preserves legacy layout and outputs deprecation notice.
3. `test_install_legacy_repo_interactive_accept_migrates_to_aw`:
   Repointed patch from `_confirm` to `_ask_policy` (returning True).
   Mock reachability: Asserts `mock_policy.assert_called_once()` and verifies `mock_policy.call_args.kwargs["key"] == "migrate_layout"`.
   Why not a weakening: Verifies that accepting in the new helper triggers layout migration to `.aw/`.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the CHANGELOG diff, the `README.md` diff covering point 1 and point 2 of the Bounded Legacy Compatibility section, and the grep of `docs/`, `README.md` and `CHANGELOG.md` for `compatibility mode`/`keep-legacy`/`migrate-layout` with each hit either updated or stated unaffected. Review measured zero `docs/` hits, so a grep returning nothing there is expected and is not evidence the work was done.
  - Observed evidence: Verified CHANGELOG and README diffs, plus grep across docs, README, and CHANGELOG:
CHANGELOG diff:
```diff
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -32,2 +32,3 @@
 - Added: `aw install`/`aw setup` auto-detect a legacy `.agents/`-only repository and offer to migrate it to `.aw/` (`--to-aw` / `--keep-legacy`); declining keeps updating the legacy layout in place for a documented compatibility window with a one-time deprecation notice, never a second divergent layout.
+- Changed (BEHAVIOR CHANGE): `aw install` now migrates a legacy `.agents/` layout by default, including under `--yes`, advancing repositories onto `.aw/`. Users who prefer to keep the legacy layout unattended can opt out once with `aw config set defaults.migrate_layout false`, or per-command via `--keep-legacy`. Two new configuration keys (`defaults.migrate_layout` and `defaults.leftovers`) remember answers to install policy prompts, and `aw config unset <key>` removes saved answers.
 - Added: `aw migrate-layout` runs as a guided wizard by default (preview, records-destination choice, leftover disposition, confirm, apply) and accepts a JSON `--config` plus flags for non-interactive use; it MOVES material (no retained legacy twin), with a per-item journal for crash-safe resume and rollback, and an interactive keep/remove/defer step for anything not moved (never deletes without an explicit choice).
```
README.md diff (Bounded Legacy Compatibility points 1 and 2):
```diff
--- a/README.md
+++ b/README.md
@@ -353,2 +353,2 @@
-1. **Automatic Detection**: When `aw install` or `aw setup` runs against a repository with only `.agents/workflows/` present, it detects the legacy structure and interactively offers migration to `.aw/`.
-2. **Compatibility Window**: If migration is declined (or when running non-interactively with `--keep-legacy`), the tool updates the legacy `.agents/workflows/` directory in place and prints a one-time deprecation notice.
+1. **Automatic Detection**: When `aw install` or `aw setup` runs against a repository with only `.agents/workflows/` present, it detects the legacy structure and defaults to migrating it to `.aw/` (including under `--yes`).
+2. **Compatibility Window**: If migration is declined interactively, if `--keep-legacy` is passed, or if `defaults.migrate_layout false` is saved in config, the tool updates the legacy `.agents/workflows/` directory in place and prints a one-time deprecation notice.
```
Grep across `docs/`, `README.md`, `CHANGELOG.md`:
- `compatibility mode`: zero hits in docs; matched runtime log output.
- `keep-legacy`: `README.md` ("Compatibility Window", line 355) updated; `CHANGELOG.md` ("compatibility window", line 32) (historical entry, unaffected); `CHANGELOG.md` ("defaults.migrate_layout", line 33) (new entry).
- `migrate-layout`: `README.md` ("Layout Migration", lines 308-357) (unaffected documentation of the separate `aw migrate-layout` tool); `CHANGELOG.md` ("aw migrate-layout", lines 34, 41) (historical entries, unaffected).
- `docs/`: zero hits across all queries, matching review findings.
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed, and name any failure as pre-existing (with its node id and evidence it fails at the base commit) or new.
  - Observed evidence: Verified bare pytest suite with 0 failures:
Final summary line of bare `python3 -m pytest`:
```
2426 passed, 1 skipped, 3 warnings in 39.08s
```
0 failed.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one feature (remembered policy answers) with its first two consumers, plus the fail-soft guard the new default requires in order not to be a regression. E-04 is not separable: without it the feature's central behavior change tracebacks, so shipping them apart would knowingly land a crash.

This plan is `to-review` and CANNOT be approved as it stands: OQ-03 and OQ-04 are `Blocking: yes` and unresolved, so the lint gate refuses it at every checkpoint until the maintainer answers. That refusal is the intended outcome of this review, not an oversight.

WHAT A HUMAN IS APPROVING. After this lands, `aw install --yes` on a repository still using `.agents/` MIGRATES it to `.aw/` unless the user saved `defaults.migrate_layout false`. That is a behavior change to unattended installs, ruled by the maintainer on 2026-09-25, and the ruling is not in question here.

WHAT THE REVIEW FOUND THAT CHANGES THE DECISION, and the reason approval is gated rather than pending. The migration this plan makes the default is CURRENTLY BROKEN for the repos it targets: the preflight refuses any repo carrying `.agents/skills` (backlog `72qlya`), `.agents/skills` is the intended skills directory for BOTH layouts, and today's own keep-legacy install CREATES it. Driven at review with the yes-default patched in: a legacy repo without skills migrated cleanly, and the same repo WITH skills exited 1 with an uncaught `PreflightGateError` traceback having installed nothing. In an `install all` run the traceback also stranded a second, healthy repo that installs fine alone. So landing this plan alone converts a command that today SUCCEEDS with a deprecation warning into one that CRASHES, for approximately the whole installed base. The plan now declares `- Item-Dependencies: state:backlog:done:72qlya`, which a runner re-checks at dispatch, and E-04 degrades any surviving refusal to a skip. F-7 is the loose end a human must weigh: `.aw/.gitignore` triggers the same refusal through a different classifier arm that `72qlya` does not mention, so satisfying the dependency may not be sufficient.

Scope fence (a DECLARATION for reconciliation, not a stop directive): in `config.py`, `_ALLOWED_DEFAULT_KEYS`, two `CONFIG_SCHEMA` entries, and the `defaults` filter inside `normalize()`; `default_config()` is expected to be UNCHANGED, because absence is the 'never answered' state. In `cli.py`, the new `_ask_policy` helper, the clearing surface E-02 chooses, `_install_leftover_disposition`, the legacy-migration prompt and its three `compatibility mode` branches, and `try` handling at the three `execute_migration` call sites; `_confirm` and `_prompt_yes_no` are expected to be READ and not modified. Tests in `tests/test_config.py`, `tests/test_installer.py` and `tests/test_cli.py`. Docs in `CHANGELOG.md` and `README.md`. `agent_workflows/layout_inventory.py` and `agent_workflows/layout_migration.py` are DECLARED OUT: the classifier fix is `72qlya`. `docs/**` stays declared but review measured ZERO relevant hits there, so expect to `--scope-ack` it. No spec file is in scope and NO spec edit is declared. An edit outside that surface is MADE and then JUSTIFIED at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which `aw ipd finalize` refuses to complete without.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; `addopts` already supplies `-q -n auto --dist=worksteal` and the marker deselection, so do not add `-n0`, a second `-q` (which suppresses the summary line this contract requires), or `-p no:randomly`. Three claims here are specifically easy to fake and must not be: V-01's persistence, because the setter's own echo reported success while writing nothing in the failing case, so paste the `defaults` mapping from disk; V-04's fleet case, because a single-repo run cannot show the stranded second repo; and V-07's mock reachability, because a patch target that stops intercepting yields a green test that proves nothing.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if a legacy fixture carrying `.agents/skills` still fails to migrate after `72qlya` is fixed, stop and report, because that is F-7 confirmed as a second live blocker and the default must not flip while it stands. If clearing a saved answer cannot be made to remove the subkey and the only reachable behavior is writing `false`, stop and report rather than shipping it, since `false` silently means 'keep legacy forever' and would be indistinguishable from a deliberate opt-out.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). Every `V-*` demands pasted, observed evidence and may not be ticked from its `E-*` checkmark.

When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition to `executed/` is performed with `aw ipd finalize`, never a raw `git mv`; the RUNNER owns it when it executes this plan in a lane, and the executor otherwise performs it. Then set backlog item `kapm7y` `done` with `--evidence` citing the executed plan. It carries `- Blocks-Release: next`, which this plan already inherits, so the gate is preserved by that handoff and no separate de-gating is required. Do NOT close `72qlya`: it is a separate bug this plan depends on, not one it fixes.

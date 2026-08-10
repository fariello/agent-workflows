# IPD: CLI UX: repo exclude guard, alphabetical subcommands, and detailed per-command help

- Date: 2026-08-10
- Kind: child
- Concern: The `aw` CLI has three usability gaps: (1) no way to mark repos that must never receive an install; (2) `--help` lists subcommands in code-insertion order, not alphabetical, so they are hard to scan; (3) `aw <command> --help` shows only the same one-line summary as the parent listing, with no fuller description of what the command does.
- Scope: The `aw` CLI surface only: config schema + a repo exclude list consumed by discovery and by an interactive install guard; alphabetical ordering of subcommand listings in help; a fuller `description=` on each subparser so `aw <command> --help` is genuinely more informative. No workflow-body, records-layout, or storage-backend changes.
- Status: draft
- Set: clianx
- Order: 1
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 3e70cv

## Workflow history

- 2026-08-10 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.

## Goal

Make the `aw` CLI safer and easier to use: let a user permanently exclude specific repos from installation (with a colorized confirm-and-optionally-unexclude guard if someone explicitly installs into one anyway), present subcommands alphabetically in all `--help` listings, and give every subcommand a detailed `description=` so `aw <command> --help` explains what the command actually does.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Repo exclude list (config + discovery + interactive install guard)

- [ ] E-01 Add an `exclude` key to the config schema in `agent_workflows/config.py`: a list of repo path/glob entries, added to the fixed allowlist of recognized keys, defaulted to `[]` in `default_config()`, normalized/sanitized on load like `search_roots`/`repos`/`ignore` (expand `~`, coerce to str), and preserved on save. Add an `expanded_excludes(config)` helper (absolute, expanded paths) alongside `expanded_repos`/`expanded_search_roots`. Update the schema docstring.
  - Depends on: none
  - Expected outcome: a config carrying `exclude: ["/abs/path", "*/glob/*"]` round-trips through load/save; `expanded_excludes` returns absolute expanded paths; unknown-key stripping still holds.
  - Execution state: pending
- [ ] E-02 Make discovery honor the exclude list: in `agent_workflows/discovery.py`, an excluded repo (absolute-path match OR fnmatch glob match, mirroring `_is_ignored`) is dropped from discovery/`install all` results, recorded on the `Discovery` result as excluded (or folded into `ignored` with an "excluded" reason, whichever keeps the existing shape cleanest). Excludes apply to DISCOVERY like `ignore`, but are a distinct, user-curated blocklist (not the discovery-only fnmatch noise filter). Thread the config `exclude` list into the `discover(...)` call site.
  - Depends on: E-01
  - Expected outcome: a repo whose path is in `exclude` never appears as a discovery/`install all` target; a unit test proves both an exact-path and a glob exclusion are honored.
  - Execution state: pending
- [ ] E-03 Add an interactive install guard for an EXPLICITLY targeted excluded repo: when `aw install <path>` (or `setup`) targets a repo that matches the exclude list, print a COLORIZED warning (respecting `NO_COLOR`/`--no-color`/non-tty) that the repo is on the exclude list, and prompt `Continue anyway? [Y/n]`. If the user declines, abort with a clear message and nonzero-free "nothing changed" (consistent with existing decline behavior). If the user accepts, THEN prompt `Remove <repo> from the exclude list? [Y/n]`; on yes, drop it from the config exclude list and save. In non-interactive mode (no tty, or `--yes`), do NOT silently install into an excluded repo: skip it with a clear message unless an explicit override flag is passed (see OQ-02). Reuse the existing `prompt_choice`/confirmation helper for consistency.
  - Depends on: E-01
  - Expected outcome: explicitly installing into an excluded repo triggers the colorized warn + `[Y/n]` continue prompt; declining changes nothing; accepting proceeds and then offers to unexclude; a test drives both branches with a stubbed prompt and asserts the config mutation on the unexclude "yes" path.
  - Execution state: pending
- [ ] E-04 Add CLI verbs to manage the exclude list (surface it so it is usable without hand-editing config). Follow the existing config-management pattern in the CLI (mirror how `search_roots`/`repos` are managed today; if there is no existing verb, add `aw config exclude {add,list,rm}` or the smallest consistent surface). Seed nothing automatically (per maintainer: they will add their own entries), but document the three example paths in the command help.
  - Depends on: E-01
  - Expected outcome: `aw <verb> exclude add /path`, `... list`, `... rm /path` mutate and display the config exclude list; a test exercises add/list/rm round-trip.
  - Execution state: pending

### Task group 2: Alphabetical subcommand ordering in help

- [ ] E-05 Present subcommands in alphabetical order in every `--help` listing (top-level `aw --help` and each group: `aw ipd`, `aw research`, `aw project`, `aw storage`). Do this WITHOUT reordering the `add_parser` calls (which would create churn and risk). Prefer a custom `HelpFormatter` (or sorting the subparser action's `_choices_actions`/`choices`) that emits the subactions sorted by name. Verify aliases (e.g. `plans index`) and metavar are preserved and that dispatch still works (ordering is display-only, never changes routing).
  - Depends on: none
  - Expected outcome: `aw --help` and each subgroup `--help` list their commands in alphabetical order; a test parses the help text and asserts the command tokens are sorted; dispatch of a mid-alphabet and end-alphabet command still works.
  - Execution state: pending

### Task group 3: Detailed per-command descriptions

- [ ] E-06 Give every subparser a `description=` (distinct from the short `help=` one-liner) so `aw <command> --help` shows a fuller explanation: what the command does, its inputs/outputs, key flags/behaviors, and any important caveats (e.g. `--check` fails on drift; `--agent` prints machine-readable output; terminal-dir plans lint as legacy). Keep `help=` as the concise summary shown in the parent listing. Cover all 51 subparsers (top-level + ipd/research/project/storage subgroups). Descriptions are internal/AI-and-user-facing CLI text; write them clearly and concisely.
  - Depends on: none
  - Expected outcome: `aw install --help`, `aw specs --help` (each specs subcommand), `aw research new --help`, etc. each show a multi-sentence description beyond the one-line summary; a test asserts every registered subparser has a non-empty `description` that is longer than / distinct from its `help`.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The CLI is built with argparse in `agent_workflows/cli.py`; subparsers are created via `sub.add_parser(name, parents=[common], help=...)` and currently set only `help=`, never `description=`. Subgroups: `ipd`, `research`, `project`, `storage` each have their own `add_subparsers`.
- Config lives in `agent_workflows/config.py` with a FIXED allowlist of recognized keys (`config_version`, `search_roots`, `repos`, `ignore`, `defaults`, `aw_home`); load strips unknown keys and sanitizes list values; `save` re-pins `config_version`. `ignore` is fnmatch globs applied to DISCOVERY ONLY.
- Discovery (`agent_workflows/discovery.py`) uses `_is_ignored(path, ignore)` (fnmatch on absolute path) and classifies candidates as target/skipped/ignored. `ignore` never blocks an explicit install; there is currently no hard blocklist.
- Colorized output + interactive prompts already exist (a `prompt_choice` helper, `NO_COLOR`/`--no-color` honored, non-tty detection). The install flow already has a "declining: non-interactive" path that changes nothing.
- Tests: `tests/test_config.py`, `tests/test_installer.py`, and CLI tests exist; the suite is stdlib `unittest`, run with `python3 -m unittest discover -s tests -t .`.

## Findings

- Exclude semantics (item 3) differ from the existing `ignore`: `ignore` is a discovery-noise fnmatch filter; `exclude` is a deliberate, user-curated "never install here" list with an interactive guard on explicit targeting. Keeping them as separate keys avoids conflating the two intents.
- Alphabetical ordering (item 4) must be display-only. argparse preserves insertion order in `_choices_actions`; a custom formatter or a one-time sort of that list achieves alphabetical display without touching dispatch.
- Per-command descriptions (item 5): argparse shows `description=` at the top of a subcommand's own `--help`, and `help=` in the parent listing. Today all 51 subparsers set only `help=`, so `aw <cmd> --help` repeats the one-liner. Adding `description=` is additive and low-risk.

## Proposed changes (ordered, validatable)

1. Config: add + sanitize + expose the `exclude` list (E-01) and `expanded_excludes`.
2. Discovery: honor `exclude` (drop excluded repos from discovery/`install all`).
3. Install/setup: interactive colorized guard on explicitly targeting an excluded repo (continue `[Y/n]`, then optional unexclude `[Y/n]`); non-interactive skip.
4. CLI: add exclude-management verbs.
5. Help: alphabetical subcommand ordering (display-only formatter/sort).
6. Help: add a detailed `description=` to every subparser.

## Deferred / out of scope (with reason)

- Repo layout adoption/migration for THIS repo (the `.agents/` vs external roots question): deferred; the maintainer is authoring a separate IPD Set for the layout.
- Seeding the maintainer's three example excluded paths into config: deferred to the maintainer (they will add their own entries); we only document them as examples.
- Any change to workflow bodies, records routing, or storage backends: out of scope (CLI UX only).

## Scope check

- Over-scope: none.
- Under-scope: none known; the three items are self-contained CLI-UX changes.

## Required tests / validation

- `tests/test_config.py`: `exclude` round-trips load/save; unknown keys still stripped; `expanded_excludes` expands `~` and returns absolute paths.
- `tests/test_discovery.py` (or existing discovery test): an exact-path exclude and a glob exclude are both dropped from discovery/`install all`.
- Install-guard test: stub the prompt; explicitly targeting an excluded repo -> colorized warn + continue `[Y/n]`; decline changes nothing; accept proceeds and the unexclude `[Y/n]=yes` path removes the entry from config. Non-interactive/`--yes` skips an excluded repo with a clear message (no silent install).
- Exclude-verb test: add/list/rm round-trip.
- Help-ordering test: parse `aw --help` and each subgroup `--help`; assert command tokens are alphabetically sorted; assert dispatch of a mid- and end-alphabet command still works.
- Help-description test: every registered subparser (top-level + all subgroups) has a non-empty `description` that is distinct from and longer than its `help`.
- Full suite: `python3 -m unittest discover -s tests -t .` stays green (paste the `Ran N tests ... OK` summary). Leak-clean (`aw sanitize --agent`).

## Spec / documentation sync

- README: document the exclude list and the `aw` exclude-management verbs in the install section; note the interactive guard behavior.
- CHANGELOG (pending 2.0.0): add entries for the exclude list + guard, alphabetical help, and detailed per-command help.
- No formal spec governs the CLI help/exclude surface today; if one is added later it should reference these behaviors. (N/A otherwise.)

## Open questions

### OQ-01: Reuse `ignore` or add a distinct `exclude` key?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Add a DISTINCT `exclude` key. `ignore` is a discovery-only fnmatch noise filter; `exclude` is a deliberate user blocklist with an interactive guard. Conflating them would overload one key with two intents.

### OQ-02: Non-interactive behavior when an excluded repo is explicitly targeted (e.g. `--yes` or no tty)?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Proposed default: in non-interactive mode, SKIP an excluded repo with a clear message rather than install (fail-safe), unless a future explicit `--install-excluded` override flag is passed. Confirm this default at review; the interactive path (warn + `[Y/n]`) is already specified by the maintainer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a test showing a config with `exclude` round-trips load/save, unknown keys are stripped, and `expanded_excludes` returns absolute expanded paths.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. When asked to REVIEW or report, do not modify or commit. STOP and report if execution exceeds this plan's scope (CLI UX only: exclude list + guard, alphabetical help, detailed descriptions). The no-em/en-dash rule does NOT apply to this IPD (internal artifact, GUIDING_PRINCIPLES P13). Terminal transition (move to `executed/`) is a POST-gate transaction, not a checklist item. Never create or push a git tag, a GitHub Release, or a registry/PyPI upload.

This plan requires explicit human approval before execution (`Status: draft` -> `to-review` -> `reviewed` -> `approved`).

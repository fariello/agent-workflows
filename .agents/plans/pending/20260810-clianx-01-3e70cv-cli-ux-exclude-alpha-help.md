# IPD: CLI UX: repo exclude guard, alphabetical subcommands, and detailed per-command help

- Date: 2026-08-10
- Kind: child
- Concern: The `aw` CLI has three usability gaps: (1) no way to mark repos that must never receive an install; (2) `--help` lists subcommands in code-insertion order, not alphabetical, so they are hard to scan; (3) `aw <command> --help` shows only the same one-line summary as the parent listing, with no fuller description of what the command does.
- Scope: The `aw` CLI surface only: config schema + a repo exclude list consumed by discovery and by an interactive install guard; alphabetical ordering of subcommand listings in help; a fuller `description=` on each subparser so `aw <command> --help` is genuinely more informative. No workflow-body, records-layout, or storage-backend changes.
- Status: reviewed
- Set: clianx
- Order: 1
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 3e70cv

## Workflow history

- 2026-08-10 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-10 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed; OQ-02 resolved (non-interactive/--yes on an excluded repo skips with a message, no override flag). Status draft -> reviewed. GO - PENDING HUMAN APPROVAL.

## Goal

Make the `aw` CLI safer and easier to use: let a user permanently exclude specific repos from installation (with a colorized confirm-and-optionally-unexclude guard if someone explicitly installs into one anyway), present subcommands alphabetically in all `--help` listings, and give every subcommand a detailed `description=` so `aw <command> --help` explains what the command actually does.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Repo exclude list (config + discovery + interactive install guard)

- [ ] E-01 Add an `exclude` key to the config schema in `agent_workflows/config.py`: a list of repo path/glob entries, added to the fixed allowlist of recognized keys, defaulted to `[]` in `default_config()`, normalized/sanitized on load like `search_roots`/`repos`/`ignore` (expand `~`, coerce to str), and preserved on save. Add an `expanded_excludes(config)` helper (absolute, expanded paths) alongside `expanded_repos`/`expanded_search_roots`. Update the schema docstring.
  - Depends on: none
  - Expected outcome: a config carrying `exclude: ["/abs/path", "*/glob/*"]` round-trips through load/save; `expanded_excludes` returns absolute expanded paths; unknown-key stripping still holds.
  - Execution state: pending
- [ ] E-02 Make discovery honor the exclude list: in `agent_workflows/discovery.py`, add a NEW `excluded: List[Path]` field to the `Discovery` dataclass (discovery.py:30) and a `_is_excluded(path, exclude)` matcher (absolute-path equality OR fnmatch glob, mirroring `_is_ignored` at discovery.py:75). An excluded repo is dropped from `targets` and recorded in the new `excluded` list. Do NOT fold it into `ignored` (which is the discovery-only fnmatch NOISE filter): keeping `excluded` distinct from `ignored` preserves the two intents (deliberate blocklist vs noise) and avoids freezing an accidental shape (rubric D). Add `exclude` as a keyword arg to `discover(...)` (defaulting to `None`/`[]` for back-compat) and thread the config `exclude` list into the call site.
  - Depends on: E-01
  - Expected outcome: a repo whose path is in `exclude` never appears in `targets` and DOES appear in `Discovery.excluded`; `ignored` is unchanged in meaning; a unit test proves both an exact-path and a glob exclusion land in `excluded` (not `targets`, not `ignored`).
  - Execution state: pending
- [ ] E-03 Add an interactive install guard for an EXPLICITLY targeted excluded repo: when `aw install <path>` (or `setup`) targets a repo that matches the exclude list, print a COLORIZED warning (respecting `NO_COLOR`/`--no-color`/non-tty) that the repo is on the exclude list, and prompt `Continue anyway? [Y/n]` (default YES on empty input, since the user explicitly asked to install here). If the user declines, abort with a clear message and a "nothing changed" result (consistent with existing decline behavior). If the user accepts, THEN prompt `Remove <repo> from the exclude list? [Y/n]` (default NO); on yes, drop it from the config exclude list and save.
  - CRITICAL (do NOT reuse `_confirm` verbatim): the existing `_confirm(term, prompt, assume_yes)` (agent_workflows/cli.py:1078) returns `True` UNCONDITIONALLY when `assume_yes` is set, and `install --yes` sets `assume_yes`. Reusing it for this guard would make `aw install --yes <excluded>` auto-proceed, silently installing into an excluded repo, which is the OPPOSITE of the intended fail-safe. The non-interactive / `--yes` path for an excluded repo MUST always SKIP-WITH-MESSAGE (fail-safe, never auto-install), independent of `assume_yes`. Per OQ-02 (resolved) there is NO override flag: to install into an excluded repo the user must first `aw config exclude rm <path>` or use the interactive continue+unexclude path. Also `_confirm` renders `[y/N]` (default-No); the continue prompt needs default-YES, so add a default-yes prompt variant or an explicit `default` parameter rather than reusing `_confirm` as-is. `NO_COLOR`/`--no-color`/non-tty color suppression still applies to the warning.
  - Depends on: E-01
  - Expected outcome: explicitly installing into an excluded repo (interactive) triggers the colorized warn + default-yes `[Y/n]` continue prompt; declining changes nothing; accepting proceeds and then offers the default-no unexclude prompt; `aw install --yes <excluded>` (non-interactive) SKIPS with a message and does NOT install and does NOT mutate config; tests drive the decline branch, the accept+unexclude-yes branch (asserting the config entry is removed), and the `--yes` skip branch (asserting no install and no config mutation), all with a stubbed prompt.
  - Execution state: pending
- [ ] E-04 Add CLI verbs to manage the exclude list (surface it so it is usable without hand-editing config). NOTE (verified): there is NO existing `aw config` verb today; user config (`search_roots`) is managed only through `setup` / `install --search-root` flags (agent_workflows/cli.py:1779-1816), not a dedicated verb. So this INTRODUCES a new `aw config exclude {add,list,rm}` subcommand group (the smallest consistent surface): `add <path>` appends and saves, `list` prints the current exclude list, `rm <path>` removes and saves. Use `config.save()` and the recognized-key allowlist from E-01. Seed nothing automatically (per maintainer: they will add their own entries), but document a couple of generic EXAMPLE paths (e.g. `~/src/legacy-repo`, `~/src/vendored-tool`) in the command help/description. Do NOT hardcode the maintainer's real repo paths anywhere.
  - Depends on: E-01
  - Expected outcome: `aw config exclude add /path`, `aw config exclude list`, `aw config exclude rm /path` mutate and display the config exclude list; a test exercises the add/list/rm round-trip against a temp config.
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

### Plan-review findings (2026-08-10 /plan-review, opencode its_direct/pt3-claude-opus-4.8-1m-us)

- PR-001 (HIGH, IN-SCOPE): the existing `_confirm` helper (agent_workflows/cli.py:1078-1093) returns `True` unconditionally when `assume_yes` is set, and `install --yes` sets it. Naive reuse for the exclude guard would make `aw install --yes <excluded>` auto-install into an excluded repo, defeating the guard. FIXED: E-03 now forbids verbatim `_confirm` reuse, mandates a fail-safe SKIP-with-message for the non-interactive/`--yes` path, and requires a `--yes` skip test. This also makes OQ-02 blocking (resolved below).
- PR-002 (MEDIUM, UNDER-SCOPE): V-02..V-06 had placeholder "TODO falsifiable evidence". FIXED: each now specifies concrete, per-item evidence including the exact branches to prove and a pasted `Ran N tests ... OK` line.
- PR-003 (MEDIUM, IN-SCOPE): plan specifies `[Y/n]` default-yes prompts but `_confirm` renders `[y/N]` default-no. FIXED: E-03 now requires a default-yes prompt variant / explicit `default` param for the continue prompt (unexclude prompt stays default-no).
- PR-004 (LOW, IN-SCOPE): E-02 offered an ambiguous "excluded OR folded into ignored" shape. FIXED: E-02 now pins a distinct `Discovery.excluded` field, keeping it separate from noise-`ignored`.
- PR-005 (LOW, UNDER-SCOPE): E-04 implied an existing config-management verb; there is none. FIXED: E-04 now states it INTRODUCES a new `aw config exclude {add,list,rm}` group.

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
- Under-scope: two gaps found and FIXED in review: concrete V-02..V-06 evidence (PR-002) and the explicit new `aw config exclude` verb group (PR-005). No remaining under-scope.

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

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: This was blocking because a wrong default would let `aw install --yes <excluded>` silently install into an excluded repo (see PR-001). RESOLVED 2026-08-10 (maintainer, via /plan-review interactive prompt): non-interactive / `--yes` targeting an excluded repo SKIPS with a clear message and NEVER installs. NO override flag is added (no `--install-excluded`); to install into an excluded repo you must first `aw config exclude rm <path>` or use the interactive continue+unexclude path. This matches the existing "refuse to change things silently" non-interactive stance (agent_workflows/cli.py:1084). The guard MUST NOT route through the auto-yes `_confirm` (PR-001).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a test showing a config with `exclude` round-trips load/save, unknown keys are stripped, and `expanded_excludes` returns absolute expanded paths.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a `tests/test_discovery.py` run showing that a repo whose absolute path is in `exclude`, and a repo matched by an exclude GLOB, both appear in `Discovery.excluded` and NOT in `Discovery.targets`, while a non-excluded repo still lands in `targets`; and that `ignored` retains its prior meaning (an fnmatch-`ignore` entry is still recorded in `ignored`, not `excluded`). Paste the `Ran N tests ... OK` line.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste tests (stubbing the prompt) proving THREE branches: (a) interactive decline -> no install, config unchanged, clear message; (b) interactive accept + unexclude-yes -> install proceeds AND the repo is removed from the config `exclude` list (assert the saved config); (c) `aw install --yes <excluded>` (assume_yes / non-interactive) -> SKIPPED with a message, NO install performed, config NOT mutated (proving the guard does not route through the auto-yes `_confirm`). Paste the `Ran N tests ... OK` line.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste a test running `aw config exclude add <p>`, `list`, `rm <p>` against a temp config, asserting the exclude list contains `<p>` after add, prints it on list, and no longer contains it after rm (round-trip). Paste the `Ran N tests ... OK` line.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste a test that parses `aw --help` and each subgroup help (`aw ipd --help`, `aw research --help`, `aw project --help`, `aw storage --help`), extracts the listed command tokens, and asserts each list equals its own sorted order; PLUS a test that dispatch of a mid-alphabet command (e.g. `path`) and an end-alphabet command (e.g. `uninstall`, `storage`) still routes correctly (ordering is display-only). Paste the `Ran N tests ... OK` line.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste a test that enumerates every registered subparser (top-level + ipd/research/project/storage subgroups) and asserts each has a non-empty `description` that is DISTINCT from and longer than its `help`. Paste the `Ran N tests ... OK` line. (Also confirm `aw install --help` and one subgroup command show the fuller description in their output.)
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. When asked to REVIEW or report, do not modify or commit. STOP and report if execution exceeds this plan's scope (CLI UX only: exclude list + guard, alphabetical help, detailed descriptions). The no-em/en-dash rule does NOT apply to this IPD (internal artifact, GUIDING_PRINCIPLES P13). Terminal transition (move to `executed/`) is a POST-gate transaction, not a checklist item. Never create or push a git tag, a GitHub Release, or a registry/PyPI upload.

This plan requires explicit human approval before execution (`Status: draft` -> `to-review` -> `reviewed` -> `approved`).

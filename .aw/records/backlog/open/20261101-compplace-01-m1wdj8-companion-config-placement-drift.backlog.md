- Id: m1wdj8
- Status: open
- Blocks-Release: next
- Set: compplace
- Priority: medium
- Work-Kind: bug
- Summary: Companion preset leaves config_project untracked in the target and the companion directory is not a git repository, contrary to the companion-tracked placement contract

## Workflow history
- 2026-11-02 created (aw backlog): Companion preset leaves config_project untracked in the target and the companion directory is not a git repository, contrary to the companion-tracked placement contract

## Problem

The `public-target-private-companion` preset declares `config_project`, `state_durable` and `records` as `companion-tracked` (`project_schema.py` `PRESET_PLACEMENTS`), which the layout spec `20260810-1447-01` defines as "under `<companion>/.aw/` and intentionally tracked by the companion Git repository" (its placement list, line 94). The observed behavior does not match.

Probe, 2026-11-01, scratch directory with an isolated `AW_HOME`: `git init` a target, then `aw install --preset public-target-private-companion --yes --no-interactive` (exit 0). Observed:

1. `project.json` was written to `<target>/.aw/config/project.json`, NOT under the companion, and `git status` in the target showed it untracked (`?? .aw/config/`). Its own `placements` block says `"config_project": "companion-tracked"`. So the durable project config is tracked nowhere.
2. The resolver agrees with the install, not with the contract: `project_context.project_config_dir` returns `<repo>/.aw/config` whenever a `project.json` or `local.json` exists there, and `aw context` reported `config -> <target>/.aw/config`.
3. The companion directory `<target>.aw/` contained only `records/` and was not a git repository (`git log` there: "not a git repository"), so nothing `companion-tracked` is actually tracked.
4. No `companion_identity.json` was written (`storage.COMPANION_IDENTITY_RELPATH`), although `storage.create_companion_identity` exists to write a portable identity.
5. `local.json` recorded `"companion_dir": null`; the records root came from the `<repo>.aw` default in `resolve_project_context`.

Impact: a companion-backed project's durable configuration (preset, placements, cutovers, and any future tracked key such as the `federation` block of `c1f6rd`) does not survive a fresh clone or reach another machine. Federation (`c1f6rd` D8) refuses companion-backed peers until this is resolved.

## Required change

Decide which side is wrong, then make code, install, and spec agree:

- Either the contract holds: install creates or requires a companion git repository, writes `config_project` and `state_durable` under `<companion>/.aw/`, writes `companion_identity.json`, and `project_config_dir` resolves the companion location for a companion-backed project;
- or the contract changes: amend the layout spec so `config_project` is `target-tracked` for this preset, and make install leave it tracked in the target.

Acceptance: a pasted probe in a scratch directory showing, after install with this preset, where `project.json` lives, that `git ls-files` in the owning repository lists it, that the companion is (or is documented not to be) a git repository, and that `aw context` reports the same location; plus the full suite run bare as `python3 -m pytest`.

# IPD: Add aw oc opencode subcommand group dispatching to the packaged runner

- Date: 2026-08-24
- Kind: child
- Concern: With the runner core packaged (child 01), `aw` still has no way to invoke it. `aw`'s argparse tree (`agent_workflows/cli.py`) defines top-level subcommand groups via `p_<group> = sub.add_parser(...)` + `<group>_sub = p_<group>.add_subparsers(...)` (e.g. `p_ipd`/`ipd_sub` at cli.py:780) and dispatches in `main()` via `if args.command == "<group>"` (cli.py:6786 for ipd). A new host group is required to surface `aw oc runipd`.
- Scope: Add an `oc` top-level subcommand group (alias `opencode`, mirroring the `ipd`/`plan`/`plans` aliasing) to `agent_workflows/cli.py`, with a `runipd` subcommand whose arguments mirror the packaged runner's argparse surface, dispatching into `agent_workflows.oc_runipd`. Add a CLI-parity test. Child 02 of the awocrunner Set; depends on child 01.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/oc_runipd.py, tests/test_oc_runipd_cli.py
- Status: to-review
- Set: awocrunner
- Order: 2
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: nfo184

## Workflow history
- 2026-08-25 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): Completed drafting: fully authored, lint-conforming, ready to critique

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; child 02 of awocrunner Set (aw oc/opencode subcommand group).

## Goal

Expose the packaged runner as `aw oc runipd` (alias `aw opencode runipd`) with CLI parity to the standalone script, so any installed `aw` can review/execute IPD queues.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Expose runipd's argparse for reuse

- [ ] E-01 In `agent_workflows/oc_runipd.py`, ensure the runner's argparse construction is exposed as a reusable function (e.g. `build_parser()` returning the configured parser, and a `run(args)`/`main(argv)` entry) so the CLI group can attach the same subcommands/options without duplicating flag definitions. If child 01 already left `main(argv)`/`build_parser()` usable, this is a no-op verification; otherwise refactor minimally to expose them (still behavior-preserving).
  - Depends on: none
  - Expected outcome: `oc_runipd.build_parser()` (or equivalent) is importable and produces the runner's full CLI (start/resume/status/report + options).
  - Execution state: pending

### Task group 2: Wire the aw oc / aw opencode group

- [ ] E-02 In `agent_workflows/cli.py`, add a top-level `oc` subparser (with `opencode` as an alias, following the existing `ipd`/`plan`/`plans` alias pattern) and an `oc`-level subparsers group with a `runipd` subcommand that mirrors the runner's options; in `main()`, add `if args.command in ("oc", "opencode"):` dispatch that forwards the parsed args into `agent_workflows.oc_runipd`. Reuse the runner's flag definitions from E-01 rather than re-declaring them, to guarantee parity.
  - Depends on: E-01
  - Expected outcome: `aw oc runipd ...` and `aw opencode runipd ...` invoke the packaged runner; `aw oc runipd --help` shows the runner's subcommands/options.
  - Execution state: pending

### Task group 3: CLI-parity test

- [ ] E-03 Add `tests/test_oc_runipd_cli.py` asserting: `aw oc runipd --help` and `aw opencode runipd --help` succeed; a non-mutating invocation (e.g. `status`/`report` against a fixture run dir under a temp repo) produces the same result as calling `oc_runipd.main([...])` directly; and the `oc`/`opencode` alias pair resolve to the same handler.
  - Depends on: E-01, E-02
  - Expected outcome: passing test proving the subcommand path and the packaged `main` are the same behavior, across both aliases.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Subcommand-group pattern: `p_<group> = sub.add_parser("<group>", ...)`; `<group>_sub = p_<group>.add_subparsers(dest="<group>_command")`; dispatched in `main()` by `if args.command == "<group>":` (see `p_ipd`/`ipd_sub` at cli.py:780 and dispatch at cli.py:6786). Aliases are handled by `if args.command in ("ipd", "plan", "plans")`.
- The `aw` entrypoint is `agent_workflows.cli:main` (pyproject.toml:48-49).
- `aw ipd execute-set` (`ipd_set_plan.run_execute_set`, dispatched cli.py:6813-6816) is the precedent for a cli.py handler that delegates into a packaged runner module.
- Contributor contract: path-scoped commits only, no push, no em/en dashes in user-facing prose.

## Findings

| ID | Severity | Persona | Finding |
|---|---|---|---|
| F-01 | High | Toolkit user | No `aw` subcommand reaches the packaged runner; a host group (`oc`/`opencode`) with a `runipd` subcommand is required. |
| F-02 | Med | Maintainer | Re-declaring the runner's flags in cli.py would risk drift; the CLI group must reuse the runner's own parser to guarantee parity. |

## Proposed changes (ordered, validatable)

1. Expose/confirm a reusable `build_parser()`/`main(argv)` in `oc_runipd`.
2. Add the `aw oc`/`aw opencode` group + `runipd` subcommand in cli.py, dispatching into `oc_runipd`.
3. Add a CLI-parity test across both aliases.

## Deferred / out of scope (with reason)

- Additional `oc` subcommands beyond `runipd` are out of scope; only `runipd` graduates in this Set.
- Antigravity (`aw agy ...`), `pwatch`, and output normalization are the deferred backlog (child 04), not this child.

## Scope check

- Over-scope: none. Confined to the CLI group wiring, a minimal parser-exposure in `oc_runipd`, and the parity test.
- Under-scope: none. Delivers a fully usable `aw oc runipd`/`aw opencode runipd` with a parity guard.

## Required tests / validation

- `python3 -m pytest tests/test_oc_runipd_cli.py` green.
- Manual: `aw oc runipd --help`, `aw opencode runipd --help`, and `aw oc runipd status <run-id>` on a fixture run dir behave identically to `python3 -m agent_workflows.oc_runipd status <run-id>`.
- `python3 -m pytest tests/` green overall.
- `pre-commit run --files agent_workflows/cli.py agent_workflows/oc_runipd.py tests/test_oc_runipd_cli.py`.

## Spec / documentation sync

- User-facing docs are child 04. If cli.py carries a command-catalog/help-metadata table (as it does for other groups), add the `oc`/`opencode` + `runipd` entries there so `aw --help` lists it.

## Open questions

### OQ-01: Should `oc` be the canonical name with `opencode` the alias, or vice versa?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: RESOLVED: `oc` canonical, `opencode` alias, matching the tool's conventional shorthand and the existing short-canonical/long-alias precedent. Non-blocking; both resolve to the same handler.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: snippet showing `oc_runipd.build_parser()`/`main` importable and producing the runner CLI.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw oc runipd --help` and `aw opencode runipd --help` output showing the runner subcommands/options.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `python3 -m pytest tests/test_oc_runipd_cli.py` output showing the parity + alias tests passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (surface the packaged runner as `aw oc runipd`), reusing the runner's own parser for parity, with a parity test.

### Execution contract

1. Open questions RESOLVED: OQ-01 resolved (`oc` canonical, `opencode` alias). No blocking open question remains.
2. Scope fence: touch ONLY `agent_workflows/cli.py`, `agent_workflows/oc_runipd.py` (minimal parser exposure only), and `tests/test_oc_runipd_cli.py`. Reuse the runner's parser; do NOT re-declare its flags. Do NOT modify the runner's behavior/output or the `tools/` shim (child 03). If a fix seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/checks passed, paste the ACTUAL runner output (`python3 -m pytest ...`, the `--help` output); never claim a pass from narration or an unchecked box.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the lifecycle workflow).

# IPD: Accept --repo as an alias of --dir on aw runs so the run footer's hints compose

- Date: 2026-09-26
- Kind: child
- Concern: `aw runs <run-id> --repo X` FAILS with `aw runs: error: unrecognized arguments: --repo X` (re-measured at HEAD `61ef21d8`; `aw runs show run-x --repo /tmp` fails the same way), while `aw oc run` spells the same concept `--repo` ("Target Git repository root"). The runner's own closing footer (`runner_shared.render_continuation_hint`) prints `aw runs {run_id}` on the success path and `{cmd} resume --repo {repo} {run_id}` on the resume path, and `runner_shared` also prints "Run `aw runs <run-id>` for more info.", so an operator working on a repository other than the current directory naturally carries `--repo` across and hits the error. Every `aw runs` parser site accepts only `--dir`: the shared `_runs_viewer_flags` parent (bare `aw runs` and `aw runs list`), `_register_run_leaf` (the `runs` leaves `show`, `evidence`, `verify-ledger`, `next`, `resume`, `status`, `decisions`, `questions`), and the separately registered `runs analyze`, `runs query`, `runs export`, `runs submit` parsers, all in `cli._build_parser`. Every consumer reads `getattr(args, "dir", None)` (`run_viewer`, `run_cli`, `run_analytics_cli`).
- Scope: IN: (a) add `"--repo"` as a SECOND option string on each existing `--dir` argument under `aw runs`, with `dest="dir"` so every consumer is untouched: `_runs_viewer_flags`, `_register_run_leaf` (which also serves the `aw run` writing leaves `start`/`record`/`cancel`/`finalize`, which gain the alias too, since one helper registers both nouns), and the `runs analyze`/`runs query`/`runs export`/`runs submit` parsers; (b) add `"--repo"` to the `legacy_flags` of every `COMMAND_INVENTORY` declaration in `command_surface` that already lists `"--dir"` for one of those leaves (today only `runs list`), so the declared surface names the accepted spelling; (c) behavioral tests that parse real argv through `cli._build_parser()` and assert `args.dir`. OUT: adding `--dir` to `aw oc run` / `aw agy run` (deferred, see below); renaming either flag; changing any other command family's `--dir`.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_runs_repo_alias.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: tqaxjw
- Set: runsrepo
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8y13kn

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog tqaxjw. Authored review-ready; the --repo refusal and every aw runs parser site were re-measured at HEAD 61ef21d8 by walking cli._build_parser().
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Let `aw runs` (and its leaves) accept `--repo` as a backward-compatible alias of `--dir`, so the invocation an operator copies from `aw oc run`'s footer works without editing the flag.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE at the executing HEAD. Run `aw runs run-x --repo /tmp` and `aw runs show run-x --repo /tmp` and paste the errors. Walk `cli._build_parser()` recursively and print, for every parser whose path starts with `runs` or `run`, the option strings among `--dir`/`--repo` it accepts. If any `runs` parser already accepts `--repo`, drop it from E-02/E-03 and say so.
  - Depends on: none
  - Expected outcome: both commands fail with `unrecognized arguments: --repo /tmp`; every `runs *` parser and `run start|record|cancel|finalize` list `['--dir']` only.
  - Execution state: pending

### Task group 2: add the alias

- [ ] E-02 ADD `"--repo"` to the shared viewer flags and the ledger leaves: in `cli._build_parser`, change `_runs_viewer_flags.add_argument("--dir", ...)` and `_register_run_leaf`'s `_pr.add_argument("--dir", ...)` to `add_argument("--dir", "--repo", dest="dir", default=None, help=...)`, appending to the help text that `--repo` is accepted as an alias matching `aw oc run`. Carry a comment citing `tqaxjw` and noting the alias is additive (no existing invocation changes).
  - Depends on: E-01
  - Expected outcome: `aw runs --repo X`, `aw runs <id> --repo X`, `aw runs list --repo X`, and `aw runs show <id> --repo X` parse with `args.dir == X`.
  - Execution state: pending

- [ ] E-03 ADD `"--repo"` to the four separately registered `runs` leaves (`_p_runs_analyze`, `_p_runs_query`, `_p_runs_export`, `_p_runs_submit`) in the same form (`"--dir", "--repo", dest="dir"`), so no `aw runs` leaf is left refusing the spelling its siblings accept.
  - Depends on: E-01
  - Expected outcome: `aw runs analyze|query|export|submit ... --repo X` parse with `args.dir == X`.
  - Execution state: pending

- [ ] E-04 DECLARE THE ALIAS in `command_surface.COMMAND_INVENTORY`: for each declaration of a leaf touched by E-02/E-03 whose `legacy_flags` already contains `"--dir"` (at HEAD, `runs list`), add `"--repo"` immediately after it. Do not add `"--dir"` to declarations that do not already list it (that is a pre-existing omission outside this plan). Confirm `tests/test_command_surface_declarations.py` still passes.
  - Depends on: E-02, E-03
  - Expected outcome: `command_surface.get_declaration("runs list").legacy_flags` contains both `--dir` and `--repo`; `test_zero_undeclared_parser_leaves` passes.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 ADD `tests/test_runs_repo_alias.py`, behavioral only (no source-text pins, per the maintainer's 2026-09-26 ruling). For each of the argv shapes `["runs", "--repo", R]`, `["runs", "run-x", "--repo", R]`, `["runs", "list", "--repo", R]`, `["runs", "show", "run-x", "--repo", R]`, `["runs", "status", "run-x", "--repo", R]`, `["runs", "analyze", "--repo", R]`, `["runs", "query", "schema", "--repo", R]`, `["runs", "export", "--repo", R]`, parse with `cli._build_parser().parse_args(argv)` and assert `args.dir == R`; repeat with `--dir` as a control. Add one END-TO-END case: create a temp repo with an empty `.aw/records/runs/`, run `cli.main(["runs", "--repo", str(tmp)])` capturing output, and assert the exit code is not the argparse usage-error code 2 and the output does not contain `unrecognized arguments`. Add a declaration case: every flag in `get_declaration("runs list").legacy_flags` is accepted by the `runs list` parser (the same shape `tests/test_prompts_new.py::test_the_declared_flag_surface_matches_the_parser` uses).
  - Depends on: E-04
  - Expected outcome: all `--repo` cases and the end-to-end case FAIL before E-02/E-03 and pass after; the `--dir` controls pass before and after.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `aw runs` and `aw runs list` share ONE flag parent, `_runs_viewer_flags`, so the bare viewer and the leaf "cannot drift apart" (comment at its definition, runnamecollapse `0soncw` E-03). Adding the alias there covers both.
- `_register_run_leaf` registers leaves on BOTH `runs_sub` (reading leaves in `_RUNS_VIEWER_LEAVES`) and `run_sub` (writing leaves), so the alias reaches `aw run start|record|cancel|finalize` too. That is consistent (both nouns name a repository root) and is stated in Scope rather than hidden.
- Consumers read `getattr(args, "dir", None)` (`run_viewer.run_viewer_cli`, `run_cli`, `run_analytics_cli`), so `dest="dir"` keeps every read site unchanged.
- `COMMAND_INVENTORY` declares leaves; `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` checks every parser leaf has a declaration, not flag-by-flag equality, so option strings can be added without breaking it; `legacy_flags` is updated anyway so the declared surface is truthful.
- Tests run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`. Tests are behavioral only (maintainer ruling 2026-09-26).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `61ef21d8`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | LOW | `cli._build_parser`, `aw runs` | `--repo` is refused on the bare viewer and every leaf. | `aw runs run-x --repo /tmp` -> `aw runs: error: unrecognized arguments: --repo /tmp` |
| F-2 | LOW | `runner_shared.render_continuation_hint` | The footer prints `aw runs {run_id}` beside `{cmd} resume --repo {repo} {run_id}`, teaching both spellings side by side. | `lines.append(f"  aw runs {run_id}")` / `lines.append(f"  {cmd} resume --repo {repo} {run_id}")` |
| F-3 | INFO | parser walk | Every `runs *` parser (13 leaves plus the root) and `run start|record|cancel|finalize` accept `--dir` only. | recursive walk printed `['--dir']` for each |
| F-4 | INFO | `command_surface` | Only `runs list` lists `--dir` in `legacy_flags`; the other `runs` declarations list `("--agent", "--json")` or workflow flags. | `rg -n '"--dir"' agent_workflows/command_surface.py` |

## Proposed changes (ordered, validatable)

1. E-01 re-measures.
2. E-02 adds the alias on the shared parent and the ledger-leaf helper.
3. E-03 adds it on the four separately registered leaves.
4. E-04 declares it where `--dir` is declared.
5. E-05 adds parse-level and end-to-end behavioral tests.

## Deferred / out of scope (with reason)

- Adding `--dir` as an alias on `aw oc run` / `aw agy run` (the reverse direction the backlog item suggests).
  - Carrier-Declined: a whole-CLI naming review is under way (research `ffi66q`, the live-parser command inventory prepared as input to it), and which spelling the runner families adopt is a CLI-contract decision for that review, not for this friction fix. This plan only removes the failure an operator actually hits.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/runner_shared.py` (the footer) is deliberately NOT changed: once `--repo` is accepted, its hints compose as written.
- Scope-Paths justification: `cli.py` holds every parser site; `command_surface.py` holds the declaration; the new test file holds E-05.

## Required tests / validation

- `tests/test_runs_repo_alias.py` (new): eight `--repo` parse cases with `--dir` controls, one end-to-end `cli.main` case, one declaration-matches-parser case.
- `python3 -m pytest -o addopts="" -q tests/test_command_surface_declarations.py` stays green.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- N/A for specs: no spec enumerates `aw runs` flags (grep of `.aw/records/specs/` for `aw runs --dir` finds nothing). No `.spec.md` is in `- Scope-Paths:`.
- The help text itself documents the alias; the `_RUNS_EPILOG` examples use no repo flag and need no change.

## Open questions

### OQ-01: Should the alias be added in the other direction (`--dir` on `aw oc run`) in the same plan?

- Blocking: no
- Status: resolved
- Owner: maintainer (via the graduation brief), 2026-09-26
- Resolution or deferral rationale: No. Maintainer ruling 2026-09-26 in the graduation brief: that direction is a CLI-contract choice and is deferred with a Carrier-Declined reason because a whole-CLI naming review is under way (research `ffi66q`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste both `unrecognized arguments` errors and the parser-walk output with the HEAD hash.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of the two `add_argument` calls and `aw runs --repo <tmp>` plus `aw runs show run-x --repo <tmp>` now failing (if at all) on the missing run rather than on `unrecognized arguments`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff for the four leaves and the parser walk re-run showing every `runs *` parser listing both `--dir` and `--repo`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `command_surface` diff and `python3 -m pytest -o addopts="" -q tests/test_command_surface_declarations.py` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_runs_repo_alias.py` passing with its count; the same run with E-02/E-03 temporarily reverted showing the `--repo` and end-to-end cases FAILING and the `--dir` controls passing; then the bare `python3 -m pytest` summary line before and after with the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. `aw runs` and all its leaves (plus the `aw run` ledger-writing leaves, which share the same helper) accept `--repo` as an alias of `--dir`, stored in the same `args.dir`, so nothing that reads the flag changes and every existing invocation keeps working. The reverse alias on `aw oc run` is deliberately left to the CLI naming review.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/cli.py` (the `--dir` arguments of the `runs` family and `_register_run_leaf`), `agent_workflows/command_surface.py` (the `legacy_flags` of declarations already listing `--dir` for those leaves), and the new `tests/test_runs_repo_alias.py`. Any edit outside the declared paths is justified at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-05 must show the new `--repo` cases FAILING before the change.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `tqaxjw` `done` with `--evidence` citing the executed plan.

# IPD: Accept --repo as an alias of --dir on aw runs so the run footer's hints compose

- Date: 2026-09-26
- Kind: child
- Concern: `aw runs <run-id> --repo X` FAILS with `aw runs: error: unrecognized arguments: --repo X` (re-measured at HEAD `61ef21d8`; `aw runs show run-x --repo /tmp` fails the same way), while `aw oc run` spells the same concept `--repo` ("Target Git repository root"). The runner's own closing footer (`runner_shared.render_continuation_hint`) prints `aw runs {run_id}` on the success path and `{cmd} resume --repo {repo} {run_id}` on the resume path, and `runner_shared` also prints "Run `aw runs <run-id>` for more info.", so an operator working on a repository other than the current directory naturally carries `--repo` across and hits the error. Every `aw runs` parser site accepts only `--dir`: the shared `_runs_viewer_flags` parent (bare `aw runs` and `aw runs list`), `_register_run_leaf` (the `runs` leaves `show`, `evidence`, `verify-ledger`, `next`, `resume`, `status`, `decisions`, `questions`), and the separately registered `runs analyze`, `runs query`, `runs export`, `runs submit` parsers, all in `cli._build_parser`. Every consumer reads `getattr(args, "dir", None)` (`run_viewer`, `run_cli`, `run_analytics_cli`).
- Scope: IN: (a) add `"--repo"` as a SECOND option string on each existing `--dir` argument under `aw runs`, with `dest="dir"` so every consumer is untouched: `_runs_viewer_flags`, `_register_run_leaf` (which also serves the `aw run` writing leaves `start`/`record`/`cancel`/`finalize`, which gain the alias too, since one helper registers both nouns), and the `runs analyze`/`runs query`/`runs export`/`runs submit` parsers; (b) add `"--repo"` to the `legacy_flags` of every `COMMAND_INVENTORY` declaration in `command_surface` that already lists `"--dir"` for one of those leaves (today only `runs list`), so the declared surface names the accepted spelling; (c) behavioral tests that parse real argv through `cli._build_parser()` and assert `args.dir`. OUT: adding `--dir` to `aw oc run` / `aw agy run` (deferred, see below); renaming either flag; changing any other command family's `--dir`.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_runs_repo_alias.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: tqaxjw
- Set: runsrepo
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8y13kn

## Workflow history
- 2026-09-26 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901..PR-906 all FIXED. All four of the plan's findings hold, including F-3's exact leaf count (13 `runs` leaves plus the root), and both cited artifacts resolve. Review did not stop at the diagnosis: it APPLIED the six-site change, measured it, and reverted it, leaving `cli.py` byte-unchanged - the coverage walk returned an EMPTY violation set, ten argv shapes parsed to the same `args.dir`, `runs --repo <tmp>` exited 0 with output identical to `--dir`, the help line rendered `--dir, --repo DIR` with no help-string edit, and the bare suite held at `2436 passed, 1 skipped`. So the approach is demonstrated, recorded as F-5. The gaps were elsewhere. PR-901: the plan never checked that the alias becomes VISIBLE, although discoverability is its entire purpose; added E-06 (argparse renders it automatically, as the sibling `--last, --latest, -l` line in the same parser shows, but nothing would have noticed otherwise). PR-903: review lost a cycle to `aw` importing `agent_workflows` from a DIFFERENT checkout and showing stale help, so E-01/E-06 now mandate the in-tree route and a banner check. PR-904: neither check named for E-04 can detect a missing declaration (`find_undeclared_leaves` is about leaves; `declared - accepted` passes for a subset), so V-04 asserts the tuple directly. PR-902: the declared cross-noun widening to the four `aw run` writing leaves had no test; E-05 now covers it plus a derived coverage walk. PR-905: F-3's row had unescaped pipes (9 cells, not 6); while fixing it review mis-corrected the leaf count and caught itself by re-running the walk, so the plan's original number stands. 5 items -> 6 with a 6:6 E/V bijection. Review record: `.aw/records/reviews/20260926-runsrepo-01-8y13kn-accept-repo-as-an-alias-of-dir-on-aw-runs-so-the-run-footer.review.md`.
- 2026-09-26 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED; PR-901..PR-906 all FIXED. All four findings hold; review APPLIED the six-site change, measured it (empty coverage-violation set, 10 argv shapes, end-to-end exit 0, help renders --dir/--repo, 2436 passed) and reverted it. 5 items -> 6.

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog tqaxjw. Authored review-ready; the --repo refusal and every aw runs parser site were re-measured at HEAD 61ef21d8 by walking cli._build_parser().
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Let `aw runs` (and its leaves) accept `--repo` as a backward-compatible alias of `--dir`, so the invocation an operator copies from `aw oc run`'s footer works without editing the flag.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE at the executing HEAD. Run `aw runs run-x --repo /tmp` and `aw runs show run-x --repo /tmp` and paste the errors. Walk `cli._build_parser()` recursively and print, for every parser whose path starts with `runs` or `run`, the option strings among `--dir`/`--repo` it accepts. MEASURE THE IN-TREE PACKAGE, and check for the mismatch banner before trusting any `aw` output (review PR-903): `aw` may import `agent_workflows` from a DIFFERENT checkout and prints `aw: invoked in checkout ... but imported agent_workflows from ...` on stderr when it does. Review lost a cycle to exactly this, reading a stale `--help` that still showed bare `--dir` after the change was applied in-tree. When the banner appears, re-run through `python3 -m agent_workflows ...` or drive `cli._build_parser()` in-process, and say in the evidence which route produced each number. When deduplicating the parser walk, key on `id(subparser)` rather than on the choice NAME, since aliases map several names to one parser object. If any `runs` parser already accepts `--repo`, drop it from E-02/E-03 and say so.
  - Depends on: none
  - Expected outcome: both commands fail with `unrecognized arguments: --repo /tmp` (review measured exit 2 for the first and the same error via the top-level parser for the second); every `runs *` parser and `run start|record|cancel|finalize` list `['--dir']` only - review's walk printed exactly that for 15 `runs` paths plus 4 `run` writing leaves, with `run`, `run as` and `run ipd` accepting neither.
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

- [ ] E-04 DECLARE THE ALIAS in `command_surface.COMMAND_INVENTORY`: for each declaration of a leaf touched by E-02/E-03 whose `legacy_flags` already contains `"--dir"` (at HEAD, `runs list` is the ONLY one - review confirmed by iterating `get_all_declarations()`: the other seven `--dir` declarations are `normalize-lanes`, `ipd execute-set`, `ipd recheck-readiness`, `ipd begin`, `ipd finalize`, `work begin` and `finish`, none of which this plan touches), add `"--repo"` immediately after it. Do not add `"--dir"` to declarations that do not already list it (that is a pre-existing omission outside this plan). Confirm `tests/test_command_surface_declarations.py` still passes. BE HONEST ABOUT WHAT THAT PROVES: nothing. Review measured that the shipped test asserts only `find_undeclared_leaves(...) == set()` (undeclared LEAVES, not flags), and that E-05's declared-flags-vs-parser case checks only `declared - accepted == set()`, which is satisfied whether or not `--repo` is declared. So this item is verified ONLY by V-04's direct assertion on the tuple; do not report a green suite as evidence for it.
  - Depends on: E-02, E-03
  - Expected outcome: `command_surface.get_declaration("runs list").legacy_flags` contains both `--dir` and `--repo`; `test_zero_undeclared_parser_leaves` passes (while proving nothing about the flag - see above).
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 ADD `tests/test_runs_repo_alias.py`, behavioral only (no source-text pins, per the maintainer's 2026-09-26 ruling). For each of the argv shapes `["runs", "--repo", R]`, `["runs", "run-x", "--repo", R]`, `["runs", "list", "--repo", R]`, `["runs", "show", "run-x", "--repo", R]`, `["runs", "status", "run-x", "--repo", R]`, `["runs", "analyze", "--repo", R]`, `["runs", "query", "schema", "--repo", R]`, `["runs", "export", "--repo", R]`, `["runs", "submit", "--repo", R]`, parse with `cli._build_parser().parse_args(argv)` and assert `args.dir == R`; repeat with `--dir` as a control. ADD `["run", "start", "run-x", "--repo", R]` (review PR-902): `_register_run_leaf` serves BOTH nouns, so the `aw run` writing leaves gain the alias whether or not anyone intended it, and a declared consequence with no test is an undeclared one. Add a COVERAGE case that derives the surface instead of trusting this list: walk `cli._build_parser()` and assert that EVERY parser whose path starts with `runs` or `run` and which accepts `--dir` ALSO accepts `--repo` - review ran exactly this walk and it returns an empty violation set once E-02/E-03 land, so a leaf added later cannot silently regress. Add one END-TO-END case: create a temp repo with an empty `.aw/records/runs/`, run `cli.main(["runs", "--repo", str(tmp)])` capturing output, and assert the exit code is not the argparse usage-error code 2 and the output does not contain `unrecognized arguments` (review measured exit 0 with `no matching runs found`, identical to the `--dir` spelling). Add a declaration case asserting BOTH directions on `get_declaration("runs list")`: every declared flag is accepted by the parser (the `tests/test_prompts_new.py::test_the_declared_flag_surface_matches_the_parser` shape) AND `"--repo"` is present in `legacy_flags`; the second half is required because the first passes with or without E-04 (review measured `declared - accepted == set()` already).
  - Depends on: E-04
  - Expected outcome: all `--repo` cases, the `run start` case, the coverage walk, and the end-to-end case FAIL before E-02/E-03 and pass after; the `--dir` controls pass before and after; the declaration case's `--repo` half fails before E-04.
  - Execution state: pending

- [ ] E-06 CONFIRM THE HELP TEXT ACTUALLY ADVERTISES THE ALIAS, since discoverability is this plan's entire point and an alias nobody can see only half fixes it (review PR-901). `argparse` renders multiple option strings on one line automatically, so `--dir, --repo DIR` should appear with no extra work; VERIFY it rather than assuming, by capturing `cli._build_parser()`'s `runs` help and asserting the rendered line names both spellings, then doing the same for one `_register_run_leaf` leaf and one separately-registered leaf. Use the IN-TREE parser (`python3 -m agent_workflows ...` or `_build_parser().format_help()`), NOT a bare `aw`: review wasted a cycle reading stale output because `aw` can import `agent_workflows` from a DIFFERENT checkout and says so on stderr (`aw: invoked in checkout ... but imported agent_workflows from ...`). Review confirmed the in-tree render is `  --dir, --repo DIR     Target Git repository root (default: current directory).` If the alias does NOT render, stop and report rather than hand-editing help strings.
  - Depends on: E-05
  - Expected outcome: the `runs` help line reads `--dir, --repo`; the same for a ledger leaf and a separately-registered leaf; no help string is hand-edited to achieve it.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `aw runs` and `aw runs list` share ONE flag parent, `_runs_viewer_flags`, so the bare viewer and the leaf "cannot drift apart" (comment at its definition, runnamecollapse `0soncw` E-03). Adding the alias there covers both.
- `_register_run_leaf` registers leaves on BOTH `runs_sub` (reading leaves in `_RUNS_VIEWER_LEAVES`) and `run_sub` (writing leaves), so the alias reaches `aw run start|record|cancel|finalize` too. That is consistent (both nouns name a repository root) and is stated in Scope rather than hidden.
- Consumers read `getattr(args, "dir", None)` (`run_viewer.run_viewer_cli`, `run_cli`, `run_analytics_cli`), so `dest="dir"` keeps every read site unchanged.
- `COMMAND_INVENTORY` declares leaves; `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` checks every parser leaf has a declaration, not flag-by-flag equality, so option strings can be added without breaking it; `legacy_flags` is updated anyway so the declared surface is truthful. COROLLARY THE PLAN ORIGINALLY MISSED (review F-7): because no shipped check compares `archive`-style declared flags to the parser in BOTH directions, E-04's declaration edit is verified only by asserting the tuple directly. Do not treat a green suite as evidence for it.
- ARGPARSE RENDERS MULTIPLE OPTION STRINGS ON ONE HELP LINE, so the alias is self-documenting and no help string needs hand-editing to advertise it. The precedent is in the very parser being changed: `_runs_viewer_flags` already declares `--last`, `--latest`, `-l` on one argument and `--ipd`, `--id6` on another, rendering as `--last, --latest, -l [N]` and `--ipd, --id6 IPD`. Review confirmed the new line renders as `--dir, --repo DIR`.
- MEASURE THROUGH THE IN-TREE PACKAGE. `aw` may import `agent_workflows` from a different checkout, announcing it on stderr as `aw: invoked in checkout <A> but imported agent_workflows from <B>`; in this worktree that banner is present on every invocation. Use `python3 -m agent_workflows ...` or drive `cli._build_parser()` in-process when the measurement is about code you just changed (review F-8).
- Tests run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`. Tests are behavioral only (maintainer ruling 2026-09-26).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `61ef21d8`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | LOW | `cli._build_parser`, `aw runs` | `--repo` is refused on the bare viewer and every leaf. | `aw runs run-x --repo /tmp` -> `aw runs: error: unrecognized arguments: --repo /tmp` |
| F-2 | LOW | `runner_shared.render_continuation_hint` | The footer prints `aw runs {run_id}` beside `{cmd} resume --repo {repo} {run_id}`, teaching both spellings side by side. | `lines.append(f"  aw runs {run_id}")` / `lines.append(f"  {cmd} resume --repo {repo} {run_id}")` |
| F-3 | INFO | parser walk | Every `runs *` parser and the four `run` writing leaves (`start`, `record`, `cancel`, `finalize`) accept `--dir` only. Review re-ran the walk and CONFIRMS the count exactly: 13 `runs` leaves plus the `runs` root accept `--dir` (`show`, `evidence`, `verify-ledger`, `next`, `resume`, `status`, `decisions`, `questions`, `list`, `analyze`, `query`, `export`, `submit`), while `run`, `run as` and `run ipd` accept neither flag. The cell's pipes were unescaped, which broke this table row; rewritten as a list. | recursive walk printed `['--dir']` for each; review's walk deduplicated on `id(subparser)` so alias names are not double-counted, and returned 14 `runs` paths = 13 leaves + root |
| F-4 | INFO | `command_surface` | Only `runs list` lists `--dir` in `legacy_flags`; the other `runs` declarations list `("--agent", "--json")` or workflow flags. | grep of `--dir` in `agent_workflows/command_surface.py`; review enumerated `get_all_declarations()` and confirmed the eight `--dir` declarations are `runs list` plus `normalize-lanes`, `ipd execute-set`, `ipd recheck-readiness`, `ipd begin`, `ipd finalize`, `work begin`, `finish` - only the first is in scope |
| F-5 | INFO | the approach, PROVEN by review probe | THE FIX WORKS EXACTLY AS SPECIFIED, applied and measured rather than reasoned about. Review implemented all six sites (`"--dir", "--repo", dest="dir"`), re-walked the parser, and every `runs`/`run` parser that accepts `--dir` then accepted `--repo` with an EMPTY violation set; ten argv shapes parsed to `args.dir == R`; the three `--dir` controls still parsed; the end-to-end `runs --repo <tmp>` exited 0 with `no matching runs found`, byte-identical to the `--dir` spelling; the bare suite stayed at `2436 passed, 1 skipped`; `tests/test_command_surface_declarations.py` passed. The probe was reverted and `agent_workflows/cli.py` is byte-unchanged. | Review probe at HEAD `47c0e0ca`, reverted with `git checkout` |
| F-6 | MED | help discoverability (review PR-901) | THE PLAN NEVER CHECKS THAT THE ALIAS IS VISIBLE, which matters because discoverability IS the concern: an operator who cannot see `--repo` in `--help` has no reason to try it. Review confirmed `argparse` renders both spellings automatically (the sibling `--last, --latest, -l [N]` line in the same parser proves the pattern ships already), and measured the in-tree render as `--dir, --repo DIR`. So nothing extra is needed - but it must be VERIFIED, not assumed, hence E-06. | In-tree `format_help()` after the probe: `  --dir, --repo DIR     Target Git repository root (default: current directory).`; pre-existing precedent `--last, --latest, -l [N]` in `_runs_viewer_flags` |
| F-7 | MED | E-04's and E-05's declaration evidence (review PR-904) | NEITHER NAMED CHECK CAN DETECT A MISSING DECLARATION. `tests/test_command_surface_declarations.py` holds one test asserting `find_undeclared_leaves(...) == set()`, which is about LEAVES and not flags. E-05's declared-flags case (the `prompts new` shape) asserts `declared - accepted == set()`, which is satisfied whether or not `--repo` is declared, since a declared subset of an accepted set always passes. So E-04 could be skipped entirely with every named check still green. | Review measured `set(get_declaration("runs list").legacy_flags) - accepted == set()` BEFORE any declaration change, with `--repo` accepted by the parser and absent from `legacy_flags`; `tests/test_command_surface_declarations.py` -> `1 passed in 0.38s` |
| F-8 | LOW | measurement route (review PR-903) | THE `aw` WRAPPER CAN MEASURE A DIFFERENT CHECKOUT. It prints `aw: invoked in checkout <A> but imported agent_workflows from <B>` on stderr and then runs B's code. Review hit this: after applying the probe in-tree, `aw runs --help` still showed bare `--dir`, which reads exactly like "the alias does not render" and cost a cycle to diagnose. Any E-01/E-06 measurement through `aw` must check for that banner or use the in-tree route. | The banner appears on every `AW_NO_REEXEC=1` invocation in this worktree; `python3 -m agent_workflows runs --help` showed `--dir, --repo DIR` at the same moment `aw runs --help` showed `--dir DIR` |

## Proposed changes (ordered, validatable)

1. E-01 re-measures, through the in-tree package.
2. E-02 adds the alias on the shared parent and the ledger-leaf helper.
3. E-03 adds it on the four separately registered leaves.
4. E-04 declares it where `--dir` is declared, with honest evidence about what that proves.
5. E-05 adds parse-level, `run start`, derived-coverage, end-to-end and two-way declaration tests.
6. E-06 verifies the alias is actually visible in `--help`.

## Deferred / out of scope (with reason)

- Adding `--dir` as an alias on `aw oc run` / `aw agy run` (the reverse direction the backlog item suggests).
  - Carrier-Declined: a whole-CLI naming review is under way (research `ffi66q`, the live-parser command inventory prepared as input to it), and which spelling the runner families adopt is a CLI-contract decision for that review, not for this friction fix. This plan only removes the failure an operator actually hits.

## Scope check

- Over-scope: none.
- Under-scope: closed by review with three additions, none of which widens the file set. The plan tested only the `runs` noun although `_register_run_leaf` demonstrably gives `aw run start|record|cancel|finalize` the alias too, so that consequence is now tested rather than merely declared (F-5/PR-902). Help visibility, which is the plan's actual purpose, was never checked and is now E-06 (F-6). And the declaration evidence could not detect its own omission, so V-04 asserts the tuple directly (F-7).
- `agent_workflows/runner_shared.py` (the footer) is deliberately NOT changed: once `--repo` is accepted, its hints compose as written. Review verified both footer lines verbatim (`lines.append(f"  aw runs {run_id}")` on the success path and `lines.append(f"  {cmd} resume --repo {repo} {run_id}")` on the resume path), so the claim holds.
- Scope-Paths justification: `cli.py` holds every parser site; `command_surface.py` holds the declaration; the new test file holds E-05 and E-06.

## Required tests / validation

- `tests/test_runs_repo_alias.py` (new): nine `runs` `--repo` parse cases with `--dir` controls, one `run start` case, one DERIVED coverage walk (every `runs`/`run` parser accepting `--dir` also accepts `--repo`), one end-to-end `cli.main` case, one two-way declaration case, and the E-06 help-rendering assertions.
- `python3 -m pytest -o addopts="" -q tests/test_command_surface_declarations.py` stays green (while proving nothing about the declared flag - F-7).
- Bare `python3 -m pytest` before and after; compare failing node IDs. Review's probe measured `2436 passed, 1 skipped` with the alias applied, so no regression is expected.

## Spec / documentation sync

- N/A for specs: no spec enumerates `aw runs` flags (grep of `.aw/records/specs/` for `aw runs --dir` finds nothing). No `.spec.md` is in `- Scope-Paths:`.
- The help text itself documents the alias; the `_RUNS_EPILOG` examples use no repo flag and need no change.

## Open questions

### OQ-01: Should the alias be added in the other direction (`--dir` on `aw oc run`) in the same plan?

- Blocking: no
- Status: resolved
- Owner: maintainer (via the graduation brief), 2026-09-26
- Resolution or deferral rationale: No. Maintainer ruling 2026-09-26 in the graduation brief: that direction is a CLI-contract choice and is deferred with a Carrier-Declined reason because a whole-CLI naming review is under way (research `ffi66q`). Review confirmed that research document exists and is live (`ffi66q`, status `todo`, "Every aw command, subcommand and sub-subcommand ... as input to the CLI naming review"), so the deferral names a real carrier rather than an intention.

### OQ-02: Is it acceptable that `aw run start|record|cancel|finalize` also gain `--repo`?

- Blocking: no
- Status: resolved
- Owner: review (see review record `8y13kn` D-2)
- Resolution or deferral rationale: Yes, from repository evidence, and the plan was right to declare it rather than hide it. `_register_run_leaf` is ONE helper registering leaves on both `runs_sub` and `run_sub`, so the alias cannot be given to the reading leaves without also giving it to the four writing leaves unless the helper is forked - and forking a helper whose stated purpose is that the two surfaces "cannot drift apart" to withhold a harmless alias would be a worse outcome than the widening. Both nouns name a repository root, the flag lands in the same `args.dir`, and review measured `["run","start","run-x","--repo",R]` parsing to `args.dir == R` with no other behavior change. The only correction review made is that E-05 now TESTS this rather than leaving it as prose: a declared consequence with no test is indistinguishable from an accident, and the next person to touch the helper has nothing to tell them the cross-noun alias was intended.

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
  - Required evidence: paste the `command_surface` diff, `python3 -c "from agent_workflows import command_surface as cs; print(cs.get_declaration('runs list').legacy_flags)"` showing BOTH `--dir` and `--repo`, and `python3 -m pytest -o addopts="" -q tests/test_command_surface_declarations.py` passing. The direct print is the ONLY evidence that counts here: state explicitly that the passing suite does not verify the flag, because `find_undeclared_leaves` checks leaves and the declared-flags case checks only `declared - accepted`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_runs_repo_alias.py` passing with its count; the same run with E-02/E-03 temporarily reverted showing the `--repo` cases, the `run start` case, the coverage walk and the end-to-end case FAILING and the `--dir` controls passing; the declaration case's `--repo` half shown failing with E-04 reverted; then the bare `python3 -m pytest` summary line before and after with the after-minus-before failing node-ID set (must be empty). Review's own probe measured the bare suite at `2436 passed, 1 skipped` WITH the alias applied, so a regression here is not expected; report the numbers rather than the expectation.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the rendered help line for `runs`, for one `_register_run_leaf` leaf, and for one separately-registered leaf, each showing `--dir, --repo`; name the route used (in-process `format_help()` or `python3 -m agent_workflows`) and confirm no `aw`-vs-package mismatch banner was present in the captured output. Confirm no help string was hand-edited to force the rendering.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: six items, one concern (one flag spelling accepted across one command family). E-06 is separate from E-05 because help RENDERING is a different surface from argv PARSING and would otherwise go unchecked, which matters here since discoverability is the whole point of the change.

WHAT A HUMAN IS APPROVING. `aw runs` and all its leaves (plus the `aw run` ledger-writing leaves, which share the same helper) accept `--repo` as an alias of `--dir`, stored in the same `args.dir`, so nothing that reads the flag changes and every existing invocation keeps working. The reverse alias on `aw oc run` is deliberately left to the CLI naming review.

REVIEW APPLIED THIS CHANGE AND MEASURED IT BEFORE APPROVING THE PLAN, so the human is approving something demonstrated rather than argued. All six parser sites were edited, the parser re-walked (every `runs`/`run` parser accepting `--dir` then accepted `--repo`, empty violation set), ten argv shapes parsed to the same `args.dir`, `runs --repo <tmp>` exited 0 with output byte-identical to the `--dir` spelling, the help line rendered as `--dir, --repo DIR` with no help-string edit, the bare suite stayed at `2436 passed, 1 skipped`, and the probe was then reverted (`agent_workflows/cli.py` byte-unchanged). The one consequence worth a human's eye is the widening beyond the stated noun: `aw run start|record|cancel|finalize` gain `--repo` too, because one helper registers both nouns. That is consistent (both name a repository root) and is now tested rather than only declared.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/cli.py` (the `--dir` arguments of the `runs` family and `_register_run_leaf`), `agent_workflows/command_surface.py` (the `legacy_flags` of declarations already listing `--dir` for those leaves), and the new `tests/test_runs_repo_alias.py`. Any edit outside the declared paths is justified at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-05 must show the new `--repo` cases FAILING before the change. TWO SPECIFIC CLAIMS ARE NOT ACCEPTED AS EVIDENCE. A green `tests/test_command_surface_declarations.py` does NOT verify E-04: that test checks undeclared LEAVES, and E-05's declared-flags case checks only `declared - accepted`, so both pass with `--repo` undeclared (F-7). And any `aw ...` output carrying the banner `aw: invoked in checkout ... but imported agent_workflows from ...` is measuring a DIFFERENT checkout and must be re-taken through `python3 -m agent_workflows` or in-process (F-8).

GENUINE STOP CONDITIONS:
- The E-06 help render does NOT show both spellings: stop and report rather than hand-editing help strings to fake it. Argparse should do this automatically (the sibling `--last, --latest, -l` line proves the pattern), so a failure means something non-obvious is rewriting help and is worth a human's attention.
- The derived coverage walk in E-05 finds a `runs`/`run` parser accepting `--dir` but not `--repo` after E-02/E-03: stop. It means a parser site exists that the plan's six did not cover.
- Any existing invocation changes behavior: the alias is strictly additive, so a `--dir` control failing is a real regression, not a test to adjust.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `tqaxjw` `done` with `--evidence` citing the executed plan.

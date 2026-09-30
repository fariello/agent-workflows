# IPD: Lift the two remaining liftable host integrate shells into runner shared so the exit contract and the operator stream routing exist once

- Date: 2026-09-29
- Kind: child
- Concern: `oc_runipd._integrate_stranded_lanes` and `agy_runipd._integrate_stranded_lanes` are BYTE-IDENTICAL after AST normalization with docstrings stripped, and so are `oc_runipd.handle_integrate_command` and `agy_runipd.handle_integrate_command`. Re-measured in this lane at HEAD `8fdc89f0` with the repository's own committed scanner (`python3 tools/runner_fork_scan.py`), which reports `REAL FORKS 10, byte-identical 4` and names all four (`StallWatchdog`, `_integrate_stranded_lanes`, `disable_lane_prompt`, `handle_integrate_command`) at similarity `1.000`. Two of those four are ALREADY DECIDED AGAINST LIFTING for recorded reasons and are not this plan's business (see Deferred), so the live residue is exactly the two the backlog item names. Each carries a small but real contract that a one-sided edit silently breaks: `handle_integrate_command` owns the verb's EXIT CONTRACT (0 integrated / 1 refused / 2 driver error) and its STREAM ROUTING (success to stdout, refusal to stderr, measured on both hosts), and `_integrate_stranded_lanes` owns the resume pass's operator narration sink (`Palette(should_color(sys.stdout))` colorized to stderr). A fix to either lands on one driver only, which is the class of defect `cjefq5` already shipped from this exact file pair.
- Scope: Give each of the two symbols ONE definition in `runner_shared.py`, reached from both hosts by the sanctioned thin-wrapper form this repository already uses for `integrate_lane_branch`, `save_state`, `write_report` and 40-odd others. The host-varying inputs (`integrate_lane_branch`, `run_suite_check`, `save_state`, `append_jsonl`, `process_backlog_close`) are INJECTED exactly as `runner_shared.integrate_stranded_lanes` and `runner_shared.reintegrate_lane` already inject them one layer down, so this adds no new mechanism. Also re-derive and record whether the backlog item's note about `handle_integrate_command` being classified `still-defined-twice` still describes anything that exists. EXCLUDES the other two byte-identical symbols (both already decided; see Deferred), EXCLUDES all six divergent forks, and changes NO behavior: not the exit codes, not the stream routing, not the narration text, not the refusal wording.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_runner_shared.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: baskrx
- Set: baskrx
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 9oj6t2
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (aw set): status set to reviewed

- 2026-09-30 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-B01 (HIGH, fixed), PR-B02 (MEDIUM, fixed), PR-B03 (MEDIUM, fixed), PR-B04 (LOW, fixed), PR-B05 (LOW, fixed), PR-B06 (LOW, fixed). Findings recorded in `.aw/records/reviews/20260930-baskrx-01-9oj6t2-lift-the-two-remaining-liftable-host-integrate-shells-into-r.review.md`. I re-ran the scanner and reproduced the census byte-for-byte on a later HEAD (`46` wrappers, `REAL FORKS 10`, `byte-identical 4`, both targets `1.000`), confirmed both bodies are byte-identical between hosts, confirmed the closure, confirmed `tests/test_rununify_main.py` is gone and `run_suite_check` is one shared object while `integrate_lane_branch` is not, measured the unasserted exit contract on both hosts (`rc=1`, empty stdout, identical stderr refusal), and measured the `attention` probe degrading when the attribute is deleted. The plan's direction, its thin-wrapper form, and OQ-01's parameters-not-descriptor resolution are all correct. THE ONE SERIOUS GAP: the plan asserts its own success in prose ("leaving 8 real forks by the scanner's count") while no `E-*` or `V-*` required it, and both target bodies are MULTI-STATEMENT today (3 and 6 non-docstring statements), which is precisely why `is_pure_delegation` returns False and the scanner counts them as forks. A wrapper retaining one setup line would have satisfied every original V-item while the census stayed at 10 and the symbols stayed forked, i.e. the plan's whole purpose unmet with full green evidence. Verified the reduction IS reachable for both (every pre-delegation statement is host-neutral; `Palette`/`should_color`/`append_jsonl` are `is`-identical across all three modules), so this is now a requirement in E-01/E-02/E-03/E-06 rather than an aspiration. Three further corrections: the twice-cited `tests/test_runner_shared.py::NoRunnerImportTests` DOES NOT EXIST (deleted in `19313eed`, only prose comments survive), so E-03 must not propagate that citation into a new docstring; the tree ALREADY SHIPS a per-symbol AST re-fork guard (`test_add_output_mode_flags_not_reforked_in_hosts`, passing) that OQ-02's P16 argument did not acknowledge, so the answer stays NO on a narrower basis with the counterexample now visible; and the suite baselines drift (bare `3312 passed` at review; the narrow gate's `357 passed` held but its timing did not), so comparisons must use freshly captured node-id sets. Also corrected F-5's "all four `test_rununify_*` files" to the eleven actually deleted.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `baskrx`, graduating it. The item's own closing instruction ("Re-measure with `python3 tools/runner_fork_scan.py` before acting; do not trust these counts") was followed, and re-measurement changes the plan's shape in FOUR ways the item could not know. FIRST, the census is no longer NINETEEN byte-identical forks: it is FOUR, because `li44r9`'s lift plus the `rununify` and `runnerlayer` work since then landed, so this is a two-symbol plan and not a nineteen-symbol one. SECOND, the item names hostdedup Order 02 (`nmlx47`) as "the natural place to absorb these two"; that plan is now in `superseded/` (retired 2026-09-23, its lane deleted), so it cannot be the home and this plan must be. THIRD, the item's hand-off note says `nmlx47` "already declares all four `test_rununify_*` pin files"; all four were DELETED in `19313eed`, along with `test_hostdedup_identical_lift.py` and `test_runner_refork_guard.py`, so there is no pin table to re-base and the declared fence is the two host suites plus the shared one instead. FOURTH, the item asks whoever lifts `handle_integrate_command` to "re-derive whether that reason still holds" for its `still-defined-twice` classification; the classification's HOME no longer exists, and the reason it recorded (each host binds its own `integrate_lane_branch` wrapper and its own `run_suite_check`) is now measurably HALF FALSE, because `run_suite_check` is the SAME OBJECT on both hosts and in `runner_shared` (`oc.run_suite_check is agy.run_suite_check` is True) since it was re-homed. That re-derivation is E-01 and F-6 rather than an executor's judgement call.

## Goal

Delete the last two liftable copies in the host-runner pair, so the `integrate` verb's exit contract and
the resume pass's narration have ONE definition each rather than two that must be remembered together.

WHY THIS IS SMALL AND STILL WORTH DOING. The measured residue is 11 `ast.unparse` lines across the two
symbols (4 for `_integrate_stranded_lanes`, 7 for `handle_integrate_command`), which is not a line-count
argument and this plan does not make one. The argument is that both bodies are BINDING SITES for contracts
that live one layer down, and a binding site is exactly where a one-sided edit hides: the shared
`reintegrate_lane` returns an outcome object and the HOST body decides that `integrated` means exit 0 to
stdout and anything else means exit 1 to stderr. Nothing in the tree asserts those two hosts agree on that
mapping today. Measured in this lane, they do agree, byte for byte; the point of the lift is that after it
they agree BY CONSTRUCTION, and a third host inherits the mapping instead of re-deriving it.

WHAT THE BACKLOG ITEM GOT RIGHT AND WHAT MEASUREMENT CHANGED. The item is right that these two symbols are
byte-identical, right that `li44r9` never reviewed them, and right that lifting them is a DIFFERENT act
from measuring them. Every structural claim about where the work should go is now stale, because the
intended home was retired and the pin tables it named were deleted. So this plan takes the work itself,
declares the fence that actually exists, and re-derives the one classification the item flagged.

THE FOUR-SYMBOL CENSUS, and why only two of them are here. Measured at HEAD `8fdc89f0`:

| byte-identical symbol | disposition here | reason |
|---|---|---|
| `_integrate_stranded_lanes` | LIFT (E-02) | closure is fully injectable; no host-varying value survives |
| `handle_integrate_command` | LIFT (E-03) | same, plus it owns the exit contract worth pinning once |
| `disable_lane_prompt` | DEFERRED, already decided | it mutates a module-level `_LANE_PROMPT_DISABLED` through `global`; `runner_shared` carries a standing in-code refusal and `tests/test_forkresid_shared_shells.py::LanePromptSuppressionTests` pins the per-host behavior |
| `StallWatchdog` | DEFERRED, already lifted | the LOGIC is already ONE definition (`runner_shared.StallWatchdog`); both hosts subclass it to bind their own tunable grace constants, verified by `issubclass` on both |

Both deferrals are recorded decisions, not omissions, and re-opening either is out of scope. Note the
scanner counts both as REAL FORKS by its own admission: `StallWatchdog` is a SUBCLASS rather than a
single-statement delegation, so `is_pure_delegation` returns False for it, which is a limitation of the
predicate and not evidence of duplication. Do not "fix" that by flattening the subclass.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Re-measure, then re-derive the one stale classification

- [ ] E-01 RE-MEASURE THE CENSUS AND THE CLOSURE AT EXECUTION HEAD, AND REFUSE TO PROCEED ON THIS PLAN'S NUMBERS. Run `python3 tools/runner_fork_scan.py` and `python3 tools/runner_fork_scan.py --closure --symbols _integrate_stranded_lanes handle_integrate_command`, and compare the identical set against the four this plan names. The scanner is the repository's own instrument and prints its metric with its output, so quote both. THEN RE-DERIVE THE ITEM'S FLAGGED CLASSIFICATION, which is a separate question its own sentence asks: the item says `handle_integrate_command` is classified `still-defined-twice` in `tests/test_rununify_main.py` "with a recorded reason (each host binds its own `integrate_lane_branch` wrapper and its own `run_suite_check`)". Establish BOTH halves at execution HEAD: whether that file still exists, and whether each named binding is still host-specific. Authoring measurement, to be confirmed or refuted rather than inherited: the file is GONE (deleted in `19313eed` with the other three `test_rununify_*` pin files), and the reason is HALF FALSE because `run_suite_check` is now a single shared object on both hosts while `integrate_lane_branch` genuinely is still a per-host wrapper binding a different `host_label`. If the re-derivation disagrees with that, STOP and record the disagreement instead of lifting.
  - Depends on: none
  ALSO CAPTURE THE PRE-LIFT `is_pure_delegation` BASELINE for both target symbols, because that predicate is this plan's success criterion (F-12) and a criterion with no before-value cannot be shown to have moved. Drive `tools.runner_fork_scan.is_pure_delegation` over each host's `FunctionDef` for both symbols and record the statement count beside the verdict. Authoring-and-review measurement to confirm: `_integrate_stranded_lanes stmts=3 False` and `handle_integrate_command stmts=6 False` on both hosts, against `save_state stmts=1 True` in the same file as the sanctioned shape.
  - Expected outcome: the scanner's output pasted with its metric, the four-symbol identical set confirmed or the difference named, a two-line verdict on the item's classification note (file present or absent; each binding host-specific or shared) supported by what was run, and the pre-lift `is_pure_delegation` verdict plus statement count for both symbols on both hosts.
  - Execution state: pending

### Task group 2: Lift the two symbols

- [ ] E-02 LIFT `_integrate_stranded_lanes` INTO `runner_shared` AS ONE DEFINITION, leaving each host a thin delegating wrapper. The shared function it wraps (`runner_shared.integrate_stranded_lanes`) already takes every host binding as a keyword parameter, so the lifted shell threads them through rather than inventing a seam: `integrate`, `suite_check`, `save_state`, `append_jsonl`, `process_backlog_close`, `report`. THE ONE THING THAT MUST NOT CHANGE IS THE NARRATION SINK. Both current bodies build `Palette(should_color(sys.stdout))` and then print to `sys.stderr`, which looks like a typo and is not: `should_color` is asked about the stream a human is reading while the text goes to the operational stream, and the shared `integrate_stranded_lanes` docstring's own reasoning for stderr narration applies. Preserve that pairing EXACTLY; a "tidy-up" to `should_color(sys.stderr)` is a behavior change to colorization under redirection and is out of scope. `Palette`, `should_color` and `append_jsonl` are already the SAME objects in all three modules (verified by `is` at authoring), so no import moves.
  - Depends on: E-01
  THE WRAPPER MUST REDUCE TO EXACTLY ONE NON-DOCSTRING STATEMENT, and this is the plan's measurable success criterion rather than a style preference (F-12). The body is 3 statements today, which is precisely why `tools/runner_fork_scan.py::is_pure_delegation` returns False for it and why the scanner counts it a REAL FORK despite classing it `BOTH-DELEGATE`. A wrapper that still opens with `repo = Path(state["repo"])` or `pal = Palette(...)` would satisfy every other requirement here while leaving the census at `REAL FORKS 10` and the symbol still a fork, i.e. the work would not have been done. Both of those statements are host-NEUTRAL and must move INTO the shared body: `repo` reads only `state`, and `Palette`/`should_color` are `is`-identical in all three modules (F-13). Pass only what genuinely varies. Per F-16, `suite_check` and `append_jsonl` need not be threaded at all (`run_suite_check` and `append_jsonl` are the SAME OBJECT in all three modules), while `integrate`, `save_state` and `process_backlog_close` must be, because each is a per-host wrapper binding its own host callables even where its source text matches.
  - Expected outcome: one definition in `runner_shared`, a thin wrapper in each host at the unchanged name `_integrate_stranded_lanes` with the unchanged `(run_dir, state)` signature, so the single call site in each host's `run_queue` is untouched. State whether the shared shell takes the two bindings that vary (`integrate`, `save_state`) as parameters or reads them some other way, and paste the diff of the two call sites showing they did not change. AND paste `tools.runner_fork_scan.is_pure_delegation` returning True for both host wrappers, with the statement count shown as 1.
  - Execution state: pending

- [ ] E-03 LIFT `handle_integrate_command` INTO `runner_shared` AS ONE DEFINITION, with the same wrapper treatment, and CARRY THE EXIT CONTRACT AND THE STREAM ROUTING INTO THE SHARED BODY RATHER THAN LEAVING EITHER IN A HOST. The mapping to preserve, measured on both hosts at authoring by calling each host's function directly against a git repo with no run record: `rc=1`, stdout EMPTY, and the refusal sentence on stderr beginning `integrate zzzzzz REFUSED (no-lane-record): ...`. The success half routes to stdout instead (`sys.stdout if outcome.integrated else sys.stderr`). Preserve the `getattr(args, ...)` tolerance verbatim: it is what lets the verb be reached through two different argv routes (the driver subcommand and the `cli.py` host-noun alias) without each one having to populate identical attributes. Note the third exit code in the docstring's contract (2 for a usage/driver error) is produced by each host's `main` error handling, NOT by this body, so lifting this body does not move it and the shared docstring must not claim it does.
  - Depends on: E-01
  THE SAME SINGLE-STATEMENT CRITERION APPLIES (F-12): this body is 6 non-docstring statements today and `is_pure_delegation` is False for it. All six are host-neutral except the injected `integrate_lane_branch` (`repo`/`id6` are `getattr` reads of `args`; `outcome`/`message`/`print`/`return` reach only shared symbols), so the reduction is available (F-13) and the wrapper must take it. ALSO: do NOT repeat the two production docstrings' claim that `tests/test_runner_shared.py::NoRunnerImportTests` forbids `runner_shared` importing a driver. That test DOES NOT EXIST; it was deleted in `19313eed` and only prose comments survive (F-14). The INVARIANT is real and the shared docstring should state it as a rule, but it must not cite a test an executor cannot run.
  - Expected outcome: one definition in `runner_shared`, a thin wrapper in each host at the unchanged name so `main`'s `if args.command == "integrate": return handle_integrate_command(args)` dispatch is untouched, and the attribute `handle_integrate_command` still present on BOTH host modules (see E-05 for why that is load-bearing). AND `is_pure_delegation` True for both host wrappers with the statement count shown as 1, plus confirmation that no new docstring cites `NoRunnerImportTests`.
  - Execution state: pending

### Task group 3: Pin what the lift could silently break

- [ ] E-04 PIN THE EXIT CONTRACT AND THE STREAM ROUTING ON BOTH HOSTS, BEHAVIORALLY, IN BOTH DIRECTIONS. This is the assertion that makes the lift safe rather than merely smaller, and it does not exist today: no test in the tree checks that the two hosts agree on which stream a refusal goes to or that a refusal exits nonzero with an empty stdout. Drive each host's real `main(["integrate", ...])` (not the lifted function in isolation) and assert, per host: a refusal gives a nonzero exit with the refusal text on stderr and NOTHING on stdout, and a success gives exit 0 with the confirmation on stdout. The success half has an existing fixture family to reuse rather than reinvent: `tests/test_runner_shared.py` exports `_repo_with_pending_plan`, `_verified_lane`, `_write_run_state`, `_stranded_item` and `_passing_suite`, and both host suites already import them for their merge-subject tests. NO SOURCE INSPECTION, NO SYMBOL CENSUS, NO DOCSTRING PIN (GUIDING_PRINCIPLES P16): this asserts exit codes and stream contents, which is what a one-sided edit would actually change.
  - Depends on: E-02, E-03
  - Expected outcome: the new assertions added to `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` beside each host's existing integrate-verb class, green, with the run pasted. State explicitly that each host's merge subject test (`integrate(aw oc run): ...` / `integrate(aw agy run): ...`) still passes, since that is the one thing the shared body may NOT bind and the lift's most plausible way to go wrong.
  - Execution state: pending

- [ ] E-05 CONFIRM THE `attention` PROBE STILL RESOLVES, because it reads one of the lifted names BY ATTRIBUTE and a lift is exactly what could break it. `attention.LANE_INTEGRATE_PROBE_SYMBOL` is the literal string `"handle_integrate_command"`, and `attention.lane_remedy_hint` does `hasattr(oc_runipd, LANE_INTEGRATE_PROBE_SYMBOL)` to decide whether to print `Recover it with \`aw oc integrate <id6>\`` or to fall back to "no `aw integrate` verb exists yet". THE WRAPPER FORM THIS PLAN CHOOSES KEEPS THAT TRUE, and the failure mode is measured rather than hypothetical: with the attribute deleted the hint degrades to the by-hand sentence (verified at authoring), and `tests/test_attention.py::LaneRemedyHintTests` already asserts both the present and absent branches on BOTH hosts. So this item is a CHECK, not a change: run that test and confirm it passes unchanged. If a chosen implementation would remove the attribute from either host module, that implementation is wrong and the wrapper must stay.
  - Depends on: E-03
  - Expected outcome: `tests/test_attention.py::LaneRemedyHintTests` green after the lift with no edit to it, pasted, plus the hint string itself shown unchanged for one id6.
  - Execution state: pending

- [ ] E-06 RUN THE FULL SUITE AND COMPARE AGAINST A BASELINE TAKEN THE SAME WAY. Bare `python3 -m pytest`, per the repository's execution contract; do not add flags. TAKE THE BASELINE FRESH, IN THE SAME CHECKOUT, BEFORE ANY EDIT, AND DO NOT COMPARE AGAINST ANY COUNT WRITTEN IN THIS PLAN: the bare total is a live population that every merged lane moves, and it stood at `3312 passed, 2 skipped` at review against no authoring figure at all, while the narrow three-file gate's `357 passed` held but its `24.05s` timing did not. Compare FAILING NODE IDS, not totals. A test that fails only after the lift is a real regression in this plan's scope and must be fixed rather than re-based, because this plan changes no behavior and therefore has no license to move an assertion. THEN RE-RUN THE SCANNER and show the census MOVED: `REAL FORKS` must drop from 10 to 8 and `byte-identical` from 4 to 2, with the two lifted symbols absent from the IDENTICAL FORKS section. That is the plan's own asserted outcome (its Scope check says "leaving 8 real forks by the scanner's count") and until this item measures it, nothing does (F-12).
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: two pasted summary lines, before and after, from a freshly captured baseline, with any difference named and explained rather than absorbed; plus the post-lift scanner output showing `REAL FORKS 8` and `byte-identical 2` with neither lifted symbol listed as a fork.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `runner_shared.py` is the established home for host-neutral runner logic, and it may import NEITHER
  runner, so it cannot ask which host it serves: the caller supplies host-varying values. The two
  functions one layer below these shells (`runner_shared.integrate_stranded_lanes` and
  `runner_shared.reintegrate_lane`) already do exactly that, taking `integrate`, `suite_check`,
  `save_state`, `append_jsonl` and `process_backlog_close` as keyword parameters, so this plan reuses a
  seam rather than designing one.
- THE THIN WRAPPER IS THE TARGET FORM, not a compromise, ruled by the maintainer in `818uru` OQ-02 and
  visible at scale: `tools/runner_fork_scan.py` reports 46 sanctioned thin wrappers at HEAD and its
  `is_pure_delegation` predicate excludes them from the fork count by design.
- A WRAPPER IS NOT THE SAME OBJECT, and any evidence phrased as object identity is unsatisfiable under
  this design. Verified at authoring: `oc_runipd.integrate_lane_branch is agy_runipd.integrate_lane_branch`
  is False, and so is each against `runner_shared`. What IS identical, because it was re-homed rather than
  wrapped, is `run_suite_check`, `append_jsonl`, `should_color`, `Palette` and `pinned_child_env` (all
  `is`-equal across all three modules).
- `runner_shared.HostLabels` carries every host-varying STRING, bound per host as `OC_HOST_LABELS` /
  `AGY_HOST_LABELS`. NEITHER symbol in this plan needs it, and that absence is the evidence the lift is
  decision-free: the only host-varying thing either body reaches is `integrate_lane_branch`, which is a
  CALLABLE that already carries its own `host_label` internally (`"aw oc run"` / `"aw agy run"`), so the
  label travels with the injected function and never needs to be named here. Needing `HostLabels` for a
  supposedly identical symbol would be the signal that it is not identical after all.
- TESTS ARE NOT IMMOVABLE, but they are re-based DELIBERATELY as part of the work and never weakened
  silently (maintainer ruling recorded in `orziju`'s history). This plan expects to re-base NOTHING, and
  that expectation is itself evidence: the pin tables that `li44r9` had to re-base for the same class of
  lift were deleted in `19313eed`, so the only guards left over these symbols are behavioral.
- GUIDING_PRINCIPLES P16 forbids source inspection, census pins, docstring pins and architectural
  placement pins. That directly shapes E-04: the invariant this plan establishes may NOT be asserted as
  "both hosts delegate to `runner_shared`" (a placement pin), and must instead be asserted as "both hosts
  produce the same exit code and the same stream routing", which is the observable consequence.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | The census is FOUR byte-identical real forks, not the NINETEEN the item recorded. The item's own instruction is to re-measure and not trust its counts, so this is the instruction working, not a contradiction. | `python3 tools/runner_fork_scan.py` at HEAD `8fdc89f0`: `co-defined in both runners : 56`, `sanctioned thin wrappers : 46 (NOT forks)`, `REAL FORKS 10`, of which `byte-identical 4` and `divergent 6`. The four are named in the IDENTICAL FORKS section. RE-MEASURED AT REVIEW on a later HEAD: byte-for-byte the same figures (`46` wrappers, `REAL FORKS 10`, `byte-identical 4`, `divergent 6`, the same four names at `1.000`), so this census is stable rather than merely recent |
| F-2 | Both target symbols measure similarity `1.000` and are classified `BOTH-DELEGATE`, i.e. each is already a shell over a shared implementation one layer down. That is what makes this a low-risk move: the DECISIONS were lifted long ago and only the binding shells remain. | scanner PER-SYMBOL table: `_integrate_stranded_lanes BOTH-DELEGATE . 4 4 1.000`, `handle_integrate_command BOTH-DELEGATE . 7 7 1.000` |
| F-3 | The closure of both symbols is fully injectable, with no host-varying VALUE left behind. `--closure` reports every module-level dependency `ok` except `runner_shared` itself (which is `ABSENT-FROM-SHARED` only because the shared module does not import itself), and the two genuinely host-specific deps are CALLABLES already injected one layer down. | `python3 tools/runner_fork_scan.py --closure --symbols ...`: for `handle_integrate_command`, `Path/argparse/sys` import-ok, `integrate_lane_branch` def, `run_suite_check` import-ok; for `_integrate_stranded_lanes`, additionally `Palette`, `should_color`, `append_jsonl`, `save_state`, `process_backlog_close` |
| F-4 | THE ITEM'S NAMED HOME NO LONGER EXISTS. It says hostdedup Order 02 (`nmlx47`) "is the natural place to absorb these two". `nmlx47` is RETIRED to `superseded/`, its central move was one `main` deliberately reverted, and its lane is deleted. | `.aw/records/plans/superseded/20260917-hostdedup-02-nmlx47-...ipd.md`, whose own RETIRED header (dated 2026-09-23) records the revert and states "The lane `aw/lane/nmlx47` is DELETED" |
| F-5 | THE ITEM'S DECLARED FENCE NO LONGER EXISTS EITHER. It relies on `nmlx47` already declaring the `test_rununify_*` pin files; they were deleted, as were `test_hostdedup_identical_lift.py` and `test_runner_refork_guard.py`. So there is NO `STILL_DOUBLE_DEFINED` / `THIN_WRAPPERS_OVER_RUNNER_SHARED` table left to re-base, which removes the largest single piece of work `li44r9` did for the same class of lift. | `git show --name-status --diff-filter=D 19313eed -- tests/` (subject: "test: trim test suite from 9,136 to under 2,000 tests") lists ELEVEN deleted `test_rununify_*` files, not four, plus the two named above; corrected at review, where the authoring figure of "four" undercounted. `grep -rn "STILL_DOUBLE_DEFINED\|THIN_WRAPPERS_OVER_RUNNER_SHARED" tests/` returns nothing |
| F-6 | THE ITEM'S FLAGGED CLASSIFICATION IS HALF FALSE AT HEAD, and its home is gone. It asks whoever lifts `handle_integrate_command` to re-derive whether the `still-defined-twice` reason ("each host binds its own `integrate_lane_branch` wrapper and its own `run_suite_check`") still holds. `integrate_lane_branch` IS still per host; `run_suite_check` is NOT, it is one shared object all three modules bind. | `oc_runipd.run_suite_check is agy_runipd.run_suite_check is runner_shared.run_suite_check` -> True (both hosts import it from `runner_shared`, with an in-code note that re-homing it "removes the reason for the injection"); `oc_runipd.integrate_lane_branch is agy_runipd.integrate_lane_branch` -> False |
| F-7 | THE EXIT CONTRACT AND STREAM ROUTING THIS PLAN LIFTS IS UNASSERTED TODAY, which is the substantive risk the lift removes. Measured identical on both hosts, and nothing in the suite would notice if one drifted. | calling each host's `handle_integrate_command` against a fresh git repo with no run record: both give `rc=1`, `stdout=''`, and the same `integrate zzzzzz REFUSED (no-lane-record): ...` on stderr. The existing host tests assert the help text, the argv routing, the shared-call spy and the merge subject, but never the exit code paired with the stream |
| F-8 | ONE PRODUCTION CONSUMER READS A LIFTED NAME BY ATTRIBUTE, so the wrapper form is load-bearing rather than stylistic. `attention.lane_remedy_hint` probes `hasattr(oc_runipd, "handle_integrate_command")` to decide which remedy sentence to print. | `attention.LANE_INTEGRATE_PROBE_SYMBOL = "handle_integrate_command"`; with the attribute present the hint is `Recover it with \`aw oc integrate abc123\`.` and with it deleted the hint degrades to the by-hand sentence naming "no `aw integrate` verb exists yet" (both measured at authoring). `tests/test_attention.py::LaneRemedyHintTests` asserts both branches on both hosts |
| F-9 | The `Palette(should_color(sys.stdout))`-then-print-to-`sys.stderr` pairing in `_integrate_stranded_lanes` is DELIBERATE and must survive verbatim. It is not unique to these bodies: `runner_shared` itself does the same in several places, and the shared narration contract puts operational lines on stderr. | both host bodies construct the palette from `sys.stdout` and pass `report=lambda message: print(pal(message, "cyan"), file=sys.stderr)`; `runner_shared.integration_lock_progress_reporter` records the same stderr rationale ("operational narration beside a run's output") |
| F-10 | The other two byte-identical symbols are ALREADY DECIDED and must not be swept in. `disable_lane_prompt` carries a standing in-code refusal with its reason; `StallWatchdog`'s logic is already shared and each host SUBCLASSES it to keep its own grace constants live. | `runner_shared` comment: "`disable_lane_prompt` is deliberately ABSENT and stays in both runners: it mutates a module-level `_LANE_PROMPT_DISABLED` via `global`", pinned by `tests/test_forkresid_shared_shells.py::LanePromptSuppressionTests`; `issubclass(oc_runipd.StallWatchdog, runner_shared.StallWatchdog)` and the agy twin both True |
| F-12 | **THE LIFT HAS A MEASURABLE SUCCESS CRITERION AND NO `E-*` OR `V-*` REQUIRED IT.** Both target bodies are MULTI-STATEMENT today (`_integrate_stranded_lanes` 3 non-docstring statements, `handle_integrate_command` 6), which is exactly why `is_pure_delegation` returns False for both and why the scanner counts them as real forks despite classing them `BOTH-DELEGATE`. So a wrapper that still opens with `repo = Path(state["repo"])` or `pal = Palette(...)` would satisfy every V-item as originally written while the census stayed at `REAL FORKS 10` and the two symbols remained forks. The plan even asserts the intended outcome ("leaving 8 real forks by the scanner's count") in its Scope check, but nothing obliged the executor to produce it. | Drove `tools.runner_fork_scan.is_pure_delegation` over both host `FunctionDef` nodes: `_integrate_stranded_lanes stmts=3 is_pure_delegation=False`, `handle_integrate_command stmts=6 is_pure_delegation=False`, against `save_state stmts=1 True` and `process_backlog_close stmts=1 True` as the sanctioned shape in the same file |
| F-13 | **THE SINGLE-STATEMENT WRAPPER IS REACHABLE FOR BOTH SYMBOLS, so F-12's criterion is a requirement rather than an aspiration.** Every statement the host bodies execute before delegating is host-NEUTRAL and can move into the shared body: `repo = Path(state["repo"])` reads only `state`; `pal = Palette(should_color(sys.stdout))` uses two objects that are `is`-identical in all three modules; `repo`/`id6` in `handle_integrate_command` are `getattr` reads of `args`. The only genuinely host-varying input is the CALLABLE `integrate_lane_branch`. So each wrapper can reduce to one `return runner_shared.<shell>(...)` call passing the per-host callables, which `is_pure_delegation` accepts (it permits any number of keyword arguments; it requires one STATEMENT). | `oc.Palette is agy.Palette is rs.Palette` True; `oc.should_color is agy.should_color is rs.should_color` True; `oc.append_jsonl is agy.append_jsonl is rs.append_jsonl` True; `is_pure_delegation`'s body requires `len(body) == 1` and a `runner_shared.X(...)` call, with no constraint on arity |
| F-14 | **THE CITED `NoRunnerImportTests` DOES NOT EXIST**, so the plan (and both production docstrings it quotes) name a guard that was deleted. The INVARIANT is still real and still worth stating, but there is no shipped test asserting it, and an executor told "a shipped AST test forbids `runner_shared` importing either driver" would be unable to run it and might conclude the lift had broken something. | `grep -rn "NoRunnerImportTests" tests/` returns nothing; the name appears only inside `oc_runipd.handle_integrate_command`'s own docstring as `tests/test_runner_shared.py::NoRunnerImportTests`. The two surviving references to the rule in `tests/test_runner_shared.py` are prose comments ("this module may not import a runner", "`runner_shared` may not import either driver"), not assertions |
| F-15 | **THE REPOSITORY ALREADY SHIPS A PER-SYMBOL AST RE-FORK GUARD, which OQ-02 does not consider.** `tests/test_runner_shared.py::test_add_output_mode_flags_not_reforked_in_hosts` parses BOTH host modules and asserts each host's `_add_output_mode_flags` is exactly one non-docstring statement calling `runner_shared.add_output_mode_flags`, plus that neither body calls `add_argument` directly. It passes today. This is not a census TABLE (which P16 plainly forbids and OQ-02 correctly rejects) but a single-symbol shape assertion, and its own docstring already records its coverage bound. OQ-02's answer may well stay NO, but it currently rejects a form the tree accepts without acknowledging the counterexample. | `python3 -m pytest tests/test_runner_shared.py -k add_output_mode_flags_not_reforked` -> `1 passed`. GUIDING_PRINCIPLES P16: "No architectural placement pins: Do not assert which module holds a `def` by inspecting ASTs or module dictionaries", so the shipped test and the principle are in genuine tension and a reviewer should see that rather than a one-sided citation |
| F-16 | **ONLY ONE OF THE FIVE INJECTED BINDINGS IS A REAL HOST DIFFERENCE, which sharpens what the lift must thread and what it may simply use.** `run_suite_check` and `append_jsonl` are the SAME OBJECT in all three modules, so the shared body can call them directly. `save_state` and `process_backlog_close` are per-host wrappers whose SOURCE is byte-identical between hosts but which bind different host callables internally (`write_report`, `run_checked`, `close_backlog_item`, `commit_backlog_close`), so they must still be injected. `integrate_lane_branch` is the only one whose own source differs. | `oc.run_suite_check is agy.run_suite_check is rs.run_suite_check` True; `oc.append_jsonl is agy.append_jsonl is rs.append_jsonl` True; `inspect.getsource` equal for `save_state` and `process_backlog_close` across hosts but each delegates with its own host bindings; `inspect.getsource` DIFFERS for `integrate_lane_branch` |
| F-11 | The scanner counts `StallWatchdog` as a REAL FORK only because `is_pure_delegation` requires a single-statement delegation and a subclass is not one. This is a known predicate limitation, stated so an executor does not "fix" the census by flattening the subclass and silently making each host's grace tuning inert. | `tools/runner_fork_scan.py::is_pure_delegation` requires exactly one non-docstring statement calling `runner_shared.X(...)`; `runner_shared.StallWatchdog`'s own docstring records that the reaper is injected precisely so a host's tunable grace constants still apply |

## Proposed changes (ordered, validatable)

1. Re-measure the census and the closure with the committed scanner at execution HEAD, and re-derive the
   item's `still-defined-twice` note in both its halves (E-01). Refuse on a stale list.
2. Lift `_integrate_stranded_lanes` to `runner_shared` with the narration sink preserved verbatim,
   leaving a thin wrapper per host at the unchanged name and signature (E-02).
3. Lift `handle_integrate_command` the same way, carrying the exit contract and the stream routing into
   the shared body, and keeping the host attribute present for the `attention` probe (E-03).
4. Add the behavioral pin that does not exist today: exit code paired with stream routing, in both
   directions, on both hosts, through each host's real `main` (E-04).
5. Confirm the `attention` remedy hint still resolves unchanged (E-05).
6. Full suite, before and after, bare invocation, with both summary lines pasted (E-06).

## Deferred / out of scope (with reason)

- `disable_lane_prompt` IS NOT LIFTED, and this is a decision already recorded in the code rather than a
  gap this plan leaves. It mutates a module-level `_LANE_PROMPT_DISABLED` through `global`, and each
  host's `_lane_reclaim_prompt` reads ITS OWN copy of that flag at call time, so a shared body would write
  `runner_shared`'s flag while both hosts kept reading theirs: prompt suppression on a repeated interrupt
  would silently stop working, and the only symptom would be an unattended run pausing for a question
  nobody is there to answer. `tests/test_forkresid_shared_shells.py::LanePromptSuppressionTests` pins the
  current behavior. Re-opening this needs its own plan and its own review, not a line in this one.
  - Carrier-Declined: Nothing is owed, because this is a SETTLED DESIGN DECISION rather than deferred
    work. The refusal is recorded IN THE SHARED MODULE ITSELF with its reason, and the per-host behavior
    it protects is pinned by a shipped behavioral test, so there is no defect and no gap for a carrier to
    own. Filing an item would misrepresent a deliberate exclusion as outstanding debt and would invite a
    future agent to "close" it by making each host's prompt suppression inert. A maintainer who ever wants
    the flag shared would be choosing a different mechanism (a mutable shared cell, or threading the state
    through both `_lane_reclaim_prompt` bodies), which is a behavior-risking redesign and a human's call.
- `StallWatchdog` IS NOT LIFTED because it ALREADY IS: the logic has one definition in `runner_shared` and
  each host subclasses it solely to bind its own `terminate_process`, which forwards that module's tunable
  grace constants at call time. Flattening the subclass to satisfy the scanner's predicate would make
  those constants inert, which is the exact defect the subclass exists to prevent.
  - Carrier-Declined: Nothing is owed, because THE WORK IS ALREADY DONE. `issubclass` measures True on
    both hosts against `runner_shared.StallWatchdog`, so there is no duplicated logic left to lift and no
    obligation to carry. The only thing outstanding is a limitation of the SCANNER'S predicate
    (`is_pure_delegation` requires a single-statement delegation, which a subclass is not), and that
    limitation is documented in F-11 precisely so nobody files it as duplication. A carrier here would
    create a ticket whose only possible resolution is the harmful one.
- THE SIX DIVERGENT FORKS are out of scope: `build_parser`, `execute_item`, `handle_audit_command`,
  `initialize_run`, `main`, `run_queue`. Five are the LARGE functions whose split has its own long history
  (`rununify` 07-11 each measured it and recorded `NO SPLIT WAS PERFORMED`), and `handle_audit_command` is
  deliberately one-sided (the agy body is a refusal naming the working spelling, which is a host
  CAPABILITY difference and not drift). Nothing here touches them.
  - Carrier-Declined: NOTHING IS OWED BY THIS PLAN, and no in-tree citation would be honest here, which
    is why this declines rather than claiming evidence: the divergent set is NOT addressed, it is simply
    not this plan's concern. Its disposition is already RECORDED by an executed acceptance plan
    (`04vf1h`, hostdedup Order 04) which re-derived the residue by name and classified each symbol, and
    the three backlog items that owned specific divergent symbols (`xw4rb7`, `ga2dz1`, `zt2b16`) are all
    `done`. What remains is the FIVE LARGE FUNCTIONS, and filing an item for them would duplicate an
    authorization that already exists and has stalled five times on its own merits: `rununify` 07-11 are
    five approved plans that each performed the measurement and recorded `NO SPLIT WAS PERFORMED`, and
    `a5wdne`'s own Deferred section says the correct next step is a maintainer DECISION about those five
    plans, not a sixth plan over them. That decision is a human's. Stated as a reportable fact rather
    than smuggled: there is no LIVE carrier for the large-function split today, and this plan is not the
    place to create one.
- NO BEHAVIOR CHANGE OF ANY KIND belongs in this plan: not the exit codes, not the stream routing, not the
  narration wording, not the refusal sentences, not the colorization decision. A lift that also fixes
  something makes the fix invisible in review. If the executor finds a defect in either body, file it.
  - Carrier-Declined: This row records a PROHIBITION ON THIS PLAN, not a deferred defect, so nothing is
    owed and there is nothing for a carrier to own. No finding here measures a fault in either body; the
    whole premise is that both are correct and merely duplicated. The prohibition is enforced inside this
    plan by the scope fence, by E-02's and E-03's explicit "preserve verbatim" requirements, and by V-02's
    and V-03's demand for a diff showing each body moved unchanged. Its closing sentence already routes any
    defect an executor DOES find to a new item, which is the handoff, rather than to this row.

## Scope check

- Over-scope: none. E-02 and E-03 move code without changing it; E-04 and E-05 add or run the checks the
  move makes prudent; E-01 and E-06 are the measurement gates. The two test files in `Scope-Paths` beyond
  the three source modules are there because E-04 adds assertions to them, and `tests/test_runner_shared.py`
  is declared because E-04 reuses its exported fixtures and may need to widen what it exports.
- Under-scope: deliberate and named. This plan lifts 2 of the 4 byte-identical symbols and 0 of the 6
  divergent ones, leaving 8 real forks by the scanner's count. Both exclusions from the identical set are
  recorded decisions (see Deferred) rather than remaining work this plan declines, and the divergent set
  has its own history. Also NOT done: re-creating a `STILL_DOUBLE_DEFINED`-style census guard to replace
  the ones `19313eed` deleted. That would be a symbol census, which GUIDING_PRINCIPLES P16 prohibits
  outright, so the anti-re-fork protection here is behavioral (E-04) by design and not by omission.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, with both summary lines pasted and the invocation form
  stated. Do not add flags: `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal
  -m 'not slow'`, and a second `-q` would suppress the very summary line this requires. CAPTURE THE BEFORE
  LINE FRESH at execution HEAD and compare FAILING NODE IDS, never a total read from this plan: the bare
  total is a live population that every merged lane moves and it measured `3312 passed, 2 skipped` at
  review.
- THE TWO HOST SUITES AND THE SHARED ONE RUN TOGETHER, which is the narrow gate for this change:
  `python3 -m pytest tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py`.
  Authoring baseline in this lane at HEAD `8fdc89f0`: `357 passed in 24.05s`; re-measured at review, the
  COUNT held at `357 passed` while the wall time did not (`134.62s`), so treat the count as the bar and the
  timing as noise.
- THE SCANNER RE-RUN AFTER THE LIFT, showing `REAL FORKS` at 8 and `byte-identical` at 2 with neither
  lifted symbol listed. This plan asserts that outcome in its Scope check and E-06 is what measures it;
  a green suite alone cannot, because a multi-statement wrapper passes every test while leaving both
  symbols forks (F-12).
- `python3 -m pytest tests/test_attention.py` for E-05, with `LaneRemedyHintTests` shown passing and NOT
  edited.
- THE EXIT-CONTRACT PIN IN BOTH DIRECTIONS AND ON BOTH HOSTS, driven through each host's real `main`: a
  refusal exits nonzero with the refusal on stderr and nothing on stdout; a success exits 0 with the
  confirmation on stdout. This is the check that would catch F-7's unasserted contract, and a green suite
  without it proves nothing about the property this plan is protecting.
- EACH HOST'S MERGE SUBJECT STILL NAMES ITS OWN DRIVER, from a real merge: `integrate(aw oc run): merge
  verified lane <id6> to main` and `integrate(aw agy run): ...`. These tests exist already
  (`tests/test_oc_runipd.py::HostIntegrateVerbTests::test_this_hosts_merge_subject_says_aw_oc_run` and the
  agy twin); paste them green, because the host label is the one thing a shared body cannot bind and is
  the most plausible way this lift goes wrong.
- THE CLOSURE OUTPUT from E-01 pasted BEFORE any lift evidence, with the scanner's metric quoted as it
  prints it.
- `git diff` evidence that each body moved UNCHANGED, including the `should_color(sys.stdout)` /
  `file=sys.stderr` pairing and the `getattr(args, ...)` tolerance.
- NO SOURCE-INSPECTION, CENSUS, OR DOCSTRING ASSERTION may be added by this plan (GUIDING_PRINCIPLES P16).
  If the executor feels the need for one to prove the lift happened, that is the signal to assert the
  behavioral consequence instead.

## Spec / documentation sync

No `.spec.md` governs which module hosts a runner symbol, and this plan changes no runner BEHAVIOR, so no
spec amendment is declared and no `.spec.md` appears in `Scope-Paths`. Spec `25kzda` constrains the
deterministic run-and-verify behavior these symbols participate in, and the exit contract and stream
routing this plan lifts are preserved byte for byte, so nothing it says becomes stale. If the executor
finds itself needing to change a spec, that is evidence the lift stopped being decision-free and it should
stop and report rather than amend.

## Open questions

### OQ-01: Should the lifted `handle_integrate_command` take the host bindings as parameters, or read them from a `HostLabels`-style descriptor?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: TAKE THEM AS PARAMETERS, resolved from repository evidence rather than
  preference. The function one layer down already does exactly this: `runner_shared.reintegrate_lane` is
  declared `(repo, id6, *, integrate, suite_check, run_id=None, candidate=None)`, and
  `runner_shared.integrate_stranded_lanes` is keyword-only across `integrate`, `suite_check`, `save_state`,
  `append_jsonl`, `process_backlog_close` and `report`. A descriptor would be the wrong instrument twice
  over: `HostLabels` carries STRINGS (its own docstring says "Every host-varying STRING"), while what
  varies here is a CALLABLE, and the one host-varying string in play (`"aw oc run"` versus `"aw agy run"`)
  is already carried inside `integrate_lane_branch` rather than being read at this layer. So the injected
  callable brings its own label and the descriptor is not needed. Adding a `HostLabels` field for a value
  no body at this layer reads would be a parameter nobody consumes, which `li44r9`'s own rule forbids.

### OQ-02: Should this plan restore a census-style anti-re-fork guard to replace the tables `19313eed` deleted?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, and the repository has already ruled on it in general terms, so
  this is not a judgement call. GUIDING_PRINCIPLES P16 prohibits "No count or census pins" and "No
  architectural placement pins" explicitly, and the managed `AGENTS.md` block restates the prohibition
  for restored coverage specifically: "NEVER assert on caller counts, symbol censuses, or module line
  counts as a proxy for correctness", and restored coverage "must always exercise the code". A
  `STILL_DOUBLE_DEFINED` table is precisely a symbol census over production source, and the four files
  carrying such tables were deleted in a commit whose subject is trimming the suite. Restoring one would
  re-introduce what the principle forbids and what that commit removed. The protection this plan provides
  instead is E-04's behavioral pin, which is strictly stronger against the failure that matters: a census
  guard notices that a host re-defined a symbol, while E-04 notices that a host CHANGED WHAT THE VERB DOES,
  which is the harm. A re-fork that preserves the exit contract and the streams is invisible to E-04 and
  that is accepted: by P16's own reasoning, if the behavior is indistinguishable there is nothing left to
  complain about.

  ONE COUNTEREXAMPLE MUST BE NAMED RATHER THAN OMITTED, added at review, because the answer above cites
  P16 one-sidedly. The tree ALREADY SHIPS a per-symbol AST re-fork guard and it passes today:
  `tests/test_runner_shared.py::test_add_output_mode_flags_not_reforked_in_hosts` parses both host modules
  and asserts each host's `_add_output_mode_flags` is exactly one non-docstring statement calling
  `runner_shared.add_output_mode_flags`, and that neither body calls `add_argument` directly (F-15). That
  is not a census TABLE over many symbols, which is the form P16 most clearly forbids and which the four
  deleted files carried; it is a single-symbol shape assertion with its own recorded coverage bound. It is
  nonetheless in genuine tension with P16's "No architectural placement pins: Do not assert which module
  holds a `def` by inspecting ASTs or module dictionaries". THE ANSWER STAYS NO for this plan, on a
  narrower and honest basis: adding such a guard would be a THIRD production-shape assertion in a plan
  whose whole premise is that it changes no behavior, and the precedent's existence makes it a maintainer's
  call about P16's boundary rather than something a decision-free lift may settle. What changes at review
  is that the precedent is now visible to the reviewer instead of the plan implying no such thing exists.

### OQ-03: Is the scanner's `disable_lane_prompt` NEITHER-DELEGATES residue something this plan should close?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO. It is the scanner's STRICT residue (1 symbol, 3 lines) and it is
  the one symbol the shared module refuses to accept, in writing, with its reason: a shared `global` would
  write `runner_shared`'s flag while each host's `_lane_reclaim_prompt` kept reading its own, so prompt
  suppression on a repeated interrupt would silently stop working. That refusal is pinned by
  `tests/test_forkresid_shared_shells.py::LanePromptSuppressionTests`. The residue number is therefore a
  correct report of a deliberate state, not an open defect, and closing it would need a redesign of how the
  flag is read (a mutable shared cell, or threading the state through both `_lane_reclaim_prompt` bodies)
  which is a behavior-risking change with its own review, not a line in a decision-free lift.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the two scanner invocations pasted with their output INCLUDING the metric line the
    tool prints, and the identical set compared explicitly against this plan's four symbols. Plus a
    two-part verdict on the item's classification note: whether `tests/test_rununify_main.py` exists at
    execution HEAD (paste the command that answers it), and whether each of `integrate_lane_branch` and
    `run_suite_check` is host-specific or shared (paste an `is`-comparison across all three modules). Any
    divergence from the authoring measurement stated, not absorbed. PLUS the pre-lift
    `is_pure_delegation` baseline for both symbols on both hosts, with the statement count beside each
    verdict, since that predicate is this plan's success criterion (F-12) and V-06 compares against it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the shared definition's signature quoted, plus the `git diff` for both hosts showing
    each body replaced by a thin delegation at the UNCHANGED name and `(run_dir, state)` signature. The
    diff must show `Palette(should_color(sys.stdout))` and `file=sys.stderr` still paired as they are
    today. Plus proof the single call site in each host's `run_queue` is byte-unchanged (show it in the
    diff context or state that the diff does not touch that line). Plus the resume-pass behavior still
    working end to end on BOTH hosts: `tests/test_oc_runipd.py::HostResumeIntegratesInsteadOfDispatchingTests`
    and `tests/test_agy_runipd_cli.py::AgyResumeIntegratesInsteadOfDispatchingTests` pasted green, since
    those drive each host's real `run_queue` through the lifted shell. PLUS the wrapper shown to be
    EXACTLY ONE non-docstring statement, with `tools.runner_fork_scan.is_pure_delegation` returning True
    for both host wrappers where it returned False at HEAD. A multi-statement wrapper leaves the symbol a
    REAL FORK by the scanner's own predicate, so the lift would not have been performed (F-12); a diff
    that merely looks smaller does not satisfy this.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the shared definition's signature quoted, plus the `git diff` for both hosts showing
    a thin delegation at the unchanged name. The `getattr(args, ...)` tolerance shown preserved. Plus
    `hasattr(oc_runipd, "handle_integrate_command")` and the agy equivalent both True after the lift,
    pasted (this is the F-8 attribute, and its absence would silently degrade a production hint). Plus the
    existing both-spellings routing tests green on both hosts
    (`test_both_spellings_reach_the_same_implementation` and
    `test_both_spellings_reach_the_shared_implementation_once`), because they spy on the shared call and
    would catch a wrapper that stopped reaching it. NOTE those two tests have DIFFERENT names per host
    (`test_both_spellings_reach_the_same_implementation` is oc's,
    `test_both_spellings_reach_the_shared_implementation_once` is agy's), so name each against its own
    file rather than looking for both in both. PLUS `is_pure_delegation` True with a statement count of 1
    for both host wrappers, as in V-02. PLUS confirmation that no docstring this item writes cites
    `tests/test_runner_shared.py::NoRunnerImportTests`, which does not exist (F-14).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the new test code quoted, and its run pasted green. The evidence must show, PER
    HOST and in BOTH directions, four concrete observations: refusal exit code (nonzero), refusal stream
    (stderr carries the refusal text), refusal stdout (EMPTY), and success (exit 0 with the confirmation on
    stdout). Plus a demonstration that the new assertion is SENSITIVE rather than vacuous: state what
    would have to change in the production body to make it fail, and prefer showing it (for example by
    temporarily inverting the stream choice and pasting the failure) over asserting it. Plus both hosts'
    merge-subject tests pasted green, unedited.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `python3 -m pytest tests/test_attention.py` pasted green, with `git diff --stat`
    showing that file UNCHANGED by this plan. Plus the hint itself for one concrete id6, showing it still
    reads `Recover it with \`aw oc integrate <id6>\`.` rather than the by-hand degradation.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the BEFORE and AFTER `python3 -m pytest` summary lines pasted, with the invocation
    form stated verbatim and shown to carry no added flags, where the BEFORE line is captured fresh at
    execution HEAD and NOT read from this plan (the bare total is a live population; it measured
    `3312 passed, 2 skipped` at review). Compare failing NODE IDS rather than totals, and name any
    difference. A claim of "no new failures" without both lines does not satisfy this item. PLUS the
    post-lift scanner run pasted, showing `REAL FORKS` at 8 and `byte-identical` at 2 with neither lifted
    symbol in the IDENTICAL FORKS section; without that the plan's own asserted outcome is unverified.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A decision-free code move: two byte-identical host shells get ONE definition in
`runner_shared`, reached from each host by the sanctioned thin-wrapper form, plus the behavioral pin
(exit code paired with stream routing, both directions, both hosts) that does not exist today. No exit code,
stream, narration string or refusal sentence changes. I verified every measurement in this plan rather than
taking any on trust: the scanner's census reproduces byte-for-byte on a later HEAD (`REAL FORKS 10`,
`byte-identical 4`, both targets at similarity `1.000`), both bodies really are byte-identical between
hosts, the closure is fully injectable, `tests/test_rununify_main.py` is gone, `run_suite_check` really is
one shared object while `integrate_lane_branch` is not, the exit contract really is unasserted (both hosts
measured `rc=1`, empty stdout, identical refusal on stderr), and the `attention` probe really does degrade
when the attribute is removed.

REVIEW ADDED ONE SUBSTANTIVE REQUIREMENT AND THREE CORRECTIONS, none of which changes the design. THE
REQUIREMENT: the plan asserted its own success ("leaving 8 real forks") but no item measured it, and both
target bodies are MULTI-STATEMENT today (3 and 6), which is exactly why `is_pure_delegation` returns False
and the scanner counts them as forks. So a wrapper that kept one setup line would have passed every
original V-item while the census stayed at 10 and the work was not done. E-01 now captures the predicate
baseline, E-02/E-03 require a single-statement wrapper, and E-06 requires the census to be shown dropping to
8/2. THE CORRECTIONS: the cited `NoRunnerImportTests` DOES NOT EXIST (deleted in `19313eed`), so a docstring
must not send an executor to it; the tree ALREADY SHIPS a per-symbol AST re-fork guard that OQ-02's P16
citation did not acknowledge, which is now named so the reviewer sees the tension rather than a one-sided
argument; and the suite baselines drift (bare `3312` at review), so comparisons must use freshly captured
node-id sets.

EXECUTION CONTRACT. Commit ONLY the paths this plan declares in `Scope-Paths`, through `aw commit <plan>
-- <paths>`, never `git add -A` and never with `--no-verify`, and never push. Paste ACTUAL runner output
for every test claim; a summary written from memory is not evidence. This plan changes NO behavior, so it
has no license to re-base an assertion: a test that fails only after the lift is a regression in this
plan's own work and must be fixed in the production code. An edit outside the declared paths is to be MADE
and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, not treated as a reason to stop. DO stop
and report for the genuinely unsafe conditions: E-01's refusal condition below, and a case where the
single-statement reduction turns out NOT to be reachable for either symbol, because that would mean a
host-varying VALUE survives in the body and the lift is no longer decision-free.

FOUR WAYS THIS PLAN CAN FAIL SILENTLY, all measured at review, and a green suite catches none of them.
FIRST, A WRAPPER THAT IS NOT THIN. Leave `repo = Path(state["repo"])` or `pal = Palette(...)` in the host
body and every test still passes while `is_pure_delegation` stays False, the symbol stays a REAL FORK, and
the plan's stated outcome is false. SECOND, COMPARING SUITE TOTALS instead of node ids, where a drifting
live count reads as a regression that did not happen. THIRD, "TIDYING" `should_color(sys.stdout)` to
`should_color(sys.stderr)` while moving the narration sink, which looks like a typo fix and is a
colorization behavior change under redirection (F-9). FOURTH, DROPPING THE HOST ATTRIBUTE. If either host
module stops carrying `handle_integrate_command`, `attention.lane_remedy_hint` silently degrades to the
by-hand sentence; measured at review by deleting the attribute, and `tests/test_attention.py::LaneRemedyHintTests`
would catch it via its `hasattr` assertions on both hosts, which is why E-05 is a check and not a change.

POST-GATE LIFECYCLE. Do not hand-edit the terminal state and do NOT hand-roll a `git mv` into
`.aw/records/plans/executed/`: that bypasses the scope reconciliation this fence depends on. The transition
is obligatory but its OWNER is conditional (`AW-LIFECYCLE-ROLE-001`): under a managed runner
(`aw oc run` / `aw agy run`) the RUNNER owns finalize and the executor must not call it, while for a
hand-run execution the executor calls `aw ipd finalize` once `aw ipd lint --phase pre-transition` reports
conforming AND every `V-*` above carries concrete pasted evidence. E-01's refusal condition is real: if the
re-measurement disagrees with F-1, F-2, F-3 or F-6, stop and report the disagreement rather than proceeding
on this plan's authoring numbers.

BACKLOG ITEM `baskrx` IS ALREADY `graduated` and needs no transition; verified at review, it carries
`- Status: graduated` and `- Graduated-To: baskrx`. Its `- Work-Kind:` is `chore`, which is NOT in the
repository's release-gating set (default `bug` alone), so this plan correctly carries no
`- Blocks-Release:` and none should be added.

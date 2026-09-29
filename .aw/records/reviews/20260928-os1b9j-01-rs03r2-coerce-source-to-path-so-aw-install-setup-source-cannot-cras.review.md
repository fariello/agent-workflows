# Review findings: plan rs03r2

- Subject-Id: rs03r2
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `da816198` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after revision (exit 0, `findings: 0`). No pre-review snapshot was owed: the plan was
committed and unmodified, byte-identical to its `.aw/state/lane-inputs/rev-6/` copy. No production
code was modified by this review; every fix-side measurement was staged through `mock.patch.object`
or an out-of-tree pytest plugin, and every install was driven into a throwaway `git init` repo under
`.aw/state/` that was removed afterwards, with `git status --short` empty before and after.

**THE PLAN IS CORRECT ABOUT THE BUG AND ABOUT THE FIX, AND BOTH WERE INDEPENDENTLY RE-MEASURED
RATHER THAN TAKEN ON TRUST.** F-01 reproduces exactly, including every frame in order: `cli.main` ->
`_dispatch` -> `_run_install` -> `_diagnostics_ok` -> `engine.build_install_plan` ->
`engine.resolve_source_root` -> `AttributeError: 'str' object has no attribute 'expanduser'` at
`candidate = provided.expanduser().resolve()`. It is an unhandled traceback, not a diagnostic:
`cli.main` catches only `KeyboardInterrupt` and `EOFError`. F-02 reproduces (the identical command
plus `--dry-run` exits `OK [DRY RUN] No changes written`, and the dry-run `continue` precedes the
`_diagnostics_ok` call). F-03 reproduces (`engine.parse_args` declares `type=Path`; both `cli.py`
declarations omit it). F-04's crash claim reproduces when a `setup`-parsed namespace is handed
directly to `_diagnostics_ok`. F-05 reproduces exactly: three `cli.py` sites wrap as
`Path(args.source_root).expanduser()` while `build_install_plan` passes raw. F-08 reproduces
(`--source` appears zero times under `tests/`). F-11's provenance reproduces (`git log -S` ->
`ccceb144`). AND THE FIX WAS MEASURED: with the coercion staged in memory the previously crashing
real install runs to completion and reports `Changes committed successfully.`, the str/`Path` parity
probe returns the same resolved bundle path, and the bare suite reports `3202 passed, 2 skipped, 3
warnings` both with and without the patch, so nothing in the tree depends on the resolver rejecting a
string. The `type=Path` tilde concern E-02 raises is real and correctly analyzed: `type=Path` yields
`PosixPath('~/somewhere')` with the tilde intact, so the resolver's own `.expanduser()` remains
load-bearing.

**EVERY FINDING THIS ROUND IS IN THE EVIDENCE THE PLAN HANDS ITS EXECUTOR, NOT IN ITS DESIGN.** The
three-line fix is right. What review found is that four of the plan's own measurements would send an
executor down a wrong path, and two would have them assert against figures that have already moved.

**PR-901 (MEDIUM): F-10's REPRODUCER PRESCRIPTION IS OVERSTATED, AND E-03 INHERITS IT AS A HARD
REQUIREMENT.** F-10 says a reproduction "MUST pass `--preset private-target --delivery-mode tracked
--records-backend repository -y`". Measured on a fresh repo per invocation, the crash is reached by
the full three-flag set, by `-y` ALONE, and by `--preset private-target` alone; only a wholly
flagless non-interactive invocation refuses with the `FAIL Noninteractive first install requires
complete policy choices` message. The mechanism is in `_run_install`, which auto-supplies
`explicit_preset = Preset.PRIVATE_TARGET.value` when `--yes` is passed with no `--preset` and no
`--delivery-mode`. This matters practically rather than pedantically: E-03 and V-01 both inherit the
prescription, so the new regression test couples itself to three policy surfaces that have nothing to
do with this defect and can each change independently, breaking the test for the wrong reason.

**PR-902 (LOW): BOTH SUITE FIGURES HAVE DRIFTED BY 93 TESTS, AND THE PLAN TELLS THE EXECUTOR TO
REPORT THAT AS A FINDING.** F-07 and Required tests cite `3109 passed, 2 skipped`, and Required tests
adds that "a materially different count is itself a finding to report rather than to normalize".
Review's clean-tree bare run reads `3202 passed, 2 skipped, 3 warnings in 71.88s`. An executor
obeying that instruction literally opens a finding about other people's work. The count is a live
population; the bar is zero failures and a delta against the executor's own baseline.

**PR-903 (LOW): `tests/test_doctor.py` NEVER REACHES THE BRANCH E-01 CHANGES.** Required tests names
it alongside `test_installer.py` as one of "the modules that call `resolve_source_root` directly ...
and so are the likeliest to notice a mistake in E-01". Both of its calls are
`resolve_source_root(None)`, which takes the `provided is None` arm entirely. `test_installer.py`
genuinely does pass a value and is the real guard. The module is cheap to run, so the fix is to
correct the stated rationale rather than drop it, but as written it would let an executor believe
their evidence covers something it does not.

**PR-904 (MEDIUM): A REAL `aw setup` RUN MUTATES STATE OUTSIDE THE WORKSPACE, WHICH IS A STRONGER
REASON THAN COST FOR E-03's PARSER-LEVEL COVERAGE.** E-03 justifies covering `setup` only at the
parser level because "a full `setup` install is expensive and interactive to drive end-to-end". True,
but the binding reason is that `aw setup` DISCOVERS REPOS ACROSS THE USER'S FILESYSTEM and WRITES
`~/.config/agent-workflows/config.json`. Review triggered exactly that while probing F-04: the run
enumerated directories far outside this workspace and reported `Saved config to <user config path>`.
An executor reading only "expensive and interactive" may decide the cost is acceptable and drive it.
Recorded with the safe alternative review used instead (parse the namespace, call `_diagnostics_ok`
directly), which covers the real crash site on that verb with no side effects.

**PR-905 (LOW): F-09's COUNT IS WRONG AND ITS `engine.py` CLAIM CONTRADICTS THE STEP-0 BULLET.**
F-09 says `Path | str` appears "on 18 parameters" in `runner_stop.py`; the measured count is 13. More
consequentially, the Step-0 conventions bullet says to prefer the modern spelling "which `engine.py`
already uses for its own annotations elsewhere", while F-09 correctly states `engine.py` has none and
that E-01 introduces the first. The convention claim itself is sound and is what E-01 relies on.

**PR-906 (MEDIUM): THE GATE CARRIED NO SCOPE FENCE AND NO APPROVAL SUMMARY.** The gate had the
execution contract, the lifecycle transition and the maintainer-overrule note, but no declared fence
the runner can reconcile against and no one-paragraph statement of what a human is approving. The
fence matters here because the plan has four distinct negative constraints scattered through its
Deferred section (do not remove the three call-site coercions, do not reorder `--dry-run`, do not
touch the rest of `resolve_source_root`, do not coerce `repo_root`), each with its own measured
reason, and none of them was collected where an executor looks.

**WHAT REVIEW CHECKED AND FOUND SOUND.** All four Deferred entries are correct, and the `repo_root`
one was verified rather than accepted: `engine.parse_args` declares `--repo` as `type=Path`,
`_diagnostics_ok` assigns the already-`Path` argument, and `engine.main` assigns from `repo_roots`,
so no caller reaches that line with a string and there is genuinely no defect to fix. The
`--dry-run` deferral is well argued on three independent grounds. E-03's three hard constraints
(enter through the CLI, pass a string, never `--dry-run`) are each necessary and each backed by a
measurement. Right-sizing is appropriate: three E-items, one deliverable each, correctly sequenced.
The spec-sync section is correct that no approved spec governs `resolve_source_root`'s parameter type
or the argparse declaration, and that this restores behavior the flag's own help text promises. The
`Blocks-Release: next` gate is correctly inherited from item `os1b9j` per the every-live-bug rule,
and the gate prose correctly forbids closing the item `done` before execution.

Every finding is FIXED by in-place revision. None was deferred, so no escalation to a
`- Blocking: yes` question is owed and none was written. OQ-01 and OQ-02 both survive review
unchanged and are UPHELD on re-measured evidence: OQ-01's tiebreaker (the resolver has seven call
sites and the three that forward a user value each hand-roll the coercion the broken path forgot) was
independently confirmed, and OQ-02's three grounds hold.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | MEDIUM | IN-SCOPE | E. Testing / A. Correctness (evidence accuracy) | four invocations, each into its own fresh `git init` repo: full three-flag set -> `AttributeError`; `-y` alone -> `AttributeError`; `--preset private-target` alone with `< /dev/null` -> `AttributeError`; no flags with `< /dev/null` -> `FAIL Noninteractive first install requires complete policy choices`; the `explicit_preset = Preset.PRIVATE_TARGET.value` auto-default branch in `_run_install` | F-10's THREE-FLAG REPRODUCER PRESCRIPTION IS OVERSTATED, AND E-03/V-01 INHERIT IT AS A REQUIREMENT. `-y` alone reaches the crash, because `--yes` with no `--preset`/`--delivery-mode` auto-supplies the default preset. Writing three flags into the regression test couples it to three policy surfaces unrelated to this defect, each independently changeable, so the test can fail for a reason that has nothing to do with the bug it guards. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 narrowed in place with the measured correction; added F-12 with all four invocations and the auto-default mechanism. E-03's fixture paragraph now prescribes `-y` alone as the minimum and explicitly warns against hardcoding the three policy flags. Required tests' reproduction bullet and V-01 both updated, and both now require a FRESH repo per invocation (an already-installed repo is no longer a first install). The Step-0 conventions bullet corrected. |
| PR-902 | LOW | IN-SCOPE | G. Plan executability (live-artifact convention) | review's clean-tree `python3 -m pytest` -> `3202 passed, 2 skipped, 3 warnings in 71.88s` at HEAD `da816198`, against F-07's `3109 passed, 2 skipped` at `36904869` | BOTH SUITE FIGURES HAD DRIFTED BY 93 TESTS WHILE THE PLAN INSTRUCTED THE EXECUTOR TO REPORT A DIFFERING COUNT AS A FINDING. That instruction, followed literally, produces a finding about unrelated work landing between authoring and execution. A count over a live population is context; the bar is zero failures and a delta against the executor's own pre-work baseline. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-14 with both measurements. The full-suite bullet now carries both figures labelled as context, states the 93-test drift as the reason, and explicitly removes the report-a-differing-count instruction. V-03 now requires a delta against the executor's own baseline rather than a transcribed figure. |
| PR-903 | LOW | IN-SCOPE | A. Correctness (evidence accuracy) / E. Testing | `rg -n "resolve_source_root" tests/test_doctor.py` -> two `engine.resolve_source_root(None)` calls; `tests/test_installer.py`'s `INS.resolve_source_root(self.root)` passing a real `Path`; the `provided is not None` branch guard in `engine.resolve_source_root` | `tests/test_doctor.py` NEVER REACHES THE BRANCH E-01 CHANGES, so the plan's stated reason for running it is wrong. Both its calls pass `None` and take the other arm. Running it is harmless breadth, but as written an executor would believe that green run is evidence about E-01 when it proves nothing. `tests/test_releases.py` is a third unmentioned `None`-passing caller. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-15 establishing which callers pass a value and which pass `None`. The focused-surface bullet now names `test_installer.py` as the real guard, keeps `test_doctor.py` as breadth explicitly labelled non-evidential, and names `test_releases.py`. V-01's evidence requirement narrowed to `test_installer.py` with the same caveat. |
| PR-904 | MEDIUM | IN-SCOPE | B. Security and privacy / C. Architecture and operability | an observed real `aw setup --source` run enumerating directories outside this workspace and reporting `Saved config to <user config path>`; the guarded path (`setup` resolves `source_root` with its own `Path(...)` wrapper first, and reaches `_diagnostics_ok` only inside `if found.targets and _confirm(...)`); a direct `_diagnostics_ok(Path("."), setup_args)` call raising the `AttributeError` | A REAL `aw setup` RUN MUTATES STATE OUTSIDE THE TARGET REPO AND OUTSIDE THE WORKSPACE, and E-03 justified its parser-level coverage only as "expensive and interactive". An executor who judges that cost acceptable will drive the verb and scan the user's filesystem plus write a user-level config. The correct reason is side effects, not cost, and the safe alternative (parse the namespace, call `_diagnostics_ok` directly) covers the actual crash site rather than only the parsed type. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-16 with the observed side effects, the guarded reachability path, and the direct probe. E-03's both-verbs paragraph now forbids driving the real verb with the side-effect reason stated, and offers the side-effect-free `_diagnostics_ok` probe as optional stronger coverage. V-02 forbids obtaining the parsed type by running the verb and requires `cli._build_parser()` instead. A Step-0 conventions bullet and the execution contract both carry the warning. |
| PR-905 | LOW | IN-SCOPE | A. Correctness (evidence accuracy) | `rg -o "Path \| str\|str \| Path" agent_workflows/runner_stop.py \| wc -l` -> 13, with the 13 lines enumerated; per-file counts `run_analytics_query.py` 7, `run_analytics_privacy.py` 2, `engine.py` 0, `run_cli.py` 3 `Union[str, Path]` | F-09's COUNT IS WRONG (13, not 18) AND THE STEP-0 BULLET CONTRADICTS F-09 ABOUT `engine.py`. The bullet says to prefer the spelling "which `engine.py` already uses for its own annotations elsewhere"; `engine.py` has zero, and F-09 correctly says E-01 introduces the first. The convention claim E-01 relies on is sound; a wrong number and a self-contradiction invite a reader to discount the row. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-17 with the corrected count and per-file breakdown, stating plainly that the convention claim holds. The Step-0 bullet corrected to 13 and its false `engine.py` clause replaced with the accurate statement that E-01 introduces the module's first such annotation. |
| PR-906 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | the gate section as authored, carrying the execution contract, the lifecycle move and the maintainer-overrule note but no declared fence and no approval summary; the four negative constraints scattered across the Deferred section | THE GATE CARRIED NO SCOPE FENCE AND NO APPROVAL-SUMMARY PARAGRAPH. The runner needs a declaration to reconcile the actual diff against, and this plan has FOUR distinct negative constraints (keep the three call-site coercions, do not reorder `--dry-run`, do not touch the rest of `resolve_source_root`, do not coerce `repo_root`) each with its own measured reason and none collected where an executor looks. A human approving also had no single paragraph stating what changes and what the user-visible effect is. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SCOPE FENCE naming the three paths and all four negative constraints with their reasons, and a WHAT A HUMAN WOULD BE APPROVING paragraph carrying the change, the user-visible effect, and review's re-measured evidence. The execution contract gained the in-memory-staging rule (both source files are shared-checkout) and the no-real-`aw setup` rule. The first gate paragraph updated from the authoring-time `to-review` wording to the reviewed state with its readiness and the approval command. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | F-10 prescribes three policy flags for the reproducer; review measured `-y` alone as sufficient. Correct the finding, or leave the belt-and-braces prescription in place? | CORRECT IT, and prescribe `-y` alone as the minimum while noting the three-flag form also works. | (a) Leave it: three flags do reach the crash, so the instruction is not false - rejected, because E-03 inherits it as a hard requirement and the test then depends on three policy surfaces unrelated to the defect, which is a real maintenance cost for zero coverage gain. (b) Drop the policy discussion entirely - rejected: a wholly flagless non-interactive install genuinely refuses before the defect, so an executor with no guidance hits a clean `FAIL` and may read it as the bug being absent, which is the exact false negative F-10 exists to prevent. | Four measured invocations (full set, `-y` alone, `--preset` alone, flagless) into fresh repos; the `explicit_preset = Preset.PRIVATE_TARGET.value` auto-default branch in `_run_install`. | yes |
| D-2 | `tests/test_doctor.py` proves nothing about E-01. Remove it from the required focused run, or keep it with a corrected rationale? | KEEP IT, with the rationale corrected and the module explicitly labelled non-evidential. | (a) Remove it - rejected: it is cheap, it exercises the resolver's other branch, and removing a passing module from a bug-fix plan's test list buys nothing while narrowing breadth. (b) Leave the rationale as written - rejected: it tells the executor their green run is evidence about E-01, and it is not; a false evidence claim in a V-item is exactly what the mutation-proof discipline elsewhere in this plan exists to prevent. | `rg -n "resolve_source_root" tests/test_doctor.py` -> two `(None)` calls; the `if provided is not None:` branch guard; `test_installer.py`'s value-passing calls. | yes |
| D-3 | E-03 defers end-to-end `setup` coverage on cost grounds. Should review restate the reason, or also widen the coverage? | RESTATE THE REASON as side effects (not cost) and OFFER the side-effect-free `_diagnostics_ok` probe as optional stronger coverage; do NOT require end-to-end `setup`. | (a) Require end-to-end `setup` coverage for symmetry with `install` - rejected on measured grounds: the verb scans the user's filesystem and writes a user-level config, so a test driving it would mutate state outside the repository under test, which no test in this suite should do. (b) Leave "expensive and interactive" as the reason - rejected: an executor may judge the cost acceptable and drive it, which is what review itself accidentally did. (c) Require the `_diagnostics_ok` probe rather than offering it - rejected: the parser-level assertion plus E-01's own coverage already close the defect, and mandating a second probe is scope the plan does not need. | The observed `aw setup` run enumerating outside directories and writing the user config; the guarded reachability path through `_confirm`; the direct `_diagnostics_ok` probe raising the same `AttributeError` with no side effects. | yes |
| D-4 | Review found six findings, two MEDIUM concerning evidence quality. Does any make this plan NO-GO, or is escalation owed? | NEITHER. All six were FIXED by in-place revision, so no unfixed BLOCKER/HIGH remains and the readiness is `go-pending-approval`. | (a) NO-GO on the MEDIUMs - rejected: severity is for reporting and the Fix Bar alone decides fixing; every fix here is a prose or evidence correction at Low Remediation Risk on all four axes, touching no code. (b) Escalate one as `- Blocking: yes` - rejected: escalation is owed only for a finding left OPEN or DEFERRED at or above the gate threshold, and none was left unfixed. (c) REPLAN - rejected outright: the three-line fix is correct and was independently verified to work and to be suite-clean. | The `plan-review` Fix Bar and readiness vocabulary; `aw ipd lint --phase review-finalize --agent` conforming after revision; `review_findings_gate` absent from `.aw/config/project.json` so the default `HIGH` threshold applies and nothing sits unfixed at it. | yes |
| D-5 | The gate had no scope fence. Should review add one, given the maintainer ruling that a fence must not instruct the executor to stop? | ADD A DECLARATIVE FENCE naming the three paths and the four negative constraints, with NO "STOP and report" clause. | (a) Leave the gate without a fence - rejected: the workflow requires the reviewer to ADD a missing execution-contract element in place and record it as a finding, and the runner needs a declaration to reconcile the diff against. (b) Add a fence with a stop directive for out-of-scope edits - rejected explicitly by the 2026-09-01 maintainer ruling: a fence is a DECLARATION, and the stop wording contradicts the work done to stop runs stranding unfinished turns; `aw ipd finalize` already enforces justification per out-of-scope path. | The plan-review Step 4 execution-contract requirement and its SCOPE-FENCE WORDING ruling; the four Deferred entries supplying the negative constraints, each already measured by the plan or by review. | yes |

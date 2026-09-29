# IPD: Prove the git_commit_helper commit-prompt fence holds, and stop the CI/AW_NONINTERACTIVE rung from overriding an explicit interactive=True

- Date: 2026-09-29
- Kind: child
- Concern: Backlog `41mtsm` reports that `git_commit_helper._is_interactive` keys on stdin alone, so a driver-spawned `aw` verb with stdin inherited and stdout piped prints `Commit these path-scoped changes? [Y/n]` into the pipe and blocks on `input()`. The ROOT CAUSE IS ALREADY FIXED IN CODE by commit `64c04288` (plan `da9n1s`), which landed AFTER the item was filed, so this plan does not re-fix it: it pins the fixed behavior with the behavioral regression test the item's measurement describes and that no test currently performs, corrects the two stale docstrings that still publish the superseded `sys.stdin.isatty()` contract, and fixes a SECOND defect measured while verifying the first, in which the forced-non-interactive rung swallows an EXPLICIT `interactive=True` argument and turns six tests red whenever `CI` is set (main is red on this today).
- Scope: `agent_workflows/git_commit_helper.py` (the `interactive=` docstring line and the `_is_interactive` argument-vs-environment ordering), `agent_workflows/term.py` (the `stdin_is_interactive` advice paragraph that names a superseded remedy), and `tests/test_git_commit_helper.py` plus `tests/test_stdin_interactive.py` (the behavioral pty-plus-pipe regression test and the ambient-`CI` isolation the six red tests need). NOT in scope: changing the maintainer-ruled asymmetric precedence ladder, editing any `.spec.md`, or repairing the unrelated red tests in `tests/test_completion.py` and `tests/test_runner_shared.py` (see Deferred).
- Scope-Paths: agent_workflows/git_commit_helper.py, agent_workflows/term.py, tests/test_git_commit_helper.py, tests/test_stdin_interactive.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 41mtsm
- Blocks-Release: next
- Set: 41mtsm
- Order: 1
- Highest E allocated: 05
- Author: agent aw oc run
- Id: 0brmmy

## Workflow history

- 2026-09-29 draft (agent aw oc run): created.
- 2026-09-29 to-review (agent aw oc run): authored from backlog `41mtsm` after re-measuring the reported reproduction at HEAD `b78c055c`. The reported wedge DOES NOT REPRODUCE (the fence now holds); a second, previously unrecorded defect in the same predicate DOES, and turns `main`'s CI red. Plan rewritten around what is actually true rather than around the item's now-stale premise.

## Goal

Close backlog `41mtsm` honestly. Its reported wedge no longer reproduces because plan `da9n1s` fixed the predicate a day after the item was filed, so the remaining real work is (a) to PIN the fixed behavior with a behavioral test that performs the item's own pty-plus-pipe measurement, since nothing in the suite does and the fence is therefore one careless edit from regressing silently; (b) to correct two docstrings that still publish the superseded stdin-only contract and steer readers to a remedy that is no longer the right one; and (c) to fix the defect found while verifying (a), in which `_is_interactive`'s delegation lets `CI`/`AW_NONINTERACTIVE` override an EXPLICIT `interactive=True` argument, which is both wrong on its own terms and currently red on `main`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the fence that is already correct

- [ ] E-01 Add a BEHAVIORAL regression test to `tests/test_git_commit_helper.py` that performs the backlog item's own measurement: spawn a child process with stdin on a REAL pty (`pty.openpty`) and stdout on a PIPE, have it call `git_commit_helper.offer_commit` on a throwaway repo with no `assume_yes`, and assert the call RETURNS `STATUS_SKIPPED` within a bounded timeout rather than emitting the `[Y/n]` prompt text into the pipe. Assert on BOTH observable outcomes: the returned status, and the absence of `Commit these path-scoped changes?` from the captured pipe bytes. Scrub `CI` and `AW_NONINTERACTIVE` from the child environment, or the test passes for the wrong reason (the env rung, not the output-stream rung). Mark it `skipif` on `win32`, where `pty` does not exist.
  - Depends on: none
  - Expected outcome: a test that FAILS against the pre-`64c04288` predicate and PASSES at HEAD, so the fence is pinned by behavior rather than by a mock asserting a delegation happened.
  - Execution state: pending

### Task group 2: correct the two docstrings that publish the superseded contract

- [ ] E-02 Correct the `interactive:` parameter line in `git_commit_helper.offer_commit`'s docstring, which still reads ``None`` -> ``sys.stdin.isatty()``. That is the exact contract this item was filed against and it is no longer what the code does: `None` now reaches `term.is_interactive`, which requires stdin AND the output stream to be a TTY and honors `AW_NONINTERACTIVE`/`CI`. State the real contract and name the resolver, so a reader cannot conclude from the docstring that the reported bug is still live.
  - Depends on: none
  - Expected outcome: the parameter line describes the shipped four-rung resolver; no occurrence of `sys.stdin.isatty()` remains as a description of this parameter's behavior.
  - Execution state: pending

- [ ] E-03 Correct the "honest limit" paragraph in `term.stdin_is_interactive`'s docstring, which tells a caller about to block on input to "use `artifact_adopt.leak_gate_is_interactive`". That advice is now misdirection: `leak_gate_is_interactive` is itself a two-line delegation to `term.is_interactive`, so the paragraph routes readers through an indirection instead of to the originating definition in the same module. Point at `term.is_interactive` directly, and keep the paragraph's still-true warning that `stdin_is_interactive` answers the narrower question. Do NOT delete the list of hardened sites; it is accurate history and explains why the stronger fence exists.
  - Depends on: none
  - Expected outcome: the paragraph names `term.is_interactive` as the predicate to use, with the three hardened sites preserved as the precedent they are.
  - Execution state: pending

### Task group 3: stop the env rung swallowing an explicit argument

- [ ] E-04 Fix `git_commit_helper._is_interactive` so an EXPLICIT `interactive=` argument is honored rather than being overridden by `CI`/`AW_NONINTERACTIVE`. Today it forwards the caller's value as `override=`, and `term.is_interactive`'s ladder places the forced-non-interactive rung ABOVE a positive override, so `_is_interactive(True)` answers False whenever `CI` is set. Return the caller's explicit boolean directly when it is not `None`, and delegate to `term.is_interactive()` only for the `None` case. DO NOT CHANGE `term.is_interactive`'s LADDER: its asymmetry is a maintainer ruling (plan `bmf32u` OQ-03, Gabriele Fariello, 2026-09-28, Option A) protecting a signal-handler prompt with no timeout, and this fix is deliberately local to the one caller that has a direct in-process argument rather than a user-facing flag. Record in a comment WHY the two differ: `--interactive` is an operator's ambient wish that CI must be allowed to veto, whereas `interactive=False`/`True` here is a programmatic caller's statement about a channel it already knows, and `runner_shared` passes `interactive=False` for exactly that reason.
  - Depends on: E-01
  - Expected outcome: `_is_interactive(True)` is True and `_is_interactive(False)` is False regardless of `CI`/`AW_NONINTERACTIVE`; `_is_interactive(None)` still reaches the resolver and still honors every rung.
  - Execution state: pending

- [ ] E-05 Make the six tests this defect turns red pass under an ambient `CI` by scrubbing `CI`/`AW_NONINTERACTIVE` in the two suites this plan owns (`tests/test_git_commit_helper.py`, `tests/test_stdin_interactive.py`), and assert the E-04 property directly rather than only implicitly: add a test that `_is_interactive(True)` stays True with `CI=1` set and `_is_interactive(False)` stays False with both unset. Scrub per-test with `monkeypatch.delenv`, NOT process-wide in `conftest.py`: a global scrub would mask the same class of defect in every other suite, and `tests/test_interactivity_resolver.py` deliberately drives these variables as inputs. Fix ONLY the failures inside this plan's two declared test files; the others are recorded in Deferred with their owner.
  - Depends on: E-04
  - Expected outcome: `tests/test_git_commit_helper.py` and `tests/test_stdin_interactive.py` pass both with `CI` unset and with `CI=true` exported, and the new assertion pins the argument-beats-environment property so a future revert of E-04 fails a test instead of only CI.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE INTERACTIVITY DECISION HAS EXACTLY ONE ORIGINATING DEFINITION, `term.is_interactive`, and `tests/test_interactivity_resolver.py` enforces that with an AST walk over every `*.py` in the package (`SingleOriginatingDefinitionTests.test_exactly_one_originating_is_interactive_in_package`). It maintains an explicit `SANCTIONED_DELEGATIONS` allowlist that names `("git_commit_helper.py", "_is_interactive")` and a `_is_pure_delegation` predicate requiring the body be ONE statement returning a single call on a module attribute. E-04 must therefore keep `_is_interactive` recognizable to that predicate or the guard fails; a plain `if interactive is not None: return interactive` guard added ABOVE the delegating return is what the pre-`64c04288` implementation looked like and V-04 must confirm the guard's verdict rather than assume it.
- THE ASYMMETRIC LADDER IS A RULING, NOT AN ACCIDENT, and must not be "tidied". `term.is_interactive`'s docstring states the order as `--no-interactive` > `AW_NONINTERACTIVE`/`CI` > `--interactive` > stream detection, and plan `bmf32u`'s OQ-03 records the maintainer adopting that Option A on 2026-09-28 because `runner_stop.interrupt_menu_is_safe` prompts inside a SIGNAL HANDLER with `readline()` and no timeout while holding the run lock. `runner_stop.interrupt_menu_is_safe`'s own docstring independently rules the same way for its `AW_FORCE_INTERACTIVE_INTERRUPT` escape: "a deliberate CI setting must win over a stale force flag".
- THE REPOSITORY HAS A MEASURED PRECEDENT FOR THIS BUG CLASS, cited at three code sites. `ipd_lifecycle.run_finalize`'s `ttywedge` comment records that stdin-only consent "wedged a real finalize for 1h49m holding its run lock, leaving the plan `approved` in pending/ while the run reported `complete`". That is why a stdin-only predicate is treated as a defect here rather than a style preference.
- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (AGENTS.md; GUIDING_PRINCIPLES P16). This is why E-01 spawns a real subprocess over a real pty instead of asserting that `_is_interactive` called a mock: the existing coverage is exactly such a mock (`test_git_commit_helper_reaches_resolver` asserts `is_interactive` was `called_once_with(override=None)`), and that test PASSES on a predicate that wedges, because it checks the wiring rather than the outcome.
- RUN THE SUITE BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. A narrowed run needing per-test counts clears the defaults with `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All findings measured in this lane worktree at HEAD `b78c055c`, git 2.43.0, Python 3.14.6, Linux.

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE REPORTED BUG DOES NOT REPRODUCE, AND THE ITEM IS NOT WRONG: IT IS STALE. A probe reproducing the item's stated shape exactly (child with stdin on a `pty.openpty` pty, stdout on a pipe, `CI`/`AW_NONINTERACTIVE` scrubbed, calling `offer_commit(repo, ["mine.txt"], message="probe")`) printed `STDIN_ISATTY True`, `STDOUT_ISATTY False`, then `OUTCOME skipped | skipped: non-interactive; pass --commit to commit these changes` and exited 0 well inside a 25s budget. No prompt text reached the pipe and nothing blocked. So the plan must NOT re-fix the predicate. | The probe run and its output, reproduced by E-01's test |
| F-02 | WHAT FIXED IT, AND WHY THE ITEM COULD NOT HAVE KNOWN. Commit `64c04288` ("feat(term): route every interactivity decision through one resolver (da9n1s)", 2026-09-28 14:09) rewrote `_is_interactive` from `if interactive is not None: return interactive` + `term.stdin_is_interactive()` to a single `term.is_interactive(override=interactive)`. The backlog item was filed 2026-09-27 03:16 (`d58de058`), roughly 35 hours EARLIER. Its measurement was correct when taken. | `git show 64c04288 -- agent_workflows/git_commit_helper.py`; `git log -1 --format=%ad d58de058` |
| F-03 | NO TEST PERFORMS THE ITEM'S MEASUREMENT, so the fence is pinned by nothing behavioral and a regression would be silent. The nearest coverage is `tests/test_interactivity_resolver.py::SanctionedPredicatesRoutingTests::test_git_commit_helper_reaches_resolver`, which patches `term.is_interactive` to return True and asserts it was `called_once_with(override=None)` - a WIRING assertion that passes on a wedging predicate. `tests/test_git_commit_helper.py::test_non_interactive_commit_modes` covers `interactive=False` and a `_FakeStdin` whose `isatty` returns False, i.e. the stdin-FALSE case, never the stdin-TRUE-and-stdout-PIPE case that is the whole bug. No `pty` import exists anywhere under `tests/`. | The two named tests; `rg -n 'pty' tests/` returns no import in any test module |
| F-04 | A SECOND DEFECT IN THE SAME PREDICATE IS LIVE, FOUND WHILE VERIFYING F-01. `_is_interactive` forwards its argument as `override=`, and the resolver's ladder puts the forced-non-interactive rung ABOVE a positive override, so an EXPLICIT `interactive=True` is discarded when `CI` is set. Measured directly: with `CI=1`, `term.is_interactive(override=True)` -> False and `git_commit_helper._is_interactive(True)` -> False; with both variables unset, both -> True. This is a real behavior change from the pre-`64c04288` code, which returned the explicit argument before consulting anything. | The two-command comparison under `CI=1` and under `env -u CI -u AW_NONINTERACTIVE` |
| F-05 | F-04 IS CURRENTLY RED ON `main`, WHICH IS WHY IT IS IN THIS PLAN RATHER THAN ONLY IN A NOTE. A bare `python3 -m pytest` in this lane passes (`3246 passed, 2 skipped, 3 warnings in 47.75s`); the SAME suite with `CI=true` fails 6 tests, `tests/test_git_commit_helper.py::test_interactive_commit_prompts_and_responses` among them (`assert 0 == 1` - `input()` was never called because the prompt branch was skipped). GitHub Actions exports `CI=true`, and run `36511595872` on `main` ("integrate(aw agy run): merge verified lane tl2b2r to main") FAILED with that same test named in its log on both the macOS py3.14 and Windows py3.12 jobs. | `python3 -m pytest` vs `CI=true python3 -m pytest` in this lane; `gh run view 36511595872`; the job log for 109224724582 naming `FAILED tests/test_git_commit_helper.py::test_interactive_commit_prompts_and_responses - assert 0 == 1` |
| F-06 | THE FIX BELONGS AT THE CALLER, NOT IN THE LADDER, because the ladder's order is a ruling. Plan `bmf32u` OQ-03 records the maintainer (Gabriele Fariello, 2026-09-28) adopting Option A so that `--interactive` beats detection only and never a CI signal, on the measured ground that a prompt inside `runner_stop`'s signal handler has no timeout and holds the run lock. Editing `term.is_interactive` to honor a positive override above the env rung would reverse that ruling for every site at once. The distinction that makes a local fix correct: the ladder governs an operator's ambient WISH expressed as a flag, while `_is_interactive`'s parameter is a programmatic caller's statement about a channel it already knows - which is how `runner_shared` uses it, passing `interactive=False` explicitly. | Plan `bmf32u` OQ-03 resolution text; `runner_stop.interrupt_menu_is_safe` docstring; the `interactive=False` call in `runner_shared` |
| F-07 | TWO DOCSTRINGS STILL PUBLISH THE SUPERSEDED CONTRACT. `offer_commit`'s `interactive:` parameter line still says ``None`` -> ``sys.stdin.isatty()``, which is precisely the contract `41mtsm` was filed against and is no longer what the code does. Separately, `term.stdin_is_interactive`'s honest-limit paragraph still advises "use `artifact_adopt.leak_gate_is_interactive` when a caller is about to block on input", although that function is now a two-line delegation to `term.is_interactive` in the very module the advice is written in. Both are cheap to correct and both actively mislead a reader trying to decide whether this item is still live. | The `interactive:` line in `offer_commit`'s docstring; the honest-limit paragraph in `term.stdin_is_interactive`; `artifact_adopt.leak_gate_is_interactive`'s two-line body |
| F-08 | THE SINGLE-DEFINITION GUARD CONSTRAINS HOW E-04 MAY BE WRITTEN, so this is a compatibility fact and not a style note. `tests/test_interactivity_resolver.py` allowlists `("git_commit_helper.py", "_is_interactive")` in `SANCTIONED_DELEGATIONS` and tests delegations with `_is_pure_delegation`, which requires exactly ONE non-docstring, non-import statement returning a call on a module attribute. An early-return guard adds a second statement, so V-04 must PASS that guard rather than assume it, and E-04 must not silently break it. | `SANCTIONED_DELEGATIONS` and `_is_pure_delegation` in `tests/test_interactivity_resolver.py` |
| F-09 | FOUR OTHER TESTS ARE RED UNDER `CI` FOR A DIFFERENT REASON AND ARE NOT THIS ITEM'S. `tests/test_completion.py` (3 tests) and `tests/test_runner_shared.py::IntegrationDeferralLadderTests::test_interactive_ask_behavior_and_prompt_predicate` also fail under `CI=true`, but they route through `cli._configure_completion` and `runner_shared`, neither of which this plan's `Scope-Paths` names. They share the same ROOT CLASS (a suite that assumes no ambient `CI`), so they want one deliberate decision about suite-wide isolation rather than four scattered patches. | The `CI=true` failure list; `grep -n is_interactive agent_workflows/cli.py` showing the completion prompt site at a `cli`-owned call |

## Proposed changes (ordered, validatable)

1. Add the pty-plus-pipe behavioral regression test for `offer_commit`'s fence, with the child environment scrubbed of `CI`/`AW_NONINTERACTIVE` and a bounded timeout, asserting both the returned status and the absence of prompt text in the pipe (E-01).
2. Correct `offer_commit`'s `interactive:` docstring line to describe the shipped resolver instead of `sys.stdin.isatty()` (E-02).
3. Correct `term.stdin_is_interactive`'s honest-limit paragraph to point at `term.is_interactive` directly, preserving the hardened-site precedent (E-03).
4. Make `_is_interactive` honor an explicit boolean argument ahead of the environment rung, leaving `term.is_interactive`'s ruled ladder untouched and recording why the two differ (E-04).
5. Scrub ambient `CI`/`AW_NONINTERACTIVE` per-test in this plan's two declared test files and assert the argument-beats-environment property directly (E-05).

## Deferred / out of scope (with reason)

- CHANGING `term.is_interactive`'s PRECEDENCE LADDER. Deliberately refused. Its asymmetry is a maintainer ruling (plan `bmf32u` OQ-03, 2026-09-28, Option A) grounded in a measured wedge, and it is published as normative in `docs/cli-output-contract.md`. This plan fixes ONE caller that holds a direct programmatic argument, and states in a comment why that is not the same thing as a flag. A reviewer who disagrees should say so before execution rather than have the ladder edited mid-run.
- REPAIRING THE FOUR OTHER `CI=true` FAILURES in `tests/test_completion.py` and `tests/test_runner_shared.py` (F-09). They are the same root CLASS but sit behind `cli` and `runner_shared`, which this plan's `Scope-Paths` does not name, and fixing them properly means deciding whether the suite wants one shared isolation mechanism. Doing it here would either take undeclared out-of-scope edits or install a `conftest.py` scrub that masks this very defect class everywhere else. Recorded as F-09 with its evidence so it is not rediscovered from scratch; needs its own backlog item, which this plan does not file because filing is the runner's step.
- A PROCESS-WIDE `conftest.py` SCRUB OF `CI`/`AW_NONINTERACTIVE`. Refused for a reason beyond scope: it would hide every future instance of this bug class, and `tests/test_interactivity_resolver.py` legitimately drives those variables as INPUTS, so a global scrub would fight its own matrix.
- WIDENING THE FENCE TO OTHER PROMPT SITES. `cli._confirm` and the hardened sites already route through the resolver; nothing measured here shows a gap, and changing them on suspicion is how a plan acquires unreviewed scope.
- EDITING ANY `.spec.md`. None is required: no spec states the behavior this plan changes. `docs/cli-output-contract.md` publishes the ladder, and the ladder is NOT being changed, so the published contract stays true. This is why no `.spec.md` appears in `- Scope-Paths:`.

## Scope check

- Over-scope: none. Each of the four declared paths is touched by a named E-item: `git_commit_helper.py` by E-02 and E-04, `term.py` by E-03, `tests/test_git_commit_helper.py` by E-01 and E-05, `tests/test_stdin_interactive.py` by E-05.
- Under-scope: the four red tests in `tests/test_completion.py` and `tests/test_runner_shared.py` (F-09) remain red under an ambient `CI` after this plan, so `main`'s CI is not fully green on this plan alone. That is stated rather than papered over, and the reason those files are excluded is in Deferred. V-05 must therefore report the `CI=true` result for this plan's two files specifically, and must NOT claim a green whole-suite run under `CI=true`.

## Required tests / validation

- `python3 -m pytest` BARE, for the unchanged baseline, pasting the summary line.
- `CI=true python3 -m pytest tests/test_git_commit_helper.py tests/test_stdin_interactive.py` to prove this plan's two files survive an ambient CI signal, pasting the summary line.
- `python3 -m pytest tests/test_interactivity_resolver.py` to prove the single-originating-definition AST guard and the rung matrix still pass after E-04 (F-08).
- A demonstration that E-01's test is a REAL regression test and not a tautology: show it FAILING against the pre-`64c04288` predicate (temporarily restoring the old two-line body, or equivalently by monkeypatching `_is_interactive` to the old stdin-only behavior) and PASSING at HEAD. A test that cannot fail pins nothing.
- `aw ipd lint --phase pre-transition` on this plan, conforming.

## Spec / documentation sync

NO `.spec.md` FILE IS EDITED, and that is a checked judgement rather than an omission. No spec states `offer_commit`'s interactivity contract. `docs/cli-output-contract.md` publishes the interactivity precedence ladder normatively, and this plan deliberately does NOT change that ladder (E-04 is local to one caller's explicit argument), so the published contract remains accurate and needs no amendment. The two documentation edits this plan does make (E-02, E-03) are DOCSTRINGS in files already declared in `- Scope-Paths:`, correcting text that describes behavior commit `64c04288` already changed. If a reviewer judges that the argument-beats-environment distinction E-04 introduces is itself contract-worthy and belongs in `docs/cli-output-contract.md`, that file must be added to `- Scope-Paths:` BEFORE execution, since the runners announce declared spec and doc edits at run start.

## Open questions

### OQ-01: Should the backlog item be closed as fixed-elsewhere, or does the residual work justify keeping it open?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: RECORDED, NOT DECIDED HERE, because it is a disposition call and this plan is authoring-only. The reported wedge is fixed (F-01, F-02) and the honest reading is that `41mtsm` was closed by `da9n1s` incidentally. This plan nonetheless carries real work under the item's `- Blocks-Release: next` gate: the missing behavioral pin (F-03), two misleading docstrings (F-07), and a live CI-red defect in the same predicate (F-04, F-05). The plan therefore inherits the gate and the `From-Backlog` link, which is the mechanism that lets the item reach `graduated` without dropping the gate. No answer is needed before execution: every E-item stands on its own measured evidence regardless of how the item is ultimately dispositioned.

### OQ-02: Should the `interactive=` parameter's argument-beats-environment behavior become a published contract in `docs/cli-output-contract.md`?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DELIBERATELY LEFT TO THE REVIEWER because publishing it would extend a normative document this plan does not declare. The plan's position: it should NOT be published yet. The ladder in that document governs the USER-FACING flag pair, and `interactive=` is an internal keyword argument with one non-test caller passing a literal (`runner_shared`, `interactive=False`); documenting an internal parameter beside two operator flags invites a reader to conclude the flags behave the same way, which is exactly the confusion F-06 exists to prevent. E-04 therefore records the distinction in a CODE COMMENT at the site that needs it. If the reviewer disagrees, add `docs/cli-output-contract.md` to `- Scope-Paths:` before execution rather than at execution time.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new test's SOURCE, showing the `pty.openpty` call, the piped stdout, the `CI`/`AW_NONINTERACTIVE` scrub of the child environment, the bounded timeout, and BOTH assertions (returned status is `STATUS_SKIPPED`; the captured pipe bytes do NOT contain `Commit these path-scoped changes?`). Then paste the test PASSING at HEAD, and separately paste it FAILING against the pre-`64c04288` stdin-only predicate, naming exactly how the old behavior was reintroduced for that run. The failing run is the load-bearing half: without it this item cannot distinguish a real pin from a test that would pass on the wedging code too, which is precisely the defect F-03 records about the existing mock-based coverage.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `interactive:` parameter block from `offer_commit`'s docstring BEFORE and AFTER, and paste the output of a search for `sys.stdin.isatty()` in `agent_workflows/git_commit_helper.py` showing no remaining occurrence that describes this parameter's behavior. State whether the corrected text names `term.is_interactive` and mentions both the output-stream requirement and the `AW_NONINTERACTIVE`/`CI` rung, since a correction that merely deletes the wrong sentence leaves the reader with no contract at all.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the honest-limit paragraph from `term.stdin_is_interactive` BEFORE and AFTER. Show that the AFTER text names `term.is_interactive` and that the three hardened sites (`ipd_lifecycle.run_finalize`, `runner_stop.interrupt_menu_is_safe`, `artifact_adopt.leak_gate_is_interactive`) are still named, since deleting them would destroy the precedent that explains why the stronger fence exists. Confirm no behavior changed by pasting a passing `python3 -m pytest tests/test_stdin_interactive.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new `_is_interactive` body, then paste an executed four-cell table of `_is_interactive(True)`, `_is_interactive(False)`, and `_is_interactive(None)` under (a) `CI=1` and (b) `CI`/`AW_NONINTERACTIVE` unset, with the actual returned values. The table must show explicit `True` surviving `CI=1` (the fix), explicit `False` unchanged, and `None` still answering False when stdout is not a TTY (proving the fence E-01 pins was NOT weakened - this is the direction that matters, because a careless fix here re-opens the original wedge). Then paste `python3 -m pytest tests/test_interactivity_resolver.py` PASSING, and quote the single-originating-definition result specifically, since F-08 records that the AST guard's `_is_pure_delegation` predicate may reject a body with an added early-return statement. Also paste the `term.is_interactive` source to show its ladder is BYTE-FOR-BYTE unchanged, and state that the `bmf32u` OQ-03 ruling was not reversed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `CI=true python3 -m pytest tests/test_git_commit_helper.py tests/test_stdin_interactive.py` with its summary line, and the same two files with `CI` unset, both passing. Paste the new assertion's source showing `_is_interactive(True)` is asserted True with `CI=1` set. Paste the scrub mechanism and confirm it is per-test (`monkeypatch.delenv`) and NOT in `conftest.py`. Paste a bare `python3 -m pytest` summary line for the whole suite. Finally, state EXPLICITLY that four tests in `tests/test_completion.py` and `tests/test_runner_shared.py` remain red under `CI=true` (F-09) and are out of scope: claiming a fully green suite under `CI=true` would be false, and V-05 is the item where that temptation lands.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution; nothing here approves it.

THE EXECUTOR MUST RE-MEASURE BEFORE IMPLEMENTING. Every finding above was taken at HEAD `b78c055c`, and this plan exists because the backlog item's own measurement went stale in 35 hours. Specifically: re-run the F-01 probe, and re-run `CI=true python3 -m pytest` to confirm F-04/F-05 are still live. If the `CI` failures are already fixed on `main` by then, E-04 and E-05 may be unnecessary; report that rather than manufacturing a change, and do not mark a V-item pass on evidence collected before the re-measurement.

Execution contract: commit ONLY the paths this plan declares, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push. Paste ACTUAL runner output for every test claim. On completion, run `aw ipd lint --phase pre-transition`, confirm it reports conforming, verify every `V-*` item carries concrete pasted evidence, and only then move this plan to `.aw/records/plans/executed/` through the tooled transition.

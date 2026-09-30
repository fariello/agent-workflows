# IPD: Prove the git_commit_helper commit-prompt fence holds, and stop the CI/AW_NONINTERACTIVE rung from overriding an explicit interactive=True

- Date: 2026-09-29
- Kind: child
- Concern: Backlog `41mtsm` reports that `git_commit_helper._is_interactive` keys on stdin alone, so a driver-spawned `aw` verb with stdin inherited and stdout piped prints `Commit these path-scoped changes? [Y/n]` into the pipe and blocks on `input()`. The ROOT CAUSE IS ALREADY FIXED IN CODE by commit `64c04288` (plan `da9n1s`), which landed AFTER the item was filed, so this plan does not re-fix it: it pins the fixed behavior with the behavioral regression test the item's measurement describes and that no test currently performs, corrects the two stale docstrings that still publish the superseded `sys.stdin.isatty()` contract, and fixes a SECOND defect measured while verifying the first, in which the forced-non-interactive rung swallows an EXPLICIT `interactive=True` argument (main is red on this today). CORRECTED AT REVIEW: the ambient-`CI` failure count is EIGHT, not six, and two of them sit in `tests/test_interactivity_resolver.py`, a file this plan does not declare and whose assertions bear on the ladder's own contract (F-10, E-07, OQ-03); also added at review, `docs/cli-output-contract.md` publishes the ladder in `override=` terms and so MUST be amended alongside this change rather than left alone (F-11, E-06).
- Scope: `agent_workflows/git_commit_helper.py` (the `interactive=` docstring line and the `_is_interactive` argument-vs-environment ordering), `agent_workflows/term.py` (the `stdin_is_interactive` advice paragraph that names a superseded remedy), `tests/test_git_commit_helper.py` plus `tests/test_stdin_interactive.py` (the behavioral pty-plus-pipe regression test and the ambient-`CI` isolation), and `docs/cli-output-contract.md` (ADDED AT REVIEW: its ladder table is worded in `override=` terms and E-04 makes one of its rows false, so the doc is amended in the same change rather than left to drift). NOT in scope: changing the maintainer-ruled asymmetric precedence ladder itself, editing any `.spec.md`, or repairing the seven unrelated ambient-`CI` failures in `tests/test_completion.py`, `tests/test_runner_shared.py` and `tests/test_interactivity_resolver.py` (see Deferred; the last two are recorded by E-07 and raised as OQ-03 because they bear on the ladder's contract rather than being mere `CI` noise).
- Scope-Paths: agent_workflows/git_commit_helper.py, agent_workflows/term.py, tests/test_git_commit_helper.py, tests/test_stdin_interactive.py, docs/cli-output-contract.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 41mtsm
- Blocks-Release: next
- Set: 41mtsm
- Order: 1
- Highest E allocated: 07
- Author: agent aw oc run
- Id: 0brmmy
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (aw set): status set to reviewed

- 2026-09-29 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901..PR-908, all FIXED. AN UNUSUALLY WELL EVIDENCED PLAN WHOSE CENTRAL JUDGEMENT IS RIGHT, and I verified its refusal to re-fix rather than accepting it: I RAN THE F-01 PROBE (child stdin on a real `pty.openpty` pty, stdout piped, `CI`/`AW_NONINTERACTIVE` scrubbed) and got `STDIN_ISATTY True`, `STDOUT_ISATTY False`, `OUTCOME skipped | skipped: non-interactive; pass --commit to commit these changes`, exit 0, prompt string absent from the pipe. F-02 verifies by `git show 64c04288`, whose pre-image is exactly the shape E-04 restores; F-03, F-04, F-06, F-07 verify, and F-04 reproduces exactly (`CI=1` -> False, unset -> True). TWO HIGH FINDINGS, both from the same blind spot - counting without reading the whole list, and asserting a document stayed true without opening it. PR-901: the ambient-`CI` failure count is EIGHT, not six, and the two unnamed ones are in `tests/test_interactivity_resolver.py`, where they assert `term.is_interactive(..., override=True)` is True; that is E-04's own premise one layer lower, so the repository holds the asymmetric ladder AND a suite encoding the opposite, a tension neither this plan nor I may resolve (one reading rewrites undeclared tests, the other reverses the `bmf32u` ruling). Recorded as E-07, raised as OQ-03, non-blocking. PR-902: the plan's "the published contract stays true" is FALSE - `docs/cli-output-contract.md` words its ladder in `override=` terms, so E-04 makes a published sentence untrue; OQ-02 is RESOLVED as yes, the doc is now declared, and E-06 makes the minimum accuracy-restoring edit. THREE FINDINGS MAKE THE PLAN'S CASE STRONGER THAN IT CLAIMED, recorded because correction runs both ways: F-08's feared AST-guard constraint DOES NOT EXIST because `_is_pure_delegation` is dead code, proven by applying E-04's shape and getting `20 passed` (PR-903); E-04 cannot change any shipped caller today because `assume_yes` short-circuits first and the one `interactive=`-passing caller also passes `assume_yes=True` (PR-905); and E-04 ALONE clears the red test without E-05's scrub, measured `8 failed` -> `7 failed` (PR-904). Also corrected F-09's three to four (PR-907) and fixed six pre-existing `check.ipd-uncarried-obligation` violations with a specific reason each (PR-906, now CLEAN), and reordered the plan's oldest-first `## Workflow history` to the repository's newest-first contract, text preserved verbatim (PR-908). Five decisions recorded in the typed review record, all `Reversible: yes`. Structural preflight `conforming` at `author` and `review-finalize`.
- 2026-09-29 to-review (agent aw oc run): authored from backlog `41mtsm` after re-measuring the reported reproduction at HEAD `b78c055c`. The reported wedge DOES NOT REPRODUCE (the fence now holds); a second, previously unrecorded defect in the same predicate DOES, and turns `main`'s CI red. Plan rewritten around what is actually true rather than around the item's now-stale premise.
- 2026-09-29 draft (agent aw oc run): created.

## Goal

Close backlog `41mtsm` honestly. Its reported wedge no longer reproduces because plan `da9n1s` fixed the predicate a day after the item was filed, so the remaining real work is (a) to PIN the fixed behavior with a behavioral test that performs the item's own pty-plus-pipe measurement, since nothing in the suite does and the fence is therefore one careless edit from regressing silently; (b) to correct two docstrings that still publish the superseded stdin-only contract and steer readers to a remedy that is no longer the right one; and (c) to fix the defect found while verifying (a), in which `_is_interactive`'s delegation lets `CI`/`AW_NONINTERACTIVE` override an EXPLICIT `interactive=True` argument, which is both wrong on its own terms and currently red on `main`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the fence that is already correct

- [x] E-01 Add a BEHAVIORAL regression test to `tests/test_git_commit_helper.py` that performs the backlog item's own measurement: spawn a child process with stdin on a REAL pty (`pty.openpty`) and stdout on a PIPE, have it call `git_commit_helper.offer_commit` on a throwaway repo with no `assume_yes`, and assert the call RETURNS `STATUS_SKIPPED` within a bounded timeout rather than emitting the `[Y/n]` prompt text into the pipe. Assert on BOTH observable outcomes: the returned status, and the absence of `Commit these path-scoped changes?` from the captured pipe bytes. Scrub `CI` and `AW_NONINTERACTIVE` from the child environment, or the test passes for the wrong reason (the env rung, not the output-stream rung). Mark it `skipif` on `win32`, where `pty` does not exist.
  - Depends on: none
  - Expected outcome: a test that FAILS against the pre-`64c04288` predicate and PASSES at HEAD, so the fence is pinned by behavior rather than by a mock asserting a delegation happened.
  - Execution state: performed

### Task group 2: correct the two docstrings that publish the superseded contract

- [x] E-02 Correct the `interactive:` parameter line in `git_commit_helper.offer_commit`'s docstring, which still reads ``None`` -> ``sys.stdin.isatty()``. That is the exact contract this item was filed against and it is no longer what the code does: `None` now reaches `term.is_interactive`, which requires stdin AND the output stream to be a TTY and honors `AW_NONINTERACTIVE`/`CI`. State the real contract and name the resolver, so a reader cannot conclude from the docstring that the reported bug is still live.
  - Depends on: none
  - Expected outcome: the parameter line describes the shipped four-rung resolver; no occurrence of `sys.stdin.isatty()` remains as a description of this parameter's behavior.
  - Execution state: performed

- [x] E-03 Correct the "honest limit" paragraph in `term.stdin_is_interactive`'s docstring, which tells a caller about to block on input to "use `artifact_adopt.leak_gate_is_interactive`". That advice is now misdirection: `leak_gate_is_interactive` is itself a two-line delegation to `term.is_interactive`, so the paragraph routes readers through an indirection instead of to the originating definition in the same module. Point at `term.is_interactive` directly, and keep the paragraph's still-true warning that `stdin_is_interactive` answers the narrower question. Do NOT delete the list of hardened sites; it is accurate history and explains why the stronger fence exists.
  - Depends on: none
  - Expected outcome: the paragraph names `term.is_interactive` as the predicate to use, with the three hardened sites preserved as the precedent they are.
  - Execution state: performed

### Task group 3: stop the env rung swallowing an explicit argument

- [x] E-04 Fix `git_commit_helper._is_interactive` so an EXPLICIT `interactive=` argument is honored rather than being overridden by `CI`/`AW_NONINTERACTIVE`. Today it forwards the caller's value as `override=`, and `term.is_interactive`'s ladder places the forced-non-interactive rung ABOVE a positive override, so `_is_interactive(True)` answers False whenever `CI` is set. Return the caller's explicit boolean directly when it is not `None`, and delegate to `term.is_interactive()` only for the `None` case. DO NOT CHANGE `term.is_interactive`'s LADDER: its asymmetry is a maintainer ruling (plan `bmf32u` OQ-03, Gabriele Fariello, 2026-09-28, Option A) protecting a signal-handler prompt with no timeout, and this fix is deliberately local to the one caller that has a direct in-process argument rather than a user-facing flag. Record in a comment WHY the two differ: `--interactive` is an operator's ambient wish that CI must be allowed to veto, whereas `interactive=False`/`True` here is a programmatic caller's statement about a channel it already knows, and `runner_shared` passes `interactive=False` for exactly that reason.
  - Depends on: E-01
  - Expected outcome: `_is_interactive(True)` is True and `_is_interactive(False)` is False regardless of `CI`/`AW_NONINTERACTIVE`; `_is_interactive(None)` still reaches the resolver and still honors every rung.
  - Execution state: performed

- [x] E-05 Make the tests this defect turns red pass under an ambient `CI` by scrubbing `CI`/`AW_NONINTERACTIVE` in the two suites this plan owns (`tests/test_git_commit_helper.py`, `tests/test_stdin_interactive.py`), and assert the E-04 property directly rather than only implicitly: add a test that `_is_interactive(True)` stays True with `CI=1` set and `_is_interactive(False)` stays False with both unset. Scrub per-test with `monkeypatch.delenv`, NOT process-wide in `conftest.py`: a global scrub would mask the same class of defect in every other suite, and `tests/test_interactivity_resolver.py` deliberately drives these variables as inputs.
  TWO CORRECTIONS FROM REVIEW, both measured. FIRST, "the six tests" IS WRONG: the count at review HEAD is EIGHT, and the two the plan never named live in `tests/test_interactivity_resolver.py`, which this plan does not declare (F-10). Do NOT silently fix those two here. Re-measure the count at execution HEAD and report it rather than repeating any number from this plan. SECOND, THIS ITEM IS NOT WHAT FIXES THE `git_commit_helper` FAILURE: E-04 alone fixes it, measured (`8 failed` -> `7 failed`, with `test_interactive_commit_prompts_and_responses` gone from the FAILED list, no test edits applied) (F-14). So this item's real deliverables are the NEW direct assertion and whatever scrub the two declared files still need; if a scrub turns out to be unnecessary in one of them, say so instead of adding a no-op `delenv` to look busy.
  - Depends on: E-04
  - Expected outcome: `tests/test_git_commit_helper.py` and `tests/test_stdin_interactive.py` pass both with `CI` unset and with `CI=true` exported; the new assertion pins the argument-beats-environment property so a future revert of E-04 fails a test instead of only CI; and the report states the re-measured failing count with the two resolver tests identified as out of scope.
  - Execution state: performed

### Task group 4: reconcile the published contract with the change

- [x] E-06 AMEND `docs/cli-output-contract.md`'s interactivity ladder so it stops publishing a statement E-04 makes untrue, locating the table by the content string `--no-interactive  >  AW_NONINTERACTIVE / CI  >  --interactive`. ADDED AT REVIEW. The document's rungs 1 and 3 are written in `override=` terms ("`--no-interactive` (or `override=False`)", "`--interactive` (or `override=True`) forces interactive mode on when not in a forced non-interactive environment"), so after E-04 a reader following that document would predict `_is_interactive(True)` is False under `CI` when it is True (F-11). DO NOT CHANGE THE LADDER ITSELF and do not touch `term.is_interactive`: the amendment is to state that the ladder governs `term.is_interactive`'s `override=` (the resolver behind the `--interactive`/`--no-interactive` flag pair), and to add ONE short row or note recording that a module-local predicate holding a DIRECT programmatic argument may honor it ahead of the environment rung, naming `git_commit_helper._is_interactive` as the instance and the reason (a caller that already knows its channel is not an operator's ambient wish). KEEP THE FAIL-SAFE INVARIANT SENTENCE INTACT. This is the smallest edit that leaves the document true; a larger rewrite of the ladder would touch the `bmf32u` ruling and is refused.
  - Depends on: E-04
  - Expected outcome: `docs/cli-output-contract.md` no longer asserts that `override=True` is beaten by the env rung in ALL cases without qualification, names the one module-local exception with its reason, leaves the five-rung ladder and the fail-safe invariant otherwise unchanged, and so remains accurate after E-04.
  - Execution state: performed

- [x] E-07 RECONCILE THE TWO `tests/test_interactivity_resolver.py` FAILURES WITH THIS PLAN'S POSITION, WITHOUT FIXING THEM HERE, and record the finding. ADDED AT REVIEW. `InteractivityResolverOverrideTests::test_explicit_override_short_circuits_both_ways` and `::test_explicit_override_beats_process_wide_override` FAIL under ambient `CI` because each asserts `term.is_interactive(..., override=True)` is True, which the env rung overrides (F-10). THIS IS EVIDENCE WORTH STATING PLAINLY, because it cuts in this plan's favor and the plan never noticed it: the repository's own resolver suite already encodes "an explicit positive override wins", i.e. E-04's premise one layer lower, which means the asymmetric ladder and the resolver's own tests are in TENSION with each other independently of anything this plan does. DELIVERABLE: state in this plan, at finalize, (a) that both tests fail under `CI` at execution HEAD (re-measured, not quoted), (b) that they are NOT in `- Scope-Paths:` and are deliberately untouched, and (c) which of the two readings a maintainer must eventually choose - either those tests encode a stale expectation and should scrub `CI`, or the ladder's rung-2-over-rung-3 asymmetry is narrower than `bmf32u` recorded. Do NOT choose between those readings and do NOT edit that file: choosing is the maintainer's call and is raised as OQ-03.
  - Depends on: none
  - Expected outcome: a recorded, re-measured statement of the two resolver failures, an explicit note that they are out of scope and untouched, and the two candidate readings named without the plan picking one.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE INTERACTIVITY DECISION HAS EXACTLY ONE ORIGINATING DEFINITION, `term.is_interactive`, and `tests/test_interactivity_resolver.py` enforces that with an AST walk over every `*.py` in the package (`SingleOriginatingDefinitionTests.test_exactly_one_originating_is_interactive_in_package`). It maintains an explicit `SANCTIONED_DELEGATIONS` allowlist that names `("git_commit_helper.py", "_is_interactive")`. CORRECTED AT REVIEW: this convention ALSO claimed a `_is_pure_delegation` predicate constrains how E-04 may be written, and that constraint DOES NOT EXIST - the predicate is defined and never called (dead code), and the only consumer of the allowlist just walks for any call to `is_interactive`/`is_forced_noninteractive` in the function body. Review applied E-04's exact early-return shape and ran the file: `20 passed` (F-12). The pre-`64c04288` implementation was precisely that shape, which is a second reason to expect it to pass. V-04 still reports the file's real result; it no longer chases a nonexistent guard.
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
| F-09 | OTHER TESTS ARE RED UNDER `CI` FOR A DIFFERENT REASON AND ARE NOT THIS ITEM'S. `tests/test_completion.py` (4 tests, CORRECTED AT REVIEW from 3) and `tests/test_runner_shared.py::IntegrationDeferralLadderTests::test_interactive_ask_behavior_and_prompt_predicate` also fail under `CI=true`, but they route through `cli`-owned completion prompts and `runner_shared`, neither of which this plan's `Scope-Paths` names. They share the same ROOT CLASS (a suite that assumes no ambient `CI`), so they want one deliberate decision about suite-wide isolation rather than scattered patches. | Re-measured at review HEAD `4e7dd52c`: `CI=true python3 -m pytest` reports `8 failed, 3238 passed, 2 skipped`; the `test_completion.py` failures are `SetupCompletionPromptTests::test_every_input_combination_reaches_its_declared_outcome`, `RcWriteOfferTests::test_rc_write_offer_consenting`, `RcWriteOfferTests::test_rc_write_offer_non_consenting_and_absent`, `RcWriteOfferTests::test_uninstall_rc_stanza_offer` |
| F-10 | ADDED AT REVIEW, AND IT IS THE MOST IMPORTANT CORRECTION HERE: THE FAILING COUNT IS EIGHT, NOT SIX, AND THE TWO THE PLAN NEVER NAMES ARE IN `tests/test_interactivity_resolver.py` - A FILE THIS PLAN DOES NOT DECLARE AND WHOSE FAILING ASSERTIONS PIN THE EXACT BEHAVIOR E-04 RELIES ON. `InteractivityResolverOverrideTests::test_explicit_override_short_circuits_both_ways` asserts `term.is_interactive(stdin=non_tty, output_stream=non_tty, override=True)` is True, and `test_explicit_override_beats_process_wide_override` asserts the same for an explicit True over a process-wide False. Both fail under ambient `CI` because the env rung outranks a positive override. So the repository's OWN resolver suite already encodes "an explicit positive override wins", which is E-04's premise applied one layer lower. | Re-measured at review HEAD `4e7dd52c`: `CI=true python3 -m pytest` names both tests in its `FAILED` list; their assertions read directly in `tests/test_interactivity_resolver.py` |
| F-11 | ADDED AT REVIEW: `docs/cli-output-contract.md` PUBLISHES THE VERY BEHAVIOR E-04 CHANGES, IN `override=` TERMS, so the plan's claim that "the published contract stays true" is FALSE as written. Its ladder table says rung 1 is "`--no-interactive` (or `override=False`)" and rung 3 is "`--interactive` (or `override=True`) forces interactive mode on WHEN NOT IN A FORCED NON-INTERACTIVE ENVIRONMENT". That is a normative statement about `override=`, not only about the flags, and E-04 makes `_is_interactive`'s explicit argument stop obeying it. The plan's own Deferred section asserts the opposite ("the ladder is NOT being changed, so the published contract stays true"), and OQ-02 treats publication as optional polish. | `docs/cli-output-contract.md`, the interactivity ladder table rows 1-3, quoted above |
| F-12 | ADDED AT REVIEW: F-08's STATED CONSTRAINT ON HOW E-04 MAY BE WRITTEN DOES NOT EXIST, because `_is_pure_delegation` IS DEAD CODE - defined and never called. F-08 says "V-04 must PASS that guard rather than assume it" and warns an early-return "adds a second statement", implying a real risk. There is none: the only consumer of `SANCTIONED_DELEGATIONS` is `test_sanctioned_delegations_are_closed_and_reach_term_resolver`, which merely walks for ANY call to `is_interactive`/`is_forced_noninteractive` inside the function. PROVEN BY EXECUTION, not by reading: I applied E-04's exact early-return shape and ran the file - 20 passed. | `grep -n '_is_pure_delegation' tests/test_interactivity_resolver.py` returns only its docstring mention (line 344) and its definition (line 363), no call site; with E-04's shape applied, `python3 -m pytest tests/test_interactivity_resolver.py -o addopts=""` reported `20 passed` |
| F-13 | ADDED AT REVIEW: E-04 IS SAFER THAN THE PLAN'S OWN RISK FRAMING SUGGESTS, and the reason is worth recording so a reviewer does not over-weight it. `offer_commit` checks `if assume_yes: proceed = True` BEFORE reaching `elif _is_interactive(interactive)`, and the ONLY non-test `offer_commit` caller passing `interactive=` (in `runner_shared`) also passes `assume_yes=True`, so that call never reaches the predicate at all. The `cli` self-commit caller passes no `interactive=` and so keeps the `None` path unchanged. E-04 therefore cannot change any shipped caller's behavior today; its effect is on the predicate's contract and on tests. | The `if assume_yes:` / `elif _is_interactive(interactive):` branch order in `offer_commit`; the single `interactive=False` + `assume_yes=True` `offer_commit` call in `runner_shared`; the `cli` self-commit call site passing no `interactive=` |
| F-14 | ADDED AT REVIEW: E-04 ALONE FIXES THE `git_commit_helper` FAILURE, WITHOUT E-05's SCRUB, which matters because the plan sequences E-05 as the item that makes the red tests pass. MEASURED: with only E-04's early return applied and no test edits, `CI=true python3 -m pytest` went from `8 failed` to `7 failed` and `test_interactive_commit_prompts_and_responses` no longer appears in the `FAILED` list. | `CI=true python3 -m pytest` before (`8 failed, 3238 passed`) and after applying E-04's shape alone (`7 failed, 3239 passed`), with the `FAILED` lists compared |

## Proposed changes (ordered, validatable)

1. Add the pty-plus-pipe behavioral regression test for `offer_commit`'s fence, with the child environment scrubbed of `CI`/`AW_NONINTERACTIVE` and a bounded timeout, asserting both the returned status and the absence of prompt text in the pipe (E-01).
2. Correct `offer_commit`'s `interactive:` docstring line to describe the shipped resolver instead of `sys.stdin.isatty()` (E-02).
3. Correct `term.stdin_is_interactive`'s honest-limit paragraph to point at `term.is_interactive` directly, preserving the hardened-site precedent (E-03).
4. Make `_is_interactive` honor an explicit boolean argument ahead of the environment rung, leaving `term.is_interactive`'s ruled ladder untouched and recording why the two differ (E-04).
5. Scrub ambient `CI`/`AW_NONINTERACTIVE` per-test in this plan's two declared test files and assert the argument-beats-environment property directly (E-05).
6. Amend `docs/cli-output-contract.md` so its `override=`-worded ladder no longer publishes a statement E-04 makes false, naming the one module-local exception (E-06, added at review from F-11 and OQ-02).
7. Record the two out-of-scope `tests/test_interactivity_resolver.py` failures and the two candidate readings they force, without fixing them (E-07, added at review from F-10; the decision is OQ-03).

ORDERING: E-01, E-02, E-03 and E-07 are mutually independent. E-04 gates E-05 and E-06, because both describe or assert its post-fix behavior. Note E-04 does NOT depend on E-01: review measured that E-04 alone clears the `git_commit_helper` failure (F-14), so the pin and the fix are separable; E-04's declared dependency on E-01 is kept deliberately, so the fence is pinned BEFORE the predicate is touched.

## Deferred / out of scope (with reason)

- CHANGING `term.is_interactive`'s PRECEDENCE LADDER. Deliberately refused. Its asymmetry is a maintainer ruling (plan `bmf32u` OQ-03, 2026-09-28, Option A) grounded in a measured wedge, and it is published as normative in `docs/cli-output-contract.md`. This plan fixes ONE caller that holds a direct programmatic argument, and states in a comment why that is not the same thing as a flag. A reviewer who disagrees should say so before execution rather than have the ladder edited mid-run. NOTE ADDED AT REVIEW: whether this refusal is even the right long-term call is now an OPEN maintainer question, because the resolver's own test suite asserts the opposite for `override=True` (F-10, OQ-03). The refusal stands for THIS plan either way, since a local fix is correct under both readings.
  - Carrier-Declined: The obligation, if there is one, is carried by OQ-03 rather than dropped: that question names both candidate readings and E-07 writes the re-measured evidence into this plan's record at finalize. A carrier item cannot be cited because the work does not exist until the maintainer chooses a reading, and filing one would presuppose that choice. If the maintainer picks reading (b), that decision is the trigger to file work against `term.is_interactive`.
- REPAIRING THE OTHER `CI=true` FAILURES. CORRECTED AT REVIEW: there are SEVEN, not four - five in `tests/test_completion.py` (4) and `tests/test_runner_shared.py` (1) per F-09, plus TWO in `tests/test_interactivity_resolver.py` per F-10. They are the same root CLASS but sit behind `cli`, `runner_shared` and the resolver suite, none of which this plan's `Scope-Paths` names, and fixing them properly means deciding whether the suite wants one shared isolation mechanism. Doing it here would either take undeclared out-of-scope edits or install a `conftest.py` scrub that masks this very defect class everywhere else. The two resolver ones are NOT merely ambient-`CI` noise and must not be swept up as such: their assertions bear on the ladder's own contract, which is why they are separated into E-07 and OQ-03 rather than lumped here.
  - Carrier-Declined: No carrier is cited because the remedy is not yet decided and the deciding question is recorded: for the five F-09 failures the open choice is whether the suite adopts ONE shared isolation mechanism or per-file scrubs, which is a test-architecture judgement nobody has made; for the two F-10 failures the choice is OQ-03's. Both are preserved with their measurements in F-09, F-10, E-07 and OQ-03, and V-05 is required to re-measure and re-state the full out-of-scope list at finalize, so the population cannot silently vanish when this plan closes. Filing an item now would presuppose the isolation decision.
- A PROCESS-WIDE `conftest.py` SCRUB OF `CI`/`AW_NONINTERACTIVE`. Refused for a reason beyond scope: it would hide every future instance of this bug class, and `tests/test_interactivity_resolver.py` legitimately drives those variables as INPUTS (verified at review: its rung matrix passes `{"CI": "1"}`, `{"CI": "false"}`, `{"AW_NONINTERACTIVE": "no"}` and siblings as explicit `environ=` fixtures), so a global scrub would fight its own matrix.
  - Carrier-Declined: This is a WON'T-FIX on correctness grounds, not a deferral: a process-wide scrub is the WRONG mechanism and its current absence is the correct terminal state, so there is nothing for a carrier to carry onward. An item proposing it could only be closed unfixed.
- WIDENING THE FENCE TO OTHER PROMPT SITES. `cli._confirm` and the hardened sites already route through the resolver; nothing measured here shows a gap, and changing them on suspicion is how a plan acquires unreviewed scope.
  - Carrier-Declined: No carrier because no defect was measured here: this row records the ABSENCE of a found problem, so there is no obligation to preserve. Acting on suspicion is what it exists to refuse.
- EDITING ANY `.spec.md`. None is required: no spec states the behavior this plan changes. CORRECTED AT REVIEW, because the second half of this row was FALSE: it read "the ladder is NOT being changed, so the published contract stays true", but `docs/cli-output-contract.md` publishes the ladder in `override=` TERMS ("`--interactive` (or `override=True`) forces interactive mode on when not in a forced non-interactive environment"), which is exactly the sentence E-04 makes untrue for `git_commit_helper._is_interactive`'s argument (F-11). The `.spec.md` conclusion still stands and is unaffected; the DOC conclusion did not, and `docs/cli-output-contract.md` is now DECLARED in `- Scope-Paths:` with E-06 owning the amendment.
  - Carrier-Declined: Nothing outstanding to carry: no spec governs this behavior, so there is no deferred spec work, and the documentation half is no longer deferred at all (E-06 performs it in this plan).

## Scope check

- Over-scope: none. Each of the five declared paths is touched by a named E-item: `git_commit_helper.py` by E-02 and E-04, `term.py` by E-03, `tests/test_git_commit_helper.py` by E-01 and E-05, `tests/test_stdin_interactive.py` by E-05, and `docs/cli-output-contract.md` by E-06 (added at review; declared rather than left to a `--scope-reason`, since the runners announce declared doc edits at run start). E-07's deliverable is prose in this plan and adds no path.
- Under-scope: SEVEN tests remain red under an ambient `CI` after this plan, corrected at review from "four". Five are F-09's (four in `tests/test_completion.py`, one in `tests/test_runner_shared.py`), and TWO are in `tests/test_interactivity_resolver.py` (F-10), which the plan had not noticed at all; E-07 records them and OQ-03 raises the decision. So `main`'s CI is NOT fully green on this plan alone, which is stated rather than papered over. V-05 must report the re-measured whole-suite `CI=true` figure and name all seven as out of scope, and must NOT claim a green whole-suite run under `CI=true`.

## Required tests / validation

- `python3 -m pytest` BARE, for the unchanged baseline, pasting the summary line.
- `CI=true python3 -m pytest tests/test_git_commit_helper.py tests/test_stdin_interactive.py` to prove this plan's two files survive an ambient CI signal, pasting the summary line.
- `python3 -m pytest tests/test_interactivity_resolver.py` WITH `CI` UNSET, to prove the single-originating-definition AST guard and the rung matrix still pass after E-04. Review already ran this against E-04's exact shape and got `20 passed`, so a failure here is a real signal and not the expected friction F-08 predicted (F-12 records that the `_is_pure_delegation` constraint does not exist). Under `CI=true` this file reports 2 failures that E-04 does not cause and does not fix (F-10); if that run is pasted, its environment must be stated.
- A demonstration that E-01's test is a REAL regression test and not a tautology: show it FAILING against the pre-`64c04288` predicate (temporarily restoring the old two-line body, or equivalently by monkeypatching `_is_interactive` to the old stdin-only behavior) and PASSING at HEAD. A test that cannot fail pins nothing.
- `aw ipd lint --phase pre-transition` on this plan, conforming.

## Spec / documentation sync

NO `.spec.md` FILE IS EDITED, and that is a checked judgement rather than an omission. No spec states `offer_commit`'s interactivity contract. `docs/cli-output-contract.md` publishes the interactivity precedence ladder normatively, and this plan deliberately does NOT change that ladder (E-04 is local to one caller's explicit argument), so the published contract remains accurate and needs no amendment. The two documentation edits this plan does make (E-02, E-03) are DOCSTRINGS in files already declared in `- Scope-Paths:`, correcting text that describes behavior commit `64c04288` already changed. If a reviewer judges that the argument-beats-environment distinction E-04 introduces is itself contract-worthy and belongs in `docs/cli-output-contract.md`, that file must be added to `- Scope-Paths:` BEFORE execution, since the runners announce declared spec and doc edits at run start.

## Open questions

### OQ-01: Should the backlog item be closed as fixed-elsewhere, or does the residual work justify keeping it open?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: No carrier is owed, because the mechanism that prevents silent loss is already in place and is structural rather than clerical: this plan carries `- From-Backlog: 41mtsm` and inherits its `- Blocks-Release: next` gate, which is exactly the handoff the repository's close-legitimacy rule requires, so item `41mtsm` cannot close `done` while dropping its gate regardless of how the disposition question is answered. The question asks only WHICH disposition label the item ends with; no implementation work hangs on it.
- Resolution or deferral rationale: RECORDED, NOT DECIDED HERE, because it is a disposition call and this plan is authoring-only. The reported wedge is fixed (F-01, F-02) and the honest reading is that `41mtsm` was closed by `da9n1s` incidentally. This plan nonetheless carries real work under the item's `- Blocks-Release: next` gate: the missing behavioral pin (F-03), two misleading docstrings (F-07), and a live CI-red defect in the same predicate (F-04, F-05). The plan therefore inherits the gate and the `From-Backlog` link, which is the mechanism that lets the item reach `graduated` without dropping the gate. No answer is needed before execution: every E-item stands on its own measured evidence regardless of how the item is ultimately dispositioned.

### OQ-02: Should the `interactive=` parameter's argument-beats-environment behavior become a published contract in `docs/cli-output-contract.md`?

- Blocking: no
- Status: resolved
- Owner: plan reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW, AND THE ANSWER IS YES - NOT AS POLISH BUT AS A CORRECTION, which is why this is no longer a maintainer question. The plan framed publication as optional ("it should NOT be published yet") on the ground that the document governs the user-facing flag pair while `interactive=` is internal. THAT FRAMING DOES NOT SURVIVE READING THE DOCUMENT: its ladder table is written in `override=` terms, rung 1 as "`--no-interactive` (or `override=False`)" and rung 3 as "`--interactive` (or `override=True`) forces interactive mode on when not in a forced non-interactive environment" (F-11). So the document already makes a normative claim about the override mechanism itself, and after E-04 a reader following it would predict `_is_interactive(True)` is False under `CI` when the measured answer is True. That is not an un-published nicety, it is a published statement becoming false. The plan's own instruction is therefore followed literally: `docs/cli-output-contract.md` IS added to `- Scope-Paths:` before execution, and new E-06 makes the SMALLEST edit that restores accuracy - the ladder and the fail-safe invariant are untouched, and the one module-local exception is named with its reason. The plan's underlying worry (that documenting an internal parameter beside two operator flags invites confusion) is respected rather than dismissed: E-06 is required to state the DISTINCTION, which is the opposite of implying the flags behave the same way.

### OQ-03: Two resolver tests assert that an explicit `override=True` wins, and fail under an ambient `CI`. Is the ladder's rung-2-over-rung-3 asymmetry narrower than `bmf32u` recorded, or are those tests stale?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: This asks the maintainer to DECIDE between two readings of their own 2026-09-28 ruling, and it owes no implementation work until they answer; filing a carrier now would presuppose the answer. The observation cannot vanish silently: it is recorded as finding F-10 with its measurement, and E-07 writes the re-measured statement and both candidate readings into this plan's own record at finalize, so a later reader meets the tension whether or not this question is ever answered.
- Resolution or deferral rationale: RAISED AT REVIEW, NOT DECIDED, because either answer edits something a reviewer has no authority over. MEASURED at review HEAD `4e7dd52c`: `tests/test_interactivity_resolver.py::InteractivityResolverOverrideTests::test_explicit_override_short_circuits_both_ways` and `::test_explicit_override_beats_process_wide_override` both FAIL under `CI=true`, each because it asserts `term.is_interactive(..., override=True)` is True while the env rung returns False. WHY THIS IS NOT MERELY ANOTHER AMBIENT-`CI` TEST BUG: those two assertions are the resolver suite's own statement that an explicit positive override wins, which is E-04's premise one layer lower, so the repository currently holds the asymmetric ladder AND a test suite encoding the opposite for `override=True`. The two readings a maintainer must choose between: (a) the tests encode a pre-ruling expectation and should scrub `CI` like the rest, leaving the ladder as ruled; or (b) the ruling's rung-2-over-rung-3 asymmetry was meant for the FLAG and not for a programmatic `override=`, in which case `term.is_interactive` itself may be narrower than `bmf32u` recorded and E-04's local fix is a symptom rather than the fix. NOT BLOCKING: every E-item in this plan stands under either reading, because E-04 is local to one caller and E-06 documents exactly that locality. Deliberately NOT resolved by the reviewer: (a) rewrites tests this plan does not declare, and (b) would reverse a named maintainer ruling.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the new test's SOURCE, showing the `pty.openpty` call, the piped stdout, the `CI`/`AW_NONINTERACTIVE` scrub of the child environment, the bounded timeout, and BOTH assertions (returned status is `STATUS_SKIPPED`; the captured pipe bytes do NOT contain `Commit these path-scoped changes?`). Then paste the test PASSING at HEAD, and separately paste it FAILING against the pre-`64c04288` stdin-only predicate, naming exactly how the old behavior was reintroduced for that run. The failing run is the load-bearing half: without it this item cannot distinguish a real pin from a test that would pass on the wedging code too, which is precisely the defect F-03 records about the existing mock-based coverage.
  - Observed evidence: PASS. Source of pty test verified, passing at HEAD (0.88s) and failing with TimeoutExpired on pre-64c04288 wedging predicate (10.41s).
    Source of `test_offer_commit_pty_stdin_and_pipe_stdout_skips_without_prompt` in `tests/test_git_commit_helper.py`:
    ```python
    @pytest.mark.skipif(sys.platform == "win32", reason="pty does not exist on win32")
    def test_offer_commit_pty_stdin_and_pipe_stdout_skips_without_prompt(repo: Path):
        """E-01: child with stdin on real pty and stdout on pipe returns skipped without prompting."""
        import pty

        mine = _write(repo, "mine.txt", "mine\n")
        master, slave = pty.openpty()
        env = dict(os.environ)
        env.pop("CI", None)
        env.pop("AW_NONINTERACTIVE", None)

        code = (
            "import sys\n"
            "from pathlib import Path\n"
            "from agent_workflows import git_commit_helper as H\n"
            "out = H.offer_commit(Path(sys.argv[1]), ['mine.txt'], message='probe')\n"
            "print('STATUS:' + out.status)\n"
        )

        proc = subprocess.Popen(
            [sys.executable, "-c", code, str(repo)],
            stdin=slave,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
        )
        os.close(slave)
        slave = -1
        try:
            stdout, stderr = proc.communicate(timeout=10)
        finally:
            os.close(master)
            if proc.poll() is None:
                proc.kill()
                proc.communicate()

        assert proc.returncode == 0, f"child process failed: {stderr}"
        assert "STATUS:skipped" in stdout
        assert "Commit these path-scoped changes?" not in stdout
    ```
    Passing at HEAD:
    ```
    $ python3 -m pytest tests/test_git_commit_helper.py -k test_offer_commit_pty_stdin_and_pipe_stdout_skips_without_prompt -o addopts=""
    collected 25 items / 24 deselected / 1 selected
    tests/test_git_commit_helper.py .                                        [100%]
    ======================= 1 passed, 24 deselected in 0.88s =======================
    ```
    Failing against pre-`64c04288` stdin-only predicate (reintroduced by temporarily setting `_is_interactive` to `return _term.stdin_is_interactive()`):
    ```
    $ python3 -m pytest tests/test_git_commit_helper.py -k test_offer_commit_pty_stdin_and_pipe_stdout_skips_without_prompt -o addopts=""
    collected 25 items / 24 deselected / 1 selected
    tests/test_git_commit_helper.py F                                        [100%]
    =================================== FAILURES ===================================
    _______ test_offer_commit_pty_stdin_and_pipe_stdout_skips_without_prompt _______
    ...
    E   subprocess.TimeoutExpired: Command ... timed out after 10 seconds
    stdout_seq = [b'The following path-scoped changes are ready to commit:\n  mine.txt\nCommit these path-scoped changes? [Y/n] ', b'']
    ====================== 1 failed, 24 deselected in 10.41s =======================
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `interactive:` parameter block from `offer_commit`'s docstring BEFORE and AFTER, and paste the output of a search for `sys.stdin.isatty()` in `agent_workflows/git_commit_helper.py` showing no remaining occurrence that describes this parameter's behavior. State whether the corrected text names `term.is_interactive` and mentions both the output-stream requirement and the `AW_NONINTERACTIVE`/`CI` rung, since a correction that merely deletes the wrong sentence leaves the reader with no contract at all.
  - Observed evidence: PASS. Corrected docstring names term.is_interactive, output-stream TTY requirement, and AW_NONINTERACTIVE/CI rung; sys.stdin.isatty search yields 0 matches.
    `offer_commit` docstring `interactive:` parameter BEFORE:
    ```python
        interactive:
            Explicit interactivity override; ``None`` -> ``sys.stdin.isatty()``.
    ```
    `offer_commit` docstring `interactive:` parameter AFTER:
    ```python
        interactive:
            Explicit interactivity override (used by tests and programmatic callers);
            ``None`` delegates to :func:`agent_workflows.term.is_interactive`, which requires
            both stdin and the output stream to be a TTY and honors ``AW_NONINTERACTIVE``/``CI``.
    ```
    Search for `sys.stdin.isatty()` in `agent_workflows/git_commit_helper.py`:
    ```
    $ grep -n "sys.stdin.isatty" agent_workflows/git_commit_helper.py
    (exit code 1, 0 matches)
    ```
    The corrected text explicitly names `term.is_interactive` and mentions both that stdin and the output stream must be a TTY, as well as honoring the `AW_NONINTERACTIVE`/`CI` environment rung.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the honest-limit paragraph from `term.stdin_is_interactive` BEFORE and AFTER. Show that the AFTER text names `term.is_interactive` and that the three hardened sites (`ipd_lifecycle.run_finalize`, `runner_stop.interrupt_menu_is_safe`, `artifact_adopt.leak_gate_is_interactive`) are still named, since deleting them would destroy the precedent that explains why the stronger fence exists. Confirm no behavior changed by pasting a passing `python3 -m pytest tests/test_stdin_interactive.py`.
  - Observed evidence: PASS. Honest-limit paragraph updated to point to term.is_interactive directly; three hardened sites preserved; tests/test_stdin_interactive.py passes 5/5.
    Honest-limit paragraph in `term.stdin_is_interactive` BEFORE:
    ```python
        The honest limit: this answers "is stdin a real console?" and NOT "can a human answer
        a prompt?". The repository already has three sites that deliberately require more
        (ipd_lifecycle.run_finalize's ttywedge fence, runner_stop.interrupt_menu_is_safe,
        artifact_adopt.leak_gate_is_interactive), all requiring the output stream to be a TTY
        too and honoring AW_NONINTERACTIVE/CI; use artifact_adopt.leak_gate_is_interactive
        when a caller is about to block on input.
    ```
    Honest-limit paragraph in `term.stdin_is_interactive` AFTER:
    ```python
        The honest limit: this answers "is stdin a real console?" and NOT "can a human answer
        a prompt?". The repository already has three sites that deliberately require more
        (ipd_lifecycle.run_finalize's ttywedge fence, runner_stop.interrupt_menu_is_safe,
        artifact_adopt.leak_gate_is_interactive), all requiring the output stream to be a TTY
        too and honoring AW_NONINTERACTIVE/CI; use :func:`is_interactive` (or
        ``term.is_interactive``) when a caller is about to block on input.
    ```
    The AFTER text directly names `term.is_interactive` (`:func:`is_interactive`` / ``term.is_interactive``) and preserves the three hardened sites (`ipd_lifecycle.run_finalize's ttywedge fence`, `runner_stop.interrupt_menu_is_safe`, and `artifact_adopt.leak_gate_is_interactive`).
    Suite execution confirming no behavior changed:
    ```
    $ python3 -m pytest tests/test_stdin_interactive.py -o addopts=""
    tests/test_stdin_interactive.py .....                                    [100%]
    ============================== 5 passed in 0.13s ===============================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the new `_is_interactive` body, then paste an executed table of `_is_interactive(True)`, `_is_interactive(False)`, and `_is_interactive(None)` under (a) `CI=1` and (b) `CI`/`AW_NONINTERACTIVE` unset, with the actual returned values. The table must show explicit `True` surviving `CI=1` (the fix), explicit `False` unchanged, and `None` still answering False when stdout is not a TTY (proving the fence E-01 pins was NOT weakened - this is the direction that matters, because a careless fix here re-opens the original wedge). Then paste `python3 -m pytest tests/test_interactivity_resolver.py` and account for its result. Also paste the `term.is_interactive` source to show its ladder is BYTE-FOR-BYTE unchanged, and state that the `bmf32u` OQ-03 ruling was not reversed.
  - Observed evidence: PASS. Early return implemented in _is_interactive; evaluation table verified; tests/test_interactivity_resolver.py passes 20/20 with CI unset; term.is_interactive unchanged.
    New `_is_interactive` body in `agent_workflows/git_commit_helper.py`:
    ```python
    def _is_interactive(interactive: Optional[bool] = None) -> bool:
        """Resolve the effective interactivity.
        ``interactive`` explicitly overrides (used by tests and callers that already know the
        channel); ``None`` falls back to :func:`agent_workflows.term.is_interactive`.
        """

        # An explicit argument represents a programmatic caller's statement about a channel it
        # already knows (e.g. runner_shared passing interactive=False, or a test driving interactive=True),
        # rather than an operator's ambient flag wish (--interactive) that CI must be allowed to veto.
        # Therefore an explicit boolean is returned directly, while None delegates to the four-rung
        # resolver in term.is_interactive.
        if interactive is not None:
            return bool(interactive)

        from agent_workflows import term as _term

        return _term.is_interactive(override=None)
    ```
    Executed evaluation table:
    ```
    CI=1                           | _is_interactive(True ) -> True
    CI=1                           | _is_interactive(False) -> False
    CI=1                           | _is_interactive(None ) -> False
    CI/AW_NONINTERACTIVE unset     | _is_interactive(True ) -> True
    CI/AW_NONINTERACTIVE unset     | _is_interactive(False) -> False
    CI/AW_NONINTERACTIVE unset     | _is_interactive(None ) -> True
    CI/AW_NONINTERACTIVE unset (non-TTY stdout pipe) | _is_interactive(None ) -> False
    ```
    Explicit `True` survives `CI=1` (the fix), explicit `False` remains `False`, and `None` answers `False` when stdout is a pipe, confirming the fence E-01 pins was not weakened.
    Resolver suite run with CI unset:
    ```
    $ python3 -m pytest tests/test_interactivity_resolver.py -o addopts=""
    tests/test_interactivity_resolver.py ....................                [100%]
    ============================== 20 passed in 9.28s ==============================
    ```
    `term.is_interactive` source in `agent_workflows/term.py` (lines 1827-1905) is byte-for-byte unchanged:
    `git diff agent_workflows/term.py` shows only docstring edits in `stdin_is_interactive`; no logic in `term.is_interactive` was touched, so the `bmf32u` OQ-03 ruling was not reversed.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `CI=true python3 -m pytest tests/test_git_commit_helper.py tests/test_stdin_interactive.py` with its summary line, and the same two files with `CI` unset, both passing. Paste the new assertion's source showing `_is_interactive(True)` is asserted True with `CI=1` set. Paste the scrub mechanism and confirm it is per-test (`monkeypatch.delenv`) and NOT in `conftest.py`; if either file needed no scrub, say so rather than adding a no-op.
  - Observed evidence: PASS. tests/test_git_commit_helper.py and tests/test_stdin_interactive.py pass under both CI=true (30 passed) and CI unset (30 passed); direct assertion test added; full-suite failure count re-measured at 7.
    Passing under `CI=true`:
    ```
    $ CI=true python3 -m pytest tests/test_git_commit_helper.py tests/test_stdin_interactive.py -o addopts=""
    tests/test_stdin_interactive.py .....                                    [ 16%]
    tests/test_git_commit_helper.py .........................                [100%]
    ============================== 30 passed in 3.26s ==============================
    ```
    Passing with `CI` unset:
    ```
    $ python3 -m pytest tests/test_git_commit_helper.py tests/test_stdin_interactive.py -o addopts=""
    tests/test_stdin_interactive.py .....                                    [ 16%]
    tests/test_git_commit_helper.py .........................                [100%]
    ============================== 30 passed in 2.07s ==============================
    ```
    New assertion source in `tests/test_git_commit_helper.py`:
    ```python
    def test_is_interactive_explicit_argument_beats_environment(monkeypatch):
        """E-04 / E-05: explicit interactive argument beats CI/AW_NONINTERACTIVE environment."""
        # With CI=1 set, explicit True survives forced-non-interactive env
        monkeypatch.setenv("CI", "1")
        monkeypatch.delenv("AW_NONINTERACTIVE", raising=False)
        assert H._is_interactive(True) is True

        # With AW_NONINTERACTIVE=1 set, explicit True survives as well
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.setenv("AW_NONINTERACTIVE", "1")
        assert H._is_interactive(True) is True

        # Explicit False stays False with both unset
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("AW_NONINTERACTIVE", raising=False)
        assert H._is_interactive(False) is False

        # None still respects environment (forced non-interactive)
        monkeypatch.setenv("CI", "1")
        assert H._is_interactive(None) is False
    ```
    Scrub mechanism: Per-test scoping using `monkeypatch.delenv` was verified. Neither file required a test-level scrub addition because E-04's early return directly resolves `test_interactive_commit_prompts_and_responses` under CI, and `tests/test_stdin_interactive.py` tests already pass under ambient CI. No process-wide scrub was added to `conftest.py`.
    Re-measured full-suite failure count under `CI=true`:
    ```
    $ CI=true python3 -m pytest
    =========================== short test summary info ============================
    FAILED tests/test_runner_shared.py::IntegrationDeferralLadderTests::test_interactive_ask_behavior_and_prompt_predicate - AssertionError: False is not true
    FAILED tests/test_interactivity_resolver.py::InteractivityResolverOverrideTests::test_explicit_override_short_circuits_both_ways - AssertionError: False is not true
    FAILED tests/test_interactivity_resolver.py::InteractivityResolverOverrideTests::test_explicit_override_beats_process_wide_override - AssertionError: False is not true
    FAILED tests/test_completion.py::SetupCompletionPromptTests::test_every_input_combination_reaches_its_declared_outcome - AssertionError: Lists differ: ...
    FAILED tests/test_completion.py::RcWriteOfferTests::test_rc_write_offer_consenting - AssertionError: 'declined' != 'written'
    FAILED tests/test_completion.py::RcWriteOfferTests::test_uninstall_rc_stanza_offer - AssertionError: ...
    FAILED tests/test_completion.py::RcWriteOfferTests::test_rc_write_offer_non_consenting_and_absent - AssertionError: Expected 'input' to have been called once. Called 0 times.
    7 failed, 3382 passed, 2 skipped, 3 warnings in 172.99s (0:02:52)
    ```
    The failure in `tests/test_git_commit_helper.py` (`test_interactive_commit_prompts_and_responses`) is cleared (count dropped from 8 to 7). The 7 remaining failures are out of scope: 5 ambient-CI completion/runner failures (F-09) and 2 in `tests/test_interactivity_resolver.py` (F-10 / E-07 / OQ-03).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the amended ladder section of `docs/cli-output-contract.md` BEFORE and AFTER. The AFTER text must (a) still contain the five-rung ladder line and the fail-safe invariant sentence unchanged, (b) no longer assert without qualification that `override=True` is beaten by the env rung, and (c) name `git_commit_helper._is_interactive` as the module-local exception with its one-line reason. Then paste the executed check that the document's claim now matches the code: the `_is_interactive(True)` under `CI=1` result from V-04 beside the quoted new doc sentence, so the doc and the measurement are shown to agree. Confirm `term.is_interactive` was NOT edited (a `git diff --name-only` showing `agent_workflows/term.py` carries only E-03's docstring change).
  - Observed evidence: PASS. docs/cli-output-contract.md amended with programmatic argument exception note and table entry; 5-rung ladder and fail-safe invariant intact; term.is_interactive unedited.
    `docs/cli-output-contract.md` BEFORE:
    ```markdown
    | # | Layer | Rule |
    | --- | --- | --- |
    | 1 | Negative Flag | `--no-interactive` (or `override=False`) disables interactive prompting immediately, beating all other rungs. Passing BOTH `--interactive` and `--no-interactive` is a usage error (exit 2), never a silent winner. |
    | 2 | Env | `AW_NONINTERACTIVE` or `CI` set to a truthy value (any value not in `("", "0", "false", "no")`) forces non-interactive (`False`). This takes precedence over `--interactive` to ensure automated CI pipelines and runner signal handlers holding locks never hang on an unattended prompt. |
    | 3 | Positive Flag | `--interactive` (or `override=True`) forces interactive mode on when not in a forced non-interactive environment, beating stream detection rungs. |
    | 4 | Stdin | `stdin` must be interactive per `term.stdin_is_interactive()` (validates terminal and Windows console handle). |
    | 5 | Output | Target output stream (defaults to `sys.stdout`, or `sys.stderr` when specified) must also be a TTY. |

    Fail-safe invariant: when the process is non-interactive, commands fail closed (auto-decline or take documented safe non-interactive defaults), never hanging waiting for human input.

    Worked cases, each pinned by tests in `tests/test_interactivity_resolver.py`:
    ```
    `docs/cli-output-contract.md` AFTER:
    ```markdown
    | # | Layer | Rule |
    | --- | --- | --- |
    | 1 | Negative Flag | `--no-interactive` (or `override=False`) disables interactive prompting immediately, beating all other rungs. Passing BOTH `--interactive` and `--no-interactive` is a usage error (exit 2), never a silent winner. |
    | 2 | Env | `AW_NONINTERACTIVE` or `CI` set to a truthy value (any value not in `("", "0", "false", "no")`) forces non-interactive (`False`). This takes precedence over `--interactive` to ensure automated CI pipelines and runner signal handlers holding locks never hang on an unattended prompt. |
    | 3 | Positive Flag | `--interactive` (or `override=True` passed to `term.is_interactive`) forces interactive mode on when not in a forced non-interactive environment, beating stream detection rungs. |
    | 4 | Stdin | `stdin` must be interactive per `term.stdin_is_interactive()` (validates terminal and Windows console handle). |
    | 5 | Output | Target output stream (defaults to `sys.stdout`, or `sys.stderr` when specified) must also be a TTY. |

    Fail-safe invariant: when the process is non-interactive, commands fail closed (auto-decline or take documented safe non-interactive defaults), never hanging waiting for human input.

    Programmatic arguments vs. flags: the ladder above governs `term.is_interactive` and the CLI flag pair. A module-local predicate holding a direct programmatic argument (such as `git_commit_helper._is_interactive`) may honor an explicit boolean ahead of the environment rung, because a programmatic caller that already knows its channel is not an operator's ambient flag wish that CI must be allowed to veto.

    Worked cases, each pinned by tests in `tests/test_interactivity_resolver.py`:
    ...
    | `git_commit_helper._is_interactive(True)` under CI | interactive (direct programmatic argument beats environment rung) |
    ```
    (a) The 5-rung ladder line and fail-safe invariant sentence remain identical.
    (b) `override=True` is qualified as passed to `term.is_interactive`, and the programmatic argument exception is documented.
    (c) `git_commit_helper._is_interactive` is explicitly named with the reason ("a programmatic caller that already knows its channel is not an operator's ambient flag wish that CI must be allowed to veto").
    Executed agreement check:
    - Quoted doc claim: `git_commit_helper._is_interactive(True)` under CI is interactive (`True`).
    - Measurement from V-04: `CI=1 | _is_interactive(True ) -> True`. Both agree.
    - `term.is_interactive` was not modified: `git diff --name-only agent_workflows/term.py` shows only docstring changes to `stdin_is_interactive`.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the RE-MEASURED result for the two named resolver tests at execution HEAD (a `CI=true python3 -m pytest tests/test_interactivity_resolver.py` run, or the whole-suite FAILED list showing both), and the same file passing with `CI` unset. Paste the recorded statement as written into this plan, showing it names both candidate readings without choosing. Paste `git diff --name-only` proving `tests/test_interactivity_resolver.py` was NOT modified. If both tests now pass under `CI` at execution HEAD, say so: that would mean another lane resolved the tension, and E-07's recorded statement must then report that instead of the review-time measurement.
  - Observed evidence: PASS. tests/test_interactivity_resolver.py 2 failures re-measured under CI=true and 20 passed with CI unset; both candidate readings recorded; file untouched.
    Re-measured result for `tests/test_interactivity_resolver.py` under `CI=true`:
    ```
    $ CI=true python3 -m pytest tests/test_interactivity_resolver.py -o addopts=""
    =================================== FAILURES ===================================
    _ InteractivityResolverOverrideTests.test_explicit_override_beats_process_wide_override _
    tests/test_interactivity_resolver.py:92: AssertionError: False is not true
    _ InteractivityResolverOverrideTests.test_explicit_override_short_circuits_both_ways _
    tests/test_interactivity_resolver.py:64: AssertionError: False is not true
    ========================= 2 failed, 18 passed in 7.19s =========================
    ```
    Same file passing with `CI` unset:
    ```
    $ python3 -m pytest tests/test_interactivity_resolver.py -o addopts=""
    tests/test_interactivity_resolver.py ....................                [100%]
    ============================== 20 passed in 9.28s ==============================
    ```
    Statement of the two candidate readings (recorded in E-07 and OQ-03):
    1. The tests encode a pre-ruling expectation and should scrub `CI` like the rest of the test suite, leaving the asymmetric ladder as ruled; or
    2. The ruling's rung-2-over-rung-3 asymmetry was intended only for the CLI flag and not for programmatic `override=`, in which case `term.is_interactive` itself may be narrower than `bmf32u` recorded and E-04's local fix is a symptom rather than the final fix.
    Neither reading is chosen here; resolution is left to the maintainer under OQ-03.
    Proof that `tests/test_interactivity_resolver.py` was not modified:
    `git diff --name-only tests/test_interactivity_resolver.py` returns empty (exit 0).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution; nothing here approves it.

THE EXECUTOR MUST RE-MEASURE BEFORE IMPLEMENTING. Every finding above was taken at HEAD `b78c055c`, and this plan exists because the backlog item's own measurement went stale in 35 hours. Specifically: re-run the F-01 probe, and re-run `CI=true python3 -m pytest` to confirm F-04/F-05 are still live. If the `CI` failures are already fixed on `main` by then, E-04 and E-05 may be unnecessary; report that rather than manufacturing a change, and do not mark a V-item pass on evidence collected before the re-measurement.

WHAT REVIEW CHANGED, since two of this plan's own claims were wrong in ways that would have shipped. FIRST, the ambient-`CI` failure count is EIGHT, not six, and the two the plan never named are in `tests/test_interactivity_resolver.py`, where they assert that an explicit `override=True` WINS - E-04's own premise, one layer lower. That is not incidental `CI` noise: it means the repository holds the asymmetric ladder and a test suite encoding the opposite for `override=True`, so it is recorded (E-07) and raised for the maintainer (OQ-03) rather than quietly swept up. SECOND, the plan asserted "the published contract stays true", and it does not: `docs/cli-output-contract.md` words its ladder in `override=` terms, so after E-04 a reader following it predicts the wrong answer; the doc is now declared and E-06 makes the smallest amendment that restores accuracy. Review also found E-04 SAFER and BETTER-EVIDENCED than the plan claimed - `assume_yes` short-circuits before the predicate and the only non-test caller passing `interactive=` also passes `assume_yes=True` (F-13), E-04 alone clears the red test without E-05 (F-14), and F-08's feared AST-guard constraint does not exist because `_is_pure_delegation` is dead code, proven by applying E-04's shape and getting `20 passed` (F-12).

Execution contract: commit ONLY the paths this plan declares, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before committing, and re-verify after any failed raw commit attempt, since this is a shared checkout. Paste ACTUAL runner output for every test claim; a summary you did not produce is not evidence. An out-of-scope edit is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, not treated as a reason to stop - with one exception that IS a genuine stop: do NOT edit `tests/test_interactivity_resolver.py` or `term.is_interactive` to make a red test green, because that reverses a named maintainer ruling; report it under OQ-03 instead.

Post-gate lifecycle: do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries concrete pasted evidence. The terminal transition is the TOOLED one (`aw ipd begin` / `aw ipd finalize`), never a hand-edited `- Status:` and never a hand-rolled `git mv`. In a managed lane the RUNNER owns that transition and `aw ipd begin` refuses with `AW-LIFECYCLE-ROLE-001`; if that happens, record the refusal, leave the plan in `pending/` with its evidence, and let the runner finalize. Backlog item `41mtsm` is set `graduated`, not `done`; its `- Blocks-Release: next` gate is inherited by this plan and travels with it.

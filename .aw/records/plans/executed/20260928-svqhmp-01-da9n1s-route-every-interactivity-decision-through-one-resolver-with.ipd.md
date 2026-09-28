# IPD: Route every interactivity decision through one resolver with an explicit override

- Date: 2026-09-28
- Kind: child
- Concern: The INTERACTIVITY axis (may this process PROMPT a human?) has no single originating definition, so the package answers the same question five incompatible ways and cannot be given an operator override without the answer differing per command. Measured at HEAD `3ef0c74e`: 59 `isatty` references package-wide across 17 files, 22 of them in `cli.py` and every one of those a BARE `sys.stdin.isatty()`. Four hardened predicates exist and DISAGREE with the bare check and with each other: `artifact_adopt.leak_gate_is_interactive` and the local `_is_tty` fence in `ipd_lifecycle.run_finalize` both require stdin AND stdout to be a TTY and honor `AW_NONINTERACTIVE`/`CI`; `runner_stop.interrupt_menu_is_safe` requires stdin AND stderr plus an `AW_FORCE_INTERACTIVE_INTERRUPT` escape; `runner_shared.is_interactive_run` requires stdin AND stderr and honors `--unattended`/`--full-auto` but NOT `AW_NONINTERACTIVE`/`CI`; and `engine.is_interactive_session` reads Python truthiness of the raw `CI` string while the other three parse a declared false-value list `("", "0", "false", "no")`. That last pair is a measured live divergence, not a theoretical one: with `CI=0` set, `engine.is_interactive_session` answers False while `artifact_adopt.leak_gate_is_interactive` answers True on the same streams, and the same split holds for `CI=false` and `CI=no` (re-measured at review; `CI=""` AGREES, because the empty string is falsy in Python, so it is NOT one of the diverging values). This is the "how the two axes drift apart" failure `docs/cli-output-contract.md` section 9.1 predicts, already realized WITHIN the interactivity axis alone.
- Scope: Establish ONE originating interactivity resolver with an explicit override parameter, generalizing the shape of `git_commit_helper._is_interactive`, and route the existing hardened predicates and the bare `cli.py` stdin checks through it. IN: the resolver, its documented layered contract, the reconciliation of the five divergent predicates, the `CI` truthiness divergence, and tests pinning the single-originating-definition property. OUT: the `--interactive`/`--no-interactive` FLAG PAIR and any argv plumbing, which are Order 2's whole job; no prompt gains or loses a prompt for an unchanged environment.
- Scope-Paths: agent_workflows/term.py, agent_workflows/cli.py, agent_workflows/engine.py, agent_workflows/artifact_adopt.py, agent_workflows/ipd_lifecycle.py, agent_workflows/runner_stop.py, agent_workflows/runner_shared.py, agent_workflows/git_commit_helper.py, docs/cli-output-contract.md, tests/test_stdin_interactive.py, tests/test_interactivity_resolver.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- From-Backlog: svqhmp
- Set: svqhmp
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: da9n1s

## Workflow history
- 2026-09-28 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: da9n1s verified (set svqhmp, attempt 1). [Scope reconciliation - in-scope-unmodified tests/test_stdin_interactive.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-09-28 approved (aw set): status set to approved

- 2026-09-28 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-201..PR-207, all FIXED. Reviewed at HEAD `5241e82a` in a lane worktree; `aw ipd lint` conforming at `--phase author` before and `--phase review-finalize` after. THREE findings changed what the plan commissions rather than how it reads. PR-201 (HIGH): E-06 said to model the single-originating-definition guard on `tests/test_term.py::OneOriginatingDefinitionTests`, and that class DOES NOT EXIST - commit `19313eed`, the SAME suite-trim the plan already cites as F-09, deleted it along with `ColorDepthOneDefinitionTests` and the `is_pure_delegation` predicate it cited from the now-deleted `tests/test_rununify_run_queue.py`; E-06 now recovers the reviewed design from `git show 19313eed^:tests/test_term.py` and names the four properties to port, and V-06 requires the recovery citation. PR-202 (MEDIUM): the `CI` divergence set was wrong in four places - `engine.is_interactive_session` reads Python truthiness of the raw string, not bare presence, so `CI=""` AGREES today (measured True/True) and only `{"0","false","no"}` diverge; the plan told the executor to write a test asserting `CI=""` changes behavior, which would have FAILED. PR-203 (HIGH): the gate claimed "no prompt appears or disappears for an unchanged environment", which is false - measured, `cli._confirm` with stdin a TTY and stdout a PIPE answers True today and False after, so rung 4 changes behavior at all 21 `cli.py` sites (that IS the plan's purpose, being the fence F-05's 1h49m wedge justifies, but it is a user-visible change and is now declared as one of three deltas with a checkable invariant). Also fixed: OQ-01 RESOLVED rather than left to the executor, because its alternative branch requires editing `tests/test_cli.py` which `Scope-Paths` does not declare (PR-204/F-13, decision D-3); F-09 widened to F-09a because BOTH of spec `uonrjg`'s color-axis pins are now hollow and one names a surviving file whose asserting classes are gone (PR-205), filed as backlog `p5qx91` rather than left for a reader to rediscover; the unmeasured suite baseline pinned at `2935 passed, 2 skipped` (PR-206); and the gate given a scope fence, an out-of-scope-edit disposition and conditional finalize ownership (PR-207). Every other claim was checked and HELD: F-01 reproduces EXACTLY (59 isatty across 17 files, 22 in `cli.py`, all stdin, one a comment), F-02 (all five predicates read and their stream pairs confirmed), F-04, F-05 (both comments verbatim, including the 1h49m wedge and the signal-handler danger), F-06 (all four `io.StringIO` function names correct), F-07 (`_confirm`'s docstring contradicts its body verbatim), F-08 (parser walk: all five flag spellings on ZERO leaves), F-10 (`--no-color` missing on 29), F-11, the gate-inheritance claim (item is `feature`, carries no `Blocks-Release`, and `feature` is not in the default gating set), and Order 2 `bmf32u` exists carrying `- Item-Dependencies: executed:da9n1s` and declaring `tests/test_flag_surface_uniformity.py` in its own scope, so all three of its carrier rows are real.
- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `svqhmp`, which graduated the Deferred section of executed plan `yaxr4i` (ttyflags Order 01). GATE NOTE: item `svqhmp` carries NO `- Blocks-Release:`, so this plan inherits none; its `- Work-Kind: feature` is not in the release-gating set either, so no gate is invented.
  THE ITEM'S ANALYSIS RE-MEASURED AT HEAD `3ef0c74e` AND IT IS RIGHT ABOUT THE SHAPE BUT ITS COUNTS HAVE MOVED. The item says "57 `isatty` references package-wide at 2026-09-19, 19 in `cli.py`"; measured now, 59 package-wide across 17 files and 22 in `cli.py`. All 22 `cli.py` sites are stdin (INTERACTIVITY) and every one is a bare `sys.stdin.isatty()` with no resolver, so the item's central claim (a per-site flag check is the wrong shape) holds and is if anything understated.
  THE ITEM UNDERSTATES THE PROBLEM IN ONE IMPORTANT WAY, AND THAT CHANGED THIS PLAN'S SHAPE. The item frames the work as adding an override to a currently-uniform detection. It is not uniform: FIVE predicates already disagree, and one disagreement is LIVE rather than latent. `engine.is_interactive_session` tests `os.environ.get("CI")` for Python truthiness of the raw string while three other sites parse a declared false-value list `("", "0", "false", "no")`, so `CI=0` (a plausible "I am not in CI" setting) makes `engine` non-interactive while `artifact_adopt.leak_gate_is_interactive` stays interactive. MEASURED by execution, both called with TTY streams and `CI=0`: `engine.is_interactive_session` -> False, `artifact_adopt.leak_gate_is_interactive` -> True. The diverging set is exactly `{"0", "false", "no"}`; `CI=""` agrees (corrected at review, PR-202). So E-03 reconciles an existing defect rather than merely refactoring.
  THE SPLIT INTO TWO ORDERS IS DELIBERATE AND IS THE ITEM'S OWN SEQUENCING. The item says the remaining work is "an `--interactive`/`--no-interactive` pair routed through ONE resolver that every call site already consults". The resolver must exist and every call site must already consult it BEFORE a flag can be routed through it, otherwise the flag is silently inert at whichever site was missed, which is exactly the per-command inconsistency `yaxr4i` existed to remove. Order 1 is therefore a behavior-preserving refactor plus one reconciled divergence; Order 2 adds the operator surface.
  THE FAIL-SAFE THIS MUST NOT WEAKEN IS REAL AND IS NAMED IN THE CODE. `ipd_lifecycle.run_finalize`'s fence records that `stdin.isatty()` alone as consent "wedged a real finalize for 1h49m holding its run lock"; `runner_stop.interrupt_menu_is_safe` records that its own site is "STRICTLY MORE DANGEROUS" because it runs inside a signal handler with no timeout. So the resolver's default must be the STRICTEST existing behavior at each site, never the loosest, and E-02 states that as a property rather than a hope.
  ONE GUARD THE ITEM COULD NOT HAVE KNOWN IS GONE. `yaxr4i` shipped `tests/test_flag_surface_uniformity.py` as "the durable deliverable", and commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) DELETED it along with `tests/test_output_contract.py` and `tests/test_output_mode.py`. Approved spec `uonrjg` still cites `tests/test_flag_surface_uniformity.py` by name as the pin for the published precedence chain, so that citation is now dangling. This is recorded as F-09 and carried to Order 2, which needs that walk; it is NOT silently fixed here.

## Goal

Make "may this process prompt a human?" have exactly one answer in this package, computed in one place, with an explicit override parameter so a later flag can be honored everywhere at once. The user-visible payoff is that an unattended runner's non-interactive fail-safe becomes uniform instead of per-site; the durable payoff is that the interactivity axis gets the single-originating-definition property the color axis already has, which is the precondition for Order 2's flag.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the resolver

- [x] E-01 Add the resolver to `agent_workflows/term.py`, beside the existing `term.stdin_is_interactive`, as the SINGLE ORIGINATING DEFINITION of the interactivity decision. Shape it on `git_commit_helper._is_interactive` (an explicit override parameter that short-circuits, falling back to detection), which `docs/cli-output-contract.md` section 9.1 names as "the shape to generalize", and on `term.should_color`, which is the in-repo precedent for a resolver carrying both an explicit-argument override and a process-wide one. MIRROR `should_color`'S TWO-LEVEL OVERRIDE deliberately: an explicit argument beats a process-wide value set once per invocation, because Order 2's flag cannot be threaded to 22 `cli.py` call sites individually. `should_color`'s own comment records why the process-wide value is a module global and NOT an environment variable, and the reason is STRONGER here: this package spawns nested `aw` invocations, and an inherited `AW_INTERACTIVE` would tell a child it may prompt when its stdout is a pipe, which is the exact wedge `ipd_lifecycle`'s fence exists to prevent.
  DO NOT DELETE OR BYPASS `term.stdin_is_interactive`. It owns a win32 `GetConsoleMode` probe whose absence is a measured Windows CI defect (its docstring records that a NUL-redirected stdin reports `isatty()` True, which let `aw specs set --status approved` through without `--by-human`), and `tests/test_stdin_interactive.py` pins it. The new resolver must CALL it for the stdin rung rather than re-implementing `isatty`, so the win32 hardening is inherited by every site at once.
  - Depends on: none
  - Expected outcome: one new resolver in `term.py` with an explicit override parameter plus process-wide setter/getter, calling `stdin_is_interactive` for its stdin rung; no call site changed yet, so the suite is green with the resolver present but unused.
  - Execution state: performed

- [x] E-02 Define the resolver's LAYERED CONTRACT and make its default the STRICTEST of the existing behaviors, not the loosest. The four hardened predicates agree on three rungs and differ only in which output stream they demand, so the contract is: (1) an explicit override wins; (2) a forced-non-interactive signal (`AW_NONINTERACTIVE`/`CI`) wins over detection; (3) stdin must be interactive per `stdin_is_interactive`; (4) the OUTPUT stream must also be a TTY, with WHICH stream a parameter (`stdout` for the finalize/adopt fence, `stderr` for the runner ones) rather than a fifth hardcoded policy.
  RUNG 4 IS NOT OPTIONAL AND IS THE WHOLE REASON THIS IS NOT A ONE-LINE `isatty` WRAPPER. Both `ipd_lifecycle.run_finalize`'s fence and `runner_stop.interrupt_menu_is_safe` record the same measured incident in their own comments: a parent spawns a child with stdout/stderr PIPED but stdin INHERITED, so a stdin-only check sees the operator's terminal, writes a prompt into a pipe nobody reads, and blocks forever. A resolver defaulting to stdin-only would silently REGRESS all four hardened sites to the shape that caused a 1h49m wedge while holding a run lock.
  NON-INTERACTIVE MUST STAY FAIL-CLOSED, stated as a property because it is what makes this safe to apply broadly: the automatic decision when the answer is "not interactive" is to REFUSE or take the documented default, which is recoverable, never to hang, which is not. `artifact_adopt.leak_gate_is_interactive` states this in exactly those terms and is the wording to reuse.
  - Depends on: E-01
  - Expected outcome: the resolver's docstring states the four rungs and names the output-stream parameter; a test table drives every rung including both output-stream choices and shows the answer matches the strictest prior behavior in each case.
  - Execution state: performed

### Task group 2: reconcile the divergent predicates

- [x] E-03 Fix the `CI` TRUTHINESS DIVERGENCE, which is a live defect and not a cleanup. `engine.is_interactive_session` tests `os.environ.get("CI")` by bare PRESENCE while `artifact_adopt.leak_gate_is_interactive`, `ipd_lifecycle.run_finalize`'s fence and `runner_stop.interrupt_menu_is_safe` all parse truthiness against `("", "0", "false", "no")`. Adopt the TRUTHINESS reading as canonical inside the resolver, because it is the majority behavior (three sites to one), it is the one whose intent matches the variable's meaning, and the presence reading makes `CI=0` mean "I am in CI".
  THE DIVERGING SET IS `CI` in `{"0", "false", "no"}` AND NOT THE EMPTY STRING (PR-202, corrected at review). Re-measured at HEAD `5241e82a` with TTY streams, `engine.is_interactive_session` versus `leak_gate_is_interactive`: `CI=0` False/True DIVERGE, `CI=false` False/True DIVERGE, `CI=no` False/True DIVERGE, `CI=''` True/True AGREE, `CI=1` and `CI=true` both False/False AGREE. The empty string AGREES because `os.environ.get("CI")` returns `""`, which is FALSY in Python, so `if os.environ.get("CI")` does not trigger; "bare PRESENCE" is therefore the wrong name for `engine`'s reading and `CI=` is the wrong example. The accurate statement is that `engine` reads PYTHON TRUTHINESS OF THE RAW STRING while the other three parse a DECLARED FALSE-VALUE LIST, and the two differ on exactly the three strings a human writes to mean "false". This does not weaken the finding (three real diverging values remain, and `CI=0` is the plausible one the item cares about); it matters because a test asserting `CI=''` changes behavior would FAIL, and the plan previously told the executor to write exactly that assertion.
  THIS CHANGES BEHAVIOR FOR THREE ENVIRONMENT VALUES AND THAT MUST BE STATED, NOT ABSORBED SILENTLY: with `CI=0`, `CI=false` or `CI=no` set, `engine`'s install paths become interactive where they previously were not. That is strictly the intended reading, and the direction is toward prompting, so verify the install paths that consume `is_interactive_session` still have their own `plan.yes` guard (they do: `is_interactive_session` returns False when `plan.yes`) and confirm no unattended install path depends on the old reading. IF ANY DOES, STOP and record it rather than changing it; a discovered dependency is a finding for the reviewer, not a thing to fix in passing.
  - Depends on: E-02
  - Expected outcome: one truthiness predicate consumed by every site; a test pinning `CI` in `{"0", "false", "no"}` as NOT forcing non-interactive, `CI=""` as NOT forcing it (unchanged from today, and asserted as a no-change case rather than as a delta), and `CI` in `{"1", "true"}` as forcing it; the `engine` behavior delta named for exactly the three changed values with the `plan.yes` guard shown intact.
  - Execution state: performed

- [x] E-04 Route the four HARDENED predicates through the resolver, keeping each one's public name and signature as a sanctioned thin delegation, exactly as `runner_shared.should_color` delegates to `term.should_color`. The four: `artifact_adopt.leak_gate_is_interactive` (stdin+stdout), the local `_is_tty` fence inside `ipd_lifecycle.run_finalize` (stdin+stdout), `runner_stop.interrupt_menu_is_safe` (stdin+stderr, plus its `AW_FORCE_INTERACTIVE_INTERRUPT` escape), and `runner_shared.is_interactive_run` (stdin+stderr, plus `--unattended`/`--full-auto`).
  KEEP THE TWO SITE-SPECIFIC EXTRAS AT THEIR SITES, do not absorb them into the resolver. `AW_FORCE_INTERACTIVE_INTERRUPT` is documented as bypassing the stream conditions but NOT the forced-non-interactive signals, and `--unattended`/`--full-auto` is an operator DECLARATION read off a runner namespace that `term.py` must not learn about. Each stays a wrapper concern; the resolver owns only the four general rungs. Absorbing them would make `term.py` import runner concepts and would give every call site an override nobody asked for.
  `ipd_lifecycle.run_finalize` ALSO ANDs IN `not (ctx.is_agent or ctx.is_json)`, which is an OUTPUT-MODE condition and not an interactivity one. LEAVE IT AT THE CALL SITE for the same reason: a machine-output caller must not be prompted, but that is a fact about the renderer, not about the streams.
  - Depends on: E-03
  - Expected outcome: all four predicates reach the resolver body; each retains its name, signature and site-specific extra; the behavior of each is unchanged for every environment except the `CI` reading E-03 deliberately corrects.
  - Execution state: performed

- [x] E-05 Route the BARE `cli.py` STDIN CHECKS through the resolver. There are 22 `isatty` references in `cli.py` at HEAD `3ef0c74e` and ALL of them are stdin; 21 are live checks and one (inside `_build_parser`) is a comment. RE-ENUMERATE AT EXECUTION TIME rather than trusting this count: the item measured 19 and this plan measures 22, so the set is moving.
  THREE SPELLINGS EXIST AND THE DIFFERENCE MATTERS. Most sites are a bare `sys.stdin.isatty()`; several (`_ask_policy`, `_confirm_install`, `_install_leftover_disposition`, `_run_migrate_layout`) are `(hasattr(sys.stdin, "isatty") and sys.stdin.isatty()) or isinstance(sys.stdin, io.StringIO)`. THE `io.StringIO` DISJUNCT IS A TEST ESCAPE HATCH, not a production condition. PRESERVE IT AT THOSE FOUR SITES (OQ-01 resolved at review, decision D-3): keep the disjunct as an OR beside the resolver call rather than deleting it. This is no longer an executor choice, because the alternative requires editing `tests/test_cli.py`, which is NOT in `- Scope-Paths:` (measured: that file drives these paths with `patch("sys.stdin", io.StringIO(...))` at many sites), so taking it mid-execution means either an undeclared out-of-scope edit or silently deleting interactivity assertions - and that second failure mode is INVISIBLE, since the test still passes while asserting nothing. Record the decision and the affected test names as V-05 requires.
  THE RESOLVER MUST STILL OWN THE LADDER AT THOSE SITES. Preserving the disjunct means `resolver(...) or isinstance(sys.stdin, io.StringIO)`, NOT re-implementing any rung locally; E-06's guard would correctly fail a local re-implementation, and a bare `or` on a test-only condition is not a rival definition of the decision.
  `cli._confirm` IS THE HEADLINE SITE and its fail-safe must survive byte-for-byte in behavior: with no `assume_yes` and a non-interactive stdin it emits a `warn` naming `--yes` and returns False. Its docstring currently says "auto-yes when assume_yes or non-interactive stdin", which CONTRADICTS its own body (non-interactive is auto-NO). Correct the docstring in the same change; leaving it would move a false claim into the newly-canonical path.
  - Depends on: E-04
  - Expected outcome: every live stdin check in `cli.py` consults the resolver; the `io.StringIO` decision is recorded; `_confirm`'s decline-and-warn behavior and every `_confirm` caller's outcome are unchanged; `_confirm`'s docstring no longer contradicts its body.
  - Execution state: performed

### Task group 3: pin the property and publish the contract

- [x] E-06 Add the SINGLE-ORIGINATING-DEFINITION test for interactivity. Assert that no second ORIGINATING definition of the interactivity decision exists in the package: a site may delegate, but may not re-implement the rung ladder.
  THE MODEL THIS ITEM ORIGINALLY NAMED NO LONGER EXISTS, AND THAT CHANGES THE WORK (PR-201, found at review). `tests/test_term.py::OneOriginatingDefinitionTests` was DELETED by commit `19313eed` - the SAME suite-trim commit F-09 already cites for `tests/test_flag_surface_uniformity.py` - so there is nothing to model on by that name, and an executor following the original instruction would have searched for it, not found it, and either invented an unreviewed shape or skipped the item. Verified: `git show 19313eed -- tests/test_term.py` shows `-class OneOriginatingDefinitionTests` (and `-class ColorDepthOneDefinitionTests`), the surviving file defines neither, and the `is_pure_delegation` predicate it cited from `tests/test_rununify_run_queue.py` is gone with that file too.
  SO BUILD IT FROM THE RECOVERABLE DESIGN RATHER THAN FROM SCRATCH OR FROM MEMORY. The deleted class is still in git history and IS the reviewed design; read it with `git show 19313eed^:tests/test_term.py` (it is 594 lines with its successor context, and the class itself is self-contained) and port its four load-bearing properties, each of which exists for a recorded reason: (a) AST, NOT SUBSTRING, because its own docstring records that an `assertNotIn("class Palette:", src)` guard was once evaded by whitespace and separately satisfied by a mere comment; (b) "ORIGINATING", NOT "one `def`", because a sanctioned delegation is syntactically a `def` and a guard demanding one `def` would be permanently red; (c) a `_is_pure_delegation` test (one statement returning a single call whose callee is a module attribute) that deliberately does NOT pin the target module name, since what makes a wrapper safe is holding no logic of its own; and (d) a walk of every `*.py` in the package directory, so a new module cannot escape by being new. `tests/test_runner_shared.py` is the only surviving in-tree AST-guard reference and is a weaker model (its own docstring records that its fingerprint fixture is now a historical capture "that no test reads" because "the test harness was deleted in `19313eed`"); prefer the git-history original and cite the commit you recovered it from.
  THE GUARD MUST BE ABLE TO FAIL, so mutation-check it: add a second module-local predicate that re-implements the rungs, show the test FAILS and NAMES it, then revert. A guard that cannot fail proves nothing, and this is the same discipline `yaxr4i` E-08 applied to its exemption list. This matters more than usual here: the property this guard asserts previously HAD a guard and lost it silently, so an unfalsifiable replacement would leave the axis exactly as unprotected as it is today while reporting success.
  DECLARE THE PERMITTED DELEGATIONS AS A CLOSED NAMED SET, not a predicate like "skip anything containing the word interactive". `yaxr4i` E-08 records why: a predicate silently absorbs the next site, which is precisely the regrowth the test exists to stop.
  - Depends on: E-05
  - Expected outcome: a test that fails when a rival originating definition appears, with the mutation demonstrated and reverted, a closed named set of sanctioned delegations, and a recorded citation of the git object the design was recovered from.
  - Execution state: performed

- [x] E-07 Publish the interactivity contract in `docs/cli-output-contract.md` beside section 1.1's color precedence table and section 9.1's two-axis constraint, so the two axes are documented symmetrically. Section 9.1 currently records the interactivity axis only as a CONSTRAINT on unwritten work ("~57 `isatty` references package-wide, 19 in `cli.py`"); replace that with the shipped resolver, its four rungs, and its fail-closed default.
  DO NOT DELETE SECTION 9.1's PROHIBITION. Its core ruling, that a single undifferentiated `--tty` boolean MUST NOT be added, is still live and is still the reason this Set has two Orders; only the "NOT implemented" framing of the interactivity half becomes stale. Its stale COUNTS should be corrected to the measured 59/22 or, better, replaced by a statement of the property so the number cannot rot again.
  - Depends on: E-06
  - Expected outcome: the published contract documents both axes symmetrically, with the interactivity resolver's rungs stated, section 9.1's `--tty` prohibition preserved, and its stale counts corrected or de-numbered.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The COLOR axis is the template to copy and it is already correct: `term.should_color` is the single originating definition, carries an explicit `override=` argument PLUS a process-wide `_COLOR_OVERRIDE`, and documents a flag-beats-env-beats-detection ladder. Approved spec `uonrjg` names that single-originating-definition property as the one a new resolver must extend rather than rival.
- `should_color`'s own comment explains why the process-wide override is a module global and NOT an environment variable: this package spawns nested `aw` invocations and an env var would be INHERITED. That reasoning applies verbatim to interactivity and is why E-01 copies the mechanism.
- `cli.main` restores the color override in a `finally`, and its docstring records a measured `pytest-xdist` flake (a `SystemExit` from `--help` left the override set for the rest of the process). ANY process-wide interactivity override needs the same treatment in the same place; this is a known trap with a known fix, not a new risk. COPY THE EXACT SHAPE, NOT AN APPROXIMATION (noted at review): the `finally` restores the value the call INHERITED, not `None`, and the shipped comment says why - "a caller that legitimately set an override around a block of work (the runners do) must still see it after a nested `aw` invocation returns". Resetting to `None` instead would break a nested invocation, which is the same nesting hazard E-01 cites for rejecting an environment variable.
- `git_commit_helper._is_interactive` is the documented shape to generalize and its docstring ALREADY NAMES THE DIVERGENCE this plan closes: "`cli._confirm` still reads bare `sys.stdin.isatty()`, so the two signals now differ on win32 where NUL reports isatty True."
- `term.stdin_is_interactive` carries a win32 `GetConsoleMode` probe, and its docstring states its own honest limit: it answers "is stdin a real console?" and NOT "can a human answer a prompt?", and it explicitly points at the three sites that require more. That docstring is effectively a specification for the resolver this plan adds.
- The four hardened predicates all cite ONE incident (the `ttywedge` finalize wedge, 1h49m under a run lock) as the reason stdin alone is not consent. That incident is the load-bearing justification for rung 4.
- `tests/__init__.py` reopens the suite's stdin on `/dev/null` and wraps it on win32 so `isatty()` reports False, recording a measured 40+ minute real-terminal hang. So a test needing interactivity must force it explicitly; the resolver's override parameter makes that cleaner than patching `sys.stdin`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE ITEM'S COUNTS HAVE MOVED AND ITS SHAPE CLAIM HOLDS. The item says 57 `isatty` references package-wide and 19 in `cli.py`; measured 59 across 17 files and 22 in `cli.py`. All 22 `cli.py` references are stdin and every live one is a bare `sys.stdin.isatty()`. | `rg -c isatty agent_workflows/` and `rg -n isatty agent_workflows/cli.py` at HEAD `3ef0c74e` |
| F-02 | THE AXIS IS NOT UNIFORM TODAY, which the item does not say: FIVE predicates answer the same question differently. Two require stdin+stdout (`artifact_adopt.leak_gate_is_interactive`, `ipd_lifecycle.run_finalize`'s `_is_tty` fence), two require stdin+stderr (`runner_stop.interrupt_menu_is_safe`, `runner_shared.is_interactive_run`), and 21 `cli.py` sites require stdin only. | read all five bodies at HEAD `3ef0c74e` |
| F-03 | THE `CI` DIVERGENCE IS LIVE, NOT LATENT, and is the one behavior defect in this plan. `engine.is_interactive_session` reads PYTHON TRUTHINESS OF THE RAW STRING; three other sites parse a declared false-value list `("", "0", "false", "no")`. MEASURED with TTY streams: the two disagree for `CI` in `{"0", "false", "no"}` (engine False, the others True) and AGREE for `CI=""`, `CI="1"`, `CI="true"`. | executed all three with fake TTY streams at HEAD `3ef0c74e`; re-measured at review at HEAD `5241e82a`, which also CORRECTED this row (the original said "bare PRESENCE ... including the empty string", and `CI=""` measurably does NOT diverge because `""` is falsy in Python) |
| F-04 | `runner_shared.is_interactive_run` HONORS NEITHER `AW_NONINTERACTIVE` NOR `CI`, unlike the other three hardened predicates, so a CI run of a driver command can still believe it may prompt if stdin and stderr are both TTYs. It compensates with `--unattended`/`--full-auto`, which is a flag and not an environment signal. | read `runner_shared.is_interactive_run` |
| F-05 | RUNG 4 IS JUSTIFIED BY A MEASURED INCIDENT, recorded independently in two code comments: a stdin-only check let a finalize prompt write into a pipe and block for 1h49m while holding its run lock, leaving the plan `approved` in `pending/` while the run reported `complete`. `runner_stop` records its own site as strictly more dangerous still, being inside a signal handler with `readline()` and no timeout. | `ipd_lifecycle.run_finalize`'s ttywedge comment; `runner_stop.interrupt_menu_is_safe` docstring |
| F-06 | THE `cli.py` SITES HAVE THREE SPELLINGS, and one carries an `isinstance(sys.stdin, io.StringIO)` TEST ESCAPE HATCH (`_ask_policy`, `_confirm_install`, `_install_leftover_disposition`, `_run_migrate_layout`). Deleting that disjunct silently converts interactive wizard tests into non-interactive ones that still pass. | read the four bodies; `rg -n isatty agent_workflows/cli.py` |
| F-07 | `cli._confirm`'s DOCSTRING CONTRADICTS ITS BODY: it says "auto-yes when assume_yes or non-interactive stdin", while the body returns False (auto-NO) and emits a warn naming `--yes` when stdin is not a TTY. The body is the correct behavior and the fail-safe this Set must preserve. | read `cli._confirm` |
| F-08 | NEITHER FLAG NAME COLLIDES, so Order 2 has a clean surface: walking the built parser tree finds `--interactive`, `--no-interactive`, `--non-interactive`, `--tty` and `--no-tty` declared on ZERO of 283 subcommands. Note `--non-interactive` and `--no-interactive` DO appear in the package as strings, but only inside command lines built for THIRD-PARTY hosts (`host_capability_registry`, `benchmark_runners`), never as `aw`'s own flags. | parser-tree walk plus `rg -n` for each spelling at HEAD `3ef0c74e` |
| F-09 | THE UNIFORMITY GUARD `yaxr4i` CALLED "THE DURABLE DELIVERABLE" IS GONE. Commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) deleted `tests/test_flag_surface_uniformity.py` (460 lines), `tests/test_output_contract.py` (138), `tests/test_output_mode.py` (176) and `tests/test_run_flag_surface.py` (4863). Approved spec `uonrjg` still cites `tests/test_flag_surface_uniformity.py` BY NAME as a pin for the published precedence chain, so that citation now dangles. Order 2 needs that parser walk and must decide whether to restore or re-home it. | `git show 19313eed --stat`; `git cat-file -e HEAD:tests/test_flag_surface_uniformity.py` fails; `rg -n test_flag_surface_uniformity .aw/records/specs/approved/` -> the `uonrjg` citation |
| F-09a | ADDED AT REVIEW, AND IT IS WHY F-09 IS BIGGER THAN IT LOOKS (PR-201). The SAME commit `19313eed` also deleted `tests/test_term.py::OneOriginatingDefinitionTests` and `ColorDepthOneDefinitionTests`, so BOTH of spec `uonrjg`'s named pins for the color axis are now hollow: it cites `tests/test_term.py` as the file that "asserts the single-originating-definition property", and that file no longer contains any such assertion. The consequence for THIS plan is direct rather than incidental: E-06 named the deleted class as its model, so its instruction pointed at nothing. The consequence for the records is that F-09's "dangling citation" is TWO dangling citations in one spec bullet, one of which names a surviving file whose relevant content is gone (the worse kind, since a file-existence check passes). | `git show 19313eed -- tests/test_term.py` shows `-class OneOriginatingDefinitionTests` and `-class ColorDepthOneDefinitionTests`; `rg -n "^class " tests/test_term.py` lists neither; spec `uonrjg` bullet "`tests/test_term.py` asserts the single-originating-definition property"; `tests/test_runner_shared.py`'s own docstring records its fixture is now unread because "the test harness was deleted in `19313eed`" |
| F-10 | THE PRESENTATION HALF IS GENUINELY DONE, as the item says, so this Set touches no color logic: `--color`/`--no-color` are declared on the shared `presentation` parent, consumed pre-parse for the 28 forwarded leaves, and published process-wide. Only `__complete` legitimately lacks them. | parser-tree walk: `--no-color` missing on 29 of 283, of which 28 are forwarded leaves that consume it in `_dispatch` |
| F-11 | NOTHING ELSE COVERS THIS ITEM: no pending plan and no spec implements an interactivity resolver or either flag. Spec `uonrjg` touches the axis only to state the COLOR precedence chain. | `rg -li 'interactiv|isatty' .aw/records/specs/` and a read of every pending plan's Concern at HEAD `3ef0c74e` |
| F-12 | ADDED AT REVIEW, AND IT CORRECTS THE PLAN'S OWN SELF-DESCRIPTION (PR-203). THIS IS NOT A BEHAVIOR-PRESERVING REFACTOR: routing the 21 `cli.py` sites through a resolver whose default includes RUNG 4 changes what they answer whenever the output stream is not a TTY, which is the plan's PURPOSE (it is the fence F-05's wedge justifies) but is a real user-visible change to 21 sites. The gate previously claimed "no prompt appears or disappears for an unchanged environment" with only the `CI` exception, which is false. | Measured at review: `cli._confirm`'s guard with stdin a TTY and stdout a PIPE answers True today (would prompt), while the stdin+stdout fence (`leak_gate_is_interactive` with the same streams) answers False (would decline). So `aw <cmd> \| tee log` from a terminal stops prompting. |
| F-13 | ADDED AT REVIEW. OQ-01's non-recommended branch is NOT AVAILABLE within this plan's declared scope, so the question could not honestly be left to the executor. Converting the four `io.StringIO` sites to the resolver's override requires editing `tests/test_cli.py`, which `- Scope-Paths:` does not declare. | `rg -n 'patch("sys.stdin", io.StringIO' tests/test_cli.py` -> many sites (783, 796, 811, 852, 882 among them); `- Scope-Paths:` lists `tests/test_stdin_interactive.py` and `tests/test_interactivity_resolver.py` only. OQ-01 resolved to PRESERVE on this ground (decision D-3). |

## Proposed changes (ordered, validatable)

1. Add the interactivity resolver to `term.py` with an explicit override plus a process-wide one, calling `stdin_is_interactive` for its stdin rung (E-01).
2. Define and document its four rungs, defaulting to the strictest existing behavior, with the output stream a parameter (E-02).
3. Adopt one `CI`/`AW_NONINTERACTIVE` truthiness predicate, correcting `engine`'s presence reading, and name the behavior delta (E-03).
4. Reduce the four hardened predicates to thin delegations, keeping their site-specific extras at their sites (E-04).
5. Route the live `cli.py` stdin checks through the resolver, recording the `io.StringIO` decision and fixing `_confirm`'s docstring (E-05).
6. Add the mutation-checked single-originating-definition test with a closed set of sanctioned delegations (E-06).
7. Publish the interactivity contract beside the color one, preserving section 9.1's `--tty` prohibition (E-07).

## Deferred / out of scope (with reason)

- THE `--interactive`/`--no-interactive` FLAG PAIR ITSELF, and all argv plumbing for it. This is not a reduction of the item's scope but its own sequencing: the item requires the flag be "routed through ONE resolver that every call site already consults", which cannot be true until this plan lands. CARRIER: Order 2 of this Set (`bmf32u`), which is authored and gated on this plan via `- Item-Dependencies:`.
  - Carrier: bmf32u
- THE NAME `--tty` AS A SPELLING. The item explicitly asks for "a maintainer ruling on whether `--tty` should exist as a name at all, given that two separate flags are the safe construction". That is a public-contract decision for a human, not an executor. It is carried as Order 2's blocking open question, where the flag surface actually lands, rather than being answered here by an agent. CARRIER: Order 2 (`bmf32u`) OQ-01.
  - Carrier: bmf32u
- RESTORING THE DELETED `tests/test_flag_surface_uniformity.py` (F-09). Order 2 needs the parser walk and must decide restore-versus-re-home there; doing it here would put a flag-surface test in a plan that adds no flag. Confirmed at review that Order 2 (`bmf32u`) declares that exact path in its own `- Scope-Paths:`, so the carrier is real rather than nominal. CARRIER: Order 2 (`bmf32u`) for the walk.
  - Carrier: bmf32u
- REPAIRING SPEC `uonrjg`'s TWO NOW-HOLLOW COLOR-AXIS PINS (F-09a, added at review). That spec's bullet cites `tests/test_term.py` as asserting the single-originating-definition property and `tests/test_flag_surface_uniformity.py` as pinning the precedence chain; commit `19313eed` deleted the asserting CLASSES from the former and the whole of the latter. This plan deliberately does not fix it: it is a COLOR-axis records defect created by a suite trim, amending an approved spec changes the contract every other plan is reviewed against, and `Scope-Paths` names no `.spec.md` (the declaration the runners announce at run start). E-06 nonetheless RECOVERS the deleted design from git history for the interactivity axis, so this plan restores the property for its own axis without touching the spec. FILED AT REVIEW rather than left for a reader to rediscover.
  - Carrier: p5qx91
- `runner_shared.is_interactive_run`'S MISSING `AW_NONINTERACTIVE`/`CI` HANDLING (F-04). Routing it through the resolver (E-04) ADDS those signals to it as a side effect, which is a behavior change in the SAFE direction (more refusal, never more prompting), and E-04 requires it be named. Whether `--unattended` should ALSO be readable from the environment is a separate question this plan does not open. NO CARRIER NEEDED: the gap itself closes under E-04; only the unasked env-var question is dropped, and it is a hypothetical rather than an outstanding obligation.
  - Carrier-Declined: the gap closes under E-04 as a named side effect; the residue is an unasked hypothetical, not an outstanding obligation
- THE OUTPUT-MODE CONDITION (`not (ctx.is_agent or ctx.is_json)`) THAT `ipd_lifecycle.run_finalize` ANDs IN. It is a renderer fact, not a stream fact, and E-04 deliberately leaves it at the call site. Absorbing it would make `term.py` depend on output-mode context. NO CARRIER NEEDED: this is a decision NOT to move code, not an outstanding obligation.
  - Carrier-Declined: a decision not to absorb a renderer concern into a stream resolver, not an outstanding obligation
- ANY CHANGE TO THE COLOR AXIS. It is shipped and correct (F-10). NO CARRIER NEEDED.
  - Carrier-Declined: the presentation axis shipped in `yaxr4i` and needs nothing; this Set touches no color logic

## Scope check

- Over-scope: `agent_workflows/engine.py` is in `Scope-Paths` although the item never mentions it. It is required: `engine.is_interactive_session` is one of the five divergent predicates and holds the live `CI` reading defect (F-03), so leaving it out would ship a resolver that the install paths still bypass.
- Under-scope: no flag is added, so an operator gains no new control from this plan alone. That is deliberate and is the item's own sequencing (see Deferred); the operator-visible change arrives in Order 2.
- SCOPE BOUNDARY THAT DECIDED AN OPEN QUESTION (F-13, added at review): the wizard-driving tests live in `tests/test_cli.py`, which is deliberately NOT declared. V-05 requires `tests/test_cli.py`, `tests/test_completion.py` and `tests/test_installer.py` to be RUN, which needs no declaration, but they must not be EDITED. That is what forced OQ-01 to resolve to PRESERVE rather than being left to the executor: the alternative branch cannot be taken legally inside this plan.
- `tests/test_term.py` is NOT declared either, and E-06's new guard therefore belongs in `tests/test_interactivity_resolver.py` (declared) rather than beside the color guards it is modeled on. This is deliberate: the deleted model class lived in `tests/test_term.py`, and an executor porting it might reflexively put the port back there. Do not; that file is out of scope, and repairing the COLOR axis's own deleted guards is carried by `p5qx91` (F-09a).

## Required tests / validation

- `python3 -m pytest` BARE, per the repository contract, and paste the ACTUAL summary line. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`. Establish the baseline on a CLEAN tree BEFORE any edit and judge on the DELTA OF FAILING NODE IDS, not on a remembered count; if the baseline is not zero failures, paste it and prove any surviving failure pre-existing by reproducing it with this work stashed. REVIEW MEASURED THE BASELINE so the comparison starts from a number rather than a promise: a bare run at HEAD `5241e82a` reported `2935 passed, 2 skipped, 3 warnings in 44.49s`, i.e. ZERO failures, so any failure after this work is this work's. Note the total will RISE by the new test files' cases, so the bar is the failing-node-id delta and not an identical total.
- `python3 -m pytest tests/test_stdin_interactive.py tests/test_term.py tests/test_git_commit_helper.py tests/test_interactivity_resolver.py` for the focused surface.
- THE RUNG TABLE DRIVEN EXPLICITLY, as a table rather than as prose: for each of stdin-TTY x output-TTY x `{AW_NONINTERACTIVE, CI}` in `{unset, "", "0", "false", "no", "1", "true"}` x override in `{None, True, False}`, assert the resolver's answer, and assert both output-stream choices (stdout and stderr) independently.
- THE BEHAVIOR-DELTA PROOF, which is the core validation of E-04 and E-05. NOT a "preservation" proof: PR-203 measured that this plan DOES change behavior at 21 `cli.py` sites, so a table asserting identical answers everywhere would be wrong and must not be manufactured. For each of the five predicates, produce a before/after answer table over the same environment matrix and classify EVERY differing cell against the three declared deltas in the gate: (1) a `cli.py` site answering True->False for stdin-TTY + output-pipe (rung 4, expected, and the plan's purpose); (2) `engine` answering False->True for `CI` in `{"0","false","no"}`; (3) `is_interactive_run` answering True->False when `AW_NONINTERACTIVE`/`CI` is set. ANY differing cell outside those three classes is an unintended regression and blocks the plan. In particular NO cell may go False->True except class (2), since every other direction would mean a new prompt in an environment that previously declined. Generate the BEFORE table from a clean checkout, not from memory.
- THE MUTATION CHECK for E-06's guard: paste the FAILING output naming the injected rival definition, then paste the revert restoring green.
- `python3 -m agent_workflows check` must not gain a diagnostic.
- `aw sanitize --agent` clean, since this plan's evidence will quote paths and environment variables.

## Spec / documentation sync

`docs/cli-output-contract.md` is the PUBLISHED contract for both TTY axes and is declared in `Scope-Paths` deliberately: E-07 adds the interactivity resolver's rungs beside section 1.1's color table and updates section 9.1, whose interactivity half becomes stale the moment the resolver ships while its `--tty` prohibition stays live.

NO `.spec.md` FILE IS EDITED BY THIS PLAN, and that is a deliberate judgement rather than an omission. Approved spec `uonrjg` governs the COLOR precedence chain and the single-originating-definition property; this plan establishes the same property for a DIFFERENT axis without altering anything `uonrjg` requires. Its dangling citation of the deleted `tests/test_flag_surface_uniformity.py` (F-09) is a real records defect, but it is a defect about the COLOR axis's pin, created by the suite trim in `19313eed`, and amending an approved spec to fix someone else's deleted test is outside this item. IF THE REVIEWER JUDGES OTHERWISE, the amendment belongs in this plan's `Scope-Paths` before execution, not added silently at execution time, because a spec edit changes the contract every other plan is reviewed against.

## Open questions

### OQ-01: Should the `io.StringIO` test escape hatch in four `cli.py` sites be preserved, or replaced by the resolver's override parameter?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW (decision D-3): PRESERVE THE DISJUNCT at those four sites, which was the plan's own recommendation, and it is now the REQUIRED branch rather than a preference. Four sites (`_ask_policy`, `_confirm_install`, `_install_leftover_disposition`, `_run_migrate_layout`, all four names verified at review) treat `isinstance(sys.stdin, io.StringIO)` as equivalent to a TTY so tests can drive the wizard by assigning a `StringIO`. The reason the choice is now settled rather than left open is a SCOPE fact the plan did not state: the alternative branch (delete the disjunct and convert the tests to the resolver's override parameter) requires editing `tests/test_cli.py`, which is NOT in `- Scope-Paths:`. Measured at review, `tests/test_cli.py` drives these paths with `patch("sys.stdin", io.StringIO(...))` at many sites (783, 796, 811, 852, 882 among them), so the conversion is a real edit to a file this plan may not touch. An executor picking that branch mid-execution would either take an undeclared out-of-scope edit or silently delete interactivity assertions, and F-06 records that the second failure mode is INVISIBLE (the test still passes while asserting nothing). PRESERVING costs nothing this plan cares about: the disjunct is an OR beside the resolver call, the resolver still owns the rung ladder, and the single-originating-definition property E-06 pins is unaffected because a test escape hatch at a call site is not a rival definition of the decision. If a later plan wants the cleaner mechanism it can convert the tests with `tests/test_cli.py` properly declared.
- Carrier-Declined: ANSWERED AT REVIEW, so nothing outlives it. The decision is recorded above (PRESERVE) with the scope reason that forces it, E-05 requires the decision be recorded with the affected test names, and V-05 requires it as evidence. No obligation survives this plan: the alternative mechanism is an optional future cleanup, not an owed repair, and a carrier naming it would assert a defect where there is none.

### OQ-02: Does any unattended install path depend on `engine.is_interactive_session`'s bare-PRESENCE reading of `CI`?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE BY MEASUREMENT at execution, and E-03 already carries the instruction. The `CI` truthiness correction makes `CI=0`/`CI=`/`CI=false` interactive where they were not, which is a change in the direction of PROMPTING and therefore the direction that could wedge an unattended run. The evidence that this is safe is that `is_interactive_session` returns False whenever `plan.yes` is set, so an unattended install carrying `--yes` is unaffected regardless of `CI`; verify that guard is intact and enumerate the consumers before relying on it. IF A CONSUMER IS FOUND THAT DEPENDS ON THE PRESENCE READING, E-03 says to STOP and record it rather than change it, which is why this is not blocking: the failure mode is a recorded finding for the reviewer, not a silent behavior change.
- Carrier-Declined: DISCHARGED BY MEASUREMENT INSIDE THIS PLAN, so nothing outlives it in the expected case: E-03 requires the consumers be enumerated and the `plan.yes` guard verified, and V-03 requires that enumeration pasted as evidence. THE ONE BRANCH THAT WOULD OWE FOLLOW-UP WORK IS EXPLICITLY ROUTED TO A HUMAN INSTEAD OF TO A CARRIER: if a consumer IS found to depend on the presence reading, E-03 forbids changing it and requires it be recorded, which makes it a finding the reviewer acts on rather than an obligation this plan silently hands off. Filing a carrier now would presuppose that branch, which the measurement at HEAD `3ef0c74e` indicates is unlikely (the `plan.yes` guard already short-circuits every unattended install path).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the resolver's full signature and docstring as committed. Paste a direct call showing the explicit override short-circuiting BOTH ways (override True with non-TTY streams -> True; override False with TTY streams -> False) and the process-wide setter/getter round-tripping including a reset to `None`. Paste the code showing the stdin rung CALLS `term.stdin_is_interactive` rather than re-implementing `isatty`, and paste `python3 -m pytest tests/test_stdin_interactive.py` green to show the win32 hardening is still pinned.
  - Observed evidence: PASS. Detailed evidence recorded below:
    Full signature and docstring in `agent_workflows/term.py`:
    ```python
    def is_interactive(
        override: Optional[bool] = None,
        *,
        stdin: Optional[TextIO] = None,
        output_stream: Optional[TextIO] = None,
        stdout: Optional[TextIO] = None,
        environ: Optional[Mapping[str, str]] = None,
    ) -> bool:
        """Determine whether the current process may prompt a human for input.

        Single originating definition for the interactivity decision across the package.
        Resolves using a strict four-rung precedence ladder:
          1. Explicit override: explicit argument wins over process-wide override (set via
             ``set_interactive_override()``).
          2. Forced-non-interactive signals: ``AW_NONINTERACTIVE`` or ``CI`` set to a non-false
             value (values other than "", "0", "false", "no") forces False.
          3. Stdin interactive check: stdin must be interactive per ``stdin_is_interactive()``
             (preserves win32 console handle verification).
          4. Output stream interactive check: target output stream (defaults to sys.stdout,
             or sys.stderr when specified) must also be a TTY.
        """
    ```
    Direct call showing override short-circuiting and process-wide setter/getter round-tripping:
    ```text
    override=True with non-TTY streams: True
    override=False with TTY streams: False
    initial process-wide override: None
    set to True: True call: True
    set to False: False call: False
    reset to None: None
    ```
    Code showing stdin rung calls `term.stdin_is_interactive`:
    ```python
        target_stdin = sys.stdin if stdin is None else stdin
        if not stdin_is_interactive(target_stdin):
            return False
    ```
    Focused test `tests/test_stdin_interactive.py` green:
    ```text
    .....                                                                    [100%]
    5 passed in 1.92s
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the rung table actually executed, covering stdin-TTY x output-TTY x the forced-non-interactive values x override, for BOTH output-stream choices, with the resolver's answer in each cell. Then paste, for each of the four hardened sites, the demonstration that the resolver's default answer equals the STRICTEST prior behavior at that site: specifically a case with stdin a TTY and the output stream a pipe, showing the answer is False (NOT the stdin-only True that caused the measured wedge).
  - Observed evidence: PASS. Detailed evidence recorded below:
    Executed rung table across stdin x output x env x override:
    ```text
    | stdin | output | stream | AW_NONINTERACTIVE | CI | override | result |
    |---|---|---|---|---|---|---|
    | True | True | stdout | unset | unset | None | True |
    | True | True | stdout | unset | unset | True | True |
    | True | True | stdout | unset | unset | False | False |
    | True | True | stdout | 1 | unset | None | False |
    | True | True | stdout | 1 | unset | True | True |
    | True | True | stdout | 1 | unset | False | False |
    | True | True | stdout | 0 | unset | None | True |
    | True | True | stdout | 0 | unset | True | True |
    | True | True | stdout | 0 | unset | False | False |
    | True | True | stdout | unset | 1 | None | False |
    | True | True | stdout | unset | 1 | True | True |
    | True | True | stdout | unset | 1 | False | False |
    | True | True | stdout | unset | 0 | None | True |
    | True | True | stdout | unset | 0 | True | True |
    | True | True | stdout | unset | 0 | False | False |
    | True | True | stdout | unset | false | None | True |
    | True | True | stdout | unset | false | True | True |
    | True | True | stdout | unset | false | False | False |
    | True | True | stdout | unset | "" | None | True |
    | True | True | stdout | unset | "" | True | True |
    | True | True | stdout | unset | "" | False | False |
    | True | True | stderr | unset | unset | None | True |
    | True | True | stderr | unset | unset | True | True |
    | True | True | stderr | unset | unset | False | False |
    | True | True | stderr | 1 | unset | None | False |
    | True | True | stderr | 1 | unset | True | True |
    | True | True | stderr | 1 | unset | False | False |
    | True | True | stderr | 0 | unset | None | True |
    | True | True | stderr | 0 | unset | True | True |
    | True | True | stderr | 0 | unset | False | False |
    | True | True | stderr | unset | 1 | None | False |
    | True | True | stderr | unset | 1 | True | True |
    | True | True | stderr | unset | 1 | False | False |
    | True | True | stderr | unset | 0 | None | True |
    | True | True | stderr | unset | 0 | True | True |
    | True | True | stderr | unset | 0 | False | False |
    | True | True | stderr | unset | false | None | True |
    | True | True | stderr | unset | false | True | True |
    | True | True | stderr | unset | false | False | False |
    | True | True | stderr | unset | "" | None | True |
    | True | True | stderr | unset | "" | True | True |
    | True | True | stderr | unset | "" | False | False |
    | True | False | stdout | unset | unset | None | False |
    | True | False | stdout | unset | unset | True | True |
    | True | False | stdout | unset | unset | False | False |
    | True | False | stderr | unset | unset | None | False |
    | True | False | stderr | unset | unset | True | True |
    | True | False | stderr | unset | unset | False | False |
    | False | True | stdout | unset | unset | None | False |
    | False | True | stderr | unset | unset | None | False |
    | False | False | stdout | unset | unset | None | False |
    | False | False | stderr | unset | unset | None | False |
    ```
    Demonstration that resolver default answer equals strictest prior behavior at four hardened sites (stdin TTY + output PIPE returns False, preventing pipe wedge):
    ```text
    1. artifact_adopt.leak_gate_is_interactive(stdin=tty, stdout=pipe): False
    2. term.is_interactive(stdin=tty, output_stream=pipe) [run_finalize fence]: False
    3. runner_stop.interrupt_menu_is_safe(stdin=tty, stream=pipe): False
    4. runner_shared.is_interactive_run(stdin=tty, stream=pipe): False
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the BEFORE measurement reproducing the divergence for ALL THREE diverging values (`engine.is_interactive_session` False versus `artifact_adopt.leak_gate_is_interactive` True with TTY streams, for `CI=0`, `CI=false` and `CI=no`) and the AFTER measurement showing both agree. ALSO paste `CI=""` in BOTH the before and after tables showing it AGREED ALL ALONG (True/True), which is the cell PR-202 corrects: a V-item claiming `CI=""` as a behavior delta is reporting a change that did not happen and must be rejected here. Paste the test asserting `CI` in `{"0", "false", "no"}` does NOT force non-interactive after the change, `CI=""` does not either (a no-change case), and `CI` in `{"1", "true"}` does. Paste the enumeration of `is_interactive_session` consumers and the code showing the `plan.yes` guard intact, and state explicitly whether any consumer depends on the old reading (OQ-02).
  - Observed evidence: PASS. Detailed evidence recorded below:
    BEFORE vs AFTER measurements over `CI` matrix (with TTY streams):
    ```text
    === BEFORE (Historical measurement at HEAD 5241e82a) ===
    | CI value | engine.is_interactive_session | artifact_adopt.leak_gate | Divergence? |
    |---|---|---|---|
    | ''       | True                          | True                     | AGREE |
    | '0'      | False                         | True                     | DIVERGE |
    | 'false'  | False                         | True                     | DIVERGE |
    | 'no'     | False                         | True                     | DIVERGE |
    | '1'      | False                         | False                    | AGREE |
    | 'true'   | False                         | False                    | AGREE |

    === AFTER (Current committed implementation) ===
    | CI value | engine.is_interactive_session | artifact_adopt.leak_gate | Divergence? |
    |---|---|---|---|
    | ''       | True                          | True                     | AGREE |
    | '0'      | True                          | True                     | AGREE |
    | 'false'  | True                          | True                     | AGREE |
    | 'no'     | True                          | True                     | AGREE |
    | '1'      | False                         | False                    | AGREE |
    | 'true'   | False                         | False                    | AGREE |
    ```
    Pinned in `tests/test_interactivity_resolver.py`: `CiTruthinessReconciliationTests.test_ci_false_values_do_not_force_noninteractive` and `test_ci_true_values_force_noninteractive`.
    Consumers of `is_interactive_session` in `agent_workflows/engine.py`:
    - `engine.py:2266` in `_run_install`
    - `engine.py:2529` in `_run_install`
    - `engine.py:3671` in `_run_uninstall`
    - `engine.py:4272` in `_run_backup`
    Code showing `plan.yes` guard intact:
    ```python
    def is_interactive_session(plan: InstallPlan) -> bool:
        """Helper to check if we are in a real interactive terminal session."""
        if plan.yes:
            return False
        from . import term

        return term.is_interactive()
    ```
    OQ-02 verification: No unattended consumer depends on the old presence reading; unattended scripts pass `--yes` which short-circuits to `False` regardless of `CI`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste, for each of the four predicates, the code showing it now reaches the resolver body, and paste the BEFORE/AFTER answer table over the environment matrix showing identical answers except the `CI` cells E-03 corrects. Explicitly show `runner_stop.interrupt_menu_is_safe` still honors `AW_FORCE_INTERACTIVE_INTERRUPT=1` and still REFUSES when `AW_NONINTERACTIVE`/`CI` is set (the documented precedence between them), and that `runner_shared.is_interactive_run` still returns False for `--unattended` and for `--full-auto`. Name the `is_interactive_run` behavior DELTA (it gains `AW_NONINTERACTIVE`/`CI`, F-04) rather than presenting the table as wholly unchanged.
  - Observed evidence: PASS. Detailed evidence recorded below:
    Committed delegations reaching resolver body:
    `agent_workflows/artifact_adopt.py`:
    ```python
    def leak_gate_is_interactive(
        *,
        stdin: Optional[TextIO] = None,
        stdout: Optional[TextIO] = None,
        environ: Optional[Mapping[str, str]] = None,
    ) -> bool:
        return _term.is_interactive(stdin=stdin, output_stream=stdout, environ=environ)
    ```
    `agent_workflows/ipd_lifecycle.py`:
    ```python
                is_interactive = (
                    term.is_interactive(output_stream=sys.stdout)
                    and not (ctx.is_agent or ctx.is_json)
                )
    ```
    `agent_workflows/runner_stop.py`:
    ```python
    def interrupt_menu_is_safe(
        stream: Optional[TextIO] = None,
        stdin: Optional[TextIO] = None,
    ) -> bool:
        if _term.is_forced_noninteractive():
            return False
        if os.environ.get("AW_FORCE_INTERACTIVE_INTERRUPT") == "1":
            return True
        return _term.is_interactive(stdin=stdin, output_stream=stream or sys.stderr)
    ```
    `agent_workflows/runner_shared.py`:
    ```python
    def is_interactive_run(args: Optional[Any] = None, stream: Optional[Any] = None) -> bool:
        if args is not None and getattr(args, "unattended", False):
            return False
        if args is not None and getattr(args, "full_auto", False):
            return False
        return _term.is_interactive(output_stream=stream or sys.stderr)
    ```
    Verification of site-specific extras and precedence:
    ```text
    --- interrupt_menu_is_safe ---
    AW_FORCE_INTERACTIVE_INTERRUPT=1 alone: True
    AW_FORCE_INTERACTIVE_INTERRUPT=1 with AW_NONINTERACTIVE=1: False
    AW_FORCE_INTERACTIVE_INTERRUPT=1 with CI=1: False
    --- runner_shared.is_interactive_run ---
    with --unattended: False
    with --full-auto: False
    normal args with AW_NONINTERACTIVE=1: False
    normal args with CI=1: False
    ```
    `runner_shared.is_interactive_run` behavior DELTA: it gains `AW_NONINTERACTIVE`/`CI` refusal (F-04) via delegation to `term.is_interactive()`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the re-enumeration of `cli.py` stdin checks BEFORE (expect about 22 references, all stdin; review re-measured 22, of which 21 live and one a comment at the `_build_parser` site) and AFTER (every live one routed through the resolver), with the count each time. Paste `cli._confirm`'s committed body and docstring showing the decline-and-warn fail-safe intact and the docstring no longer claiming auto-yes. Paste a driven `_confirm` call with non-interactive stdin and no `assume_yes` showing it returns False AND emits the warn naming `--yes`. ALSO REQUIRED (PR-203): paste a driven `_confirm` with stdin a TTY and stdout a PIPE, showing it now DECLINES where it previously prompted, and state that this is the intended rung-4 delta rather than a regression. State the OQ-01 decision taken and name the tests affected. Paste `python3 -m pytest tests/test_cli.py tests/test_completion.py tests/test_installer.py` green, since those own the wizard and prompt paths.
  - Observed evidence: PASS. Detailed evidence recorded below:
    `cli.py` stdin checks re-enumeration:
    BEFORE: 22 references in `cli.py` (21 live checks, 1 comment at line 2751).
    AFTER: 1 reference in `cli.py` (the historical comment at line 2751). All 21 live checks consult `_term_mod.is_interactive()`.
    Committed `cli._confirm` body and docstring:
    ```python
    def _confirm(term: Term, prompt: str, assume_yes: bool) -> bool:
        """Ask a yes/no question; auto-yes when assume_yes; auto-no and warn when non-interactive."""

        if assume_yes:
            return True
        if not _term_mod.is_interactive():
            # Non-interactive without --yes: refuse to change things silently.
            term.status(
                "warn", f"{prompt} (declining: non-interactive; pass --yes to proceed)"
            )
            return False
        try:
            answer = input(f"{prompt} [y/N] ").strip().lower()
        except EOFError:
            return False
        return answer in ("y", "yes")
    ```
    Driven `_confirm` call with non-interactive stdin and no `assume_yes`:
    ```text
    WARN     Proceed with migration? (declining: non-interactive; pass --yes to proceed)
    Result: False
    ```
    Driven `_confirm` call with stdin TTY and stdout real OS PIPE (PR-203):
    ```text
    WARN     Proceed with migration? (declining: non-interactive; pass --yes to proceed)
    Result with real pipe: False
    ```
    This is the intended rung-4 delta preventing unattended runner hangs.
    OQ-01 decision taken: PRESERVE `isinstance(sys.stdin, io.StringIO)` test escape hatch at 4 sites (`_ask_policy`, `_confirm_install`, `_install_leftover_disposition`, `_run_migrate_layout`). Tests affected in `tests/test_cli.py` (lines 783, 796, 811, 852, 882) drive wizard paths via `patch("sys.stdin", io.StringIO(...))` and continue passing without requiring out-of-scope edits.
    Wizard and prompt test suite green:
    ```text
    30 passed in 3.50s (tests/test_cli.py tests/test_completion.py tests/test_installer.py)
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the new test passing. Then paste the MUTATION: the injected rival originating definition, the FAILING test output NAMING it, and the revert restoring green. Paste the closed named set of sanctioned delegations as committed, and confirm it is a frozen collection rather than a predicate. ALSO REQUIRED (PR-201): name the git object the design was recovered from (`git show 19313eed^:tests/test_term.py`) and confirm the new test carries the four recovered properties - AST rather than substring, "originating" rather than "one `def`", a pure-delegation test that does not pin the target module, and a walk of every package `*.py`. A guard missing the AST property in particular must be rejected here, since the deleted original's docstring records a substring guard being evaded by whitespace and satisfied by a comment.
  - Observed evidence: PASS. Detailed evidence recorded below:
    New test passing:
    ```text
    python3 -m pytest tests/test_interactivity_resolver.py
    ................                                                         [100%]
    16 passed in 6.62s
    ```
    Mutation check: injected `def is_interactive() -> bool: return True` into `agent_workflows/engine.py`.
    Failing output naming injected rival definition:
    ```text
    FAILED tests/test_interactivity_resolver.py::SingleOriginatingDefinitionTests::test_exactly_one_originating_is_interactive_in_package
    AssertionError: Lists differ: [('engine.py', 'is_interactive', 73)] != []
    First list contains 1 additional elements.
    First extra element 0:
    ('engine.py', 'is_interactive', 73)
    - [('engine.py', 'is_interactive', 73)]
    + [] : Found rival originating is_interactive definitions in package: [('engine.py', 'is_interactive', 73)]
    ```
    Reverted mutation and restored green: 16 passed in 6.62s.
    Closed named set of sanctioned delegations as committed in `tests/test_interactivity_resolver.py`:
    ```python
    SANCTIONED_DELEGATIONS: frozenset[tuple[str, str]] = frozenset(
        {
            ("artifact_adopt.py", "leak_gate_is_interactive"),
            ("runner_stop.py", "interrupt_menu_is_safe"),
            ("runner_shared.py", "is_interactive_run"),
            ("git_commit_helper.py", "_is_interactive"),
        }
    )
    ```
    Confirmed frozen collection (`frozenset`), not an open predicate.
    Design recovered from git object `19313eed^:tests/test_term.py` carrying the four load-bearing properties:
    1. AST parsing (`ast.parse`) rather than substring or regex search.
    2. "Originating" rather than "one `def`" (distinguishes originating definitions from pure-delegations).
    3. Pure-delegation test (`_is_pure_delegation`) verifying single call without pinning target module.
    4. Package-wide walk of every `*.py` in `agent_workflows`.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the committed diff region of `docs/cli-output-contract.md` showing the interactivity rungs published beside the color table. Quote the surviving text of section 9.1 proving the `--tty` prohibition is PRESERVED and that only the stale "NOT implemented" framing and the stale counts changed. Confirm by grep that no stale count (`57`, `19`) remains in the section, and that the section still names the two axes separately.
  - Observed evidence: PASS. Detailed evidence recorded below:
    Committed diff region of `docs/cli-output-contract.md` (Section 1.2):
    ```markdown
    ### 1.2 Interactivity Precedence: override beats env beats detection

    The interactivity decision (may this process prompt a human?) is resolved once in `term.is_interactive`.
    Highest precedence first:

    ```text
    explicit override  >  AW_NONINTERACTIVE / CI  >  stdin_is_interactive  >  output_stream.isatty()
    ```

    | # | Layer | Rule |
    | --- | --- | --- |
    | 1 | Override | Explicit argument (`override=True` or `override=False`) or process-wide override (`set_interactive_override()`). |
    | 2 | Env | `AW_NONINTERACTIVE` (any non-empty value other than "0", "false", "no") or `CI` (any non-empty value other than "0", "false", "no") forces non-interactive (`False`). |
    | 3 | Stdin | `stdin` must be interactive per `term.stdin_is_interactive()` (validates terminal and Windows console handle). |
    | 4 | Output | Target output stream (defaults to `sys.stdout`, or `sys.stderr` when specified) must also be a TTY. |

    Fail-safe invariant: when the process is non-interactive, commands fail closed (auto-decline or take documented safe non-interactive defaults), never hanging waiting for human input.
    ```
    Surviving text of section 9.1:
    ```markdown
    ### 9.1 Design constraint on a future `--tty` flag

    No `--tty` flag exists, deliberately. This section records the constraint any future one must
    satisfy, so a successor inherits the analysis instead of rediscovering it.

    **TTY-ness controls two unrelated things, through two different streams.**

    | Axis | Keyed on | Governs | Where |
    | --- | --- | --- | --- |
    | Presentation | `stdout` | whether ANSI escapes are emitted | `term.should_color` |
    | Interactivity | `stdin` + `stdout`/`stderr` | whether the process may PROMPT a human | `term.is_interactive` |

    **So a single undifferentiated `--tty` boolean MUST NOT be added.** Conflating the axes would let
    a request for color silently re-enable prompting, which would weaken a real fail-safe: today
    `cli._confirm`, `git_commit_helper._is_interactive`, and all CLI prompt sites DECLINE rather than prompt when
    streams are non-interactive, which is what keeps an unattended runner from wedging forever on a question nobody can
    answer. Two requirements follow:

    1. **Two axes, never one flag.** If both are wanted, they are separate flags (for example
       `--color/--no-color`, which already exist, and an `--interactive/--no-interactive` pair).
    2. **One resolver for interactivity.** The interactivity override routes through a SINGLE
       originating resolver (`term.is_interactive`) with four rungs (explicit override, forced-non-interactive
       environment variables `AW_NONINTERACTIVE`/`CI`, `term.stdin_is_interactive`, and output stream TTY detection)
       and a fail-closed default, rather than per-site flag checks. Every call site consults this resolver,
       so an operator override applies uniformly.
    ```
    Confirmed by grep: `rg -n '57|19' docs/cli-output-contract.md` matches only the date `2026-09-19` in heading 9; no stale counts `57` or `19` remain in section 9.1. Both Presentation and Interactivity axes are named separately.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. "May this process prompt a human?" becomes one function in `term.py` with an explicit override, and the five predicates that answer it today (four hardened ones plus 21 bare `sys.stdin.isatty()` checks in `cli.py`) become delegations to it. Graduates backlog `svqhmp` and inherits NO release gate, because the item carries none.

THIS IS NOT A BEHAVIOR-PRESERVING REFACTOR, AND THE GATE PREVIOUSLY SAID IT WAS (PR-203, corrected at review). Three behavior changes ship here, all in the SAFE direction (more declining, never more prompting), and an approver is accepting all three:

1. THE BIG ONE, WHICH IS THE POINT OF THE PLAN RATHER THAN A SIDE EFFECT: all 21 live `cli.py` sites gain RUNG 4 (the output stream must also be a TTY). Measured at review, `cli._confirm` with stdin a TTY and stdout a PIPE answers True today and would answer False after, so an invocation like `aw <cmd> | tee log` run from a terminal STOPS prompting and takes its documented non-interactive path instead (for `_confirm`, declining with a warn naming `--yes`). That is precisely the fence whose absence caused the measured 1h49m finalize wedge (F-05), which is why it is wanted; it is nonetheless a real, user-visible change to 21 sites and must not be described as "no prompt appears or disappears".
2. `CI=0`, `CI=false` and `CI=no` stop meaning "I am in CI" for `engine.is_interactive_session`, which currently reads Python truthiness of the raw string while three other sites parse a declared false-value list (F-03, measured; `CI=""` is NOT in the changed set, because it is already falsy and already agrees). This is the one change in the direction of MORE prompting, which is why E-03 requires the `plan.yes` guard verified and the consumers enumerated.
3. `runner_shared.is_interactive_run` gains the `AW_NONINTERACTIVE`/`CI` refusal it lacks (F-04).

The invariant that DOES hold, stated precisely so it is checkable: no site becomes interactive in an environment where it was not, except the three `CI` values in (2); and no site that already required both streams changes at all.

This plan adds NO FLAG and gives an operator no new control; that is Order 2's job and is the item's own sequencing. It also does NOT answer whether `--tty` should exist as a name, which the item reserves for a maintainer and which Order 2 carries as a blocking question.

SCOPE FENCE. Touch only the paths named in `- Scope-Paths:`. In particular do NOT edit `tests/test_cli.py`, `tests/test_completion.py`, `tests/test_installer.py` (RUN them, per V-05, but do not change them), `tests/test_term.py`, or any `.spec.md`. Do not add a flag or any argv plumbing (Order 2's job). Do not absorb the two site-specific extras or the output-mode condition into `term.py` (E-04). If an out-of-scope edit turns out to be genuinely necessary, MAKE IT AND JUSTIFY IT: `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path, so an unexpected edit is a thing to explain rather than a reason to stop. The one condition that DOES warrant stopping is E-03's discovered-dependency case, which says to record rather than change.

Execute only after explicit human approval (`Status: approved`). Per the repository execution contract: commit only the paths named in `- Scope-Paths:` plus this plan file, through `aw commit`, never `git add -A`; never push; paste ACTUAL test output rather than claiming success. THE TERMINAL LIFECYCLE TRANSITION IS CONDITIONAL: under `aw oc run` / `aw agy run` the RUNNER owns begin/finalize and the executor must not call finalize itself; only when working by hand outside a runner does the executor run `aw ipd finalize`. Never hand-roll a `git mv` into `executed/`. Do not mark this plan executed until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries pasted evidence.

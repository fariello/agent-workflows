# IPD: Route every interactivity decision through one resolver with an explicit override

- Date: 2026-09-28
- Kind: child
- Concern: The INTERACTIVITY axis (may this process PROMPT a human?) has no single originating definition, so the package answers the same question five incompatible ways and cannot be given an operator override without the answer differing per command. Measured at HEAD `3ef0c74e`: 59 `isatty` references package-wide across 17 files, 22 of them in `cli.py` and every one of those a BARE `sys.stdin.isatty()`. Four hardened predicates exist and DISAGREE with the bare check and with each other: `artifact_adopt.leak_gate_is_interactive` and the local `_is_tty` fence in `ipd_lifecycle.run_finalize` both require stdin AND stdout to be a TTY and honor `AW_NONINTERACTIVE`/`CI`; `runner_stop.interrupt_menu_is_safe` requires stdin AND stderr plus an `AW_FORCE_INTERACTIVE_INTERRUPT` escape; `runner_shared.is_interactive_run` requires stdin AND stderr and honors `--unattended`/`--full-auto` but NOT `AW_NONINTERACTIVE`/`CI`; and `engine.is_interactive_session` reads `CI` by bare PRESENCE while the other three parse truthiness. That last pair is a measured live divergence, not a theoretical one: with `CI=0` set, `engine.is_interactive_session` answers False while `artifact_adopt.leak_gate_is_interactive` answers True on the same streams. This is the "how the two axes drift apart" failure `docs/cli-output-contract.md` section 9.1 predicts, already realized WITHIN the interactivity axis alone.
- Scope: Establish ONE originating interactivity resolver with an explicit override parameter, generalizing the shape of `git_commit_helper._is_interactive`, and route the existing hardened predicates and the bare `cli.py` stdin checks through it. IN: the resolver, its documented layered contract, the reconciliation of the five divergent predicates, the `CI` truthiness divergence, and tests pinning the single-originating-definition property. OUT: the `--interactive`/`--no-interactive` FLAG PAIR and any argv plumbing, which are Order 2's whole job; no prompt gains or loses a prompt for an unchanged environment.
- Scope-Paths: agent_workflows/term.py, agent_workflows/cli.py, agent_workflows/engine.py, agent_workflows/artifact_adopt.py, agent_workflows/ipd_lifecycle.py, agent_workflows/runner_stop.py, agent_workflows/runner_shared.py, agent_workflows/git_commit_helper.py, docs/cli-output-contract.md, tests/test_stdin_interactive.py, tests/test_interactivity_resolver.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Backlog: svqhmp
- Set: svqhmp
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: da9n1s

## Workflow history

- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `svqhmp`, which graduated the Deferred section of executed plan `yaxr4i` (ttyflags Order 01). GATE NOTE: item `svqhmp` carries NO `- Blocks-Release:`, so this plan inherits none; its `- Work-Kind: feature` is not in the release-gating set either, so no gate is invented.
  THE ITEM'S ANALYSIS RE-MEASURED AT HEAD `3ef0c74e` AND IT IS RIGHT ABOUT THE SHAPE BUT ITS COUNTS HAVE MOVED. The item says "57 `isatty` references package-wide at 2026-09-19, 19 in `cli.py`"; measured now, 59 package-wide across 17 files and 22 in `cli.py`. All 22 `cli.py` sites are stdin (INTERACTIVITY) and every one is a bare `sys.stdin.isatty()` with no resolver, so the item's central claim (a per-site flag check is the wrong shape) holds and is if anything understated.
  THE ITEM UNDERSTATES THE PROBLEM IN ONE IMPORTANT WAY, AND THAT CHANGED THIS PLAN'S SHAPE. The item frames the work as adding an override to a currently-uniform detection. It is not uniform: FIVE predicates already disagree, and one disagreement is LIVE rather than latent. `engine.is_interactive_session` tests `os.environ.get("CI")` by bare PRESENCE while three other sites parse truthiness against `("", "0", "false", "no")`, so `CI=0` (a plausible "I am not in CI" setting) makes `engine` non-interactive while `artifact_adopt.leak_gate_is_interactive` stays interactive. MEASURED by execution, both called with TTY streams and `CI=0`: `engine.is_interactive_session` -> False, `artifact_adopt.leak_gate_is_interactive` -> True. So E-03 reconciles an existing defect rather than merely refactoring.
  THE SPLIT INTO TWO ORDERS IS DELIBERATE AND IS THE ITEM'S OWN SEQUENCING. The item says the remaining work is "an `--interactive`/`--no-interactive` pair routed through ONE resolver that every call site already consults". The resolver must exist and every call site must already consult it BEFORE a flag can be routed through it, otherwise the flag is silently inert at whichever site was missed, which is exactly the per-command inconsistency `yaxr4i` existed to remove. Order 1 is therefore a behavior-preserving refactor plus one reconciled divergence; Order 2 adds the operator surface.
  THE FAIL-SAFE THIS MUST NOT WEAKEN IS REAL AND IS NAMED IN THE CODE. `ipd_lifecycle.run_finalize`'s fence records that `stdin.isatty()` alone as consent "wedged a real finalize for 1h49m holding its run lock"; `runner_stop.interrupt_menu_is_safe` records that its own site is "STRICTLY MORE DANGEROUS" because it runs inside a signal handler with no timeout. So the resolver's default must be the STRICTEST existing behavior at each site, never the loosest, and E-02 states that as a property rather than a hope.
  ONE GUARD THE ITEM COULD NOT HAVE KNOWN IS GONE. `yaxr4i` shipped `tests/test_flag_surface_uniformity.py` as "the durable deliverable", and commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) DELETED it along with `tests/test_output_contract.py` and `tests/test_output_mode.py`. Approved spec `uonrjg` still cites `tests/test_flag_surface_uniformity.py` by name as the pin for the published precedence chain, so that citation is now dangling. This is recorded as F-09 and carried to Order 2, which needs that walk; it is NOT silently fixed here.

## Goal

Make "may this process prompt a human?" have exactly one answer in this package, computed in one place, with an explicit override parameter so a later flag can be honored everywhere at once. The user-visible payoff is that an unattended runner's non-interactive fail-safe becomes uniform instead of per-site; the durable payoff is that the interactivity axis gets the single-originating-definition property the color axis already has, which is the precondition for Order 2's flag.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the resolver

- [ ] E-01 Add the resolver to `agent_workflows/term.py`, beside the existing `term.stdin_is_interactive`, as the SINGLE ORIGINATING DEFINITION of the interactivity decision. Shape it on `git_commit_helper._is_interactive` (an explicit override parameter that short-circuits, falling back to detection), which `docs/cli-output-contract.md` section 9.1 names as "the shape to generalize", and on `term.should_color`, which is the in-repo precedent for a resolver carrying both an explicit-argument override and a process-wide one. MIRROR `should_color`'S TWO-LEVEL OVERRIDE deliberately: an explicit argument beats a process-wide value set once per invocation, because Order 2's flag cannot be threaded to 22 `cli.py` call sites individually. `should_color`'s own comment records why the process-wide value is a module global and NOT an environment variable, and the reason is STRONGER here: this package spawns nested `aw` invocations, and an inherited `AW_INTERACTIVE` would tell a child it may prompt when its stdout is a pipe, which is the exact wedge `ipd_lifecycle`'s fence exists to prevent.
  DO NOT DELETE OR BYPASS `term.stdin_is_interactive`. It owns a win32 `GetConsoleMode` probe whose absence is a measured Windows CI defect (its docstring records that a NUL-redirected stdin reports `isatty()` True, which let `aw specs set --status approved` through without `--by-human`), and `tests/test_stdin_interactive.py` pins it. The new resolver must CALL it for the stdin rung rather than re-implementing `isatty`, so the win32 hardening is inherited by every site at once.
  - Depends on: none
  - Expected outcome: one new resolver in `term.py` with an explicit override parameter plus process-wide setter/getter, calling `stdin_is_interactive` for its stdin rung; no call site changed yet, so the suite is green with the resolver present but unused.
  - Execution state: pending

- [ ] E-02 Define the resolver's LAYERED CONTRACT and make its default the STRICTEST of the existing behaviors, not the loosest. The four hardened predicates agree on three rungs and differ only in which output stream they demand, so the contract is: (1) an explicit override wins; (2) a forced-non-interactive signal (`AW_NONINTERACTIVE`/`CI`) wins over detection; (3) stdin must be interactive per `stdin_is_interactive`; (4) the OUTPUT stream must also be a TTY, with WHICH stream a parameter (`stdout` for the finalize/adopt fence, `stderr` for the runner ones) rather than a fifth hardcoded policy.
  RUNG 4 IS NOT OPTIONAL AND IS THE WHOLE REASON THIS IS NOT A ONE-LINE `isatty` WRAPPER. Both `ipd_lifecycle.run_finalize`'s fence and `runner_stop.interrupt_menu_is_safe` record the same measured incident in their own comments: a parent spawns a child with stdout/stderr PIPED but stdin INHERITED, so a stdin-only check sees the operator's terminal, writes a prompt into a pipe nobody reads, and blocks forever. A resolver defaulting to stdin-only would silently REGRESS all four hardened sites to the shape that caused a 1h49m wedge while holding a run lock.
  NON-INTERACTIVE MUST STAY FAIL-CLOSED, stated as a property because it is what makes this safe to apply broadly: the automatic decision when the answer is "not interactive" is to REFUSE or take the documented default, which is recoverable, never to hang, which is not. `artifact_adopt.leak_gate_is_interactive` states this in exactly those terms and is the wording to reuse.
  - Depends on: E-01
  - Expected outcome: the resolver's docstring states the four rungs and names the output-stream parameter; a test table drives every rung including both output-stream choices and shows the answer matches the strictest prior behavior in each case.
  - Execution state: pending

### Task group 2: reconcile the divergent predicates

- [ ] E-03 Fix the `CI` TRUTHINESS DIVERGENCE, which is a live defect and not a cleanup. `engine.is_interactive_session` tests `os.environ.get("CI")` by bare PRESENCE, so ANY value including `0` and the empty string forces non-interactive, while `artifact_adopt.leak_gate_is_interactive`, `ipd_lifecycle.run_finalize`'s fence and `runner_stop.interrupt_menu_is_safe` all parse truthiness against `("", "0", "false", "no")`. MEASURED at HEAD `3ef0c74e` with TTY streams and `CI=0`: `engine.is_interactive_session` -> False, `leak_gate_is_interactive` -> True. Adopt the TRUTHINESS reading as canonical inside the resolver, because it is the majority behavior (three sites to one), it is the one whose intent matches the variable's meaning, and the presence reading makes `CI=0` mean "I am in CI".
  THIS CHANGES BEHAVIOR FOR ONE ENVIRONMENT AND THAT MUST BE STATED, NOT ABSORBED SILENTLY: with `CI=0` or `CI=` set, `engine`'s install paths become interactive where they previously were not. That is strictly the intended reading, and the direction is toward prompting, so verify the install paths that consume `is_interactive_session` still have their own `plan.yes` guard (they do: `is_interactive_session` returns False when `plan.yes`) and confirm no unattended install path depends on the presence reading. IF ANY DOES, STOP and record it rather than changing it; a discovered dependency is a finding for the reviewer, not a thing to fix in passing.
  - Depends on: E-02
  - Expected outcome: one truthiness predicate consumed by every site; a test pinning `CI=0`, `CI=`, `CI=false`, `CI=no` as NOT forcing non-interactive and `CI=1`/`CI=true` as forcing it; the `engine` behavior delta named explicitly with the `plan.yes` guard shown intact.
  - Execution state: pending

- [ ] E-04 Route the four HARDENED predicates through the resolver, keeping each one's public name and signature as a sanctioned thin delegation, exactly as `runner_shared.should_color` delegates to `term.should_color`. The four: `artifact_adopt.leak_gate_is_interactive` (stdin+stdout), the local `_is_tty` fence inside `ipd_lifecycle.run_finalize` (stdin+stdout), `runner_stop.interrupt_menu_is_safe` (stdin+stderr, plus its `AW_FORCE_INTERACTIVE_INTERRUPT` escape), and `runner_shared.is_interactive_run` (stdin+stderr, plus `--unattended`/`--full-auto`).
  KEEP THE TWO SITE-SPECIFIC EXTRAS AT THEIR SITES, do not absorb them into the resolver. `AW_FORCE_INTERACTIVE_INTERRUPT` is documented as bypassing the stream conditions but NOT the forced-non-interactive signals, and `--unattended`/`--full-auto` is an operator DECLARATION read off a runner namespace that `term.py` must not learn about. Each stays a wrapper concern; the resolver owns only the four general rungs. Absorbing them would make `term.py` import runner concepts and would give every call site an override nobody asked for.
  `ipd_lifecycle.run_finalize` ALSO ANDs IN `not (ctx.is_agent or ctx.is_json)`, which is an OUTPUT-MODE condition and not an interactivity one. LEAVE IT AT THE CALL SITE for the same reason: a machine-output caller must not be prompted, but that is a fact about the renderer, not about the streams.
  - Depends on: E-03
  - Expected outcome: all four predicates reach the resolver body; each retains its name, signature and site-specific extra; the behavior of each is unchanged for every environment except the `CI` reading E-03 deliberately corrects.
  - Execution state: pending

- [ ] E-05 Route the BARE `cli.py` STDIN CHECKS through the resolver. There are 22 `isatty` references in `cli.py` at HEAD `3ef0c74e` and ALL of them are stdin; 21 are live checks and one (inside `_build_parser`) is a comment. RE-ENUMERATE AT EXECUTION TIME rather than trusting this count: the item measured 19 and this plan measures 22, so the set is moving.
  THREE SPELLINGS EXIST AND THE DIFFERENCE MATTERS. Most sites are a bare `sys.stdin.isatty()`; several (`_ask_policy`, `_confirm_install`, `_install_leftover_disposition`, `_run_migrate_layout`) are `(hasattr(sys.stdin, "isatty") and sys.stdin.isatty()) or isinstance(sys.stdin, io.StringIO)`. THE `io.StringIO` DISJUNCT IS A TEST ESCAPE HATCH, not a production condition, and removing it would break tests that drive the wizard by assigning a `StringIO` to `sys.stdin`. Either preserve it at those sites or give the resolver's override parameter the job and convert those tests to use it; EITHER IS ACCEPTABLE but the choice must be recorded, because silently deleting the disjunct turns interactive wizard tests into non-interactive ones that still pass while asserting nothing.
  `cli._confirm` IS THE HEADLINE SITE and its fail-safe must survive byte-for-byte in behavior: with no `assume_yes` and a non-interactive stdin it emits a `warn` naming `--yes` and returns False. Its docstring currently says "auto-yes when assume_yes or non-interactive stdin", which CONTRADICTS its own body (non-interactive is auto-NO). Correct the docstring in the same change; leaving it would move a false claim into the newly-canonical path.
  - Depends on: E-04
  - Expected outcome: every live stdin check in `cli.py` consults the resolver; the `io.StringIO` decision is recorded; `_confirm`'s decline-and-warn behavior and every `_confirm` caller's outcome are unchanged; `_confirm`'s docstring no longer contradicts its body.
  - Execution state: pending

### Task group 3: pin the property and publish the contract

- [ ] E-06 Add the SINGLE-ORIGINATING-DEFINITION test for interactivity, modeled on `tests/test_term.py::OneOriginatingDefinitionTests`, which already enforces this for `should_color` and is cited by approved spec `uonrjg` as the property a depth resolver must extend. Assert that no second ORIGINATING definition of the interactivity decision exists in the package: a site may delegate, but may not re-implement the rung ladder.
  THE GUARD MUST BE ABLE TO FAIL, so mutation-check it: add a second module-local predicate that re-implements the rungs, show the test FAILS and NAMES it, then revert. A guard that cannot fail proves nothing, and this is the same discipline `yaxr4i` E-08 applied to its exemption list.
  DECLARE THE PERMITTED DELEGATIONS AS A CLOSED NAMED SET, not a predicate like "skip anything containing the word interactive". `yaxr4i` E-08 records why: a predicate silently absorbs the next site, which is precisely the regrowth the test exists to stop.
  - Depends on: E-05
  - Expected outcome: a test that fails when a rival originating definition appears, with the mutation demonstrated and reverted, and a closed named set of sanctioned delegations.
  - Execution state: pending

- [ ] E-07 Publish the interactivity contract in `docs/cli-output-contract.md` beside section 1.1's color precedence table and section 9.1's two-axis constraint, so the two axes are documented symmetrically. Section 9.1 currently records the interactivity axis only as a CONSTRAINT on unwritten work ("~57 `isatty` references package-wide, 19 in `cli.py`"); replace that with the shipped resolver, its four rungs, and its fail-closed default.
  DO NOT DELETE SECTION 9.1's PROHIBITION. Its core ruling, that a single undifferentiated `--tty` boolean MUST NOT be added, is still live and is still the reason this Set has two Orders; only the "NOT implemented" framing of the interactivity half becomes stale. Its stale COUNTS should be corrected to the measured 59/22 or, better, replaced by a statement of the property so the number cannot rot again.
  - Depends on: E-06
  - Expected outcome: the published contract documents both axes symmetrically, with the interactivity resolver's rungs stated, section 9.1's `--tty` prohibition preserved, and its stale counts corrected or de-numbered.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The COLOR axis is the template to copy and it is already correct: `term.should_color` is the single originating definition, carries an explicit `override=` argument PLUS a process-wide `_COLOR_OVERRIDE`, and documents a flag-beats-env-beats-detection ladder. Approved spec `uonrjg` names that single-originating-definition property as the one a new resolver must extend rather than rival.
- `should_color`'s own comment explains why the process-wide override is a module global and NOT an environment variable: this package spawns nested `aw` invocations and an env var would be INHERITED. That reasoning applies verbatim to interactivity and is why E-01 copies the mechanism.
- `cli.main` restores the color override in a `finally`, and its docstring records a measured `pytest-xdist` flake (a `SystemExit` from `--help` left the override set for the rest of the process). ANY process-wide interactivity override needs the same treatment in the same place; this is a known trap with a known fix, not a new risk.
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
| F-03 | THE `CI` DIVERGENCE IS LIVE, NOT LATENT, and is the one behavior defect in this plan. `engine.is_interactive_session` reads `CI` by bare PRESENCE; three other sites parse truthiness against `("", "0", "false", "no")`. MEASURED with TTY streams and `CI=0`: `engine.is_interactive_session` -> False, `artifact_adopt.leak_gate_is_interactive` -> True, `runner_stop.interrupt_menu_is_safe` -> True. | executed all three with fake TTY streams at HEAD `3ef0c74e` |
| F-04 | `runner_shared.is_interactive_run` HONORS NEITHER `AW_NONINTERACTIVE` NOR `CI`, unlike the other three hardened predicates, so a CI run of a driver command can still believe it may prompt if stdin and stderr are both TTYs. It compensates with `--unattended`/`--full-auto`, which is a flag and not an environment signal. | read `runner_shared.is_interactive_run` |
| F-05 | RUNG 4 IS JUSTIFIED BY A MEASURED INCIDENT, recorded independently in two code comments: a stdin-only check let a finalize prompt write into a pipe and block for 1h49m while holding its run lock, leaving the plan `approved` in `pending/` while the run reported `complete`. `runner_stop` records its own site as strictly more dangerous still, being inside a signal handler with `readline()` and no timeout. | `ipd_lifecycle.run_finalize`'s ttywedge comment; `runner_stop.interrupt_menu_is_safe` docstring |
| F-06 | THE `cli.py` SITES HAVE THREE SPELLINGS, and one carries an `isinstance(sys.stdin, io.StringIO)` TEST ESCAPE HATCH (`_ask_policy`, `_confirm_install`, `_install_leftover_disposition`, `_run_migrate_layout`). Deleting that disjunct silently converts interactive wizard tests into non-interactive ones that still pass. | read the four bodies; `rg -n isatty agent_workflows/cli.py` |
| F-07 | `cli._confirm`'s DOCSTRING CONTRADICTS ITS BODY: it says "auto-yes when assume_yes or non-interactive stdin", while the body returns False (auto-NO) and emits a warn naming `--yes` when stdin is not a TTY. The body is the correct behavior and the fail-safe this Set must preserve. | read `cli._confirm` |
| F-08 | NEITHER FLAG NAME COLLIDES, so Order 2 has a clean surface: walking the built parser tree finds `--interactive`, `--no-interactive`, `--non-interactive`, `--tty` and `--no-tty` declared on ZERO of 283 subcommands. Note `--non-interactive` and `--no-interactive` DO appear in the package as strings, but only inside command lines built for THIRD-PARTY hosts (`host_capability_registry`, `benchmark_runners`), never as `aw`'s own flags. | parser-tree walk plus `rg -n` for each spelling at HEAD `3ef0c74e` |
| F-09 | THE UNIFORMITY GUARD `yaxr4i` CALLED "THE DURABLE DELIVERABLE" IS GONE. Commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) deleted `tests/test_flag_surface_uniformity.py` (460 lines), `tests/test_output_contract.py` and `tests/test_output_mode.py`. Approved spec `uonrjg` still cites `tests/test_flag_surface_uniformity.py` BY NAME as a pin for the published precedence chain, so that citation now dangles. Order 2 needs that parser walk and must decide whether to restore or re-home it. | `git show 19313eed --stat`; `git cat-file -e main:tests/test_flag_surface_uniformity.py` fails; `rg -n test_flag_surface_uniformity .aw/records/specs/approved/` |
| F-10 | THE PRESENTATION HALF IS GENUINELY DONE, as the item says, so this Set touches no color logic: `--color`/`--no-color` are declared on the shared `presentation` parent, consumed pre-parse for the 28 forwarded leaves, and published process-wide. Only `__complete` legitimately lacks them. | parser-tree walk: `--no-color` missing on 29 of 283, of which 28 are forwarded leaves that consume it in `_dispatch` |
| F-11 | NOTHING ELSE COVERS THIS ITEM: no pending plan and no spec implements an interactivity resolver or either flag. Spec `uonrjg` touches the axis only to state the COLOR precedence chain. | `rg -li 'interactiv|isatty' .aw/records/specs/` and a read of every pending plan's Concern at HEAD `3ef0c74e` |

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
- RESTORING THE DELETED `tests/test_flag_surface_uniformity.py` (F-09). Order 2 needs the parser walk and must decide restore-versus-re-home there; doing it here would put a flag-surface test in a plan that adds no flag. The dangling spec `uonrjg` citation is a separate records defect that neither Order should fix in passing. CARRIER: Order 2 (`bmf32u`) for the walk.
  - Carrier: bmf32u
- `runner_shared.is_interactive_run`'S MISSING `AW_NONINTERACTIVE`/`CI` HANDLING (F-04). Routing it through the resolver (E-04) ADDS those signals to it as a side effect, which is a behavior change in the SAFE direction (more refusal, never more prompting), and E-04 requires it be named. Whether `--unattended` should ALSO be readable from the environment is a separate question this plan does not open. NO CARRIER NEEDED: the gap itself closes under E-04; only the unasked env-var question is dropped, and it is a hypothetical rather than an outstanding obligation.
  - Carrier-Declined: the gap closes under E-04 as a named side effect; the residue is an unasked hypothetical, not an outstanding obligation
- THE OUTPUT-MODE CONDITION (`not (ctx.is_agent or ctx.is_json)`) THAT `ipd_lifecycle.run_finalize` ANDs IN. It is a renderer fact, not a stream fact, and E-04 deliberately leaves it at the call site. Absorbing it would make `term.py` depend on output-mode context. NO CARRIER NEEDED: this is a decision NOT to move code, not an outstanding obligation.
  - Carrier-Declined: a decision not to absorb a renderer concern into a stream resolver, not an outstanding obligation
- ANY CHANGE TO THE COLOR AXIS. It is shipped and correct (F-10). NO CARRIER NEEDED.
  - Carrier-Declined: the presentation axis shipped in `yaxr4i` and needs nothing; this Set touches no color logic

## Scope check

- Over-scope: `agent_workflows/engine.py` is in `Scope-Paths` although the item never mentions it. It is required: `engine.is_interactive_session` is one of the five divergent predicates and holds the live `CI` presence-versus-truthiness defect (F-03), so leaving it out would ship a resolver that the install paths still bypass.
- Under-scope: no flag is added, so an operator gains no new control from this plan alone. That is deliberate and is the item's own sequencing (see Deferred); the operator-visible change arrives in Order 2.

## Required tests / validation

- `python3 -m pytest` BARE, per the repository contract, and paste the ACTUAL summary line. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`. Establish the baseline on a CLEAN tree BEFORE any edit and judge on the DELTA OF FAILING NODE IDS, not on a remembered count; if the baseline is not zero failures, paste it and prove any surviving failure pre-existing by reproducing it with this work stashed.
- `python3 -m pytest tests/test_stdin_interactive.py tests/test_term.py tests/test_git_commit_helper.py tests/test_interactivity_resolver.py` for the focused surface.
- THE RUNG TABLE DRIVEN EXPLICITLY, as a table rather than as prose: for each of stdin-TTY x output-TTY x `{AW_NONINTERACTIVE, CI}` in `{unset, "", "0", "false", "no", "1", "true"}` x override in `{None, True, False}`, assert the resolver's answer, and assert both output-stream choices (stdout and stderr) independently.
- THE BEHAVIOR-PRESERVATION PROOF, which is the core validation of E-04 and E-05: for each of the five predicates, a before/after answer table over the same environment matrix, showing IDENTICAL answers except for the `CI` cells E-03 deliberately corrects. Generate the BEFORE table from a clean checkout, not from memory.
- THE MUTATION CHECK for E-06's guard: paste the FAILING output naming the injected rival definition, then paste the revert restoring green.
- `python3 -m agent_workflows check` must not gain a diagnostic.
- `aw sanitize --agent` clean, since this plan's evidence will quote paths and environment variables.

## Spec / documentation sync

`docs/cli-output-contract.md` is the PUBLISHED contract for both TTY axes and is declared in `Scope-Paths` deliberately: E-07 adds the interactivity resolver's rungs beside section 1.1's color table and updates section 9.1, whose interactivity half becomes stale the moment the resolver ships while its `--tty` prohibition stays live.

NO `.spec.md` FILE IS EDITED BY THIS PLAN, and that is a deliberate judgement rather than an omission. Approved spec `uonrjg` governs the COLOR precedence chain and the single-originating-definition property; this plan establishes the same property for a DIFFERENT axis without altering anything `uonrjg` requires. Its dangling citation of the deleted `tests/test_flag_surface_uniformity.py` (F-09) is a real records defect, but it is a defect about the COLOR axis's pin, created by the suite trim in `19313eed`, and amending an approved spec to fix someone else's deleted test is outside this item. IF THE REVIEWER JUDGES OTHERWISE, the amendment belongs in this plan's `Scope-Paths` before execution, not added silently at execution time, because a spec edit changes the contract every other plan is reviewed against.

## Open questions

### OQ-01: Should the `io.StringIO` test escape hatch in four `cli.py` sites be preserved, or replaced by the resolver's override parameter?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE AT EXECUTION from repository evidence, recorded so the choice is deliberate rather than accidental. Four sites (`_ask_policy`, `_confirm_install`, `_install_leftover_disposition`, `_run_migrate_layout`) treat `isinstance(sys.stdin, io.StringIO)` as equivalent to a TTY so tests can drive the wizard by assigning a `StringIO`. The RECOMMENDED approach is to PRESERVE the disjunct at those four sites initially, because the override parameter is the cleaner mechanism but converting the tests is a separate change whose failure mode is silent: a test that loses its interactivity assertion still PASSES while asserting nothing (F-06). Whichever is chosen must be recorded with the affected test names. This is not blocking because either answer satisfies the plan's property.
- Carrier-Declined: DISCHARGED BY THIS PLAN'S OWN EXECUTION, so no durable carrier can legitimately hold it and one would double-file the work. This is an IMPLEMENTATION CHOICE the executing turn must make and RECORD, not an obligation outliving execution: E-05 requires the decision be taken and the affected test names recorded, and V-05 requires that decision be stated as evidence, so by the time this plan could reach `executed` the question is necessarily answered in-tree. The `open` status is honest (nobody has chosen yet) while the obligation terminates with this plan.

### OQ-02: Does any unattended install path depend on `engine.is_interactive_session`'s bare-PRESENCE reading of `CI`?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE BY MEASUREMENT at execution, and E-03 already carries the instruction. The `CI` truthiness correction makes `CI=0`/`CI=`/`CI=false` interactive where they were not, which is a change in the direction of PROMPTING and therefore the direction that could wedge an unattended run. The evidence that this is safe is that `is_interactive_session` returns False whenever `plan.yes` is set, so an unattended install carrying `--yes` is unaffected regardless of `CI`; verify that guard is intact and enumerate the consumers before relying on it. IF A CONSUMER IS FOUND THAT DEPENDS ON THE PRESENCE READING, E-03 says to STOP and record it rather than change it, which is why this is not blocking: the failure mode is a recorded finding for the reviewer, not a silent behavior change.
- Carrier-Declined: DISCHARGED BY MEASUREMENT INSIDE THIS PLAN, so nothing outlives it in the expected case: E-03 requires the consumers be enumerated and the `plan.yes` guard verified, and V-03 requires that enumeration pasted as evidence. THE ONE BRANCH THAT WOULD OWE FOLLOW-UP WORK IS EXPLICITLY ROUTED TO A HUMAN INSTEAD OF TO A CARRIER: if a consumer IS found to depend on the presence reading, E-03 forbids changing it and requires it be recorded, which makes it a finding the reviewer acts on rather than an obligation this plan silently hands off. Filing a carrier now would presuppose that branch, which the measurement at HEAD `3ef0c74e` indicates is unlikely (the `plan.yes` guard already short-circuits every unattended install path).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the resolver's full signature and docstring as committed. Paste a direct call showing the explicit override short-circuiting BOTH ways (override True with non-TTY streams -> True; override False with TTY streams -> False) and the process-wide setter/getter round-tripping including a reset to `None`. Paste the code showing the stdin rung CALLS `term.stdin_is_interactive` rather than re-implementing `isatty`, and paste `python3 -m pytest tests/test_stdin_interactive.py` green to show the win32 hardening is still pinned.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the rung table actually executed, covering stdin-TTY x output-TTY x the forced-non-interactive values x override, for BOTH output-stream choices, with the resolver's answer in each cell. Then paste, for each of the four hardened sites, the demonstration that the resolver's default answer equals the STRICTEST prior behavior at that site: specifically a case with stdin a TTY and the output stream a pipe, showing the answer is False (NOT the stdin-only True that caused the measured wedge).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the BEFORE measurement reproducing the divergence (`engine.is_interactive_session` False versus `artifact_adopt.leak_gate_is_interactive` True with `CI=0` and TTY streams) and the AFTER measurement showing both agree. Paste the test asserting `CI` in `{"", "0", "false", "no"}` does NOT force non-interactive and `CI` in `{"1", "true"}` does. Paste the enumeration of `is_interactive_session` consumers and the code showing the `plan.yes` guard intact, and state explicitly whether any consumer depends on the presence reading (OQ-02).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste, for each of the four predicates, the code showing it now reaches the resolver body, and paste the BEFORE/AFTER answer table over the environment matrix showing identical answers except the `CI` cells E-03 corrects. Explicitly show `runner_stop.interrupt_menu_is_safe` still honors `AW_FORCE_INTERACTIVE_INTERRUPT=1` and still REFUSES when `AW_NONINTERACTIVE`/`CI` is set (the documented precedence between them), and that `runner_shared.is_interactive_run` still returns False for `--unattended` and for `--full-auto`. Name the `is_interactive_run` behavior DELTA (it gains `AW_NONINTERACTIVE`/`CI`, F-04) rather than presenting the table as wholly unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the re-enumeration of `cli.py` stdin checks BEFORE (expect about 22 references, all stdin) and AFTER (every live one routed through the resolver), with the count each time. Paste `cli._confirm`'s committed body and docstring showing the decline-and-warn fail-safe intact and the docstring no longer claiming auto-yes. Paste a driven `_confirm` call with non-interactive stdin and no `assume_yes` showing it returns False AND emits the warn naming `--yes`. State the OQ-01 decision taken and name the tests affected. Paste `python3 -m pytest tests/test_cli.py tests/test_completion.py tests/test_installer.py` green, since those own the wizard and prompt paths.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the new test passing. Then paste the MUTATION: the injected rival originating definition, the FAILING test output NAMING it, and the revert restoring green. Paste the closed named set of sanctioned delegations as committed, and confirm it is a frozen collection rather than a predicate.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the committed diff region of `docs/cli-output-contract.md` showing the interactivity rungs published beside the color table. Quote the surviving text of section 9.1 proving the `--tty` prohibition is PRESERVED and that only the stale "NOT implemented" framing and the stale counts changed. Confirm by grep that no stale count (`57`, `19`) remains in the section, and that the section still names the two axes separately.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. "May this process prompt a human?" becomes one function in `term.py` with an explicit override, and the five predicates that answer it today (four hardened ones plus 21 bare `sys.stdin.isatty()` checks in `cli.py`) become delegations to it. No prompt appears or disappears for an unchanged environment, with ONE deliberate exception stated plainly: `CI=0`, `CI=`, `CI=false` and `CI=no` stop meaning "I am in CI" for `engine.is_interactive_session`, which currently reads that variable by bare presence while three other sites parse truthiness (F-03, measured). Two documented behaviors also become uniform as a side effect, both in the SAFE direction: `runner_shared.is_interactive_run` gains the `AW_NONINTERACTIVE`/`CI` refusal it lacks (F-04), and every `cli.py` site gains the stdin+output-stream fence whose absence caused a measured 1h49m finalize wedge (F-05). Graduates backlog `svqhmp` and inherits NO release gate, because the item carries none.

This plan adds NO FLAG and gives an operator no new control; that is Order 2's job and is the item's own sequencing. It also does NOT answer whether `--tty` should exist as a name, which the item reserves for a maintainer and which Order 2 carries as a blocking question.

Execute only after explicit human approval (`Status: approved`). Per the repository execution contract: commit only the paths named in `- Scope-Paths:` through `aw commit`, never `git add -A`; never push; paste ACTUAL test output rather than claiming success; and leave the terminal lifecycle transition to the runner, which owns begin/finalize for a managed lane. Do not mark this plan executed until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries pasted evidence.

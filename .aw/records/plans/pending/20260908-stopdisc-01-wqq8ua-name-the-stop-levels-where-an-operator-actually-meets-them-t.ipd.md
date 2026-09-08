# IPD: Name the stop levels where an operator actually meets them: the continuity footer, the interrupt message, and the run-level help

- Date: 2026-09-08
- Kind: child
- Concern: Three operator-facing surfaces that an operator reads at exactly the moment they want a run to stop say nothing about the graceful-stop protocol. FIRST, the continuity footer (`oc_runipd.render_continuation_hint:7539`, `agy_runipd:4479`) prints captured session ids, a reuse command, and either `aw runs <run-id>` or a resume command, and mentions stopping nowhere. SECOND, the `main` KeyboardInterrupt message (`oc_runipd.py:8389-8399`) says only "Interrupted; durable run state was preserved." with no hint that a graceful level exists or how to request one. THIRD, the run-level help says nothing: I ran `aw oc run start --help` and grepped for stop, interrupt and ctrl, with zero matches.
  THE ITEM'S PREMISE IS OTHERWISE FALSE, AND THAT IS WHY THIS PLAN IS NARROW. The item says "Ctrl-C does not mention the levels exist, and the interrupt report does not say how to request one". Both halves are wrong at HEAD. All four levels ship (`LEVEL_AFTER_CALL` through `LEVEL_NOW_FORCE`, `runner_stop.py:210-215`), with no `NotImplementedError` skeleton. A full out-of-band verb ships: I ran `aw oc run stop --help` and it renders four per-level descriptions and four worked example commands. And the R16 request report ALREADY names the level, the awaited boundary and the exact escalation command: I called it and got `stop accepted: level 1 (after-call) ...; waiting for the in-flight agent turn to finish; no further item will be started; to stop harder, press Ctrl-C again (or run \`aw oc run stop <run-id> --now\`) to request level 3 (now)`. So the "state what each level does and give the exact command" ask is largely delivered, and re-delivering it would duplicate an existing surface in violation of GUIDING_PRINCIPLES P8.
  ONE FINDING GOES BEYOND DISCOVERABILITY AND IS DELIBERATELY NOT FIXED HERE. The item's stated non-goal, an interactive Ctrl-C prompt, HAS SHIPPED (`prompt_interrupt_action:1794`, wired into the live SIGINT handler at `runner_stop.py:1936-1953`), and on any TTY it BYPASSES the documented `SIGINT_LADDER` entirely, recording `LEVEL_NOW_FORCE` for two of its three choices. Spec `c4gd2h` R12 says "First SIGINT (Ctrl-C) requests level 1. Repeated SIGINT escalates 1 -> 3 -> 4". So on a terminal the shipped behavior contradicts the spec, and the item's own non-goal was overridden by code. That is a spec-conformance question and a maintainer decision, not a documentation change: it is filed as its own backlog item and this plan documents only what is true on both paths.
- Scope: Add stop-level discoverability to the three surfaces that lack it: a stopping line in the continuity footer on both hosts, a graceful-stop hint in the `main` interrupt message on both hosts, and a stopping paragraph on the run-level (`start`/`resume`) help. Text must POINT AT the existing `stop` verb rather than restating its per-level help, and must describe only behavior true on both the interactive and non-interactive paths. EXCLUDES any change to `runner_stop`'s levels, budgets, escalation, or the R16 request report; excludes adding, removing or altering the interactive Ctrl-C prompt; excludes resolving the R12 conflict that prompt creates.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_stop_triggers.py
- Item-Dependencies: none
- Status: to-review
- Set: stopdisc
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: wqq8ua
- From-Backlog: 1m3nul

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `1m3nul`, HEAVILY NARROWED because most of what it asks for already exists. The item carries no `- Blocks-Release:` so none is inherited or invented.
  THE ITEM TOLD ME TO VERIFY WHICH LEVELS SHIP BEFORE DOCUMENTING THEM, SO I DID, BY RUNNING THE CODE. All four levels are wired with no skeletons: `LEVEL_AFTER_CALL`/`AFTER_SET`/`NOW`/`NOW_FORCE` (`runner_stop.py:210-215`), budgets at `:248`, `request_stop:547`, `poll_stop:640`, and agy mirrors each. The out-of-band verb exists: `python3 -m agent_workflows oc run stop --help` exits 0 and renders four per-level descriptions plus four worked commands, and `stop` appears in the subcommand table of `oc run --help`. And I CALLED the R16 reporter directly: `render_request_accepted(LEVEL_AFTER_CALL, requester=...)` returns the level, the awaited boundary, and the exact escalation command. So three of the item's four asks are already satisfied and this plan must not rebuild them.
  WHAT ACTUALLY SURVIVES, each confirmed by reading the function and running the command: the continuity footer never mentions stopping (I read `render_continuation_hint` end to end on both hosts: sessions, a reuse command, then `aw runs <id>` or a resume command, and nothing else); the `main` KeyboardInterrupt message is two possible sentences neither of which names a level or the verb; and `aw oc run start --help` matches nothing for stop, interrupt or ctrl. Those three are this plan's whole scope.
  THE BLOCKING DISCOVERY, and the reason this plan is documentation-only rather than the "better reporting" the item envisioned. The item explicitly rejected an interactive Ctrl-C prompt on 2026-09-05, citing two reasons. That prompt has since SHIPPED (`646be41f`, a direct maintainer commit with no plan and no spec authorization that I could find). Worse, `_sigint` (`runner_stop.py:1936-1953`) computes `is_interactive` from `sys.stdin.isatty()` and, when true, SKIPS the `SIGINT_LADDER` entirely, calling the prompt and then recording `LEVEL_NOW_FORCE` for choices 1 and 2. I read the code and the test that pins it (`tests/test_interrupt_menu.py:332-355` asserts exactly this). So on a TTY the first Ctrl-C is level 4, not level 1, while spec `c4gd2h` R12 (`:106`) requires 1 then 1->3->4. That is a CORRECTNESS and spec-conformance issue, contradicting the item's own "this is a DISCOVERABILITY item, not a correctness one", and resolving it means either removing shipped maintainer-authored behavior or amending an approved spec's requirement. Neither is an agent's call, so it is filed as its own backlog item and E-01 requires this plan's text to be TRUE ON BOTH PATHS, which is what keeps it honest without pre-empting that decision.
  I ALSO CORRECTED TWO OF THE ITEM'S CITATIONS. Its `oc_runipd.py:5931` KeyboardInterrupt reference is now two distinct handlers, `:6410` in `execute_item` and `:8358` in `main`; only the second is the interrupt REPORT. And its `:5936-5941` "repeated interrupt" citation no longer describes that code: repeated-interrupt handling now lives in `prompt_interrupt_action` (`runner_stop.py:1832-1837`). Its claim that `i6015i` is "pending" is also stale: that plan is in `executed/`, so there is no adjacent pending overlap.

## Goal

Make an operator who wants to stop a run cleanly able to learn that graceful levels exist, at the three moments they are actually looking: when a run ends, when they press Ctrl-C, and when they read the run command's help, without duplicating the `stop` verb's own already-good help and without documenting behavior that a TTY does not deliver.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish what may honestly be claimed

- [ ] E-01 ESTABLISH AND WRITE DOWN THE TEXT'S TRUTH CONDITION, before writing any operator-facing sentence: every claim must hold on BOTH the interactive and non-interactive paths.
  WHY THIS IS AN E-ITEM AND NOT A NOTE. The obvious sentence to add is "press Ctrl-C to stop after the current item", and on a TTY that is FALSE: `_sigint` (`runner_stop.py:1936-1953`) bypasses `SIGINT_LADDER` when `sys.stdin.isatty()`, shows the interactive menu, and records `LEVEL_NOW_FORCE` for two of three choices. Documenting the ladder as the Ctrl-C behavior would ship a false statement to the exact operator most likely to rely on it.
  DERIVE THE CLAIM FROM THE CODE, NOT FROM THE SPEC, and state which is which. Spec R12 describes the ladder; the code implements the ladder ONLY when not on a TTY. Where they disagree, the text must describe the code, and the disagreement is recorded (see the separate backlog item) rather than papered over.
  THE SAFE, TRUE-EVERYWHERE CLAIM is the OUT-OF-BAND verb: `aw oc run stop <run-id> --after-call` behaves identically on both paths because it writes the request through `request_stop` regardless of terminal state. So the out-of-band command is what these three surfaces should point at, and it is also what the item's own "give the exact command to request one" ask means.
  RE-VERIFY BEFORE WRITING rather than trusting this plan: run `oc run stop --help`, call the R16 reporter, and read `_sigint`. `runner_stop.py` is under active change and if the interactive bypass has been removed by the time this executes, the truth condition changes and the text may then describe the ladder.
  - Depends on: none
  - Expected outcome: a written statement of what may be claimed on both paths, grounded in re-verified code rather than the spec, identifying the out-of-band command as the safe referent and recording any code/spec disagreement found.
  - Execution state: pending

### Task group 2: the three surfaces

- [ ] E-02 ADD A STOPPING LINE TO THE CONTINUITY FOOTER ON BOTH HOSTS (`oc_runipd.render_continuation_hint:7539`, `agy_runipd:4479`).
  THIS IS THE ITEM'S CLEANEST SURVIVING ASK. The footer is what an operator reads when a run ends, and it already teaches three other things (reuse a session, inspect a summary, resume this run) while saying nothing about stopping the next one.
  PUT IT WHERE IT IS USEFUL, WHICH MEANS ON THE UNFINISHED BRANCH. The footer branches on `all_success`: successes get `aw runs <run-id>`, and anything else gets a resume command. An operator who will resume a run is exactly the operator who may later want to stop one gracefully, so the resume branch is where the line earns its place. Decide whether it also belongs on the all-success branch and state why; a line printed after a fully successful run is arguably noise.
  KEEP IT TO ONE LINE PLUS THE COMMAND, matching the surrounding style ("To resume this run:" then an indented command). Do NOT restate the four levels here; the `stop` verb's help already does that well and duplicating it is exactly the P8 violation this repository forbids. Name the verb and one level, and let `--help` carry the rest.
  DO THE SAME THING TWICE, IDENTICALLY. Both hosts have this function and an operator moving between them should not meet two different phrasings. If a shared helper is the natural way to guarantee that, prefer it, but do not restructure the footer to get one.
  - Depends on: E-01
  - Expected outcome: both hosts' continuity footers name graceful stopping and give one exact out-of-band command, in the surrounding style, with identical wording across hosts; the branch placement decided and stated; the four levels NOT restated.
  - Execution state: pending

- [ ] E-03 ADD A GRACEFUL-STOP HINT TO THE `main` KeyboardInterrupt MESSAGE ON BOTH HOSTS (`oc_runipd.py:8389-8399` and the agy twin).
  THE CURRENT TEXT IS TWO SENTENCES, "Terminated without clean up; worktree and lanes left in place." or "Interrupted; durable run state was preserved.", and neither says that a gentler option existed. This is the moment an operator learns what just happened, so it is the moment to teach that next time they could have asked for level 1 instead.
  DO NOT TURN THIS INTO A PROMPT. The item is emphatic and its reasoning stands: Ctrl-C is the path taken by an operator who wants OUT, and blocking it on a question risks the unbounded wait `qyaime` documented. This is one extra sentence on the way out, nothing more.
  BE TRUTHFUL ABOUT WHAT JUST HAPPENED, which is where E-01 binds. On a TTY the interrupt likely came through the interactive menu at level 4, so a message implying the operator had just requested a graceful level would be wrong. Phrase it as what is available NEXT TIME via the out-of-band verb, which is true on both paths.
  PRESERVE THE EXIT CODES AND THE EXISTING SENTENCES. The handler returns `143` for SIGTERM and `130` otherwise, and the `just-terminate-no-cleanup` branch is a distinct message. Add to the message; change no branch, no code, no ledger call, and do not reorder `emit_shutdown_report`.
  - Depends on: E-01
  - Expected outcome: both hosts' interrupt messages gain one truthful sentence about requesting a graceful stop next time via the out-of-band verb; no prompt; exit codes 143 and 130 and all existing branches and their ordering unchanged.
  - Execution state: pending

- [ ] E-04 ADD A STOPPING PARAGRAPH TO THE RUN-LEVEL HELP, since `aw oc run start --help` currently matches nothing for stop, interrupt or ctrl (verified).
  POINT, DO NOT DUPLICATE. The `stop` verb's own help is already exemplary: four per-level descriptions and four worked commands, plus the cleanup-is-unconditional and monotonic-escalation guarantees. The run-level help needs a short pointer telling an operator that graceful stopping exists and where to read about it, not a second copy. A second copy would drift from the first, which is the real cost.
  PUT IT WHERE ARGPARSE WILL SHOW IT. Find the run parser via `build_parser` (`oc_runipd.py:7661`, `agy_runipd.py:4565`) and use the description or epilog that actually renders for `start` and `resume`. Verify by RUNNING `--help`, not by reading the argparse call: which text renders where depends on the subparser wiring.
  BOTH HOSTS, IDENTICAL WORDING, for the same reason as E-02.
  - Depends on: E-01
  - Expected outcome: `start` and `resume` help on both hosts mention graceful stopping and point at the `stop` verb, verified by running `--help`; no per-level text duplicated from the `stop` verb.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 TEST THE THREE SURFACES, asserting the text is present and that nothing behavioral moved.
  ASSERT ON RENDERED OUTPUT, NOT ON A CONSTANT. The point is that an operator SEES this, so the test must render the footer, the interrupt message and the help, and assert the text appears there. A test asserting a string constant exists proves nothing about whether it reaches a terminal.
  COVER BOTH HOSTS. Every one of these three surfaces is duplicated across `oc_runipd` and `agy_runipd`, and the wording must match. A test that asserts oc only would let agy drift, which is the failure mode this repository's shared-runner work exists to prevent.
  ASSERT NO BEHAVIOR CHANGED: the exit codes (143 for SIGTERM, 130 otherwise), the existing footer branches, and the `just-terminate-no-cleanup` message must all still be exactly as before. `tests/test_interrupt_menu.py` already drives `main` with mocks and asserts both the code and the message, so the pattern exists; do not modify that file's existing assertions, only add beside them if that is the right home.
  DO NOT ASSERT THE LADDER'S TTY BEHAVIOR either way. That is the contested question filed separately; a test here that pinned it would be taking a side on a maintainer decision.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: tests asserting the new text in the rendered footer, interrupt message and help on BOTH hosts, plus assertions that exit codes, footer branches and existing messages are unchanged; no assertion about the interactive-versus-ladder question.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ALL FOUR LEVELS SHIP AND THE `stop` VERB EXISTS. `LEVEL_AFTER_CALL`..`LEVEL_NOW_FORCE` (`runner_stop.py:210-215`), `SIGINT_LADDER` (`:1620`), `SIGTERM_LEVEL` (`:1623`), `add_stop_parser` (`:2096`), `stop_command` (`:2165`). Verified by running `oc run stop --help`.
- THE R16 REPORT IS ALREADY COMPLETE. `render_request_accepted` (`:1691`) plus `AWAITING` (`:1646`), `escalation_target` (`:1654`) and `_escalation_hint` (`:1669`) produce level, awaited boundary and escalation command. Verified by calling it. Do not rebuild it.
- LEVEL 2 IS REACHABLE ONLY OUT OF BAND, deliberately: the comment at `runner_stop.py:1616-1619` states the ladder is 1->3->4 with "no free key position for a second between-turn level", and calls it "a decision, not an omission". Any text must not imply Ctrl-C can reach level 2.
- THE INTERACTIVE MENU BYPASSES THE LADDER ON A TTY (`runner_stop.py:1936-1953`), recording `LEVEL_NOW_FORCE` for two of three choices, pinned by `tests/test_interrupt_menu.py:332-355`. This is the constraint that shapes every sentence this plan writes.
- EVERY TARGET SURFACE IS DUPLICATED ACROSS HOSTS: `render_continuation_hint` (`oc_runipd.py:7539`, `agy_runipd.py:4479`), the `main` KeyboardInterrupt handler (`oc_runipd.py:8358`, `agy_runipd.py:4993`), `build_parser` (`:7661`, `:4565`). Both must change identically.
- GUIDING_PRINCIPLES P8 FORBIDS A SECOND IMPLEMENTATION of an existing surface, which here means pointing at the `stop` verb's help rather than restating its per-level text.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses).

## Findings

| Id | Severity | Location (measured at HEAD `fac69fbd`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `runner_stop.py:1936-1953`, spec `c4gd2h:106` (R12) | THE SHIPPED TTY BEHAVIOR CONTRADICTS THE SPEC. `_sigint` bypasses `SIGINT_LADDER` when `sys.stdin.isatty()`, showing the interactive menu and recording `LEVEL_NOW_FORCE` for choices 1 and 2, so an interactive operator's FIRST Ctrl-C is level 4, not level 1. R12 requires 1 then 1->3->4. Pinned by `tests/test_interrupt_menu.py:332-355`. Also: the interactive prompt was the item's explicit non-goal and shipped anyway (`646be41f`), with no plan or spec authorization found. NOT fixed here (maintainer decision); filed as its own backlog item. | source read; test read; `git log -S` |
| F-2 | N/A | `runner_stop.py:210-215`, `:2096`, `:2165` | ALL FOUR LEVELS SHIP WITH NO SKELETON, AND SO DOES THE `stop` VERB, whose `--help` renders four per-level descriptions and four worked commands. The item's core premise ("no way to learn that this is precisely level 1") is false at the verb level. | ran `oc run stop --help` (exit 0) |
| F-3 | N/A | `runner_stop.py:1691`, `:1646`, `:1654`, `:1669` | THE R16 REPORT ALREADY STATES LEVEL, BOUNDARY AND ESCALATION COMMAND. I called it: `stop accepted: level 1 (after-call) ...; waiting for the in-flight agent turn to finish; no further item will be started; to stop harder, press Ctrl-C again (or run \`aw oc run stop <run-id> --now\`) to request level 3 (now)`. So the item's "the interrupt report does not say how to request one" is false. | called `render_request_accepted` |
| F-4 | MED | `oc_runipd.py:7539-7586`, `agy_runipd.py:4479` | SURVIVES: the continuity footer mentions stopping NOWHERE. It prints session ids, a reuse command, and either `aw runs <run-id>` or a resume command. The item's cleanest remaining ask. | read the function end to end on both hosts |
| F-5 | MED | `oc_runipd.py:8389-8399` | SURVIVES: the `main` interrupt message is "Terminated without clean up; worktree and lanes left in place." or "Interrupted; durable run state was preserved." Neither names a level or the verb. | source read |
| F-6 | MED | `aw oc run start --help` | SURVIVES: the run-level help says nothing about stopping. Grepping its output for stop, interrupt and ctrl returns no match. | ran it |
| F-7 | LOW | `oc_runipd.py:7462-7465`, `render_stream.py:1656` | THE SUMMARY TABLE LABELS A COMPLETED STOP (`STOPPED (Level N: ...)` via `exit_reason`) but never advertises a POSSIBLE one. Partial coverage: the level is named after the fact, which is why the footer beside it is the better insertion point. | source read |
| F-8 | N/A | `runner_stop.py:1616-1619` | LEVEL 2 IS INTENTIONALLY UNREACHABLE BY SIGNAL, documented as "a decision, not an omission". Text must not imply Ctrl-C reaches it. | source read |
| F-9 | N/A | `.aw/records/plans/executed/...i6015i...` | THE ITEM'S "RELATED" CLAIM IS STALE: `i6015i` is EXECUTED, not pending, so there is no adjacent pending overlap. No pending plan covers this item and none carries `- From-Backlog: 1m3nul`. | file location; grep |
| F-10 | LOW | `oc_runipd.py:6410` vs `:8358` | THE ITEM'S `:5931` CITATION IS NOW TWO HANDLERS: `execute_item`'s (`:6410`) and `main`'s (`:8358`); only the latter is the interrupt REPORT. Its `:5936-5941` repeated-interrupt citation now lives in `prompt_interrupt_action` (`runner_stop.py:1832-1837`). | source read |

## Proposed changes (ordered, validatable)

1. E-01 fixes the truth condition: every claim must hold on both the interactive and non-interactive paths, which makes the out-of-band verb the safe referent.
2. E-02 adds a stopping line to the continuity footer on both hosts, in the surrounding style, without restating the levels.
3. E-03 adds one truthful sentence to the `main` interrupt message on both hosts, with no prompt and no behavior change.
4. E-04 adds a stopping pointer to the run-level help on both hosts, verified by running `--help`.
5. E-05 pins all three surfaces on both hosts and asserts exit codes, branches and existing messages unchanged.

## Deferred / out of scope (with reason)

- RESOLVING THE INTERACTIVE-PROMPT-VERSUS-LADDER CONFLICT (F-1). The sharpest thing found, and explicitly a maintainer decision: fixing it means either removing shipped maintainer-authored behavior (`646be41f`) or amending spec `c4gd2h` R12, an approved requirement. An agent may not choose between those. Filed as its own backlog item so it is tracked rather than lost, and E-01 keeps this plan's text honest in the meantime.
- ANY INTERACTIVE PROMPT ON Ctrl-C, added or removed. The item rejected adding one for reasons that still hold (Ctrl-C is the operator's way OUT; blocking it risks the `qyaime` unbounded wait). Removing the one that exists is the deferred decision above.
- REBUILDING THE R16 REQUEST REPORT (F-3). It already states level, boundary and escalation command. Touching it would duplicate a working surface (P8).
- RESTATING THE FOUR LEVELS IN THE RUN HELP OR THE FOOTER (F-2). The `stop` verb's help already does this well; a second copy would drift.
- ANY CHANGE TO LEVELS, BUDGETS, ESCALATION, POLLING, OR THE STOP-REQUEST FLAG. This plan is text-only on three surfaces.
- MAKING LEVEL 2 SIGNAL-REACHABLE (F-8). A documented decision, not an omission.
- CHANGING THE SUMMARY TABLE'S `exit_reason` (F-7). It correctly labels a completed stop; advertising a possible one belongs in the footer that prints beside it.

## Scope check

- Over-scope: none. All three declared paths are modified: both runner modules by E-02 through E-04, and the test file by E-05.
- Under-scope: stated rather than left as `none`. Deliberately, after this plan the TTY Ctrl-C path still contradicts spec R12 (F-1) and no test here pins either side of it. If E-05's tests are better housed in `tests/test_interrupt_menu.py` or a new file rather than `tests/test_runner_stop_triggers.py`, that path is outside `- Scope-Paths:` and must be declared before execution or justified at finalize; decide and state which.

## Required tests / validation

`python3 -m pytest` bare in the executing worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS rather than totals. Then the stop-related suites explicitly: `tests/test_runner_stop_triggers.py` and `tests/test_interrupt_menu.py` (joint baseline with `tests/test_statefork_dh0uno.py` measured at `72 passed`). Because this plan is text-only, the strongest validation is OPERATOR-VISIBLE output: paste the actual rendered footer, the actual interrupt message, and the actual `--help` output for both hosts, rather than asserting on constants. Also paste `aw oc run stop --help` unchanged, since a plan about stop discoverability must prove it did not disturb the one surface that was already good.

## Spec / documentation sync

NO SPEC IS AMENDED, and the reason matters. Spec `c4gd2h` owns the stop protocol, carries `- Blocks-Release: next`, and sits at `- Status: implementing`. This plan adds operator-facing TEXT on three surfaces and changes no protocol behavior, so it amends nothing. R16 ("the driver prints the level accepted, what it is waiting for, and how to escalate") is already satisfied by `render_request_accepted` and is untouched.
THE ONE PLACE A SPEC EDIT WOULD BE REQUIRED IS DELIBERATELY OUT OF SCOPE. F-1 shows the shipped TTY behavior contradicts R12, and closing that gap means either changing code the maintainer wrote or amending R12. Either would put `c4gd2h` in `- Scope-Paths:` and trigger the run-start spec-edit announcement. This plan does neither, and the separate backlog item records the choice so the conflict is not silently inherited by whoever executes this.
VERIFY BEFORE EXECUTING rather than assuming: re-read R16 and R12 and confirm the added text CONTRADICTS NEITHER. In particular do not write a sentence implying the SIGINT ladder governs an interactive terminal, which is R12's claim and not the code's behavior. If the executor concludes the text cannot be written without asserting something a spec requirement denies, STOP and report; that is the F-1 decision surfacing, not a wording problem.

## Open questions

### OQ-01: Should the footer line print on the all-success branch too?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as the RESUME BRANCH FIRST, with the all-success branch optional and stated. The footer branches on `all_success`: successes get `aw runs <run-id>` and everything else gets a resume command. An operator who will resume is the one most likely to want a graceful stop later, so that branch is where the line earns attention; after a fully successful run the same line is closer to noise, and a nudge that prints when it cannot be acted on trains readers to skip the footer. The executor may include it on both branches if the wording stays short, but must state the choice rather than letting it fall out of the code.

### OQ-02: Where do E-05's tests belong?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-05 states the requirement (rendered output, both hosts, no behavioral drift) and any placement meeting it is fine. `tests/test_runner_stop_triggers.py` is declared, but `tests/test_interrupt_menu.py` already drives `main` with mocks and asserts both exit code and message, which is exactly the harness E-03's assertion needs. Reusing it risks entangling new assertions with the tests that pin the contested interactive behavior (F-1), which is an argument for a separate file. Decide at execution, and note that a new file is a `- Scope-Paths:` change.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the written truth condition. Paste the RE-VERIFICATION performed at execution time, not this plan's claims: `oc run stop --help` output, a call to `render_request_accepted`, and the current `_sigint` source showing whether the interactive bypass still exists. State explicitly whether the ladder governs a TTY at execution time, and therefore which claims are safe to write.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the ACTUAL rendered footer from both hosts, on the resume branch and the all-success branch, showing the new line and its exact command. Paste both hosts' text side by side proving identical wording. Confirm the four levels are NOT restated. State the OQ-01 branch decision as implemented.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the ACTUAL interrupt message from both hosts for the ordinary interrupt AND the `just-terminate-no-cleanup` branch, showing the new sentence and the preserved originals. Paste the exit codes observed: 143 for SIGTERM and 130 otherwise. Paste a diff proving no branch, no ledger call, and no ordering of `emit_shutdown_report` changed. Confirm no prompt was added.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `--help` output for `start` and `resume` on BOTH hosts showing the new paragraph, obtained by RUNNING the command rather than reading the argparse source. Paste `aw oc run stop --help` proving it is unchanged. Confirm no per-level text was duplicated.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new tests and their passing output, showing assertions on RENDERED output for all three surfaces on BOTH hosts. Paste the unchanged-behavior assertions (exit codes, footer branches, existing messages). Paste `tests/test_runner_stop_triggers.py` and `tests/test_interrupt_menu.py` green (joint baseline with `tests/test_statefork_dh0uno.py` was `72 passed`). Confirm no test asserts either side of the interactive-versus-ladder question. Paste the bare full-suite summary line with the worktree baseline and a node-id comparison. State the OQ-02 placement decision.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the paths in `- Scope-Paths:` (plus a new test file if OQ-02 resolves that way, which must then be declared or justified). Do NOT change any level, budget, escalation rule, poll site, or the stop-request flag. Do NOT touch `render_request_accepted` or any part of the R16 report; it is already complete. Do NOT add, remove or alter the interactive Ctrl-C prompt, and do NOT resolve the R12 conflict (F-1): that is a maintainer decision tracked by its own backlog item. Do NOT add a prompt of any kind to the interrupt path. Do NOT restate the four levels in the footer or the run help. Do NOT make level 2 signal-reachable. Do NOT edit spec `c4gd2h`. Do NOT modify existing assertions in `tests/test_interrupt_menu.py`. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN, and this warning is not boilerplate here: `oc_runipd.py` and `agy_runipd.py` moved roughly 70 and 95 lines in a single day and are under live edit, and this backlog item's own citations were already stale by up to 480 lines. Find `render_continuation_hint`, `build_parser`, `render_run_summary_table`, `install_stop_signal_handlers`, `_sigint`, `render_request_accepted` and `prompt_interrupt_action` by name. Find the `main` interrupt handler by its "durable run state was preserved" text.

SHARED CHECKOUT WARNING: both runner modules are among the most heavily edited files in this repository and live runs may be editing them now. Confirm each target text is present as quoted before editing; if it has changed, STOP and report rather than reconciling someone else's in-flight edit.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved wqq8ua --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, backlog `1m3nul` (carried as `- From-Backlog:`) may be closed `done`: this plan delivers every surviving part of it, the rest having already shipped, and the F-1 conflict it uncovered is NOT part of that item's ask and lives on as its own item. That item carries no release gate, so none is inherited.

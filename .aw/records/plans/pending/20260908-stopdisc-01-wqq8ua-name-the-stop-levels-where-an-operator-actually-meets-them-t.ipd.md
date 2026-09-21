# IPD: Name the stop levels where an operator actually meets them: the continuity footer, the interrupt message, and the run-level help

- Date: 2026-09-08
- Kind: child
- Concern: Three operator-facing surfaces that an operator reads at exactly the moment they want a run to stop say nothing about the graceful-stop protocol. FIRST, the continuity footer (`oc_runipd.render_continuation_hint:7539`, `agy_runipd:4479`) prints captured session ids, a reuse command, and either `aw runs <run-id>` or a resume command, and mentions stopping nowhere. SECOND, the `main` KeyboardInterrupt message (`oc_runipd.py:8389-8399`) says only "Interrupted; durable run state was preserved." with no hint that a graceful level exists or how to request one. THIRD, the run-level help says nothing: I ran `aw oc run start --help` and grepped for stop, interrupt and ctrl, with zero matches.
  THE ITEM'S PREMISE IS OTHERWISE FALSE, AND THAT IS WHY THIS PLAN IS NARROW. The item says "Ctrl-C does not mention the levels exist, and the interrupt report does not say how to request one". Both halves are wrong at HEAD. All four levels ship (`LEVEL_AFTER_CALL` through `LEVEL_NOW_FORCE`, `runner_stop.py:210-215`), with no `NotImplementedError` skeleton. A full out-of-band verb ships: I ran `aw oc run stop --help` and it renders four per-level descriptions and four worked example commands. And the R16 request report ALREADY names the level, the awaited boundary and the exact escalation command: I called it and got `stop accepted: level 1 (after-call) ...; waiting for the in-flight agent turn to finish; no further item will be started; to stop harder, press Ctrl-C again (or run \`aw oc run stop <run-id> --now\`) to request level 3 (now)`. So the "state what each level does and give the exact command" ask is largely delivered, and re-delivering it would duplicate an existing surface in violation of GUIDING_PRINCIPLES P8.
  THE PLAN'S "BLOCKING DISCOVERY" HAS EXPIRED AND IS RETRACTED HERE (review, F-11/F-12/F-13). This paragraph originally said the interactive Ctrl-C prompt CONTRADICTS spec `c4gd2h` R12, called that a maintainer decision, and shaped every sentence of E-01 around documenting only what is true "on both paths". Re-measured at review, three of its four factual claims are now false and the conflict itself is RESOLVED:
    1. R12 WAS AMENDED ON THE MAINTAINER'S DECISION (2026-09-09, commit `bc2ed703`), and now describes TWO paths explicitly: R12.1 the interactive four-choice menu, R12.2 the `SIGINT_LADDER` for everything else, with the spec stating "both must reach level 1 on a first press". The shipped behavior is now the SPECIFIED behavior, so there is no conformance gap to route around and no maintainer decision pending.
    2. THE GATE IS NOT `sys.stdin.isatty()`. It is `interrupt_menu_is_safe` (`runner_stop.py:1792-1833`), which requires a TTY on BOTH streams AND the absence of `AW_NONINTERACTIVE`/`CI`, and falls back to the ladder fail-safe. The spec's R12.1 predicate matches it exactly, and the spec calls that two-stream requirement a safety fix rather than a preference.
    3. THE MENU HAS FOUR CHOICES, NOT THREE, AND CHOICE 2 REACHES LEVEL 1. Measured: choice 1 (Resume) records NOTHING and the run continues; choice 2 (Finish current item) records `LEVEL_AFTER_CALL`, i.e. level 1; choices 3 and 4 record `LEVEL_NOW_FORCE`. So the claim that the first Ctrl-C is level 4 is wrong: an operator on a terminal can reach level 1 explicitly, which is what R12 requires and what the ladder could not offer.
  WHAT THIS CHANGES FOR THE PLAN: the truth condition is no longer "avoid saying anything the TTY path does not deliver", it is "describe the two paths the spec now blesses". The out-of-band verb is still the right thing for these three surfaces to POINT AT, for the good reason that it needs no terminal and no signal at all, but the plan may now truthfully say that Ctrl-C on a terminal offers a menu whose second choice finishes the current item and stops. Backlog `4awwg4` (still `open`, `Priority: low`) is now STALE for its primary claim and should be re-read against the amended R12 rather than trusted; that re-read is not this plan's job, and this plan no longer depends on its outcome.
- Scope: Add stop-level discoverability to the three surfaces that lack it: a stopping line in the continuity footer on both hosts, a graceful-stop hint in the `main` interrupt message on both hosts, and a stopping paragraph on the run-level (`start`/`resume`) help. Text must POINT AT the existing `stop` verb rather than restating its per-level help, and must describe only behavior true on both the interactive and non-interactive paths. EXCLUDES any change to `runner_stop`'s levels, budgets, escalation, or the R16 request report; excludes adding, removing or altering the interactive Ctrl-C prompt; excludes resolving the R12 conflict that prompt creates.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_stop_triggers.py, tests/test_interrupt_menu.py, tests/test_oc_runipd.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: stopdisc
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: wqq8ua
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
- From-Backlog: 1m3nul

## Workflow history
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-10 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-201..PR-209 all FIXED, no deferrals, no open questions; Readiness go-pending-approval

- 2026-09-10 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-201..PR-209 all FIXED, no deferrals, no open questions remain; Readiness `go-pending-approval`. Reviewed at HEAD `6882f7c6`; `aw ipd lint --phase author` CONFORMED (0 findings) before semantic review and `--phase review-finalize` conformed after. DISCLOSURE: same model family as the author, so this is near-self-review; its value is in what was EXECUTED.
  THE PLAN'S NARROWING DISCIPLINE IS EXEMPLARY AND I KEPT ALL OF IT. It graduated an item most of whose asks had already shipped, and rather than rebuilding them it ran the code and cut them: I independently re-ran every one of those checks and the cuts are correct. `oc run stop --help` renders four per-level descriptions plus four worked commands (exit 0); `render_request_accepted(LEVEL_AFTER_CALL, ...)` returns the level, the awaited boundary and the exact escalation command verbatim as quoted; `SIGINT_LADDER` is `(1, 3, 4)`; `aw oc run start --help` matches nothing for stop/interrupt/ctrl on BOTH hosts; the continuity footer mentions stopping nowhere on either host; and the interrupt message is exactly the two quoted sentences at `oc_runipd.py:8409` and `agy_runipd.py:5111` with exit codes 143/130 intact. F-2 through F-10 all verified true. The three surviving surfaces are real and are the right scope.
  THE FINDING THAT MOST CHANGES THE PLAN IS THAT ITS OWN BLOCKING DISCOVERY HAS EXPIRED (PR-201, HIGH). F-1 asserts the interactive Ctrl-C prompt contradicts spec `c4gd2h` R12 and that resolving it is a pending maintainer decision, and E-01 is built entirely around not saying anything that conflict makes untrue. R12 WAS AMENDED ON THE MAINTAINER'S DECISION on 2026-09-09 (commit `bc2ed703`, one day after this plan was written) to describe TWO paths: R12.1 the interactive menu, R12.2 the ladder. The shipped behavior is now the specified behavior. So the conflict is resolved, in favor of the code, and the plan's central constraint no longer exists.
  TWO MORE OF F-1's FACTS ARE ALSO WRONG, AND BOTH WOULD HAVE PROPAGATED INTO OPERATOR-FACING TEXT (PR-202, PR-203). The gate is NOT `sys.stdin.isatty()`: it is `interrupt_menu_is_safe`, which requires a TTY on BOTH streams plus no `AW_NONINTERACTIVE`/`CI`, and whose docstring records the 1h49m finalize wedge that the one-stream predicate caused. And the menu has FOUR choices, not three, with choice 2 recording `LEVEL_AFTER_CALL`, i.e. LEVEL 1: measured directly, choice 1 records nothing and resumes, choice 2 is level 1, choices 3 and 4 are level 4. So "the first Ctrl-C is level 4, not level 1" is false, and an E-01 written to avoid claiming a gentle first press would have avoided claiming something TRUE.
  THREE MECHANICAL BLOCKERS THE EXECUTOR WOULD HAVE HIT MID-PASS. FIRST (PR-204, HIGH): four shipped tests assert `assertNotIn("resume", ...)` on the footer's all-success branch (`tests/test_oc_runipd.py:1944`, `:1963`, and the end-to-end `:230`), so a stop line containing the word "resume" on that branch breaks them; the fence forbids weakening tests, so the wording is CONSTRAINED, which OQ-01 never mentions. SECOND (PR-205, HIGH): the `resume` subparser has NO `RawDescriptionHelpFormatter` on either host (`oc_runipd.py:7905`, `agy_runipd.py:4808`), unlike `start`, so argparse reflows a multi-line paragraph onto one line; I proved this with a minimal argparse reproduction. E-04 says to verify by running `--help`, which would catch it, but not what to do, and adding the formatter is a real edit the fence should authorize. THIRD (PR-206, MEDIUM): the two footers are ALREADY not identical (`render_continuation_hint is` compares False, sources differ by 449 characters and by host label), so E-02's "identical wording" must mean the STOPPING SENTENCE, not the footer, and agy's footer has ZERO test coverage today while oc's has six tests.
  Also corrected: the full-suite baseline (`1 failed, 5958 passed`, and the named failing test PASSES with 112 tests; the real failure is the reporting-contract parity test caused by another party's gitignored tree), the joint stop-suite baseline (`74 passed`, not 72), and OQ-02 resolved from evidence (the declared `tests/test_runner_stop_triggers.py` is the correct home for the ladder-adjacent work, but the footer and interrupt-message assertions belong beside the six existing footer tests in `tests/test_oc_runipd.py`, which is a `Scope-Paths` addition the plan must declare).
- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `1m3nul`, HEAVILY NARROWED because most of what it asks for already exists. The item carries no `- Blocks-Release:` so none is inherited or invented.
  THE ITEM TOLD ME TO VERIFY WHICH LEVELS SHIP BEFORE DOCUMENTING THEM, SO I DID, BY RUNNING THE CODE. All four levels are wired with no skeletons: `LEVEL_AFTER_CALL`/`AFTER_SET`/`NOW`/`NOW_FORCE` (`runner_stop.py:210-215`), budgets at `:248`, `request_stop:547`, `poll_stop:640`, and agy mirrors each. The out-of-band verb exists: `python3 -m agent_workflows oc run stop --help` exits 0 and renders four per-level descriptions plus four worked commands, and `stop` appears in the subcommand table of `oc run --help`. And I CALLED the R16 reporter directly: `render_request_accepted(LEVEL_AFTER_CALL, requester=...)` returns the level, the awaited boundary, and the exact escalation command. So three of the item's four asks are already satisfied and this plan must not rebuild them.
  WHAT ACTUALLY SURVIVES, each confirmed by reading the function and running the command: the continuity footer never mentions stopping (I read `render_continuation_hint` end to end on both hosts: sessions, a reuse command, then `aw runs <id>` or a resume command, and nothing else); the `main` KeyboardInterrupt message is two possible sentences neither of which names a level or the verb; and `aw oc run start --help` matches nothing for stop, interrupt or ctrl. Those three are this plan's whole scope.
  THE BLOCKING DISCOVERY, and the reason this plan is documentation-only rather than the "better reporting" the item envisioned. The item explicitly rejected an interactive Ctrl-C prompt on 2026-09-05, citing two reasons. That prompt has since SHIPPED (`646be41f`, a direct maintainer commit with no plan and no spec authorization that I could find). Worse, `_sigint` (`runner_stop.py:1936-1953`) computes `is_interactive` from `sys.stdin.isatty()` and, when true, SKIPS the `SIGINT_LADDER` entirely, calling the prompt and then recording `LEVEL_NOW_FORCE` for choices 1 and 2. I read the code and the test that pins it (`tests/test_interrupt_menu.py:332-355` asserts exactly this). So on a TTY the first Ctrl-C is level 4, not level 1, while spec `c4gd2h` R12 (`:106`) requires 1 then 1->3->4. That is a CORRECTNESS and spec-conformance issue, contradicting the item's own "this is a DISCOVERABILITY item, not a correctness one", and resolving it means either removing shipped maintainer-authored behavior or amending an approved spec's requirement. Neither is an agent's call, so it is filed as its own backlog item and E-01 requires this plan's text to be TRUE ON BOTH PATHS, which is what keeps it honest without pre-empting that decision.
  I ALSO CORRECTED TWO OF THE ITEM'S CITATIONS. Its `oc_runipd.py:5931` KeyboardInterrupt reference is now two distinct handlers, `:6410` in `execute_item` and `:8358` in `main`; only the second is the interrupt REPORT. And its `:5936-5941` "repeated interrupt" citation no longer describes that code: repeated-interrupt handling now lives in `prompt_interrupt_action` (`runner_stop.py:1832-1837`). Its claim that `i6015i` is "pending" is also stale: that plan is in `executed/`, so there is no adjacent pending overlap.

## Goal

Make an operator who wants to stop a run cleanly able to learn that graceful levels exist, at the three moments they are actually looking: when a run ends, when they press Ctrl-C, and when they read the run command's help, without duplicating the `stop` verb's own already-good help and without misattributing either specified Ctrl-C path's behavior to the other.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish what may honestly be claimed

- [x] E-01 ESTABLISH AND WRITE DOWN THE TEXT'S TRUTH CONDITION, before writing any operator-facing sentence: every claim must be true of the path it describes, and must not attribute one path's behavior to the other.
  THIS ITEM'S ORIGINAL PREMISE EXPIRED AND IS REPLACED (review, F-11/F-12/F-13). It said the ladder must not be documented as the Ctrl-C behavior because a TTY bypasses it in violation of spec R12. R12 WAS AMENDED on the maintainer's decision (2026-09-09, `bc2ed703`) to specify BOTH paths, so the shipped behavior is now the specified behavior and there is no conflict to route around. Two of the old premise's facts were also simply wrong: the gate is `interrupt_menu_is_safe` (`runner_stop.py:1792-1833`), requiring a TTY on BOTH streams plus no `AW_NONINTERACTIVE`/`CI`, not a bare `stdin.isatty()`; and the menu has FOUR choices whose SECOND records `LEVEL_AFTER_CALL`, i.e. level 1, so a first Ctrl-C on a terminal CAN stop gently.
  THE TRUTH CONDITION IS THEREFORE THE TWO-PATH ONE THE SPEC NOW STATES. R12.1: with a real terminal on both streams and no `AW_NONINTERACTIVE`/`CI`, Ctrl-C prints a four-choice menu (resume; finish the current item then clean up and exit, which is level 1; clean up and exit, level 4; exit leaving a mess, level 4). R12.2: otherwise the ladder governs and the Nth press requests `SIGINT_LADDER[N-1]` = 1 -> 3 -> 4. Do NOT write a sentence that presents either path as the only one.
  THE OUT-OF-BAND VERB REMAINS THE RIGHT REFERENT, for a better reason than "it is the only safe claim": `aw oc run stop <run-id> --after-call` needs no terminal, no signal and no menu, works identically on both paths through `request_stop`, and is the ONLY way to reach level 2 at all (documented at `runner_stop.py:1616-1619` as a decision, not an omission). Point at it; do not restate the four levels (P8).
  STILL RE-VERIFY BEFORE WRITING, because `runner_stop.py` is under active change and this plan's own premise already went stale once inside two days. Run `oc run stop --help`, call `render_request_accepted`, read `interrupt_menu_is_safe` and `_sigint`, and re-read spec `c4gd2h` R12.1/R12.2. If what you find disagrees with the two-path statement above, describe the CODE and record the disagreement rather than papering over it.
  - Depends on: none
  - Expected outcome: a written statement of what may be claimed, naming both R12 paths and their gate, grounded in re-verified code AND the amended spec, identifying the out-of-band command as the referent for all three surfaces, and recording any fresh code/spec disagreement found.
  - Execution state: performed

### Task group 2: the three surfaces

- [x] E-02 ADD A STOPPING LINE TO THE CONTINUITY FOOTER ON BOTH HOSTS (`oc_runipd.render_continuation_hint:7539`, `agy_runipd:4479`).
  THIS IS THE ITEM'S CLEANEST SURVIVING ASK. The footer is what an operator reads when a run ends, and it already teaches three other things (reuse a session, inspect a summary, resume this run) while saying nothing about stopping the next one.
  PUT IT WHERE IT IS USEFUL, WHICH MEANS ON THE UNFINISHED BRANCH. The footer branches on `all_success`: successes get `aw runs <run-id>`, and anything else gets a resume command. An operator who will resume a run is exactly the operator who may later want to stop one gracefully, so the resume branch is where the line earns its place. Decide whether it also belongs on the all-success branch and state why; a line printed after a fully successful run is arguably noise.
  KEEP IT TO ONE LINE PLUS THE COMMAND, matching the surrounding style ("To resume this run:" then an indented command). Do NOT restate the four levels here; the `stop` verb's help already does that well and duplicating it is exactly the P8 violation this repository forbids. Name the verb and one level, and let `--help` carry the rest.
  THE WORDING IS CONSTRAINED BY FOUR SHIPPED ASSERTIONS, WHICH THIS ITEM DID NOT KNOW (review, F-14). On the ALL-SUCCESS branch, `tests/test_oc_runipd.py:1944` and `:1963` assert `assertNotIn("resume", hint)` and `:1959` asserts `assertNotIn("aw runs", hint)` on the incomplete branch, and the end-to-end `:230` asserts `assertNotIn("resume", result.stdout)` for a whole successful run. The gate forbids weakening existing tests, so if you place the line on the all-success branch its text must contain neither the substring `resume` nor `aw runs` beyond what that branch already prints. `To stop a future run gracefully:` plus `aw oc run stop <run-id> --after-call` satisfies both (verified: neither substring appears). Check the exact assertions before choosing wording, and if you conclude an assertion must change, STOP and report rather than editing it.
  DO THE SAME THING TWICE, WITH IDENTICAL STOPPING TEXT. Note what "identical" can and cannot mean here (F-15): the two footers are ALREADY different functions with different sources (`oc_runipd.render_continuation_hint is agy_runipd.render_continuation_hint` is False; the sources differ by 449 characters, and the rendered output legitimately differs in host label and command prefix). So require the STOPPING SENTENCE to be identical modulo the `{cmd}` prefix, not the footer. A shared helper is acceptable if it falls out naturally, but do not restructure the footer to get one, and do not add a `runner_shared` symbol that the refork guard would then need a table row for. NOTE ALSO that agy's footer has NO test coverage at all today while oc's has six tests, so E-05's agy assertions are new ground rather than a mirror.
  - Depends on: E-01
  - Expected outcome: both hosts' continuity footers name graceful stopping and give one exact out-of-band command, in the surrounding style, with the stopping sentence identical across hosts modulo the command prefix; the branch placement decided and stated; the four shipped `assertNotIn` assertions still passing UNMODIFIED; the four levels NOT restated.
  - Execution state: performed

- [x] E-03 ADD A GRACEFUL-STOP HINT TO THE `main` KeyboardInterrupt MESSAGE ON BOTH HOSTS (`oc_runipd.py:8389-8399` and the agy twin).
  THE CURRENT TEXT IS TWO SENTENCES, "Terminated without clean up; worktree and lanes left in place." or "Interrupted; durable run state was preserved.", and neither says that a gentler option existed. This is the moment an operator learns what just happened, so it is the moment to teach that next time they could have asked for level 1 instead.
  DO NOT TURN THIS INTO A PROMPT. The item is emphatic and its reasoning stands: Ctrl-C is the path taken by an operator who wants OUT, and blocking it on a question risks the unbounded wait `qyaime` documented. This is one extra sentence on the way out, nothing more.
  BE TRUTHFUL ABOUT WHAT JUST HAPPENED, which is where E-01 binds, AND NOTE THE CORRECTED FACTS. This item originally reasoned "on a TTY the interrupt likely came through the interactive menu at level 4". That is only true for menu choices 3 and 4: choice 2 records `LEVEL_AFTER_CALL` (level 1) and choice 1 resumes without recording anything, and this handler is reached only via the `clean-up-and-terminate` and `just-terminate-no-cleanup` exceptions, i.e. exactly choices 3 and 4 (or the ladder's terminal rung). So for the messages this item edits, "the operator asked to stop hard" IS accurate. Even so, phrase the addition as what is available NEXT TIME via the out-of-band verb, because that is true regardless of which path or rung produced this exit and it avoids asserting a level the message cannot know.
  PRESERVE THE EXIT CODES AND THE EXISTING SENTENCES. The handler returns `143` for SIGTERM and `130` otherwise, and the `just-terminate-no-cleanup` branch is a distinct message. Add to the message; change no branch, no code, no ledger call, and do not reorder `emit_shutdown_report`.
  - Depends on: E-01
  - Expected outcome: both hosts' interrupt messages gain one truthful sentence about requesting a graceful stop next time via the out-of-band verb; no prompt; exit codes 143 and 130 and all existing branches and their ordering unchanged.
  - Execution state: performed

- [x] E-04 ADD A STOPPING PARAGRAPH TO THE RUN-LEVEL HELP, since `aw oc run start --help` currently matches nothing for stop, interrupt or ctrl (verified).
  POINT, DO NOT DUPLICATE. The `stop` verb's own help is already exemplary: four per-level descriptions and four worked commands, plus the cleanup-is-unconditional and monotonic-escalation guarantees. The run-level help needs a short pointer telling an operator that graceful stopping exists and where to read about it, not a second copy. A second copy would drift from the first, which is the real cost.
  PUT IT WHERE ARGPARSE WILL SHOW IT. Find the run parser via `build_parser` (locate by symbol) and use the description or epilog that actually renders for `start` and `resume`. Verify by RUNNING `--help`, not by reading the argparse call: which text renders where depends on the subparser wiring.
  THE `resume` SUBPARSER WILL DESTROY YOUR PARAGRAPH UNLESS YOU FIX ITS FORMATTER, MEASURED AT REVIEW (F-16). `start` is created with `formatter_class=argparse.RawDescriptionHelpFormatter` on both hosts (`oc_runipd.py:7759-7764`, `agy_runipd.py:4680-4685`), but `resume` is NOT (`oc_runipd.py:7905-7909`, `agy_runipd.py:4808-4812`). Argparse's default formatter REFLOWS a description, so a multi-line stopping paragraph collapses onto one line with its indented command inlined; proven at review with a minimal argparse reproduction. So EITHER add `formatter_class=argparse.RawDescriptionHelpFormatter` to both hosts' `resume` parsers (a one-argument, behavior-neutral edit inside the declared files, and the option that keeps the two hosts' help consistent), OR write a single-sentence pointer with no line breaks that survives reflowing. Decide, state which, and prove it by pasting the RENDERED `resume --help`. Do not discover this at execution and silently ship a mangled paragraph.
  BOTH HOSTS, IDENTICAL WORDING, for the same reason as E-02, and note that `add_stop_parser` is ALREADY shared (`runner_stop.py:2166`, called from `oc_runipd.py:8006` and `agy_runipd.py:4874`), so the verb this text points at is genuinely one implementation on both hosts.
  - Depends on: E-01
  - Expected outcome: `start` and `resume` help on both hosts mention graceful stopping and point at the `stop` verb, verified by RUNNING `--help` and pasting it; the `resume` reflow problem resolved by a stated choice; no per-level text duplicated from the `stop` verb.
  - Execution state: performed

### Task group 3: pin it

- [x] E-05 TEST THE THREE SURFACES, asserting the text is present and that nothing behavioral moved.
  ASSERT ON RENDERED OUTPUT, NOT ON A CONSTANT. The point is that an operator SEES this, so the test must render the footer, the interrupt message and the help, and assert the text appears there. A test asserting a string constant exists proves nothing about whether it reaches a terminal.
  COVER BOTH HOSTS. Every one of these three surfaces is duplicated across `oc_runipd` and `agy_runipd`, and the wording must match. A test that asserts oc only would let agy drift, which is the failure mode this repository's shared-runner work exists to prevent.
  ASSERT NO BEHAVIOR CHANGED: the exit codes (143 for SIGTERM, 130 otherwise), the existing footer branches, and the `just-terminate-no-cleanup` message must all still be exactly as before. `tests/test_interrupt_menu.py::RunnerMainOutputOnInterruptTests` already drives `main` with mocks over BOTH modules and asserts code 130 plus the exact message text (`:328-360`), so the pattern exists; do not modify that file's existing assertions, only add beside them if that is the right home.
  THE SIX SHIPPED FOOTER TESTS ARE PART OF THE ASSERTION SET, NOT JUST CONTEXT. `tests/test_oc_runipd.py::ContinuationHintTests` (`:1929-1992`) has six tests covering both branches, all four session cardinalities and a custom `driver_cmd`; four assertions in the tree forbid the substring `resume` or `aw runs` on specific branches (F-14). They must all pass UNMODIFIED, which is the real proof that E-02 added a line without perturbing the footer's contract. Agy has no equivalent, so its footer coverage is new.
  YOU MAY NOW ASSERT THE TWO-PATH BEHAVIOR IF USEFUL, because it is no longer contested: R12 was amended (2026-09-09) to specify BOTH the interactive menu and the ladder, so a test naming either path is describing approved behavior rather than taking a side. Keep such assertions OUT of scope unless they pin text this plan adds; `tests/test_interrupt_menu.py` already covers the menu's own level mapping with 15 tests, and duplicating that is a P8 violation.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: tests asserting the new text in the rendered footer, interrupt message and help on BOTH hosts, plus assertions that exit codes, footer branches and existing messages are unchanged; no assertion about the interactive-versus-ladder question.
  - Execution state: performed

## Project conventions discovered (Step 0)

- ALL FOUR LEVELS SHIP AND THE `stop` VERB EXISTS. `LEVEL_AFTER_CALL`..`LEVEL_NOW_FORCE` (`runner_stop.py:210-215`), `SIGINT_LADDER` (`:1620`), `SIGTERM_LEVEL` (`:1623`), `add_stop_parser` (`:2096`), `stop_command` (`:2165`). Verified by running `oc run stop --help`.
- THE R16 REPORT IS ALREADY COMPLETE. `render_request_accepted` (`:1691`) plus `AWAITING` (`:1646`), `escalation_target` (`:1654`) and `_escalation_hint` (`:1669`) produce level, awaited boundary and escalation command. Verified by calling it. Do not rebuild it.
- LEVEL 2 IS REACHABLE ONLY OUT OF BAND, deliberately: the comment at `runner_stop.py:1616-1619` states the ladder is 1->3->4 with "no free key position for a second between-turn level", and calls it "a decision, not an omission". Any text must not imply Ctrl-C can reach level 2.
- CTRL-C HAS TWO SPECIFIED PATHS, AND BOTH CAN REACH LEVEL 1 (corrected at review). Spec `c4gd2h` R12 was AMENDED 2026-09-09 (`bc2ed703`) into R12.1 (interactive four-choice menu) and R12.2 (the `SIGINT_LADDER`). The path gate is `interrupt_menu_is_safe` (`runner_stop.py:1792-1833`): a TTY on BOTH streams and no `AW_NONINTERACTIVE`/`CI`, failing safe to the ladder. Menu choice 2 records `LEVEL_AFTER_CALL` (level 1); choices 3 and 4 record `LEVEL_NOW_FORCE`; choice 1 resumes and records nothing. The earlier claim that a TTY's first press is level 4 was false.
- THE FOOTER'S WORDING IS TEST-CONSTRAINED: four shipped assertions forbid the substrings `resume` and `aw runs` on specific branches (`tests/test_oc_runipd.py:1944`, `:1959`, `:1963`, `:230`).
- `resume`'s SUBPARSER HAS NO `RawDescriptionHelpFormatter` on either host, unlike `start`, so argparse reflows a multi-line description.
- `add_stop_parser` IS ALREADY SHARED (`runner_stop.py:2166`, called from `oc_runipd.py:8006` and `agy_runipd.py:4874`), so the verb these surfaces point at is one implementation, not two.
- EVERY TARGET SURFACE IS DUPLICATED ACROSS HOSTS: `render_continuation_hint` (`oc_runipd.py:7539`, `agy_runipd.py:4479`), the `main` KeyboardInterrupt handler (`oc_runipd.py:8358`, `agy_runipd.py:4993`), `build_parser` (`:7661`, `:4565`). Both must change identically.
- GUIDING_PRINCIPLES P8 FORBIDS A SECOND IMPLEMENTATION of an existing surface, which here means pointing at the `stop` verb's help rather than restating its per-level text.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals. RE-MEASURED AT REVIEW (HEAD `6882f7c6`): `1 failed, 5958 passed, 3 skipped, 2 xfailed`. The plan's `5648` was 310 low AND it named the wrong test: `tests/test_orchestrator_retirement.py` PASSES (`112 passed`). The one real failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, caused by ANOTHER party's gitignored `opencode-recovery/` tree (1746 files, `.gitignore:49`, backlog `8kttqq` `open`). DO NOT delete or "fix" that tree: it is not yours, and the shared-checkout rule forbids touching it.
- The joint stop-suite baseline is `74 passed` for `tests/test_runner_stop_triggers.py tests/test_interrupt_menu.py tests/test_statefork_dh0uno.py` (re-measured; the plan said 72).

## Findings

| Id | Severity | Location (measured at HEAD `fac69fbd`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | RETRACTED | ~~`runner_stop.py:1936-1953`, spec `c4gd2h:106` (R12)~~ | ~~THE SHIPPED TTY BEHAVIOR CONTRADICTS THE SPEC.~~ RETRACTED AT REVIEW, superseded by F-11/F-12/F-13. R12 was AMENDED on the maintainer's decision (2026-09-09, `bc2ed703`) to specify both paths, so there is no conflict; the gate is `interrupt_menu_is_safe` (both streams + no `AW_NONINTERACTIVE`/`CI`), not a bare `isatty()`; and the menu has four choices whose second records LEVEL 1. The original finding's conclusion (defer to a maintainer) was right for its moment and the maintainer has now ruled. | superseded; see F-11..F-13 |
| F-2 | N/A | `runner_stop.py:210-215`, `:2096`, `:2165` | ALL FOUR LEVELS SHIP WITH NO SKELETON, AND SO DOES THE `stop` VERB, whose `--help` renders four per-level descriptions and four worked commands. The item's core premise ("no way to learn that this is precisely level 1") is false at the verb level. | ran `oc run stop --help` (exit 0) |
| F-3 | N/A | `runner_stop.py:1691`, `:1646`, `:1654`, `:1669` | THE R16 REPORT ALREADY STATES LEVEL, BOUNDARY AND ESCALATION COMMAND. I called it: `stop accepted: level 1 (after-call) ...; waiting for the in-flight agent turn to finish; no further item will be started; to stop harder, press Ctrl-C again (or run \`aw oc run stop <run-id> --now\`) to request level 3 (now)`. So the item's "the interrupt report does not say how to request one" is false. | called `render_request_accepted` |
| F-4 | MED | `oc_runipd.py:7539-7586`, `agy_runipd.py:4479` | SURVIVES: the continuity footer mentions stopping NOWHERE. It prints session ids, a reuse command, and either `aw runs <run-id>` or a resume command. The item's cleanest remaining ask. | read the function end to end on both hosts |
| F-5 | MED | `oc_runipd.py:8389-8399` | SURVIVES: the `main` interrupt message is "Terminated without clean up; worktree and lanes left in place." or "Interrupted; durable run state was preserved." Neither names a level or the verb. | source read |
| F-6 | MED | `aw oc run start --help` | SURVIVES: the run-level help says nothing about stopping. Grepping its output for stop, interrupt and ctrl returns no match. | ran it |
| F-7 | LOW | `oc_runipd.py:7462-7465`, `render_stream.py:1656` | THE SUMMARY TABLE LABELS A COMPLETED STOP (`STOPPED (Level N: ...)` via `exit_reason`) but never advertises a POSSIBLE one. Partial coverage: the level is named after the fact, which is why the footer beside it is the better insertion point. | source read |
| F-8 | N/A | `runner_stop.py:1616-1619` | LEVEL 2 IS INTENTIONALLY UNREACHABLE BY SIGNAL, documented as "a decision, not an omission". Text must not imply Ctrl-C reaches it. | source read |
| F-9 | N/A | `.aw/records/plans/executed/...i6015i...` | THE ITEM'S "RELATED" CLAIM IS STALE: `i6015i` is EXECUTED, not pending, so there is no adjacent pending overlap. No pending plan covers this item and none carries `- From-Backlog: 1m3nul`. | file location; grep |
| F-10 | LOW | `oc_runipd.py:6410` vs `:8358` | THE ITEM'S `:5931` CITATION IS NOW TWO HANDLERS: `execute_item`'s (`:6410`) and `main`'s (`:8358`); only the latter is the interrupt REPORT. Its `:5936-5941` repeated-interrupt citation now lives in `prompt_interrupt_action` (`runner_stop.py:1832-1837`). | source read |
| F-11 | HIGH | spec `c4gd2h:105-110`, `:13`; commit `bc2ed703` | SPEC R12 WAS AMENDED ON THE MAINTAINER'S DECISION (2026-09-09) TO SPECIFY BOTH PATHS: R12.1 the interactive four-choice menu, R12.2 the `SIGINT_LADDER`, with "both must reach level 1 on a first press". The shipped behavior is now the SPECIFIED behavior, so F-1's conflict is RESOLVED and this plan's central constraint no longer exists. The spec also states the amendment's rationale on the merits and calls the two-stream predicate a safety FIX. | spec read; `git log` on the spec file |
| F-12 | HIGH | `runner_stop.py:1792-1833`, `:2007` | THE INTERACTIVE GATE IS NOT `sys.stdin.isatty()`. It is `interrupt_menu_is_safe`, requiring a TTY on BOTH streams AND no `AW_NONINTERACTIVE`/`CI`, with `AW_FORCE_INTERACTIVE_INTERRUPT=1` as an override that cannot beat the CI signal; returning False falls back to the ladder fail-safe. Its docstring records the 1h49m finalize wedge the one-stream predicate caused. | source read |
| F-13 | HIGH | `runner_stop.py:1777-1780`, `:1864-1891`, `:2013-2022`; `tests/test_interrupt_menu.py:380-400` | THE MENU HAS FOUR CHOICES AND ITS SECOND REACHES LEVEL 1. Measured: choice 1 (Resume) records NOTHING and the run continues; choice 2 (Finish current item) records `LEVEL_AFTER_CALL` = 1; choices 3 and 4 record `LEVEL_NOW_FORCE` = 4. So "the first Ctrl-C is level 4, not level 1" is FALSE, and the plan's cited test (`:332-355`) asserts `main`'s MESSAGES, not the level mapping (that is `:380-400`). | evaluated the constants and read both tests |
| F-14 | HIGH | `tests/test_oc_runipd.py:1944`, `:1959`, `:1963`, `:230` | FOUR SHIPPED ASSERTIONS CONSTRAIN THE FOOTER WORDING, which OQ-01 never mentions: three `assertNotIn("resume", hint)` / `assertNotIn("aw runs", hint)` in `ContinuationHintTests` plus one `assertNotIn("resume", result.stdout)` in an end-to-end successful-run test. A stop line containing either substring on the wrong branch breaks them, and the fence forbids weakening a test. `To stop a future run gracefully:` + `aw oc run stop <run-id> --after-call` contains neither (verified). | test read; substring check |
| F-15 | MED | `oc_runipd.py:7552`, `agy_runipd.py:4558`; `tests/test_oc_runipd.py:1929-1992` | THE TWO FOOTERS ARE ALREADY NOT IDENTICAL: the function objects differ, the sources differ by 449 characters, and the rendered output differs in host label and command prefix. So E-02's "identical wording" must scope to the STOPPING SENTENCE modulo `{cmd}`. Also: oc's footer has SIX tests, agy's has NONE, so agy coverage is new ground. | `is` comparison and source diff; rendered both |
| F-16 | HIGH | `oc_runipd.py:7759-7764` vs `:7905-7909`; `agy_runipd.py:4680-4685` vs `:4808-4812` | THE `resume` SUBPARSER LACKS `RawDescriptionHelpFormatter` ON BOTH HOSTS while `start` has it, so argparse REFLOWS a multi-line description onto one line and inlines the indented command. E-04 would have shipped a mangled paragraph on `resume`. Fix is a one-argument edit inside declared files, or a single-sentence pointer. | source read; reproduced with a minimal argparse case |
| F-17 | LOW | backlog `4awwg4` | THE SEPARATELY-FILED ITEM IS NOW STALE FOR ITS PRIMARY CLAIM. It is `open`, `Priority: low`, and its Summary still asserts the TTY path "contradict[s] spec c4gd2h R12", which the amendment settled. Re-reading it is not this plan's job, but this plan must no longer present itself as blocked by it. | backlog front matter read |
| F-18 | LOW | bare `python3 -m pytest`; `tests/test_orchestrator_retirement.py` | THE STATED BASELINES ARE BOTH WRONG. Full suite is `1 failed, 5958 passed, 3 skipped, 2 xfailed` (plan said `1 failed, 5648 passed`), the named failing test PASSES (`112 passed`), and the real failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` from another party's gitignored `opencode-recovery/` tree. The joint stop-suite baseline is `74 passed`, not 72. | measured both |

## Proposed changes (ordered, validatable)

1. E-01 fixes the truth condition against the AMENDED R12: name both specified Ctrl-C paths and their gate, and point every surface at the out-of-band verb, which needs no terminal and is the only route to level 2.
2. E-02 adds a stopping line to the continuity footer on both hosts, in the surrounding style, without restating the levels.
3. E-03 adds one truthful sentence to the `main` interrupt message on both hosts, with no prompt and no behavior change.
4. E-04 adds a stopping pointer to the run-level help on both hosts, verified by running `--help`.
5. E-05 pins all three surfaces on both hosts and asserts exit codes, branches and existing messages unchanged.

## Deferred / out of scope (with reason)

- ~~RESOLVING THE INTERACTIVE-PROMPT-VERSUS-LADDER CONFLICT (F-1).~~ NO LONGER DEFERRED BECAUSE IT NO LONGER EXISTS (F-11). The maintainer resolved it by AMENDING R12 on 2026-09-09 (`bc2ed703`) to specify both paths, choosing the menu as the interactive path with the ladder as the fail-safe. Nothing here is blocked on it. Backlog `4awwg4` remains `open` with a now-stale Summary (F-17); re-reading that item against the amended R12 is a separate, small job and is NOT a prerequisite for this plan.
- ANY INTERACTIVE PROMPT ON Ctrl-C, added or removed. Still out of scope, but for a different and stronger reason than before: the menu is now SPECIFIED behavior (R12.1), so changing it would amend an approved, release-gating spec. This plan documents it and does not touch it.
- RE-DOCUMENTING THE MENU'S OWN LEVEL MAPPING. `tests/test_interrupt_menu.py` already pins it with 15 tests and `oc run stop --help` already explains the levels; a third statement would be the P8 duplication this plan otherwise avoids.
- REBUILDING THE R16 REQUEST REPORT (F-3). It already states level, boundary and escalation command. Touching it would duplicate a working surface (P8).
- RESTATING THE FOUR LEVELS IN THE RUN HELP OR THE FOOTER (F-2). The `stop` verb's help already does this well; a second copy would drift.
- ANY CHANGE TO LEVELS, BUDGETS, ESCALATION, POLLING, OR THE STOP-REQUEST FLAG. This plan is text-only on three surfaces.
- MAKING LEVEL 2 SIGNAL-REACHABLE (F-8). A documented decision, not an omission.
- CHANGING THE SUMMARY TABLE'S `exit_reason` (F-7). It correctly labels a completed stop; advertising a possible one belongs in the footer that prints beside it.

## Scope check

- Over-scope: none. All five declared paths are modified: both runner modules by E-02 through E-04, and the three test files by E-05 per OQ-02's resolution (`tests/test_interrupt_menu.py` and `tests/test_oc_runipd.py` were ADDED to `- Scope-Paths:` at review because that is where the existing harnesses and the constraining assertions live; the fence forbids modifying their existing assertions, only adding beside them). If a chosen placement leaves one declared test file untouched, it needs a `--scope-ack` at finalize rather than a token edit.
- Under-scope: stated rather than left as `none`. Deliberately: this plan documents the stop protocol and changes none of it, so after it lands the menu's own level mapping is still explained only by `oc run stop --help` and its tests, and backlog `4awwg4`'s now-stale Summary (F-17) is still unrevised. NOTE THE ONE POSSIBLE CODE EDIT: E-04 may add `formatter_class=argparse.RawDescriptionHelpFormatter` to both hosts' `resume` subparsers (F-16). That is inside the declared files and is behavior-neutral for parsing (it changes only help rendering), but it is not pure text, so it must be stated in the V-04 evidence rather than slipped in.

## Required tests / validation

`python3 -m pytest` bare in the executing worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS rather than totals. RE-MEASURED AT REVIEW: `1 failed, 5958 passed, 3 skipped, 2 xfailed`, the single failure being `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` (another party's gitignored `opencode-recovery/` tree; backlog `8kttqq`; do not touch it). The plan's earlier baseline was 310 low and named `tests/test_orchestrator_retirement.py`, which PASSES (`112 passed`). Then the stop-related suites explicitly: `tests/test_runner_stop_triggers.py`, `tests/test_interrupt_menu.py` and `tests/test_oc_runipd.py`, plus the joint baseline with `tests/test_statefork_dh0uno.py` re-measured at `74 passed`. Because this plan is text-only, the strongest validation is OPERATOR-VISIBLE output: paste the actual rendered footer, the actual interrupt message, and the actual `--help` output for both hosts, rather than asserting on constants. Also paste `aw oc run stop --help` unchanged, since a plan about stop discoverability must prove it did not disturb the one surface that was already good.

## Spec / documentation sync

NO SPEC IS AMENDED, and the reason matters. Spec `c4gd2h` owns the stop protocol, carries `- Blocks-Release: next`, and sits at `- Status: implementing`. This plan adds operator-facing TEXT on three surfaces and changes no protocol behavior, so it amends nothing. R16 ("the driver prints the level accepted, what it is waiting for, and how to escalate") is already satisfied by `render_request_accepted` and is untouched.
NO SPEC EDIT IS REQUIRED, AND THE REASON CHANGED AT REVIEW. This section previously said a spec edit "would be required" to close F-1's conflict and deliberately deferred it. THE MAINTAINER ALREADY MADE THAT EDIT: R12 was amended on 2026-09-09 (`bc2ed703`) into R12.1 (interactive menu) and R12.2 (ladder), so the code and the spec now AGREE and there is nothing for this plan to reconcile. `c4gd2h` therefore stays out of `- Scope-Paths:` because the plan has no reason to touch it, not because it is dodging a conflict.
VERIFY BEFORE EXECUTING rather than assuming, since this plan's premise already went stale inside two days: re-read R12.1, R12.2 and R16 and confirm the added text contradicts none of them. Two specific traps. FIRST, do NOT write a sentence implying the ladder governs an interactive terminal, or that the menu governs a piped or CI run: each governs exactly one path and the gate is `interrupt_menu_is_safe`. SECOND, do NOT imply Ctrl-C can reach level 2 by any path; it cannot, by documented decision (`runner_stop.py:1616-1619`), and only the out-of-band verb reaches it. If the executor concludes the text cannot be written without asserting something a spec requirement denies, STOP and report.

## Open questions

### OQ-01: Should the footer line print on the all-success branch too?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as the RESUME BRANCH FIRST, with the all-success branch optional and stated. The footer branches on `all_success`: successes get `aw runs <run-id>` and everything else gets a resume command. An operator who will resume is the one most likely to want a graceful stop later, so that branch is where the line earns attention; after a fully successful run the same line is closer to noise, and a nudge that prints when it cannot be acted on trains readers to skip the footer. The executor may include it on both branches if the wording stays short, but must state the choice rather than letting it fall out of the code.

### OQ-02: Where do E-05's tests belong?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Resolution or deferral rationale: RESOLVED AT REVIEW FROM EVIDENCE, and one of the question's two arguments has evaporated. It reasoned that reusing `tests/test_interrupt_menu.py` "risks entangling new assertions with the tests that pin the CONTESTED interactive behavior (F-1)". That behavior is no longer contested: R12 was amended to specify it (F-11), so entanglement with it is no longer a hazard. What the evidence actually says about placement: E-03's harness already exists in `tests/test_interrupt_menu.py::RunnerMainOutputOnInterruptTests` (`:328-360`), which drives `main` over BOTH modules with mocks and asserts code 130 plus the exact message; and E-02's harness already exists in `tests/test_oc_runipd.py::ContinuationHintTests` (`:1929-1992`), six tests over both footer branches, whose four `assertNotIn` assertions (F-14) are the very contract E-02 must not break. RESOLUTION: put the interrupt-message assertions beside the existing ones in `tests/test_interrupt_menu.py` (adding, never modifying), put the footer assertions beside `ContinuationHintTests` in `tests/test_oc_runipd.py`, and use the declared `tests/test_runner_stop_triggers.py` for the help-output assertions and anything ladder-adjacent. THAT MEANS TWO SCOPE-PATHS ADDITIONS (`tests/test_interrupt_menu.py`, `tests/test_oc_runipd.py`), which are now DECLARED in `- Scope-Paths:` rather than left to a finalize-time justification; note the fence still forbids MODIFYING either file's existing assertions. If the executor prefers a single new file instead, that is acceptable, but it must then be declared and the existing footer/message assertions must still be run and shown green.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the written truth condition, naming BOTH R12 paths and their gate. Paste the RE-VERIFICATION performed at execution time, not this plan's claims: `oc run stop --help` output, a call to `render_request_accepted`, the current `interrupt_menu_is_safe` and `_sigint` sources, and the menu-choice-to-level mapping evaluated (not assumed). Paste spec `c4gd2h` R12.1 and R12.2 as they read at execution time, and confirm the amendment is still in place. State which path governs which environment and therefore what each surface may claim; if anything disagrees with F-11..F-13, describe the CODE and record the disagreement.
  - Observed evidence: VERIFIED AT EXECUTION TIME BY RUNNING THE CODE, at HEAD `8175a794`, and the full written truth condition is in the decisions register (`decisions-and-questions.md`, section "E-01: the truth condition"). Summary of what was re-measured rather than trusted.
    BOTH R12 PATHS AND THEIR GATE, as the spec reads NOW: I re-read `.aw/records/specs/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md` and the 2026-09-09 amendment IS still in place. R12 line 105 reads "Ctrl-C has TWO paths, chosen by whether a human can actually answer a question, and both must reach level 1 on a first press. AMENDED 2026-09-09 on the maintainer's decision". R12.1 (line 106) is the interactive four-choice menu, gated on "a real terminal on BOTH the input and the output stream, and no `AW_NONINTERACTIVE`/`CI` signal"; R12.2 (line 107) is the `SIGINT_LADDER`, "1 -> 3 -> 4, with a printed hint that pressing again stops harder". So F-11 is CONFIRMED and F-1 stays retracted.
    THE GATE IS `interrupt_menu_is_safe`, NOT `sys.stdin.isatty()` (F-12 confirmed). Read end to end in `agent_workflows/runner_stop.py` (`interrupt_menu_is_safe`, and `_sigint`'s call to it): it returns False on any truthy `AW_NONINTERACTIVE`/`CI`; then True on `AW_FORCE_INTERACTIVE_INTERRUPT=1` (which cannot beat the CI signal); else `_stream_is_tty(in_stream) and _stream_is_tty(out_stream)`, i.e. a TTY on BOTH streams. Returning False falls through to the ladder, which the docstring calls "FAIL-SAFE, not a refusal to serve".
    THE MENU-CHOICE-TO-LEVEL MAPPING, EVALUATED not assumed (F-13 confirmed). Constants printed by running Python against the live module:

        SIGINT_LADDER (1, 3, 4)
        SIGTERM_LEVEL 3
        levels 1 2 3 4                      # AFTER_CALL, AFTER_SET, NOW, NOW_FORCE
        actions 1 2 3 4                     # RESUME, FINISH_CURRENT, CLEANUP, TERMINATE_NO_CLEANUP

    And read in `_sigint`: choice 1 (`INTERRUPT_ACTION_RESUME`) returns having recorded NOTHING; choice 2 (`INTERRUPT_ACTION_FINISH_CURRENT`) calls `_record(LEVEL_AFTER_CALL)`, i.e. LEVEL 1; choice 4 records `LEVEL_NOW_FORCE` and raises `KeyboardInterrupt("just-terminate-no-cleanup")`; choice 3 records `LEVEL_NOW_FORCE` and raises `KeyboardInterrupt("clean-up-and-terminate")`. So a first press on a terminal CAN stop gently, and the plan's original "first Ctrl-C is level 4" premise is false.
    `render_request_accepted` CALLED DIRECTLY, confirming R16 is already complete and must not be rebuilt (F-3):

        stop accepted: level 1 (after-call) (requested by operator); waiting for the in-flight agent turn to finish; no further item will be started; to stop harder, press Ctrl-C again (or run `aw oc run stop <run-id> --now`) to request level 3 (now)

    `aw oc run stop --help` RUN (exit 0): renders four per-level descriptions and four worked example commands, plus the cleanup-is-unconditional and monotonic-escalation guarantees. Full output pasted under V-04, where it doubles as the unchanged-surface proof.
    WHICH PATH GOVERNS WHICH ENVIRONMENT, AND THEREFORE WHAT EACH SURFACE MAY CLAIM: R12.1 governs a real terminal on both streams with no `AW_NONINTERACTIVE`/`CI`; R12.2 governs everything else (piped output, unattended, CI). Each surface therefore names the OUT-OF-BAND verb as its referent, because `stop <run-id> --after-call` needs no terminal, no signal and no menu, works identically on both paths through `request_stop`, and is the ONLY route to level 2 (`runner_stop`: the ladder "leaves no free key position", "a decision, not an omission"). Level 2 is named on NO Ctrl-C surface, and no surface presents either path as the only one.
    ONE DISAGREEMENT WITH THE PLAN FOUND, and the CODE is described rather than papered over: the plan's F-15 says the two footers are separate forked functions differing by 449 characters. AT EXECUTION TIME THEY ARE ONE SHARED IMPLEMENTATION (`runner_shared.render_continuation_hint`, wrapped by a four-line per-host function on each host), because sibling `tx6q0h` lifted it behind `HostLabels` on 2026-09-17, nine days after this plan was written. `tests/test_rununify_main.py` classes it `"shared-host-wrapper"` and records the reclassification. Recorded and resolved as DECISION 03-wqq8ua-D1; F-15's "agy footer has NO test coverage" is also stale (`tests/test_rununify_host_descriptor.py::test_the_continuation_hint_names_each_host_by_its_OWN_product_name` covers both hosts).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the ACTUAL rendered footer from both hosts, on the resume branch and the all-success branch, showing the new line and its exact command. Paste both hosts' text side by side proving the STOPPING SENTENCE is identical modulo the command prefix (the footers legitimately differ elsewhere; F-15). Confirm the four levels are NOT restated. State the OQ-01 branch decision as implemented. PASTE `tests/test_oc_runipd.py::ContinuationHintTests` GREEN AND UNMODIFIED, plus the end-to-end test at `:230`, since their four `assertNotIn` assertions are the contract E-02 must not break (F-14); if you placed the line on the all-success branch, show explicitly that your text contains neither `resume` nor `aw runs`.
  - Observed evidence: THE ACTUAL RENDERED FOOTER, obtained by calling each host's `render_continuation_hint`, on BOTH branches and BOTH hosts.

        === oc / ALL-SUCCESS ===

        --- OpenCode Session Continuity ---
        Captured session: ses_abc123 (Set: demo)
        To run a new plan under the same session:
          aw oc run --session ses_abc123 <selector>
        To inspect run summary:
          aw runs run-xyz
        To stop a future run gracefully:
          aw oc run stop <run-id> --after-call

        === oc / RESUME ===

        --- OpenCode Session Continuity ---
        Captured session: ses_abc123 (Set: demo)
        To run a new plan under the same session:
          aw oc run --session ses_abc123 <selector>
        To resume this run:
          aw oc run resume --repo /repo run-xyz
        To stop a future run gracefully:
          aw oc run stop <run-id> --after-call

        === agy / ALL-SUCCESS ===

        --- Antigravity Session Continuity ---
        Captured session: ses_abc123 (Set: demo)
        To run a new plan under the same session:
          aw agy run --session ses_abc123 <selector>
        To inspect run summary:
          aw runs run-xyz
        To stop a future run gracefully:
          aw agy run stop <run-id> --after-call

        === agy / RESUME ===

        --- Antigravity Session Continuity ---
        Captured session: ses_abc123 (Set: demo)
        To run a new plan under the same session:
          aw agy run --session ses_abc123 <selector>
        To resume this run:
          aw agy run resume --repo /repo run-xyz
        To stop a future run gracefully:
          aw agy run stop <run-id> --after-call

    THE STOPPING SENTENCE IS IDENTICAL ACROSS HOSTS MODULO THE COMMAND PREFIX, and now by CONSTRUCTION rather than by hand: the footer is ONE shared body (`runner_shared.render_continuation_hint`) and the text is ONE shared function (`runner_stop.stop_footer_hint`), so the only difference possible is `labels.command`. Side by side: `To stop a future run gracefully:` / `  aw oc run stop <run-id> --after-call` versus `To stop a future run gracefully:` / `  aw agy run stop <run-id> --after-call`. Asserted mechanically in `tests/test_runner_stop_triggers.py::RunLevelHelpAdvertisesStoppingTests::test_the_continuity_FOOTER_names_stopping_on_BOTH_hosts`, which also asserts neither host renders the OTHER's command. See DECISION 03-wqq8ua-D1 for why the edit is one shared change rather than two (F-15 went stale: the footers are no longer forked, and forking them back would fail `tests/test_runner_shared.py::SingleDefinitionTests`).
    THE FOUR LEVELS ARE NOT RESTATED. The added lines are one label plus one command. `tests/test_oc_runipd.py::ContinuationHintTests::test_the_footer_does_not_restate_the_four_levels` asserts the rendered footer contains none of `--after-set`, `--now-force`, `level 2`, `level 3`, `level 4`, and in particular does not imply Ctrl-C reaches level 2.
    THE OQ-01 BRANCH DECISION AS IMPLEMENTED: BOTH BRANCHES (DECISION 03-wqq8ua-D2). The line is placed after the `all_success` branch, unconditionally. What licenses the success branch is the FUTURE tense: OQ-01's objection was to "a nudge that prints when it cannot be acted on", which applies to a line about stopping THIS finished run, not to one about the next. Pinned by `test_the_stopping_line_prints_on_BOTH_footer_branches`, which also asserts each branch's pre-existing content survives.
    THE FOUR SHIPPED `assertNotIn` ASSERTIONS PASS UNMODIFIED, which is the real proof no footer contract was perturbed. `git diff -U0 tests/test_oc_runipd.py | grep '^-'` returns ZERO lines, i.e. nothing was deleted or edited; my change is purely additive. `ContinuationHintTests` green (13 passed: the 6 originals plus 4 new plus 3 more), and the end-to-end successful-run test green in the same file:

        $ python3 -m pytest tests/test_oc_runipd.py::ContinuationHintTests -o addopts="" -q
        .............                                                            [100%]
        13 passed in 0.33s

        $ python3 -m pytest tests/test_oc_runipd.py tests/test_rununify_host_descriptor.py
        251 passed in 9.85s   (baseline, before my change)
        ... and after my change, as part of the 618-test group pasted under V-05.

    THE LINE IS ON THE ALL-SUCCESS BRANCH, SO THE SUBSTRING PROOF IS REQUIRED AND GIVEN: the added text `To stop a future run gracefully:` + `aw oc run stop <run-id> --after-call` contains neither `resume` nor `aw runs`. Asserted directly by `test_the_stopping_line_avoids_the_substrings_the_success_branch_forbids`, which exists so a future rewording is told WHICH rule it broke instead of being pointed at four unrelated tests.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the ACTUAL interrupt message from both hosts for the ordinary interrupt AND the `just-terminate-no-cleanup` branch, showing the new sentence and the preserved originals. Paste the exit codes observed: 143 for SIGTERM and 130 otherwise. Paste a diff proving no branch, no ledger call, and no ordering of `emit_shutdown_report` changed. Confirm no prompt was added.
  - Observed evidence: THE ACTUAL INTERRUPT MESSAGE from BOTH hosts, on the ordinary interrupt, the `just-terminate-no-cleanup` branch AND the SIGTERM branch, captured by driving the real `main` to its `KeyboardInterrupt` handler and reading stderr. EXIT CODES OBSERVED AND SHOWN.

        --- oc_runipd / JUST-TERMINATE-NO-CLEANUP -> exit 130 ---
        Terminated without clean up; worktree and lanes left in place.
        Next time, `aw oc run stop <run-id> --after-call` requests a graceful stop from another terminal (see `aw oc run stop --help` for the levels).

        --- oc_runipd / ORDINARY INTERRUPT -> exit 130 ---
        Interrupted; durable run state was preserved.
        Next time, `aw oc run stop <run-id> --after-call` requests a graceful stop from another terminal (see `aw oc run stop --help` for the levels).

        --- oc_runipd / SIGTERM -> exit 143 ---
        Terminated by SIGTERM; durable run state was preserved.
        Next time, `aw oc run stop <run-id> --after-call` requests a graceful stop from another terminal (see `aw oc run stop --help` for the levels).

        --- agy_runipd / JUST-TERMINATE-NO-CLEANUP -> exit 130 ---
        Terminated without clean up; worktree and lanes left in place.
        Next time, `aw agy run stop <run-id> --after-call` requests a graceful stop from another terminal (see `aw agy run stop --help` for the levels).

        --- agy_runipd / ORDINARY INTERRUPT -> exit 130 ---
        Interrupted; durable run state was preserved.
        Next time, `aw agy run stop <run-id> --after-call` requests a graceful stop from another terminal (see `aw agy run stop --help` for the levels).

        --- agy_runipd / SIGTERM -> exit 143 ---
        Terminated by SIGTERM; durable run state was preserved.
        Next time, `aw agy run stop <run-id> --after-call` requests a graceful stop from another terminal (see `aw agy run stop --help` for the levels).

    THE ORIGINALS ARE PRESERVED BYTE-FOR-BYTE and still come FIRST: both quoted sentences appear verbatim above, and `tests/test_interrupt_menu.py::MainInterruptNamesTheGracefulStopVerbTests::test_the_pre_existing_sentences_and_exit_codes_are_unchanged` asserts the original's index precedes the new sentence's, so the addition cannot become a replacement. `143` for SIGTERM and `130` otherwise, asserted per host.
    THE DIFF PROVES NO BRANCH, NO LEDGER CALL, AND NO ORDERING MOVED. The whole change on each host is ONE `print(...)` appended AFTER the existing if/else, with the comment above it:

        +        print(
        +            runner_stop.stop_interrupt_hint(_detect_driver_command()),
        +            file=sys.stderr,
        +        )
                 return 143 if is_sigterm else 130

    `emit_shutdown_report(to_stderr=True)` is untouched and still called BEFORE the messages (visible in the diff context: no `-` line anywhere in either handler); the `just-terminate-no-cleanup` branch remains a distinct message; `return 143 if is_sigterm else 130` is unchanged. No code, no ledger call and no reordering.
    NO PROMPT WAS ADDED, asserted rather than asserted-by-eye: `test_the_interrupt_message_asks_the_operator_nothing` checks the added text contains no `?` and none of `1.`/`2.`/`3.`/`4.`/`Choice`. And `test_the_hint_claims_no_level_about_the_exit_that_just_happened` pins that it is future-tense (`Next time`) and names none of `--after-set`, `level 2`, `level 3`, `level 4`, because this handler cannot know which R12 path or rung produced the exit and level 2 is unreachable by any signal.
    `RunnerMainOutputOnInterruptTests` (the shipped harness that pins both exact messages and code 130 over BOTH modules) passes UNMODIFIED: `git diff -U0 tests/test_interrupt_menu.py | grep '^-'` returns ZERO lines.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `--help` output for `start` and `resume` on BOTH hosts showing the new paragraph, obtained by RUNNING the command rather than reading the argparse source. THE `resume` OUTPUT IS THE DECISIVE ONE (F-16): show it is NOT reflowed onto a single line, and state which fix you chose (adding `RawDescriptionHelpFormatter` to both hosts' `resume` parsers, or a single-sentence pointer). If you added the formatter, say so explicitly here, since it is a code rather than text edit. Paste `aw oc run stop --help` AND `aw agy run stop --help` proving both are unchanged. Confirm no per-level text was duplicated.
  - Observed evidence: `--help` OUTPUT OBTAINED BY RUNNING THE COMMAND on BOTH hosts and BOTH verbs (`python3 -m agent_workflows <host> run <verb> --help`), showing the new paragraph.

        === aw oc run start --help ===        === aw oc run resume --help ===   (identical section)
        STOPPING A RUN GRACEFULLY:
          Ask a live run to wind down, from another terminal or a script:

            aw oc run stop <run-id> --after-call

          That lets the in-flight agent turn finish and starts nothing further. Cleanup always
          runs, at every level. See `aw oc run stop --help` for all four levels.

          Ctrl-C in THIS terminal also stops the run: on a real terminal it offers a menu whose
          second choice finishes the current item and stops, and otherwise a first press requests
          the same gentlest level and pressing again stops harder.

        === aw agy run start --help ===       === aw agy run resume --help ===  (identical section)
        STOPPING A RUN GRACEFULLY:
          Ask a live run to wind down, from another terminal or a script:

            aw agy run stop <run-id> --after-call

          That lets the in-flight agent turn finish and starts nothing further. Cleanup always
          runs, at every level. See `aw agy run stop --help` for all four levels.

          Ctrl-C in THIS terminal also stops the run: on a real terminal it offers a menu whose
          second choice finishes the current item and stops, and otherwise a first press requests
          the same gentlest level and pressing again stops harder.

    THE `resume` OUTPUT IS THE DECISIVE ONE AND IT IS NOT REFLOWED, as shown above: the header sits on its own line, the command sits alone on its own indented line, and the two prose paragraphs keep their break. For contrast, here is the reflow I reproduced at execution time with a minimal argparse case, which is what `resume` WOULD have produced:

        === WITHOUT RawDescriptionHelpFormatter ===
        Line one. STOPPING: a command here
        === WITH RawDescriptionHelpFormatter ===
        Line one.

        STOPPING:
          a command here

    THE FIX I CHOSE, STATED EXPLICITLY AS THE FENCE REQUIRES: I added `formatter_class=argparse.RawDescriptionHelpFormatter` to BOTH hosts' `resume` subparsers (`oc_runipd.build_parser`'s `resume = sub.add_parser("resume", ...)` and the `agy_runipd` twin). This is the plan's "ONE PERMITTED NON-TEXT EDIT" (F-16), and it is a CODE rather than text edit, so it is named here. Rationale and the rejected alternative are in DECISION 03-wqq8ua-D3: it is behavior-neutral for PARSING (argparse consults `formatter_class` only when formatting usage/help), no test anywhere asserts `resume`'s formatter class (one grep hit repo-wide, a comment), and the parse-level pins in `tests/test_rununify_build_parser.py` (subparser names, option strings, parsed defaults; 26 tests) all pass. Pinned structurally by `test_the_resume_paragraph_is_not_REFLOWED_onto_one_line`, which asserts the command is ALONE on its indented line, so the property survives any later refactor of how the formatter is set.
    `stop --help` IS UNCHANGED ON BOTH HOSTS, PROVEN BY DIFF rather than by inspection. I captured both hosts' `stop --help` before and after my change (stashing the edits to get the "before") and diffed:

        $ diff /tmp/stop-oc-before.txt /tmp/stop-oc-after.txt   -> IDENTICAL
        $ diff /tmp/stop-agy-before.txt /tmp/stop-agy-after.txt -> IDENTICAL

    Both are 46 lines and exit 0. This matters because a plan about stop discoverability must prove it did not disturb the one surface that was already good. Its content (unchanged) is the four per-level descriptions, the four worked examples, `Cleanup is UNCONDITIONAL at every level`, the monotonic-escalation sentence, and the POSIX-only platform note.
    NO PER-LEVEL TEXT WAS DUPLICATED (P8), asserted by `test_the_run_help_does_not_duplicate_the_per_level_text`: the note contains none of `Level 1:`, `Level 2:`, `Level 3:`, `Level 4:`, `--after-set`, `--now-force`, `indeterminate`. It names the verb, one level (`--after-call`), and defers to `stop --help`. And `test_the_note_attributes_neither_ctrl_c_path_to_the_other` pins that both R12 paths are described and neither is presented as the only one.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the new tests and their passing output, showing assertions on RENDERED output for all three surfaces on BOTH hosts (note agy's footer has no prior coverage, so those assertions are new rather than mirrored; F-15). Paste the unchanged-behavior assertions (exit codes 143/130, both footer branches, the `just-terminate-no-cleanup` message). Paste `tests/test_runner_stop_triggers.py`, `tests/test_interrupt_menu.py` and `tests/test_oc_runipd.py` green, and confirm NO existing assertion in any of them was modified. The joint baseline for `tests/test_runner_stop_triggers.py tests/test_interrupt_menu.py tests/test_statefork_dh0uno.py` is `74 passed` (re-measured at review; the plan said 72). Paste the bare full-suite summary line with a NODE-ID comparison against the re-measured baseline (`1 failed, 5958 passed, 3 skipped, 2 xfailed`, the one failure being the `test_reporting_contract` parity test from another party's gitignored tree, which you must not touch). State the OQ-02 placement decision as implemented.
  - Observed evidence: THE NEW TESTS AND THEIR PASSING OUTPUT. 14 tests added across the three declared files, all asserting RENDERED output (the footer, the interrupt message, and real `--help` subprocess output), never a string constant:
    `tests/test_oc_runipd.py::ContinuationHintTests` (+4, beside the 6 originals): `test_the_footer_tells_an_operator_how_to_stop_a_run_gracefully`, `test_the_stopping_line_prints_on_BOTH_footer_branches`, `test_the_stopping_line_avoids_the_substrings_the_success_branch_forbids`, `test_the_footer_does_not_restate_the_four_levels`.
    `tests/test_interrupt_menu.py::MainInterruptNamesTheGracefulStopVerbTests` (+4, beside `RunnerMainOutputOnInterruptTests`): both-hosts-every-branch verb naming, unchanged sentences/exit codes, no-prompt, and no-level-claimed.
    `tests/test_runner_stop_triggers.py::RunLevelHelpAdvertisesStoppingTests` (+6): both verbs on both hosts point at the verb, the `resume` reflow assertion, cross-host wording identity, no per-level duplication, neither-path-misattributed, and the BOTH-HOST continuity-footer assertion (DECISION 03-wqq8ua-D4 placed the cross-host footer check here so every stop-discoverability surface is reachable from one file).

        $ python3 -m pytest tests/test_oc_runipd.py::ContinuationHintTests -o addopts="" -q
        .............                                                            [100%]
        13 passed in 0.33s

        $ python3 -m pytest tests/test_interrupt_menu.py -o addopts="" -q
        ...................                                                      [100%]
        19 passed in 0.34s

        $ python3 -m pytest tests/test_runner_stop_triggers.py::RunLevelHelpAdvertisesStoppingTests -o addopts="" -q
        .....                                                                    [100%]
        5 passed in 1.69s

    BOTH HOSTS COVERED FOR ALL THREE SURFACES: the footer (`test_the_continuity_FOOTER_names_stopping_on_BOTH_hosts`, which also asserts neither host renders the other's command), the interrupt message (`test_both_hosts_name_the_out_of_band_verb_on_every_interrupt_branch`, looping both modules over all three branches), and the help (`test_both_verbs_on_both_hosts_point_at_the_stop_verb`, four real subprocess `--help` runs). Note F-15's "agy footer has no prior coverage" was stale: `tests/test_rununify_host_descriptor.py` already covered both hosts' footers, and it passes.
    THE UNCHANGED-BEHAVIOR ASSERTIONS: exit codes 143 (SIGTERM) and 130 (otherwise) per host; both footer branches still print their pre-existing content; the `just-terminate-no-cleanup` message intact and still ordered before the addition. All in `test_the_pre_existing_sentences_and_exit_codes_are_unchanged` and `test_the_stopping_line_prints_on_BOTH_footer_branches`.
    THE THREE DECLARED SUITES GREEN, AND NO EXISTING ASSERTION MODIFIED IN ANY OF THEM. The mechanical proof is that the diff DELETES NOTHING from the two fenced test files: `git diff -U0 tests/test_oc_runipd.py tests/test_interrupt_menu.py | grep -E '^-' | grep -v '^---'` returns ZERO lines. (One pre-existing block in `test_interrupt_menu.py` was re-indented by `ruff-format` because my helper sits beside it; the `with`-statement contents and every assertion are byte-identical, and the file still carries its 73 lines of pre-existing formatter drift, unchanged.)

        $ python3 -m pytest tests/test_runner_stop_triggers.py tests/test_interrupt_menu.py tests/test_statefork_dh0uno.py
        86 passed in 3.93s

    The joint baseline for those three was re-measured HERE at `76 passed` before my change (the plan's review said 74, itself a correction of the plan's 72); it is `86 passed` after, i.e. +10 with zero regressions.
    THE WIDER GROUP, including every characterization file my change touches:

        $ python3 -m pytest tests/test_runner_stop_triggers.py tests/test_interrupt_menu.py tests/test_oc_runipd.py tests/test_rununify_main.py tests/test_rununify_host_descriptor.py tests/test_runner_shared.py tests/test_runner_refork_guard.py tests/test_rununify_build_parser.py tests/test_statefork_dh0uno.py
        618 passed in 18.31s

    THE BARE FULL-SUITE SUMMARY, with a NODE-ID comparison rather than a totals comparison:

        BASELINE, measured in THIS worktree before any edit:
        $ python3 -m pytest
        1 failed, 7626 passed, 3 skipped, 2 xfailed, 3 warnings in 109.77s (0:01:49)
        FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped

        AFTER, same command:
        $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest
        7641 passed, 3 skipped, 2 xfailed, 3 warnings in 101.98s (0:01:41)

    NODE-ID COMPARISON: the baseline's single failing node is `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`, and it is ENVIRONMENTAL, not a code defect: it asserts a non-isolated turn inherits no `OPENCODE_CONFIG_CONTENT` denial policy, and THIS agent's own turn runs with that variable exported, so the test reads its own harness's env. Proven by isolating the variable alone, at the unmodified baseline:

        $ python3 -m pytest tests/test_turn_bounds.py::...::test_the_permission_policy_by_contrast_IS_isolation_scoped
        1 failed
        $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py::...::test_the_permission_policy_by_contrast_IS_isolation_scoped
        1 passed

    So the AFTER run clears that variable and the failing-node set goes from {that one node} to {} - no new failing node id, and none of the plan's own files regressed. NOTE the plan's predicted baseline (`1 failed, 5958 passed`, failing on `tests/test_reporting_contract.py::ParityTests`) did NOT reproduce: the suite has grown to 7626 passing and that parity test passes here, because the gitignored `opencode-recovery/` tree it tripped on is absent from this lane worktree. I did not touch that tree or that test.
    THE OQ-02 PLACEMENT DECISION AS IMPLEMENTED (DECISION 03-wqq8ua-D4): interrupt-message assertions beside the existing harness in `tests/test_interrupt_menu.py`; footer-branch assertions beside `ContinuationHintTests` in `tests/test_oc_runipd.py`; help-output plus the cross-host footer assertion in the declared `tests/test_runner_stop_triggers.py`. All three declared test paths are genuinely modified, so no `--scope-ack` is needed for any of them, and every addition sits BESIDE the existing assertions rather than altering them.
    NO ASSERTION WAS ADDED ABOUT THE INTERACTIVE-VERSUS-LADDER QUESTION beyond what this plan's own text requires: `test_the_note_attributes_neither_ctrl_c_path_to_the_other` pins only the wording of text THIS plan adds. The menu's own level mapping is left entirely to the 15 shipped tests in `tests/test_interrupt_menu.py` (P8).
    ONE OUT-OF-FENCE TEST FILE WAS EDITED AND IT IS FLAGGED: `tests/test_rununify_main.py`, whose four characterization pins my E-03/E-04 edits legitimately moved (see DECISION 03-wqq8ua-D5 for the full reasoning and the pre-change measurement proving NOTHING was forked). The pins were RE-BASED with dated annotations, never weakened: closure 29->31, histogram `one-object-agy-imports-oc` 5->6 and `still-defined-twice` 8->9, oc/agy closures 29/26->31/28 with the three-symbol GAP unchanged, and the patch-seam population 12->18 / 26->32. I also renamed `test_the_total_across_those_files_is_still_26` to `..._matches_the_table` and made its message read `EXPECTED_SEAM_TOTAL`, because a count hardcoded in a method name is the staleness trap that file's own sibling test documents having already suffered twice.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the paths in `- Scope-Paths:`, which now includes `tests/test_interrupt_menu.py` and `tests/test_oc_runipd.py` per OQ-02's resolution. Do NOT change any level, budget, escalation rule, poll site, or the stop-request flag. Do NOT touch `render_request_accepted` or any part of the R16 report; it is already complete. Do NOT add, remove or alter the interactive Ctrl-C prompt: it is now SPECIFIED behavior (R12.1, amended 2026-09-09), so changing it would amend an approved release-gating spec. Do NOT add a prompt of any kind to the interrupt path. Do NOT restate the four levels in the footer or the run help. Do NOT make level 2 signal-reachable. Do NOT edit spec `c4gd2h`. Do NOT MODIFY ANY EXISTING ASSERTION in `tests/test_interrupt_menu.py` or `tests/test_oc_runipd.py`; add beside them only, and in particular do not relax the four `assertNotIn` footer assertions (F-14) to accommodate your wording; if your wording cannot satisfy them, change the wording. THE ONE PERMITTED NON-TEXT EDIT is adding `formatter_class=argparse.RawDescriptionHelpFormatter` to both hosts' `resume` subparsers if E-04 needs it (F-16); state it in V-04. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN, and this warning is not boilerplate here: `oc_runipd.py` and `agy_runipd.py` moved roughly 70 and 95 lines in a single day and are under live edit, this backlog item's own citations were already stale by up to 480 lines, and REVIEW FOUND THIS PLAN'S OWN CENTRAL FINDING STALE WITHIN TWO DAYS (F-11: the spec was amended the day after authoring). Treat every claim below as needing re-measurement, not just every line number. Find `render_continuation_hint`, `build_parser`, `render_run_summary_table`, `install_stop_signal_handlers`, `_sigint`, `interrupt_menu_is_safe`, `render_request_accepted` and `prompt_interrupt_action` by name. Find the `main` interrupt handler by its "durable run state was preserved" text.

SHARED CHECKOUT WARNING: both runner modules are among the most heavily edited files in this repository and live runs may be editing them now. Confirm each target text is present as quoted before editing; if it has changed, STOP and report rather than reconciling someone else's in-flight edit.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved wqq8ua --by-human --message ...`) before execution. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, backlog `1m3nul` (carried as `- From-Backlog:`) may be closed `done`: this plan delivers every surviving part of it, the rest having already shipped, and the interrupt-path question it uncovered is NOT part of that item's ask and lives on as backlog `4awwg4` (whose primary claim the R12 amendment has since made stale; see F-17). That item carries no release gate, so none is inherited.

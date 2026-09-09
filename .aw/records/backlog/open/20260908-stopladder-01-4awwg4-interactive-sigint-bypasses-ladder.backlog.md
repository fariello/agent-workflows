- Id: 4awwg4
- Status: open
- Set: stopladder
- Priority: high
- Work-Kind: bug
- Summary: on a TTY the first Ctrl-C requests level 4 (now-force), not level 1: the interactive interrupt menu bypasses SIGINT_LADDER entirely, contradicting spec c4gd2h R12

## Workflow history
- 2026-09-08 created (aw backlog): Found while graduating backlog 1m3nul (plan wqq8ua), which deliberately does NOT fix it: resolving this means either removing shipped maintainer-authored behavior (646be41f) or amending an approved spec requirement, and neither is an agent's call. Filed high because it is a correctness and spec-conformance defect on the operator's primary escape path, not a documentation gap.

PARTLY OBSOLETE 2026-09-09, AND THE SEVERITY DROPS. Commit `42c975b2` ("render_stream, runner_stop:
fix Statusline pause deadlock and provide 4-choice interrupt menu") landed after this item was filed and
fixed THE HARM, though not the spec conformance. Read this header before acting on the body below: the
Summary line is now wrong in its central claim.

WHAT CHANGED. The menu gained a FOURTH choice and `_sigint` now routes it to level 1:

    1. Resume?
    2. Finish current item, clean up, and exit?     <- NEW, records LEVEL_AFTER_CALL
    3. Clean up and exit?
    4. Exit, leaving a mess?

At `runner_stop.py:1962-1964`, `INTERRUPT_ACTION_FINISH_CURRENT` records `LEVEL_AFTER_CALL` and returns
without raising. So the gentle "let the in-flight turn finish" behavior that spec R12 promises for a
first Ctrl-C IS NOW REACHABLE on a TTY, which it was not when this item was filed. The measured harm in
the Summary ("the first Ctrl-C requests level 4") is FIXED: choosing 2 requests level 1, and only
choices 3 and 4 record `LEVEL_NOW_FORCE`.

WHAT SURVIVES, and it is narrower and less urgent. The ladder is still BYPASSED on a TTY: `_sigint`
(`runner_stop.py:1954`) still branches on `is_interactive` and returns before `SIGINT_LADDER` is ever
indexed (`:1971-1972`), so on a terminal the escalation sequence R12 specifies (1 -> 3 -> 4 across
repeated presses) does not run. Two consequences remain:

  1. SPEC R12 IS STILL NOT SATISFIED AS WRITTEN. R12 (`c4gd2h:106`) says "First SIGINT (Ctrl-C) requests
     level 1. Repeated SIGINT escalates 1 -> 3 -> 4, with a printed hint that pressing again stops
     harder." The shipped interactive behavior is a MENU, not an escalating ladder, and there is no
     printed escalation hint because there is no escalation. The spec text describes a design the code
     deliberately no longer implements on a TTY.
  2. LEVEL 2 (after-set) IS UNREACHABLE FROM THE MENU, as it is from the ladder. That is consistent with
     the documented decision at `runner_stop.py:1617-1620` ("level 2 is reachable ONLY out-of-band via
     `stop --after-set`"), so it is not a new defect, just a thing to state.

REPEATED Ctrl-C IS HANDLED, so the impatient-operator case is safe: `prompt_interrupt_action`
(`:1840-1842`) catches a second `KeyboardInterrupt` during the prompt and returns `CLEANUP` rather than
asking again.

WHAT THIS ITEM IS NOW, restated so nobody re-reads the stale Summary as live: a SPEC-VERSUS-CODE
RECONCILIATION, not a correctness bug. The remaining decision is unchanged in KIND but much lower in
stakes: either amend R12 to describe the interactive menu as the TTY path (keeping the ladder as the
non-interactive path, which is what the code does today and is defensible, since an explicit menu is
arguably better UX than an invisible escalating ladder), or restore the ladder on a TTY and drop the
menu. The first is now clearly the better option BECAUSE the menu delivers R12's INTENT (a first Ctrl-C
can stop gently) through a different mechanism. Still a maintainer call: it means editing an approved,
release-gating spec, or deleting maintainer-authored behavior.

SUGGESTED REPRIORITIZATION: `high` -> `low`, since nothing is broken for an operator and the surviving
work is documentation of a design that already exists. Left at `high` pending the maintainer's read,
because dropping a priority on someone else's filed severity is not an agent's call either.

ORIGINAL ITEM TEXT FOLLOWS, whose Summary and first paragraph are now superseded by the above.

A MAINTAINER DECISION, WHICH IS WHY IT IS AN ITEM AND NOT A PLAN. Two shipped things disagree, and
choosing between them means either deleting behavior the maintainer wrote by hand or amending an
approved spec requirement. An agent may not pick.

THE CONFLICT, verified at HEAD `fac69fbd` by reading both sides.

SIDE 1, THE SPEC. `c4gd2h` R12 (`:106`) states: "First SIGINT (Ctrl-C) requests level 1. Repeated SIGINT
escalates 1 -> 3 -> 4, with a printed hint that pressing again stops harder." The code implements that
ladder as `SIGINT_LADDER = (LEVEL_AFTER_CALL, LEVEL_NOW, LEVEL_NOW_FORCE)` (`runner_stop.py:1620`),
whose own comment (`:1616-1619`) explains that level 2 is deliberately absent because the ladder is
1 -> 3 -> 4. The spec carries `- Blocks-Release: next` and `- Status: implementing`.

SIDE 2, THE CODE THAT BYPASSES IT. `_sigint` (`runner_stop.py:1936-1953`) computes
`is_interactive = (sys.stdin.isatty()) or os.environ.get("AW_FORCE_INTERACTIVE_INTERRUPT") == "1"` and,
when true, RETURNS BEFORE EVER INDEXING `SIGINT_LADDER`: it calls `handle_interactive_interrupt`, and
then for choice 1 (clean up and terminate) and choice 2 (terminate without cleanup) it records
`LEVEL_NOW_FORCE` and raises. Choice 3 resumes. The ladder lines (`:1954-1955`,
`index = min(_SIGINT_PRESSES, len(SIGINT_LADDER)) - 1`) are reached only on the NON-interactive path.

THE CONSEQUENCE, stated plainly: ON ANY TERMINAL, an operator's FIRST Ctrl-C requests LEVEL 4
(`now-force`), the most violent level, whose own help says the in-flight turn's "outcome becomes
indeterminate and needs reconciliation before a resume". R12 promises level 1, which lets the in-flight
turn FINISH. So the documented gentle-first behavior does not exist where almost every human uses it,
and `SIGINT_LADDER` is effectively dead code on a TTY.

PINNED BY A TEST, so this is intended behavior rather than an accident:
`tests/test_interrupt_menu.py:332-355` (`InteractiveSigintSignalTests::test_interactive_sigint_actions`)
sets `AW_FORCE_INTERACTIVE_INTERRUPT=1` and asserts exactly this, including
`mock_request.assert_called_with(run_dir, runner_stop.LEVEL_NOW_FORCE, "")` for choice 1.

PROVENANCE. The interactive menu shipped in `646be41f` ("runner: add interactive Ctrl-C menu with
cleanup, terminate, and resume options", 2026-09-05), a direct maintainer commit with an empty body.
I could find no plan carrying it (`grep -rn "prompt_interrupt_action\|INTERRUPT_ACTION"` over
`.aw/records/plans/` returns nothing) and no spec requirement authorizing it (spec `c4gd2h` contains no
mention of a prompt or menu). Note the ADDED IRONY, worth recording because it shows how this was
missed: backlog item `1m3nul`, written the SAME DAY, lists "an interactive prompt on Ctrl-C" under
"EXPLICITLY NOT WANTED", giving two reasons, and the prompt shipped anyway.

WHAT MUST BE DECIDED, and these are genuinely exclusive:
  1. KEEP THE MENU AND AMEND R12, if the maintainer prefers an explicit choice at interrupt time to a
     silent ladder. R12 would then have to describe the interactive path (menu) and the
     non-interactive path (ladder) separately, and the menu's mapping of "clean up and terminate" onto
     LEVEL 4 rather than a gentler level should be re-examined, since a user choosing "clean up"
     plausibly expects the in-flight turn to be allowed to finish.
  2. REMOVE OR GATE THE MENU so the ladder governs Ctrl-C as R12 requires, perhaps keeping the menu
     behind an opt-in flag rather than defaulting to it on every TTY.
  3. RECONCILE IN THE MIDDLE: keep the menu but map its choices onto the LADDER (first Ctrl-C offers
     the level-1 wind-down as the default choice), which would satisfy R12's intent while keeping the
     explicit prompt.

WHY 1m3nul DID NOT FIX THIS (so this is not a dropped ball). `1m3nul` is a DISCOVERABILITY item and its
graduated plan `wqq8ua` is text-only on three surfaces. That plan's E-01 exists precisely because of
this conflict: it requires every operator-facing sentence to be TRUE ON BOTH the interactive and
non-interactive paths, so that no new documentation asserts the ladder governs a terminal. That keeps
the docs honest without pre-empting this decision.

NOT A RELEASE BLOCKER AS FILED, and deliberately so: the stop protocol works, cleanup is unconditional
at every level, and durable state is preserved on every path, so nothing is lost or corrupted. What is
wrong is that the operator gets a harder stop than the spec promises. If the maintainer judges the
in-flight-turn indeterminacy on a first Ctrl-C to be release-relevant, set `--blocks-release next`;
note spec `c4gd2h` itself already carries that gate.

VERIFY WITH: read `runner_stop.py:1936-1955` and confirm the interactive branch returns before
`SIGINT_LADDER` is indexed; read spec `c4gd2h` R12; run
`python3 -m pytest tests/test_interrupt_menu.py` (green today, `tests/test_interrupt_menu.py` plus
`test_runner_stop_triggers.py` and `test_statefork_dh0uno.py` measured at `72 passed`).

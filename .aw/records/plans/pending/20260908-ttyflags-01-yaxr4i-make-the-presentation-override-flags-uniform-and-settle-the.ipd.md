# IPD: Make the presentation override flags uniform and settle the documented non-TTY mode rule

- Date: 2026-09-08
- Kind: child
- Concern: The presentation overrides are inconsistent per command, which is worse than uniformly absent because it cannot be scripted around. `--no-color` is declared once on the shared `common` parent and inherited almost everywhere, but 25 subcommands do not inherit it, so `aw oc run --no-color` is a usage error today while `aw attention --no-color` works, and the gap lands exactly on the long-running driver commands whose output a user most wants to capture. `--color` exists only as the `FORCE_COLOR` env var and has no flag form. `--tty` has no equivalent at all. Underneath, a published contract and the code disagree: `docs/cli-output-contract.md` and `select_output`'s own docstring both state that non-TTY stdout selects AGENT mode, and the code never calls `stdout.isatty()` for mode selection at all.
- Scope: Close the mechanical gap and the styling gap, and SETTLE the doc-versus-code divergence before any `--tty` semantics are specified. IN: `--no-color` on the 25 missing subcommands; a `--color` flag as its mutually exclusive twin threaded through the existing color engine; a parser-walk test asserting the trio's presence on every non-hidden subcommand; and a decision on the non-TTY mode rule with docs and code made to agree. OUT: `--tty` itself and any change to interactive prompting, both of which depend on that decision and on a maintainer ruling.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/term.py, agent_workflows/result_types.py, docs/cli-output-contract.md, tests/test_term.py, tests/test_output_contract.py, tests/test_flag_surface_uniformity.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: ttyflags
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: yaxr4i
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
- From-Backlog: isg0kg

## Workflow history
- 2026-09-19 executed (opencode its_direct/pt3-claude-opus-5-1m-us): all 8 E-items performed, all 8 V-items verified with pasted evidence; `aw ipd lint --phase pre-transition` conforms with ZERO findings. Bare suite: `1 failed, 7333 passed, 3 skipped, 2 xfailed`, the single failure (`test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`) PROVEN pre-existing by reproducing it identically with this work stashed; it reads other agents' `reaskscore` plans, which this lane never touches. Terminal transition left to the runner, which owns begin/finalize for a managed lane (`aw ipd begin` refused here with `AW-LIFECYCLE-ROLE-001`).
  THE PLAN'S CENTRAL MECHANISM WAS WRONG AND THE FIX IS DIFFERENT FROM WHAT E-01 SPECIFIES. E-01 said to add `parents=[common]` to the subcommands lacking it, and the review hardened that to "NINE registration edits, not 25". MEASURED: that change makes the parser WALK see the flag and leaves the COMMAND BROKEN. With `parents=[common]` on `p_oc_runipd`, `aw oc run --no-color status` still exited 2 with `runipd: error: unrecognized arguments: --no-color`, because all 11 non-hidden objects in the gap are host-driver leaves whose argv `cli._dispatch` forwards VERBATIM to another program's parser BEFORE `parse_args` runs. So the flags are now CONSUMED in `_dispatch` (`_consume_presentation_flags`) and published process-wide (`term.set_color_override`), and the forwarded leaves deliberately declare NOTHING, because `tests/test_run_dispatch.py` requires a route to own zero flags and `aw oc run --help` renders the DRIVER's help, making a declaration there invisible decoration. Recorded as decision `1-yaxr4i-D1`; had the plan been followed literally, a green parser-walk test would have shipped over a still-broken CLI.
  THE GAP HAD GROWN AGAIN, for the fourth measurement in a row: item 18 of 175, plan 25 of 219, review 25 of 219, execution 29 of 229 (the four `integrate` leaves are new since review). That is the strongest possible argument for E-04 being the durable deliverable, and it is why the new test asserts a LOWER BOUND on the subcommand count rather than the plan's expected 219.
  E-08's LETTER WAS DEVIATED FROM, DELIBERATELY (decision `1-yaxr4i-D3`): the exemption is TWO closed named sets rather than one, because 28 forwarded leaves DO accept the flags but must not DECLARE them. E-08's actual property is preserved and mutation-tested: both lists are closed named sets, not predicates, so a 30th flagless command fails until a human decides. This is the one place a reviewer may wish to check my reading of intent.
  ONE SHIPPED TEST WAS DELIBERATELY CHANGED, named and justified: `tests/test_output_contract.py` asserted the literal heading `Automatic Non-TTY Migration Policy (Hard Cutover)`, i.e. it PINNED THE FALSE PROMISE that E-05 exists to retract. It now asserts the retraction is explicit. No other assertion in that file was touched, and `tests/test_output_mode.py` (which owns the `select_output` truth table) passes UNMODIFIED.
  TWO BACKLOG ITEMS FILED so this plan's deferred obligations survive its own execution: `svqhmp` (`--tty` as two separate axes behind one interactivity resolver) and `zy1okf` (the latent `conflict_handler="resolve"` silent-overwrite hazard, F-14, re-measured as having no live collision). OQ-02 moved `open` -> `resolved` with measured exit-2 evidence on both the parsed and the forwarded path.
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-10 readiness re-check (opencode its_direct/pt3-claude-opus-5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: `plan_readiness.has_unresolved_blocking_question` -> False; `review_findings.subject_gating_blocks` -> empty; `plan_readiness.newest_verdict` polarity -> neutral (not negative). Specifically, its blocking OQ-01 was answered on 2026-09-10 (correct the document, retract the auto-switch explicitly) and the finding it escalated, PR-001, is now closed in review round 2. Performed at HEAD `5692797e` at the maintainer's explicit instruction of 2026-09-10, who was shown that 12 of 15 `no-go` plans were held by stale bookkeeping and chose to have them fixed with evidence recorded rather than re-reviewed. This is the SECOND such cleanup in one session; the durable fix is plan `qhy3i3` E-07, authored and awaiting approval. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-09-10 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: REVIEWED - OPEN QUESTIONS; PR-001..PR-008 fixed; OQ-01 remains OPEN (maintainer ruling required, no interactive channel this run); readiness no-go
- 2026-09-10 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; readiness NO-GO. PR-001..PR-008 FIXED; OQ-01 remains OPEN and is the sole blocker.
  THE PLAN'S TECHNICAL DIAGNOSIS IS ACCURATE IN EVERY PARTICULAR, WHICH IS UNUSUAL AND WORTH RECORDING. I re-measured independently rather than trusting it, and all of it held: 25 of 219 nested subcommands lack `--no-color`, with the SAME 25 names; `--color` and `--tty` are both at 0 of 219; a piped `select_output` gives `mode=OutputMode.HUMAN color=False` while a TTY gives `HUMAN color=True`; and `result_types.py` contains exactly TWO `isatty` mentions, both inside the docstring that makes the false claim. The doc-versus-code divergence is real and total.
  THE STRUCTURAL LINTER FAILED THE PLAN AT `author` PHASE AND THAT IS THE HEADLINE. `aw ipd lint --phase author` exits 1 on `IPD-Q501`: OQ-01 is `Blocking: yes` and still `open`, so `aw ipd begin` is blocked at every checkpoint. The plan could not have been executed as it stood. I did NOT resolve the question, because it is not resolvable from repository evidence: Option A knowingly breaks existing consumers and Option B retracts a recorded maintainer decision, and choosing between a compatibility break and a contract retraction is the maintainer's call on risk appetite and published promises. This run had no interactive channel, so per the workflow's non-interactive rule the question stays OPEN, the verdict is REVIEWED - OPEN QUESTIONS, and readiness is NO-GO.
  I DID ADD THREE MEASUREMENTS TO MAKE THAT RULING EASIER. The divergence is total rather than half-built (no branch exists to finish, so Option A is a new feature not a bug fix); the shipped behavior was confirmed on real commands (`aw check reviews` piped emits human text; only `--agent` emits JSONL); and Option A's in-repo blast radius is small but nonzero, since `docs/cli-migration.md:50` and `docs/cli-human-guide.md:103` both document piping `aw` and reading prose and would need rewriting. Those two paths are now named in Deferred with the condition attached.
  THE MOST USEFUL MECHANICAL FINDING SHRINKS E-01 BY MORE THAN HALF. The 25 missing NAMES are only TEN DISTINCT PARSER OBJECTS, verified by `id()`: the four `oc`/`opencode` run leaves are ONE object and the six `agy`/`antigravity` run leaves are ONE object. So E-01 is NINE registration edits, not 25 and not the "roughly half" the plan estimated, and editing per name would touch the same object repeatedly. I also found a latent hazard the plan missed: `conflict_handler="resolve"` is set on EVERY parser, so adding `parents=[common]` to a parser that already declared one of the three flags would SILENTLY replace a definition instead of erroring. Measured: no collision exists today, and E-01 now carries a re-check.
  E-02's MECHANISM IS VERIFIED RATHER THAN ASSUMED: a mutually-exclusive group declared on an `add_help=False` parent DOES propagate through `parents=[...]`, and passing both flags raises `SystemExit(2)`. So OQ-02's structural-refusal requirement is satisfiable exactly as written.
  ALSO FIXED: the suite baseline was stale AND carried an open-ended environmental-failure allowance (`1 failed, 5648 passed` plus "expect additional environmental failures"), while the real baseline is `5959 passed, 3 skipped, 2 xfailed` with ZERO failures; that combination is how a genuine regression gets waved through. The two `IPD-Z602` density advisories were treated as actionable rather than dismissed: E-04's exemption-list concern is now its own item E-08, with a mutation test proving the exemption is a gate and not a hole. E-07 was noted to be a REGRESSION GUARD, since its byte-identity property already holds today.

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `isg0kg`. GATE NOTE: this item carries NO `- Blocks-Release:`, so this plan inherits none, despite `Priority: high`. NOTHING IN THIS ITEM IS OBSOLETE and nothing covers it. RE-MEASURED AT HEAD `a2e0438a` by walking the built parser tree exactly as the item did, and THE GAP HAS GROWN: the item reports `--no-color` missing on 18 of 175 nested subcommands; I measure 25 of 219 missing, and the list has changed shape as well as size. It now includes `run as`, `run ipd`, `oc review`, `agy review`, `opencode review` and `antigravity review`, which did not exist when the item was written, alongside the 9-doubled host-driver set it named. So the mechanical fix is broader than filed and, more importantly, THE GAP IS ACTIVELY REGROWING: every new nested subcommand added since has missed `common` too, which is precisely why E-04's parser-walk test is the durable deliverable rather than the flag additions themselves. `--color` and `--tty` remain at 0 of 219, as filed. THE DOC-VERSUS-CODE DIVERGENCE IS CONFIRMED LIVE and is the reason this plan deliberately does NOT specify `--tty`: measured by execution, non-TTY stdout gives `mode=OutputMode.HUMAN color=False` and TTY stdout gives `mode=OutputMode.HUMAN color=True`, i.e. piping yields monochrome HUMAN text, never JSONL. Meanwhile `docs/cli-output-contract.md:18` publishes "non-TTY stdout (pipe/redirect) => agent", `:161` calls it a maintainer decision adopted "immediately upon release", and `select_output`'s docstring repeats it at `result_types.py:75`. I verified the code has no such branch at all: `result_types.py` contains exactly TWO `isatty` mentions, both inside that docstring (`:75`, `:76`), and the only real TTY consultation is the COLOR one via `should_color(out_stream)` at `:159`. The item is right that this must be settled first: if the documented rule were implemented, `--tty` would flip AUDIENCE MODE as a side effect, turning a styling override into a much larger behavior change. I also re-counted the interactivity axis: 49 `isatty` references across the package (the item said 44), 18 of them in `cli.py` alone, which is why E-06 records the ONE-resolver requirement rather than letting a future `--tty` sprinkle flag checks across them.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the same presentation flags work on every command, and make the published output contract true. The user-visible payoff is that `aw` output becomes reliably capturable in a log, a CI job or a demo recording; the durable payoff is a test that stops the coverage gap regrowing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: close the mechanical gap

- [x] E-01 Give the subcommands that do not inherit `common` their `parents=[common]`, in `agent_workflows/cli.py`. RE-ENUMERATE THE LIST AT EXECUTION TIME rather than trusting this plan: the item measured 18 and this plan measured 25 at `a2e0438a`, so the set is moving. Re-measured at review (HEAD `5075613e`): still 25 of 219, and the NAMES are unchanged from this plan's list, so the set has held for now.
  THE 25 NAMES ARE ONLY **10 DISTINCT PARSER OBJECTS**, AND 9 OF THEM NEED FIXING. This plan estimated "roughly half"; the measured answer is much better than that and is exact, because alias groups share ONE parser object (verified by `id()`). The 10 groups: `run as`; `run ipd`; {`oc runipd`, `oc run`, `opencode runipd`, `opencode run`} (ONE object, all four names); {`oc review`, `opencode review`}; {`agy runipd`, `agy run`, `agy runagy`, `antigravity runipd`, `antigravity run`, `antigravity runagy`} (ONE object, all six); {`agy review`, `antigravity review`}; {`agy sessions`, `antigravity sessions`}; {`agy view`, `agy view-antigravity-jsonl`, `antigravity view`, `antigravity view-antigravity-jsonl`}; {`agy exec`, `antigravity exec`}; and `__complete`. So this is NINE registration edits, not 25 and not "about 12". Verify the grouping with `id()` before editing, because editing per NAME would touch the same object repeatedly and could double-add the flag.
  EXCLUDE `__complete` DELIBERATELY: it is the hidden shell-completion command and the item is explicit that it correctly lacks the flag.
  `conflict_handler="resolve"` IS SET ON EVERY PARSER (`_AwArgumentParser.__init__`), WHICH IS A SILENT-OVERWRITE HAZARD. If a target parser already declared its own `--no-color`/`--agent`/`--json`, adding `parents=[common]` would SILENTLY REPLACE one definition instead of erroring. MEASURED: none of the 25 currently declares `--agent` or `--json`, so no collision exists today. Re-check that at execution time rather than assuming, since the set has moved before.
  - Depends on: none
  - Expected outcome: `aw oc run --no-color` and `aw agy run --no-color` parse successfully; every non-hidden subcommand accepts `--no-color`; `__complete` still does not; the fix is applied once per PARSER OBJECT (9 edits) with the `id()` grouping and the no-collision re-check both recorded.
  - Execution state: performed

- [x] E-02 Add `--color` to the `common` parent as the MUTUALLY EXCLUSIVE twin of `--no-color`, so both are inherited by construction rather than added per command. LOCATE `common` BY SYMBOL inside `_build_parser`: the citation `cli.py:789-794` in this plan is STALE; at HEAD `5075613e` the `--no-color` declaration is at `cli.py:804-808`.
  THE MECHANISM IS VERIFIED TO WORK AND TO GIVE EXIT 2, so implement it rather than re-deriving it. Measured: a `add_mutually_exclusive_group()` declared on an `add_help=False` PARENT does propagate through `parents=[...]` to a subparser, and passing both flags raises `SystemExit(2)` with `argument --no-color: not allowed with argument --color`. `_AwArgumentParser.error` also ends in `self.exit(2)`, so the exit code is 2 from both paths and OQ-02's requirement is satisfied structurally. Passing both must be a usage error with exit 2, not a silent winner; use argparse's mutually-exclusive group so the refusal is structural. Thread the flag into the two existing seams rather than inventing a third: the `Term(color=...)` construction which already handles the `no_color` half, and `select_output`'s color resolution at `result_types.py:157-159`. `should_color` (`term.py:74-98`) needs an explicit override parameter so a flag can beat env detection WITHOUT the code setting `os.environ`, which would leak into subprocesses. NOTE the maintainer asked for 256-COLOR and no new capability tier is needed: `Term.color256` and the 16-color `colorize` are gated by the SAME single `self.color` boolean, so `--color` sets that one boolean. A distinct 16-versus-256 capability level is a SEPARATE question and must not be smuggled in.
  - Depends on: E-01
  - Expected outcome: `--color` forces color on where detection would disable it; `--no-color --color` exits 2; no `os.environ` mutation; the 256-color path is reached by the same boolean.
  - Execution state: performed

- [x] E-03 Write the PRECEDENCE down and enforce it: flag beats env beats detection. The env layer already implements `NO_COLOR` off unless `FORCE_COLOR` overrides (`term.py:83-88`), then `TERM=dumb`/unset off (`:90-92`), then `isatty()` (`:94-98`); the flag layer must sit ABOVE all of it. Record the resulting table in `docs/cli-output-contract.md`, which already owns this contract at `:18-34`, and pin it in `tests/test_term.py`, which ALREADY exercises the `NO_COLOR`/`FORCE_COLOR`/isatty matrix against fake TTY and pipe streams (`:46`, `:52`, `:56`, `:60`, `:65`), so a flag override slots straight into that harness rather than needing a new one.
  - Depends on: E-02
  - Expected outcome: a written precedence table matching a passing test matrix, covering flag-versus-env conflicts in both directions.
  - Execution state: performed

- [x] E-04 Add the PARSER-WALK TEST asserting that every non-hidden subcommand, nested included, accepts the presentation flags. Walk the built parser tree recursively rather than spot-checking.
  WHY A RECURSIVE WALK IS THE DURABLE FIX: the item measured 18 missing, this plan measured 25, and the newly-missing ones (`run as`, `run ipd`, the four `review` leaves) are commands added AFTER the item was filed, so each new nested subcommand has been missing `common` as it landed. A per-command spot check demonstrably did not catch this.
  THE WALK IS ALREADY WRITTEN AND VERIFIED, so reuse this shape rather than inventing one: recurse `parser._actions`, descend into every `argparse._SubParsersAction.choices`, and test membership with `any(flag in (a.option_strings or []) for a in sub._actions)`. That exact walk reproduces 219 subcommands and the 25-missing set at review, so a test built on it is known to see what this review saw.
  - Depends on: E-01, E-02
  - Expected outcome: a recursive parser-walk test asserting the presentation flags on every non-hidden subcommand, reproducing the 219 total, that FAILS pre-change naming the 25 and passes after E-01/E-02.
  - Execution state: performed

- [x] E-08 DECLARE THE EXEMPTION LIST EXPLICITLY IN THAT TEST, as a closed named set rather than a predicate, so an exemption is a deliberate reviewable decision instead of a silent skip. Today the only exemption is `__complete`, the hidden shell-completion command, which the item says correctly lacks the flag.
  MAKE IT A CLOSED LIST OF NAMES, NOT A RULE LIKE "SKIP ANYTHING HIDDEN". A predicate would silently absorb the next hidden or newly-added subcommand, which is precisely the regrowth this plan exists to stop: the gap grew from 18 to 25 exactly because new leaves inherited nothing and nobody was forced to notice. A closed list makes a 26th command FAIL the test until someone decides about it.
  MUTATION-CHECK THE EXEMPTION so it is not decoration: add a second fake subcommand with no presentation flags and show the test FAILS naming it, then revert. A guard that cannot fail proves nothing.
  - Depends on: E-04
  - Expected outcome: the exemption is a closed named set containing only `__complete`, with a comment stating why; a mutation adding an unlisted flagless subcommand FAILS the test and names it; reverting restores green.
  - Execution state: performed

### Task group 2: settle the divergence before specifying --tty

- [x] E-05 SETTLE THE NON-TTY MODE RULE and make docs and code agree, which the item requires be done BEFORE `--tty` is specified. The published contract says non-TTY stdout selects AGENT mode: `docs/cli-output-contract.md:18` ("non-TTY stdout (pipe/redirect) => agent"), `:24-27`, and `:161` ("Per maintainer decision OQ-01, non-TTY stdout adopts `aw.agent/v1` JSONL immediately upon release"), with the same claim in `select_output`'s docstring (`result_types.py:75`). THE CODE DOES NOT DO IT: `result_types.py` contains exactly two `isatty` mentions and both are inside that docstring; the only real TTY consultation is `should_color(out_stream)` at `:159`, for COLOR. Measured: non-TTY stdout gives `mode=OutputMode.HUMAN color=False`. Only ONE of the two may stand. This item's job is to IMPLEMENT THE RULED ANSWER, not to choose: OQ-01 carries the choice to the maintainer because implementing the documented rule would change what every piped `aw` invocation emits, which is a breaking change for any existing consumer, while correcting the docs retracts a published maintainer decision.
  - Depends on: none
  - Expected outcome: docs and code state the same rule, with the maintainer's choice recorded and the losing text removed rather than left contradicting.
  - Execution state: performed

- [x] E-06 RECORD, and do not implement, the `--tty` design constraint, so a successor does not conflate the two axes. TTY-ness controls two unrelated things through two different streams: PRESENTATION keyed on stdout (`should_color`, `term.py:94-98`; the color resolution at `result_types.py:157-159`) and INTERACTIVITY keyed on stdin (49 `isatty` references across the package at `a2e0438a`, 18 in `cli.py` alone, plus `git_commit_helper._is_interactive`). The existing contract deliberately keeps them apart: `select_output`'s docstring (`:76`) says "`stdin.isatty()` controls interactive prompting, NOT audience/mode" and `docs/cli-output-contract.md:28` repeats it. So a single undifferentiated `--tty` boolean would silently weaken the non-interactive fail-safe that those call sites rely on, where `_confirm` currently DECLINES rather than prompting. Write the constraint into `docs/cli-output-contract.md` next to the precedence table: if `--tty` is ever added, it must NOT be one boolean, and the interactivity axis must route through ONE resolver rather than a flag check at each of the 49 sites.
  - Depends on: E-05
  - Expected outcome: the two-axis constraint and the one-resolver requirement are written into the published contract; no `--tty` flag is added and no prompting behavior changes.
  - Execution state: performed

- [x] E-07 Verify NO REGRESSION in the machine surfaces, because `--color` and the E-05 decision both touch `select_output`, which every renderer consumes. `tests/test_output_contract.py` owns the `select_output` mode/color contract and must pass unmodified except where E-05 deliberately changes it (and any such change must be called out, not quietly absorbed). Confirm that `--agent` and `--json` remain unaffected by `--color`/`--no-color` (both are styling-only per `docs/cli-output-contract.md:34`), that an `aw.agent/v1` record never gains ANSI bytes, and that the exit codes of a representative sample of commands are unchanged by any presentation flag.
  - Depends on: E-03, E-05
  - Expected outcome: machine output is byte-identical under every presentation flag combination; any deliberate `test_output_contract.py` change is named and justified.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `--no-color` is declared ONCE on the shared `common` parent (`cli.py:788-794`) and inherited via `parents=[common]`, which is why coverage is nearly total and why both the gap and its fix are mechanical.
- The color ENGINE is already correct and complete: `should_color` (`term.py:74-98`) implements `NO_COLOR` unless `FORCE_COLOR`, then `TERM` capability, then `isatty()`. This item adds a flag SURFACE over a working engine; it does not need new color logic.
- `Term.color256` and the 16-color `colorize` share ONE `self.color` boolean, so forcing color needs no new capability tier.
- The two TTY axes are deliberately separate, stated in both `select_output`'s docstring and the published contract. That separation is a fail-safe: 18 `cli.py` sites plus `git_commit_helper._is_interactive` decline rather than prompt when non-interactive.
- `git_commit_helper._is_interactive` already accepts an explicit override, which is the precedent for the ONE-resolver shape any future `--tty` should use.
- `docs/cli-output-contract.md` is the published contract for this behavior (`:18-34`) and `docs/cli-agent-protocol.md` covers the machine surface; a change here must update the former.
- The test harnesses already exist and are the right homes: `tests/test_term.py` exercises the env/isatty matrix against fake streams, and `tests/test_output_contract.py` owns the `select_output` contract.
- The `awcliux` Set (executed) added `STATUS_COLOR_256` and `Term.color256`, i.e. the 256-color path this item exposes; it is prior art, not a conflict.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | THE GAP HAS GROWN AND IS REGROWING: the item reports `--no-color` missing on 18 of 175 nested subcommands; measured 25 of 219 at HEAD, and the newly-missing entries (`run as`, `run ipd`, `oc review`, `agy review`, and the `opencode`/`antigravity` twins) postdate the item. | parser-tree walk at `a2e0438a` |
| F-2 | So each new nested subcommand has been landing WITHOUT `common`, which is why the parser-walk test is the durable fix rather than the flag additions. | comparison of the item's 2026-09-01 list against the measured list |
| F-3 | `--color` and `--tty` are both at 0 of 219 subcommands, exactly as filed. | parser-tree walk at `a2e0438a` |
| F-4 | `--no-color` is declared once on `common`, confirming the fix is mechanical. | `cli.py:788-794` |
| F-5 | THE PUBLISHED CONTRACT AND THE CODE DISAGREE, confirmed live: docs say non-TTY stdout selects AGENT, and measured behavior is `mode=OutputMode.HUMAN color=False` on a pipe. | `docs/cli-output-contract.md:18`, `:161`; measured via `select_output` with a fake pipe at `a2e0438a` |
| F-6 | The code has NO mode-selection TTY branch at all: `result_types.py` contains exactly two `isatty` mentions and both are inside the docstring that makes the false claim; the only real consultation is for COLOR at `:159`. | read at `a2e0438a` |
| F-7 | The divergence must be settled BEFORE `--tty`, because implementing the documented rule would make `--tty` flip AUDIENCE MODE as a side effect, turning a styling override into a breaking change. | the item's own analysis, verified against F-5/F-6 |
| F-8 | The interactivity axis is large and must not grow per-site flag checks: 49 `isatty` references across the package, 18 in `cli.py` alone. | measured at `a2e0438a` (the item counted 44) |
| F-9 | The color engine already implements the wanted precedence, so `--color` is a missing surface rather than missing logic. | `term.py:83-98` |
| F-10 | The 256-color requirement needs no new tier: both palettes are gated by one boolean. | `Term.color256` and `colorize` share `self.color` |
| F-11 | Nothing covers this item: no pending or approved plan and no spec touches `--color`, `--tty`, or the `common` parent's flag set. | grep over `.aw/records/plans/pending/` and `.aw/records/specs/` at `a2e0438a` |
| F-12 | EVERY MEASUREMENT IN THIS PLAN RE-VERIFIED AT REVIEW (HEAD `5075613e`), which is unusual and worth recording: 25 of 219 missing `--no-color` with the SAME 25 names; `--color` and `--tty` both at 0 of 219; a piped `select_output` gives `mode=OutputMode.HUMAN color=False` and a TTY gives `HUMAN color=True`; `result_types.py` contains exactly TWO `isatty` mentions, both inside the docstring making the false claim. The plan's technical diagnosis is accurate. | independent parser walk; `select_output` driven with fake pipe/TTY streams; `grep -n isatty agent_workflows/result_types.py` |
| F-13 | THE 25 NAMES ARE ONLY **10 DISTINCT PARSER OBJECTS**, so E-01 is NINE edits, not 25 and not the "roughly half" this plan estimated. Alias groups share one object (verified by `id()`): `oc run`/`oc runipd`/`opencode run`/`opencode runipd` are ONE parser; the six `agy`/`antigravity` run leaves are ONE parser. Editing per NAME would touch the same object repeatedly. | grouped the 25 missing parsers by `id()` |
| F-14 | `conflict_handler="resolve"` IS SET ON EVERY PARSER (`_AwArgumentParser.__init__`), so adding `parents=[common]` to a parser that already declared `--no-color`/`--agent`/`--json` would SILENTLY REPLACE a definition rather than error. Measured: none of the 25 declares any of the three today, so no collision exists, but the hazard is real and must be re-checked at execution time. | read `_AwArgumentParser.__init__`; checked all 25 for `--agent`/`--json` |
| F-15 | E-02's MECHANISM IS VERIFIED, INCLUDING ITS EXIT CODE. A mutually-exclusive group declared on an `add_help=False` parent DOES propagate through `parents=[...]`, and passing both flags raises `SystemExit(2)` with `argument --no-color: not allowed with argument --color`. `_AwArgumentParser.error` independently ends in `self.exit(2)`. So OQ-02's requirement is satisfiable structurally, as specified. | built a minimal parent/subparser reproduction and caught `SystemExit` |
| F-16 | THE SUITE BASELINE IS STALE AND ITS ALLOWANCE IS DANGEROUS. Re-measured at HEAD `781d70ae`: `5959 passed, 3 skipped, 2 xfailed`, ZERO failures, versus the plan's `1 failed, 5648 passed` plus an allowance for "additional environmental failures inside a lane worktree". A stale known-failure baseline plus an open-ended environmental allowance is how a real regression gets waved through. | bare `python3 -m pytest` in an isolated worktree |
| F-17 | E-07's BYTE-IDENTITY PREMISE HOLDS TODAY, so it is a regression guard rather than a fix: `aw check reviews --agent` and `aw check reviews --agent --no-color` produce byte-identical output containing ZERO ANSI escapes. | ran both and compared; counted `\x1b` occurrences |
| F-18 | TWO CITED LINE NUMBERS ARE STALE. `--no-color` is declared at `cli.py:804-808`, not `:789-794`. The `isatty` reference count is 51 package-wide, not 49 (the `cli.py` count of 18 is exact). The plan already mandates re-measuring, which is the right mitigation. | read `_build_parser`; re-counted `isatty` |
| F-19 | THE STRUCTURAL LINTER FAILED THE PLAN AT `author` PHASE, exit 1, on `IPD-Q501`: OQ-01 is `Blocking: yes` and still `open`, which blocks `aw ipd begin` at every checkpoint. Two `IPD-Z602` density advisories also fired, on E-01 and E-04. This is a GATE, not a note: the plan could not have been executed as it stood. | `aw ipd lint --phase author --agent` -> exit 1, 3 findings |

## Proposed changes (ordered, validatable)

1. Add `parents=[common]` to the 25 missing subcommands, excluding `__complete` (E-01).
2. Add `--color` on `common` as `--no-color`'s mutually exclusive twin, with an override parameter on `should_color` (E-02).
3. Write and pin the flag-beats-env-beats-detection precedence (E-03).
4. Add the parser-walk uniformity test with an explicit exemption list (E-04).
5. Settle the non-TTY mode rule and make docs and code agree (E-05).
6. Record the two-axis `--tty` constraint without implementing `--tty` (E-06).
7. Prove the machine surfaces are unaffected (E-07).

## Deferred / out of scope (with reason)

- `--tty` ITSELF. The item presents three options (presentation-only, both axes, or two separate flags) and asks the maintainer to rule; it also requires the doc-versus-code divergence be settled FIRST, because that decision changes what `--tty` would mean. Implementing it here would either guess the ruling or silently weaken the non-interactive fail-safe that 49 call sites rely on. E-06 records the constraint so the successor inherits the analysis rather than redoing it. CARRIER: backlog `svqhmp` (`--tty` as two separate axes behind one interactivity resolver), filed at execution so this obligation survives this plan reaching `executed`.
  - Carrier: svqhmp
- ANY CHANGE TO INTERACTIVE PROMPTING, including an `--interactive`/`--no-interactive` pair. Same reason: it is the second axis and depends on the same ruling. Note the fail-safe being protected is real, `_confirm` deliberately DECLINES and warns when non-interactive rather than proceeding silently. CARRIER: backlog `svqhmp`, which owns this axis together with `--tty` itself, since they are the same decision.
  - Carrier: svqhmp
- A DISTINCT 16-COLOR VERSUS 256-COLOR CAPABILITY TIER. The item explicitly says this must not be smuggled in; `--color` sets the one existing boolean. NO CARRIER NEEDED: this is a decision NOT to do something, not an outstanding obligation. Spec `uonrjg` section 9.3a already owns the depth-tier question if it is ever wanted.
  - Carrier-Declined: a decision NOT to add a capability tier, not an outstanding obligation; the item explicitly forbids it and `--color` sets the one existing boolean
- RETROFITTING THE `FORCE_COLOR`/`NO_COLOR` ENV LAYER. Already correct; this plan adds a flag layer above it. NO CARRIER NEEDED: nothing is outstanding, the existing layer is unchanged and is now documented as rung 2 of the published precedence table.
  - Carrier-Declined: nothing is outstanding; the env layer was already correct and is unchanged, now published as rung 2 of the section 1.1 precedence table
- CHANGING `conflict_handler="resolve"` ON `_AwArgumentParser` (F-14). It makes a duplicate option definition silently replace rather than error, which is a real latent hazard for any future `parents=` addition, but changing it repo-wide could surface duplicate definitions across 219 subcommands and is unrelated to this item's flags. E-01 mitigates it with a per-parser collision re-check instead; a general fix is its own item. CARRIER: backlog `zy1okf`. RE-MEASURED AT EXECUTION: no live collision exists (all 12 parser objects lacking `--no-color` were checked and none declared `--no-color`/`--agent`/`--json`), so the hazard remains latent.
  - Carrier: zy1okf
- REWRITING THE TWO IN-REPO DOCS THAT ASSUME HUMAN PIPED OUTPUT (`docs/cli-migration.md:50` documents `aw status | grep -i current`; `docs/cli-human-guide.md:103` documents `aw doctor | head`). These matter ONLY if OQ-01 is ruled Option A, in which case both examples become wrong and must be fixed in the same change. Recorded here so the ruling's true cost is visible; neither file is in `- Scope-Paths:` today because Option B (the recommendation) leaves both correct. RESOLVED AT EXECUTION, NO CARRIER NEEDED: OPTION B WAS RULED, so both examples remain accurate and neither file was touched. This row is now closed rather than outstanding.
  - Carrier-Declined: resolved at execution by the OQ-01 Option B ruling, which leaves both documented examples accurate, so neither file needed changing

## Scope check

- Over-scope: `docs/cli-output-contract.md` is edited by E-03, E-05 and E-06 although the item frames the work as flags. It is required: the item names that file as the owner of this contract, and E-05 exists precisely because the doc currently contradicts the code.
- Under-scope: `--tty` and the interactivity axis are analyzed and documented but not implemented (see Deferred), so this plan delivers two of the item's three requested flags plus the precondition for the third.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. THE BASELINE IS CLEAN, corrected at review: re-measured in an isolated worktree at HEAD `781d70ae`, a bare run is `5959 passed, 3 skipped, 2 xfailed` with ZERO failures. The figure previously recorded here (`1 failed, 5648 passed`, blaming a known `test_orchestrator_retirement` failure, plus an allowance for "additional environmental failures") is STALE; that module passes. Judge on the DELTA of failing NODE IDS, and with a clean baseline the only acceptable end state is zero failures. Do NOT carry forward the environmental-failure allowance: it would excuse a regression this plan caused.
- `python3 -m pytest tests/test_term.py tests/test_output_contract.py tests/test_flag_surface_uniformity.py` for the focused surface.
- The parser-walk enumeration re-run before and after, pasting the missing-subcommand count each time.
- A representative sample of the 25 fixed subcommands invoked with `--no-color` and with `--color`, exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`), since the whole point is that these are the long-running driver commands.
- `python3 -m agent_workflows check` must not gain a diagnostic.

## Spec / documentation sync

`docs/cli-output-contract.md` is the PUBLISHED contract for this behavior and is declared in `Scope-Paths` deliberately: E-03 adds the flag precedence table, E-05 removes whichever of the doc-or-code claims the maintainer retires, and E-06 records the two-axis `--tty` constraint. `docs/cli-agent-protocol.md` covers the machine surface and needs no change if E-07 holds (machine output byte-identical under presentation flags); if E-07 finds otherwise, that file enters the fence and the change must be justified. No `.spec.md` file governs the CLI presentation flags, so none is edited. NOTE that `select_output`'s docstring (`result_types.py:71-78`) is itself documentation making a false claim today, so E-05 must correct it in the same change; leaving it would move the contradiction from the docs into the code.

## Open questions

### OQ-01: Should non-TTY stdout select AGENT mode as documented, or should the documentation be corrected to match the code?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`): OPTION B, CORRECT THE DOCUMENT. Piped output stays human-readable and `--agent` remains the explicit way to get `aw.agent/v1` JSONL. Option A (implement the promise) was declined on blast radius, and a third option offered in the prompt (implement behind a deprecation window) was also declined, since the contract's own text specifies a hard cutover with no window, so that route would amend the document anyway while still delivering the break eventually.
  THE ASYMMETRY THAT DECIDED IT, re-verified at HEAD `aa65ae28` rather than carried from review. THE PROMISE HAS NEVER BEEN TRUE: `docs/cli-output-contract.md:159-163` states under "Automatic Non-TTY Migration Policy (Hard Cutover)" that "non-TTY stdout adopts `aw.agent/v1` JSONL immediately upon release with no deprecation window", while piping `aw att --type plan` today emits ordinary human prose. NOTHING CAN DEPEND ON THE DOCUMENTED BEHAVIOR because it never shipped; an UNKNOWN number of consumers depend on the actual behavior, including any external script, log capture or CI step that pipes `aw` and reads prose, which is invisible from inside this repository. THE CAPABILITY IS NOT LOST: `--agent` already emits the JSONL (verified), and this repository's own CI already uses the explicit flag (`.github/workflows/tests.yml:169`) rather than relying on the auto-switch, so the switch was convenience rather than capability.
  THE RETRACTION MUST BE EXPLICIT, NOT A QUIET DELETION, and this is an obligation on E-05 rather than a preference. The section records a maintainer decision adopted "immediately upon release"; removing it silently would leave a reader unable to tell whether the policy was reversed or lost in an edit. State in the document that the policy is RETRACTED, the date, and the reason (never implemented, nothing depends on it, `--agent` covers the need), so the next reader does not re-propose it as an unimplemented contract defect.
  DO NOT READ THIS AS A RULING THAT NON-TTY DETECTION IS UNWANTED. The maintainer retracted an AUTO-SWITCH promise, not the ability to detect a non-TTY, and the plan's remaining work on uniform presentation-override flags is untouched. A future proposal to make piped output machine-readable is not foreclosed; it would simply need its own decision and a migration story the retracted section never had.

### OQ-02: Should `--color` and `--no-color` be a mutually exclusive pair, or should the last flag win?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE, recorded so it is deliberate. The item specifies mutually exclusive with exit 2 ("`--no-color` with `--color` is a usage error, not a silent winner"), and that is the recommended and implemented choice: a silent winner makes a scripted invocation's behavior depend on argument order, which is exactly the unscriptability this item exists to fix. Implement mutual exclusion via argparse so the refusal is structural rather than hand-checked, and confirm the resulting exit code is 2 by measuring it UNPIPED.
  RESOLVED AND IMPLEMENTED AT EXECUTION (2026-09-19) AS SPECIFIED: mutually exclusive, exit 2. Measured UNPIPED: `aw attention --no-color --color` exit=2, `aw check reviews --color --no-color` exit=2, and `aw oc run --no-color --color status` exit=2. The message is identical on both paths: `agent-workflows: error: argument --color: not allowed with argument --no-color`. On the parsed path the refusal is STRUCTURAL (an argparse `add_mutually_exclusive_group` on the shared `presentation` parent). THE FORWARDED PATH NEEDED ITS OWN REFUSAL, which this question did not anticipate: those leaves never reach the group because `_dispatch` intercepts their argv first (see E-01), so `_consume_presentation_flags` reports both-seen and `_dispatch` renders the same message with the same exit code. Without that, `aw oc run` would have silently taken a winner while `aw attention` refused, which is exactly the per-command inconsistency this plan exists to remove.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the parser-walk enumeration BEFORE (naming the missing subcommands and their count; expect 25 of 219) and AFTER (count 1, only `__complete`). Paste the `id()` GROUPING showing the 25 names collapse to 10 distinct parser objects, and state that exactly NINE registration edits were made rather than 25. Paste the re-check that none of the target parsers already declared `--no-color`/`--agent`/`--json`, since `conflict_handler="resolve"` would otherwise SILENTLY replace a definition (F-14). Then paste at least four real invocations from the fixed set, including `aw oc run --no-color` and `aw agy run --no-color`, showing they no longer produce a usage error, with exit codes measured UNPIPED.
  - Observed evidence: PARSER WALK BEFORE (clean tree, HEAD `1c7de29a`): `total subcommands (nested incl): 229` /
    `--no-color: missing 29 of 229` / `--color: missing 229 of 229` / `--tty: missing 229 of 229`.
    The 29 names: `run as`, `run ipd`, `oc runipd`, `oc run`, `oc review`, `oc integrate`,
    `opencode runipd`, `opencode run`, `opencode review`, `opencode integrate`, `agy runipd`,
    `agy run`, `agy runagy`, `agy review`, `agy integrate`, `agy sessions`, `agy view`,
    `agy view-antigravity-jsonl`, `agy exec`, the six `antigravity` twins, and `__complete`.
    NOTE THE SET MOVED AGAIN, exactly as the plan predicted: the plan measured 25 of 219 and the
    item 18 of 175; the four `integrate` leaves are new since review.
    `id()` GROUPING: the 29 names are **12 distinct parser objects**:
      ['run as'] / ['run ipd'] / ['oc runipd','oc run','opencode runipd','opencode run'] /
      ['oc review','opencode review'] / ['oc integrate','opencode integrate'] /
      ['agy runipd','agy run','agy runagy','antigravity runipd','antigravity run','antigravity runagy'] /
      ['agy review','antigravity review'] / ['agy integrate','antigravity integrate'] /
      ['agy sessions','antigravity sessions'] /
      ['agy view','agy view-antigravity-jsonl','antigravity view','antigravity view-antigravity-jsonl'] /
      ['agy exec','antigravity exec'] / ['__complete'].
    COLLISION RE-CHECK (F-14, `conflict_handler="resolve"` silent-overwrite hazard): every one of
    the 12 reports `none` for `--no-color`/`--agent`/`--json`, so no definition could be silently
    replaced. Re-measured at execution time, not carried from review.
    THE PLAN'S STATED MECHANISM DOES NOT WORK, AND THIS IS THE CENTRAL FINDING (decision
    `1-yaxr4i-D1`). `parents=[common]` makes the parser WALK see the flag and leaves the command
    BROKEN, because all 11 non-hidden objects are host-driver leaves whose argv `cli._dispatch`
    forwards VERBATIM before `parse_args` runs. Measured by patching `parents=[common]` onto
    `p_oc_runipd` alone: the walk then reported `oc run declares --no-color: True` while
    `aw oc run --no-color status` still exited 2 with
    `runipd: error: unrecognized arguments: --no-color`. Reverted.
    SO THE FIX IS CONSUMPTION, NOT DECLARATION: `_consume_presentation_flags` strips the two color
    tokens in `_dispatch` before every interception, and `term.set_color_override` publishes the
    decision. NINE REGISTRATION EDITS WERE NOT MADE: the forwarded leaves deliberately declare NO
    flags, because `tests/test_run_dispatch.py::test_each_added_route_owns_no_flags_and_declares_its_contract`
    requires a route to own zero flags (it FAILED when they were added, and passes now), and
    `aw oc run --help` renders the DRIVER's help so a declaration there is invisible decoration.
    REAL INVOCATIONS, exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`), all with zero
    `unrecognized arguments`:
      aw oc run --no-color status          exit=2   (the driver's own "run_id required", not a flag error)
      aw agy run --no-color status         exit=2   (same)
      aw agy run --color status            exit=2   (same)
      aw oc review --no-color --help       exit=0
      aw agy sessions --no-color --help    exit=0
      aw agy view --no-color --help        exit=0
      aw agy exec --color --help           exit=0
      aw run as --no-color --help          exit=0
      aw run ipd --no-color                exit=2   (the profile refusal, not a flag error)
      aw attention --no-color              exit=0
    BEFORE the change the first of those printed `runipd: error: unrecognized arguments: --no-color`.
    AFTER: `total subcommands: 229`, `declared gaps: 29 = 1 hidden (__complete) + 28 forwarded
    (flag consumed instead)`, `UNEXPLAINED gaps: {}`.
    MEASUREMENT DISCIPLINE, since it changes how to reproduce this: the `aw` console script resolves
    `agent_workflows` from the MAIN checkout (`sys.path` carries the repo root), not from this lane,
    so every invocation above was run with `PYTHONPATH=<lane>` to exercise the lane's code. Without
    it the flag appears broken because the OLD code is running.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `aw <cmd> --color` output showing ANSI bytes present where a pipe would otherwise disable color (show the raw bytes or an escape-sequence count), paste `aw <cmd> --no-color --color` with its UNPIPED exit code of 2 and its message, and paste a grep proving no `os.environ` assignment was added for color. Show the 256-color path reached by the same boolean.
  - Observed evidence: `--color` FORCES COLOR WHERE A PIPE WOULD DISABLE IT. `aw attention --type plan` piped: `0` ESC
    bytes. Same command with `--color`, piped: `20` ESC bytes in the first 20 lines. Raw sample
    (`cat -v`): `^[[1mStatus   Type ...^[[0m` then
    `^[[1;38;5;46mapproved^[[0m ^[[1;38;5;33mplan^[[0m ...`.
    BOTH FLAGS EXIT 2, UNPIPED, on the parsed AND the forwarded path:
      aw attention --no-color --color        exit=2
      aw check reviews --color --no-color    exit=2
      aw oc run --no-color --color status    exit=2
    Message, identical on both paths:
      `agent-workflows: error: argument --color: not allowed with argument --no-color`
    (argparse's own mutually-exclusive-group wording on the parsed path; `_dispatch` reproduces it
    verbatim for the forwarded path, where the group never runs).
    NO `os.environ` MUTATION: `grep -n "os\.environ\[[^]]*\] *="` across `cli.py`, `term.py` and
    `result_types.py` returns NOTHING, and a grep for assignments to `NO_COLOR`/`FORCE_COLOR`
    likewise returns nothing. The override travels as a function argument plus one module-level
    value (decision `1-yaxr4i-D2`), so a spawned `aw` child cannot inherit it.
    THE 256-COLOR PATH IS REACHED BY THE SAME BOOLEAN: the escapes above are `38;5;N` (xterm-256),
    emitted by `Term.color256`, and `tests/test_term.py::test_the_256_color_path_is_reached_by_the_same_boolean`
    asserts `color256` and the 16-color `colorize` both follow the one `self.color` flag and both
    go plain when it is False. No new capability tier was added.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the precedence table as written into `docs/cli-output-contract.md` AND the passing test matrix that enforces it, covering at minimum: `--color` beating `NO_COLOR`; `--no-color` beating `FORCE_COLOR`; env beating detection with no flag; and detection alone with neither.
  - Observed evidence: TABLE AS WRITTEN into `docs/cli-output-contract.md` section 1.1 ("Color Precedence: flag beats
    env beats detection"), chain `--color / --no-color  >  NO_COLOR / FORCE_COLOR  >  TERM
    capability  >  stdout.isatty()`, with a four-row layer table and a five-row worked-case table.
    MEASURED MATRIX (ESC byte counts, piped, `aw attention --type plan`):
      NO_COLOR=1 with --color          -> 112   (flag beats env)
      FORCE_COLOR=1 with --no-color    -> 0     (flag beats env, other direction)
      FORCE_COLOR=1 no flag            -> 112   (env beats detection)
      neither flag nor env             -> 0     (detection alone)
    TEST MATRIX: `tests/test_term.py::ColorPrecedenceTests`, 10 tests covering each rung plus
    `--color` beating `TERM=dumb`, the module-level override applying and RESETTING, an explicit
    argument beating it, and `test_no_env_mutation`. Run: `26 passed` for the file.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the new test's source (showing it walks the tree RECURSIVELY through `argparse._SubParsersAction.choices` rather than spot-checking), the total subcommand count it observes (expect 219), its FAILING output against pre-change code naming the missing subcommands, and its passing result after. A test that only passes after does not prove it would have caught the regression.
  - Observed evidence: NEW FILE `tests/test_flag_surface_uniformity.py`. The walk is RECURSIVE through
    `argparse._SubParsersAction.choices` (`_walk_subcommands` calls `visit(sub, [*path, name])` for
    every choice of every subparsers action), not a spot check.
    TOTAL OBSERVED: 229 subcommands (the plan expected 219; the CLI grew, which is why
    `test_the_walk_sees_a_deep_tree_not_just_top_level_verbs` asserts a LOWER BOUND plus two known
    deep leaves - `ipd dependencies set` at depth 3 and `oc run` - rather than a brittle exact count).
    FAILING PRE-CHANGE: with the implementation stashed, the file reports `13 failed, 3 passed`, and
    the load-bearing assertion FAILS naming every gap:
      `AssertionError: {'install': ['--color'], 'setup': ['--color'], ... 'run as': ['--no-color',
      '--color', '--agent', '--json'], 'oc run': ['--no-color', '--color', '--agent', '--json'],
      ... 'completion': ['--color']}`
    i.e. it names the 11 forwarded objects missing ALL FOUR flags and every other subcommand missing
    `--color`. A test that only passes after would not have proved it catches the regression; this
    one was observed red first.
    PASSING AFTER: `17 passed in 0.54s`.
    NOTE THE SHAPE CHANGED FROM THE PLAN'S (decision `1-yaxr4i-D3`): because the forwarded leaves
    must declare no flags, the declared-surface assertion skips them and
    `ForwardedPathBehaviorTests` asserts their contract BEHAVIORALLY instead - 12 commands x 2 flags
    proving the token is consumed, plus a `--` passthrough case and a case proving `--agent` is
    never stolen from a downstream parser.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the exemption list AS ENCODED, showing it is a CLOSED NAMED SET containing only `__complete` and not a predicate such as "skip anything hidden", plus the comment stating why that command is exempt. Then paste the MUTATION: add a second flagless subcommand not on the list, show the test FAILS and NAMES it, revert, show it passes. A V-08 without the mutation has not shown the exemption is a gate rather than a hole.
  - Observed evidence: THE EXEMPTION AS ENCODED, both lists CLOSED NAMED SETS and neither a predicate:
      `EXEMPT_SUBCOMMANDS = frozenset({"__complete"})` with the comment stating why (hidden
      shell-completion query, invoked by the shell, emits a bare candidate list, always exits 0, so
      styling flags are meaningless), and an explicit note that a predicate such as "skip anything
      hidden" would SILENTLY ABSORB the next command, which is the regrowth being prevented.
      `FORWARDED_SUBCOMMANDS = frozenset({...28 names...})` for the leaves that accept the flags by
      CONSUMPTION rather than declaration, with the reason and the conflicting shipped test named.
    DEVIATION FROM E-08's LETTER, recorded deliberately: E-08 says the set contains ONLY
    `__complete`. Two sets were required because the 28 forwarded leaves DO accept the flags but
    must not DECLARE them (decision `1-yaxr4i-D3`). E-08's property is preserved exactly: both are
    closed named sets, so a 30th flagless command fails until a human decides.
    THE MUTATION, in `test_an_unlisted_flagless_subcommand_fails_the_gate`: it builds the real
    parser, grafts on `zz-mutation-probe` (flagless, unlisted), and asserts the gate's predicate
    reports it BY NAME, that it reports all four flags missing, and that it is the ONLY offender
    (so the failure comes from the mutation, not a pre-existing gap). Executed as part of the file:
    `17 passed`. Reverting is implicit - the probe exists only inside that test's local parser, so
    the suite is green immediately afterwards.
    ALSO A POSITIVE GUARD so the skip cannot rot into a blanket pass:
    `test_the_forwarded_leaves_declare_no_flags_as_their_own_contract_requires` fails if anyone adds
    `parents=[common]` to a forwarded leaf, and `test_the_exemption_is_a_closed_named_set_and_is_minimal`
    fails if an exempt name stops existing.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: state which OQ-01 option was ruled and implemented. Paste the measured behavior AFTER the change for both a pipe and a TTY (mode and color for each), paste the `git diff` of `docs/cli-output-contract.md` and of `select_output`'s docstring showing the losing claim REMOVED rather than left standing, and confirm no other documented rule was altered.
  - Observed evidence: OPTION RULED AND IMPLEMENTED: **Option B, correct the document** (OQ-01, maintainer ruling
    2026-09-10). The code was already correct; the DOCUMENT and the DOCSTRING were wrong.
    MEASURED AFTER THE CHANGE (unchanged behavior, which is the point of Option B):
      pipe (`FakeStream(is_a_tty=False)`) -> `mode=OutputMode.HUMAN`, `color=False`
      TTY  (`FakeStream(is_a_tty=True)`)  -> `mode=OutputMode.HUMAN`, `color=True`
    and end to end, `aw attention --type plan` piped emits human prose with 0 ESC bytes, while
    `--agent` emits `aw.agent/v1` JSONL. No invocation emits JSONL on account of being piped.
    THE LOSING TEXT IS REMOVED, NOT LEFT STANDING, in three places:
      1. `docs/cli-output-contract.md` section 1: the precedence line
         `explicit > --agent > non-TTY stdout (pipe/redirect) => agent > TTY stdout => human`
         became `explicit (--json / --format <fmt>)  >  --agent  >  human`, and clause 2 no longer
         claims `not stdout.isatty()` selects AGENT.
      2. Section 9, retitled `Automatic Non-TTY Migration Policy: RETRACTED 2026-09-19`. The
         retraction is EXPLICIT as OQ-01 requires: it quotes the retracted sentence, states what is
         true instead, and gives the three reasons (never shipped, nothing can depend on behavior
         that never existed while an unknown number of consumers depend on the actual behavior,
         `--agent` already covers the capability). It also states what the ruling does NOT say, so
         a later reader does not re-propose it as an unimplemented contract defect.
      3. `select_output`'s docstring (`result_types.py`): step 3 no longer says
         `or not stdout.isatty()`, and a closing paragraph records that the docstring itself used to
         make the false claim and why it was retracted. Leaving it would have moved the
         contradiction from the docs into the code.
    ONE TEST DELIBERATELY CHANGED, named and justified here and in the file:
    `tests/test_output_contract.py::test_output_contract_doc_exists_and_contains_required_sections`
    asserted the literal heading `Automatic Non-TTY Migration Policy (Hard Cutover)`, i.e. it was
    PINNING THE FALSE PROMISE IN PLACE. It now asserts the section exists, that `RETRACTED` is
    present, that `(Hard Cutover)` is GONE, and that the precedence table and `--color` are
    documented. Nothing else in that test was touched.
    NO OTHER DOCUMENTED RULE ALTERED: sections 2-8 and 10-12 are untouched
    (`git diff docs/cli-output-contract.md` shows edits only in section 1, the new 1.1/1.2, and
    section 9 plus its new 9.1).
    `docs/cli-migration.md` was NOT rewritten, and this is the correct outcome rather than an
    omission: the plan's Deferred section says its two prose examples "matter ONLY if OQ-01 is ruled
    Option A". Option B was ruled, so `aw status | grep -i current` and `aw doctor | head` remain
    accurate, and neither path is in `Scope-Paths`.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the added contract text stating the two-axis constraint and the one-resolver requirement, plus a re-measured count of `isatty` references (package-wide and in `cli.py`) at execution time. Paste `git diff --stat` proving no `--tty` flag was added and no prompting call site was modified.
  - Observed evidence: ADDED CONTRACT TEXT: `docs/cli-output-contract.md` section 9.1, "Design constraint on a future
    `--tty` flag (NOT implemented)". It states the TWO-AXIS constraint as a table (Presentation
    keyed on `stdout` via `term.should_color`; Interactivity keyed on `stdin` across the `isatty`
    call sites plus `git_commit_helper._is_interactive`), says a single undifferentiated `--tty`
    boolean MUST NOT be added and why (it would silently re-enable prompting and weaken the
    fail-safe where `cli._confirm` and `_is_interactive` DECLINE rather than prompt), and states the
    ONE-RESOLVER requirement naming `git_commit_helper._is_interactive` as the shape to generalize.
    `isatty` RE-COUNTED AT EXECUTION TIME: **57** references package-wide (the plan said 49, review
    said 51: it keeps growing, which strengthens the one-resolver argument) and **19** in `cli.py`
    (the plan said 18). The doc cites the re-measured figures, not the plan's.
    NO `--tty` FLAG ADDED: `grep -rn '"--tty"' agent_workflows/ tests/` returns NOTHING.
    NO PROMPTING CALL SITE MODIFIED: `git diff --stat` covers only `agent_workflows/cli.py`,
    `agent_workflows/result_types.py`, `agent_workflows/term.py`, `docs/cli-output-contract.md`,
    `tests/test_output_contract.py`, `tests/test_term.py` plus the new
    `tests/test_flag_surface_uniformity.py`; `git_commit_helper.py` is untouched, and the `cli.py`
    diff contains no edit to `_confirm` or any `stdin.isatty()` site.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `--agent` and `--json` output for the same command under `--color`, `--no-color`, and neither, showing the payloads are BYTE-IDENTICAL and contain no ANSI escapes. NOTE this property HOLDS TODAY (measured at review: `aw check reviews --agent` and `--agent --no-color` are byte-identical with zero `\x1b` bytes), so E-07 is a REGRESSION GUARD and a difference means `--color` leaked into a machine surface. Paste the `tests/test_output_contract.py` result and name any test deliberately changed by E-05 with its justification. Paste the bare `python3 -m pytest` summary line and compare it against the CORRECTED baseline of `5959 passed, 3 skipped, 2 xfailed` with ZERO failures, not the stale figure this plan originally recorded.
  - Observed evidence: MACHINE SURFACES BYTE-IDENTICAL under every presentation-flag combination, for three commands,
    with zero ANSI in all of them (`cmp -s` on the captured bytes):
      aw check reviews --agent                    | none vs --no-color: IDENTICAL | none vs --color: IDENTICAL | ESC 0/0/0
      aw find plans --status approved --agent     | IDENTICAL | IDENTICAL | ESC 0/0/0
      aw attention --type plan --agent            | IDENTICAL | IDENTICAL | ESC 0/0/0
      aw check reviews --json                     | IDENTICAL | IDENTICAL | ESC 0/0/0
      aw find plans --status approved --json      | IDENTICAL | IDENTICAL | ESC 0/0/0
    As the plan notes, this property HELD ALREADY, so E-07 is a REGRESSION GUARD and the value of
    running it is the confirmation that `--color` did not leak into a machine surface. It did not.
    EXIT CODES UNCHANGED by any presentation flag, measured UNPIPED across five commands
    (none / --no-color / --color): `check reviews` 0/0/0, `attention` 0/0/0, `doctor` 1/1/1,
    `status` 0/0/0, `ipd board` 0/0/0.
    `tests/test_output_contract.py`: passes. ONE test deliberately changed, named and justified in
    V-05 (it pinned the retracted hard-cutover heading and therefore the false promise); no other
    assertion in that file was altered. `tests/test_output_mode.py` passes UNMODIFIED, which is the
    stronger signal for E-07 since it owns the `select_output` mode/color truth table.
    BARE SUITE, actual summary line:
      `1 failed, 7333 passed, 3 skipped, 2 xfailed in 90.55s (0:01:30)`
    THE ONE FAILURE IS PRE-EXISTING AND NOT MINE, proven rather than asserted:
    `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`
    fails IDENTICALLY with my changes stashed (`1 failed` on the clean tree, same three plan names:
    `reaskscore` `s0gnha`, `ty7w6o`, `svacmz`). It is a real-corpus test reading other agents'
    pending plans, which this lane does not touch. The plan's corrected baseline of
    `5959 passed, 3 skipped, 2 xfailed` with ZERO failures is itself now stale (the suite has grown
    to 7334 collected here), so the judgement is on the DELTA of failing NODE IDS, which is EMPTY:
    the same single node fails before and after, and no test that passed before fails now.
    `python3 -m agent_workflows check` GAINS NO DIAGNOSTIC ON ANY FILE I TOUCHED. It reports 243
    findings on the clean tree and 255 with this work uncommitted (both deterministic over three
    runs each). All 12 are `check.scope-drift` on TWO OTHER AGENTS' pending plans (`m7gvuz`,
    `w2y5ac`), which flag every UNCOMMITTED working-tree path outside their own declared fences; my
    7 files appear against each. Verified by enumerating the drift details: every added row names a
    file of mine and a plan that is not mine, and no new rule fires on any of my paths. It is an
    artifact of measuring a shared checkout mid-edit and clears once committed.
    `aw sanitize --agent`: `outcome":"clean","exit":0 ... "findings":0`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan has been REVIEWED (`/plan-review`, 2026-09-10) and carries `- Readiness: no-go`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`, AND, before that is even meaningful, until OQ-01 is ANSWERED.

OQ-01 IS THE ONE THING BLOCKING THIS PLAN, and it is a maintainer decision that the review could not make. `aw ipd lint --phase author` currently FAILS at exit 1 with `IPD-Q501` because a `Blocking: yes` question is still `open`, which blocks `aw ipd begin` at every checkpoint. That is the gate functioning correctly, not a defect to route around. DO NOT clear it by setting `- Blocking: no`: E-05 cannot implement a ruling that does not exist, and E-06 and E-07 both depend on E-05.

WHAT A REVIEWER OR MAINTAINER SHOULD KNOW ABOUT THE READINESS: everything else in this plan is ready. Task group 1 (E-01 through E-04, E-08) is independent of OQ-01, fully measured, and mechanically clear: nine parser-registration edits, one inherited flag, a verified mutual-exclusion mechanism, and a parser-walk test whose exact walk has already been demonstrated to reproduce the 25-of-219 finding. If the maintainer wants value before ruling on OQ-01, task group 1 could be split into its own plan and executed immediately; the review did not do that unilaterally because splitting an approved-shape plan is a scope decision.

A reviewer should note this plan deliberately delivers TWO of the item's three requested flags plus the precondition for the third, with `--tty` deferred and its analysis recorded (F-7, F-8, E-06). If the maintainer wants `--tty` in this plan, it needs the OQ-01 ruling first and a fourth task group.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE that `cli.py` is large and shared, so re-enumerate the missing-subcommand set by walking the parser at execution time rather than trusting the list above, which has already moved once. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.

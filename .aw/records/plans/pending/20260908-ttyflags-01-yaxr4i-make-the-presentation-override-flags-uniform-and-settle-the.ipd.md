# IPD: Make the presentation override flags uniform and settle the documented non-TTY mode rule

- Date: 2026-09-08
- Kind: child
- Concern: The presentation overrides are inconsistent per command, which is worse than uniformly absent because it cannot be scripted around. `--no-color` is declared once on the shared `common` parent and inherited almost everywhere, but 25 subcommands do not inherit it, so `aw oc run --no-color` is a usage error today while `aw attention --no-color` works, and the gap lands exactly on the long-running driver commands whose output a user most wants to capture. `--color` exists only as the `FORCE_COLOR` env var and has no flag form. `--tty` has no equivalent at all. Underneath, a published contract and the code disagree: `docs/cli-output-contract.md` and `select_output`'s own docstring both state that non-TTY stdout selects AGENT mode, and the code never calls `stdout.isatty()` for mode selection at all.
- Scope: Close the mechanical gap and the styling gap, and SETTLE the doc-versus-code divergence before any `--tty` semantics are specified. IN: `--no-color` on the 25 missing subcommands; a `--color` flag as its mutually exclusive twin threaded through the existing color engine; a parser-walk test asserting the trio's presence on every non-hidden subcommand; and a decision on the non-TTY mode rule with docs and code made to agree. OUT: `--tty` itself and any change to interactive prompting, both of which depend on that decision and on a maintainer ruling.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/term.py, agent_workflows/result_types.py, docs/cli-output-contract.md, tests/test_term.py, tests/test_output_contract.py, tests/test_flag_surface_uniformity.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Set: ttyflags
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: yaxr4i
- From-Backlog: isg0kg

## Workflow history
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

- [ ] E-01 Give the subcommands that do not inherit `common` their `parents=[common]`, in `agent_workflows/cli.py`. RE-ENUMERATE THE LIST AT EXECUTION TIME rather than trusting this plan: the item measured 18 and this plan measured 25 at `a2e0438a`, so the set is moving. Re-measured at review (HEAD `5075613e`): still 25 of 219, and the NAMES are unchanged from this plan's list, so the set has held for now.
  THE 25 NAMES ARE ONLY **10 DISTINCT PARSER OBJECTS**, AND 9 OF THEM NEED FIXING. This plan estimated "roughly half"; the measured answer is much better than that and is exact, because alias groups share ONE parser object (verified by `id()`). The 10 groups: `run as`; `run ipd`; {`oc runipd`, `oc run`, `opencode runipd`, `opencode run`} (ONE object, all four names); {`oc review`, `opencode review`}; {`agy runipd`, `agy run`, `agy runagy`, `antigravity runipd`, `antigravity run`, `antigravity runagy`} (ONE object, all six); {`agy review`, `antigravity review`}; {`agy sessions`, `antigravity sessions`}; {`agy view`, `agy view-antigravity-jsonl`, `antigravity view`, `antigravity view-antigravity-jsonl`}; {`agy exec`, `antigravity exec`}; and `__complete`. So this is NINE registration edits, not 25 and not "about 12". Verify the grouping with `id()` before editing, because editing per NAME would touch the same object repeatedly and could double-add the flag.
  EXCLUDE `__complete` DELIBERATELY: it is the hidden shell-completion command and the item is explicit that it correctly lacks the flag.
  `conflict_handler="resolve"` IS SET ON EVERY PARSER (`_AwArgumentParser.__init__`), WHICH IS A SILENT-OVERWRITE HAZARD. If a target parser already declared its own `--no-color`/`--agent`/`--json`, adding `parents=[common]` would SILENTLY REPLACE one definition instead of erroring. MEASURED: none of the 25 currently declares `--agent` or `--json`, so no collision exists today. Re-check that at execution time rather than assuming, since the set has moved before.
  - Depends on: none
  - Expected outcome: `aw oc run --no-color` and `aw agy run --no-color` parse successfully; every non-hidden subcommand accepts `--no-color`; `__complete` still does not; the fix is applied once per PARSER OBJECT (9 edits) with the `id()` grouping and the no-collision re-check both recorded.
  - Execution state: pending

- [ ] E-02 Add `--color` to the `common` parent as the MUTUALLY EXCLUSIVE twin of `--no-color`, so both are inherited by construction rather than added per command. LOCATE `common` BY SYMBOL inside `_build_parser`: the citation `cli.py:789-794` in this plan is STALE; at HEAD `5075613e` the `--no-color` declaration is at `cli.py:804-808`.
  THE MECHANISM IS VERIFIED TO WORK AND TO GIVE EXIT 2, so implement it rather than re-deriving it. Measured: a `add_mutually_exclusive_group()` declared on an `add_help=False` PARENT does propagate through `parents=[...]` to a subparser, and passing both flags raises `SystemExit(2)` with `argument --no-color: not allowed with argument --color`. `_AwArgumentParser.error` also ends in `self.exit(2)`, so the exit code is 2 from both paths and OQ-02's requirement is satisfied structurally. Passing both must be a usage error with exit 2, not a silent winner; use argparse's mutually-exclusive group so the refusal is structural. Thread the flag into the two existing seams rather than inventing a third: the `Term(color=...)` construction which already handles the `no_color` half, and `select_output`'s color resolution at `result_types.py:157-159`. `should_color` (`term.py:74-98`) needs an explicit override parameter so a flag can beat env detection WITHOUT the code setting `os.environ`, which would leak into subprocesses. NOTE the maintainer asked for 256-COLOR and no new capability tier is needed: `Term.color256` and the 16-color `colorize` are gated by the SAME single `self.color` boolean, so `--color` sets that one boolean. A distinct 16-versus-256 capability level is a SEPARATE question and must not be smuggled in.
  - Depends on: E-01
  - Expected outcome: `--color` forces color on where detection would disable it; `--no-color --color` exits 2; no `os.environ` mutation; the 256-color path is reached by the same boolean.
  - Execution state: pending

- [ ] E-03 Write the PRECEDENCE down and enforce it: flag beats env beats detection. The env layer already implements `NO_COLOR` off unless `FORCE_COLOR` overrides (`term.py:83-88`), then `TERM=dumb`/unset off (`:90-92`), then `isatty()` (`:94-98`); the flag layer must sit ABOVE all of it. Record the resulting table in `docs/cli-output-contract.md`, which already owns this contract at `:18-34`, and pin it in `tests/test_term.py`, which ALREADY exercises the `NO_COLOR`/`FORCE_COLOR`/isatty matrix against fake TTY and pipe streams (`:46`, `:52`, `:56`, `:60`, `:65`), so a flag override slots straight into that harness rather than needing a new one.
  - Depends on: E-02
  - Expected outcome: a written precedence table matching a passing test matrix, covering flag-versus-env conflicts in both directions.
  - Execution state: pending

- [ ] E-04 Add the PARSER-WALK TEST asserting that every non-hidden subcommand, nested included, accepts the presentation flags. Walk the built parser tree recursively rather than spot-checking.
  WHY A RECURSIVE WALK IS THE DURABLE FIX: the item measured 18 missing, this plan measured 25, and the newly-missing ones (`run as`, `run ipd`, the four `review` leaves) are commands added AFTER the item was filed, so each new nested subcommand has been missing `common` as it landed. A per-command spot check demonstrably did not catch this.
  THE WALK IS ALREADY WRITTEN AND VERIFIED, so reuse this shape rather than inventing one: recurse `parser._actions`, descend into every `argparse._SubParsersAction.choices`, and test membership with `any(flag in (a.option_strings or []) for a in sub._actions)`. That exact walk reproduces 219 subcommands and the 25-missing set at review, so a test built on it is known to see what this review saw.
  - Depends on: E-01, E-02
  - Expected outcome: a recursive parser-walk test asserting the presentation flags on every non-hidden subcommand, reproducing the 219 total, that FAILS pre-change naming the 25 and passes after E-01/E-02.
  - Execution state: pending

- [ ] E-08 DECLARE THE EXEMPTION LIST EXPLICITLY IN THAT TEST, as a closed named set rather than a predicate, so an exemption is a deliberate reviewable decision instead of a silent skip. Today the only exemption is `__complete`, the hidden shell-completion command, which the item says correctly lacks the flag.
  MAKE IT A CLOSED LIST OF NAMES, NOT A RULE LIKE "SKIP ANYTHING HIDDEN". A predicate would silently absorb the next hidden or newly-added subcommand, which is precisely the regrowth this plan exists to stop: the gap grew from 18 to 25 exactly because new leaves inherited nothing and nobody was forced to notice. A closed list makes a 26th command FAIL the test until someone decides about it.
  MUTATION-CHECK THE EXEMPTION so it is not decoration: add a second fake subcommand with no presentation flags and show the test FAILS naming it, then revert. A guard that cannot fail proves nothing.
  - Depends on: E-04
  - Expected outcome: the exemption is a closed named set containing only `__complete`, with a comment stating why; a mutation adding an unlisted flagless subcommand FAILS the test and names it; reverting restores green.
  - Execution state: pending

### Task group 2: settle the divergence before specifying --tty

- [ ] E-05 SETTLE THE NON-TTY MODE RULE and make docs and code agree, which the item requires be done BEFORE `--tty` is specified. The published contract says non-TTY stdout selects AGENT mode: `docs/cli-output-contract.md:18` ("non-TTY stdout (pipe/redirect) => agent"), `:24-27`, and `:161` ("Per maintainer decision OQ-01, non-TTY stdout adopts `aw.agent/v1` JSONL immediately upon release"), with the same claim in `select_output`'s docstring (`result_types.py:75`). THE CODE DOES NOT DO IT: `result_types.py` contains exactly two `isatty` mentions and both are inside that docstring; the only real TTY consultation is `should_color(out_stream)` at `:159`, for COLOR. Measured: non-TTY stdout gives `mode=OutputMode.HUMAN color=False`. Only ONE of the two may stand. This item's job is to IMPLEMENT THE RULED ANSWER, not to choose: OQ-01 carries the choice to the maintainer because implementing the documented rule would change what every piped `aw` invocation emits, which is a breaking change for any existing consumer, while correcting the docs retracts a published maintainer decision.
  - Depends on: none
  - Expected outcome: docs and code state the same rule, with the maintainer's choice recorded and the losing text removed rather than left contradicting.
  - Execution state: pending

- [ ] E-06 RECORD, and do not implement, the `--tty` design constraint, so a successor does not conflate the two axes. TTY-ness controls two unrelated things through two different streams: PRESENTATION keyed on stdout (`should_color`, `term.py:94-98`; the color resolution at `result_types.py:157-159`) and INTERACTIVITY keyed on stdin (49 `isatty` references across the package at `a2e0438a`, 18 in `cli.py` alone, plus `git_commit_helper._is_interactive`). The existing contract deliberately keeps them apart: `select_output`'s docstring (`:76`) says "`stdin.isatty()` controls interactive prompting, NOT audience/mode" and `docs/cli-output-contract.md:28` repeats it. So a single undifferentiated `--tty` boolean would silently weaken the non-interactive fail-safe that those call sites rely on, where `_confirm` currently DECLINES rather than prompting. Write the constraint into `docs/cli-output-contract.md` next to the precedence table: if `--tty` is ever added, it must NOT be one boolean, and the interactivity axis must route through ONE resolver rather than a flag check at each of the 49 sites.
  - Depends on: E-05
  - Expected outcome: the two-axis constraint and the one-resolver requirement are written into the published contract; no `--tty` flag is added and no prompting behavior changes.
  - Execution state: pending

- [ ] E-07 Verify NO REGRESSION in the machine surfaces, because `--color` and the E-05 decision both touch `select_output`, which every renderer consumes. `tests/test_output_contract.py` owns the `select_output` mode/color contract and must pass unmodified except where E-05 deliberately changes it (and any such change must be called out, not quietly absorbed). Confirm that `--agent` and `--json` remain unaffected by `--color`/`--no-color` (both are styling-only per `docs/cli-output-contract.md:34`), that an `aw.agent/v1` record never gains ANSI bytes, and that the exit codes of a representative sample of commands are unchanged by any presentation flag.
  - Depends on: E-03, E-05
  - Expected outcome: machine output is byte-identical under every presentation flag combination; any deliberate `test_output_contract.py` change is named and justified.
  - Execution state: pending

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

- `--tty` ITSELF. The item presents three options (presentation-only, both axes, or two separate flags) and asks the maintainer to rule; it also requires the doc-versus-code divergence be settled FIRST, because that decision changes what `--tty` would mean. Implementing it here would either guess the ruling or silently weaken the non-interactive fail-safe that 49 call sites rely on. E-06 records the constraint so the successor inherits the analysis rather than redoing it.
- ANY CHANGE TO INTERACTIVE PROMPTING, including an `--interactive`/`--no-interactive` pair. Same reason: it is the second axis and depends on the same ruling. Note the fail-safe being protected is real, `_confirm` deliberately DECLINES and warns when non-interactive rather than proceeding silently.
- A DISTINCT 16-COLOR VERSUS 256-COLOR CAPABILITY TIER. The item explicitly says this must not be smuggled in; `--color` sets the one existing boolean.
- RETROFITTING THE `FORCE_COLOR`/`NO_COLOR` ENV LAYER. Already correct; this plan adds a flag layer above it.
- CHANGING `conflict_handler="resolve"` ON `_AwArgumentParser` (F-14). It makes a duplicate option definition silently replace rather than error, which is a real latent hazard for any future `parents=` addition, but changing it repo-wide could surface duplicate definitions across 219 subcommands and is unrelated to this item's flags. E-01 mitigates it with a per-parser collision re-check instead; a general fix is its own item.
- REWRITING THE TWO IN-REPO DOCS THAT ASSUME HUMAN PIPED OUTPUT (`docs/cli-migration.md:50` documents `aw status | grep -i current`; `docs/cli-human-guide.md:103` documents `aw doctor | head`). These matter ONLY if OQ-01 is ruled Option A, in which case both examples become wrong and must be fixed in the same change. Recorded here so the ruling's true cost is visible; neither file is in `- Scope-Paths:` today because Option B (the recommendation) leaves both correct. If Option A is ruled, add both paths before executing.

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
- Status: open
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: BLOCKING, because the two options have very different blast radii and the item requires this settled before `--tty` is specified. OPTION A, implement the documented rule: every piped or redirected `aw` invocation would start emitting `aw.agent/v1` JSONL instead of human text, which is a BREAKING change for any existing script, log capture or CI job that pipes `aw` and parses prose. OPTION B, correct the docs: retracts a decision the contract records as a maintainer decision adopted "immediately upon release" (`docs/cli-output-contract.md:161`), and leaves piped output human-readable, which is what has actually shipped for its whole life. EVIDENCE FOR B: the documented behavior has never been implemented, so nothing depends on it, while an unknown number of consumers depend on today's actual behavior; and `--agent` already exists as the explicit opt-in, so the auto-switch buys convenience rather than capability. EVIDENCE FOR A: the maintainer decided it once, deliberately, and an unimplemented published contract is itself a defect. RECOMMENDED: B, correcting the docs, with `--agent` remaining the explicit way to get JSONL. Either way E-05 must remove the losing text; the plan does not depend on which.
  STILL OPEN AFTER `/plan-review` (2026-09-10), AND DELIBERATELY SO. This review ran with NO interactive question channel available, so the question could not be put to the maintainer. It was NOT resolved from evidence, because it is not the kind of question repository evidence can settle: Option A knowingly breaks existing consumers and Option B retracts a recorded maintainer decision, and choosing between a compatibility break and a contract retraction is a maintainer's call about risk appetite and published promises, not a reviewer's. Resolving it here would be exactly the forbidden act of inventing a human decision.
  THE CONSEQUENCE IS THAT THIS PLAN CANNOT BE EXECUTED YET, AND THAT IS THE GATE WORKING. `aw ipd lint --phase author` FAILS with `IPD-Q501` ("BLOCKING question is still 'open'") at exit 1, which blocks `aw ipd begin` at every checkpoint. Do NOT clear the lint by flipping `- Blocking:` to `no`: the question genuinely does block, because E-05 cannot implement a ruling that does not exist and E-06/E-07 both depend on E-05.
  REVIEW ADDED THREE MEASUREMENTS THAT SHOULD MAKE THE DECISION EASIER, all at HEAD `781d70ae`. FIRST, the divergence is total rather than partial: `result_types.py` contains exactly TWO `isatty` mentions and BOTH are inside the docstring making the false claim, so there is no half-implemented branch to finish, and Option A is a genuinely new feature rather than a bug fix. SECOND, the actual behavior was confirmed by execution on real commands, not just on `select_output`: `aw check reviews` piped emits human text (`AW check reviews`, `CONFORMS 135 reviews checked`) and only `--agent` produces JSONL, so today's shipped contract is unambiguous. THIRD, the in-repo blast radius of Option A is small but NOT zero: `docs/cli-migration.md:50` documents `aw status | grep -i current` and `docs/cli-human-guide.md:103` documents `aw doctor | head`, both of which assume human piped output and would need rewriting. The unknown external consumers remain unknown, which is itself the strongest argument for B.
  WHAT TO DO WITH THE ANSWER: record it here with `- Status: resolved` and the ruling, then E-05 implements it and removes the losing text (including `select_output`'s docstring, which is documentation making a false claim inside the code). Once resolved, re-run `aw ipd lint --phase author` and expect `IPD-Q501` to clear.

### OQ-02: Should `--color` and `--no-color` be a mutually exclusive pair, or should the last flag win?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE, recorded so it is deliberate. The item specifies mutually exclusive with exit 2 ("`--no-color` with `--color` is a usage error, not a silent winner"), and that is the recommended and implemented choice: a silent winner makes a scripted invocation's behavior depend on argument order, which is exactly the unscriptability this item exists to fix. Implement mutual exclusion via argparse so the refusal is structural rather than hand-checked, and confirm the resulting exit code is 2 by measuring it UNPIPED.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the parser-walk enumeration BEFORE (naming the missing subcommands and their count; expect 25 of 219) and AFTER (count 1, only `__complete`). Paste the `id()` GROUPING showing the 25 names collapse to 10 distinct parser objects, and state that exactly NINE registration edits were made rather than 25. Paste the re-check that none of the target parsers already declared `--no-color`/`--agent`/`--json`, since `conflict_handler="resolve"` would otherwise SILENTLY replace a definition (F-14). Then paste at least four real invocations from the fixed set, including `aw oc run --no-color` and `aw agy run --no-color`, showing they no longer produce a usage error, with exit codes measured UNPIPED.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw <cmd> --color` output showing ANSI bytes present where a pipe would otherwise disable color (show the raw bytes or an escape-sequence count), paste `aw <cmd> --no-color --color` with its UNPIPED exit code of 2 and its message, and paste a grep proving no `os.environ` assignment was added for color. Show the 256-color path reached by the same boolean.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the precedence table as written into `docs/cli-output-contract.md` AND the passing test matrix that enforces it, covering at minimum: `--color` beating `NO_COLOR`; `--no-color` beating `FORCE_COLOR`; env beating detection with no flag; and detection alone with neither.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new test's source (showing it walks the tree RECURSIVELY through `argparse._SubParsersAction.choices` rather than spot-checking), the total subcommand count it observes (expect 219), its FAILING output against pre-change code naming the missing subcommands, and its passing result after. A test that only passes after does not prove it would have caught the regression.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the exemption list AS ENCODED, showing it is a CLOSED NAMED SET containing only `__complete` and not a predicate such as "skip anything hidden", plus the comment stating why that command is exempt. Then paste the MUTATION: add a second flagless subcommand not on the list, show the test FAILS and NAMES it, revert, show it passes. A V-08 without the mutation has not shown the exemption is a gate rather than a hole.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: state which OQ-01 option was ruled and implemented. Paste the measured behavior AFTER the change for both a pipe and a TTY (mode and color for each), paste the `git diff` of `docs/cli-output-contract.md` and of `select_output`'s docstring showing the losing claim REMOVED rather than left standing, and confirm no other documented rule was altered.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the added contract text stating the two-axis constraint and the one-resolver requirement, plus a re-measured count of `isatty` references (package-wide and in `cli.py`) at execution time. Paste `git diff --stat` proving no `--tty` flag was added and no prompting call site was modified.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `--agent` and `--json` output for the same command under `--color`, `--no-color`, and neither, showing the payloads are BYTE-IDENTICAL and contain no ANSI escapes. NOTE this property HOLDS TODAY (measured at review: `aw check reviews --agent` and `--agent --no-color` are byte-identical with zero `\x1b` bytes), so E-07 is a REGRESSION GUARD and a difference means `--color` leaked into a machine surface. Paste the `tests/test_output_contract.py` result and name any test deliberately changed by E-05 with its justification. Paste the bare `python3 -m pytest` summary line and compare it against the CORRECTED baseline of `5959 passed, 3 skipped, 2 xfailed` with ZERO failures, not the stale figure this plan originally recorded.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan has been REVIEWED (`/plan-review`, 2026-09-10) and carries `- Readiness: no-go`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`, AND, before that is even meaningful, until OQ-01 is ANSWERED.

OQ-01 IS THE ONE THING BLOCKING THIS PLAN, and it is a maintainer decision that the review could not make. `aw ipd lint --phase author` currently FAILS at exit 1 with `IPD-Q501` because a `Blocking: yes` question is still `open`, which blocks `aw ipd begin` at every checkpoint. That is the gate functioning correctly, not a defect to route around. DO NOT clear it by setting `- Blocking: no`: E-05 cannot implement a ruling that does not exist, and E-06 and E-07 both depend on E-05.

WHAT A REVIEWER OR MAINTAINER SHOULD KNOW ABOUT THE READINESS: everything else in this plan is ready. Task group 1 (E-01 through E-04, E-08) is independent of OQ-01, fully measured, and mechanically clear: nine parser-registration edits, one inherited flag, a verified mutual-exclusion mechanism, and a parser-walk test whose exact walk has already been demonstrated to reproduce the 25-of-219 finding. If the maintainer wants value before ruling on OQ-01, task group 1 could be split into its own plan and executed immediately; the review did not do that unilaterally because splitting an approved-shape plan is a scope decision.

A reviewer should note this plan deliberately delivers TWO of the item's three requested flags plus the precondition for the third, with `--tty` deferred and its analysis recorded (F-7, F-8, E-06). If the maintainer wants `--tty` in this plan, it needs the OQ-01 ruling first and a fourth task group.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE that `cli.py` is large and shared, so re-enumerate the missing-subcommand set by walking the parser at execution time rather than trusting the list above, which has already moved once. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.

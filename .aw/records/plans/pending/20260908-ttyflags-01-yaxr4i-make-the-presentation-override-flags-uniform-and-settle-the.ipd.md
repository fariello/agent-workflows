# IPD: Make the presentation override flags uniform and settle the documented non-TTY mode rule

- Date: 2026-09-08
- Kind: child
- Concern: The presentation overrides are inconsistent per command, which is worse than uniformly absent because it cannot be scripted around. `--no-color` is declared once on the shared `common` parent and inherited almost everywhere, but 25 subcommands do not inherit it, so `aw oc run --no-color` is a usage error today while `aw attention --no-color` works, and the gap lands exactly on the long-running driver commands whose output a user most wants to capture. `--color` exists only as the `FORCE_COLOR` env var and has no flag form. `--tty` has no equivalent at all. Underneath, a published contract and the code disagree: `docs/cli-output-contract.md` and `select_output`'s own docstring both state that non-TTY stdout selects AGENT mode, and the code never calls `stdout.isatty()` for mode selection at all.
- Scope: Close the mechanical gap and the styling gap, and SETTLE the doc-versus-code divergence before any `--tty` semantics are specified. IN: `--no-color` on the 25 missing subcommands; a `--color` flag as its mutually exclusive twin threaded through the existing color engine; a parser-walk test asserting the trio's presence on every non-hidden subcommand; and a decision on the non-TTY mode rule with docs and code made to agree. OUT: `--tty` itself and any change to interactive prompting, both of which depend on that decision and on a maintainer ruling.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/term.py, agent_workflows/result_types.py, docs/cli-output-contract.md, tests/test_term.py, tests/test_output_contract.py, tests/test_flag_surface_uniformity.py
- Item-Dependencies: none
- Status: to-review
- Set: ttyflags
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: yaxr4i
- From-Backlog: isg0kg

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `isg0kg`. GATE NOTE: this item carries NO `- Blocks-Release:`, so this plan inherits none, despite `Priority: high`. NOTHING IN THIS ITEM IS OBSOLETE and nothing covers it. RE-MEASURED AT HEAD `a2e0438a` by walking the built parser tree exactly as the item did, and THE GAP HAS GROWN: the item reports `--no-color` missing on 18 of 175 nested subcommands; I measure 25 of 219 missing, and the list has changed shape as well as size. It now includes `run as`, `run ipd`, `oc review`, `agy review`, `opencode review` and `antigravity review`, which did not exist when the item was written, alongside the 9-doubled host-driver set it named. So the mechanical fix is broader than filed and, more importantly, THE GAP IS ACTIVELY REGROWING: every new nested subcommand added since has missed `common` too, which is precisely why E-04's parser-walk test is the durable deliverable rather than the flag additions themselves. `--color` and `--tty` remain at 0 of 219, as filed. THE DOC-VERSUS-CODE DIVERGENCE IS CONFIRMED LIVE and is the reason this plan deliberately does NOT specify `--tty`: measured by execution, non-TTY stdout gives `mode=OutputMode.HUMAN color=False` and TTY stdout gives `mode=OutputMode.HUMAN color=True`, i.e. piping yields monochrome HUMAN text, never JSONL. Meanwhile `docs/cli-output-contract.md:18` publishes "non-TTY stdout (pipe/redirect) => agent", `:161` calls it a maintainer decision adopted "immediately upon release", and `select_output`'s docstring repeats it at `result_types.py:75`. I verified the code has no such branch at all: `result_types.py` contains exactly TWO `isatty` mentions, both inside that docstring (`:75`, `:76`), and the only real TTY consultation is the COLOR one via `should_color(out_stream)` at `:159`. The item is right that this must be settled first: if the documented rule were implemented, `--tty` would flip AUDIENCE MODE as a side effect, turning a styling override into a much larger behavior change. I also re-counted the interactivity axis: 49 `isatty` references across the package (the item said 44), 18 of them in `cli.py` alone, which is why E-06 records the ONE-resolver requirement rather than letting a future `--tty` sprinkle flag checks across them.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the same presentation flags work on every command, and make the published output contract true. The user-visible payoff is that `aw` output becomes reliably capturable in a log, a CI job or a demo recording; the durable payoff is a test that stops the coverage gap regrowing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: close the mechanical gap

- [ ] E-01 Give the 25 subcommands that do not inherit `common` their `parents=[common]`, in `agent_workflows/cli.py`. RE-ENUMERATE THE LIST AT EXECUTION TIME rather than trusting this plan: the item measured 18 and I measure 25 at `a2e0438a`, so the set is moving. The measured set is `run as`, `run ipd`, `oc runipd`, `oc run`, `oc review`, `opencode runipd`, `opencode run`, `opencode review`, `agy runipd`, `agy run`, `agy runagy`, `agy review`, `agy sessions`, `agy view`, `agy view-antigravity-jsonl`, `agy exec`, and the `antigravity` twins of each `agy` entry, plus `__complete`. EXCLUDE `__complete` DELIBERATELY: it is the hidden shell-completion command and the item is explicit that it correctly lacks the flag. Note the host groups are each registered twice under an alias (`agy`/`antigravity`, `oc`/`opencode`), so the real count of distinct parsers to fix is roughly half the reported names; fix the registration once per parser rather than once per alias if they share a builder.
  - Depends on: none
  - Expected outcome: `aw oc run --no-color` and `aw agy run --no-color` parse successfully; every non-hidden subcommand accepts `--no-color`; `__complete` still does not.
  - Execution state: pending

- [ ] E-02 Add `--color` to the `common` parent (`cli.py:789-794`, where `--no-color` is declared) as the MUTUALLY EXCLUSIVE twin of `--no-color`, so both are inherited by construction rather than added per command. Passing both must be a usage error with exit 2, not a silent winner; use argparse's mutually-exclusive group so the refusal is structural. Thread the flag into the two existing seams rather than inventing a third: the `Term(color=...)` construction which already handles the `no_color` half, and `select_output`'s color resolution at `result_types.py:157-159`. `should_color` (`term.py:74-98`) needs an explicit override parameter so a flag can beat env detection WITHOUT the code setting `os.environ`, which would leak into subprocesses. NOTE the maintainer asked for 256-COLOR and no new capability tier is needed: `Term.color256` and the 16-color `colorize` are gated by the SAME single `self.color` boolean, so `--color` sets that one boolean. A distinct 16-versus-256 capability level is a SEPARATE question and must not be smuggled in.
  - Depends on: E-01
  - Expected outcome: `--color` forces color on where detection would disable it; `--no-color --color` exits 2; no `os.environ` mutation; the 256-color path is reached by the same boolean.
  - Execution state: pending

- [ ] E-03 Write the PRECEDENCE down and enforce it: flag beats env beats detection. The env layer already implements `NO_COLOR` off unless `FORCE_COLOR` overrides (`term.py:83-88`), then `TERM=dumb`/unset off (`:90-92`), then `isatty()` (`:94-98`); the flag layer must sit ABOVE all of it. Record the resulting table in `docs/cli-output-contract.md`, which already owns this contract at `:18-34`, and pin it in `tests/test_term.py`, which ALREADY exercises the `NO_COLOR`/`FORCE_COLOR`/isatty matrix against fake TTY and pipe streams (`:46`, `:52`, `:56`, `:60`, `:65`), so a flag override slots straight into that harness rather than needing a new one.
  - Depends on: E-02
  - Expected outcome: a written precedence table matching a passing test matrix, covering flag-versus-env conflicts in both directions.
  - Execution state: pending

- [ ] E-04 Add the PARSER-WALK TEST, which is the durable deliverable of this plan. Assert that EVERY non-hidden subcommand, nested included, accepts the presentation flags, by walking the built parser tree recursively rather than spot-checking. THE EVIDENCE THAT THIS IS THE REAL FIX: the item measured 18 missing, I measure 25, and the newly-missing ones (`run as`, `run ipd`, the four `review` leaves) are commands added AFTER the item was filed, so each new nested subcommand has been missing `common` as it landed. A per-command spot check demonstrably did not catch this. The test must enumerate the hidden exemptions explicitly (only `__complete` today) so an exemption is a deliberate, reviewable list rather than a silent skip.
  - Depends on: E-01, E-02
  - Expected outcome: a test that FAILS at HEAD `a2e0438a` naming the 25 missing subcommands, and passes after E-01/E-02, with `__complete` as the sole declared exemption.
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

## Scope check

- Over-scope: `docs/cli-output-contract.md` is edited by E-03, E-05 and E-06 although the item frames the work as flags. It is required: the item names that file as the owner of this contract, and E-05 exists precisely because the doc currently contradicts the code.
- Under-scope: `--tty` and the interactivity axis are analyzed and documented but not implemented (see Deferred), so this plan delivers two of the item's three requested flags plus the precondition for the third.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline on `main` is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
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
- Resolution or deferral rationale: BLOCKING, because the two options have very different blast radii and the item requires this settled before `--tty` is specified. OPTION A, implement the documented rule: every piped or redirected `aw` invocation would start emitting `aw.agent/v1` JSONL instead of human text, which is a BREAKING change for any existing script, log capture or CI job that pipes `aw` and parses prose. OPTION B, correct the docs: retracts a decision the contract records as a maintainer decision adopted "immediately upon release" (`docs/cli-output-contract.md:161`), and leaves piped output human-readable, which is what has actually shipped for its whole life. EVIDENCE FOR B: the documented behavior has never been implemented, so nothing depends on it, while an unknown number of consumers depend on today's actual behavior; and `--agent` already exists as the explicit opt-in, so the auto-switch buys convenience rather than capability. EVIDENCE FOR A: the maintainer decided it once, deliberately, and an unimplemented published contract is itself a defect. RECOMMENDED: B, correcting the docs, with `--agent` remaining the explicit way to get JSONL. Either way E-05 must remove the losing text; the plan does not depend on which.

### OQ-02: Should `--color` and `--no-color` be a mutually exclusive pair, or should the last flag win?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE, recorded so it is deliberate. The item specifies mutually exclusive with exit 2 ("`--no-color` with `--color` is a usage error, not a silent winner"), and that is the recommended and implemented choice: a silent winner makes a scripted invocation's behavior depend on argument order, which is exactly the unscriptability this item exists to fix. Implement mutual exclusion via argparse so the refusal is structural rather than hand-checked, and confirm the resulting exit code is 2 by measuring it UNPIPED.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the parser-walk enumeration BEFORE (naming the missing subcommands and their count) and AFTER (count 1, only `__complete`). Then paste at least four real invocations from the fixed set, including `aw oc run --no-color` and `aw agy run --no-color`, showing they no longer produce a usage error, with exit codes measured UNPIPED.
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
  - Required evidence: paste the new test's source (showing it walks the tree recursively and declares its exemption list), its FAILING output against pre-change code naming the missing subcommands, and its passing result after. A test that only passes after does not prove it would have caught the regression.
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
  - Required evidence: paste `--agent` and `--json` output for the same command under `--color`, `--no-color`, and neither, showing the payloads are BYTE-IDENTICAL and contain no ANSI escapes. Paste the `tests/test_output_contract.py` result and name any test deliberately changed by E-05 with its justification. Paste the bare `python3 -m pytest` summary line and compare it to the stated baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened. OQ-01 is BLOCKING: it decides whether every piped `aw` invocation changes format, and the item requires it settled before `--tty` is specified at all.

A reviewer should note this plan deliberately delivers TWO of the item's three requested flags plus the precondition for the third, with `--tty` deferred and its analysis recorded (F-7, F-8, E-06). If the maintainer wants `--tty` in this plan, it needs the OQ-01 ruling first and a fourth task group.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE that `cli.py` is large and shared, so re-enumerate the missing-subcommand set by walking the parser at execution time rather than trusting the list above, which has already moved once. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.

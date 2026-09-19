# IPD: Unify the three divergent should_color implementations and stop a falsey FORCE_COLOR forcing color on

- Date: 2026-09-19
- Kind: child
- Concern: THREE INDEPENDENT `should_color` IMPLEMENTATIONS DISAGREE WITH EACH OTHER, and one inverts the meaning of a value users set deliberately. Measured by EXECUTION 2026-09-19, not by reading. `term.py:90` checks `TERM`, tests `NO_COLOR` by PRESENCE, and lets `FORCE_COLOR` escape it. `runner_shared.py:276` IGNORES `TERM` entirely and tests by TRUTHINESS, so `TERM=dumb aw oc run` emits color while `TERM=dumb aw attention` does not. `pwatch.py:951` ignores `FORCE_COLOR` completely, so `FORCE_COLOR=1 aw pwatch | cat` is plain while every other command colorizes. Worst of the four: `FORCE_COLOR=0` FORCES COLOR ON, even to a pipe, because the string `"0"` is truthy in Python, so a user writing the value that plainly means "do not force" gets the opposite. This blocks spec `uonrjg` R9.3a.2, which requires the depth resolver have EXACTLY ONE definition: a resolver cannot have one definition while the capability decision beneath it has three.
- Scope: IN: one shared `should_color` with one definition, carrying the maintainer's 2026-09-19 semantics (`NO_COLOR` presence-only; `FORCE_COLOR` interprets falsey values); `runner_shared.py` and `pwatch.py` consuming it instead of reimplementing; and a test pinning every cell of the two measured tables, none of which is pinned today. OUT: the depth ladder and the 16-color tier (child `pow5sj`, which sits ON this seam), the `--color`/`--no-color` FLAG surface (plan `yaxr4i`), and any lifecycle glyph or palette work.
- Scope-Paths: agent_workflows/term.py, agent_workflows/runner_shared.py, agent_workflows/pwatch.py, tests/test_term.py
- Item-Dependencies: none
- Status: to-review
- Set: lifeglyph
- Order: 9
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: z8ddk0
- From-Backlog: nyz8dt
- Blocks-Release: next
- Work-Kind: bug

## Workflow history

- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `nyz8dt` on the maintainer's instruction to convert it into a lifeglyph child rather than keep it standalone. Carries `nyz8dt`'s `Blocks-Release: next` and `Work-Kind: bug`. ORDER 9 IS NOT ITS QUEUE POSITION: `queue_sort_key` puts `dependency_depth` FIRST, so this depth-0 child precedes `pow5sj`, which declares `executed:z8ddk0`. The Order number is a filename cluster, not evidence of sequence.

## Goal

Make the color capability decision have one definition with the maintainer's ruled semantics, so the depth resolver `pow5sj` builds can honestly claim R9.3a.2's "exactly one definition" and so a falsey `FORCE_COLOR` stops meaning its own opposite.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: One definition, with the ruled semantics

- [ ] E-01 Make `term.should_color` the single definition and apply the maintainer's 2026-09-19 semantics: `NO_COLOR` is PRESENCE-ONLY (any setting disables, empty included, no value interpreted); `FORCE_COLOR` INTERPRETS its value, so `0`/`false`/`no`/`off` mean NOT FORCING and fall through to ordinary TTY detection rather than suppressing.
  - Depends on: none
  - Expected outcome: `FORCE_COLOR=0` no longer forces color and no longer reaches a pipe; it falls through, giving color on a TTY and plain to a pipe. `FORCE_COLOR=1` still beats `NO_COLOR=1`, so `tests/test_term.py:48` keeps passing unchanged. The internal contradiction where `FORCE_COLOR=''` is read by presence on line 100 and by truthiness on line 103 is gone.
  - Execution state: pending

- [ ] E-02 Convert `runner_shared.py:276` and `pwatch.py:951` to consume the single definition instead of reimplementing it. Note this makes the runners start honoring `TERM=dumb` and makes `pwatch` start honoring `FORCE_COLOR`, both of which are behavior CHANGES and both correct.
  - Depends on: E-01
  - Expected outcome: exactly one `should_color` definition in the package. `TERM=dumb aw oc run` is plain, matching `aw attention`. `FORCE_COLOR=1 aw pwatch | cat` colorizes, matching every other command.
  - Execution state: pending

### Task group 2: Pin what was never pinned

- [ ] E-03 Pin EVERY cell of the two measured tables: the 4x4 `NO_COLOR` x `FORCE_COLOR` grid (unset / `''` / `'0'` / `'1'`) against both a TTY and a pipe, plus the `TERM` axis (`xterm-256color` / `dumb` / `''` / unset). None of the empty-string or `'0'` cases is pinned today, which is why all four defects survived: the behavior is accidental, not contractual.
  - Depends on: E-02
  - Expected outcome: a table-driven test whose cases are the measured grid. Reverting any part of E-01 or E-02 fails at least one named case.
  - Execution state: pending

- [ ] E-04 Add a guard asserting the package contains exactly ONE `should_color` definition, so a future module cannot quietly add a fourth. This is the mechanical property R9.3a.2 demands and that `pow5sj`'s V-01 will grep for.
  - Depends on: E-03
  - Expected outcome: a test that FAILS if a second definition is introduced. `pow5sj`'s one-definition evidence becomes true by construction rather than by inspection at that moment.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Verified 2026-09-19 BY EXECUTION: with `NO_COLOR=1 FORCE_COLOR=1` on a TTY, `term.should_color` returns True, so `FORCE_COLOR` currently beats `NO_COLOR` and the maintainer's Reading A preserves that.
- Verified 2026-09-19: `FORCE_COLOR=0` yields color to a PIPE in both `term.py` and `runner_shared.py`; `TERM=dumb` yields color in `runner_shared.py` but not `term.py`; `FORCE_COLOR=1` yields plain in `pwatch.py` alone.
- Verified 2026-09-19: NOTHING in the package, the runners, or CI ever SETS `NO_COLOR` or `FORCE_COLOR` (zero assignments; only a docstring mentions them), so both are always the user's own environment.
- `--no-color` exists on the shared `common` parser (`cli.py:832`) but does NOT set `NO_COLOR` or route through `should_color`: it constructs `Term(color=False)` directly. `--color` does not exist at all. Both facts belong to `yaxr4i`, not here.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md.
- `- Readiness:` is deliberately absent (it is `/plan-review`'s output; IPD-M107 refuses an unattested value).

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | `FORCE_COLOR=0` forces color ON, even to a pipe, because `"0"` is truthy. A user writing it means the opposite. This is the likeliest of the four to be hit, since `FORCE_COLOR=0` is common in CI configuration. | Measured 2026-09-19: `NO_COLOR` unset, `FORCE_COLOR='0'` gives COLOR to both a TTY and a pipe in `term.py` and `runner_shared.py`. |
| F-02 | High | Three implementations, three behaviors. They agree on the four ordinary cases and diverge on empty strings and on `TERM`, so the spec's Section 9.3 instruction to "preserve current behavior" is UNDERSPECIFIED: there are three current behaviors. | `term.py:90`, `runner_shared.py:276`, `pwatch.py:951`, each read and executed 2026-09-19. |
| F-03 | Medium | `yaxr4i` line 97 asserts "The color ENGINE is already correct and complete... it does not need new color logic". That premise is FALSIFIED by F-01 and F-02, and `yaxr4i` is `approved`, so an executor would otherwise trust it and leave the engine alone. This plan does not amend `yaxr4i` (it is approved and owns a different axis) but records the falsification so the next reader of that line is not misled. | `yaxr4i` line 97; contradicted by the measurements above. |
| F-04 | Medium | No test pins any empty-string or `'0'` case, so none of this behavior is contractual and all four defects were free to survive. | `grep` for `NO_COLOR.*= ""` in `tests/` returns nothing, 2026-09-19. |

## Proposed changes (ordered, validatable)

1. One definition in `term.py` carrying the ruled semantics (E-01).
2. `runner_shared` and `pwatch` consume it (E-02).
3. Table-driven pins for the full measured grid plus the `TERM` axis (E-03).
4. A guard forbidding a fourth definition (E-04).

## Deferred / out of scope (with reason)

- The `--color` / `--no-color` FLAG surface and their mutual exclusivity: owned by plan `yaxr4i` E-02, which the maintainer ruled on 2026-09-19 (two flags, mutually exclusive). This plan fixes the ENGINE those flags will sit on.
  - Carrier: yaxr4i
- The depth ladder, the authored 16-color tier, and `aw config` depth pinning: child `pow5sj`, which declares `executed:z8ddk0` so it builds on the unified seam.
  - Carrier: pow5sj
- Amending spec `uonrjg` Section 9.3a.2, whose "unchanged, and unconditional" wording is false as written (`FORCE_COLOR` does currently defeat `NO_COLOR`), and Section 9.3, which says "preserve current behavior" where three behaviors exist.
  - Carrier: 7p3tt8
- Amending `yaxr4i` to correct its falsified "engine is already correct and complete" premise (F-03).
  - Carrier-Declined: NOT THIS PLAN'S TO EDIT, and the risk it guards against is already removed by this plan EXISTING. `yaxr4i` is `approved` and owns the flag surface, a different axis; amending an approved plan to fix a premise about work this plan now performs would be churn. The hazard was that an executor trusts line 97 and leaves the engine alone, and that cannot happen once the engine is owned by a child with its own E-items. F-03 records the falsification so the next reader of that line is not misled, which is the durable part.

## Scope check

- Over-scope: none. Each E-item maps to a measured divergence or to R9.3a.2's one-definition requirement.
- Under-scope: none for the engine. NOTE this plan deliberately does NOT widen to the flag surface even though it is adjacent, because `yaxr4i` already owns it and two plans editing one argparse parent is how a Set acquires merge conflicts for no benefit.

## Required tests / validation

Run the suite BARE: `python3 -m pytest`, and paste the actual summary line. E-02 changes runner and pwatch behavior, so the run must be read for collateral damage rather than only for green: any test that encoded the OLD divergence (runner colorizing under `TERM=dumb`, pwatch ignoring `FORCE_COLOR`) should be UPDATED with its reason recorded, never deleted silently.

## Spec / documentation sync

No `.spec.md` edit here, so none is declared in `- Scope-Paths:`. The two false statements in `uonrjg` (Section 9.3a.2's "unchanged, and unconditional" and Section 9.3's "preserve current behavior") are carried by child `7p3tt8`, which already declares a specs path and owns the amendment work. `docs/cli-human-guide.md`'s color section is likewise `7p3tt8`'s.

## Open questions

### OQ-01: Should `--no-color` route through the unified `should_color` rather than bypassing it?

- Blocking: no
- Status: open
- Owner: none
- Carrier: yaxr4i
- Resolution or deferral rationale: NOT BLOCKING because this plan's own deliverable is complete without it: unifying three implementations and fixing the falsey-value inversion neither needs nor prevents the flag routing change. Recorded because the measurement that found the three divergent engines also found that `--no-color` does not reach any of them (`cli.py:832` sets `Term(color=False)` directly), which means the top rung of the precedence chain is split across two layers, and `pow5sj` F-06 already notes the same thing. The flag layer is `yaxr4i`'s, which is why the carrier points there rather than at this plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the executed 4x4 grid (`NO_COLOR` unset/`''`/`'0'`/`'1'` x `FORCE_COLOR` unset/`''`/`'0'`/`'1'`) against a TTY and a pipe, showing: `FORCE_COLOR='0'` now falls through (COLOR on a TTY, plain to a pipe) rather than forcing; `NO_COLOR=''` disables; and `FORCE_COLOR='1'` still beats `NO_COLOR='1'`. Paste `tests/test_term.py:48` `test_force_color_overrides_no_color` PASSING unchanged, since the ruling preserves it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste `grep -rn "def should_color" agent_workflows/` returning exactly ONE line. Paste `TERM=dumb` output from a runner command and from `aw attention` showing both plain (they diverge today). Paste `FORCE_COLOR=1 ... | cat` from `pwatch` showing color (plain today).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the new table-driven test's case list and its passing output, showing a named case for every cell of the 4x4 grid on both stream kinds plus the four `TERM` values. Then prove the pins BITE: revert E-01's `FORCE_COLOR` change in a scratch edit, paste the suite FAILING with the case named, and restore. A pin that cannot fail is not evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the guard test passing, then add a second `def should_color` in a scratch module, paste the guard FAILING, and remove it. Paste the BARE `python3 -m pytest` summary line for the final state. Also list any test updated because it encoded the old divergence, with the reason for each.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved z8ddk0 --by-human`). It declares NO dependencies and is depth-0, so `queue_sort_key` places it ahead of `pow5sj`, which declares `executed:z8ddk0`. Its Order of 9 is a filename cluster and is NOT its queue position; the runner sorts by dependency depth first and re-checks each edge at dispatch.

WHY THIS CHILD EXISTS RATHER THAN A STANDALONE BACKLOG ITEM: it was first filed as backlog `nyz8dt`, on three reasons the maintainer asked me to re-examine, of which two were FALSE (the Set already declares `term.py` and `runner_shared.py` in three children's `Scope-Paths`, and `yaxr4i` does NOT rewrite the engine, it asserts the engine is already correct) and one was unsupported (`pow5sj`'s scope does not exclude behavior changes). The maintainer then ruled to convert it. Recorded because the honest reason for a plan's shape is worth more to a later reader than a tidy one.

On completion: append the workflow-history line, set the terminal `Status: executed`, and `git mv` this plan to `.aw/records/plans/executed/` as a post-gate lifecycle step via `aw ipd finalize`, never as a checklist item. Commit path-scoped; never push.

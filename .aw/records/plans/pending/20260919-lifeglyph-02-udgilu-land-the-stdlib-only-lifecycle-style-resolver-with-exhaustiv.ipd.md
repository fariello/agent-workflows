# IPD: Land the stdlib-only lifecycle_style resolver with exhaustive owner-enum coverage tests

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` R10.1 requires ONE semantic source for lifecycle presentation, and it does not exist: `agent_workflows/lifecycle_style.py` is absent (verified 2026-09-19). Meanwhile four partial tables are live and disagree, which is the spec's Section 1 problem statement measured in code: `term.py:117 STATUS_COLOR_256`, `attention.py:1403 _STATUS_COLOR_256`, `render_stream.py:51 _STATUS_COLOR`, and the re-export chain `oc_runipd.py:104` / `agy_runipd.py:104` / `runner_shared.py:168` that spreads `render_stream`'s palette into both drivers. Nothing can be converted to a shared resolver until the resolver exists.
- Scope: IN: create `agent_workflows/lifecycle_style.py` containing the 21 semantic stages of Section 5 with their Unicode glyph, ASCII fallback, xterm-256 index and bold flag; the native mappings of Sections 6.1-6.7; the runner/ledger mappings of Sections 7.1-7.4; the precedence resolver of Section 8; and the self-validation of R10.1 that rejects duplicate keys and incomplete coverage. Plus the A2 enumeration tests that fail when an owner adds a status without a mapping. OUT: emitting any ANSI (R10.1 forbids it in this module), the depth ladder and 16-color tier (child `pow5sj`), the `Term` rendering helpers (child `bn026f`), and converting any consumer (children `f9t5hz` onward).
- Scope-Paths: agent_workflows/lifecycle_style.py, tests/test_lifecycle_style.py
- Item-Dependencies: executed:yaxr4i, executed:n4xq3l
- Status: to-review
- Set: lifeglyph
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: udgilu
- From-Spec: uonrjg
- Blocks-Release: next

## Workflow history

- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from spec uonrjg R10.1/R10.4 and Section 12 step 1. Carries the spec's `Blocks-Release: next` gate and the Section 12a `executed:yaxr4i` edge.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Create the single stdlib-only module that resolves any artifact status, runner state, or ledger state to exactly one semantic presentation stage, with tests that fail when a new owner status lacks a mapping, so every later child has one authority to consume.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The stage vocabulary and its data

- [ ] E-01 Create `agent_workflows/lifecycle_style.py` defining the 21 semantic stages of spec Section 5 as an immutable table, each carrying its Unicode grapheme, ASCII fallback character, xterm-256 foreground index, and bold flag. Use the exact text-presentation forms: `⚠︎` is U+26A0 U+FE0E and `↩︎` is U+21A9 U+FE0E.
  - Depends on: none
  - Expected outcome: Importing the module yields a stage table whose values match spec Section 5 row for row. The module imports only from the standard library and emits no ANSI.
  - Execution state: pending

- [ ] E-02 Add the native artifact mappings of spec Sections 6.1 through 6.7, scoped by artifact family (plans, specs, backlog, research, prompts, releases, reviews/no-lifecycle), plus the `unknown` versus `none` distinction R10.4 requires.
  - Depends on: E-01
  - Expected outcome: Each family maps its own status set, and a known family with an unrecognized status resolves `unknown` while a family with no lifecycle resolves `none`. Neither silently becomes parked gray.
  - Execution state: pending

- [ ] E-03 Add the runner, ledger, and set-state mappings of spec Sections 7.1 through 7.4, INCLUDING the five rows the spec added at review that a naive reading would drop: `needs_input` and `awaiting-human` to `waiting-input`, `ran` to `recovering`, `unknown_outcome` to `failed`, and `quarantined` to `parked`.
  - Depends on: E-01
  - Expected outcome: All five formerly-orphan words resolve to their spec-assigned stage rather than falling through to `unknown`. `ran` resolves `recovering` and NOT `done`; `unknown_outcome` resolves `failed` and NOT `unknown`.
  - Execution state: pending

### Task group 2: The resolver and its self-validation

- [ ] E-04 Implement the Section 8 precedence resolver: integrity-failure, then named obstruction, then live activity, then native mapping, then `unknown`, then `none`. Return the native status and the activity SEPARATELY from the resolved stage, and mutate neither input.
  - Depends on: E-02, E-03
  - Expected outcome: A resolver that returns an immutable result carrying stage, native status, and activity as distinct fields. A failed integrity input wins over a stale active field; a blocked obstruction wins over a ready native status.
  - Execution state: pending

- [ ] E-05 Add the R10.1 self-validation that rejects duplicate stage keys and incomplete known-status coverage, raising at import or via an explicit validate call rather than degrading silently.
  - Depends on: E-04
  - Expected outcome: A duplicate key or a mapping table missing a known status is a hard error with a message naming the offending key, not a silent gray fallthrough.
  - Execution state: pending

- [ ] E-06 Add `tests/test_lifecycle_style.py` implementing criterion A2: enumerate the repository's OWNER enums (the real status vocabularies for plans, specs, backlog, research, prompts, releases, runner dispositions, ledger states) and assert every member resolves to exactly one stage, so a later change that adds a status without a mapping FAILS.
  - Depends on: E-05
  - Expected outcome: The test discovers statuses from the owners rather than from a hand-copied list, so it cannot drift. Adding a fake status to an owner enum in a test fixture makes the suite fail.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Verified 2026-09-19: `agent_workflows/lifecycle_style.py` does not exist, so every E-item here is genuinely new work rather than a refactor.
- Verified 2026-09-19: four live lifecycle palettes exist at `term.py:117`, `attention.py:1403`, `render_stream.py:51`, and via re-export into both runners (`oc_runipd.py:104`, `agy_runipd.py:104`, `runner_shared.py:168`). This child does NOT delete them; `qdd5jq` does, after every consumer is converted, per spec Section 12 step 6.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `- Readiness:` is deliberately absent (it is `/plan-review`'s output; IPD-M107 refuses an unattested value).

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | The single semantic source the spec's whole architecture rests on does not exist, so this child is on the critical path for every other code child in the Set. | `ls agent_workflows/lifecycle_style.py` -> No such file or directory, verified 2026-09-19. |
| F-02 | High | Four independent lifecycle palettes are live today, confirming the spec's Section 1 problem statement is current rather than historical. | `term.py:117`, `attention.py:1403`, `render_stream.py:51`, plus re-exports at `oc_runipd.py:104`, `agy_runipd.py:104`, `runner_shared.py:168`. |
| F-03 | Medium | Three of the five review-added rows are judgement calls the spec argues at length, so an implementer working from Section 5 alone would plausibly get them wrong. `ran` to `recovering` (not `done`) and `unknown_outcome` to `failed` (not `unknown`) are the two most likely errors. | `uonrjg` Section 7.2 commentary and D13/D14; `ran` as `done` would paint an exit-1 item as success. |

## Proposed changes (ordered, validatable)

1. Stage table with exact graphemes and text-presentation selectors (E-01).
2. Native artifact mappings plus the unknown/none distinction (E-02).
3. Runner, ledger, and set-state mappings including the five review-added rows (E-03).
4. The precedence resolver returning stage, status, and activity separately (E-04).
5. Self-validation rejecting duplicates and incomplete coverage (E-05).
6. Owner-enum enumeration tests implementing A2 (E-06).

## Deferred / out of scope (with reason)

- ANSI emission: R10.1 explicitly forbids it in this module; rendering is `bn026f`'s.
  - Carrier: bn026f
- The depth ladder, the authored 16-color tier, and `aw config` pinning: child `pow5sj`, because they are a `term.py` concern and A12a-A12d are written against the rendering seam, not the semantic one.
  - Carrier: pow5sj
- Deleting the four duplicate tables: child `qdd5jq`, after all consumers convert, per Section 12 step 6. Deleting earlier would break live views.
  - Carrier: qdd5jq
- A display-width helper: spec Section 9.4 records that reusing `render_stream`'s proven ASCII-table-behind-a-capability-flag pattern satisfies the requirement WITHOUT a width helper, and calls that the cheaper route. No helper is built here.
  - Carrier-Declined: A conforming alternative is CHOSEN, not postponed. Section 9.4 is satisfied in full by the ASCII-table-behind-a-capability-flag route, which the spec itself calls the cheaper and already-proven option. Nothing is outstanding; a future consumer needing true width is bound by Section 9.4 to make it shared, which is that change's constraint rather than this plan's debt.

## Scope check

- Over-scope: none. Each E-item maps to a named R10.1 bullet or to criterion A2.
- Under-scope: none for the semantic layer. The rendering, depth, and conversion layers are deliberately separate children because they have independent test surfaces (capability matrix, config validation, per-consumer snapshots) and would each make this item unreviewable in one pass.

## Required tests / validation

Run the suite BARE: `python3 -m pytest`. Paste the actual summary line. The new `tests/test_lifecycle_style.py` must cover: every stage's glyph/ASCII/color/bold matching Section 5; every owner enum member resolving (A2); the five review-added rows resolving to their spec-assigned stage; the precedence order of Section 8; and the `unknown` versus `none` distinction (R10.4, criterion A20).

## Spec / documentation sync

No spec amendment in this child. `uonrjg` is implemented BY this Set rather than changed by it, and the one amendment the spec demands (`25kzda` Section 5.6) is carried by child `7p3tt8`. No `.spec.md` file is declared in `- Scope-Paths:` here, which is deliberate and correct: declaring one would make both runners announce a spec edit this child does not make.

## Open questions

### OQ-01: Which owner enums are the authoritative source for the A2 enumeration?

- Blocking: no
- Status: open
- Owner: none
- Carrier-Declined: RESOLVED INSIDE THIS PLAN'S OWN EXECUTION by reading the repository, so nothing outlives it. E-06 must enumerate the owner modules that define each status vocabulary, and V-06 requires proof the resulting test can FAIL (add a bogus status, show the suite red, remove it, show it green). A test that cannot fail would be caught by that evidence demand rather than escaping as a silent debt.
- Resolution or deferral rationale: NOT BLOCKING because the answer is discoverable from the repository at execution time rather than requiring a human ruling: each records tree has an owner module that defines its status vocabulary, and criterion A2 says to enumerate "the repository's owner enums". The executing agent must READ those owners rather than hand-copying a status list into the test, since a hand-copied list is exactly the drift A2 exists to catch. Recorded as a question rather than silently assumed because the enumeration's completeness is what makes A2 meaningful, and an agent that guesses the wrong source produces a test that passes while covering nothing.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste a Python one-liner's output dumping each stage's glyph, ASCII char, color index, and bold flag, and diff it against spec Section 5's table by eye in the evidence block. Additionally paste the code points of `⚠︎` and `↩︎` proving U+FE0E is present (criterion A5 requires the emoji forms be absent).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste resolver output for every native status in spec Sections 6.1-6.7, showing the resolved stage for each. Include one unrecognized status in a KNOWN family proving it yields `unknown`, and one no-lifecycle family proving it yields `none`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste resolver output for all five review-added words. `ran` MUST show `recovering`, `unknown_outcome` MUST show `failed`, `needs_input` and `awaiting-human` MUST show `waiting-input`, `quarantined` MUST show `parked`. A run showing `ran` as `done` or `unknown_outcome` as `unknown` FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste test output for the Section 8 precedence cases: a failed-integrity input beating a stale active field (criterion A8), a blocked obstruction beating a ready native status (A9), and a live activity beating a native mapping (A7). Also paste evidence the resolver returned native status and activity as separate fields and mutated neither input.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the raised error (message included) from a deliberately duplicated stage key, and from a mapping table with a known status removed. Silent success on either FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste the BARE `python3 -m pytest` summary line. Then paste proof the A2 test actually bites: add a bogus status to an owner enum in a scratch fixture, show the suite FAILING, then remove it and show it passing. A test that cannot fail is not evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved udgilu --by-human`). Its `- Item-Dependencies: executed:yaxr4i, executed:n4xq3l` edges are re-checked at dispatch: `yaxr4i` because spec Section 12a makes it upstream, and `n4xq3l` because the same section forbids building the resolver before the re-review round is recorded.

On completion: append the workflow-history line, set the terminal `Status: executed`, and `git mv` this plan to `.aw/records/plans/executed/` as a post-gate lifecycle step via `aw ipd finalize`, never as a checklist item. Commit path-scoped; never push.

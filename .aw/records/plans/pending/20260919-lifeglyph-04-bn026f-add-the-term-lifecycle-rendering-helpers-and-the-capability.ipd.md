# IPD: Add the Term lifecycle rendering helpers and the capability matrix tests

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` R10.2 keeps `agent_workflows/term.py` as the terminal capability and ANSI boundary, and requires it to expose a small rendering API over the resolver that `udgilu` builds: `resolve_lifecycle`, `format_lifecycle_marker`, and `style_lifecycle_text`. Resolution and rendering MUST remain separate and testable, which is precisely what the current code does not do: `term.py:287`, `term.py:394`, and `term.py:469` each look up `STATUS_COLOR_256` inline at the point of emitting ANSI, so there is no seam to test resolution independently of styling. Without these helpers no consumer can be converted, because every consumer needs a rendering entry point rather than a bare data structure.
- Scope: IN: the three R10.2 helpers (names may differ, per the spec, but resolution and rendering MUST stay separate); the Section 9.1 full-row styling rule that glyph, id6, and status share one color and weight while type and title do not; the Section 9.2 compact `GLYPH id6` form and the legend; the Section 9.4 grapheme-safety rule that no visible column is computed with `len()`; and the criterion A16 capability matrix. OUT: the semantic tables (child `udgilu`), the depth ladder (child `pow5sj`), and every consumer conversion (children `f9t5hz` onward). Also OUT: building a display-width helper, for the reason in Deferred.
- Scope-Paths: agent_workflows/term.py, tests/test_term.py
- Item-Dependencies: executed:udgilu, executed:pow5sj
- Status: to-review
- Set: lifeglyph
- Order: 4
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: bn026f
- From-Spec: uonrjg
- Blocks-Release: next

## Workflow history

- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from spec uonrjg R10.2, Sections 9.1/9.2/9.4, and criteria A10/A15/A16. Carries the spec's `Blocks-Release: next` gate.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give every consumer one rendering entry point that turns a resolved lifecycle stage into styled terminal output, with resolution and rendering separated so each is testable alone, and with grapheme handling that survives variation selectors and ANSI stripping.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The rendering API

- [ ] E-01 Add the R10.2 helpers to `agent_workflows/term.py`: a resolve entry point delegating to `lifecycle_style` (no semantic data duplicated into `term.py`), a marker formatter returning the glyph in the active tier's form, and a text styler applying the resolved color and bold to a given string.
  - Depends on: none
  - Expected outcome: Three callable helpers. Resolution returns data with no ANSI; only the rendering helpers emit escapes. `term.py` gains no lifecycle stage table of its own.
  - Execution state: pending

- [ ] E-02 Implement the Section 9.1 full-row rule: glyph, id6, and status word take the SAME resolved color and bold flag, while artifact type, title, and path take none. Whole-row coloring must be impossible through this API rather than merely discouraged.
  - Depends on: E-01
  - Expected outcome: A caller styling a full row gets the three lifecycle elements colored identically and the rest neutral. Criterion A10 holds.
  - Execution state: pending

- [ ] E-03 Implement the Section 9.2 compact form `GLYPH id6` with glyph and id6 styled together, plus the legend the section requires to be available in command help and shown once in a view with three or more stages.
  - Depends on: E-01
  - Expected outcome: A compact id6-only view communicates the stage, and a legend renders in word order matching the lifecycle rather than in color-name order (Section 11 item 6).
  - Execution state: pending

### Task group 2: Grapheme safety and the capability matrix

- [ ] E-04 Enforce the Section 9.4 rule that a lifecycle symbol is an opaque grapheme: ANSI stripping, padding, and truncation operate on visible text, and no visible column is computed with `len(styled_text)`. Reuse the proven `render_stream` pattern (an ASCII substitution table behind one capability flag) rather than adding a width helper.
  - Depends on: E-01
  - Expected outcome: Variation selectors survive stripping and truncation (criterion A15). No new `len()`-based column arithmetic is introduced on styled text.
  - Execution state: pending

- [ ] E-05 Add the criterion A16 capability matrix tests covering the normal UTF-8 profile, ASCII mode, colored TTY, plain TTY, piped output, and `TERM=dumb`, plus A13 (`FORCE_COLOR` enables ANSI per existing precedence but does not force Unicode onto an incompatible stream).
  - Depends on: E-02, E-03, E-04
  - Expected outcome: Six named environment profiles asserted, each showing the expected glyph form and ANSI presence. `FORCE_COLOR` does not override ASCII stream capability.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Verified 2026-09-19: `term.py` looks up `STATUS_COLOR_256` inline at three separate emit sites (term.py:287, 394, 469), which is why R10.2's separation requirement is a real refactor rather than a rename.
- Verified 2026-09-19: `AW_ASCII_ONLY` and `FORCE_ASCII` already exist in `term.py`, so the ASCII half of the capability matrix tests existing behavior.
- Spec Section 9.4 records that NO display-width helper exists in the package (no `wcwidth`, no `display_width` symbol) and that `render_stream.py` deliberately did not build one, solving the same problem with an ASCII table behind a `use_unicode` flag. That is the pattern to reuse.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md.
- `- Readiness:` is deliberately absent (it is `/plan-review`'s output; IPD-M107 refuses an unattested value).

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | Resolution and rendering are currently fused at three sites in `term.py`, so there is no seam at which a test can check resolution without also checking ANSI. R10.2 exists to fix exactly this. | `term.py:287`, `term.py:394`, `term.py:469` each call `STATUS_COLOR_256.get(...)` immediately before emitting. |
| F-02 | Medium | Two glyphs this spec uses are already MEASURED as East Asian Width ambiguous by `render_stream.py`: `▶` U+25B6 (`executing`) and `◇` U+25C7 (`parked`). So Section 9.4's alignment caveat applies to this spec's own symbols and is not hypothetical. | `uonrjg` Section 9.4 prior-art note, citing `render_stream`'s own `east_asian_width` measurement over its ten glyphs, five ambiguous. |
| F-03 | Medium | `render_stream.py` computes its padding in CODEPOINTS via `len`, which is the exact failure Section 9.4 forbids, and it documents this as "exact only for glyphs a terminal renders SINGLE-WIDTH". Converting that module (child `qdd5jq`) inherits the problem, so these helpers must not replicate the pattern. | `uonrjg` Section 9.4 prior-art note. |

## Proposed changes (ordered, validatable)

1. The three R10.2 helpers with resolution and rendering separated (E-01).
2. The Section 9.1 full-row color discipline (E-02).
3. The Section 9.2 compact form and legend (E-03).
4. Grapheme-safe stripping, padding, and truncation (E-04).
5. The A16 capability matrix plus A13 (E-05).

## Deferred / out of scope (with reason)

- A display-width helper (wcwidth-style 0/1/2 table): spec Section 9.4 permits one but records that reusing `render_stream`'s ASCII-table-behind-a-flag pattern satisfies the section WITHOUT one, and calls that the cheaper and already-proven route. Choosing the cheaper conforming route is not under-scope. If a later consumer genuinely needs true width, Section 9.4 requires it be SHARED rather than per-module, which is a separate change.
  - Carrier-Declined: A conforming alternative is CHOSEN, not postponed. Section 9.4 permits a width helper but records that the ASCII-table route satisfies the section without one and is the cheaper, already-proven path. Nothing is outstanding.
- Per-consumer snapshot updates: each conversion child owns its own snapshots, because a snapshot belongs with the view that produces it.
  - Carrier: f9t5hz
- Generic `Term` OK/WARN/FAIL outcomes: R10.3 explicitly keeps them valid and outside this spec, and warns against mechanically replacing every checkmark in the repository.
  - Carrier-Declined: EXPLICITLY OUT OF SCOPE by the spec: R10.3 keeps these valid and warns against mechanically replacing every checkmark in the repository. There is no obligation to carry, and creating one would assert work the spec forbids.

## Scope check

- Over-scope: none. Every E-item maps to R10.2, Section 9.1, 9.2, 9.4, or criterion A13/A15/A16.
- Under-scope: none for the rendering boundary. The consumers are deliberately separate children because each carries its own snapshot surface and can regress independently.

## Required tests / validation

Run the suite BARE: `python3 -m pytest`. Paste the actual summary line. Tests must cover criterion A10 (glyph, id6, status share one color; titles and paths do not), A13 (`FORCE_COLOR` precedence without forcing Unicode), A15 (variation selectors survive ANSI stripping, truncation, snapshots, copyable output), and A16 (the six-profile capability matrix).

## Spec / documentation sync

No `.spec.md` edit in this child, so none is declared in `- Scope-Paths:`. The canonical legend's appearance in command help and user documentation is child `7p3tt8`'s item; this child only provides the legend RENDERER.

## Open questions

### OQ-01: Do the helpers keep the spec's suggested names or adopt existing term.py naming?

- Blocking: no
- Status: open
- Owner: none
- Carrier-Declined: PRE-ANSWERED BY THE SPEC, so there is no obligation at all. R10.2 states "Names may differ, but resolution and rendering MUST remain separate and testable", making the constraint structural rather than lexical. This question is recorded only to stop a later reviewer reading the spec's three example names as a literal API requirement; it creates no work.
- Resolution or deferral rationale: NOT BLOCKING, and the spec pre-answers it: R10.2 says "Names may differ, but resolution and rendering MUST remain separate and testable." So the constraint is structural, not lexical, and the executing agent should follow whatever `term.py` already does for naming consistency. Recorded only so a later reviewer does not read the spec's three example names as a literal API requirement and file a finding against a conforming implementation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the three helper signatures and proof that the resolve entry point returns ANSI-free data (show its raw repr containing no escape bytes). Paste `grep` proving `term.py` contains no NEW lifecycle stage table of its own.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste a rendered full row with escapes visible (e.g. via `repr`), showing the SAME color code on glyph, id6, and status word, and NO color code on type or title. Criterion A10.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste a compact `GLYPH id6` render with glyph and id6 styled together, and paste the legend output showing lifecycle word order rather than color-name order.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste a round trip proving variation selectors survive: style a `⚠︎` row, strip ANSI, truncate it, and show U+FE0E still present in the code points. Paste `grep` proving no `len(` is applied to styled text in the new code. Criterion A15.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the BARE `python3 -m pytest` summary line, then the six capability profiles each with its asserted output: UTF-8, ASCII mode, colored TTY, plain TTY, piped, `TERM=dumb`. Include the `FORCE_COLOR`-does-not-force-Unicode case explicitly (A13).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved bn026f --by-human`). Its `- Item-Dependencies: executed:udgilu, executed:pow5sj` edges are re-checked at dispatch: `udgilu` supplies the semantic data these helpers render, and `pow5sj` supplies the depth tier the marker formatter selects.

On completion: append the workflow-history line, set the terminal `Status: executed`, and `git mv` this plan to `.aw/records/plans/executed/` as a post-gate lifecycle step via `aw ipd finalize`, never as a checklist item. Commit path-scoped; never push.

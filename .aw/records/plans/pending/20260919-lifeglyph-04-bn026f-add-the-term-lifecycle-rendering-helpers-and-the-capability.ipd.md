# IPD: Add the Term lifecycle rendering helpers and the capability matrix tests

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` R10.2 keeps `agent_workflows/term.py` as the terminal capability and ANSI boundary, and requires it to expose a small rendering API over the resolver that `udgilu` builds: `resolve_lifecycle`, `format_lifecycle_marker`, and `style_lifecycle_text`. Resolution and rendering MUST remain separate and testable, which is precisely what the current LIFECYCLE path does not do: `Term.status_256` (`term.py:285-291`) calls `STATUS_COLOR_256.get(status.lower(), 244)` and `self.color256(...)` on consecutive lines, so there is no seam at which a test can check resolution without also checking ANSI. Without these helpers no consumer can be converted, because every consumer needs a rendering entry point rather than a bare data structure.
  ONLY ONE OF `term.py`'S FOUR TABLE READS IS A LIFECYCLE SITE, corrected at review after this field cited three (see F-04). Measured 2026-09-19: `grep -n STATUS_COLOR_256 agent_workflows/term.py` returns the definition at 117 and reads at 287, 394, 469, 477. Of the four reads, `Term.status_256` (287) is the lifecycle path this child replaces; `Term.format_outcome` (394) renders a GENERIC command-outcome banner (its only callers are `renderers.py:89` with a command result's status and `term.py:625` with the default `"clean"`), `Term.badge` (469) resolves an arbitrary caller-supplied `role_or_code`, and `Term.format_path` (477) looks up the non-lifecycle `"paths"` role. R10.3 keeps all three of those explicitly OUT of this spec ("Generic `Term` outcomes such as command-level OK, WARN, and FAIL remain valid... Do not mechanically replace every checkmark"), and this plan's own Deferred section says the same, so citing them as the fusion to fix contradicted both. The seam argument stands on `status_256` alone.
- Scope: IN: the three R10.2 helpers (names may differ, per the spec, but resolution and rendering MUST stay separate); the Section 9.1 full-row styling rule that glyph, id6, and status share one color and weight while type and title do not; the Section 9.2 compact `GLYPH id6` form and the legend RENDERER; the Section 9.4 grapheme-safety contract, including the ANSI-and-zero-width-aware visible-width measurement and grapheme-safe truncation that contract requires in UTF-8 mode; and the criterion A16 capability matrix. OUT: the semantic tables (child `udgilu`), the depth ladder (child `pow5sj`), and every consumer conversion (children `f9t5hz` onward). Also OUT: placing the legend in command help or in user documentation (child `7p3tt8`), converting the generic `format_outcome`/`badge`/`format_path` roles named in Concern, and a full wcwidth-style 0/1/2 East-Asian-width table, for the reason in Deferred.
- Scope-Paths: agent_workflows/term.py, tests/test_term.py
- Item-Dependencies: executed:udgilu, executed:pow5sj
- Status: reviewed
- Readiness: go-pending-approval
- Set: lifeglyph
- Order: 4
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: bn026f
- From-Spec: uonrjg
- Blocks-Release: next

## Workflow history
- 2026-09-19 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED. PR-401..PR-407 all FIXED, none deferred, none open. Two HIGH scope-understatements fixed: E-04 delegated all of spec Section 9.4 to an ASCII table satisfying one of its four contract bullets (three fail by measurement in UTF-8 mode), and E-03 claimed legend placement obligations this child structurally cannot meet. Readiness go-pending-approval; dispatch still gated by udgilu PR-203 and pow5sj PR-301.

- 2026-09-19 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-401 through PR-407 all FIXED, none deferred, none open. Reviewed at HEAD `a25fe45d`; `aw ipd lint --phase author --agent` clean, exit 0, before and after. THE DESIGN IS SOUND AND ITS SEQUENCING IS RIGHT; both serious findings were SCOPE UNDERSTATEMENTS that would have let a conforming-looking execution leave release-gating criteria unmet. PR-403 (HIGH): E-04 delegated ALL of Section 9.4 to the ASCII substitution table, but that table satisfies only the section's THIRD contract bullet and is inert in UTF-8 mode where the other three live, and all three FAIL by measurement today (`status_256('⚠︎', width=4)` pads to 4 codepoints but 3 rendered columns while `◕` gives 4 and 4; `format_table` leaves a VS15 row one column short; `render_stream._one_line` DROPS U+FE0E when clipping at a boundary). E-04 now requires a zero-width-aware width measurement and a VS-safe truncation, scoped to this child's own rendering, with the wcwidth/ambiguous-width part still correctly declined - the boundary being that AMBIGUOUS width is a terminal-policy judgement Section 9.4 admits is unreachable, while ZERO width is a deterministic Unicode property. PR-402 (HIGH): E-03 claimed Section 9.2's legend PLACEMENT obligations ("available in command help", "shown once in a view with 3+ stages") that this child structurally cannot meet, since its Scope-Paths is `term.py` plus its test and it runs before any consumer view exists; placement is `7p3tt8`'s and this file was the ONLY one in the Set mentioning the showing rule, so it was the single point where that rule could have been lost. PR-401 (MEDIUM) corrects a factual claim the plan led with: the Concern cited THREE fusion sites, but `format_outcome` and `badge` are generic command-outcome roles R10.3 explicitly keeps OUT and this plan's own Deferred section already excluded, so only `status_256` is a lifecycle site. V-04 now demands four separate measured pastes, one per Section 9.4 bullet, including a truncation asserted at the ADVERSARIAL boundary, because a plausible single round trip passes while three bullets fail. Suite baseline recorded: `8369 passed, 3 skipped, 2 xfailed`. OQ-01 resolved from the spec text. Readiness go-pending-approval; note both declared dependencies carry unresolved blocking questions of their own, so dispatch waits on those rulings regardless.
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

- [ ] E-03 Implement the Section 9.2 compact form `GLYPH id6` with glyph and id6 styled together. Also add the legend RENDERER: one function that emits every stage's glyph, ASCII fallback, and word, GENERATED from `lifecycle_style`'s table rather than from a literal list, ordered in lifecycle word order and not by color name (Section 11 item 6).
  - Depends on: E-01
  - Expected outcome: A compact id6-only view communicates the stage. A legend renderer exists, is generated from the shared table so it cannot drift, and orders stages as Section 5 does.
  - Execution state: pending

  THE BOUNDARY WITH `7p3tt8`, tightened at review (F-06) because the original wording claimed Section 9.2's PLACEMENT obligations that this child cannot discharge. Section 9.2 requires a legend to be "available in the command help" and "SHOWN ONCE in a view that contains three or more semantic stages". Neither is achievable here: this child's `- Scope-Paths:` is `term.py` and `tests/test_term.py`, so it touches no argparse help and no view, and it is ordered BEFORE every consumer conversion, so no converted view exists yet to show a legend in. `7p3tt8` E-03/E-04 own both (help placement, documentation reference, and the generated-not-hand-maintained drift guard), and `grep` confirms this plan was the ONLY file in the Set mentioning the "three or more" rule, so claiming it here was the one place it could have been lost between the two children. This child owns the RENDERER; `7p3tt8` owns where it appears. The GENERATED-FROM-THE-TABLE property is stated here rather than left to `7p3tt8` because a hand-written literal legend shipped in `term.py` is what `7p3tt8` E-04's drift guard would then have to retrofit.

  ONE SHOWING RULE TO HAND FORWARD, not to implement: the "show once per view with 3+ stages" decision is a per-view judgement and each converting child (`f9t5hz`, `9zvl2w`, `qdd5jq`) applies it to its own view. This child MUST NOT add a call-count or once-per-process latch to `term.py` to enforce it, because a module-level latch would make output depend on invocation order and would be untestable in a shared-process suite.

### Task group 2: Grapheme safety and the capability matrix

- [ ] E-04 Enforce the Section 9.4 rule that a lifecycle symbol is an opaque grapheme, in UTF-8 mode as well as ASCII mode. Add TWO small shared primitives in `term.py` and route this child's own marker/row/compact rendering through them: (a) a visible-width measurement that strips ANSI AND counts a zero-width code point as 0 columns, and (b) a truncation that never severs a base character from its following variation selector. The ASCII substitution table (`render_stream`'s proven pattern) remains the ASCII-mode answer and is necessary but NOT sufficient, for the measured reason below.
  - Depends on: E-01
  - Expected outcome: `⚠︎` and `↩︎` measure 1 visible column rather than 2, so a padded lifecycle column aligns in UTF-8 mode; truncating a styled row at any boundary leaves U+FE0E attached to its base (criterion A15); and no visible column in the new code is computed with a bare `len()` on styled or VS-bearing text.
  - Execution state: pending

  WHY THE ASCII TABLE ALONE DOES NOT SATISFY SECTION 9.4, added at review (F-05) after measuring all four of the section's contract bullets. The ASCII table delivers exactly ONE of them (bullet 3, "guaranteed single-byte alignment in ASCII mode"). Bullets 1, 2 and 4 are UTF-8-MODE obligations and an ASCII substitution table is inert in UTF-8 mode by construction, because the substitution never happens there. All three currently FAIL, measured by execution on 2026-09-19 rather than read:

  ```text
  # bullet 2 (stable alignment in the normal UTF-8 profile) - term.status_256 pads by codepoint
  Term(color=False).status_256('\u26a0\ufe0e', width=4) -> '⚠︎  '   codepoints=4  rendered_cols=3
  Term(color=False).status_256('\u25d5',       width=4) -> '◕   '  codepoints=4  rendered_cols=4
  # bullet 4 (no len() computing a visible column) - format_table is ANSI-aware but not zero-width-aware
  format_table rows [⚠︎ | ◕]: codepoints=26,26  rendered_cols=25,26   # the VS15 row is one column short
  # bullet 1 (no broken variation selector in every UTF-8 mode) - codepoint truncation severs the VS
  render_stream._one_line('x'*198 + '\u26a0\ufe0e' + 'tail', limit=200): VS15 in input True -> in output False
  ```

  So `status_256` (`term.py:289`, `width > len(status)`) and `format_table` (`term.py:424,428,440`, `len(strip_ansi(...))`) both compute a visible column in CODEPOINTS, and `strip_ansi` is not the missing piece: it already preserves U+FE0E correctly (verified), the defect is that a zero-width code point is then counted as one column. And term.py has NO truncation primitive at all (`'[:'` slice count in `term.py` is 0), so V-04's truncation evidence could not be produced by any existing code path.

  THIS IS NOT THE WIDTH HELPER THE DEFERRED SECTION DECLINES, and the distinction is the whole reason this is a bounded fix. Declined: a wcwidth-style 0/1/2 table resolving East-Asian AMBIGUOUS width, which is what Section 9.4 admits cannot be guaranteed across terminals. Required here: treating a zero-width code point as zero columns, which is not a terminal-policy judgement but a Unicode property (`unicodedata.combining`/`category` in `Mn`/`Cf`) and is deterministic. Section 9.4 explicitly permits this ("An implementation MAY add a shared display-width helper... but MUST NOT create per-renderer width guesses"), so putting both primitives in `term.py` where every later consumer reaches them is the conforming placement; adding them per-consumer in `f9t5hz`/`9zvl2w`/`qdd5jq` is what the section forbids. Do NOT attempt to make `▶` (U+25B6) or `◇` (U+25C7) align across ambiguous-width terminals; F-02 records that as out of reach and Section 9.4 agrees.

  SCOPE LIMIT, so this does not become a repository-wide refactor: this child routes ITS OWN new lifecycle rendering through the two primitives and leaves the existing generic call sites alone. Repairing `status_256`'s and `format_table`'s codepoint padding for non-lifecycle callers is not this child's work, and `render_stream._one_line` belongs to `qdd5jq`; both are recorded in Deferred with carriers.

- [ ] E-05 Add the criterion A16 capability matrix tests covering the normal UTF-8 profile, ASCII mode, colored TTY, plain TTY, piped output, and `TERM=dumb`, plus A13 (`FORCE_COLOR` enables ANSI per existing precedence but does not force Unicode onto an incompatible stream).
  - Depends on: E-02, E-03, E-04
  - Expected outcome: Six named environment profiles asserted, each showing the expected glyph form and ANSI presence. `FORCE_COLOR` does not override ASCII stream capability.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Verified 2026-09-19 and CORRECTED AT REVIEW: `term.py` reads `STATUS_COLOR_256` at four sites (287, 394, 469, 477), of which exactly ONE (`status_256`, 287) is a lifecycle path. See F-04 and the Concern for why the other three are out of scope by R10.3.
- Verified 2026-09-19: `AW_ASCII_ONLY` and `FORCE_ASCII` already exist in `term.py` (`should_unicode`, `term.py:220-237`), so the ASCII half of the capability matrix tests existing behavior.
- Spec Section 9.4 records that NO display-width helper exists in the package, and that is still true (`grep -rn "wcwidth\|display_width\|visible_width" agent_workflows/` matches one COMMENT at `render_stream.py:111` and no symbol). `render_stream.py` solved its ASCII case with a substitution table behind a `use_unicode` flag, and that pattern is reused for ASCII mode. It is NOT sufficient for the UTF-8-mode half of Section 9.4: see F-05.
- Verified 2026-09-19: `strip_ansi` (`term.py:35-37`) already PRESERVES U+FE0E and is already the shared ANSI-aware measurement primitive at six call sites (`pwatch.py:87`, `run_viewer.py:1452,1490`, `term.py:424,428,440`). E-04's width measurement must build on it, not add a second stripping path.
- Verified 2026-09-19: `term.py` contains NO truncation or clipping primitive (`'[:'` slice count is 0), so A15's truncation clause cannot be evidenced by any existing `term.py` code path.
- Verified 2026-09-19 (A13 half-way already holds): `should_unicode` reads only `AW_ASCII_ONLY`, `FORCE_ASCII` and the stream encoding, and never `FORCE_COLOR`, so with `FORCE_COLOR=1` on an `encoding="ascii"` pipe, `should_color` is True while `should_unicode` is False. A13's "does not force Unicode onto an incompatible stream" is therefore a CHARACTERIZATION test of existing behavior, not new work; assert it so a later change cannot break it.
- Verified 2026-09-19: the suite harness for exactly this matrix already exists and MUST be reused rather than reinvented: `tests/test_term.py:15-22` defines `_FakeTTY`/`_FakePipe` and `:38-41` the `_clear()` env helper, with `:26-36` the save/restore `setUp`/`tearDown`. Note `io.StringIO` HAS an `encoding` attribute whose value is `None`, so a stream double needs an explicit `encoding` class attribute to exercise the ASCII-capability rung.
- SUITE BASELINE at review HEAD `a25fe45d`, so an executor can tell a pre-existing failure from one it caused: `8369 passed, 3 skipped, 2 xfailed in 187.72s`. Compare node ids, not just counts.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `- Readiness:` is deliberately absent at authoring (it is `/plan-review`'s output; IPD-M107 refuses an unattested value). This review writes it.

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | Resolution and rendering are fused in `term.py`'s lifecycle path, so there is no seam at which a test can check resolution without also checking ANSI. R10.2 exists to fix exactly this. CORRECTED AT REVIEW: the site is `status_256` ALONE, not three sites; see F-04. | `term.py:285-291` (`Term.status_256`) calls `STATUS_COLOR_256.get(status.lower(), 244)` then `self.color256(...)` on the next line. |
| F-02 | Medium | Two glyphs this spec uses are already MEASURED as East Asian Width ambiguous by `render_stream.py`: `▶` U+25B6 (`executing`) and `◇` U+25C7 (`parked`). So Section 9.4's alignment caveat applies to this spec's own symbols and is not hypothetical. This is the part that is genuinely OUT of reach and is why the Deferred wcwidth entry is correct. | `uonrjg` Section 9.4 prior-art note, citing `render_stream`'s own `east_asian_width` measurement over its ten glyphs, five ambiguous. Re-measured 2026-09-19: `unicodedata.east_asian_width` is `A` for U+25B6, U+25C7, U+FE0E and U+2026, and `N` for U+26A0 and U+21A9. |
| F-03 | Medium | `render_stream.py` computes its padding in CODEPOINTS via `len`, which is the exact failure Section 9.4 forbids, and it documents this as "exact only for glyphs a terminal renders SINGLE-WIDTH". Converting that module (child `qdd5jq`) inherits the problem, so these helpers must not replicate the pattern. | `uonrjg` Section 9.4 prior-art note; `render_stream.py:103-111`, `render_stream.py:214` (`label.ljust(event_prefix_pad(...))`), `render_stream.py:226` (`len(collapsed) > limit`). |
| F-04 | Medium | ADDED AT REVIEW. The Concern and F-01 cited THREE fusion sites (287, 394, 469), but two of those are generic, non-lifecycle roles this spec explicitly excludes, and this plan's own Deferred section says so. Harm if uncorrected: an executor reading the Concern as the work statement would refactor `format_outcome` and `badge`, violating R10.3's "do not mechanically replace every checkmark" and touching a banner whose only real caller passes a command result's status, not an artifact status. Fixed in place: Concern and F-01 now cite `status_256` alone and enumerate why the other three reads are out. | `grep -n STATUS_COLOR_256 agent_workflows/term.py` -> def 117, reads 287, 394, 469, 477. `format_outcome` callers are `renderers.py:89` (command outcome) and `term.py:625` (default `"clean"`); `badge` takes an arbitrary `role_or_code` (`term.py:466-469`); `format_path` reads `"paths"` (`term.py:477`), a key absent from spec `uonrjg`. `uonrjg` R10.3. |
| F-05 | High | ADDED AT REVIEW. E-04 delegated ALL of Section 9.4 to the ASCII substitution table, but that table satisfies only the section's third contract bullet (ASCII-mode alignment) and is inert in UTF-8 mode, where the other three bullets live. All three currently fail by measurement, so E-04 as authored would have been marked complete with A15 unmet and V-04's truncation evidence unproducible (term.py has no truncation primitive to exercise). Fixed in place: E-04 now requires an ANSI-and-zero-width-aware width measurement and a VS-safe truncation, scoped to this child's own rendering, with the wcwidth/ambiguous-width part still declined. | Measured by execution 2026-09-19: `status_256('⚠︎', width=4)` -> 4 codepoints but 3 rendered columns, while `status_256('◕', width=4)` -> 4 and 4; `format_table` rows differ by one rendered column for a VS15 row (`term.py:289`, `term.py:424,428,440`); `render_stream._one_line` drops U+FE0E when clipping at a boundary (`render_stream.py:226`). `strip_ansi` itself PRESERVES U+FE0E, so the defect is zero-width counting, not stripping. `'[:'` slice count in `term.py` is 0. |
| F-06 | Medium | ADDED AT REVIEW. E-03 claimed Section 9.2's legend PLACEMENT obligations ("available in command help", "shown once in a view with 3+ stages") that this child structurally cannot meet: its `Scope-Paths` is `term.py` plus its test, so it touches no argparse help and no view, and it runs BEFORE any consumer conversion so no such view exists yet. Left as written, V-03 would have demanded evidence of help-text placement from a plan that may not edit help text. Fixed in place: E-03 owns the generated legend RENDERER, `7p3tt8` owns placement, and the showing rule is explicitly handed to the converting children with a prohibition on a module-level latch. | Plan `- Scope-Paths:` (this file); `7p3tt8` E-03 ("reachable from command help per Section 9.2") and E-04 (generated-not-hand-maintained drift guard); `uonrjg` Section 9.2. `grep -rn "three or more\|shown once"` across all eight `lifeglyph` children matches THIS FILE ONLY. |
| F-07 | Low | ADDED AT REVIEW. Two Step 0 claims were inherited from the spec's prose rather than measured, and one is materially incomplete: the "no display-width helper exists" claim is true, but the same grep shows `strip_ansi` is already used as an ANSI-aware measurement helper at six sites, which is the half of the primitive that already exists and which E-04 must build on rather than duplicate. Recorded so an executor does not add a second stripping path. | `grep -rn "wcwidth\|display_width\|visible_width" agent_workflows/` -> one comment in `render_stream.py:111` and no symbol. `grep -rn "len(strip_ansi"` -> `pwatch.py:87`, `run_viewer.py:1452,1490`, `term.py:424,428,440`. |

## Proposed changes (ordered, validatable)

1. The three R10.2 helpers with resolution and rendering separated (E-01).
2. The Section 9.1 full-row color discipline (E-02).
3. The Section 9.2 compact form and the generated legend renderer (E-03).
4. The two grapheme-safety primitives (zero-width-aware visible width, VS-safe truncation) plus the ASCII table, with this child's rendering routed through them (E-04).
5. The A16 capability matrix plus A13 (E-05).

## Deferred / out of scope (with reason)

- A TRUE display-width helper (a wcwidth-style 0/1/2 table resolving East Asian AMBIGUOUS width): spec Section 9.4 admits perfect alignment "cannot be guaranteed across every terminal's ambiguous-width policy", so this is declined on the spec's own terms, not postponed. F-02 measures `▶` U+25B6 and `◇` U+25C7 as `A`, and no table can make a terminal's ambiguous-width policy agree with ours. NOTE THE BOUNDARY, since it moved at review: the ZERO-width case (a variation selector counting as 0 columns) is NOT part of this deferral and IS in scope as E-04, because it is a deterministic Unicode property rather than a terminal-policy judgement, and Section 9.4's remaining three contract bullets cannot be met without it (F-05).
  - Carrier-Declined: DECLINED ON THE SPEC'S OWN TERMS. Section 9.4 states the ambiguous-width guarantee is unreachable and requires only the four contract bullets, all four of which E-04 now delivers. Nothing is outstanding and no later plan inherits an obligation.
- Repairing `status_256`'s and `format_table`'s codepoint-based padding for their EXISTING non-lifecycle callers: measured as real (F-05) but out of scope here. This child adds the correct primitives and routes its own lifecycle rendering through them; the generic callers are converted when their views are.
  - Carrier: 9zvl2w
- `render_stream._one_line`'s VS-severing clip (`render_stream.py:226`): a real instance of the same defect in a module this child may not touch (`- Scope-Paths:` excludes it), and `qdd5jq` already declares `render_stream.py` and owns its lifecycle conversion.
  - Carrier: qdd5jq
- Placing the legend in command help and in user documentation, and the legend drift guard: this child ships the generated RENDERER only (F-06).
  - Carrier: 7p3tt8
- Per-consumer snapshot updates: each conversion child owns its own snapshots, because a snapshot belongs with the view that produces it.
  - Carrier: f9t5hz
- Generic `Term` OK/WARN/FAIL outcomes, including `format_outcome` (`term.py:394`), `badge` (`term.py:469`) and `format_path` (`term.py:477`): R10.3 explicitly keeps them valid and outside this spec, and warns against mechanically replacing every checkmark in the repository.
  - Carrier-Declined: EXPLICITLY OUT OF SCOPE by the spec: R10.3 keeps these valid and warns against mechanically replacing every checkmark in the repository. There is no obligation to carry, and creating one would assert work the spec forbids.

## Scope check

- Over-scope: none. Every E-item maps to R10.2, Section 9.1, 9.2, 9.4, or criterion A13/A15/A16. E-04's two primitives are the narrowest change that satisfies Section 9.4's four contract bullets, and Section 9.4 itself requires such a helper be SHARED rather than per-renderer, so placing them in `term.py` is the conforming location rather than added scope.
- Under-scope: CLOSED AT REVIEW. E-04 previously delegated all of Section 9.4 to an ASCII table that satisfies one of its four bullets (F-05), and E-03 previously claimed legend placement this child cannot perform (F-06). Both are now correctly bounded, with the excluded parts carried by named children rather than dropped.
- The consumers are deliberately separate children because each carries its own snapshot surface and can regress independently.

## Required tests / validation

Run the suite BARE: `python3 -m pytest` (no added flags; `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`). Paste the actual summary line and compare against the review baseline `8369 passed, 3 skipped, 2 xfailed` at HEAD `a25fe45d`; a differing count must be explained by node id, not by a count alone.

REUSE THE SHIPPED HARNESS rather than inventing a second stream-double pattern: `tests/test_term.py:15-22` (`_FakeTTY`, `_FakePipe`), `:38-41` (`_clear()`), `:26-36` (env save/restore). For the ASCII-capability rung give the double an explicit `encoding` class attribute, because `io.StringIO.encoding` exists and is `None`, which `should_unicode` treats as "no information" and falls through to True.

Tests must cover:
- **A10** glyph, id6, and status carry the SAME color code and bold flag while type, title and path carry none. Assert on the escape bytes (`repr`), not on stripped text, or the test cannot fail.
- **A13** `FORCE_COLOR` enables ANSI per existing precedence and does NOT force Unicode onto an incompatible stream. This is a CHARACTERIZATION test of shipped behavior (`should_unicode` never reads `FORCE_COLOR`), so it must be written to fail if a later change couples them.
- **A15** variation selectors survive ANSI stripping AND truncation. Truncation must be asserted at the adversarial boundary (immediately after the base character), because a naive codepoint clip passes at every other offset; F-05 records the measured failure this pins.
- **A16** the six capability profiles: normal UTF-8, ASCII mode, colored TTY, plain TTY, piped, `TERM=dumb`.
- Section 9.4 bullet 2, which is NOT one of the lettered criteria and would otherwise go untested: a padded lifecycle column of VS-bearing and non-VS glyphs aligns to the same rendered width in the normal UTF-8 profile.

## Spec / documentation sync

No `.spec.md` edit in this child, so none is declared in `- Scope-Paths:`. The canonical legend's appearance in command help and user documentation is child `7p3tt8`'s item; this child only provides the legend RENDERER.

NO SPEC AMENDMENT IS OWED, checked at review rather than assumed. E-04 adds a shared width primitive, which Section 9.4 already PERMITS in as many words ("An implementation MAY add a shared display-width helper... but MUST NOT create per-renderer width guesses"), so the change is inside the existing contract and needs no amendment. Had E-04 instead declined the UTF-8-mode bullets, THAT would have required amending Section 9.4, which is a reviewed, `approved`, release-gating spec; the cheaper-looking route was the one that carried the spec-edit cost.

## Open questions

### OQ-01: Do the helpers keep the spec's suggested names or adopt existing term.py naming?

- Blocking: no
- Status: resolved
- Owner: none
- Carrier-Declined: PRE-ANSWERED BY THE SPEC, so there is no obligation at all. R10.2 states "Names may differ, but resolution and rendering MUST remain separate and testable", making the constraint structural rather than lexical. This question is recorded only to stop a later reviewer reading the spec's three example names as a literal API requirement; it creates no work.
- Resolution or deferral rationale: RESOLVED AT REVIEW 2026-09-19 from the spec text itself rather than left open, because leaving a question `open` that the controlling document already answers costs a maintainer a decision they do not need to make. R10.2 says in as many words: "Names may differ, but resolution and rendering MUST remain separate and testable." So the constraint is STRUCTURAL, not lexical. RESOLUTION: use the spec's three names (`resolve_lifecycle`, `format_lifecycle_marker`, `style_lifecycle_text`) unless `term.py`'s existing convention gives a clearly better fit, since `term.py` has no competing lifecycle naming to conflict with (its nearest neighbour is `status_256`, which this API supersedes for lifecycle use). Either choice conforms; V-01 pins whatever is chosen by pasting the real signatures. Recorded so a later reviewer does not read the spec's example names as a literal API requirement and file a finding against a conforming implementation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the three helper signatures as `inspect.signature` output. Paste the resolve entry point's raw `repr` and show it contains no `\x1b`, proving it returns ANSI-free data. Paste `grep -n "STATUS_COLOR_256\|_STAGE\|GLYPH" agent_workflows/term.py` proving `term.py` gained no lifecycle stage table of its own and that the helpers import their data from `lifecycle_style`. ALSO paste proof the three EXCLUDED generic reads are untouched: `grep -n STATUS_COLOR_256 agent_workflows/term.py` must still show reads inside `format_outcome`, `badge` and `format_path` (F-04).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste a rendered full row via `repr` so the escapes are visible, showing the SAME `38;5;N` code and the same bold prefix on glyph, id6 and status word, and NO escape at all around type, title or path. Criterion A10. Then paste the NEGATIVE case that proves the API cannot whole-row color: show that the row helper leaves the neutral cells unstyled even when asked to style the row, or paste the signature proving no parameter exists that would color them. An A10 test that only asserts the positive case cannot catch a regression to whole-row coloring.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste a compact `GLYPH id6` render (via `repr`) showing glyph and id6 inside ONE escape pair rather than two adjacent pairs. Paste the legend renderer's full output showing every stage with its glyph, ASCII fallback and word, in Section 5's lifecycle order. Paste proof the legend is GENERATED: show that it iterates `lifecycle_style`'s table (paste the source lines) and that its row count equals the stage table's length computed at runtime, not a literal. Paste `grep` showing `term.py` contains no once-per-process legend latch (F-06).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: FOUR separate pastes, one per Section 9.4 contract bullet, because a single round trip passes while three bullets fail (F-05).
    1. WIDTH: paste the visible-width helper's output for `⚠︎` (U+26A0 U+FE0E), `↩︎` (U+21A9 U+FE0E) and `◕`, showing `1` for all three while `len()` reports `2, 2, 1`. Show the same helper returns the same value for the styled and unstyled forms of one of them, proving it is ANSI-aware.
    2. ALIGNMENT (bullet 2): paste a two-row padded lifecycle column, one row VS-bearing and one not, and show both rows measure the SAME rendered width by the new helper. Contrast with the pre-change behavior measured at review (`status_256('⚠︎', width=4)` -> 3 rendered columns versus `status_256('◕', width=4)` -> 4).
    3. TRUNCATION (bullet 1): truncate a styled `⚠︎` row AT THE ADVERSARIAL BOUNDARY (a limit that lands between U+26A0 and U+FE0E) and show U+FE0E is still present in the resulting code points, as a `[hex(ord(c)) for c in out]` dump. A truncation asserted only at a safe offset proves nothing.
    4. NO BARE `len()` (bullet 4): paste `grep -n` over the lines E-04 adds showing no `len(` computing a visible column on styled or VS-bearing text, and showing the new width helper is the single measurement path (F-07: do NOT add a second `strip_ansi` path).
    Criterion A15 is satisfied by items 1, 3 and 4 together; item 2 is the Section 9.4 bullet no lettered criterion covers.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the BARE `python3 -m pytest` summary line and compare it to the baseline `8369 passed, 3 skipped, 2 xfailed` (HEAD `a25fe45d`); explain any difference by node id. Then paste all SIX capability profiles, each with its asserted output and each showing both the glyph FORM (Unicode grapheme versus the exact Section 5 ASCII fallback) and ANSI presence or absence: normal UTF-8, ASCII mode (`AW_ASCII_ONLY=1`), colored TTY, plain TTY, piped, `TERM=dumb`. Paste the `FORCE_COLOR`-does-not-force-Unicode case as its OWN named case (A13): a stream with `encoding="ascii"` under `FORCE_COLOR=1`, showing ANSI present AND the ASCII fallback used. Paste the test node ids so each profile is a distinct named test rather than one composite assertion.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved bn026f --by-human`). Its `- Item-Dependencies: executed:udgilu, executed:pow5sj` edges are re-checked at dispatch, and both are load-bearing rather than nominal: `udgilu` supplies the stage table these helpers read (E-01 forbids duplicating it into `term.py`, so without that module there is nothing to render), and `pow5sj` supplies the resolved depth tier the marker formatter and text styler select a color from (without it there is no tier to select and the helpers would hardcode the 256 palette, which is the fused design R10.2 exists to end).

OPEN QUESTIONS: OQ-01 is non-blocking and is pre-answered by the spec (R10.2: "Names may differ"); it creates no work and gates nothing. There is no blocking question on this child.

NOTE THE SET CONTEXT, which is not this plan's to resolve and which TOOLING ALREADY ENFORCES. Both of this plan's declared dependencies carry an unresolved blocking finding of their own: `udgilu`'s PR-203 (`integration-deferred` has no spec Section 7.2 row, so criterion A2 is unsatisfiable) and `pow5sj`'s PR-301 (whether `FORCE_COLOR` still defeats `NO_COLOR` at the depth resolver). Verified at review, `aw check` reports this against THIS FILE, twice, as `check.ipd-dependency-findings-blocked` at severity `error`:

```text
dependency `executed:udgilu` resolves but does not satisfy the edge: udgilu: review finding PR-203 is blocker/open and unresolved
dependency `executed:pow5sj` resolves but does not satisfy the edge: pow5sj: review finding PR-301 is blocker/open and unresolved
```

Both diagnostics PRE-DATE this review (measured by re-running `aw check` against the unmodified file) and neither is a defect in this plan: they are the dependency machinery correctly refusing to let a downstream child dispatch on an unsettled upstream contract. So this plan's own readiness is `go-pending-approval`, and approving it does NOT make it runnable until those two rulings land. Do not attempt to clear these by editing this file; the only fixes are in `udgilu` and `pow5sj`.

SCOPE FENCE: the files this plan may write are those declared in `- Scope-Paths:` (`agent_workflows/term.py`, `tests/test_term.py`). An out-of-scope edit is permitted but must then be JUSTIFIED, which `aw ipd finalize` enforces by refusing to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. In particular this child must NOT convert any consumer, must NOT touch `render_stream.py` (its `_one_line` VS-severing clip is `qdd5jq`'s, per Deferred), must NOT edit argparse help or user documentation (the legend's placement is `7p3tt8`'s, per F-06), must NOT refactor `format_outcome`, `badge` or `format_path` (generic roles R10.3 keeps out, per F-04), and must NOT delete `term.py`'s `STATUS_COLOR_256`, which is `qdd5jq`'s work after every consumer moves off it; deleting it here would break live views. DO STOP AND REPORT for one genuinely unsafe condition: if `udgilu` or `pow5sj` landed a stage table or depth resolver whose symbols are ABSENT or whose shape differs from what E-01 reads, report that rather than hand-copying a stage table into `term.py`, which would recreate the duplicate-table defect this whole Set exists to remove.

HONESTY RULE (hard MUST): when reporting tests or measurements, paste the ACTUAL command output. Never claim a suite run, a rendered row, a width measurement, a truncation round trip, or a capability profile you did not run. A `V-*` evidence block must contain real output, not a description of expected output. V-04 in particular demands four separate measured pastes precisely because a plausible-sounding single round trip would have hidden three real failures (F-05).

On completion: append the workflow-history line, set the terminal `Status: executed`, and move this plan to `.aw/records/plans/executed/` via `aw ipd finalize` as a post-gate lifecycle step, never as a checklist item and never as a hand-rolled `git mv`. When a runner owns the turn it performs that finalize itself; a hand-run executor invokes it directly. Commit path-scoped (`git commit -m msg -- <path>`); never `git add -A`; never push.

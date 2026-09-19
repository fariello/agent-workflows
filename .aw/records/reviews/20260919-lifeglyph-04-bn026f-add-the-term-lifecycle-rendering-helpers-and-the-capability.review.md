# Review findings: plan bn026f

- Subject-Id: bn026f
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `a25fe45d`. The plan on disk was byte-identical to the sealed lane input (`diff`
empty) and `git status --porcelain` was clean, so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0, both before and
after the revisions.

THE DESIGN IS SOUND AND ITS PLACE IN THE SET IS RIGHT. R10.2 asks for a rendering boundary over
`udgilu`'s data and `pow5sj`'s tier, this plan builds exactly that, and its two dependency edges are
genuinely load-bearing rather than decorative. Both serious findings are the same KIND of defect and
it is the kind worth naming: the plan UNDERSTATED its own scope in two places, and in each the
understatement was invisible because it read as commendable restraint. A plan that claims too much
gets caught by a scope fence. A plan that claims too little executes cleanly, passes its own
validation, and leaves a release-gating criterion unmet with every checkbox ticked.

**1. E-04 delegated all of Section 9.4 to a mechanism that satisfies one quarter of it (PR-403).**
The plan's reasoning was quoted from the spec and sounded airtight: Section 9.4 permits a width helper
but records that `render_stream`'s ASCII-table-behind-a-flag pattern satisfies the section WITHOUT one,
so choose the cheaper proven route. I checked that against Section 9.4's four contract bullets and the
claim does not survive. The ASCII table delivers bullet 3, "guaranteed single-byte alignment in ASCII
mode". Bullets 1, 2 and 4 are UTF-8-MODE obligations, and an ASCII substitution table is inert in UTF-8
mode by construction, because the substitution never happens there. I measured all three by execution:

```text
# bullet 2 - stable alignment in the normal UTF-8 profile
Term(color=False).status_256('\u26a0\ufe0e', width=4) -> '⚠︎  '   codepoints=4  rendered_cols=3
Term(color=False).status_256('\u25d5',       width=4) -> '◕   '  codepoints=4  rendered_cols=4
# bullet 4 - no len() computing a visible column
format_table rows [⚠︎ | ◕]: codepoints=26,26  rendered_cols=25,26
# bullet 1 - no broken variation selector in any UTF-8 mode
render_stream._one_line('x'*198 + '\u26a0\ufe0e' + 'tail', limit=200): VS15 in -> True, out -> False
```

So `status_256` pads by codepoint (`term.py:289`) and `format_table` measures with
`len(strip_ansi(...))` (`term.py:424,428,440`), which is ANSI-aware but not zero-width-aware. `strip_ansi`
is not the missing piece; it already preserves U+FE0E correctly. And `term.py` has NO truncation
primitive at all (`'[:'` count is 0), so V-04's truncation evidence could not have been produced by any
existing code path, which is the tell that the item was under-specified rather than merely optimistic.

THE BOUNDARY THAT MAKES THE FIX BOUNDED, and it is the substantive judgement in this review: the plan
was right to decline a wcwidth-style table and wrong to think that settled the section. AMBIGUOUS East
Asian width is a terminal-policy disagreement Section 9.4 explicitly admits is unreachable ("perfect
alignment cannot be guaranteed"), and F-02's own measurement of `▶` and `◇` as `A` is why. ZERO width is
a deterministic Unicode property (`unicodedata.combining`, category `Mn`/`Cf`) with one right answer.
E-04 now requires the second and still declines the first. Note the cost asymmetry that clinches it:
Section 9.4 PERMITS a shared width helper in as many words, so the fix needs no spec amendment, whereas
declining the UTF-8 bullets would have required amending an `approved`, `Blocks-Release: next` spec. The
route that looked cheaper carried the spec-edit cost.

**2. E-03 claimed legend obligations this child cannot discharge, and it was the only file in the Set
that mentioned them (PR-402).** Section 9.2 requires a legend "available in the command help" and
"SHOWN ONCE in a view that contains three or more semantic stages". This child's `- Scope-Paths:` is
`term.py` and `tests/test_term.py`, so it touches no argparse help and no view, and it is ordered
BEFORE every consumer conversion, so no converted view exists yet to show a legend in. `7p3tt8` E-03/E-04
own placement and the drift guard. What made this worth a HIGH rather than a tidy-up: `grep -rn "three
or more\|shown once"` across all eight `lifeglyph` children matches THIS FILE ONLY, so this was the
single point at which the showing rule could vanish between the two children that both half-own it.
E-03 now owns the generated RENDERER, hands the showing rule forward explicitly, and forbids a
once-per-process latch in `term.py` (which would make output depend on invocation order and be
untestable in a shared-process suite).

**3. The plan led with a factual claim about the code that was two-thirds wrong (PR-401).** The Concern
and F-01 both said resolution and rendering are fused at THREE sites, citing `term.py:287`, `394` and
`469`. Only 287 (`status_256`) is a lifecycle path. 394 is `format_outcome`, a generic command-outcome
banner whose only callers pass a command result's status (`renderers.py:89`) or the literal default
`"clean"` (`term.py:625`); 469 is `badge`, resolving an arbitrary caller-supplied `role_or_code`; and
477 (uncited) is `format_path` reading the non-lifecycle `"paths"` key, absent from the spec entirely.
R10.3 keeps all three explicitly OUT and warns against mechanically replacing every checkmark, and this
plan's own Deferred section already excluded them, so the Concern contradicted the Deferred section.
An executor reading the Concern as the work statement would have refactored two generic surfaces the
spec protects. Fixed by citing `status_256` alone and enumerating why the rest are out.

WHAT I DID NOT FLAG, since a reviewer's silence should be legible. The dependency edges are correct and
I verified both are load-bearing. The right-sizing is genuinely right: five E-items, each one concern,
and E-04 remains one concern after growing because both primitives serve the single obligation "a
lifecycle symbol is an opaque grapheme". The Deferred section's use of `Carrier-Declined` for the
wcwidth entry is correct on the spec's own terms, not an evasion. And A13 turns out to be a
CHARACTERIZATION test rather than new work: `should_unicode` never reads `FORCE_COLOR`
(`term.py:220-237`), so with `FORCE_COLOR=1` on an `encoding="ascii"` stream I measured `should_color`
True and `should_unicode` False already. That is worth asserting precisely so a later change cannot
couple them, and the plan now says so.

Suite baseline at review HEAD, run bare per AGENTS.md: `8369 passed, 3 skipped, 2 xfailed in 187.72s`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | MEDIUM | IN-SCOPE | A. correctness; G. executability | `grep -n STATUS_COLOR_256 agent_workflows/term.py` -> def 117, reads 287, 394, 469, 477; `renderers.py:89` and `term.py:625` are `format_outcome`'s only callers; `term.py:466-469` (`badge` takes arbitrary `role_or_code`); `term.py:477` (`"paths"`); `uonrjg` R10.3 | The Concern and F-01 cited three fusion sites, but only `status_256` (287) is a lifecycle path. 394/469/477 are generic command-outcome and formatting roles R10.3 explicitly excludes and the plan's own Deferred section already excluded, so the Concern contradicted the Deferred section and would have directed an executor to refactor surfaces the spec protects | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Concern, F-01 and the Step 0 note now cite `status_256` alone and enumerate why the other three reads are out; new F-04 records the correction; the scope fence names them as forbidden; V-01 demands a grep proving they are untouched |
| PR-402 | HIGH | IN-SCOPE | C. architecture; G. executability; scope boundary | Plan `- Scope-Paths:` (`term.py`, `tests/test_term.py`); `7p3tt8` E-03/E-04; `uonrjg` Section 9.2; `grep -rn "three or more\|shown once"` across all eight `lifeglyph` children matches this file only | E-03 claimed Section 9.2's legend PLACEMENT obligations (command help, shown-once-per-view) that this child structurally cannot meet: it touches no help text and no view, and runs before any consumer view exists. V-03 would have demanded help-placement evidence from a plan that may not edit help text, and this file was the ONLY place in the Set naming the showing rule, so it was the single point at which that rule could be lost between the two children | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now owns the GENERATED legend renderer only, records the `7p3tt8` boundary with evidence, hands the showing rule to the converting children, and forbids a once-per-process latch; V-03 demands proof the legend is generated from the shared table and that no latch exists; new F-06 records it; Deferred gains a `Carrier: 7p3tt8` entry |
| PR-403 | HIGH | UNDER-SCOPE | A. correctness; D. anti-regression; E. verification | Measured by execution 2026-09-19: `status_256('⚠︎', width=4)` -> 4 codepoints, 3 rendered columns vs `status_256('◕', width=4)` -> 4 and 4 (`term.py:289`); `format_table` VS15 row one column short (`term.py:424,428,440`); `render_stream._one_line` drops U+FE0E at a clip boundary (`render_stream.py:226`); `'[:'` count in `term.py` is 0; `uonrjg` Section 9.4 four contract bullets | E-04 delegated ALL of Section 9.4 to the ASCII substitution table, which satisfies only bullet 3 and is inert in UTF-8 mode where bullets 1, 2 and 4 live. All three fail today by measurement, so E-04 as authored would have been ticked complete with A15 unmet, and V-04's truncation evidence was unproducible because no truncation primitive exists to exercise | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 now requires two primitives (zero-width-aware ANSI-stripping width measurement, VS-safe truncation) with the measured failures pasted inline, scoped to this child's own rendering; the wcwidth/AMBIGUOUS-width part stays declined with the zero-width-versus-ambiguous boundary stated; new F-05 records it; Deferred gains carriers for the generic call sites (`9zvl2w`) and `render_stream._one_line` (`qdd5jq`); Spec sync records why no amendment is owed |
| PR-404 | MEDIUM | UNDER-SCOPE | E. testing and verification | V-04 original text ("Paste a round trip proving variation selectors survive"); measured: a naive codepoint clip preserves U+FE0E at every offset EXCEPT immediately after the base character | V-04 demanded one composite round trip, which passes against the very defect it is meant to catch: truncating at any offset other than the base/VS boundary leaves the selector intact, so the evidence would have looked convincing while bullets 1, 2 and 4 stayed broken. Section 9.4 bullet 2 (UTF-8 alignment) was also demanded by no criterion and no V-item | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-04 restructured into four separate pastes, one per Section 9.4 bullet, with truncation asserted AT THE ADVERSARIAL BOUNDARY and a contrast against the pre-change measurement; Required tests adds bullet 2 explicitly as the obligation no lettered criterion covers |
| PR-405 | MEDIUM | UNDER-SCOPE | E. testing; D. anti-regression | `should_unicode` reads only `AW_ASCII_ONLY`/`FORCE_ASCII`/encoding (`term.py:220-237`), never `FORCE_COLOR`; measured `FORCE_COLOR=1` + `encoding="ascii"` -> `should_color` True, `should_unicode` False; `tests/test_term.py:15-22,26-41` harness; `io.StringIO().encoding` is `None` | A13, A10 and A16 were named without stating what would make each able to FAIL. A13 is a characterization test of already-correct behavior (so it must be written to break if a later change couples the two decisions, not merely to pass); A10 asserted on stripped text cannot see a color code; and an executor would have reinvented the stream doubles that already ship, missing that `io.StringIO` HAS an `encoding` attribute of `None`, which `should_unicode` treats as no-information | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Required tests now states the failure mode for each criterion, cites the shipped harness by path and line, records the `encoding=None` trap, and adds the negative whole-row-coloring case to V-02; Step 0 records the measured A13 behavior |
| PR-406 | LOW | UNDER-SCOPE | E. verification; G. executability | AGENTS.md suite contract; sibling reviews of `udgilu`/`pow5sj` record baselines; `aw ipd lint` IPD-M107 | No suite baseline was recorded, so an executor could not distinguish a pre-existing failure from one it caused, and the plan gave no guard against the `-n0` / double-`-q` / `-p no:randomly` flag additions AGENTS.md forbids. OQ-01 sat `open` while the spec text already answered it, costing a maintainer a decision they do not need to make | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline `8369 passed, 3 skipped, 2 xfailed` at `a25fe45d` recorded with a compare-node-ids rule; the bare-run prohibition restated; OQ-01 resolved from R10.2 with the resolution written in and V-01 pinning whichever names are chosen |
| PR-407 | LOW | UNDER-SCOPE | G. executability; execution contract | Plan gate (original two-paragraph form) | The gate carried no scope fence, no paste-the-actual-output honesty rule, no open-questions disposition, and instructed a `git mv` to `executed/`, which the workflow names as a finding | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now carries the fence (naming `render_stream.py`, help text, the three generic roles, and the `STATUS_COLOR_256` deletion as forbidden), the honesty MUST tied to V-04's four pastes, both dependency edges' load-bearing reasons, one legitimate stop condition, the Set-context note that both dependencies carry unresolved blocking questions, and conditional `aw ipd finalize` ownership with no hand-rolled `git mv` |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Section 9.4 permits a width helper but records the ASCII-table route as satisfying the section without one. Is E-04's ASCII-only approach conforming, or does it need a width primitive? | IT NEEDS ONE, narrowly: a ZERO-width-aware measurement and a VS-safe truncation, scoped to this child's own rendering. The AMBIGUOUS-width (wcwidth 0/1/2) part stays declined. Fixed in place rather than escalated. | (a) Accept the plan as authored: rejected by measurement, since three of Section 9.4's four contract bullets fail today and are UTF-8-mode obligations an ASCII substitution table cannot reach. (b) Require a full wcwidth table: rejected, Section 9.4 itself admits ambiguous-width alignment is unguaranteeable and F-02 measures this spec's own `▶`/`◇` as `A`, so it would be scope with no achievable acceptance test. (c) Escalate to the maintainer as blocking: rejected, the spec PERMITS a shared width helper in as many words, so no contract question is open and nothing user-visible or irreversible turns on it; escalating would stall a plan on a question the spec answers. (d) Defer the primitives to the consumer children: rejected as the worst option, since Section 9.4 forbids per-renderer width guesses and three consumers would each grow their own. | `uonrjg` Section 9.4 four contract bullets and "An implementation MAY add a shared display-width helper... but MUST NOT create per-renderer width guesses"; measured `status_256('⚠︎', width=4)` -> 3 rendered columns vs `◕` -> 4; `format_table` VS15 row one column short (`term.py:424,428,440`); `render_stream._one_line` drops U+FE0E (`render_stream.py:226`); `'[:'` count in `term.py` is 0; `unicodedata.east_asian_width` `A` for U+25B6/U+25C7 versus `combining`/`Mn` for U+FE0E. | yes |
| D-2 | E-03 claimed Section 9.2's legend placement obligations that `7p3tt8` also claims. Split them, or leave the overlap? | SPLIT: this child owns the generated RENDERER, `7p3tt8` owns help placement and documentation, and the shown-once rule is handed explicitly to each converting child with a prohibition on a module-level latch. | (a) Leave the overlap: rejected, V-03 would demand help-text evidence from a plan whose Scope-Paths forbids editing help text, so the item could only be satisfied by an out-of-scope edit or by weakening the evidence. (b) Move the whole legend to `7p3tt8`: rejected, `7p3tt8` E-04's drift guard requires the legend be GENERATED from the shared module, and the generator belongs at the rendering boundary this child owns; parking it downstream would have `7p3tt8` retrofitting a hand-written literal. (c) Implement the shown-once rule here with a latch: rejected, a once-per-process latch in `term.py` makes output depend on invocation order and is untestable in a shared-process suite. | `uonrjg` Section 9.2; plan `- Scope-Paths:`; `7p3tt8` E-03 ("reachable from command help per Section 9.2") and E-04 (generated-not-hand-maintained drift guard); `grep -rn "three or more\|shown once"` across all eight `lifeglyph` children matches this file only. | yes |
| D-3 | OQ-01 asks whether the helpers keep the spec's three suggested names. Leave it open for the maintainer, or resolve it? | RESOLVE from the spec text, non-blocking: use the spec's three names unless `term.py` convention fits better, since either conforms. | (a) Leave `open`: rejected, R10.2 answers it verbatim ("Names may differ, but resolution and rendering MUST remain separate and testable"), and an open question the controlling document already answers spends a maintainer's attention for nothing while reading as an unresolved risk. (b) Mandate the spec's names exactly: rejected, it would over-constrain an internal naming choice the spec deliberately left free and could force a name that clashes with local convention. | `uonrjg` R10.2; `term.py` has no competing lifecycle naming (nearest neighbour `status_256`, which this API supersedes for lifecycle use); V-01 pins the chosen signatures with pasted evidence. | yes |
| D-4 | Both declared dependencies (`udgilu`, `pow5sj`) carry unresolved `Blocking: yes` questions. Does that make THIS plan no-go? | NO. Readiness is `go-pending-approval` on this plan's own merits; the dependency edges are recorded in the gate as the mechanism that defers dispatch. | (a) Mark this plan `no-go` too: rejected, readiness reports whether THIS plan passed review, and propagating a sibling's open question would conflate the plan's quality with the Set's schedule and hide that this file needs no further authoring work. (b) Say nothing about the siblings: rejected as misleading, since a reader seeing `go-pending-approval` could reasonably think approving it makes it runnable. | Workflow readiness definitions (`NO-GO` is for a genuine not-ready condition of the reviewed plan: an open question in IT, or an unfixed BLOCKER/HIGH in IT); `udgilu` and `pow5sj` front matter (`Readiness: no-go`, each with OQ-02 `Blocking: yes`); this plan's `- Item-Dependencies:` re-checked at dispatch. | yes |

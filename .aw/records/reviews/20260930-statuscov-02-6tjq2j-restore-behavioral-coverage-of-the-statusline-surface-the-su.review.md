# Review findings: plan 6tjq2j

- Subject-Id: 6tjq2j
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-301 (HIGH, fixed), PR-302 (HIGH, fixed), PR-303 (HIGH, fixed), PR-304 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `3ca69a863`. The plan file was committed and the tree was
clean (`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic
review; `--phase review-finalize` reports `conforming` after revision. This plan's own first `- Kind:`
bullet reads `child`, so the `IPD-S407` orchestrator child-row check does not apply.

THE PREMISE IS CORRECT AND I CONFIRMED IT SYMBOL BY SYMBOL. A per-symbol census over `tests/` returns
ZERO references for 16 of the 19 public statusline symbols the plan lists, with only `format_progress_bar`
(2 files), `StreamTracker` (2) and `format_duration` (1) referenced at all, and there is no
`tests/test_render_stream.py` and no statusline test module of any kind. `git show --stat 19313eed`
shows `tests/test_render_stream.py | 2706 -------------` inside a commit of 318 files and 219,063
deletions titled "test: trim test suite from 9,136 to under 2,000 tests", and the pre-trim blob holds 50
`def test_` functions across the nine classes named, including the three statusline-specific ones. F-03's
byte-pin-versus-property distinction is verbatim in that blob: the user-example test's own docstring says
it "pins four WHOLE box lines byte-for-byte", and the exact-layout test's says it asserts "the SEGMENTED
structure ... which is a structural decomposition rather than a data row". Both traps in F-04 reproduce
exactly: free-text activity returns `('', 0)` while `"abandoned"` returns a 10-column cell against a
20-member `ALL_STAGES`, and `"recovering"` returns width 10 against `len()` 11; one fixed `now_ts` renders
`22:13:20`, `14:13:20` and `03:43:20` under UTC, America/Los_Angeles and Asia/Kolkata at a CONSTANT width.
I also re-drove the formatter boundary tables, all seven action-derivation shapes including precedence, the
full `Statusline` class surface (non-TTY silence writing `''` and `'x\n'`; first redraw with no cursor-up
and second with `\x1b[3A`; `update_item` preserving on empty/None and replacing on real values; all three
watchdog branches returning `None`/`42.0`/`None`; module-level pause/resume a clean no-op), and F-07's
ASCII residue (clean only at `current_idx=0`, U+2588 at states 1 through 10). All of it holds.

SO THIS IS A WELL-EVIDENCED PLAN WITH A GENUINE HOLE TO CLOSE, and three of its four findings are the
same failure mode: an assertion it mandates cannot pass on the tree it claims to be green against.

PR-301 IS THE ONE THAT WOULD HAVE SHIPPED A RED MODULE. E-02 mandated a zero-width-space `setid` in its
hostile-input list AND mandated that every hostile case assert "the four-line count and the single visible
width". Those two cannot both hold: measured at review, `setid="a\u200bb"` returns per-line visible widths
`127, 126, 127, 127`, because the column is computed with bare `len()` while `term.visible_width("\u200b")`
is 0. This directly contradicts the plan's own F-05 claim that every prescribed property was measured green,
and its whole landable-characterization premise. What makes it unambiguous rather than a judgement call is
that approved plan `it6tpj` OWNS this exact defect and its own guard is explicitly required to FAIL pre-fix
"for every zero-width case in both styling modes". So the plan had, in one E-item, written the sibling's
failing assertion into a module whose stated contract is to be green today. It is the same shape as F-07,
which the plan handled correctly for the ASCII case; it simply missed that the zero-width case is the
identical situation. Fixed by removing the case from the mandatory list, permitting it only as tuple-length
characterization exactly as the newline case is handled, and recording both in V-02.

PR-302 is the same defect reached from the other direction, and it matters because fixing E-02 alone would
not have saved the module. E-01 sweeps `setid` and `id6` "across present, absent and long" and asserts
rectangularity over the sweep; nothing stopped an executor from putting a zero-width or newline value into
that sweep, which would make E-01 red for the same reason. I verified a zero-width-free sweep satisfies all
four invariants, at scale: 31,104 renders over the product of every varied field in both styling modes AND
both unicode modes gave a four-line tuple every time, `_strip_ansi(styled) == plain` with ZERO mismatches,
exactly one distinct visible width per render, and byte-identical repeat renders. The sweep is now fenced.

PR-303 is the stale baseline, and it is worse here than in a normal plan precisely BECAUSE this plan sets a
deliberately sharper bar. F-08 told the executor to expect `1 failed, 3457 passed` and to treat
`test_release_exempt_setter_roundtrip_and_parity` as pre-existing. That test now PASSES and the suite is
fully green at `3589 passed, 2 skipped`. Since this plan adds ONLY a test file, a failure in that node after
the change could only have been caused by this module's own global or thread residue, which is exactly what
V-05 exists to detect, and the original wording granted standing permission to wave it through. Corrected in
all four places to zero failures compared by node id against a freshly re-derived baseline.

PR-304: E-03 instructed that "an alias maps to the same label as its canonical spelling (`plan` and `ipd`
both to `IPD`)" under a bullet covering "both label formatters". Measured, that alias exists only in
`ARTIFACT_DISPLAY_MAP`; `ACTION_DISPLAY_MAP` has no `plan` key and `format_action_label("plan")` returns the
fallback `'Plan'`. An executor reading the instruction literally would write a failing assertion. Fixed by
naming each map's actual alias pairs and forbidding a cross-map alias assertion, which the plan's own
derive-from-the-maps rule already gives for free.

WHAT I DID NOT WEAKEN. The plan's restraint is its best feature and I left all of it: the refusal to restore
the byte-pins, the refusal to assert ASCII purity (F-07's reasoning is exactly right and is the model the two
new findings are fixed to match), the visible-column rather than code-point truncation bound (which I verified
holds at 7 both ways today and survives `it6tpj`), OQ-01's honest characterization-not-judgement stance on
`format_compact_tokens(999_999) == '1000k'` (verified), the timezone discipline, the mutation-in-memory
requirement, and the thread/global residue proof, which is the most valuable single requirement in the plan
given that the suite runs randomized and parallel. I also left the deferral set intact: all five rows are
correctly carried or correctly declined, and `render_run_summary_table` really is already covered by
`tests/test_run_summary_visible_width.py`.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | IN-SCOPE | D. Anti-regression / E. Testing (a mandated assertion that cannot pass on the tree the plan claims to be green against) | Measured: `format_statusline_lines(..., setid="a\u200bb")` returns visible widths `127, 126, 127, 127`; `term.visible_width("\u200b")` is 0 while the column uses bare `len()`. `it6tpj` is `- Status: approved`, owns `agent_workflows/render_stream.py`, and requires its own module to FAIL pre-fix "for every zero-width case in both styling modes" | **E-02 mandated a zero-width-space `setid` AND mandated every hostile case assert a single visible width; those cannot both hold today, so the module would have been RED on an unmodified tree.** That contradicts the plan's own F-05 claim and its landable-characterization premise. It is the identical situation to F-07's ASCII case, which the plan handled correctly, so the omission is an inconsistency rather than a disagreement | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | ZWSP removed from E-02's mandatory list; permitted only as tuple-length-plus-no-raise characterization exactly as the newline case is; E-02's property rule now names both documented exceptions with the reason; V-02 requires stating which route was taken and fails an executor who asserts rectangularity for it or edits production code to satisfy one. New F-10 carries the measurement and the `it6tpj` ownership |
| PR-302 | HIGH | IN-SCOPE | D. Anti-regression (the same contradiction reachable through E-01, so fixing E-02 alone would not save the module) | E-01 sweeps `setid`/`id6` "across present, absent and long" and asserts rectangularity; nothing excluded a zero-width or newline value. A zero-width-free sweep of 31,104 renders gave one distinct width every time, zero strip mismatches, four lines always, and byte-identical repeats | **The E-01 sweep could independently admit the PR-301 input and go red for the same reason,** so the two E-items had to be fenced together; an executor fixing only the explicit hostile case would still be free to sweep a zero-width setid | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now requires every swept `setid`/`id6` value to be free of zero-width and newline code points, with the reason and the sibling ownership stated, and records the 31,104-render verification; V-01 requires stating how the sweep's value list was checked. F-09's "second, weaker interaction" sentence corrected, since `it6tpj` MAKES the property true rather than making it more thoroughly true |
| PR-303 | HIGH | IN-SCOPE | E. Testing (a stale live baseline used as a bar, granting permission to ignore the one failure this module could cause) | Authoring F-08: `1 failed, 3457 passed` at `c2b3a3c1f` naming `test_release_exempt_setter_roundtrip_and_parity`. Review HEAD `3ca69a863`: `3589 passed, 2 skipped, 3 warnings`; that test alone reports `1 passed` | **The named "pre-existing" failure no longer occurs, and because this plan adds only a test file, a failure in that node after the change could ONLY come from this module's global or thread residue, which V-05 exists to catch.** The plan's deliberately sharper bar therefore pointed the wrong way: it licensed tolerating the single most diagnostic failure the change could produce | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | All four sites (F-08 header, validation section, V-05, post-gate lifecycle) corrected to ZERO failures compared by node id against a freshly re-derived baseline; the authoring figure retained as labelled historical context. New F-11 records both measurements and states why the error was dangerous here specifically |
| PR-304 | MEDIUM | IN-SCOPE | A. Correctness (a prescribed assertion that is false as written) | Measured: `ARTIFACT_DISPLAY_MAP` contains `'ipd': 'IPD'` and `'plan': 'IPD'`; `ACTION_DISPLAY_MAP` has no `plan` key and `format_action_label("plan")` returns `'Plan'`. The action map's alias pairs are `execute`/`exec`, `graduate`/`graduat`, `validate`/`validat`, `orchestrate`/`orchest` | **E-03 gave `plan` and `ipd` both yielding `IPD` as the alias example under a bullet covering BOTH label formatters, which is false for the action formatter,** so an executor following it literally writes a failing assertion in a module required to be green | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now states the alias belongs to the artifact map only, gives both maps' actual alias pairs, explains that deriving cases FROM the maps yields them for free, and forbids a hand-written cross-map alias assertion; V-03 requires confirming no assertion claims `format_action_label("plan")` yields `IPD` |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-301: the zero-width case cannot satisfy the rectangularity assertion today. Drop the case, keep it as characterization, or let the module be red until `it6tpj` lands? | Keep it as CHARACTERIZATION (tuple length plus no-raise), with rectangularity explicitly forbidden for it | (a) Drop the zero-width input entirely; (b) keep the rectangularity assertion and accept a red module until `it6tpj` lands; (c) declare `render_stream.py` in scope and fix the width computation here | Option (b) destroys the plan's central property, which is that it changes no production code and is green on an unmodified tree, and it would also couple a `followup` characterization module to a release-gated `bug` fix, the exact coupling F-07 correctly refuses for the ASCII case. Option (c) is a scope violation the gate forbids in terms ("ANY production edit is out of scope, without exception") and would collide with an approved plan already editing that file. Option (a) loses real information: the renderer's behavior on a zero-width input is worth recording, and recording it as characterization is what makes the later tightening visible when `it6tpj` lands. The plan already established this exact pattern for the newline case, so the fix follows its own precedent rather than inventing one | yes |
| D-2 | PR-302: how should the E-01 sweep be prevented from admitting the same input? | Fence the sweep's `setid`/`id6` values explicitly and require V-01 to state how the list was checked | (a) Rely on E-02's fix alone, since that is where the ZWSP case was named; (b) weaken E-01's rectangularity property to "at most two distinct widths" so zero-width inputs pass | Option (a) leaves the hazard live: E-01's instruction is "vary across present, absent and long", and a conscientious executor testing robustness would reasonably reach for an exotic identifier, landing on the same red assertion from a direction E-02's fix does not cover. Option (b) is the forbidden move, hollowing out an assertion to make it pass everywhere, which `GUIDING_PRINCIPLES` P16's last bullet names and which this plan's own Step 0 bullet quotes with `DECISIONS.md` D78 as precedent; it would also silently accept the very defect `it6tpj` exists to fix. Fencing the input keeps the assertion at full strength and localizes the exception to one documented case | yes |
| D-3 | PR-303: F-08's named failure now passes. Update the figure, or remove the bar? | Remove the BAR; keep both figures as labelled context and require zero failures by node id | (a) Replace `1 failed, 3457 passed` with `3589 passed` and keep a total-based comparison; (b) delete F-08 | Option (a) restates a live population as a fixed fact, and this plan is exposed to that drift for longer than most: it is `followup` priority `medium` with no release gate, so it may sit in `pending/` through many merges. Option (b) discards the genuinely useful inference that the tree was green at both points, which is what licenses "any new failure is this module's fault", and that inference is sharper here than anywhere else because the scope is one test file. The deciding factor is the DIRECTION of the error: a stale "tolerate this one failure" instruction does not merely mislead, it specifically excuses the residue failure this module is most likely to cause | yes |
| D-4 | PR-304: the alias instruction is wrong for one of the two formatters. Correct the example, or delete the alias requirement? | Correct it per map, and point at the derive-from-the-maps rule that produces the right pairs automatically | (a) Delete the alias bullet as redundant with the full-map coverage; (b) keep one generic "an alias maps to its canonical label" sentence with no example | Option (a) is defensible, since deriving every key from each map already covers each alias, and I rejected it narrowly: the alias is the case a reader is most likely to hand-write as a readable spot check, so naming the real pairs is what prevents the wrong one being written back later. Option (b) is what produced the defect: a generic instruction with a wrong parenthetical example is worse than either a correct example or none, because the example is what gets copied. Listing both maps' actual pairs costs two clauses and makes the instruction self-checking against the code | yes |

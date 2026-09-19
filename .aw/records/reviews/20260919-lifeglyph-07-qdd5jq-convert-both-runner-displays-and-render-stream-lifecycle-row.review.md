# Review findings: plan qdd5jq

- Subject-Id: qdd5jq
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `67ac3495`. The plan on disk was byte-identical to the sealed lane input (`diff`
empty) and `git status --porcelain` was clean, so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0, before and after
the revisions.

THE DIAGNOSIS IS RIGHT AND F-01 IS THE BEST FINDING IN THIS SET. I verified it: `_STATUS_COLOR` maps
`executed`, `reviewed`, `approved` AND `substantially-complete` all to `green`, so the live runner really
does collapse readiness into completion, which is the single distinction Section 5 was written to
protect. The re-export chain reaching both drivers is real too. This child is correctly placed last and
correctly scoped to the largest surface.

The findings are of two kinds: one item that would have BROKEN WORKING FEATURES, and several places
where the plan's own measurement stopped one level short of the code.

**1. E-04 would have deleted three working, in-spec features, and the parent had already said so
(PR-704, BLOCKER).** E-04 read "Delete `term.py`'s `STATUS_COLOR_256`". Measured, that symbol has four
readers and only ONE is lifecycle:

```text
term.py:287  status_256      LIFECYCLE
term.py:394  format_outcome  GENERIC  -> command-level OK/WARN/FAIL banner
term.py:469  badge           GENERIC  -> arbitrary caller-supplied role_or_code
term.py:477  format_path     GENERIC  -> the "paths" role (33)
```

I confirmed all three generic paths resolve through it by execution: `format_outcome("ok","done")` ->
`\x1b[1;38;5;46m✓ OK\x1b[0m  done`, `badge("RULE","error")` -> `[\x1b[1;38;5;196mRULE\x1b[0m]`,
`format_path(".aw/x")` -> `\x1b[38;5;33m.aw/x\x1b[0m`. R10.3 keeps exactly these, and this plan's OWN
Deferred section already excluded them, so E-04 contradicted its own plan. Parent `2xz59a` states the
requirement verbatim and names this child: E-04 "must SPLIT this table, retaining the generic roles under
a non-lifecycle name... A17 is satisfied when no second LIFECYCLE table remains, not when the string
`STATUS_COLOR_256` is absent." I classified all 56 keys against the spec's Section 6/7 mapping rows and
wrote the 32/24 split into the item so the executor does not re-derive it. Two keys needed judgement:
`ready` is a spec STAGE name and no tree's native status, so as a `term.py` key it is generic;
`quarantined` is a condition input whose rendering `9zvl2w` owns. I also noted the parent's own "22
generic" count is not reproducible, being substring-derived.

**2. Removing the table breaks a public method the plan never mentions (PR-705).** The plan named one
reader in `render_stream.py`. There are two: `Palette.status()` at `:88` does `_STATUS_COLOR.get(status)`,
is called at `:2269`, and `Palette` is re-exported (`oc_runipd.py:106`, `__all__` `:449`) and instantiated
in the drivers at `:1324`, `:2018`, `:2057`. So this is a public surface, and the failure mode is an
import or call error at execution rather than a reviewable mismatch.

**3. An obligation this Set explicitly assigned to this plan was uncarried (PR-706).** My `bn026f` review
deferred `render_stream._one_line`'s variation-selector-severing clip with `Carrier: qdd5jq`, because
`bn026f` may not touch this file. `grep -c _one_line` on this plan returned 0. That is exactly the
carrier mechanism failing in the direction it is meant to prevent: criterion A15 would have had no owner
for this module.

**4. The F-01 collapse survives the conversion at one site (folded into E-02).** At
`runner_shared.py:14047-14050` the run-finish line computes `glyph = "✓" if reached_success else "●"` and
`glyph_color = "green" if reached_success else _STATUS_COLOR.get(...)`. Converting only the table lookup
leaves a literal `green` and a literal glyph pair on the success path, in the one line printed at the end
of every run. E-02's original wording covered the lookup only.

**5. E-03 was not implementable as worded (PR-707).** It asked for five action-aware activities. Measured,
`runner_shared.INTEGRATION_ACTION_KINDS` is exactly `('execute', 'review')`. The other three activities do
exist, but on different fields: `verification_status` (`:11394`), `integration_signal` (`:1466`), and the
retry/correction state. An agent reading only `action` would emit generic `active` for three of five and
silently fail A3, or would add action kinds, which Section 0.5 bounds out as a vocabulary change. The item
now names the field per activity and REQUIRES an honest partial to be reported, since Section 7.1 permits
generic `active` when a subtype is genuinely unavailable.

**6. The A17 guard was the wrong instrument (PR-708).** V-04's `grep STATUS_COLOR_256` false-passes,
because the retained generic table could be renamed while still mapping a lifecycle status, and
false-fails, because `attention.py` defines the same symbol and its removal belongs to sibling `f9t5hz`.
A17's text is a property ("No second lifecycle color or glyph table remains"), so it must be asserted by
content. Relatedly, E-04 breaks `tests/test_term_components.py::PaletteSingleSourceTests` three ways at
once and that file was undeclared (PR-709): it asserts `palette["approved"] == 46` (spec: 45),
`palette["active"] == 39` (spec: 220), and that the only `COLOR` dict in `term.py` is exactly
`["STATUS_COLOR_256"]`, which fails under BOTH deletion and split. It passes today (16 passed), so it is a
real regression, and its docstring encodes the premise this Set replaces, so it should be rewritten rather
than deleted.

WHAT I RESOLVED RATHER THAN ASKING. OQ-01 asked whether a statusline cell needs a glyph the ASCII pattern
cannot satisfy. It CONFLATED TWO PROBLEMS, and separating them changed the work. Measuring the five
activity glyphs: `◎`, `▶` and `◆` are East Asian Width Ambiguous (THREE, not the two the question
implied), `⇄` is Narrow, and `↩︎` is two code points. The ambiguous hazard is terminal-dependent and
Section 9.4 declines it on its own terms, with ASCII mode as the guarantee, exactly as the question
reasoned. But `↩︎`'s variation selector makes a `len()`-padded cell one column short on EVERY terminal,
and the statusline does pad with bare `len()` (`render_stream.py:936-942`). Half (b) is a real defect with
an owner, and it is the same fix as `_one_line`'s, so E-01 now carries both.

One more thing worth recording as a near-miss I did NOT flag as work: `render_stream.py:170-181` defines
`STATUS_GLYPHS` keyed `completed`/`error`/`running`/`other`. Two of those keys look like lifecycle words,
but they are TOOL-EVENT outcomes that R10.3 permits this module to keep and criterion A18 requires proving
were not remapped. A grep-driven edit would fold them into lifecycle styling, which is precisely what A18
exists to catch, so the scope fence now names them as untouchable.

Suite baseline at review HEAD, run bare: `7468 passed, 3 skipped, 2 xfailed in 109.52s`. Focused baseline
for the four declared test files: `266 passed in 26.07s`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | LOW | IN-SCOPE | A. correctness; G. executability | plan said `runner_shared.py:12789`; measured `:14049`; other four numbers hold; `grep -rn "_STATUS_COLOR\b"` returns 8 matches | The consumption-site line number had drifted +1260 lines, so an executor trusting it would edit the wrong region of a 12822-line file | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Number corrected; E-02 and Step 0 now mandate locating every site by grep and record the 8-match locator; V-02 requires the grep |
| PR-702 | MEDIUM | IN-SCOPE | A. correctness; D. anti-regression | `runner_shared.py:14047-14050` (`glyph = "✓" if reached_success else "●"`, `glyph_color = "green" if reached_success else ...`) | Converting only the `_STATUS_COLOR` lookup leaves a hardcoded glyph pair and a literal `green` success color at the consumption site, so the F-01 readiness/completion collapse survives in the line printed at the end of every run | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | E-02 now requires routing BOTH the glyph and the color through the resolver; V-02 demands that line as evidence; F-01 updated to name the literal |
| PR-703 | MEDIUM | IN-SCOPE | C. architecture; D. anti-regression | `render_stream.py:170-181` (`STATUS_GLYPHS`, `STATUS_GLYPHS_ASCII`), `_status_glyph_char` at `:184`; R10.3; criterion A18 | `STATUS_GLYPHS` is a TOOL-EVENT outcome table whose keys include `running` and `error`, so it reads as a lifecycle table to a grep-driven edit. Folding it in would violate A18, which exists to catch exactly this | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 names it as a trap not a target; F-03 extended; the scope fence forbids touching it; V-01 requires a grep proving it unchanged |
| PR-704 | BLOCKER | OVER-SCOPE | A. correctness; D. anti-regression; F. UX | `term.py:287` lifecycle vs `:394`, `:469`, `:477` generic; verified by execution that all three generic paths resolve through the table; `uonrjg` R10.3; parent `2xz59a`; this plan's own Deferred section | E-04 said DELETE `term.py`'s `STATUS_COLOR_256`, but only one of its four readers is lifecycle. Deleting it removes `aw`'s command-outcome banner, every bracketed badge, and all path styling, while the plan reports criterion A17 satisfied. The parent orchestrator had already ruled the action must be a SPLIT and named this child | C:Low; U:Medium; S:Low; F:High; Overall:Medium | FIXED | E-04 rewritten to SPLIT the table, with the 32/24 key classification measured at review and the `ready`/`quarantined` judgement calls recorded; F-04 added as BLOCKER; Scope, Deferred and the scope fence all state the generic roles are retained; V-04 demands the three retained features still produce output |
| PR-705 | HIGH | UNDER-SCOPE | C. architecture; G. executability | `render_stream.py:88` (`Palette.status`), called `:2269`; `Palette` re-exported `oc_runipd.py:106`, `__all__` `:449`, instantiated `:1324`, `:2018`, `:2057` | The plan named one reader of `_STATUS_COLOR` in this module; there are two, and the second is a PUBLIC method re-exported into both drivers. Removing the table without converting it breaks a public surface, discovered as an import/call failure rather than at review | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | E-01 now names both readers and requires `Palette.status()` be converted or deliberately removed; F-05 added; V-01 item 1 requires the grep to account for both and to state the method's disposition |
| PR-706 | HIGH | UNDER-SCOPE | A. correctness; E. verification | `render_stream.py:222-227`; `bn026f` Deferred `Carrier: qdd5jq`; `grep -c _one_line` on this plan returned 0 | An obligation this Set explicitly assigned to this plan was uncarried: `bn026f` deferred `_one_line`'s variation-selector-severing clip to this child, which never mentioned it. Criterion A15 would have had no owner for this module and the defect would ship | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now carries the fix using `bn026f`'s VS-safe primitive; F-06 added; V-01 item 3 requires the truncation asserted at the ADVERSARIAL boundary with a code-point dump |
| PR-707 | HIGH | IN-SCOPE | A. correctness; G. executability | `runner_shared.INTEGRATION_ACTION_KINDS == ('execute','review')` (`:2451-2455`); `verification_status` `:11394`; `integration_signal` `:1466`; spec A3, Section 7.1, Section 0.5 | E-03 asked for five action-aware activities but `action` carries only two. An agent implementing it literally would emit generic `active` for three of five and silently fail A3, or would widen `INTEGRATION_ACTION_KINDS`, which is a vocabulary change Section 0.5 bounds out | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now names the field per activity, forbids widening the action vocabulary, and REQUIRES an unreachable signal be reported as generic `active` with the activity and missing signal named; F-07 added; V-03 demands the field per activity and the honest-partial disclosure |
| PR-708 | MEDIUM | IN-SCOPE | E. verification | `attention.py:1435` defines the same symbol (owned by `f9t5hz`); criterion A17's text is a property; the retained generic table must survive the split under some name | V-04's `grep STATUS_COLOR_256` guard both FALSE-PASSES (a renamed table could still map a lifecycle status) and FALSE-FAILS (the result depends on a sibling child's work), so it cannot establish A17 | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 and V-05 now require a CONTENT-based guard (no module outside `lifecycle_style` maps a native status to a color or glyph), plus proof it passes WITH the retained generic table; F-08 added; V-04 requires the grep result be interpreted as necessary-but-not-sufficient |
| PR-709 | MEDIUM | UNDER-SCOPE | D. anti-regression; E. testing | `tests/test_term_components.py::PaletteSingleSourceTests` (verified 16 passed): `palette["approved"] == 46` (spec 45), `palette["active"] == 39` (spec 220), and `:68-73` `term_dicts == ["STATUS_COLOR_256"]` | E-04 breaks a currently-passing shipped test in an UNDECLARED file, three ways, including one assertion that fails under both the deletion and the split. Its docstring encodes the single-palette premise this Set replaces | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `tests/test_term_components.py` and `tests/test_term.py` added to `- Scope-Paths:`; E-05 requires the test REWRITTEN to the new invariant rather than deleted, and a check that `test_term.py` no longer references either removed symbol; F-09 added; V-05 demands the repair be described |
| PR-710 | LOW | IN-SCOPE | A. correctness; F. UX | Measured `east_asian_width`: `◎` A, `▶` A, `◆` A, `⇄` N, `↩︎` two code points; statusline padding by bare `len()` at `render_stream.py:936-942` | OQ-01 named one hazard (ambiguous width) and undercounted it as two glyphs when three are Ambiguous, while missing a SECOND, deterministic hazard: `↩︎`'s variation selector misaligns a `len()`-padded cell on every terminal, not just an ambiguous-width one | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 resolved by splitting it: the ambiguous half declined on Section 9.4's own terms in Deferred, the VS half brought in scope under E-01/E-03; F-10 added; V-03 requires a VS-bearing statusline cell measured against a non-VS one |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-04 says delete `term.py`'s `STATUS_COLOR_256`, but three of its four readers are generic roles the spec protects. Fix in place, or escalate as blocking? | FIX IN PLACE as a SPLIT, and write the measured 32/24 key classification into the item so the split is reproducible. | (a) Leave E-04 as written: rejected, it deletes `aw`'s command-outcome banner, every bracketed badge and all path styling, while reporting A17 satisfied. (b) Escalate as `Blocking: yes`: rejected, nothing is open to decide - R10.3 excludes the generic roles in as many words, this plan's own Deferred section already excluded them, and parent `2xz59a` had ALREADY ruled the action is a split and named this child; escalating would spend a maintainer turn re-answering a settled question. (c) Split but leave the key classification to execution: rejected, "which keys are lifecycle" is exactly the judgement that produced the error, and an executor under time pressure would re-derive it from key SHAPE, which is how `ready` and `quarantined` get misplaced. | `term.py:287` (lifecycle) vs `:394`/`:469`/`:477` (generic), each verified by execution; `uonrjg` R10.3 ("Generic `Term` outcomes... remain valid and are outside this spec"); parent `2xz59a` ("child `qdd5jq`'s E-04 must SPLIT this table, retaining the generic roles under a non-lifecycle name"); 56 keys classified against Section 6/7 mapping rows -> 32 lifecycle, 24 generic. | yes |
| D-2 | OQ-01: does a width-constrained statusline cell need machinery the ASCII pattern cannot provide? | SPLIT THE QUESTION. Decline the AMBIGUOUS-width half on Section 9.4's own terms with ASCII mode as the guarantee; bring the VARIATION-SELECTOR half into scope under E-01/E-03 via `bn026f`'s primitives. | (a) Resolve it as the plan framed it ("a conforming ASCII fallback always exists, nothing to do"): rejected, that is true for the ambiguous-width half and FALSE for the VS half, which misaligns deterministically on every terminal in UTF-8 mode where no substitution happens. (b) Require a true wcwidth table: rejected, Section 9.4 states ambiguous alignment cannot be guaranteed, so it would be scope with no achievable acceptance test. (c) Leave OQ-01 open: rejected, both halves are answerable from measurement and each has a clear owner. | Measured `unicodedata.east_asian_width`: `◎` A, `▶` A, `◆` A, `⇄` N, and `↩︎` = U+21A9 + U+FE0E; statusline pads with bare `len()` at `render_stream.py:936-942`; `uonrjg` Section 9.4 ("perfect alignment cannot be guaranteed across every terminal's ambiguous-width policy" and "MUST NOT create per-renderer width guesses"); `bn026f` E-04 builds both primitives. | yes |
| D-3 | Criterion A3 wants five activities but the runner's `action` carries two. Mandate a data-flow change, or permit a partial? | PERMIT AN HONEST PARTIAL, and REQUIRE it be disclosed with the activity and the missing signal named. Forbid widening the action vocabulary. | (a) Mandate all five render: rejected, three signals live on fields other than `action` and reaching them at the render site may require a data-flow change beyond presentation, which Section 0.5 bounds out of this spec. (b) Permit the partial silently: rejected, that is how a criterion gets reported satisfied when three of five were never wired, and it is unfalsifiable from the evidence. (c) Widen `INTEGRATION_ACTION_KINDS` to add the missing kinds: rejected outright, that is a runner VOCABULARY change, which Section 0.5 excludes and this plan's Deferred section already excludes. | `runner_shared.INTEGRATION_ACTION_KINDS == ('execute','review')` (`:2451-2455`); `item["verification_status"]` (`:11394`), `item["integration_signal"]` (`:1466`), retry ladder constants (`:2696-2730`); spec Section 7.1 permits generic `running`/`active` "only when the subtype is genuinely unavailable"; Section 0.5 ("covers DISPLAY only"). | yes |
| D-4 | Should criterion A17 be asserted by the absence of the string `STATUS_COLOR_256`, as V-04 required? | NO. Assert by CONTENT: no module outside `lifecycle_style` maps a native status to a color or glyph. | (a) Keep the name-based grep as the proof: rejected, it false-passes (the retained generic table could be renamed while still mapping `approved`) and false-fails (`attention.py` defines the same symbol, and its removal belongs to sibling `f9t5hz`, so this child's guard would depend on another child's work). (b) Drop the grep entirely: rejected, it remains useful corroboration and is cheap; it is just not sufficient, so V-04 now requires its result be INTERPRETED rather than presented as the whole proof. | Criterion A17's text is "No second lifecycle color or glyph table remains", a property rather than a symbol name; `attention.py:1435`; the split necessarily leaves a generic role dict in `term.py`; `tests/test_term_components.py:68-73` shows a name-based assertion failing on exactly that. | yes |
| D-5 | `bn026f` assigned `render_stream._one_line` to this plan and the plan did not carry it. Add it here, or let the carrier chain lapse? | ADD IT HERE, under E-01, using `bn026f`'s VS-safe truncation primitive. | (a) Let it lapse: rejected, criterion A15 would have no owner for this module and the defect ships; the carrier mechanism exists precisely to prevent a deferral evaporating. (b) Send it back to `bn026f`: rejected, `bn026f`'s `- Scope-Paths:` is `term.py` plus its test, so it may not edit `render_stream.py`; that is WHY it was deferred here. (c) File a new child for it: rejected as disproportionate for one clip site in a file this plan already declares and already converts. | `render_stream.py:222-227` (`collapsed[: limit - 1]`); `bn026f` Deferred section, `Carrier: qdd5jq`, with the measured U+FE0E loss; `bn026f` `- Scope-Paths:` excludes `render_stream.py`; this plan declares it. | yes |
